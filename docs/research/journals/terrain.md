# Journal: the terrain (chunk 2.W1)

What was tried, measured and learned for `tools/argonia_world/terrain/` and ArgoniaWorld.esm, so nothing is lost
at a hand-off. The lane reports are `docs/research/2026-10-29/lane-2.W1-terrain.md`.

## 2026-10-29: the data side (lane 2.W1-terrain, first context)

- **The frame.** Imported positions run x east and y SOUTH from the province's north-west corner. I measured
  this on the route-grade profiles: they sit on the heightfield at row = y / 1.82784 with a median error of
  0.23 m, against 21 m with y flipped. Row 0 of the heightfield is the north edge. `su.province_to_skyrim`
  converts; a plain `metres_to_units` on y mirrors the province north to south.
- **The grid.** One sample is 1.82784 m (hydrology `mpp`), which is 128 units, one LAND vertex. The province
  spans cells -62..63 on both axes, as the old ESP export's meta.json has it. The near apron is 68 cells beyond
  each side (the old apron-source-near pad of 2,176 samples).
- **VHGT, checked on 42 vanilla Tamriel cell pairs.** The offset is in 8-unit steps (0 seam this way, 973 units
  with the offset in units). Mutagen's HeightMap is [x, y], x east and y north from the south. A VTXT position
  is x + 17 * y: 0.003 mean quadrant-edge mismatch this way, 0.22 the other way. Vanilla uses at most 6 alpha
  layers per quadrant. VNML is signed bytes; flat ground is about (0, 0, 127).
- **The patch chain** verified by sha256: frozen 4a74.. -> 119 terrain patches applied, 47 refused -> 0248.. ->
  118 route-grade applied -> `refined-height-f32.npy` 638c... The result differs from frozen in 47,084 samples,
  all of them inside patch regions. The outcomes are now `terrain_patch_outcome` rows.
- **LTEX.** Skyrim.esm has 68. Tropical Skyrim (LE 33017 in the vault) replaces 66 of them, all but
  LMineFloorDirt01 and LScrub01. To re-check against SE 78044 when 0.2 syncs the masters.

## 2026-10-29: the limiter, the full run, the writer (continuation)

- **The limiter spreads locally.** The L-infinity midpoint of the 127-Lipschitz envelopes ramps a cliff at
  half the allowed slope, so a 1000-step jump moved vertices 5 samples away by 182 steps. The fix: pin both
  ends of every overflowing pair to the midpoint, and clamp every other vertex into the cone those pins allow.
  The ramp then runs at the full 127 steps per sample, centred on the cliff (0 0 0 0 0 0 55 182 309 436 | 563
  690 817 944 1000 ...). The result is 127-Lipschitz on every edge, and no vertex moves further than the
  midpoint would move it (tested on rough random ground).
- **The overflow survey** (raw quantised 4-neighbour steps over 127, province only): 23,880 pairs. 3,660 lie
  wholly under the sea, 8,940 are sea cliffs (bottom below 0, top above) and 11,280 are on land, in 674 cells.
  The steepest is 135.1 m in one sample. The worst cell is (-19, 58), with 177 pairs over -106..159 m. After
  the limiter, 53,748 province vertices differ from the heightfield by more than rounding (0.33 %): 47,637 by
  more than 0.5 m, 24,902 by more than 10 m, at most 60.4 m. Those are the cliff faces, which VHGT cannot
  store steeper than 82.9 degrees. Whether they read as cliffs at the play camera is an L4 still (terrain-vantage).
- **The full run.** 15,876 province cells plus 17,899 apron cells written, and 34,869 apron cells skipped as open
  sea under -2 m: 3 min 51 s, 684 MB peak. The L1 check over every cell takes 17 s at 109 MB.
- **ArgoniaGen world (LandWorld.cs).** Mutagen's default parallel writer peaked at 3.2 GB, because it buffers
  every block. `.SingleThread()` with a 1.5 GB heap limit and GCConserveMemory 9 peaks at 1.08 GB in 24 s and
  writes the same bytes (sha256 d7f6cb48..). That holds across four builds, both writers and `make plugin`.
  Vanilla facts copied: LAND DATA 0x1F, compressed; BTXT layer 0xFFFF; ATXT 0..n-1; VTXT only above zero;
  cells HasWater; the persistent top cell at 0, 0.
- **Border region.** Skyrim.esm's BorderRegionSkyrim (0C5859) has the BorderRegion major flag, one area with
  falloff 0 and 173 points, and a Map entry. Ours is one area over the province square; 2.W3 writes it in
  Argonia.esm.

## 2026-10-29: Tropical Skyrim SE re-check, records half (0.2 synced the masters)

- `Tropical Skyrim.esp` (SE, master Skyrim.esm only) overrides **22 LTEX** (their grass lists; the TXST links
  are unchanged) and 14 GRAS, and has no TXST. `Tropical Skyrim -- Birds.esp` has no LTEX.
- **13 of our 27 seed LTEX** get Tropical Skyrim's grass through these overrides: LCoastBeachGrass01 (an empty
  list), LDirt02, LFallForestDirt01, LFallForestGrass01, LFallForestLeaves01, LFieldGrass01, LFieldGrass02,
  LFrozenMarshDirtSlopes01, LPineForest02, LPineForest03, LReachDirt01, LReachMoss01 and LTundra01. The other
  14 keep vanilla Skyrim.esm's grass list.
- **Owed: the texture half.** Tropical Skyrim's texture files are not on the build VM: only the plugins and the
  mesh lists were synced, with no loose `textures/landscape` and no Tropical Skyrim BSA. The "replaces 66 of 68
  by file" finding still rests on the LE file list. The vantage stills (L4, on the game machine) settle it.

## 2026-10-29: no vanilla grass on the painted ground (planner's call on the re-check)

- ArgoniaGen `ltex` scans every LTEX's winning copy and every GRAS's plugins (out/ltex-scan.json: 143 LTEX, 97 GRAS,
  1.2 s). With the full load order, Depths of Skyrim wins 7 of our 27 forms (the underwater ones) with its own flora.
- Plan in the db: `grass_source` (Tropical Skyrim.esp; DepthsOfSkyrim.esp for underwater flora only, my call),
  `ltex_grass_plan` (27 rows, 6 bare on purpose), `ltex_grass` (51). Seeded as the winning list filtered to the
  sources; LFallForestDirt01 gets TropicalGrassPlant01 instead of going bare.
- Before: the check fails on 8 forms (FieldGrass02, FallForestGrass01/02, SnowGrass01, RockGrassWater01,
  WaterCoralGrass01). Argonia.esm now overrides those 8 LTEX (winner's fields, our grass list); after: 0. The
  test also fails once on purpose (a SnowGrass01 left in a marsh list).

## 2026-10-29: the vault's meta.json y-axis note is wrong

`$ARGONIA_DATA/terrain/meta.json` says "row 0 is the southernmost sample". It is the frozen vault's own file (not
ours to edit). Measured three ways, row 0 is the **north** edge: `terrain/grid.py`, the route-grade profiles
(0.23 m median error this way, 21 m flipped) and the chart's mirror test (flipped, Thorn lands in the sea). Trust
`grid.py` and `su.province_to_skyrim`, never that note.
