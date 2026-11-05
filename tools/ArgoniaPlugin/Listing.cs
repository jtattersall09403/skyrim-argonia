using System.Text;
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;

// list <Argonia.esp> <out.md>: every record the built plugin holds, read back from the ESP, grouped as shutdown.json
// groups them, each override checked for the change it is meant to carry.
static class Listing
{
    public static int Run(string esp, string md, string[] loadOrder)
    {
        using var mod = SkyrimMod.CreateFromBinaryOverlay(esp, SkyrimRelease.SkyrimSE, Survey.NoStrings);
        var plan = JsonDocument.Parse(File.ReadAllText(Path.Combine(AppContext.BaseDirectory, "shutdown.json"))).RootElement;
        var errs = new List<string>();
        var glob = mod.Globals.Single(g => g.EditorID == "ARG_VanillaStoryManager");
        var quests = mod.Quests.ToDictionary(q => q.EditorID ?? q.FormKey.ToString());
        var nodes = mod.EnumerateMajorRecords<IAStoryManagerNodeGetter>().ToList();
        var sb = new StringBuilder();
        sb.AppendLine("# Argonia.esp: every record, read back from the built plugin");
        sb.AppendLine();
        sb.AppendLine($"Written by `make plugin-check` (tools/ArgoniaPlugin `list`) from `out/Argonia.esp`; masters: {string.Join(", ", mod.ModHeader.MasterReferences.Select(m => m.Master))}. " +
                      $"{mod.EnumerateMajorRecords().Count()} records. Quest overrides keep the winning record (aliases, stages, scripts) with Start Game Enabled off and their player-visible text removed; " +
                      $"story-manager overrides gain a first condition `GetGlobalValue ARG_VanillaStoryManager == 1` (the global is 0), so nothing under the node starts. The why is in `tools/ArgoniaPlugin/shutdown.json` and `mods/allowed-quests.json`.");
        sb.AppendLine();
        sb.AppendLine("| Group | Kind | Change | Records (editor id, form id) |");
        sb.AppendLine("|---|---|---|---|");
        string Row(IEnumerable<(string id, FormKey fk)> rs) => string.Join(", ", rs.Select(r => $"{r.id} `{r.fk.IDString()}`"));
        // Ours.
        foreach (var r in mod.EnumerateMajorRecords().Where(r => r.FormKey.ModKey == mod.ModKey))
            sb.AppendLine($"| ours | {Kind(r)} | new | {r.EditorID} `{r.FormKey}` |");
        var mq = quests["MQ101"];
        var mqOk = !mq.Flags.HasFlag(Quest.Flag.StartGameEnabled) && mq.Stages.Count == 1 && mq.Aliases.Count == 0
                   && mq.VirtualMachineAdapter is IQuestAdapterGetter a && a.Fragments.Single().Stage == 0 && a.Scripts.Single().Name == "ARG_QF_MQ101";
        if (!mqOk) errs.Add("MQ101 is not the one-stage diversion");
        sb.AppendLine($"| intro | quest | replaced: one stage 0 whose fragment (ARG_QF_MQ101) starts ARG_Opening and stops MQ101; no aliases, scenes or Helgen stages | MQ101 `{mq.FormKey}` |");
        var ws = mod.Worldspaces.Single();
        sb.AppendLine($"| opening | worldspace | BM&V's record kept, our marker in its persistent cell | {ws.EditorID} `{ws.FormKey}` |");
        var seen = new HashSet<string> { "MQ101", "ARG_Opening" };
        foreach (var g in plan.GetProperty("quests_sge_off").EnumerateObject())
        {
            var rs = new List<(string, FormKey)>();
            foreach (var e in g.Value.EnumerateArray())
            {
                var id = e.GetString()!; seen.Add(id);
                if (!quests.TryGetValue(id, out var q)) { errs.Add($"{id}: missing"); continue; }
                if (q.Flags.HasFlag(Quest.Flag.StartGameEnabled)) errs.Add($"{id}: still Start Game Enabled");
                if (q.Name != null || q.Stages.Any(s => s.LogEntries.Any(l => l.Entry != null))) errs.Add($"{id}: text not stripped");
                rs.Add((id, q.FormKey));
            }
            sb.AppendLine($"| {g.Name} | quest | Start Game Enabled off | {Row(rs)} |");
        }
        foreach (var q in quests.Values.Where(q => !seen.Contains(q.EditorID ?? "")))
            errs.Add($"{q.EditorID}: a quest override no group names");
        var byId = nodes.ToDictionary(n => n.EditorID ?? n.FormKey.ToString());
        foreach (var g in plan.GetProperty("story_nodes_off").EnumerateObject())
        {
            var rs = new List<(string, FormKey)>();
            foreach (var e in g.Value.EnumerateArray())
            {
                var id = e.GetString()!;
                var n = byId.GetValueOrDefault(id) ?? nodes.FirstOrDefault(x => x.FormKey.ToString() == id);
                if (n == null) { errs.Add($"{id}: node missing"); continue; }
                var c = n.Conditions.FirstOrDefault() as IConditionFloatGetter;
                if (c?.Data is not IGetGlobalValueConditionDataGetter d || d.Global.Link.FormKey != glob.FormKey || c.ComparisonValue != 1 || c.CompareOperator != CompareOperator.EqualTo)
                    errs.Add($"{id}: first condition is not the global gate");
                rs.Add((n.EditorID ?? "(no editor id)", n.FormKey));
            }
            sb.AppendLine($"| {g.Name} | story-manager node | gated off | {Row(rs)} |");
        }
        if (loadOrder.Length > 0)  // against the load order's winners: nothing but the intended change
        {
            var lo = Survey.Load(loadOrder);
            var wq = Survey.Winners<IQuestGetter>(lo); var wn = Survey.Winners<IAStoryManagerNodeGetter>(lo);
            foreach (var q in quests.Values.Where(q => q.FormKey.ModKey != mod.ModKey && q.EditorID != "MQ101"))
            {
                var w = wq[q.FormKey].rec;
                if (q.Stages.Count != w.Stages.Count || q.Aliases.Count != w.Aliases.Count || q.DialogConditions.Count != w.DialogConditions.Count
                    || (q.VirtualMachineAdapter?.Scripts.Count ?? 0) != (w.VirtualMachineAdapter?.Scripts.Count ?? 0) || q.Flags != (w.Flags & ~Quest.Flag.StartGameEnabled))
                    errs.Add($"{q.EditorID}: differs from the winner beyond the flag");
            }
            foreach (var n in nodes)
            {
                var w = wn[n.FormKey].rec;
                if (n.Conditions.Count != w.Conditions.Count + 1 || n.Parent.FormKey != w.Parent.FormKey || n.PreviousSibling.FormKey != w.PreviousSibling.FormKey)
                    errs.Add($"{n.EditorID ?? n.FormKey.ToString()}: differs from the winner beyond the gate");
            }
            sb.AppendLine();
            sb.AppendLine($"Compared with the load order's winners ({loadOrder.Length} plugins): stage, alias, condition and script counts, flags, parent and sibling links equal but for the change.");
        }
        if (nodes.Count != plan.GetProperty("story_nodes_off").EnumerateObject().Sum(g => g.Value.GetArrayLength())) errs.Add("node count differs from shutdown.json");
        sb.AppendLine();
        sb.AppendLine(errs.Count == 0 ? "Read-back: every override carries its change (MQ101 one stage; no quest named here is Start Game Enabled or keeps text; every node's first condition is the gate)." : "Read-back FAILED: " + string.Join("; ", errs));
        File.WriteAllText(md, sb.ToString());
        foreach (var e in errs) Console.Error.WriteLine(e);
        Console.WriteLine($"{md}: {sb.ToString().Split('\n').Length} lines, {errs.Count} errors");
        return errs.Count == 0 ? 0 : 1;
    }

    static string Kind(Mutagen.Bethesda.Plugins.Records.IMajorRecordGetter r) => r switch
    {
        IQuestGetter => "quest", IGlobalGetter => "global", IPlacedObjectGetter => "XMarker reference", _ => r.GetType().Name.Replace("BinaryOverlay", ""),
    };
}
