// ArgoniaNav: the walkable surface of each exterior cell, by Recast (DotRecast, zlib licence), 2.W4 §b.
//   cells --in <dir> --out <dir>
// Input (tools/navmesh/inputs.py): grid.json {rows, cols, x0, ytop, step, cells: [x0, y0, x1, y1], params{...}}
// and three row-major rasters (and skip.u8, one byte a cell), row 0 north, one sample per LAND vertex: height.f32 (the game's ground, units),
// water.f32 (the water surface over a wet sample, NaN where dry), flags.u8 (bit 0 painted road).
// Placed collision as triangles of 3 world corners: objects.f32 (a place's: walkable where level enough) and
// objects/cy+NNN.f32 with .n.i32 (the world's scatter, a file a cell row: solid obstacles).
// Output: raw/cy+NNN.bin, one file per cell row, each cell: i32 x, y, nv, nt; nv x f32 (x, y, z) world units;
// nt x (u16 v0, v1, v2, u8 area). Triangles are counter-clockwise seen from above, as every vanilla NAVM's.
// No choice is made here that the params do not name; seams, links and the NVNM are tools/navmesh/stitch.py's.
using System.Text.Json;
using DotRecast.Core;
using DotRecast.Core.Numerics;
using DotRecast.Recast;

namespace ArgoniaNav;

static class Program
{
    static int Main(string[] args)
    {
        string? Opt(string n) { var i = Array.IndexOf(args, n); return i >= 0 && i + 1 < args.Length ? args[i + 1] : null; }
        if (args.Length == 0 || args[0] != "cells") { Console.Error.WriteLine("usage: ArgoniaNav cells --in <dir> --out <dir>"); return 2; }
        var input = Opt("--in") ?? throw new ArgumentException("--in");
        var output = Opt("--out") ?? throw new ArgumentException("--out");
        return Cells.Run(input, output);
    }
}

sealed class Params
{
    public float SnapMax, Cs, Ch, MaxSlopeDeg, ObjAgentRadius, AgentHeight, AgentRadius, AgentClimb, EdgeMaxLen, EdgeMaxError, DetailSampleDist, DetailSampleMaxError, WaterMaxDepth, WeldZ;
    public int BorderSamples, RegionMinSize, RegionMergeSize, VertsPerPoly;
    public static Params From(JsonElement p) => new()
    {
        SnapMax = p.GetProperty("snapMax").GetSingle(), Cs = p.GetProperty("cs").GetSingle(), Ch = p.GetProperty("ch").GetSingle(),
        MaxSlopeDeg = p.GetProperty("maxSlopeDeg").GetSingle(), ObjAgentRadius = p.GetProperty("objAgentRadius").GetSingle(), AgentHeight = p.GetProperty("agentHeight").GetSingle(),
        AgentRadius = p.GetProperty("agentRadius").GetSingle(), AgentClimb = p.GetProperty("agentClimb").GetSingle(),
        EdgeMaxLen = p.GetProperty("edgeMaxLen").GetSingle(), EdgeMaxError = p.GetProperty("edgeMaxError").GetSingle(),
        DetailSampleDist = p.GetProperty("detailSampleDist").GetSingle(), DetailSampleMaxError = p.GetProperty("detailSampleMaxError").GetSingle(),
        WaterMaxDepth = p.GetProperty("waterMaxDepth").GetSingle(), WeldZ = p.GetProperty("weldZ").GetSingle(),
        BorderSamples = p.GetProperty("borderSamples").GetInt32(), RegionMinSize = p.GetProperty("regionMinSize").GetInt32(),
        RegionMergeSize = p.GetProperty("regionMergeSize").GetInt32(), VertsPerPoly = p.GetProperty("vertsPerPoly").GetInt32(),
    };
}

static class Cells
{
    public const int Null = 0, Water = 1, Road = 2, Walkable = 63;  // Recast area ids; 63 is RC_WALKABLE_AREA

    public static int Run(string inDir, string outDir)
    {
        using var doc = JsonDocument.Parse(File.ReadAllText(Path.Combine(inDir, "grid.json")));
        var g = doc.RootElement;
        int rows = g.GetProperty("rows").GetInt32(), cols = g.GetProperty("cols").GetInt32();
        float x0 = g.GetProperty("x0").GetSingle(), ytop = g.GetProperty("ytop").GetSingle(), step = g.GetProperty("step").GetSingle();
        var box = g.GetProperty("cells").EnumerateArray().Select(e => e.GetInt32()).ToArray();
        var p = Params.From(g.GetProperty("params"));
        var hgt = Raster<float>(Path.Combine(inDir, "height.f32"), rows * cols);
        var wat = Raster<float>(Path.Combine(inDir, "water.f32"), rows * cols);
        var flg = File.ReadAllBytes(Path.Combine(inDir, "flags.u8"));
        if (flg.Length != rows * cols) throw new InvalidDataException("flags.u8 size");
        if (File.Exists(Path.Combine(inDir, "skip.u8")) && new FileInfo(Path.Combine(inDir, "skip.u8")).Length != (box[2] - box[0] + 1) * (box[3] - box[1] + 1)) throw new InvalidDataException("skip.u8 size");
        // skip.u8 (inputs.py): one byte per cell of the box, north row first; 1 = no navmesh (margin, off the table)
        var skipPath = Path.Combine(inDir, "skip.u8");
        var skip = File.Exists(skipPath) ? File.ReadAllBytes(skipPath) : null;
        var raw = Path.Combine(outDir, "raw");
        Directory.CreateDirectory(raw);
        foreach (var old in Directory.GetFiles(raw, "cy*.bin")) File.Delete(old);
        // the placed objects' collision, triangles of 3 corners of world x, y, z: objects.f32 (inputs.py: a place's
        // or a test's own, whole) and objects/cy+NNN.f32 (placed.py write_rows: the province's, one file a cell
        // row, each holding the triangles within the pad of that row). A row's cells read both, in that order.
        var objPath = Path.Combine(inDir, "objects.f32");
        var objAll = File.Exists(objPath) ? Raster<float>(objPath, (int)(new FileInfo(objPath).Length / 4)) : Array.Empty<float>();
        var objDir = Path.Combine(inDir, "objects");
        long cells = 0, tris = 0, reused = 0;
        int nx = box[2] - box[0] + 1, B = p.BorderSamples;
        float pad = (B + 1) * step;
        // the triangles; where the row file's begin (those are obstacles only); and for each of those the placed
        // object it belongs to (cy+NNN.n.i32: the triangle count of each object in turn)
        (float[], int, int[]) RowObjects(int cy)
        {
            var keep = new List<float>();
            for (var t = 0; t + 9 <= objAll.Length; t += 9)
            {
                float ya = MathF.Min(objAll[t + 1], MathF.Min(objAll[t + 4], objAll[t + 7])) - pad, yb = MathF.Max(objAll[t + 1], MathF.Max(objAll[t + 4], objAll[t + 7])) + pad;
                if ((int)MathF.Floor(ya / CellUnits) <= cy && (int)MathF.Floor(yb / CellUnits) >= cy) for (var k = 0; k < 9; k++) keep.Add(objAll[t + k]);
            }
            var rowPath = Path.Combine(objDir, $"cy{cy:+000;-000}.f32");
            if (!File.Exists(rowPath)) return (keep.ToArray(), keep.Count, Array.Empty<int>());
            var row = Raster<float>(rowPath, (int)(new FileInfo(rowPath).Length / 4));
            var runPath = Path.Combine(objDir, $"cy{cy:+000;-000}.n.i32");
            var runs = Raster<int>(runPath, (int)(new FileInfo(runPath).Length / 4));
            var group = new int[row.Length / 9];
            var at = 0;
            for (var r = 0; r < runs.Length; r++) for (var k = 0; k < runs[r]; k++) group[at++] = r;
            if (at != group.Length) throw new InvalidDataException($"{runPath}: counts do not add up to the triangles");
            if (keep.Count == 0) return (row, 0, group);
            var from = keep.Count;
            keep.AddRange(row);
            return (keep.ToArray(), from, group);
        }
        // Checkpoint (decision 0037): each cell's result in cache/cx_cy.bin under the sha256 of what it reads (the
        // params, its window of height, water and flags samples, CacheVersion, and every object triangle within the
        // pad of the cell, its neighbours' included); a rerun, a ground change elsewhere or a re-scatter elsewhere
        // reuses every cell whose inputs are unchanged. Written by temp file and rename.
        var cache = Path.Combine(outDir, "cache");
        Directory.CreateDirectory(cache);
        var prm = System.Text.Encoding.UTF8.GetBytes(g.GetProperty("params").GetRawText() + "|" + CacheVersion + "|" + step + "|" + x0 + "|" + ytop);
        for (var cy = box[3]; cy >= box[1]; cy--)
        {
            var (obj, obstacleFrom, group) = RowObjects(cy);
            var grid = new Grid(rows, cols, x0, ytop, step, hgt, wat, flg, obj, obstacleFrom, group);
            // each cell's object triangles, bucketed once, in file order
            var buckets = new List<int>[nx];
            for (var k = 0; k < nx; k++) buckets[k] = new List<int>();
            for (var t = 0; t + 9 <= obj.Length; t += 9)
            {
                float xa = MathF.Min(obj[t], MathF.Min(obj[t + 3], obj[t + 6])) - pad, xb = MathF.Max(obj[t], MathF.Max(obj[t + 3], obj[t + 6])) + pad;
                int cxa = Math.Max(box[0], (int)MathF.Floor(xa / CellUnits)), cxb = Math.Min(box[2], (int)MathF.Floor(xb / CellUnits));
                for (var cx = cxa; cx <= cxb; cx++) buckets[cx - box[0]].Add(t);
            }
            var all = new (List<float>, List<int>)[nx];
            var rowY = cy;
            Parallel.For(0, nx, new ParallelOptions { MaxDegreeOfParallelism = Threads }, k =>
            {
                int cx = box[0] + k, sk = (box[3] - rowY) * nx + k;
                if (skip != null && skip[sk] != 0) { all[k] = (new List<float>(), new List<int>()); return; }
                var key = CellKey(grid, prm, B, cx, rowY, buckets[k]);
                var file = Path.Combine(cache, $"{cx}_{rowY}.bin");
                if (File.Exists(file))
                {
                    var r = Load(file, key);
                    if (r is { } got) { all[k] = got; Interlocked.Increment(ref reused); return; }
                }
                all[k] = Cell(grid, p, cx, rowY, buckets[k]);
                var tmp = file + $".{Environment.ProcessId}.tmp";
                using (var w = new BinaryWriter(File.Create(tmp))) { w.Write(key); WriteCell(w, cx, rowY, all[k]); }
                File.Move(tmp, file, true);
            });
            using var f = File.Create(Path.Combine(raw, $"cy{cy:+000;-000}.bin"));
            using var wr = new BinaryWriter(f);
            for (var k = 0; k < nx; k++)
            {
                WriteCell(wr, box[0] + k, cy, all[k]);
                cells++; tris += all[k].Item2.Count / 4;
            }
        }
        Console.WriteLine($"cells: {reused} of {cells} reused from the cache");
        Console.WriteLine($"cells: {cells} cells, {tris} triangles");
        return 0;
    }

    const string CacheVersion = "cells/2";  // bump when Cell's method changes: every cached cell is then rebuilt

    static void WriteCell(BinaryWriter w, int cx, int cy, (List<float>, List<int>) c)
    {
        var (v, t) = c;
        w.Write(cx); w.Write(cy); w.Write(v.Count / 3); w.Write(t.Count / 4);
        foreach (var x in v) w.Write(x);
        for (var i = 0; i < t.Count; i += 4) { w.Write((ushort)t[i]); w.Write((ushort)t[i + 1]); w.Write((ushort)t[i + 2]); w.Write((byte)t[i + 3]); }
    }

    static (List<float>, List<int>)? Load(string file, byte[] key)
    {
        try
        {
            using var r = new BinaryReader(File.OpenRead(file));
            if (!r.ReadBytes(32).AsSpan().SequenceEqual(key)) return null;
            r.ReadInt32(); r.ReadInt32();
            int nv = r.ReadInt32(), nt = r.ReadInt32();
            var v = new List<float>(nv * 3); var t = new List<int>(nt * 4);
            for (var i = 0; i < nv * 3; i++) v.Add(r.ReadSingle());
            for (var i = 0; i < nt; i++) { t.Add(r.ReadUInt16()); t.Add(r.ReadUInt16()); t.Add(r.ReadUInt16()); t.Add(r.ReadByte()); }
            return (v, t);
        }
        catch (Exception) { return null; }  // a torn or old file: rebuilt
    }

    static byte[] CellKey(Grid g, byte[] prm, int B, int cx, int cy, List<int> objIdx)
    {
        using var h = System.Security.Cryptography.IncrementalHash.CreateHash(System.Security.Cryptography.HashAlgorithmName.SHA256);
        h.AppendData(prm);
        int n = 32 + 2 * B + 1, c0 = g.Col(cx * CellUnits) - B, r0 = g.Row(cy * CellUnits + CellUnits) - B;
        h.AppendData(BitConverter.GetBytes(c0)); h.AppendData(BitConverter.GetBytes(r0));
        for (var j = 0; j < n; j++)
        {
            int k = (r0 + j) * g.Cols + c0;
            if (k < 0 || k + n > g.H.Length) continue;  // Cell throws on such a window
            h.AppendData(System.Runtime.InteropServices.MemoryMarshal.AsBytes(g.H.AsSpan(k, n)));
            h.AppendData(System.Runtime.InteropServices.MemoryMarshal.AsBytes(g.W.AsSpan(k, n)));
            h.AppendData(g.F.AsSpan(k, n));
        }
        // an obstacle triangle is hashed with which of the cell's objects it belongs to, counted from the cell's first:
        // a re-scatter elsewhere in the row renumbers the row's objects and leaves this cell's key as it was
        var firstGroup = -1;
        int first(int t) { if (firstGroup < 0) firstGroup = g.Group[(t - g.ObstacleFrom) / 9]; return firstGroup; }
        foreach (var t in objIdx)
        {
            h.AppendData(System.Runtime.InteropServices.MemoryMarshal.AsBytes(g.Obj.AsSpan(t, 9)));
            if (t >= g.ObstacleFrom) h.AppendData(BitConverter.GetBytes(g.Group[(t - g.ObstacleFrom) / 9] - first(t)));
        }
        return h.GetHashAndReset();
    }

    static T[] Raster<T>(string path, int n) where T : struct
    {
        var b = File.ReadAllBytes(path);
        var a = new T[n];
        if (b.Length != n * System.Runtime.InteropServices.Marshal.SizeOf<T>()) throw new InvalidDataException($"{path}: size");
        Buffer.BlockCopy(b, 0, a, 0, b.Length);
        return a;
    }

    sealed record Grid(int Rows, int Cols, float X0, float Ytop, float Step, float[] H, float[] W, byte[] F, float[] Obj, int ObstacleFrom, int[] Group)
    {
        // sample (row, col) from world (x, y) at sample positions
        public int Col(float x) => (int)Math.Round((x - X0) / Step);
        public int Row(float y) => (int)Math.Round((Ytop - y) / Step);
    }

    const int CellUnits = 4096;
    static readonly int Threads = int.TryParse(Environment.GetEnvironmentVariable("ARGONIA_NAV_THREADS"), out var t) && t > 0 ? t : Math.Max(1, Math.Min(4, Environment.ProcessorCount));  // shared VM: four at most

    // The ground under a plan point: the mean of the quad's two triangulations (the LAND's own diagonal is the
    // engine's), bilinear in effect.
    static float Ground(Grid g, float x, float y)
    {
        float c = (x - g.X0) / g.Step, r = (g.Ytop - y) / g.Step;
        int c0 = Math.Clamp((int)MathF.Floor(c), 0, g.Cols - 2), r0 = Math.Clamp((int)MathF.Floor(r), 0, g.Rows - 2);
        float u = c - c0, v = r - r0;
        float a = g.H[r0 * g.Cols + c0], b = g.H[r0 * g.Cols + c0 + 1], cc = g.H[(r0 + 1) * g.Cols + c0], d = g.H[(r0 + 1) * g.Cols + c0 + 1];
        float z1 = u >= v ? a + u * (b - a) + v * (d - b) : a + v * (cc - a) + u * (d - cc);
        float z2 = u + v <= 1 ? a + u * (b - a) + v * (cc - a) : d + (1 - u) * (cc - d) + (1 - v) * (b - d);
        return (z1 + z2) / 2;
    }

    static (List<float>, List<int>) Cell(Grid g, Params p, int cx, int cy, List<int> objIdx)
    {
        float wx0 = cx * CellUnits, wy0 = cy * CellUnits;
        int B = p.BorderSamples, n = 32 + 2 * B + 1;  // samples per side of the window
        int c0 = g.Col(wx0) - B, r0 = g.Row(wy0 + CellUnits) - B;  // window's north-west sample
        if (c0 < 0 || r0 < 0 || c0 + n > g.Cols || r0 + n > g.Rows) throw new InvalidDataException($"cell {cx},{cy}: window leaves the input grid");
        // Recast space: (x, up, z) = (world x, world z, world y)
        var verts = new float[n * n * 3];
        var wet = new float[n * n];
        var road = new bool[n * n];
        float zmin = float.MaxValue, zmax = float.MinValue;
        for (var j = 0; j < n; j++)
            for (var i = 0; i < n; i++)
            {
                int k = (r0 + j) * g.Cols + (c0 + i), q = j * n + i;
                float h = g.H[k], wl = g.W[k];
                verts[3 * q] = g.X0 + (c0 + i) * g.Step;
                verts[3 * q + 1] = h;
                verts[3 * q + 2] = g.Ytop - (r0 + j) * g.Step;
                wet[q] = float.IsNaN(wl) ? float.NaN : wl - h;  // depth
                road[q] = (g.F[k] & 1) != 0;
                zmin = Math.Min(zmin, h); zmax = Math.Max(zmax, h);
            }
        var tris = new List<int>();
        var areas = new List<int>();
        float cosMax = MathF.Cos(p.MaxSlopeDeg * MathF.PI / 180f);
        void Tri(int a, int b, int c)
        {
            tris.Add(a); tris.Add(b); tris.Add(c);
            areas.Add(Area(verts, wet, road, a, b, c, cosMax, p.WaterMaxDepth));
        }
        for (var j = 0; j < n - 1; j++)
            for (var i = 0; i < n - 1; i++)
            {
                int a = j * n + i, b = a + 1, c = a + n, d = c + 1;  // a NW, b NE, c SW, d SE
                Tri(a, c, b); Tri(b, c, d);
            }
        // the placed objects' collision (triangles, 3 corners of world x, y, z) over the window, rasterised with the
        // ground. The heightfield's
        // height range takes them in, or a tall object would be clipped to a false top inside itself.
        float wxa = verts[0], wxb = verts[3 * (n - 1)], wyb = verts[2], wya = verts[3 * (n * n - 1) + 2];
        var objV = new List<float>();
        var objT = new List<int>();
        var objA = new List<int>();
        var objG = new List<int>();  // the placed object an obstacle triangle belongs to, -1 for a place's triangle
        foreach (var t in objIdx)  // the bucketed triangles, a superset of those the window takes, in file order
        {
            float xa = MathF.Min(g.Obj[t], MathF.Min(g.Obj[t + 3], g.Obj[t + 6])), xb = MathF.Max(g.Obj[t], MathF.Max(g.Obj[t + 3], g.Obj[t + 6]));
            float ya = MathF.Min(g.Obj[t + 1], MathF.Min(g.Obj[t + 4], g.Obj[t + 7])), yb = MathF.Max(g.Obj[t + 1], MathF.Max(g.Obj[t + 4], g.Obj[t + 7]));
            if (xb < wxa || xa > wxb || yb < wya || ya > wyb) continue;
            var k0 = objV.Count / 3;
            for (var k = 0; k < 3; k++)
            {
                objV.Add(g.Obj[t + 3 * k]); objV.Add(g.Obj[t + 3 * k + 2]); objV.Add(g.Obj[t + 3 * k + 1]);  // Recast space
                zmin = Math.Min(zmin, g.Obj[t + 3 * k + 2]); zmax = Math.Max(zmax, g.Obj[t + 3 * k + 2]);
            }
            objT.Add(k0); objT.Add(k0 + 1); objT.Add(k0 + 2);
            objA.Add(t >= g.ObstacleFrom ? Null : Walkable);
            objG.Add(t >= g.ObstacleFrom ? g.Group[(t - g.ObstacleFrom) / 9] : -1);
        }
        // A place's collision carries an actor where a face is within the slope limit (a porch, a deck, a stair). The
        // world's scatter (trees, rocks, logs, cliff pieces: the row files) only stands in the way: no face of it is
        // floor, so no mesh is laid on a trunk's root flare, a log or a boulder's top, and whatever of it stays
        // under the climb height is stepped over on the ground's own mesh (the low-obstacle filter below).
        var ov = objV.ToArray();
        for (var t = 0; t < objT.Count; t += 3) if (objA[t / 3] != Null) objA[t / 3] = Slope(ov, objT[t], objT[t + 1], objT[t + 2], cosMax);
        float bord = B * g.Step;
        var bmin = new RcVec3f(wx0 - bord, zmin - 2 * p.Ch, wy0 - bord);
        var bmax = new RcVec3f(wx0 + CellUnits + bord, zmax + p.AgentHeight + 2 * p.Ch, wy0 + CellUnits + bord);
        int border = (int)MathF.Round(bord / p.Cs);
        int size = (int)MathF.Round((CellUnits + 2 * bord) / p.Cs);
        var ctx = new RcContext();
        int walkH = (int)MathF.Ceiling(p.AgentHeight / p.Ch), walkC = (int)MathF.Floor(p.AgentClimb / p.Ch), walkR = (int)MathF.Ceiling((objA.Count > 0 ? p.ObjAgentRadius : p.AgentRadius) / p.Cs);
        var hf = new RcHeightfield(size, size, bmin, bmax, p.Cs, p.Ch, border);
        RcRasterizations.RasterizeTriangles(ctx, verts, tris.ToArray(), areas.ToArray(), areas.Count, hf, walkC);
        if (objA.Count > 0)
        {
            // a place's triangles go in with the ground; the scatter's are voxelised apart, each column's solid runs
            // found first, and each run then meets the ground once: a run whose top is within the climb of the ground
            // is stepped over, any other is an obstacle. (Rasterised straight in, a finely cut rock climbs face by
            // face, each within the climb of the last, and its top ends up floor.)
            var pt = new List<int>(); var pa = new List<int>(); var st = new List<int>(); var sg = new List<int>();
            for (var t = 0; t < objT.Count; t += 3)
            {
                var into = objG[t / 3] < 0 ? pt : st;
                into.Add(objT[t]); into.Add(objT[t + 1]); into.Add(objT[t + 2]);
                if (objG[t / 3] < 0) pa.Add(objA[t / 3]); else sg.Add(objG[t / 3]);
            }
            if (pa.Count > 0) RcRasterizations.RasterizeTriangles(ctx, ov, pt.ToArray(), pa.ToArray(), pa.Count, hf, walkC);
            if (sg.Count > 0)
            {
                var solid = new RcHeightfield(size, size, bmin, bmax, p.Cs, p.Ch, border);
                RcRasterizations.RasterizeTriangles(ctx, ov, st.ToArray(), new int[sg.Count], sg.Count, solid, walkC);
                FillObstacles(solid, ov, st, sg, walkC);
                for (var k = 0; k < solid.spans.Length; k++)
                    for (var sp = solid.spans[k]; sp != null; sp = sp.next)
                        RcRasterizations.AddSpan(hf, k % solid.width, k / solid.width, sp.smin, sp.smax, Null, walkC);
            }
            SolidGround(hf, g);
        }
        RcFilters.FilterLowHangingWalkableObstacles(ctx, walkC, hf);
        RcFilters.FilterLedgeSpans(ctx, walkH, walkC, hf);
        RcFilters.FilterWalkableLowHeightSpans(ctx, walkH, hf);
        var chf = RcCompacts.BuildCompactHeightfield(ctx, walkH, walkC, hf);
        RcAreas.ErodeWalkableArea(ctx, walkR, chf);
        RcRegions.BuildDistanceField(ctx, chf);
        RcRegions.BuildRegions(ctx, chf, p.RegionMinSize, p.RegionMergeSize);
        var cset = RcContours.BuildContours(ctx, chf, p.EdgeMaxError, (int)(p.EdgeMaxLen / p.Cs), RcBuildContoursFlags.RC_CONTOUR_TESS_WALL_EDGES);
        var outV = new List<float>();
        var outT = new List<int>();
        if (cset.conts.Count == 0) return (outV, outT);
        var pm = RcMeshs.BuildPolyMesh(ctx, cset, p.VertsPerPoly);
        if (pm.npolys == 0) return (outV, outT);
        var dm = RcMeshDetails.BuildPolyMeshDetail(ctx, pm, chf, p.DetailSampleDist, p.DetailSampleMaxError);
        Weld(dm, pm, p.WeldZ, outV, outT);
        // Recast's heights are voxel tops (up to a voxel high, more on a slope): each vertex goes back onto the
        // nearest surface under or over it, the ground or a walkable face of a placed object (a porch, a deck, a
        // stair), within snapMax.
        for (var i = 0; i < outV.Count; i += 3)
        {
            float x = outV[i], y = outV[i + 1], z0 = outV[i + 2];
            var z = Ground(g, x, y);
            for (var t = 0; t < objT.Count; t += 3)
            {
                if (objA[t / 3] == Null) continue;
                var s = OnTriangle(ov, objT[t], objT[t + 1], objT[t + 2], x, y);
                if (s is float zs && MathF.Abs(zs - z0) < MathF.Abs(z - z0)) z = zs;
            }
            if (MathF.Abs(z0 - z) <= p.SnapMax) outV[i + 2] = z;
        }
        return (outV, outT);
    }

    // An obstacle is solid, not a shell: Recast rasterises a mesh's faces, so the ground inside a trunk's hull or
    // under a boulder's skin would stay open floor with head room. For each placed object in turn, every column whose
    // centre its faces cross is filled between the crossings, bottom to top in pairs (in, out); with an odd count
    // the lowest crossing is the top of a body open underneath (a rock's collision has no underside) and the column
    // is filled from the bottom up to it.
    static void FillObstacles(RcHeightfield hf, float[] v, List<int> tris, List<int> group, int walkC)
    {
        var cross = new Dictionary<int, List<float>>();
        void Flush()
        {
            foreach (var (col, hs) in cross)
            {
                hs.Sort();
                int x = col % hf.width, z = col / hf.width;
                void Span(float lo, float hi)
                {
                    int a = Math.Clamp((int)MathF.Floor((lo - hf.bmin.Y) / hf.ch), 0, 0x1FFE), b = Math.Clamp((int)MathF.Ceiling((hi - hf.bmin.Y) / hf.ch), a + 1, 0x1FFF);
                    RcRasterizations.AddSpan(hf, x, z, a, b, Null, walkC);
                }
                var k = 0;
                if (hs.Count % 2 == 1) { Span(hf.bmin.Y, hs[0]); k = 1; }
                for (; k + 1 < hs.Count; k += 2) Span(hs[k], hs[k + 1]);
            }
            cross.Clear();
        }
        var cur = -1;
        for (var t = 0; t < tris.Count; t += 3)
        {
            var gI = group[t / 3];
            if (gI < 0) continue;
            if (gI != cur) { Flush(); cur = gI; }
            int a = 3 * tris[t], b = 3 * tris[t + 1], c = 3 * tris[t + 2];
            float ax = v[a], az = v[a + 2], bx = v[b], bz = v[b + 2], cx = v[c], cz = v[c + 2];
            float d = (bz - cz) * (ax - cx) + (cx - bx) * (az - cz);
            if (MathF.Abs(d) < 1e-6f) continue;  // a vertical face crosses no column's centre line
            int x0 = Math.Max(0, (int)MathF.Ceiling((MathF.Min(ax, MathF.Min(bx, cx)) - hf.bmin.X) / hf.cs - 0.5f));
            int x1 = Math.Min(hf.width - 1, (int)MathF.Floor((MathF.Max(ax, MathF.Max(bx, cx)) - hf.bmin.X) / hf.cs - 0.5f));
            int z0 = Math.Max(0, (int)MathF.Ceiling((MathF.Min(az, MathF.Min(bz, cz)) - hf.bmin.Z) / hf.cs - 0.5f));
            int z1 = Math.Min(hf.height - 1, (int)MathF.Floor((MathF.Max(az, MathF.Max(bz, cz)) - hf.bmin.Z) / hf.cs - 0.5f));
            for (var z = z0; z <= z1; z++)
                for (var x = x0; x <= x1; x++)
                {
                    float px = hf.bmin.X + (x + 0.5f) * hf.cs, pz = hf.bmin.Z + (z + 0.5f) * hf.cs;
                    float l1 = ((bz - cz) * (px - cx) + (cx - bx) * (pz - cz)) / d, l2 = ((cz - az) * (px - cx) + (ax - cx) * (pz - cz)) / d, l3 = 1 - l1 - l2;
                    // a centre on a face's edge is taken by two of its three edges only, so two faces sharing it seldom both count
                    if (l1 < 0 || l2 < 0 || l3 <= 0) continue;
                    if (!cross.TryGetValue(x + z * hf.width, out var hs)) cross[x + z * hf.width] = hs = new List<float>();
                    hs.Add(l1 * v[a + 1] + l2 * v[b + 1] + l3 * v[c + 1]);
                }
        }
        Flush();
    }

    // The ground is solid, as the game's terrain is: in each column every span below the one that holds the ground
    // joins it. Without this, collision that reaches under the ground (a hut's buried base, a pier's footing) is
    // open floor beneath it, and Recast's ledge filter drops the real ground beside it as a ledge.
    static void SolidGround(RcHeightfield hf, Grid g)
    {
        for (var z = 0; z < hf.height; z++)
            for (var x = 0; x < hf.width; x++)
            {
                var first = hf.spans[x + z * hf.width];
                if (first == null || first.next == null) continue;
                float wx = hf.bmin.X + (x + 0.5f) * hf.cs, wy = hf.bmin.Z + (z + 0.5f) * hf.cs;
                var gi = (int)MathF.Floor((Ground(g, wx, wy) - hf.bmin.Y) / hf.ch);
                RcSpan? at = null;
                for (var sp = first; sp != null && sp.smin <= gi + 1; sp = sp.next) at = sp;
                if (at == null || at == first) continue;
                at.smin = first.smin;
                hf.spans[x + z * hf.width] = at;
            }
    }

    static int Slope(float[] v, int a, int b, int c, float cosMax)
    {
        float ux = v[3 * b] - v[3 * a], uy = v[3 * b + 1] - v[3 * a + 1], uz = v[3 * b + 2] - v[3 * a + 2];
        float wx = v[3 * c] - v[3 * a], wy = v[3 * c + 1] - v[3 * a + 1], wz = v[3 * c + 2] - v[3 * a + 2];
        float nx = uy * wz - uz * wy, ny = uz * wx - ux * wz, nz = ux * wy - uy * wx;
        float len = MathF.Sqrt(nx * nx + ny * ny + nz * nz);
        // facing up: counter-clockwise seen from above in the world, as Havok winds the outside of a collision mesh;
        // (x, y, z) -> Recast (x, z, y) is a mirror, so that is a negative Recast normal y
        return len > 0 && -ny / len >= cosMax ? Walkable : Null;
    }

    // The height of a triangle (Recast space: x, up, world y) over the plan point (x, y), or null when the point is
    // outside it in plan (half a unit of slack).
    static float? OnTriangle(float[] v, int a, int b, int c, float x, float y)
    {
        float ax = v[3 * a], ay = v[3 * a + 2], bx = v[3 * b], by = v[3 * b + 2], cx = v[3 * c], cy = v[3 * c + 2];
        float d = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy);
        if (MathF.Abs(d) < 1e-6f) return null;
        float l1 = ((by - cy) * (x - cx) + (cx - bx) * (y - cy)) / d, l2 = ((cy - ay) * (x - cx) + (ax - cx) * (y - cy)) / d, l3 = 1 - l1 - l2;
        float eps = 0.5f / MathF.Max(1f, MathF.Sqrt(MathF.Abs(d)));
        if (l1 < -eps || l2 < -eps || l3 < -eps) return null;
        return l1 * v[3 * a + 1] + l2 * v[3 * b + 1] + l3 * v[3 * c + 1];
    }

    static int Area(float[] v, float[] wet, bool[] road, int a, int b, int c, float cosMax, float waterMaxDepth)
    {
        float da = wet[a], db = wet[b], dc = wet[c];
        if (!float.IsNaN(da) && !float.IsNaN(db) && !float.IsNaN(dc) && da > 0 && db > 0 && dc > 0)  // every corner under water
            return (da + db + dc) / 3f <= waterMaxDepth ? Water : Null;
        if (road[a] || road[b] || road[c]) return Road;  // the painted road is walkable, whatever its grade
        // the normal's up component (Recast's y is up)
        float ux = v[3 * b] - v[3 * a], uy = v[3 * b + 1] - v[3 * a + 1], uz = v[3 * b + 2] - v[3 * a + 2];
        float wx = v[3 * c] - v[3 * a], wy = v[3 * c + 1] - v[3 * a + 1], wz = v[3 * c + 2] - v[3 * a + 2];
        float nx = uy * wz - uz * wy, ny = uz * wx - ux * wz, nz = ux * wy - uy * wx;
        float len = MathF.Sqrt(nx * nx + ny * ny + nz * nz);
        return len > 0 && MathF.Abs(ny) / len >= cosMax ? Walkable : Null;
    }

    // The detail triangles of every polygon as one mesh in world (x, y, z): shared vertices welded (same plan
    // position, heights within weldZ), counter-clockwise from above, each with its polygon's area.
    static void Weld(RcPolyMeshDetail dm, RcPolyMesh pm, float weldZ, List<float> outV, List<int> outT)
    {
        var at = new Dictionary<(float, float), List<int>>();
        int Vertex(float x, float y, float z)
        {
            if (!at.TryGetValue((x, y), out var l)) at[(x, y)] = l = new List<int>();
            foreach (var i in l) if (MathF.Abs(outV[3 * i + 2] - z) <= weldZ) return i;
            var k = outV.Count / 3;
            outV.Add(x); outV.Add(y); outV.Add(z);
            l.Add(k);
            return k;
        }
        for (var m = 0; m < dm.nmeshes; m++)
        {
            int vb = dm.meshes[4 * m], tb = dm.meshes[4 * m + 2], tn = dm.meshes[4 * m + 3];
            int area = pm.areas[m];
            for (var t = 0; t < tn; t++)
            {
                var idx = new int[3];
                for (var k = 0; k < 3; k++)
                {
                    var vi = vb + dm.tris[4 * (tb + t) + k];
                    idx[k] = Vertex(dm.verts[3 * vi], dm.verts[3 * vi + 2], dm.verts[3 * vi + 1]);
                }
                if (idx[0] == idx[1] || idx[1] == idx[2] || idx[0] == idx[2]) continue;
                float ax = outV[3 * idx[0]], ay = outV[3 * idx[0] + 1];
                float cr = (outV[3 * idx[1]] - ax) * (outV[3 * idx[2] + 1] - ay) - (outV[3 * idx[1] + 1] - ay) * (outV[3 * idx[2]] - ax);
                if (cr == 0) continue;
                if (cr < 0) (idx[1], idx[2]) = (idx[2], idx[1]);
                outT.Add(idx[0]); outT.Add(idx[1]); outT.Add(idx[2]); outT.Add(area);
            }
        }
        if (outV.Count / 3 > ushort.MaxValue) throw new InvalidDataException("more than 65535 vertices in a cell");
    }
}
