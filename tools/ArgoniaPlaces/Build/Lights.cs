using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Cache;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Noggog;

// lightpairs <out.json> <plugin...>: the evidence for which bases carry a light, measured on the plugins' own placements
// (tools/places/light_pairs.py turns it into the pairing table). In every interior cell and every worldspace (its
// exterior cells pooled), each placed light (a ref whose base is a LIGH) belongs to the nearest other placed ref within
// 128 units whose base is not a light and not an editor marker, as the lights stage binds a light to its fixture. Per
// base: how often it is placed, how often with a light, and each light's base and its offset in the base's own frame.
static class LightPairs
{
    const float Bind = 128f;
    sealed class P { public FormKey Base; public float X, Y, Z, Rx, Ry, Rz, S; public bool Light; }

    public static int Run(string outPath, string[] plugins)
    {
        var mods = plugins.Select(C.Open).ToList();
        var cache = mods.ToImmutableLinkCache();
        var isLight = new Dictionary<FormKey, bool>();
        bool Light(FormKey k) { if (!isLight.TryGetValue(k, out var v)) isLight[k] = v = cache.TryResolve<ILightGetter>(k, out _); return v; }
        var marker = new Dictionary<FormKey, bool>();
        bool Marker(FormKey k)
        {
            if (marker.TryGetValue(k, out var v)) return v;
            v = !cache.TryResolve<IMajorRecordGetter>(k, out var r) || (r.EditorID ?? "").Contains("Marker", StringComparison.OrdinalIgnoreCase)
                || r is ISoundMarkerGetter || r is ITextureSetGetter || r is INpcGetter || r is IIdleMarkerGetter;
            return marker[k] = v;
        }
        var placed = new Dictionary<FormKey, int>();
        var lit = new Dictionary<FormKey, List<object>>();
        int groups = 0, lights = 0, bound = 0;
        void Group(IEnumerable<IPlacedGetter> refs)
        {
            groups++;
            var ps = new List<P>();
            foreach (var r in refs.OfType<IPlacedObjectGetter>())
            {
                var k = r.Base.FormKey; if (k.IsNull || r.Placement == null) continue;
                var pl = r.Placement;
                ps.Add(new P { Base = k, X = pl.Position.X, Y = pl.Position.Y, Z = pl.Position.Z, Rx = pl.Rotation.X, Ry = pl.Rotation.Y, Rz = pl.Rotation.Z,
                    S = r.Scale ?? 1f, Light = Light(k) });
            }
            var grid = new Dictionary<(int, int), List<P>>();
            foreach (var p in ps.Where(p => !p.Light && !Marker(p.Base)))
            {
                placed[p.Base] = placed.GetValueOrDefault(p.Base) + 1;
                var c = ((int)MathF.Floor(p.X / Bind), (int)MathF.Floor(p.Y / Bind));
                if (!grid.TryGetValue(c, out var l)) grid[c] = l = new();
                l.Add(p);
            }
            foreach (var l in ps.Where(p => p.Light))
            {
                lights++;
                P? best = null; var bd = Bind * Bind;
                int cx = (int)MathF.Floor(l.X / Bind), cy = (int)MathF.Floor(l.Y / Bind);
                for (int dx = -1; dx <= 1; dx++) for (int dy = -1; dy <= 1; dy++)
                    if (grid.TryGetValue((cx + dx, cy + dy), out var cand))
                        foreach (var f in cand)
                        {
                            var d = (f.X - l.X) * (f.X - l.X) + (f.Y - l.Y) * (f.Y - l.Y) + (f.Z - l.Z) * (f.Z - l.Z);
                            if (d <= bd) { bd = d; best = f; }
                        }
                if (best == null) continue;
                bound++;
                // the light in the fixture's own frame: R^T (l - f) / s, R = Rx(-x) Ry(-y) Rz(-z) (tools/places/xform.py)
                var o = Local(best, l.X - best.X, l.Y - best.Y, l.Z - best.Z);
                if (!lit.TryGetValue(best.Base, out var ll)) lit[best.Base] = ll = new();
                ll.Add(new object[] { C.Key(l.Base), Math.Round(o[0], 1), Math.Round(o[1], 1), Math.Round(o[2], 1) });
            }
        }
        foreach (var m in mods)
        {
            foreach (var c in C.Interiors(m)) Group(c.Persistent.Concat(c.Temporary));
            foreach (var ws in m.Worldspaces) Group(C.Cells(ws).SelectMany(c => c.Persistent.Concat(c.Temporary)).Concat(ws.TopCell?.Persistent ?? []));
        }
        string Edid(FormKey k) => cache.TryResolve<IMajorRecordGetter>(k, out var r) ? r.EditorID ?? "" : "";
        string Sig(FormKey k) => cache.TryResolve<IMajorRecordGetter>(k, out var r) ? C.Sig(r) : "";
        string? Mdl(FormKey k) => cache.TryResolve<IMajorRecordGetter>(k, out var r) ? C.Model(r) : null;
        var rows = placed.Select(kv => new Dictionary<string, object?>
        {
            ["base"] = C.Key(kv.Key), ["edid"] = Edid(kv.Key), ["type"] = Sig(kv.Key), ["model"] = Mdl(kv.Key), ["placed"] = kv.Value,
            ["lights"] = lit.GetValueOrDefault(kv.Key) ?? new List<object>(),
        }).Where(r => ((List<object>)r["lights"]!).Count > 0 || System.Text.RegularExpressions.Regex.IsMatch($"{r["edid"]} {r["model"]}",
            "candle|lantern|lamp|torch|sconce|brazier|fire|hearth|forge|glow|crystal|mushroom|chandel|ember|light|lit", System.Text.RegularExpressions.RegexOptions.IgnoreCase)).ToList();
        C.WriteJson(outPath, new Dictionary<string, object> { ["plugins"] = plugins, ["groups"] = groups, ["lights"] = lights, ["bound"] = bound, ["bases"] = rows });
        Console.WriteLine($"lightpairs: {groups} groups, {lights} lights, {bound} bound, {rows.Count} bases");
        return 0;
    }

    static double[] Local(P f, float dx, float dy, float dz)
    {
        static double[][] Mul(double[][] a, double[][] b) => Enumerable.Range(0, 3).Select(i => Enumerable.Range(0, 3).Select(j => a[i][0] * b[0][j] + a[i][1] * b[1][j] + a[i][2] * b[2][j]).ToArray()).ToArray();
        static double[][] Rx(double a) => new[] { new[] { 1.0, 0, 0 }, new[] { 0, Math.Cos(a), -Math.Sin(a) }, new[] { 0, Math.Sin(a), Math.Cos(a) } };
        static double[][] Ry(double a) => new[] { new[] { Math.Cos(a), 0, Math.Sin(a) }, new[] { 0, 1.0, 0 }, new[] { -Math.Sin(a), 0, Math.Cos(a) } };
        static double[][] Rz(double a) => new[] { new[] { Math.Cos(a), -Math.Sin(a), 0 }, new[] { Math.Sin(a), Math.Cos(a), 0 }, new[] { 0, 0, 1.0 } };
        var R = Mul(Rx(-f.Rx), Mul(Ry(-f.Ry), Rz(-f.Rz)));
        var s = f.S == 0 ? 1 : f.S;
        return Enumerable.Range(0, 3).Select(j => (R[0][j] * dx + R[1][j] * dy + R[2][j] * dz) / s).ToArray();
    }
}
