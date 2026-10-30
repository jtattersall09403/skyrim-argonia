// `links`: every FormLink in our built plugins resolved against the game's exact load order, and every master present
// and loaded before the plugin that names it (game-6: a null base crashed coc ARG_HoldingCell, 2026-10-30).
//   links --data <dir> --order <file> --check Argonia.esm,ArgoniaWorld.esm [--ours <dir>[,<dir>...]]
// --order lists the plugins in the order the game is given them (vanilla, then the profile's plugins.txt, then
// ours); lines may carry plugins.txt's '*'. The engine then loads every master-flagged plugin before the rest, and
// hoists a non-master that a master names above that master; the check applies the same rule. Plugins are read
// from the --ours dirs first (the first that has it), then --data. One plugin at a time through the binary overlay, keeping only the FormKeys
// we need (the memory guidance), never a whole-environment LinkCache. Exit 1 on any finding.
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;

namespace ArgoniaGen;

static class LinkCheck
{
    record Plug(string Name, bool Master, string[] Masters);

    public static int Run(string data, string orderFile, string[] check, string? ours)
    {
        // Case-insensitive, as Windows finds them: vanilla-data-files.txt is lower case, Data is not.
        var files = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        foreach (var d in new[] { data }.Concat((ours ?? "").Split(',', StringSplitOptions.RemoveEmptyEntries).Reverse()))
            foreach (var f in Directory.EnumerateFiles(d)) files[Path.GetFileName(f)] = f;
        string PathOf(string name) => files.TryGetValue(name, out var f) ? f : Path.Combine(data, name);
        var given = File.ReadAllLines(orderFile).Select(l => l.Trim().TrimStart('*')).Where(l => l.Length > 0 && !l.StartsWith('#'))
            .Distinct(StringComparer.OrdinalIgnoreCase).ToList();
        var problems = new List<string>();
        var plugs = new List<Plug>();
        foreach (var n in given)
        {
            var p = PathOf(n);
            if (!File.Exists(p)) { problems.Add($"order: {n} is listed but not found in {data}"); continue; }
            using var m = SkyrimMod.CreateFromBinaryOverlay(p, SkyrimRelease.SkyrimSE);
            var ext = Path.GetExtension(n).ToLowerInvariant();
            bool master = ext is ".esm" or ".esl" || m.ModHeader.Flags.HasFlag(SkyrimModHeader.HeaderFlag.Master);
            plugs.Add(new Plug(n, master, m.ModHeader.MasterReferences.Select(r => r.Master.FileName.String).ToArray()));
        }
        var order = Effective(plugs);
        var at = order.Select((p, i) => (p.Name, i)).ToDictionary(t => t.Name, t => t.i, StringComparer.OrdinalIgnoreCase);
        Console.WriteLine($"links: {order.Count} plugins in the engine's order; ours at " +
                          string.Join(", ", check.Select(c => $"{c} {(at.TryGetValue(c, out var i) ? i : -1)}")));

        // Masters: present, and loaded before the plugin that names them. All plugins, not only ours: one unmet
        // master anywhere makes the engine drop or misread that plugin.
        foreach (var p in order)
            foreach (var mname in p.Masters)
                if (!at.TryGetValue(mname, out var mi)) problems.Add($"master: {p.Name} needs {mname}, which is not loaded");
                else if (mi > at[p.Name]) problems.Add($"master: {p.Name} (slot {at[p.Name]}) needs {mname}, which loads after it (slot {mi})");

        // Our plugins list every master's own masters, as the Creation Kit does: else the engine hoists an ESP master
        // above an ESM of ours but leaves that ESP's own master below it (Cipactli above HTBM, game-6).
        var byName = order.ToDictionary(p => p.Name, StringComparer.OrdinalIgnoreCase);
        foreach (var c in check.Where(byName.ContainsKey))
        {
            var mine = new HashSet<string>(byName[c].Masters, StringComparer.OrdinalIgnoreCase);
            foreach (var mname in byName[c].Masters.Where(x => byName.ContainsKey(x) && !Official.Contains(x, StringComparer.OrdinalIgnoreCase)))
                foreach (var mm in byName[mname].Masters.Where(x => !mine.Contains(x)))
                    problems.Add($"master: {c} names {mname} but not {mname}'s own master {mm}");
        }

        // FormLinks: each link in our plugins resolves, as its type, in the order up to and including its plugin.
        foreach (var c in check)
        {
            if (!at.ContainsKey(c)) { problems.Add($"links: {c} is not in the order"); continue; }
            var need = new Dictionary<FormKey, List<(string From, Type Want)>>();
            var owner = ModKey.FromFileName(c);
            using (var m = SkyrimMod.CreateFromBinaryOverlay(PathOf(c), SkyrimRelease.SkyrimSE))
            {
                var allowed = new HashSet<ModKey>(m.ModHeader.MasterReferences.Select(r => r.Master)) { owner };
                // A music type with no track is an access violation when the engine picks one (SkyrimSE.exe+0327DC4).
                foreach (var mu in m.MusicTypes)
                    if (mu.Tracks is not { Count: > 0 }) problems.Add($"music: {c} {Describe(mu)} has no track");
                foreach (var r in m.EnumerateMajorRecords())
                    foreach (var l in r.EnumerateFormLinks())
                    {
                        if (l.IsNull) continue;
                        if (!allowed.Contains(l.FormKey.ModKey))
                        {
                            problems.Add($"links: {c} {Describe(r)} names {l.FormKey}, whose plugin is not one of its masters");
                            continue;
                        }
                        if (!need.TryGetValue(l.FormKey, out var list)) need[l.FormKey] = list = new();
                        if (list.Count < 3) list.Add((Describe(r), l.Type));
                    }
            }
            var found = new Dictionary<FormKey, Type>();
            foreach (var p in order.Take(at[c] + 1))
            {
                var mk = ModKey.FromFileName(p.Name);
                using var m = SkyrimMod.CreateFromBinaryOverlay(PathOf(p.Name), SkyrimRelease.SkyrimSE);
                foreach (var r in m.EnumerateMajorRecords())
                    if (need.ContainsKey(r.FormKey) && (r.FormKey.ModKey == mk || !found.ContainsKey(r.FormKey)))
                        found[r.FormKey] = r.GetType();
            }
            int bad = 0;
            foreach (var (fk, uses) in need.OrderBy(k => k.Key.ToString()))
                foreach (var (from, want) in uses)
                {
                    string? why = !found.TryGetValue(fk, out var got) ? "unresolved"
                        : !want.IsAssignableFrom(got) ? $"is a {got.Name.Replace("BinaryOverlay", "")}, wanted {want.Name}" : null;
                    if (why == null) continue;
                    if (++bad <= 200) problems.Add($"links: {c} {from} -> {fk} {why}");
                }
            if (bad > 200) problems.Add($"links: {c}: {bad - 200} more");
            Console.WriteLine($"links: {c}: {need.Count} distinct targets, {bad} bad");
        }
        foreach (var p in problems) Console.WriteLine(p);
        Console.WriteLine(problems.Count == 0 ? "links: OK" : $"links: {problems.Count} problems");
        return problems.Count == 0 ? 0 : 1;
    }

    // The five official masters always load first, in this order, whatever the list says: never hoisted, so the
    // parent-master rule skips them.
    static readonly string[] Official = { "Skyrim.esm", "Update.esm", "Dawnguard.esm", "HearthFires.esm", "Dragonborn.esm" };

    static string Describe(IMajorRecordGetter r) => $"{r.Registration.Name}:{r.FormKey}" + (r.EditorID is { } e ? $" ({e})" : "");

    // The engine's order: master-flagged plugins first, each preceded by any non-master it names (hoisted), then the
    // rest in the given order.
    static List<Plug> Effective(List<Plug> given)
    {
        var by = given.ToDictionary(p => p.Name, StringComparer.OrdinalIgnoreCase);
        given = Official.Where(by.ContainsKey).Select(o => by[o])
            .Concat(given.Where(p => !Official.Contains(p.Name, StringComparer.OrdinalIgnoreCase))).ToList();
        var outl = new List<Plug>();
        var placed = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (var p in given.Where(p => p.Master))
        {
            foreach (var mn in p.Masters)
                if (by.TryGetValue(mn, out var mp) && !mp.Master && placed.Add(mp.Name)) outl.Add(mp);
            if (placed.Add(p.Name)) outl.Add(p);
        }
        outl.AddRange(given.Where(p => placed.Add(p.Name)));
        return outl;
    }
}
