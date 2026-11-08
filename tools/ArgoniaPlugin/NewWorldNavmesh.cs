// The new world's navmesh in ArgoniaNewWorld.esm (nw-02 step 10): every cell's NAVM and the NAVI, from
// tools/navmesh (`python -m tools.navmesh build`, out/newworld/plugin/navmesh). No layout knowledge and no choices
// here: the Python side packs each record whole (tools/navmesh/nvnm.py, stitch.py, whose NVNM codec reproduces every
// Skyrim.esm NVNM byte for byte); this hands the bytes to Mutagen's own parser with the contract's master list, so
// Mutagen maps every FormID inside (the world, edge-link navmeshes) on write.
//   <dir>/navi.json            {"schema": 1, "masters": [file], "self": file, "build_id", "navi": base64 NAVI record}
//   <dir>/navm/cy+NNN.jsonl.gz {"x", "y", "formKey", "navm": base64 NAVM record (uncompressed)} per cell
// NewWorld.Write calls Attach once, after its cells are made: records built from another land build are left out
// (the ESM is written without a navmesh and says so). `newworld navmesh count <esm>`: the NAVMs and NAVI entries.
using System.IO.Compression;
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Binary.Streams;
using Mutagen.Bethesda.Plugins.Masters;
using Mutagen.Bethesda.Plugins.Meta;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;

static class NewWorldNavmesh
{
    const SkyrimRelease Rel = SkyrimRelease.SkyrimSE;

    static string S(JsonElement e, string k) => e.GetProperty(k).GetString() ?? throw new InvalidDataException($"{k} is null");

    static ParsingMeta Meta(IEnumerable<string> masters, string self)
    {
        var key = ModKey.FromFileName(self);
        var refs = new MasterReferenceCollection(key, masters.Select(m => new MasterReference { Master = ModKey.FromFileName(m) }));
        var pkg = SeparatedMasterPackage.Factory(GameRelease.SkyrimSE, key, MasterStyle.Full, refs, null);
        return new ParsingMeta(GameConstants.Get(GameRelease.SkyrimSE), key, pkg);
    }

    static MutagenFrame Frame(byte[] b, ParsingMeta meta) => new(new MutagenMemoryReadStream(b, meta, 0));

    /// The navmesh of `<dir of outPath>/navmesh` onto the worldspace's cells and the NAVI into the mod, when it was
    /// built from this land build; returns the NAVM count (0 when there is none to attach).
    public static int Attach(SkyrimMod mod, Worldspace ws, string outPath, string buildId)
    {
        var dir = Environment.GetEnvironmentVariable("NW_NAVMESH") ?? Path.Combine(Path.GetDirectoryName(Path.GetFullPath(outPath))!, "navmesh");
        var naviPath = Path.Combine(dir, "navi.json");
        if (!File.Exists(naviPath)) { Console.WriteLine($"newworld navmesh: none at {dir}"); return 0; }
        using var doc = JsonDocument.Parse(File.ReadAllText(naviPath));
        var r = doc.RootElement;
        if (r.GetProperty("schema").GetInt32() != 1) throw new InvalidDataException("navi.json schema must be 1");
        var built = r.TryGetProperty("build_id", out var b) ? b.GetString() : null;
        if (built != buildId) { Console.WriteLine($"newworld navmesh: {dir} is from land build {built}, not {buildId}: left out"); return 0; }
        var meta = Meta(r.GetProperty("masters").EnumerateArray().Select(e => e.GetString()!), S(r, "self"));
        var navi = NavigationMeshInfoMap.CreateFromBinary(Frame(Convert.FromBase64String(S(r, "navi")), meta));
        var cells = new Dictionary<(int, int), Cell>();
        foreach (var blk in ws.SubCells) foreach (var sb in blk.Items) foreach (var c in sb.Items)
            if (c.Grid is { } g) cells[(g.Point.X, g.Point.Y)] = c;
        int applied = 0;
        foreach (var path in Directory.GetFiles(Path.Combine(dir, "navm"), "cy*.jsonl.gz").OrderBy(p => p, StringComparer.Ordinal))
        {
            using var f = File.OpenRead(path);
            using var z = new GZipStream(f, CompressionMode.Decompress);
            using var rd = new StreamReader(z);
            while (rd.ReadLine() is { } line)
            {
                using var d = JsonDocument.Parse(line);
                var e = d.RootElement;
                var at = (e.GetProperty("x").GetInt32(), e.GetProperty("y").GetInt32());
                if (!cells.TryGetValue(at, out var cell)) throw new InvalidDataException($"navmesh for cell {at}, which the ESM does not have");
                var n = NavigationMesh.CreateFromBinary(Frame(Convert.FromBase64String(S(e, "navm")), meta));
                n.IsCompressed = true;  // stored compressed, as vanilla's
                cell.NavigationMeshes.Add(n);
                applied++;
            }
        }
        if (applied != navi.MapInfos.Count) throw new InvalidDataException($"navmesh: {applied} NAVM applied, the NAVI lists {navi.MapInfos.Count}");
        mod.NavigationMeshInfoMaps.Add(navi);
        Console.WriteLine($"newworld navmesh: {applied} NAVM and the NAVI from {dir}");
        return applied;
    }

    public static int Run(string[] a)
    {
        if (a.Length < 2 || a[0] != "count") throw new ArgumentException("newworld navmesh count <esm>");
        using var mod = SkyrimMod.CreateFromBinaryOverlay(a[1], Rel, Survey.NoStrings);
        int navm = 0, cells = 0;
        foreach (var c in mod.EnumerateMajorRecords<ICellGetter>())
        {
            var k = c.NavigationMeshes.Count;
            navm += k;
            if (k > 0) cells++;
        }
        var entries = mod.NavigationMeshInfoMaps.Sum(n => n.MapInfos.Count);
        Console.WriteLine($"newworld navmesh count: {a[1]}: {navm} NAVM in {cells} cells, NAVI entries {entries}");
        return navm == entries ? 0 : 1;
    }
}
