// dump <esp> <world.esm> <out.json>: the built place layer read back for tools/places/check.py, the way xEdit would
using Mutagen.Bethesda.Plugins.Aspects;
// show it: masters, record counts by type, every link that resolves nowhere, and the rows the checks read (refs
// with their bases, overrides of the world's refs, LAND, actors, packages, factions, classes, levelled lists
// reachable from ours). Navmesh is read by check.py from the plugin's bytes (tools/navmesh/esm.py).
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Cache;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;

static class Dump
{
    public static int Run(string esp, string worldEsm, string outPath)
    {
        var mod = SkyrimMod.CreateFromBinaryOverlay(esp, C.Rel, Survey.NoStrings);
        var world = C.Open(worldEsm);
        var lo = Write.Masters.Select(m => C.Open(m)).Append(world).Append(mod).ToList();
        var cache = lo.ToImmutableLinkCache();
        var me = mod.ModKey;
        var counts = new SortedDictionary<string, int>();
        void Count(string k) => counts[k] = counts.GetValueOrDefault(k) + 1;
        var unresolved = new List<string>();
        foreach (var r in mod.EnumerateMajorRecords())
        {
            Count(r.GetType().Name.Replace("BinaryOverlay", "") + (r.FormKey.ModKey == me ? "" : " (override)"));
            foreach (var l in r.EnumerateFormLinks())
                if (!l.FormKey.IsNull && !cache.TryResolve(l.FormKey, l.Type, out _))
                    if (unresolved.Count < 200) unresolved.Add($"{C.Key(r.FormKey)} -> {C.Key(l.FormKey)} <{l.Type.Name}>");
        }
        var refs = new List<object>();
        var overrides = new List<object>();
        var land = new List<object>();
        var actors = new List<object>();
        var cellsOut = new List<object>();
        void Walk(ICellGetter c, string space, int[]? grid)
        {
            foreach (var (r, persistent) in c.Persistent.Select(x => (x, true)).Concat(c.Temporary.Select(x => (x, false))))
            {
                var d = C.Ref(r, cache);
                d["space"] = space; d["grid"] = grid; d["persistent"] = persistent;
                if (cache.TryResolve<IMajorRecordGetter>(C.Fk((string)d["base"]!), out var b))
                    d["keywords"] = (b as IKeywordedGetter<IKeywordGetter>)?.Keywords?.Select(k => cache.TryResolve<IKeywordGetter>(k.FormKey, out var kw) ? kw.EditorID : C.Key(k.FormKey)).ToList();
                if (r is IPlacedNpcGetter) actors.Add(d);
                else if (r.FormKey.ModKey == me) refs.Add(d);
                else overrides.Add(d);
            }
            if (c.Landscape is { } l && l.VertexHeightMap is { } h)
            {
                var bytes = Enumerable.Range(0, 33 * 33).Select(i => unchecked((byte)h.HeightMap[i % 33, i / 33])).ToArray();
                land.Add(new Dictionary<string, object?>
                {
                    ["x"] = grid?[0], ["y"] = grid?[1], ["fk"] = C.Key(l.FormKey), ["offset"] = h.Offset, ["deltas"] = Convert.ToBase64String(bytes),
                    ["layers"] = l.Layers?.Count ?? 0,
                    ["alpha"] = l.Layers?.OfType<IAlphaLayerGetter>().Select(a => new Dictionary<string, object?> { ["quadrant"] = (int)a.Header!.Quadrant, ["texture"] = C.Key(a.Header.Texture.FormKey), ["n"] = a.AlphaLayerData?.Count ?? 0 }).ToList(),
                });
            }
            cellsOut.Add(new Dictionary<string, object?> { ["fk"] = C.Key(c.FormKey), ["edid"] = c.EditorID, ["space"] = space, ["grid"] = grid, ["override"] = c.FormKey.ModKey != me, ["navm"] = c.NavigationMeshes.Select(n => C.Key(n.FormKey)).ToList() });
        }
        foreach (var ws in mod.Worldspaces)
        {
            if (ws.TopCell is { } tc) Walk(tc, "exterior", null);
            foreach (var c in C.Cells(ws)) Walk(c, "exterior", c.Grid is { } g ? new[] { g.Point.X, g.Point.Y } : null);
        }
        foreach (var c in mod.EnumerateMajorRecords<ICellGetter>().Where(c => c.Grid == null && c.FormKey.ModKey == me)) Walk(c, c.EditorID ?? C.Key(c.FormKey), null);

        var npcs = mod.Npcs.Select(n => new Dictionary<string, object?>
        {
            ["fk"] = C.Key(n.FormKey), ["edid"] = n.EditorID, ["name"] = n.Name?.String, ["race"] = C.Key(n.Race.FormKey),
            ["level"] = n.Configuration.Level is INpcLevelGetter nl ? nl.Level : -1, ["pc_level_mult"] = n.Configuration.Level is IPcLevelMultGetter,
            ["template"] = C.Key(n.Template.FormKey), ["crime_faction"] = C.Key(n.CrimeFaction.FormKey), ["class"] = C.Key(n.Class.FormKey),
            ["packages"] = n.Packages.Select(p => C.Key(p.FormKey)).ToList(),
            ["factions"] = n.Factions.Select(f => cache.TryResolve<IFactionGetter>(f.Faction.FormKey, out var fa) ? fa.EditorID : C.Key(f.Faction.FormKey)).ToList(),
            ["faction_keys"] = n.Factions.Select(f => C.Key(f.Faction.FormKey)).ToList(),
            ["items"] = n.Items?.Select(i => C.Key(i.Item.Item.FormKey)).ToList(), ["outfit"] = C.Key(n.DefaultOutfit.FormKey),
        }).ToList();
        var packages = mod.Packages.Select(p => new Dictionary<string, object?>
        {
            ["fk"] = C.Key(p.FormKey), ["edid"] = p.EditorID, ["template"] = C.Key(p.PackageTemplate.FormKey), ["hour"] = p.ScheduleHour, ["minutes"] = p.ScheduleDurationInMinutes,
            ["location"] = p.Data.Values.OfType<IPackageDataLocationGetter>().Select(d => d.Location.Target is ILocationTargetGetter t ? C.Key(t.Link.FormKey) : null).FirstOrDefault(),
            ["radius"] = p.Data.Values.OfType<IPackageDataLocationGetter>().Select(d => (int?)d.Location.Radius).FirstOrDefault(),
            ["target"] = p.Data.Values.OfType<IPackageDataTargetGetter>().Select(d => d.Target is IPackageTargetSpecificReferenceGetter s ? C.Key(s.Reference.FormKey) : null).FirstOrDefault(x => x != null),
        }).ToList();
        var factions = mod.Factions.Select(f => new Dictionary<string, object?>
        {
            ["fk"] = C.Key(f.FormKey), ["edid"] = f.EditorID, ["flags"] = (int)f.Flags, ["vendor"] = f.Flags.HasFlag(Faction.FactionFlag.Vendor),
            ["chest"] = C.Key(f.MerchantContainer.FormKey), ["list"] = C.Key(f.VendorBuySellList.FormKey), ["crime"] = f.Flags.HasFlag(Faction.FactionFlag.TrackCrime),
        }).ToList();
        var classes = mod.Classes.Select(c => new Dictionary<string, object?> { ["fk"] = C.Key(c.FormKey), ["edid"] = c.EditorID, ["teaches"] = c.Teaches?.ToString(), ["max_level"] = c.MaxTrainingLevel }).ToList();
        // levelled lists reachable from our NPCs, containers and outfits
        var levelled = new List<string>();
        void Item(string from, FormKey k)
        {
            if (cache.TryResolve<ILeveledItemGetter>(k, out var li) && People.Levelled(li)) levelled.Add($"{from} -> {C.Key(k)} {li.EditorID}");
        }
        foreach (var n in mod.Npcs)
        {
            foreach (var i in n.Items ?? Array.Empty<IContainerEntryGetter>()) Item(n.EditorID ?? "", i.Item.Item.FormKey);
            if (cache.TryResolve<IOutfitGetter>(n.DefaultOutfit.FormKey, out var o)) foreach (var i in o.Items ?? Array.Empty<IFormLinkGetter<IOutfitTargetGetter>>()) Item(n.EditorID + " outfit", i.FormKey);
            if (n.Configuration.Level is IPcLevelMultGetter) levelled.Add($"{n.EditorID}: PC level mult");
            if (cache.TryResolve<ILeveledNpcGetter>(n.Template.FormKey, out _)) levelled.Add($"{n.EditorID}: templated on a LVLN");
        }
        foreach (var c in mod.Containers) foreach (var i in c.Items ?? Array.Empty<IContainerEntryGetter>()) Item(c.EditorID ?? "", i.Item.Item.FormKey);
        foreach (var a in actors.Cast<Dictionary<string, object?>>()) if (cache.TryResolve<ILeveledNpcGetter>(C.Fk((string)a["base"]!), out _)) levelled.Add($"actor {a["fk"]} is a LVLN");
        foreach (var r in refs.Cast<Dictionary<string, object?>>()) if (cache.TryResolve<ILeveledItemGetter>(C.Fk((string)r["base"]!), out var li) && People.Levelled(li)) levelled.Add($"ref {r["fk"]} -> {li.EditorID}");

        C.WriteJson(outPath, new Dictionary<string, object?>
        {
            ["esp"] = esp, ["masters"] = mod.ModHeader.MasterReferences.Select(m => m.Master.FileName.String).ToList(),
            ["flags"] = (int)mod.ModHeader.Flags, ["counts"] = counts, ["unresolved"] = unresolved,
            ["refs"] = refs, ["overrides"] = overrides, ["land"] = land, ["actors"] = actors, ["cells"] = cellsOut,
            ["npcs"] = npcs, ["packages"] = packages, ["factions"] = factions, ["classes"] = classes, ["levelled"] = levelled,
        });
        Console.WriteLine($"dump: {esp}: {string.Join(", ", counts.Select(kv => $"{kv.Key} {kv.Value}"))}; unresolved {unresolved.Count}");
        return 0;
    }
}
