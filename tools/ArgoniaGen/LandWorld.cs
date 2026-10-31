// world: the generated ground (decision 0031) -> ArgoniaWorld.esm, a master of Argonia.esm.
//   --in <world.json>   the WRLD intermediate (tools/argonia_world/terrain/world.py)
//   --land <dir>        the cell shards (tools/argonia_world/terrain/build.py): one JSON line per cell, gzip
// As Generate.cs: no unit maths and no choices; every number, id and link arrives resolved. The shards are read
// one line at a time. Facts measured on Skyrim.esm's Tamriel (2026-10-29): LAND DATA flags 0x1F and compressed;
// per quadrant BottomLeft, BottomRight, TopLeft, TopRight one BTXT (layer 0xFFFF) then its ATXT layers 0..n-1,
// each VTXT entry only where the opacity is above zero; Array2d indexed [x, y] (x east, y north from the south).
using System.IO.Compression;
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Strings;
using Noggog;

namespace ArgoniaGen;

static class LandWorld
{
    const SkyrimRelease Rel = SkyrimRelease.SkyrimSE;
    const int V = 33, QV = 17;
    const Landscape.Flag LandFlags = (Landscape.Flag)0x1F;  // as every vanilla Tamriel LAND
    static readonly Quadrant[] Quads = { Quadrant.BottomLeft, Quadrant.BottomRight, Quadrant.TopLeft, Quadrant.TopRight };

    static string S(JsonElement e, string k) => e.GetProperty(k).GetString() ?? throw new InvalidDataException($"{k} is null");
    static FormKey FK(string s) => FormKey.Factory(s);
    static P2Int16 P2(JsonElement e, string k) => new((short)e.GetProperty(k)[0].GetInt32(), (short)e.GetProperty(k)[1].GetInt32());

    public static int Run(string inPath, string landDir, string data, string outPath, string? waterDir = null, string? navDir = null)
    {
        using var doc = JsonDocument.Parse(File.ReadAllText(inPath));
        var root = doc.RootElement;
        if (root.GetProperty("schema").GetInt32() != 1) throw new InvalidDataException("world intermediate schema must be 1");
        var modKey = ModKey.FromFileName(S(root, "mod"));
        var mod = new SkyrimMod(modKey, Rel);
        mod.ModHeader.Flags |= SkyrimModHeader.HeaderFlag.Master;
        mod.ModHeader.Author = S(root, "author");
        mod.ModHeader.Description = S(root, "description");
        var loadOrder = root.GetProperty("loadOrder").EnumerateArray().Select(e => ModKey.FromFileName(e.GetString()!)).ToList();
        var records = root.GetProperty("records").EnumerateArray().ToList();
        if (records.Count != 1 || S(records[0], "type") != "WRLD")
            throw new InvalidDataException("the world intermediate holds exactly one record, the WRLD");
        var ws = World(records[0]);
        mod.Worldspaces.Add(ws);
        var water = waterDir is null ? null : WaterRecords.Load(mod, ws, waterDir);  // 2.W2 (WaterRecords.cs)
        var nav = navDir is null ? null : NavmeshRecords.Load(navDir);  // 2.W4 §b (NavmeshRecords.cs)
        // the REGN shells and each cell's XCLR (regions/api.py: Argonia.esm overrides the shells with the authored part)
        foreach (var g in root.TryGetProperty("regions", out var rg) ? rg.EnumerateArray() : Enumerable.Empty<JsonElement>())
            mod.Regions.Add(RegionWriters.Shell(g, ws.FormKey));
        var xclr = new Dictionary<(int, int), FormKey>();
        foreach (var run in root.TryGetProperty("cellRegions", out var cr) ? cr.EnumerateArray() : Enumerable.Empty<JsonElement>())
            for (var cx = run.GetProperty("cx0").GetInt32(); cx <= run.GetProperty("cx1").GetInt32(); cx++)
                xclr[(cx, run.GetProperty("cy").GetInt32())] = FK(S(run, "region"));
        // the border region, listed by every cell: the engine holds the player only at a border its cell lists
        FormKey? border = root.TryGetProperty("borderRegion", out var br) && br.ValueKind == JsonValueKind.String ? FK(br.GetString()!) : null;

        // block (32 x 32 cells) -> sub-block (8 x 8) -> cells, all in number order: the bytes never depend on the
        // order the shards were read in
        var blocks = new SortedDictionary<(int, int), SortedDictionary<(int, int), SortedDictionary<(int, int), Cell>>>();
        long n = 0;
        foreach (var path in Directory.GetFiles(landDir, "cy*.jsonl.gz").Order(StringComparer.Ordinal))
        {
            using var f = File.OpenRead(path);
            using var z = new GZipStream(f, CompressionMode.Decompress);
            using var rd = new StreamReader(z);
            while (rd.ReadLine() is { } line)
            {
                using var cd = JsonDocument.Parse(line);
                var c = ExteriorCell(cd.RootElement, out var x, out var y);
                water?.ApplyCell(c, x, y);
                nav?.ApplyCell(c, x, y);
                if (xclr.TryGetValue((x, y), out var reg)) c.Regions = new ExtendedList<IFormLinkGetter<IRegionGetter>> { new FormLink<IRegionGetter>(reg) };
                if (border is { } bk) (c.Regions ??= new ExtendedList<IFormLinkGetter<IRegionGetter>>()).Add(new FormLink<IRegionGetter>(bk));
                int bx = x >> 5, by = y >> 5, sx = x >> 3, sy = y >> 3;  // floor division, as the engine's blocks
                if (!blocks.TryGetValue((bx, by), out var subs)) blocks[(bx, by)] = subs = new();
                if (!subs.TryGetValue((sx, sy), out var cells)) subs[(sx, sy)] = cells = new();
                if (!cells.TryAdd((x, y), c)) throw new InvalidDataException($"cell {x},{y} twice in {landDir}");
                n++;
            }
        }
        foreach (var ((bx, by), subs) in blocks)
        {
            var b = new WorldspaceBlock { BlockNumberX = (short)bx, BlockNumberY = (short)by, GroupType = GroupTypeEnum.ExteriorCellBlock };
            foreach (var ((sx, sy), cells) in subs)
            {
                var sb = new WorldspaceSubBlock { BlockNumberX = (short)sx, BlockNumberY = (short)sy, GroupType = GroupTypeEnum.ExteriorCellSubBlock };
                sb.Items.AddRange(cells.Values);
                b.Items.Add(sb);
            }
            ws.SubCells.Add(b);
        }
        water?.CheckAllApplied();
        nav?.Finish(mod);
        Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(outPath))!);
        mod.BeginWrite
            .ToPath(outPath)
            .WithLoadOrder(loadOrder.Append(modKey))
            .WithDataFolder(data)
            .SingleThread()  // the parallel writer buffers every block in memory: 3.2 GB peak against 0.95 GB here
            .Write();
        Console.WriteLine($"world: {outPath}: 1 WRLD, {mod.Regions.Count} REGN shells, {n} cells with LAND");
        return 0;
    }

    internal static Worldspace World(JsonElement r)
    {
        var ws = new Worldspace(FK(S(r, "formKey")), Rel)
        {
            EditorID = S(r, "edid"),
            Name = new TranslatedString(Language.English, S(r, "name")),
            LandDefaults = new WorldspaceLandDefaults
            {
                DefaultLandHeight = r.GetProperty("defaultLandHeight").GetSingle(),
                DefaultWaterHeight = r.GetProperty("defaultWaterHeight").GetSingle(),
            },
            ObjectBoundsMin = new P2Float(r.GetProperty("boundsMin")[0].GetSingle(), r.GetProperty("boundsMin")[1].GetSingle()),
            ObjectBoundsMax = new P2Float(r.GetProperty("boundsMax")[0].GetSingle(), r.GetProperty("boundsMax")[1].GetSingle()),
            Flags = 0,
        };
        var m = r.GetProperty("map");
        ws.MapData = new WorldspaceMap
        {
            UsableDimensions = new P2Int(m.GetProperty("usable")[0].GetInt32(), m.GetProperty("usable")[1].GetInt32()),
            NorthwestCellCoords = P2(m, "nw"),
            SoutheastCellCoords = P2(m, "se"),
            CameraMinHeight = m.GetProperty("cameraMin").GetSingle(),
            CameraMaxHeight = m.GetProperty("cameraMax").GetSingle(),
            CameraInitialPitch = m.GetProperty("cameraPitch").GetSingle(),
        };
        if (r.TryGetProperty("mapOffset", out var mo))  // ONAM: scale, cell x, y, z offset (Argonia.esm's override: FWMF's)
        {
            ws.WorldMapOffsetScale = mo[0].GetSingle();
            ws.WorldMapCellOffset = new P3Float(mo[1].GetSingle(), mo[2].GetSingle(), mo[3].GetSingle());
        }
        var top = r.GetProperty("topCell");
        ws.TopCell = new Cell(FK(S(top, "formKey")), Rel)
        {
            Flags = Cell.Flag.HasWater,
            Grid = new CellGrid { Point = new P2Int(0, 0) },
            MajorFlags = Cell.MajorFlag.Persistent,
        };
        return ws;
    }

    static byte[] B64(JsonElement e, string k, int len)
    {
        var b = Convert.FromBase64String(S(e, k));
        if (b.Length != len) throw new InvalidDataException($"{k}: {b.Length} bytes, expected {len}");
        return b;
    }

    static Cell ExteriorCell(JsonElement e, out int x, out int y)
    {
        x = e.GetProperty("x").GetInt32();
        y = e.GetProperty("y").GetInt32();
        var vhgt = B64(e, "vhgt", V * V);
        var vnml = B64(e, "vnml", V * V * 3);
        var vclr = B64(e, "vclr", V * V * 3);
        var hm = new Array2d<sbyte>(V, V, 0);
        var nm = new Array2d<P3UInt8>(V, V, new P3UInt8(0, 0, 0));
        var cm = new Array2d<P3UInt8>(V, V, new P3UInt8(0, 0, 0));
        for (var j = 0; j < V; j++)  // input arrays are [y][x], y from the south
            for (var i = 0; i < V; i++)
            {
                var k = j * V + i;
                hm[i, j] = unchecked((sbyte)vhgt[k]);
                nm[i, j] = new P3UInt8(vnml[3 * k], vnml[3 * k + 1], vnml[3 * k + 2]);  // signed bytes, as stored
                cm[i, j] = new P3UInt8(vclr[3 * k], vclr[3 * k + 1], vclr[3 * k + 2]);
            }
        var land = new Landscape(FK(S(e, "land")), Rel)
        {
            Flags = LandFlags,
            IsCompressed = true,
            VertexHeightMap = new LandscapeVertexHeightMap { Offset = e.GetProperty("offset").GetSingle(), HeightMap = hm },
            VertexNormals = nm,
            VertexColors = cm,
            Layers = new ExtendedList<BaseLayer>(),
        };
        var quads = e.GetProperty("quads").EnumerateArray().ToList();
        if (quads.Count != 4) throw new InvalidDataException($"cell {x},{y}: {quads.Count} quadrants");
        for (var qi = 0; qi < 4; qi++)
        {
            var q = quads[qi];
            var quad = Enum.Parse<Quadrant>(S(q, "q"));
            if (quad != Quads[qi]) throw new InvalidDataException($"cell {x},{y}: quadrant {qi} is {quad}");
            land.Layers.Add(new BaseLayer { Header = new LayerHeader { Texture = new FormLink<ILandscapeTextureGetter>(FK(S(q, "base"))), Quadrant = quad, LayerNumber = 0xFFFF } });
            ushort ln = 0;
            foreach (var l in q.GetProperty("layers").EnumerateArray())
            {
                var alpha = B64(l, "alpha", QV * QV);
                var data = new ExtendedList<AlphaLayerData>();
                for (ushort p = 0; p < alpha.Length; p++)
                    if (alpha[p] > 0) data.Add(new AlphaLayerData { Position = p, Opacity = alpha[p] / 255f });
                land.Layers.Add(new AlphaLayer
                {
                    Header = new LayerHeader { Texture = new FormLink<ILandscapeTextureGetter>(FK(S(l, "ltex"))), Quadrant = quad, LayerNumber = ln++ },
                    AlphaLayerData = data,
                });
            }
        }
        return new Cell(FK(S(e, "cell")), Rel)
        {
            Flags = Cell.Flag.HasWater,
            Grid = new CellGrid { Point = new P2Int(x, y) },
            Landscape = land,
        };
    }
}
