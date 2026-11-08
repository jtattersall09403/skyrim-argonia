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

    // One quest's common read-back: stages, journal, objectives, fragments in the record and the .pex, aliases forced and
    // persistent, zones (prereq, stage), alias packages gated on the stage, every topic's info lines against quest_lines.
    static void Generic(ISkyrimModGetter ours, Dictionary<FormKey, (IPlacedGetter rec, ModKey from)> placed, Func<string, string, bool> Pex,
        string edid, string id, string code, int[] stages, int[] ends, string[] aliases, (string zone, int prereq, int stage)[] zones, (string alias, string pack, int stage)[] packs)
    {
        Console.WriteLine($"{edid} ({id})");
        var q = ours.Quests.First(x => x.EditorID == edid);
        var journal = LocalQuests.Journal(id); var objectives = LocalQuests.Objectives(id);
        Ok("Start Game Enabled, Side Quest", q.Flags.HasFlag(Quest.Flag.StartGameEnabled) && q.Type == Quest.TypeEnum.SideQuest);
        Ok("stages as the record", journal.Keys.Order().SequenceEqual(stages), string.Join(",", journal.Keys.Order()));
        var script = "ARG_QF_" + edid[4..];
        foreach (var n in stages)
        {
            var st = q.Stages.FirstOrDefault(s => s.Index == n); var le = st?.LogEntries.FirstOrDefault();
            var frag = q.VirtualMachineAdapter!.Fragments.FirstOrDefault(f => f.Stage == n);
            var obj = !objectives.TryGetValue(n, out var ot) || q.Objectives.FirstOrDefault(o => o.Index == n)?.DisplayText?.String == ot;
            Ok($"stage {n}", st != null && le?.Entry?.String == journal[n] && (le.Flags ?? 0).HasFlag(QuestLogEntry.Flag.CompleteQuest) == ends.Contains(n)
                && obj && frag?.FragmentName == $"Fragment_{n}" && Pex(script, $"Fragment_{n}"), $"fragment {frag?.FragmentName ?? "MISSING"}, pex {Pex(script, $"Fragment_{n}")}");
        }
        Ok("endings complete and stop", Pex(script, "IncSideQuests") && Pex(script, "Stop"));
        foreach (var name in aliases)
        {
            var a = q.Aliases.First(x => x.Name == name); var r = placed[a.ForcedReference.FormKey].rec;
            Ok($"alias {name}: forced, persistent", (r.MajorRecordFlagsRaw & 0x400) != 0, $"{a.ForcedReference.FormKey} {a.Flags}");
        }
        foreach (var (zone, prereq, stage) in zones)
        {
            var z = (IPlacedObjectGetter)placed.Values.First(v => v.rec.EditorID == zone).rec;
            var sc = z.VirtualMachineAdapter?.Scripts.FirstOrDefault(x => x.Name == "defaultSetStageTrigScript");
            int P(string n) => sc?.Properties.OfType<IScriptIntPropertyGetter>().FirstOrDefault(p => p.Name == n)?.Data ?? -1;
            Ok($"zone {zone}: {prereq} -> {stage}", P("prereqStageOPT") == prereq && P("stage") == stage && z.Primitive != null);
        }
        foreach (var (alias, pack, stage) in packs)
        {
            var a = q.Aliases.First(x => x.Name == alias);
            var p = ours.Packages.First(x => x.EditorID == pack);
            Ok($"alias {alias} carries {pack} from stage {stage}", a.PackageData.Any(l => l.FormKey == p.FormKey)
                && p.Conditions.Any(c => c.Data is IGetStageConditionDataGetter g && g.Quest.Link.FormKey == q.FormKey && ((IConditionFloatGetter)c).ComparisonValue == stage));
        }
        var lines = LocalQuests.Lines(code);
        foreach (var t in ours.DialogTopics.Where(x => x.Quest.FormKey == q.FormKey && x.Subtype == DialogTopic.SubtypeEnum.Custom))
        {
            var key = lines.EnumerateObject().First(o => t.EditorID == $"ARG_{code.ToUpper()}_" + string.Concat(o.Name.Split('-').Skip(1).Select(w => char.ToUpper(w[0]) + w[1..])));
            foreach (var r in t.Responses)
            {
                var text = r.Responses.Select(x => x.Text.String).ToList();
                var match = key.Value.EnumerateObject().Where(v => v.Value.ValueKind == System.Text.Json.JsonValueKind.Array)
                    .Any(v => v.Value.EnumerateArray().Select(l => l.GetString()).SequenceEqual(text));
                var tif = r.VirtualMachineAdapter?.ScriptFragments?.OnEnd?.ScriptName;
                Ok($"topic {t.EditorID} info", match && r.Conditions.Any(c => c.Data is IGetIsIDConditionDataGetter) && (tif == null || Pex(tif, "SetStage")), $"lines {(match ? "=record" : "DIFFER")}, sets via {tif ?? "-"}");
            }
        }
        BandsOf(ours, q, lines, code, Ok);
    }

    static IEnumerable<IConditionFloatGetter> Ranks(IDialogResponsesGetter r) => r.Conditions.Where(c => c.Data is IGetRelationshipRankConditionDataGetter).Cast<IConditionFloatGetter>();
    static bool Is(IConditionFloatGetter c, CompareOperator op, float v) => c.CompareOperator == op && c.ComparisonValue == v;
    // A band INFO: warm (rank >= 1) or cool (rank < 0); the default of a banded topic carries the complement (< 1, >= 0).
    internal static bool Banded(IDialogResponsesGetter r) => Ranks(r).Any(c => Is(c, CompareOperator.GreaterThanOrEqualTo, 1) || Is(c, CompareOperator.LessThan, 0));

    // The wording bands: every rank-gated INFO speaks its key@high (rank >= 1 with the player) or key@low (rank < 0) lines,
    // and a default INFO with the same other gates and fragment carries the complement, so the bands are exclusive by
    // condition (Spriggit's YAML does not keep INFO order). Prints the counts.
    public static void BandsOf(ISkyrimModGetter ours, IQuestGetter q, System.Text.Json.JsonElement lines, string code, Action<string, bool, string> ok)
    {
        int warm = 0, cool = 0;
        string Sig(IDialogResponsesGetter r) => string.Join(",", r.Conditions.Where(c => c.Data is not IGetRelationshipRankConditionDataGetter)
            .Select(c => c.Data.GetType().Name + ((IConditionFloatGetter)c).CompareOperator + ((IConditionFloatGetter)c).ComparisonValue))
            + "|" + r.VirtualMachineAdapter?.ScriptFragments?.OnEnd?.ScriptName;
        foreach (var t in ours.DialogTopics.Where(x => x.Quest.FormKey == q.FormKey && x.Subtype == DialogTopic.SubtypeEnum.Custom))
        {
            var key = lines.EnumerateObject().First(o => t.EditorID == $"ARG_{code.ToUpper()}_" + string.Concat(o.Name.Split('-').Skip(1).Select(w => char.ToUpper(w[0]) + w[1..])));
            var rs = t.Responses.ToList();
            for (var i = 0; i < rs.Count; i++)
            {
                if (!Banded(rs[i])) continue;
                var rank = Ranks(rs[i]).Single();
                var band = rank.CompareOperator == CompareOperator.GreaterThanOrEqualTo && rank.ComparisonValue == 1 ? "high"
                    : rank.CompareOperator == CompareOperator.LessThan && rank.ComparisonValue == 0 ? "low" : "?";
                var onPlayer = ((IGetRelationshipRankConditionDataGetter)rank.Data).TargetNpc.Link.FormKey == FormKey.Factory("000014:Skyrim.esm");
                var text = rs[i].Responses.Select(x => x.Text.String).ToList();
                var match = key.Value.EnumerateObject().Where(v => v.Name.EndsWith("@" + band)).Any(v => v.Value.EnumerateArray().Select(l => l.GetString()).SequenceEqual(text));
                var dflt = rs.Any(r => !Banded(r) && Sig(r) == Sig(rs[i]) && Ranks(r).Any(c => band == "high" ? Is(c, CompareOperator.LessThan, 1) : Is(c, CompareOperator.GreaterThanOrEqualTo, 0)));
                if (band == "high") warm++; else cool++;
                ok($"{t.EditorID} {band} band: rank with the player {rank.CompareOperator} {rank.ComparisonValue}, default excludes it", band != "?" && onPlayer && match && dflt,
                    $"lines {(match ? "=record" : "DIFFER")}, default with the same gates and fragment and the complement {dflt}");
            }
        }
        Console.WriteLine($"  BANDS {q.EditorID}: warm {warm}, cool {cool}, race 0");
    }

    // The wording bands of a quest whose band text is looked up from its default's (MQ03, MQ04, MQ05, TG01, TG02): every
    // rank-gated INFO of its topics is on the player (warm >= 1, cool < 0), speaks expect(default's lines, band), and has a
    // default with the same other gates and fragment carrying the complement; and the counts equal the written bands'.
    public static void BandsBy(ISkyrimModGetter ours, IQuestGetter q, Func<List<string>, string, List<string>?> expect, int written, Action<string, bool, string> ok)
    {
        int warm = 0, cool = 0;
        foreach (var t in ours.DialogTopics.Where(x => x.Quest.FormKey == q.FormKey && x.Subtype == DialogTopic.SubtypeEnum.Custom))
        {
            var rs = t.Responses.ToList();
            foreach (var r in rs.Where(Banded))
            {
                var rank = Ranks(r).Single();
                var band = Is(rank, CompareOperator.GreaterThanOrEqualTo, 1) ? "high" : Is(rank, CompareOperator.LessThan, 0) ? "low" : "?";
                var onPlayer = ((IGetRelationshipRankConditionDataGetter)rank.Data).TargetNpc.Link.FormKey == FormKey.Factory("000014:Skyrim.esm");
                var dflt = rs.FirstOrDefault(d => !Banded(d) && Sig(d) == Sig(r) && Ranks(d).Any(c => band == "high" ? Is(c, CompareOperator.LessThan, 1) : Is(c, CompareOperator.GreaterThanOrEqualTo, 0)));
                var want = dflt == null ? null : expect([.. dflt.Responses.Select(x => x.Text.String ?? "")], band);
                var match = want != null && want.Count > 0 && !want.Any(l => l.Contains("[player race]")) && r.Responses.Select(x => x.Text.String).SequenceEqual(want);
                if (band == "high") warm++; else cool++;
                ok($"{t.EditorID} {band} band: rank with the player {rank.CompareOperator} {rank.ComparisonValue}, default excludes it", band != "?" && onPlayer && dflt != null && match,
                    $"lines {(match ? "=record" : "DIFFER")}, default with the same gates and fragment and the complement {dflt != null}");
            }
        }
        ok($"{q.EditorID} bands built = written ({written})", warm + cool == written, $"warm {warm}, cool {cool}");
        Console.WriteLine($"  BANDS {q.EditorID}: warm {warm}, cool {cool}, race 0");
    }
    static string Sig(IDialogResponsesGetter r) => string.Join(",", r.Conditions.Where(c => c.Data is not IGetRelationshipRankConditionDataGetter)
        .Select(c => c.Data.GetType().Name + ((IConditionFloatGetter)c).CompareOperator + ((IConditionFloatGetter)c).ComparisonValue))
        + "|" + r.VirtualMachineAdapter?.ScriptFragments?.OnEnd?.ScriptName;

    // An after-quest Hello: per person, one INFO per written line, gated on the ref and on the endings (OR'd, each EqualTo).
    public static void AfterOf(ISkyrimModGetter ours, IQuestGetter q, string topic, (FormKey who, List<string> said, int[] endings)[] people, Action<string, bool, string> ok)
    {
        var t = ours.DialogTopics.FirstOrDefault(x => x.EditorID == topic);
        ok($"{topic}: a Hello topic of {q.EditorID}", t != null && t.Subtype == DialogTopic.SubtypeEnum.Hello && t.Quest.FormKey == q.FormKey, "");
        if (t == null) return;
        foreach (var (who, said, endings) in people)
        {
            var mine = t.Responses.Where(r => r.Conditions.Any(c => c.Data is IGetIsReferenceConditionDataGetter g && g.Target.Link.FormKey == who)
                && r.Conditions.Any(c => c.Data is IGetStageConditionDataGetter && endings.Contains((int)((IConditionFloatGetter)c).ComparisonValue))).ToList();
            var text = mine.Select(r => r.Responses.Single().Text.String).ToList();
            var gates = mine.All(r => r.Conditions.Where(c => c.Data is IGetStageConditionDataGetter g && g.Quest.Link.FormKey == q.FormKey)
                .Select(c => (int)((IConditionFloatGetter)c).ComparisonValue).Order().SequenceEqual(endings.Order())
                && r.Conditions.Where(c => c.Data is IGetStageConditionDataGetter).All(c => ((IConditionFloatGetter)c).CompareOperator == CompareOperator.EqualTo)
                && r.Conditions.Count(c => c.Flags.HasFlag(Condition.Flag.OR)) == endings.Length - 1);
            ok($"{topic}: {who} after {string.Join("/", endings)}", said.Count >= 2 && text.Order().SequenceEqual(said.Order()) && gates, $"{mine.Count} lines, gates {gates}");
        }
        Console.WriteLine($"  AFTER {q.EditorID}: {t.Responses.Count} after-quest INFOs");
    }

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
            var hits = t.Responses.Where(r => !Banded(r) && r.Conditions.Any(c => c.Data is IGetStageConditionDataGetter g && g.Quest.Link.FormKey == q.FormKey
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
        BandsOf(ours, q, lines, "bc03", Ok);
        var seasons = ours.DialogTopics.First(x => x.EditorID == "ARG_BC03_TheSeason").Responses;
        Ok("F4 the season sets ARG_BC03_SeasonHeard (every band)", seasons.All(season => season.VirtualMachineAdapter?.ScriptFragments?.OnEnd?.ScriptName == "TIF_ARG_BC03_Season") && Pex("TIF_ARG_BC03_Season", "SetValue"), $"{seasons.Count} infos");
        var bc01q = ours.Quests.First(x => x.EditorID == "ARG_BC01");
        var opens = ours.DialogTopics.First(x => x.EditorID == "ARG_BC03_LastSeason").Responses;
        Ok("BC03 opens once BC01 is at 90 or more", opens.SelectMany(r => r.Conditions).Any(c => c.Data is IGetStageConditionDataGetter g && g.Quest.Link.FormKey == bc01q.FormKey && ((IConditionFloatGetter)c).ComparisonValue == 90));
        Ok("BC03 90 adds 10 to ARG_ChainbreakersStanding", Pex(script, "ChainbreakersStanding") && Pex(script, "Mod"));

        Generic(ours, placed, Pex, "ARG_BC01", "quest.bc.bc01", "bc01", [10, 40, 90, 91, 94], [90, 91, 94],
            ["Patron", "Debtor", "Steward", "Chest"], [("ARG_BC01_ChannelEndZone", 40, 91)],
            [("Patron", "ARG_BC01_PatronAtLanding", 10), ("Debtor", "ARG_BC01_DebtorFollow", 40)]);
        FormKey RefOf(string e) => ours.EnumerateMajorRecords<IPlacedGetter>().First(r => r.EditorID == e).FormKey;
        AfterOf(ours, ours.Quests.First(x => x.EditorID == "ARG_BC01"), "ARG_BC01_AfterHello", [(RefOf("ARG_BC01_RowsForAnotherRef"), LocalQuests.After("bc01", "rows-for-another"), [90, 91])], Ok);
        var cuts = ours.DialogTopics.First(x => x.EditorID == "ARG_BC01_CutLoose").Responses;
        Ok("BC01 cut-loose: night (C-time) and unseen by three (C-detected)", cuts.Any(cut => cut.Conditions.Count(c => c.Data is IGetCurrentTimeConditionDataGetter) == 2 && cut.Conditions.Count(c => c.Data is IGetDetectedConditionDataGetter) == 3 && cut.VirtualMachineAdapter != null),
            string.Join(" | ", cuts.Select(r => string.Join(",", r.Conditions.Select(c => c.Data.GetType().Name.Replace("ConditionData", "").Replace("BinaryOverlay", ""))))));
        Ok("BC01 bring-down gated on the debt book (C-item)", ours.DialogTopics.First(x => x.EditorID == "ARG_BC01_BringDown").Responses[0].Conditions.Any(c => c.Data is IGetItemCountConditionDataGetter));
        Ok("BC01 10 puts the book in the chest; 90 moves her to Blackrose", Pex("ARG_QF_BC01", "AddItem") && Pex("ARG_QF_BC01", "MoveTo") && Pex("ARG_QF_BC01", "ChainbreakersStanding"));

        Generic(ours, placed, Pex, "ARG_BC02", "quest.bc.bc02", "bc02", [20, 30, 31, 32, 33, 91, 92, 93, 94], [91, 92, 93, 94],
            ["Patron", "GateKeeper", "Speaker", "Killer", "Mother"],
            [("ARG_BC02_InZone", 20, 30), ("ARG_BC02_OutSpeakerZone", 31, 91), ("ARG_BC02_OutKillerZone", 32, 92), ("ARG_BC02_OutMotherZone", 33, 93)],
            [("Speaker", "ARG_BC02_SpeakerFollow", 31), ("Killer", "ARG_BC02_KillerFollow", 32), ("Mother", "ARG_BC02_MotherFollow", 33)]);
        string[] writer = ["says-it-plain", "hides-in-reeds", "keeps-the-old-count"]; string[] held = ["Speaker", "Killer", "Mother"];
        AfterOf(ours, ours.Quests.First(x => x.EditorID == "ARG_BC02"), "ARG_BC02_AfterHello",
            [.. Enumerable.Range(0, 3).Select(i => (RefOf($"ARG_BC02_{held[i]}Ref"), LocalQuests.After("bc02", writer[i]), new[] { 91 + i }))], Ok);
        var fires = ours.DialogTopics.First(x => x.EditorID == "ARG_BC02_TheFire").Responses;
        Ok("BC02 opens once BC01 is at 90 or more", fires.SelectMany(r => r.Conditions).Any(c => c.Data is IGetStageConditionDataGetter g && g.Quest.Link.FormKey == bc01q.FormKey && ((IConditionFloatGetter)c).ComparisonValue == 90));
        Ok("BC02 gate and let-by at Speech 25", new[] { "ARG_BC02_TheGate", "ARG_BC02_LetBy" }.All(t => ours.DialogTopics.First(x => x.EditorID == t).Responses.Any(r => r.Conditions.Any(c => c.Data is IGetActorValueConditionDataGetter && ((IConditionFloatGetter)c).ComparisonValue == 25))));
        Ok("BC02 31/32/33 disable the other two (E-enable), no kill", Pex("ARG_QF_BC02", "Disable") && Pex("ARG_QF_BC02", "KillerParent"));
        foreach (var k in new[] { "Speaker", "Killer", "Mother" })
        {
            var r = (IPlacedNpcGetter)placed[ours.Quests.First(x => x.EditorID == "ARG_BC02").Aliases.First(a => a.Name == k).ForcedReference.FormKey].rec;
            var par = r.EnableParent == null ? null : placed[r.EnableParent.Reference.FormKey].rec;
            Ok($"BC02 {k} under an initially disabled parent of its own", par != null && (par.MajorRecordFlagsRaw & 0x800) != 0);
        }
        Console.WriteLine(fails == 0 ? "CHAINBREAKERS READ-BACK: PASS" : $"CHAINBREAKERS READ-BACK: {fails} FAIL");
        return fails == 0 ? 0 : 1;
    }
}
