// Water read-backs and studies (read only; lane W, walk 5).
//   waterstudy records <edid,edid,...|*> <plugins...>   every field of the named WATR records in each plugin (the last wins)
//   waterstudy tamriel <Data dir>                       how Tamriel uses its water: cells per WATR (XCWT), placed water
//                                                       activators (ACTI with a water type) per WATR, and the flowing types
//   waterstudy cells <esm> <cells.json>                 what our cells reference: has-water flag, XCLW, XCWT per kind
using System.Drawing;
using System.Reflection;
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Noggog;

static class WaterStudy
{
    const SkyrimRelease Rel = SkyrimRelease.SkyrimSE;

    public static int Run(string[] a) => a[0] switch
    {
        "records" => Records(a[1], a[2..]),
        "tamriel" => Tamriel(a[1]),
        "cells" => Cells(a[1], a[2]),
        "check" => Check(a[1], a[2], a[3], a[4], a.Length > 5 ? a[5] : null),
        "plan" => Plan(a[1], a[2], a[3], a.Length > 4 ? a[4] : null),
        "selftest" => SelfTest(),
        "shore" => Shore(a[1], a[2..]),
        _ => throw new ArgumentException("waterstudy records|tamriel|cells|shore"),
    };

    /// heights of a LAND's 33 x 33 vertices in world units (VHGT: offset, then row starts carried north, then deltas along x)
    public static float[,] Heights(ILandscapeGetter land)
    {
        var vh = land.VertexHeightMap!;
        var z = new float[33, 33];
        float row = vh.Offset;
        for (var y = 0; y < 33; y++)
        {
            row += vh.HeightMap[0, y];
            float h = row;
            z[0, y] = h * 8;
            for (var x = 1; x < 33; x++) { h += vh.HeightMap[x, y]; z[x, y] = h * 8; }
        }
        return z;
    }

    /// shore <Data> [world] [box x0,y0,x1,y1 name ...]: how land vertices sit against each cell's own water plane in
    /// cells the shore crosses, per group (water type, and named boxes): the share of near-shore vertices (|z - water| <= 64)
    /// in each band of height, and the rise across each grid edge that crosses the plane.
    static int Shore(string plugins, string[] a)
    {   // plugins: comma-separated paths, masters first
        var world = a.Length > 0 ? a[0] : "Tamriel";
        var boxes = new List<(int x0, int y0, int x1, int y1, string name)>();
        for (var i = 1; i + 1 < a.Length; i += 2)
        {
            var b = a[i].Split(',').Select(int.Parse).ToArray();
            boxes.Add((b[0], b[1], b[2], b[3], a[i + 1]));
        }
        var lo = plugins.Split(',').Select(f => SkyrimMod.CreateFromBinaryOverlay(f, Rel)).ToList();
        var water = new Dictionary<FormKey, IWaterGetter>();
        foreach (var m in lo) foreach (var w in m.Waters) water[w.FormKey] = w;
        // the last plugin's cell header wins; the land is Skyrim.esm's (Update.esm overrides few)
        var head = new Dictionary<(int, int), ICellGetter>();
        var landOf = new Dictionary<(int, int), ILandscapeGetter>();
        float defH = 0; FormKey def = FormKey.Null;
        foreach (var m in lo)
            foreach (var ws in m.Worldspaces.Where(w => w.EditorID == world))
            {
                if (!ws.Water.IsNull) def = ws.Water.FormKey;
                defH = ws.LandDefaults?.DefaultWaterHeight ?? defH;
                foreach (var b in ws.SubCells) foreach (var sb in b.Items) foreach (var c in sb.Items)
                    if (c.Grid is { } g)
                    {
                        head[(g.Point.X, g.Point.Y)] = c;
                        if (c.Landscape?.VertexHeightMap != null) landOf[(g.Point.X, g.Point.Y)] = c.Landscape;
                    }
            }
        var whs = head.Values.GroupBy(c => c.WaterHeight is { } v ? (v > 1e9 || float.IsNaN(v) ? "huge/nan" : v < -10000 ? "below -10000" : Math.Round(v / 1000.0) * 1000 + "") : "none").OrderByDescending(g => g.Count());
        Console.WriteLine("water heights (XCLW, to 1000): " + string.Join(", ", whs.Take(12).Select(g => $"{g.Key} {g.Count()}")) + $"; cells with land {landOf.Count}");
        var bands = new[] { 0f, 4, 8, 16, 32, 64 };
        var hist = new Dictionary<string, long[]>();
        var rises = new Dictionary<string, List<float>>();
        var ncell = new Dictionary<string, int>();
        var straightN = new Dictionary<string, int>(); var gridN = new Dictionary<string, int>(); var straightAt = new List<string>();
        foreach (var (xy, c) in head)
        {
            if (!landOf.TryGetValue(xy, out var land) || !c.Flags.HasFlag(Cell.Flag.HasWater)) continue;
            var wh = c.WaterHeight is { } cw && cw < 1e9 && !float.IsNaN(cw) ? cw : defH;   // FLT_MAX: the world's default
            var z = Heights(land);
            float mn = float.MaxValue, mx = float.MinValue;
            foreach (var v in z) { mn = Math.Min(mn, v); mx = Math.Max(mx, v); }
            if (!(mn < wh && mx > wh)) continue;          // the shore crosses this cell
            var wk = c.Water.IsNull ? def : c.Water.FormKey;
            var ed = water.TryGetValue(wk, out var ww) ? ww.EditorID ?? "?" : wk.ToString();
            if (ed.StartsWith("ANW_WaterBlend_")) ed = "blend of " + ed[15..ed.LastIndexOf('_')];
            var groups = new List<string> { "all", ed + (wh == defH ? " (world level)" : " (own level)") };
            groups.AddRange(boxes.Where(b => xy.Item1 >= b.x0 && xy.Item1 <= b.x1 && xy.Item2 >= b.y0 && xy.Item2 <= b.y1).Select(b => b.name));
            // the waterline's points in this cell (each crossing edge, interpolated): a straight shore is one whose
            // points lie within 8 units of one line over at least half a cell; grid-aligned when that line runs
            // within 3 degrees of a multiple of 45 (the vertex grid and its triangle diagonals)
            var pts = new List<(double x, double y)>();
            for (var y = 0; y < 33; y++)
                for (var x = 0; x < 33; x++)
                {
                    if (x < 32 && (z[x, y] <= wh) != (z[x + 1, y] <= wh)) pts.Add((x + (wh - z[x, y]) / (z[x + 1, y] - z[x, y]), y));
                    if (y < 32 && (z[x, y] <= wh) != (z[x, y + 1] <= wh)) pts.Add((x, y + (wh - z[x, y]) / (z[x, y + 1] - z[x, y])));
                }
            var (straight, grid) = (false, false);
            if (pts.Count >= 12)
            {
                double mx0 = pts.Average(p => p.x), my0 = pts.Average(p => p.y);
                double sxx = pts.Sum(p => (p.x - mx0) * (p.x - mx0)), syy = pts.Sum(p => (p.y - my0) * (p.y - my0)), sxy = pts.Sum(p => (p.x - mx0) * (p.y - my0));
                var ang = 0.5 * Math.Atan2(2 * sxy, sxx - syy);
                double ux = Math.Cos(ang), uy = Math.Sin(ang);
                var along = pts.Select(p => (p.x - mx0) * ux + (p.y - my0) * uy).ToList();
                var rms = Math.Sqrt(pts.Average(p => Math.Pow(-(p.x - mx0) * uy + (p.y - my0) * ux, 2))) * 128;
                straight = rms < 8 && (along.Max() - along.Min()) * 128 >= 2048;
                var deg = (ang * 180 / Math.PI % 45 + 45) % 45;
                grid = straight && Math.Min(deg, 45 - deg) < 3;
                if (straight) straightAt.Add($"{xy.Item1},{xy.Item2}@{ang * 180 / Math.PI:F0}");
            }
            foreach (var g in groups)
            {
                ncell[g] = ncell.GetValueOrDefault(g) + 1;
                if (straight) straightN[g] = straightN.GetValueOrDefault(g) + 1;
                if (grid) gridN[g] = gridN.GetValueOrDefault(g) + 1;
                var h = hist.TryGetValue(g, out var hh) ? hh : hist[g] = new long[2 * bands.Length + 1];
                var r = rises.TryGetValue(g, out var rr) ? rr : rises[g] = new List<float>();
                for (var y = 0; y < 33; y++)
                    for (var x = 0; x < 33; x++)
                    {
                        var d = z[x, y] - wh;
                        if (Math.Abs(d) <= 64)
                        {   // bins: [-64,-32) ... [-4,0) | exactly 0 | (0,4] ... (32,64]
                            int bi;
                            if (d == 0) bi = bands.Length;
                            else
                            {
                                var ad = Math.Abs(d); var k = 1;
                                while (k < bands.Length && ad > bands[k]) k++;
                                bi = d > 0 ? bands.Length + k : bands.Length - k;
                            }
                            h[bi]++;
                        }
                        if (x < 32 && (z[x, y] <= wh) != (z[x + 1, y] <= wh)) r.Add(Math.Abs(z[x + 1, y] - z[x, y]));
                        if (y < 32 && (z[x, y] <= wh) != (z[x, y + 1] <= wh)) r.Add(Math.Abs(z[x, y + 1] - z[x, y]));
                    }
            }
        }
        Console.WriteLine($"straight shores at (cell@angle): {string.Join(" ", straightAt.Take(60))}");
        foreach (var g in hist.Keys.OrderByDescending(k => ncell[k]).Take(14))
        {
            var h = hist[g]; double tot = h.Sum();
            var r = rises[g]; r.Sort();
            float P(double q) => r.Count == 0 ? 0 : r[Math.Min(r.Count - 1, (int)(q * r.Count))];
            Console.WriteLine($"{g}: {ncell[g]} shore cells, {tot} vertices within 64 units of the plane");
            Console.WriteLine("   below: " + string.Join("  ", Enumerable.Range(1, bands.Length - 1).Reverse().Select(k => $"[{-bands[k]},{-bands[k - 1]}) {h[bands.Length - k] / tot:P1}")));
            Console.WriteLine($"   exactly on the plane: {h[bands.Length] / tot:P2}; within 4 units (|dz|<=4): {(h[bands.Length] + h[bands.Length - 1] + h[bands.Length + 1]) / tot:P2}; within 8: {(h[bands.Length] + h[bands.Length - 1] + h[bands.Length + 1] + h[bands.Length - 2] + h[bands.Length + 2]) / tot:P2}");
            Console.WriteLine("   above: " + string.Join("  ", Enumerable.Range(1, bands.Length - 1).Select(k => $"({bands[k - 1]},{bands[k]}] {h[bands.Length + k] / tot:P1}")));
            Console.WriteLine($"   rise across an edge crossing the plane (units per 128): p10 {P(.1)}, p25 {P(.25)}, median {P(.5)}, p75 {P(.75)}, p90 {P(.9)}; edges {r.Count}");
            Console.WriteLine($"   straight shores (8 units of one line over half a cell or more): {straightN.GetValueOrDefault(g) / (double)ncell[g]:P1} of shore cells; grid-aligned {gridN.GetValueOrDefault(g) / (double)ncell[g]:P1}");
        }
        return 0;
    }

    public static IEnumerable<(string name, string val)> Fields(object o, string pre = "")
    {
        foreach (var p in o.GetType().GetProperties(BindingFlags.Public | BindingFlags.Instance).OrderBy(p => p.Name))
        {
            if (p.GetIndexParameters().Length > 0 || p.Name is "Registration" or "StaticRegistration" or "FormKey" or "FormVersion"
                or "VersionControl" or "Version2" or "MajorFlags" or "SkyrimMajorRecordFlags" or "IsCompressed" or "IsDeleted" or "EditorID" or "Name") continue;
            object? v;
            try { v = p.GetValue(o); } catch { continue; }
            var t = p.PropertyType;
            if (v is null) { yield return (pre + p.Name, "null"); continue; }
            if (v is Color c) yield return (pre + p.Name, $"{c.R},{c.G},{c.B},{c.A}");
            else if (v is string || t.IsPrimitive || t.IsEnum || v is P3Float || v is P2Float) yield return (pre + p.Name, v.ToString()!);
            else if (v is IFormLinkGetter fl) yield return (pre + p.Name, fl.FormKeyNullable?.ToString() ?? "null");
            else if (v is System.Collections.Generic.IReadOnlyList<byte> ms) yield return (pre + p.Name, $"bytes[{ms.Count}]");
            else if (v is System.Collections.IEnumerable e && v is not string)
            {
                var i = 0;
                foreach (var x in e) { if (x is IFormLinkGetter l) yield return ($"{pre}{p.Name}[{i}]", l.FormKey.ToString()); else yield return ($"{pre}{p.Name}[{i}]", x?.ToString() ?? "null"); i++; }
            }
            else if (t.Namespace?.StartsWith("Mutagen") == true && pre.Count(ch => ch == '.') < 2)
                foreach (var f in Fields(v, pre + p.Name + ".")) yield return f;
        }
    }

    static int Records(string names, string[] plugins)
    {
        var want = names == "*" ? null : names.Split(',').ToHashSet(StringComparer.OrdinalIgnoreCase);
        foreach (var path in plugins)
        {
            using var m = SkyrimMod.CreateFromBinaryOverlay(path, Rel);
            foreach (var w in m.Waters)
            {
                if (want != null && !want.Contains(w.EditorID ?? "") && !want.Contains(w.FormKey.ToString())) continue;
                Console.WriteLine($"== {w.EditorID} {w.FormKey} in {Path.GetFileName(path)}");
                foreach (var (n, v) in Fields(w)) Console.WriteLine($"   {n} = {v}");
            }
        }
        return 0;
    }

    static int Tamriel(string data)
    {
        var lo = new[] { "Skyrim.esm", "Update.esm" }.Select(f => SkyrimMod.CreateFromBinaryOverlay(Path.Combine(data, f), Rel)).ToList();
        var water = new Dictionary<FormKey, IWaterGetter>();
        var acti = new Dictionary<FormKey, IActivatorGetter>();
        foreach (var m in lo) { foreach (var w in m.Waters) water[w.FormKey] = w; foreach (var x in m.Activators) acti[x.FormKey] = x; }
        string E(FormKey k) => k.IsNull ? "(none)" : water.TryGetValue(k, out var w) ? w.EditorID ?? k.ToString() : k.ToString();
        foreach (var name in new[] { "Tamriel" })
        {
            var cells = new Dictionary<(int, int), ICellGetter>();
            FormKey def = FormKey.Null;
            var actiPlaced = new Dictionary<string, int>();
            var actiByWater = new Dictionary<string, int>();
            foreach (var m in lo)
                foreach (var ws in m.Worldspaces.Where(w => w.EditorID == name))
                {
                    if (!ws.Water.IsNull) def = ws.Water.FormKey;
                    Console.WriteLine($"{m.ModKey}: world water {E(ws.Water.FormKey)}, LOD water {E(ws.LodWater.FormKey)} at {ws.LodWaterHeight}, default water height {ws.LandDefaults?.DefaultWaterHeight}");
                    foreach (var b in ws.SubCells) foreach (var sb in b.Items) foreach (var c in sb.Items)
                    {
                        if (c.Grid is { } g) cells[(g.Point.X, g.Point.Y)] = c;
                        foreach (var r in c.Temporary.OfType<IPlacedObjectGetter>().Concat(c.Persistent.OfType<IPlacedObjectGetter>()))
                            if (acti.TryGetValue(r.Base.FormKey, out var ac) && !ac.WaterType.IsNull)
                            {
                                var k = $"{ac.EditorID} -> {E(ac.WaterType.FormKey)}";
                                actiPlaced[k] = actiPlaced.GetValueOrDefault(k) + 1;
                                actiByWater[E(ac.WaterType.FormKey)] = actiByWater.GetValueOrDefault(E(ac.WaterType.FormKey)) + 1;
                            }
                    }
                }
            var byType = cells.Values.GroupBy(c => c.Water.IsNull ? "(world) " + E(def) : E(c.Water.FormKey)).OrderByDescending(g => g.Count());
            Console.WriteLine($"{name}: {cells.Count} cells; has-water flag {cells.Values.Count(c => c.Flags.HasFlag(Cell.Flag.HasWater))}; own water height (XCLW) {cells.Values.Count(c => c.WaterHeight != null)}");
            foreach (var g in byType) Console.WriteLine($"  cells {g.Count(),5}  {g.Key}");
            Console.WriteLine("placed water activators (ACTI with a water type), by water type:");
            foreach (var kv in actiByWater.OrderByDescending(k => k.Value)) Console.WriteLine($"  {kv.Value,5}  {kv.Key}");
            foreach (var kv in actiPlaced.OrderByDescending(k => k.Value).Take(40)) Console.WriteLine($"    {kv.Value,5}  {kv.Key}");
        }
        return 0;
    }

    static int Cells(string esm, string cellsJson)
    {
        using var m = SkyrimMod.CreateFromBinaryOverlay(esm, Rel);
        var kinds = JsonDocument.Parse(File.ReadAllText(cellsJson)).RootElement.GetProperty("cells");
        var ours = m.Waters.ToDictionary(w => w.FormKey);
        foreach (var ws in m.Worldspaces)
        {
            Console.WriteLine($"world {ws.EditorID}: water {ws.Water.FormKey}, LOD water {ws.LodWater.FormKey} at {ws.LodWaterHeight}, default water height {ws.LandDefaults?.DefaultWaterHeight}; persistent cell flags {ws.TopCell?.Flags} water {ws.TopCell?.Water.FormKeyNullable}");
            var per = new Dictionary<string, Dictionary<string, int>>();
            int n = 0, flag = 0, xclw = 0;
            foreach (var b in ws.SubCells) foreach (var sb in b.Items) foreach (var c in sb.Items)
            {
                if (c.Grid is not { } g) continue;
                n++; if (c.Flags.HasFlag(Cell.Flag.HasWater)) flag++; if (c.WaterHeight != null) xclw++;
                if (!kinds.TryGetProperty($"{g.Point.X},{g.Point.Y}", out var ci) || !ci.TryGetProperty("water", out var kv)) continue;
                var kind = kv.GetString()!;
                var w = c.Water.IsNull ? "(none)" : ours.TryGetValue(c.Water.FormKey, out var ow) ? (ow.EditorID!.StartsWith("ANW_WaterBlend_") ? "blend" : ow.EditorID!) : c.Water.FormKey.ToString();
                per.TryAdd(kind, new()); per[kind][w] = per[kind].GetValueOrDefault(w) + 1;
            }
            Console.WriteLine($"  cells {n}, has-water flag {flag}, XCLW {xclw}");
            foreach (var (k, d) in per.OrderBy(k => k.Key)) Console.WriteLine($"  {k,-18} " + string.Join(", ", d.OrderByDescending(x => x.Value).Select(x => $"{x.Key} {x.Value}")));
        }
        return 0;
    }

    /// a cell's water key without its flow direction: "river-045" or "river-NE" -> "river"
    public static string KindOf(string key)
    {
        var i = key.LastIndexOf('-');
        if (i < 0) return key;
        var tail = key[(i + 1)..];
        return tail is "NE" or "NW" or "SE" or "SW" || tail.All(char.IsDigit) ? key[..i] : key;
    }

    /// a record's look as one vector: shallow, deep and reflection colours, and opacity (0..255 each)
    public static double[] LookVec(IWaterGetter w) => new double[]
    {
        w.ShallowColor.R, w.ShallowColor.G, w.ShallowColor.B, w.DeepColor.R, w.DeepColor.G, w.DeepColor.B,
        w.ReflectionColor.R, w.ReflectionColor.G, w.ReflectionColor.B, w.Opacity,
    };

    /// the heading the record's current runs toward (compass degrees, 0 north, 90 east), or null when it has none
    public static double? VelHeading(IWaterGetter w)
    {
        if (w.LinearVelocity is not { } v) return null;
        return Math.Abs(v.X) + Math.Abs(v.Y) < 1e-3 ? null : (Math.Atan2(v.X, v.Y) * 180 / Math.PI + 360) % 360;
    }

    static double NoiseHeading(IWaterGetter w) => WaterBlend.NoiseHeading(w);

    public static double AngErr(double a, double b) { var d = Math.Abs(a - b) % 360; return d > 180 ? 360 - d : d; }

    /// check <esm> <Data> <cells.json> <water_flow_cells.json> [out.json]: the water as the game reads it, per kind
    static int Check(string esm, string data, string cellsJson, string flowJson, string? outJson)
    {
        var water = new Dictionary<FormKey, IWaterGetter>();
        var lo = new[] { "Skyrim.esm", "Update.esm" }.Select(f => SkyrimMod.CreateFromBinaryOverlay(Path.Combine(data, f), Rel)).ToList();
        using var m = SkyrimMod.CreateFromBinaryOverlay(esm, Rel);
        foreach (var x in lo.Append(m)) foreach (var w in x.Waters) water[w.FormKey] = w;
        var keys = JsonDocument.Parse(File.ReadAllText(cellsJson)).RootElement.GetProperty("cells");
        var flow = FlowCells(flowJson);
        var ws = m.Worldspaces.First();
        var def = ws.Water.FormKey;
        var cellKey = new Dictionary<(int, int), string>();
        var eff = new Dictionary<(int, int), IWaterGetter>();
        foreach (var b in ws.SubCells) foreach (var sb in b.Items) foreach (var c in sb.Items)
        {
            if (c.Grid is not { } g || !keys.TryGetProperty($"{g.Point.X},{g.Point.Y}", out var ci) || !ci.TryGetProperty("water", out var kv)) continue;
            cellKey[(g.Point.X, g.Point.Y)] = kv.GetString()!;
            eff[(g.Point.X, g.Point.Y)] = water[c.Water.IsNull ? def : c.Water.FormKey];
        }
        var byEdid = m.Waters.Where(w => w.EditorID != null).GroupBy(w => w.EditorID!).ToDictionary(g => g.Key, g => (IWaterGetter)g.First());
        var pureLook = new Dictionary<string, IWaterGetter>();
        foreach (var p in JsonDocument.Parse(File.ReadAllText(cellsJson)).RootElement.GetProperty("watr").EnumerateObject())
            if (p.Value.TryGetProperty("edid", out var ed) && byEdid.TryGetValue(ed.GetString()!, out var pw)) pureLook.TryAdd(KindOf(p.Name), pw);
        var rep = Measure(cellKey, eff, flow, pureLook);
        rep["convention"] = Convention(new[] { "RiverWaterFlowNE", "RiverWaterFlowNW", "CreekWaterFlowSE", "CreekWaterFlowSW" }
            .Select(e => lo[1].Waters.First(w => w.EditorID == e)));
        rep["shore"] = ShoreOf(ws);
        rep["world_water"] = water.TryGetValue(def, out var ww) ? ww.EditorID ?? def.ToString() : def.ToString();
        var js = JsonSerializer.Serialize(rep, new JsonSerializerOptions { WriteIndented = true });
        if (outJson != null) File.WriteAllText(outJson, js);
        Console.WriteLine(js);
        return 0;
    }

    /// plan <plugin dir> <Data> <water_flow_cells.json> [out.json]: the water the writer would make from cells.json
    /// (WaterBlend.Records and Blend, in memory, no ESM) measured as check measures a built ESM
    static int Plan(string plugDir, string data, string flowJson, string? outJson)
    {
        var mod = new SkyrimMod(ModKey.FromFileName("ArgoniaNewWorld.esm"), Rel);
        using var fc = new ForeignCopy(mod, new[] { "Skyrim.esm", "Update.esm", "Black Marsh.esm" }.Select(f => ModKey.FromFileName(f)).ToList(), data, 0x900);
        var cj = JsonDocument.Parse(File.ReadAllText(Path.Combine(plugDir, "cells.json"))).RootElement;
        var (keyOf, recs) = WaterBlend.Records(mod, fc, cj.GetProperty("watr"));
        var cellKey = new Dictionary<(int, int), string>();
        foreach (var e in cj.GetProperty("cells").EnumerateObject())
            if (e.Value.TryGetProperty("water", out var wv))
            {
                var xy = e.Name.Split(',');
                cellKey[(int.Parse(xy[0]), int.Parse(xy[1]))] = wv.GetString()!;
            }
        var (cellWater, blend) = WaterBlend.Blend(mod, _ => fc.NextIdTake(), cellKey, keyOf, recs);
        var byKey = mod.Waters.ToDictionary(w => w.FormKey, w => (IWaterGetter)w);
        var pureLook = new Dictionary<string, IWaterGetter>();
        foreach (var (k, w) in recs) pureLook.TryAdd(KindOf(k), w);
        var rep = Measure(cellKey, cellWater.ToDictionary(kv => kv.Key, kv => byKey[kv.Value]), FlowCells(flowJson), pureLook);
        rep["blend"] = blend;
        rep["records"] = mod.Waters.Count;
        var js = JsonSerializer.Serialize(rep, new JsonSerializerOptions { WriteIndented = true });
        if (outJson != null) File.WriteAllText(outJson, js);
        Console.WriteLine(js);
        return 0;
    }

    public static Dictionary<(int, int), double> FlowCells(string flowJson)
    {
        var flow = new Dictionary<(int, int), double>();
        foreach (var e in JsonDocument.Parse(File.ReadAllText(flowJson)).RootElement.EnumerateArray())
            if (e.TryGetProperty("flow_deg", out var fd) && fd.ValueKind == JsonValueKind.Number)
                flow[(e.GetProperty("cell")[0].GetInt32(), e.GetProperty("cell")[1].GetInt32())] = fd.GetDouble();
        return flow;
    }

    /// a key with a flow heading ("river-045", or the old "river-NE"): running water; any other key is still water
    public static bool Flowing(string key) => KindOf(key) != key;

    static double Dist(double[] a, double[] b) => a.Zip(b).Max(p => Math.Abs(p.First - p.Second));

    /// per kind: cells, the share carrying the kind's own record, the share within 14 of its own look and the share
    /// that looks nearer its own kind than any other (pureLook: kind -> the kind's own record); the kinds' own looks'
    /// nearest pair; flowing cells' current and drift against the channel graph; still cells with a current; the
    /// look's step at every edge between two water cells
    public static Dictionary<string, object> Measure(Dictionary<(int, int), string> cellKey, Dictionary<(int, int), IWaterGetter> eff,
        Dictionary<(int, int), double> flow, Dictionary<string, IWaterGetter> pureLook)
    {
        var own = pureLook.ToDictionary(kv => kv.Key, kv => LookVec(kv.Value));
        var n = new Dictionary<string, int>(); var pure = new Dictionary<string, int>(); var sum = new Dictionary<string, double[]>();
        var near = new Dictionary<string, int>(); var asOwn = new Dictionary<string, int>(); var dOwn = new Dictionary<string, List<double>>();
        int flowing = 0, velOk = 0, noiseOk = 0, stillN = 0, stillMoving = 0;
        var velErr = new List<double>(); var noiseErr = new List<double>(); var bad = new List<string>();
        foreach (var ((gx, gy), key) in cellKey)
        {
            var kind = KindOf(key);
            var w = eff[(gx, gy)];
            n[kind] = n.GetValueOrDefault(kind) + 1;
            if (w.EditorID?.StartsWith("ANW_WaterBlend_") != true) pure[kind] = pure.GetValueOrDefault(kind) + 1;
            var v = LookVec(w);
            if (!sum.ContainsKey(kind)) sum[kind] = new double[v.Length];
            for (var i = 0; i < v.Length; i++) sum[kind][i] += v[i];
            if (own.TryGetValue(kind, out var ov))
            {
                var d = Dist(v, ov);
                (dOwn.TryGetValue(kind, out var dl) ? dl : dOwn[kind] = new()).Add(d);
                if (d <= WaterBlend.STEP + 1) near[kind] = near.GetValueOrDefault(kind) + 1;
                if (own.All(o => o.Key == kind || Dist(v, o.Value) > d)) asOwn[kind] = asOwn.GetValueOrDefault(kind) + 1;
            }
            if (!Flowing(key))
            {
                stillN++;
                if (VelHeading(w) != null) stillMoving++;
            }
            else if (flow.TryGetValue((gx, gy), out var want))
            {
                flowing++;
                var vh = VelHeading(w);
                var ve = vh is { } h ? AngErr(h, want) : 180; velErr.Add(ve); if (ve <= 22.5) velOk++;
                var ne = AngErr(NoiseHeading(w), want); noiseErr.Add(ne); if (ne <= 22.5) noiseOk++;
                if ((ve > 22.5 || ne > 22.5) && bad.Count < 5) bad.Add($"{gx},{gy} {key} wants {want}: velocity {vh:F0}, noise {NoiseHeading(w):F0}");
            }
        }
        var steps = new List<double>();    // the look's step at every edge (side or corner) between two water cells that differ
        foreach (var ((gx, gy), _) in cellKey)
            foreach (var (dx, dy) in new[] { (1, 0), (0, 1), (1, 1), (1, -1) })
                if (eff.TryGetValue((gx + dx, gy + dy), out var nb) && !ReferenceEquals(nb, eff[(gx, gy)]))
                {
                    var s = WaterBlend.Delta(eff[(gx, gy)], nb);
                    if (s > 0) steps.Add(s);
                }
        steps.Sort();
        var mean = sum.ToDictionary(kv => kv.Key, kv => kv.Value.Select(x => x / n[kv.Key]).ToArray());
        var ks = mean.Keys.OrderBy(k => k).ToList();
        var pairs = new List<(string a, string b, double d)>();
        var ok = own.Keys.OrderBy(k => k).ToList();
        for (var i = 0; i < ok.Count; i++)
            for (var j = i + 1; j < ok.Count; j++)
                pairs.Add((ok[i], ok[j], Dist(own[ok[i]], own[ok[j]])));
        pairs.Sort((p, q) => p.d.CompareTo(q.d));
        velErr.Sort(); noiseErr.Sort();
        double P(List<double> l, double q) => l.Count == 0 ? 0 : Math.Round(l[Math.Min(l.Count - 1, (int)(q * l.Count))], 1);
        var rep = new Dictionary<string, object>
        {
            ["kinds"] = ks.ToDictionary(k => k, k => (object)new Dictionary<string, object>
            {
                ["cells"] = n[k], ["pure"] = pure.GetValueOrDefault(k), ["pure_share"] = Math.Round(pure.GetValueOrDefault(k) / (double)n[k], 3),
                ["near_own_share"] = Math.Round(near.GetValueOrDefault(k) / (double)n[k], 3),
                ["reads_as_own_share"] = Math.Round(asOwn.GetValueOrDefault(k) / (double)n[k], 3),
                ["own_distance_median"] = dOwn.TryGetValue(k, out var dl) ? P(dl.OrderBy(x => x).ToList(), .5) : -1,
                ["mean_look"] = mean[k].Select(x => Math.Round(x)).ToArray(),
            }),
            ["own_look_pairs"] = pairs.Select(p => new object[] { p.a, p.b, Math.Round(p.d, 1) }).ToArray(),
            ["own_look_min_pair"] = pairs.Count == 0 ? 0 : Math.Round(pairs[0].d, 1),
            ["flowing_cells"] = flowing, ["velocity_within_22_5"] = velOk, ["noise_within_22_5"] = noiseOk,
            ["velocity_err_p50_p90_max"] = new[] { P(velErr, .5), P(velErr, .9), P(velErr, 1) },
            ["noise_err_p50_p90_max"] = new[] { P(noiseErr, .5), P(noiseErr, .9), P(noiseErr, 1) },
            ["flow_examples_off"] = bad,
            ["still_cells"] = stillN, ["still_cells_with_flow"] = stillMoving,
            ["edge_steps"] = steps.Count, ["edge_step_p50_p99_max"] = new[] { P(steps, .5), P(steps, .99), P(steps, 1) },
        };
        return rep;
    }

    /// Update.esm's directional records: their surface drift (NoiseHeading) against their own current; a wrong reading
    /// of the wind-direction convention puts them far apart
    public static Dictionary<string, object> Convention(IEnumerable<IWaterGetter> waters)
    {
        var res = new Dictionary<string, object>();
        foreach (var w in waters)
            if (VelHeading(w) is { } vh) res[w.EditorID!] = new[] { Math.Round(vh), Math.Round(NoiseHeading(w)), Math.Round(AngErr(vh, NoiseHeading(w))) };
        return res;
    }

    /// land against the water plane, read from the ESM's LAND (Heights): vertices within the fighting band
    /// (|z - water| < 8), on the plane, near it (64), and the rise across each grid edge that crosses it
    public static Dictionary<string, object> ShoreOf(IWorldspaceGetter ws)
    {
        long nearN = 0, fight = 0, on = 0;
        var rises = new List<double>();
        float defH = ws.LandDefaults?.DefaultWaterHeight ?? 0;
        foreach (var b in ws.SubCells) foreach (var sb in b.Items) foreach (var c in sb.Items)
        {
            if (c.Landscape?.VertexHeightMap == null) continue;
            var wh = c.WaterHeight is { } cw && cw < 1e9 && !float.IsNaN(cw) ? cw : defH;
            var z = Heights(c.Landscape);
            for (var y = 0; y < 33; y++)
                for (var x = 0; x < 33; x++)
                {
                    var d = Math.Abs(z[x, y] - wh);
                    if (d <= 64) nearN++;
                    if (d < 8) fight++;
                    if (d == 0) on++;
                    if (x < 32 && (z[x, y] <= wh) != (z[x + 1, y] <= wh)) rises.Add(Math.Abs(z[x + 1, y] - z[x, y]));
                    if (y < 32 && (z[x, y] <= wh) != (z[x, y + 1] <= wh)) rises.Add(Math.Abs(z[x, y + 1] - z[x, y]));
                }
        }
        rises.Sort();
        double P(double q) => rises.Count == 0 ? 0 : rises[Math.Min(rises.Count - 1, (int)(q * rises.Count))];
        return new Dictionary<string, object>
        {
            ["vertices_near"] = nearN, ["within_fight_band"] = fight, ["on_plane"] = on, ["crossing_edges"] = rises.Count,
            ["rise_p10_median_p90"] = new[] { P(.1), P(.5), P(.9) },
        };
    }

    /// selftest: NoiseHeading, Head and Blend on hand-made records and a small grid; exit 1 naming each failure
    static int SelfTest()
    {
        var fails = new List<string>();
        void Ok(bool c, string what) { if (!c) fails.Add(what); }
        var mod = new SkyrimMod(ModKey.FromFileName("WaterSelfTest.esm"), Rel);
        uint id = 0x800;
        Water Rec(string ed, (int, int, int) shallow, byte opacity, float d1, float d2, float d3)
        {
            var w = new Water(new FormKey(mod.ModKey, id++), Rel)
            {
                EditorID = ed, ShallowColor = Color.FromArgb(0, shallow.Item1, shallow.Item2, shallow.Item3),
                DeepColor = Color.FromArgb(0, shallow.Item1 / 3, shallow.Item2 / 3, shallow.Item3 / 3),
                ReflectionColor = Color.FromArgb(0, 100, 110, 120), Opacity = opacity,
                NoiseLayerOneWindDirection = d1, NoiseLayerTwoWindDirection = d2, NoiseLayerThreeWindDirection = d3,
                NoiseLayerOneAmplitudeScale = 0.9f, NoiseLayerTwoAmplitudeScale = 0.6f, NoiseLayerThreeAmplitudeScale = 0.9f,
                NoiseLayerOneWindSpeed = 0.09f, NoiseLayerTwoWindSpeed = 0.04f, NoiseLayerThreeWindSpeed = 0.3f,
                FogAboveWaterDistanceFarPlane = opacity * 2f,
            };
            mod.Waters.Add(w);
            return w;
        }
        // NoiseHeading: ripples from the west (270) drift east (90); vanilla RiverWaterFlowNE's layers drift east-north-east
        var west = Rec("W", (0, 0, 0), 0, 270, 270, 270);
        Ok(AngErr(NoiseHeading(west), 90) < 0.01, $"NoiseHeading of layers from 270: {NoiseHeading(west):F1}, wants 90");
        var ne = Rec("NE", (0, 0, 0), 0, 233, 267, 252);
        Ok(AngErr(NoiseHeading(ne), 62) < 22.5, $"NoiseHeading of RiverWaterFlowNE's layers: {NoiseHeading(ne):F1}, its current runs 62");
        // Head: turned to 200, the drift and the current both run 200, the layers keep their spread
        var spread = (ne.NoiseLayerTwoWindDirection - ne.NoiseLayerOneWindDirection + 360) % 360;
        WaterBlend.Head(ne, 200, 2.0);
        Ok(AngErr(NoiseHeading(ne), 200) < 0.01, $"Head 200: drift {NoiseHeading(ne):F2}");
        Ok(VelHeading(ne) is { } vh && AngErr(vh, 200) < 0.01, $"Head 200: current {VelHeading(ne)}");
        Ok(Math.Abs((ne.NoiseLayerTwoWindDirection - ne.NoiseLayerOneWindDirection + 360) % 360 - spread) < 0.01, "Head changed the layers' spread");
        // Blend: sea (bright) west of x = 20, swamp (dark) east, a river running north at x = 30; the far ends keep their records
        var sea = Rec("Sea", (80, 175, 165), 30, 270, 210, 225);
        var swamp = Rec("Swamp", (44, 30, 16), 95, 22, 150, 0);
        var river = Rec("River", (112, 104, 44), 70, 233, 267, 252);
        WaterBlend.Head(river, 0, 2.9);
        var recs = new Dictionary<string, IWaterGetter> { ["sea"] = sea, ["blackwater-swamp"] = swamp, ["river-000"] = river };
        var keyOf = recs.ToDictionary(kv => kv.Key, kv => kv.Value.FormKey);
        var cells = new Dictionary<(int, int), string>();
        for (var x = 0; x < 60; x++) for (var y = 0; y < 12; y++) cells[(x, y)] = x == 30 ? "river-000" : x < 20 ? "sea" : "blackwater-swamp";
        var (cw, rep) = WaterBlend.Blend(mod, _ => id++, cells, keyOf, recs);
        var byKey = mod.Waters.ToDictionary(w => w.FormKey, w => (IWaterGetter)w);
        var eff = cw.ToDictionary(kv => kv.Key, kv => byKey[kv.Value]);
        double worst = 0;
        foreach (var ((x, y), _) in cells)
            foreach (var (dx, dy) in new[] { (1, 0), (0, 1), (1, 1), (1, -1) })
                if (eff.TryGetValue((x + dx, y + dy), out var nb)) worst = Math.Max(worst, WaterBlend.Delta(eff[(x, y)], nb));
        Ok(worst <= WaterBlend.STEP + 1, $"Blend: an edge steps {worst} > {WaterBlend.STEP + 1}");
        Ok(cw[(0, 5)] == sea.FormKey && cw[(59, 5)] == swamp.FormKey, "Blend: cells far from a seam lost their own record");
        Ok(cw[(19, 5)] != sea.FormKey && cw[(20, 5)] != swamp.FormKey, "Blend: the seam's cells were not graded");
        var rb = eff[(30, 5)];
        Ok(rb.NoiseLayerOneWindDirection == river.NoiseLayerOneWindDirection && rb.NoiseLayerThreeWindSpeed == river.NoiseLayerThreeWindSpeed
           && rb.NoiseLayerOneAmplitudeScale == river.NoiseLayerOneAmplitudeScale && rb.LinearVelocity == river.LinearVelocity,
           "Blend: a river cell's motion was mixed");
        var sb = eff[(29, 5)];
        Ok(sb.LinearVelocity == swamp.LinearVelocity && sb.NoiseLayerThreeWindSpeed == swamp.NoiseLayerThreeWindSpeed, "Blend: a swamp cell took the river's motion");
        foreach (var f in fails) Console.WriteLine("FAIL " + f);
        Console.WriteLine(fails.Count == 0 ? "waterstudy selftest: ok" : $"waterstudy selftest: {fails.Count} failed");
        return fails.Count == 0 ? 0 : 1;
    }
}
