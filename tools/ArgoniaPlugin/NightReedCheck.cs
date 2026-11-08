using System.Text;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;
using Noggog;

// nightreedcheck <Argonia.esp> <pex dir> <plugins in load order...>: the per-quest read-back of TG01 and TG02 (Phase 4
// part D), from the built plugin and the compiled scripts only. Per stage of each record (as re-authored in
// NightReed.cs): the stage and its log entry (text where the record has a journal, Complete/Fail flags on the endings),
// its fragment in the quest's VMAD and the .pex, the objectives it shows and completes, the lines that set it with
// their speaker, stage and skill/item/alive conditions and their TIF .pex, the aliases and their scripts (TR-death,
// TR-zone), the people on their host navmesh, persistent and behind the enable parents, and the world edits (locks).
// Exit 1 on any failure.
static class NightReedCheck
{
    public static int Run(string esp, string pexDir, string[] paths)
    {
        var mods = Survey.Load(paths.Append(esp));
        var mine = mods[^1];
        var byEdid = mine.EnumerateMajorRecords().Where(r => r.EditorID != null && r.FormKey.ModKey == mine.ModKey).GroupBy(r => r.EditorID!).ToDictionary(g => g.Key, g => g.First());
        FormKey F(string edid) => byEdid.TryGetValue(edid, out var r) ? r.FormKey : FormKey.Null;
        var placed = mine.EnumerateMajorRecords<IPlacedGetter>().GroupBy(r => r.FormKey).ToDictionary(g => g.Key, g => g.First());
        var infos = mine.DialogTopics.SelectMany(t => t.Responses.Select(i => (t, i))).ToList();
        var navs = Survey.Winners<INavigationMeshGetter>(mods.Take(mods.Count - 1).ToList());
        int fails = 0, checks = 0;
        void Check(string what, bool ok) { checks++; if (!ok) { fails++; Console.WriteLine($"  FAIL {what}"); } }
        bool Pex(string script, params string[] strings)
        {
            var f = Path.Combine(pexDir, script + ".pex");
            if (!File.Exists(f)) return false;
            var text = Encoding.Latin1.GetString(File.ReadAllBytes(f)).ToLowerInvariant();
            return strings.All(s => text.Contains(s.ToLowerInvariant()));
        }
        bool OnNav(FormKey k, FormKey mesh)
        {
            if (!placed.TryGetValue(k, out var r) || r.Placement is not { } p) return false;
            var d = navs[mesh].rec.Data!; var v = d.Vertices;
            return d.Triangles.Any(t => { var a = v[t.Vertices.X]; var b = v[t.Vertices.Y]; var c = v[t.Vertices.Z];
                return MathF.Abs(MathF.Round((a.X + b.X + c.X) / 3) - p.Position.X) < 1 && MathF.Abs(MathF.Round((a.Y + b.Y + c.Y) / 3) - p.Position.Y) < 1 && MathF.Abs(MathF.Round((a.Z + b.Z + c.Z) / 3) - p.Position.Z) < 1; });
        }
        bool Persistent(FormKey k) => placed.TryGetValue(k, out var r) && (r.MajorRecordFlagsRaw & 0x400) != 0;
        FormKey ParentOf(FormKey k) => placed.TryGetValue(k, out var r) ? r switch { IPlacedObjectGetter o => o.EnableParent?.Reference.FormKey ?? FormKey.Null, IPlacedNpcGetter n => n.EnableParent?.Reference.FormKey ?? FormKey.Null, _ => FormKey.Null } : FormKey.Null;
        bool StageCond(IReadOnlyList<IConditionGetter> cs, IQuestGetter q, CompareOperator op, int s) =>
            cs.OfType<IConditionFloatGetter>().Any(c => c.Data is IGetStageConditionDataGetter g && g.Quest.Link.FormKey == q.FormKey && c.CompareOperator == op && c.ComparisonValue == s);
        bool Speaker(IReadOnlyList<IConditionGetter> cs, string npc) => cs.OfType<IConditionFloatGetter>().Any(c => c.Data is IGetIsIDConditionDataGetter g && g.Object.Link.FormKey == F(npc) && c.ComparisonValue == 1);
        bool SpeechAtLeast(IReadOnlyList<IConditionGetter> cs, int v) => cs.OfType<IConditionFloatGetter>().Any(c => c.Data is IGetActorValueConditionDataGetter g && g.ActorValue == ActorValue.Speech && c.ComparisonValue == v && c.Data.RunOnType == Condition.RunOnType.Reference);
        bool ItemAtLeast(IReadOnlyList<IConditionGetter> cs, FormKey item, int n, bool player = true) => cs.OfType<IConditionFloatGetter>().Any(c => c.Data is IGetItemCountConditionDataGetter g && g.ItemOrList.Link.FormKey == item && c.ComparisonValue == n
            && c.CompareOperator == CompareOperator.GreaterThanOrEqualTo && (c.Data.RunOnType == Condition.RunOnType.Reference) == player);
        bool DeadIs(IReadOnlyList<IConditionGetter> cs, uint alias, int v) => cs.OfType<IConditionFloatGetter>().Any(c => c.Data is IGetDeadConditionDataGetter && c.Data.RunOnType == Condition.RunOnType.QuestAlias && c.Data.RunOnTypeIndex == alias && c.ComparisonValue == v);
        // A line of a topic: top-level branch of the quest, its conditions, and its fragment script compiled with the call.
        bool Line(string topic, IQuestGetter q, Func<IReadOnlyList<IConditionGetter>, bool> conds, string? call)
        {
            return infos.Where(x => x.t.EditorID == topic).Any(x =>
            {
                var branch = mine.DialogBranches.SingleOrDefault(b => b.FormKey == x.t.Branch.FormKey);
                var okBranch = branch != null && branch.StartingTopic.FormKey == x.t.FormKey && branch.Flags?.HasFlag(DialogBranch.Flag.TopLevel) == true && branch.Quest.FormKey == q.FormKey;
                var frag = x.i.VirtualMachineAdapter?.ScriptFragments?.OnEnd;
                var okFrag = call == null ? x.i.VirtualMachineAdapter == null
                    : frag != null && frag.FragmentName == "Fragment_0" && Pex(frag.ScriptName, "Fragment_0", call);
                return okBranch && okFrag && x.t.Quest.FormKey == q.FormKey && !string.IsNullOrWhiteSpace(x.i.Responses.FirstOrDefault()?.Text?.String) && conds(x.i.Conditions);
            });
        }
        void QuestCheck(string edid, string script, (int s, bool log, QuestLogEntry.Flag flag, string[] pexCalls)[] stages, ushort[] objectives)
        {
            var q = mine.Quests.Single(x => x.EditorID == edid);
            var vm = q.VirtualMachineAdapter!;
            foreach (var (s, log, flag, calls) in stages)
            {
                var st = q.Stages.SingleOrDefault(x => x.Index == s);
                Check($"{edid} stage {s} exists", st != null);
                if (st == null) continue;
                var e = st.LogEntries.FirstOrDefault();
                Check($"{edid} stage {s} log entry {(log ? "with" : "without")} text", e != null && string.IsNullOrWhiteSpace(e.Entry?.String) != log);
                Check($"{edid} stage {s} log flags {flag}", e != null && e.Flags == flag);
                Check($"{edid} stage {s} start-up flag only on 0", st.Flags.HasFlag(QuestStage.Flag.StartUpStage) == (s == 0));
                if (s != 0)
                {
                    Check($"{edid} stage {s} fragment in VMAD", vm.Fragments.Any(f => f.Stage == s && f.StageIndex == 0 && f.ScriptName == script && f.FragmentName == $"Fragment_{s}"));
                    Check($"{edid} stage {s} fragment in .pex with its calls", Pex(script, [$"Fragment_{s}", .. calls]));
                }
            }
            foreach (var o in objectives) Check($"{edid} objective {o}", q.Objectives.Any(x => x.Index == o && !string.IsNullOrWhiteSpace(x.DisplayText?.String)));
            foreach (var p in vm.Scripts.Single(x => x.Name == script).Properties.OfType<IScriptObjectPropertyGetter>())
                Check($"{edid} property {p.Name} set", !p.Object.FormKey.IsNull);
        }

        Console.WriteLine("TG01 A Dry Hand in a Wet City");
        var t1 = mine.Quests.Single(x => x.EditorID == "ARG_TG01"); var t2 = mine.Quests.Single(x => x.EditorID == "ARG_TG02");
        Check("TG01 Start Game Enabled, Side Quest", t1.Flags.HasFlag(Quest.Flag.StartGameEnabled) && t1.Type == Quest.TypeEnum.SideQuest);
        QuestCheck("ARG_TG01", "ARG_QF_TG01", [
            (0, false, 0, []), (20, true, 0, ["SetObjectiveDisplayed", "Enable", "AddItem"]), (30, true, 0, ["SetObjectiveCompleted"]),
            (40, true, 0, ["RemoveItem", "AddItem", "SetRelationshipRank"]), (41, true, 0, ["RemoveItem", "AddItem", "SetRelationshipRank"]),
            (90, true, QuestLogEntry.Flag.CompleteQuest, ["SetFactionRank", "SetStage", "IncSideQuests", "Stop"]),
            (91, true, QuestLogEntry.Flag.CompleteQuest, ["SetFactionRank", "SetStage", "IncSideQuests", "Stop"])], [20, 30, 31, 40]);
        var neck = F("ARG_TG01_JasperNecklace"); var gold = FormKey.Factory("00000F:Skyrim.esm");
        // 0 -> 20: Tilts-The-Jug's opening line at stage 0.
        Check("TG01 0->20 Tilts' line at stage 0 sets 20", Line("ARG_TG01_TopicTest", t1, c => Speaker(c, "ARG_TG_Tilts") && StageCond(c, t1, CompareOperator.EqualTo, 0), "SetStage"));
        Check("TG01 S'Tabi's line before 20, no fragment", Line("ARG_TG01_TopicDoor", t1, c => Speaker(c, "ARG_TG_STabi") && StageCond(c, t1, CompareOperator.LessThan, 20), null));
        // 20 -> 30: the friend on Speech 25 or 10 gold; the bed zone; either death.
        Check("TG01 20->30 friend, Speech 25", Line("ARG_TG01_TopicBed", t1, c => Speaker(c, "ARG_TG_SitsByTheWater") && StageCond(c, t1, CompareOperator.EqualTo, 20) && SpeechAtLeast(c, 25), "SetStage"));
        Check("TG01 20->30 friend, 10 gold", Line("ARG_TG01_TopicBed", t1, c => Speaker(c, "ARG_TG_SitsByTheWater") && StageCond(c, t1, CompareOperator.EqualTo, 20) && ItemAtLeast(c, gold, 10), "PayFriend") && Pex("ARG_QF_TG01", "PayFriend", "RemoveItem"));
        var zone = F("ARG_TG01_ZoneBed");
        Check("TG01 20->30 bed zone: prereq 20, stage 30, forced alias", placed[zone] is IPlacedObjectGetter z && z.VirtualMachineAdapter!.Scripts.Any(s => s.Name == "defaultSetStageTrigScript"
            && s.Properties.OfType<IScriptIntPropertyGetter>().Any(p => p.Name == "prereqStageOPT" && p.Data == 20) && s.Properties.OfType<IScriptIntPropertyGetter>().Any(p => p.Name == "stage" && p.Data == 30)
            && s.Properties.OfType<IScriptObjectPropertyGetter>().Any(p => p.Name == "myQuest" && p.Object.FormKey == t1.FormKey)) && t1.Aliases.Any(a => a.ID == NightReed.T1Zone && a.ForcedReference.FormKey == zone));
        foreach (var a in new[] { NightReed.T1Thief, NightReed.T1Friend })
            Check($"TG01 20->30 death of alias {a}", t1.VirtualMachineAdapter!.Aliases.Any(x => x.Property.Alias == a && x.Scripts.Any(s => s.Name == "defaultSetStageOnDeathRefAlias"
                && s.Properties.OfType<IScriptIntPropertyGetter>().Any(p => p.Name == "preReqStage" && p.Data == 20) && s.Properties.OfType<IScriptIntPropertyGetter>().Any(p => p.Name == "StageToSet" && p.Data == 30))));
        // 30: the necklace off the thief (Speech 35 or 60 gold, he has it); 30 -> 40/41 at Tilts with the necklace, thief alive or dead.
        Check("TG01 30 thief gives it up on Speech 35", Line("ARG_TG01_TopicGiveBack", t1, c => Speaker(c, "ARG_TG_KeepsWhatFloats") && StageCond(c, t1, CompareOperator.EqualTo, 30) && SpeechAtLeast(c, 35) && ItemAtLeast(c, neck, 1, false), "NecklaceFrom"));
        Check("TG01 30 thief sells it for 60", Line("ARG_TG01_TopicGiveBack", t1, c => Speaker(c, "ARG_TG_KeepsWhatFloats") && StageCond(c, t1, CompareOperator.EqualTo, 30) && ItemAtLeast(c, gold, 60) && ItemAtLeast(c, neck, 1, false), "NecklaceFrom"));
        Check("TG01 30->40 return, thief alive", Line("ARG_TG01_TopicReturn", t1, c => Speaker(c, "ARG_TG_Tilts") && StageCond(c, t1, CompareOperator.EqualTo, 30) && ItemAtLeast(c, neck, 1) && DeadIs(c, NightReed.T1Thief, 0), "SetStage"));
        Check("TG01 30->41 return, thief dead", Line("ARG_TG01_TopicReturn", t1, c => Speaker(c, "ARG_TG_Tilts") && StageCond(c, t1, CompareOperator.EqualTo, 30) && ItemAtLeast(c, neck, 1) && DeadIs(c, NightReed.T1Thief, 1), "SetStage"));
        Check("TG01 40->90 Bent-Spine's welcome", Line("ARG_TG01_TopicWelcome", t1, c => Speaker(c, "ARG_TG_BentSpine") && StageCond(c, t1, CompareOperator.EqualTo, 40), "SetStage"));
        Check("TG01 41->91 Bent-Spine's welcome", Line("ARG_TG01_TopicWelcome", t1, c => Speaker(c, "ARG_TG_BentSpine") && StageCond(c, t1, CompareOperator.EqualTo, 41), "SetStage"));
        Check("TG01 thief's three packages on his alias, scheduled 6/18/23", t1.Aliases.Single(a => a.ID == NightReed.T1Thief).PackageData.Count == 3
            && new[] { "ARG_TG01_ThiefDay", "ARG_TG01_ThiefEvening", "ARG_TG01_ThiefSleep" }.Zip(new[] { 6, 18, 23 }).All(p => mine.Packages.Single(x => x.EditorID == p.First).ScheduleHour == p.Second));
        Check("TG01 thief Cowardly", mine.Npcs.Single(n => n.EditorID == "ARG_TG_KeepsWhatFloats").AIData?.Confidence == Confidence.Cowardly);

        Console.WriteLine("TG02 The Drowned Lockbox");
        Check("TG02 not start-enabled (TR-chain from TG01 90/91)", !t2.Flags.HasFlag(Quest.Flag.StartGameEnabled) && t2.Type == Quest.TypeEnum.SideQuest);
        QuestCheck("ARG_TG02", "ARG_QF_TG02", [
            (0, false, 0, []), (20, true, 0, ["Enable", "SetObjectiveDisplayed"]), (21, false, 0, ["ClaimHeard"]), (22, false, 0, ["ClaimHeard"]), (23, false, 0, ["ClaimHeard"]),
            (40, true, 0, ["SetObjectiveDisplayed"]), (43, false, 0, ["SaleMade"]), (44, false, 0, ["SaleMade"]), (45, false, 0, ["SaleMade"]),
            (90, true, QuestLogEntry.Flag.CompleteQuest, ["IncSideQuests", "Stop"]), (91, true, QuestLogEntry.Flag.CompleteQuest, ["SetRelationshipRank", "IncSideQuests", "Stop"]),
            (92, true, QuestLogEntry.Flag.FailQuest, ["SetRelationshipRank", "Stop"])], [20, 41, 42]);
        Check("TG02 20 Bent-Spine's job line at 20", Line("ARG_TG02_TopicJob", t2, c => Speaker(c, "ARG_TG_BentSpine") && StageCond(c, t2, CompareOperator.EqualTo, 20), null));
        Check("TG02 20->21 Neeta-Haj's claim", Line("ARG_TG02_TopicClaimFigurine", t2, c => Speaker(c, "ARG_TG_NeetaHaj") && StageCond(c, t2, CompareOperator.EqualTo, 20), "SetStage"));
        Check("TG02 20->22 Okan-Tei's claim, Speech 30", Line("ARG_TG02_TopicClaimCharm", t2, c => Speaker(c, "ARG_TG_OkanTei") && StageCond(c, t2, CompareOperator.EqualTo, 20) && SpeechAtLeast(c, 30), "SetStage"));
        Check("TG02 20->22 Okan-Tei's claim, 20 gold", Line("ARG_TG02_TopicClaimCharm", t2, c => Speaker(c, "ARG_TG_OkanTei") && StageCond(c, t2, CompareOperator.EqualTo, 20) && ItemAtLeast(c, gold, 20), "PayOkan"));
        Check("TG02 20->23 Dar-Zeel's claim", Line("ARG_TG02_TopicClaimBeads", t2, c => Speaker(c, "ARG_TG_DarZeel") && StageCond(c, t2, CompareOperator.EqualTo, 20), "SetStage"));
        Check("TG02 21/22/23->40 guarded check in .pex", Pex("ARG_QF_TG02", "ClaimHeard", "GetStageDone", "claimsTaken"));
        var fig = F("ARG_TG02_BoneFigurine"); var charm = F("ARG_TG02_NeesakCharm"); var beads = F("ARG_TG02_GlassBeads");
        foreach (var (who, id) in new[] { ("ARG_TG_NeetaHaj", "Neeta"), ("ARG_TG_OkanTei", "Okan"), ("ARG_TG_DarZeel", "Dar") })
            Check($"TG02 40->90 hand-over to {id} with all three", Line($"ARG_TG02_TopicHandOver{id}", t2, c => Speaker(c, who) && StageCond(c, t2, CompareOperator.EqualTo, 40) && ItemAtLeast(c, fig, 1) && ItemAtLeast(c, charm, 1) && ItemAtLeast(c, beads, 1), "HandOver"));
        foreach (var (topic, who, item) in new[] { ("ARG_TG02_TopicSellFigurine", "ARG_TG_NeetaHaj", fig), ("ARG_TG02_TopicSellCharm", "ARG_TG_OkanTei", charm), ("ARG_TG02_TopicSellBeads", "ARG_TG_DarZeel", beads) })
            Check($"TG02 40->43/44/45 {topic}: Speech 30, the thing in hand", Line(topic, t2, c => Speaker(c, who) && StageCond(c, t2, CompareOperator.EqualTo, 40) && ItemAtLeast(c, item, 1) && SpeechAtLeast(c, 30), "SellBack"));
        Check("TG02 43/44/45->91 guarded check in .pex", Pex("ARG_QF_TG02", "SaleMade", "GetStageDone", "salesTaken"));
        foreach (var a in new[] { NightReed.T2Neeta, NightReed.T2Okan, NightReed.T2Dar })
            Check($"TG02 ->92 death of alias {a}", t2.VirtualMachineAdapter!.Aliases.Any(x => x.Property.Alias == a && x.Scripts.Any(s => s.Name == "defaultSetStageOnDeathRefAlias"
                && s.Properties.OfType<IScriptIntPropertyGetter>().Any(p => p.Name == "preReqStage" && p.Data == 20) && s.Properties.OfType<IScriptIntPropertyGetter>().Any(p => p.Name == "StageToSet" && p.Data == 92))));
        Check("TG01 90/91 start TG02 (NextQuest = ARG_TG02)", t1.VirtualMachineAdapter!.Scripts[0].Properties.OfType<IScriptObjectPropertyGetter>().Any(p => p.Name == "NextQuest" && p.Object.FormKey == t2.FormKey));
        var box = F("ARG_TG02_LockboxRef");
        Check("TG02 lockbox: Apprentice lock, three things, under water", placed[box] is IPlacedObjectGetter b && b.Lock?.Level == LockLevel.Apprentice && b.Placement!.Position.Z < -300
            && mine.Containers.Single(c => c.EditorID == "ARG_TG02_Lockbox").Items!.Select(i => i.Item.Item.FormKey).ToHashSet().SetEquals([fig, charm, beads]));

        Console.WriteLine("People and places");
        var p1 = F("ARG_TG01_Parent"); var p2 = F("ARG_TG02_Parent");
        foreach (var (r, mesh, parent) in new[] {
            ("ARG_TG_TiltsRef", NightReed.HouseNav, FormKey.Null), ("ARG_TG_STabiRef", NightReed.SoulrestNav, FormKey.Null),
            ("ARG_TG_KeepsWhatFloatsRef", NightReed.SoulrestNav, p1), ("ARG_TG_SitsByTheWaterRef", NightReed.SoulrestNav, p1),
            ("ARG_TG_BentSpineRef", NightReed.ChapterRoom, p1), ("ARG_TG_ChapterLookout1Ref", NightReed.ChapterRoom, p1), ("ARG_TG_ChapterLookout2Ref", NightReed.ChapterRoom, p1),
            ("ARG_TG_NeetaHajRef", NightReed.BankNav, p2), ("ARG_TG_OkanTeiRef", NightReed.BankNav, p2), ("ARG_TG_DarZeelRef", NightReed.BankNav, p2),
            ("ARG_TG01_DayMarker", NightReed.SoulrestNav, FormKey.Null), ("ARG_TG01_DrinkMarker", NightReed.SoulrestNav, FormKey.Null), ("ARG_TG01_SleepMarker", NightReed.SoulrestNav, FormKey.Null) })
        {
            var k = F(r);
            Check($"{r} on navmesh {mesh}", OnNav(k, mesh));
            Check($"{r} persistent", Persistent(k));
            Check($"{r} enable parent {(parent.IsNull ? "none" : parent.ToString())}", ParentOf(k) == parent);
        }
        Check("enable parents initially disabled", placed[p1].MajorRecordFlagsRaw == 0xC00 && placed[p2].MajorRecordFlagsRaw == 0xC00);
        foreach (var n in mine.Npcs.Where(n => n.EditorID?.StartsWith("ARG_TG_") == true))
            Check($"{n.EditorID} fixed level, not PC-level-mult", n.Configuration.Level is INpcLevelGetter && !n.Configuration.Flags.HasFlag(NpcConfiguration.Flag.Unique) == (n.EditorID == "ARG_TG_RipperEel"));
        foreach (var d in NightReed.LockedDoors)
        {
            var o = placed.TryGetValue(FormKey.Factory(d), out var r) ? r as IPlacedObjectGetter : null;
            Check($"door {d} locked, requires key, no key (level {o?.Lock?.Level}, key {o?.Lock?.Key.FormKey})", o?.Lock is { } lk && ((int)lk.Level & 0xFF) == 0xFF && lk.Key.FormKey.IsNull);
        }
        Check("trapdoor 16BF7F locked at Novice", placed.TryGetValue(NightReed.Trapdoor, out var td) && td is IPlacedObjectGetter tdo && tdo.Lock?.Level == LockLevel.Novice);

        Console.WriteLine($"{checks - fails} of {checks} checks pass{(fails > 0 ? $", {fails} FAIL" : "")}");
        return fails > 0 ? 1 : 0;
    }
}
