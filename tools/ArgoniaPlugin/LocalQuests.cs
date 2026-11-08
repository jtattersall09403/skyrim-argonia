using System.Text.Json;
using Noggog;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;

// Phase 4's two local quests at Helstrom (story data quest.local.lq30, quest.local.lq25), built from Phase 3's proven
// blocks only (docs/design/blocks.md; each record's review finding B1 says what was re-authored). Both stand in BM&V's
// BlackMarsh2 (0D6960). Journal and objective text come from the story data rows; the dialogue from
// story/data/quest_lines/<code>.json (dialogue-write, text-review). Allocated after Combat in Generate, LQ30 then LQ25.
static class LocalQuests
{
    public static readonly FormKey BlackMarsh2 = FormKey.Factory("0D6960:Black Marsh.esm");
    static FormKey K(string k) => FormKey.Factory(k);
    static FormLink<ISkyrimMajorRecordGetter> L(FormKey k) => new(k);
    static readonly FormKey XMarker = K("00003B:Skyrim.esm"), PlayerRef = K("000014:Skyrim.esm"), Gold = K("00000F:Skyrim.esm"),
        Achievements = K("0FC85D:Skyrim.esm"), TrigBase = K("099312:Skyrim.esm");
    // The ref BM&V placed at Helstrom's gate (the levy warden; MQ05 cites him too).
    public static readonly FormKey Warden = K("08D5E9:Black Marsh North.esp");
    public static readonly FormKey Poler = K("08D5EE:Black Marsh North.esp"), Steerer = K("08D5EF:Black Marsh North.esp"), Captain = K("08D5F1:Black Marsh North.esp");
    public const uint L30Kin = 0, L30Youth = 1, L30Viper = 2, L30Warden = 3;
    public const uint L25Poler = 0, L25Steerer = 1, L25Captain = 2, L25Croc = 3;
    public static readonly List<ModKey> Masters = [];

    static readonly string Db = Path.Combine("story", "data", "db");
    static IEnumerable<JsonElement> Rows(string table) =>
        File.ReadLines(Path.Combine(Db, table + ".jsonl")).Where(l => l.Trim().Length > 0).Select(l => JsonDocument.Parse(l).RootElement);
    static string S(JsonElement e, string k) => e.GetProperty(k).GetString()!;
    public static Dictionary<int, string> Journal(string quest) =>
        Rows("quest_stage").Where(r => S(r, "quest_id") == quest).ToDictionary(r => r.GetProperty("id").GetInt32(), r => S(r, "journal_text"));
    // the objective of the stage at stages_ord, keyed by that stage's id
    public static Dictionary<int, string> Objectives(string quest)
    {
        var ids = Rows("quest_stage").Where(r => S(r, "quest_id") == quest).ToDictionary(r => r.GetProperty("ord").GetInt32(), r => r.GetProperty("id").GetInt32());
        return Rows("quest_objective").Where(r => S(r, "quest_id") == quest).ToDictionary(r => ids[r.GetProperty("stages_ord").GetInt32()], r => S(r, "objective_text"));
    }
    public static JsonElement Lines(string code) => JsonDocument.Parse(File.ReadAllText(Path.Combine("story", "data", "quest_lines", code + ".json"))).RootElement;

    // BlackMarsh2's override in our plugin: the load order's winner without its cells; persistent refs go in its top cell.
    internal static Worldspace World(SkyrimMod mod, List<ISkyrimModGetter> mods, FormKey? key = null)
    {
        // MapFix may already hold the override (its pan box), without a top cell
        var (win, from) = Survey.Winners<IWorldspaceGetter>(mods)[key ?? BlackMarsh2];
        var w = mod.Worldspaces.FirstOrDefault(x => x.FormKey == (key ?? BlackMarsh2));
        if (w == null)
        {
            w = win.DeepCopy(new Worldspace.TranslationMask(true) { SubCells = false, TopCell = false });
            mod.Worldspaces.Add(w);
        }
        w.TopCell ??= win.TopCell!.DeepCopy(new Cell.TranslationMask(true) { Persistent = false, Temporary = false, NavigationMeshes = false, Landscape = false });
        if (!Masters.Contains(from)) Masters.Add(from);
        return w;
    }

    // The nearest unused triangle centre of the navmeshes of the named cells (the placement method, blocks.md W-ref).
    internal sealed class Snapper(List<ISkyrimModGetter> mods)
    {
        readonly Dictionary<FormKey, (INavigationMeshGetter rec, ModKey from)> nav = Survey.Winners<INavigationMeshGetter>(mods);
        readonly HashSet<(FormKey, int)> used = [];
        public P3Float At(string cell, float x, float y)
        {
            // every plugin's copy of the cell: an override (Black Marsh North's) carries no navmesh group of its own
            var meshes = mods.SelectMany(m => m.EnumerateMajorRecords<ICellGetter>().Where(c => c.FormKey == K(cell)))
                .SelectMany(c => c.NavigationMeshes.Select(n => n.FormKey)).Distinct().Select(k => nav[k].rec).ToList();
            var best = meshes.SelectMany(m =>
            {
                var d = m.Data!; var v = d.Vertices;
                return Enumerable.Range(0, d.Triangles.Count).Where(i => !used.Contains((m.FormKey, i))).Select(i =>
                {
                    var t = d.Triangles[i].Vertices; var a = v[t.X]; var b = v[t.Y]; var c = v[t.Z];
                    return (m.FormKey, i, p: new P3Float((a.X + b.X + c.X) / 3, (a.Y + b.Y + c.Y) / 3, (a.Z + b.Z + c.Z) / 3));
                });
            }).MinBy(e => (e.p.X - x) * (e.p.X - x) + (e.p.Y - y) * (e.p.Y - y));
            used.Add((best.FormKey, best.i));
            return new P3Float(MathF.Round(best.p.X), MathF.Round(best.p.Y), MathF.Round(best.p.Z));
        }
    }

    const NpcConfiguration.TemplateFlag Looks = NpcConfiguration.TemplateFlag.Traits | NpcConfiguration.TemplateFlag.Factions
        | NpcConfiguration.TemplateFlag.SpellList | NpcConfiguration.TemplateFlag.AIData | NpcConfiguration.TemplateFlag.AIPackages
        | NpcConfiguration.TemplateFlag.ModelAnimation | NpcConfiguration.TemplateFlag.Inventory | NpcConfiguration.TemplateFlag.Script
        | NpcConfiguration.TemplateFlag.DefPackList | NpcConfiguration.TemplateFlag.AttackData | NpcConfiguration.TemplateFlag.Keywords;

    internal sealed class Kit(SkyrimMod mod, List<ISkyrimModGetter> mods, FormKey? world = null)
    {
        public readonly Dictionary<FormKey, (INpcGetter rec, ModKey from)> Npcs = Survey.Winners<INpcGetter>(mods);
        public readonly Dictionary<FormKey, (IPlacedGetter rec, ModKey from)> Placed = Survey.Winners<IPlacedGetter>(mods);
        public readonly Worldspace World = World(mod, mods, world);
        public readonly Snapper Snap = new(mods);

        // W-npc / W-fixed: our base templated on BM&V's for looks and AI; stats ours, a fixed level (decision 0035).
        public Npc Base(string id, string name, string tpl, short level, NpcConfiguration.Flag extra)
        {
            var t = Npcs[K(tpl)].rec;
            var n = mod.Npcs.AddNew(id);
            n.Name = name; n.Template.SetTo(t.FormKey); n.Race.SetTo(t.Race.FormKey); n.Class.SetTo(t.Class.FormKey);
            n.Configuration.TemplateFlags = Looks;
            n.Configuration.Level = new NpcLevel { Level = level };
            n.Configuration.Flags = NpcConfiguration.Flag.AutoCalcStats | (t.Configuration.Flags & NpcConfiguration.Flag.Female) | extra;
            return n;
        }
        public PlacedObject Marker(string id, P3Float p, int flags = 0x400) => new(mod.GetNextFormKey(), SkyrimRelease.SkyrimSE)
        { EditorID = id, Base = new FormLinkNullable<IPlaceableObjectGetter>(XMarker), MajorRecordFlagsRaw = flags, Placement = new Placement { Position = p } };
        public PlacedNpc Actor(string id, Npc b, P3Float p, PlacedObject? parent = null)
        {
            var r = new PlacedNpc(mod.GetNextFormKey(), SkyrimRelease.SkyrimSE) { EditorID = id, MajorRecordFlagsRaw = 0x400, Placement = new Placement { Position = p } };
            r.Base.SetTo(b.FormKey);
            if (parent != null) { r.EnableParent = new EnableParent(); r.EnableParent.Reference.SetTo(parent.FormKey); }
            return r;
        }
        // A BM&V ref an alias names: persistent (record flag 0x400), and, when a new base is given, placing it.
        public void Persist(FormKey key, Npc? newBase = null)
        {
            var existing = World.TopCell!.Persistent.OfType<PlacedNpc>().FirstOrDefault(r => r.FormKey == key);
            // talk's override (Talk.cs) may already hold it in its cell: take it from there, one record per form
            foreach (var b in World.SubCells) foreach (var sb in b.Items) foreach (var c in sb.Items)
                if (existing == null && c.Temporary.OfType<PlacedNpc>().FirstOrDefault(r => r.FormKey == key) is { } t) { c.Temporary.Remove(t); existing = t; }
            var src = (IPlacedNpcGetter)Placed[key].rec;
            if (existing == null && newBase == null && (src.MajorRecordFlagsRaw & 0x400) != 0) return;
            var r = existing ?? (PlacedNpc)src.DeepCopy();
            r.MajorRecordFlagsRaw |= 0x400;
            if (newBase != null) r.Base.SetTo(newBase.FormKey);
            if (existing == null) World.TopCell!.Persistent.Add(r);
        }
        public P3Float Pos(FormKey key) => Placed[key].rec.Placement!.Position;
        public PlacedObject Zone(string id, P3Float at, P3Float half, Quest q, int prereq, int stage)
        {
            var tpl = mods[0].EnumerateMajorRecords<IPlacedObjectGetter>().First(r => r.Base.FormKey == TrigBase && r.Primitive != null);
            var z = new PlacedObject(mod.GetNextFormKey(), SkyrimRelease.SkyrimSE)
            {
                EditorID = id, MajorRecordFlagsRaw = 0x400, Placement = new Placement { Position = at }, Primitive = tpl.Primitive!.DeepCopy(),
                VirtualMachineAdapter = new VirtualMachineAdapter { Scripts = { Script("defaultSetStageTrigScript", Obj("myQuest", q.FormKey), Int("prereqStageOPT", prereq), Int("stage", stage)) } },
            };
            z.Primitive.Bounds = half;
            z.Base.SetTo(TrigBase);
            return z;
        }
    }

    public static ScriptEntry Script(string name, params ScriptProperty[] ps) { var e = new ScriptEntry { Name = name }; e.Properties.AddRange(ps); return e; }
    internal static ScriptObjectProperty Obj(string n, FormKey k) => new() { Name = n, Object = L(k) };
    internal static ScriptObjectProperty Alias(string n, Quest q, uint id) => new() { Name = n, Object = L(q.FormKey), Alias = (short)id };
    internal static ScriptIntProperty Int(string n, int v) => new() { Name = n, Data = v };
    internal static ConditionFloat C(ConditionData d, CompareOperator op, float v) => new() { CompareOperator = op, ComparisonValue = v, Data = d };
    public static ConditionFloat StageIs(Quest q, CompareOperator op, int s) { var d = new GetStageConditionData(); d.Quest.Link.SetTo(q.FormKey); return C(d, op, s); }
    internal static ConditionFloat IsId(FormKey npc) { var d = new GetIsIDConditionData(); d.Object.Link.SetTo(npc); return C(d, CompareOperator.EqualTo, 1); }
    internal static ConditionFloat IsRef(FormKey r) { var d = new GetIsReferenceConditionData(); d.Target.Link.SetTo(r); return C(d, CompareOperator.EqualTo, 1); }

    // The quest: Side Quest, Start Game Enabled, empty start-up stage 0, a log entry per stage, completing stages flagged.
    internal static Quest NewQuest(SkyrimMod mod, string edid, string name, string id, int[] stages, int[] ends)
    {
        var q = mod.Quests.AddNew(edid);
        q.Name = name; q.Priority = 50; q.Type = Quest.TypeEnum.SideQuest; q.Flags = Quest.Flag.StartGameEnabled;
        var journal = Journal(id);
        q.Stages.Add(new QuestStage { Index = 0, Flags = QuestStage.Flag.StartUpStage, LogEntries = { new QuestLogEntry { Flags = 0 } } });
        foreach (var s in stages)
            q.Stages.Add(new QuestStage { Index = (ushort)s, LogEntries = { new QuestLogEntry { Flags = ends.Contains(s) ? QuestLogEntry.Flag.CompleteQuest : 0, Entry = journal[s] } } });
        foreach (var (s, text) in Objectives(id).OrderBy(e => e.Key))
            q.Objectives.Add(new QuestObjective { Index = (ushort)s, DisplayText = text });
        return q;
    }
    internal static QuestAlias Forced(Quest q, uint id, string name, FormKey r, QuestAlias.Flag flags = 0)
    {
        var a = new QuestAlias { ID = id, Type = QuestAlias.TypeEnum.Reference, Name = name, Flags = flags };
        a.ForcedReference.SetTo(r);
        q.Aliases.Add(a);
        return a;
    }
    internal static QuestFragmentAlias AliasScript(Quest q, uint id, ScriptEntry s) { var f = new QuestFragmentAlias { Property = Alias("", q, id) }; f.Scripts.Add(s); return f; }
    internal static ScriptEntry OnDeath(Quest q, int prereq, int set) => Script("defaultSetStageOnDeathRefAlias", Obj("myQST", q.FormKey), Int("preReqStage", prereq), Int("StageToSet", set));

    // TR-topic: one top-level player topic per record topic; one INFO per stage band, each gated on the speaker and stage.
    static void Topic(SkyrimMod mod, Quest q, string code, JsonElement lines, string topic, ConditionFloat speaker, params (int? sets, ConditionFloat[] conds)[] infos) =>
        TopicV(mod, q, code, lines, topic, speaker, infos.Select(i => (i.sets, i.conds, (string?)null)).ToArray());
    // As Topic; an info with a variant speaks the topic's lines under that key (e.g. "fail") instead of "lines".
    internal static void TopicV(SkyrimMod mod, Quest q, string code, JsonElement lines, string topic, ConditionFloat speaker, params (int? sets, ConditionFloat[] conds, string? variant)[] infos)
    {
        var t0 = lines.GetProperty(topic);
        var prompt = S(t0, "prompt");
        var id = $"ARG_{code}_" + string.Concat(topic.Split('-').Skip(1).Select(p => char.ToUpper(p[0]) + p[1..]));
        var branch = mod.DialogBranches.AddNew(id + "Branch");
        var t = mod.DialogTopics.AddNew(id);
        branch.Quest.SetTo(q.FormKey); branch.Category = DialogBranch.CategoryType.Player; branch.Flags = DialogBranch.Flag.TopLevel;
        branch.StartingTopic.SetTo(t.FormKey);
        t.Name = prompt; t.Quest.SetTo(q.FormKey); t.Branch.SetTo(branch.FormKey); t.Priority = 50;
        t.Category = DialogTopic.CategoryEnum.Topic; t.Subtype = DialogTopic.SubtypeEnum.Custom; t.SubtypeName = new RecordType("CUST");
        foreach (var (sets, conds, variant) in infos)
        {
            var info = new DialogResponses(mod.GetNextFormKey(), SkyrimRelease.SkyrimSE) { Flags = new DialogResponseFlags(), Prompt = prompt };
            byte n = 1;
            foreach (var l in t0.GetProperty(variant ?? "lines").EnumerateArray())
                info.Responses.Add(new DialogResponse { Text = l.GetString()!, ResponseNumber = n++, Emotion = Emotion.Neutral });
            info.Conditions.Add(speaker.DeepCopy());
            info.Conditions.AddRange(conds);
            if (sets is int s)
            {
                var name = $"TIF_ARG_{code}_{s}";
                info.VirtualMachineAdapter = new DialogResponsesAdapter
                {
                    Scripts = { Script(name) },
                    ScriptFragments = new ScriptFragments { FileName = name, OnEnd = new ScriptFragment { ScriptName = name, FragmentName = "Fragment_0" } },
                };
            }
            t.Responses.Add(info);
        }
    }
    internal static void Fragments(Quest q, string script, IEnumerable<int> stages)
    {
        foreach (var s in stages)
            q.VirtualMachineAdapter!.Fragments.Add(new QuestScriptFragment { Stage = (ushort)s, StageIndex = 0, ScriptName = script, FragmentName = $"Fragment_{s}" });
    }

    public static void Add(SkyrimMod mod, List<ISkyrimModGetter> mods)
    {
        var kit = new Kit(mod, mods);
        Lq30(mod, kit);
        Lq25(mod, mods, kit);
    }

    // LQ30 The Gates of Helstrom: Haj-Wan's topic (0 -> 30), the viper's death (30 -> 40), the gate zone (40 -> 91) or
    // Sei-Wan's topic (40 -> 92); Sei-Wan's death (30, 40 -> 93).
    static void Lq30(SkyrimMod mod, Kit kit)
    {
        const string id = "quest.local.lq30";
        var q = NewQuest(mod, "ARG_LQ30", "The Gates of Helstrom", id, [30, 40, 91, 92, 93], [91, 92, 93]);
        var kin = kit.Base("ARG_LQ30_HajWan", "Haj-Wan", "02A1EE:Black Marsh.esm", 5, NpcConfiguration.Flag.Protected | NpcConfiguration.Flag.Unique);
        var youth = kit.Base("ARG_LQ30_SeiWan", "Sei-Wan", "00FF4D:Black Marsh.esm", 3, NpcConfiguration.Flag.Protected | NpcConfiguration.Flag.Unique);
        var viper = kit.Base("ARG_LQ30_Viper", "Viper", "17BC83:Black Marsh.esm", 12, 0); // band 3, fixed

        var gate = kit.Pos(Warden);                                   // (-27858, 77815): BM&V's gate soldier
        var kinAt = kit.Snap.At("0D787F:Black Marsh.esm", gate.X + 150, gate.Y - 100);
        var markAt = kit.Snap.At("0D787F:Black Marsh.esm", gate.X - 600, gate.Y - 250); // inside the city, out of sight of the zone
        var youthAt = kit.Snap.At("0D7883:Black Marsh.esm", -18324, 77678); // the roots in the shallows, navmesh 1FAE4C
        var viperAt = kit.Snap.At("0D7883:Black Marsh.esm", -18093, 77568);
        var viperParent = kit.Marker("ARG_LQ30_ViperParent", new P3Float(viperAt.X, viperAt.Y, viperAt.Z - 200), 0xC00);
        var kinRef = kit.Actor("ARG_LQ30_HajWanRef", kin, kinAt);
        var youthRef = kit.Actor("ARG_LQ30_SeiWanRef", youth, youthAt, viperParent); // absent before 30 (quest review)
        var viperRef = kit.Actor("ARG_LQ30_ViperRef", viper, viperAt, viperParent);
        var mark = kit.Marker("ARG_LQ30_GateMarker", markAt);
        var zone = kit.Zone("ARG_LQ30_GateZone", new P3Float(gate.X, gate.Y, gate.Z + 100), new P3Float(400, 400, 300), q, 40, 91);
        kit.World.TopCell!.Persistent.AddRange([viperParent, kinRef, youthRef, viperRef, mark, zone]);
        kit.Persist(Warden);

        Forced(q, L30Kin, "Kin", kinRef.FormKey);
        Forced(q, L30Youth, "Youth", youthRef.FormKey, QuestAlias.Flag.Protected);
        Forced(q, L30Viper, "Viper", viperRef.FormKey, QuestAlias.Flag.AllowDisabled);
        Forced(q, L30Warden, "Warden", Warden);
        q.VirtualMachineAdapter = new QuestAdapter
        {
            FileName = "ARG_QF_LQ30",
            Scripts = { Script("ARG_QF_LQ30", Alias("Kin", q, L30Kin), Alias("Youth", q, L30Youth), Obj("ViperParent", viperParent.FormKey),
                Obj("GateMarker", mark.FormKey), Obj("GateZone", zone.FormKey), Obj("Gold001", Gold), Obj("AchievementsQuest", Achievements)) },
            Aliases = { AliasScript(q, L30Viper, OnDeath(q, 30, 40)), AliasScript(q, L30Youth, OnDeath(q, 30, 93)) },
        };
        Fragments(q, "ARG_QF_LQ30", [30, 40, 91, 92, 93]);

        var lines = Lines("lq30");
        Topic(mod, q, "LQ30", lines, "topic.lq30-walked-out", IsId(kin.FormKey),
            (30, [StageIs(q, CompareOperator.EqualTo, 0)]), (null, [StageIs(q, CompareOperator.EqualTo, 30)]));
        Topic(mod, q, "LQ30", lines, "topic.lq30-the-basin", IsRef(Warden), (null, [StageIs(q, CompareOperator.EqualTo, 30)]));
        Topic(mod, q, "LQ30", lines, "topic.lq30-come-back", IsId(youth.FormKey), (92, [StageIs(q, CompareOperator.EqualTo, 40)]));
    }

    // LQ25 The River Monster: Okan-Zish's topic once MQ05 is at 40 (0 -> 20), the crocodile's death (20 -> 40), the
    // captain's topic with the bucket (40 -> 91) or Wuleen-Taza's (40 -> 92); the captain's death (40 -> 93).
    static void Lq25(SkyrimMod mod, List<ISkyrimModGetter> mods, Kit kit)
    {
        const string id = "quest.local.lq25";
        var q = NewQuest(mod, "ARG_LQ25", "The River Monster", id, [20, 40, 91, 92, 93], [91, 92, 93]);
        var poler = kit.Base("ARG_LQ25_OkanZish", "Okan-Zish", "00FF4D:Black Marsh.esm", 5, NpcConfiguration.Flag.Protected | NpcConfiguration.Flag.Unique);
        var steerer = kit.Base("ARG_LQ25_WuleenTaza", "Wuleen-Taza", "02A1EE:Black Marsh.esm", 5, NpcConfiguration.Flag.Protected | NpcConfiguration.Flag.Unique);
        var croc = kit.Base("ARG_LQ25_Crocodile", "Crocodile", "0BCB00:Black Marsh.esm", 4, 0); // band 1, fixed
        var bucket = mod.MiscItems.AddNew("ARG_LQ25_BaitBucket");
        bucket.Name = "Bait Bucket"; bucket.Value = 0; bucket.Weight = 2;
        bucket.Model = new Model { File = mods[0].MiscItems.First(m => m.FormKey == K("012FDF:Skyrim.esm")).Model!.File.DataRelativePath.Path }; // Bucket01

        // The lair: the shallows under the crew's plank walk (BM&V's 05A835 planks), navmesh 1FAEB6 in 0D77AF.
        var crocAt = kit.Snap.At("0D77AF:Black Marsh.esm", -36450, 64100);
        var bucketNav = kit.Snap.At("0D77AF:Black Marsh.esm", -36600, 64150);
        var bucketAt = new P3Float(bucketNav.X, bucketNav.Y, bucketNav.Z + 30);
        var crocParent = kit.Marker("ARG_LQ25_CrocParent", new P3Float(crocAt.X, crocAt.Y, crocAt.Z - 200), 0xC00);
        var crocRef = kit.Actor("ARG_LQ25_CrocodileRef", croc, crocAt, crocParent);
        var bucketRef = kit.Marker("ARG_LQ25_BaitBucketRef", bucketAt);
        bucketRef.Base.SetTo(bucket.FormKey);
        bucketRef.EnableParent = new EnableParent(); bucketRef.EnableParent.Reference.SetTo(crocParent.FormKey);
        kit.World.TopCell!.Persistent.AddRange([crocParent, crocRef, bucketRef]);
        kit.Persist(Poler, poler); kit.Persist(Steerer, steerer); kit.Persist(Captain);

        Forced(q, L25Poler, "Poler", Poler);
        Forced(q, L25Steerer, "Steerer", Steerer);
        Forced(q, L25Captain, "Captain", Captain);
        Forced(q, L25Croc, "Crocodile", crocRef.FormKey, QuestAlias.Flag.AllowDisabled);
        q.VirtualMachineAdapter = new QuestAdapter
        {
            FileName = "ARG_QF_LQ25",
            Scripts = { Script("ARG_QF_LQ25", Alias("Steerer", q, L25Steerer), Alias("Captain", q, L25Captain), Obj("CrocParent", crocParent.FormKey),
                Obj("BaitBucket", bucket.FormKey), Obj("Gold001", Gold), Obj("AchievementsQuest", Achievements)) },
            Aliases = { AliasScript(q, L25Croc, OnDeath(q, 20, 40)), AliasScript(q, L25Captain, OnDeath(q, 40, 93)) },
        };
        Fragments(q, "ARG_QF_LQ25", [20, 40, 91, 92, 93]);

        // C-stage on MQ05 (ARG_MQ05, the MQ05 lane's quest): gated when it is built in this plugin.
        var mq05 = mod.Quests.FirstOrDefault(x => x.EditorID == "ARG_MQ05");
        if (mq05 == null) Console.WriteLine("LQ25: ARG_MQ05 not in the plugin; the opening topic's MQ05 >= 40 gate is left out until it is");
        ConditionFloat[] open = mq05 == null ? [StageIs(q, CompareOperator.EqualTo, 0)] : [StageIs(q, CompareOperator.EqualTo, 0), StageIs(mq05, CompareOperator.GreaterThanOrEqualTo, 40)];
        var hasBucket = new GetItemCountConditionData { RunOnType = Condition.RunOnType.Reference }; hasBucket.Reference.SetTo(PlayerRef); hasBucket.ItemOrList.Link.SetTo(bucket.FormKey);
        var lines = Lines("lq25");
        Topic(mod, q, "LQ25", lines, "topic.lq25-the-beast", IsId(poler.FormKey), (20, open), (null, [StageIs(q, CompareOperator.EqualTo, 20)]));
        Topic(mod, q, "LQ25", lines, "topic.lq25-tell-captain", IsRef(Captain), (91, [StageIs(q, CompareOperator.EqualTo, 40), C(hasBucket, CompareOperator.GreaterThanOrEqualTo, 1)]));
        Topic(mod, q, "LQ25", lines, "topic.lq25-keep-quiet", IsId(steerer.FormKey), (92, [StageIs(q, CompareOperator.EqualTo, 40)]));
    }
}
