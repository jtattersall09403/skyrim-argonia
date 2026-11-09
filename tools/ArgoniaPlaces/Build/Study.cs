// study <Data dir> <plugin...>: the evidence for how a plugin lays land, navmesh and refs over a master's worldspace
// (place-studio.md, Build): per plugin, its NAVI (entries, and how many name navmeshes of its own vs a master's), its
// NAVM, LAND and CELL overrides of a master, and its placed-ref overrides of a master by how they are switched off.
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;

static class Study
{
    public static int Run(string[] a)
    {
        var data = a[0];
        foreach (var f in a[1..])
        {
            using var m = SkyrimMod.CreateFromBinaryOverlay(Path.Combine(data, f), SkyrimRelease.SkyrimSE, Survey.NoStrings);
            var me = m.ModKey;
            int naviEntries = 0, naviOwn = 0;
            foreach (var n in m.NavigationMeshInfoMaps)
                foreach (var e in n.MapInfos) { naviEntries++; if (e.NavigationMesh.FormKey.ModKey == me) naviOwn++; }
            int navmOver = 0, navmNew = 0, landOver = 0, cellOver = 0, refOver = 0, refDel = 0, refDis = 0, refLow = 0, refNew = 0, refNewPersist = 0;
            foreach (var c in m.EnumerateMajorRecords<ICellGetter>())
            {
                if (c.FormKey.ModKey != me) cellOver++;
                foreach (var n in c.NavigationMeshes) { if (n.FormKey.ModKey != me) navmOver++; else navmNew++; }
                if (c.Landscape is { } l && l.FormKey.ModKey != me) landOver++;
                foreach (var r in c.Temporary.Concat(c.Persistent))
                {
                    if (r.FormKey.ModKey == me) { refNew++; if (c.Persistent.Contains(r)) refNewPersist++; continue; }
                    refOver++;
                    if (r.IsDeleted) refDel++;
                    else if ((r.MajorRecordFlagsRaw & 0x800) != 0) { refDis++; if (r is IPlacedObjectGetter p && p.Placement?.Position.Z < -29000) refLow++; }
                }
            }
            Console.WriteLine($"{f}: NAVI {m.NavigationMeshInfoMaps.Count} rec, {naviEntries} NVMI ({naviOwn} own navmeshes, {naviEntries - naviOwn} a master's); NAVM {navmNew} new, {navmOver} overrides; LAND overrides {landOver}; CELL overrides {cellOver}; refs new {refNew} (persistent {refNewPersist}), overrides {refOver}: deleted {refDel}, initially disabled {refDis} (of them at z<-29000: {refLow})");
        }
        return 0;
    }
}
