// ArgoniaNav: the walkable surface of each exterior cell, by Recast (DotRecast, zlib licence), 2.W4 §b.
//   cells --in <dir> --out <dir>
// Input (tools/navmesh/inputs.py): grid.json {rows, cols, x0, ytop, step, cells: [x0, y0, x1, y1], params{...}}
// and three row-major rasters, row 0 north, one sample per LAND vertex: height.f32 (the game's ground, units),
// water.f32 (the water surface over a wet sample, NaN where dry), flags.u8 (bit 0 painted road).
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
    public float SnapMax, Cs, Ch, MaxSlopeDeg, AgentHeight, AgentRadius, AgentClimb, EdgeMaxLen, EdgeMaxError, DetailSampleDist, DetailSampleMaxError, WaterMaxDepth, WeldZ;
    public int BorderSamples, RegionMinSize, RegionMergeSize, VertsPerPoly;
    public static Params From(JsonElement p) => new()
    {
        SnapMax = p.GetProperty("snapMax").GetSingle(), Cs = p.GetProperty("cs").GetSingle(), Ch = p.GetProperty("ch").GetSingle(),
        MaxSlopeDeg = p.GetProperty("maxSlopeDeg").GetSingle(), AgentHeight = p.GetProperty("agentHeight").GetSingle(),
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
        var raw = Path.Combine(outDir, "raw");
        Directory.CreateDirectory(raw);
        foreach (var old in Directory.GetFiles(raw, "cy*.bin")) File.Delete(old);
        var grid = new Grid(rows, cols, x0, ytop, step, hgt, wat, flg);
        long cells = 0, tris = 0;
        for (var cy = box[3]; cy >= box[1]; cy--)
        {
            using var f = File.Create(Path.Combine(raw, $"cy{cy:+000;-000}.bin"));
            using var w = new BinaryWriter(f);
            var row = new (List<float>, List<int>)[box[2] - box[0] + 1];  // cells in parallel, written in order
            Parallel.For(0, row.Length, new ParallelOptions { MaxDegreeOfParallelism = Threads }, i => row[i] = Cell(grid, p, box[0] + i, cy));
            for (var cx = box[0]; cx <= box[2]; cx++)
            {
                var (v, t) = row[cx - box[0]];
                w.Write(cx); w.Write(cy); w.Write(v.Count / 3); w.Write(t.Count / 4);
                foreach (var c in v) w.Write(c);
                for (var i = 0; i < t.Count; i += 4) { w.Write((ushort)t[i]); w.Write((ushort)t[i + 1]); w.Write((ushort)t[i + 2]); w.Write((byte)t[i + 3]); }
                cells++; tris += t.Count / 4;
            }
        }
        Console.WriteLine($"cells: {cells} cells, {tris} triangles");
        return 0;
    }

    static T[] Raster<T>(string path, int n) where T : struct
    {
        var b = File.ReadAllBytes(path);
        var a = new T[n];
        if (b.Length != n * System.Runtime.InteropServices.Marshal.SizeOf<T>()) throw new InvalidDataException($"{path}: size");
        Buffer.BlockCopy(b, 0, a, 0, b.Length);
        return a;
    }

    sealed record Grid(int Rows, int Cols, float X0, float Ytop, float Step, float[] H, float[] W, byte[] F)
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

    static (List<float>, List<int>) Cell(Grid g, Params p, int cx, int cy)
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
        float bord = B * g.Step;
        var bmin = new RcVec3f(wx0 - bord, zmin - 2 * p.Ch, wy0 - bord);
        var bmax = new RcVec3f(wx0 + CellUnits + bord, zmax + p.AgentHeight + 2 * p.Ch, wy0 + CellUnits + bord);
        int border = (int)MathF.Round(bord / p.Cs);
        int size = (int)MathF.Round((CellUnits + 2 * bord) / p.Cs);
        var ctx = new RcContext();
        int walkH = (int)MathF.Ceiling(p.AgentHeight / p.Ch), walkC = (int)MathF.Floor(p.AgentClimb / p.Ch), walkR = (int)MathF.Ceiling(p.AgentRadius / p.Cs);
        var hf = new RcHeightfield(size, size, bmin, bmax, p.Cs, p.Ch, border);
        RcRasterizations.RasterizeTriangles(ctx, verts, tris.ToArray(), areas.ToArray(), areas.Count, hf, walkC);
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
        // Recast's heights are voxel tops (up to a voxel high, more on a slope): a vertex that came from the ground
        // goes back onto it. Placed-object collision, when it joins, keeps its own heights (beyond snapMax).
        for (var i = 0; i < outV.Count; i += 3)
        {
            var z = Ground(g, outV[i], outV[i + 1]);
            if (MathF.Abs(outV[i + 2] - z) <= p.SnapMax) outV[i + 2] = z;
        }
        return (outV, outT);
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
