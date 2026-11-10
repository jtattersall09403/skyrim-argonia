using System.Text;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;

// mqcheck <Argonia.esp> <pex dir> <plugins in load order...>: the act's quests MQ04 and MQ05 read back from the built
// plugin and the compiled scripts against the record (story/data/db quest_stage, quest_objective, quest_successor).
// Per stage: the stage is in the quest with the record's journal text and ending flag; its objectives at their index
// with the record's text; its fragment is bound and compiled; and something in the ESP sets it (a topic line's TIF
// whose .pex is compiled, a set-stage box, an alias script, or another quest's fragment that starts it). Exit 1 on any
// failure.
static class MQCheck
{
    public static int Run(string esp, string pexDir, string[] paths)
    {
        var mods = Survey.Load(paths.Append(esp));
        var mine = mods[^1];
        var fails = 0;
        string Pex(string script) { var f = Path.Combine(pexDir, script + ".pex"); return File.Exists(f) ? Encoding.Latin1.GetString(File.ReadAllBytes(f)).ToLowerInvariant() : ""; }
        var quests = new[] { ("ARG_MQ04", MQ04.Id, "ARG_QF_MQ04", MQ04.FragmentStages), ("ARG_MQ05", MQ05.Id, "ARG_QF_MQ05", MQ05.FragmentStages) };
        var placed = mine.EnumerateMajorRecords<IPlacedObjectGetter>().ToList();
        foreach (var (edid, id, frag, fragStages) in quests)
        {
            var q = mine.Quests.Single(x => x.EditorID == edid);
            var vm = q.VirtualMachineAdapter!;
            var qpex = Pex(frag);
            var objs = QuestKit.Objectives(id);
            var infos = mine.DialogTopics.Where(t => t.Quest.FormKey == q.FormKey).SelectMany(t => t.Responses).ToList();
            bool StageCond(IDialogResponsesGetter i, int s) => i.Conditions.OfType<IConditionFloatGetter>().Any(c => c.Data is IGetStageConditionDataGetter g && g.Quest.Link.FormKey == q.FormKey);
            foreach (var (s, journal, ending) in QuestKit.Stages(id))
            {
                var why = new List<string>();
                var st = q.Stages.SingleOrDefault(x => x.Index == s);
                if (st == null) why.Add("no stage");
                else
                {
                    var e = st.LogEntries.FirstOrDefault();
                    if (e?.Entry?.String != journal) why.Add("journal text differs");
                    if ((e != null && e.Flags.HasValue && e.Flags.Value.HasFlag(QuestLogEntry.Flag.CompleteQuest)) != ending) why.Add("ending flag");
                }
                var mineObjs = objs.Where(o => o.stage == s).Select((o, n) => (o, n)).ToList();
                foreach (var (o, n) in mineObjs)
                    if (!q.Objectives.Any(x => x.Index == s + n && x.DisplayText?.String == o.text)) why.Add($"objective {o.id} at {s + n}");
                if (fragStages.Contains(s))
                {
                    if (!vm.Fragments.Any(f => f.Stage == s && f.ScriptName == frag && f.FragmentName == $"Fragment_{s}")) why.Add("fragment not bound");
                    if (!qpex.Contains($"fragment_{s}")) why.Add("fragment not in .pex");
                }
                // The setter: a TIF that sets s (its .pex compiled, the info gated on this quest's stage), a box, an alias script.
                var setters = new List<string>();
                foreach (var i in infos.Where(i => i.VirtualMachineAdapter?.ScriptFragments?.OnEnd != null))
                {
                    var tif = i.VirtualMachineAdapter!.ScriptFragments!.OnEnd!.ScriptName;
                    var p = Pex(tif);
                    if (p.Contains("setstage") && File.ReadAllText(Path.Combine("papyrus", tif + ".psc")).Contains($"SetStage({s})") && StageCond(i, s)) setters.Add(tif);
                }
                foreach (var z in placed.Where(z => z.VirtualMachineAdapter?.Scripts.Any(sc => sc.Name == "defaultSetStageTrigScript") == true))
                {
                    var sc = z.VirtualMachineAdapter!.Scripts.First(x => x.Name == "defaultSetStageTrigScript");
                    if (sc.Properties.OfType<IScriptObjectPropertyGetter>().Any(p => p.Name == "myQuest" && p.Object.FormKey == q.FormKey)
                        && sc.Properties.OfType<IScriptIntPropertyGetter>().Any(p => p.Name == "stage" && p.Data == s)) setters.Add("zone " + z.EditorID);
                }
                foreach (var a in vm.Aliases)
                    foreach (var sc in a.Scripts)
                        if (sc.Properties.OfType<IScriptIntPropertyGetter>().Any(p => p.Name == "StageToSet" && p.Data == s)) setters.Add($"alias {a.Property.Alias} {sc.Name}");
                // Started from another quest's fragment (NextQuest.SetStage(10)).
                foreach (var other in mine.Quests.Where(o => o.VirtualMachineAdapter != null && o.FormKey != q.FormKey))
                    foreach (var sc in other.VirtualMachineAdapter!.Scripts)
                        if (sc.Properties.OfType<IScriptObjectPropertyGetter>().Any(p => p.Name == "NextQuest" && p.Object.FormKey == q.FormKey)
                            && File.Exists(Path.Combine("papyrus", sc.Name + ".psc")) && File.ReadAllText(Path.Combine("papyrus", sc.Name + ".psc")).Contains($"NextQuest.SetStage({s})")
                            && Pex(sc.Name).Contains("setstage")) setters.Add($"{other.EditorID} {sc.Name}");
                if (setters.Count == 0 && !(edid == "ARG_MQ04" && s == 10)) why.Add("nothing sets it");
                var setBy = setters.Count == 0 ? (s == 10 ? "ARG_MQ03 (its lane)" : "-") : string.Join(", ", setters.Distinct());
                Console.WriteLine($"{(why.Count == 0 ? "PASS" : "FAIL")} {edid} {s}: set by {setBy}{(why.Count == 0 ? "" : "; " + string.Join("; ", why))}");
                if (why.Count > 0) fails++;
            }
            // The wording bands: each gate's variants_high / variants_low (QuestKit.BandLines), found by its default's lines.
            // MQ05's word is one INFO (the speech gate's lines); the record's item and default gates of it are not built
            var gates = QuestKit.Gates($"topic.{edid[4..].ToLower()}-").Where(g => !(g.topic == "topic.mq05-the-word" && g.gate != "speech")).ToList();
            ChainbreakersCheck.BandsBy(mine, q, (said, band) => gates.Where(g => QuestKit.Lines(g.topic, g.speaker, g.gate).SequenceEqual(said))
                .Select(g => QuestKit.BandLines(g.topic, g.speaker, g.gate, band)).FirstOrDefault(),
                gates.Sum(g => (QuestKit.BandLines(g.topic, g.speaker, g.gate, "low").Count > 0 ? 1 : 0) + (QuestKit.BandLines(g.topic, g.speaker, g.gate, "high").Count > 0 ? 1 : 0)),
                (w, ok, d) => { Console.WriteLine($"{(ok ? "PASS" : "FAIL")} {w}{(ok ? "" : "; " + d)}"); if (!ok) fails++; });
        }
        void Shape(string what, bool ok) { Console.WriteLine($"{(ok ? "PASS" : "FAIL")} {what}"); if (!ok) fails++; }
        var q4 = mine.Quests.Single(x => x.EditorID == "ARG_MQ04"); var q5 = mine.Quests.Single(x => x.EditorID == "ARG_MQ05"); var lq30 = mine.Quests.Single(x => x.EditorID == "ARG_LQ30");
        bool Stage(IDialogResponsesGetter i, IQuestGetter q, CompareOperator op, int v) => i.Conditions.OfType<IConditionFloatGetter>().Any(c => c.Data is IGetStageConditionDataGetter g && g.Quest.Link.FormKey == q.FormKey && c.CompareOperator == op && c.ComparisonValue == v);
        IEnumerable<IDialogResponsesGetter> Infos(string topic) => mine.DialogTopics.Single(t => t.EditorID == topic).Responses;
        foreach (var q in new[] { q4, q5 })
        {
            Shape($"{q.EditorID} every objective has a compass target", q.Objectives.All(o => o.Targets.Count > 0));
            Shape($"{q.EditorID} Run Once", q.Flags.HasFlag(Quest.Flag.RunOnce));
        }
        Shape("MQ04 the cut root (CutRootMark) is a forced alias and the target of 20 and 45", q4.Aliases.Any(a => a.Name == "CutRootMark" && !a.ForcedReference.IsNull)
            && new ushort[] { 20, 45 }.All(i => q4.Objectives.Single(o => o.Index == i).Targets.Any(t => t.AliasID == MQ04.AMark)));
        Shape("MQ04 Cut: the repeat INFO (>= 40) ends before 91 and asks 'Tell me about the cut root again.'", Infos("ARG_MQ04_CutTopic").Where(i => Stage(i, q4, CompareOperator.GreaterThanOrEqualTo, 40))
            .All(i => Stage(i, q4, CompareOperator.LessThan, 91) && i.Prompt?.String == "Tell me about the cut root again."));
        Shape("MQ05 no KaskaGoPost, EiTujaGoPost or their markers", !mine.Packages.Any(p => p.EditorID is "ARG_MQ05_KaskaGoPost" or "ARG_MQ05_EiTujaGoPost") && !mine.EnumerateMajorRecords<IPlacedObjectGetter>().Any(r => r.EditorID is "ARG_MQ05_KaskaPost" or "ARG_MQ05_EiTujaPost"));
        var word = Infos("ARG_MQ05_WordTopic").ToList();
        Shape("MQ05 Word: one INFO at stage 10 setting 20, no skill, gold or item check", word.Count == 1 && Stage(word[0], q5, CompareOperator.EqualTo, 10) && word[0].VirtualMachineAdapter?.ScriptFragments?.OnEnd?.ScriptName == "TIF_ARG_MQ05_20"
            && !word[0].Conditions.Any(c => c.Data is IGetActorValueConditionDataGetter or IGetItemCountConditionDataGetter) && word[0].Responses.Count == 5);
        Shape("MQ05 Quarrel and Watch end before 91; Basin ends before 91 and not while LQ30 is at 30", new[] { "ARG_MQ05_QuarrelTopic", "ARG_MQ05_WatchTopic" }.All(t => Infos(t).All(i => Stage(i, q5, CompareOperator.LessThan, 91)))
            && Infos("ARG_MQ05_BasinTopic").All(i => Stage(i, q5, CompareOperator.LessThan, 91) && Stage(i, lq30, CompareOperator.NotEqualTo, 30)));
        Shape("MQ05 Kaska-Meen and Ei-Tuja aliases Protected; deaths 10 -> 92 and 10 -> 91", new[] { MQ05.AKaska, MQ05.AEiTuja }.All(a => q5.Aliases.Single(x => x.ID == a).Flags?.HasFlag(QuestAlias.Flag.Protected) == true)
            && new[] { (MQ05.AKaska, 92), (MQ05.AEiTuja, 91) }.All(d => q5.VirtualMachineAdapter!.Aliases.Any(x => x.Property.Alias == d.Item1 && x.Scripts.Any(sc => sc.Name == "defaultSetStageOnDeathRefAlias"
                && sc.Properties.OfType<IScriptIntPropertyGetter>().Any(p => p.Name == "preReqStage" && p.Data == 10) && sc.Properties.OfType<IScriptIntPropertyGetter>().Any(p => p.Name == "StageToSet" && p.Data == d.Item2)))));
        Console.WriteLine(fails == 0 ? "mqcheck: all stages pass" : $"mqcheck: {fails} stage(s) fail");
        return fails == 0 ? 0 : 1;
    }
}
