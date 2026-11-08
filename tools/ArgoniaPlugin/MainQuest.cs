using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Strings;
using Noggog;
using static NightReed;

// The opening act's first two main quests (Phase 4 part C): MQ01 "No Name on the Work Roll" (the new game: the barge hold
// at Lilmoth's dock, the march, the camp at Hereguard Plantation's paddy edge and the strike) and MQ03 "A Dead Prisoner's
// Use" (the camp at dawn, the Reed's house in Lilmoth, the dream in the empty hold), from quest.main.mq01 and
// quest.main.mq03. Journal and objective text from the story data rows; the lines from story/data/quest_lines/mq01.json
// and mq03.json. Every stage, trigger, condition and effect is a proven block's shape (docs/design/blocks.md); where the
// record names a shape with no proven block, the re-authoring is named where it is built (and in Phase 4's Measured):
// the three scenes (opening, strike, dream) have no written lines, so the march ends at a fire zone (10 -> 40), the strike
// is stage 40's fragment, and the dream ends at a door zone (40 -> 45 -> 90/91 on the oath global).
// MQ101's override starts ARG_MQ01 (Generate); ARG_Opening keeps its forms and never starts. Called after NightReed.
static class MainQuest
{
    static FormKey K(string k) => FormKey.Factory(k);
    static readonly FormKey World = K("23D689:Black Marsh.esm"), XMarker = K("00003B:Skyrim.esm"), Gold = K("00000F:Skyrim.esm"),
        Lockpick = K("00000A:Skyrim.esm"), TrigBase = K("099312:Skyrim.esm");
    // Hosts (measured 2026-11-08 with `ArgoniaPlugin nightreed`): the barge hold and its navmesh (main deck z 7010); Lilmoth's
    // Dock1 (1,-2) navmesh, the plank's foot at 5350,-7800; the camp cell (-1,0) navmesh at the paddy edge, deep water west
    // of x -4400 (land -336 at -4608,1024; -1336 at -5120,1024); the Reed's house (BM&V's sinking cabin: no navmesh where
    // the rooms are, a floor tilted 0.4 rad, top z = 7409 + (1301 - y) * 0.4228, read from its floor pieces).
    public static readonly FormKey HoldCell = K("0F9178:Black Marsh.esm"), HoldNav = K("0F9179:Black Marsh.esm"),
        DockNav = K("079823:Black Marsh.esm"), CampNav = K("07990E:Black Marsh.esm"), HouseCell = K("0FE7F7:Black Marsh.esm"),
        HoldDoor = K("0F92EC:Black Marsh.esm"), HoldDoorFar = K("0F9399:Black Marsh.esm"), PierDoor = K("005AB4:Black Marsh.esm"), HouseDoorOut = K("0FE95A:Black Marsh.esm"), DaintySload = K("07B91A:Skyrim.esm"),
        Welcome = K("03B21E:Black Marsh.esm");
    public static readonly string[] Valenwood = ["0BCC51:Valenwood.esp", "0F0F3E:Valenwood.esp"];
    public static float HouseFloor(float y) => MathF.Round(7409 + (1301 - y) * 0.4228f);
    // The camp's spots (x, y): the fire, the shed and the cutting at the far (north-east) end, the huts over the deep water
    // to the west under the plank boards, the shore below (south), the water's edge where the cell came in (north-west).
    public static readonly (float X, float Y) Fire = (-3750, 1300), Shed = (-3450, 1800), Cutting = (-3300, 1900), Huts1 = (-4500, 1450),
        Huts2 = (-4550, 1050), Planks = (-4350, 1250), Trap = (-4600, 1150), Shore = (-4050, 650), WaterEdge = (-4080, 2000);

    // MQ01 alias ids.
    public const uint A1WuleenHold = 0, A1UxHold = 1, A1Buys = 2, A1Courier = 3, A1WuleenMarch = 4, A1UxMarch = 5, A1DivesMarch = 6,
        A1FindsMarch = 7, A1Sal = 8, A1Deesh = 9, A1Leader = 10, A1Cutter1 = 11, A1Cutter2 = 12, A1Ties = 13, A1ZoneFire = 14,
        A1ZoneShed = 15, A1ZoneHuts = 16, A1Shore90 = 17, A1Shore91 = 18, A1Shore93 = 19, A1HoldDoor = 20, A1FireMark = 21, A1ZoneCamp = 22;
    // MQ03 alias ids.
    public const uint A3Officer = 0, A3Stranger = 1, A3Sap = 2, A3Nesh = 3, A3Salts = 4, A3Ties = 5, A3DoorZone = 6, A3Trap = 7;

    public static Quest Mq01 = null!, Mq03 = null!;
    public static PlacedObject StartMarker = null!;
    static P3Float HoldInside;  // the arrival spot inside the hold, in front of its stair door
    // record person id -> our base editor ids that speak for it (the read-back's speaker check)
    public static readonly Dictionary<string, string[]> Speakers = [];
    public sealed record Line(string Quest, string Topic, string Variant, string Edid, string Prompt, string[] Text, string? Script, string? Body);
    public static readonly List<Line> Lines = [];
    static readonly List<(string script, string body)> TifBodies = [];

    static string Root => Directory.Exists("story") ? "." : AppContext.BaseDirectory;
    public static JsonElement LinesOf(string code) => JsonDocument.Parse(File.ReadAllText(Path.Combine("story", "data", "quest_lines", code + ".json"))).RootElement;
    // Objectives: (stage, ord within the stage, text), indexed stage + ord (MQ03's 10, 11, 12 and 20, 21, 22).
    public static List<(int stage, int index, string text)> Objectives(string quest)
    {
        IEnumerable<JsonElement> Rows(string t) => File.ReadLines(Path.Combine("story", "data", "db", t + ".jsonl")).Where(l => l.Trim().Length > 0).Select(l => JsonDocument.Parse(l).RootElement);
        var ids = Rows("quest_stage").Where(r => r.GetProperty("quest_id").GetString() == quest).ToDictionary(r => r.GetProperty("ord").GetInt32(), r => r.GetProperty("id").GetInt32());
        return Rows("quest_objective").Where(r => r.GetProperty("quest_id").GetString() == quest)
            .Select(r => { var s = ids[r.GetProperty("stages_ord").GetInt32()]; return (s, s + r.GetProperty("ord").GetInt32(), r.GetProperty("objective_text").GetString()!); }).ToList();
    }

    sealed class Ctx(SkyrimMod mod, List<ISkyrimModGetter> mods)
    {
        public readonly SkyrimMod Mod = mod;
        public readonly List<ISkyrimModGetter> Mods = mods;
        public readonly Worldspace World = mod.Worldspaces.First(w => w.FormKey == MainQuest.World);
        public readonly Snapper Snap = new(mods);
        public readonly Dictionary<FormKey, (INpcGetter rec, ModKey from)> Npcs = Survey.Winners<INpcGetter>(mods);
        public readonly Dictionary<FormKey, (IPlacedGetter rec, ModKey from)> Placed = Survey.Winners<IPlacedGetter>(mods);
        public readonly Dictionary<FormKey, (ICellGetter rec, ModKey from)> Cells = Survey.Winners<ICellGetter>(mods);
        public float Land(float x, float y) => Surface.Land(Mods, MainQuest.World, x, y) ?? throw new InvalidOperationException($"no land at {x},{y}");

        const NpcConfiguration.TemplateFlag Looks = NpcConfiguration.TemplateFlag.Traits | NpcConfiguration.TemplateFlag.SpellList
            | NpcConfiguration.TemplateFlag.ModelAnimation | NpcConfiguration.TemplateFlag.AttackData | NpcConfiguration.TemplateFlag.Keywords
            | NpcConfiguration.TemplateFlag.Inventory;
        // W-npc / W-fixed: our base templated for looks (sex and face come with Traits, so the template is of the person's
        // sex and race); a fixed level (decision 0035); no packages of its own (alias packages only).
        public Npc Base(string id, string name, string tpl, short level, NpcConfiguration.Flag extra, Aggression aggression = Aggression.Unaggressive)
        {
            var t = Npcs[K(tpl)].rec;
            var n = Mod.Npcs.AddNew(id);
            n.Name = name; n.Template.SetTo(t.FormKey); n.Race.SetTo(t.Race.FormKey); n.Class.SetTo(t.Class.FormKey);
            n.Configuration.TemplateFlags = Looks;
            n.Configuration.Level = new NpcLevel { Level = level };
            n.Configuration.Flags = NpcConfiguration.Flag.AutoCalcStats | (t.Configuration.Flags & NpcConfiguration.Flag.Female) | extra;
            n.AIData = new AIData { Aggression = aggression, Confidence = Confidence.Average, Responsibility = Responsibility.NoCrime, Assistance = Assistance.HelpsNobody };
            n.Voice.SetTo(t.Voice.FormKey);
            return n;
        }
        public PlacedObject Marker(string id, P3Float p, FormKey? baseKey = null, int flags = 0x400, PlacedObject? parent = null, bool opposite = false)
        {
            var r = new PlacedObject(Mod.GetNextFormKey(), SkyrimRelease.SkyrimSE)
            { EditorID = id, Base = new FormLinkNullable<IPlaceableObjectGetter>(baseKey ?? XMarker), MajorRecordFlagsRaw = flags, Placement = new Placement { Position = p } };
            if (parent != null) Parent(r, parent, opposite);
            return r;
        }
        public static void Parent(IPlaced r, PlacedObject parent, bool opposite = false)
        {
            var e = new EnableParent { Flags = opposite ? EnableParent.Flag.SetEnableStateToOppositeOfParent : 0 };
            e.Reference.SetTo(parent.FormKey);
            switch (r) { case PlacedObject o: o.EnableParent = e; break; case PlacedNpc n: n.EnableParent = e; break; }
        }
        public PlacedNpc Actor(string id, Npc b, P3Float p, PlacedObject? parent = null)
        {
            var r = new PlacedNpc(Mod.GetNextFormKey(), SkyrimRelease.SkyrimSE) { EditorID = id, MajorRecordFlagsRaw = 0x400, Placement = new Placement { Position = p } };
            r.Base.SetTo(b.FormKey);
            if (parent != null) Parent(r, parent);
            return r;
        }
        // TR-zone: the vanilla set-stage box, gated by its prerequisite stage only.
        public PlacedObject Zone(string id, P3Float at, P3Float half, Quest q, int prereq, int stage, PlacedObject? parent = null)
        {
            var tpl = Mods[0].EnumerateMajorRecords<IPlacedObjectGetter>().First(r => r.Base.FormKey == TrigBase && r.Primitive != null);
            var z = new PlacedObject(Mod.GetNextFormKey(), SkyrimRelease.SkyrimSE)
            {
                EditorID = id, MajorRecordFlagsRaw = 0x400, Placement = new Placement { Position = at }, Primitive = tpl.Primitive!.DeepCopy(),
                VirtualMachineAdapter = new VirtualMachineAdapter { Scripts = { Script("defaultSetStageTrigScript", Obj("myQuest", q.FormKey), Int("prereqStageOPT", prereq), Int("stage", stage)) } },
            };
            z.Primitive.Bounds = half;
            z.Base.SetTo(TrigBase);
            if (parent != null) Parent(z, parent);
            return z;
        }
        // An interior cell's override in our plugin (no refs copied), found or added.
        public Cell Interior(FormKey k)
        {
            foreach (var b in Mod.Cells.Records) foreach (var sb in b.SubBlocks) foreach (var c in sb.Cells) if (c.FormKey == k) return c;
            var id = k.ID; var bn = (int)(id % 10); var sn = (int)(id / 10 % 10);
            var block = Mod.Cells.Records.FirstOrDefault(b => b.BlockNumber == bn);
            if (block == null) { block = new CellBlock { BlockNumber = bn, GroupType = GroupTypeEnum.InteriorCellBlock }; Mod.Cells.Records.Add(block); }
            var sub = block.SubBlocks.FirstOrDefault(s => s.BlockNumber == sn);
            if (sub == null) { sub = new CellSubBlock { BlockNumber = sn, GroupType = GroupTypeEnum.InteriorCellSubBlock }; block.SubBlocks.Add(sub); }
            var cell = Cells[k].rec.DeepCopy(new Cell.TranslationMask(true) { Persistent = false, Temporary = false, NavigationMeshes = false, Landscape = false });
            sub.Cells.Add(cell); return cell;
        }
        // E-package: a copy of a vanilla package (Travel: BlockTest's DA06 shape; Follow: WERoad02Follow) with our conditions.
        public Package Travel(string id, PlacedObject to, int radius, params ConditionFloat[] conds)
        {
            var p = Mods[0].Packages.First(x => x.EditorID == "DA06YamarzStage70PostForcegreet").Duplicate(Mod.GetNextFormKey());
            p.EditorID = id; p.OwnerQuest.Clear(); p.Conditions.Clear(); p.Conditions.AddRange(conds);
            var loc = (PackageDataLocation)p.Data[0];
            loc.Location = new LocationTargetRadius { Target = new LocationTarget(), Radius = (uint)radius };
            ((LocationTarget)loc.Location.Target).Link.SetTo(to.FormKey);
            Mod.Packages.Add(p); return p;
        }
        public Package Follow(string id, params ConditionFloat[] conds)
        {
            var p = Mods[0].Packages.First(x => x.EditorID == "WERoad02Follow").Duplicate(Mod.GetNextFormKey());
            p.EditorID = id; p.OwnerQuest.Clear(); p.Conditions.Clear(); p.Conditions.AddRange(conds);
            var t = p.Data.Values.OfType<PackageDataTarget>().First();
            var target = new PackageTargetSpecificReference(); target.Reference.SetTo(K("000014:Skyrim.esm"));
            t.Target = target;
            Mod.Packages.Add(p); return p;
        }
    }

    static ConditionFloat Glob(Global g, float v) { var d = new GetGlobalValueConditionData(); d.Global.Link.SetTo(g.FormKey); return C(d, CompareOperator.EqualTo, v); }
    static ConditionFloat Stage(Quest q, CompareOperator op, int s) { var d = new GetStageConditionData(); d.Quest.Link.SetTo(q.FormKey); return C(d, op, s); }
    static ConditionFloat Done(Quest q, int s) { var d = new GetStageDoneConditionData { Stage = s }; d.Quest.Link.SetTo(q.FormKey); return C(d, CompareOperator.EqualTo, 1); }
    static ConditionFloat Or(ConditionFloat c) { c.Flags |= Condition.Flag.OR; return c; }
    static ConditionFloat Not(ConditionFloat c) { c.ComparisonValue = 0; c.CompareOperator = CompareOperator.EqualTo; return c; }
    static ConditionFloat SpeechBelow(float v) => C(OnPlayer(new GetActorValueConditionData { ActorValue = ActorValue.Speech }), CompareOperator.LessThan, v);

    // The quest: Main Quest (blocks.md: the act's line), an empty start-up stage 0, a log entry per stage (text from the
    // record's journal rows; hidden stages carry none), Complete Quest on the endings; objectives from the record's rows.
    static Quest NewQuest(Quest q, string name, string id, int[] hidden, int[] ends, string script)
    {
        q.Name = name; q.Priority = 60; q.Type = Quest.TypeEnum.MainQuest; q.Flags = 0;
        var journal = LocalQuests.Journal(id);
        q.Stages.Add(new QuestStage { Index = 0, Flags = QuestStage.Flag.StartUpStage, LogEntries = { new QuestLogEntry { Flags = 0 } } });
        foreach (var s in journal.Keys.Concat(hidden).OrderBy(s => s))
            q.Stages.Add(new QuestStage { Index = (ushort)s, LogEntries = { new QuestLogEntry { Flags = ends.Contains(s) ? QuestLogEntry.Flag.CompleteQuest : 0, Entry = hidden.Contains(s) ? null : journal[s] } } });
        foreach (var (_, i, text) in Objectives(id)) q.Objectives.Add(new QuestObjective { Index = (ushort)i, DisplayText = text });
        q.VirtualMachineAdapter = new QuestAdapter { FileName = script };
        foreach (var s in q.Stages.Where(s => s.Index != 0))
            q.VirtualMachineAdapter.Fragments.Add(new QuestScriptFragment { Stage = s.Index, StageIndex = 0, ScriptName = script, FragmentName = $"Fragment_{s.Index}" });
        return q;
    }

    // TR-topic: one top-level player topic per record topic; one INFO per (variant, conditions, fragment body). The lines come
    // from the topic's JSON infos by variant; the body calls the quest script (properties stay on it).
    // A choice (Under set): the topic joins that branch, not top level, and is offered only by an INFO's Link To (TCLT), as
    // Skyrim's question-and-answer pairs: the question's INFO lists its answers, which follow it in the same conversation.
    static DialogBranch? Under;
    static DialogTopic Topic(SkyrimMod mod, Quest q, string code, JsonElement lines, string topic, ConditionFloat[] speaker, params (string variant, string? body, ConditionFloat[] conds)[] infos)
    {
        var t0 = lines.GetProperty(topic);
        var id = $"ARG_{code}_" + string.Concat(topic.Split('-').Skip(1).Select(p => char.ToUpper(p[0]) + p[1..]));
        var branch = Under ?? mod.DialogBranches.AddNew(id + "Branch");
        var t = mod.DialogTopics.AddNew(id);
        var first = t0.GetProperty("infos")[0].GetProperty("prompt").GetString()!;
        if (Under == null)
        {
            branch.Quest.SetTo(q.FormKey); branch.Category = DialogBranch.CategoryType.Player; branch.Flags = DialogBranch.Flag.TopLevel;
            branch.StartingTopic.SetTo(t.FormKey);
        }
        t.Name = first; t.Quest.SetTo(q.FormKey); t.Branch.SetTo(branch.FormKey); t.Priority = 50;
        t.Category = DialogTopic.CategoryEnum.Topic; t.Subtype = DialogTopic.SubtypeEnum.Custom; t.SubtypeName = new RecordType("CUST");
        var n = 0;
        foreach (var (variant, body, conds) in infos)
        {
            var v = t0.GetProperty("infos").EnumerateArray().Single(x => x.GetProperty("variant").GetString() == variant);
            var prompt = v.GetProperty("prompt").GetString()!;
            var info = new DialogResponses(mod.GetNextFormKey(), SkyrimRelease.SkyrimSE) { Flags = new DialogResponseFlags(), Prompt = prompt };
            byte r = 1;
            var text = v.GetProperty("lines").EnumerateArray().Select(l => l.GetString()!).ToArray();
            foreach (var l in text) info.Responses.Add(new DialogResponse { Text = l, ResponseNumber = r++, Emotion = Emotion.Neutral });
            info.Conditions.AddRange(speaker.Select(c => c.DeepCopy()));
            info.Conditions.AddRange(conds);
            // The wording bands (lines@high, lines@low), as LocalQuests.TopicV: each a copy of this INFO (gates and fragment)
            // on GetRelationshipRank with the player (>= 1, < 0), the default taking the complement.
            var bands = new List<DialogResponses>();
            foreach (var (band, op, rv) in LocalQuests.Bands)
                if (v.TryGetProperty($"lines@{band}", out var bl))
                {
                    var b = new DialogResponses(mod.GetNextFormKey(), SkyrimRelease.SkyrimSE) { Flags = new DialogResponseFlags(), Prompt = prompt };
                    byte br = 1;
                    foreach (var l in bl.EnumerateArray()) b.Responses.Add(new DialogResponse { Text = l.GetString()!, ResponseNumber = br++, Emotion = Emotion.Neutral });
                    b.Conditions.AddRange(info.Conditions.Where(c => c.Data is not GetRelationshipRankConditionData).Select(c => c.DeepCopy()));
                    b.Conditions.Add(LocalQuests.Rank(op, rv));
                    info.Conditions.Add(LocalQuests.Rank(band == "high" ? CompareOperator.LessThan : CompareOperator.GreaterThanOrEqualTo, band == "high" ? 1 : 0));
                    bands.Add(b);
                }
            string? script = null;
            if (body != null)
            {
                script = $"TIF_{id}_{n}";
                info.VirtualMachineAdapter = new DialogResponsesAdapter
                {
                    Scripts = { Script(script) },
                    ScriptFragments = new ScriptFragments { FileName = script, OnEnd = new ScriptFragment { ScriptName = script, FragmentName = "Fragment_0" } },
                };
                TifBodies.Add((script, body));
            }
            Lines.Add(new Line(code, topic, variant, id, prompt, text, script, body));
            foreach (var b in bands) { b.VirtualMachineAdapter = info.VirtualMachineAdapter?.DeepCopy(); t.Responses.Add(b); }
            t.Responses.Add(info);
            n++;
        }
        return t;
    }

    public static void Add(SkyrimMod mod, List<ISkyrimModGetter> mods)
    {
        var x = new Ctx(mod, mods);
        Mq01 = mod.Quests.AddNew("ARG_MQ01");
        Mq03 = mod.Quests.AddNew("ARG_MQ03");
        var mq01Parts = BuildMq01(x);
        BuildMq03(x, mq01Parts);
        Console.WriteLine($"main quest: MQ01 {Mq01.FormKey}, MQ03 {Mq03.FormKey}, {Lines.Count} lines");
    }

    sealed record Mq01Parts(PlacedNpc Ties, PlacedObject Survivors, PlacedObject Broker, PlacedObject Aftermath);

    static Mq01Parts BuildMq01(Ctx x)
    {
        var mod = x.Mod; var q = Mq01;
        const NpcConfiguration.Flag P = NpcConfiguration.Flag.Protected, U = NpcConfiguration.Flag.Unique, E = NpcConfiguration.Flag.Essential;
        // Templates: BM&V's Argonians (female 160E6A, 02A1EE; male 00FF4D, 045E50, 1DE49D, 02A1E6), vanilla Khajiit (Ri'saad,
        // Atahba) and a Dunmer woman (Brelyna Maryon) for looks.
        var wuleen = x.Base("ARG_MQ01_WuleenSei", "Wuleen-Sei", "160E6A:Black Marsh.esm", 10, P | U);
        var wuleenM = x.Base("ARG_MQ01_WuleenSeiMarch", "Wuleen-Sei", "160E6A:Black Marsh.esm", 10, P | U);
        var ux = x.Base("ARG_MQ01_UxXeek", "Ux-Xeek", "02A1EE:Black Marsh.esm", 5, P | U);
        var uxM = x.Base("ARG_MQ01_UxXeekMarch", "Ux-Xeek", "02A1EE:Black Marsh.esm", 5, P | U);
        var buys = x.Base("ARG_MQ01_BuysTheMonths", "Buys-The-Months", "045E50:Black Marsh.esm", 10, P | U);
        var courier = x.Base("ARG_MQ01_MeeTuja", "Mee-Tuja", "1DE49D:Black Marsh.esm", 8, U);
        var dives = x.Base("ARG_MQ01_DivesWithoutARope", "Dives-Without-A-Rope", "160E6A:Black Marsh.esm", 4, P | U);
        var divesM = x.Base("ARG_MQ01_DivesWithoutARopeMarch", "Dives-Without-A-Rope", "160E6A:Black Marsh.esm", 4, P | U);
        var finds = x.Base("ARG_MQ01_FindsTheOtherBank", "Finds-The-Other-Bank", "02A1EE:Black Marsh.esm", 4, P | U);
        var findsM = x.Base("ARG_MQ01_FindsTheOtherBankMarch", "Finds-The-Other-Bank", "02A1EE:Black Marsh.esm", 4, P | U);
        // the rest of the gang: two refs each (the hold, and the shore's survivors), never both enabled, so not Unique
        var risakka = x.Base("ARG_MQ01_RiSakka", "Ri'Sakka", "01B1DB:Skyrim.esm", 4, P);
        var tsanji = x.Base("ARG_MQ01_Tsanji", "Tsanji", "01B1DA:Skyrim.esm", 4, P);
        var llarvi = x.Base("ARG_MQ01_LlarviMaryon", "Llarvi Maryon", "01C196:Skyrim.esm", 4, P);
        var neshNeel = x.Base("ARG_MQ01_NeshNeel", "Nesh-Neel", "160E6A:Black Marsh.esm", 4, P | U);
        var sal = x.Base("ARG_MQ01_SalSei", "Sal-Sei", "00FF4D:Black Marsh.esm", 5, U);
        var deesh = x.Base("ARG_MQ01_DeeshDuun", "Deesh-Duun", "02A1EE:Black Marsh.esm", 5, U);
        var ties = x.Base("ARG_MQ01_TiesTheLoosePlank", "Ties-The-Loose-Plank", "02A1E6:Black Marsh.esm", 5, E | U);
        var leader = x.Base("ARG_MQ01_CutsTheOldKnot", "Cuts-the-Old-Knot", "160E6A:Black Marsh.esm", 20, U);
        var cutter = x.Base("ARG_MQ01_RootCutter", "Root-Cutter", "00FF4D:Black Marsh.esm", 3, 0, Aggression.Aggressive);
        var root = mod.Factions.AddNew("ARG_UnboundRoot");
        root.Name = "Unbound Root"; root.Flags = Faction.FactionFlag.HiddenFromPC;
        foreach (var n in new[] { leader, cutter }) n.Factions.Add(new RankPlacement { Faction = root.ToLink<IFactionGetter>(), Rank = 0 });
        foreach (var (rec, ids) in new (string, string[])[] {
            ("npc.pirate-freeholds.opening-work-barge.npc-opening-overseer", ["ARG_MQ01_WuleenSei", "ARG_MQ01_WuleenSeiMarch"]),
            ("npc.pirate-freeholds.opening-work-barge.npc-opening-roll-reader", ["ARG_MQ01_UxXeek", "ARG_MQ01_UxXeekMarch"]),
            ("npc.mercantile-coast.lilmoth.broker-buys-the-months", ["ARG_MQ01_BuysTheMonths"]),
            ("npc.pirate-freeholds.opening-work-camp.n1-2", ["ARG_MQ01_DivesWithoutARope", "ARG_MQ01_DivesWithoutARopeMarch"]),
            ("npc.pirate-freeholds.opening-work-camp.n1", ["ARG_MQ01_TiesTheLoosePlank"]) })
            Speakers[rec] = ids;

        // Items: Sal-Sei's reed-knife (e-sal's reward; our copy of the iron dagger, renamed).
        var knife = Survey.Winners<IWeaponGetter>(x.Mods)[K("01397E:Skyrim.esm")].rec.Duplicate(mod.GetNextFormKey());
        knife.EditorID = "ARG_MQ01_SalReedKnife"; knife.Name = "Sal-Sei's Reed-Knife"; knife.VirtualMachineAdapter = null;
        mod.Weapons.Add(knife);
        var rollRead = mod.Globals.AddNewShort("ARG_MQ01_RollRead"); rollRead.Data = 0;
        var answered = mod.Globals.AddNewShort("ARG_MQ01_Answered"); answered.Data = 0;
        var savedSal = mod.Globals.AddNewShort("ARG_MQ01_SavedSal"); savedSal.Data = 0;     // flag.mq01.saved-sal (E-global)
        var savedDeesh = mod.Globals.AddNewShort("ARG_MQ01_SavedDeesh"); savedDeesh.Data = 0; // flag.mq01.saved-deesh

        // Places. The hold (we.mq01.start, .barge-crew, .gang): the main deck, away from the door 0F9399 at the far end.
        StartMarker = x.Marker("ARG_MQ01_StartMarker", x.Snap.At(HoldNav, 2750, 3900, 7010));
        var holdParent = x.Marker("ARG_MQ01_HoldParent", new P3Float(2750, 3700, 6700), null, 0x400);   // on until 40
        var crewParent = x.Marker("ARG_MQ01_CrewParent", new P3Float(2750, 3750, 6700), null, 0x400);   // on until the end
        var wuleenRef = x.Actor("ARG_MQ01_WuleenSeiRef", wuleen, x.Snap.At(HoldNav, 2850, 4300, 7010), crewParent);
        var uxRef = x.Actor("ARG_MQ01_UxXeekRef", ux, x.Snap.At(HoldNav, 2950, 4150, 7010), crewParent);
        var gangHold = new[] { (dives, 2650f, 4000f), (finds, 2700f, 3800f), (risakka, 3000f, 3900f), (tsanji, 3100f, 4400f), (llarvi, 2600f, 4450f) }
            .Select(g => x.Actor($"ARG_MQ01_{g.Item1.EditorID![9..]}HoldRef", g.Item1, x.Snap.At(HoldNav, g.Item2, g.Item3, 7010), holdParent)).ToList();
        // The hold cell: the vanilla location 'Dainty Sload' cleared (we.mq01.hold-location).
        var hold = x.Interior(HoldCell);
        hold.Location.Clear();
        hold.Persistent.AddRange([StartMarker, holdParent, crewParent, wuleenRef, uxRef, .. gangHold]);
        // we.mq01.hold-door (W-override, the door audit of walk 4): the hold is BM&V's copy of the ship 01Ship, whose way out
        // Black Marsh North moved to the door at the top of the stairs (0AA6C9); the copy's stair door 0F92EC has a load
        // door's model and no teleport (it did nothing), and its far door 0F9399, an opening door with a room behind it,
        // teleported to the pier. The stair door becomes the way out, paired with the pier door 005AB4 both ways (the
        // arrival in the hold is BMN's own in front of 0AA6C9; on the pier, 0F9399's old one), locked with no key until
        // the answer (stage 20's fragment unlocks it); 0F9399 loses its teleport and opens onto its room.
        var holdTo = ((IPlacedObjectGetter)x.Placed[HoldDoorFar].rec).TeleportDestination!;
        var stairIn = ((IPlacedObjectGetter)x.Placed[K("039827:Black Marsh.esm")].rec).TeleportDestination!;
        var stairDoor = (PlacedObject)((IPlacedObjectGetter)x.Placed[HoldDoor].rec).DeepCopy();
        stairDoor.MajorRecordFlagsRaw |= 0x400;
        stairDoor.TeleportDestination = new TeleportDestination { Position = holdTo.Position, Rotation = holdTo.Rotation };
        stairDoor.TeleportDestination.Door.SetTo(PierDoor);
        stairDoor.Lock = new LockData { Level = LockLevel.RequiresKey };
        var farDoor = (PlacedObject)((IPlacedObjectGetter)x.Placed[HoldDoorFar].rec).DeepCopy();
        farDoor.TeleportDestination = null; farDoor.MajorRecordFlagsRaw |= 0x400;
        var pierDoor = (PlacedObject)((IPlacedObjectGetter)x.Placed[PierDoor].rec).DeepCopy();
        pierDoor.MajorRecordFlagsRaw |= 0x400;
        pierDoor.TeleportDestination = new TeleportDestination { Position = stairIn.Position, Rotation = stairIn.Rotation };
        pierDoor.TeleportDestination.Door.SetTo(HoldDoor);
        hold.Persistent.AddRange([stairDoor, farDoor]);
        x.World.TopCell!.Persistent.Add(pierDoor);
        HoldInside = stairIn.Position;

        // The pier (we.mq01.broker) and the march copies at the plank's foot (we.mq01.march), Dock1's navmesh 079823.
        var brokerParent = x.Marker("ARG_MQ01_BrokerParent", new P3Float(5380, -7500, -300), null, 0x400);
        var marchParent = x.Marker("ARG_MQ01_MarchParent", new P3Float(5350, -7800, -300), null, 0xC00);
        var buysRef = x.Actor("ARG_MQ01_BuysTheMonthsRef", buys, x.Snap.At(DockNav, 5380, -7500), brokerParent);
        var courierRef = x.Actor("ARG_MQ01_MeeTujaRef", courier, x.Snap.At(DockNav, 5300, -7350));
        var wuleenMRef = x.Actor("ARG_MQ01_WuleenSeiMarchRef", wuleenM, x.Snap.At(DockNav, 5350, -7800), marchParent);
        var uxMRef = x.Actor("ARG_MQ01_UxXeekMarchRef", uxM, x.Snap.At(DockNav, 5300, -7850), marchParent);
        var divesMRef = x.Actor("ARG_MQ01_DivesWithoutARopeMarchRef", divesM, x.Snap.At(DockNav, 5400, -7880), marchParent);
        var findsMRef = x.Actor("ARG_MQ01_FindsTheOtherBankMarchRef", findsM, x.Snap.At(DockNav, 5250, -7900), marchParent);

        // The camp (we.mq01.camp, .families, .cell), on BM&V's own navmesh 07990E; the dressing from BM&V's and vanilla
        // statics under three enable parents (orderly, attacked, aftermath; "standing" things are the opposite of aftermath).
        var fireAt = x.Snap.At(CampNav, Fire.X, Fire.Y);
        var orderly = x.Marker("ARG_MQ01_CampOrderly", new P3Float(fireAt.X, fireAt.Y, fireAt.Z - 300), null, 0xC00);
        var attacked = x.Marker("ARG_MQ01_CampAttacked", new P3Float(fireAt.X + 20, fireAt.Y, fireAt.Z - 300), null, 0xC00);
        var aftermath = x.Marker("ARG_MQ01_CampAftermath", new P3Float(fireAt.X + 40, fireAt.Y, fireAt.Z - 300), null, 0xC00);
        var cellParent = x.Marker("ARG_MQ01_CellParent", new P3Float(fireAt.X + 60, fireAt.Y, fireAt.Z - 300), null, 0xC00);
        var survivors = x.Marker("ARG_MQ01_SurvivorsParent", new P3Float(fireAt.X + 80, fireAt.Y, fireAt.Z - 300), null, 0xC00);
        var shore93Parent = x.Marker("ARG_MQ01_Shore93Parent", new P3Float(fireAt.X + 100, fireAt.Y, fireAt.Z - 300), null, 0x400);
        var fireMark = x.Marker("ARG_MQ01_FireMarker", x.Snap.At(CampNav, Fire.X + 100, Fire.Y - 50));
        var shedMark = x.Marker("ARG_MQ01_ShedMarker", x.Snap.At(CampNav, Shed.X, Shed.Y - 150));
        var hutsMark = x.Marker("ARG_MQ01_HutsMarker", new P3Float(Huts1.X, Huts1.Y, 10)); // in the huts over the deep water (no navmesh: entered from the water)
        var shoreMark = x.Marker("ARG_MQ01_ShoreMarker", x.Snap.At(CampNav, Shore.X, Shore.Y));
        var waterMark = x.Marker("ARG_MQ01_WaterEdgeMarker", x.Snap.At(CampNav, WaterEdge.X, WaterEdge.Y));
        var salRef = x.Actor("ARG_MQ01_SalSeiRef", sal, x.Snap.At(CampNav, Fire.X + 60, Fire.Y + 150));
        var deeshRef = x.Actor("ARG_MQ01_DeeshDuunRef", deesh, x.Snap.At(CampNav, Fire.X - 60, Fire.Y - 150));
        var neshNeelRef = x.Actor("ARG_MQ01_NeshNeelRef", neshNeel, x.Snap.At(CampNav, Fire.X + 150, Fire.Y + 100), orderly);
        var leaderRef = x.Actor("ARG_MQ01_CutsTheOldKnotRef", leader, x.Snap.At(CampNav, Fire.X - 150, Fire.Y + 120), cellParent);
        var cutter1Ref = x.Actor("ARG_MQ01_RootCutter1Ref", cutter, x.Snap.At(CampNav, Shed.X + 50, Shed.Y - 200), cellParent);
        var cutter2Ref = x.Actor("ARG_MQ01_RootCutter2Ref", cutter, x.Snap.At(CampNav, Shed.X - 80, Shed.Y - 220), cellParent);
        var tiesRef = x.Actor("ARG_MQ01_TiesTheLoosePlankRef", ties, x.Snap.At(CampNav, Shore.X + 120, Shore.Y + 60));
        tiesRef.MajorRecordFlagsRaw = 0xC00; // off until MQ01's endings (his own ref, outside the survivors parent)
        var survivorRefs = new[] { (risakka, 80f, -60f), (tsanji, -100f, 90f), (llarvi, 200f, 120f) }
            .Select(g => x.Actor($"ARG_MQ01_{g.Item1.EditorID![9..]}ShoreRef", g.Item1, x.Snap.At(CampNav, Shore.X + g.Item2, Shore.Y + g.Item3), survivors)).ToList();
        P3Float OnLand((float X, float Y) p, float dz = 0) => new(p.X, p.Y, MathF.Round(x.Land(p.X, p.Y) + dz));
        var dressing = new List<PlacedObject>
        {
            x.Marker("ARG_MQ01_Campfire", new P3Float(fireAt.X, fireAt.Y, fireAt.Z), K("035F49:Skyrim.esm"), 0x400, aftermath, opposite: true), // Campfire01Burning
            x.Marker("ARG_MQ01_Shed", OnLand(Shed), K("0A013F:Black Marsh.esm"), 0x400),                       // 01shed, the hatching shed (uxith); 01strawhut's HutExterior.nif is in no archive
            x.Marker("ARG_MQ01_Cutting", OnLand(Cutting), K("1B32E5:Black Marsh.esm"), 0x400),                // 01swamptreecoolmoss, scaled down below
            x.Marker("ARG_MQ01_Hut1", new P3Float(Huts1.X, Huts1.Y, 0), K("0AA5F0:Black Marsh.esm"), 0x400, aftermath, opposite: true), // 001Hut2
            x.Marker("ARG_MQ01_Hut2", new P3Float(Huts2.X, Huts2.Y, 0), K("0AA5F2:Black Marsh.esm"), 0x400, aftermath, opposite: true), // 001hut3
            x.Marker("ARG_MQ01_HutBurnt", new P3Float(Huts1.X, Huts1.Y - 200, 0), K("0D8589:Black Marsh.esm"), 0x400, aftermath),    // a destroyed shack
            x.Marker("ARG_MQ01_Planks", new P3Float(Planks.X, Planks.Y, 0), K("0008CB:HearthFires.esm"), 0x400),                      // BYOHFishDock01
            x.Marker("ARG_MQ01_HutFire1", new P3Float(Huts1.X, Huts1.Y, 120), K("035F49:Skyrim.esm"), 0x400, attacked),
            x.Marker("ARG_MQ01_HutFire2", new P3Float(Huts2.X, Huts2.Y, 120), K("035F49:Skyrim.esm"), 0x400, attacked),
        };
        foreach (var (dx, dy) in new[] { (-40f, 0f), (30f, 30f), (10f, -40f) })
            dressing.Add(x.Marker($"ARG_MQ01_Egg{dressing.Count}", OnLand((Shed.X + dx, Shed.Y + dy), 5), K("17BF06:Black Marsh.esm"), 0x400)); // 01egg, the clutch
        dressing.Single(d => d.EditorID == "ARG_MQ01_Cutting").Scale = 0.15f;
        dressing.Single(d => d.EditorID == "ARG_MQ01_Planks").Placement!.Rotation = new P3Float(0, 0, MathF.PI / 2);
        // Zones: the camp's edge (30 -> 35, hidden: the gang is put at the fire before the player arrives), the fire (the
        // march's end, 35 -> 40), the shed (40 -> 41), the huts' water (40 -> 42), the shore's three boxes. The camp box
        // holds the fire box, so any way in crosses it first.
        var campZone = x.Zone("ARG_MQ01_ZoneCamp", new P3Float(fireAt.X, fireAt.Y, fireAt.Z + 100), new P3Float(2500, 2500, 1500), q, 30, 35);
        var fireZone = x.Zone("ARG_MQ01_ZoneFire", new P3Float(fireAt.X, fireAt.Y, fireAt.Z + 100), new P3Float(300, 300, 200), q, 35, 40);
        var shedZone = x.Zone("ARG_MQ01_ZoneShed", new P3Float(Shed.X, Shed.Y - 100, x.Land(Shed.X, Shed.Y) + 100), new P3Float(250, 250, 200), q, 40, 41);
        var hutsZone = x.Zone("ARG_MQ01_ZoneHuts", new P3Float(Huts1.X, Huts1.Y - 150, -100), new P3Float(300, 350, 250), q, 40, 42);
        var shoreAt = new P3Float(shoreMark.Placement!.Position.X, shoreMark.Placement.Position.Y, shoreMark.Placement.Position.Z + 100);
        var shore90 = x.Zone("ARG_MQ01_ZoneShore90", shoreAt, new P3Float(350, 350, 250), q, 41, 90);
        var shore91 = x.Zone("ARG_MQ01_ZoneShore91", shoreAt, new P3Float(350, 350, 250), q, 42, 91);
        var shore93 = x.Zone("ARG_MQ01_ZoneShore93", shoreAt, new P3Float(350, 350, 250), q, 40, 93, shore93Parent);

        // Packages on the aliases (E-package). BM&V's navmeshes carry no edge links (0 of 17,589 in Black Marsh.esm and
        // Black Marsh North.esp; `plugin.sh inspect navstat`), so no one walks from one navmesh to another: the gang sets off
        // along Dock1's own navmesh to its landward end (30 to 34) and is moved to the fire at the camp's edge zone (35,
        // E-move), where it waits (35 to 39). The leader to the water's edge from 40, the cutters from 41 (they go and are
        // disabled at the ending); the saved one follows the player on 41 or 42.
        var dockEnd = x.Marker("ARG_MQ01_DockEndMarker", x.Snap.At(DockNav, 5340, -5000));
        var march = x.Travel("ARG_MQ01_MarchOff", dockEnd, 200, Stage(q, CompareOperator.GreaterThanOrEqualTo, 30), Stage(q, CompareOperator.LessThan, 35));
        var atFire = x.Travel("ARG_MQ01_WaitAtFire", fireMark, 300, Stage(q, CompareOperator.GreaterThanOrEqualTo, 35), Stage(q, CompareOperator.LessThan, 40));
        var leave = x.Travel("ARG_MQ01_LeaderLeaves", waterMark, 128, Stage(q, CompareOperator.GreaterThanOrEqualTo, 40));
        var cutLeave = x.Travel("ARG_MQ01_CuttersLeave", waterMark, 200, Stage(q, CompareOperator.GreaterThanOrEqualTo, 41));
        var salFollow = x.Follow("ARG_MQ01_SalSeiFollows", Stage(q, CompareOperator.EqualTo, 41));
        var deeshFollow = x.Follow("ARG_MQ01_DeeshDuunFollows", Stage(q, CompareOperator.EqualTo, 42));

        NewQuest(q, "No Name on the Work Roll", "quest.main.mq01", [35], [90, 91, 93], "ARG_QF_MQ01");
        const QuestAlias.Flag AD = QuestAlias.Flag.AllowDisabled;
        Forced(q, A1WuleenHold, "WuleenSei", wuleenRef.FormKey, AD | QuestAlias.Flag.Essential);
        Forced(q, A1UxHold, "UxXeek", uxRef.FormKey, AD);
        Forced(q, A1Buys, "BuysTheMonths", buysRef.FormKey, AD);
        var courierA = Forced(q, A1Courier, "Courier", courierRef.FormKey, QuestAlias.Flag.Essential);
        courierA.PackageData.Add(march.ToLink()); courierA.PackageData.Add(atFire.ToLink());
        foreach (var (id, name, r, f) in new[] { (A1WuleenMarch, "WuleenSeiMarch", wuleenMRef, AD | QuestAlias.Flag.Essential), (A1UxMarch, "UxXeekMarch", uxMRef, AD),
                     (A1DivesMarch, "DivesMarch", divesMRef, AD), (A1FindsMarch, "FindsMarch", findsMRef, AD) })
        {
            var a = Forced(q, id, name, r.FormKey, f);
            a.PackageData.Add(march.ToLink()); a.PackageData.Add(atFire.ToLink());
        }
        Forced(q, A1Sal, "SalSei", salRef.FormKey, QuestAlias.Flag.Essential).PackageData.Add(salFollow.ToLink());
        Forced(q, A1Deesh, "DeeshDuun", deeshRef.FormKey, QuestAlias.Flag.Essential).PackageData.Add(deeshFollow.ToLink());
        Forced(q, A1Leader, "CutsTheOldKnot", leaderRef.FormKey, AD | QuestAlias.Flag.Protected).PackageData.Add(leave.ToLink());
        Forced(q, A1Cutter1, "RootCutter1", cutter1Ref.FormKey, AD).PackageData.Add(cutLeave.ToLink());
        Forced(q, A1Cutter2, "RootCutter2", cutter2Ref.FormKey, AD).PackageData.Add(cutLeave.ToLink());
        Forced(q, A1Ties, "TiesTheLoosePlank", tiesRef.FormKey, AD);
        Forced(q, A1ZoneFire, "ZoneFire", fireZone.FormKey);
        Forced(q, A1ZoneShed, "ZoneShed", shedZone.FormKey, AD);
        Forced(q, A1ZoneHuts, "ZoneHuts", hutsZone.FormKey, AD);
        Forced(q, A1Shore90, "ZoneShore90", shore90.FormKey);
        Forced(q, A1Shore91, "ZoneShore91", shore91.FormKey);
        Forced(q, A1Shore93, "ZoneShore93", shore93.FormKey, AD);
        // TR-activate on the hold's stair door (BlockTest's door shape): opening it once the answer is given sets 30.
        Forced(q, A1HoldDoor, "HoldDoor", HoldDoor);
        Forced(q, A1FireMark, "FireMarker", fireMark.FormKey);
        Forced(q, A1ZoneCamp, "ZoneCamp", campZone.FormKey);
        q.VirtualMachineAdapter!.Aliases.Add(AliasScript(q, A1HoldDoor, Script("defaultSetStageAliasScript", Int("stage", 30), Int("prereqStageOPT", 20), Int("TriggerType", 0))));
        // Objective targets (the compass marker): Wuleen-Sei at 10, the stair door at 20, the camp's fire at 30.
        foreach (var (o, a) in new[] { (10, A1WuleenHold), (20, A1HoldDoor), (30, A1FireMark) })
            q.Objectives.Single(ob => ob.Index == o).Targets.Add(new QuestObjectiveTarget { AliasID = (int)a });
        q.VirtualMachineAdapter!.Scripts.Add(Script("ARG_QF_MQ01",
            Obj("StartMarker", StartMarker.FormKey), Obj("Tunic", K("03C9FE:Skyrim.esm")), Obj("Footwraps", K("03CA00:Skyrim.esm")),
            Obj("RollRead", rollRead.FormKey), Obj("Answered", answered.FormKey), Obj("SavedSal", savedSal.FormKey), Obj("SavedDeesh", savedDeesh.FormKey),
            Obj("CampOrderly", orderly.FormKey), Obj("CampAttacked", attacked.FormKey), Obj("CampAftermath", aftermath.FormKey),
            Obj("MarchParent", marchParent.FormKey), Obj("HoldParent", holdParent.FormKey), Obj("CrewParent", crewParent.FormKey),
            Obj("BrokerParent", brokerParent.FormKey), Obj("CellParent", cellParent.FormKey), Obj("SurvivorsParent", survivors.FormKey),
            Obj("Shore93Parent", shore93Parent.FormKey), Obj("ShedZone", shedZone.FormKey), Obj("HutsZone", hutsZone.FormKey),
            Obj("ShedMark", shedMark.FormKey), Obj("HutsMark", hutsMark.FormKey), Obj("ShoreMark", shoreMark.FormKey),
            Obj("FireMark", fireMark.FormKey), Obj("HoldDoor", HoldDoor),
            Alias("Courier", q, A1Courier), Alias("Leader", q, A1Leader), Alias("SalSei", q, A1Sal), Alias("DeeshDuun", q, A1Deesh),
            Alias("WuleenMarch", q, A1WuleenMarch), Alias("UxMarch", q, A1UxMarch), Alias("Ties", q, A1Ties),
            Alias("Cutter1", q, A1Cutter1), Alias("Cutter2", q, A1Cutter2), Alias("DivesMarch", q, A1DivesMarch), Alias("FindsMarch", q, A1FindsMarch),
            Obj("ReedKnife", knife.FormKey), Obj("NextQuest", Mq03.FormKey)));

        // Lines (TR-topic). The roll at 10 is a question: its INFO links to the three answers (choices in its branch, as
        // Skyrim's question-and-answer pairs), so they follow it at once and come back with it if the player walks off.
        // Each answer sets Answered (the broker's line) and stage 20; the broker, the port hand and Dives-Without-A-Rope
        // from 10 until the strike.
        var lines = LinesOf("mq01");
        const string Q = "(GetOwningQuest() as ARG_QF_MQ01)";
        ConditionFloat[] Who(params Npc[] ns) => ns.Select((n, i) => i < ns.Length - 1 ? Or(IsId(n)) : IsId(n)).ToArray();
        var at10 = Stage(q, CompareOperator.EqualTo, 10);
        ConditionFloat[] Before40() => [Stage(q, CompareOperator.GreaterThanOrEqualTo, 10), Stage(q, CompareOperator.LessThan, 40)];
        var roll = Topic(mod, q, "MQ01", lines, "topic.mq01-the-roll", Who(wuleen), ("main", $"{Q}.ReadRoll()", [at10.DeepCopy()]));
        Under = mod.DialogBranches.Single(b => b.FormKey == roll.Branch.FormKey);
        foreach (var t in new[] { "topic.mq01-answer-name", "topic.mq01-answer-silent", "topic.mq01-answer-defy" })
        {
            var answer = Topic(mod, q, "MQ01", lines, t, Who(wuleen), ("main", $"{Q}.Answer()", [at10.DeepCopy()]));
            foreach (var r in roll.Responses) r.LinkTo.Add(answer.ToLink<IDialogTopicGetter>());
        }
        Under = null;
        Topic(mod, q, "MQ01", lines, "topic.mq01-the-hire", Who(buys), ("after-answer", null, [.. Before40(), Glob(answered, 1)]), ("before-answer", null, [at10.DeepCopy()]));
        Topic(mod, q, "MQ01", lines, "topic.mq01-the-water", Who(ux, uxM), ("main", null, Before40()));
        Topic(mod, q, "MQ01", lines, "topic.mq01-the-march", Who(dives, divesM), ("main", null, Before40()));

        // World edits: exterior persistent refs in the worldspace's persistent cell.
        x.World.TopCell!.Persistent.AddRange([brokerParent, marchParent, buysRef, courierRef, wuleenMRef, uxMRef, divesMRef, findsMRef,
            orderly, attacked, aftermath, cellParent, survivors, shore93Parent, fireMark, shedMark, hutsMark, shoreMark, waterMark,
            salRef, deeshRef, neshNeelRef, leaderRef, cutter1Ref, cutter2Ref, tiesRef, .. survivorRefs, .. dressing,
            fireZone, shedZone, hutsZone, shore90, shore91, shore93, dockEnd, campZone]);
        // we.mq01.no-valenwood, we.mq01.no-welcome: Valenwood.esp's start-game quests and BM&V's greeting quest off at
        // the start; MQ03's ending starts them (Valenwood's two deferred there too: no first-entry trigger is a block).
        foreach (var k in Valenwood.Append(Welcome.ToString()))
        {
            var key = K(k);
            if (!Survey.Winners<IQuestGetter>(x.Mods).TryGetValue(key, out var w)) { Console.WriteLine($"MQ01: no quest {k} in the load order"); continue; }
            var copy = mod.Quests.FirstOrDefault(z => z.FormKey == key) ?? (Quest)w.rec.DeepCopy();
            copy.Flags &= ~Quest.Flag.StartGameEnabled;
            if (!mod.Quests.Any(z => z.FormKey == key)) mod.Quests.Add(copy);
        }
        return new Mq01Parts(tiesRef, survivors, brokerParent, aftermath);
    }

    static void BuildMq03(Ctx x, Mq01Parts m1)
    {
        var mod = x.Mod; var q = Mq03;
        const NpcConfiguration.Flag P = NpcConfiguration.Flag.Protected, U = NpcConfiguration.Flag.Unique;
        var nesh = x.Base("ARG_MQ03_NeshDeeka", "Nesh-Deeka", "160E6A:Black Marsh.esm", 15, U);
        var salts = x.Base("ARG_MQ03_SaltsTheCatch", "Salts-The-Catch", "02A1EE:Black Marsh.esm", 6, P | U);
        var officer = x.Base("ARG_MQ03_NeverWritesTwice", "Never-Writes-Twice", "160E6A:Black Marsh.esm", 12, U);
        var stranger = x.Base("ARG_MQ03_ReedStranger", "Stranger", "1DE49D:Black Marsh.esm", 12, U);
        Speakers["npc.nesh-deeka"] = ["ARG_MQ03_NeshDeeka"];
        Speakers["npc.dunmer-north.stormhold.reed-officer"] = ["ARG_MQ03_NeverWritesTwice"];
        var reed = mod.Factions.AddNew("ARG_VeiledReed");
        reed.Name = "Veiled Reed"; reed.Flags = Faction.FactionFlag.HiddenFromPC;
        reed.Ranks.Add(new Rank { Number = 0, Title = new GenderedItem<TranslatedString?>(new TranslatedString(Language.English, "Sworn Hand"), new TranslatedString(Language.English, "Sworn Hand")) });

        // Items (we.mq03.jar-marks): the phial on vanilla's potion bottle, the courier's tag on a key's model, the sunk fish-trap
        // (our copy of vanilla's lockbox, Novice), the spilled sap (our copy of vanilla's inert oil pool activator), the key.
        var phial = mod.MiscItems.AddNew("ARG_MQ03_SapPhial");
        phial.Name = "Phial of Spilled Sap"; phial.Value = 0; phial.Weight = 0.2f;
        phial.Model = new Model { File = x.Mods[0].Ingestibles.First(i => i.FormKey == K("03EADD:Skyrim.esm")).Model!.File.DataRelativePath.Path };
        var tag = mod.MiscItems.AddNew("ARG_MQ03_CourierTag");
        tag.Name = "Courier's Brass Tag"; tag.Value = 0; tag.Weight = 0.1f;
        tag.Model = new Model { File = x.Mods[0].Keys.First(k => k.Model != null).Model!.File.DataRelativePath.Path };
        var trap = Survey.Winners<IContainerGetter>(x.Mods)[K("09424C:Skyrim.esm")].rec.Duplicate(mod.GetNextFormKey());
        trap.EditorID = "ARG_MQ03_FishTrap"; trap.Name = "Sunk Fish-Trap"; trap.VirtualMachineAdapter = null;
        trap.Items = [new ContainerEntry { Item = new ContainerItem { Item = new FormLink<IItemGetter>(tag.FormKey), Count = 1 } }];
        trap.Flags &= ~Container.Flag.Respawns;
        mod.Containers.Add(trap);
        var sap = Survey.Winners<IActivatorGetter>(x.Mods)[K("0F02E1:Skyrim.esm")].rec.Duplicate(mod.GetNextFormKey());
        sap.EditorID = "ARG_MQ03_SpilledSap"; sap.Name = "Spilled Sap"; sap.VirtualMachineAdapter = null; sap.ActivateTextOverride = "Taste";
        mod.Activators.Add(sap);
        var key = mod.Keys.AddNew("ARG_MQ03_HouseKey");
        key.Name = "Key to the House in Lilmoth"; key.Value = 0; key.Weight = 0;
        key.Model = new Model { File = x.Mods[0].Keys.First(k => k.Model != null).Model!.File.DataRelativePath.Path };
        var attackTold = mod.Globals.AddNewShort("ARG_MQ03_AttackTold"); attackTold.Data = 0;
        var nightTold = mod.Globals.AddNewShort("ARG_MQ03_NightTold"); nightTold.Data = 0;
        var sworn = mod.Globals.AddNewShort("ARG_MQ03_ReedSworn"); sworn.Data = 0;       // flag.mq03.reed-sworn
        var declined = mod.Globals.AddNewShort("ARG_MQ03_ReedDeclined"); declined.Data = 0; // flag.mq03.reed-declined
        var hist = mod.Globals.FirstOrDefault(g => g.EditorID == "ARG_HistHearing") as Global ?? NewShort(mod, "ARG_HistHearing"); // grantHistStep (E-global)

        // The camp at dawn: the jar-marks parent (sap, trap, picks) and the Reed's strangers on the shore.
        var jarParent = x.Marker("ARG_MQ03_JarParent", new P3Float(Shed.X, Shed.Y, x.Land(Shed.X, Shed.Y) - 300), null, 0xC00);
        var reedParent = x.Marker("ARG_MQ03_ReedParent", new P3Float(Shore.X, Shore.Y, x.Land(Shore.X, Shore.Y) - 300), null, 0xC00);
        var sapRef = x.Marker("ARG_MQ03_SpilledSapRef", new P3Float(Shed.X + 20, Shed.Y - 60, MathF.Round(x.Land(Shed.X + 20, Shed.Y - 60) + 2)), sap.FormKey, 0x400, jarParent);
        var trapRef = x.Marker("ARG_MQ03_FishTrapRef", new P3Float(Trap.X, Trap.Y, MathF.Round(x.Land(Trap.X, Trap.Y) + 10)), trap.FormKey, 0x400, jarParent);
        trapRef.Lock = new LockData { Level = LockLevel.Novice };
        var fireAt = x.Snap.At(CampNav, Fire.X + 120, Fire.Y + 60);
        var picks = Enumerable.Range(0, 5).Select(i => x.Marker($"ARG_MQ03_Lockpick{i + 1}", new P3Float(fireAt.X + 15 * i, fireAt.Y, MathF.Round(x.Land(fireAt.X + 15 * i, fireAt.Y) + 30)), Lockpick, 0x400, jarParent)).ToList();
        var officerRef = x.Actor("ARG_MQ03_NeverWritesTwiceRef", officer, x.Snap.At(CampNav, Shore.X + 100, Shore.Y - 50), reedParent);
        var strangerRef = x.Actor("ARG_MQ03_ReedStrangerRef", stranger, x.Snap.At(CampNav, Shore.X + 160, Shore.Y - 10), reedParent);

        // The house (we.mq03.house, .rooms): Nesh-Deeka and the mats in the back room, Salts-The-Catch at the outer door; on
        // the tilted floor (no navmesh where the rooms are: the actors are placed 10 units over the floor and settle).
        P3Float H(float hx, float hy) => new(hx, hy, HouseFloor(hy) + 10);
        var neshRef = x.Actor("ARG_NeshDeekaRef", nesh, H(1620, 1250));
        var saltsRef = x.Actor("ARG_MQ03_SaltsTheCatchRef", salts, H(1850, 800));
        var houseMark = x.Marker("ARG_MQ03_HouseMarker", H(1750, 950));
        var matMark = x.Marker("ARG_MQ03_MatMarker", H(1550, 1150));
        var mats = new[] { x.Marker("ARG_MQ03_Mat1", new P3Float(1540, 1180, HouseFloor(1180)), K("0B8371:Skyrim.esm"), 0x400),
                           x.Marker("ARG_MQ03_Mat2", new P3Float(1540, 1060, HouseFloor(1060)), K("0B8371:Skyrim.esm"), 0x400) };
        var house = x.Interior(HouseCell);
        house.Persistent.AddRange([neshRef, saltsRef, houseMark, matMark, .. mats]);

        // The dream (we.mq03.dream) in the empty hold: a ring of BM&V's thorn roots on the walk from the mark to the door,
        // under the dream parent; the door-gap's zone at the hold door (40 -> 45; 45 splits 90/91 on the oath global).
        var dreamParent = x.Marker("ARG_MQ03_DreamParent", new P3Float(2850, 3300, 6700), null, 0xC00);
        var dreamMark = x.Marker("ARG_MQ03_DreamMarker", x.Snap.At(HoldNav, 2850, 3300, 7010));
        var roots = new[] { (2650f, 3700f), (3100f, 3700f), (2600f, 4300f), (3150f, 4300f), (2700f, 4850f), (3100f, 4850f) }
            .Select((p, i) => x.Marker($"ARG_MQ03_DreamRoot{i + 1}", new P3Float(p.Item1, p.Item2, 7010), K("1B331F:Black Marsh.esm"), 0x400, dreamParent)).ToList();
        var doorPos = HoldInside; // in front of the hold's stair door, its way out (MQ01)
        var doorZone = x.Zone("ARG_MQ03_ZoneDoor", doorPos, new P3Float(150, 150, 150), q, 40, 45);
        x.Interior(HoldCell).Persistent.AddRange([dreamParent, dreamMark, .. roots, doorZone]);

        // we.mq03.door: the outer door locked to the house key (setDoorAccess: the key handed at e-sworn).
        var door = (PlacedObject)((IPlacedObjectGetter)x.Placed[HouseDoorOut].rec).DeepCopy();
        door.MajorRecordFlagsRaw |= 0x400;
        door.Lock = new LockData { Level = LockLevel.RequiresKey };
        door.Lock.Key.SetTo(key.FormKey);

        NewQuest(q, "A Dead Prisoner's Use", "quest.main.mq03", [11, 45], [90, 91], "ARG_QF_MQ03");
        const QuestAlias.Flag AD = QuestAlias.Flag.AllowDisabled;
        Forced(q, A3Officer, "NeverWritesTwice", officerRef.FormKey, AD | QuestAlias.Flag.Essential);
        Forced(q, A3Stranger, "Stranger", strangerRef.FormKey, AD | QuestAlias.Flag.Essential);
        Forced(q, A3Sap, "SpilledSap", sapRef.FormKey, AD);
        Forced(q, A3Nesh, "NeshDeeka", neshRef.FormKey);
        Forced(q, A3Salts, "SaltsTheCatch", saltsRef.FormKey);
        Forced(q, A3Ties, "TiesTheLoosePlank", m1.Ties.FormKey, AD);
        Forced(q, A3DoorZone, "ZoneDoor", doorZone.FormKey);
        Forced(q, A3Trap, "FishTrap", trapRef.FormKey, AD);
        var vm = q.VirtualMachineAdapter!;
        // TR-activate: the taste (the alias set-stage script on activate, prereq 10) sets the hidden stage 11; TR-death: the
        // officer's death moves 10 to 20, Nesh-Deeka's 20 to 40 (the record's fail-forwards).
        vm.Aliases.Add(AliasScript(q, A3Sap, Script("defaultSetStageAliasScript", Int("stage", 11), Int("prereqStageOPT", 10), Int("TriggerType", 0))));
        vm.Aliases.Add(AliasScript(q, A3Officer, OnDeath(q, 10, 20)));
        vm.Aliases.Add(AliasScript(q, A3Nesh, OnDeath(q, 20, 40)));
        vm.Scripts.Add(Script("ARG_QF_MQ03",
            Obj("JarParent", jarParent.FormKey), Obj("ReedParent", reedParent.FormKey), Obj("SurvivorsParent", m1.Survivors.FormKey),
            Obj("DreamParent", dreamParent.FormKey), Obj("BrokerParent", m1.Broker.FormKey), Obj("HouseMark", houseMark.FormKey),
            Obj("MatMark", matMark.FormKey), Obj("DreamMark", dreamMark.FormKey), Obj("HoldDoor", HoldDoor), Obj("HouseKey", key.FormKey),
            Obj("Phial", phial.FormKey), Obj("Gold001", Gold), Obj("VeiledReed", reed.FormKey), Obj("ReedSworn", sworn.FormKey),
            Obj("ReedDeclined", declined.FormKey), Obj("AttackTold", attackTold.FormKey), Obj("NightTold", nightTold.FormKey),
            Obj("HistHearing", hist.FormKey), Alias("Ties", q, A3Ties),
            new ScriptObjectListProperty { Name = "Deferred", Objects = Valenwood.Append(Welcome.ToString()).Where(k => mod.Quests.Any(z => z.FormKey == K(k)))
                .Select(k => new ScriptObjectProperty { Object = new FormLink<ISkyrimMajorRecordGetter>(K(k)) }).ToExtendedList() }));

        // Lines.
        var lines = LinesOf("mq03");
        const string Q = "(GetOwningQuest() as ARG_QF_MQ03)";
        var before20 = Stage(q, CompareOperator.LessThan, 20);
        var at20 = Stage(q, CompareOperator.EqualTo, 20);
        Topic(mod, q, "MQ03", lines, "topic.mq03-the-boat", [IsId(officer)],
            ("ready", "GetOwningQuest().SetStage(20)", [before20.DeepCopy(), Done(q, 11), Or(Has(phial.FormKey, 1)), Has(tag.FormKey, 1)]),
            ("where", null, [before20.DeepCopy(), Stage(q, CompareOperator.GreaterThanOrEqualTo, 10)]));
        Topic(mod, q, "MQ03", lines, "topic.mq03-the-attack", [IsId(nesh)],
            ("phial-carried", $"{Q}.TellAttack(akSpeakerRef, True)", [at20.DeepCopy(), Has(phial.FormKey, 1)]),
            ("phial-none", $"{Q}.TellAttack(akSpeakerRef, False)", [at20.DeepCopy()]));
        Topic(mod, q, "MQ03", lines, "topic.mq03-the-night", [IsId(ties0(x))],
            ("tag", $"{Q}.TellNight()", [at20.DeepCopy(), Has(tag.FormKey, 1)]),
            ("words", $"{Q}.TellNight()", [at20.DeepCopy(), Speech(25)]),
            ("low", null, [at20.DeepCopy(), SpeechBelow(25)]));
        Topic(mod, q, "MQ03", lines, "topic.mq03-the-offer", [IsId(nesh)], ("main", null, [at20.DeepCopy()]));
        Topic(mod, q, "MQ03", lines, "topic.mq03-take-oath", [IsId(nesh)], ("main", $"{Q}.TakeOath()", [at20.DeepCopy(), Glob(attackTold, 1), Glob(nightTold, 1)]));
        Topic(mod, q, "MQ03", lines, "topic.mq03-refuse-oath", [IsId(nesh)], ("main", "GetOwningQuest().SetStage(40)", [at20.DeepCopy(), Glob(attackTold, 1), Glob(nightTold, 1)]));

        x.World.TopCell!.Persistent.AddRange([jarParent, reedParent, sapRef, trapRef, .. picks, officerRef, strangerRef, door]);
    }
    static GlobalShort NewShort(SkyrimMod mod, string id) { var g = mod.Globals.AddNewShort(id); g.Data = 0; return g; }
    static Npc ties0(Ctx x) => x.Mod.Npcs.Single(n => n.EditorID == "ARG_MQ01_TiesTheLoosePlank");

    // After every quest is allocated (Generate's end): MQ03's endings start ARG_MQ04 at 10 when it is in the plugin.
    public static void Finish(SkyrimMod mod)
    {
        var mq04 = mod.Quests.FirstOrDefault(q => q.EditorID == "ARG_MQ04");
        var props = Mq03.VirtualMachineAdapter!.Scripts.Single(s => s.Name == "ARG_QF_MQ03").Properties;
        props.RemoveAll(p => p.Name == "NextQuest");
        if (mq04 != null) props.Add(Obj("NextQuest", mq04.FormKey));
        else Console.WriteLine("MQ03: ARG_MQ04 not in the plugin; its endings start nothing until it is");
    }

    // The TIF fragment scripts the lines above use (Papyrus source, generated into papyrus/generated by the seed).
    public static void WritePsc(string dir)
    {
        Directory.CreateDirectory(dir);
        foreach (var (script, body) in TifBodies)
            File.WriteAllText(Path.Combine(dir, script + ".psc"),
                $"Scriptname {script} extends TopicInfo Hidden\n{{Generated by tools/ArgoniaPlugin/MainQuest.cs: one main-quest line's end fragment (TR-topic).}}\n\n;BEGIN FRAGMENT Fragment_0\nFunction Fragment_0(ObjectReference akSpeakerRef)\n\t{body}\nEndFunction\n;END FRAGMENT\n");
    }
}
