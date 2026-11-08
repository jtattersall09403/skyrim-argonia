using Mutagen.Bethesda.Strings;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Noggog;

// Phase 3's test quest ARG_BlockTest (docs/phases/3-building-blocks.md): every block of docs/design/blocks.md once, on
// Lilmoth's dock. Throwaway: removed once the owner's walk has passed; the shapes stay as Phase 4's templates.
// Allocated after the opening's records, in this fixed order, so form ids are stable.
static class BlockTest
{
    static FormKey K(string k) => FormKey.Factory(k);
    static FormLink<ISkyrimMajorRecordGetter> L(FormKey k) => new(k);
    public static readonly FormKey Navmesh = K("07EEF8:Black Marsh.esm"), ShipNavmesh = K("0AA666:Black Marsh.esm");
    public static readonly FormKey Door = K("0AA664:Black Marsh.esm"), Ship = K("0AA665:Black Marsh.esm"), DockCell = K("005A21:Black Marsh.esm");
    public static readonly string[] Naga = ["03E409", "03E40A", "03E40B", "03E40C", "03E40D"];
    static readonly FormKey XMarker = K("00003B:Skyrim.esm"), PlayerRef = K("000014:Skyrim.esm"), Gold = K("00000F:Skyrim.esm"), Achievements = K("0FC85D:Skyrim.esm");
    // Alias ids, in the order the design lists them.
    public const uint AKeeper = 0, AWalker = 1, ACrab = 2, AToken = 3, ADoor = 4, AZoneA = 5, AZoneB = 6;

    // The nearest triangle centre of a winning navmesh to a spot, never one already used (no two things on one spot).
    sealed class Snapper(List<ISkyrimModGetter> mods)
    {
        readonly Dictionary<FormKey, (INavigationMeshGetter rec, ModKey from)> nav = Survey.Winners<INavigationMeshGetter>(mods);
        readonly HashSet<(FormKey, int)> used = [];
        public P3Float At(FormKey mesh, float x, float y)
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
    }

    static ConditionFloat C(ConditionData d, CompareOperator op, float v, bool or = false) =>
        new() { CompareOperator = op, ComparisonValue = v, Data = d, Flags = or ? Condition.Flag.OR : 0 };
    static T OnPlayer<T>(T d) where T : ConditionData { d.RunOnType = Condition.RunOnType.Reference; d.Reference.SetTo(PlayerRef); return d; }
    static GetStageConditionData Stage(Quest q) { var d = new GetStageConditionData(); d.Quest.Link.SetTo(q.FormKey); return d; }
    static GetStageDoneConditionData Done(Quest q, int s) { var d = new GetStageDoneConditionData { Stage = s }; d.Quest.Link.SetTo(q.FormKey); return d; }

    static ScriptEntry Script(string name, params ScriptProperty[] ps) { var e = new ScriptEntry { Name = name }; e.Properties.AddRange(ps); return e; }
    static ScriptObjectProperty Obj(string n, FormKey k) => new() { Name = n, Object = L(k) };
    static ScriptObjectProperty Alias(string n, Quest q, uint id) => new() { Name = n, Object = L(q.FormKey), Alias = (short)id };
    static ScriptIntProperty Int(string n, int v) => new() { Name = n, Data = v };

    public static void Add(SkyrimMod mod, List<ISkyrimModGetter> mods, Worldspace world, P3Float spot)
    {
        var snap = new Snapper(mods);
        var placed = Survey.Winners<IPlacedGetter>(mods);
        PlacedObject Marker(string id, P3Float p, int flags = 0x400) => new(mod.GetNextFormKey(), SkyrimRelease.SkyrimSE)
        { EditorID = id, Base = new FormLinkNullable<IPlaceableObjectGetter>(XMarker), MajorRecordFlagsRaw = flags, Placement = new Placement { Position = p } };

        // Quests first (their form ids head the block).
        var q = mod.Quests.AddNew("ARG_BlockTest");
        var end = mod.Quests.AddNew("ARG_BlockTestEnd");

        // W-npc, W-fixed: our three bases, templated on BM&V's villagers and vanilla's mudcrab for looks and AI; the
        // stats are ours (no Stats template flag), a fixed level, never PC-level-mult (decision 0035).
        const NpcConfiguration.TemplateFlag looks = NpcConfiguration.TemplateFlag.Traits | NpcConfiguration.TemplateFlag.Factions
            | NpcConfiguration.TemplateFlag.SpellList | NpcConfiguration.TemplateFlag.AIData | NpcConfiguration.TemplateFlag.AIPackages
            | NpcConfiguration.TemplateFlag.ModelAnimation | NpcConfiguration.TemplateFlag.Inventory | NpcConfiguration.TemplateFlag.Script
            | NpcConfiguration.TemplateFlag.DefPackList | NpcConfiguration.TemplateFlag.AttackData | NpcConfiguration.TemplateFlag.Keywords;
        var npcs = Survey.Winners<INpcGetter>(mods);
        Npc Base(string id, string name, string tpl, short level, NpcConfiguration.Flag extra)
        {
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
        var keeper = Base("ARG_BT_Keeper", "Dock Keeper", "00FF4D:Black Marsh.esm", 5, 0);
        var walker = Base("ARG_BT_Walker", "Dock Walker", "02A1EE:Black Marsh.esm", 5, NpcConfiguration.Flag.Protected);
        var crab = Base("ARG_BT_Crab", "Mudcrab", "0E4011:Skyrim.esm", 4, 0);

        // Positions: each snapped to a 07EEF8 triangle centre (the walker to the ship's 0AA666), the read-back checks it.
        var keeperAt = snap.At(Navmesh, spot.X, spot.Y + 210);       // 3 m north of the opening marker
        var startAt = snap.At(Navmesh, keeperAt.X - 140, keeperAt.Y); // 2 m from the keeper
        var walkerAt = snap.At(Navmesh, keeperAt.X + 100, keeperAt.Y); // beside the keeper
        var doorPos = placed[Door].rec.Placement!.Position;
        var doorAt = snap.At(Navmesh, doorPos.X - 150, doorPos.Y);    // in front of the ship door
        var crabAt = snap.At(Navmesh, spot.X + 1050, spot.Y);         // 15 m east, or 07EEF8's nearest to it
        // The token on the dock planks (BM&V's BYOHFishDock01 02A20A), 3 m east of the keeper, 30 units above the planks'
        // own top surface read from their mesh by the placement helper (Surface.cs; blocks.md W-ref). The start marker and
        // the keeper stand on land: navmesh 07EEF8 covers both, so a navmesh spot "between them" was land (owner walk
        // 2026-11-07, item 4). Loose items 30 units up settle onto the surface (Havok), never inside it.
        var tokenXY = (X: 31040f, Y: -2700f);
        var tokenTop = Surface.On(Surface.Under(mods, new Surface.Assets(Surface.Paths), world.FormKey, tokenXY.X, tokenXY.Y), "BYOHFishDock01", 30)
            ?? throw new InvalidOperationException("ARG_BT_TokenRef: no dock planks under the token's spot");
        var tokenAt = new P3Float(tokenXY.X, tokenXY.Y, tokenTop);
        // The ship door stands off 07EEF8's east edge (no navmesh at dock height reaches it in BlackMarsh; 0FE9A3 under it
        // is another worldspace's): the door marker is 07EEF8's nearest triangle, and the zone boxes (the player's, not an
        // actor's) sit on the door, 1.5 m toward the dock, so the player enters them on the way to it.
        float dx = doorAt.X - doorPos.X, dy = doorAt.Y - doorPos.Y, dl = MathF.Sqrt(dx * dx + dy * dy);
        var zoneAt = new P3Float(MathF.Round(doorPos.X + 100 * dx / dl), MathF.Round(doorPos.Y + 100 * dy / dl), MathF.Round(doorPos.Z));
        var shipDoor = placed[K("0AA837:Black Marsh.esm")].rec.Placement!.Position; // the ship's side of the door
        var inShip = snap.At(ShipNavmesh, shipDoor.X, shipDoor.Y);

        PlacedNpc Actor(string id, Npc b, P3Float p, int flags, PlacedObject? parent = null)
        {
            var r = new PlacedNpc(mod.GetNextFormKey(), SkyrimRelease.SkyrimSE)
            { EditorID = id, MajorRecordFlagsRaw = flags, Placement = new Placement { Position = p } };
            r.Base.SetTo(b.FormKey);
            if (parent != null) { r.EnableParent = new EnableParent(); r.EnableParent.Reference.SetTo(parent.FormKey); }
            return r;
        }
        var tokenParent = Marker("ARG_BT_TokenParent", new P3Float(tokenAt.X, tokenAt.Y, tokenAt.Z - 200), 0xC00);
        var crabParent = Marker("ARG_BT_CrabParent", new P3Float(crabAt.X, crabAt.Y, crabAt.Z - 200), 0xC00);
        var keeperRef = Actor("ARG_BT_KeeperRef", keeper, keeperAt, 0x400);
        var walkerRef = Actor("ARG_BT_WalkerRef", walker, inShip, 0xC00);
        var crabRef = Actor("ARG_BT_CrabRef", crab, crabAt, 0x400, crabParent);
        var startMarker = Marker("ARG_BT_StartMarker", startAt);
        var walkerMarker = Marker("ARG_BT_WalkerMarker", walkerAt);
        var doorMarker = Marker("ARG_BT_DoorMarker", doorAt);

        // TR-acquire: the token (a vanilla wooden bowl's model; no Nordic mark) and its ref behind its enable parent.
        var token = mod.MiscItems.AddNew("ARG_BT_Token");
        token.Name = "Test Token"; token.Value = 0; token.Weight = 0.1f;
        token.Model = new Model { File = @"Clutter\Dining Set\BasicWoodenBowl01.nif" };
        var tokenRef = Marker("ARG_BT_TokenRef", tokenAt);
        tokenRef.Base.SetTo(token.FormKey);
        tokenRef.EnableParent = new EnableParent(); tokenRef.EnableParent.Reference.SetTo(tokenParent.FormKey);

        // E-item (setDoorAccess): the key, with a vanilla key's model.
        var key = mod.Keys.AddNew("ARG_BT_Key");
        key.Name = "Ship Door Key"; key.Value = 0; key.Weight = 0;
        key.Model = new Model { File = mods[0].Keys.First(k => k.Model != null).Model!.File.DataRelativePath.Path };

        // TR-zone and two triggers for one outcome: two vanilla set-stage boxes at one spot, both setting the same stage 71
        // (Bethesda's shape: 22 (quest, stage) pairs in Skyrim.esm are set by 2 to 6 boxes, e.g. CWSiege 8 by 6). The
        // box script checks GetStageDone(stage) and then calls SetStage, a cross-object call between check and set, so two
        // boxes entered in one frame can both call SetStage(71) (owner walk 2026-11-07: 71 and 72 both done); fragment 71
        // guards itself (blocks.md, the race guard) and counts its runs in two globals the owner reads from the console.
        var trigTemplate = mods[0].EnumerateMajorRecords<IPlacedObjectGetter>().First(r => r.Base.FormKey == K("099312:Skyrim.esm") && r.Primitive != null);
        PlacedObject Zone(string id, int stage)
        {
            var z = new PlacedObject(mod.GetNextFormKey(), SkyrimRelease.SkyrimSE)
            {
                EditorID = id, MajorRecordFlagsRaw = 0x400, Placement = new Placement { Position = new P3Float(zoneAt.X, zoneAt.Y, zoneAt.Z + 100) },
                Primitive = trigTemplate.Primitive!.DeepCopy(),
                VirtualMachineAdapter = new VirtualMachineAdapter { Scripts = { Script("defaultSetStageTrigScript", Obj("myQuest", q.FormKey), Int("prereqStageOPT", 65), Int("stage", stage)) } },
            };
            z.Primitive.Bounds = new P3Float(150, 150, 100); // a 300 x 300 x 200 box (half extents)
            z.Base.SetTo(K("099312:Skyrim.esm"));
            return z;
        }
        var zoneA = Zone("ARG_BT_ZoneA", 71);
        var zoneB = Zone("ARG_BT_ZoneB", 71);

        // E-global, E-faction.
        var standing = mod.Globals.AddNewShort("ARG_BT_Global"); standing.Data = 0;
        var raceHits = mod.Globals.AddNewShort("ARG_BT_RaceHits"); raceHits.Data = 0; // every entry into fragment 71
        var raceRuns = mod.Globals.AddNewShort("ARG_BT_RaceRuns"); raceRuns.Data = 0; // entries past the guard: must be 1
        var faction = mod.Factions.AddNew("ARG_BT_Faction");
        faction.Name = "Dock Hands";
        faction.Ranks.Add(new Rank { Number = 0, Title = new GenderedItem<TranslatedString?>(new TranslatedString(Language.English, "Hand"), new TranslatedString(Language.English, "Hand")) });

        // E-package: Travel to the door marker, copied from a vanilla Travel package (template 016FAA), gated on stage 60;
        // C-detected rides on it as a PACK condition (GetDetected player >= 0: the check is read, the walk never gated).
        var travel = mods[0].Packages.First(p => p.EditorID == "DA06YamarzStage70PostForcegreet");
        var walk = travel.Duplicate(mod.GetNextFormKey());
        walk.EditorID = "ARG_BT_WalkPackage";
        walk.OwnerQuest.SetTo(q.FormKey);
        walk.Conditions.Clear();
        walk.Conditions.Add(C(Stage(q), CompareOperator.GreaterThanOrEqualTo, 60));
        var det = new GetDetectedConditionData(); det.TargetNpc.Link.SetTo(PlayerRef);
        walk.Conditions.Add(C(det, CompareOperator.GreaterThanOrEqualTo, 0));
        var loc = (PackageDataLocation)walk.Data[0];
        loc.Location = new LocationTargetRadius { Target = new LocationTarget(), Radius = 64 };
        ((LocationTarget)loc.Location.Target).Link.SetTo(doorMarker.FormKey);
        mod.Packages.Add(walk);

        // E-scene / TR-scene: one phase, two lines each, the end fragment sets 60.
        DialogTopic SceneTopic(string id, string line)
        {
            var t = mod.DialogTopics.AddNew(id);
            t.Quest.SetTo(q.FormKey); t.Category = DialogTopic.CategoryEnum.Scene; t.Subtype = DialogTopic.SubtypeEnum.Scene;
            t.SubtypeName = new RecordType("SCEN"); t.Priority = 50;
            var info = new DialogResponses(mod.GetNextFormKey(), SkyrimRelease.SkyrimSE) { Flags = new DialogResponseFlags() };
            info.Responses.Add(new DialogResponse { Text = line, ResponseNumber = 1, Emotion = Emotion.Neutral });
            t.Responses.Add(info);
            return t;
        }
        var lines = new (uint actor, string id, string text)[]
        {
            (AKeeper, "ARG_BT_Scene1", "You came out of the ship. Good."),
            (AWalker, "ARG_BT_Scene2", "The hold is dry. I counted every crate."),
            (AKeeper, "ARG_BT_Scene3", "Then walk the planks to the door and wait there."),
            (AWalker, "ARG_BT_Scene4", "To the door, then."),
        };
        var sceneTopics = lines.Select(l => SceneTopic(l.id, l.text)).ToList();
        var scene = mod.Scenes.AddNew("ARG_BT_Scene");
        scene.Quest.SetTo(q.FormKey);
        scene.Phases.Add(new ScenePhase { Name = "" });
        foreach (var a in new[] { AKeeper, AWalker })
            scene.Actors.Add(new SceneActor { ID = a, Flags = 0, BehaviorFlags = SceneActor.BehaviorFlag.DeathEnd | SceneActor.BehaviorFlag.CombatEnd | SceneActor.BehaviorFlag.DialoguePause });
        for (var i = 0; i < lines.Length; i++)
        {
            var act = new SceneAction { Type = SceneAction.TypeEnum.Dialog, ActorID = (int)lines[i].actor, Index = (uint)(i + 1), StartPhase = 0, EndPhase = 0, Flags = SceneAction.Flag.FaceTarget, Name = "" };
            act.Topic.SetTo(sceneTopics[i].FormKey);
            scene.Actions.Add(act);
        }
        scene.LastActionIndex = (uint)lines.Length;
        scene.VirtualMachineAdapter = new SceneAdapter
        {
            Scripts = { Script("SF_ARG_BT_Scene") },
            ScriptFragments = new SceneScriptFragments { FileName = "SF_ARG_BT_Scene", OnEnd = new ScriptFragment { ScriptName = "SF_ARG_BT_Scene", FragmentName = "Fragment_0" } },
        };

        // TR-topic and every condition: the keeper's lines, each its own top-level branch (one player choice each).
        ConditionFloat IsKeeper() { var d = new GetIsIDConditionData(); d.Object.Link.SetTo(keeper.FormKey); return C(d, CompareOperator.EqualTo, 1); }
        DialogResponses Info(string reply, int? sets, params ConditionFloat[] conds)
        {
            var info = new DialogResponses(mod.GetNextFormKey(), SkyrimRelease.SkyrimSE) { Flags = new DialogResponseFlags() };
            info.Responses.Add(new DialogResponse { Text = reply, ResponseNumber = 1, Emotion = Emotion.Neutral });
            info.Conditions.Add(IsKeeper());
            info.Conditions.AddRange(conds);
            if (sets is int s)
                info.VirtualMachineAdapter = new DialogResponsesAdapter
                {
                    Scripts = { Script($"TIF_ARG_BT_{s}") },
                    ScriptFragments = new ScriptFragments { FileName = $"TIF_ARG_BT_{s}", OnEnd = new ScriptFragment { ScriptName = $"TIF_ARG_BT_{s}", FragmentName = "Fragment_0" } },
                };
            return info;
        }
        void Topic(string id, string prompt, params DialogResponses[] infos)
        {
            var branch = mod.DialogBranches.AddNew(id.Replace("Topic", "Branch"));
            var t = mod.DialogTopics.AddNew(id);
            branch.Quest.SetTo(q.FormKey); branch.Category = DialogBranch.CategoryType.Player; branch.Flags = DialogBranch.Flag.TopLevel;
            branch.StartingTopic.SetTo(t.FormKey);
            t.Name = prompt; t.Quest.SetTo(q.FormKey); t.Branch.SetTo(branch.FormKey); t.Priority = 50;
            t.Category = DialogTopic.CategoryEnum.Topic; t.Subtype = DialogTopic.SubtypeEnum.Custom; t.SubtypeName = new RecordType("CUST");
            foreach (var i in infos) { i.Prompt = prompt; t.Responses.Add(i); }
        }
        ConditionFloat StageIs(int s) => C(Stage(q), CompareOperator.EqualTo, s);
        ConditionFloat Speech(float v) { var d = OnPlayer(new GetActorValueConditionData { ActorValue = ActorValue.Speech }); return C(d, CompareOperator.GreaterThanOrEqualTo, v); }
        var hasToken = new GetItemCountConditionData(); hasToken.ItemOrList.Link.SetTo(token.FormKey); OnPlayer(hasToken);
        var glob = new GetGlobalValueConditionData(); glob.Global.Link.SetTo(standing.FormKey);
        var inFaction = new GetInFactionConditionData(); inFaction.Faction.Link.SetTo(faction.FormKey); OnPlayer(inFaction);
        ConditionFloat CrabDead() => C(new GetDeadConditionData { RunOnType = Condition.RunOnType.QuestAlias, RunOnTypeIndex = (int)ACrab }, CompareOperator.EqualTo, 1);
        ConditionFloat Hour(CompareOperator op, float h, bool or = false) => C(new GetCurrentTimeConditionData(), op, h, or);
        Topic("ARG_BT_Topic20", "I am ready for the test.", Info("Then take this key, and find the token on the planks.", 20, StageIs(10)));
        Topic("ARG_BT_Topic40", "Here is the token.", Info("Good. You are one of the dock hands now.", 40,
            C(hasToken, CompareOperator.GreaterThanOrEqualTo, 1), C(glob, CompareOperator.GreaterThanOrEqualTo, 1), StageIs(30)));
        Topic("ARG_BT_Topic50", "Talk me into it.", Info("You talk well enough. Watch the walker.", 50,
            C(inFaction, CompareOperator.EqualTo, 1), Speech(15), StageIs(40)));
        Topic("ARG_BT_Topic50Never", "Talk me into it, master.", Info("You should never hear this.", null, Speech(100), StageIs(40)));
        Topic("ARG_BT_Topic90", "The crab is dead.",
            Info("By day, too. Done.", 90, CrabDead(), Hour(CompareOperator.GreaterThanOrEqualTo, 6), Hour(CompareOperator.LessThan, 20), C(Done(q, 80), CompareOperator.EqualTo, 1)),
            Info("At this hour. Done.", 90, CrabDead(), Hour(CompareOperator.LessThan, 6, or: true), Hour(CompareOperator.GreaterThanOrEqualTo, 20), C(Done(q, 80), CompareOperator.EqualTo, 1)));

        // The quest: E-stage and its objectives; one log entry per stage so each fragment binds.
        // Side Quest, not Misc: Skyrim.esm's misc quests (104 that complete) are objective lists whose completing entry
        // carries text in 7; completed misc quests leave the journal. The rule (blocks.md, E-stage): type Side Quest, the
        // completing stage has the Complete Quest flag on a log entry with text, its fragment completes the last objective
        // and calls Stop() (no CompleteQuest(); vanilla's QF_dunVolunruudQST Fragment_16 is exactly that), and no quest
        // completes in its start-up stage (0 of Skyrim.esm's 300 completing quests do).
        q.Name = "Block Test"; q.Priority = 50; q.Type = Quest.TypeEnum.SideQuest; q.Flags = 0;
        int[] stages = [10, 20, 30, 40, 50, 60, 65, 71, 75, 80, 90, 100];
        foreach (var s in stages)
            q.Stages.Add(new QuestStage
            {
                Index = (ushort)s, Flags = s == 10 ? QuestStage.Flag.StartUpStage : 0,
                LogEntries = { new QuestLogEntry { Flags = s == 100 ? QuestLogEntry.Flag.CompleteQuest : 0, Entry = s switch {
                    10 => "I am to take the block test on Lilmoth's dock.", 100 => "I passed the block test.", _ => null } } },
            });
        foreach (var (i, text) in new (ushort, string)[] { (10, "Speak to the Dock Keeper"), (20, "Find the token on the planks"), (30, "Bring the token to the Dock Keeper"),
                     (60, "Kill the mudcrab"), (65, "Walk to the ship door"), (75, "Open the ship door"), (80, "Tell the Dock Keeper") })
            q.Objectives.Add(new QuestObjective { Index = i, DisplayText = text });
        QuestAlias Forced(uint id, string name, IPlacedGetter r, QuestAlias.Flag flags = 0)
        {
            var a = new QuestAlias { ID = id, Type = QuestAlias.TypeEnum.Reference, Name = name, Flags = flags };
            a.ForcedReference.SetTo(r.FormKey);
            q.Aliases.Add(a);
            return a;
        }
        Forced(AKeeper, "Keeper", keeperRef);
        Forced(AWalker, "Walker", walkerRef, QuestAlias.Flag.AllowDisabled | QuestAlias.Flag.Optional | QuestAlias.Flag.Protected).PackageData.Add(walk.ToLink());
        Forced(ACrab, "Crab", crabRef, QuestAlias.Flag.AllowDisabled);
        Forced(AToken, "Token", tokenRef, QuestAlias.Flag.AllowDisabled);
        Forced(ADoor, "ShipDoor", placed[Door].rec);
        Forced(AZoneA, "ZoneA", zoneA);
        Forced(AZoneB, "ZoneB", zoneB);
        QuestFragmentAlias AliasScript(uint id, ScriptEntry s) { var f = new QuestFragmentAlias { Property = Alias("", q, id) }; f.Scripts.Add(s); return f; }
        int[] fragStages = [10, 20, 30, 40, 50, 60, 65, 71, 75, 80, 90, 100];
        q.VirtualMachineAdapter = new QuestAdapter
        {
            FileName = "ARG_QF_BlockTest",
            Scripts =
            {
                Script("ARG_QF_BlockTest",
                    Alias("Keeper", q, AKeeper), Alias("Walker", q, AWalker), Obj("RaceHits", raceHits.FormKey), Obj("RaceRuns", raceRuns.FormKey),
                    Obj("StartMarker", startMarker.FormKey), Obj("WalkerMarker", walkerMarker.FormKey), Obj("TokenParent", tokenParent.FormKey), Obj("CrabParent", crabParent.FormKey),
                    Obj("ShipKey", key.FormKey), Obj("Token", token.FormKey), Obj("Gold001", Gold), Obj("Standing", standing.FormKey), Obj("DockHands", faction.FormKey),
                    Obj("TalkScene", scene.FormKey), Obj("EndQuest", end.FormKey), Obj("AchievementsQuest", Achievements)),
            },
            Aliases =
            {
                AliasScript(ACrab, Script("defaultSetStageOnDeathRefAlias", Obj("myQST", q.FormKey), Int("preReqStage", 60), Int("StageToSet", 65))),
                AliasScript(AToken, Script("defaultSetStageOnPlayerAcquire", Obj("myQST", q.FormKey), Int("preReqStage", 20), Int("StageToSet", 30))),
                AliasScript(ADoor, Script("defaultSetStageAliasScript", Int("stage", 80), Int("prereqStageOPT", 75), Int("TriggerType", 0))), // 0: on activate (vanilla's HornActivator, FarengarEnchanter)
            },
        };
        foreach (var s in fragStages)
            q.VirtualMachineAdapter.Fragments.Add(new QuestScriptFragment { Stage = (ushort)s, StageIndex = 0, ScriptName = "ARG_QF_BlockTest", FragmentName = $"Fragment_{s}" });

        // TR-chain: the second quest, started by the first's SetStage(10) (Bethesda's chain shape) and completed at 100 by
        // the first quest's last fragment; an empty start-up stage 0, as vanilla's (none completes in its start-up stage).
        end.Name = "Block Test, the end"; end.Priority = 50; end.Type = Quest.TypeEnum.SideQuest;
        end.Stages.Add(new QuestStage { Index = 0, Flags = QuestStage.Flag.StartUpStage, LogEntries = { new QuestLogEntry { Flags = 0 } } });
        end.Stages.Add(new QuestStage { Index = 10, LogEntries = { new QuestLogEntry { Flags = 0, Entry = "The second quest started from the first." } } });
        end.Stages.Add(new QuestStage { Index = 100, LogEntries = { new QuestLogEntry { Flags = QuestLogEntry.Flag.CompleteQuest, Entry = "The second quest ended with the first." } } });
        // The journal lists a quest by its objectives: all 23 of Skyrim.esm's completing Side Quests have some (blockstudy),
        // and the end quest, which had none, showed "completed" on screen and in the Stats but not in the journal (walk 3).
        end.Objectives.Add(new QuestObjective { Index = 10, DisplayText = "Wait for the first quest to end" });
        // Vanilla side quests count on the Stats page by their own last fragment (blockstudy: 21 of Skyrim.esm's 23 completing
        // side quests call AchievementsScript.IncSideQuests(), Game.IncrementStat("Side Quests Completed")), so this one too.
        end.VirtualMachineAdapter = new QuestAdapter { FileName = "ARG_QF_BlockTestEnd", Scripts = { Script("ARG_QF_BlockTestEnd", Obj("AchievementsQuest", Achievements)) } };
        end.VirtualMachineAdapter.Fragments.Add(new QuestScriptFragment { Stage = 10, StageIndex = 0, ScriptName = "ARG_QF_BlockTestEnd", FragmentName = "Fragment_10" });
        end.VirtualMachineAdapter.Fragments.Add(new QuestScriptFragment { Stage = 100, StageIndex = 0, ScriptName = "ARG_QF_BlockTestEnd", FragmentName = "Fragment_100" });

        // The world edits: our dock refs in the worldspace's persistent cell; the door's lock (W-override); the five
        // Naga disabled where Black Marsh North placed them (W-ref removal); the ship's name and the walker inside (W-name).
        world.TopCell!.Persistent.AddRange([tokenParent, crabParent, keeperRef, crabRef, startMarker, walkerMarker, doorMarker, tokenRef, zoneA, zoneB]);
        var door = (PlacedObject)((IPlacedObjectGetter)placed[Door].rec).DeepCopy();
        door.MajorRecordFlagsRaw |= 0x400;
        door.Lock = new LockData { Level = LockLevel.RequiresKey };
        door.Lock.Key.SetTo(key.FormKey);
        world.TopCell.Persistent.Add(door);
        var cells = Survey.Winners<ICellGetter>(mods);
        var noRefs = new Cell.TranslationMask(true) { Persistent = false, Temporary = false, NavigationMeshes = false, Landscape = false };
        var dock = cells[DockCell].rec.DeepCopy(noRefs);
        foreach (var n in Naga)
        {
            var naga = (PlacedNpc)((IPlacedNpcGetter)placed[K(n + ":Black Marsh North.esp")].rec).DeepCopy();
            naga.MajorRecordFlagsRaw |= 0x800; // initially disabled
            dock.Temporary.Add(naga);
        }
        world.SubCells.Add(new WorldspaceBlock { BlockNumberX = 0, BlockNumberY = -1, GroupType = GroupTypeEnum.ExteriorCellBlock,
            Items = { new WorldspaceSubBlock { BlockNumberX = 0, BlockNumberY = -1, GroupType = GroupTypeEnum.ExteriorCellSubBlock, Items = { dock } } } });
        var ship = cells[Ship].rec.DeepCopy(noRefs);
        ship.Name = "Test Ship";
        ship.Persistent.Add(walkerRef);
        mod.Cells.Records.Add(new CellBlock { BlockNumber = 7, GroupType = GroupTypeEnum.InteriorCellBlock,
            SubBlocks = { new CellSubBlock { BlockNumber = 5, GroupType = GroupTypeEnum.InteriorCellSubBlock, Cells = { ship } } } });
    }
}
