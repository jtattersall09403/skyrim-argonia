// vegetation: the province's vegetation (2.W4 §a, our own placement from the region rules) spliced into a written
// ArgoniaWorld.esm (decision 0031 §1) as REFRs at the end of each exterior cell's Temporary group.
//   --in <ArgoniaWorld.esm>  as `world` wrote it;  --veg <dir> the shards of tools/argonia_world/vegetation;
//   --out <esm>
//   cy<+NNN>.jsonl.gz: {"x", "y", "region", "bases": [FormKey], "refs": [[local FormID, base index, x, y, z,
//                       rx, ry, rz, scale]]}
// Why a splice and not Mutagen's model: 942k PlacedObjects ran out of memory at a 2.25 GB heap (2.49 GB RSS,
// measured 2026-10-30). The records are written in Mutagen's own layout for a REFR (measured on the water's: header
// flags 0, VCS 0, form version 44; NAME, XSCL when the scale is not 1, DATA), every group size above them grown by
// what it gains, and the header's record count raised. As Generate.cs: no unit maths and no choices. The
// vegetation check reads the result back through Mutagen (`vegcheck`).
using System.Buffers.Binary;
using System.IO.Compression;
using System.Text;
using System.Text.Json;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;

namespace ArgoniaGen;

static class VegetationRecords
{
    const int Hdr = 24;
    const uint Compressed = 0x00040000;

    static string Tag(byte[] b, int o) => Encoding.ASCII.GetString(b, o, 4);
    static uint U32(byte[] b, int o) => BinaryPrimitives.ReadUInt32LittleEndian(b.AsSpan(o));

    /// The REFR bytes per cell (x, y), and their count.
    static Dictionary<(int, int), byte[]> Load(string dir, IReadOnlyList<string> masters, uint own, out long n)
    {
        var mi = masters.Select((m, i) => (m, i)).ToDictionary(t => t.m, t => (uint)t.i, StringComparer.OrdinalIgnoreCase);
        var outp = new Dictionary<(int, int), byte[]>();
        n = 0;
        foreach (var path in Directory.GetFiles(dir, "cy*.jsonl.gz").Order(StringComparer.Ordinal))
        {
            using var f = File.OpenRead(path);
            using var z = new GZipStream(f, CompressionMode.Decompress);
            using var rd = new StreamReader(z);
            while (rd.ReadLine() is { } line)
            {
                if (line.Length == 0) continue;
                using var doc = JsonDocument.Parse(line);
                var e = doc.RootElement;
                var key = (e.GetProperty("x").GetInt32(), e.GetProperty("y").GetInt32());
                var bases = e.GetProperty("bases").EnumerateArray().Select(b =>
                {
                    var s = b.GetString()!.Split(':');
                    if (!mi.TryGetValue(s[1], out var k)) throw new InvalidDataException($"vegetation: {s[1]} is not a master of the plugin");
                    return (k << 24) | Convert.ToUInt32(s[0], 16);
                }).ToArray();
                using var ms = new MemoryStream();
                var w = new BinaryWriter(ms);
                foreach (var r in e.GetProperty("refs").EnumerateArray())
                {
                    var sc = r[8].GetSingle();
                    var scaled = Math.Abs(sc - 1f) > 1e-6;
                    w.Write(Encoding.ASCII.GetBytes("REFR"));
                    w.Write((uint)(10 + (scaled ? 10 : 0) + 30));
                    w.Write(0u);  // flags
                    w.Write(own | r[0].GetUInt32());
                    w.Write(0u);  // VCS
                    w.Write((ushort)44);  // form version
                    w.Write((ushort)0);
                    w.Write(Encoding.ASCII.GetBytes("NAME")); w.Write((ushort)4); w.Write(bases[r[1].GetInt32()]);
                    if (scaled) { w.Write(Encoding.ASCII.GetBytes("XSCL")); w.Write((ushort)4); w.Write(sc); }
                    w.Write(Encoding.ASCII.GetBytes("DATA")); w.Write((ushort)24);
                    for (var k = 2; k <= 7; k++) w.Write(r[k].GetSingle());
                    n++;
                }
                if (!outp.TryAdd(key, ms.ToArray())) throw new InvalidDataException($"vegetation: cell {key} twice");
            }
        }
        return outp;
    }

    static (int, int)? Xclc(byte[] b, int o)
    {
        var size = (int)U32(b, o + 4);
        byte[] d;
        int p;
        if ((U32(b, o + 8) & Compressed) != 0)
        {
            using var zs = new ZLibStream(new MemoryStream(b, o + Hdr + 4, size - 4), CompressionMode.Decompress);
            using var ms = new MemoryStream();
            zs.CopyTo(ms);
            d = ms.ToArray();
            p = 0;
            size = d.Length;
        }
        else { d = b; p = o + Hdr; }
        var end = p + size;
        while (p + 6 <= end)
        {
            var len = BinaryPrimitives.ReadUInt16LittleEndian(d.AsSpan(p + 4));
            if (Tag(d, p) == "XCLC") return (BinaryPrimitives.ReadInt32LittleEndian(d.AsSpan(p + 6)), BinaryPrimitives.ReadInt32LittleEndian(d.AsSpan(p + 10)));
            p += 6 + len;
        }
        return null;
    }

    public static int Run(string inPath, string vegDir, string outPath)
    {
        var b = File.ReadAllBytes(inPath);
        if (Tag(b, 0) != "TES4") throw new InvalidDataException($"{inPath}: not a plugin");
        int tesEnd = Hdr + (int)U32(b, 4), hedr = -1;
        var masters = new List<string>();
        for (var p = Hdr; p < tesEnd;)
        {
            var len = BinaryPrimitives.ReadUInt16LittleEndian(b.AsSpan(p + 4));
            if (Tag(b, p) == "HEDR") hedr = p + 6;
            if (Tag(b, p) == "MAST") masters.Add(Encoding.ASCII.GetString(b, p + 6, len).TrimEnd('\0'));
            p += 6 + len;
        }
        var cells = Load(vegDir, masters, (uint)masters.Count << 24, out var n);
        // pass 1: what each group gains, and where each cell's REFRs go (its Temporary group's offset)
        var gain = new Dictionary<int, long>();
        var insert = new Dictionary<int, byte[]>();
        var cellAt = new Dictionary<uint, (int, int)>();
        var placed = 0;
        long Walk(int o, int end)
        {
            long total = 0;
            while (o < end)
            {
                var size = (int)U32(b, o + 4);
                if (Tag(b, o) == "GRUP")
                {
                    var g = Walk(o + Hdr, o + size);
                    if (BinaryPrimitives.ReadInt32LittleEndian(b.AsSpan(o + 12)) == 9 && cellAt.TryGetValue(U32(b, o + 8), out var key)
                        && cells.TryGetValue(key, out var refs))
                    {
                        insert[o] = refs;
                        g += refs.Length;
                        placed++;
                    }
                    if (g != 0) gain[o] = g;
                    total += g;
                    o += size;
                }
                else
                {
                    if (Tag(b, o) == "CELL" && Xclc(b, o) is { } xy) cellAt[U32(b, o + 12)] = xy;
                    o += Hdr + size;
                }
            }
            return total;
        }
        Walk(tesEnd, b.Length);
        if (placed != cells.Count)
            throw new InvalidDataException($"vegetation: {cells.Count - placed} cells have no Temporary group in {inPath}");
        // pass 2: the copy, sizes grown, REFRs at each Temporary group's end
        Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(outPath))!);
        using var fo = new FileStream(outPath, FileMode.Create, FileAccess.Write, FileShare.None, 1 << 20);
        var head = b.AsSpan(0, tesEnd).ToArray();
        var hp = hedr + 4;
        BinaryPrimitives.WriteInt32LittleEndian(head.AsSpan(hp), checked(BinaryPrimitives.ReadInt32LittleEndian(head.AsSpan(hp)) + (int)n));
        fo.Write(head);
        void Copy(int o, int end)
        {
            while (o < end)
            {
                var size = (int)U32(b, o + 4);
                if (Tag(b, o) == "GRUP")
                {
                    var h = b.AsSpan(o, Hdr).ToArray();
                    if (gain.TryGetValue(o, out var g)) BinaryPrimitives.WriteUInt32LittleEndian(h.AsSpan(4), checked((uint)(size + g)));
                    fo.Write(h);
                    Copy(o + Hdr, o + size);
                    if (insert.TryGetValue(o, out var refs)) fo.Write(refs);
                    o += size;
                }
                else
                {
                    fo.Write(b, o, Hdr + size);
                    o += Hdr + size;
                }
            }
        }
        Copy(tesEnd, b.Length);
        Console.WriteLine($"vegetation: {outPath}: {n} REFRs spliced into {placed} cells");
        return 0;
    }

    /// The read-back (the vegetation check): the spliced plugin through Mutagen's binary overlay, every exterior
    /// cell's Temporary group parsed, and the vegetation REFRs per cell (FormIDs in the reserved range) as JSON lines
    /// {"x", "y", "n"} for the check to compare with the shards.
    public static int Check(string esm, uint first, uint last, string outPath)
    {
        using var mod = SkyrimMod.CreateFromBinaryOverlay(esm, SkyrimRelease.SkyrimSE);
        using var w = new StreamWriter(outPath);
        long total = 0;
        foreach (var ws in mod.Worldspaces)
            foreach (var blk in ws.SubCells)
                foreach (var sb in blk.Items)
                    foreach (var c in sb.Items)
                    {
                        var k = 0;
                        foreach (var r in c.Temporary)
                        {
                            var id = r.FormKey.ID;
                            if (r is IPlacedObjectGetter p && id >= first && id <= last)
                            {
                                _ = p.Base.FormKey;
                                _ = p.Placement?.Position;
                                k++;
                            }
                        }
                        if (k > 0 && c.Grid is { } g) { w.WriteLine($"{{\"x\":{g.Point.X},\"y\":{g.Point.Y},\"n\":{k}}}"); total += k; }
                    }
        Console.WriteLine($"vegcheck: {total} vegetation REFRs read back");
        return 0;
    }
}
