using System.Text;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Archives;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;
using Noggog;

// The placement helper (docs/design/blocks.md, W-ref): what surface lies under a point. Navmesh says where an actor can
// walk, not what is there; this reads the placed statics around the point (the winning refs of the cell and its
// neighbours), each base's model from the load order's archives and loose files (later wins), and casts a vertical
// ray through the model's triangles at that x,y; the land's height comes from the cell's LAND. Game files are read here
// and never written anywhere (decision 0003).
//   surface <worldspace formkey> <x> <y> <plugins in load order...>   every surface under x,y, highest first
static class Surface
{
    public record Hit(string Kind, FormKey Ref, FormKey Base, string? EditorId, string Model, float Top, float? Mesh);

    // The load order's assets: the game's own archives first, then each plugin's archives and loose folder in order.
    public sealed class Assets
    {
        readonly List<(string dir, List<IArchiveReader> bsas)> sources = [];
        public Assets(IEnumerable<string> pluginPaths)
        {
            foreach (var dir in pluginPaths.Select(p => Path.GetDirectoryName(Path.GetFullPath(p))!).Distinct())
            {
                var stems = pluginPaths.Where(p => Path.GetDirectoryName(Path.GetFullPath(p)) == dir).Select(Path.GetFileNameWithoutExtension).ToList();
                var bsas = Directory.GetFiles(dir, "*.bsa").Where(b => stems.Any(s => Path.GetFileName(b).StartsWith(s!, StringComparison.OrdinalIgnoreCase))
                        || Path.GetFileName(b).StartsWith("Skyrim - ", StringComparison.OrdinalIgnoreCase))
                    .OrderBy(b => b).Select(b => Archive.CreateReader(GameRelease.SkyrimSE, new FilePath(b))).ToList();
                sources.Add((dir, bsas));
            }
        }
        public byte[]? Read(string rel)
        {
            rel = rel.Replace('/', '\\').TrimStart('\\');
            for (var i = sources.Count - 1; i >= 0; i--)
            {
                var (dir, bsas) = sources[i];
                if (Loose(dir, rel) is { } ci) return File.ReadAllBytes(ci);
                for (var j = bsas.Count - 1; j >= 0; j--)
                    foreach (var f in bsas[j].Files)
                        if (string.Equals(f.Path.Replace('/', '\\'), rel, StringComparison.OrdinalIgnoreCase)) return f.GetBytes();
            }
            return null;
        }
        // A loose file under dir, each folder and the name matched without case (the game's paths ignore case; a
        // record's "Meshes\Architecture\..." names the folder "meshes/architecture" on this disk).
        static string? Loose(string dir, string rel)
        {
            var at = dir;
            var parts = rel.Split('\\', StringSplitOptions.RemoveEmptyEntries);
            for (var i = 0; i < parts.Length; i++)
            {
                var exact = Path.Combine(at, parts[i]);
                var last = i == parts.Length - 1;
                if (last ? File.Exists(exact) : Directory.Exists(exact)) { at = exact; continue; }
                if (!Directory.Exists(at)) return null;
                var hit = (last ? Directory.GetFiles(at) : Directory.GetDirectories(at)).FirstOrDefault(f => string.Equals(Path.GetFileName(f), parts[i], StringComparison.OrdinalIgnoreCase));
                if (hit == null) return null;
                at = hit;
            }
            return at;
        }
    }

    // A NIF's triangles in model space (BSTriShape family under NiNode transforms; SSE 20.2.0.7, BS version 100).
    public static List<(P3Float a, P3Float b, P3Float c)> Triangles(byte[] nif)
    {
        var r = new BinaryReader(new MemoryStream(nif));
        var line = new StringBuilder(); byte ch; while ((ch = r.ReadByte()) != 0x0A) line.Append((char)ch);
        r.ReadUInt32(); r.ReadByte(); r.ReadUInt32(); var nBlocks = r.ReadInt32(); var bsver = r.ReadUInt32();
        for (var i = 0; i < 3; i++) r.ReadBytes(r.ReadByte());
        if (bsver >= 103) r.ReadBytes(r.ReadByte());
        var types = Enumerable.Range(0, r.ReadUInt16()).Select(_ => Encoding.ASCII.GetString(r.ReadBytes(r.ReadInt32()))).ToArray();
        var typeOf = Enumerable.Range(0, nBlocks).Select(_ => types[r.ReadUInt16() & 0x7FFF]).ToArray();
        var sizes = Enumerable.Range(0, nBlocks).Select(_ => r.ReadUInt32()).ToArray();
        var nStr = r.ReadUInt32(); r.ReadUInt32(); for (var i = 0; i < nStr; i++) r.ReadBytes(r.ReadInt32());
        var nGroups = r.ReadUInt32(); for (var i = 0; i < nGroups; i++) r.ReadUInt32();
        var starts = new long[nBlocks]; var pos = r.BaseStream.Position;
        for (var i = 0; i < nBlocks; i++) { starts[i] = pos; pos += sizes[i]; }

        // Each block's local transform and children (NiNode family) or triangles (BSTriShape family).
        var local = new (float[] m, P3Float t, float s)[nBlocks];
        var children = new List<int>[nBlocks];
        var tris = new List<(P3Float, P3Float, P3Float)>?[nBlocks];
        P3Float V(BinaryReader b) => new(b.ReadSingle(), b.ReadSingle(), b.ReadSingle());
        for (var i = 0; i < nBlocks; i++)
        {
            var t = typeOf[i];
            var isNode = t is "NiNode" or "BSFadeNode" or "BSLeafAnimNode" or "BSOrderedNode" or "BSMultiBoundNode" or "BSValueNode";
            var isShape = t is "BSTriShape" or "BSLODTriShape" or "BSMeshLODTriShape" or "BSSubIndexTriShape";
            if (!isNode && !isShape) continue;
            r.BaseStream.Position = starts[i];
            r.ReadInt32(); r.ReadBytes(4 * r.ReadInt32()); r.ReadInt32(); // name, extra data, controller
            r.ReadUInt32(); var tr = V(r); var m = Enumerable.Range(0, 9).Select(_ => r.ReadSingle()).ToArray(); var sc = r.ReadSingle();
            r.ReadInt32(); // collision
            local[i] = (m, tr, sc);
            if (isNode)
            {
                children[i] = Enumerable.Range(0, r.ReadInt32()).Select(_ => r.ReadInt32()).Where(c => c >= 0 && c < nBlocks).ToList();
                continue;
            }
            r.ReadBytes(16); r.ReadInt32(); r.ReadInt32(); r.ReadInt32(); // bound, skin, shader, alpha
            var desc = r.ReadUInt64();
            var nTri = bsver >= 130 ? (int)r.ReadUInt32() : r.ReadUInt16();
            var nVert = r.ReadUInt16(); var dataSize = r.ReadUInt32();
            if (dataSize == 0 || nVert == 0) continue;
            var stride = (int)(desc & 0xF) * 4;
            var full = bsver < 130 || ((desc >> 44) & 0x400) != 0;
            var verts = new P3Float[nVert];
            for (var v = 0; v < nVert; v++)
            {
                var at = r.BaseStream.Position;
                verts[v] = full ? V(r) : new P3Float((float)r.ReadHalf(), (float)r.ReadHalf(), (float)r.ReadHalf());
                r.BaseStream.Position = at + stride;
            }
            tris[i] = Enumerable.Range(0, nTri).Select(_ => (verts[r.ReadUInt16()], verts[r.ReadUInt16()], verts[r.ReadUInt16()])).ToList();
        }
        // Walk from the root (block 0) composing transforms.
        var outTris = new List<(P3Float, P3Float, P3Float)>();
        void Walk(int i, float[] m, P3Float t, float s, int depth)
        {
            if (depth > 64 || local[i].m == null) return;
            var (lm, lt, ls) = local[i];
            // world = parent * local: R = Rp * Rl, T = Tp + sp * Rp * tl, S = sp * sl (NIF rotations are row-major).
            var R = new float[9];
            for (var a = 0; a < 3; a++) for (var b = 0; b < 3; b++) R[a * 3 + b] = m[a * 3] * lm[b] + m[a * 3 + 1] * lm[3 + b] + m[a * 3 + 2] * lm[6 + b];
            var T = Add(t, Mul(m, lt, s)); var S = s * ls;
            if (tris[i] is { } ts) foreach (var (a, b, c) in ts) outTris.Add((Add(T, Mul(R, a, S)), Add(T, Mul(R, b, S)), Add(T, Mul(R, c, S))));
            if (children[i] is { } cs) foreach (var c in cs) Walk(c, R, T, S, depth + 1);
        }
        Walk(0, [1, 0, 0, 0, 1, 0, 0, 0, 1], new P3Float(0, 0, 0), 1, 0);
        return outTris;
    }
    internal static P3Float Add(P3Float a, P3Float b) => new(a.X + b.X, a.Y + b.Y, a.Z + b.Z);
    internal static P3Float Mul(float[] m, P3Float v, float s) => new(s * (m[0] * v.X + m[1] * v.Y + m[2] * v.Z), s * (m[3] * v.X + m[4] * v.Y + m[5] * v.Z), s * (m[6] * v.X + m[7] * v.Y + m[8] * v.Z));

    // A ref's rotation (Skyrim: radians, applied Z then Y then X, i.e. world = Rz * Ry * Rx; we need its inverse to bring
    // the probe into model space).
    internal static float[] RefRot(P3Float r)
    {
        float cx = MathF.Cos(-r.X), sx = MathF.Sin(-r.X), cy = MathF.Cos(-r.Y), sy = MathF.Sin(-r.Y), cz = MathF.Cos(-r.Z), sz = MathF.Sin(-r.Z);
        float[] X = [1, 0, 0, 0, cx, -sx, 0, sx, cx], Y = [cy, 0, sy, 0, 1, 0, -sy, 0, cy], Z = [cz, -sz, 0, sz, cz, 0, 0, 0, 1];
        return M(M(Z, Y), X);
    }
    static float[] M(float[] a, float[] b)
    {
        var o = new float[9];
        for (var i = 0; i < 3; i++) for (var j = 0; j < 3; j++) o[i * 3 + j] = a[i * 3] * b[j] + a[i * 3 + 1] * b[3 + j] + a[i * 3 + 2] * b[6 + j];
        return o;
    }

    // The highest point of a model's triangles at a world x,y, if the vertical line there crosses any.
    static float? MeshTop(List<(P3Float a, P3Float b, P3Float c)> tris, float[] rot, P3Float origin, float scale, float x, float y) =>
        MeshCrossings(tris, rot, origin, scale, x, y).Cast<float?>().DefaultIfEmpty(null).Max();
    // Every height at which a model's triangles cross the vertical line at a world x,y (a deck under a ceiling).
    static List<float> MeshCrossings(List<(P3Float a, P3Float b, P3Float c)> tris, float[] rot, P3Float origin, float scale, float x, float y)
    {
        var all = new List<float>();
        foreach (var (a0, b0, c0) in tris)
        {
            P3Float W(P3Float p) => Add(origin, Mul(rot, p, scale));
            var a = W(a0); var b = W(b0); var c = W(c0);
            var den = (b.Y - c.Y) * (a.X - c.X) + (c.X - b.X) * (a.Y - c.Y);
            if (MathF.Abs(den) < 1e-6f) continue;
            var l1 = ((b.Y - c.Y) * (x - c.X) + (c.X - b.X) * (y - c.Y)) / den;
            var l2 = ((c.Y - a.Y) * (x - c.X) + (a.X - c.X) * (y - c.Y)) / den;
            var l3 = 1 - l1 - l2;
            if (l1 < 0 || l2 < 0 || l3 < 0) continue;
            all.Add(l1 * a.Z + l2 * b.Z + l3 * c.Z);
        }
        return all;
    }

    // The land's height at x,y from the winning LAND of the exterior cell (33 x 33 vertices, 128 units apart).
    public static float? Land(List<ISkyrimModGetter> mods, FormKey world, float x, float y)
    {
        var gx = (int)MathF.Floor(x / 4096); var gy = (int)MathF.Floor(y / 4096);
        if (!ReferenceEquals(landFor, mods)) { landFor = mods; landCache.Clear(); }
        if (!landCache.TryGetValue((world, gx, gy), out var h))
        {
            ILandscapeGetter? land = null;
            foreach (var m in mods)
                foreach (var w in m.Worldspaces.Where(w => w.FormKey == world))
                    foreach (var c in w.SubCells.SelectMany(b => b.Items).SelectMany(s => s.Items))
                        if (c.Grid?.Point == new P2Int(gx, gy) && c.Landscape?.VertexHeightMap != null) land = c.Landscape;
            if (land?.VertexHeightMap is { } hm)
            {
                h = new float[33, 33]; var rowStart = hm.Offset * 8;
                for (var row = 0; row < 33; row++)
                {
                    rowStart += (sbyte)hm.HeightMap[0, row] * 8; var v = rowStart; h[0, row] = v;
                    for (var col = 1; col < 33; col++) { v += (sbyte)hm.HeightMap[col, row] * 8; h[col, row] = v; }
                }
            }
            landCache[(world, gx, gy)] = h;
        }
        if (h == null) return null;
        float fx = (x - gx * 4096) / 128, fy = (y - gy * 4096) / 128;
        int ix = Math.Clamp((int)fx, 0, 31), iy = Math.Clamp((int)fy, 0, 31); float tx = fx - ix, ty = fy - iy;
        return (h[ix, iy] * (1 - tx) + h[ix + 1, iy] * tx) * (1 - ty) + (h[ix, iy + 1] * (1 - tx) + h[ix + 1, iy + 1] * tx) * ty;
    }

    static object? landFor; static readonly Dictionary<(FormKey, int, int), float[,]?> landCache = [];

    // Every placed static (or other modelled base) whose model lies under x,y, highest first; the land last.
    static object? prepFor; static FormKey prepWorld;
    static Dictionary<FormKey, (string? EditorID, string? Model, IObjectBoundsGetter? ObjectBounds)> bases = [];
    static Dictionary<FormKey, IPlacedObjectGetter>? allRefs;
    static readonly Dictionary<string, List<(P3Float, P3Float, P3Float)>?> meshCache = new(StringComparer.OrdinalIgnoreCase);
    // The plugin paths of the load order, set by the command that loaded them (seed), for the asset reader.
    public static string[] Paths = [];
    public static List<Hit> Under(List<ISkyrimModGetter> mods, Assets assets, FormKey world, float x, float y, float radius = 3000)
    {
        if (!ReferenceEquals(prepFor, mods) || prepWorld != world)
        {
            prepFor = mods; prepWorld = world; Bases(mods);
            allRefs = [];
            foreach (var m in mods)
                foreach (var w in m.Worldspaces.Where(w => w.FormKey == world))
                    foreach (var r in (w.TopCell?.Persistent ?? []).Concat(w.SubCells.SelectMany(b => b.Items).SelectMany(s => s.Items).SelectMany(c => c.Persistent.Concat(c.Temporary))))
                        if (r is IPlacedObjectGetter o && o.Placement != null) allRefs[o.FormKey] = o;
        }
        var hits = UnderRefs(allRefs!.Values.Where(o => MathF.Abs(o.Placement!.Position.X - x) < radius && MathF.Abs(o.Placement!.Position.Y - y) < radius), assets, x, y);
        if (Land(mods, world, x, y) is float lz) hits.Add(new Hit("land", FormKey.Null, FormKey.Null, null, "", lz, lz));
        return hits;
    }

    // The bases with a model (statics, moveable statics, activators, furniture), load-order winners, read once per load.
    static object? basesFor;
    internal static void Bases(List<ISkyrimModGetter> mods)
    {
        if (ReferenceEquals(basesFor, mods)) return;
        basesFor = mods;
        bases = Survey.Winners<IStaticGetter>(mods).ToDictionary(k => k.Key, k => (k.Value.rec.EditorID, k.Value.rec.Model?.File.DataRelativePath.Path, k.Value.rec.ObjectBounds));
        foreach (var (k, (a, _)) in Survey.Winners<IMoveableStaticGetter>(mods)) bases[k] = (a.EditorID, a.Model?.File.DataRelativePath.Path, a.ObjectBounds);
        foreach (var (k, (a, _)) in Survey.Winners<IActivatorGetter>(mods)) bases[k] = (a.EditorID, a.Model?.File.DataRelativePath.Path, a.ObjectBounds);
        foreach (var (k, (a, _)) in Survey.Winners<IFurnitureGetter>(mods)) bases[k] = (a.EditorID, a.Model?.File.DataRelativePath.Path, a.ObjectBounds);
    }
    internal static void AddBases(Dictionary<FormKey, (string? EditorID, string? Model, IObjectBoundsGetter? ObjectBounds)> more) { foreach (var (k, v) in more) bases[k] = v; }
    internal static (string? EditorID, string? Model, IObjectBoundsGetter? ObjectBounds)? Base(FormKey k) => bases.TryGetValue(k, out var b) ? b : null;
    // A model's triangles in model space (cached; null when the model cannot be read).
    internal static List<(P3Float a, P3Float b, P3Float c)>? Mesh(Assets assets, string model)
    {
        if (meshCache.TryGetValue(model, out var tris)) return tris;
        var rel = model.Replace('/', '\\'); if (!rel.StartsWith("meshes\\", StringComparison.OrdinalIgnoreCase)) rel = "meshes\\" + rel;
        var bytes = assets.Read(rel);
        try { tris = bytes == null ? null : Triangles(bytes); } catch { tris = null; }
        return meshCache[model] = tris;
    }

    // The modelled surfaces of the given refs under x,y (any world or interior cell), highest first; Bases must be read.
    // With every crossing, each height a model crosses is a hit of its own (the floor of a one-mesh interior under its roof).
    internal static List<Hit> UnderRefs(IEnumerable<IPlacedObjectGetter> refs, Assets assets, float x, float y, bool everyCrossing = false)
    {
        var hits = new List<Hit>();
        foreach (var o in refs)
        {
            if ((o.MajorRecordFlagsRaw & 0x800) != 0 || !bases.TryGetValue(o.Base.FormKey, out var b) || b.Item2 is not { } model) continue;
            if (model.Replace('/', '\\').Contains("Effects\\", StringComparison.OrdinalIgnoreCase)) continue; // fog, light shafts: no surface
            var p = o.Placement!; var s = o.Scale ?? 1; var rot = RefRot(p.Rotation);
            // Object bounds first (cheap): the probe in model space inside the footprint.
            var inv = new[] { rot[0], rot[3], rot[6], rot[1], rot[4], rot[7], rot[2], rot[5], rot[8] };
            var d = Mul(inv, new P3Float(x - p.Position.X, y - p.Position.Y, 0), 1 / s);
            var ob = b.ObjectBounds; if (ob == null) continue;
            var slack = 64 / s;
            if (d.X < ob.First.X - slack || d.X > ob.Second.X + slack || d.Y < ob.First.Y - slack || d.Y > ob.Second.Y + slack) continue;
            float obTop = float.MinValue;
            foreach (var cx in new[] { ob.First.X, ob.Second.X }) foreach (var cy in new[] { ob.First.Y, ob.Second.Y }) foreach (var cz in new[] { ob.First.Z, ob.Second.Z })
                obTop = MathF.Max(obTop, Add(p.Position, Mul(rot, new P3Float(cx, cy, cz), s)).Z);
            var tris = Mesh(assets, model);
            if (everyCrossing && tris != null)
            {
                foreach (var z in MeshCrossings(tris, rot, p.Position, s, x, y).Select(z => MathF.Round(z)).Distinct())
                    hits.Add(new Hit("mesh", o.FormKey, o.Base.FormKey, b.EditorID, model, z, z));
                continue;
            }
            var top = tris == null ? null : MeshTop(tris, rot, p.Position, s, x, y);
            if (tris != null && top == null) continue; // the footprint's box, but the model has nothing at this x,y
            hits.Add(new Hit(tris == null ? "bounds" : "mesh", o.FormKey, o.Base.FormKey, b.EditorID, model, top ?? obTop, top));
        }
        return hits.OrderByDescending(h => h.Top).ToList();
    }

    // The top of the named surface (an editor id or model path fragment) under x,y, plus a lift; null if none is there.
    public static float? On(List<Hit> hits, string what, float lift) =>
        hits.FirstOrDefault(h => (h.EditorId ?? "").Contains(what, StringComparison.OrdinalIgnoreCase) || h.Model.Contains(what, StringComparison.OrdinalIgnoreCase)) is { } h ? MathF.Round(h.Top + lift) : null;

    internal static IEnumerable<float> NavZ(List<INavigationMeshGetter> navs, float x, float y)
    {
        foreach (var n in navs)
        {
            var d = n.Data!; var v = d.Vertices;
            foreach (var t0 in d.Triangles)
            {
                var t = t0.Vertices; var a = v[t.X]; var b = v[t.Y]; var c = v[t.Z];
                if (x < MathF.Min(a.X, MathF.Min(b.X, c.X)) || x > MathF.Max(a.X, MathF.Max(b.X, c.X)) || y < MathF.Min(a.Y, MathF.Min(b.Y, c.Y)) || y > MathF.Max(a.Y, MathF.Max(b.Y, c.Y))) continue;
                var den = (b.Y - c.Y) * (a.X - c.X) + (c.X - b.X) * (a.Y - c.Y);
                if (MathF.Abs(den) < 1e-6f) continue;
                var l1 = ((b.Y - c.Y) * (x - c.X) + (c.X - b.X) * (y - c.Y)) / den; var l2 = ((c.Y - a.Y) * (x - c.X) + (a.X - c.X) * (y - c.Y)) / den; var l3 = 1 - l1 - l2;
                if (l1 >= 0 && l2 >= 0 && l3 >= 0) yield return l1 * a.Z + l2 * b.Z + l3 * c.Z;
            }
        }
    }

    // surface <worldspace> <x,y[;x,y...]> <plugins...>: every surface under each point, highest first (effects skipped).
    // SURFACE_GRID=<step> instead prints a 13 x 13 map around each point: top modelled surface z / navmesh z.
    public static void Run(string[] args)
    {
        var world = FormKey.Factory(args[0]);
        var paths = args[2..];
        var mods = Survey.Load(paths); var assets = new Assets(paths);
        foreach (var pt in args[1].Split(';'))
        {
            var xy = pt.Split(',').Select(float.Parse).ToArray();
            if (Environment.GetEnvironmentVariable("SURFACE_GRID") is { } g)
            {
                var st = float.Parse(g);
                var navs = Survey.Winners<INavigationMeshGetter>(mods).Values.Select(v => v.rec).Where(n => n.Data is { } d && d.Parent is IWorldspaceNavmeshParentGetter wp && wp.Parent.FormKey == world).ToList();
                for (var gy = 6; gy >= -6; gy--)
                {
                    var line = new StringBuilder();
                    for (var gx = -6; gx <= 6; gx++)
                    {
                        float px = xy[0] + gx * st, py = xy[1] + gy * st;
                        var top = Under(mods, assets, world, px, py, 1500).FirstOrDefault(h => h.Kind == "mesh" && !h.Model.Contains("Effects"));
                        var nav = NavZ(navs, px, py).Select(z => z).DefaultIfEmpty(float.NaN).Max();
                        line.Append($"{(top == null ? "  .  " : $"{top.Top,5:F0}")}/{(float.IsNaN(nav) ? "  .  " : $"{nav,5:F0}")} ");
                    }
                    Console.WriteLine(line);
                }
                continue;
            }
            Console.WriteLine($"{xy[0]:F0},{xy[1]:F0}:");
            foreach (var h in Under(mods, assets, world, xy[0], xy[1]).Where(h => !h.Model.Contains("Effects", StringComparison.OrdinalIgnoreCase)))
                Console.WriteLine($"  {h.Kind,-6} top z {h.Top,8:F1}  {h.EditorId ?? "-"}  {h.Model}  ref {h.Ref.IDString()}{(h.Ref.IsNull ? "" : ":" + h.Ref.ModKey)}");
        }
    }
}
