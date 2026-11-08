using System.Text;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;

// localcheck <Argonia.esp> <pex dir> <plugins in load order...>: Phase 4's read-back of LQ30 and LQ25 (part D) from the
// files the game reads: every stage's journal and objective against the story data, its fragment in the record and in
// the compiled .pex, every alias (forced, persistent), every topic's speaker and stage conditions and the stage it sets,
// and every trigger's script properties. Exit 1 on any failure.
static class LocalQuestsCheck
{
    static int fails;
    static void Ok(string what, bool pass, string detail = "") { if (!pass) fails++; Console.WriteLine($"  {(pass ? "PASS" : "FAIL")} {what}{(detail.Length > 0 ? ": " + detail : "")}"); }

    record Trig(uint alias, int prereq, int set);
    record Info(string topic, string speaker, int stage, int? sets, bool needsItem = false);

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
        void Check(string edid, string id, int[] stages, int[] ends, Trig[] deaths, Info[] infos, (string alias, string refKey)[] aliases)
        {
            Console.WriteLine($"{edid} ({id})");
            var q = ours.Quests.First(x => x.EditorID == edid);
            var journal = LocalQuests.Journal(id); var objectives = LocalQuests.Objectives(id);
            Ok("Start Game Enabled, Side Quest", q.Flags.HasFlag(Quest.Flag.StartGameEnabled) && q.Type == Quest.TypeEnum.SideQuest);
            var s0 = q.Stages.FirstOrDefault(s => s.Index == 0);
            Ok("stage 0: start-up, empty", s0 != null && s0.Flags.HasFlag(QuestStage.Flag.StartUpStage) && s0.LogEntries.All(l => string.IsNullOrEmpty(l.Entry?.String)));
            var script = q.VirtualMachineAdapter!.Scripts[0].Name;
            foreach (var n in stages)
            {
                var st = q.Stages.FirstOrDefault(s => s.Index == n);
                var le = st?.LogEntries.FirstOrDefault();
                var frag = q.VirtualMachineAdapter.Fragments.FirstOrDefault(f => f.Stage == n);
                var obj = objectives.TryGetValue(n, out var ot) ? q.Objectives.FirstOrDefault(o => o.Index == n)?.DisplayText?.String == ot : true;
                Ok($"stage {n}", st != null && le?.Entry?.String == journal[n] && (le.Flags ?? 0).HasFlag(QuestLogEntry.Flag.CompleteQuest) == ends.Contains(n)
                    && obj && frag?.FragmentName == $"Fragment_{n}" && Pex(script, $"Fragment_{n}"),
                    $"journal {(le?.Entry?.String == journal[n] ? "=record" : "DIFFERS")}, completes {(le?.Flags ?? 0).HasFlag(QuestLogEntry.Flag.CompleteQuest)}, objective {(objectives.ContainsKey(n) ? (obj ? "=record" : "DIFFERS") : "none")}, fragment {frag?.FragmentName ?? "MISSING"}, pex {Pex(script, $"Fragment_{n}")}");
            }
            foreach (var e in ends)
                Ok($"ending {e} completes and stops", Pex(script, "IncSideQuests") && Pex(script, "Stop"));
            foreach (var (name, key) in aliases)
            {
                var a = q.Aliases.First(x => x.Name == name);
                var r = placed[FormKey.Factory(key)].rec;
                Ok($"alias {name}", a.ForcedReference.FormKey == FormKey.Factory(key) && (r.MajorRecordFlagsRaw & 0x400) != 0, $"forced {a.ForcedReference.FormKey}, persistent {(r.MajorRecordFlagsRaw & 0x400) != 0}");
            }
            foreach (var d in deaths)
            {
                var f = q.VirtualMachineAdapter.Aliases.FirstOrDefault(x => x.Property.Alias == d.alias)?.Scripts.FirstOrDefault(s => s.Name == "defaultSetStageOnDeathRefAlias");
                int P(string n) => f?.Properties.OfType<IScriptIntPropertyGetter>().FirstOrDefault(p => p.Name == n)?.Data ?? -1;
                Ok($"TR-death on alias {d.alias}: {d.prereq} -> {d.set}", P("preReqStage") == d.prereq && P("StageToSet") == d.set);
            }
            ChainbreakersCheck.BandsOf(ours, q, LocalQuests.Lines(edid[4..].ToLower()), edid[4..].ToLower(), Ok);
            foreach (var i in infos)
            {
                var t = ours.DialogTopics.First(x => x.EditorID == i.topic);
                var hit = t.Responses.FirstOrDefault(r => !ChainbreakersCheck.Banded(r) && r.Conditions.Any(c => c.Data is IGetStageConditionDataGetter g && g.Quest.Link.FormKey == q.FormKey
                    && c is IConditionFloatGetter cf && cf.ComparisonValue == i.stage && cf.CompareOperator == CompareOperator.EqualTo));
                var speaker = hit?.Conditions.Select(c => c.Data switch { IGetIsIDConditionDataGetter x => x.Object.Link.FormKey.ToString(), IGetIsReferenceConditionDataGetter x => x.Target.Link.FormKey.ToString(), _ => null }).FirstOrDefault(x => x != null);
                var tif = hit?.VirtualMachineAdapter?.ScriptFragments?.OnEnd?.ScriptName;
                var setsOk = i.sets is int s ? tif != null && Pex(tif, "SetStage") && tif.EndsWith($"_{s}") : tif == null;
                var item = !i.needsItem || hit!.Conditions.Any(c => c.Data is IGetItemCountConditionDataGetter);
                Ok($"topic {i.topic} at stage {i.stage}", hit != null && speaker == i.speaker && setsOk && item && hit.Responses.Count > 0,
                    $"speaker {speaker}, sets {(i.sets?.ToString() ?? "nothing")} via {tif ?? "-"}, {hit?.Responses.Count} responses{(i.needsItem ? ", item gate " + item : "")}");
            }
        }
        string Base(string edid) => ours.Npcs.First(n => n.EditorID == edid).FormKey.ToString();
        string Ref(string edid) => ours.EnumerateMajorRecords<IPlacedGetter>().First(r => r.EditorID == edid).FormKey.ToString();

        Check("ARG_LQ30", "quest.local.lq30", [30, 40, 91, 92, 93], [91, 92, 93],
            [new(LocalQuests.L30Viper, 30, 40), new(LocalQuests.L30Youth, 30, 93)],
            [new("ARG_LQ30_WalkedOut", Base("ARG_LQ30_HajWan"), 0, 30), new("ARG_LQ30_WalkedOut", Base("ARG_LQ30_HajWan"), 30, null),
             new("ARG_LQ30_TheBasin", LocalQuests.Warden.ToString(), 30, null), new("ARG_LQ30_ComeBack", Base("ARG_LQ30_SeiWan"), 40, 92)],
            [("Kin", Ref("ARG_LQ30_HajWanRef")), ("Youth", Ref("ARG_LQ30_SeiWanRef")), ("Viper", Ref("ARG_LQ30_ViperRef")), ("Warden", LocalQuests.Warden.ToString())]);
        var seiWan = FormKey.Factory(Ref("ARG_LQ30_SeiWanRef"));
        ChainbreakersCheck.AfterOf(ours, ours.Quests.First(x => x.EditorID == "ARG_LQ30"), "ARG_LQ30_AfterHello",
            [(seiWan, LocalQuests.After("lq30", "sei-wan", "after91"), [91]), (seiWan, LocalQuests.After("lq30", "sei-wan", "after92"), [92])], Ok);
        var zone = ours.EnumerateMajorRecords<IPlacedObjectGetter>().First(r => r.EditorID == "ARG_LQ30_GateZone");
        int Z(string n) => zone.VirtualMachineAdapter!.Scripts[0].Properties.OfType<IScriptIntPropertyGetter>().First(p => p.Name == n).Data;
        Ok("  TR-zone at the gate: 40 -> 91, unconditioned", Z("prereqStageOPT") == 40 && Z("stage") == 91 && (zone.MajorRecordFlagsRaw & 0x400) != 0);
        Ok("  Sei-Wan and the viper behind the viper's parent, which starts disabled",
            new[] { "ARG_LQ30_SeiWanRef", "ARG_LQ30_ViperRef" }.All(e => ours.EnumerateMajorRecords<IPlacedNpcGetter>().First(r => r.EditorID == e).EnableParent?.Reference.FormKey.ToString() == Ref("ARG_LQ30_ViperParent"))
            && (placed[FormKey.Factory(Ref("ARG_LQ30_ViperParent"))].rec.MajorRecordFlagsRaw & 0x800) != 0);

        Check("ARG_LQ25", "quest.local.lq25", [20, 40, 91, 92, 93], [91, 92, 93],
            [new(LocalQuests.L25Croc, 20, 40), new(LocalQuests.L25Captain, 40, 93)],
            [new("ARG_LQ25_TheBeast", Base("ARG_LQ25_OkanZish"), 0, 20), new("ARG_LQ25_TheBeast", Base("ARG_LQ25_OkanZish"), 20, null),
             new("ARG_LQ25_TellCaptain", LocalQuests.Captain.ToString(), 40, 91, true), new("ARG_LQ25_KeepQuiet", Base("ARG_LQ25_WuleenTaza"), 40, 92)],
            [("Poler", LocalQuests.Poler.ToString()), ("Steerer", LocalQuests.Steerer.ToString()), ("Captain", LocalQuests.Captain.ToString()), ("Crocodile", Ref("ARG_LQ25_CrocodileRef"))]);
        var mq05 = ours.Quests.FirstOrDefault(x => x.EditorID == "ARG_MQ05");
        Console.WriteLine(mq05 == null ? "  NOTE MQ05 >= 40 gate on the opening topic: ARG_MQ05 not in this plugin yet (the MQ05 lane builds it)" : "  MQ05 present");
        foreach (var (r, b) in new[] { (LocalQuests.Poler, "ARG_LQ25_OkanZish"), (LocalQuests.Steerer, "ARG_LQ25_WuleenTaza") })
            Ok($"  {r} placed as {b}", ((IPlacedNpcGetter)placed[r].rec).Base.FormKey.ToString() == Base(b));
        Console.WriteLine(fails == 0 ? "LOCAL QUESTS READ-BACK: PASS" : $"LOCAL QUESTS READ-BACK: {fails} FAIL");
        return fails == 0 ? 0 : 1;
    }
}
