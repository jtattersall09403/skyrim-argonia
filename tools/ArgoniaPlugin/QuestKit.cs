using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Strings;
using Noggog;

// The one quest kit: the proven block shapes of ARG_BlockTest (BlockTest.cs, docs/design/blocks.md) as helpers for every
// quest builder (MainQuest, LocalQuests, Chainbreakers, NightReed, MQ04, MQ05). Each helper builds exactly the record
// shape the block test proved, once; a builder constructs a kit per quest and defines no helper of its own.
//   spots      Snap (navmesh), Land; Marker, Ref, Actor, Zone, Lock, Item, Global, Faction, Persist, Interior, Exterior, World
//   base       Base (Ai.Template: looks and AI from the template; Ai.Own: looks only, our own AI data)
//   packages   Travel, Follow, Schedule
//   conditions C, OnPlayer, StageIs, Done, Glob, Or, Not, Speech, Has, HasOn, IsId, IsRef, Hour, Dead, Rank, Unseen
//   scripts    Script, Obj, Alias, Int, AliasScript, Forced, DeathSets, AcquireSets, ActivateSets, OnDeath, Target, Finish
//   quest      Header, FromRecord, SetStages, StagesFromRecord, ObjectivesFromRecord
//   dialogue   Gate, Banded, Topic, Record, RecordV, Store, Hello, Info; readers Rows, Lines, BandLines, Gates, Label,
//              QuestLines, After, Written, StoreBand; WritePsc
sealed class QuestKit(SkyrimMod mod, List<ISkyrimModGetter> mods, Quest? q = null, string prefix = "")
{
    public static FormKey K(string k) => FormKey.Factory(k);
    public static FormLink<ISkyrimMajorRecordGetter> L(FormKey k) => new(k);
    public static readonly FormKey XMarker = K("00003B:Skyrim.esm"), PlayerRef = K("000014:Skyrim.esm"), Gold = K("00000F:Skyrim.esm"),
        TrigBase = K("099312:Skyrim.esm");
    public SkyrimMod Mod => mod;
    public Quest Q => q ?? throw new InvalidOperationException("this kit has no quest");

    // ---- what the load order holds, read once for every kit
    sealed class Data(List<ISkyrimModGetter> mods)
    {
        public readonly List<ISkyrimModGetter> Mods = mods;
        public readonly Dictionary<FormKey, (IPlacedGetter rec, ModKey from)> Placed = Survey.Winners<IPlacedGetter>(mods);
        public readonly Dictionary<FormKey, (INpcGetter rec, ModKey from)> Npcs = Survey.Winners<INpcGetter>(mods);
        // The winning navmesh of each id: the last plugin in the load order that has it (one that deleted it carries no data).
        public readonly Dictionary<FormKey, (INavigationMeshGetter rec, ModKey from)> Nav = mods.SelectMany(m => m.EnumerateMajorRecords<INavigationMeshGetter>()
            .Select(r => (r, m.ModKey))).GroupBy(e => e.r.FormKey).ToDictionary(g => g.Key, g => g.Last());
        public IPlacedObjectGetter? Trig;
    }
    static Data? loaded;
    Data D => loaded != null && ReferenceEquals(loaded.Mods, mods) ? loaded : loaded = new Data(mods);
    public Dictionary<FormKey, (IPlacedGetter rec, ModKey from)> Placed => D.Placed;
    public Dictionary<FormKey, (INpcGetter rec, ModKey from)> Npcs => D.Npcs;
    // The triangles every kit has taken, so no two places stand on one triangle.
    static readonly HashSet<(FormKey, int)> used = [];
    // The base of each placed actor a kit made or re-based, so a check can read the base of a ref the load order does not hold.
    static readonly Dictionary<FormKey, FormKey> madeBase = [];
    /// The triangles taken so far, to put back after a trial build (Taken(saved)).
    public static HashSet<(FormKey, int)> Taken() => [.. used];
    public static void Taken(HashSet<(FormKey, int)> saved) { used.Clear(); used.UnionWith(saved); }

    // ---- story data (story/data/db, the one source)
    static readonly string Db = Path.Combine("story", "data", "db");
    public static IEnumerable<JsonElement> Rows(string table) =>
        File.ReadLines(Path.Combine(Db, table + ".jsonl")).Where(l => l.Trim().Length > 0).Select(l => JsonDocument.Parse(l).RootElement);
    static string? Str(JsonElement e, string k) => e.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.String ? v.GetString() : null;
    /// The record's stages of a quest: id, journal text, completing; objectives by stage.
    public static List<(int id, string journal, bool ending)> Stages(string quest) =>
        Rows("quest_stage").Where(r => Str(r, "quest_id") == quest)
            .Select(r => (int.Parse(r.GetProperty("id").ToString()), Str(r, "journal_text") ?? "", Str(r, "ending") != null)).OrderBy(s => s.Item1).ToList();
    /// The record's failing endings (quest_stage ending = failed): a Fail Quest log entry instead of Complete Quest.
    public static HashSet<int> Failed(string quest) =>
        [.. Rows("quest_stage").Where(r => Str(r, "quest_id") == quest && Str(r, "ending") == "failed").Select(r => int.Parse(r.GetProperty("id").ToString()))];
    /// The record's hidden stages (quest_stage rows with hidden = 1 and no text): set by script, never in the journal.
    public static HashSet<int> Hidden(string quest) =>
        [.. Rows("quest_stage").Where(r => Str(r, "quest_id") == quest && r.TryGetProperty("hidden", out var h) && h.ValueKind == JsonValueKind.Number && h.GetInt32() == 1)
            .Select(r => int.Parse(r.GetProperty("id").ToString()))];
    public static List<(int stage, string id, string text)> Objectives(string quest)
    {
        var byOrd = Rows("quest_stage").Where(r => Str(r, "quest_id") == quest)
            .ToDictionary(r => r.GetProperty("ord").GetInt32(), r => int.Parse(r.GetProperty("id").ToString()));
        return Rows("quest_objective").Where(r => Str(r, "quest_id") == quest)
            .OrderBy(r => r.GetProperty("stages_ord").GetInt32()).ThenBy(r => r.GetProperty("ord").GetInt32())
            .Select(r => (byOrd[r.GetProperty("stages_ord").GetInt32()], Str(r, "id")!, Str(r, "objective_text") ?? "")).ToList();
    }
    /// The written lines of a topic for a speaker and gate (dialogue_line keys_topic, speaker), in id order; empty until written.
    /// A gate (default, speech, item) is the id's second-last segment (line.<topic>.<speaker>.<gate>.<nn>).
    public static List<string> Lines(string topic, string speaker, string gate = "default") =>
        Rows("dialogue_line").Where(r => Str(r, "keys_topic") == topic && Str(r, "speaker") == speaker && Str(r, "id")!.Split('.')[^2] == gate)
            .OrderBy(r => Str(r, "id")).Select(r => Str(r, "words")!).ToList();
    /// A gate's wording band (low or high): the variants_<band> of the gate's first row, the whole band's text, spoken as
    /// lines split at sentence ends (about 150 characters each); empty when the band is not written.
    public static List<string> BandLines(string topic, string speaker, string gate, string band)
    {
        var row = Rows("dialogue_line").Where(r => Str(r, "keys_topic") == topic && Str(r, "speaker") == speaker && Str(r, "id")!.Split('.')[^2] == gate)
            .OrderBy(r => Str(r, "id")).FirstOrDefault();
        var s = row.ValueKind == JsonValueKind.Undefined ? null : Str(row, "variants_" + band);
        if (string.IsNullOrWhiteSpace(s)) return [];
        var lines = new List<string>();
        foreach (var sentence in System.Text.RegularExpressions.Regex.Split(s.Trim(), @"(?<=[.!?])\s+"))
            if (lines.Count > 0 && lines[^1].Length + 1 + sentence.Length <= 150) lines[^1] += " " + sentence; else lines.Add(sentence);
        return lines;
    }
    /// The gates (topic, speaker, gate) of the written quest lines whose topic starts with the prefix (topic.mq04-).
    public static List<(string topic, string speaker, string gate)> Gates(string prefix) =>
        [.. Rows("dialogue_line").Where(r => Str(r, "keys_topic")?.StartsWith(prefix) == true && Str(r, "status") == "written")
            .Select(r => (Str(r, "keys_topic")!, Str(r, "speaker")!, Str(r, "id")!.Split('.')[^2])).Distinct()];
    public static string Label(string topic) =>
        Rows("quest_topic").Where(r => Str(r, "id") == topic).Select(r => Str(r, "label")).FirstOrDefault() ?? throw new Exception($"no topic {topic}");
    /// A quest's lines by topic (story/data/quest_lines/<code>.json): a topic has either "infos" (one per variant, each with
    /// its prompt and lines) or its own prompt and lines, with other variants as further keys; a band is "<key>@high" / "<key>@low".
    public static JsonElement QuestLines(string code) => JsonDocument.Parse(File.ReadAllText(Path.Combine("story", "data", "quest_lines", code + ".json"))).RootElement;
    /// The written after-quest lines (story/data/dialogue-writer/quest/<code>/<who>.after.tsv) of one variant.
    public static List<string> After(string code, string who, string variant = "after") =>
        File.ReadLines(Path.Combine("story", "data", "dialogue-writer", "quest", code, who + ".after.tsv")).Skip(1)
            .Select(l => l.Split('\t')).Where(p => p.Length >= 5 && p[1] == variant).Select(p => p[4]).ToList();
    /// A line store (a TSV of "<key><tab><line>"; # comments): the lines by key. Bands are keys "<key>@<band>.<n>".
    public static Dictionary<string, string> Written(string path) => File.ReadLines(path).Where(l => l.Length > 0 && l[0] != '#')
        .Select(l => l.Split('\t', 2)).ToDictionary(x => x[0], x => x[1]);
    /// A band's spoken lines of a store key, in n order; empty when not written.
    public static List<string> StoreBand(Dictionary<string, string> store, string key, string band) =>
        [.. store.Where(w => w.Key.StartsWith($"{key}@{band}.")).OrderBy(w => int.Parse(w.Key[(w.Key.LastIndexOf('.') + 1)..])).Select(w => w.Value)];

    // ---- conditions (C-stage, C-skill, C-item, C-time, C-global, GetIsID / GetIsReference as W-talk)
    public static ConditionFloat C(ConditionData d, CompareOperator op, float v, bool or = false) =>
        new() { CompareOperator = op, ComparisonValue = v, Data = d, Flags = or ? Condition.Flag.OR : 0 };
    public static T OnPlayer<T>(T d) where T : ConditionData { d.RunOnType = Condition.RunOnType.Reference; d.Reference.SetTo(PlayerRef); return d; }
    public static ConditionFloat StageIs(Quest q, CompareOperator op, int s) { var d = new GetStageConditionData(); d.Quest.Link.SetTo(q.FormKey); return C(d, op, s); }
    public ConditionFloat StageIs(int s, CompareOperator op = CompareOperator.EqualTo) => StageIs(Q, op, s);
    public static ConditionFloat Done(Quest q, int s) { var d = new GetStageDoneConditionData { Stage = s }; d.Quest.Link.SetTo(q.FormKey); return C(d, CompareOperator.EqualTo, 1); }
    public static ConditionFloat Glob(Global g, float v) { var d = new GetGlobalValueConditionData(); d.Global.Link.SetTo(g.FormKey); return C(d, CompareOperator.EqualTo, v); }
    public static ConditionFloat Or(ConditionFloat c) { c.Flags |= Condition.Flag.OR; return c; }
    public static ConditionFloat Not(ConditionFloat c) { c.ComparisonValue = 0; c.CompareOperator = CompareOperator.EqualTo; return c; }
    public static ConditionFloat Speech(CompareOperator op, float v) => C(OnPlayer(new GetActorValueConditionData { ActorValue = ActorValue.Speech }), op, v);
    public static ConditionFloat Speech(float v) => Speech(CompareOperator.GreaterThanOrEqualTo, v);
    public static ConditionFloat Has(FormKey item, float n) { var d = new GetItemCountConditionData(); d.ItemOrList.Link.SetTo(item); OnPlayer(d); return C(d, CompareOperator.GreaterThanOrEqualTo, n); }
    /// C-item on the speaker (the condition's default subject).
    public static ConditionFloat HasOn(FormKey item, float n = 1) { var d = new GetItemCountConditionData(); d.ItemOrList.Link.SetTo(item); return C(d, CompareOperator.GreaterThanOrEqualTo, n); }
    public static ConditionFloat IsId(FormKey npc) { var d = new GetIsIDConditionData(); d.Object.Link.SetTo(npc); return C(d, CompareOperator.EqualTo, 1); }
    public static ConditionFloat IsId(INpcGetter npc) => IsId(npc.FormKey);
    public static ConditionFloat IsRef(FormKey r) { var d = new GetIsReferenceConditionData(); d.Target.Link.SetTo(r); return C(d, CompareOperator.EqualTo, 1); }
    public static ConditionFloat Hour(CompareOperator op, float h, bool or = false) => C(new GetCurrentTimeConditionData(), op, h, or);
    public static ConditionFloat Dead(uint alias, bool dead) => C(new GetDeadConditionData { RunOnType = Condition.RunOnType.QuestAlias, RunOnTypeIndex = (int)alias }, CompareOperator.EqualTo, dead ? 1 : 0);
    /// The speaker's regard for the player (Talk's greet-friend gate): warm at rank >= 1, cool below 0 (rival or worse).
    public static ConditionFloat Rank(CompareOperator op, float v) { var d = new GetRelationshipRankConditionData(); d.TargetNpc.Link.SetTo(PlayerRef); return C(d, op, v); }
    public static readonly (string band, CompareOperator op, float v)[] Bands = [("high", CompareOperator.GreaterThanOrEqualTo, 1), ("low", CompareOperator.LessThan, 0)];
    /// C-detected: the reference does not detect the player.
    public static ConditionFloat Unseen(IFormKeyGetter by) { var d = new GetDetectedConditionData { RunOnType = Condition.RunOnType.Reference }; d.Reference.SetTo(by.FormKey); d.TargetNpc.Link.SetTo(PlayerRef); return C(d, CompareOperator.EqualTo, 0); }

    /// C-detected: the reference detects the player (an estate man's watch); `or` chains it with the next.
    public static ConditionFloat Seen(IFormKeyGetter by, bool or = false) { var d = new GetDetectedConditionData { RunOnType = Condition.RunOnType.Reference }; d.Reference.SetTo(by.FormKey); d.TargetNpc.Link.SetTo(PlayerRef); return C(d, CompareOperator.EqualTo, 1, or); }

    // ---- scripts
    public static ScriptEntry Script(string name, params ScriptProperty[] ps) { var e = new ScriptEntry { Name = name }; e.Properties.AddRange(ps); return e; }
    public static ScriptObjectProperty Obj(string n, FormKey k) => new() { Name = n, Object = L(k) };
    public ScriptObjectProperty Alias(string n, uint id) => Alias(n, Q, id);
    public static ScriptObjectProperty Alias(string n, Quest q, uint id) => new() { Name = n, Object = L(q.FormKey), Alias = (short)id };
    public static ScriptIntProperty Int(string n, int v) => new() { Name = n, Data = v };

    // ---- world edits
    public enum Ai { Template, Own }
    /// W-npc / W-fixed: a base templated on a BM&V or vanilla base for looks, our name, a fixed level (decision 0035).
    /// Ai.Template takes looks and AI (data, packages, factions, script) from the template; Ai.Own takes looks only, with
    /// our own AI data (no crime, helps nobody) and the template's voice. The female flag is the template's unless given.
    public Npc Base(string id, string name, string tpl, short level, NpcConfiguration.Flag extra = 0, Ai ai = Ai.Template,
        Aggression aggression = Aggression.Unaggressive, bool? female = null)
    {
        const NpcConfiguration.TemplateFlag looks = NpcConfiguration.TemplateFlag.Traits | NpcConfiguration.TemplateFlag.SpellList
            | NpcConfiguration.TemplateFlag.ModelAnimation | NpcConfiguration.TemplateFlag.AttackData | NpcConfiguration.TemplateFlag.Keywords
            | NpcConfiguration.TemplateFlag.Inventory;
        const NpcConfiguration.TemplateFlag all = looks | NpcConfiguration.TemplateFlag.Factions | NpcConfiguration.TemplateFlag.AIData
            | NpcConfiguration.TemplateFlag.AIPackages | NpcConfiguration.TemplateFlag.Script | NpcConfiguration.TemplateFlag.DefPackList;
        var t = Npcs[K(tpl)].rec;
        var n = mod.Npcs.AddNew(id);
        n.Name = name;
        n.Template.SetTo(t.FormKey);
        n.Race.SetTo(t.Race.FormKey);
        n.Class.SetTo(t.Class.FormKey);
        n.Configuration.TemplateFlags = ai == Ai.Own ? looks : all;
        n.Configuration.Level = new NpcLevel { Level = level };
        var sex = female is bool f ? (f ? NpcConfiguration.Flag.Female : 0) : t.Configuration.Flags & NpcConfiguration.Flag.Female;
        n.Configuration.Flags = NpcConfiguration.Flag.AutoCalcStats | sex | extra;
        if (ai == Ai.Own)
        {
            n.AIData = new AIData { Aggression = aggression, Confidence = Confidence.Average, Responsibility = Responsibility.NoCrime, Assistance = Assistance.HelpsNobody };
            n.Voice.SetTo(t.Voice.FormKey);
        }
        return n;
    }

    // The nearest unused triangle centre of a navmesh to a spot (BlockTest's Snapper): over the last copy of each navmesh that
    // carries data; the used set is shared by every kit, so no two places in the plugin stand on one triangle.
    IEnumerable<(FormKey mesh, int i, P3Float p)> Triangles(FormKey mesh)
    {
        var (rec, from) = D.Nav.TryGetValue(mesh, out var w) ? w : throw new InvalidOperationException($"navmesh {mesh} is in no plugin of the load order");
        var d = rec.Data ?? throw new InvalidOperationException($"navmesh {mesh}: the winner, {from.FileName}, carries no data (deleted); name the navmesh that replaced it (plugin.sh inspect navnear)");
        var v = d.Vertices;
        return Enumerable.Range(0, d.Triangles.Count).Where(i => !used.Contains((mesh, i))).Select(i =>
        {
            var t = d.Triangles[i].Vertices; var a = v[t.X]; var b = v[t.Y]; var c = v[t.Z];
            return (mesh, i, p: new P3Float((a.X + b.X + c.X) / 3, (a.Y + b.Y + c.Y) / 3, (a.Z + b.Z + c.Z) / 3));
        });
    }
    static P3Float Take(IEnumerable<(FormKey mesh, int i, P3Float p)> triangles, Func<P3Float, float> cost)
    {
        var best = triangles.MinBy(e => cost(e.p));
        used.Add((best.mesh, best.i));
        return new P3Float(MathF.Round(best.p.X), MathF.Round(best.p.Y), MathF.Round(best.p.Z));
    }
    public P3Float Snap(FormKey mesh, float x, float y) => Take(Triangles(mesh), p => (p.X - x) * (p.X - x) + (p.Y - y) * (p.Y - y));
    /// The same, nearest in three dimensions: a deck above a deck (MainQuest's barge hold) keeps to the named level.
    public P3Float Snap(FormKey mesh, float x, float y, float z) => Take(Triangles(mesh), p => (p.X - x) * (p.X - x) + (p.Y - y) * (p.Y - y) + 16 * (p.Z - z) * (p.Z - z));
    /// The same over every navmesh of a cell, from every plugin's copy of the cell (an override, Black Marsh North's, carries
    /// no navmesh group of its own).
    public P3Float Snap(string cell, float x, float y)
    {
        var meshes = mods.SelectMany(m => m.EnumerateMajorRecords<ICellGetter>().Where(c => c.FormKey == K(cell)))
            .SelectMany(c => c.NavigationMeshes.Select(n => n.FormKey)).Distinct();
        return Take(meshes.Where(m => D.Nav.TryGetValue(m, out var w) && w.rec.Data != null).SelectMany(Triangles), p => (p.X - x) * (p.X - x) + (p.Y - y) * (p.Y - y));
    }
    /// The land's height under a spot of a worldspace.
    public float Land(FormKey world, float x, float y) => Surface.Land(mods, world, x, y) ?? throw new InvalidOperationException($"no land at {x},{y}");
    /// The navmeshes of a cell (exterior or interior), from the load order's winners.
    public List<FormKey> Meshes(FormKey cell) => D.Nav.Where(kv => kv.Value.rec.Data?.Parent is { } p
        && p.GetType().GetProperties().Any(pr => pr.GetValue(p) is IFormLinkGetter l && l.FormKey == cell)).Select(kv => kv.Key).ToList();
    public INavigationMeshGetter Mesh(FormKey k) => D.Nav[k].rec.Data != null ? D.Nav[k].rec : throw new InvalidOperationException($"navmesh {k}: the winner carries no data (deleted)");
    public P3Float Pos(FormKey key) => Placed[key].rec.Placement!.Position;

    static void Parent(IPlaced r, PlacedObject parent, bool opposite = false)
    {
        var e = new EnableParent { Flags = opposite ? EnableParent.Flag.SetEnableStateToOppositeOfParent : 0 };
        e.Reference.SetTo(parent.FormKey);
        switch (r) { case PlacedObject o: o.EnableParent = e; break; case PlacedNpc n: n.EnableParent = e; break; }
    }
    /// A marker (the vanilla X marker, or a base given), persistent unless flagged, optionally under an enable parent.
    public PlacedObject Marker(string id, P3Float p, FormKey? baseKey, int flags = 0x400, PlacedObject? parent = null, bool opposite = false)
    {
        var r = new PlacedObject(mod.GetNextFormKey(), SkyrimRelease.SkyrimSE)
        { EditorID = prefix + id, Base = new FormLinkNullable<IPlaceableObjectGetter>(baseKey ?? XMarker), MajorRecordFlagsRaw = flags, Placement = new Placement { Position = p } };
        if (parent != null) Parent(r, parent, opposite);
        return r;
    }
    public PlacedObject Marker(string id, P3Float p, int flags = 0x400) => Marker(id, p, null, flags);
    /// W-ref: a placed thing (static, furniture, item, door) of a base, persistent, optionally under an enable parent.
    public PlacedObject Ref(string id, FormKey baseKey, P3Float p, PlacedObject? parent = null, float? scale = null, P3Float? rot = null)
    {
        var r = new PlacedObject(mod.GetNextFormKey(), SkyrimRelease.SkyrimSE)
        { EditorID = prefix + id, MajorRecordFlagsRaw = 0x400, Placement = new Placement { Position = p, Rotation = rot ?? new P3Float() }, Scale = scale };
        r.Base.SetTo(baseKey);
        if (parent != null) Parent(r, parent);
        return r;
    }
    public PlacedNpc Actor(string id, Npc b, P3Float p, PlacedObject? parent = null, int flags = 0x400)
    {
        var r = new PlacedNpc(mod.GetNextFormKey(), SkyrimRelease.SkyrimSE)
        { EditorID = prefix + id, MajorRecordFlagsRaw = flags, Placement = new Placement { Position = p } };
        r.Base.SetTo(b.FormKey);
        madeBase[r.FormKey] = b.FormKey;
        if (parent != null) Parent(r, parent);
        return r;
    }
    // The zones this kit made for its quest (Finish binds them to the quest script and refuses overlapping consecutive ones).
    readonly List<(PlacedObject z, int prereq, int stage, P3Float half)> zones = [];
    /// TR-zone: the vanilla set-stage box (defaultSetStageTrigScript, a prerequisite stage), 2 * half in each axis
    /// (300 x 300 x 200 when none is given), optionally under an enable parent. Recorded for the quest: Finish gives the
    /// quest script every zone in its `Zones` array, which the endings disarm.
    public PlacedObject Zone(string id, P3Float p, int prereq, int stage, P3Float? half = null, PlacedObject? parent = null)
    {
        var trig = D.Trig ??= mods[0].EnumerateMajorRecords<IPlacedObjectGetter>().First(r => r.Base.FormKey == TrigBase && r.Primitive != null);
        var z = new PlacedObject(mod.GetNextFormKey(), SkyrimRelease.SkyrimSE)
        {
            EditorID = prefix + id, MajorRecordFlagsRaw = 0x400, Placement = new Placement { Position = p },
            Primitive = trig.Primitive!.DeepCopy(),
            VirtualMachineAdapter = new VirtualMachineAdapter { Scripts = { Script("defaultSetStageTrigScript", Obj("myQuest", Q.FormKey), Int("prereqStageOPT", prereq), Int("stage", stage)) } },
        };
        z.Primitive.Bounds = half ?? new P3Float(300, 300, 200);
        z.Base.SetTo(TrigBase);
        if (parent != null) Parent(z, parent);
        zones.Add((z, prereq, stage, z.Primitive.Bounds));
        return z;
    }
    /// W-override: our copy of a winning placed door or container, persistent, locked (to a key when given).
    public PlacedObject Lock(FormKey placed, LockLevel level, FormKey? key = null)
    {
        var r = (PlacedObject)((IPlacedObjectGetter)Placed[placed].rec).DeepCopy();
        r.MajorRecordFlagsRaw |= 0x400;
        r.Lock = new LockData { Level = level };
        if (key is FormKey k) r.Lock.Key.SetTo(k);
        return r;
    }
    /// A BM&V ref an alias names: persistent (record flag 0x400), and, when a new base is given, placing it, in the world's
    /// persistent cell.
    public void Persist(Worldspace world, FormKey key, Npc? newBase = null)
    {
        var other = Overrides.Placed(mod, key);
        var existing = world.TopCell!.Persistent.OfType<PlacedNpc>().FirstOrDefault(r => r.FormKey == key);
        if (other is PlacedNpc moved && existing == null)
        {
            // another step (Talk's names) overrode it in its exterior cell: move that override to the persistent cell
            foreach (var b in world.SubCells) foreach (var sb in b.Items) foreach (var c in sb.Items) c.Temporary.Remove(moved);
            existing = moved; world.TopCell!.Persistent.Add(moved);
        }
        else if (other != null && existing == null) throw new Exception($"{key}: overridden by another step where this quest cannot take it");
        var src = (IPlacedNpcGetter)Placed[key].rec;
        if (existing == null && newBase == null && (src.MajorRecordFlagsRaw & 0x400) != 0) return;
        var r = existing ?? (PlacedNpc)src.DeepCopy();
        r.MajorRecordFlagsRaw |= 0x400;
        if (newBase != null) { r.Base.SetTo(newBase.FormKey); madeBase[r.FormKey] = newBase.FormKey; }
        if (existing == null) world.TopCell!.Persistent.Add(r);
    }
    /// A quest item (MISC) with an existing model (never made art).
    public MiscItem Item(string id, string name, string model, float weight = 0.5f)
    {
        var m = mod.MiscItems.AddNew(prefix + id);
        m.Name = name; m.Value = 0; m.Weight = weight; m.Model = new Model { File = model };
        return m;
    }
    public string ModelOf(FormKey baseKey) =>
        mods.SelectMany(m => m.EnumerateMajorRecords<IModeledGetter>()).Last(r => ((IMajorRecordGetter)r).FormKey == baseKey).Model!.File.DataRelativePath.Path;
    public Global Global(string id) { var g = mod.Globals.AddNewShort(prefix + id); g.Data = 0; return g; }
    /// E-faction: a faction with a rank of each title, optionally hidden from the player.
    public Faction Faction(string id, string name, bool hidden = false, params string[] ranks)
    {
        var f = mod.Factions.AddNew(prefix + id);
        f.Name = name;
        if (hidden) f.Flags = Mutagen.Bethesda.Skyrim.Faction.FactionFlag.HiddenFromPC;
        for (var i = 0; i < ranks.Length; i++)
            f.Ranks.Add(new Rank { Number = (uint)i, Title = new GenderedItem<TranslatedString?>(new TranslatedString(Language.English, ranks[i]), new TranslatedString(Language.English, ranks[i])) });
        return f;
    }

    // ---- packages
    Package Duplicate(string from) => mods[0].Packages.First(p => p.EditorID == from).Duplicate(mod.GetNextFormKey());
    static void Locate(Package p, PlacedObject at, int radius)
    {
        foreach (var d in p.Data.Values.OfType<PackageDataLocation>().Take(1))
        {
            d.Location = new LocationTargetRadius { Target = new LocationTarget(), Radius = (uint)radius };
            ((LocationTarget)d.Location.Target).Link.SetTo(at.FormKey);
        }
    }
    /// E-package: the proven Travel package (a copy of vanilla DA06YamarzStage70PostForcegreet) to a marker, gated. The quest
    /// owns every package the kit makes.
    public Package Travel(string id, PlacedObject to, int radius, params ConditionFloat[] conds)
    {
        var p = Duplicate("DA06YamarzStage70PostForcegreet");
        p.EditorID = prefix + id; p.OwnerQuest.SetTo(Q.FormKey); p.Conditions.Clear(); p.Conditions.AddRange(conds);
        Locate(p, to, radius);
        mod.Packages.Add(p);
        return p;
    }
    /// E-package: follow the player (a copy of vanilla WERoad02Follow), gated.
    public Package Follow(string id, params ConditionFloat[] conds)
    {
        var p = Duplicate("WERoad02Follow");
        p.EditorID = prefix + id; p.OwnerQuest.SetTo(Q.FormKey); p.Conditions.Clear(); p.Conditions.AddRange(conds);
        var t = p.Data.Values.OfType<PackageDataTarget>().First();
        var target = new PackageTargetSpecificReference(); target.Reference.SetTo(PlayerRef);
        t.Target = target;
        mod.Packages.Add(p);
        return p;
    }
    /// E-package: a copy of a named vanilla package on a schedule (hour -1: always), its location (when it has one and `at`
    /// is given) set to a marker, gated.
    public Package Schedule(string id, string from, PlacedObject? at, int radius, sbyte hour, int minutes, params ConditionFloat[] conds)
    {
        var p = Duplicate(from);
        p.EditorID = prefix + id; p.OwnerQuest.SetTo(Q.FormKey); p.Conditions.Clear(); p.Conditions.AddRange(conds);
        p.ScheduleHour = hour; p.ScheduleDurationInMinutes = minutes;
        if (at != null) Locate(p, at, radius);
        mod.Packages.Add(p);
        return p;
    }

    // ---- quest records
    public QuestAlias Forced(uint id, string name, FormKey r, QuestAlias.Flag flags = 0)
    {
        var a = new QuestAlias { ID = id, Type = QuestAlias.TypeEnum.Reference, Name = name, Flags = flags };
        a.ForcedReference.SetTo(r);
        Q.Aliases.Add(a);
        return a;
    }
    public QuestAlias Forced(uint id, string name, IPlacedGetter r, QuestAlias.Flag flags = 0) => Forced(id, name, r.FormKey, flags);
    public QuestFragmentAlias AliasScript(uint id, ScriptEntry s) { var f = new QuestFragmentAlias { Property = Alias("", id) }; f.Scripts.Add(s); return f; }
    public static ScriptEntry OnDeath(Quest q, int prereq, int set) =>
        Script("defaultSetStageOnDeathRefAlias", Obj("myQST", q.FormKey), Int("preReqStage", prereq), Int("StageToSet", set));
    /// TR-death: the alias's death sets a stage. An Essential person cannot die, so an alias flagged Essential, or whose
    /// forced ref has an Essential base, is refused.
    public static QuestFragmentAlias DeathSets(QuestKit k, uint id, int prereq, int stage)
    {
        var a = k.Q.Aliases.Single(x => x.ID == id);
        if (a.Flags is { } af && af.HasFlag(QuestAlias.Flag.Essential)) throw new InvalidOperationException($"{k.Q.EditorID}: alias {id} ({a.Name}) is Essential and cannot die; no death trigger");
        var r = a.ForcedReference.FormKey;
        var b = madeBase.TryGetValue(r, out var mb) ? mb : k.Placed.TryGetValue(r, out var p) && p.rec is IPlacedNpcGetter pn ? pn.Base.FormKey : default;
        var flags = k.Mod.Npcs.FirstOrDefault(n => n.FormKey == b)?.Configuration.Flags ?? (k.Npcs.TryGetValue(b, out var n0) ? n0.rec.Configuration.Flags : 0);
        if (b != default && flags.HasFlag(NpcConfiguration.Flag.Essential)) throw new InvalidOperationException($"{k.Q.EditorID}: alias {id} ({a.Name}) holds an Essential base ({b}); no death trigger");
        return k.AliasScript(id, OnDeath(k.Q, prereq, stage));
    }
    public static QuestFragmentAlias AcquireSets(QuestKit k, uint id, int prereq, int stage) =>
        k.AliasScript(id, Script("defaultSetStageOnPlayerAcquire", Obj("myQST", k.Q.FormKey), Int("preReqStage", prereq), Int("StageToSet", stage)));
    /// TR-activate: the alias's ref, once activated, sets a stage (defaultSetStageAliasScript, TriggerType 0).
    public static QuestFragmentAlias ActivateSets(QuestKit k, uint id, int prereq, int stage) =>
        k.AliasScript(id, Script("defaultSetStageAliasScript", Int("stage", stage), Int("prereqStageOPT", prereq), Int("TriggerType", 0)));

    /// An objective's compass targets: the aliases it points at (the objective's index, the quest's alias ids).
    public void Target(int objective, params uint[] aliasIds)
    {
        var o = Q.Objectives.SingleOrDefault(x => x.Index == objective) ?? throw new InvalidOperationException($"{Q.EditorID}: no objective {objective} to target");
        foreach (var id in aliasIds)
        {
            if (!Q.Aliases.Any(x => x.ID == id)) throw new InvalidOperationException($"{Q.EditorID}: objective {objective} targets alias {id}, which the quest does not have");
            o.Targets.Add(new QuestObjectiveTarget { AliasID = (int)id });
        }
    }
    /// The last call of a builder's quest: Run Once; the quest script's `Zones` array bound to exactly the zones the kit made
    /// for the quest (the endings disarm them); a refusal of an objective without a target; and a refusal of two zones
    /// that overlap when one's stage is the other's prerequisite (a walk through one would set the next at once).
    public void Finish()
    {
        Q.Flags |= Quest.Flag.RunOnce;
        if (zones.Count > 0)
        {
            var script = Q.VirtualMachineAdapter?.Scripts.SingleOrDefault(x => x.Name == Q.VirtualMachineAdapter.FileName)
                ?? throw new InvalidOperationException($"{Q.EditorID}: no quest script to hold its Zones");
            script.Properties.RemoveAll(p => p.Name == "Zones");
            script.Properties.Add(new ScriptObjectListProperty { Name = "Zones", Objects = zones.Select(z => (ScriptObjectProperty)new ScriptObjectProperty { Object = L(z.z.FormKey) }).ToExtendedList() });
        }
        foreach (var a in zones) foreach (var b in zones)
        {
            if (a.z == b.z || a.stage != b.prereq) continue;
            var pa = a.z.Placement!.Position; var pb = b.z.Placement!.Position;
            if (MathF.Abs(pa.X - pb.X) < a.half.X + b.half.X && MathF.Abs(pa.Y - pb.Y) < a.half.Y + b.half.Y && MathF.Abs(pa.Z - pb.Z) < a.half.Z + b.half.Z)
                throw new InvalidOperationException($"{Q.EditorID}: zone {a.z.EditorID} (sets {a.stage}) overlaps {b.z.EditorID} (needs {b.prereq}): one step would set the next");
        }
        var bare = Q.Objectives.Where(o => o.Targets.Count == 0).Select(o => o.Index).ToList();
        if (bare.Count > 0) throw new InvalidOperationException($"{Q.EditorID}: objective(s) {string.Join(", ", bare)} have no compass target (quest_objective.target, TargetsFromRecord)");
    }

    /// The quest's header: Main Quest (the act's line) or Side Quest, and its flags.
    /// Every quest the kit sets up is Run Once (plus the flags the builder asks, Start Game Enabled).
    public void Header(string name, byte priority, Quest.TypeEnum type, Quest.Flag flags) { Q.Name = name; Q.Priority = priority; Q.Type = type; Q.Flags = flags | Quest.Flag.RunOnce; }
    /// E-stage: the stages with their log entries (a null entry is a hidden stage), the stage 0 start-up, the objectives, and
    /// a script fragment for each stage in `fragments` (default: every stage but 0).
    public void SetStages((int s, string? log, QuestLogEntry.Flag flag)[] stages, (ushort i, string text)[] objectives, string script, IEnumerable<int>? fragments = null)
    {
        foreach (var (s, log, flag) in stages)
            Q.Stages.Add(new QuestStage { Index = (ushort)s, Flags = s == 0 ? QuestStage.Flag.StartUpStage : 0, LogEntries = { new QuestLogEntry { Flags = flag, Entry = log } } });
        foreach (var (i, text) in objectives) Q.Objectives.Add(new QuestObjective { Index = i, DisplayText = text });
        Q.VirtualMachineAdapter ??= new QuestAdapter();
        Q.VirtualMachineAdapter.FileName = script;
        foreach (var s in fragments ?? stages.Where(x => x.s != 0).Select(x => x.s))
            Q.VirtualMachineAdapter.Fragments.Add(new QuestScriptFragment { Stage = (ushort)s, StageIndex = 0, ScriptName = script, FragmentName = $"Fragment_{s}" });
    }
    /// E-stage from the record's rows (story/data/db quest_stage, quest_objective): an empty start-up stage 0, a log entry per
    /// stage (`stages`, default every record stage) with the record's journal text, `hidden` stages without any, the completing
    /// stages flagged (`ends`, default the record's endings), and the objectives, each indexed by its stage id plus its
    /// order within the stage.
    public void FromRecord(string quest, string script, int[]? stages = null, int[]? hidden = null, int[]? ends = null, IEnumerable<int>? fragments = null)
    {
        var rec = Stages(quest).ToDictionary(s => s.id);
        var hid = hidden ?? [.. Hidden(quest)]; // the record's hidden stages unless the builder names others
        var failed = Failed(quest);
        var list = new List<(int, string?, QuestLogEntry.Flag)> { (0, null, 0) };
        foreach (var s in (stages ?? [.. rec.Keys]).Union(hid).OrderBy(s => s))
        {
            var ending = ends != null ? ends.Contains(s) : rec.TryGetValue(s, out var r) && r.ending;
            list.Add((s, hid.Contains(s) ? null : rec[s].journal, ending ? (failed.Contains(s) ? QuestLogEntry.Flag.FailQuest : QuestLogEntry.Flag.CompleteQuest) : 0));
        }
        var objectives = new List<(ushort, string)>();
        foreach (var g in Objectives(quest).GroupBy(o => o.stage))
        {
            ushort i = (ushort)g.Key;
            foreach (var o in g) objectives.Add((i++, o.text));
        }
        SetStages([.. list], [.. objectives], script, fragments);
    }
    /// The compass targets of the record's objectives (quest_objective.target, a comma list: either/or objectives point at each
    /// of them): `aliases` maps each target id of the data to the quest alias ids that stand for it. A target id with no alias
    /// fails the build; an empty column is the builder's own Target call.
    public void TargetsFromRecord(string quest, Dictionary<string, uint[]> aliases)
    {
        foreach (var g in Rows("quest_objective").Where(r => Str(r, "quest_id") == quest)
                     .OrderBy(r => r.GetProperty("stages_ord").GetInt32()).ThenBy(r => r.GetProperty("ord").GetInt32()).GroupBy(r => r.GetProperty("stages_ord").GetInt32()))
        {
            var stage = Stages(quest).Select(x => x.id).ToList();
            var byOrd = Rows("quest_stage").Where(r => Str(r, "quest_id") == quest).ToDictionary(r => r.GetProperty("ord").GetInt32(), r => int.Parse(r.GetProperty("id").ToString()));
            var i = byOrd[g.Key];
            foreach (var o in g)
            {
                foreach (var id in (Str(o, "target") ?? "").Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries))
                    Target(i, aliases.TryGetValue(id, out var a) ? a : throw new InvalidOperationException($"{Q.EditorID} objective {i}: the record's target {id} has no alias"));
                i++;
            }
        }
    }
    /// E-stage: the record's stages with their journal text, the completing ones flagged; an empty start-up stage 0.
    public void StagesFromRecord(string quest, string fragScript, IEnumerable<int> fragmentStages)
    {
        Q.Stages.Add(new QuestStage { Index = 0, Flags = QuestStage.Flag.StartUpStage, LogEntries = { new QuestLogEntry { Flags = 0 } } });
        var hid = Hidden(quest);
        foreach (var (id, journal, ending) in Stages(quest))
            Q.Stages.Add(new QuestStage { Index = (ushort)id, LogEntries = { new QuestLogEntry { Flags = ending ? QuestLogEntry.Flag.CompleteQuest : 0, Entry = hid.Contains(id) ? null : journal } } });
        Q.VirtualMachineAdapter ??= new QuestAdapter();
        Q.VirtualMachineAdapter.FileName = fragScript;
        foreach (var s in fragmentStages)
            Q.VirtualMachineAdapter.Fragments.Add(new QuestScriptFragment { Stage = (ushort)s, StageIndex = 0, ScriptName = fragScript, FragmentName = $"Fragment_{s}" });
    }
    /// Objective indices: the stage id plus the objective's order within the stage.
    public Dictionary<string, ushort> ObjectivesFromRecord(string quest)
    {
        var map = new Dictionary<string, ushort>();
        foreach (var g in Objectives(quest).GroupBy(o => o.stage))
        {
            ushort i = (ushort)g.Key;
            foreach (var o in g) { Q.Objectives.Add(new QuestObjective { Index = i, DisplayText = o.text }); map[o.id] = i++; }
        }
        return map;
    }

    // ---- dialogue
    /// One INFO: the lines, a TIF fragment (a gate that sets a stage runs TIF_<script>) with its properties, its conditions.
    DialogResponses Make(IEnumerable<string> lines, string? tif, ScriptProperty[] props, ConditionFloat[] conds, string? prompt)
    {
        var info = new DialogResponses(mod.GetNextFormKey(), SkyrimRelease.SkyrimSE) { Flags = new DialogResponseFlags() };
        if (prompt != null) info.Prompt = prompt;
        byte n = 1;
        foreach (var l in lines) info.Responses.Add(new DialogResponse { Text = l, ResponseNumber = n++, Emotion = Emotion.Neutral });
        if (info.Responses.Count == 0) info.Responses.Add(new DialogResponse { Text = "", ResponseNumber = 1, Emotion = Emotion.Neutral }); // dialogue owed
        info.Conditions.AddRange(conds);
        if (tif != null)
            info.VirtualMachineAdapter = new DialogResponsesAdapter
            {
                Scripts = { Script(tif, props) },
                ScriptFragments = new ScriptFragments { FileName = tif, OnEnd = new ScriptFragment { ScriptName = tif, FragmentName = "Fragment_0" } },
            };
        return info;
    }
    public DialogResponses Info(IEnumerable<string> lines, string? tif, params ConditionFloat[] conds) => Info(lines, tif, [], conds);
    public DialogResponses Info(IEnumerable<string> lines, string? tif, ScriptProperty[] props, params ConditionFloat[] conds) => Make(lines, tif, props, conds, null);
    /// What a gate says: its prompt (null: the topic's), its default lines, and each wording band's lines (null: not written).
    public sealed record Said(string? Prompt, List<string> Lines, Func<string, List<string>?> Band);
    /// One gate of a topic with its wording bands: the warm band on GetRelationshipRank with the player >= 1, the cool < 0, and
    /// the default with the complement, so they are exclusive by condition; each band INFO carries the same gates and the same
    /// fragment (no new script). Returned in topic order, the bands then the default; the INFO form ids are allocated in
    /// that order.
    public List<DialogResponses> Gate(Said said, string? tif, ScriptProperty[] props, ConditionFloat[] conds)
    {
        var present = Bands.Select(b => (b.band, b.op, b.v, text: said.Band(b.band))).Where(b => b.text != null).ToList();
        var rest = conds.ToList();
        foreach (var b in present) rest.Add(Rank(b.band == "high" ? CompareOperator.LessThan : CompareOperator.GreaterThanOrEqualTo, b.band == "high" ? 1 : 0));
        var infos = new List<DialogResponses>();
        foreach (var b in present)
            infos.Add(Make(b.text!, tif, [.. props.Select(p => (ScriptProperty)p.DeepCopy())], [.. conds.Select(c => c.DeepCopy()), Rank(b.op, b.v)], said.Prompt));
        infos.Add(Make(said.Lines, tif, props, [.. rest], said.Prompt));
        return infos;
    }
    /// A gate of the db rows (dialogue_line) with its wording bands, bands first.
    public DialogResponses[] Banded(string topic, string speaker, string gate, string? tif, ScriptProperty[] props, params ConditionFloat[] conds) =>
        [.. Gate(new Said(null, Lines(topic, speaker, gate), b => BandLines(topic, speaker, gate, b) is { Count: > 0 } l ? l : null), tif, props, conds)];
    public DialogResponses[] Banded(string topic, string speaker, string gate, string? tif, params ConditionFloat[] conds) => Banded(topic, speaker, gate, tif, [], conds);

    DialogTopic Open(string branchId, string topicId, string prompt, DialogBranch? under)
    {
        var branch = under ?? mod.DialogBranches.AddNew(branchId);
        var t = mod.DialogTopics.AddNew(topicId);
        if (under == null)
        {
            branch.Quest.SetTo(Q.FormKey); branch.Category = DialogBranch.CategoryType.Player; branch.Flags = DialogBranch.Flag.TopLevel;
            branch.StartingTopic.SetTo(t.FormKey);
        }
        t.Name = prompt; t.Quest.SetTo(Q.FormKey); t.Branch.SetTo(branch.FormKey); t.Priority = 50;
        t.Category = DialogTopic.CategoryEnum.Topic; t.Subtype = DialogTopic.SubtypeEnum.Custom; t.SubtypeName = new RecordType("CUST");
        return t;
    }
    /// TR-topic: a top-level player topic of the quest from INFOs built already (Banded), one INFO per gate.
    public DialogTopic Topic(string id, string prompt, params DialogResponses[] infos)
    {
        var t = Open(prefix + id + "Branch", prefix + id + "Topic", prompt, null);
        foreach (var i in infos) { i.Prompt ??= prompt; t.Responses.Add(i); }
        return t;
    }
    /// The INFOs with their own prompt (Skyrim's INFO prompt overrides the topic's), for one gate of a topic that is asked another way.
    public static DialogResponses[] Prompted(string prompt, params DialogResponses[] infos) { foreach (var i in infos) i.Prompt = prompt; return infos; }
    /// A topic of banded gates (Banded): each gate's band INFOs and its default.
    public DialogTopic Topic(string id, string prompt, params DialogResponses[][] gates) => Topic(id, prompt, [.. gates.SelectMany(g => g)]);

    /// One gate of a topic's lines from a source: its variant, its TIF fragment name ("{id}" and "{n}" stand for the topic's
    /// id and the gate's number; null: none) and the Papyrus body written for it (null: written by hand), its conditions.
    sealed record Gt(string? Variant, string? Tif, string? Body, ConditionFloat[] Conds);
    /// The INFO a gate wrote, for a builder that lists its lines (NightReedCheck, MainQuestCheck read them).
    public sealed record LineInfo(string Id, string Key, int N, string? Variant, string Prompt, string[] Text, string? Script, string? Body);
    public Action<LineInfo>? OnLine;
    /// The note a generated TIF fragment's header carries (the builder file that wrote it).
    public string TifNote = "";
    static readonly List<(string script, string body, string note)> tifs = [];
    /// Psc writing: every TIF fragment body any builder registered, one script each.
    public static void WritePsc(string dir)
    {
        Directory.CreateDirectory(dir);
        foreach (var (script, body, note) in tifs)
            File.WriteAllText(Path.Combine(dir, script + ".psc"),
                $"Scriptname {script} extends TopicInfo Hidden\n{{{note}}}\n\n;BEGIN FRAGMENT Fragment_0\nFunction Fragment_0(ObjectReference akSpeakerRef)\n\t{body}\nEndFunction\n;END FRAGMENT\n");
    }

    DialogTopic Build(string id, string key, string prompt, Gt[] gates, Func<int, Gt, Said> said, ConditionFloat[] speaker, DialogBranch? under)
    {
        var t = Open(id + "Branch", id, prompt, under);
        var n = 0;
        foreach (var g in gates)
        {
            var s = said(n, g);
            var tif = g.Tif?.Replace("{id}", id).Replace("{n}", n.ToString());
            if (tif != null && g.Body != null) tifs.Add((tif, g.Body, TifNote));
            t.Responses.AddRange(Gate(s with { Prompt = s.Prompt ?? prompt }, tif, [], [.. speaker.Select(c => c.DeepCopy()), .. g.Conds]));
            OnLine?.Invoke(new LineInfo(id, key, n, g.Variant, s.Prompt ?? prompt, [.. s.Lines], tif, g.Body));
            n++;
        }
        return t;
    }
    /// The topic's editor id from its record key: ARG_<code>_<Words>.
    public static string TopicId(string code, string topic) => $"ARG_{code}_" + string.Concat(topic.Split('-').Skip(1).Select(p => char.ToUpper(p[0]) + p[1..]));
    static List<string> Strs(JsonElement a) => [.. a.EnumerateArray().Select(l => l.GetString()!)];
    static Said JsonSaid(JsonElement t0, string? variant)
    {
        if (t0.TryGetProperty("infos", out var infos))
        {
            var v = infos.EnumerateArray().Single(x => x.GetProperty("variant").GetString() == variant);
            return new Said(v.GetProperty("prompt").GetString()!, Strs(v.GetProperty("lines")), b => v.TryGetProperty($"lines@{b}", out var bl) ? Strs(bl) : null);
        }
        var key = variant ?? "lines";
        return new Said(t0.GetProperty("prompt").GetString()!, Strs(t0.GetProperty(key)), b => t0.TryGetProperty($"{key}@{b}", out var bl) ? Strs(bl) : null);
    }
    static string JsonPrompt(JsonElement t0) => t0.TryGetProperty("infos", out var infos) ? infos[0].GetProperty("prompt").GetString()! : t0.GetProperty("prompt").GetString()!;
    /// TR-topic from a quest_lines record topic (MainQuest's): one top-level player topic, one gate per (variant, Papyrus body
    /// of its fragment TIF_<topic id>_<n>, conditions), each gated on the speaker. The topic joins `under`'s branch when given
    /// (a choice: offered only by an INFO's Link To, Skyrim's question-and-answer pairs). The topic and its branch are
    /// allocated first, then each gate's bands and then its default INFO.
    public DialogTopic Record(string code, JsonElement lines, string topic, DialogBranch? under, ConditionFloat[] speaker, params (string variant, string? body, ConditionFloat[] conds)[] infos)
    {
        var t0 = lines.GetProperty(topic);
        return Build(TopicId(code, topic), topic, JsonPrompt(t0), [.. infos.Select(i => new Gt(i.variant, i.body == null ? null : "TIF_{id}_{n}", i.body, i.conds))],
            (_, g) => JsonSaid(t0, g.Variant), speaker, under);
    }
    /// TR-topic from a quest_lines record topic (LocalQuests'): one top-level player topic, one gate per (stage it sets, conditions,
    /// variant), each gated on the speaker; a gate that sets a stage runs the hand-written TIF_ARG_<code>_<stage>. A variant
    /// speaks the topic's lines under that key (e.g. "fail") instead of "lines". Allocated topic first, a gate's bands first.
    public DialogTopic RecordV(string code, JsonElement lines, string topic, ConditionFloat speaker, params (int? sets, ConditionFloat[] conds, string? variant)[] infos)
    {
        var t0 = lines.GetProperty(topic);
        return Build(TopicId(code, topic), topic, JsonPrompt(t0), [.. infos.Select(i => new Gt(i.variant, i.sets is int s ? $"TIF_ARG_{code}_{s}" : null, null, i.conds))],
            (_, g) => JsonSaid(t0, g.Variant), [speaker], null);
    }
    /// TR-topic from a line store (NightReed's TSV): one top-level player topic, one gate per (intent, Papyrus body of its
    /// fragment TIF_<id>_<n>, conditions); the gate's written line is the store's "<id>_<n>", every gate must have one.
    public DialogTopic Store(string path, string id, string prompt, params (string text, string? body, ConditionFloat[] conds)[] infos) =>
        Store(path, id, prompt, id, 0, null, infos);
    /// The same for one route of a gated topic (Skyrim's way: a topic per way of asking, the route in the prompt): the gate's
    /// written line is the store's "<key>_<from + n>". A `fallback` (the conditions of the player who fails the route's check) adds
    /// an INFO speaking the store's "<key>_fallback" lines, what is needed in the speaker's words; none is built while the store
    /// has no such key (the key is listed in `MissingKeys`).
    public DialogTopic Store(string path, string id, string prompt, string key, int from, ConditionFloat[]? fallback, params (string text, string? body, ConditionFloat[] conds)[] infos)
    {
        var store = LineStores.TryGetValue(path, out var w) ? w : LineStores[path] = Written(path);
        var gates = infos.Select(i => new Gt(null, i.body == null ? null : "TIF_{id}_{n}", i.body, i.conds)).ToList();
        var fb = fallback != null && store.ContainsKey(key + "_fallback");
        if (fallback != null && !fb) MissingKeys.Add(key + "_fallback");
        if (fb) gates.Add(new Gt(null, null, null, fallback!));
        return Build(id, id, prompt, [.. gates],
            (n, _) => fb && n == infos.Length
                ? new Said(null, [store[key + "_fallback"]], b => StoreBand(store, key + "_fallback", b) is { Count: > 0 } l ? l : null)
                : new Said(null, [store.TryGetValue($"{key}_{from + n}", out var line) ? line : throw new InvalidDataException($"no written line {key}_{from + n} in {path}")],
                    b => StoreBand(store, $"{key}_{from + n}", b) is { Count: > 0 } l ? l : null), [], null);
    }
    /// The store keys a builder asked for and the writing lane has not written (each owed one INFO).
    public static readonly List<string> MissingKeys = [];
    static readonly Dictionary<string, Dictionary<string, string>> LineStores = [];
    /// A line heard without talking (Say from a stage fragment): a quest topic of the Misc category with one INFO, gated on the
    /// speaker, spoken by `Say(topic)` on the speaker's alias; its subtitle shows with General Subtitles on. The written line is
    /// the record's `topic` (quest_lines json, variant main).
    public DialogTopic Shout(string code, JsonElement lines, string topic, params ConditionFloat[] speaker)
    {
        var t0 = lines.GetProperty(topic);
        var t = mod.DialogTopics.AddNew(TopicId(code, topic));
        t.Quest.SetTo(Q.FormKey); t.Priority = 50;
        t.Category = DialogTopic.CategoryEnum.Misc; t.Subtype = DialogTopic.SubtypeEnum.Custom; t.SubtypeName = new RecordType("CUST");
        t.Responses.Add(Info(JsonSaid(t0, "main").Lines, null, speaker));
        return t;
    }
    /// An after-quest greeting: one Random INFO per written line, gated on the person's ref and on the quest's ending
    /// stages (any of them). The topic belongs to ARG_Talk, the dialogue quest that always runs: a stopped quest's own
    /// topics are never offered, and GetStage still reads a stopped quest's last stage.
    public void Hello(string id, params (FormKey who, List<string> said, int[] endings)[] people)
    {
        var talk = mod.Quests.FirstOrDefault(x => x.EditorID == "ARG_Talk") ?? throw new InvalidOperationException("Hello: ARG_Talk is not allocated yet");
        var t = mod.DialogTopics.AddNew(id);
        t.Quest.SetTo(talk.FormKey); t.Priority = 50;
        t.Category = DialogTopic.CategoryEnum.Misc; t.Subtype = DialogTopic.SubtypeEnum.Hello; t.SubtypeName = new RecordType("HELO");
        foreach (var (who, said, endings) in people)
        foreach (var l in said)
        {
            var info = new DialogResponses(mod.GetNextFormKey(), SkyrimRelease.SkyrimSE) { Flags = new DialogResponseFlags { Flags = DialogResponses.Flag.Random } };
            info.Responses.Add(new DialogResponse { Text = l, ResponseNumber = 1, Emotion = Emotion.Neutral });
            info.Conditions.Add(IsRef(who));
            for (var i = 0; i < endings.Length; i++)
            {
                var c = StageIs(Q, CompareOperator.EqualTo, endings[i]);
                if (i < endings.Length - 1) c.Flags = Condition.Flag.OR;
                info.Conditions.Add(c);
            }
            t.Responses.Add(info);
        }
    }

    /// The after-quest greetings a person's written file (story/data/dialogue-writer/quest/<code>/<who>.after.tsv) holds, each variant
    /// with the endings it is gated on: "after" on `plain` (the endings that leave the person in the state those lines describe),
    /// "after<N>" on stage N. A variant naming a stage the quest does not have is not returned (`skipped` says why).
    public static List<(List<string> said, int[] endings)> AfterSets(string code, string writer, int[] plain, IEnumerable<int> stages, List<string>? skipped = null)
    {
        var have = stages.ToHashSet();
        var sets = new List<(List<string>, int[])>();
        var variants = File.ReadLines(Path.Combine("story", "data", "dialogue-writer", "quest", code, writer + ".after.tsv")).Skip(1)
            .Select(l => l.Split('\t')).Where(p => p.Length >= 5).Select(p => p[1]).Distinct().ToList();
        foreach (var v in variants)
        {
            int[] endings = v == "after" ? plain : int.TryParse(v[5..], out var n) ? [n] : throw new InvalidDataException($"{code}/{writer}: variant {v}");
            var missing = endings.Where(e => !have.Contains(e)).ToList();
            if (endings.Length == 0 || missing.Count > 0) { skipped?.Add($"{code}/{writer} {v}: {(endings.Length == 0 ? "no plain endings given" : "the quest has no stage " + string.Join(",", missing))}"); continue; }
            sets.Add((After(code, writer, v), endings));
        }
        return sets;
    }
    /// The after-quest greetings of people (AfterSets): a Hello INFO set per variant, gated on the person's ref and its ending.
    public void AfterHellos(string id, string code, params (FormKey who, string writer, int[] plain)[] people)
    {
        var list = new List<(FormKey, List<string>, int[])>();
        var skipped = new List<string>();
        foreach (var (who, writer, plain) in people)
            foreach (var (said, endings) in AfterSets(code, writer, plain, Q.Stages.Select(x => (int)x.Index), skipped)) list.Add((who, said, endings));
        foreach (var sk in skipped) Console.WriteLine($"SKIP {Q.EditorID} after-quest {sk}");
        Hello(id, [.. list]);
    }

    // ---- cells: our override of an exterior cell's or interior cell's record, merged with one already in the mod
    public Cell Interior(FormKey cellKey) => Overrides.Interior(mod, mods, cellKey);
    public Cell Exterior(Worldspace world, FormKey cellKey) => Overrides.Exterior(mods, world, cellKey);
    /// The worldspace override in the mod (Generate's BlackMarsh, MapFix's others), with its persistent cell.
    public Worldspace World(FormKey wk) => Overrides.World(mod, mods, wk);
}
