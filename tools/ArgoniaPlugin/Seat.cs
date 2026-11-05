using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;
using Noggog;
// The navmesh under a spot, from the load order's winning navmeshes: the triangle whose x,y outline holds the spot.
static class Seat
{
    public record Hit(FormKey Navmesh, ModKey From, int Triangle, float Z);

    public static List<Hit> Under(List<ISkyrimModGetter> mods, P3Float p)
    {
        var hits = new List<Hit>();
        foreach (var (fk, (n, from)) in Survey.Winners<INavigationMeshGetter>(mods))
        {
            if (n.Data is not { } d || d.Vertices.Count == 0) continue;
            var v = d.Vertices;
            if (p.X < v.Min(q => q.X) || p.X > v.Max(q => q.X) || p.Y < v.Min(q => q.Y) || p.Y > v.Max(q => q.Y)) continue;
            for (var i = 0; i < d.Triangles.Count; i++)
            {
                var t = d.Triangles[i].Vertices; var a = v[t.X]; var b = v[t.Y]; var c = v[t.Z];
                var den = (b.Y - c.Y) * (a.X - c.X) + (c.X - b.X) * (a.Y - c.Y);
                if (Math.Abs(den) < 1e-6) continue;
                var l1 = ((b.Y - c.Y) * (p.X - c.X) + (c.X - b.X) * (p.Y - c.Y)) / den;
                var l2 = ((c.Y - a.Y) * (p.X - c.X) + (a.X - c.X) * (p.Y - c.Y)) / den;
                var l3 = 1 - l1 - l2;
                if (l1 < 0 || l2 < 0 || l3 < 0) continue;
                hits.Add(new Hit(fk, from, i, l1 * a.Z + l2 * b.Z + l3 * c.Z));
            }
        }
        return hits;
    }

    // seat <x> <y> <z> <plugins...>: the winning navmesh triangles under the spot, and the winner of each named record.
    public static void Run(string[] args)
    {
        var p = new P3Float(float.Parse(args[0]), float.Parse(args[1]), float.Parse(args[2]));
        var mods = Survey.Load(args[3..]);
        foreach (var h in Under(mods, p)) Console.WriteLine($"NAVM {h.Navmesh} winner={h.From} tri={h.Triangle} z={h.Z:F1} (spot z {p.Z})");
        foreach (var key in new[] { "005A9F:Black Marsh.esm", "00591F:Black Marsh.esm", "23D689:Black Marsh.esm", "079823:Black Marsh.esm" })
        {
            var fk = FormKey.Factory(key);
            foreach (var m in mods)
                foreach (var r in m.EnumerateMajorRecords().Where(r => r.FormKey == fk))
                    Console.WriteLine($"{key} in {m.ModKey}: {r.GetType().Name.Replace("BinaryOverlay", "")} {r.EditorID} {(r is IPlacedObjectGetter po ? $"pos={po.Placement?.Position} flags={po.MajorRecordFlagsRaw:X} enable={po.EnableParent?.Reference.FormKey}" : "")}");
        }
        // The worldspace's own fields and its persistent cell, each plugin's version, and the refs near the spot.
        var wfk = FormKey.Factory("23D689:Black Marsh.esm");
        var mask = new Worldspace.TranslationMask(true) { SubCells = false, TopCell = false };
        var ws = mods.SelectMany(m => m.Worldspaces.Where(w => w.FormKey == wfk).Select(w => (m.ModKey, w))).ToList();
        foreach (var (mk, w) in ws.Skip(1))
            Console.WriteLine($"BlackMarsh {mk} vs {ws[0].ModKey}: fields equal={w.DeepCopy(mask).Equals(ws[0].w.DeepCopy(mask))} flags={w.Flags} parent={w.Parent?.Worldspace.FormKey} top={w.TopCell?.FormKey} topPersistent={w.TopCell?.Persistent.Count}");
        foreach (var (mk, w) in ws)
            foreach (var r in (w.TopCell?.Persistent ?? []).Concat(w.SubCells.SelectMany(b => b.Items).SelectMany(sb => sb.Items).Where(c => c.Grid?.Point == new P2Int(1, -2)).SelectMany(c => c.Persistent.Concat(c.Temporary))))
                if (r is IPlacedGetter pl && pl.Placement is { } pp && Math.Abs(pp.Position.X - p.X) < 300 && Math.Abs(pp.Position.Y - p.Y) < 300)
                    Console.WriteLine($"  near spot in {mk}: {r.FormKey} {r.GetType().Name.Replace("BinaryOverlay", "")} pos={pp.Position}");
    }
}
