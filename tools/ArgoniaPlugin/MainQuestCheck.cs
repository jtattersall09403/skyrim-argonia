using System.Text;
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;

// mainquestcheck <Argonia.esp> <pex dir> <plugins in load order...>: the read-back of MQ01 and MQ03 (Phase 4 part D) from
// the built plugin and the compiled scripts, against the records: every stage's journal text and Complete flag (the
// record's journal rows), every objective (the record's objective rows), every fragment in the VMAD and the .pex with its
// calls, every alias (forced ref, flags, packages and scripts), every zone (quest, prereq, stage), every enable parent,
// every line (the topic's JSON: prompt, text in order, speaker as the record's person, stage and gate conditions, fragment
// .pex), MQ101's start, ARG_Opening retired, and the placements on their navmesh. Exit 1 on any failure.
static class MainQuestCheck
{
    static IEnumerable<JsonElement> Rows(string t) => File.ReadLines(Path.Combine("story", "data", "db", t + ".jsonl")).Where(l => l.Trim().Length > 0).Select(l => JsonDocument.Parse(l).RootElement);

    public static int Run(string esp, string pexDir, string[] paths)
    {
        var mods = Survey.Load(paths.Append(esp));
        var mine = mods[^1];
        var byEdid = mine.EnumerateMajorRecords().Where(r => r.EditorID != null && r.FormKey.ModKey == mine.ModKey).GroupBy(r => r.EditorID!).ToDictionary(g => g.Key, g => g.First());
        FormKey F(string edid) => byEdid.TryGetValue(edid, out var r) ? r.FormKey : FormKey.Null;
        var placed = mine.EnumerateMajorRecords<IPlacedGetter>().GroupBy(r => r.FormKey).ToDictionary(g => g.Key, g => g.First());
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
        bool Disabled(FormKey k) => placed.TryGetValue(k, out var r) && (r.MajorRecordFlagsRaw & 0x800) != 0;
        (FormKey, bool) ParentOf(FormKey k) => placed.TryGetValue(k, out var r) ? r switch
        {
            IPlacedObjectGetter o when o.EnableParent != null => (o.EnableParent.Reference.FormKey, o.EnableParent.Flags.HasFlag(EnableParent.Flag.SetEnableStateToOppositeOfParent)),
            IPlacedNpcGetter n when n.EnableParent != null => (n.EnableParent.Reference.FormKey, n.EnableParent.Flags.HasFlag(EnableParent.Flag.SetEnableStateToOppositeOfParent)),
            _ => (FormKey.Null, false),
        } : (FormKey.Null, false);
        IEnumerable<IConditionFloatGetter> Cf(IReadOnlyList<IConditionGetter> cs) => cs.OfType<IConditionFloatGetter>();
        bool StageCond(IReadOnlyList<IConditionGetter> cs, IQuestGetter q, CompareOperator op, int s) => Cf(cs).Any(c => c.Data is IGetStageConditionDataGetter g && g.Quest.Link.FormKey == q.FormKey && c.CompareOperator == op && c.ComparisonValue == s);
        bool DoneCond(IReadOnlyList<IConditionGetter> cs, IQuestGetter q, int s) => Cf(cs).Any(c => c.Data is IGetStageDoneConditionDataGetter g && g.Quest.Link.FormKey == q.FormKey && g.Stage == s && c.ComparisonValue == 1);
        bool GlobCond(IReadOnlyList<IConditionGetter> cs, string g, int v) => Cf(cs).Any(c => c.Data is IGetGlobalValueConditionDataGetter d && d.Global.Link.FormKey == F(g) && c.ComparisonValue == v);
        bool ItemCond(IReadOnlyList<IConditionGetter> cs, string item) => Cf(cs).Any(c => c.Data is IGetItemCountConditionDataGetter d && d.ItemOrList.Link.FormKey == F(item) && c.ComparisonValue == 1 && c.Data.RunOnType == Condition.RunOnType.Reference);
        bool SpeechCond(IReadOnlyList<IConditionGetter> cs, CompareOperator op) => Cf(cs).Any(c => c.Data is IGetActorValueConditionDataGetter d && d.ActorValue == ActorValue.Speech && c.ComparisonValue == 25 && c.CompareOperator == op);
        // The speaker: GetIsID on each of our bases that speak for the record's person (OR-joined), and on nothing else.
        bool SpeakerIs(IReadOnlyList<IConditionGetter> cs, string person)
        {
            var ids = Cf(cs).Where(c => c.Data is IGetIsIDConditionDataGetter).Select(c => ((IGetIsIDConditionDataGetter)c.Data).Object.Link.FormKey).ToHashSet();
            var want = person switch
            {
                "npc.pirate-freeholds.opening-work-barge.npc-opening-overseer" => new[] { "ARG_MQ01_WuleenSei" },
                "npc.pirate-freeholds.opening-work-barge.npc-opening-roll-reader" => ["ARG_MQ01_UxXeek", "ARG_MQ01_UxXeekMarch"],
                "npc.mercantile-coast.lilmoth.broker-buys-the-months" => ["ARG_MQ01_BuysTheMonths"],
                "npc.pirate-freeholds.opening-work-camp.n1-2" => ["ARG_MQ01_DivesWithoutARope", "ARG_MQ01_DivesWithoutARopeMarch"],
                "npc.pirate-freeholds.opening-work-camp.n1" => ["ARG_MQ01_TiesTheLoosePlank"],
                "npc.nesh-deeka" => ["ARG_MQ03_NeshDeeka"],
                "npc.dunmer-north.stormhold.reed-officer" => ["ARG_MQ03_NeverWritesTwice"],
                _ => [],
            };
            return want.Length > 0 && ids.SetEquals(want.Select(F));
        }

        // The record's topics (speaker), so the JSON's speaker is checked against the record too.
        var recTopics = new Dictionary<string, string>();
        foreach (var r in Rows("quest_topic")) if (r.TryGetProperty("id", out var id) && r.TryGetProperty("person", out var p) && p.ValueKind == JsonValueKind.String) recTopics[id.GetString()!] = p.GetString()!;

        void QuestCheck(string code, string recId, string edid, string script, int[] hidden, int[] ends, Dictionary<int, string[]> calls, int extraBands = 0)
        {
            Console.WriteLine($"{code} {recId}");
            var q = mine.Quests.Single(x => x.EditorID == edid);
            var vm = q.VirtualMachineAdapter!;
            Check($"{code} Main Quest, Run Once, not start-enabled", q.Type == Quest.TypeEnum.MainQuest && q.Flags.HasFlag(Quest.Flag.RunOnce) && !q.Flags.HasFlag(Quest.Flag.StartGameEnabled));
            var zoneKeys = mine.EnumerateMajorRecords<IPlacedObjectGetter>().Where(z => z.VirtualMachineAdapter?.Scripts.Any(sc => sc.Name == "defaultSetStageTrigScript"
                && sc.Properties.OfType<IScriptObjectPropertyGetter>().Any(pr => pr.Name == "myQuest" && pr.Object.FormKey == q.FormKey)) == true).Select(z => z.FormKey).ToHashSet();
            var bound = vm.Scripts.Single(x => x.Name == script).Properties.OfType<IScriptObjectListPropertyGetter>().SingleOrDefault(pr => pr.Name == "Zones")?.Objects.Select(o => o.Object.FormKey).ToHashSet() ?? [];
            Check($"{code} Zones property is exactly the quest's {zoneKeys.Count} zones", zoneKeys.Count > 0 && bound.SetEquals(zoneKeys));
            Check($"{code} every objective has a target", q.Objectives.All(o => o.Targets.Count > 0));
            var journal = Rows("quest_stage").Where(r => r.GetProperty("quest_id").GetString() == recId && r.TryGetProperty("journal_text", out var jt) && jt.ValueKind == JsonValueKind.String).ToDictionary(r => r.GetProperty("id").GetInt32(), r => r.GetProperty("journal_text").GetString()!);
            var st0 = q.Stages.SingleOrDefault(s => s.Index == 0);
            Check($"{code} stage 0 start-up, empty", st0 != null && st0.Flags.HasFlag(QuestStage.Flag.StartUpStage) && string.IsNullOrEmpty(st0.LogEntries.FirstOrDefault()?.Entry?.String));
            foreach (var s in journal.Keys.Concat(hidden))
            {
                var st = q.Stages.SingleOrDefault(x => x.Index == s);
                Check($"{code} stage {s} exists", st != null);
                if (st == null) continue;
                var e = st.LogEntries.FirstOrDefault();
                Check($"{code} stage {s} journal {(hidden.Contains(s) ? "empty (hidden)" : "is the record's")}", hidden.Contains(s) ? string.IsNullOrEmpty(e?.Entry?.String) : e?.Entry?.String == journal[s]);
                Check($"{code} stage {s} Complete flag {ends.Contains(s)}", e != null && (e.Flags ?? 0).HasFlag(QuestLogEntry.Flag.CompleteQuest) == ends.Contains(s));
                Check($"{code} stage {s} fragment in VMAD", vm.Fragments.Any(f => f.Stage == s && f.StageIndex == 0 && f.ScriptName == script && f.FragmentName == $"Fragment_{s}"));
                Check($"{code} stage {s} fragment in .pex with its calls", Pex(script, [$"Fragment_{s}", .. calls.GetValueOrDefault(s, [])]));
            }
            foreach (var (stage, index, text) in MainQuest.Objectives(recId))
                Check($"{code} objective {index} (stage {stage}) is the record's", q.Objectives.Any(o => o.Index == index && o.DisplayText?.String == text));
            foreach (var p in vm.Scripts.Single(x => x.Name == script).Properties)
                Check($"{code} property {p.Name} set", p switch { IScriptObjectPropertyGetter o => !o.Object.FormKey.IsNull, IScriptObjectListPropertyGetter l => l.Objects.Count > 0, _ => true });
            foreach (var a in q.Aliases)
            {
                Check($"{code} alias {a.Name} forced to a persistent ref", a.ForcedReference.FormKey is var k && !k.IsNull && (Persistent(k) || placed.ContainsKey(k) == false && k.ModKey != mine.ModKey));
                if (Disabled(a.ForcedReference.FormKey) || ParentOf(a.ForcedReference.FormKey).Item1 != FormKey.Null)
                    Check($"{code} alias {a.Name} may start disabled: Allow Disabled", a.Flags?.HasFlag(QuestAlias.Flag.AllowDisabled) == true);
            }
            // The lines: every info of every topic of the JSON, as built.
            var lines = MainQuest.LinesOf(code.ToLowerInvariant());
            foreach (var tp in lines.EnumerateObject())
            {
                var topicId = $"ARG_{code}_" + string.Concat(tp.Name.Split('-').Skip(1).Select(p => char.ToUpper(p[0]) + p[1..]));
                var person = tp.Value.GetProperty("speaker").GetString()!;
                Check($"{code} {tp.Name} speaker is the record's", recTopics.Count == 0 || recTopics.GetValueOrDefault(tp.Name) == person);
                var t = mine.DialogTopics.SingleOrDefault(x => x.EditorID == topicId);
                if (t != null && t.Category != DialogTopic.CategoryEnum.Topic)
                {   // a line said by a fragment (QuestKit.Shout: a Misc topic of the quest, no prompt), not a player topic
                    var said = tp.Value.GetProperty("infos").EnumerateArray().Select(v => v.GetProperty("lines").EnumerateArray().Select(l => l.GetString()!).ToArray()).ToList();
                    Check($"{code} {tp.Name}: a said line of the quest, its lines in order", t.Quest.FormKey == q.FormKey
                        && said.All(tx => t.Responses.Any(i => i.Responses.Select(r => r.Text.String).SequenceEqual(tx))));
                    continue;
                }
                // a top-level topic starts its own branch; a choice (TR-choice) sits in its question's branch, linked from it
                bool choice = t != null && mine.DialogTopics.Any(o => o.Branch.FormKey == t.Branch.FormKey && o.Responses.Any(r => r.LinkTo.Any(l => l.FormKey == t.FormKey)));
                Check($"{code} topic {topicId} built, {(choice ? "a choice linked from its question's branch" : "top-level player branch")} of the quest", t != null && t.Quest.FormKey == q.FormKey
                    && mine.DialogBranches.Any(b => b.FormKey == t.Branch.FormKey && (choice || b.StartingTopic.FormKey == t.FormKey) && b.Flags?.HasFlag(DialogBranch.Flag.TopLevel) == true && b.Quest.FormKey == q.FormKey));
                if (t == null) continue;
                foreach (var v in tp.Value.GetProperty("infos").EnumerateArray())
                {
                    var text = v.GetProperty("lines").EnumerateArray().Select(l => l.GetString()!).ToArray();
                    var prompt = v.GetProperty("prompt").GetString()!;
                    var info = t.Responses.FirstOrDefault(i => i.Prompt?.String == prompt && i.Responses.Select(r => r.Text.String).SequenceEqual(text));
                    Check($"{code} {tp.Name}/{v.GetProperty("variant").GetString()} prompt and lines loaded in order", info != null);
                    if (info != null) Check($"{code} {tp.Name}/{v.GetProperty("variant").GetString()} speaker", SpeakerIs(info.Conditions, person));
                }
            }
            // The wording bands: each info's lines@high / lines@low, found by its default's lines.
            var infosJ = lines.EnumerateObject().SelectMany(tp => tp.Value.GetProperty("infos").EnumerateArray()).ToList();
            static List<string> Strs(JsonElement e) => [.. e.EnumerateArray().Select(l => l.GetString()!)];
            ChainbreakersCheck.BandsBy(mine, q, (said, band) => infosJ.Where(v => Strs(v.GetProperty("lines")).SequenceEqual(said) && v.TryGetProperty($"lines@{band}", out _))
                .Select(v => Strs(v.GetProperty($"lines@{band}"))).FirstOrDefault(), infosJ.Sum(v => v.EnumerateObject().Count(p => p.Name.StartsWith("lines@"))) + extraBands, (w, ok, _) => Check(w, ok));
        }
        IQuestGetter Q(string e) => mine.Quests.Single(x => x.EditorID == e);
        // An info of a topic, by its order, with a gate predicate and its fragment's call in the .pex (null: no fragment).
        void Info(string topic, int n, string what, Func<IReadOnlyList<IConditionGetter>, bool> gate, string? call)
        {
            var t = mine.DialogTopics.SingleOrDefault(x => x.EditorID == topic);
            // any info of the topic (the order of INFOs is the engine's, not checked): its gate and its fragment's call
            Check($"{topic} ({n}) {what}", t != null && t.Responses.Any(i => gate(i.Conditions) && (call == null ? i.VirtualMachineAdapter == null
                : i.VirtualMachineAdapter?.ScriptFragments?.OnEnd is { } frag && Pex(frag.ScriptName, "Fragment_0", call))));
        }
        void Zone(string edid, string quest, int prereq, int stage, string? parent = null)
        {
            var k = F(edid);
            Check($"{edid}: {quest} prereq {prereq} sets {stage}{(parent != null ? $", under {parent}" : "")}", placed.TryGetValue(k, out var r) && r is IPlacedObjectGetter z && z.Primitive != null
                && z.VirtualMachineAdapter!.Scripts.Any(s => s.Name == "defaultSetStageTrigScript"
                && s.Properties.OfType<IScriptIntPropertyGetter>().Any(p => p.Name == "prereqStageOPT" && p.Data == prereq) && s.Properties.OfType<IScriptIntPropertyGetter>().Any(p => p.Name == "stage" && p.Data == stage)
                && s.Properties.OfType<IScriptObjectPropertyGetter>().Any(p => p.Name == "myQuest" && p.Object.FormKey == F(quest)))
                && ParentOf(k).Item1 == (parent == null ? FormKey.Null : F(parent)) && Persistent(k));
        }
        void Pkg(string quest, uint alias, string pkg, Func<IReadOnlyList<IConditionGetter>, bool> gate)
        {
            var q = Q(quest); var p = mine.Packages.SingleOrDefault(x => x.EditorID == pkg);
            Check($"{quest} alias {alias} carries {pkg} with its stage gate", p != null && q.Aliases.Single(a => a.ID == alias).PackageData.Any(l => l.FormKey == p.FormKey) && gate(p.Conditions));
        }

        // ---- MQ01 ----
        var m1 = Q("ARG_MQ01"); var m3 = Q("ARG_MQ03");
        // (the stage 30, 32 and 40 calls are those of the march: the walkers' 3D loaded, then the package evaluated; they read the new .pex)
        QuestCheck("MQ01", "quest.main.mq01", "ARG_MQ01", "ARG_QF_MQ01", [32], [90, 91, 93], new()
        {
            [10] = ["Enable", "SetObjectiveDisplayed"], [20] = ["Lock", "SetObjectiveCompleted", "SetObjectiveDisplayed"], [30] = ["Enable", "Disable", "RegisterForSingleUpdate", "SetObjectiveDisplayed"], [32] = ["EvaluatePackage"],
            [40] = ["Enable", "Disable", "Kill", "MoveTo", "Clear", "AtFire"], [41] = ["Choose", "choiceTaken", "GetStageDone"],
            [42] = ["Choose", "choiceTaken", "GetStageDone"], [90] = ["Ending", "endTaken", "AddItem", "SetValue", "DisarmZones"], [91] = ["Ending", "endTaken", "SetValue"], [93] = ["Ending", "Kill"],
        });
        Check("MQ01 chargen and stage 10 in the quest script (.pex)", Pex("ARG_QF_MQ01", "ShowRaceMenu", "OnUpdate", "IsRunning") && Pex("ARG_QF_MQ01", "Ending", "Stop", "NextQuest"));
        var mq101 = mine.Quests.SingleOrDefault(x => x.FormKey == FormKey.Factory("03372B:Skyrim.esm"));
        Check("MQ101's override starts ARG_MQ01 at the hold's start marker", mq101?.VirtualMachineAdapter?.Scripts.Single().Properties.OfType<IScriptObjectPropertyGetter>()
            .Any(p => p.Name == "StartQuest" && p.Object.FormKey == m1.FormKey) == true
            && mq101.VirtualMachineAdapter.Scripts.Single().Properties.OfType<IScriptObjectPropertyGetter>().Any(p => p.Name == "StartMarker" && p.Object.FormKey == F("ARG_MQ01_StartMarker"))
            && Pex("ARG_QF_MQ101", "StartQuest", "MoveTo", "Start"));
        var opening = mine.Quests.SingleOrDefault(x => x.EditorID == "ARG_Opening");
        Check("ARG_Opening kept, never starts (not start-enabled, no script, nothing names it)", opening != null && !opening.Flags.HasFlag(Quest.Flag.StartGameEnabled) && opening.VirtualMachineAdapter == null
            && !mine.EnumerateMajorRecords().Where(r => r.FormKey != opening.FormKey).SelectMany(r => r.EnumerateFormLinks()).Any(l => l.FormKey == opening.FormKey));
        Check("MQ01 has no camp zone, wait-at-fire package or dock-end marker, and no stage 35", F("ARG_MQ01_ZoneCamp").IsNull && F("ARG_MQ01_WaitAtFire").IsNull && F("ARG_MQ01_DockEndMarker").IsNull && m1.Stages.All(x => x.Index != 35));
        Zone("ARG_MQ01_ZoneFire", "ARG_MQ01", 32, 40); Zone("ARG_MQ01_ZoneShed", "ARG_MQ01", 40, 41); Zone("ARG_MQ01_ZoneHuts", "ARG_MQ01", 40, 42);
        Zone("ARG_MQ01_ZoneShore90", "ARG_MQ01", 41, 90); Zone("ARG_MQ01_ZoneShore91", "ARG_MQ01", 42, 91); Zone("ARG_MQ01_ZoneShore93", "ARG_MQ01", 40, 93, "ARG_MQ01_Shore93Parent");
        Info("ARG_MQ01_TheRoll", 0, "Wuleen-Sei at 10 reads the roll", c => StageCond(c, m1, CompareOperator.EqualTo, 10), "ReadRoll");
        var rollT = mine.DialogTopics.Single(x => x.EditorID == "ARG_MQ01_TheRoll");
        foreach (var t in new[] { "ARG_MQ01_AnswerName", "ARG_MQ01_AnswerSilent", "ARG_MQ01_AnswerDefy" })
        {
            Info(t, 0, "an answer at 10 sets Answered and stage 20", c => StageCond(c, m1, CompareOperator.EqualTo, 10), "Answer");
            var at = mine.DialogTopics.Single(x => x.EditorID == t);
            Check($"{t} a choice the roll's INFO links to, in its branch (not top level)", at.Branch.FormKey == rollT.Branch.FormKey
                && rollT.Responses.All(r => r.LinkTo.Any(l => l.FormKey == at.FormKey)));
        }
        Check("MQ01 Answer sets Answered and stage 20; stage 20 unlocks the hold door (.pex)", Pex("ARG_QF_MQ01", "Answer", "SetStage", "Fragment_20", "Lock") && Pex("ARG_QF_MQ01", "Fragment_32", "StartMarch", "EvaluatePackage"));
        Info("ARG_MQ01_TheHire", 0, "the broker after the answer, until the strike", c => StageCond(c, m1, CompareOperator.LessThan, 40) && GlobCond(c, "ARG_MQ01_Answered", 1), null);
        Info("ARG_MQ01_TheHire", 1, "the broker before it", c => StageCond(c, m1, CompareOperator.EqualTo, 10), null);
        Info("ARG_MQ01_TheMarch", 0, "the march from 10 until the strike", c => StageCond(c, m1, CompareOperator.GreaterThanOrEqualTo, 10) && StageCond(c, m1, CompareOperator.LessThan, 40), null);
        foreach (var a in new[] { MainQuest.A1Courier, MainQuest.A1WuleenMarch, MainQuest.A1UxMarch, MainQuest.A1DivesMarch, MainQuest.A1FindsMarch })
        {
            Pkg("ARG_MQ01", a, "ARG_MQ01_MarchOff", c => StageCond(c, m1, CompareOperator.GreaterThanOrEqualTo, 32) && StageCond(c, m1, CompareOperator.LessThan, 40));
        }
        // The hold's doors (we.mq01.hold-door): the stair door the way out, paired both ways with the pier door, locked with
        // no key until 20, opening it at 20 sets 30 (TR-activate); the far door opens onto its room.
        var stair = placed.GetValueOrDefault(MainQuest.HoldDoor) as IPlacedObjectGetter; var pier = placed.GetValueOrDefault(MainQuest.PierDoor) as IPlacedObjectGetter;
        var far = placed.GetValueOrDefault(MainQuest.HoldDoorFar) as IPlacedObjectGetter;
        Check("hold stair door 0F92EC teleports to the pier door 005AB4, which teleports back", stair?.TeleportDestination?.Door.FormKey == MainQuest.PierDoor && pier?.TeleportDestination?.Door.FormKey == MainQuest.HoldDoor
            && Persistent(MainQuest.HoldDoor) && Persistent(MainQuest.PierDoor));
        Check("hold stair door locked, requires key, no key (stage 20 unlocks it)", stair?.Lock is { } lk && ((int)lk.Level & 0xFF) == 0xFF && lk.Key.IsNull);
        Check("hold far door 0F9399 has no teleport (opens onto its room)", far != null && far.TeleportDestination == null);
        Check("hold door alias: defaultSetStageAliasScript on activate, prereq 20, sets 30", m1.VirtualMachineAdapter!.Aliases.Any(a => a.Property.Alias == MainQuest.A1HoldDoor
            && a.Scripts.Any(s => s.Name == "defaultSetStageAliasScript" && s.Properties.OfType<IScriptIntPropertyGetter>().Any(p => p.Name == "stage" && p.Data == 30)
            && s.Properties.OfType<IScriptIntPropertyGetter>().Any(p => p.Name == "prereqStageOPT" && p.Data == 20) && s.Properties.OfType<IScriptIntPropertyGetter>().Any(p => p.Name == "TriggerType" && p.Data == 0))));
        foreach (var (o, a) in new[] { (10, MainQuest.A1WuleenHold), (20, MainQuest.A1HoldDoor), (30, MainQuest.A1FireMark), (40, MainQuest.A1Sal), (40, MainQuest.A1Deesh), (41, MainQuest.A1ShoreMark), (42, MainQuest.A1ShoreMark) })
            Check($"MQ01 objective {o} targets alias {a}", m1.Objectives.SingleOrDefault(x => x.Index == o)?.Targets.Any(t => t.AliasID == a) == true);
        Pkg("ARG_MQ01", MainQuest.A1Leader, "ARG_MQ01_LeaderLeaves", c => StageCond(c, m1, CompareOperator.GreaterThanOrEqualTo, 40));
        Check("MQ01 the cutters carry no package (they stay at the shed until the ending disables them)", F("ARG_MQ01_CuttersLeave").IsNull && new[] { MainQuest.A1Cutter1, MainQuest.A1Cutter2 }.All(a => m1.Aliases.Single(x => x.ID == a).PackageData.Count == 0));
        Pkg("ARG_MQ01", MainQuest.A1Sal, "ARG_MQ01_SalSeiFollows", c => StageCond(c, m1, CompareOperator.EqualTo, 41));
        Pkg("ARG_MQ01", MainQuest.A1Deesh, "ARG_MQ01_DeeshDuunFollows", c => StageCond(c, m1, CompareOperator.EqualTo, 42));
        foreach (var (a, f) in new[] { (MainQuest.A1WuleenHold, QuestAlias.Flag.Essential), (MainQuest.A1WuleenMarch, QuestAlias.Flag.Essential), (MainQuest.A1Courier, QuestAlias.Flag.Essential),
                     (MainQuest.A1Sal, QuestAlias.Flag.Essential), (MainQuest.A1Deesh, QuestAlias.Flag.Essential), (MainQuest.A1Leader, QuestAlias.Flag.Protected) })
            Check($"MQ01 alias {a} {f} (the record's build notes)", m1.Aliases.Single(x => x.ID == a).Flags?.HasFlag(f) == true);
        Check("Ties-The-Loose-Plank essential (MQ01's start to MQ03's end)", mine.Npcs.Single(n => n.EditorID == "ARG_MQ01_TiesTheLoosePlank").Configuration.Flags.HasFlag(NpcConfiguration.Flag.Essential));
        Check("the cutters unaggressive (no combat at the strike), in the Unbound Root", mine.Npcs.Single(n => n.EditorID == "ARG_MQ01_RootCutter") is var cu && cu.AIData?.Aggression == Aggression.Unaggressive && cu.Factions.Any(f => f.Faction.FormKey == F("ARG_UnboundRoot")));
        Check("hold cell: 'Dainty Sload' location cleared", mine.Cells.Records.SelectMany(b => b.SubBlocks).SelectMany(s => s.Cells).Any(c => c.FormKey == MainQuest.HoldCell && c.Location.FormKey.IsNull));
        foreach (var k in MainQuest.Valenwood.Append(MainQuest.Welcome.ToString()))
            Check($"{k} held back: not start-enabled, started by MQ03's endings", mine.Quests.SingleOrDefault(x => x.FormKey == FormKey.Factory(k)) is { } w && !w.Flags.HasFlag(Quest.Flag.StartGameEnabled)
                && m3.VirtualMachineAdapter!.Scripts.Single(s => s.Name == "ARG_QF_MQ03").Properties.OfType<IScriptObjectListPropertyGetter>().Single(p => p.Name == "Deferred").Objects.Any(o => o.Object.FormKey == w.FormKey));
        Check("MQ01's endings start MQ03 (NextQuest)", m1.VirtualMachineAdapter!.Scripts.Single(s => s.Name == "ARG_QF_MQ01").Properties.OfType<IScriptObjectPropertyGetter>().Any(p => p.Name == "NextQuest" && p.Object.FormKey == m3.FormKey));

        // ---- MQ03 ----
        QuestCheck("MQ03", "quest.main.mq03", "ARG_MQ03", "ARG_QF_MQ03", [11, 45], [90, 91], new()
        {
            [10] = ["Enable", "SetObjectiveDisplayed"], [11] = ["Alchemy", "AddItem", "SetObjectiveCompleted"], [20] = ["MoveTo", "HistHearing", "Disable", "houseTaken", "Lock"], [40] = ["MoveTo", "Lock", "Enable", "dreamStarted"],
            [45] = ["dreamTaken", "ReedSworn"], [90] = ["SetFactionRank", "AddItem", "Ending", "endTaken", "DisarmZones"], [91] = ["ReedDeclined", "Ending", "endTaken"],
        }, extraBands: 2);
        Check("MQ03 endings: Deferred starts, MQ04 at 10 when present, Stop (.pex)", Pex("ARG_QF_MQ03", "Deferred", "NextQuest", "Stop", "Unlock") || Pex("ARG_QF_MQ03", "Deferred", "NextQuest", "Stop", "Lock"));
        var mq04 = mine.Quests.SingleOrDefault(x => x.EditorID == "ARG_MQ04");
        Check($"MQ03 NextQuest is ARG_MQ04 ({(mq04 == null ? "absent: no property" : "present")})", m3.VirtualMachineAdapter!.Scripts.Single(s => s.Name == "ARG_QF_MQ03").Properties.OfType<IScriptObjectPropertyGetter>()
            .Where(p => p.Name == "NextQuest").Select(p => p.Object.FormKey).SingleOrDefault() == (mq04?.FormKey ?? FormKey.Null));
        Zone("ARG_MQ03_ZoneDoor", "ARG_MQ03", 40, 45);
        var mvm = m3.VirtualMachineAdapter!;
        bool AliasScript(uint a, string script, int pre, int set, string preName, string setName) => mvm.Aliases.Any(x => x.Property.Alias == a && x.Scripts.Any(s => s.Name == script
            && s.Properties.OfType<IScriptIntPropertyGetter>().Any(p => p.Name == preName && p.Data == pre) && s.Properties.OfType<IScriptIntPropertyGetter>().Any(p => p.Name == setName && p.Data == set)));
        Check("MQ03 10->11 the taste (TR-activate on the sap's alias)", AliasScript(MainQuest.A3Sap, "defaultSetStageAliasScript", 10, 11, "prereqStageOPT", "stage"));
        Check("MQ03 the officer (Essential) has no death trigger", !mvm.Aliases.Any(x => x.Property.Alias == MainQuest.A3Officer));
        Check("MQ03 HouseDoor is the Reed's house door", mvm.Scripts.Single(x => x.Name == "ARG_QF_MQ03").Properties.OfType<IScriptObjectPropertyGetter>().Any(p => p.Name == "HouseDoor" && p.Object.FormKey == MainQuest.HouseDoorOut));
        foreach (var (o, a) in new[] { (10, MainQuest.A3Sap), (11, MainQuest.A3Trap), (12, MainQuest.A3Officer), (20, MainQuest.A3Nesh), (21, MainQuest.A3Ties), (22, MainQuest.A3Nesh), (40, MainQuest.A3HoldDoor) })
            Check($"MQ03 objective {o} targets alias {a}", m3.Objectives.SingleOrDefault(x => x.Index == o)?.Targets.Any(t => t.AliasID == a) == true);
        Check("MQ03 20->40 Nesh-Deeka's death", AliasScript(MainQuest.A3Nesh, "defaultSetStageOnDeathRefAlias", 20, 40, "preReqStage", "StageToSet"));
        Info("ARG_MQ03_TheBoat", 0, "ready: before 20, tasted, phial or tag", c => StageCond(c, m3, CompareOperator.LessThan, 20) && DoneCond(c, m3, 11) && ItemCond(c, "ARG_MQ03_SapPhial") && ItemCond(c, "ARG_MQ03_CourierTag"), "SetStage");
        Info("ARG_MQ03_TheBoat", 1, "where things lie, from 10, before the sap is tasted (exclusive of ready)", c => StageCond(c, m3, CompareOperator.LessThan, 20) && StageCond(c, m3, CompareOperator.GreaterThanOrEqualTo, 10)
            && Cf(c).Any(x => x.Data is IGetStageDoneConditionDataGetter g && g.Quest.Link.FormKey == m3.FormKey && g.Stage == 11 && x.ComparisonValue == 0), null);
        Info("ARG_MQ03_TheBoat", 2, "where things lie, from 10, with neither phial nor tag (exclusive of ready)", c => StageCond(c, m3, CompareOperator.LessThan, 20) && StageCond(c, m3, CompareOperator.GreaterThanOrEqualTo, 10)
            && Cf(c).Any(x => x.Data is IGetItemCountConditionDataGetter d && d.ItemOrList.Link.FormKey == F("ARG_MQ03_SapPhial") && x.ComparisonValue == 0)
            && Cf(c).Any(x => x.Data is IGetItemCountConditionDataGetter d && d.ItemOrList.Link.FormKey == F("ARG_MQ03_CourierTag") && x.ComparisonValue == 0), null);
        Info("ARG_MQ03_TheAttack", 0, "with the phial, takes it", c => StageCond(c, m3, CompareOperator.EqualTo, 20) && ItemCond(c, "ARG_MQ03_SapPhial"), "TellAttack");
        Info("ARG_MQ03_TheAttack", 1, "without", c => StageCond(c, m3, CompareOperator.EqualTo, 20), "TellAttack");
        Info("ARG_MQ03_TheNight", 0, "shown the tag", c => StageCond(c, m3, CompareOperator.EqualTo, 20) && ItemCond(c, "ARG_MQ03_CourierTag"), "TellNight");
        Info("ARG_MQ03_TheNight", 1, "Speech 25", c => StageCond(c, m3, CompareOperator.EqualTo, 20) && SpeechCond(c, CompareOperator.GreaterThanOrEqualTo), "TellNight");
        Info("ARG_MQ03_TheNight", 2, "refuses below Speech 25", c => StageCond(c, m3, CompareOperator.EqualTo, 20) && SpeechCond(c, CompareOperator.LessThan), null);
        Info("ARG_MQ03_TheOffer", 0, "the offer at 20", c => StageCond(c, m3, CompareOperator.EqualTo, 20), null);
        Info("ARG_MQ03_TakeOath", 0, "once the attack is told: sworn, 40 (the night need not be: a new character cannot pass Ties's gate)", c => StageCond(c, m3, CompareOperator.EqualTo, 20) && GlobCond(c, "ARG_MQ03_AttackTold", 1) && !GlobCond(c, "ARG_MQ03_NightTold", 1), "TakeOath");
        Info("ARG_MQ03_RefuseOath", 0, "once the attack is told: 40", c => StageCond(c, m3, CompareOperator.EqualTo, 20) && GlobCond(c, "ARG_MQ03_AttackTold", 1) && !GlobCond(c, "ARG_MQ03_NightTold", 1), "SetStage");
        Check("MQ03 TakeOath sets the sworn global and 40 (.pex)", Pex("ARG_QF_MQ03", "TakeOath", "ReedSworn", "SetStage"));
        Check("MQ03 aliases: the strangers essential until 20", new[] { MainQuest.A3Officer, MainQuest.A3Stranger }.All(a => m3.Aliases.Single(x => x.ID == a).Flags?.HasFlag(QuestAlias.Flag.Essential) == true));
        Check("ARG_NeshDeekaRef is Nesh-Deeka, in the house", placed.TryGetValue(F("ARG_NeshDeekaRef"), out var nr) && nr is IPlacedNpcGetter nn && nn.Base.FormKey == F("ARG_MQ03_NeshDeeka")
            && mine.Cells.Records.SelectMany(b => b.SubBlocks).SelectMany(s => s.Cells).Single(c => c.FormKey == MainQuest.HouseCell).Persistent.Any(r => r.FormKey == nr.FormKey));
        Check("fish-trap: Novice lock, the tag in it, under water", placed.TryGetValue(F("ARG_MQ03_FishTrapRef"), out var tr) && tr is IPlacedObjectGetter to && to.Lock?.Level == LockLevel.Novice && to.Placement!.Position.Z < -100
            && mine.Containers.Single(c => c.EditorID == "ARG_MQ03_FishTrap").Items!.Single().Item.Item.FormKey == F("ARG_MQ03_CourierTag"));
        Check("house door: locked to the house key", placed.TryGetValue(MainQuest.HouseDoorOut, out var hd) && hd is IPlacedObjectGetter hdo && hdo.Lock?.Key.FormKey == F("ARG_MQ03_HouseKey"));

        // ---- People, places, enable parents ----
        Console.WriteLine("People and places");
        foreach (var (r, mesh, parent) in new (string, FormKey?, string?)[] {
            ("ARG_MQ01_StartMarker", MainQuest.HoldNav, null), ("ARG_MQ01_WuleenSeiRef", MainQuest.HoldNav, "ARG_MQ01_CrewParent"), ("ARG_MQ01_UxXeekRef", MainQuest.HoldNav, "ARG_MQ01_CrewParent"),
            ("ARG_MQ01_DivesWithoutARopeHoldRef", MainQuest.HoldNav, "ARG_MQ01_HoldParent"), ("ARG_MQ01_FindsTheOtherBankHoldRef", MainQuest.HoldNav, "ARG_MQ01_HoldParent"),
            ("ARG_MQ01_RiSakkaHoldRef", MainQuest.HoldNav, "ARG_MQ01_HoldParent"), ("ARG_MQ01_TsanjiHoldRef", MainQuest.HoldNav, "ARG_MQ01_HoldParent"), ("ARG_MQ01_LlarviMaryonHoldRef", MainQuest.HoldNav, "ARG_MQ01_HoldParent"),
            ("ARG_MQ01_BuysTheMonthsRef", MainQuest.DockNav, "ARG_MQ01_BrokerParent"), ("ARG_MQ01_MeeTujaRef", MainQuest.DockNav, null),
            ("ARG_MQ01_WuleenSeiMarchRef", MainQuest.DockNav, "ARG_MQ01_MarchParent"), ("ARG_MQ01_UxXeekMarchRef", MainQuest.DockNav, "ARG_MQ01_MarchParent"),
            ("ARG_MQ01_DivesWithoutARopeMarchRef", MainQuest.DockNav, "ARG_MQ01_MarchParent"), ("ARG_MQ01_FindsTheOtherBankMarchRef", MainQuest.DockNav, "ARG_MQ01_MarchParent"),
            ("ARG_MQ01_SalSeiRef", MainQuest.DockNav, null), ("ARG_MQ01_DeeshDuunRef", MainQuest.DockNav, null), ("ARG_MQ01_NeshNeelRef", MainQuest.DockNav, "ARG_MQ01_CampOrderly"),
            ("ARG_MQ01_CutsTheOldKnotRef", MainQuest.DockNav, "ARG_MQ01_CellParent"), ("ARG_MQ01_RootCutter1Ref", MainQuest.DockNav, "ARG_MQ01_CellParent"), ("ARG_MQ01_RootCutter2Ref", MainQuest.DockNav, "ARG_MQ01_CellParent"),
            ("ARG_MQ01_TiesTheLoosePlankRef", MainQuest.DockNav, null), ("ARG_MQ01_RiSakkaShoreRef", MainQuest.DockNav, "ARG_MQ01_SurvivorsParent"),
            ("ARG_MQ01_TsanjiShoreRef", MainQuest.DockNav, "ARG_MQ01_SurvivorsParent"), ("ARG_MQ01_LlarviMaryonShoreRef", MainQuest.DockNav, "ARG_MQ01_SurvivorsParent"),
            ("ARG_MQ01_FireMarker", MainQuest.DockNav, null), ("ARG_MQ01_ShedMarker", MainQuest.DockNav, null), ("ARG_MQ01_ShoreMarker", MainQuest.DockNav, null), ("ARG_MQ01_WaterEdgeMarker", MainQuest.DockNav, null),
            ("ARG_MQ01_HutsMarker", MainQuest.DockNav, null), ("ARG_MQ01_Campfire", null, "ARG_MQ01_CampAftermath"), ("ARG_MQ01_Hut1", null, "ARG_MQ01_CampAftermath"), ("ARG_MQ01_HutBurnt", null, "ARG_MQ01_CampAftermath"),
            ("ARG_MQ01_HutFire1", null, "ARG_MQ01_CampAttacked"),
            ("ARG_MQ03_NeverWritesTwiceRef", MainQuest.DockNav, "ARG_MQ03_ReedParent"), ("ARG_MQ03_ReedStrangerRef", MainQuest.DockNav, "ARG_MQ03_ReedParent"),
            ("ARG_MQ03_SpilledSapRef", null, "ARG_MQ03_JarParent"), ("ARG_MQ03_FishTrapRef", null, "ARG_MQ03_JarParent"), ("ARG_MQ03_Lockpick1", null, "ARG_MQ03_JarParent"),
            ("ARG_NeshDeekaRef", null, null), ("ARG_MQ03_SaltsTheCatchRef", null, null), ("ARG_MQ03_HouseMarker", null, null), ("ARG_MQ03_MatMarker", null, null),
            ("ARG_MQ03_DreamMarker", MainQuest.HoldNav, null), ("ARG_MQ03_DreamRoot1", null, "ARG_MQ03_DreamParent") })
        {
            var k = F(r);
            if (mesh is FormKey m) Check($"{r} on navmesh {m}", OnNav(k, m));
            Check($"{r} persistent", Persistent(k));
            Check($"{r} enable parent {parent ?? "none"}", ParentOf(k).Item1 == (parent == null ? FormKey.Null : F(parent)));
        }
        Check("the camp's standing things are the opposite of the aftermath", ParentOf(F("ARG_MQ01_Hut1")).Item2 && ParentOf(F("ARG_MQ01_Campfire")).Item2 && !ParentOf(F("ARG_MQ01_HutBurnt")).Item2);
        foreach (var p in new[] { "ARG_MQ01_MarchParent", "ARG_MQ01_CampOrderly", "ARG_MQ01_CampAttacked", "ARG_MQ01_CampAftermath", "ARG_MQ01_CellParent", "ARG_MQ01_SurvivorsParent", "ARG_MQ03_JarParent", "ARG_MQ03_ReedParent", "ARG_MQ03_DreamParent" })
            Check($"{p} starts disabled", placed.TryGetValue(F(p), out var pr) && pr.MajorRecordFlagsRaw == 0xC00);
        foreach (var p in new[] { "ARG_MQ01_HoldParent", "ARG_MQ01_CrewParent", "ARG_MQ01_BrokerParent", "ARG_MQ01_Shore93Parent" })
            Check($"{p} starts enabled", placed.TryGetValue(F(p), out var pr) && pr.MajorRecordFlagsRaw == 0x400);
        Check("Ties's own ref starts disabled (MQ01's endings enable it)", Disabled(F("ARG_MQ01_TiesTheLoosePlankRef")));
        foreach (var n in mine.Npcs.Where(n => n.EditorID?.StartsWith("ARG_MQ0") == true))
            Check($"{n.EditorID} fixed level", n.Configuration.Level is INpcLevelGetter);

        Console.WriteLine($"{checks - fails} of {checks} checks pass{(fails > 0 ? $", {fails} FAIL" : "")}");
        return fails > 0 ? 1 : 0;
    }
}
