using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Noggog;

// QuestForm: the one generic builder. Every quest form (tools/questform/schema.json; docs/design/quest-form.md, "How a
// form becomes records") becomes the same shape of records, and no quest has code of its own:
//   the quest       QUST, Run Once, Main Quest (kind main) or Side Quest, Start Game Enabled when it runs from a new game;
//                   one log entry per stage (text when shown; Complete or Fail Quest on an ending); its objectives
//   the people and things  one forced-reference alias per ref (the alias's name is the ref id); an existing ref made
//                   persistent; a new one placed from its anchor (Snap on the navmesh, or the Surface under it),
//                   persistent; a person on a base of ours templated on the form's base (hostile: aggressive and brave);
//                   a thing in a container, or in a person's pocket, by a create-in alias; a lock (XLOC) and an owner (XOWN) on
//                   a door or a thing placed or overridden; a new container's contents, its own copy of the base with those items
//                   and no respawn
//   the stage rows  ARG_QuestStages on the quest: every stage's work as rows of three arrays (Op, What, Num) that
//                   ARG_Effects carries out; one fragment per stage that has rows
//   the lines       topics and responses; ARG_LineEffects on every response with the line's rows; the speaks-first
//                   person's one force-greet package (template ForceGreet) and the same line under their greeting
//   the triggers    vanilla's default alias scripts (take, use, read, death); another quest's stage as rows in that quest
//   who must live   a failed ending on their death (vanilla's death script; for a main or faction quest the mortal
//                   watch, ARG_MortalWatch, with the message box), and the start's check that they are alive
// Form ids come from plugin/questform-formids.json (FormIds), named by the quest id and the ref or line id, so adding a
// quest never moves another's. Anything the builder cannot build exactly fails the build with one line naming the quest
// and the rule (Refused); it never approximates. `questform --selftest` proves each refusal on hand-made forms.
static class QuestForm
{
    public sealed class Refused(string quest, string rule, string what) : Exception($"questform {quest}: {rule}: {what}")
    {
        public readonly string Rule = rule, Quest = quest;
    }

    // ---- the operations of ARG_Effects (papyrus/ARG_Effects.psc; the numbers are the script's)
    public static class Op
    {
        public const int SetStage = 1, ShowObjective = 2, CompleteObjective = 3, FailObjective = 4, SetActive = 5, StopQuest = 6,
            IncSideQuests = 7, FailIfDead = 8, SetStageIfRunning = 9, IfStageDone = 10, IfQuestOpen = 11, StartOnStage = 12, IfStageAtMost = 13, IfHolds = 14,
            CompleteAll = 15, FailAll = 16,
            GiveItem = 20, TakeItem = 21, GiveGold = 22, TakeGold = 23, SetNumber = 24, AddNumber = 25, JoinFaction = 26,
            SetRank = 27, ChangeRegard = 28, SwitchOn = 29, SwitchOff = 30, LockDoor = 31, UnlockDoor = 32, ShowMessage = 33,
            SpeakerHostile = 34, StartQuest = 35, GiveOwnership = 36;
        public static readonly Dictionary<string, int> OfResult = new()
        {
            ["set_stage"] = SetStage, ["give_item"] = GiveItem, ["take_item"] = TakeItem, ["give_gold"] = GiveGold, ["take_gold"] = TakeGold,
            ["set_number"] = SetNumber, ["add_number"] = AddNumber, ["join_faction"] = JoinFaction, ["set_rank"] = SetRank,
            ["change_regard"] = ChangeRegard, ["switch_on"] = SwitchOn, ["switch_off"] = SwitchOff, ["lock_door"] = LockDoor,
            ["unlock_door"] = UnlockDoor, ["show_message"] = ShowMessage, ["speaker_hostile"] = SpeakerHostile, ["start_quest"] = StartQuest,
            ["give_ownership"] = GiveOwnership,
        };
    }
    public sealed record Row(int Op, FormKey What, float Num);
    public const int MaxRows = 128;
    public const int DoorStand = 150;    // a person placed by a load door stands within this many units of where the player comes out
    public const int GreetReach = 500;   // a speaks-first person greets a player within this many units   // a Papyrus array made by `new` holds 128; no vanilla property array exceeds 35

    public static readonly FormKey XMarker = FormKey.Factory("00003B:Skyrim.esm"), Player = FormKey.Factory("000014:Skyrim.esm"),
        Gold = FormKey.Factory("00000F:Skyrim.esm"), Achievements = FormKey.Factory("0FC85D:Skyrim.esm"),
        ForceGreetTemplate = FormKey.Factory("03C1C4:Skyrim.esm"), ForceGreetCopy = FormKey.Factory("01703F:Skyrim.esm"); // MS05InductionForcegreet
    public const string StagesScript = "ARG_QuestStages", LineScript = "ARG_LineEffects", AliasScript = "ARG_AliasEffects";
    public static readonly string FormIdsPath = Environment.GetEnvironmentVariable("QUESTFORM_IDS") ?? "plugin/questform-formids.json";
    public const string Kind = "questform";
    public const string WatchId = "ARG_MortalWatch";
    public const string MainMessage = "With this death the root of what was to come is cut: the main story can no longer be finished. Load an earlier save to let it grow again, or go on in the marsh as it now is.";
    public const string FactionMessage = "With this death the root of what was to come is cut: this faction's story can no longer be finished. Load an earlier save to let it grow again, or go on in the marsh as it now is.";
    // The vanilla scripts a trigger or a who-must-live row puts on an alias (docs/research/skyrim/quest-form-engine-facts.md §5e).
    public const string TakeRefScript = "defaultSetStageOnPlayerAcquireItem";
    public const string TakeScript = "defaultSetStageOnPlayerAcquire", UseScript = "defaultSetStageAliasScript",
        ReadScript = "defaultSetStageOnCloseBook", DeathScript = "defaultSetStageOnDeathRefAlias";
    // ARG_AliasEffects's On: the event its rows run on (its death when left out); a take, use or read with an `until`
    public const int AliasOnTake = 1, AliasOnActivate = 2, AliasOnRead = 3;

    // ---- the forms
    /// Every quest form (*.json) of the directories, by file name; a directory not there holds none.
    public static List<(string path, JsonElement form)> Load(IEnumerable<string> dirs) =>
        [.. dirs.Where(Directory.Exists).SelectMany(d => Directory.GetFiles(d, "*.json")).OrderBy(Path.GetFileName, StringComparer.Ordinal)
            .Select(p => (p, JsonDocument.Parse(File.ReadAllText(p)).RootElement))];
    /// The directories the seed reads: QUESTFORM_DIRS (colon-separated), else the compiled forms and the block test's.
    public static string[] Dirs() => (Environment.GetEnvironmentVariable("QUESTFORM_DIRS") ?? "out/questform:tools/questform/blocktest")
        .Split(':', StringSplitOptions.RemoveEmptyEntries);
    public static string QuestIdOf(JsonElement f) => f.GetProperty("quest").GetProperty("id").GetString()!;

    static string S(JsonElement e, string k) => e.GetProperty(k).GetString()!;
    static string? So(JsonElement e, string k) => e.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.String ? v.GetString() : null;
    static int I(JsonElement e, string k) => e.GetProperty(k).GetInt32();
    static bool B(JsonElement e, string k) => e.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.True;
    static IEnumerable<JsonElement> A(JsonElement e, string k) => e.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.Array ? v.EnumerateArray() : [];
    public static string Slug(string id) => new([.. id.Select(c => char.IsAsciiLetterOrDigit(c) ? c : '_')]);
    public static string Sha(string s) => Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(s)))[..12].ToLowerInvariant();

    // ---- what a ref became
    sealed class Ref
    {
        public string Id = "", Kind = ""; public uint Alias; public JsonElement Json;
        public FormKey Placed;              // the placed reference (null for a thing created in a container)
        public FormKey Base;                // its base (the item for a thing in a container)
        public bool Created, Enabled, Hostile, Npc, Fresh;
        public bool Standing;               // a person at the form's exact spot where there is no navmesh (they will not walk)
        public (FormKey door, P3Float arrival)? Door;   // the load door it stands by: where the player comes out of it
        public QuestAlias A = null!;
    }
    sealed class Built
    {
        public string Qid = "", Edid = "", Kind = ""; public JsonElement F; public Quest Q = null!;
        public Dictionary<string, Ref> Refs = [];
        public SortedDictionary<int, List<Row>> Own = [];          // a stage's own rows (the start check, results, objectives)
        public SortedDictionary<int, List<Row>> From = [];         // rows other forms add to a stage (their starts and triggers)
        public SortedDictionary<int, List<Row>> Tail = [];         // an ending's closing rows (every objective closed, the count)
        public List<string> Labels = [];
        public Dictionary<uint, List<ScriptEntry>> AliasScripts = [];
        public HashSet<int> Endings = [];
        public int Start;
    }

    // ---- the build
    sealed class Ctx(SkyrimMod mod, List<ISkyrimModGetter> mods, FormIds ids)
    {
        public readonly SkyrimMod Mod = mod; public readonly List<ISkyrimModGetter> Mods = mods; public readonly FormIds Ids = ids;
        public readonly Dictionary<string, Built> Quests = new(StringComparer.Ordinal);
        public Dictionary<FormKey, (IPlacedGetter rec, ModKey from)> Placed = [];
        public Dictionary<FormKey, (INpcGetter rec, ModKey from)> Npcs = [];
        public Dictionary<FormKey, Where> Wheres = [];
        public Dictionary<(FormKey world, int x, int y), FormKey> Grid = [];
        public Dictionary<FormKey, FormKey> CellWorld = [];
        public Dictionary<FormKey, P3Float> Arrivals = [];
        public Dictionary<FormKey, INavigationMeshGetter> NavWin = [];
        public Dictionary<FormKey, (ICellGetter rec, ModKey from)>? CellWin;
        public Dictionary<FormKey, (string Quest, string Name)> CellNames = [];   // an interior's name, by the first form to name it
        public List<P3Float> Stood = [];   // where the people placed on navmesh stand, so no two share a spot
        public Dictionary<string, (string Quest, string Same, FormKey Placed, FormKey Base, bool Npc, bool Created)> Shared = [];   // a load door: where the player comes out of it
        public FormKey Key(string name) => new(Mod.ModKey, Ids.Take(Kind, name));
        public string Q = ""; public Built? Cur;
        public Refused No(string rule, string what) => new(Q, rule, what);
    }
    public sealed record Where(FormKey Cell, FormKey World, bool Interior, P3Float Pos);

    /// Builds every form into the mod. The forms are first all allocated (so one may start or watch another), then built.
    public static List<string> Build(SkyrimMod mod, List<ISkyrimModGetter> mods, IList<(string path, JsonElement form)> forms, FormIds ids)
    {
        var c = new Ctx(mod, mods, ids);
        if (forms.Count == 0) return [];
        c.Placed = Survey.Winners<IPlacedGetter>(mods);
        c.Npcs = Survey.Winners<INpcGetter>(mods);
        Index(c);
        foreach (var (path, f) in forms)
        {
            var b = new Built { F = f, Qid = QuestIdOf(f), Edid = S(f.GetProperty("quest"), "editor_id"), Kind = S(f.GetProperty("quest"), "kind") };
            c.Q = b.Qid; c.Cur = b;
            if (c.Quests.ContainsKey(b.Qid)) throw c.No("unique", $"two forms of the quest ({path})");
            if (mod.Quests.Any(q => q.EditorID == b.Edid)) throw c.No("editor-id", $"{b.Edid} is already a quest of the plugin");
            b.Q = new Quest(c.Key("quest:" + b.Qid), SkyrimRelease.SkyrimSE) { EditorID = b.Edid };
            mod.Quests.Add(b.Q);
            c.Quests[b.Qid] = b;
        }
        foreach (var b in c.Quests.Values) { c.Q = b.Qid; c.Cur = b; Quest(c, b); }
        foreach (var b in c.Quests.Values) { c.Q = b.Qid; c.Cur = b; Lines(c, b); }
        foreach (var b in c.Quests.Values) { c.Q = b.Qid; c.Cur = b; Triggers(c, b); }
        Watch(c);
        foreach (var b in c.Quests.Values) { c.Q = b.Qid; c.Cur = b; Places(c, b); }
        foreach (var b in c.Quests.Values) { c.Q = b.Qid; c.Cur = b; Finish(c, b); }
        Starts.Clear();
        foreach (var b in c.Quests.Values) { c.Q = b.Qid; c.Cur = b; Starts[b.Edid] = Window(c, b); }
        return [.. c.Quests.Keys];
    }

    static readonly Dictionary<string, List<ConditionFloat>> Starts = new(StringComparer.Ordinal);
    /// The conditions that hold while a form-built quest (by editor id) can start, for talk that points at it (a rumour);
    /// null for a quest not built from a form.
    public static List<ConditionFloat>? StartWindow(string edid) => Starts.TryGetValue(edid, out var l) ? [.. l.Select(x => (ConditionFloat)x.DeepCopy())] : null;
    // The start window: the quest's stage not past its start (at it, for a quest running from a new game); the stage of the
    // quest that starts it done; and every other quest's stage that each opening line (open at the start, moving the stage)
    // asks for, when every such line asks it and no take or use trigger opens it instead.
    static List<ConditionFloat> Window(Ctx c, Built b)
    {
        var start = b.F.GetProperty("quest").GetProperty("start");
        var l = new List<ConditionFloat>();
        if (S(start, "by") == "game") l.Add(Cond(StageData(b.Q.FormKey), CompareOperator.EqualTo, b.Start));
        else
        {
            l.Add(Cond(StageData(b.Q.FormKey), CompareOperator.LessThanOrEqualTo, b.Start));
            if (S(start, "by") == "quest_stage") l.Add(Cond(Done(QuestKey(c, S(start, "quest")), I(start, "quest_stage")), CompareOperator.EqualTo, 1));
        }
        var opening = A(b.F, "lines").Where(x => I(x, "first_stage") <= b.Start && b.Start <= I(x, "last_stage") && A(x, "results").Any(r => S(r, "do") == "set_stage")).ToList();
        if (opening.Count == 0 || A(b.F, "triggers").Any(t => S(t, "kind") is "take" or "use" && I(t, "prerequisite") == b.Start)) return l;
        string[] stageWords = ["stage_is", "stage_at_least", "stage_done"];
        IEnumerable<string> Gates(JsonElement x) => A(x, "conditions").Where(cd => stageWords.Contains(S(cd, "is")) && S(cd, "quest") != b.Qid).Select(cd => cd.GetRawText());
        foreach (var raw in opening.Skip(1).Aggregate(Gates(opening[0]).ToHashSet(), (acc, x) => { acc.IntersectWith(Gates(x)); return acc; }).OrderBy(x => x, StringComparer.Ordinal))
            l.Add(Condition(c, b, JsonDocument.Parse(raw).RootElement));
        return l;
    }

    // Where every placed ref of the load order stands (cell, world, interior, position), and each world's grid of cells.
    static void Index(Ctx c)
    {
        foreach (var m in c.Mods.Append(c.Mod))
        {
            foreach (var w in m.Worldspaces)
            {
                foreach (var r in w.TopCell?.Persistent ?? [])
                    if (Arrive(c, r) && Pos(r) is { } p) c.Wheres[r.FormKey] = new Where(FormKey.Null, w.FormKey, false, p);
                foreach (var cell in w.SubCells.SelectMany(b => b.Items).SelectMany(s => s.Items))
                {
                    if (cell.Grid != null) { c.Grid[(w.FormKey, cell.Grid.Point.X, cell.Grid.Point.Y)] = cell.FormKey; c.CellWorld[cell.FormKey] = w.FormKey; }
                    foreach (var r in cell.Persistent.Concat(cell.Temporary))
                        if (Arrive(c, r) && Pos(r) is { } p) c.Wheres[r.FormKey] = new Where(cell.FormKey, w.FormKey, false, p);
                }
            }
            foreach (var cell in m.Cells.Records.SelectMany(b => b.SubBlocks).SelectMany(s => s.Cells))
                foreach (var r in cell.Persistent.Concat(cell.Temporary))
                    if (Arrive(c, r) && Pos(r) is { } p) c.Wheres[r.FormKey] = new Where(cell.FormKey, FormKey.Null, true, p);
        }
        foreach (var (k, w) in c.Wheres.ToList())
            if (!w.Interior && w.Cell.IsNull) c.Wheres[k] = w with { Cell = CellAt(c, w.World, w.Pos) };
    }
    static bool Arrival(Ctx c, string key)
    {
        try { return c.Arrivals.ContainsKey(FormKey.Factory(key)); } catch (Exception) { return false; }
    }
    static bool Arrive(Ctx c, IMajorRecordGetter r)
    {
        if (r is IPlacedObjectGetter o && o.TeleportDestination is { } t && !t.Door.IsNull) c.Arrivals[t.Door.FormKey] = t.Position;
        return true;
    }
    static P3Float? Pos(IMajorRecordGetter r) => r switch { IPlacedObjectGetter o => o.Placement?.Position, IPlacedNpcGetter n => n.Placement?.Position, _ => null };
    static FormKey CellAt(Ctx c, FormKey world, P3Float p) =>
        c.Grid.TryGetValue((world, (int)MathF.Floor(p.X / 4096), (int)MathF.Floor(p.Y / 4096)), out var k) ? k : FormKey.Null;

    // ---- the quest, its stages, objectives, refs and results
    static void Quest(Ctx c, Built b)
    {
        var f = b.F; var q = b.Q; var head = f.GetProperty("quest");
        q.Name = S(head, "name");
        q.Priority = 50;
        q.Type = b.Kind == "main" ? Mutagen.Bethesda.Skyrim.Quest.TypeEnum.MainQuest : Mutagen.Bethesda.Skyrim.Quest.TypeEnum.SideQuest;
        var start = head.GetProperty("start");
        b.Start = I(start, "stage");
        var byGame = S(start, "by") == "game";
        q.Flags = Mutagen.Bethesda.Skyrim.Quest.Flag.RunOnce | (byGame ? Mutagen.Bethesda.Skyrim.Quest.Flag.StartGameEnabled : 0);
        var stages = A(f, "stages").ToList();
        if (stages.Count > 0 && !stages.Any(s => I(s, "number") == b.Start)) throw c.No("start", $"the start stage {b.Start} is not a stage");
        foreach (var s in stages.OrderBy(s => I(s, "number")))
        {
            var n = I(s, "number"); var ending = S(s, "ending");
            if (ending != "none") b.Endings.Add(n);
            var shown = B(s, "shown");
            q.Stages.Add(new QuestStage
            {
                Index = (ushort)n, Flags = byGame && n == b.Start ? QuestStage.Flag.StartUpStage : 0,
                LogEntries = { new QuestLogEntry { Flags = ending == "completed" ? QuestLogEntry.Flag.CompleteQuest : ending == "failed" ? QuestLogEntry.Flag.FailQuest : 0,
                    Entry = shown ? So(s, "journal") : null } },
            });
        }
        if (S(start, "by") == "quest_stage")
        {
            var other = S(start, "quest");
            if (!c.Quests.TryGetValue(other, out var o)) throw c.No("start", $"started by {other}, which is not built from a form");
            Add(o.From, I(start, "quest_stage"), new Row(Op.StartOnStage, q.FormKey, b.Start));
        }
        Refs(c, b);
        foreach (var o in A(f, "objectives"))
        {
            var obj = new QuestObjective { Index = (ushort)I(o, "number"), DisplayText = S(o, "text") };
            foreach (var t in A(o, "targets"))
                obj.Targets.Add(new QuestObjectiveTarget { AliasID = (int)RefOf(c, b, t.GetString()!, "objective target").Alias });
            q.Objectives.Add(obj);
        }
        // must live: checked alive at the start, before anything else of the start stage
        foreach (var m in A(f, "must_live"))
        {
            var r = RefOf(c, b, S(m, "ref"), "must live");
            if (!r.Npc) throw c.No("must-live", $"{r.Id} is not a person");
            if (Within(m, b.Start)) Add(b.Own, b.Start, new Row(Op.FailIfDead, r.Placed, I(m, "fail_stage")));
        }
        foreach (var s in stages.OrderBy(s => I(s, "number")))
            foreach (var res in A(s, "results"))
            {
                if (S(res, "do") == "speaker_hostile") throw c.No("vocabulary", $"stage {I(s, "number")}: speaker_hostile is a line's result");
                Add(b.Own, I(s, "number"), Result(c, b, res, q.FormKey));
            }
        // objectives: completed, then shown; the stage that shows the first objective makes the quest the tracked one
        var objs = A(f, "objectives").ToList();
        var first = objs.SelectMany(o => A(o, "shown_at").Select(x => x.GetInt32())).DefaultIfEmpty(-1).Min();
        foreach (var s in stages.Select(s => I(s, "number")).OrderBy(x => x))
        {
            foreach (var o in objs.Where(o => A(o, "completed_at").Any(x => x.GetInt32() == s)))
                Add(b.Own, s, new Row(Op.CompleteObjective, FormKey.Null, I(o, "number")));
            foreach (var o in objs.Where(o => A(o, "shown_at").Any(x => x.GetInt32() == s)))
                Add(b.Own, s, new Row(Op.ShowObjective, FormKey.Null, I(o, "number")));
            if (s == first) Add(b.Own, s, new Row(Op.SetActive, FormKey.Null, 0));
        }
        foreach (var s in stages.Where(s => S(s, "ending") != "none"))
        {
            var n = I(s, "number"); var done = S(s, "ending") == "completed";
            // every objective shown and still open is closed, in number order: one row up to the highest objective
            if (objs.Count > 0) Add(b.Tail, n, new Row(done ? Op.CompleteAll : Op.FailAll, FormKey.Null, objs.Max(o => I(o, "number"))));
            if (done && b.Kind != "main") Add(b.Tail, n, new Row(Op.IncSideQuests, Achievements, 0));
        }
        b.Labels.Add("quest=" + b.Qid);
        b.Labels.Add("kind=" + b.Kind);
    }
    static void Add(SortedDictionary<int, List<Row>> rows, int stage, params Row[] r) { if (!rows.TryGetValue(stage, out var l)) rows[stage] = l = []; l.AddRange(r); }
    static Ref RefOf(Ctx c, Built b, string id, string where) => b.Refs.TryGetValue(id, out var r) ? r : throw c.No("refs-exist", $"{where} names {id}, which is not a ref of the form");

    // One form result as rows (`self` is the form's quest: a set_stage sets its stage).
    static Row[] Result(Ctx c, Built b, JsonElement res, FormKey self)
    {
        var w = S(res, "do");
        if (!Op.OfResult.TryGetValue(w, out var op)) throw c.No("vocabulary", $"no result {w}");
        return w switch
        {
            "set_stage" => So(res, "if_held") is { } held ? [new Row(Op.IfHolds, Item(c, b, held), 1), new Row(op, FormKey.Null, I(res, "stage"))] : [new Row(op, FormKey.Null, I(res, "stage"))],
            "give_item" or "take_item" => [new Row(op, Item(c, b, S(res, "item")), I(res, "count"))],
            "give_gold" or "take_gold" => [new Row(op, Gold, I(res, "amount"))],
            "set_number" or "add_number" => [new Row(op, Number(c, S(res, "number")), (float)res.GetProperty("value").GetDouble())],
            "join_faction" => [new Row(op, Faction(c, S(res, "faction")), 0)],
            "set_rank" => [new Row(op, Faction(c, S(res, "faction")), I(res, "rank"))],
            "change_regard" => [new Row(op, PersonRef(c, b, S(res, "ref"), w), I(res, "by"))],
            "switch_on" or "switch_off" => [new Row(op, PlacedRef(c, b, S(res, "ref"), w), 0)],
            "lock_door" or "unlock_door" => [new Row(op, DoorRef(c, b, S(res, "ref"), w == "unlock_door"), 0)],
            "give_ownership" => [new Row(op, OwnedRef(c, b, S(res, "ref")), 0)],
            "show_message" => [new Row(op, Message(c, b, S(res, "text")), 0)],
            "speaker_hostile" => [new Row(op, FormKey.Null, 0)],
            "start_quest" => [new Row(op, QuestKey(c, S(res, "quest")), I(res, "stage"))],
            _ => throw c.No("vocabulary", $"no result {w}"),
        };
    }
    static FormKey PlacedRef(Ctx c, Built b, string id, string what)
    {
        var r = RefOf(c, b, id, what);
        return r.Created ? throw c.No("created", $"{what} names {id}, a thing made in a container, which has no reference to act on") : r.Placed;
    }
    static FormKey PersonRef(Ctx c, Built b, string id, string what)
    {
        var r = RefOf(c, b, id, what);
        return r.Npc ? r.Placed : throw c.No("person", $"{what} names {id}, which is not a person");
    }
    // A thing a result gives the player: a placed thing of the form with an owner (a container another owns).
    static FormKey OwnedRef(Ctx c, Built b, string id)
    {
        var r = RefOf(c, b, id, "give_ownership");
        if (r.Kind != "thing" || !r.Json.TryGetProperty("owner", out _)) throw c.No("owner", $"give_ownership names {id}, which is no thing with an owner");
        return PlacedRef(c, b, id, "give_ownership");
    }
    // A door a result locks or unlocks; one that is unlocked starts locked (requires a key, none given), as vanilla's quest doors.
    static FormKey DoorRef(Ctx c, Built b, string id, bool unlocked)
    {
        var r = RefOf(c, b, id, "a lock");
        if (r.Kind != "door") throw c.No("refs-exist", $"{id} is locked or unlocked and is not a door");
        if (unlocked && Overrides.Placed(c.Mod, r.Placed) is PlacedObject o && o.Lock == null)
        {
            o.Lock = new LockData { Level = LockLevel.RequiresKey };
            Label(c, $"autolock={r.Id}");
        }
        return r.Placed;
    }

    // ---- what the vocabulary names
    static readonly Dictionary<string, ActorValue> Skills = new(StringComparer.Ordinal)
    {
        ["Speech"] = ActorValue.Speech, ["Sneak"] = ActorValue.Sneak, ["Lockpicking"] = ActorValue.Lockpicking, ["Pickpocket"] = ActorValue.Pickpocket,
        ["Alchemy"] = ActorValue.Alchemy, ["OneHanded"] = ActorValue.OneHanded, ["TwoHanded"] = ActorValue.TwoHanded, ["Archery"] = ActorValue.Archery,
        ["Block"] = ActorValue.Block, ["HeavyArmor"] = ActorValue.HeavyArmor, ["LightArmor"] = ActorValue.LightArmor, ["Smithing"] = ActorValue.Smithing,
        ["Enchanting"] = ActorValue.Enchanting, ["Alteration"] = ActorValue.Alteration, ["Conjuration"] = ActorValue.Conjuration,
        ["Destruction"] = ActorValue.Destruction, ["Illusion"] = ActorValue.Illusion, ["Restoration"] = ActorValue.Restoration,
    };
    /// The skill's actor value: Skyrim's own name for it (the form holds no other).
    public static ActorValue? Skill(string s) => Skills.TryGetValue(s, out var v) ? v : null;
    /// The name the reader writes for an actor value: Skyrim's.
    public static string SkillName(ActorValue v) => v.ToString();

    // Each id the form names that the record it resolves to cannot carry (a number's id, a story item's or faction's id,
    // a container's base) is kept as a label on the quest, "name=<kind>|<what it became>|<the form's word>", so the plugin
    // reader writes the form's word back.
    static FormKey Named(Ctx c, string kind, string given, FormKey k)
    {
        if (given != k.ToString()) Label(c, $"name={kind}|{k}|{given}");
        return k;
    }
    static void Label(Ctx c, string l) { if (c.Cur is { } b && !b.Labels.Contains(l)) b.Labels.Add(l); }
    static FormKey Number(Ctx c, string id) => Named(c, "number", id, Number0(c, id));
    static FormKey Faction(Ctx c, string id) => Named(c, "faction", id, Faction0(c, id));
    // an item named by a thing of the form is labelled "thing" (its base keeps its own word where it is placed)
    static FormKey Item(Ctx c, Built b, string id) => Named(c, b.Refs.ContainsKey(id) ? "thing" : "item", id, Item0(c, b, id));
    static FormKey Race(Ctx c, string v) => Named(c, "race", v, Race0(c, v));
    static ActorValue SkillOf(Ctx c, string s) => Skill(s) ?? throw c.No("vocabulary", $"no skill {s}");

    static FormKey QuestKey(Ctx c, string qid) =>
        c.Quests.TryGetValue(qid, out var o) ? o.Q.FormKey : throw c.No("quest", $"{qid} is not built from a form");
    static FormKey Number0(Ctx c, string id)
    {
        var k = c.Key("glob:" + id);
        if (!c.Mod.Globals.Any(g => g.FormKey == k)) c.Mod.Globals.Add(new GlobalFloat(k, SkyrimRelease.SkyrimSE) { EditorID = "ARG_N_" + Slug(id), Data = 0 });
        return k;
    }
    static FormKey Faction0(Ctx c, string id)
    {
        if (id.Contains(':')) return Exists<IFactionGetter>(c, id, "faction");
        var k = c.Key("fac:" + id);
        if (c.Mod.Factions.Any(g => g.FormKey == k)) return k;
        var name = QuestKit.Rows("faction").Where(r => r.GetProperty("id").GetString() == id).Select(r => r.GetProperty("name").GetString()).FirstOrDefault();
        c.Mod.Factions.Add(new Faction(k, SkyrimRelease.SkyrimSE) { EditorID = "ARG_F_" + Slug(id), Name = name ?? id });
        return k;
    }
    static FormKey Exists<T>(Ctx c, string key, string what) where T : class, IMajorRecordGetter
    {
        FormKey k;
        try { k = FormKey.Factory(key); } catch (Exception) { throw c.No("form-key", $"{what} {key} is no form key"); }
        if (c.Mod.EnumerateMajorRecords<T>().Any(r => r.FormKey == k) || c.Mods.Any(m => m.EnumerateMajorRecords<T>().Any(r => r.FormKey == k))) return k;
        throw c.No("form-key", $"{what} {key} is in no plugin of the load order");
    }
    static readonly string[] ItemTypes = ["MISC", "BOOK", "WEAP", "ARMO", "ALCH", "INGR", "KEYM", "SLGM", "AMMO", "SCRL", "LIGH"];
    static Dictionary<string, FormKey>? itemsByEdid; static object? itemsFor;
    /// An item: a form key; a ref id of a thing of the form (its base); or a story item whose first Skyrim record
    /// (item_asset_record) is an item of the load order.
    static FormKey Item0(Ctx c, Built b, string id)
    {
        if (id.Contains(':')) return Exists<IItemGetter>(c, id, "item");
        if (RefJson(c, b, id) is { } rj)
        {
            if (S(rj, "kind") != "thing") throw c.No("item", $"{id} is a {S(rj, "kind")}, not a thing");
            var bas = rj.GetProperty("placement").TryGetProperty("base", out var bb) ? bb : default;
            if (bas.ValueKind != JsonValueKind.Object) throw c.No("item", $"{id} is an existing reference, not an item");
            var bk = S(bas, "kind"); var bid = S(bas, "id");
            if (bk == "template_item" || (bk == "item" && bid == id)) return OwnItem(c, b, id, rj);
            if (bk == "item") return Item0(c, b, bid);
            throw c.No("item", $"{id} is a thing of base kind {bk}, not an item");
        }
        if (c.Quests.Values.Select(q => q.F).Prepend(b.F).Any(f => f.TryGetProperty("texts", out var tx) && tx.TryGetProperty(id, out _)))
            return OwnItem(c, b, id, null);
        var edid = QuestKit.Rows("item_asset_record").Where(x => x.GetProperty("item_id").GetString() == id && x.GetProperty("ord").GetInt32() == 0)
            .Select(x => x.GetProperty("value").GetString()).FirstOrDefault() ?? throw c.No("item", $"{id}: no form key, no thing of the form and no item_asset_record");
        if (!ReferenceEquals(itemsFor, c.Mods))
        {
            itemsFor = c.Mods; itemsByEdid = new(StringComparer.OrdinalIgnoreCase);
            foreach (var m in c.Mods) foreach (var it in m.EnumerateMajorRecords<IItemGetter>()) if (it.EditorID is { } e) itemsByEdid[e] = it.FormKey;
        }
        return itemsByEdid!.TryGetValue(edid, out var k) ? k : throw c.No("item", $"{id}: its record {edid} is no item of the load order");
    }
    /// The ref of that id in this form, else in any other form being built (a lock's key another form places).
    static JsonElement? RefJson(Ctx c, Built b, string id)
    {
        foreach (var f in c.Quests.Values.Select(q => q.F).Prepend(b.F))
            foreach (var r in A(f, "refs")) if (S(r, "id") == id) return r;
        return null;
    }
    // The templates of a new item of ours whose form gives none (an item whose id is the ref's own, or a page the form
    // gives the words of): a key when some lock names it, a note when it has words, else a clay pot.
    public static readonly FormKey KeyTemplate = FormKey.Factory("10E7E6:Skyrim.esm"), NoteTemplate = FormKey.Factory("0A0F46:Skyrim.esm"),
        MiscTemplate = FormKey.Factory("0B9BD2:Skyrim.esm");
    /// A new item of ours: a `template_item` thing's copy of its template, or an item whose id is the ref's own (or a page
    /// of the form's `texts`) on the template of its kind; called by the ref's name (or the form's `names`), with the
    /// ref's text (or the form's `texts`) for a book. One record per id, whichever form names it first.
    static FormKey OwnItem(Ctx c, Built b, string id, JsonElement? rj)
    {
        var k = c.Key("item:" + id);
        if (c.Mod.EnumerateMajorRecords<IItemGetter>().Any(x => x.FormKey == k)) return Named(c, "item", id, k);
        string? Word(string field) =>
            c.Quests.Values.Select(q => q.F).Prepend(b.F).Select(f => f.TryGetProperty(field, out var m) && m.TryGetProperty(id, out var v) ? v.GetString() : null).FirstOrDefault(x => x != null);
        var name = (rj is { } r0 ? So(r0, "name") : null) ?? Word("names") ?? throw c.No("item", $"{id}: a new item with no name");
        var text = (rj is { } r1 ? So(r1, "text") : null) ?? Word("texts");
        var bas = rj is { } r2 ? r2.GetProperty("placement").GetProperty("base") : default;
        FormKey tk; string? template = null;
        if (bas.ValueKind == JsonValueKind.Object && S(bas, "kind") == "template_item") { template = S(bas, "id"); tk = Item0(c, b, template); }
        else if (c.Quests.Values.Select(q => q.F).Prepend(b.F).SelectMany(f => A(f, "refs")).Any(x => x.TryGetProperty("lock", out var l) && So(l, "key") == id)) tk = KeyTemplate;
        else tk = text != null ? NoteTemplate : MiscTemplate;
        var src = Enumerable.Reverse(c.Mods).SelectMany(m => m.EnumerateMajorRecords<IItemGetter>()).FirstOrDefault(x => x.FormKey == tk)
            ?? throw c.No("item", $"{id}: its template {tk} is no item of the load order");
        var copy = (IItemGetter)((IMajorRecordGetter)src).Duplicate(k);
        var rec = (IMajorRecord)copy;
        rec.EditorID = $"ARG_I_{Slug(id)}";
        // the name the player sees, set on each kind's own name (the shared name interfaces miss a key's)
        var full = new Mutagen.Bethesda.Strings.TranslatedString(Mutagen.Bethesda.Strings.Language.English, name);
        switch (copy)
        {
            case Key x: x.Name = full; break; case Book x: x.Name = full; break; case MiscItem x: x.Name = full; break;
            case Armor x: x.Name = full; break; case Weapon x: x.Name = full; break; case Ingredient x: x.Name = full; break;
            case Ingestible x: x.Name = full; break;
        }
        var got = copy switch { Key x => x.Name?.String, Book x => x.Name?.String, MiscItem x => x.Name?.String, Armor x => x.Name?.String,
            Weapon x => x.Name?.String, Ingredient x => x.Name?.String, Ingestible x => x.Name?.String, _ => null };
        if (got != name) throw c.No("item", $"{id}: its copy of {tk} took the name '{got}', not '{name}'");
        if (copy is Book bk2)
        {
            if (text != null) bk2.BookText = text;
            bk2.Teaches = null; bk2.VirtualMachineAdapter = null;
        }
        switch (copy)
        {
            case Key kk: kk.VirtualMachineAdapter = null; c.Mod.Keys.Add(kk); break;
            case Book bo: c.Mod.Books.Add(bo); break;
            case MiscItem mi: mi.VirtualMachineAdapter = null; c.Mod.MiscItems.Add(mi); break;
            case Armor ar: c.Mod.Armors.Add(ar); break;
            case Weapon we: c.Mod.Weapons.Add(we); break;
            case Ingredient ig: c.Mod.Ingredients.Add(ig); break;
            case Ingestible ie: c.Mod.Ingestibles.Add(ie); break;
            default: throw c.No("item", $"{id}: its template {tk} is a {copy.GetType().Name}, which the builder does not copy");
        }
        if (template != null) Label(c, $"name=template|{k}|{template}");
        return Named(c, "item", id, k);
    }

    static FormKey Message(Ctx c, Built b, string text)
    {
        var k = c.Key($"msg:{b.Qid}:{Sha(text)}");
        if (!c.Mod.Messages.Any(m => m.FormKey == k))
            c.Mod.Messages.Add(new Message(k, SkyrimRelease.SkyrimSE) { EditorID = $"{b.Edid}_Msg_{Sha(text)[..6]}", Description = text, Flags = Mutagen.Bethesda.Skyrim.Message.Flag.MessageBox });
        return k;
    }
    static FormKey Race0(Ctx c, string v)
    {
        if (v.Contains(':')) return Exists<IRaceGetter>(c, v, "race");
        var name = v.StartsWith("race.") ? v[5..] : v;
        foreach (var m in Enumerable.Reverse(c.Mods))
            foreach (var r in m.Races)
                if (string.Equals(r.EditorID, name, StringComparison.OrdinalIgnoreCase) || string.Equals(r.EditorID, name + "Race", StringComparison.OrdinalIgnoreCase)) return r.FormKey;
        throw c.No("race", $"no race {v} in the load order");
    }

    // ---- the refs
    static void Refs(Ctx c, Built b)
    {
        uint n = 0;
        var refs = A(b.F, "refs").ToList();
        foreach (var j in refs)
        {
            var r = new Ref { Id = S(j, "id"), Kind = S(j, "kind"), Json = j, Alias = n++, Enabled = B(j, "enabled"), Hostile = B(j, "hostile") };
            if (b.Refs.ContainsKey(r.Id)) throw c.No("unique-ids", $"two refs {r.Id}");
            b.Refs[r.Id] = r;
        }
        // containers first: a thing in a container names the container's alias
        foreach (var r in b.Refs.Values) Place(c, b, r);
        foreach (var r in b.Refs.Values.Where(r => r.Fresh)) Decorate(c, b, r);
        foreach (var r in b.Refs.Values)
        {
            var a = new QuestAlias { ID = r.Alias, Type = QuestAlias.TypeEnum.Reference, Name = r.Id };
            if (r.Created)
            {
                var pl = r.Json.GetProperty("placement");
                var cont = b.Refs[So(pl, "container") ?? S(pl, "carried_by")];
                a.CreateReferenceToObject = new CreateReferenceToObject { AliasID = (short)cont.Alias, Create = CreateReferenceToObject.CreateEnum.In, Level = Level.Easy };
                a.CreateReferenceToObject.Object.SetTo(r.Base);
            }
            else
            {
                a.ForcedReference.SetTo(r.Placed);
                if (!r.Enabled) a.Flags = QuestAlias.Flag.AllowDisabled;
            }
            r.A = a;
            b.Q.Aliases.Add(a);
        }
    }

    static void Place(Ctx c, Built b, Ref r)
    {
        var j = r.Json; var p = j.GetProperty("placement");
        if (r.Hostile && r.Kind != "person") throw c.No("hostile", $"{r.Id} is hostile and not a person");
        // a ref another form names too is the same reference: one placement, which both forms must state alike
        var same = $"{r.Kind}|{p.GetRawText()}|{r.Enabled}|{r.Hostile}|{(j.TryGetProperty("lock", out var l1) ? l1.GetRawText() : "")}|{So(j, "owner")}|{(j.TryGetProperty("contents", out var c1) ? c1.GetRawText() : "")}|{(j.TryGetProperty("level", out var lv1) ? lv1.GetInt32() : null)}";
        if (c.Shared.TryGetValue(r.Id, out var had))
        {
            if (had.Same != same) throw c.No("shared-ref", $"{r.Id} is placed otherwise by {had.Quest}");
            if (had.Created) throw c.No("shared-ref", $"{r.Id} is made in a container for {had.Quest}; a made thing belongs to one quest");
            (r.Placed, r.Base, r.Npc) = (had.Placed, had.Base, had.Npc);
            if (r.Npc && j.TryGetProperty("level", out _)) Label(c, $"level={r.Id}");   // its fixed level, for this quest's reader
            if (p.TryGetProperty("base", out var sb) && S(sb, "kind") == "item" && S(sb, "id") != r.Id) Item(c, b, S(sb, "id"));   // its item word, for this quest's reader
            return;
        }
        try { PlaceOnce(c, b, r, p); r.Fresh = true; }
        finally { if (!r.Placed.IsNull || r.Created) c.Shared[r.Id] = (b.Qid, same, r.Placed, r.Base, r.Npc, r.Created); }
    }

    static void PlaceOnce(Ctx c, Built b, Ref r, JsonElement p)
    {
        var j0 = r.Json;
        if (p.TryGetProperty("existing", out var ex))
        {
            if (r.Hostile) throw c.No("hostile", $"{r.Id}: a person the player fights is a new placement (its base of ours is made aggressive)");
            FormKey k;
            try { k = FormKey.Factory(ex.GetString()!); } catch (Exception) { throw c.No("form-key", $"{r.Id}: {ex.GetString()} is no form key"); }
            if (!c.Placed.TryGetValue(k, out var src) && Overrides.Placed(c.Mod, k) == null) throw c.No("placement", $"{r.Id}: {k} is no placed reference of the load order");
            var rec = (IPlacedGetter?)Overrides.Placed(c.Mod, k) ?? src.rec;
            r.Npc = rec is IPlacedNpcGetter;
            if ((r.Kind == "person") != r.Npc) throw c.No("placement", $"{r.Id}: a {r.Kind} placed as {(r.Npc ? "an actor" : "an object")}");
            r.Base = rec switch { IPlacedNpcGetter pn => pn.Base.FormKey, IPlacedObjectGetter po => po.Base.FormKey, _ => FormKey.Null };
            if (r.Kind == "door" && !c.Mods.Any(m => m.Doors.Any(d => d.FormKey == r.Base))) throw c.No("placement", $"{r.Id}: {k} is not a door");
            var parent = rec switch { IPlacedNpcGetter pn => pn.EnableParent, IPlacedObjectGetter po => po.EnableParent, _ => null };
            if (parent != null && !parent.Reference.IsNull) throw c.No("placement", $"{r.Id}: {k} hangs on an enable parent, so the form cannot say when it is on");
            r.Placed = k;
            Persist(c, k, r.Enabled, j0.TryGetProperty("lock", out _) || j0.TryGetProperty("owner", out _));
            return;
        }
        var bas = p.GetProperty("base"); var bk = S(bas, "kind"); var bid = S(bas, "id");
        var holder = So(p, "container") is { } cn ? (cn, "thing", "container") : So(p, "carried_by") is { } cb ? (cb, "person", "carrier") : default;
        if (holder.Item1 != null)
        {
            if (p.TryGetProperty("anchor", out _) || (p.TryGetProperty("container", out _) && p.TryGetProperty("carried_by", out _))) throw c.No("placement", $"{r.Id}: more than one of an anchor, a container and a carrier");
            if (r.Kind != "thing" || bk is not ("item" or "template_item")) throw c.No("placement", $"{r.Id}: only an item thing sits in a {holder.Item3}");
            if (!r.Enabled) throw c.No("placement", $"{r.Id}: a thing made in a {holder.Item3} is there from the quest's start (enabled)");
            if (!b.Refs.TryGetValue(holder.Item1, out var box) || box.Kind != holder.Item2) throw c.No("placement", $"{r.Id}: its {holder.Item3} {holder.Item1} is not a {holder.Item2} of the form");
            r.Base = bk == "template_item" ? OwnItem(c, b, r.Id, r.Json) : Item(c, b, bid); r.Created = true;
            return;
        }
        if (!p.TryGetProperty("anchor", out var anchor)) throw c.No("placement", $"{r.Id}: a new placement with neither an anchor, a container nor a carrier");
        var (cell, world, interior, at) = Spot(c, b, r, anchor);
        var key = c.Key($"ref:{r.Id}");
        var edid = $"ARG_R_{Slug(r.Id)}";
        var flags = 0x400 | (r.Enabled ? 0 : 0x800);
        IPlaced placed;
        if (r.Kind == "person")
        {
            if (bk != "template_person") throw c.No("placement", $"{r.Id}: a new person is a template_person");
            var npc = Person(c, b, r, bid);
            // by a load door, facing where the player comes out of it (heading 0 is north, +y; clockwise)
            var face = r.Door is { } dr ? new P3Float(0, 0, MathF.Atan2(dr.arrival.X - at.X, dr.arrival.Y - at.Y)) : new P3Float();
            var a = new PlacedNpc(key, SkyrimRelease.SkyrimSE) { EditorID = edid, MajorRecordFlagsRaw = flags, Placement = new Placement { Position = at, Rotation = face } };
            a.Base.SetTo(npc); r.Base = npc; r.Npc = true; placed = a;
        }
        else
        {
            if (bk == "template_person") throw c.No("placement", $"{r.Id}: a {r.Kind} placed as a person");
            r.Base = bk == "template_item" ? OwnItem(c, b, r.Id, r.Json) : bk == "item" ? Item(c, b, bid) : Exists<IPlaceableObjectGetter>(c, bid, "base");
            if (j0.TryGetProperty("contents", out var contents)) r.Base = Contents(c, b, r, bk, bid, contents);
            else if (bk == "existing_base" && So(j0, "name") != null && IsContainer(c.Mods, r.Base)) r.Base = Contents(c, b, r, bk, bid, null);
            if (r.Kind == "door" && !c.Mods.Any(m => m.Doors.Any(d => d.FormKey == r.Base))) throw c.No("placement", $"{r.Id}: base {bid} is not a door");
            if (S(anchor, "rule") == "surface") at = Footprint(c, cell, world, interior, at, r.Base);
            var o = new PlacedObject(key, SkyrimRelease.SkyrimSE) { EditorID = edid, MajorRecordFlagsRaw = flags, Placement = new Placement { Position = at, Rotation = new P3Float() } };
            o.Base.SetTo(r.Base); placed = o;
            if (j0.TryGetProperty("count", out var cnt)) o.ItemCount = cnt.GetInt32();
        }
        r.Placed = key;
        if (interior) Overrides.Interior(c.Mod, c.Mods, cell).Persistent.Add(placed);
        else Overrides.World(c.Mod, c.Mods, world).TopCell!.Persistent.Add(placed);
        c.Wheres[key] = new Where(cell, world, interior, at);
    }

    // A new container's contents: our own copy of the form's container base with exactly those items and no respawn.
    // A named container of an existing base is that copy too, carrying the form's name and holding only what the form
    // puts in it (the base's own loot is levelled; nothing is levelled against the player, decision 0035).
    static FormKey Contents(Ctx c, Built b, Ref r, string bk, string bid, JsonElement? contents)
    {
        if (r.Kind != "thing" || bk != "existing_base") throw c.No("contents", $"{r.Id}: contents are set on a new container, a thing of an existing base");
        var baseKey = r.Base;
        var src = Enumerable.Reverse(c.Mods).SelectMany(m => m.Containers).FirstOrDefault(x => x.FormKey == baseKey)
            ?? throw c.No("contents", $"{r.Id}: base {bid} is no container of the load order");
        var k = c.Key($"cont:{r.Id}");
        var cont = src.Duplicate(k);
        cont.EditorID = $"ARG_R_{Slug(r.Id)}_Cont";
        cont.Flags &= ~Container.Flag.Respawns;
        if (So(r.Json, "name") is { } shown) cont.Name = shown;
        cont.Items = contents is not { } items ? null : items.EnumerateArray()
            .Select(x => new ContainerEntry { Item = new ContainerItem { Item = new FormLink<IItemGetter>(ItemIn(c, b, S(x, "item"), r)), Count = I(x, "count") } })
            .ToExtendedList();
        c.Mod.Containers.Add(cont);
        Named(c, "base", bid, k);
        return k;
    }
    static FormKey ItemIn(Ctx c, Built b, string id, Ref r)
    {
        if (b.Refs.ContainsKey(id)) throw c.No("contents", $"{r.Id}: content {id} is a ref of the form: name an item by its own id");
        return Item(c, b, id);
    }

    static LockLevel LevelOf(Ctx c, string w) => w switch
    {
        "novice" => LockLevel.Novice, "apprentice" => LockLevel.Apprentice, "adept" => LockLevel.Adept, "expert" => LockLevel.Expert,
        "master" => LockLevel.Master, "key" => LockLevel.RequiresKey, _ => throw c.No("lock", $"no lock level {w}"),
    };
    public static bool IsContainer(IEnumerable<ISkyrimModGetter> mods, FormKey k) => mods.Any(m => m.Containers.Any(x => x.FormKey == k));

    // A lock (XLOC) and an owner (XOWN) on the placed reference: on our new placement, or on our override of an existing one
    // (which says something the winning record does not: a form that states what the reference already has is refused).
    static void Decorate(Ctx c, Built b, Ref r)
    {
        var j = r.Json;
        var hasLock = j.TryGetProperty("lock", out var lk); var hasOwner = j.TryGetProperty("owner", out var ow);
        if (!hasLock && !hasOwner) return;
        var what = hasLock ? "lock" : "owner";
        if (r.Created) throw c.No(what, $"{r.Id}: a thing made in a container or a pocket has no reference to {(hasLock ? "lock" : "own")}");
        var o = Overrides.Placed(c.Mod, r.Placed) as PlacedObject ?? throw c.No(what, $"{r.Id}: only a placed object takes a {what}");
        var before = c.Placed.TryGetValue(r.Placed, out var src) ? src.rec as IPlacedObjectGetter : null;
        if (hasLock)
        {
            if (r.Kind == "thing" ? !IsContainer(c.Mods.Append(c.Mod), r.Base) : r.Kind != "door") throw c.No("lock", $"{r.Id}: only a door or a container is locked");
            var level = LevelOf(c, S(lk, "level"));
            FormKey? key = null;
            if (So(lk, "key") is { } kid)
            {
                var kk = Item(c, b, kid);
                if (!c.Mods.Append(c.Mod).Any(m => m.Keys.Any(x => x.FormKey == kk))) throw c.No("lock", $"{r.Id}: its key {kid} is no key item");
                key = kk;
            }
            if (before?.Lock is { } was && ((int)was.Level & 0xFF) == ((int)level & 0xFF) && (was.Key.IsNull ? null : (FormKey?)was.Key.FormKey) == key) throw c.No("lock", $"{r.Id}: the lock states what the reference already has");
            var ld = new LockData { Level = level };
            if (key is { } kv) ld.Key.SetTo(kv);
            o.Lock = ld;
        }
        if (hasOwner)
        {
            if (r.Kind != "thing") throw c.No("owner", $"{r.Id}: only a thing has an owner");
            var oid = ow.GetString()!;
            FormKey owner;
            if (b.Refs.TryGetValue(oid, out var pr))
            {
                if (!pr.Npc) throw c.No("owner", $"{r.Id}: its owner {oid} is not a person");
                if (b.Refs.Values.Count(x => x.Npc && x.Base == pr.Base) != 1) throw c.No("owner", $"{r.Id}: its owner {oid} shares a base with another person of the form, so the record cannot name one");
                owner = pr.Base;
            }
            else owner = Faction(c, oid);
            if (before is { } bo && bo.Owner.FormKey == owner) throw c.No("owner", $"{r.Id}: the owner states what the reference already has");
            o.Owner.SetTo(owner);
        }
    }

    // The spot a new placement stands on: from `at` when the form gives it, else the anchor ref's; then the rule:
    // navmesh, the nearest free triangle centre of the cell's navmeshes; surface, the modelled surface or land under it
    // nearest the spot's height.
    static (FormKey cell, FormKey world, bool interior, P3Float at) Spot(Ctx c, Built b, Ref r, JsonElement anchor)
    {
        var rule = S(anchor, "rule");
        FormKey cell, world; bool interior; P3Float p;
        // a load door as the anchor of the person who speaks first, or of a ref with no `at`: where the player comes out of
        // it, whatever `at` says (the door decides the spot); anyone else stands at `at`
        var speaksFirst = A(b.F, "lines").Any(l => S(l, "kind") == "speaks_first" && S(l, "speaker") == r.Id);
        var nearDoor = anchor.TryGetProperty("near", out var nd) && Arrival(c, nd.GetString()!) && (speaksFirst || !r.Json.TryGetProperty("at", out _));
        if (!nearDoor && r.Json.TryGetProperty("at", out var at))
        {
            interior = B(at, "interior");
            try { cell = FormKey.Factory(S(at, "cell")); } catch (Exception) { throw c.No("placement", $"{r.Id}: at.cell {S(at, "cell")} is no form key"); }
            p = new P3Float((float)at.GetProperty("x").GetDouble(), (float)at.GetProperty("y").GetDouble(), (float)at.GetProperty("z").GetDouble());
            world = interior ? FormKey.Null : c.CellWorld.TryGetValue(cell, out var w) ? w : throw c.No("placement", $"{r.Id}: exterior cell {cell} is in no world of the load order");
            if (!interior && CellAt(c, world, p) != cell) throw c.No("placement", $"{r.Id}: {p.X:F0},{p.Y:F0} is not in cell {cell}");
        }
        else if (anchor.TryGetProperty("near", out var near))
        {
            FormKey nk;
            try { nk = FormKey.Factory(near.GetString()!); } catch (Exception) { throw c.No("placement", $"{r.Id}: anchor {near.GetString()} is no form key"); }
            if (!c.Wheres.TryGetValue(nk, out var wh)) throw c.No("placement", $"{r.Id}: anchor {nk} is no placed reference of the load order");
            (cell, world, interior, p) = (wh.Cell, wh.World, wh.Interior, wh.Pos);
            // a load door: where the player comes out of it, a step further on, so the spot is in front of it and
            // clear of the player's own arrival point
            if (c.Arrivals.TryGetValue(nk, out var arr))
            {
                r.Door = (nk, arr);
                float dx = arr.X - p.X, dy = arr.Y - p.Y, dl = MathF.Max(1, MathF.Sqrt(dx * dx + dy * dy));
                p = new P3Float(arr.X + 100 * dx / dl, arr.Y + 100 * dy / dl, arr.Z);
                if (!interior) cell = CellAt(c, world, p);
            }
        }
        else throw c.No("placement", $"{r.Id}: a place anchor needs the form's `at` (where in the place it stands)");
        if (rule == "navmesh")
        {
            // the nearest point of a navmesh at the spot's level: by a load door, at the player's feet (within 100 up or
            // down, so never the water's navmesh under a pier); else within 200 of the form's height
            // outdoors the form's height is the ground's: the surface under the spot nearest it (a record gives no height)
            // (unless a navmesh lies right under the spot at the form's own height: one over a surface the reader does not
            // see, such as a giant tree's roots)
            if (!nearDoor && !interior && Surfaces(c, cell, world, interior, p) is { Count: > 0 } ground
                && NearestOn(c, Neighbours(c.Grid, cell, world, interior, p), p, 200, take: false) is not { dist: <= 1 })
                p = new P3Float(p.X, p.Y, ground.MinBy(h => MathF.Abs(h.Top - p.Z))!.Top);
            // by a load door with no navmesh at the player's level within DoorStand of the spot: on the surface there, so
            // he stands a step from where the player comes out and need not walk to greet
            if (nearDoor && NearestOn(c, Neighbours(c.Grid, cell, world, interior, p), p, 100, take: false) is not { dist: <= DoorStand })
            {
                var deck = Surfaces(c, cell, world, interior, p).Where(h => MathF.Abs(h.Top - p.Z) <= 100).MinBy(h => MathF.Abs(h.Top - p.Z))
                    ?? throw c.No("placement", $"{r.Id}: no navmesh and no surface at the player's level within {DoorStand} of where the player comes out of {r.Door!.Value.door}");
                r.Standing = true;
                var at3 = new P3Float(MathF.Round(p.X), MathF.Round(p.Y), MathF.Ceiling(deck.Top) + 1);
                Console.WriteLine($"questform {c.Q}: {r.Id} stands on {deck.EditorId ?? deck.Kind} at {at3.X:F0},{at3.Y:F0},{at3.Z:F0}, a step from where the player comes out of {r.Door!.Value.door}: no navmesh at that level within {DoorStand}");
                return (interior ? cell : CellAt(c, world, at3), world, interior, at3);
            }
            var on = NearestOn(c, Neighbours(c.Grid, cell, world, interior, p), p, nearDoor ? 100 : 200);
            if (on is { } o && o.dist <= 300)
            {
                // a unit over the navmesh, never under it
                var at2 = new P3Float(MathF.Round(o.at.X), MathF.Round(o.at.Y), MathF.Ceiling(o.at.Z) + 1);
                return (interior ? cell : CellAt(c, world, at2), world, interior, at2);
            }
            // no navmesh where the form puts a person: one who is not fought stands at the form's exact spot and will not
            // walk; a person the player fights, or one placed by a door, needs navmesh
            var why = on == null ? $"no navmesh at its level in or beside cell {cell}" : $"the nearest navmesh at its level is {on.Value.dist:F0} units from its spot";
            if (r.Kind != "person" || r.Hostile || nearDoor || !r.Json.TryGetProperty("at", out _))
                throw c.No("placement", $"{r.Id}: {why}{(r.Hostile ? " (a person the player fights must stand on navmesh)" : "")}");
            // on the floor under the form's spot: the highest surface no more than 100 above its height
            var floor = Surfaces(c, cell, world, interior, p).Where(h => h.Top <= p.Z + 100).MaxBy(h => h.Top)
                ?? throw c.No("placement", $"{r.Id}: {why}, and no floor under its spot {p.X:F0},{p.Y:F0},{p.Z:F0} to stand on");
            r.Standing = true;
            var stand = new P3Float(MathF.Round(p.X), MathF.Round(p.Y), MathF.Round(floor.Top) + 1);
            Console.WriteLine($"questform {c.Q}: {r.Id} stands at its spot {stand.X:F0},{stand.Y:F0},{stand.Z:F0} on {floor.EditorId ?? floor.Kind} in {cell}: {why}, so they will not walk");
            return (cell, world, interior, stand);
        }
        var hits = Surfaces(c, cell, world, interior, p);
        if (hits.Count == 0) throw c.No("placement", $"{r.Id}: no surface under {p.X:F0},{p.Y:F0}");
        var top = hits.MinBy(h => MathF.Abs(h.Top - p.Z))!;
        return (cell, world, interior, new P3Float(MathF.Round(p.X), MathF.Round(p.Y), MathF.Round(top.Top)));
    }

    /// A thing on a surface rests on the highest surface under its footprint (its bounds' corners, a few units in, and its
    /// centre) within 40 of the spot, so no part of it sinks into an uneven floor.
    static P3Float Footprint(Ctx c, FormKey cell, FormKey world, bool interior, P3Float at, FormKey baseKey)
    {
        var ob = c.Mod.EnumerateMajorRecords<IPlaceableObjectGetter>().Concat(Enumerable.Reverse(c.Mods).SelectMany(m => m.EnumerateMajorRecords<IPlaceableObjectGetter>()))
            .FirstOrDefault(x => x.FormKey == baseKey) is IObjectBoundedGetter bd ? bd.ObjectBounds : null;
        if (ob == null) return at;
        var z = at.Z;
        foreach (var x in new[] { ob.First.X + 4f, 0f, ob.Second.X - 4f })
            foreach (var y in new[] { ob.First.Y + 4f, 0f, ob.Second.Y - 4f })
                foreach (var h in Surfaces(c, cell, world, interior, new P3Float(at.X + x, at.Y + y, at.Z)))
                    if (MathF.Abs(h.Top - at.Z) <= 40) z = MathF.Max(z, MathF.Ceiling(h.Top));
        return new P3Float(at.X, at.Y, z);
    }

    /// Every modelled surface (and the land, outdoors) under a spot.
    static List<Surface.Hit> Surfaces(Ctx c, FormKey cell, FormKey world, bool interior, P3Float p)
    {
        var assets = new Surface.Assets(Surface.Paths);
        if (!interior) return Surface.Under(c.Mods, assets, world, p.X, p.Y);
        Surface.Bases(c.Mods);
        var refs = c.Mods.SelectMany(m => m.Cells.Records.SelectMany(x => x.SubBlocks).SelectMany(x => x.Cells)).Where(x => x.FormKey == cell)
            .SelectMany(x => x.Persistent.Concat(x.Temporary)).OfType<IPlacedObjectGetter>().GroupBy(o => o.FormKey).Select(g => g.Last()).Where(o => o.Placement != null);
        return Surface.UnderRefs(refs, assets, p.X, p.Y, everyCrossing: true);
    }

    /// The cells whose navmeshes may hold a spot: an interior's own; an exterior cell and the eight round it (a navmesh
    /// of an exterior cell is kept in the cell its triangles start in).
    public static List<FormKey> Neighbours(Dictionary<(FormKey world, int x, int y), FormKey> grid, FormKey cell, FormKey world, bool interior, P3Float p)
    {
        if (interior) return [cell];
        int gx = (int)MathF.Floor(p.X / 4096), gy = (int)MathF.Floor(p.Y / 4096);
        var l = new List<FormKey>();
        for (var dx = -1; dx <= 1; dx++) for (var dy = -1; dy <= 1; dy++) if (grid.TryGetValue((world, gx + dx, gy + dy), out var k)) l.Add(k);
        return l;
    }
    /// The winning navmesh of those cells with the triangle centre nearest the spot (in x and y), or null.
    public static FormKey? NearestMesh(List<ISkyrimModGetter> mods, List<FormKey> cells, P3Float p)
    {
        var want = cells.ToHashSet();
        var meshes = mods.SelectMany(m => m.EnumerateMajorRecords<ICellGetter>().Where(x => want.Contains(x.FormKey))).SelectMany(x => x.NavigationMeshes.Select(n => n.FormKey)).ToHashSet();
        var win = new Dictionary<FormKey, INavigationMeshGetter>();
        foreach (var m in mods) foreach (var n in m.EnumerateMajorRecords<INavigationMeshGetter>()) if (meshes.Contains(n.FormKey)) win[n.FormKey] = n;
        FormKey? best = null; var bd = float.MaxValue;
        foreach (var (k, n) in win)
        {
            if (n.Data is not { } d) continue;
            foreach (var t in d.Triangles)
            {
                var a = d.Vertices[t.Vertices.X]; var b = d.Vertices[t.Vertices.Y]; var e = d.Vertices[t.Vertices.Z];
                float x = (a.X + b.X + e.X) / 3 - p.X, y = (a.Y + b.Y + e.Y) / 3 - p.Y, dd = x * x + y * y;
                if (dd < bd) { bd = dd; best = k; }
            }
        }
        return best;
    }

    /// The nearest point of the winning navmeshes of those cells to the spot in x and y, among triangles whose height
    /// there is within `dz` of the spot's (a used point, where another placed person stands, is passed over): the
    /// navmesh, the point and its distance; null when none.
    static (FormKey mesh, P3Float at, float dist)? NearestOn(Ctx c, List<FormKey> cells, P3Float p, float dz, bool take = true)
    {
        var want = cells.ToHashSet();
        var meshes = c.Mods.SelectMany(m => m.EnumerateMajorRecords<ICellGetter>().Where(x => want.Contains(x.FormKey))).SelectMany(x => x.NavigationMeshes.Select(n => n.FormKey)).ToHashSet();
        var navs = Navs(c);
        (FormKey, P3Float, float)? best = null;
        foreach (var k in meshes)
        {
            if (!navs.TryGetValue(k, out var n) || n.Data is not { } d) continue;
            var v = d.Vertices;
            foreach (var t in d.Triangles)
            {
                P3Float a = v[t.Vertices.X], b = v[t.Vertices.Y], e = v[t.Vertices.Z];
                var (dist, z) = PlaceCheck.Nearest2D(a, b, e, p.X, p.Y);
                if (MathF.Abs(z - p.Z) > dz || (best is { } bb && dist >= bb.Item3)) continue;
                // the point itself: the spot when inside, else the nearest point of the edge (a step in from it)
                var q = Inward(a, b, e, p, dist);
                if (take && c.Stood.Any(s0 => (s0.X - q.X) * (s0.X - q.X) + (s0.Y - q.Y) * (s0.Y - q.Y) < 60 * 60)) continue;
                best = (k, new P3Float(q.X, q.Y, z), dist);
            }
        }
        if (take && best is { } r) c.Stood.Add(r.Item2);
        return best;
    }
    // The point of a triangle nearest x,y: the spot itself when it is inside, else a point 20 units in from the nearest
    // edge point towards the triangle's centre.
    static P3Float Inward(P3Float a, P3Float b, P3Float e, P3Float p, float dist)
    {
        if (dist <= 0) return p;
        var best = (d: float.MaxValue, x: 0f, y: 0f);
        foreach (var (u, w) in new[] { (a, b), (b, e), (e, a) })
        {
            float ex = w.X - u.X, ey = w.Y - u.Y, len = ex * ex + ey * ey;
            var t = len < 1e-6f ? 0 : Math.Clamp(((p.X - u.X) * ex + (p.Y - u.Y) * ey) / len, 0, 1);
            float px = u.X + t * ex, py = u.Y + t * ey, dd = (p.X - px) * (p.X - px) + (p.Y - py) * (p.Y - py);
            if (dd < best.d) best = (dd, px, py);
        }
        float cx = (a.X + b.X + e.X) / 3, cy = (a.Y + b.Y + e.Y) / 3, l = MathF.Max(1, MathF.Sqrt((cx - best.x) * (cx - best.x) + (cy - best.y) * (cy - best.y)));
        var step = MathF.Min(20, l);
        return new P3Float(best.x + step * (cx - best.x) / l, best.y + step * (cy - best.y) / l, p.Z);
    }
    /// The triangle of a navmesh (the winning copy) whose centre is nearest the spot in x and y, and that distance.
    static (int tri, float dist) NearestTriangle(Ctx c, FormKey mesh, P3Float p)
    {
        var d = Navs(c)[mesh].Data!; var v = d.Vertices;
        var best = (tri: -1, dist: float.PositiveInfinity);
        for (var i = 0; i < d.Triangles.Count; i++)
        {
            var t = d.Triangles[i].Vertices;
            float x = (v[t.X].X + v[t.Y].X + v[t.Z].X) / 3 - p.X, y = (v[t.X].Y + v[t.Y].Y + v[t.Z].Y) / 3 - p.Y, dd = MathF.Sqrt(x * x + y * y);
            if (dd < best.dist) best = (i, dd);
        }
        return best;
    }
    static Dictionary<FormKey, INavigationMeshGetter> Navs(Ctx c)
    {
        if (c.NavWin.Count == 0) foreach (var m in c.Mods) foreach (var n in m.EnumerateMajorRecords<INavigationMeshGetter>()) if (n.Data != null) c.NavWin[n.FormKey] = n;
        return c.NavWin;
    }
    /// Whether a walk over the winning navmeshes joins two spots: from the triangle nearest one to the triangle nearest the
    /// other, across the triangles' shared edges and the edge links between navmeshes.
    static bool Walk(Ctx c, (FormKey world, FormKey cell, bool interior) space, P3Float a, P3Float b)
    {
        (FormKey, int)? Near(P3Float p) =>
            NearestMesh(c.Mods, Neighbours(c.Grid, space.cell, space.world, space.interior, p), p) is { } m ? (m, NearestTriangle(c, m, p).tri) : null;
        if (Near(a) is not { } from || Near(b) is not { } to) return false;
        var navs = Navs(c);
        var seen = new HashSet<(FormKey, int)> { from }; var queue = new Queue<(FormKey, int)>([from]);
        while (queue.Count > 0)
        {
            var (m, i) = queue.Dequeue();
            if ((m, i) == to) return true;
            if (!navs.TryGetValue(m, out var nv) || nv.Data is not { } d || i < 0 || i >= d.Triangles.Count) continue;
            var t = d.Triangles[i];
            var e = new[] { (int)t.EdgeLink_0_1, (int)t.EdgeLink_1_2, (int)t.EdgeLink_2_0 };   // flag bits 0-2: that edge is a link to another navmesh
            for (var k = 0; k < 3; k++)
            {
                if (e[k] < 0) continue;
                (FormKey, int) n = ((int)t.Flags & (1 << k)) != 0
                    ? (e[k] < d.EdgeLinks.Count ? (d.EdgeLinks[e[k]].Mesh.FormKey, (int)d.EdgeLinks[e[k]].TriangleIndex) : default)
                    : (m, e[k]);
                if (n != default && seen.Add(n)) queue.Enqueue(n);
            }
        }
        return false;
    }

    // A new person's base of ours: everything from the template but the stats (a fixed level, decision 0035) and, for a
    // person the player fights, the AI data (aggressive and brave, so they attack and fight on).
    static FormKey Person(Ctx c, Built b, Ref r, string tpl)
    {
        var tk = Exists<INpcGetter>(c, tpl, "template");
        var t = c.Npcs.TryGetValue(tk, out var tw) ? tw.rec : c.Mod.Npcs.First(x => x.FormKey == tk);
        var k = c.Key($"npc:{r.Id}");
        var n = new Npc(k, SkyrimRelease.SkyrimSE) { EditorID = $"ARG_R_{Slug(r.Id)}_Base" };
        n.Template.SetTo(tk);
        n.Race.SetTo(t.Race.FormKey);
        n.Class.SetTo(t.Class.FormKey);
        const NpcConfiguration.TemplateFlag all = NpcConfiguration.TemplateFlag.Traits | NpcConfiguration.TemplateFlag.Factions | NpcConfiguration.TemplateFlag.SpellList
            | NpcConfiguration.TemplateFlag.AIData | NpcConfiguration.TemplateFlag.AIPackages | NpcConfiguration.TemplateFlag.ModelAnimation | NpcConfiguration.TemplateFlag.BaseData
            | NpcConfiguration.TemplateFlag.Inventory | NpcConfiguration.TemplateFlag.Script | NpcConfiguration.TemplateFlag.DefPackList | NpcConfiguration.TemplateFlag.AttackData
            | NpcConfiguration.TemplateFlag.Keywords;
        n.Configuration.TemplateFlags = r.Hostile ? all & ~NpcConfiguration.TemplateFlag.AIData : all;
        // the name the player sees is the form's: base data (the name among it) is then ours, not the template's
        if (So(r.Json, "name") is { } name) { n.Name = name; n.Configuration.TemplateFlags &= ~NpcConfiguration.TemplateFlag.BaseData; }
        // a fixed level: the form's, else the template's own
        short? lv = r.Json.TryGetProperty("level", out var fl) ? (short)fl.GetInt32() : null;
        if (lv != null) Label(c, $"level={r.Id}");
        n.Configuration.Level = new NpcLevel { Level = lv ?? (t.Configuration.Level is INpcLevelGetter l ? l.Level : Math.Max((short)1, t.Configuration.CalcMinLevel)) };
        n.Configuration.Flags = NpcConfiguration.Flag.AutoCalcStats | (t.Configuration.Flags & NpcConfiguration.Flag.Female);
        if (r.Hostile)
            n.AIData = new AIData { Aggression = Aggression.VeryAggressive, Confidence = Confidence.Brave, Responsibility = Responsibility.NoCrime, Assistance = Assistance.HelpsAllies };
        c.Mod.Npcs.Add(n);
        return k;
    }

    /// A ref of the load order made persistent in our plugin (an alias's forced ref must be), with its starting state.
    static void Persist(Ctx c, FormKey key, bool enabled, bool force = false)
    {
        var mine = Overrides.Placed(c.Mod, key);
        var wh = c.Wheres[key];
        if (mine == null)
        {
            var src = c.Placed[key].rec;
            var off = (src.MajorRecordFlagsRaw & 0x800) != 0;
            if ((src.MajorRecordFlagsRaw & 0x400) != 0 && off == !enabled && !force) return;
            mine = (IPlaced)((IMajorRecordGetter)src).DeepCopy();
            if (wh.Interior) Overrides.Interior(c.Mod, c.Mods, wh.Cell).Persistent.Add(mine);
            else Overrides.World(c.Mod, c.Mods, wh.World).TopCell!.Persistent.Add(mine);
        }
        else if (!wh.Interior)
        {
            // another step overrode it in its exterior cell: move that override to the world's persistent cell
            var world = Overrides.World(c.Mod, c.Mods, wh.World);
            if (!world.TopCell!.Persistent.Contains(mine))
            {
                foreach (var bl in world.SubCells) foreach (var sb in bl.Items) foreach (var cl in sb.Items) { cl.Temporary.Remove(mine); cl.Persistent.Remove(mine); }
                world.TopCell.Persistent.Add(mine);
            }
        }
        else
        {
            var cell = Overrides.Interior(c.Mod, c.Mods, wh.Cell);
            if (cell.Temporary.Remove(mine)) cell.Persistent.Add(mine);
        }
        mine.MajorRecordFlagsRaw = (mine.MajorRecordFlagsRaw | 0x400) & ~0x800 | (enabled ? 0 : 0x800);
    }

    // ---- the lines
    static readonly char[] Ends = ['.', '!', '?'];
    /// A line's words as responses: split at sentence ends into pieces of about 150 characters (a subtitle each).
    public static List<string> Pieces(string text)
    {
        var lines = new List<string>();
        foreach (var sentence in System.Text.RegularExpressions.Regex.Split(text.Trim(), @"(?<=[.!?])\s+"))
            if (lines.Count > 0 && lines[^1].Length + 1 + sentence.Length <= 150) lines[^1] += " " + sentence; else lines.Add(sentence);
        return lines;
    }

    static void Lines(Ctx c, Built b)
    {
        var lines = A(b.F, "lines").ToList();
        var byId = new Dictionary<string, JsonElement>();
        foreach (var l in lines) if (!byId.TryAdd(S(l, "id"), l)) throw c.No("unique-ids", $"two lines {S(l, "id")}");
        var talk = c.Mod.Quests.FirstOrDefault(x => x.EditorID == "ARG_Talk");
        var topics = new Dictionary<string, DialogTopic>();
        var infos = new Dictionary<string, DialogResponses>();
        // the owner of a line: the form's quest, or the always-running ARG_Talk for a line open only once the quest has
        // ended (a stopped quest's topics are never offered; GetStage still reads its last stage)
        Quest Owner(JsonElement l)
        {
            var first = I(l, "first_stage"); var last = I(l, "last_stage");
            if (!b.Endings.Any(e => e >= first && e <= last)) return b.Q;
            if (b.Endings.Min() > first) throw c.No("line-window", $"{S(l, "id")} is open before the first ending and into it");
            return talk ?? throw c.No("owner", $"{S(l, "id")} is open after the quest ends, and there is no ARG_Talk to hold it");
        }
        DialogTopic Topic(string key, string edid, Quest owner, Func<DialogTopic, DialogBranch?> branch)
        {
            if (topics.TryGetValue(key, out var t)) return t;
            t = new DialogTopic(c.Key($"dial:{b.Qid}:{key}"), SkyrimRelease.SkyrimSE) { EditorID = edid, Priority = 50 };
            t.Quest.SetTo(owner.FormKey);
            var br = branch(t);
            if (br != null) t.Branch.SetTo(br.FormKey);
            c.Mod.DialogTopics.Add(t);
            return topics[key] = t;
        }
        DialogBranch Branch(string key, string edid, Quest owner, DialogTopic start, DialogBranch.Flag flags)
        {
            var br = new DialogBranch(c.Key($"branch:{b.Qid}:{key}"), SkyrimRelease.SkyrimSE) { EditorID = edid, Category = DialogBranch.CategoryType.Player, Flags = flags };
            br.Quest.SetTo(owner.FormKey); br.StartingTopic.SetTo(start.FormKey);
            c.Mod.DialogBranches.Add(br);
            return br;
        }
        DialogTopic Hello(Quest owner)
        {
            var after = owner != b.Q;
            return Topic(after ? "hello-after" : "hello", b.Edid + (after ? "_HelloAfter" : "_Hello"), owner, t =>
            {
                t.Category = DialogTopic.CategoryEnum.Misc; t.Subtype = DialogTopic.SubtypeEnum.Hello; t.SubtypeName = new RecordType("HELO");
                return null;
            });
        }
        DialogResponses Info(string name, JsonElement l, Quest owner, bool begin)
        {
            var id = S(l, "id");
            var info = new DialogResponses(c.Key($"{name}:{b.Qid}:{id}"), SkyrimRelease.SkyrimSE) { Flags = new DialogResponseFlags() };
            byte k = 1;
            foreach (var piece in Pieces(S(l, "text"))) info.Responses.Add(new DialogResponse { Text = piece, ResponseNumber = k++, Emotion = Emotion.Neutral });
            var speaker = PlacedRef(c, b, S(l, "speaker"), $"line {id}'s speaker");
            if (!b.Refs[S(l, "speaker")].Npc) throw c.No("speaker", $"line {id}: {S(l, "speaker")} is not a person");
            info.Conditions.Add(Cond(new GetIsReferenceConditionData { Target = { Link = { FormKey = speaker } } }, CompareOperator.EqualTo, 1));
            info.Conditions.Add(Cond(StageData(b.Q.FormKey), CompareOperator.GreaterThanOrEqualTo, I(l, "first_stage")));
            info.Conditions.Add(Cond(StageData(b.Q.FormKey), CompareOperator.LessThanOrEqualTo, I(l, "last_stage")));
            foreach (var cd in A(l, "conditions")) info.Conditions.Add(Condition(c, b, cd));
            var rows = A(l, "results").SelectMany(res => Result(c, b, res, b.Q.FormKey)).ToList();
            if (rows.Count > MaxRows) throw c.No("result-limits", $"line {id} holds {rows.Count} rows, over {MaxRows}");
            var script = new ScriptEntry { Name = LineScript };
            script.Properties.AddRange(Arrays(rows));
            script.Properties.Add(new ScriptObjectProperty { Name = "Owner", Object = new FormLink<ISkyrimMajorRecordGetter>(b.Q.FormKey) });
            script.Properties.Add(new ScriptStringProperty { Name = "Line", Data = id });
            script.Properties.Add(new ScriptBoolProperty { Name = "Written", Data = B(l, "written") });
            info.VirtualMachineAdapter = new DialogResponsesAdapter { Scripts = { script } };
            if (rows.Count > 0)
            {
                var frag = new ScriptFragment { ScriptName = LineScript, FragmentName = begin ? "Fragment_Begin" : "Fragment_End" };
                info.VirtualMachineAdapter.ScriptFragments = begin ? new ScriptFragments { FileName = LineScript, OnBegin = frag } : new ScriptFragments { FileName = LineScript, OnEnd = frag };
            }
            infos[id] = info;
            return info;
        }
        // the questions first, so each answer joins its question's branch
        var answerBranch = new Dictionary<string, (DialogBranch br, Quest owner)>();
        foreach (var l in lines)
        {
            var id = S(l, "id"); var kind = S(l, "kind"); var owner = Owner(l);
            if (kind is "topic")
            {
                var prompt = So(l, "prompt") ?? throw c.No("schema", $"topic line {id} has no prompt");
                var key = $"topic:{(owner == b.Q ? "" : "after:")}{prompt}";
                DialogBranch? made = null;
                var t = Topic(key, $"{b.Edid}_T_{Sha(key)[..8]}", owner, t =>
                {
                    t.Name = prompt; t.Category = DialogTopic.CategoryEnum.Topic; t.Subtype = DialogTopic.SubtypeEnum.Custom; t.SubtypeName = new RecordType("CUST");
                    return made = Branch(key, $"{b.Edid}_B_{Sha(key)[..8]}", owner, t, DialogBranch.Flag.TopLevel);
                });
                t.Responses.Add(Info("info", l, owner, false));
                foreach (var a in A(l, "answers"))
                    if (!answerBranch.ContainsKey(a.GetString()!)) answerBranch[a.GetString()!] = (c.Mod.DialogBranches.First(x => x.FormKey == t.Branch.FormKey), owner);
            }
        }
        foreach (var l in lines)
        {
            var id = S(l, "id"); var kind = S(l, "kind"); var owner = Owner(l);
            switch (kind)
            {
                case "topic": break;
                case "answer":
                {
                    if (!answerBranch.TryGetValue(id, out var ab)) throw c.No("answer", $"answer line {id} is no question's answer");
                    var prompt = So(l, "prompt") ?? throw c.No("schema", $"answer line {id} has no prompt");
                    var key = $"answer:{ab.br.EditorID}:{prompt}";
                    var t = Topic(key, $"{b.Edid}_A_{Sha(key)[..8]}", ab.owner, t =>
                    {
                        t.Name = prompt; t.Category = DialogTopic.CategoryEnum.Topic; t.Subtype = DialogTopic.SubtypeEnum.Custom; t.SubtypeName = new RecordType("CUST");
                        return ab.br;
                    });
                    t.Responses.Add(Info("info", l, ab.owner, false));
                    break;
                }
                case "greeting":
                    Hello(owner).Responses.Add(Info("info", l, owner, false));
                    break;
                case "speaks_first":
                {
                    if (owner != b.Q) throw c.No("speaks-first", $"{id} is open after the quest ends");
                    var key = $"speaks-first:{id}";
                    var t = Topic(key, $"{b.Edid}_SF_{Sha(key)[..8]}", owner, t =>
                    {
                        t.Category = DialogTopic.CategoryEnum.Topic; t.Subtype = DialogTopic.SubtypeEnum.Custom; t.SubtypeName = new RecordType("CUST");
                        return Branch(key, $"{b.Edid}_SFB_{Sha(key)[..8]}", owner, t, DialogBranch.Flag.Blocking);
                    });
                    if (t.Responses.Count > 0) throw c.No("speaks-first", $"{id}: one speaks-first line per topic");
                    t.Responses.Add(Info("info", l, owner, true));
                    Hello(owner).Responses.Add(Info("hello", l, owner, true));
                    ForceGreet(c, b, l, t);
                    break;
                }
                default: throw c.No("vocabulary", $"line {id}: no kind {kind}");
            }
        }
        foreach (var l in lines)
            foreach (var a in A(l, "answers"))
            {
                if (!infos.ContainsKey(a.GetString()!) || !byId.TryGetValue(a.GetString()!, out var al) || S(al, "kind") != "answer") throw c.No("refs-exist", $"line {S(l, "id")}: its answer {a.GetString()} is not an answer line");
                var target = topics.Values.First(t => t.Responses.Contains(infos[a.GetString()!]));
                if (!infos[S(l, "id")].LinkTo.Any(x => x.FormKey == target.FormKey)) infos[S(l, "id")].LinkTo.Add(target.ToLink());
            }
        if (b.Q.Aliases.Count(a => a.PackageData.Count > 0) > 1) throw c.No("speaks-first", "more than one person speaks first");
    }

    /// The one package a quest has: its speaks-first person walks up and opens the line (a copy of vanilla's
    /// MS05InductionForcegreet, template ForceGreet), while the line is open, never in combat or through a load door.
    static void ForceGreet(Ctx c, Built b, JsonElement l, DialogTopic topic)
    {
        var r = b.Refs[S(l, "speaker")];
        if (r.A.PackageData.Count > 0) throw c.No("speaks-first", $"{r.Id} speaks first twice");
        // he walks up to the player: he stands on navmesh, and by a load door within the greeting's reach of where the player
        // comes out of it, with a walk over navmesh between
        // one standing where there is no navmesh greets only from a step from where the player comes out of a load door
        if (r.Standing && r.Door == null) throw c.No("speaks-first", $"{r.Id} stands where there is no navmesh, so cannot walk up to the player");
        if (r.Fresh && r.Door is { } dr && c.Wheres.TryGetValue(r.Placed, out var wh))
        {
            var dist = MathF.Sqrt((wh.Pos.X - dr.arrival.X) * (wh.Pos.X - dr.arrival.X) + (wh.Pos.Y - dr.arrival.Y) * (wh.Pos.Y - dr.arrival.Y));
            if (r.Standing)
            {
                if (dist > DoorStand) throw c.No("speaks-first", $"{r.Id} stands where there is no navmesh, {dist:F0} units from where the player comes out of {dr.door}, beyond {DoorStand}");
                Console.WriteLine($"questform {c.Q}: {r.Id} speaks first from {wh.Pos.X:F0},{wh.Pos.Y:F0},{wh.Pos.Z:F0}, {dist:F0} units from where the player comes out of {dr.door} ({dr.arrival.X:F0},{dr.arrival.Y:F0},{dr.arrival.Z:F0}), facing it; no navmesh there, so he greets without walking");
            }
            else
            {
                // the player's arrival on navmesh: then a walk must join it to him; with no navmesh there, he stands on the
                // nearest navmesh at that level (Spot) and greets once the player has walked within reach
                var arrivalOn = NearestOn(c, Neighbours(c.Grid, wh.Cell, wh.World, wh.Interior, dr.arrival), dr.arrival, 100, take: false) is { dist: <= 150 };
                if (arrivalOn && !Walk(c, (wh.World, wh.Cell, wh.Interior), dr.arrival, wh.Pos)) throw c.No("speaks-first", $"{r.Id}: no walk over navmesh from where the player comes out of {dr.door} to his spot");
                if (arrivalOn && dist > GreetReach) throw c.No("speaks-first", $"{r.Id} stands {dist:F0} units from where the player comes out of {dr.door}, beyond the greeting's {GreetReach}");
                Console.WriteLine($"questform {c.Q}: {r.Id} speaks first from {wh.Pos.X:F0},{wh.Pos.Y:F0},{wh.Pos.Z:F0}, {dist:F0} units from where the player comes out of {dr.door} ({dr.arrival.X:F0},{dr.arrival.Y:F0},{dr.arrival.Z:F0}), facing it; "
                    + (arrivalOn ? "a walk over navmesh joins them" : $"no navmesh where the player comes out, so he greets once the player is within {GreetReach} of him"));
            }
        }
        var src = c.Mods[0].Packages.FirstOrDefault(p => p.FormKey == ForceGreetCopy) ?? throw c.No("speaks-first", "vanilla MS05InductionForcegreet is not in the load order");
        var p = src.Duplicate(c.Key($"pack:{b.Qid}:{S(l, "id")}"));
        p.EditorID = $"{b.Edid}_ForceGreet";
        p.OwnerQuest.SetTo(b.Q.FormKey);
        p.Conditions.Clear();
        p.Conditions.Add(Cond(StageData(b.Q.FormKey), CompareOperator.GreaterThanOrEqualTo, I(l, "first_stage")));
        p.Conditions.Add(Cond(StageData(b.Q.FormKey), CompareOperator.LessThanOrEqualTo, I(l, "last_stage")));
        p.Conditions.Add(Cond(new IsInCombatConditionData(), CompareOperator.EqualTo, 0));
        p.Conditions.Add(Cond(new IsPlayerMovingIntoNewSpaceConditionData(), CompareOperator.EqualTo, 0));
        ((PackageDataTopic)p.Data[7]).Topics.Clear();
        ((PackageDataTopic)p.Data[7]).Topics.Add(new TopicReference { Reference = { FormKey = topic.FormKey } });
        var wait = new LocationTarget(); wait.Link.SetTo(r.Placed);
        ((PackageDataLocation)p.Data[8]).Location = new LocationTargetRadius { Target = wait, Radius = 150 };
        ((PackageDataLocation)p.Data[62]).Location.Radius = GreetReach;   // the player within 500 of the package start greets
        ((PackageDataLocation)p.Data[75]).Location.Radius = 300;   // he walks up to 300 from the player
        c.Mod.Packages.Add(p);
        r.A.PackageData.Add(p.ToLink());
    }

    // ---- conditions
    static ConditionFloat Cond(ConditionData d, CompareOperator op, float v) => new() { CompareOperator = op, ComparisonValue = v, Data = d };
    static GetStageConditionData StageData(FormKey q) { var d = new GetStageConditionData(); d.Quest.Link.SetTo(q); return d; }
    static T OnPlayer<T>(T d) where T : ConditionData { d.RunOnType = Mutagen.Bethesda.Skyrim.Condition.RunOnType.Reference; d.Reference.SetTo(Player); return d; }
    static T On<T>(T d, FormKey r) where T : ConditionData { d.RunOnType = Mutagen.Bethesda.Skyrim.Condition.RunOnType.Reference; d.Reference.SetTo(r); return d; }
    static readonly Dictionary<string, CompareOperator> Ops = new() { ["="] = CompareOperator.EqualTo, ["!="] = CompareOperator.NotEqualTo, ["<"] = CompareOperator.LessThan,
        ["<="] = CompareOperator.LessThanOrEqualTo, [">"] = CompareOperator.GreaterThan, [">="] = CompareOperator.GreaterThanOrEqualTo };
    public static CompareOperator Negate(CompareOperator o) => o switch
    {
        CompareOperator.EqualTo => CompareOperator.NotEqualTo, CompareOperator.NotEqualTo => CompareOperator.EqualTo,
        CompareOperator.GreaterThanOrEqualTo => CompareOperator.LessThan, CompareOperator.LessThan => CompareOperator.GreaterThanOrEqualTo,
        CompareOperator.GreaterThan => CompareOperator.LessThanOrEqualTo, _ => CompareOperator.GreaterThan,
    };
    static ConditionFloat Condition(Ctx c, Built b, JsonElement cd)
    {
        var w = S(cd, "is");
        var (d, op, v) = w switch
        {
            "stage_is" => ((ConditionData)StageData(QuestKey(c, S(cd, "quest"))), CompareOperator.EqualTo, (float)I(cd, "stage")),
            "stage_at_least" => (StageData(QuestKey(c, S(cd, "quest"))), CompareOperator.GreaterThanOrEqualTo, I(cd, "stage")),
            "stage_done" => (Done(QuestKey(c, S(cd, "quest")), I(cd, "stage")), CompareOperator.EqualTo, 1),
            "number_compare" => (Glob(Number(c, S(cd, "number"))), Ops.TryGetValue(S(cd, "op"), out var o) ? o : throw c.No("vocabulary", $"no op {S(cd, "op")}"), (float)cd.GetProperty("value").GetDouble()),
            "in_faction" => (OnPlayer(InFaction(Faction(c, S(cd, "faction")))), CompareOperator.EqualTo, 1),
            "rank_at_least" => (OnPlayer(FactionRank(Faction(c, S(cd, "faction")))), CompareOperator.GreaterThanOrEqualTo, I(cd, "rank")),
            "item_count_at_least" => (OnPlayer(Count(Item(c, b, S(cd, "item")))), CompareOperator.GreaterThanOrEqualTo, I(cd, "count")),
            "gold_at_least" => (OnPlayer(Count(Gold)), CompareOperator.GreaterThanOrEqualTo, I(cd, "gold")),
            "skill_at_least" => (OnPlayer(new GetActorValueConditionData { ActorValue = SkillOf(c, S(cd, "skill")) }), CompareOperator.GreaterThanOrEqualTo, I(cd, "value")),
            "alive" => (On(new GetDeadConditionData(), PersonRef(c, b, S(cd, "ref"), "alive")), CompareOperator.EqualTo, 0),
            "dead" => (On(new GetDeadConditionData(), PersonRef(c, b, S(cd, "ref"), "dead")), CompareOperator.EqualTo, 1),
            "speaker_is" => (IsRef(PersonRef(c, b, S(cd, "ref"), "speaker_is")), CompareOperator.EqualTo, 1),
            "regard_at_least" => (On(Rank(), PersonRef(c, b, S(cd, "ref"), "regard_at_least")), CompareOperator.GreaterThanOrEqualTo, I(cd, "value")),
            "race_is" => (OnPlayer(RaceIs(Race(c, S(cd, "value")))), CompareOperator.EqualTo, 1),
            "sex_is" => (OnPlayer(new GetIsSexConditionData { MaleFemaleGender = S(cd, "value") switch { "male" => MaleFemaleGender.Male, "female" => MaleFemaleGender.Female, var x => throw c.No("vocabulary", $"no sex {x}") } }), CompareOperator.EqualTo, 1),
            "spoken_before" => (new GetTalkedToPCConditionData(), CompareOperator.EqualTo, 1),
            "not_spoken_before" => (new GetTalkedToPCConditionData(), CompareOperator.EqualTo, 0),
            _ => throw c.No("vocabulary", $"no condition {w}"),
        };
        if (B(cd, "not"))
        {
            if (w == "number_compare") throw c.No("vocabulary", "number_compare is never negated: its op says it");
            op = Negate(op);
        }
        return Cond(d, op, v);
    }
    static GetStageDoneConditionData Done(FormKey q, int s) { var d = new GetStageDoneConditionData { Stage = s }; d.Quest.Link.SetTo(q); return d; }
    static GetGlobalValueConditionData Glob(FormKey g) { var d = new GetGlobalValueConditionData(); d.Global.Link.SetTo(g); return d; }
    static GetInFactionConditionData InFaction(FormKey f) { var d = new GetInFactionConditionData(); d.Faction.Link.SetTo(f); return d; }
    static GetFactionRankConditionData FactionRank(FormKey f) { var d = new GetFactionRankConditionData(); d.Faction.Link.SetTo(f); return d; }
    static GetItemCountConditionData Count(FormKey i) { var d = new GetItemCountConditionData(); d.ItemOrList.Link.SetTo(i); return d; }
    static GetIsReferenceConditionData IsRef(FormKey r) { var d = new GetIsReferenceConditionData(); d.Target.Link.SetTo(r); return d; }
    static GetRelationshipRankConditionData Rank() { var d = new GetRelationshipRankConditionData(); d.TargetNpc.Link.SetTo(Player); return d; }
    static GetIsRaceConditionData RaceIs(FormKey r) { var d = new GetIsRaceConditionData(); d.Race.Link.SetTo(r); return d; }

    // ---- triggers
    static void Triggers(Ctx c, Built b)
    {
        var seen = new HashSet<string>();
        foreach (var t in A(b.F, "triggers"))
        {
            var id = S(t, "id"); var kind = S(t, "kind"); var pre = I(t, "prerequisite"); var sets = I(t, "sets");
            if (!seen.Add(id)) throw c.No("unique-ids", $"two triggers {id}");
            if (kind == "quest_stage")
            {
                var other = S(t, "quest");
                if (!c.Quests.TryGetValue(other, out var o)) throw c.No("trigger", $"{id}: {other} is not built from a form, so its stage cannot move this quest");
                Add(o.From, I(t, "quest_stage"), new Row(Op.IfStageDone, b.Q.FormKey, pre), new Row(Op.SetStageIfRunning, b.Q.FormKey, sets));
                b.Labels.Add($"trigger={id}|quest_stage|{other}|{I(t, "quest_stage")}|{pre}|{sets}|");
                continue;
            }
            var r = RefOf(c, b, S(t, "ref"), $"trigger {id}");
            // takes of one thing, or deaths of one person, that set one stage from several stages are one script, from the
            // lowest of them (a later one is reached through it: the script's prerequisite is then done)
            int? until = t.TryGetProperty("until", out var ut) ? ut.GetInt32() : null;
            var untilLabel = until is { } u0 ? $"until={u0}|" : "";
            if (kind is "take" or "death" && A(b.F, "triggers").Any(o => S(o, "kind") == kind && S(o, "ref") == r.Id && I(o, "sets") == sets && I(o, "prerequisite") < pre
                && (o.TryGetProperty("until", out var ou) ? ou.GetInt32() : (int?)null) == until))
            {
                b.Labels.Add($"trigger={id}|{kind}|{r.Id}|{untilLabel}{pre}|{sets}|{(B(t, "choice") ? "choice" : "")}");
                continue;
            }
            // a take, use or death with an `until`: it moves the quest only while the quest's stage is below that stage
            // (ARG_AliasEffects on the event vanilla's script for the kind hooks: IfStageDone the prerequisite,
            // IfStageAtMost until - 1, then the stage, set while the quest runs)
            if (until is { } u)
            {
                if (u <= pre) throw c.No("trigger", $"{id}: its until {u} is not after its prerequisite {pre}");
                var on = kind switch
                {
                    "death" => r.Npc ? 0 : throw c.No("trigger", $"{id}: only a person dies"),
                    "take" => r.Kind == "thing" ? AliasOnTake : throw c.No("trigger", $"{id}: only a thing is taken"),
                    "use" => r.Created ? throw c.No("trigger", $"{id}: a thing made in a container is taken, not used")
                        : c.Mods.Any(m => m.Books.Any(x => x.FormKey == r.Base)) ? AliasOnRead : AliasOnActivate,
                    _ => throw c.No("vocabulary", $"no trigger kind {kind}"),
                };
                var ue = new ScriptEntry { Name = AliasScript };
                ue.Properties.AddRange(Arrays([new Row(Op.IfStageDone, b.Q.FormKey, pre), new Row(Op.IfStageAtMost, b.Q.FormKey, u - 1), new Row(Op.SetStageIfRunning, b.Q.FormKey, sets)]));
                if (on != 0) ue.Properties.Add(QuestKit.Int("On", on));
                AddAliasScript(c, b, r, ue, id);
                b.Labels.Add($"trigger={id}|{kind}|{r.Id}|{untilLabel}{pre}|{sets}|{(B(t, "choice") ? "choice" : "")}");
                continue;
            }
            ScriptEntry s = kind switch
            {
                "take" => r.Kind == "thing" ? QuestKit.Script(TakeScript, QuestKit.Obj("myQST", b.Q.FormKey), QuestKit.Int("preReqStage", pre), QuestKit.Int("StageToSet", sets))
                    : throw c.No("trigger", $"{id}: only a thing is taken"),
                "use" => r.Created ? throw c.No("trigger", $"{id}: a thing made in a container is taken, not used")
                    : c.Mods.Any(m => m.Books.Any(x => x.FormKey == r.Base)) ? QuestKit.Script(ReadScript, QuestKit.Int("preReqStage", pre), QuestKit.Int("StageToSet", sets))
                    : QuestKit.Script(UseScript, QuestKit.Int("stage", sets), QuestKit.Int("prereqStageOPT", pre), QuestKit.Int("TriggerType", 0)),
                "death" => r.Npc ? QuestKit.OnDeath(b.Q, pre, sets) : throw c.No("trigger", $"{id}: only a person dies"),
                _ => throw c.No("vocabulary", $"no trigger kind {kind}"),
            };
            if (kind == "take" && b.AliasScripts.TryGetValue(r.Alias, out var have) && have.Any(x => x.Name == TakeScript) && !r.Created
                && Overrides.Placed(c.Mod, r.Placed) is PlacedObject po && r.Fresh)
            {
                // a second take of a placed thing from another stage: vanilla's reference script, on the thing itself
                po.VirtualMachineAdapter ??= new VirtualMachineAdapter();
                if (po.VirtualMachineAdapter.Scripts.Any(x => x.Name == TakeRefScript)) throw c.No("trigger", $"{id}: {r.Id} is taken from three stages");
                po.VirtualMachineAdapter.Scripts.Add(QuestKit.Script(TakeRefScript, QuestKit.Obj("myQST", b.Q.FormKey), QuestKit.Int("preReqStage", pre), QuestKit.Int("StageToSet", sets)));
            }
            else AddAliasScript(c, b, r, s, id);
            b.Labels.Add($"trigger={id}|{kind}|{r.Id}|{pre}|{sets}|{(B(t, "choice") ? "choice" : "")}");
        }
        // a death trigger open from the start: a death before the quest began moves it as it starts (the start check)
        foreach (var t in A(b.F, "triggers").Where(t => S(t, "kind") == "death" && I(t, "prerequisite") == b.Start))
            Add(b.Own, b.Start, new Row(Op.FailIfDead, b.Refs[S(t, "ref")].Placed, I(t, "sets")));
        // who must live, outside the mortal watch: vanilla's death script sets the failed ending from any stage; within a
        // window, ARG_AliasEffects with the window's guards
        foreach (var m in A(b.F, "must_live"))
        {
            if (B(m, "main_message")) { if (b.Kind == "minor") throw c.No("main-message", $"{S(m, "ref")}: a minor quest's death shows no message"); continue; }
            var r = b.Refs[S(m, "ref")];
            if (!m.TryGetProperty("from", out _) && !m.TryGetProperty("to", out _))
                AddAliasScript(c, b, r, QuestKit.OnDeath(b.Q, -1, I(m, "fail_stage")), $"must live {r.Id}");
            else
            {
                var e = new ScriptEntry { Name = AliasScript };
                e.Properties.AddRange(Arrays([.. Window(b.Q.FormKey, m), new Row(Op.SetStageIfRunning, b.Q.FormKey, I(m, "fail_stage"))]));
                AddAliasScript(c, b, r, e, $"must live {r.Id}");
            }
        }
    }
    /// Whether a who-must-live row's window (from, to; either may be left out) holds the stage.
    static bool Within(JsonElement m, int stage) =>
        (!m.TryGetProperty("from", out var f) || stage >= f.GetInt32()) && (!m.TryGetProperty("to", out var t) || stage <= t.GetInt32());
    /// The guards of a who-must-live window: the next row runs only from its first stage up to its last.
    static List<Row> Window(FormKey q, JsonElement m)
    {
        var l = new List<Row>();
        if (m.TryGetProperty("from", out var f)) l.Add(new Row(Op.IfStageDone, q, f.GetInt32()));
        if (m.TryGetProperty("to", out var t)) l.Add(new Row(Op.IfStageAtMost, q, t.GetInt32()));
        return l;
    }
    static void AddAliasScript(Ctx c, Built b, Ref r, ScriptEntry s, string what)
    {
        if (!b.AliasScripts.TryGetValue(r.Alias, out var l)) b.AliasScripts[r.Alias] = l = [];
        if (l.Any(x => x.Name == s.Name)) throw c.No("trigger", $"{what}: {r.Id} already carries {s.Name} (one trigger of a kind per ref)");
        l.Add(s);
    }

    // ---- the places: an interior the form names otherwise than the load order's winning cell is named so in our plugin
    // (what the player reads on its doors and its loading screen); a place outdoors keeps its map markers' names
    static void Places(Ctx c, Built b)
    {
        if (!b.F.TryGetProperty("places", out var places)) return;
        foreach (var pl in places.EnumerateObject())
        {
            if (!B(pl.Value, "interior")) continue;
            var key = FormKey.Factory(pl.Name); var name = S(pl.Value, "name");
            // one cell, one name: a cell two quests name takes one neutral name true of all of it, in both records
            if (c.CellNames.TryGetValue(key, out var had) && had.Name != name)
                throw c.No("place", $"cell {pl.Name} is \"{name}\" here and \"{had.Name}\" in {had.Quest}: give both records one name for it");
            c.CellNames.TryAdd(key, (c.Q, name));
            c.CellWin ??= Survey.Winners<ICellGetter>(c.Mods);
            var win = c.CellWin.TryGetValue(key, out var w) ? w.rec : throw c.No("place", $"{pl.Name} is no cell of the load order");
            var mine = c.Mod.Cells.Records.SelectMany(x => x.SubBlocks).SelectMany(x => x.Cells).FirstOrDefault(x => x.FormKey == key);
            var now = mine?.Name?.String ?? win.Name?.String;
            // the census's own name with its settlement after it ("House, Lilmoth") is how the paper game tells places
            // apart; the cell keeps its name. A name of its own (a record's placeName) is written
            if (now == name || (now != null && name.StartsWith(now + ", ", StringComparison.Ordinal))) continue;
            Overrides.Interior(c.Mod, c.Mods, key).Name = name;
            Console.WriteLine($"questform {c.Q}: cell {key} named \"{name}\" (was \"{now}\")");
        }
    }

    // ---- the mortal watch: one always-running quest holding every person a main or faction quest cannot go on without
    static void Watch(Ctx c)
    {
        var rows = c.Quests.Values.SelectMany(b => A(b.F, "must_live").Where(m => B(m, "main_message")).Select(m => (b, m)))
            .OrderBy(x => x.b.Qid, StringComparer.Ordinal).ThenBy(x => S(x.m, "ref"), StringComparer.Ordinal).ToList();
        if (rows.Count == 0) return;
        var w = new Quest(c.Key("watch"), SkyrimRelease.SkyrimSE)
        {
            EditorID = WatchId, Priority = 0, Type = Mutagen.Bethesda.Skyrim.Quest.TypeEnum.None,
            Flags = Mutagen.Bethesda.Skyrim.Quest.Flag.StartGameEnabled | Mutagen.Bethesda.Skyrim.Quest.Flag.RunOnce,
        };
        c.Mod.Quests.Add(w);
        var vm = new QuestAdapter();
        uint id = 0;
        foreach (var (b, m) in rows)
        {
            c.Q = b.Qid; c.Cur = b;
            var r = b.Refs[S(m, "ref")];
            var msg = c.Key("watchmsg:" + b.Kind);
            if (!c.Mod.Messages.Any(x => x.FormKey == msg))
                c.Mod.Messages.Add(new Message(msg, SkyrimRelease.SkyrimSE)
                {
                    EditorID = b.Kind == "main" ? "ARG_MortalWatchMain" : "ARG_MortalWatchFaction",
                    Description = b.Kind == "main" ? MainMessage : FactionMessage, Flags = Mutagen.Bethesda.Skyrim.Message.Flag.MessageBox,
                });
            var a = new QuestAlias { ID = id, Type = QuestAlias.TypeEnum.Reference, Name = $"{b.Qid}|{r.Id}", Flags = QuestAlias.Flag.AllowDisabled | QuestAlias.Flag.Optional };
            a.ForcedReference.SetTo(r.Placed);
            w.Aliases.Add(a);
            var s = new ScriptEntry { Name = AliasScript };
            s.Properties.AddRange(Arrays([new Row(Op.IfQuestOpen, b.Q.FormKey, 0), .. Window(b.Q.FormKey, m), new Row(Op.ShowMessage, msg, 0),
                .. Window(b.Q.FormKey, m), new Row(Op.SetStageIfRunning, b.Q.FormKey, I(m, "fail_stage"))]));
            if (So(m, "message") is { } given && given != (b.Kind == "main" ? MainMessage : FactionMessage)) throw c.No("message", $"{r.Id}: the death message is the {b.Kind} quests' own, not the form's");
            var f = new QuestFragmentAlias { Property = new ScriptObjectProperty { Name = "", Object = new FormLink<ISkyrimMajorRecordGetter>(w.FormKey), Alias = (short)id } };
            f.Scripts.Add(s);
            vm.Aliases.Add(f);
            id++;
        }
        w.VirtualMachineAdapter = vm;
    }

    // ---- the quest's script: every stage's rows in three arrays, a fragment per stage that has rows
    static void Finish(Ctx c, Built b)
    {
        var rows = new List<Row>(); var stages = new List<int>(); var from = new List<int>(); var to = new List<int>();
        foreach (var s in b.Q.Stages.Select(s => (int)s.Index).OrderBy(x => x))
        {
            var mine = b.Own.GetValueOrDefault(s) ?? [];
            // the start check first, then the stage's results and objectives, then others' rows, then the ending's
            // closing rows; Stop is always the last row
            var all = mine.Where(r => r.Op == Op.FailIfDead).Concat(mine.Where(r => r.Op != Op.FailIfDead))
                .Concat(b.From.GetValueOrDefault(s) ?? []).Concat(b.Tail.GetValueOrDefault(s) ?? []).ToList();
            if (b.Endings.Contains(s)) all.Add(new Row(Op.StopQuest, FormKey.Null, 0));
            if (all.Count == 0) continue;
            stages.Add(s); from.Add(rows.Count); rows.AddRange(all); to.Add(rows.Count);
        }
        foreach (var s in b.From.Keys.Concat(b.Own.Keys).Concat(b.Tail.Keys)) if (!b.Q.Stages.Any(x => x.Index == s)) throw c.No("stages-exist", $"rows for stage {s}, which is not a stage");
        // counted as rules.built_rows (the form's own rows) and check_set (with the rows other forms add) count them
        var added = b.From.Values.Sum(l => l.Count);
        if (rows.Count - added > MaxRows) throw c.No("result-limits", $"the stages hold {rows.Count - added} rows once built, over {MaxRows}");
        if (rows.Count > MaxRows) throw c.No("result-limits", $"its stages hold {rows.Count} rows once built with the rows other forms add, over {MaxRows}");
        var script = new ScriptEntry { Name = StagesScript };
        script.Properties.AddRange(Arrays(rows));
        script.Properties.Add(new ScriptIntListProperty { Name = "Stages", Data = stages.ToExtendedList() });
        script.Properties.Add(new ScriptIntListProperty { Name = "StageFrom", Data = from.ToExtendedList() });
        script.Properties.Add(new ScriptIntListProperty { Name = "StageTo", Data = to.ToExtendedList() });
        script.Properties.Add(new ScriptStringProperty { Name = "QuestId", Data = b.Qid });
        script.Properties.Add(new ScriptStringProperty { Name = "Kind", Data = b.Kind });
        script.Properties.Add(new ScriptStringListProperty { Name = "Labels", Data = b.Labels.ToExtendedList() });
        var vm = new QuestAdapter { FileName = StagesScript, Scripts = { script } };
        foreach (var s in stages) vm.Fragments.Add(new QuestScriptFragment { Stage = (ushort)s, StageIndex = 0, ScriptName = StagesScript, FragmentName = $"Fragment_{s}" });
        foreach (var (alias, scripts) in b.AliasScripts.OrderBy(x => x.Key))
        {
            var f = new QuestFragmentAlias { Property = new ScriptObjectProperty { Name = "", Object = new FormLink<ISkyrimMajorRecordGetter>(b.Q.FormKey), Alias = (short)alias } };
            f.Scripts.AddRange(scripts);
            vm.Aliases.Add(f);
        }
        b.Q.VirtualMachineAdapter = vm;
    }

    public static IEnumerable<ScriptProperty> Arrays(List<Row> rows) =>
    [
        new ScriptIntListProperty { Name = "Op", Data = rows.Select(r => r.Op).ToExtendedList() },
        new ScriptObjectListProperty { Name = "What", Objects = rows.Select(r => new ScriptObjectProperty { Object = new FormLink<ISkyrimMajorRecordGetter>(r.What) }).ToExtendedList() },
        new ScriptFloatListProperty { Name = "Num", Data = rows.Select(r => r.Num).ToExtendedList() },
    ];
}

// Nobody is essential or protected (docs/research/skyrim/quest-form-engine-facts.md §3): at the end of the seed, every
// person of ours, every base a person placed by us or by Black Marsh & Valenwood takes those flags from (through Use
// Base Data templates), and every alias of a quest of ours is cleared of both. questcheck's `mortal` reads it back.
static class Mortality
{
    const NpcConfiguration.Flag Both = NpcConfiguration.Flag.Essential | NpcConfiguration.Flag.Protected;
    const QuestAlias.Flag AliasBoth = QuestAlias.Flag.Essential | QuestAlias.Flag.Protected;
    /// The plugins whose placed people are ours to keep mortal: ours, and Black Marsh & Valenwood's.
    public static bool Watched(ModKey m, ModKey ours) => m == ours || m.FileName.String.StartsWith("Black Marsh", StringComparison.OrdinalIgnoreCase)
        || m.FileName.String.StartsWith("Valenwood", StringComparison.OrdinalIgnoreCase);

    /// The record each placed person of the watched plugins takes Essential and Protected from: its base, or through a
    /// template with Use Base Data, the end of that chain.
    public static IEnumerable<FormKey> Holders(Func<FormKey, INpcGetter?> npc, IEnumerable<FormKey> bases)
    {
        foreach (var b in bases.Distinct())
        {
            var k = b; var guard = 0;
            while (npc(k) is { } n && n.Configuration.TemplateFlags.HasFlag(NpcConfiguration.TemplateFlag.BaseData) && !n.Template.IsNull && guard++ < 16)
                k = n.Template.FormKey;
            if (npc(k) != null) yield return k;
        }
    }

    public static void Clear(SkyrimMod mod, List<ISkyrimModGetter> mods)
    {
        var winners = Survey.Winners<INpcGetter>(mods);
        INpcGetter? Npc(FormKey k) => (INpcGetter?)mod.Npcs.FirstOrDefault(n => n.FormKey == k) ?? (winners.TryGetValue(k, out var w) ? w.rec : null);
        var bases = mods.Append(mod).SelectMany(m => m.EnumerateMajorRecords<IPlacedNpcGetter>().Where(r => Watched(r.FormKey.ModKey, mod.ModKey)).Select(r => r.Base.FormKey))
            .Concat(mod.Npcs.Select(n => n.FormKey));
        int npcs = 0, aliases = 0;
        foreach (var k in Holders(Npc, bases).Distinct())
        {
            var n = Npc(k)!;
            if ((n.Configuration.Flags & Both) == 0) continue;
            var mine = mod.Npcs.FirstOrDefault(x => x.FormKey == k);
            if (mine == null) { mine = (Npc)n.DeepCopy(); mod.Npcs.Add(mine); }
            mine.Configuration.Flags &= ~Both;
            npcs++;
        }
        foreach (var q in mod.Quests.Where(q => q.FormKey.ModKey == mod.ModKey))
            foreach (var a in q.Aliases.Where(a => a.Flags is { } f && (f & AliasBoth) != 0)) { a.Flags &= ~AliasBoth; aliases++; }
        Console.WriteLine($"mortality: {npcs} people's bases and {aliases} aliases cleared of Essential and Protected");
    }
}
