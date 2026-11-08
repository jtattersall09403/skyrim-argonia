using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;

// The slice's clean-ups (Phase 4 part B; adaptation.md §5 "The clean-up"; blocks.md W-ref removal and W-fixed): every
// world_edit_target of the slice's we.clean.* edits. "disabled: ..." is the placement's own override with the initially
// disabled flag (0x800), in its cell (the worldspace's persistent cell for a persistent ref); "fixed level: ..." is the
// placement's base overridden to a fixed level with PC-level-mult and the Stats template flag off (decision 0035), the
// level talk.md's rule gives: the base's own fixed level, or 5 where it levels with the player. Talkers left the
// clean-up (their rows were deleted from the story data with a note). Allocates no new form ids.
static class CleanUp
{
    public static readonly string[] Edits = ["we.clean.lilmoth", "we.clean.hereguardplantation", "we.clean.dock2", "we.clean.dock5",
        "we.clean.helstrom", "we.clean.village", "we.clean.blackrose", "we.clean.thorn1"];
    static readonly string Db = Path.Combine("story", "data", "db");
    static FormKey K(string k) => FormKey.Factory(k);

    public static IEnumerable<(string edit, string target, bool disable)> Targets() =>
        File.ReadLines(Path.Combine(Db, "world_edit_target.jsonl")).Where(l => l.Trim().Length > 0).Select(l => JsonDocument.Parse(l).RootElement)
            .Where(r => Edits.Contains(r.GetProperty("edit").GetString()))
            .Select(r => (r.GetProperty("edit").GetString()!, r.GetProperty("target").GetString()!, r.GetProperty("what").GetString()!.StartsWith("disabled:")))
            .OrderBy(t => t.Item1).ThenBy(t => t.Item2);

    public static void Add(SkyrimMod mod, List<ISkyrimModGetter> mods)
    {
        var placed = Survey.Winners<IPlacedGetter>(mods);
        var cells = Survey.Winners<ICellGetter>(mods);
        var npcs = Survey.Winners<INpcGetter>(mods);
        var world = mod.Worldspaces.First(w => w.FormKey == K("23D689:Black Marsh.esm"));
        var exterior = ExteriorCells(mods, world.FormKey);
        var noRefs = new Cell.TranslationMask(true) { Persistent = false, Temporary = false, NavigationMeshes = false, Landscape = false };
        var cellOf = File.ReadLines(Path.Combine(Db, "bmv_placement.jsonl")).Where(l => l.Trim().Length > 0).Select(l => JsonDocument.Parse(l).RootElement)
            .ToDictionary(r => r.GetProperty("id").GetString()!, r => r.GetProperty("cell").GetString()!);
        int off = 0, fixedN = 0;
        foreach (var (edit, target, disable) in Targets())
        {
            var key = K(target);
            var src = placed[key].rec;
            if (disable)
            {
                var mine = Existing(mod, key);
                if (mine == null)
                {
                    mine = (IPlaced)src.DeepCopy();
                    var cellKey = K(cellOf[target]);
                    if (exterior.Contains(cellKey))
                    {
                        if ((mine.MajorRecordFlagsRaw & 0x400) != 0) world.TopCell!.Persistent.Add(mine);
                        else Overrides.Exterior(mods, world, cellKey).Temporary.Add(mine);
                    }
                    else if (!cells[cellKey].rec.Flags.HasFlag(Cell.Flag.IsInteriorCell))
                    {   // an exterior cell of another BM&V worldspace (Helstrom is in BlackMarsh2)
                        var wk = mods.SelectMany(m => m.Worldspaces.Where(w => w.SubCells.Any(b => b.Items.Any(sb => sb.Items.Any(cc => cc.FormKey == cellKey))))).First().FormKey;
                        var w2 = Overrides.World(mod, mods, wk);
                        if ((mine.MajorRecordFlagsRaw & 0x400) != 0) w2.TopCell!.Persistent.Add(mine);
                        else Overrides.Exterior(mods, w2, cellKey).Temporary.Add(mine);
                    }
                    else
                    {
                        var c = Overrides.Interior(mod, mods, cellKey);
                        if ((mine.MajorRecordFlagsRaw & 0x400) != 0) c.Persistent.Add(mine); else c.Temporary.Add(mine);
                    }
                }
                mine.MajorRecordFlagsRaw |= 0x800;
                off++;
            }
            else
            {
                var baseKey = ((IPlacedNpcGetter)src).Base.FormKey;
                var n = mod.Npcs.FirstOrDefault(x => x.FormKey == baseKey);
                if (n == null) { n = (Npc)npcs[baseKey].rec.DeepCopy(); mod.Npcs.Add(n); }
                var pcMult = n.Configuration.Level is not INpcLevelGetter;
                n.Configuration.Level = new NpcLevel { Level = pcMult ? (short)5 : ((INpcLevelGetter)n.Configuration.Level).Level };
                n.Configuration.CalcMinLevel = n.Configuration.CalcMaxLevel = 0;
                n.Configuration.TemplateFlags &= ~NpcConfiguration.TemplateFlag.Stats;
                fixedN++;
            }
        }
        Console.WriteLine($"clean-up: {off} placements disabled, {fixedN} templated placements at a fixed level");
    }

    static IPlaced? Existing(SkyrimMod mod, FormKey key) => Overrides.Placed(mod, key);

    // The cells of a worldspace across the load order (an exterior cell's override goes in its worldspace's blocks).
    public static HashSet<FormKey> ExteriorCells(List<ISkyrimModGetter> mods, FormKey ws) =>
        mods.SelectMany(m => m.Worldspaces.Where(w => w.FormKey == ws)).SelectMany(w => w.SubCells).SelectMany(b => b.Items).SelectMany(s => s.Items)
            .Select(c => c.FormKey).ToHashSet();

    // cleancheck <Argonia.esp> <plugins...>: the read-back from the built plugin: every target of every slice clean-up is
    // overridden in Argonia.esp as its row says, and no target is a talker. Exit 1 on any failure.
    public static int Check(string esp, string[] paths)
    {
        var mods = Survey.Load(paths.Append(esp));
        var mine = mods[^1];
        var placed = mine.EnumerateMajorRecords<IPlacedGetter>().ToDictionary(r => r.FormKey);
        var npcs = mine.Npcs.ToDictionary(n => n.FormKey);
        var winners = Survey.Winners<IPlacedGetter>(mods);
        var talkers = File.ReadLines(Path.Combine(Db, "talk_line.jsonl")).Where(l => l.Trim().Length > 0)
            .Select(l => JsonDocument.Parse(l).RootElement.GetProperty("talker").GetString()!).ToHashSet();
        int fails = 0;
        foreach (var g in Targets().GroupBy(t => t.edit))
        {
            var bad = new List<string>();
            foreach (var (_, target, disable) in g)
            {
                var k = K(target);
                if (talkers.Contains(target)) bad.Add($"{target} is a talker");
                if (disable) { if (!placed.TryGetValue(k, out var r) || (r.MajorRecordFlagsRaw & 0x800) == 0) bad.Add($"{target} not disabled"); }
                else
                {
                    var b = ((IPlacedNpcGetter)winners[k].rec).Base.FormKey;
                    if (!npcs.TryGetValue(b, out var n) || n.Configuration.Level is not INpcLevelGetter
                        || n.Configuration.TemplateFlags.HasFlag(NpcConfiguration.TemplateFlag.Stats))
                        bad.Add($"{target} base {b} not at a fixed level");
                }
            }
            if (bad.Count > 0) fails++;
            Console.WriteLine($"{g.Key} {(bad.Count == 0 ? "PASS" : "FAIL")} ({g.Count()} targets: {g.Count(t => t.disable)} disabled, {g.Count(t => !t.disable)} fixed){(bad.Count > 0 ? ": " + string.Join("; ", bad) : "")}");
        }
        Console.WriteLine(fails == 0 ? "clean-up read-back: all PASS" : $"clean-up read-back: {fails} FAIL");
        return fails == 0 ? 0 : 1;
    }
}
