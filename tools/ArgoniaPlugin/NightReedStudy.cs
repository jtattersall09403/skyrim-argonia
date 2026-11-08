using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;
using Noggog;

// nightreed <plugins...>: read-only measurements of the Night-Reed quests' places (TG01 at Soulrest and Lilmoth, TG02 in
// Pusbottom): each host cell's navmesh, water height and notable refs, the eel's base, and vanilla package shapes.
static class NightReedStudy
{
    static FormKey K(string k) => FormKey.Factory(k);
    public static void Run(string[] paths)
    {
        var mods = Survey.Load(paths);
        var cells = Survey.Winners<ICellGetter>(mods);
        var navs = Survey.Winners<INavigationMeshGetter>(mods);
        var placed = Survey.Winners<IPlacedGetter>(mods);
        var names = new Dictionary<FormKey, string?>();
        foreach (var m in mods) foreach (var r in m.EnumerateMajorRecords()) if (r is not IPlacedGetter && r is not ICellGetter) names[r.FormKey] = r.EditorID;
        var world = K("23D689:Black Marsh.esm");
        var wrec = Survey.Winners<IWorldspaceGetter>(mods)[world].rec;
        Console.WriteLine($"world land/water {wrec.LandDefaults?.DefaultLandHeight}/{wrec.LandDefaults?.DefaultWaterHeight} water {wrec.Water.FormKey}");
        foreach (var arg in Environment.GetEnvironmentVariable("NR_CELLS")!.Split(';'))
        {
            var c = cells[K(arg)].rec;
            Console.WriteLine($"CELL {c.FormKey} {c.EditorID} grid {c.Grid?.Point} flags {c.Flags} water {c.WaterHeight}");
            foreach (var (k, (n, from)) in navs)
            {
                var par = n.Data?.Parent;
                bool mine = par is ICellNavmeshParentGetter cp ? cp.Parent.FormKey == c.FormKey
                    : par is IWorldspaceNavmeshParentGetter wp && c.Grid != null && n.Data.Vertices.Count > 0 && (int)MathF.Floor(n.Data.Vertices[0].X / 4096) == c.Grid.Point.X && (int)MathF.Floor(n.Data.Vertices[0].Y / 4096) == c.Grid.Point.Y && wp.Parent.FormKey == world;
                if (!mine) continue;
                var v = n.Data!.Vertices;
                Console.WriteLine($"  NAVM {k} from {from} tris={n.Data.Triangles.Count} x={v.Min(p => p.X):F0}..{v.Max(p => p.X):F0} y={v.Min(p => p.Y):F0}..{v.Max(p => p.Y):F0} z={v.Min(p => p.Z):F0}..{v.Max(p => p.Z):F0}");
                if (Environment.GetEnvironmentVariable("NR_TRIS") == "1")
                    foreach (var (t, i) in n.Data.Triangles.Select((t, i) => (t, i)).Where(e => e.i % 4 == 0))
                    {
                        var a = v[t.Vertices.X]; var b = v[t.Vertices.Y]; var cc = v[t.Vertices.Z];
                        Console.WriteLine($"    tri {(a.X + b.X + cc.X) / 3:F0},{(a.Y + b.Y + cc.Y) / 3:F0},{(a.Z + b.Z + cc.Z) / 3:F0}");
                    }
            }
            // the cell's refs: interior by membership in any plugin's copy, exterior by grid
            var keys = new HashSet<FormKey>();
            if (c.Grid == null)
            {
                foreach (var m in mods) foreach (var cb in m.Cells.Records) foreach (var sb in cb.SubBlocks) foreach (var cl in sb.Cells)
                    if (cl.FormKey == c.FormKey) foreach (var x in cl.Persistent.Concat(cl.Temporary)) keys.Add(x.FormKey);
            }
            else
                foreach (var (k2, (r2, _)) in placed)
                    if (r2.Placement is { } p2 && (int)MathF.Floor(p2.Position.X / 4096) == c.Grid.Point.X && (int)MathF.Floor(p2.Position.Y / 4096) == c.Grid.Point.Y) keys.Add(k2);
            foreach (var k in keys)
            {
                if (!placed.TryGetValue(k, out var e) || e.rec.Placement == null) continue;
                var r = e.rec;
                var bk = r switch { IPlacedObjectGetter o => o.Base.FormKey, IPlacedNpcGetter pn => pn.Base.FormKey, _ => FormKey.Null };
                var bn = names.GetValueOrDefault(bk) ?? bk.ToString();
                var rx = Environment.GetEnvironmentVariable("NR_RX") ?? "Door|Bed|Chair|Bench|Stool|Chest|Npc|Water|Canal|Stilt|House|Awning|Tent|Marker|Table|Barrel";
                if (r is IPlacedNpcGetter || System.Text.RegularExpressions.Regex.IsMatch(bn, rx))
                    Console.WriteLine($"  REF {k} {r.EditorID} base={bn} pos={r.Placement.Position} rot={r.Placement.Rotation} flags={r.MajorRecordFlagsRaw:X}");
            }
        }
        foreach (var k in (Environment.GetEnvironmentVariable("NR_BASES") ?? "").Split(';', StringSplitOptions.RemoveEmptyEntries))
        {
            var r = mods.SelectMany(m => m.EnumerateMajorRecords()).Last(x => x.FormKey == K(k));
            Console.WriteLine($"BASE {k} {r.GetType().Name} {r.EditorID}" + (r is INpcGetter n ? $" level={n.Configuration.Level} flags={n.Configuration.Flags} tpl={n.Template.FormKey} race={n.Race.FormKey} class={n.Class.FormKey}" : ""));
        }
        // NR_LAND=x0,y0,x1,y1,step: the land's height on a grid (rows north to south), to find water deeper than 150.
        if (Environment.GetEnvironmentVariable("NR_LAND") is { } land)
        {
            var a = land.Split(',').Select(float.Parse).ToArray();
            for (var y = a[3]; y >= a[1]; y -= a[4])
                Console.WriteLine($"LAND y={y,6}: " + string.Join(" ", Enumerable.Range(0, (int)((a[2] - a[0]) / a[4]) + 1).Select(i => $"{Surface.Land(mods, world, a[0] + i * a[4], y) ?? 9999,5:F0}")));
        }
        var prx = Environment.GetEnvironmentVariable("NR_PACK");
        if (prx != null)
            foreach (var p in mods[0].Packages.Where(p => p.EditorID != null && System.Text.RegularExpressions.Regex.IsMatch(p.EditorID, prx)).Take(40))
                Console.WriteLine($"PACK {p.FormKey} {p.EditorID} tpl={names.GetValueOrDefault(p.PackageTemplate.FormKey)} sched={p.ScheduleHour}h+{p.ScheduleDurationInMinutes}m day={p.ScheduleDayOfWeek} data={string.Join(",", p.Data.Select(d => d.Value.GetType().Name))} conds={p.Conditions.Count}");
    }
}
