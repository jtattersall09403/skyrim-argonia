// The navmesh (2.W4 §b) in ArgoniaWorld.esm: every exterior cell's NAVM and the NAVI override, from
// tools/navmesh (`python -m tools.navmesh build`). As Generate.cs: no layout knowledge and no choices. The Python side
// packs each record whole (tools/navmesh/nvnm.py, stitch.py); this hands the bytes to Mutagen's own parser with the
// contract's master list, so Mutagen maps every FormID inside (world, edge-link navmeshes, doors) on write.
//   <dir>/navi.json            {"schema": 1, "masters": [file], "self": file, "navi": base64 NAVI record}
//   <dir>/navm/cy+NNN.jsonl.gz {"x", "y", "formKey", "navm": base64 NAVM record (uncompressed)} per cell
//   navmesh roundtrip --in <jsonl.gz> --out <esm>   the same parse, onto override cells of a vanilla worldspace:
//                                                   the vanilla round trip of `python -m tools.navmesh vanilla`
using System.IO.Compression;
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Binary.Streams;
using Mutagen.Bethesda.Plugins.Masters;
using Mutagen.Bethesda.Plugins.Meta;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Noggog;

namespace ArgoniaGen;

sealed class NavmeshRecords
{
    const SkyrimRelease Rel = SkyrimRelease.SkyrimSE;
    readonly string dir;
    readonly ParsingMeta meta;
    readonly NavigationMeshInfoMap navi;
    readonly Dictionary<int, Dictionary<(int, int), byte[]>> rows = new();
    int applied, expected;

    static string S(JsonElement e, string k) => e.GetProperty(k).GetString() ?? throw new InvalidDataException($"{k} is null");

    NavmeshRecords(string dir, ParsingMeta meta, NavigationMeshInfoMap navi) { this.dir = dir; this.meta = meta; this.navi = navi; }

    public static ParsingMeta Meta(IEnumerable<string> masters, string self)
    {
        var key = ModKey.FromFileName(self);
        var refs = new MasterReferenceCollection(key, masters.Select(m => new MasterReference { Master = ModKey.FromFileName(m) }));
        var pkg = SeparatedMasterPackage.Factory(GameRelease.SkyrimSE, key, MasterStyle.Full, refs, null);
        return new ParsingMeta(GameConstants.Get(GameRelease.SkyrimSE), key, pkg);
    }

    static MutagenFrame Frame(byte[] b, ParsingMeta meta) => new(new MutagenMemoryReadStream(b, meta, 0));

    /// One NAVM record's bytes (header and subrecords) through Mutagen's parser, stored compressed as vanilla's.
    public static NavigationMesh Parse(byte[] record, ParsingMeta meta)
    {
        var n = NavigationMesh.CreateFromBinary(Frame(record, meta));
        n.IsCompressed = true;
        return n;
    }

    public static NavmeshRecords Load(string dir)
    {
        using var doc = JsonDocument.Parse(File.ReadAllText(Path.Combine(dir, "navi.json")));
        var r = doc.RootElement;
        if (r.GetProperty("schema").GetInt32() != 1) throw new InvalidDataException("navi.json schema must be 1");
        var meta = Meta(r.GetProperty("masters").EnumerateArray().Select(e => e.GetString()!), S(r, "self"));
        var navi = NavigationMeshInfoMap.CreateFromBinary(Frame(Convert.FromBase64String(S(r, "navi")), meta));
        var nav = new NavmeshRecords(dir, meta, navi) { expected = navi.MapInfos.Count };
        return nav;
    }

    Dictionary<(int, int), byte[]> Row(int y)
    {
        if (rows.TryGetValue(y, out var row)) return row;
        rows.Clear();  // LandWorld reads one shard (one cell row) at a time
        rows[y] = row = new();
        var path = Path.Combine(dir, "navm", $"cy{y:+000;-000}.jsonl.gz");
        if (!File.Exists(path)) return row;
        using var f = File.OpenRead(path);
        using var z = new GZipStream(f, CompressionMode.Decompress);
        using var rd = new StreamReader(z);
        while (rd.ReadLine() is { } line)
        {
            using var d = JsonDocument.Parse(line);
            row[(d.RootElement.GetProperty("x").GetInt32(), y)] = Convert.FromBase64String(S(d.RootElement, "navm"));
        }
        return row;
    }

    /// The cell's navmesh, when it has one.
    public void ApplyCell(Cell c, int x, int y)
    {
        if (!Row(y).Remove((x, y), out var b)) return;
        c.NavigationMeshes.Add(Parse(b, meta));
        applied++;
    }

    /// The NAVI override, once every NAVM it lists has found its cell.
    public void Finish(SkyrimMod mod)
    {
        if (applied != expected) throw new InvalidDataException($"navmesh: {applied} NAVM applied, the NAVI lists {expected}");
        mod.NavigationMeshInfoMaps.Add(navi);
    }

    /// The vanilla round trip: each line {"cell": FormKey, "x", "y", "navm": base64}, parsed with the masters of
    /// the line's own file (none: it is Skyrim.esm's), onto override cells of the worldspace in a test plugin.
    public static int RoundTrip(string inPath, string world, string outPath, string data)
    {
        var meta = Meta(Array.Empty<string>(), "Skyrim.esm");
        var mod = new SkyrimMod(ModKey.FromFileName(Path.GetFileName(outPath)), Rel);
        var ws = new Worldspace(FormKey.Factory(world), Rel);
        mod.Worldspaces.Add(ws);
        var subs = new SortedDictionary<(int, int), WorldspaceSubBlock>();
        var blocks = new SortedDictionary<(int, int), WorldspaceBlock>();
        var cells = new Dictionary<FormKey, Cell>();
        int n = 0;
        using (var f = File.OpenRead(inPath))
        using (var z = new GZipStream(f, CompressionMode.Decompress))
        using (var rd = new StreamReader(z))
            while (rd.ReadLine() is { } line)
            {
                using var d = JsonDocument.Parse(line);
                var e = d.RootElement;
                int x = e.GetProperty("x").GetInt32(), y = e.GetProperty("y").GetInt32();
                var ck = FormKey.Factory(S(e, "cell"));
                var known = cells.TryGetValue(ck, out var cell);
                if (!known) cells[ck] = cell = new Cell(ck, Rel) { Grid = new CellGrid { Point = new P2Int(x, y) } };
                cell!.NavigationMeshes.Add(Parse(Convert.FromBase64String(S(e, "navm")), meta));
                n++;
                if (known) continue;
                int bx = x >> 5, by = y >> 5, sx = x >> 3, sy = y >> 3;
                if (!blocks.TryGetValue((bx, by), out var b))
                    blocks[(bx, by)] = b = new WorldspaceBlock { BlockNumberX = (short)bx, BlockNumberY = (short)by, GroupType = GroupTypeEnum.ExteriorCellBlock };
                if (!subs.TryGetValue((sx, sy), out var sb))
                {
                    subs[(sx, sy)] = sb = new WorldspaceSubBlock { BlockNumberX = (short)sx, BlockNumberY = (short)sy, GroupType = GroupTypeEnum.ExteriorCellSubBlock };
                    b.Items.Add(sb);
                }
                sb.Items.Add(cell);
            }
        ws.SubCells.AddRange(blocks.Values);
        mod.BeginWrite.ToPath(outPath).WithLoadOrder(ModKey.FromFileName("Skyrim.esm"), mod.ModKey).WithDataFolder(data).SingleThread().Write();
        Console.WriteLine($"navmesh roundtrip: {outPath}: {n} NAVM");
        return 0;
    }

    public static int Run(string[] args, Func<string, string?> opt, Func<string?, string> dirOf)
    {
        if (args.Length < 2 || args[1] != "roundtrip") throw new ArgumentException("usage: navmesh roundtrip --in <jsonl.gz> --world <FormKey> --data <dir> --out <esm>");
        return RoundTrip(opt("--in") ?? throw new ArgumentException("missing --in"), opt("--world") ?? "00003C:Skyrim.esm",
                         opt("--out") ?? throw new ArgumentException("missing --out"), dirOf(opt("--data")));
    }
}
