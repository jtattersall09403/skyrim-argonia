// The place layers' cell overrides (0.4 §d; decisions 0026 §3, 0031 §2): a built place lays its references in the
// cells of a master (an exterior cell of ArgoniaWorld.esm, or a borrowed interior of a dependency plugin) by
// overriding that CELL in Argonia.esm. An override replaces the whole CELL record, so the master's own record is
// copied (its water, regions, lighting, flags; never its children) and only the references are ours. Persistent
// references of an exterior cell go to the worldspace's persistent cell, as the Creation Kit files them.
//   CELL {"override": true, "formKey": <the master's CELL>, "edid"?, "name"?, "worldspace"?: <WRLD FormKey, exterior only>,
//         "refs": [PlacedRefs]}
// The master is read from $ARGONIA_WORLD_ESM for ArgoniaWorld.esm (pipeline.py sets it: out/ArgoniaWorld.esm), else
// from the Data folder; a missing master or cell is an error.
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Noggog;

namespace ArgoniaGen;

sealed class PlaceCells : IDisposable
{
    const SkyrimRelease Rel = SkyrimRelease.SkyrimSE;
    readonly string data;
    readonly Dictionary<ModKey, ISkyrimModDisposableGetter> masters = new();
    readonly List<(FormKey key, string? ws, List<JsonElement> refs, string? edid, string? name)> pending = new();

    public PlaceCells(string data) { this.data = data; }

    static string S(JsonElement e, string k) => e.GetProperty(k).GetString() ?? throw new InvalidDataException($"{k} is null");
    static string? Os(JsonElement e, string k) => e.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.String ? v.GetString() : null;

    public void Add(JsonElement r)
    {
        var refs = r.TryGetProperty("refs", out var a) ? a.EnumerateArray().ToList() : new List<JsonElement>();
        pending.Add((FormKey.Factory(S(r, "formKey")), Os(r, "worldspace"), refs, Os(r, "edid"), Os(r, "name")));
    }

    ISkyrimModDisposableGetter Master(ModKey mk)
    {
        if (masters.TryGetValue(mk, out var m)) return m;
        var path = mk.FileName.String.Equals("ArgoniaWorld.esm", StringComparison.OrdinalIgnoreCase)
            ? Environment.GetEnvironmentVariable("ARGONIA_WORLD_ESM") ?? throw new InvalidDataException("ARGONIA_WORLD_ESM is not set (pipeline.py sets it)")
            : Path.Combine(data, mk.FileName);
        if (!File.Exists(path)) throw new InvalidDataException($"cell override: master {mk} not found at {path}");
        return masters[mk] = SkyrimMod.CreateFromBinaryOverlay(path, Rel);
    }

    static ICellGetter? FindInterior(ISkyrimModGetter m, FormKey k) =>
        m.Cells.Records.SelectMany(b => b.SubBlocks).SelectMany(sb => sb.Cells).FirstOrDefault(c => c.FormKey == k);

    static ICellGetter? FindExterior(IWorldspaceGetter ws, FormKey k) =>
        ws.SubCells.SelectMany(b => b.Items).SelectMany(sb => sb.Items).FirstOrDefault(c => c.FormKey == k);

    static Cell Shell(ICellGetter src, string? name)
    {
        var c = (Cell)src.DeepCopy();
        if (name != null) c.Name = name;  // a borrowed interior's displayed name is ours
        c.Temporary.Clear();
        c.Persistent.Clear();
        c.Landscape = null;
        c.NavigationMeshes.Clear();
        // The master's group stamps are not ours, and Spriggit does not keep them: zero, as every cell we write.
        c.Timestamp = 0; c.UnknownGroupData = 0;
        c.PersistentTimestamp = 0; c.PersistentUnknownGroupData = 0;
        c.TemporaryTimestamp = 0; c.TemporaryUnknownGroupData = 0;
        return c;
    }

    /// After every other record: the overrides into their blocks, persistent exterior refs into the WRLD's top cell.
    public void Finish(SkyrimMod mod)
    {
        foreach (var (key, wsKey, refs, edid, name) in pending)
        {
            var master = Master(key.ModKey);
            if (wsKey is null)
            {
                var src = FindInterior(master, key) ?? throw new InvalidDataException($"cell override: no interior {key} in {key.ModKey}");
                var c = Shell(src, name);
                foreach (var p in refs) PlacedRefs.File(c, p);
                int block = (int)(key.ID % 10), sub = (int)(key.ID / 10 % 10);
                var b = mod.Cells.Records.FirstOrDefault(x => x.BlockNumber == block);
                if (b == null) { b = new CellBlock { BlockNumber = block, GroupType = GroupTypeEnum.InteriorCellBlock }; mod.Cells.Records.Add(b); }
                var sb = b.SubBlocks.FirstOrDefault(x => x.BlockNumber == sub);
                if (sb == null) { sb = new CellSubBlock { BlockNumber = sub, GroupType = GroupTypeEnum.InteriorCellSubBlock }; b.SubBlocks.Add(sb); }
                sb.Cells.Add(c);
                continue;
            }
            var wk = FormKey.Factory(wsKey);
            var mws = master.Worldspaces.FirstOrDefault(w => w.FormKey == wk) ?? throw new InvalidDataException($"cell override: no worldspace {wk} in {key.ModKey}");
            var ws = mod.Worldspaces.FirstOrDefault(w => w.FormKey == wk) ?? throw new InvalidDataException($"cell override: Argonia.esm has no WRLD override {wk}");
            var srcCell = FindExterior(mws, key) ?? throw new InvalidDataException($"cell override: no exterior cell {key} in {wk}");
            var cell = Shell(srcCell, name);
            foreach (var p in refs)
            {
                if (PlacedRefs.Persistent(p)) ws.TopCell!.Persistent.Add(PlacedRefs.Build(p));
                else cell.Temporary.Add(PlacedRefs.Build(p));
            }
            var g = cell.Grid!.Point;
            int bx = g.X >> 5, by = g.Y >> 5, sx = g.X >> 3, sy = g.Y >> 3;  // floor division, as the engine's blocks
            var blk = ws.SubCells.FirstOrDefault(x => x.BlockNumberX == bx && x.BlockNumberY == by);
            if (blk == null) { blk = new WorldspaceBlock { BlockNumberX = (short)bx, BlockNumberY = (short)by, GroupType = GroupTypeEnum.ExteriorCellBlock }; ws.SubCells.Add(blk); }
            var sub2 = blk.Items.FirstOrDefault(x => x.BlockNumberX == sx && x.BlockNumberY == sy);
            if (sub2 == null) { sub2 = new WorldspaceSubBlock { BlockNumberX = (short)sx, BlockNumberY = (short)sy, GroupType = GroupTypeEnum.ExteriorCellSubBlock }; blk.Items.Add(sub2); }
            sub2.Items.Add(cell);
        }
        // Blocks, sub-blocks and cells in a fixed order, so the bytes do not depend on the layers' order.
        foreach (var ws in mod.Worldspaces)
        {
            var blocks = ws.SubCells.OrderBy(b => b.BlockNumberY).ThenBy(b => b.BlockNumberX).ToList();
            ws.SubCells.Clear();
            foreach (var b in blocks)
            {
                var subs = b.Items.OrderBy(s => s.BlockNumberY).ThenBy(s => s.BlockNumberX).ToList();
                b.Items.Clear();
                foreach (var s in subs)
                {
                    var cells = s.Items.OrderBy(c => c.FormKey.ID).ToList();
                    s.Items.Clear(); s.Items.AddRange(cells);
                    b.Items.Add(s);
                }
                ws.SubCells.Add(b);
            }
        }
    }

    public void Dispose()
    {
        foreach (var m in masters.Values) m.Dispose();
    }
}
