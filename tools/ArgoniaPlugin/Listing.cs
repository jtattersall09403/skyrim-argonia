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
        var mqOk = !mq.Flags.HasFlag(Quest.Flag.StartGameEnabled) && mq.Stages.Count == 1 && mq.Stages[0].LogEntries.Count == 1 && mq.Aliases.Count == 0
                   && mq.VirtualMachineAdapter is IQuestAdapterGetter a && a.Fragments.Single().Stage == 0 && a.Scripts.Single().Name == "ARG_QF_MQ101";
        if (!mqOk) errs.Add("MQ101 is not the one-stage diversion (stage 0 needs one log entry for its fragment to run)");
        sb.AppendLine($"| intro | quest | replaced: one stage 0 with one empty log entry, which its fragment (ARG_QF_MQ101) binds to (no entry, no fragment: New Game stayed on the menu, 2026-11-06); the fragment moves the player to ARG_OpeningMarker, starts ARG_Opening and stops MQ101; no aliases, scenes or Helgen stages | MQ101 `{mq.FormKey}` |");
        var ws = mod.Worldspaces.Single(w => w.FormKey == FormKey.Factory("23D689:Black Marsh.esm"));
        sb.AppendLine($"| opening | worldspace | BM&V's record kept, our marker in its persistent cell | {ws.EditorID} `{ws.FormKey}` |");
        // The map (MapFix.cs): the four BM&V worlds' MNAM pan box set, the marker names fixed. The music (Music.cs):
        // ZNAM on those four and the Underdark (a child world with no map of its own).
        foreach (var w in mod.Worldspaces)
        {
            if (w.Music.IsNull) errs.Add($"{w.EditorID}: no music");
            else sb.AppendLine($"| music | worldspace | ZNAM `{w.Music.FormKey}`, the rest kept | {w.EditorID} `{w.FormKey}` |");
            if (w.Parent != null) continue;
            var mnam = w.MapData;
            if (mnam == null || mnam.NorthwestCellCoords.X >= mnam.SoutheastCellCoords.X || mnam.NorthwestCellCoords.Y <= mnam.SoutheastCellCoords.Y)
                errs.Add($"{w.EditorID}: no map box");
            else sb.AppendLine($"| map | worldspace | MNAM pan box NW({mnam.NorthwestCellCoords.X},{mnam.NorthwestCellCoords.Y}) SE({mnam.SoutheastCellCoords.X},{mnam.SoutheastCellCoords.Y}), the rest kept | {w.EditorID} `{w.FormKey}` |");
        }
        if (mod.Worldspaces.Count != 5) errs.Add($"{mod.Worldspaces.Count} worldspace overrides, not 5");
        var markers = mod.Worldspaces.SelectMany(w => w.TopCell?.Persistent.OfType<IPlacedObjectGetter>() ?? []).Where(r => r.MapMarker != null)
            .ToDictionary(r => r.FormKey.ToString(), r => r.MapMarker!.Name?.String);
        foreach (var (k, n) in new[] { ("0934A4:Black Marsh North.esp", "Lilmoth"), ("083283:Black Marsh North.esp", "Southern Morrowind Pass") })
            if (!markers.TryGetValue(k, out var got) || got != n) errs.Add($"map marker {k}: '{got}', not '{n}'");
            else sb.AppendLine($"| map | map marker | name only: {n} | `{k}` |");
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
        // MQ01's held quests (we.mq01.no-valenwood, we.mq01.no-welcome): Start Game Enabled off, started by MQ03's ending.
        var held = Opening.Valenwood.Select(v => FormKey.Factory(v)).Append(Opening.Welcome).ToHashSet();
        var heldRows = new List<(string, FormKey)>();
        foreach (var q in quests.Values.Where(q => held.Contains(q.FormKey)))
        {
            seen.Add(q.EditorID ?? ""); heldRows.Add((q.EditorID ?? q.FormKey.ToString(), q.FormKey));
            if (q.Flags.HasFlag(Quest.Flag.StartGameEnabled)) errs.Add($"{q.EditorID}: still Start Game Enabled");
        }
        if (heldRows.Count != held.Count) errs.Add($"MQ01's held quests: {heldRows.Count} of {held.Count} overridden");
        sb.AppendLine($"| mq01-held | quest | Start Game Enabled off, started by MQ03's ending | {Row(heldRows)} |");
        foreach (var q in quests.Values.Where(q => q.FormKey.ModKey != mod.ModKey && !seen.Contains(q.EditorID ?? "")))
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
            // The worldspace: the winner's own fields, and its plugin a master.
            // Each world (the map's four): the winner's own fields but MNAM's NW/SE cells, and its plugin a master.
            var masters = mod.ModHeader.MasterReferences.Select(m => m.Master).ToList();
            var wwin = Survey.Winners<IWorldspaceGetter>(lo);
            foreach (var wo in mod.Worldspaces)
            {
                var (wwo, wfo) = wwin[wo.FormKey];
                var wmask = new Worldspace.TranslationMask(true) { SubCells = false, TopCell = false, SubCellsTimestamp = false, SubCellsUnknown = false };  // the group stamp is the writer's
                var wa = wo.DeepCopy(wmask); var wb = wwo.DeepCopy(wmask);
                if (wa.MapData != null && wb.MapData != null) { wb.MapData.NorthwestCellCoords = wa.MapData.NorthwestCellCoords; wb.MapData.SoutheastCellCoords = wa.MapData.SoutheastCellCoords; }
                wb.Music.SetTo(wa.Music.FormKey);
                if (!wa.Equals(wb)) errs.Add($"{wo.EditorID}: not the winner's record ({wfo}) beyond the map box and music: {wa.GetEqualsMask(wb)}");
                if (!masters.Contains(wfo)) errs.Add($"{wo.EditorID}: its winner {wfo} is not a master");
            }
            // Every overridden record's winning plugin is a master, and the masters are in load order.
            foreach (var r in mod.EnumerateMajorRecords().Where(r => r.FormKey.ModKey != mod.ModKey))
                if (!masters.Contains(r.FormKey.ModKey)) errs.Add($"{r.EditorID}: {r.FormKey.ModKey} not a master");
            var pos = masters.Select(m => lo.FindIndex(x => x.ModKey == m)).ToList();
            if (pos.Any(i => i < 0)) errs.Add("a master is not in the load order: " + string.Join(", ", masters.Where((m, i) => pos[i] < 0)));
            else if (!pos.SequenceEqual(pos.OrderBy(i => i))) errs.Add("masters out of load order");
            // The marker stands on a winning navmesh triangle of its worldspace, within 16 units of its height.
            var mk = mod.EnumerateMajorRecords<IPlacedObjectGetter>().Single(r => r.EditorID == "ARG_OpeningMarker");
            var spot = mk.Placement!.Position;
            var (ww, wfrom) = wwin[ws.FormKey];
            var wsNav = ww.SubCells.SelectMany(b => b.Items).SelectMany(sb => sb.Items).SelectMany(c => c.NavigationMeshes).Select(n => n.FormKey).ToHashSet();
            foreach (var m in lo) foreach (var w2 in m.Worldspaces.Where(w2 => w2.FormKey == ws.FormKey))
                foreach (var c in w2.SubCells.SelectMany(b => b.Items).SelectMany(sb => sb.Items)) foreach (var n in c.NavigationMeshes) wsNav.Add(n.FormKey);
            var under = Seat.Under(lo, spot).Where(h => wsNav.Contains(h.Navmesh) && Math.Abs(h.Z - spot.Z) <= 16).ToList();
            if (under.Count == 0) errs.Add("ARG_OpeningMarker: no winning navmesh triangle of its worldspace under it");
            sb.AppendLine();
            sb.AppendLine($"Worldspace {ws.EditorID}: the winner's record ({wfrom}), a master. ARG_OpeningMarker at {spot}: " +
                          string.Join("; ", under.Select(h => $"on navmesh `{h.Navmesh.IDString()}` ({h.From}, the winner) triangle {h.Triangle}, its height {h.Z:F1}")) + ".");
            sb.AppendLine();
            sb.AppendLine($"Compared with the load order's winners ({loadOrder.Length} plugins): stage, alias, condition and script counts, flags, parent and sibling links equal but for the change.");
        }
        if (nodes.Count != plan.GetProperty("story_nodes_off").EnumerateObject().Sum(g => g.Value.GetArrayLength())) errs.Add("node count differs from shutdown.json");
        sb.AppendLine();
        sb.AppendLine(errs.Count == 0 ? "Read-back: every override carries its change (MQ101 one stage with its log entry; no quest named here is Start Game Enabled or keeps text; every node's first condition is the gate)." : "Read-back FAILED: " + string.Join("; ", errs));
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
