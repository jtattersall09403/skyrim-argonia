# Journal: regions and roads (2.W3)

- **2026-10-29, first agent.** Data side: 48 regions over every cell, weather and object lists, climate; roads traced
  off their paint, the route graph in one component. The old raster was not in the vault, so each cell's class is
  reconstructed (0.758 leave-one-out).
- **2026-10-29, second agent.**
  - The records are written: Argonia.esm overrides REGN shells that live in ArgoniaWorld.esm, because the generated
    master's cells cannot link to their dependant (the shell pattern, added to decision 0031).
  - Weather values are ours, and only references come from the templates.
  - Roads are painted unbroken into the land cover.
  - Gates and landings are persistent refs, all pending their pieces.
  - The season rule is in ArgoniaCore.
  - Signpost arms name places, never junctions.
  - The old roads' extra length is mostly 8° grading round steep ground: our roads are straighter and 8.6% steeper
    than the cap. The next step is a slope cost in the trace.
  - Gate green.
- **2026-10-29, TS SE re-verification (masters landed).** Mutagen read of `Tropical Skyrim.esp` (SE; 70 TREE, 1 STAT,
  38 WTHR overrides; master Skyrim.esm only).
  - Of the 34 object forms (31 used by a region), all 28 TREE and the one branch-pile STAT are overridden. The three
    rock STATs (RockL01, RockL01Wet, RockPileL03FieldGrass01Moss) are not: TS carries no rock STAT. Kept as an
    intended exception (their `review` says so): a rock is not a Nordic tell by shape, and any TS rock restyle would be
    a mesh or texture file the synced Data does not show; owed to an L4 still of a rock, then swap or retexture.
  - Of the 17 weathers, 12 were overridden; five were not (OvercastRain, OvercastRainMA, StormRain, StormRainFF,
    FogCO), and our `storm` and `squall` templates copied the un-restyled StormRain. Now: `rain` is OvercastRainTU
    (`rain-ma` merged into it), `storm-rain` is StormRainTU (`storm-ff` merged into it), `fog-co` became `fog-vt`
    (FogVT), and the `storm` and `squall` templates are StormRainTU. TS has only two restyled rains and one restyled
    storm rain, so the groups now share them.
