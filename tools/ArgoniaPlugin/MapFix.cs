using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;
using Noggog;

// The world map (docs/phases/4-first-act-built.md W-wrld-map): BM&V's four worlds carry MNAM with every cell
// coordinate zero, so the map camera has no area to pan. Each gets an override from the load order's winner with only
// MNAM's north-west and south-east cells set (the camera heights and pitch kept). Bethesda's convention, measured:
// usable dimensions 0,0 in Tamriel and Solstheim, and the NW/SE box is the camera's pan area inside the land, not
// the land's edge (Tamriel's land x-57..61 y-43..50, its box NW(-30,15) SE(40,-40), about a quarter in from each
// side). So: each world's LAND cell extent across the load order (measured, mapprobe), a quarter in from each side.
static class MapFix
{
    // editor id: (form key, land x min, x max, y min, y max) measured 2026-11-08 by `plugin.sh mapprobe`
    static readonly (string key, int x0, int x1, int y0, int y1)[] Worlds =
    [
        ("23D689:Black Marsh.esm", -35, 35, -39, 18),          // BlackMarsh
        ("0D6960:Black Marsh.esm", -32, 31, -30, 31),          // BlackMarsh2
        ("005900:Black Marsh North.esp", -32, 31, -32, 32),    // BlackMarshNorth (Thorn)
        ("005900:Valenwood.esp", -32, 33, -33, 36),            // Valenwood
    ];

    public static (short nwX, short nwY, short seX, short seY) Box(int x0, int x1, int y0, int y1)
    {
        int ix = (x1 - x0) / 4, iy = (y1 - y0) / 4;
        return ((short)(x0 + ix), (short)(y1 - iy), (short)(x1 - ix), (short)(y0 + iy));
    }

    // Sets the map box on the worlds; `bm` is Generate's BlackMarsh override (extended, not duplicated).
    public static void Apply(SkyrimMod mod, List<ISkyrimModGetter> mods, Worldspace bm)
    {
        var winners = Survey.Winners<IWorldspaceGetter>(mods);
        foreach (var (key, x0, x1, y0, y1) in Worlds)
        {
            var fk = FormKey.Factory(key);
            var w = fk == bm.FormKey ? bm
                : winners[fk].rec.DeepCopy(new Worldspace.TranslationMask(true) { SubCells = false, TopCell = false });
            var (nx, ny, sx, sy) = Box(x0, x1, y0, y1);
            w.MapData ??= new WorldspaceMap();
            w.MapData.NorthwestCellCoords = new P2Int16(nx, ny);
            w.MapData.SoutheastCellCoords = new P2Int16(sx, sy);
            if (w != bm) mod.Worldspaces.Add(w);
        }
        FixNames(mod, mods);
    }

    // Map marker names spelt wrong in BM&V (Black Marsh North's "Lolmoth" on Lilmoth's walled town, 0934A4): a
    // name-only override of each marker ref, copied from the last plugin that places it, in its world's persistent cell.
    static readonly Dictionary<string, string> Names = new()
    {
        ["Lolmoth"] = "Lilmoth", ["Unkown Cave"] = "Unknown Cave", ["Southern Morowind Pass"] = "Southern Morrowind Pass",
    };

    static void FixNames(SkyrimMod mod, List<ISkyrimModGetter> mods)
    {
        var found = new Dictionary<FormKey, (FormKey world, IPlacedObjectGetter rec)>();
        foreach (var m in mods) foreach (var w in m.Worldspaces)
            foreach (var r in w.TopCell?.Persistent.OfType<IPlacedObjectGetter>() ?? [])
                if (r.MapMarker?.Name?.String is { } n && Names.ContainsKey(n)) found[r.FormKey] = (w.FormKey, r);
                else found.Remove(r.FormKey); // a later plugin renamed it already
        foreach (var (fk, (wk, r)) in found.OrderBy(f => f.Key.ToString()))
        {
            // Only in the worlds we already override: Valenwood.esp's "Unkown Cave" 18F86D stands in Skyrim's Tamriel,
            // and a Tamriel override for one name is left out (Skyrim's world is not the player's).
            var w = mod.Worldspaces.FirstOrDefault(x => x.FormKey == wk);
            if (w == null) { Console.WriteLine($"map marker {fk}: {r.MapMarker!.Name!.String} left, in world {wk}"); continue; }
            if (w.TopCell == null)
            {
                var src = Survey.Winners<IWorldspaceGetter>(mods)[wk].rec.TopCell!;
                w.TopCell = src.DeepCopy(new Cell.TranslationMask(true) { Persistent = false, Temporary = false, NavigationMeshes = false, Landscape = false });
            }
            var copy = r.DeepCopy();
            copy.MapMarker!.Name = Names[r.MapMarker!.Name!.String!];
            w.TopCell.Persistent.Add(copy);
            Console.WriteLine($"map marker {fk}: {r.MapMarker.Name.String} -> {copy.MapMarker.Name}");
        }
    }

    public static void Probe(string[] paths)
    {
        var mods = Survey.Load(paths);
        var ws = Survey.Winners<IWorldspaceGetter>(mods);
        foreach (var (fk, (w, from)) in ws)
        {
            int n = 0, x0 = int.MaxValue, x1 = int.MinValue, y0 = int.MaxValue, y1 = int.MinValue;
            foreach (var m in mods)
            {
                var mw = m.Worldspaces.FirstOrDefault(z => z.FormKey == fk); if (mw == null) continue;
                foreach (var b in mw.SubCells) foreach (var sb in b.Items) foreach (var c in sb.Items)
                    if (c.Landscape != null && c.Grid != null) { n++; var p = c.Grid.Point; x0 = Math.Min(x0, p.X); x1 = Math.Max(x1, p.X); y0 = Math.Min(y0, p.Y); y1 = Math.Max(y1, p.Y); }
            }
            var md = w.MapData;
            Console.WriteLine($"{fk}\t{w.EditorID}\twin={from}\tparent={w.Parent?.Worldspace.FormKey}\tMNAM={(md == null ? "none" : $"{md.UsableDimensions} NW{md.NorthwestCellCoords} SE{md.SoutheastCellCoords} cam {md.CameraMinHeight}/{md.CameraMaxHeight}/{md.CameraInitialPitch}")}\tbounds={w.ObjectBoundsMin}..{w.ObjectBoundsMax}\tland={n} x{x0}..{x1} y{y0}..{y1}");
        }
    }
}
