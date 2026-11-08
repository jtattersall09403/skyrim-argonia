using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;

// Skyrim's game music in BM&V's worlds (owner, walk 3, 2026-11-08: "turn on normal Skyrim game loop music for now").
// Measured (`plugin.sh musicprobe`, 2026-11-08): BM&V's five worlds carry no WRLD music (ZNAM) and none of their
// regions an RDSA music entry, so outdoors the engine has no exploration music type and plays nothing; their
// interiors mostly carry the author's XCMO (MUSDungeon, MUSDungeonFort, MUSTavern...) and are left alone; combat music
// is the engine's MUSCombat in any world. Bethesda's way for a whole separate world is Solstheim's: one exploration
// music type on the WRLD (DLC2SolstheimWorld ZNAM DLC2MUSExploreSolstheimGeneral), not a region per area as in
// Tamriel. So each BM&V world gets ZNAM from Skyrim's own types: the marsh music (Hjaalmarch's) for Black Marsh, the
// pine forest's for Valenwood, the cave dungeon's for the Underdark (as Blackreach carries a dungeon type). No new
// forms; Argonia music replaces these later.
static class Music
{
    static readonly (string world, string musc)[] Worlds =
    [
        ("23D689:Black Marsh.esm", "0C76D3:Skyrim.esm"),        // BlackMarsh: MUSExploreMarsh
        ("0D6960:Black Marsh.esm", "0C76D3:Skyrim.esm"),        // BlackMarsh2
        ("005900:Black Marsh North.esp", "0C76D3:Skyrim.esm"),  // BlackMarshNorth (Thorn)
        ("005900:Valenwood.esp", "06D546:Skyrim.esm"),          // Valenwood: MUSExploreForestPine
        ("0B8BDD:Black Marsh North.esp", "094BDD:Skyrim.esm"),  // UnderDark: MUSDungeonCave
    ];

    // Sets ZNAM on the worlds MapFix already overrides (extended, not duplicated), and adds the Underdark's override.
    public static void Apply(SkyrimMod mod, List<ISkyrimModGetter> mods)
    {
        var winners = Survey.Winners<IWorldspaceGetter>(mods);
        var musc = Survey.Winners<IMusicTypeGetter>(mods);
        foreach (var (key, m) in Worlds)
        {
            var fk = FormKey.Factory(key); var mk = FormKey.Factory(m);
            if (!musc.ContainsKey(mk)) throw new Exception($"music {mk} not in the load order");
            var w = mod.Worldspaces.FirstOrDefault(x => x.FormKey == fk);
            if (w == null)
            {
                w = winners[fk].rec.DeepCopy(new Worldspace.TranslationMask(true) { SubCells = false, TopCell = false });
                mod.Worldspaces.Add(w);
            }
            w.Music.SetTo(mk);
            Console.WriteLine($"music: {w.EditorID} -> {musc[mk].rec.EditorID}");
        }
    }

    public static void Probe(string[] paths)
    {
        var mods = Survey.Load(paths);
        var musc = Survey.Winners<IMusicTypeGetter>(mods);
        string M(IFormLinkGetter l) => l.IsNull ? "none" : musc.TryGetValue(l.FormKey, out var v) ? $"{v.rec.EditorID}({l.FormKey}, {v.from})" : $"?{l.FormKey}";
        foreach (var (fk, (w, from)) in Survey.Winners<IWorldspaceGetter>(mods))
            Console.WriteLine($"WRLD {fk}\t{w.EditorID}\twin={from}\tmusic={M(w.Music)}\tclimate={w.Climate.FormKey}\tparent={w.Parent?.Worldspace.FormKey}");
        foreach (var (fk, (r, from)) in Survey.Winners<IRegionGetter>(mods))
            Console.WriteLine($"REGN {fk}\t{r.EditorID}\twin={from}\tworld={r.Worldspace.FormKey}\tmusic={(r.Sounds == null ? "no RDSA" : M(r.Sounds.Music))}");
        foreach (var (fk, (m, from)) in musc)
            Console.WriteLine($"MUSC {fk}\t{m.EditorID}\twin={from}\ttracks={m.Tracks?.Count}");
        foreach (var m in mods)
        {
            var cells = m.Cells.SelectMany(b => b.SubBlocks).SelectMany(sb => sb.Cells).ToList();
            if (cells.Count == 0) continue;
            var by = cells.GroupBy(c => M(c.Music)).OrderByDescending(g => g.Count()).Take(6).Select(g => $"{g.Key} x{g.Count()}");
            Console.WriteLine($"CELLS {m.ModKey}\tinteriors={cells.Count}\t{string.Join("; ", by)}");
        }
    }
}
