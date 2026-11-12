using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;

// The rules for quests built by the generic quest builder (QuestForm.cs), part of `questcheck`. A form-built quest is a quest
// of ours whose script adapter names ARG_QuestStages; its stage work is rows in that script's properties (Op, What, Num, and
// Stages with StageFrom/StageTo: the rows of Stages[k] are [StageFrom[k], StageTo[k])). The watch (ARG_MortalWatch) is the
// always-running quest whose aliases carry ARG_AliasEffects. Each rule is a pure function over the small model FQ, unit-tested
// by `questcheck --selftest`; the loader fills the model from the plugin and the load order's winning records.
//   runonce      Run Once is set (not on the watch)
//   aliases      every alias is a forced reference or a create-in-container alias; every forced reference is persistent
//                (record flag 0x400) in its winning record
//   scripts      the quest's only script is ARG_QuestStages (the watch: none); alias scripts only ARG_AliasEffects (the watch, and a who-must-live death within a window),
//                defaultSetStageOnPlayerAcquire, defaultSetStageAliasScript, defaultSetStageOnCloseBook,
//                defaultSetStageOnDeathRefAlias; every response of the quest's topics carries no script but ARG_LineEffects
//   package      the quest's aliases carry at most one package in all, and it has the ForceGreet template (03C1C4:Skyrim.esm)
//   zones-scenes no placed reference of ours carries defaultSetStageTrigScript, and no scene has the quest as its quest
//   target-on    for each stage that shows an objective (op 2), each target alias's forced reference is on there: enabled
//                from the start, or switched on (op 29) at or below the stage with no later switch off (op 30) at or below it;
//                a create-in-container target counts as on
//   mortal       (whole plugin) no base of a person placed by us or by Black Marsh & Valenwood (through Use Base Data
//                templates) is Essential or Protected in its winning record, and no alias of a quest of ours is either
sealed class FA
{
    public int Id; public string Name = ""; public string? Forced; public bool Create, Persistent = true, On = true;
    public List<string> Scripts = []; public List<string?> Packs = []; // each package's PackageTemplate key (null when it has none)
}
sealed class FQ
{
    public string Edid = ""; public bool Watch, RunOnce; public List<string> Scripts = []; public List<FA> Aliases = [];
    public List<(int op, string what, float num)> Rows = []; public Dictionary<int, (int from, int to)> StageRows = [];
    public Dictionary<int, List<int>> Targets = []; // objective index -> target alias ids
    public List<(string topic, List<string> scripts)> Responses = []; public int Scenes; public List<string> ZoneRefs = [];
}
static partial class QuestCheck
{
    public const string ForceGreetKey = "03C1C4:Skyrim.esm";
    static readonly HashSet<string> AliasScriptsOk = new(StringComparer.OrdinalIgnoreCase)
        { "defaultSetStageOnPlayerAcquire", "defaultSetStageAliasScript", "defaultSetStageOnCloseBook", "defaultSetStageOnDeathRefAlias" };
    static string FFail(FQ q, string rule, string what) => $"FAIL {q.Edid} {rule}: {what}";

    public static IEnumerable<string> FRunOnce(FQ q) { if (!q.Watch && !q.RunOnce) yield return FFail(q, "runonce", "Run Once is not set"); }

    public static IEnumerable<string> FAliases(FQ q)
    {
        foreach (var a in q.Aliases)
        {
            if (a.Forced == null && !a.Create) yield return FFail(q, "aliases", $"alias {a.Name} is neither a forced reference nor a create-in-container alias");
            if (a.Forced != null && !a.Persistent) yield return FFail(q, "aliases", $"alias {a.Name}: forced reference {a.Forced} is not persistent");
        }
    }

    public static IEnumerable<string> FScripts(FQ q)
    {
        foreach (var s in q.Scripts)
            if (q.Watch || !s.Equals(QuestForm.StagesScript, StringComparison.OrdinalIgnoreCase)) yield return FFail(q, "scripts", $"quest script {s} is not allowed");
        if (!q.Watch && !q.Scripts.Contains(QuestForm.StagesScript, StringComparer.OrdinalIgnoreCase)) yield return FFail(q, "scripts", "the quest does not carry ARG_QuestStages");
        foreach (var a in q.Aliases)
            foreach (var s in a.Scripts)
                if (!(AliasScriptsOk.Contains(s) || s.Equals(QuestForm.AliasScript, StringComparison.OrdinalIgnoreCase)))
                    yield return FFail(q, "scripts", $"alias {a.Name}: script {s} is not allowed");
        foreach (var (topic, scripts) in q.Responses)
            foreach (var s in scripts.Where(s => !s.Equals(QuestForm.LineScript, StringComparison.OrdinalIgnoreCase)))
                yield return FFail(q, "scripts", $"a response of topic {topic} carries {s}");
    }

    public static IEnumerable<string> FPackage(FQ q)
    {
        var all = q.Aliases.SelectMany(a => a.Packs).ToList();
        if (all.Count > 1) yield return FFail(q, "package", $"aliases carry {all.Count} packages, at most one is allowed");
        foreach (var t in all.Where(t => t != ForceGreetKey)) yield return FFail(q, "package", $"a package has template {t ?? "none"}, not ForceGreet");
    }

    public static IEnumerable<string> FZonesScenes(FQ q)
    {
        foreach (var z in q.ZoneRefs) yield return FFail(q, "zones-scenes", $"placed reference {z} carries defaultSetStageTrigScript");
        if (q.Scenes > 0) yield return FFail(q, "zones-scenes", $"{q.Scenes} scene(s) have this quest as their quest");
    }

    // Is the alias's forced reference on once stage `stage` has run: its start state, then the switch rows of the stages up to it in order.
    static bool OnAt(FQ q, FA a, int stage)
    {
        if (a.Forced == null) return a.Create;
        var on = a.On;
        foreach (var (_, (from, to)) in q.StageRows.Where(kv => kv.Key <= stage).OrderBy(kv => kv.Key))
            for (var i = from; i < to && i < q.Rows.Count; i++)
            {
                var r = q.Rows[i];
                if (r.what != a.Forced) continue;
                if (r.op == QuestForm.Op.SwitchOn) on = true; else if (r.op == QuestForm.Op.SwitchOff) on = false;
            }
        return on;
    }

    public static IEnumerable<string> FTargetOn(FQ q)
    {
        foreach (var (s, (from, to)) in q.StageRows.OrderBy(kv => kv.Key))
            for (var i = from; i < to && i < q.Rows.Count; i++)
            {
                if (q.Rows[i].op != QuestForm.Op.ShowObjective) continue;
                var obj = (int)q.Rows[i].num;
                foreach (var id in q.Targets.GetValueOrDefault(obj) ?? [])
                    if (q.Aliases.FirstOrDefault(a => a.Id == id) is { } a && !OnAt(q, a, s))
                        yield return FFail(q, "target-on", $"stage {s} shows objective {obj} but its target alias {a.Name} ({a.Forced}) is not on");
            }
    }

    public static IEnumerable<string> FormRules(FQ q) =>
        new[] { FRunOnce(q), FAliases(q), FScripts(q), FPackage(q), FZonesScenes(q), FTargetOn(q) }.SelectMany(x => x);

    public static IEnumerable<string> MortalRule(IEnumerable<(string who, bool essential, bool prot)> held) =>
        held.Where(h => h.essential || h.prot).Select(h => $"FAIL {h.who} mortal: {(h.essential ? "Essential" : "")}{(h.essential && h.prot ? " and " : "")}{(h.prot ? "Protected" : "")}");

    // ---- the loader
    static bool IsFormBuilt(IQuestGetter q) =>
        q.FormKey.ModKey.FileName.String.Equals("Argonia.esp", StringComparison.OrdinalIgnoreCase)
        && (q.EditorID == QuestForm.WatchId || q.VirtualMachineAdapter?.FileName == QuestForm.StagesScript
            || q.VirtualMachineAdapter?.Scripts.Any(s => s.Name == QuestForm.StagesScript) == true);

    static List<string> FormLoadAndRun(List<ISkyrimModGetter> mods, out int quests)
    {
        var mine = mods[^1];
        var placed = Survey.Winners<IPlacedGetter>(mods);
        var packs = Survey.Winners<IPackageGetter>(mods);
        var npcs = Survey.Winners<INpcGetter>(mods);
        var fails = new List<string>(); quests = 0;
        foreach (var q in mine.Quests.Where(IsFormBuilt))
        {
            quests++;
            var fq = new FQ { Edid = q.EditorID ?? q.FormKey.ToString(), Watch = q.EditorID == QuestForm.WatchId, RunOnce = q.Flags.HasFlag(Quest.Flag.RunOnce) };
            var vm = q.VirtualMachineAdapter;
            var stages = vm?.Scripts.FirstOrDefault(s => s.Name == QuestForm.StagesScript);
            fq.Scripts = vm?.Scripts.Select(s => s.Name).ToList() ?? [];
            if (stages != null)
            {
                List<int> Ints(string n) => stages.Properties.OfType<IScriptIntListPropertyGetter>().FirstOrDefault(p => p.Name == n)?.Data.ToList() ?? [];
                var op = Ints("Op"); var num = stages.Properties.OfType<IScriptFloatListPropertyGetter>().FirstOrDefault(p => p.Name == "Num")?.Data.ToList() ?? [];
                var what = stages.Properties.OfType<IScriptObjectListPropertyGetter>().FirstOrDefault(p => p.Name == "What")?.Objects.Select(o => o.Object.FormKey.ToString()).ToList() ?? [];
                for (var i = 0; i < op.Count; i++) fq.Rows.Add((op[i], i < what.Count ? what[i] : "", i < num.Count ? num[i] : 0));
                var st = Ints("Stages"); var f = Ints("StageFrom"); var t = Ints("StageTo");
                for (var k = 0; k < st.Count && k < f.Count && k < t.Count; k++) fq.StageRows[st[k]] = (f[k], t[k]);
            }
            foreach (var a in q.Aliases)
            {
                var fa = new FA { Id = (int)a.ID, Name = a.Name ?? "", Create = a.CreateReferenceToObject != null };
                if (!a.ForcedReference.IsNull)
                {
                    fa.Forced = a.ForcedReference.FormKey.ToString();
                    if (placed.TryGetValue(a.ForcedReference.FormKey, out var w))
                    {
                        fa.Persistent = (w.rec.MajorRecordFlagsRaw & 0x400) != 0;
                        var ep = w.rec switch { IPlacedObjectGetter o => o.EnableParent, IPlacedNpcGetter n => n.EnableParent, _ => null };
                        fa.On = (w.rec.MajorRecordFlagsRaw & 0x800) == 0 && (ep == null || ep.Reference.IsNull);
                    }
                    else fa.Persistent = false;
                }
                foreach (var p in a.PackageData)
                    fa.Packs.Add(packs.TryGetValue(p.FormKey, out var pk) && !pk.rec.PackageTemplate.IsNull ? pk.rec.PackageTemplate.FormKey.ToString() : null);
                foreach (var al in vm?.Aliases.Where(x => x.Property.Alias == (int)a.ID) ?? [])
                    fa.Scripts.AddRange(al.Scripts.Select(s => s.Name));
                fq.Aliases.Add(fa);
            }
            foreach (var o in q.Objectives) fq.Targets[(int)o.Index] = o.Targets.Select(t => (int)t.AliasID).ToList();
            foreach (var t in mine.DialogTopics.Where(t => t.Quest.FormKey == q.FormKey))
                foreach (var r in t.Responses)
                    fq.Responses.Add((t.EditorID ?? t.FormKey.ToString(), (r.VirtualMachineAdapter?.Scripts.Select(s => s.Name) ?? []).Concat(
                        r.VirtualMachineAdapter?.ScriptFragments is { } sf ? new[] { sf.OnBegin?.ScriptName, sf.OnEnd?.ScriptName }.Where(n => !string.IsNullOrEmpty(n)).Select(n => n!) : []).Distinct().ToList()));
            fq.Scenes = mine.Scenes.Count(s => s.Quest.FormKey == q.FormKey);
            foreach (var r in mine.EnumerateMajorRecords<IPlacedObjectGetter>())
                if (r.VirtualMachineAdapter?.Scripts.Any(s => s.Name.Equals("defaultSetStageTrigScript", StringComparison.OrdinalIgnoreCase)
                    && s.Properties.OfType<IScriptObjectPropertyGetter>().Any(p => p.Object.FormKey == q.FormKey)) == true)
                    fq.ZoneRefs.Add(r.EditorID ?? r.FormKey.ToString());
            fails.AddRange(FormRules(fq));
        }
        // mortal, over the whole plugin
        var ours = mine.ModKey;
        INpcGetter? Npc(FormKey k) => npcs.TryGetValue(k, out var w) ? w.rec : null;
        var bases = mods.SelectMany(m => m.EnumerateMajorRecords<IPlacedNpcGetter>().Where(r => Mortality.Watched(r.FormKey.ModKey, ours)).Select(r => r.Base.FormKey)).ToList();
        var flags = new List<(string who, bool essential, bool prot)>();
        foreach (var k in Mortality.Holders(Npc, bases).Distinct())
        {
            var n = Npc(k)!; var e = n.Configuration.Flags;
            flags.Add(($"{n.EditorID ?? "?"} ({k})", e.HasFlag(NpcConfiguration.Flag.Essential), e.HasFlag(NpcConfiguration.Flag.Protected)));
        }
        foreach (var q in mine.Quests.Where(q => q.FormKey.ModKey == ours))
            foreach (var a in q.Aliases)
                flags.Add(($"{q.EditorID} alias {a.Name}", a.Flags?.HasFlag(QuestAlias.Flag.Essential) == true, a.Flags?.HasFlag(QuestAlias.Flag.Protected) == true));
        fails.AddRange(MortalRule(flags));
        return fails;
    }

    // ---- selftest fixtures
    static FQ FormFx()
    {
        var q = new FQ { Edid = "ARG_T", RunOnce = true, Scripts = [QuestForm.StagesScript] };
        q.Aliases.Add(new FA { Id = 0, Name = "Chest", Forced = "r1", On = false });
        q.Rows = [(QuestForm.Op.SwitchOn, "r1", 0), (QuestForm.Op.ShowObjective, "", 10)];
        q.StageRows = new() { [10] = (0, 2) };
        q.Targets[10] = [0];
        return q;
    }
    static int FormSelfTest()
    {
        var bad = 0;
        void T(string name, bool fails, Func<FQ, IEnumerable<string>> rule, Action<FQ>? tweak = null)
        {
            var q = FormFx(); tweak?.Invoke(q); var n = rule(q).Count();
            if ((n > 0) != fails) { bad++; Console.WriteLine($"SELFTEST FAIL {name}: expected {(fails ? "a finding" : "none")}, got {n}"); }
        }
        T("target-on pass: switched on at the stage", false, FTargetOn);
        T("target-on pass: enabled from the start", false, FTargetOn, q => { q.Aliases[0].On = true; q.Rows[0] = (0, "", 0); });
        T("target-on pass: create-in-container", false, FTargetOn, q => { q.Aliases[0].Forced = null; q.Aliases[0].Create = true; q.Rows[0] = (0, "", 0); });
        T("target-on fail: never switched on", true, FTargetOn, q => q.Rows[0] = (0, "", 0));
        T("target-on fail: switched on after the stage", true, FTargetOn, q => { q.Rows = [(QuestForm.Op.ShowObjective, "", 10), (QuestForm.Op.SwitchOn, "r1", 0)]; q.StageRows = new() { [10] = (0, 1), [20] = (1, 2) }; });
        T("target-on fail: switched off again", true, FTargetOn, q => { q.Rows.Insert(1, (QuestForm.Op.SwitchOff, "r1", 0)); q.StageRows[10] = (0, 3); });
        T("scripts pass", false, FScripts, q => { q.Aliases[0].Scripts.Add("defaultSetStageOnPlayerAcquire"); q.Responses.Add(("T", [QuestForm.LineScript])); });
        T("scripts fail: a second quest script", true, FScripts, q => q.Scripts.Add("QF_Old"));
        T("scripts fail: alias script not allowed", true, FScripts, q => q.Aliases[0].Scripts.Add("SomethingElse"));
        T("scripts fail: a script of no form", true, FScripts, q => q.Aliases[0].Scripts.Add("ARG_QF_MQ01"));
        T("scripts pass: AliasEffects on the watch", false, FScripts, q => { q.Watch = true; q.Scripts.Clear(); q.Aliases[0].Scripts.Add(QuestForm.AliasScript); });
        T("scripts fail: a response script", true, FScripts, q => q.Responses.Add(("T", ["TIF__Old"])));
        T("package pass: one ForceGreet", false, FPackage, q => q.Aliases[0].Packs.Add(ForceGreetKey));
        T("package fail: two", true, FPackage, q => q.Aliases[0].Packs.AddRange([ForceGreetKey, ForceGreetKey]));
        T("package fail: other template", true, FPackage, q => q.Aliases[0].Packs.Add("000001:Skyrim.esm"));
        T("aliases fail: not persistent", true, FAliases, q => q.Aliases[0].Persistent = false);
        T("aliases fail: neither forced nor created", true, FAliases, q => q.Aliases[0].Forced = null);
        T("runonce fail", true, FRunOnce, q => q.RunOnce = false);
        T("zones-scenes fail: a scene", true, FZonesScenes, q => q.Scenes = 1);
        if (MortalRule([("a", false, false)]).Any() || !MortalRule([("b", true, false)]).Any()) { bad++; Console.WriteLine("SELFTEST FAIL mortal"); }
        return bad;
    }
}
