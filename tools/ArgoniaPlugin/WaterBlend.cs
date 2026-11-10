// Water types and their seams: our WATR per kind and heading, and graded records across a change of kind only.
//   waterblend flows <esm>          every blend of a flowing type keeps its flow (exit 1 if not)
//   waterblend study <Data dir>     Tamriel's adjacent-cell water types (XCWT) in Skyrim.esm + Update.esm: which
//                                   records neighbour each other and how far their colours and fog step at a seam.
// Records (called by NewWorld.cs) builds each type cells.json names (tools/newworld/world/water_types.py): a copy of
// a vanilla record with the values set, running types with their noise rotated to drift toward the cell's heading
// and the current set to it. Blend grades seams: each cell shows the look field (every water cell's kind, land cells
// taking their nearest water's) under a (2 R + 1)^2 tent round it, so a seam is graded over 2 R + 1 cells and no cell
// edge steps more than 1 / (R + 1) of the two kinds' difference (a tent is Lipschitz: no junction of several kinds
// adds up to a step); a cell whose tent holds only its own kind keeps its kind's own record. The old 29-cell tent
// averaged most of the province into one look (walk 5: "all looked the same"); R = 5 grades over 11 cells (640 m).
// A blend is our own WATR, ANW_WaterBlend_<own type>_NNNN: a copy of the cell's own type with its colours, opacity,
// fog, reflection and specular values mixed by the weights (quantised to 32nds, so equal mixes share a record); its
// motion stays its own (textures, wind directions and speeds, the current), so a river's blend still runs its way
// at its speed and a still type's stays still.
using System.Drawing;
using System.Reflection;
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Noggog;

static class WaterBlend
{
    public const int R = 5;                   // tent half-width, cells: a seam graded over 11 cells
    const int Q = 32;                         // weights in 32nds
    static readonly Dictionary<string, double> scale = new();   // each fog value's largest size among the types

    // the interpolated members: every colour, the opacity and every scalar value (fog, specular, reflection,
    // displacement, noise scales), not the motion: wind directions and speeds and the current stay the cell's own
    static readonly PropertyInfo[] Cols = typeof(IWaterGetter).GetProperties().Where(p => p.PropertyType == typeof(Color)).ToArray();
    static readonly PropertyInfo[] Nums = typeof(IWaterGetter).GetProperties()
        .Where(p => (p.PropertyType == typeof(float) || p.PropertyType == typeof(byte)) && !p.Name.Contains("WindDirection") && !p.Name.Contains("WindSpeed")).ToArray();

    /// cells.json "watr": key -> {"copy": "Plugin:EditorID", "edid", "set": {member: value}, "heading"?, "speed"?}
    public static (Dictionary<string, FormKey> key, Dictionary<string, IWaterGetter> rec) Records(ISkyrimMod mod, ForeignCopy fc, JsonElement watr)
    {
        var keys = new Dictionary<string, FormKey>();
        var recs = new Dictionary<string, IWaterGetter>();
        foreach (var p in watr.EnumerateObject())
        {
            var v = p.Value;
            var src = v.GetProperty("copy").GetString()!.Split(':');
            var w = (Water)fc.Find(src[0], src[1]).Duplicate(new FormKey(mod.ModKey, fc.NextIdTake()));
            w.EditorID = v.GetProperty("edid").GetString();
            if (v.TryGetProperty("set", out var set))
                foreach (var f in set.EnumerateObject()) Set(w, f.Name, f.Value);
            if (v.TryGetProperty("heading", out var h) && h.ValueKind == JsonValueKind.Number)
                Head(w, h.GetDouble(), v.GetProperty("speed").GetDouble());
            mod.Waters.Add(w);
            keys[p.Name] = w.FormKey;
            recs[p.Name] = w;
        }
        return (keys, recs);
    }

    /// one member of a WATR from JSON: a colour [r, g, b], a vector [x, y, z], or a number
    public static void Set(Water w, string name, JsonElement val)
    {
        var p = typeof(Water).GetProperty(name) ?? throw new InvalidDataException($"WATR has no member {name}");
        var t = Nullable.GetUnderlyingType(p.PropertyType) ?? p.PropertyType;
        object o = t == typeof(Color) ? Color.FromArgb(0, val[0].GetInt32(), val[1].GetInt32(), val[2].GetInt32())
            : t == typeof(P3Float) ? new P3Float(val[0].GetSingle(), val[1].GetSingle(), val[2].GetSingle())
            : t == typeof(byte) ? (object)(byte)val.GetInt32()
            : t == typeof(float) ? (object)val.GetSingle()
            : throw new InvalidDataException($"WATR member {name} is {t.Name}");
        p.SetValue(w, o);
    }

    /// running water toward a compass heading: all three noise layers turned together so their drift
    /// (NoiseHeading) points along it, and the current set to it at the given speed
    public static void Head(Water w, double heading, double speed)
    {
        var turn = heading - NoiseHeading(w);
        float R(float d) => (float)(((d + turn) % 360 + 360) % 360);
        w.NoiseLayerOneWindDirection = R(w.NoiseLayerOneWindDirection);
        w.NoiseLayerTwoWindDirection = R(w.NoiseLayerTwoWindDirection);
        w.NoiseLayerThreeWindDirection = R(w.NoiseLayerThreeWindDirection);
        var r = heading * Math.PI / 180;
        w.LinearVelocity = new P3Float((float)(speed * Math.Sin(r)), (float)(speed * Math.Cos(r)), 0);
    }

    /// the heading the surface noise drifts toward (compass degrees, 0 north, 90 east): a layer's wind direction is
    /// where its ripples come from (Skyrim.esm's RiverWaterFlowNE 233/267/252 with current heading 62, NW 141/106/177
    /// with 316), so it drifts toward that + 180; the layers weighted by amplitude x speed
    public static double NoiseHeading(IWaterGetter w)
    {
        double sx = 0, sy = 0;
        foreach (var (d, a, sp) in new[] { (w.NoiseLayerOneWindDirection, w.NoiseLayerOneAmplitudeScale, w.NoiseLayerOneWindSpeed),
                                           (w.NoiseLayerTwoWindDirection, w.NoiseLayerTwoAmplitudeScale, w.NoiseLayerTwoWindSpeed),
                                           (w.NoiseLayerThreeWindDirection, w.NoiseLayerThreeAmplitudeScale, w.NoiseLayerThreeWindSpeed) })
        {
            var r = (d + 180) * Math.PI / 180;
            sx += a * sp * Math.Sin(r); sy += a * sp * Math.Cos(r);
        }
        return (Math.Atan2(sx, sy) * 180 / Math.PI + 360) % 360;
    }

    public static double Delta(IWaterGetter a, IWaterGetter b)
    {   // the largest step of any colour channel (0..255) or of the opacity (0..100)
        double d = Math.Abs(a.Opacity - b.Opacity);
        foreach (var p in Cols)
        {
            var (ca, cb) = ((Color)p.GetValue(a)!, (Color)p.GetValue(b)!);
            d = Math.Max(d, Math.Max(Math.Abs(ca.R - cb.R), Math.Max(Math.Abs(ca.G - cb.G), Math.Abs(ca.B - cb.B))));
        }
        return d;
    }

    public static double FogDelta(IWaterGetter a, IWaterGetter b)
    {   // the largest step of any fog value, as a fraction of that value's largest size among the types in use
        double d = 0;
        foreach (var p in Nums.Where(p => p.Name.Contains("Fog")))
        {
            var (x, y) = (Convert.ToDouble(p.GetValue(a)), Convert.ToDouble(p.GetValue(b)));
            var m = scale.TryGetValue(p.Name, out var sc) ? sc : Math.Max(Math.Abs(x), Math.Abs(y));
            if (m > 1e-6) d = Math.Max(d, Math.Abs(x - y) / m);
        }
        return d;
    }

    static void Mix(Water w, IReadOnlyList<(IWaterGetter w, double wt)> parts)
    {
        foreach (var p in Cols)
        {
            double r = 0, g = 0, b = 0, a = 0;
            foreach (var (x, wt) in parts) { var c = (Color)p.GetValue(x)!; r += wt * c.R; g += wt * c.G; b += wt * c.B; a += wt * c.A; }
            typeof(Water).GetProperty(p.Name)!.SetValue(w, Color.FromArgb((int)Math.Round(a), (int)Math.Round(r), (int)Math.Round(g), (int)Math.Round(b)));
        }
        foreach (var p in Nums)
        {
            double s = 0;
            foreach (var (x, wt) in parts) s += wt * Convert.ToDouble(p.GetValue(x));
            var q = typeof(Water).GetProperty(p.Name)!;
            q.SetValue(w, p.PropertyType == typeof(byte) ? (object)(byte)Math.Round(s) : (float)s);
        }
    }

    // a look: the record's colours and scalar values (types that differ only in flow share one look)
    static string Look(IWaterGetter w) => string.Join(",", Cols.Select(p => ((Color)p.GetValue(w)!).ToArgb().ToString())
        .Concat(Nums.Select(p => Convert.ToDouble(p.GetValue(w)).ToString("R"))));


    /// cells: (cx, cy) -> water type key; recs: key -> the record shown; returns (cx, cy) -> the FormKey to write, and a report.
    public static (Dictionary<(int, int), FormKey> cellWater, Dictionary<string, object> report) Blend(
        ISkyrimMod mod, Func<uint> nextId, Dictionary<(int, int), string> cells, Dictionary<string, FormKey> keyOf,
        Dictionary<string, IWaterGetter> recs)
    {
        // one representative key per look
        var lookOf = new Dictionary<string, string>();
        var rep = new Dictionary<string, string>();
        foreach (var k in recs.Keys.OrderBy(k => k, StringComparer.Ordinal)) { var l = Look(recs[k]); lookOf[k] = l; rep.TryAdd(l, k); }
        foreach (var p in Nums.Where(p => p.Name.Contains("Fog")))
            scale[p.Name] = recs.Values.Max(w => Math.Abs(Convert.ToDouble(p.GetValue(w))));
        // every cell of the water cells' box takes the look of its nearest water cell (land between two waters too),
        // so a seam is graded across a spit of land as well as along open water
        var field = new Dictionary<(int, int), string>();
        var front = new Queue<(int, int)>();
        foreach (var (c, k) in cells) { field[c] = lookOf[k]; front.Enqueue(c); }
        int x0 = cells.Keys.Min(c => c.Item1) - R, x1 = cells.Keys.Max(c => c.Item1) + R,
            y0 = cells.Keys.Min(c => c.Item2) - R, y1 = cells.Keys.Max(c => c.Item2) + R;
        while (front.Count > 0)
        {
            var (x, y) = front.Dequeue();
            foreach (var (dx, dy) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
            {
                var n = (x + dx, y + dy);
                if (n.Item1 < x0 || n.Item1 > x1 || n.Item2 < y0 || n.Item2 > y1 || field.ContainsKey(n)) continue;
                field[n] = field[(x, y)]; front.Enqueue(n);
            }
        }
        var outMap = new Dictionary<(int, int), FormKey>();
        var made = new Dictionary<string, (FormKey fk, IWaterGetter w)>();
        var eff = new Dictionary<(int, int), IWaterGetter>();
        int pure = 0;
        foreach (var ((cx, cy), own) in cells)
        {
            // the look field under a (2R + 1)^2 tent round the cell: a cell whose tent holds only its own look keeps its record
            var wsum = new Dictionary<string, double>();
            double tot = 0;
            for (var dy = -R; dy <= R; dy++)
                for (var dx = -R; dx <= R; dx++)
                {
                    if (!field.TryGetValue((cx + dx, cy + dy), out var l)) continue;
                    var wt = (R + 1.0 - Math.Abs(dx)) * (R + 1.0 - Math.Abs(dy));
                    wsum[l] = wsum.GetValueOrDefault(l) + wt; tot += wt;
                }
            var ownLook = lookOf[own];
            var q = wsum.Where(kv => kv.Key != ownLook).Select(kv => (look: kv.Key, n: (int)Math.Round(Q * kv.Value / tot)))
                        .Where(x => x.n > 0).OrderBy(x => rep[x.look], StringComparer.Ordinal).ToList();
            while (q.Sum(x => x.n) > Q) { var i = q.FindIndex(x => x.n == q.Max(y => y.n)); q[i] = (q[i].look, q[i].n - 1); }
            var ownN = Q - q.Sum(x => x.n);     // may be 0: the cell keeps only its own motion and textures
            if (q.Count == 0) { outMap[(cx, cy)] = keyOf[own]; eff[(cx, cy)] = recs[own]; pure++; continue; }
            var name = own + "|" + string.Join("+", q.Select(x => $"{rep[x.look]}:{x.n}"));
            if (!made.TryGetValue(name, out var m))
            {
                var fk = new FormKey(mod.ModKey, nextId());
                var w = (Water)recs[own].Duplicate(fk);
                // the name keeps the cell's own type (its kind and flow): ANW_WaterBlend_<own type's editor id>_NNNN
                w.EditorID = $"ANW_WaterBlend_{recs[own].EditorID}_{made.Count:D4}";
                Mix(w, q.Select(x => (recs[rep[x.look]], x.n / (double)Q)).Append((recs[own], ownN / (double)Q)).ToList());
                mod.Waters.Add(w);
                made[name] = m = (fk, w);
            }
            outMap[(cx, cy)] = m.fk;
            eff[(cx, cy)] = m.w;
        }
        double before = 0, fogBefore = 0, fogAfter = 0;
        var steps = new List<double>();       // the colour step at every edge (side or corner) between two water cells
        var stepsBefore = new List<double>();
        (int, int) at = default; double after = -1;
        var worst = new List<string>();
        foreach (var ((cx, cy), own) in cells)
            foreach (var (dx, dy) in new[] { (1, 0), (0, 1), (1, 1), (1, -1) })
                if (cells.TryGetValue((cx + dx, cy + dy), out var nb))
                {
                    var b0 = Delta(recs[own], recs[nb]);
                    before = Math.Max(before, b0); stepsBefore.Add(b0);
                    fogBefore = Math.Max(fogBefore, FogDelta(recs[own], recs[nb]));
                    var a = Delta(eff[(cx, cy)], eff[(cx + dx, cy + dy)]);
                    steps.Add(a);
                    if (a > 30 && worst.Count < 12) worst.Add($"{cx},{cy} {own} ({(outMap[(cx, cy)] == keyOf[own] ? "pure" : eff[(cx, cy)].EditorID)}) | {cx + dx},{cy + dy} {nb} ({(outMap[(cx + dx, cy + dy)] == keyOf[nb] ? "pure" : eff[(cx + dx, cy + dy)].EditorID)}): {a:F0}");
                    if (a > after) { after = a; at = (cx, cy); }
                    fogAfter = Math.Max(fogAfter, FogDelta(eff[(cx, cy)], eff[(cx + dx, cy + dy)]));
                }
        steps.Sort(); stepsBefore.Sort();
        var changed = steps.Where(x => x > 0).ToList();
        var changedBefore = stepsBefore.Where(x => x > 0).ToList();
        double Pct(List<double> l, double q) => l.Count == 0 ? 0 : l[Math.Min(l.Count - 1, (int)(q * l.Count))];
        var report = new Dictionary<string, object>
        {
            ["looks"] = rep.Count, ["blend_records"] = made.Count, ["water_cells"] = cells.Count, ["pure_cells"] = pure, ["band_cells"] = 2 * R + 1,
            ["max_colour_step_before"] = before, ["max_colour_step_after"] = after, ["max_at_cell"] = new[] { at.Item1, at.Item2 },
            ["edges"] = steps.Count, ["edges_changing_before"] = changedBefore.Count, ["edges_changing_after"] = changed.Count,
            ["step_p50_p99_before"] = new[] { Pct(changedBefore, .5), Pct(changedBefore, .99) },
            ["step_p50_p99_after"] = new[] { Pct(changed, .5), Pct(changed, .99) },
            ["edges_over_12_after"] = changed.Count(x => x > 12), ["steps_over_30"] = worst,
            ["max_fog_step_before"] = Math.Round(fogBefore, 3), ["max_fog_step_after"] = Math.Round(fogAfter, 3),
        };
        return (outMap, report);
    }

    /// waterblend flows <esm>: every blend of a flowing type keeps that type's flow (LinearVelocity); exit 1 if not.
    public static int Flows(string esm)
    {
        using var mod = SkyrimMod.CreateFromBinaryOverlay(esm, SkyrimRelease.SkyrimSE);
        int flowing = 0, still = 0, lost = 0;
        foreach (var w in mod.Waters.Where(w => w.EditorID?.StartsWith("ANW_WaterBlend_") == true))
        {
            if (!w.EditorID!.Contains("WaterFlow")) { still++; continue; }
            var v = w.LinearVelocity;
            if (v is { } p && (Math.Abs(p.X) + Math.Abs(p.Y)) > 0.01) flowing++; else lost++;
        }
        Console.WriteLine($"blends of flowing types with their flow {flowing}, without {lost}; blends of still types {still}");
        return lost == 0 && flowing > 0 ? 0 : 1;
    }

    public static int Study(string data)
    {
        var lo = new[] { "Skyrim.esm", "Update.esm" }.Select(f => SkyrimMod.CreateFromBinaryOverlay(Path.Combine(data, f), SkyrimRelease.SkyrimSE)).ToList();
        var water = new Dictionary<FormKey, IWaterGetter>();
        foreach (var m in lo) foreach (var w in m.Waters) water[w.FormKey] = w;
        var grid = new Dictionary<(int, int), FormKey>();
        FormKey def = FormKey.Null;
        foreach (var m in lo)
            foreach (var ws in m.Worldspaces.Where(w => w.EditorID == "Tamriel"))
            {
                if (!ws.Water.IsNull) def = ws.Water.FormKey;
                foreach (var b in ws.SubCells) foreach (var sb in b.Items) foreach (var c in sb.Items)
                    if (c.Grid is { } g)
                    {
                        if (!c.Water.IsNull) grid[(g.Point.X, g.Point.Y)] = c.Water.FormKey;
                        else grid.TryAdd((g.Point.X, g.Point.Y), FormKey.Null);
                    }
            }
        string Ed(FormKey k) => k.IsNull ? "(world) " + (water.TryGetValue(def, out var d) ? d.EditorID : "?") : water.TryGetValue(k, out var w) ? w.EditorID ?? k.ToString() : k.ToString();
        IWaterGetter? W(FormKey k) => water.GetValueOrDefault(k.IsNull ? def : k);
        var pairs = new Dictionary<(string, string), (int n, double col, double fog)>();
        int same = 0, diff = 0;
        foreach (var ((x, y), k) in grid)
            foreach (var (dx, dy) in new[] { (1, 0), (0, 1) })
                if (grid.TryGetValue((x + dx, y + dy), out var k2))
                {
                    var (a, b) = (Ed(k), Ed(k2));
                    if ((k.IsNull ? def : k) == (k2.IsNull ? def : k2)) { same++; continue; }
                    diff++;
                    var key = string.CompareOrdinal(a, b) < 0 ? (a, b) : (b, a);
                    var (wa, wb) = (W(k), W(k2));
                    var col = wa is null || wb is null ? -1 : Delta(wa, wb);
                    var fog = wa is null || wb is null ? -1 : FogDelta(wa, wb);
                    var cur = pairs.GetValueOrDefault(key);
                    pairs[key] = (cur.n + 1, Math.Max(cur.col, col), Math.Max(cur.fog, fog));
                }
        Console.WriteLine($"Tamriel: {grid.Count} cells; adjacent pairs same type {same}, different {diff}");
        foreach (var ((a, b), (n, col, fog)) in pairs.OrderByDescending(p => p.Value.n).Take(40))
            Console.WriteLine($"  {n,5}  colour step {col,4:F0}  fog step {fog,5:P0}  {a} | {b}");
        var steps = pairs.Values.Select(v => v.col).Where(v => v >= 0).OrderBy(v => v).ToList();
        Console.WriteLine($"colour step at seams: median {steps[steps.Count / 2]:F0}, max {steps[^1]:F0}");
        Console.WriteLine("interpolated: " + string.Join(", ", Cols.Concat(Nums).Select(p => p.Name)));
        return 0;
    }
}
