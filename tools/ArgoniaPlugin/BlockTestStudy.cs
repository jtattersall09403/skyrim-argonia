using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;

// blockstudy <Skyrim.esm>: the Skyrim.esm precedents behind the block-test fixes of the owner walk 2026-11-07
// (docs/design/blocks.md): (1) placed trigger boxes with defaultSetStageTrigScript that share one quest and stage, the
// way Bethesda gives one outcome several triggers; (2) how quests complete: type, the completing stage's flags and log
// text, whether a fragment rides on it, and quests that complete in their start-up stage.
static class BlockTestStudy
{
    public static void Run(string esm)
    {
        var mod = SkyrimMod.CreateFromBinaryOverlay(esm, SkyrimRelease.SkyrimSE, Survey.NoStrings);
        var trig = mod.EnumerateMajorRecords<IPlacedObjectGetter>()
            .Select(r => (r, s: r.VirtualMachineAdapter?.Scripts.FirstOrDefault(s => s.Name.Equals("defaultSetStageTrigScript", StringComparison.OrdinalIgnoreCase))))
            .Where(x => x.s != null)
            .Select(x => (x.r, quest: x.s!.Properties.OfType<IScriptObjectPropertyGetter>().FirstOrDefault(p => p.Name.Equals("myQuest", StringComparison.OrdinalIgnoreCase))?.Object.FormKey,
                stage: x.s.Properties.OfType<IScriptIntPropertyGetter>().FirstOrDefault(p => p.Name.Equals("stage", StringComparison.OrdinalIgnoreCase))?.Data))
            .ToList();
        var groups = trig.GroupBy(t => (t.quest, t.stage)).ToList();
        var shared = groups.Where(g => g.Count() > 1).ToList();
        var quests = mod.Quests.ToDictionary(q => q.FormKey);
        Console.WriteLine($"trigger refs with defaultSetStageTrigScript: {trig.Count}, in {groups.Count} (quest, stage) pairs; {shared.Count} pairs set by 2+ boxes ({shared.Sum(g => g.Count())} refs), largest {shared.Max(g => g.Count())}");
        foreach (var g in shared.OrderByDescending(g => g.Count()).Take(8))
            Console.WriteLine($"  {(g.Key.quest is { } k && quests.TryGetValue(k, out var q) ? q.EditorID : g.Key.quest?.ToString())} stage {g.Key.stage}: {g.Count()} boxes");
        // Two boxes for different stages of one quest whose fragments are the 'racing' shape we used: count quests where two
        // trigger boxes set two different stages (not counted as alternatives; reported for the record).
        Console.WriteLine($"  quests whose trigger boxes set 2+ different stages: {trig.GroupBy(t => t.quest).Count(g => g.Select(t => t.stage).Distinct().Count() > 1)}");

        // Completion.
        bool Completes(IQuestStageGetter s) => s.LogEntries.Any(l => l.Flags?.HasFlag(QuestLogEntry.Flag.CompleteQuest) == true);
        var completing = mod.Quests.Where(q => q.Stages.Any(Completes)).ToList();
        Console.WriteLine($"quests with a Complete Quest stage: {completing.Count} of {mod.Quests.Count}");
        foreach (var g in completing.GroupBy(q => q.Type).OrderByDescending(g => g.Count()))
        {
            var cs = g.Select(q => (q, s: q.Stages.First(Completes))).ToList();
            int withText = cs.Count(x => x.s.LogEntries.Any(l => l.Flags?.HasFlag(QuestLogEntry.Flag.CompleteQuest) == true && l.Entry != null));
            int textAny = cs.Count(x => x.q.Stages.Any(s => s.LogEntries.Any(l => l.Entry != null)));
            int frag = cs.Count(x => x.q.VirtualMachineAdapter?.Fragments.Any(f => f.Stage == x.s.Index) == true);
            int startup = cs.Count(x => x.s.Flags.HasFlag(QuestStage.Flag.StartUpStage));
            int objs = cs.Count(x => x.q.Objectives.Count > 0);
            Console.WriteLine($"  type {g.Key}: {g.Count()} quests; completing stage has log text (CNAM present) {withText}; any log text {textAny}; fragment on it {frag}; it is the start-up stage {startup}; objectives {objs}; e.g. {string.Join(", ", g.Take(4).Select(q => q.EditorID))}");
        }
        // Side quests that show in the journal: the stage's log entry carries text (CNAM) and the Complete flag together?
        var side = completing.Where(q => q.Type == Quest.TypeEnum.SideQuest).ToList();
        Console.WriteLine($"side quests: completing entry with CNAM {side.Count(q => q.Stages.First(Completes).LogEntries.Any(l => l.Flags?.HasFlag(QuestLogEntry.Flag.CompleteQuest) == true && l.Entry != null))} of {side.Count}; Fail flag stages {side.Count(q => q.Stages.Any(s => s.LogEntries.Any(l => l.Flags?.HasFlag(QuestLogEntry.Flag.FailQuest) == true)))}");
        foreach (var q in side.Take(6))
        {
            var st = q.Stages.First(Completes);
            Console.WriteLine($"  {q.EditorID}: completes at {st.Index}, fragment {q.VirtualMachineAdapter?.FileName}.{q.VirtualMachineAdapter?.Fragments.FirstOrDefault(f => f.Stage == st.Index)?.FragmentName}, later stages {string.Join(",", q.Stages.Where(s => s.Index > st.Index).Select(s => s.Index))}");
        }
        // The journal lists a quest by its objectives (owner walk 2026-11-08): side quests that complete with none.
        Console.WriteLine($"side quests: with objectives {side.Count(q => q.Objectives.Count > 0)} of {side.Count}; none: {string.Join(", ", side.Where(q => q.Objectives.Count == 0).Select(q => q.EditorID))}; all completing quests with a name and no objectives: {completing.Count(q => q.Objectives.Count == 0 && q.Name?.String is { Length: > 0 })} of {completing.Count}");
        var misc = completing.Where(q => q.Type == Quest.TypeEnum.Misc).ToList();
        Console.WriteLine($"misc quests: completing entry with CNAM {misc.Count(q => q.Stages.First(Completes).LogEntries.Any(l => l.Flags?.HasFlag(QuestLogEntry.Flag.CompleteQuest) == true && l.Entry != null))} of {misc.Count}");
        Stats(esm, mod, Completes);
    }

    // (3) The Stats page: which compiled scripts in Skyrim - Misc.bsa name IncrementStat and the quest stats, by the quest
    // type of the quest whose fragment file it is (a pex keeps its string table as plain length-prefixed strings).
    static void Stats(string esm, ISkyrimModGetter mod, Func<IQuestStageGetter, bool> completes)
    {
        var bsa = Mutagen.Bethesda.Archives.Archive.CreateReader(GameRelease.SkyrimSE, new Noggog.FilePath(Path.Combine(Path.GetDirectoryName(Path.GetFullPath(esm))!, "Skyrim - Misc.bsa")));
        var byScript = mod.Quests.Where(q => q.VirtualMachineAdapter?.FileName is { Length: > 0 }).GroupBy(q => q.VirtualMachineAdapter!.FileName!.ToLowerInvariant()).ToDictionary(g => g.Key, g => g.First());
        string[] names = ["IncSideQuests", "IncDaedricQuests", "\0\u0010Quests Completed", "Side Quests Completed", "Misc Objectives Completed", "Questlines Completed"];
        var hits = new Dictionary<string, List<string>>(); int pex = 0, inc = 0;
        foreach (var f in bsa.Files.Where(f => f.Path.EndsWith(".pex", StringComparison.OrdinalIgnoreCase)))
        {
            pex++; var text = System.Text.Encoding.Latin1.GetString(f.GetBytes());
            if (!text.Contains("IncrementStat", StringComparison.OrdinalIgnoreCase) && !text.Contains("IncSideQuests", StringComparison.OrdinalIgnoreCase)) continue; inc++;
            var stem = Path.GetFileNameWithoutExtension(f.Path.Replace('\\', '/')).ToLowerInvariant();
            var q = byScript.GetValueOrDefault(stem);
            foreach (var n in names.Where(n => text.Contains(n, StringComparison.OrdinalIgnoreCase)))
                (hits.TryGetValue(n, out var l) ? l : hits[n] = []).Add($"{stem}{(q != null ? $" ({q.EditorID}, {q.Type})" : "")}");
        }
        Console.WriteLine($"stats: {pex} pex in Skyrim - Misc.bsa, {inc} name IncrementStat");
        foreach (var n in names) Console.WriteLine($"  \"{n}\": {hits.GetValueOrDefault(n)?.Count ?? 0} scripts{(hits.TryGetValue(n, out var l) ? ": " + string.Join(", ", l.Take(12)) : "")}");
        // Which completing quests, by type, call AchievementsScript.IncSideQuests() (IncrementStat("Side Quests Completed"))
        // from their fragment file; no script names "Quests Completed" on its own, so the engine counts that one.
        var named = hits["IncSideQuests"].Select(s => s.Split(' ')[0]).ToHashSet();
        foreach (var g in mod.Quests.Where(q => q.Stages.Any(completes)).GroupBy(q => q.Type).OrderByDescending(g => g.Count()))
            Console.WriteLine($"  completing {g.Key}: {g.Count()}, of which the fragment file calls IncSideQuests: {g.Count(q => q.VirtualMachineAdapter?.FileName is { } fn && named.Contains(fn.ToLowerInvariant()))}");
    }
}
