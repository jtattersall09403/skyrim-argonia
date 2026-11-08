using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;

// The one lookup for "the mod's existing override of this world or cell, or a new one": every step (MapFix, Music,
// Talk, CleanUp, LocalQuests, NightReed, Chainbreakers, MQ*) extends the override an earlier step made rather than
// adding a second record with the same form id. A new override is the load order's winner without its refs.
public static class Overrides
{
    public static readonly Cell.TranslationMask NoRefs = new(true) { Persistent = false, Temporary = false, NavigationMeshes = false, Landscape = false };

    // The world's override with its persistent cell; the plugin its winner comes from is a master (LocalQuests.Masters).
    public static Worldspace World(SkyrimMod mod, List<ISkyrimModGetter> mods, FormKey wk)
    {
        var (win, from) = Survey.Winners<IWorldspaceGetter>(mods)[wk];
        var w = mod.Worldspaces.FirstOrDefault(x => x.FormKey == wk);
        if (w == null)
        {
            w = win.DeepCopy(new Worldspace.TranslationMask(true) { SubCells = false, TopCell = false });
            mod.Worldspaces.Add(w);
        }
        w.TopCell ??= win.TopCell!.DeepCopy(NoRefs);
        if (!LocalQuests.Masters.Contains(from)) LocalQuests.Masters.Add(from);
        return w;
    }

    // An exterior cell's override in its world's blocks (block = grid / 32, sub-block = grid / 8, rounded down).
    public static Cell Exterior(List<ISkyrimModGetter> mods, Worldspace world, FormKey cellKey)
    {
        foreach (var b in world.SubCells) foreach (var sb in b.Items) foreach (var c in sb.Items) if (c.FormKey == cellKey) return c;
        var cell = Survey.Winners<ICellGetter>(mods)[cellKey].rec.DeepCopy(NoRefs);
        var g = cell.Grid!.Point;
        short bx = (short)Math.Floor(g.X / 32.0), by = (short)Math.Floor(g.Y / 32.0), sx = (short)Math.Floor(g.X / 8.0), sy = (short)Math.Floor(g.Y / 8.0);
        var blk = world.SubCells.FirstOrDefault(x => x.BlockNumberX == bx && x.BlockNumberY == by);
        if (blk == null) { blk = new WorldspaceBlock { BlockNumberX = bx, BlockNumberY = by, GroupType = GroupTypeEnum.ExteriorCellBlock }; world.SubCells.Add(blk); }
        var sblk = blk.Items.FirstOrDefault(x => x.BlockNumberX == sx && x.BlockNumberY == sy);
        if (sblk == null) { sblk = new WorldspaceSubBlock { BlockNumberX = sx, BlockNumberY = sy, GroupType = GroupTypeEnum.ExteriorCellSubBlock }; blk.Items.Add(sblk); }
        sblk.Items.Add(cell);
        return cell;
    }

    // An interior cell's override (block = id % 10, sub-block = (id / 10) % 10).
    public static Cell Interior(SkyrimMod mod, List<ISkyrimModGetter> mods, FormKey cellKey)
    {
        foreach (var b in mod.Cells.Records) foreach (var sb in b.SubBlocks) foreach (var c in sb.Cells) if (c.FormKey == cellKey) return c;
        var cell = Survey.Winners<ICellGetter>(mods)[cellKey].rec.DeepCopy(NoRefs);
        int id = (int)cellKey.ID, bn = id % 10, sn = id / 10 % 10;
        var blk = mod.Cells.Records.FirstOrDefault(x => x.BlockNumber == bn);
        if (blk == null) { blk = new CellBlock { BlockNumber = bn, GroupType = GroupTypeEnum.InteriorCellBlock }; mod.Cells.Records.Add(blk); }
        var sblk = blk.SubBlocks.FirstOrDefault(x => x.BlockNumber == sn);
        if (sblk == null) { sblk = new CellSubBlock { BlockNumber = sn, GroupType = GroupTypeEnum.InteriorCellSubBlock }; blk.SubBlocks.Add(sblk); }
        sblk.Cells.Add(cell);
        return cell;
    }

    // The mod's override of a placed ref, if any step made one.
    public static IPlaced? Placed(SkyrimMod mod, FormKey key) => mod.EnumerateMajorRecords<IPlaced>().FirstOrDefault(r => r.FormKey == key);
}
