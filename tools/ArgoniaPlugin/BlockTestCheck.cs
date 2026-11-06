using System.Text;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;
using Noggog;

// blocktest <Argonia.esp> <pex dir> <plugins in load order...>: the agent check of Phase 3 (docs/phases/3-building-blocks.md),
// read from the built plugin and the compiled scripts only: per step, every stage, condition, alias, script property and
// fragment is present and points at the right records; refs persistent; placed things on navmesh 07EEF8 (the walker on
// the ship's 0AA666); no PC-level-mult; the five Naga initially disabled. Exit 1 on any failure.
static class BlockTestCheck
{
    public static int Run(string esp, string pexDir, string[] paths)
    {
        var mods = Survey.Load(paths.Append(esp));
        var mine = mods[^1];
        var byEdid = mine.EnumerateMajorRecords().Where(r => r.EditorID != null && r.FormKey.ModKey == mine.ModKey).ToDictionary(r => r.EditorID!, r => r);
        FormKey F(string edid) => byEdid.TryGetValue(edid, out var r) ? r.FormKey : FormKey.Null;
        var q = mine.Quests.Single(x => x.EditorID == "ARG_BlockTest");
        var endQ = mine.Quests.Single(x => x.EditorID == "ARG_BlockTestEnd");
        var vm = q.VirtualMachineAdapter!;
        var main = vm.Scripts.Single(s => s.Name == "ARG_QF_BlockTest");
        var placed = mine.EnumerateMajorRecords<IPlacedGetter>().ToDictionary(r => r.FormKey);
        var infos = mine.DialogTopics.SelectMany(t => t.Responses.Select(i => (t, i))).ToList();
        var fails = 0;
        string[] pexLog = File.Exists(Path.Combine(pexDir, "..", "compile.log")) ? File.ReadAllLines(Path.Combine(pexDir, "..", "compile.log")) : [];

        bool Pex(string script, params string[] strings)
        {
            var f = Path.Combine(pexDir, script + ".pex");
            if (!File.Exists(f)) return false;
            var text = Encoding.Latin1.GetString(File.ReadAllBytes(f)).ToLowerInvariant();
            return strings.All(s => text.Contains(s.ToLowerInvariant()));
        }
        bool Prop(string name, FormKey want, short alias = -1) =>
            main.Properties.OfType<IScriptObjectPropertyGetter>().Any(p => p.Name == name && p.Object.FormKey == want && p.Alias == alias);
        bool Frag(int stage) => vm.Fragments.Any(f => f.Stage == stage && f.StageIndex == 0 && f.ScriptName == "ARG_QF_BlockTest" && f.FragmentName == $"Fragment_{stage}")
            && q.Stages.Any(s => s.Index == stage && s.LogEntries.Count >= 1) && Pex("ARG_QF_BlockTest", $"Fragment_{stage}");
        bool Obj(int i) => q.Objectives.Any(o => o.Index == i && !string.IsNullOrEmpty(o.DisplayText?.String));
        IQuestAliasGetter? Al(uint id) => q.Aliases.SingleOrDefault(a => a.ID == id);
        bool Forced(uint id, string name, FormKey to) => Al(id) is { } a && a.Name == name && a.ForcedReference.FormKey == to && a.FindMatchingRefNearAlias == null && a.FindMatchingRefFromEvent == null;
        bool AliasScript(uint id, string script, params (string n, object v)[] props) =>
            vm.Aliases.Any(a => a.Property.Alias == id && a.Property.Object.FormKey == q.FormKey && a.Scripts.Any(s => s.Name == script && props.All(p =>
                s.Properties.Any(sp => sp.Name == p.n && (sp is IScriptIntPropertyGetter ip ? p.v is int v && ip.Data == v : sp is IScriptObjectPropertyGetter op && p.v is FormKey k && op.Object.FormKey == k)))));
        bool Persistent(FormKey k) => placed.TryGetValue(k, out var r) && (r.MajorRecordFlagsRaw & 0x400) != 0;
        bool Disabled(FormKey k) => placed.TryGetValue(k, out var r) && (r.MajorRecordFlagsRaw & 0x800) != 0;
        bool OnNav(FormKey k, FormKey mesh)
        {
            if (!placed.TryGetValue(k, out var r) || r.Placement is not { } p) return false;
            return Seat.Under(mods, p.Position).Any(h => h.Navmesh == mesh && Math.Abs(h.Z - p.Position.Z) < 64);
        }
        bool InShip(FormKey k) => mine.Cells.SelectMany(b => b.SubBlocks).SelectMany(s => s.Cells).Any(c => c.FormKey == BlockTest.Ship && c.Persistent.Any(r => r.FormKey == k));
        bool Parent(FormKey child, string parent) => placed.TryGetValue(child, out var r) && r is IPlacedObjectGetter o ? o.EnableParent?.Reference.FormKey == F(parent) : r is IPlacedNpcGetter n && n.EnableParent?.Reference.FormKey == F(parent);
        // A condition test: function data type, comparison, value, run-on, and its link.
        bool Has(IEnumerable<IConditionGetter> cs, Func<IConditionDataGetter, bool> data, CompareOperator op, float v, Condition.RunOnType run = Condition.RunOnType.Subject, bool or = false) =>
            cs.OfType<IConditionFloatGetter>().Any(c => data(c.Data) && c.CompareOperator == op && c.ComparisonValue == v && c.Data.RunOnType == run
                && (run != Condition.RunOnType.Reference || c.Data.Reference.FormKey == FormKey.Factory("000014:Skyrim.esm")) && c.Flags.HasFlag(Condition.Flag.OR) == or);
        bool IsKeeper(IConditionDataGetter d) => d is IGetIsIDConditionDataGetter g && g.Object.Link.FormKey == F("ARG_BT_Keeper");
        bool StageEq(IConditionDataGetter d) => d is IGetStageConditionDataGetter g && g.Quest.Link.FormKey == q.FormKey;
        (IDialogTopicGetter t, IDialogResponsesGetter i)[] Lines(string topic) => infos.Where(x => x.t.EditorID == topic).ToArray();
        bool Topic(string topic, string prompt, int? sets, Func<IReadOnlyList<IConditionGetter>, bool> conds, int index = 0)
        {
            var ls = Lines(topic); if (ls.Length <= index) return false;
            var (t, i) = ls[index];
            var branch = mine.DialogBranches.SingleOrDefault(b => b.FormKey == t.Branch.FormKey);
            var okBranch = branch != null && branch.StartingTopic.FormKey == t.FormKey && branch.Flags?.HasFlag(DialogBranch.Flag.TopLevel) == true && branch.Quest.FormKey == q.FormKey;
            var okFrag = sets is int s
                ? i.VirtualMachineAdapter?.ScriptFragments?.OnEnd is { } f && f.ScriptName == $"TIF_ARG_BT_{s}" && f.FragmentName == "Fragment_0" && Pex($"TIF_ARG_BT_{s}", "Fragment_0", "SetStage")
                : i.VirtualMachineAdapter == null;
            return okBranch && okFrag && t.Quest.FormKey == q.FormKey && i.Prompt?.String == prompt && Has(i.Conditions, IsKeeper, CompareOperator.EqualTo, 1) && conds(i.Conditions);
        }
        void Step(int n, string what, params (string name, bool ok)[] checks)
        {
            var bad = checks.Where(c => !c.ok).Select(c => c.name).ToList();
            if (bad.Count > 0) fails++;
            Console.WriteLine($"step {n,2} {(bad.Count == 0 ? "PASS" : "FAIL")} {what} ({checks.Length} checks){(bad.Count > 0 ? ": " + string.Join("; ", bad) : "")}");
        }
        var start = F("ARG_BT_StartMarker"); var keeperRef = F("ARG_BT_KeeperRef"); var walkerRef = F("ARG_BT_WalkerRef"); var crabRef = F("ARG_BT_CrabRef");
        var tokenRef = F("ARG_BT_TokenRef"); var zoneA = F("ARG_BT_ZoneA"); var zoneB = F("ARG_BT_ZoneB");
        var ours = new[] { "ARG_BT_Keeper", "ARG_BT_Walker", "ARG_BT_Crab" }.Select(e => mine.Npcs.Single(n => n.EditorID == e)).ToList();
        var walk = mine.Packages.Single(p => p.EditorID == "ARG_BT_WalkPackage");
        var scene = mine.Scenes.Single(s => s.EditorID == "ARG_BT_Scene");
        var door = (IPlacedObjectGetter)placed[BlockTest.Door];
        var ship = mine.Cells.SelectMany(b => b.SubBlocks).SelectMany(s => s.Cells).Single(c => c.FormKey == BlockTest.Ship);
        float Lvl(string e) => ours.Single(n => n.EditorID == e).Configuration.Level is INpcLevelGetter l ? l.Level : -1;

        Console.WriteLine($"compile.log: {pexLog.Length} lines, {pexLog.Count(l => l.Contains("error", StringComparison.OrdinalIgnoreCase) && !l.Contains("0 error", StringComparison.OrdinalIgnoreCase))} error lines; pex: {string.Join(", ", new[] { "ARG_QF_BlockTest", "TIF_ARG_BT_20", "TIF_ARG_BT_40", "TIF_ARG_BT_50", "TIF_ARG_BT_90", "SF_ARG_BT_Scene" }.Select(s => s + (File.Exists(Path.Combine(pexDir, s + ".pex")) ? "" : " MISSING")))}");
        Step(1, "console start, aliases, persistent refs, E-move (player), E-stage, Naga removed",
            ("quest not SGE, not run-once", !q.Flags.HasFlag(Quest.Flag.StartGameEnabled) && !q.Flags.HasFlag(Quest.Flag.RunOnce) && q.Name?.String == "Block Test"),
            ("stage 10 start-up", q.Stages.Single(s => s.Index == 10).Flags.HasFlag(QuestStage.Flag.StartUpStage)),
            ("fragment 10", Frag(10)), ("StartMarker prop", Prop("StartMarker", start)), ("objective 10", Obj(10)),
            ("aliases all forced", Forced(0, "Keeper", keeperRef) && Forced(1, "Walker", walkerRef) && Forced(2, "Crab", crabRef) && Forced(3, "Token", tokenRef) && Forced(4, "ShipDoor", BlockTest.Door) && Forced(5, "ZoneA", zoneA) && Forced(6, "ZoneB", zoneB)),
            ("walker alias AllowDisabled+Optional+Protected", Al(1)?.Flags is { } wf && wf.HasFlag(QuestAlias.Flag.AllowDisabled) && wf.HasFlag(QuestAlias.Flag.Optional) && wf.HasFlag(QuestAlias.Flag.Protected)),
            ("walker ref disabled, persistent, in 01Ship on 0AA666", Disabled(walkerRef) && Persistent(walkerRef) && InShip(walkerRef) && OnNav(walkerRef, BlockTest.ShipNavmesh)),
            ("start marker and keeper persistent on 07EEF8", Persistent(start) && Persistent(keeperRef) && OnNav(start, BlockTest.Navmesh) && OnNav(keeperRef, BlockTest.Navmesh)),
            ("five Naga overrides initially disabled", BlockTest.Naga.All(n => Disabled(FormKey.Factory(n + ":Black Marsh North.esp")))),
            ("no NPC_ of ours PC-level-mult", ours.All(n => n.Configuration.Level is INpcLevelGetter)));
        Step(2, "TR-topic, C-stage, E-item (key), E-enable (token), E-regard",
            ("line 20: GetIsID keeper, GetStage == 10, TIF_ARG_BT_20", Topic("ARG_BT_Topic20", "I am ready for the test.", 20, c => Has(c, StageEq, CompareOperator.EqualTo, 10))),
            ("fragment 20", Frag(20) && Pex("ARG_QF_BlockTest", "SetRelationshipRank", "AddItem", "Enable")), ("ShipKey prop", Prop("ShipKey", F("ARG_BT_Key"))),
            ("TokenParent prop, disabled", Prop("TokenParent", F("ARG_BT_TokenParent")) && Disabled(F("ARG_BT_TokenParent")) && Persistent(F("ARG_BT_TokenParent"))),
            ("token ref enable parent, on 07EEF8", Parent(tokenRef, "ARG_BT_TokenParent") && Persistent(tokenRef) && OnNav(tokenRef, BlockTest.Navmesh)),
            ("Keeper alias prop", Prop("Keeper", q.FormKey, 0)), ("objective 20", Obj(20)));
        Step(3, "TR-acquire, E-global",
            ("token alias: defaultSetStageOnPlayerAcquire myQST/preReqStage 20/StageToSet 30", AliasScript(3, "defaultSetStageOnPlayerAcquire", ("myQST", q.FormKey), ("preReqStage", 20), ("StageToSet", 30))),
            ("Token base is ARG_BT_Token", placed[tokenRef] is IPlacedObjectGetter t && t.Base.FormKey == F("ARG_BT_Token")),
            ("fragment 30, Standing prop", Frag(30) && Prop("Standing", F("ARG_BT_Global"))), ("objective 30", Obj(30)));
        Step(4, "TR-topic, C-item, C-global, E-item (taken), E-faction",
            ("line 40: GetItemCount token >= 1 (player), GetGlobalValue >= 1, GetStage == 30", Topic("ARG_BT_Topic40", "Here is the token.", 40, c =>
                Has(c, d => d is IGetItemCountConditionDataGetter g && g.ItemOrList.Link.FormKey == F("ARG_BT_Token"), CompareOperator.GreaterThanOrEqualTo, 1, Condition.RunOnType.Reference)
                && Has(c, d => d is IGetGlobalValueConditionDataGetter g && g.Global.Link.FormKey == F("ARG_BT_Global"), CompareOperator.GreaterThanOrEqualTo, 1)
                && Has(c, StageEq, CompareOperator.EqualTo, 30))),
            ("fragment 40, Token and DockHands props", Frag(40) && Prop("Token", F("ARG_BT_Token")) && Prop("DockHands", F("ARG_BT_Faction")) && Pex("ARG_QF_BlockTest", "RemoveItem", "SetFactionRank")));
        Step(5, "C-faction, C-skill both sides, E-move (actor from unloaded cell), E-enable, E-scene",
            ("line 50: GetInFaction == 1 (player), Speech >= 15 (player), GetStage == 40", Topic("ARG_BT_Topic50", "Talk me into it.", 50, c =>
                Has(c, d => d is IGetInFactionConditionDataGetter g && g.Faction.Link.FormKey == F("ARG_BT_Faction"), CompareOperator.EqualTo, 1, Condition.RunOnType.Reference)
                && Has(c, d => d is IGetActorValueConditionDataGetter g && g.ActorValue == ActorValue.Speech, CompareOperator.GreaterThanOrEqualTo, 15, Condition.RunOnType.Reference)
                && Has(c, StageEq, CompareOperator.EqualTo, 40))),
            ("never line: Speech >= 100 (player), GetStage == 40, no fragment", Topic("ARG_BT_Topic50Never", "Talk me into it, master.", null, c =>
                Has(c, d => d is IGetActorValueConditionDataGetter g && g.ActorValue == ActorValue.Speech, CompareOperator.GreaterThanOrEqualTo, 100, Condition.RunOnType.Reference)
                && Has(c, StageEq, CompareOperator.EqualTo, 40))),
            ("fragment 50, WalkerMarker/TalkScene/Walker props", Frag(50) && Prop("WalkerMarker", F("ARG_BT_WalkerMarker")) && Prop("TalkScene", scene.FormKey) && Prop("Walker", q.FormKey, 1) && Pex("ARG_QF_BlockTest", "MoveTo", "Start")),
            ("walker marker persistent on 07EEF8", Persistent(F("ARG_BT_WalkerMarker")) && OnNav(F("ARG_BT_WalkerMarker"), BlockTest.Navmesh)),
            ("scene: quest, actors keeper+walker aliases, 4 dialog actions each with one line", scene.Quest.FormKey == q.FormKey && scene.Actors.Select(a => a.ID).OrderBy(x => x).SequenceEqual([0u, 1u])
                && scene.Actions.Count == 4 && scene.Actions.All(a => a.Type == SceneAction.TypeEnum.Dialog && infos.Count(x => x.t.FormKey == a.Topic.FormKey) == 1)
                && scene.Actions.Count(a => a.ActorID == 0) == 2 && scene.Actions.Count(a => a.ActorID == 1) == 2));
        Step(6, "TR-scene, E-package, E-enable (a hostile), package priority",
            ("scene end fragment SF_ARG_BT_Scene sets 60", scene.VirtualMachineAdapter?.ScriptFragments?.OnEnd is { } se && se.ScriptName == "SF_ARG_BT_Scene" && Pex("SF_ARG_BT_Scene", "Fragment_0", "SetStage")),
            ("walker alias package list = ARG_BT_WalkPackage", Al(1)?.PackageData.Select(p => p.FormKey).SequenceEqual([walk.FormKey]) == true),
            ("package: Travel (016FAA) to ARG_BT_DoorMarker, GetStage >= 60", walk.PackageTemplate.FormKey == FormKey.Factory("016FAA:Skyrim.esm") && walk.OwnerQuest.FormKey == q.FormKey
                && walk.Data.Values.OfType<IPackageDataLocationGetter>().Any(l => l.Location.Target is ILocationTargetGetter t && t.Link.FormKey == F("ARG_BT_DoorMarker"))
                && Has(walk.Conditions, StageEq, CompareOperator.GreaterThanOrEqualTo, 60)),
            ("door marker persistent on 07EEF8", Persistent(F("ARG_BT_DoorMarker")) && OnNav(F("ARG_BT_DoorMarker"), BlockTest.Navmesh)),
            ("fragment 60, CrabParent prop disabled, crab enable parent, crab on 07EEF8", Frag(60) && Prop("CrabParent", F("ARG_BT_CrabParent")) && Disabled(F("ARG_BT_CrabParent")) && Parent(crabRef, "ARG_BT_CrabParent") && Persistent(crabRef) && OnNav(crabRef, BlockTest.Navmesh)),
            ("objective 60", Obj(60)));
        Step(7, "C-detected",
            ("package condition GetDetected player (on the walker)", Has(walk.Conditions, d => d is IGetDetectedConditionDataGetter g && g.TargetNpc.Link.FormKey == FormKey.Factory("000014:Skyrim.esm"), CompareOperator.GreaterThanOrEqualTo, 0)),
            ("ARG_BT_WalkerRef editor id for the console", byEdid.ContainsKey("ARG_BT_WalkerRef")));
        Step(8, "save and reload mid-quest",
            ("every ref a block names is persistent", new[] { start, keeperRef, walkerRef, crabRef, tokenRef, zoneA, zoneB, F("ARG_BT_WalkerMarker"), F("ARG_BT_DoorMarker"), F("ARG_BT_TokenParent"), F("ARG_BT_CrabParent"), BlockTest.Door }.All(Persistent)));
        Step(9, "TR-death, W-fixed",
            ("crab alias: defaultSetStageOnDeathRefAlias myQST/preReqStage 60/StageToSet 65", AliasScript(2, "defaultSetStageOnDeathRefAlias", ("myQST", q.FormKey), ("preReqStage", 60), ("StageToSet", 65))),
            ("crab fixed level 4 (keeper and walker 5), no Stats template flag", Lvl("ARG_BT_Crab") == 4 && Lvl("ARG_BT_Keeper") == 5 && Lvl("ARG_BT_Walker") == 5 && ours.All(n => !n.Configuration.TemplateFlags.HasFlag(NpcConfiguration.TemplateFlag.Stats))),
            ("crab base EncMudcrabLarge template", ours[2].Template.FormKey == FormKey.Factory("0E4011:Skyrim.esm")),
            ("fragment 65, objective 65", Frag(65) && Obj(65)));
        bool ZoneOk(FormKey z, int stage) => placed[z] is IPlacedObjectGetter o && o.Base.FormKey == FormKey.Factory("099312:Skyrim.esm") && o.Primitive?.Type == PlacedPrimitive.TypeEnum.Box
            && o.VirtualMachineAdapter?.Scripts.Any(s => s.Name.Equals("defaultSetStageTrigScript", StringComparison.OrdinalIgnoreCase)
                && s.Properties.OfType<IScriptObjectPropertyGetter>().Any(p => p.Name == "myQuest" && p.Object.FormKey == q.FormKey)
                && s.Properties.OfType<IScriptIntPropertyGetter>().Any(p => p.Name == "prereqStageOPT" && p.Data == 65)
                && s.Properties.OfType<IScriptIntPropertyGetter>().Any(p => p.Name == "stage" && p.Data == stage)) == true && Persistent(z);
        Step(10, "TR-zone, two triggers racing",
            ("zone A (71) and B (72): defaultSetStageTrigScript myQuest/prereqStageOPT 65/stage, box, persistent", ZoneOk(zoneA, 71) && ZoneOk(zoneB, 72)),
            ("both boxes at one spot, on the ship door (within 2 m)", placed[zoneA].Placement!.Position.Equals(placed[zoneB].Placement!.Position)
                && (placed[zoneA].Placement!.Position - door.Placement!.Position).Magnitude < 150),
            ("fragments 71, 72, 75; ZoneA/ZoneB props", Frag(71) && Frag(72) && Frag(75) && Prop("ZoneA", q.FormKey, 5) && Prop("ZoneB", q.FormKey, 6) && Pex("ARG_QF_BlockTest", "Disable")),
            ("objective 75", Obj(75)));
        Step(11, "save and reload, a trigger refiring",
            ("the losing box is disabled by the winner's fragment; both persistent", Pex("ARG_QF_BlockTest", "Disable", "GetRef") && Persistent(zoneA) && Persistent(zoneB)));
        Step(12, "TR-activate, W-override (lock), setDoorAccess, W-name",
            ("door 0AA664 override: requires key ARG_BT_Key, persistent, teleport kept", door.Lock is { } lk && ((int)lk.Level & 0xFF) == 0xFF && lk.Key.FormKey == F("ARG_BT_Key") && Persistent(BlockTest.Door) && door.TeleportDestination?.Door.FormKey == FormKey.Factory("0AA837:Black Marsh.esm")),
            ("door alias: defaultSetStageAliasScript stage 80/prereqStageOPT 75/TriggerType 0 (activate)", AliasScript(4, "defaultSetStageAliasScript", ("stage", 80), ("prereqStageOPT", 75), ("TriggerType", 0))),
            ("cell 0AA665 named Test Ship", ship.Name?.String == "Test Ship"),
            ("fragment 80, objective 80", Frag(80) && Obj(80)));
        Step(13, "C-alive, C-time, TR-topic, E-item (gold), TR-chain",
            ("day line: GetDead (Crab alias) == 1, hour >= 6 and < 20, GetStageDone 80", Topic("ARG_BT_Topic90", "The crab is dead.", 90, c =>
                Has(c, d => d is IGetDeadConditionDataGetter && d.RunOnTypeIndex == 2, CompareOperator.EqualTo, 1, Condition.RunOnType.QuestAlias)
                && Has(c, d => d is IGetCurrentTimeConditionDataGetter, CompareOperator.GreaterThanOrEqualTo, 6) && Has(c, d => d is IGetCurrentTimeConditionDataGetter, CompareOperator.LessThan, 20)
                && Has(c, d => d is IGetStageDoneConditionDataGetter g && g.Quest.Link.FormKey == q.FormKey && g.Stage == 80, CompareOperator.EqualTo, 1))),
            ("night line: hour < 6 OR >= 20", Topic("ARG_BT_Topic90", "The crab is dead.", 90, c =>
                Has(c, d => d is IGetDeadConditionDataGetter && d.RunOnTypeIndex == 2, CompareOperator.EqualTo, 1, Condition.RunOnType.QuestAlias)
                && Has(c, d => d is IGetCurrentTimeConditionDataGetter, CompareOperator.LessThan, 6, or: true) && Has(c, d => d is IGetCurrentTimeConditionDataGetter, CompareOperator.GreaterThanOrEqualTo, 20)
                && Has(c, d => d is IGetStageDoneConditionDataGetter g && g.Stage == 80, CompareOperator.EqualTo, 1), index: 1)),
            ("fragment 90 and 100, Gold001 and EndQuest props", Frag(90) && Frag(100) && Prop("Gold001", FormKey.Factory("00000F:Skyrim.esm")) && Prop("EndQuest", endQ.FormKey) && Pex("ARG_QF_BlockTest", "CompleteQuest")),
            ("stage 100 log entry completes", q.Stages.Single(s => s.Index == 100).LogEntries.Any(l => l.Flags?.HasFlag(QuestLogEntry.Flag.CompleteQuest) == true)),
            ("ARG_BlockTestEnd: stage 10 start-up, completes, its journal line", endQ.Stages.Count == 1 && endQ.Stages[0].Index == 10 && endQ.Stages[0].Flags.HasFlag(QuestStage.Flag.StartUpStage)
                && endQ.Stages[0].LogEntries.Single().Flags?.HasFlag(QuestLogEntry.Flag.CompleteQuest) == true && endQ.Stages[0].LogEntries.Single().Entry?.String == "The second quest started from the first."));
        // Where the things stand (for the owner issue and the record).
        foreach (var e in new[] { "ARG_BT_StartMarker", "ARG_BT_KeeperRef", "ARG_BT_WalkerMarker", "ARG_BT_DoorMarker", "ARG_BT_CrabRef", "ARG_BT_TokenRef", "ARG_BT_ZoneA", "ARG_BT_WalkerRef" })
        {
            var p = placed[F(e)].Placement!.Position;
            var hit = Seat.Under(mods, p).Where(h => h.Navmesh == BlockTest.Navmesh || h.Navmesh == BlockTest.ShipNavmesh).Select(h => $"{h.Navmesh.IDString()} tri {h.Triangle} z {h.Z:F0}").FirstOrDefault() ?? "no navmesh";
            Console.WriteLine($"  {e} {F(e).IDString()} at {p.X:F0},{p.Y:F0},{p.Z:F0}: {hit}");
        }
        Console.WriteLine(fails == 0 ? "blocktest: every step PASS" : $"blocktest: {fails} step(s) FAIL");
        return fails == 0 ? 0 : 1;
    }
}
