using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Strings;
using Noggog;

// The proven block shapes of ARG_BlockTest (BlockTest.cs, docs/design/blocks.md) as helpers for the act's quests
// (MQ04.cs, MQ05.cs). Each helper builds exactly the record shape the block test proved; nothing new.
sealed class QuestKit(SkyrimMod mod, List<ISkyrimModGetter> mods, Quest q, string prefix)
{
    public static FormKey K(string k) => FormKey.Factory(k);
    public static FormLink<ISkyrimMajorRecordGetter> L(FormKey k) => new(k);
    public static readonly FormKey XMarker = K("00003B:Skyrim.esm"), PlayerRef = K("000014:Skyrim.esm"), Gold = K("00000F:Skyrim.esm"),
        TrigBase = K("099312:Skyrim.esm");
    public readonly Quest Q = q;
    public readonly Dictionary<FormKey, (IPlacedGetter rec, ModKey from)> Placed = Survey.Winners<IPlacedGetter>(mods);
    readonly Dictionary<FormKey, (INpcGetter rec, ModKey from)> npcs = Survey.Winners<INpcGetter>(mods);
    // The last navmesh of each id that carries its data (an override without data does not replace the geometry).
    readonly Dictionary<FormKey, (INavigationMeshGetter rec, ModKey from)> nav = mods.SelectMany(m => m.EnumerateMajorRecords<INavigationMeshGetter>()
        .Where(r => r.Data != null).Select(r => (r, m.ModKey))).GroupBy(e => e.r.FormKey).ToDictionary(g => g.Key, g => g.Last());
    readonly HashSet<(FormKey, int)> used = [];

    // ---- story data (story/data/db, the one source)
    static readonly string Db = Path.Combine("story", "data", "db");
    public static IEnumerable<JsonElement> Rows(string table) =>
        File.ReadLines(Path.Combine(Db, table + ".jsonl")).Where(l => l.Trim().Length > 0).Select(l => JsonDocument.Parse(l).RootElement);
    static string? Str(JsonElement e, string k) => e.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.String ? v.GetString() : null;
    /// The record's stages of a quest: id, journal text, completing; objectives by stage.
    public static List<(int id, string journal, bool ending)> Stages(string quest) =>
        Rows("quest_stage").Where(r => Str(r, "quest_id") == quest)
            .Select(r => (int.Parse(r.GetProperty("id").ToString()), Str(r, "journal_text") ?? "", Str(r, "ending") != null)).OrderBy(s => s.Item1).ToList();
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
    public static string Label(string topic) =>
        Rows("quest_topic").Where(r => Str(r, "id") == topic).Select(r => Str(r, "label")).FirstOrDefault() ?? throw new Exception($"no topic {topic}");

    // ---- conditions (C-stage, C-skill, C-item, C-time, C-global, GetIsID / GetIsReference as W-talk)
    public static ConditionFloat C(ConditionData d, CompareOperator op, float v, bool or = false) =>
        new() { CompareOperator = op, ComparisonValue = v, Data = d, Flags = or ? Condition.Flag.OR : 0 };
    public static T OnPlayer<T>(T d) where T : ConditionData { d.RunOnType = Condition.RunOnType.Reference; d.Reference.SetTo(PlayerRef); return d; }
    public ConditionFloat StageIs(int s, CompareOperator op = CompareOperator.EqualTo) { var d = new GetStageConditionData(); d.Quest.Link.SetTo(Q.FormKey); return C(d, op, s); }
    public static ConditionFloat Speech(float v) => C(OnPlayer(new GetActorValueConditionData { ActorValue = ActorValue.Speech }), CompareOperator.GreaterThanOrEqualTo, v);
    public static ConditionFloat Has(FormKey item, int n) { var d = new GetItemCountConditionData(); d.ItemOrList.Link.SetTo(item); OnPlayer(d); return C(d, CompareOperator.GreaterThanOrEqualTo, n); }
    public static ConditionFloat IsId(FormKey npc) { var d = new GetIsIDConditionData(); d.Object.Link.SetTo(npc); return C(d, CompareOperator.EqualTo, 1); }
    public static ConditionFloat IsRef(FormKey r) { var d = new GetIsReferenceConditionData(); d.Target.Link.SetTo(r); return C(d, CompareOperator.EqualTo, 1); }
    public static ConditionFloat Hour(CompareOperator op, float h, bool or = false) => C(new GetCurrentTimeConditionData(), op, h, or);

    // ---- scripts
    public static ScriptEntry Script(string name, params ScriptProperty[] ps) { var e = new ScriptEntry { Name = name }; e.Properties.AddRange(ps); return e; }
    public static ScriptObjectProperty Obj(string n, FormKey k) => new() { Name = n, Object = L(k) };
    public ScriptObjectProperty Alias(string n, uint id) => new() { Name = n, Object = L(Q.FormKey), Alias = (short)id };
    public static ScriptIntProperty Int(string n, int v) => new() { Name = n, Data = v };

    // ---- world edits
    /// W-npc / W-fixed: a base templated on a BM&V or vanilla base for looks and AI, our name, a fixed level (decision 0035).
    public Npc Base(string id, string name, string tpl, short level, NpcConfiguration.Flag extra = 0)
    {
        const NpcConfiguration.TemplateFlag looks = NpcConfiguration.TemplateFlag.Traits | NpcConfiguration.TemplateFlag.Factions
            | NpcConfiguration.TemplateFlag.SpellList | NpcConfiguration.TemplateFlag.AIData | NpcConfiguration.TemplateFlag.AIPackages
            | NpcConfiguration.TemplateFlag.ModelAnimation | NpcConfiguration.TemplateFlag.Inventory | NpcConfiguration.TemplateFlag.Script
            | NpcConfiguration.TemplateFlag.DefPackList | NpcConfiguration.TemplateFlag.AttackData | NpcConfiguration.TemplateFlag.Keywords;
        var t = npcs[K(tpl)].rec;
        var n = mod.Npcs.AddNew(id);
        n.Name = name;
        n.Template.SetTo(t.FormKey);
        n.Race.SetTo(t.Race.FormKey);
        n.Class.SetTo(t.Class.FormKey);
        n.Configuration.TemplateFlags = looks;
        n.Configuration.Level = new NpcLevel { Level = level };
        n.Configuration.Flags = NpcConfiguration.Flag.AutoCalcStats | (t.Configuration.Flags & NpcConfiguration.Flag.Female) | extra;
        return n;
    }
    /// The nearest unused triangle centre of a winning navmesh to a spot (BlockTest's Snapper).
    public P3Float Snap(FormKey mesh, float x, float y)
    {
        var d = nav[mesh].rec.Data!; var v = d.Vertices;
        var best = Enumerable.Range(0, d.Triangles.Count).Where(i => !used.Contains((mesh, i))).Select(i =>
        {
            var t = d.Triangles[i].Vertices; var a = v[t.X]; var b = v[t.Y]; var c = v[t.Z];
            return (i, p: new P3Float((a.X + b.X + c.X) / 3, (a.Y + b.Y + c.Y) / 3, (a.Z + b.Z + c.Z) / 3));
        }).MinBy(e => (e.p.X - x) * (e.p.X - x) + (e.p.Y - y) * (e.p.Y - y));
        used.Add((mesh, best.i));
        return new P3Float(MathF.Round(best.p.X), MathF.Round(best.p.Y), MathF.Round(best.p.Z));
    }
    /// The navmeshes of a cell (exterior or interior), from the load order's winners.
    public List<FormKey> Meshes(FormKey cell) => nav.Where(kv => kv.Value.rec.Data?.Parent is { } p
        && p.GetType().GetProperties().Any(pr => pr.GetValue(p) is IFormLinkGetter l && l.FormKey == cell)).Select(kv => kv.Key).ToList();
    public INavigationMeshGetter Mesh(FormKey k) => nav[k].rec;

    public PlacedObject Marker(string id, P3Float p, int flags = 0x400) => new(mod.GetNextFormKey(), SkyrimRelease.SkyrimSE)
    { EditorID = prefix + id, Base = new FormLinkNullable<IPlaceableObjectGetter>(XMarker), MajorRecordFlagsRaw = flags, Placement = new Placement { Position = p } };
    /// W-ref: a placed thing (static, furniture, item, door) of a base, persistent, optionally under an enable parent.
    public PlacedObject Ref(string id, FormKey baseKey, P3Float p, PlacedObject? parent = null, float? scale = null, P3Float? rot = null)
    {
        var r = new PlacedObject(mod.GetNextFormKey(), SkyrimRelease.SkyrimSE)
        { EditorID = prefix + id, MajorRecordFlagsRaw = 0x400, Placement = new Placement { Position = p, Rotation = rot ?? new P3Float() }, Scale = scale };
        r.Base.SetTo(baseKey);
        if (parent != null) { r.EnableParent = new EnableParent(); r.EnableParent.Reference.SetTo(parent.FormKey); }
        return r;
    }
    public PlacedNpc Actor(string id, Npc b, P3Float p, PlacedObject? parent = null, int flags = 0x400)
    {
        var r = new PlacedNpc(mod.GetNextFormKey(), SkyrimRelease.SkyrimSE)
        { EditorID = prefix + id, MajorRecordFlagsRaw = flags, Placement = new Placement { Position = p } };
        r.Base.SetTo(b.FormKey);
        if (parent != null) { r.EnableParent = new EnableParent(); r.EnableParent.Reference.SetTo(parent.FormKey); }
        return r;
    }
    /// TR-zone: the vanilla set-stage box (defaultSetStageTrigScript, a prerequisite stage), a 2*hx x 2*hy x 2*hz box.
    public PlacedObject Zone(string id, P3Float p, int prereq, int stage, float hx = 300, float hy = 300, float hz = 200)
    {
        var trig = mods[0].EnumerateMajorRecords<IPlacedObjectGetter>().First(r => r.Base.FormKey == TrigBase && r.Primitive != null);
        var z = new PlacedObject(mod.GetNextFormKey(), SkyrimRelease.SkyrimSE)
        {
            EditorID = prefix + id, MajorRecordFlagsRaw = 0x400, Placement = new Placement { Position = p },
            Primitive = trig.Primitive!.DeepCopy(),
            VirtualMachineAdapter = new VirtualMachineAdapter { Scripts = { Script("defaultSetStageTrigScript", Obj("myQuest", Q.FormKey), Int("prereqStageOPT", prereq), Int("stage", stage)) } },
        };
        z.Primitive.Bounds = new P3Float(hx, hy, hz);
        z.Base.SetTo(TrigBase);
        return z;
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

    // ---- quest records
    public QuestAlias Forced(uint id, string name, IPlacedGetter r, QuestAlias.Flag flags = 0)
    {
        var a = new QuestAlias { ID = id, Type = QuestAlias.TypeEnum.Reference, Name = name, Flags = flags };
        a.ForcedReference.SetTo(r.FormKey);
        Q.Aliases.Add(a);
        return a;
    }
    public QuestFragmentAlias AliasScript(uint id, ScriptEntry s) { var f = new QuestFragmentAlias { Property = Alias("", id) }; f.Scripts.Add(s); return f; }
    public static QuestFragmentAlias DeathSets(QuestKit k, uint id, int prereq, int stage) =>
        k.AliasScript(id, Script("defaultSetStageOnDeathRefAlias", Obj("myQST", k.Q.FormKey), Int("preReqStage", prereq), Int("StageToSet", stage)));
    public static QuestFragmentAlias AcquireSets(QuestKit k, uint id, int prereq, int stage) =>
        k.AliasScript(id, Script("defaultSetStageOnPlayerAcquire", Obj("myQST", k.Q.FormKey), Int("preReqStage", prereq), Int("StageToSet", stage)));
    /// E-package: the proven Travel package (a copy of vanilla DA06YamarzStage70PostForcegreet) to a marker, gated.
    public Package Travel(string id, PlacedObject to, params ConditionFloat[] conds)
    {
        var walk = mods[0].Packages.First(p => p.EditorID == "DA06YamarzStage70PostForcegreet").Duplicate(mod.GetNextFormKey());
        walk.EditorID = prefix + id;
        walk.OwnerQuest.SetTo(Q.FormKey);
        walk.Conditions.Clear();
        walk.Conditions.AddRange(conds);
        var loc = (PackageDataLocation)walk.Data[0];
        loc.Location = new LocationTargetRadius { Target = new LocationTarget(), Radius = 64 };
        ((LocationTarget)loc.Location.Target).Link.SetTo(to.FormKey);
        mod.Packages.Add(walk);
        return walk;
    }
    /// TR-topic: a top-level player topic of the quest, one INFO per gate; a gate that sets a stage runs TIF_<script>.
    public DialogTopic Topic(string id, string prompt, params DialogResponses[] infos)
    {
        var branch = mod.DialogBranches.AddNew(prefix + id + "Branch");
        var t = mod.DialogTopics.AddNew(prefix + id + "Topic");
        branch.Quest.SetTo(Q.FormKey); branch.Category = DialogBranch.CategoryType.Player; branch.Flags = DialogBranch.Flag.TopLevel;
        branch.StartingTopic.SetTo(t.FormKey);
        t.Name = prompt; t.Quest.SetTo(Q.FormKey); t.Branch.SetTo(branch.FormKey); t.Priority = 50;
        t.Category = DialogTopic.CategoryEnum.Topic; t.Subtype = DialogTopic.SubtypeEnum.Custom; t.SubtypeName = new RecordType("CUST");
        foreach (var i in infos) { i.Prompt = prompt; t.Responses.Add(i); }
        return t;
    }
    public DialogResponses Info(IEnumerable<string> lines, string? tif, params ConditionFloat[] conds) => Info(lines, tif, [], conds);
    public DialogResponses Info(IEnumerable<string> lines, string? tif, ScriptProperty[] props, params ConditionFloat[] conds)
    {
        var info = new DialogResponses(mod.GetNextFormKey(), SkyrimRelease.SkyrimSE) { Flags = new DialogResponseFlags() };
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
    /// E-stage: the record's stages with their journal text, the completing ones flagged; an empty start-up stage 0.
    public void StagesFromRecord(string quest, string fragScript, IEnumerable<int> fragmentStages)
    {
        Q.Stages.Add(new QuestStage { Index = 0, Flags = QuestStage.Flag.StartUpStage, LogEntries = { new QuestLogEntry { Flags = 0 } } });
        foreach (var (id, journal, ending) in Stages(quest))
            Q.Stages.Add(new QuestStage { Index = (ushort)id, LogEntries = { new QuestLogEntry { Flags = ending ? QuestLogEntry.Flag.CompleteQuest : 0, Entry = journal } } });
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

    // ---- cells: our override of an exterior cell's or interior cell's record, merged with one already in the mod
    static readonly Cell.TranslationMask NoRefs = new(true) { Persistent = false, Temporary = false, NavigationMeshes = false, Landscape = false };
    public Cell Interior(FormKey cellKey)
    {
        foreach (var b in mod.Cells.Records) foreach (var sb in b.SubBlocks) foreach (var c in sb.Cells) if (c.FormKey == cellKey) return c;
        var cell = Survey.Winners<ICellGetter>(mods)[cellKey].rec.DeepCopy(NoRefs);
        int id = (int)cellKey.ID, block = id % 10, sub = id / 10 % 10;
        var blk = mod.Cells.Records.FirstOrDefault(x => x.BlockNumber == block)
            ?? new CellBlock { BlockNumber = block, GroupType = GroupTypeEnum.InteriorCellBlock };
        if (!mod.Cells.Records.Contains(blk)) mod.Cells.Records.Add(blk);
        var sblk = blk.SubBlocks.FirstOrDefault(x => x.BlockNumber == sub)
            ?? new CellSubBlock { BlockNumber = sub, GroupType = GroupTypeEnum.InteriorCellSubBlock };
        if (!blk.SubBlocks.Contains(sblk)) blk.SubBlocks.Add(sblk);
        sblk.Cells.Add(cell);
        return cell;
    }
    public Cell Exterior(Worldspace world, FormKey cellKey)
    {
        foreach (var b in world.SubCells) foreach (var sb in b.Items) foreach (var c in sb.Items) if (c.FormKey == cellKey) return c;
        var cell = Survey.Winners<ICellGetter>(mods)[cellKey].rec.DeepCopy(NoRefs);
        var g = cell.Grid!.Point;
        short bx = (short)Math.Floor(g.X / 32.0), by = (short)Math.Floor(g.Y / 32.0), sx = (short)Math.Floor(g.X / 8.0), sy = (short)Math.Floor(g.Y / 8.0);
        var blk = world.SubCells.FirstOrDefault(x => x.BlockNumberX == bx && x.BlockNumberY == by)
            ?? new WorldspaceBlock { BlockNumberX = bx, BlockNumberY = by, GroupType = GroupTypeEnum.ExteriorCellBlock };
        if (!world.SubCells.Contains(blk)) world.SubCells.Add(blk);
        var sblk = blk.Items.FirstOrDefault(x => x.BlockNumberX == sx && x.BlockNumberY == sy)
            ?? new WorldspaceSubBlock { BlockNumberX = sx, BlockNumberY = sy, GroupType = GroupTypeEnum.ExteriorCellSubBlock };
        if (!blk.Items.Contains(sblk)) blk.Items.Add(sblk);
        sblk.Items.Add(cell);
        return cell;
    }
    /// The worldspace override in the mod (Generate's BlackMarsh, MapFix's others), with its persistent cell.
    public Worldspace World(FormKey wk)
    {
        var w = mod.Worldspaces.FirstOrDefault(x => x.FormKey == wk);
        if (w == null)
        {
            w = Survey.Winners<IWorldspaceGetter>(mods)[wk].rec.DeepCopy(new Worldspace.TranslationMask(true) { SubCells = false, TopCell = false });
            mod.Worldspaces.Add(w);
        }
        w.TopCell ??= Survey.Winners<IWorldspaceGetter>(mods)[wk].rec.TopCell!.DeepCopy(NoRefs);
        return w;
    }
    public static Faction Faction(SkyrimMod mod, string id, string name)
    {
        var f = mod.Factions.AddNew(id);
        f.Name = name;
        f.Ranks.Add(new Rank { Number = 0, Title = new GenderedItem<TranslatedString?>(new TranslatedString(Language.English, name), new TranslatedString(Language.English, name)) });
        return f;
    }
}
