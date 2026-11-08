using System.Text;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;

// bccheck <Argonia.esp> <pex dir> <plugins in load order...>: Phase 4's read-back of the Chainbreakers line (part D) from
// the files the game reads: every stage's journal and objective against the story data, its fragment in the record and
// the .pex, the aliases (forced, persistent, essential; the tokens a Quest Object created in the chest), every topic's
// speaker, gates and the stage it sets, the dialogue against story/data/quest_lines. Exit 1 on any failure.
static class ChainbreakersCheck
{
    static int fails;
    static void Ok(string what, bool pass, string detail = "") { if (!pass) fails++; Console.WriteLine($"  {(pass ? "PASS" : "FAIL")} {what}{(detail.Length > 0 ? ": " + detail : "")}"); }

    public static int Run(string esp, string pexDir, string[] paths)
    {
        var mods = Survey.Load(paths.Append(esp));
        var ours = mods[^1];
        var placed = Survey.Winners<IPlacedGetter>(mods);
        bool Pex(string script, string needle)
        {
            var f = Path.Combine(pexDir, script + ".pex");
            return File.Exists(f) && Encoding.ASCII.GetString(File.ReadAllBytes(f)).Contains(needle);
        }
        const string id = "quest.bc.bc03";
        Console.WriteLine($"ARG_BC03 ({id})");
        var q = ours.Quests.First(x => x.EditorID == "ARG_BC03");
        var journal = LocalQuests.Journal(id); var objectives = LocalQuests.Objectives(id);
        int[] stages = [10, 20, 30, 90, 91, 92, 94], ends = [90, 91, 92, 94];
        Ok("Start Game Enabled, Side Quest", q.Flags.HasFlag(Quest.Flag.StartGameEnabled) && q.Type == Quest.TypeEnum.SideQuest);
        var s0 = q.Stages.FirstOrDefault(s => s.Index == 0);
        Ok("stage 0: start-up, empty", s0 != null && s0.Flags.HasFlag(QuestStage.Flag.StartUpStage) && s0.LogEntries.All(l => string.IsNullOrEmpty(l.Entry?.String)));
        Ok("stages as the record", journal.Keys.Order().SequenceEqual(stages), string.Join(",", journal.Keys.Order()));
        const string script = "ARG_QF_BC03";
        foreach (var n in stages)
        {
            var st = q.Stages.FirstOrDefault(s => s.Index == n);
            var le = st?.LogEntries.FirstOrDefault();
            var frag = q.VirtualMachineAdapter!.Fragments.FirstOrDefault(f => f.Stage == n);
            var obj = !objectives.TryGetValue(n, out var ot) || q.Objectives.FirstOrDefault(o => o.Index == n)?.DisplayText?.String == ot;
            Ok($"stage {n}", st != null && le?.Entry?.String == journal[n] && (le.Flags ?? 0).HasFlag(QuestLogEntry.Flag.CompleteQuest) == ends.Contains(n)
                && obj && frag?.FragmentName == $"Fragment_{n}" && Pex(script, $"Fragment_{n}"),
                $"journal {(le?.Entry?.String == journal[n] ? "=record" : "DIFFERS")}, objective {(objectives.ContainsKey(n) ? (obj ? "=record" : "DIFFERS") : "none")}, fragment {frag?.FragmentName ?? "MISSING"}, pex {Pex(script, $"Fragment_{n}")}");
        }
        Ok("endings complete and stop", Pex(script, "IncSideQuests") && Pex(script, "Stop"));
        Ok("ending 92 takes 50 gold and gives 100", Pex(script, "RemoveItem") && Pex(script, "AddItem"));
        foreach (var name in new[] { "Broker", "CrewBoss", "Chest" })
        {
            var a = q.Aliases.First(x => x.Name == name);
            var r = placed[a.ForcedReference.FormKey].rec;
            var essential = name == "Chest" || (a.Flags ?? 0).HasFlag(QuestAlias.Flag.Essential);
            Ok($"alias {name}", (r.MajorRecordFlagsRaw & 0x400) != 0 && essential, $"forced {a.ForcedReference.FormKey}, persistent, essential {essential}");
        }
        var chestAlias = q.Aliases.First(x => x.Name == "Chest");
        var chest = (IPlacedObjectGetter)placed[chestAlias.ForcedReference.FormKey].rec;
        Ok("chest: novice lock, owned by Ussa-Rekh", chest.Lock?.Level == LockLevel.Novice && chest.Owner.FormKey == ours.Npcs.First(n => n.EditorID == "ARG_BC03_UssaRekh").FormKey);
        var tok = q.Aliases.First(x => x.Name == "Tokens");
        Ok("F1 tokens: Quest Object, created in the chest", (tok.Flags ?? 0).HasFlag(QuestAlias.Flag.QuestObject) && tok.CreateReferenceToObject?.AliasID == (short)chestAlias.ID
            && tok.CreateReferenceToObject.Create == CreateReferenceToObject.CreateEnum.In && tok.CreateReferenceToObject.Object.FormKey == ours.MiscItems.First(m => m.EditorID == "ARG_BC03_Tokens").FormKey);
        foreach (var (alias, set) in new[] { (Chainbreakers.B3Ussa, 94), (Chainbreakers.B3Rope, 94) })
        {
            var f = q.VirtualMachineAdapter!.Aliases.FirstOrDefault(x => x.Property.Alias == alias)?.Scripts.FirstOrDefault(s => s.Name == "defaultSetStageOnDeathRefAlias");
            int P(string n) => f?.Properties.OfType<IScriptIntPropertyGetter>().FirstOrDefault(p => p.Name == n)?.Data ?? -1;
            Ok($"TR-death on alias {alias}: 10 -> {set}", P("preReqStage") == 10 && P("StageToSet") == set);
        }

        var lines = LocalQuests.Lines("bc03");
        string Base(string e) => ours.Npcs.First(n => n.EditorID == e).FormKey.ToString();
        string ussa = Base("ARG_BC03_UssaRekh"), rope = Base("ARG_BC03_HeavyRope");
        // topic, speaker, stage gate (op, value), sets, extra gate kinds, line key
        var infos = new (string topic, string key, string speaker, CompareOperator op, int stage, int? sets, string gate, string variant)[]
        {
            ("ARG_BC03_LastSeason", "topic.bc03-last-season", rope, CompareOperator.EqualTo, 0, 10, "", "lines"),
            ("ARG_BC03_LastSeason", "topic.bc03-last-season", rope, CompareOperator.GreaterThanOrEqualTo, 10, null, "", "lines"),
            ("ARG_BC03_TheSeason", "topic.bc03-the-season", ussa, CompareOperator.GreaterThanOrEqualTo, 10, null, "", "lines"),
            ("ARG_BC03_TheTokens", "topic.bc03-the-tokens", rope, CompareOperator.EqualTo, 10, 20, "global", "lines"),
            ("ARG_BC03_Brawl", "topic.bc03-brawl", rope, CompareOperator.EqualTo, 10, 30, "global", "lines"),
            ("ARG_BC03_Break", "topic.bc03-break", rope, CompareOperator.EqualTo, 20, 90, "item", "lines"),
            ("ARG_BC03_YieldTalk", "topic.bc03-yield-talk", rope, CompareOperator.EqualTo, 30, 91, "speech>=30", "lines"),
            ("ARG_BC03_YieldTalk", "topic.bc03-yield-talk", rope, CompareOperator.EqualTo, 30, null, "speech<30", "fail"),
            ("ARG_BC03_YieldPay", "topic.bc03-yield-pay", rope, CompareOperator.EqualTo, 30, 92, "item", "lines"),
        };
        foreach (var i in infos)
        {
            var t = ours.DialogTopics.First(x => x.EditorID == i.topic);
            var hits = t.Responses.Where(r => r.Conditions.Any(c => c.Data is IGetStageConditionDataGetter g && g.Quest.Link.FormKey == q.FormKey
                && c is IConditionFloatGetter cf && cf.ComparisonValue == i.stage && cf.CompareOperator == i.op)).ToList();
            bool Gate(IDialogResponsesGetter r) => i.gate switch
            {
                "global" => r.Conditions.Any(c => c.Data is IGetGlobalValueConditionDataGetter),
                "item" => r.Conditions.Any(c => c.Data is IGetItemCountConditionDataGetter),
                "speech>=30" => r.Conditions.Any(c => c.Data is IGetActorValueConditionDataGetter && c is IConditionFloatGetter f && f.ComparisonValue == 30 && f.CompareOperator == CompareOperator.GreaterThanOrEqualTo),
                "speech<30" => r.Conditions.Any(c => c.Data is IGetActorValueConditionDataGetter && c is IConditionFloatGetter f && f.ComparisonValue == 30 && f.CompareOperator == CompareOperator.LessThan),
                _ => true,
            };
            var hit = hits.FirstOrDefault(Gate);
            var speaker = hit?.Conditions.Select(c => c.Data is IGetIsIDConditionDataGetter x ? x.Object.Link.FormKey.ToString() : null).FirstOrDefault(x => x != null);
            var tif = hit?.VirtualMachineAdapter?.ScriptFragments?.OnEnd?.ScriptName;
            var setsOk = i.sets is int s ? tif != null && Pex(tif, "SetStage") && tif.EndsWith($"_{s}") : tif == null || tif == "TIF_ARG_BC03_Season";
            var want = lines.GetProperty(i.key).GetProperty(i.variant).EnumerateArray().Select(l => l.GetString()).ToList();
            var text = hit?.Responses.Select(r => r.Text.String).ToList() ?? [];
            Ok($"topic {i.topic} at stage {i.op} {i.stage} {i.gate}", hit != null && speaker == i.speaker && setsOk && text.SequenceEqual(want),
                $"speaker {(speaker == i.speaker ? "ok" : speaker)}, sets {(i.sets?.ToString() ?? "nothing")} via {tif ?? "-"}, lines {(text.SequenceEqual(want) ? "=record" : "DIFFER")}");
        }
        var season = ours.DialogTopics.First(x => x.EditorID == "ARG_BC03_TheSeason").Responses[0];
        Ok("F4 the season sets ARG_BC03_SeasonHeard", season.VirtualMachineAdapter?.ScriptFragments?.OnEnd?.ScriptName == "TIF_ARG_BC03_Season" && Pex("TIF_ARG_BC03_Season", "SetValue"));
        var bc01 = ours.Quests.FirstOrDefault(x => x.EditorID == "ARG_BC01");
        Console.WriteLine(bc01 == null ? "  NOTE BC01 >= 90 gate on the opening topic: ARG_BC01 not in this plugin yet" : "  BC01 present");
        Console.WriteLine(fails == 0 ? "CHAINBREAKERS READ-BACK: PASS" : $"CHAINBREAKERS READ-BACK: {fails} FAIL");
        return fails == 0 ? 0 : 1;
    }
}
