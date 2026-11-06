using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;
using Noggog;
// inspect <what> <plugins...>: read-only questions about the load order.
//   player   who overrides the Player NPC and the playable races, with outfit, skin and default items
//   movt     every plugin's movement types and their speeds
//   ref:<formkey>   a placed object's position in each plugin, and the objects near it there
//   navnear:<x>:<y>:<r>   winning navmesh triangle centres within r units of x,y (worldspace cell grid shown)
static class Inspect
{
    public static void Run(string what, string[] paths)
    {
        var mods = Survey.Load(paths);
        if (what == "player")
        {
            foreach (var m in mods)
            {
                foreach (var n in m.Npcs.Where(n => n.FormKey == FormKey.Factory("000007:Skyrim.esm")))
                    Console.WriteLine($"PLAYER in {m.ModKey}: outfit={n.DefaultOutfit.FormKey} skin={n.WornArmor.FormKey} race={n.Race.FormKey} items={string.Join(",", (n.Items ?? []).Select(i => i.Item.Item.FormKey))}");
                foreach (var r in m.Races.Where(r => r.Flags.HasFlag(Race.Flag.Playable)))
                    Console.WriteLine($"RACE {r.EditorID} in {m.ModKey}: skin={r.Skin.FormKey}");
                foreach (var o in m.Outfits) if (o.EditorID != null && o.EditorID.Contains("Player", StringComparison.OrdinalIgnoreCase)) Console.WriteLine($"OUTFIT {o.EditorID} in {m.ModKey}");
            }
            return;
        }
        if (what == "movt")
        {
            foreach (var m in mods)
                foreach (var t in m.MovementTypes)
                {
                    Console.WriteLine($"MOVT {t.EditorID} in {m.ModKey}: " + string.Join(" ", typeof(IMovementTypeGetter).GetProperties().Where(pp => pp.PropertyType == typeof(float)).Select(pp => $"{pp.Name}={pp.GetValue(t)}")));
                }
            return;
        }
        if (what.StartsWith("ref:"))
        {
            var k = FormKey.Factory(what[4..]);
            var bases = mods.SelectMany(m => m.EnumerateMajorRecords()).Where(r => r is not IPlacedGetter && r.EditorID != null).GroupBy(r => r.FormKey).ToDictionary(g => g.Key, g => g.Last().EditorID);
            foreach (var m in mods) foreach (var r in m.EnumerateMajorRecords<IPlacedObjectGetter>().Where(r => r.FormKey == k))
            {
                var pos = r.Placement!.Position;
                Console.WriteLine($"REF {k} in {m.ModKey}: base={bases.GetValueOrDefault(r.Base.FormKey)} pos={pos}");
                foreach (var o in mods.Where(mm => mm.ModKey.FileName.String.StartsWith("Black Marsh")).SelectMany(mm => mm.EnumerateMajorRecords<IPlacedObjectGetter>()))
                    if (o.Placement is { } op && Math.Abs(op.Position.X - pos.X) < 600 && Math.Abs(op.Position.Y - pos.Y) < 600 && Math.Abs(op.Position.Z - pos.Z) < 600)
                        Console.WriteLine($"  near: {o.FormKey} {bases.GetValueOrDefault(o.Base.FormKey)} pos={op.Position}");
            }
            return;
        }
        var a = what.Split(':'); float x = float.Parse(a[1]), y = float.Parse(a[2]), rr = float.Parse(a[3]);
        foreach (var (fk, (n, from)) in Survey.Winners<INavigationMeshGetter>(mods))
        {
            if (n.Data is not { } d || d.Vertices.Count == 0) continue;
            if (d.Parent is not IWorldspaceNavmeshParentGetter wp || wp.Parent.FormKey != FormKey.Factory("23D689:Black Marsh.esm")) continue;
            var v = d.Vertices;
            for (var i = 0; i < d.Triangles.Count; i++)
            {
                var t = d.Triangles[i].Vertices; var p = v[t.X]; var q = v[t.Y]; var s = v[t.Z];
                float cx = (p.X + q.X + s.X) / 3, cy = (p.Y + q.Y + s.Y) / 3, cz = (p.Z + q.Z + s.Z) / 3;
                if (Math.Abs(cx - x) > rr || Math.Abs(cy - y) > rr) continue;
                Console.WriteLine($"NAVM {fk} {from} tri={i} centre={cx:F0},{cy:F0},{cz:F0} cell={(int)Math.Floor(cx / 4096)},{(int)Math.Floor(cy / 4096)}");
            }
        }
    }
}
