using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;
// cell <plugin> <cell formkey>: the cell's grid, its refs (base editor id, position) and its navmesh vertices' centre.
static class CellStudy
{
    public static void Run(string path, string cellKey)
    {
        using var mod = SkyrimMod.CreateFromBinaryOverlay(path, SkyrimRelease.SkyrimSE);
        var fk = FormKey.Factory(cellKey);
        var bases = mod.EnumerateMajorRecords().Where(r => r is not IPlacedGetter && r is not ICellGetter && r is not INavigationMeshGetter)
            .GroupBy(r => r.FormKey).ToDictionary(g => g.Key, g => g.First().EditorID);
        foreach (var w in mod.Worldspaces)
        {
            if (w.TopCell is { } top && top.FormKey == fk) Console.WriteLine("top cell");
            foreach (var b in w.SubCells) foreach (var sb in b.Items) foreach (var c in sb.Items)
            {
                if (c.FormKey != fk) continue;
                Console.WriteLine($"world {w.EditorID} {w.FormKey} cell {c.EditorID} grid {c.Grid?.Point} flags {c.Flags}");
                foreach (var r in c.Temporary.Concat(c.Persistent))
                {
                    if (r is IPlacedObjectGetter po)
                        Console.WriteLine($"  REFR {po.FormKey} {po.EditorID} base={bases.GetValueOrDefault(po.Base.FormKey) ?? po.Base.FormKey.ToString()} pos={po.Placement?.Position} rot={po.Placement?.Rotation}");
                }
                foreach (var n in c.NavigationMeshes)
                    if (n.Data is { } d)
                    {
                        var v = d.Vertices;
                        Console.WriteLine($"  NAVM {n.FormKey} verts={v.Count} tris={d.Triangles.Count} x={v.Min(p => p.X):F0}..{v.Max(p => p.X):F0} y={v.Min(p => p.Y):F0}..{v.Max(p => p.Y):F0} z={v.Min(p => p.Z):F0}..{v.Max(p => p.Z):F0}");
                        foreach (var t in d.Triangles.Take(4000).Where((_, i) => i % 6 == 0))
                        {
                            var a = v[t.Vertices.X]; var b2 = v[t.Vertices.Y]; var c2 = v[t.Vertices.Z];
                            Console.WriteLine($"    tri centre {(a.X + b2.X + c2.X) / 3:F0},{(a.Y + b2.Y + c2.Y) / 3:F0},{(a.Z + b2.Z + c2.Z) / 3:F0}");
                        }
                    }
            }
        }
    }
}
