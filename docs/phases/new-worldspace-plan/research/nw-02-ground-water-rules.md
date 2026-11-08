# nw-02 ground, road, water and mist rules: measured from the game and mod files

Measured 2026-11-08 on this machine from the Data folder plugins (Skyrim, Update, Dawnguard, HearthFires, Dragonborn, Black Marsh.esm, Black Marsh North.esp, Valenwood.esp, Tropical Skyrim.esp, King of the Murkmire.esp, DepthsOfSkyrim.esp), the vanilla BSAs and `~/.argonia/stack/MO2/mods/bmv`. Units: 70 game units = 1 m; a LAND vertex is 128 units = 1.83 m; a cell is 4096 units = 58.5 m. Every number below is from the query named beside it; the throwaway scripts are in the scratchpad `/tmp/claude-1000/-home-ubuntu-skyrim-argonia/2ee3ca29-72b5-4769-8ea6-ab96786a22d4/scratchpad` (`dump/Program.cs` is the Mutagen dumper; `lib.py lands.py tex.py geo.py refs.py edge.py a1*.py a2*.py a3.py` are the analyses). The scratchpad is session-scoped; the methods are written out in section 6 so the numbers can be rerun.

**Limits of this machine.** Tropical Skyrim, King of the Murkmire and Depths of Skyrim are present only as plugins (records) and as mesh path lists in `Data/argonia-mesh-lists/*.txt`; their meshes and textures are not on this disk, so "TS equivalent" below means a record or path match, and no TS/KoTM texture was looked at. Tropical Skyrim.esp is not in the staged load order (`~/.argonia/stack/MO2/profiles/Argonia/plugins.txt` lists Black Marsh.esm, Black Marsh North.esp, Valenwood.esp and the combat/magic mods only), so "vanilla" here is Skyrim+Update(+DLC) and TS is always shown separately.

## 0. Which live docs cover this, and what this confirms or changes

Covered already: `docs/phases/new-worldspace-plan/research/nw-02-salvage.md` (texture edges, water edge sequence, roads, WATR templates), `.../nw-02-flora-rules.md` (flora co-occurrence, water distance, seabed), `docs/research/skyrim/skyrim-does-it-this-way.md` (§7 weather, §8 mist), `.../terrain-measurements.md` (heights).

- CONFIRMED: Road surface meshes plus a trough, no crown (salvage "Roads"): the road meshes (section 2) sit at +0.0 to +0.2 m over the ground. `LRiverbedEdge01` hugs the water edge (White River: 0.42 weight 0-2 m inside the water line, 0.38 at 0-2 m on land, 0.24 at 2-5 m, 0.09 at 5-10 m; salvage says "+128 u" = 1.8 m, the band is about 5 m). Flat land textures from the water line: BM&V is uniform (section 4), which is the "swathes" failure the salvage doc names.
- CONTRADICTED: salvage "RoadChunk stones on the road (lateral p50 2.8 m, ~15 per 100 m)". `RoadChunk{S,M,L}0n` are road-surface patch meshes (same `Road01` texture and a ground-texture skirt; 1.2 m to 5.3 m across by NIF extent, section 2), not stones. The stones beside roads are `RockPile*` and `Rock{S,M,L}*` refs (section 2.4).
- CONTRADICTED (detail): salvage "paint full to 5 m, gone by 7 m". Measured under road meshes the painted ground layer stays at 0.97 to 3 m, 0.76 at 5 m, 0.56 at 6 m, 0.36 at 8 m from the spine, then plateaus at 0.3 (Rift, section 2.3): the ramp is 3.5 m to 8 m from the spine, and the road texture itself is not in LAND at all.
- CONTRADICTED (scope): skyrim-does-it-this-way §8 "placed mist is site dressing, never a regional layer". True over all Tamriel (476 mist refs, 2.6% of cells) but Hjaalmarch's marsh is a regional layer: 81 of the 476 mist refs (17%) sit in 58 marsh-water cells (0.5% of Tamriel's cells), 1.4 per cell, 408 per km2, nearest-neighbour spacing p50 31 m (section 5.2).
- SUPERSEDED: salvage item 9 says read WATR templates from "Tropical Skyrim DefaultWater 81,174,165 / 28,104,140". In the staged load order TS is absent, and the winner is Update.esm: `DefaultWater` shallow (38,39,24) deep (5,14,18), opacity 50, refraction 40, flowmap scale 1 (section 3.1). Using TS's turquoise water is a decision, not a template read.
- NEW (not in any doc): flowmaps are per-cell `textures\water\<plugin>\flow.<x>.<y>.dds` selected by the `EnableFlowmap` WATR flag (section 3.3); BM&V paints no texture progression at the water's edge at all (section 4.6); BM&V's swamp plant cover is placed reed statics, not GRAS (section 1.4).

The one doc to edit: `docs/phases/new-worldspace-plan/nw-02-textures-plants-scatter-water.md` (the phase file is the work; add the rule set of section 7 under its Water, Roads and Atmosphere headings). No new file.

## Rule set in brief (each rule is derived in the section named)

Textures (s1): paint every quadrant as a base plus alpha layers numbered up to 5, an LTEX on every layer (never texture 0). Target the vanilla mix (3.15 textures per quadrant; vertices 78% pure >= 0.95, 12% at 0.7 to 0.95, 11% below 0.7), because BM&V's 1.2 to 1.7 textures per quadrant and 87 to 95% pure vertices is what produces swathes of one texture; but take BM&V's softness of ramp: neighbouring grid points (1.83 m) differ by at most 0.4 in opacity at p99 and 0.06 to 0.09 at p90 (BM&V; vanilla's p99 is 1.0, i.e. it has hard steps on 5.5% of neighbour pairs), with 1.0 reached only in a core, 58 to 100 grid points per alpha layer. BM&V's own LTEX set carries the swamp look: forest floor `tundramoss01` (LPineForest05), swamp mud `rivermud` (LFieldGrassDUPLICATE003), wet black rock with moss `rocksgrasswater01` (LPineForest04/DUPLICATE004), dark dirt-grass `fielddirtgrass01` (01MOSS1); sand `Sand02/03/06`; rock `Apel_lh_rock_02`, `rm_rock02`, `mountainslab01/04`, `RedRock04`. BM&V's road textures are dark cobblestone (`road01`, `road01fallforest01`); its only dirt track is `dirtroad01`.

Roads (s2): a road is a chain of `Road*` surface meshes (6.9 m wide road-texture surface inside a 13.9 m ground-texture skirt; `RoadChunk*` are 1 to 5 m patches of the same surface) laid on ground painted with one dirt LTEX whose weight stays >= 0.97 to 3 m and falls to about 0.35 at 8 m from the spine. Clearance from the surface edge in the five vanilla regions: trees p5 2.3 to 4.1 m (p1 1.1 to 2.5), rocks p5 0.9 to 1.6 m, shrubs and flora may lap the edge (10 to 26% within 1 m, p5 0.3 to 0.7 m). Roadside dressing per km of road within 10 m of the edge: rock piles 27 to 73 (median 1.5 to 3.5 m out), boulders 19 to 77 (median 2.8 to 6.5 m), stone walls 0 to 38 and fences 0 to 52 (only where farms are), road signs 0 to 10 (median 0.7 to 1.0 m), cairns 1.4 to 6.3 (median 1.7 to 4.1 m). TS replaces trees, shrubs, ferns and flowers (67 base models) and 2 rock files, never walls, fences or signs.

Water (s3): one WATR per kind. Still black swamp: `MurkyWater` (BM&V's world water; shallow 26,19,19, deep 9,9,6, opacity 100, no flowmap). Green marsh: `DefaultMarshWater` / `DefaultMarshWaterTransition`. Sea: `DefaultWater` (Update: shallow 38,39,24 / deep 5,14,18) or TS's turquoise. Rivers: `RiverWaterFlow` (flag EnableFlowmap, `flow.x.y.dds` per cell) and the directional `RiverWaterFlowNE/NW/SE` types set the scroll vector (2.5 to 3 units/s); creeks: `CreekWaterFlow*` (opacity 0, pale shallow); ponds: `DefaultCreekWater` / `ClearInteriorWater*`. Water type is chosen per cell (XCWT) and per placed water Activator (WNAM), never per level; only 624 of Tamriel's 11,186 cells set one, and every BM&V cell uses the world default.

Water's edge (s4): vanilla marsh bank: mud (RiverMud01 0.21 to 0.52) under the water, DirtSlopes (0.55 to 0.59) at the line, MarshGrass rising from 0.13 at the line to 0.46 at 5 to 10 m, ice and lichen as accents; sea: beach texture underwater and ashore (0.57 -> 0.40 over the first 20 m inland) with ocean floor only 0.2 to 0.34 under the water; river: RiverbedEdge (0.24 to 0.42) in the bed margin and bank, RiverBottom in the bed. Scatter density rises to 2.0 to 2.8 per 100 m2 within 20 m of water against 1.3 to 1.5 further in (vanilla marsh/river), so dress the first 20 m.

Atmosphere (s5): BM&V uses the vanilla weathers (Update versions) through `BlackMarshClimate` (SkyrimFog 45, OvercastRain 20, StormRain 20, Cloudy 10, Clear 5); Valenwood: Clear 40, OvercastRain 20, StormRain 20, ClearVT 10, SovngardeFog 10. Morthal's ground mist is 124 permanent `FXMistLow*` statics at +2.1 to 2.6 m over the ground, scale 1.3 to 1.6, no enable parents. Community Shaders in the stack contains an Exponential Height Fog feature with per-weather overrides but it is switched off by our own ruling (it veiled the sky in round 5). The native way to a mist that is strong at dawn, burned off by noon and back at night is the weather's day/night fog slots plus the climate sunrise/sunset window (section 5.4).


## 1. Landscape textures

### 1.1 What exists (query: Mutagen dump of every LTEX, TXST, GRAS, MATT; `lib.py ltex()` joins LTEX -> TXST diffuse -> MATT -> GRAS list; full tables in Appendix A)

LTEX records per plugin: Skyrim.esm 68, Update.esm 15, Dawnguard 12, Dragonborn 11, **Black Marsh.esm 3, Black Marsh North.esp 17, Valenwood.esp 11** (31 BM&V LTEX), **King of the Murkmire 23**, **Tropical Skyrim 22** (every one an override of a vanilla LTEX that changes only the GRAS list), **Depths of Skyrim 8** (overrides that add seabed GRAS). GRAS records: Skyrim 27, Update 27, KoTM 36, Depths 23, TS 14, Dragonborn 3, Dawnguard 1.

**BM&V reuses vanilla editor IDs for different images.** Its LTEX are named `LPineForestDUPLICATE004`, `LFieldGrassDUPLICATE003`, `LDirt03` and so on, but their TXST diffuse is BM&V's own texture (the name tells nothing; resolve through the TXST). Examples (LTEX -> diffuse): `LPineForest05` (formkey 00C2B5) -> `TEXTUREPACK\landscape\tundramoss01.dds`; `LFieldGrassDUPLICATE003` (040BF7) -> `TEXTUREPACK\landscape\rivermud.dds`; `LPineForest04`/`LPineForestDUPLICATE004` -> `TEXTUREPACK\landscape\grass\rocksgrasswater01.dds`.

Looked at (contact sheet of the BMV loose DDS files, `~/.argonia/stack/MO2/mods/bmv/textures`): tundramoss01 olive-green moss; rivermud near-black mud; rocksgrasswater01 black wet rock with neon yellow-green moss; fielddirtgrass01 dark olive dirt-grass; darklandgrassrocks rocky dark grass; sand02/03 pale cream sand; sand06 brown rippled sand; road01 and road01fallforest01 **dark cobblestone paving**, not dirt; dirtroad01 gravel/dirt track; apel_lh_rock_02 dark pitted rock; rm_rock02 black cracked stone; redrock04 red cliff; mountainslab01 grey slab; lavaflow dark basalt. Every BM&V diffuse path resolves: 28 of the 31 as loose files in the bmv mod, 3 (`Landscape\PineForest03.dds` twice and `Landscape\CaveBaseGround01.dds`) from the vanilla BSAs (checked against the bmv file list and the BSA list).

### 1.2 BM&V's swamp / marsh / mud / forest floor / sand / road / rock textures (usage = layer count, base + alpha, in BlackMarsh + BlackMarsh2 + BlackMarshNorth; `a1b.py`)

| role | LTEX (formkey) | diffuse | material | uses | GRAS (vanilla list) |
|---|---|---|---|---|---|
| forest floor (the swamp ground) | LPineForest03 (013876, Skyrim) | `Landscape\PineForest03.dds` | Grass | 6682 | FernGrass01, SnowGrass01Forest |
| forest floor, mossy | LPineForest05 (00C2B5) | `tundramoss01.dds` | Grass | 3332 | FernGrass01, SnowGrass01Forest |
| wet black rock/moss | LPineForestDUPLICATE004 (01A632), LPineForest04 (00C2B6) | `rocksgrasswater01.dds` | Grass | 1620 + 72 | FernGrass01, SnowGrass01Forest |
| swamp mud | LFieldGrassDUPLICATE003 (040BF7) | `rivermud.dds` | Grass | 678 | FieldGrass01, FieldGrass02 |
| marsh dirt-grass | 01MOSS1 (226330) | `fielddirtgrass01.dds` | Grass | rare | none |
| dark grass/rock | LFieldGrassDUPLICATE002 (02CFD4) | `darklandgrassrocks.dds` | Grass | 345 | TundraGrass01, TundraGrass04 |
| meadow | LFieldGrass02 (01342A), LFieldGrass01 (013428) | `FieldGrass02/01.dds` | Grass / Sand | 889 / 385 | FieldGrass01/02 / TundraGrass01, 04 |
| sand | Sand (02CF4D), LDirtDUPLICATE003 (04FFF6), LPineForestDUPLICATE005 (040C05), LTundraDUPLICATE002 (04FFF7) | `landscape\sand\Sand03/06/02/06.dds` | Dirt/Grass | 129 / 194 / 173 / 134 | none (the last two carry Fern/SnowGrass/TundraGrass) |
| road (cobble) | 01road2 (01CD6B), 01road1 (01CD6A), LDirtDUPLICATE002 (0696E0) | `TEXTUREPACK\landscape\roads\road01.dds`, `road01fallforest01.dds` | Ash / Gravel / Dirt | 237 / 108 / 112 | none |
| road (dirt) | LFieldDirtGrassDUPLICATE002 (040C03) | `dirtroad01.dds` | Grass | 25 | none |
| rock | DarkRock1 (17678B), LDirt03 (01CD80), LDirtDUPLICATE004 (063472), LTundraRocksDUPLICATE002 (039829), LTundraRocks01 (02C6C6) | `Apel_lh_rock_02`, `vvardenfell\rm\rm_rock02`, `mountainslab04`, `RedRock04`, `TundraRocks01` | Dirt / Broken stone | 197 / 420 / 37 / 146 / 228 | RockGrass01 on the last two |
| volcanic/ash | LVolcanicAsh03 (017EA4 Dragonborn), lava (01CD47) | `DLC02\landscape\volcanic_ash_05`, `lavaflow` | Ash / Dirt | 171 / 81 | none |
| river bed / coast (vanilla, a few) | LRiverBottom01NoGrass 74, LCoastBeach01 69, LRiverMud01 25 + NoGrass 22, LRiverbedEdge01 9 | vanilla | Broken stone / Sand / Mud / Stone | | TBP* (Depths) on mud, beach, bed |

Valenwood adds `LDirtPathDUPLICATE002` (01CDF5) -> `Lor\landscape\cobblestone01.dds` (cobble road, 549 uses), `LDirtDessert` and `...DUPLICATE001` -> Sand06/Sand03, `LDirtDUPLICATE004/005/002/003` -> LERock17 / mountainslab01 / LERock30 / LERock06 (Appendix A part B).

**TS adds to the GRAS list of vanilla LTEX** (Appendix A part D): LPineForest03 +FallForestGrass02, TropicalGrass01, TropicalGrassPlant01; LFieldGrass02 +TropicalGrassPlant01/02; LFrozenMarshDirtSlopes01 +CattailGrass01 (dens 30, BelowAtLeast 0 = grows in the water, the one TS reed); LTundra01/LFieldGrass01 +RockGrass01; LFallForest*/LReach*/LSnow* +TropicalGrass*. **KoTM LTEX** (23, Appendix A part C) are the Argonia marsh set: LALPAMud01 (`argonia\landscape\rivermud`), LALPAMud01Reeds (4 `EWpShore07` reed GRAS), LALPAMud01WildSaltrice, LALPAMarshGrass (`CTQ_Grass_Lush01`; fern, ram's, nettle, lupin), LALPARainforest (`CTQ_Undergrowth_01`), LALPARiverBottom01 (kelp + RockGrassWater01), LALPAMudSand01 (`_ResourcePack\Landscape\SandWet01_d`), LALPAMarshMud01Road. **Depths LTEX overrides** (8): coast/river bed LTEX gain the `TBP*` GRAS (kelp, coral, seaweed, algae, driftwood, `UnitsFromWater` 50 to 1000 below the surface, `BelowAtLeast`).

GRAS facts used by the swamp (query `out/gras_table.txt`): FernGrass01 `ferngrass01.nif` density 37 slope 0-50; SnowGrass01Forest `SnowGrass01.nif` density 30 slope 0-48; FieldGrass01 density 64, FieldGrass02 density 20 (slope 0-45); TundraGrass01/03/04 density 4/3/5 slope 0-14/19; FrozenMarshGrass01 `MarshGrassObj01` density 60; CattailGrass01 density 30; KoTM reeds density 40 `EitherAtLeast` 0 (both sides of the water line); RockGrassWater01 density 20 `BelowAtLeast` 105 units (1.5 m under water).

### 1.3 How BM&V layers each LAND quadrant (query: Mutagen LAND layers (BTXT base + ATXT/VTXT alpha) of every cell; `a1.py`, `a1b.py`, purity test in section 6)

A quadrant is a 17 x 17 grid (spacing 1.83 m). One base layer plus alpha layers numbered 0..5; each alpha layer lists only its non-zero grid points with opacity 0..1.

| world | quadrants | alpha layers per quadrant 0 / 1 / 2 / 3 / 4 / 5 | mean textures per quadrant | alpha peak p50; layers peaking >= 0.95 | vertices with one texture >= 0.95 / 0.7-0.95 / < 0.7 | adjacent-point opacity step p50 / p90 / p99; share of steps > 0.5 | alpha points per layer p50 |
|---|---|---|---|---|---|---|---|
| BlackMarshNorth | 10,932 | 7810 / 2125 / 661 / 227 / 72 / 37 | 1.42 | 0.65; 36% | 93 / 5 / 2 % | 0 / 0.06 / 0.35; 0.5% | 67 |
| BlackMarsh | 4,508 | 3302 / 1018 / 138 / 32 / 14 / 4 | 1.33 | 0.95; 51% | 95 / 3 / 2 | 0 / 0.08 / 0.41; 0.6% | 58 |
| BlackMarsh2 | 12,920 | 10244 / 2363 / 282 / 29 / 2 / 0 | 1.22 | 0.91; 49% | 95 / 4 / 2 | 0 / 0.09 / 0.31; 0.3% | 72 |
| Valenwood | 13,760 | 6794 / 4458 / 1861 / 514 / 93 / 40 | 1.73 | 0.67; 36% | 87 / 9 / 4 | 0 / 0.06 / 0.38; 0.6% | 63 |
| KoTM ArgoniaWorld | 63,724 | 49548 / 8945 / 3528 / 986 / 462 / 255 | 1.37 | 1.00; 61% | 94 / 4 / 2 | 0 / 0.08 / 0.69; 1.8% | 70 |
| vanilla Tamriel | 44,744 | 13652 / 6420 / 5725 / 5505 / 5203 / 7867 (+372 with 6) | 3.15 | 1.00; 80% | 78 / 12 / 11 | 0 / 0.23 / 1.00; 5.5% | 52 |

Reading: BM&V and KoTM paint sparsely (1.2 to 1.7 textures per quadrant, 71% of Black Marsh North quadrants have no alpha layer) with soft ramps; vanilla paints 3.15 textures and has hard steps at p99 (opacity 0 to 1 between neighbouring points) on 5.5% of neighbour pairs. Skyrim's soft look comes from the 4 to 6 layers, not from every ramp being soft. In BM&V a quadrant's ground is mostly one texture: `LPineForest05` is the base of 2,527 of 10,932 Black Marsh North quadrants (23%), `LPineForest03` of 3,645 of 12,920 BlackMarsh2 quadrants (28%) and 1,524 of 4,508 BlackMarsh quadrants (34%). That uniformity is exactly the "large swathes of identical texturing" failure; the opposite fix is the vanilla 3-layer quadrant. ATXT texture 0 ("Null" in Mutagen) is 8.2% of vanilla ATXT by a raw read (2,633 of 31,952 in the first 3,000 Skyrim.esm LAND) and 28% of Black Marsh North's alpha layers (1,302 of 4,601), 45% of BlackMarsh's (665 of 1,466), 50% of BlackMarsh2's (1,515 of 3,022), 25% of Valenwood's (2,620 of 10,294), 26% of KoTM's (5,635 of 22,082) and 10% of Tamriel's (9,676 of 96,764): texture 0 is the engine's default dirt, used as an erase layer; our tool must write real LTEX.

Typical BM&V alpha pattern (ArgoniaWorld/BM&V example read from the dump): an alpha layer lists 58 to 100 of the 289 grid points; opacity 1.0 sits in a core of a few points and falls over 1 to 3 points to under 0.1 (e.g. `... 0.84 1.00 1.00 0.34 0.18 0.34 ... 0.04 0.02`). Vanilla's first Tamriel quadrant has a Null layer 0 at 1.0 over the core and soft layers (0.58, 0.43, 0.26 ...) at its flanks.

### 1.4 What gives BM&V its swamp cover (query: placed refs by model, `a2c.py`, `edge_*`)

- BM&V BlackMarsh: **7,153 `landscape\grass\vurt_reeds.nif` statics (`001reed`), 704 `waterkelpshort01`, 533 `waterkelptall01`**, none of them grass; BM&V's reed/kelp are refs, so GRAS is only FernGrass01/SnowGrass01Forest on the moss.
- BlackMarsh2: 1,412 `FXFog01`, 994 `vurt_reeds`, 556 `FXMistLowSwirls01`, 791 yellow mountain-flower statics (see section 5).
- BM&V inland water bands carry `gkblillipad2` (0.13 to 0.37 per 100 m2 in 5 to 20 m of the water band), `kelptallstatic01aaa` 0.03 to 0.07, swordfern clusters 4 to 8 per 100 m2 on BlackMarsh ground (section 4).

## 2. Roads

### 2.1 What a Skyrim road is (queries: Tamriel refs whose model is `meshes\landscape\roads\*`; NIF vertex decode; `a2*.py`, `nif.py`)

A road is a chain of static meshes from `Meshes\Landscape\Roads\` (30 files; 5,508 placed in Tamriel, 6,466 in all six worlds: Tamriel 5,508, BlackMarshNorth 572, Valenwood 295, KoTM 71, BlackMarsh 20). Each NIF has two BSTriShapes and one collision body: shape `:0` is the **road surface** with `textures\landscape\roads\Road01.dds`, shape `:2` is a **skirt** that carries the ground texture (`landscape\Dirt02.dds` by default) and dips below the terrain at its edge (z from +8 at the centre to -27 and -37 units at the rim). Extents of `RoadStraight01`: surface 481 units (6.9 m) wide x 722 long, skirt 972 x 1024 (13.9 m x 14.6 m), surface z +1.2 to +15.7 units (0.02 to 0.22 m), vertex alpha 255 (no vertex fade: the fade is the skirt sinking into the terrain). The ref stores alternate textures: slot `:0` swaps the road texture, slot `:2` swaps the ground texture.

Variants by base editor ID (alt-texture TXST):
- plain `Road*`: `Road01.dds` + `Dirt02.dds`
- `...Snow`: `TextureSetRoad01Snow01` (`Landscape\Roads\Road01Snow01.dds`) + `Landscape\Snow01Landscape.dds`
- `...FallForestDirt01`: `Road01FallForest01.dds` + `Landscape\FallForestDirt01.dds`
- `...ReachDirt01`: `Road01Reach01.dds` + `Landscape\ReachDirt01.dds`
- `...CaveDirt`: Dirt variant for cave mouths.
Piece sizes (surface extent in units, /70 for m): `RoadChunkS01..04` 68-87 x 50-72 (1.0 to 1.2 m), `M01..04` 164-422 x 72-159 (2.3 to 6.0 m x 1.0 to 2.3 m), `L01..03` 208-269 x 287-368 (3.0 to 3.8 m x 4.1 to 5.3 m); `RoadStraight01/02`, `RoadStraightLong01/02` (12 to 25 m long), `RoadCurve90R01`, `RoadCurveLong45*`, `RoadSCurve*`, ramps and `Road3way01`.

Counts by variant in the five vanilla regions (cell boxes: Whiterun x1..14 y-9..3; Rift x36..55 y-35..-14; Falkreath x-6..12 y-28..-14; Hjaalmarch x-14..0 y13..26; Pale x3..20 y22..38): Whiterun 379 pieces (360 plain, 19 curve/ramp); Rift 284 (264 `...FallForestDirt01`, 11 curve, 8 ramp, 1 plain); Falkreath 915 (803 plain, 72 Snow, 40 curve, ramp and snow-curve); Hjaalmarch 137 (75 plain, 61 Snow, 1 curve); Pale 37 (all Snow).

### 2.2 BM&V and KoTM road texture

BM&V's roads are painted in LAND, as cobblestone: `01road2` (road01.dds) and `01road1` (road01fallforest01.dds) in Black Marsh, `LDirtPathDUPLICATE002` (cobblestone01.dds) in Valenwood; only 25 layers use the dirt track `dirtroad01`. BM&V places 572 vanilla road meshes in Black Marsh North and 295 in Valenwood, mostly inside towns; KoTM places 71 and has `LALPAMarshMud01Road` (11BA25) as its road LTEX. Painted-road edge in BM&V (raster of the road-LTEX weight on the LAND grid, `edge`/`rast.py`): the core (>= 0.8) falls to a weight of 0.22 (Black Marsh North), 0.16 (BlackMarsh) or 0.13 (BlackMarsh2) one grid step (1.8 m) outside, and to 0.01 or less at 3.7 m: a 2 m edge, against vanilla's 5 m ramp. Core width p50 7.3 m in BlackMarsh2 (11 m in Black Marsh North, which includes plazas).

### 2.3 How the road texture fades into the land (query: LAND layer stack sampled at the spine and 1 to 12 m either side of 400 straight road pieces per region, `a2d.py`; stack rule: base weight 1, each alpha layer o replaces (1-o) of what is under it)

| from spine | Rift (FallForest) | Falkreath | Hjaalmarch | Pale | Whiterun |
|---|---|---|---|---|---|
| 0 m | FallForestDirt01 1.00 | LDirt02 0.60, LSnow01 0.20, no-BTXT 0.14 | LSnow01 0.80, no-BTXT 0.13 | LSnow01 1.00 | no-BTXT 0.44, LDirt02 0.34, Null 0.21 |
| 3 m | 0.97 | LDirt02 0.46 | LSnow01 0.81 | LSnow01 0.98 | LDirt02 0.32 |
| 4 m | 0.90 | 0.36 | 0.79 | 0.96 | 0.29 |
| 5 m | 0.76 | 0.24 (LPineForest02 0.14) | 0.75 | 0.92 | 0.23 |
| 6 m | 0.56 | 0.13 | 0.69 | 0.86 | 0.15 |
| 8 m | 0.36 (GrassNoFern 0.23) | < 0.09 (LSnow01 0.25) | 0.51 | 0.67 | 0.07 |
| 12 m | 0.31 | LSnow01 0.30, PineForest02 0.18 | 0.42 | 0.60 | LFieldGrass01NoGrass 0.26 |

The painted layer under a road is the region's own dirt texture (LDirt02 in the Whiterun and Falkreath tundra/forest, FallForestDirt01 in the Rift, snow in the Pale), not a road LTEX; "no-BTXT" is a quadrant without a base layer (engine default dirt, matching the mesh skirt's default `Dirt02`). It hands over to the surrounding vegetation LTEX between 3.5 m and 8 m from the spine (the mesh surface edge is at 3.45 m, the skirt rim at 6.9 m). The grass GRAS of the vegetation LTEX therefore starts about 4 m outside the surface edge.

### 2.4 Roadside dressing (query: for each of the five regions, every non-disabled ref (Skyrim.esm/Update placement, vanilla base model) in the road cells; distance = nearest road-surface vertex of the placed `:0` shapes (transform: x' = x cos t + y sin t, y' = -x sin t + y cos t, validated by the surface-to-LAND height spread, 35 vs 61 units for the other sign); counts within 10 m of the road surface; road length = union area of the surface vertices on a 2 m raster / 6.9 m: Whiterun 2.3 km, Rift 2.1, Falkreath 4.0, Hjaalmarch 1.6, Pale 0.5; `a2e.py`, `a2b.py`) 

Per km of road within 10 m of the surface, [median distance from the surface edge in m], and the base editor IDs (vanilla model path; TS has no replacement for any of them):

| category | Whiterun | Rift | Falkreath | Hjaalmarch | Pale | vanilla models |
|---|---|---|---|---|---|---|
| rock piles | 55.5 [2.2] | 34.7 [3.5] | 72.7 [2.1] | 27.5 [3.2] | 25.3 [1.5] | `landscape\rocks\rockpiles01..04.nif`, `rockpilem01/02`, `rockpilel01..04` (RockPileS0n, RockPileM0nFieldGrass01, RockPileL0nTundraRocks01) |
| boulders | 76.9 [3.7] | 26.5 [5.2] | 67.5 [3.8] | 19.4 [6.5] | 19.0 [2.8] | `landscape\rocks\rocks01..03`, `rockm01..04`, `rockl01..05` (TS replaces `rock.nif` and `rockl01.nif` only) |
| cairns | 1.8 [4.1] | 1.4 [2.8] | 2.5 [2.4] | 3.1 [1.7] | 6.3 [3.3] | `landscape\rocks\cairns\rockcairn04.nif` (and 01..03) |
| cliff and dirt-cliff pieces | 15.1 [7.2] | 16.4 [6.3] | 14.2 [6.8] | 3.7 [8.2] | 4.2 [5.7] | `landscape\rocks\rockcliff0n`, `landscape\dirtcliffs\dirtcliffs01/03`, `...cornerout01` |
| stone walls | 0 | 6.3 [1.2] | 16.2 [1.3] | 25.6 [3.3] | 38.0 [1.6] | `architecture\farmhouse\stonewall\stonewall01/02`, `stonewallendl01/r01` (StonewallEndL01 51, EndR01 49 in 10.4 km) |
| fences | 52 [5.2] | 0 | 1.0 | 0 | 35.8 [2.9] | `architecture\whiterun\wrfarmfence\*`, `architecture\farmhouse\fencewoven01/02` (farms only) |
| road signs | 9.8 [1.0] | 4.8 [0.7] | 4.0 [0.8] | 0 | 0 | `clutter\signage\roadsigns\roadsignpost.nif`, `RoadSign<Town>01L/R` (RoadSignPost 10, Whiterun/Riften/Windhelm/Solitude signs; all within 1 m of the edge) |
| lamps, lanterns, braziers | 4.9 [2.5] | 6.7 [5.0] | 3.2 [1.9] | 1.9 | 0 | WRBrazier01, CandleLantern, `clutter\lantern*` (town-edge) |
| carts, wagons, hay | 4.4 [6.3] | 7.2 [2.9] | 5.7 [5.2] | 0 | 14.8 [5.5] | `clutter\carts\handcart01wheel.nif`, `clutter\hay\haybale01.nif` |
| barrels, crates, sacks | 8.4 [7.5] | 18.8 [5.9] | 3.2 [0.4] | 1.2 | 21.1 [8.1] | `clutter\barrel01/02.nif` |
| logs, stumps | 15.1 [5.6] | 14.0 [4.3] | 34.1 [5.2] | 24.3 [5.4] | 10.5 [8.6] | `landscape\trees\*log*`, `reachtreestump01` |
| snow drifts | 0 | 0 | 5.5 [5.1] | 25.0 [2.4] | 25.3 [3.3] | `landscape\snowdrifts\snowdriftl01..03`, `m01/02` |
| ruins, rubble, towers | 116 | 132 | 77 | 48 | 89 | include Helgen/imperial ruin and quest rubble; not a road rule |
| vegetation per km (landscape trees / landscape shrubs+ferns / flora) | 38 / 335 / 119 | 179 / 368 / 94 | 123 / 331 / 74 | 116 / 337 / 92 | 70 / 257 / 70 | background |

Enrichment: of 10.4 km of road, within 10 m of the surface the refs for `RockPileS02` are x6.7 (112 vs 16.7 expected at the 30-60 m background density), `RockPileS01` x3.7, `RockPileS03` x3.9, `RockPileS04` x5.2, `StonewallEndL01/R01` x14.7, `StockadeWoodbeamShort01` x180 (Helgen quest set, ignore). `RockL01/L02/M01/M02/S0n` are x1.5 to 2.2: they are near-uniform with the background, only 1.5 to 2 times denser than 30 to 60 m out. So the **rock pile is the roadside marker** (3 to 7 times background), boulders just follow the terrain.

Vegetation near the edge (`a2f.py`; share of refs closer than 1 m / 3 m to the surface, and p5 distance): trees 0 to 0.9% / 2.9 to 7.7%, p5 2.3 to 4.1 m (p1 1.1 to 2.5 m); landscape shrubs and ferns 8.9 to 23.8% / 21 to 48%, p5 0.3 to 0.7 m; flora (`plants\*`) 10.7 to 26% / 21 to 52%; rocks 0.6 to 6.8% / 9.6 to 25%, p5 0.9 to 1.6 m. Vanilla does not keep shrubs off the verge; it keeps trees at least about 2.5 m from the surface edge.

TS equivalents (`out/ts_map.txt`: base editor ID -> vanilla model -> TS model, 67 rows, Appendix C): TS repoints `TreeThicket01` (12,134 refs in Tamriel) to `plants\tropical\manfern.nif`, `TreeThicket01Snow` to `plants\tamira\new plants\bush03b.nif`, `TreeDeadShrub` to `landscape\trees\tropical\fanpalm4.nif`, pine forests 01..05 (and Snow, SnowL, Dead) to `gkbjungletreenew*`, `gkbtreeaspen*`, `anvil_palm_trunk`, `anvilgianttrunk`, `mangrovereachtree0gkb2/3/8/9`, `gkbtreeofwolene`, Reach cliff trees to `gkbreachclifftree01/02`, `ReachBranchPile02` to `gkbreachbranchpile02`, `ReachTreeStump01` to `gkbreachtreestump01`, Aspens to `gkbtreeaspenbamboo*`/`citsflorabamboo01`, Reach shrubs to `palmtree4`/`gkbjungletreenew2v2`, `TreeFloraMountainFlower02Blue/Purple` to `plants\tamira\new plants\bush03b/03a.nif`. The TS mesh list (`argonia-mesh-lists/tropical-skyrim-sse.txt`, 1,588 meshes) has 783 under `landscape\trees`, 689 terrain LOD (`terrain\tamriel\objects\*.bto`), 30 `landscape\grass`, 20 `plants\tamira`, and exactly 2 rocks (`rock.nif`, `rockl01.nif`; the previous audit found `rockl01.nif` has a bird-feather texture): **no TS rock, cairn, wall, fence, sign or cliff piece exists**. "Tropical cliff meshes" = `gkbreachclifftree01..04` (12 files), which are cliff-edge trees, not rock faces. BM&V supplies the rock side: `meshes\landscape\rocks\` has 312 NIFs (`cliffs` 69, `rmrocks` 60, `marocks` 34, `wgrocks` 33, `rm_rocks` 27, `azrocks` 26, `alrocks` 19 including `al_cairn01..03`, `glrocks` 16) including mossy `moss_rockl05`, `moss_rockm01`, `moss_rockcliff01/03..07`, `moss_rockpiles02/04`, `black_rockm01`; 31 fence files, 56 stone-wall files, 101 road-sign files (`roadsign*`), 19 cart files, `architecture\phitt\aldredanyia\signpost.nif` (the signpost BM&V itself places beside its roads: 9 within 10 m of the Black Marsh North road surface, median 0.4 m); KoTM adds `argonia\clutter\fencewoven01/02`, `saxhleelfence01/02`, 18 `mwimparchstonewall*`, 20 cliff LODs.

BM&V's own roadside (query `a2c.py`, within 10 m of the road surface): Black Marsh North's roads are inside Dres villages (windows, houses, planters, `01fence` 13 refs, median 0.9 m; `signpost` 9; `paperlanternsquare` 9 `01housedreslamp`, median 0.3 m); Black Marsh shows shack parts; Valenwood: `01bosmerfence` 52, `01elvenbraizer` 38, `01elvenlamp` 33, `01signpost` 31, `CandleLantern` 31 within 0.3 to 0.8 m: BM&V's roadside is lamps, signposts and fences at town entrances, with no rock dressing.

## 3. Water

### 3.1 Every WATR (query: Mutagen WATR dump of 64 unique records across all plugins; Appendix B, columns as the record: shallow/deep/reflection RGB, opacity, fog above/under water near/far amount, refraction, reflectivity, fresnel, flowmap scale, linear velocity vector)

Flags seen: 0 (everything), `CausesDamage` (Apocrypha), `EnableFlowmap` (Update.esm `RiverWaterFlow` 001232, `RiverWaterFlowBlend` 001233, `DefaultWaterFlow` 001234, `DefaultWaterFlowBlend` 001235; KoTM `BlackmarshRiverWaterFlowNE/NW/SE/SW/Blend`), `BlendNormals` (the "Blend" types). WATR records per plugin: Skyrim 34, Update 38 (4 new, the rest overrides), Dawnguard 11, Dragonborn 7, KoTM 8, TS 4 overrides (DefaultWater, DefaultMarshWater, DefaultMarshWaterTransition, DefaultVolcanicWater), Depths 0 and BM&V 0 (Depths' seabed is GRAS and refs only); 64 unique forms.

Key records (RGB; opacity; fog-above far; refraction; reflectivity):
- `DefaultWater` 000018: Skyrim shallow (37,52,37) deep (5,16,5) op 30; **Update.esm shallow (38,39,24) deep (5,14,18) refl (119,140,157) op 50 refr 40 flowmap 1** (this is the stack's sea); TS shallow (81,174,165) deep (28,104,140) op 30 fog 580 refl 0.5 (turquoise).
- `MurkyWater` 062A72 (**BM&V's world water**): shallow (26,19,19) deep (9,9,6) refl (32,35,27) op 100, fog-above 0-60 amt 0.75, fog-under -1000/1000, refr 35, reflectivity 0.55, fresnel 0.25, noise amp 0.86/0.67/0.75, linear velocity 0, no flow.
- `DefaultMarshWater` 105CC3 (Hjaalmarch): shallow (37,52,37) deep (5,16,5) refl (103,122,117) op 30, fog-under -10000/1000, reflectivity 0.23, wind speed 0.007 x3; TS (56,53,37)/(77,61,36) brown. `DefaultMarshWaterTransition` 105CC4: same colours, fog-under -4000/1200 (the edge type next to sea/land, 13 Tamriel cells).
- `DefaultRiverWater` 105CE1, `RiverWaterFlowNE/NW/SE` (0E717C, 1063AA, 108AC7): shallow (38,39,24) deep (5,14,18) refl (119,140,157) op 50, fog 150, refr 40, reflectivity 0.8, noise amp 0.90/0.92/0.65, velocity NE (2.54,1.35), NW (-1.96,2.0), SE (1.8,-2.2), wind speeds 0.09/0.04/0.3.
- `CreekWaterFlow` 015429 (and SE/SW 106A20/106A24, `DefaultCreekWater` 015427): shallow (71,78,67) deep (35,35,24) refl (71,92,116) op 0 (clear), fog 160, refr 8; `CreekWaterFlowSE` (0.70,-0.72), `SW` (-0.98,-0.70).
- `RiftenWater` 0F2407 (lake): (36,53,39)/(16,15,5), op 30, fog-under -10000.
- Ponds/interior/clear: `ClearInteriorWaterAnkleHeightStill` (67,80,70)/(36,47,38) op 0; `WRWaterType` same family; `HelgenWater` (53,49,36); `PuddleWater` (11,13,12) flowmap 1.
- Cold, volcanic, blood, lava: `DefaultWaterCold` (45,94,96)/(31,55,58); `DefaultVolcanicWater` (130,116,34)/(61,95,52) (identical colours to KoTM's `DefaultBlackmarshWater`); `LavaWater`; `DLC1BloodWater`.
- **KoTM**: `DefaultBlackmarshWater` 184260 (130,116,34)/(61,95,52) op 30 flowmap 1; `BlackmarshRiverWaterFlow{NE,NW,SE,SW,Blend}` 323837-32383B, same colours as vanilla RiverWaterFlow but yellow-green (130,116,34)/(61,95,52), flags EnableFlowmap; `DefaultHistSapWater` (162,82,2) orange, `DefaultIchorWater` (37,126,64).

### 3.2 Which water each world and cell uses (query: CELL XCWT, XCLW, flags for all exterior cells; Activator WNAM; `cells.tsv`, `actiwater.tsv`)

- **BlackMarsh, BlackMarsh2, BlackMarshNorth: world water `MurkyWater` (062A72), LOD water the same, default water height 0 for every cell (cells with XCWT: 0, with XCLW: 0)**. Sea, swamp, lagoon and river are all `MurkyWater`. The wave/shore dressing is placed: `Water1024Murky` x22 (BMN), `Water1024Marsh` x3 + `Water1024CreekFlowSE` x1 (BlackMarsh2), `DLC2OceanWavesStraight` x23 and `OceanWaveCurveOuter` x4 (BlackMarsh), FXWaterfall pieces (BMN 22+20+10+5; BlackMarsh 110+63+21+6; BlackMarsh2 201+31).
- **Valenwood**: world water `DefaultWater` (000018) -> Update version (shallow 38,39,24); placed activators `Water1024Marsh` 73, `Water1024River` 32, `Water1024Creek` 29, `Water1024CreekFlow` 14, `Water1024Murky` 19, `Water1024Cold` 12, `Water1024RiverFlowNW` 8, `TundraStream*` 4, `DLC2OceanWavesStraight` 31, `OceanWaveCurveOuter` 26.
- **KoTM ArgoniaWorld**: world water `RiverWaterFlowSE` (108AC7, flowing!), with 26 `DefaultVolcanicWater` cells and 26 `DefaultIntWaterWaistHeightStill` cells; the Blackmarsh WATR records are defined but no cell links them; placed: `Water1024DefaultIntWaistStill` 86, `TundraStreamTransition01Mud` 15, `TundraStreamBend/Straight` 23, `Water1024Volcanic` 8, `Water1024HistSap` 3.
- **Vanilla Tamriel**: world `DefaultWater` at -14000; 11,186 cells with the water flag, **only 624 name a water type** (RiverWaterFlow 417, RiverWaterFlowNE 46, DefaultMarshWater 45, DefaultVolcanicWater 39, RiverWaterFlowNW 25, CreekWaterFlowSW 15, DefaultWaterFlowBlend 13, DefaultMarshWaterTransition 13, RiverWaterFlowSE 5, DefaultCreekWater 2, MurkyWater 2, ...). Heights: 10,455 cells use the default -14000, the rest carry XCLW (rivers and lakes: 10624 x86 cells (the Rift lakes), 600 x51, -7700 x29, -8300 x26, -5050 x21...). Lakes are `DefaultWater` at their own XCLW (Lake Ilinalta: cells x 8..9, y -24..-23, height 12608, no XCWT). Marsh/Hjaalmarch: 45 `DefaultMarshWater` + 13 `...Transition` cells (x -15..-4, y 14..23, default height).

### 3.3 How vanilla makes water flow, versus still (queries: WATR flags, per-cell types, BSA `textures\water`, placed FX refs by count)

Flow is built from four layers:
1. **The type's velocity vector** (`LinearVelocity` in the WATR DNAM) scrolls the three noise layers: still types 0 or 0.2; river types 1.8 to 2.5 units/s (`RiverWaterFlowNE` (2.54,1.35), `NW` (-1.96,2.0), `SE` (1.8,-2.2)); `DLC1WaterFastFlow` (3,-3). The directional types NE/NW/SE/SW exist because the vector is fixed per type; a river that turns changes type per cell.
2. **The cell chooses the type** (XCWT) and height (XCLW). River cells in Tamriel: 417 `RiverWaterFlow` + 46 NE + 25 NW + 5 SE + 13 `DefaultWaterFlowBlend`; creeks: 15 `CreekWaterFlowSW` + 1 SE. Small bodies are Activators with a WNAM water type and a water mesh: `Water1024X` (a 1024-unit quad = 14.6 m), `Water2048`, `TundraStreamStraight01WaterA/B`, `TundraStreamBend01WaterA/B` (CreekWaterFlow), `WRStairsStream*` (WRWaterFlow), `Water1024RiverFlowNE/NW/SE` (61 NE in Tamriel), `Water1024CreekFlow*`, pools `MineralPoolSmWater01` 32 + `BigWater` 28.
3. **Flowmaps** (new in Update.esm/SE): `textures\water\skyrim.esm\flow.<cellx>.<celly>.dds` for 641 cells (x -43..47, y -26..26), picked by cell coordinates; applied where the water type has the `EnableFlowmap` flag (Update's `RiverWaterFlow`, `...Blend`, `DefaultWaterFlow`, `...Blend`; KoTM's). Of the 430 Tamriel cells using those four types, 421 have a flowmap file (no flowmap: the flow falls back to the vector). BM&V ships only 4 root water textures (`defaultwater`, `waterrainripples`, `riverflow`, `waterrainlut`) and no flowmap, so BM&V cannot render directional flow on `MurkyWater`.
4. **Placed FX statics** at rapids, falls, bends: Tamriel `FXrapidsFallsLine01` 212, `FXrapidsBig01` 127, `FxRapidsRingHeavy` 114, `FXrapidsRocks01` 81, `FXSplashSmallParticles(Long)` 290/295, `FXLargeSplashChurnWater` 125, `FXWaterfallMistBlastLite` 97, `FXWaterfallSkirtSlope` 83, `TundraStreamTransition01` 102, salmon FX `FXAmbWaterSalmon*` 772+542+459+200. Rivers have no visible flow without them. Still water has none of these: `PuddleWater`, marsh and lake cells have velocity 0.15-0.22 and no flowmap.

### 3.4 Which types would serve (our land has one water level at 0, so type is chosen by cell/placed water, never by height)

| kind | record(s) | colours | note |
|---|---|---|---|
| ocean | `DefaultWater` (Update) or TS `DefaultWater` | (38,39,24)/(5,14,18) op 50, or TS turquoise | the world water; LOD water the same (NAM3) |
| shallow coast | `DefaultMarshWaterTransition` as the edge type, or KoTM `DefaultBlackmarshWater` | (37,52,37)/(5,16,5) or (130,116,34)/(61,95,52) | fog-under -4000/1200 gives the soft turn |
| estuary | KoTM `BlackmarshRiverWaterFlowBlend` (BlendNormals) or Update `DefaultWaterFlowBlend` | yellow-green or green | blends a river into still water |
| river | `RiverWaterFlow` (flowmap) + `RiverWaterFlowNE/NW/SE` (vector) + the FX rapids | (38,39,24)/(5,14,18) op 50 | or KoTM `BlackmarshRiverWaterFlow*` for the green Argonian river |
| stream, creek | `CreekWaterFlow*`, `DefaultCreekWater` + `TundraStream*` | (71,78,67)/(35,35,24) op 0 | clear, pale gravel |
| lake | `DefaultWater` or `RiftenWater` at an XCLW | (36,53,39)/(16,15,5) | |
| pond | `DefaultCreekWater`, `ClearInteriorWater*`, `Water1024Creek` | clear (67,80,70) | |
| green marsh | `DefaultMarshWater` | (37,52,37)/(5,16,5) | no flow |
| blackwater swamp | `MurkyWater` | (26,19,19)/(9,9,6) op 100 | BM&V's own; no vanilla alternative is darker except `ShadowmereWater` (0,0,0) |

The previous planning doc's concern (adjacent cells of different types at one level show a hard shallow colour band) is real in the data: DefaultWater/Marsh/Creek/River differ in shallow RGB by up to (+/-45); to avoid the cyan strip give the types one shared shallow colour or use the `...Transition`/`...Blend` types between them.

## 4. Water's-edge progressions (queries: per-vertex LAND heights, water = LAND height < the cell's water level (XCLW or the world default), components smaller than 40 vertices dropped; signed distance transform to the water line at 1.83 m resolution; texture weights per vertex by the layer-stack rule; scatter = non-disabled vanilla refs mapped to the nearest vertex; area per band in m2; excluded: architecture, markers, lights, dungeons, actors, clutter, quest FX; `edge.py`; full trimmed outputs in Appendix D)

### 4.1 Morthal swamp (Tamriel x -16..-3, y 13..24; 0.58 km2, 19.1% water, 17 water bodies; water -14000 default)

Texture (weight in the band): in the water: 0-2 m from the line (depth median 0.23 m) DirtSlopes01 0.59 + RiverMud01 0.21; 2-5 m (0.57 m deep) DirtSlopes 0.41 + RiverMud 0.41; 5-10 m (0.91 m) RiverMud 0.52 + DirtSlopes 0.27 + RiverBottom01NoGrass 0.10; 10-20 m (3.2 m) RiverMud 0.37 + RiverBottomNoGrass 0.24 + RiverMudNoGrass 0.15; 20-40 m (10 m) RiverBottomNoGrass 0.42 + RiverMud 0.25 + RiverMudNoGrass 0.21. On land: 0-2 m (+0.11 m) `LFrozenMarshDirtSlopes01` 0.55, MarshGrass01 0.13, RiverMud01 0.10, MarshIce 0.07; 2-5 m (+0.46) MarshGrass 0.37, DirtSlopes 0.33; 5-10 m (+1.26) MarshGrass 0.46, DirtSlopes 0.17, GrassNoGrass 0.08, Ice 0.08, Lichen 0.05; 10-20 m (+3.0) MarshGrass 0.38, DirtSlopes 0.14, Ice 0.12; 20-40 m (+7.0) MarshGrass 0.25, Snow01 0.15, Ice 0.13, SnowRocks 0.09; beyond 40 m the snow textures take over. Banks: median land height +0.11, +0.46, +1.26, +3.0 m in the 0-2, 2-5, 5-10, 10-20 m bands from the line.

Scatter per 100 m2 (vanilla models; band total, top forms): water 0-2 m 1.13 (`ReachBranchPile01/02` 0.15/0.08, `CoastDriftwood03/01` 0.11/0.08); 2-5 m 0.54 (ice floes `FrozenMarshIceFloe*` 0.05 to 0.09 each, mist `FXMistLow01LongHalfVis`); 5-10 m 0.65 (ice floe chunks/frosts 0.05 to 0.08 each); 10-20 m 0.36; beyond 20 m only hawks. Land: 0-2 m 2.56 (thicket 0.26, `FloraSwampFungalPod01` 0.22, `ReachBranchPile01/02` 0.22, dead shrub 0.18); 2-5 m 2.77 (thicket 0.37, dead shrub 0.25, `ReachCliffTree01/02` 0.13 to 0.15, `ReachTree01` 0.12); 5-10 m 2.24 (thicket 0.35, dead shrub 0.23, `ReachTree02` 0.12, `ReachCliffTree` 0.12); 10-20 m 1.62; 20-40 m 1.39; 40-80 m 1.27; 80-160 m 1.48 (pine forest takes over). The first 20 m of bank carries 1.6 to 2.8 refs per 100 m2, the plateau 1.3 to 1.5: swamp trees are `TreeReachTree01/02` and `ReachCliffTree` (gnarled), shrubs `TreeThicket01` and `TreeDeadShrub`. Cattail: `CattailGrass01` is TS only; vanilla Hjaalmarch uses `MarshGrassObj01` grass (density 60) on `LFrozenMarshGrass01`.

### 4.2 Skyrim sea shore: Solitude coast (x -22..-6, y 24..38; 0.88 km2, 55.8% water) and Dawnstar coast (x 3..14, y 25..36; 0.50 km2, 71.7% water)

Solitude: water 0-2 m from the line (depth 0.23 m) `LCoastBeach01` 0.57 + `LCoastOceanFloor01` 0.20 + Beach02 0.06; 2-5 m 0.52 + 0.29; 5-10 m 0.47 + 0.34; 10-20 m 0.42 + 0.31 + Rocks01NoRocks 0.07; 20-40 m (7.8 m deep) 0.44 + 0.27 + Rocks 0.08; 40-80 m 0.55 + RocksNoRocks 0.13 + OceanFloorNoGrass 0.11. Land: 0-2 m (+0.11) Beach01 0.58, OceanFloor01 0.13, Beach02 0.08; 2-5 m (+0.46) Beach01 0.53, **BeachGrass01 0.13**, Rocks01 0.07; 5-10 m (+1.5) Beach01 0.49, Rocks01 0.17, BeachGrass 0.07; 10-20 m (+4.5) Beach01 0.40, Rocks01 0.16, Snow01 0.10; 20-40 m (+10.7) Beach01 0.23, Snow01 0.19, Rocks01 0.14; beyond 40 m snow/rock. Dawnstar: beach 0.32 + ocean floor NoGrass 0.22 + Rocks 0.17 offshore 0-2 m; land 0-2 m OceanFloor01 0.34 + Beach01 0.25; 2-5 m Beach01 0.49; 10-20 m Snow01 0.38 + Beach01 0.33. The **beach texture straddles the line** and extends 20 to 40 m inland while the ocean-floor texture holds 20 to 35% under the water; land height rises 0.46 m by 5 m, 1.5 m by 10 m, 4.5 m by 20 m.

Solitude scatter per 100 m2: water 0-2 m 0.55 (fish-egg clusters `SlaughterfishEggCluster01` 0.06, branch piles, clams `ClamThin01`, barnacle cluster); 2-10 m 0.51 to 0.62 (frozen-marsh ice floes `FrozenMarshIceFloeChunks/Frosts` 0.05 to 0.09 each, an arctic sea feature); 10-80 m 0.17 to 0.30 (boulders `RockL01..03`, `MountainTrim01`, egg and barnacle clusters). Land: 0-2 m 1.13 (`ReachBranchPile01/02` 0.12/0.08, thicket 0.10, `CoastDriftwood02` 0.08); 2-5 m 1.90 (thicket 0.27, branch pile 0.22, `RockPileM02` 0.14, `FloraSpikyGrass02` 0.12); 5-10 m 1.91 (thicket 0.31, dead shrub 0.18, branch pile 0.13, spiky grass 0.09, rock pile 0.08); 10-20 m 1.42; 20-40 m 1.38; beyond 40 m 0.9 to 1.35 (snow pines). Dawnstar: land 0-2 m 0.85 (`ReachBranchPile01` 0.12, `CoastDriftwood02` 0.07), 2-5 m 1.27 (`CoastDriftwood01/03` 0.14 each, branch piles 0.14/0.13), 5-10 m 1.28; water 0-2 m 0.37 (`Clam01` 0.08, `ClamLarge01` 0.05, wet rock pile), 10-20 m 0.41 (`NordicBarnacleCluster01` 0.07, `Clam01` 0.07). Seabed GRAS (kelp, coral) comes from the LTEX: `LCoastOceanFloor01` GRAS = `WaterKelpGrass01`, `WaterCoralGrass01`, `TBPRockGrassWater02`, `TBP*` (Depths).

### 4.3 River: the White River (x 3..30, y -6..12; 1.83 km2, 4.5% water, 23 water bodies)

Bed band (inside the line): 0-2 m `LRiverbedEdge01` 0.42, RiverBottom01 0.17, RiverBottomNoGrass 0.06; 2-5 m (0.86 m deep) RiverbedEdge 0.32, RiverBottom 0.28, RiverBottomNoGrass 0.12; 5-10 m (1.5 m) RiverBottom 0.37, NoGrass 0.20, Edge 0.18, RiverMud 0.06; 10-20 m (2.0 m) RiverBottomNoGrass 0.32, RiverBottom 0.24, RiverMud 0.19; 20-40 m (2.8 m) NoGrass 0.55, RiverMud 0.25. Bank: 0-2 m (+0.26) RiverbedEdge 0.38, RiverBottom 0.10, VolcanicTundraRocks 0.05; 2-5 m (+0.91) RiverbedEdge 0.24, VolcanicTundraDirt 0.08, Rocks01 0.08; 5-10 m (+2.5) Null 0.10, Snow01 0.10, Rocks 0.09, Edge 0.09; beyond 10 m Snow01/Rocks/VolcanicTundra. Scatter per 100 m2: water 0-2 m 1.20 (thicket 0.08, barnacle cluster 0.05, wet rock piles 0.04); 2-5 m 0.92 (`FXRapids` 0.05, barnacle 0.05, `FXWaterfallSkirtSlope` 0.04, splash FX 0.03); 5-10 m 0.83 (barnacle 0.07, `FXRapidsFallsLine01` 0.07, `FXRapidsRocks01` 0.05, `FXRapidsBig01` 0.05); 10-20 m 0.77; bank 0-2 m 1.47 (thicket 0.15, `RockPileM02Wet` (wetrocks) 0.05, `TreePineForest03` 0.04, splash FX 0.04); 2-5 m 1.99 (dead shrub 0.12, pine 0.11, thicket 0.10); 5-10 m 2.06; 10-20 m 2.00; 20-40 m 1.76; 40-80 m 1.60; 80-160 m 0.97. A distinct wet-rock set exists (`landscape\rocks\wetrocks\rockpilem02wet`).

### 4.4 Lake: Lake Ilinalta (x 5..12, y -27..-20; 0.22 km2, 2.0% water, one body, height 12608)

0-2 m inside the line (depth 0.34 m) `LRocks01NoRocks` 0.44 + `LRiverbedEdge01` 0.44; 2-5 m (1.5 m) RiverbedEdge 0.56 + Rocks 0.30; 5-20 m (3.9 to 9.3 m) RiverbedEdge 0.55 to 0.58 + RocksNoRocks 0.14 to 0.18; 20-40 m (11 m) RiverbedEdge 0.55 + Null 0.16. Land: 0-2 m (+0.23 m) Rocks01NoRocks 0.47 + RiverbedEdge 0.30; 2-5 m RocksNoRocks 0.47 + Edge 0.20; 5-10 m (+3.3) RocksNoRocks 0.38 + Dirt02 0.13 + Snow01 0.12; 10-20 m Snow01 0.23 + PineForest01 0.15 + RocksNoRocks 0.32; beyond 20 m Snow01. The lake is a rocky shelf with the river-edge texture as bed and bank. Scatter per 100 m2 on land: 0-2 m 0.60 (`TreePineForestLogSm01` 0.20, `RockM04` 0.20, `RockM02` 0.20); 2-5 m 1.81 (`TreeThicket01Snow` 0.83, `RockL02` 0.42); 5-10 m 1.78 (snow shrubs, `RockCliff05`, `MountainCliff02`); 10-20 m 1.14; 20-40 m 0.62; 40-80 m 0.36 (the lake sits in a bowl of rock). Water 0-2 m 0.25 (rock piles `RockPileL03`, `RockL04`, `MountainTrim02`, `RockCliff02`).

### 4.5 BM&V: the swamp and shore (inland ponds and the sea/lagoon are separated by water-body size and by touching the world raster edge; whole-world rasters of BlackMarshNorth (9.36 km2 of vertices), BlackMarsh, BlackMarsh2, Valenwood; water 0)

- **Black Marsh North inland water** (262 bodies, 6.2% of the vertices): the texture does not change from water to land. Water 0-2 m: `LPineForest05` 0.59, FieldGrassDUPLICATE002 0.07, FieldGrass01 0.07, Dirt03 0.06, PineForest03 0.06; land 0-2 m: 0.60, 0.07, 0.07, 0.06, 0.06; land 40-80 m: 0.41 + Null 0.14. i.e. a single moss texture from the pond floor to 40 m inland. Depth 0.23 m at 0-2 m, 1.0 m at 5-10 m, 1.9 m at 10-20 m; bank +0.11, +0.46, +0.9, +1.7 m at 1-2, 2-5, 5-10, 10-20 m, flat at +1.7 m from 16 m (matches terrain-measurements). Scatter per 100 m2 is 0.24 in the water (water lilies `gkblillipad2` 0.02 -> 0.37 by 10-20 m from shore, `kelptallstatic01aaa` 0.07), 0.29 to 0.45 on land at every band (`vvardenfell\flora\algrass03b`, `firefern01`, `FloraSpikyGrass02`, `StingingNettel_04`, `cypress3`, broken pine `DLC2 TreePineForestBroken*`): essentially no edge dressing.
- **Black Marsh sea/lagoon** (51.4% water): water 0-2 m LPineForest03 0.29 + Null (offshore default) 0.55; the land texture continues underwater to 40 m; scatter: `vurt_reeds` 0.36 -> 0.58 per 100 m2 within 20 m of the line (0.23 at 20-40 m), `gkblillipad2` 0.08 -> 0.14, `waterkelpshort/tall01` 0.03 to 0.05 each, swordferns 0.05; BM&V's one deliberate edge band is the reed belt.
- **BlackMarsh inland** (4.8% water): land 0-2 m swordfern clusters 8.7 per 100 m2 (`swordferncluster04` 2.64, `swordfern03` 1.40, `swordferncluster01` 1.22, `swordfern06` 1.21, `swordfern01` 1.02), 2-5 m 8.5, 5-10 m 6.5, 10-20 m 4.6, 20-40 m 3.6, 40-80 m 1.4; in the water 0-5 m 5.7 to 6.8 (ferns standing in the water), 10-20 m 0.6. Textures: PineForest03 0.31, Null 0.31, FieldGrass02 0.30 flat across the bands.
- **BlackMarsh2 inland** (1.5% water): ground `LPineForest03` 0.81 to 0.96 at every distance; scatter: land 0-2 m 35.9 per 100 m2 (`poisonbloomingredient` 6.82, `braken` 5.25, `TropicalPlant01` 4.43, `FernLarge03` 3.71, `BigShrub2(colorful)` 2.71, `esloebush08` 1.82), 2-5 m 3.66, 5-10 m 1.66; water 0-20 m 2.6 to 3.65 (the same ferns and bushes standing in the water), 20-40 m 0.77. (The first 2 m band is small, 18,367 m2, so 35.9 is the most extreme density measured; 2 to 5 m is 3.66.)
- **Valenwood inland** (122 bodies; 2.6% water): water 0-2 m `LPineForest03` 0.34 + FieldGrass01 0.16 + FallForestGrass01 0.15 + PineForestDUPLICATE004 0.11; by 20-40 m depth (17.6 m) the PineForestDUPLICATE004 (`PineForest03` path) 0.50 + `LDirtDUPLICATE004` (LERock17) 0.16 + rock 0.08; scatter 0.1 to 0.2 per 100 m2 in the water bands (mountain trim, cliff slopes, `FXWaterfallThin2048x128`), rocks and aspens on the bank.
- **Offshore**: BM&V's Black Marsh North sea bed falls 1.3 m by 5 m, 5.3 m by 10 m, 16 m by 20 m; beyond 29.3 m it is the -2048 default land (Null texture 0.52 to 0.97 of the weight in the 5 to 80 m water bands): there is no ocean-floor texture and no seabed plant in BM&V; Depths' `LCoastOceanFloor01` + `TBP*` GRAS (23 records, `UnitsFromWater` 50 to 1000 units below the surface) supply it.

### 4.6 Differences to design against

BM&V paints one texture (moss) from the pond floor to 40 m inland and dresses the edge with placed reeds, lilies and ferns only in a few places; vanilla paints a progression of four to six textures within 20 m of the line and a rising density of dressing (1.6 to 2.8 refs per 100 m2 within 20 m, 1.3 to 1.5 beyond, 0.3 to 0.6 in water). The rule set copies vanilla's texture progression and BM&V's reed/lily/fern statics.

## 5. Atmosphere

### 5.1 BM&V weather (query: CLMT, WRLD climate, REGN weather lists, WTHR fog slots)

- All three Black Marsh worlds use climate `BlackMarshClimate` 130762 (winner: Black Marsh North.esp): SkyrimFog 0C821E 45, SkyrimOvercastRain 0C821F 20, SkyrimStormRain 0C8220 20, SkyrimCloudy 012F89 10, SkyrimClear 00081A 5. (Black Marsh.esm's version: Fog 40, StormRain 20, OvercastRain 20, Cloudy 10, Clear 10.) Black Marsh North.esp also defines `NorthBlackMarsh` (Clear 30, Fog 20, DLC02VolcanicAsh01 20, OvercastRain 10, StormRain 10, VolcanicAshStorm 10) but no world uses it. Valenwood: `valenwoodclimate` 01CECA: Clear 40, OvercastRain 20, StormRain 20, ClearVT 10, SovngardeFog 10. BM&V defines no weather region and no WTHR (only `DefaultWeatherDUPLICATE001` in BMN and Valenwood): **BM&V's atmosphere is the vanilla weather records**, in this load order the Update.esm versions. Sunrise/sunset in every climate: 5:30-10:00 sunrise, 16:00-20:30 sunset (vanilla). Moons Masser/Secunda.
- KoTM defines its own regional weather lists (REGN `ArgoniaMurkmireNorth/Shadowfen/Blackwood/Thornmarsh/Lilmoth/South`): Fog 35-45, Clear 20-25, OvercastRain 20, Cloudy 15-20, StormRain 10-15, plus a `HistStormRain`.
- Fog slots of the weathers BM&V uses (Update.esm values; day near-far, power, max; night near-far): SkyrimFog 0-25000, 0.4, 0.95; night 0-15000; fog-near colour day (85,106,125), far (99,115,139); SkyrimOvercastRain 0-15000, 0.5, 0.9; SkyrimStormRain 0-25000, 0.45, 0.92; night 0-10000; SkyrimCloudy 0-100000, 0.4, 0.875 (night 0-50000); SkyrimClear 0-80000, 0.4, 0.85 (night 0-40000); VolcanicAsh01 0-60000, 0.35, 0.95. TS recolours the Day fog-near colour of SkyrimFog to (182,185,68), SkyrimCloudy (171,189,108), SkyrimClear (136,138,68) (yellow-green) and shortens Clear's fog power 0.4 -> 0.3; the owner wants BM&V's, so none of it is used.
- Vanilla Hjaalmarch weather for comparison: REGN `WeatherTundraMarsh` (0C5855): 10A233 40, SkyrimClearMA 20, SkyrimFogMA 20, OvercastRainMA 10, ClearMA_A 5, CloudyMA_A 5; SkyrimFogMA fog 0-50000 power 0.375 max 0.95: **Morthal's mist is not the weather's fog (far 50000) but placed statics.**

### 5.2 How Morthal's ground mist is done (query: placed refs whose model is `effects\ambient\fxmist*` in Tamriel; marsh-water cells x -15..-4, y 14..23 (45 `DefaultMarshWater` + 13 `Transition` cells = 58 cells = 0.199 km2); heights vs the LAND under each ref; NIF decode of the four meshes)

- 81 of Tamriel's 476 `FXMist*` refs sit in these 58 cells: `FXMistLow01LongHalfVis` 34, `FXMistLow01HalfVis` 22, `FXMistLow01Long` 11, `FXMistLow01` 9, `FXMistLow02HalfVis` 2, adjust variants 3. Density 1.40 per cell = 408 per km2; nearest-neighbour spacing p10/p50/p90 21.9 / 31.1 / 43.5 m. Over the whole Hjaalmarch box (110 cells) 124 mist refs plus 8 chimney smoke refs.
- Height: z is 1.35 / 2.24 / 3.15 m (p10/p50/p90) above the LAND height and about +0.2 m above the water (the marsh ground is at -13998 u median, water -14000). Scale 1.0 / 1.5 / 1.8 (p10/50/90). Per type median above ground: Long 2.6 m, LongHalfVis 2.4, FXMistLow01 2.2, HalfVis 2.1.
- No enable parents on the mist (0 of the 124; 6 of the 8 smoke refs have one), none disabled, no script: **always on**.
- The model: `FXMistLow01` is 13 x 12.5 x 2.5 m (x -459..446, y -418..438, z -89..89 units); `...Long` 14 x 36 m; two shapes (the mist body plus an EditorMarker), `BSEffectShaderProperty` with `textures\effects\CloudTile.dds` (UV-scrolling cloud) and the ambient-fog gradient `textures\effects\gradients\GradAmbFog01.dds` (so its colour follows the weather's ambient fog), a `BSEffectShaderPropertyFloatController` pair, `NiAlphaProperty`; vertex alpha 0 to 127; the HalfVis variants differ only in vertex colours/alpha (about half visibility). No weather condition exists on the NIF, so the amount of mist does not change with time or weather.
- BM&V's mist: `FXFog01` (a 7.4 m x 7.4 m x 4 m fog sprite with `FXpuffsTile.dds` + `GradSmokeUndulate.dds`) scaled x9-10 (about 70 m across), placed 1.5 to 6 m **below** the ground (dz p50 -2.8 m BMN, -1.5 BlackMarsh, -6.1 BlackMarsh2): 192 / 320 / 1,412 refs in BMN / BlackMarsh / BlackMarsh2; BlackMarsh2 also has `FXMistLowSwirls01` 561 (scale 6; `DarkSwirls.dds`), `FXAmbBlowingFog01` 229, `FXFogRollingFacing01` 38; Black Marsh North `FXMistLowSmokey01` 40; Valenwood `FXFog01` 67. KoTM places the vanilla `FXMistLow01` 123 + `Long` 75 at dz 1.9 to 3.6 m. So BM&V's "mist" is large always-on sprites, KoTM's is vanilla's.

### 5.3 What Community Shaders in the stack offers

- Staged: `~/.argonia/stack/MO2/mods/community-shaders` with 26 `Shaders/Features/*.ini` (CloudShadows, DynamicCubemaps, ExtendedMaterials, GrassCollision, GrassLighting, LightLimitFix, ScreenSpaceShadows, SkySync, SubsurfaceScattering, TerrainShadows, UnifiedWater, VolumetricLighting, VolumetricShadows, WaterEffects, ...). The shipped DLL contains the **ExponentialHeightFog** feature (settings: start distance, fogHeight, fogHeightFalloff, fogDensity, inscattering colour, directional inscattering multiplier and anisotropy, original-fog-colour amount, "disable vanilla fog", optional froxel **volumetric fog** with its own start/view distance and extinction scale), **per-weather overrides** ("This weather has custom overrides for this feature", saved as `Data\SKSE\Plugins\CommunityShaders\<feature>\<weather>.json` through the CS weather editor), and `WetnessEffects` (a rain-driven wetness weather analysis), but the feature's own INI and `Shaders/ExponentialHeightFog` folder are **not laid** (`mods/README.md:34`: "its Exponential Height Fog add-on is not laid"). Our `Argonia_ExponentialHeightFog.json` overrides it to density 0, volumetric off, "OFF (neutered)" by the round-5 ruling, because with it and volumetric lighting on "the sky was a grey veil" (`docs/research/machines/lane-1.15-r3-machine.md`, the file's own description). VolumetricLighting exterior is also off in `Argonia_VolumetricLighting.json`.
- CS has **no ground-hugging mist object or particle feature**; `ExponentialHeightFog` is global height fog (fog thickness decays above a height), tunable per weather. The Morthal-style layer remains the placed statics.

### 5.4 The native way to the requested behaviour (proposal; nothing here is measured in game, it is a design from the measured mechanisms)

Native levers, all records: (a) the weather's fog slots, which have a Day pair (near, far, power, max) and a Night pair, and the colour slots (Sunrise/Day/Sunset/Night); the engine interpolates Night -> Day across the climate's sunrise window and Day -> Night across the sunset window (CLMT SunriseBegin..End, SunsetBegin..End); (b) the weather mix per climate/region; (c) placed `FXMist` statics, always on, and a few enable-parented effects.

1. **Strong in the morning, burned off by noon, regathering at night.** Author the BM&V climates with a long sunrise window (e.g. SunriseBegin 05:00, SunriseEnd 12:00; SunsetBegin 17:00, SunsetEnd 22:00) and give the *sunny* weathers (SkyrimClear/Cloudy copies) a dense **Night** fog slot and a thin **Day** slot: Night near 0, far 6000 to 10000, power 0.4, max 0.7 to 0.8; Day far 80000 (the vanilla Clear value). The engine then lerps Night -> Day across 05:00-12:00, so mist is thickest at dawn and gone by noon, and lerps back across 17:00-22:00. Vanilla already uses this: SkyrimStormRain has Night far 10000 vs Day 25000. Keep the colour slots (Sunrise = pale warm) so the dawn cast reads as mist.
2. **Thicker after rain.** Records cannot condition on the previous weather. Options in order of cost: (i) make the rain weathers themselves dense (SkyrimOvercastRain Update value 0-15000 power 0.5 max 0.9 is already dense; keep it), and add a short-lived post-rain weather (copy of SkyrimFog) listed with a high chance in the climate so it follows rain often; (ii) a small Papyrus/SKSE script that listens for the weather-end event and `ForceWeather`s the fog weather for an hour; (iii) in Community Shaders, the `WetnessEffects` weather analysis plus per-weather ExponentialHeightFog overrides tied to rainy weather flags. (i) is records only; (ii) is the fallback if the owner wants it deterministic (CLAUDE.md: our own plugin only where no record or mod does the job).
3. **Ground mist.** Copy Morthal: place `FXMistLow01HalfVis`, `FXMistLow01LongHalfVis` and `FXMistLow01Long` statics (vanilla meshes, used by KoTM too; scale 1.3 to 1.6; Morthal puts the centre at +2.1 to 2.6 m over the ground, and the mesh is +-1.3 m tall x scale, so it fills about 0.3 to 4 m; for mist that stays below eye level put the centre at +0.5 to +1.0 m) at 31 m spacing (p50 nearest neighbour; 400 per km2; one per 2,400 m2), over the swamp and the water within 20 m of marsh banks, about 1.4 per 58.5 m cell. To make it time- and weather-dependent without a script, use **two sets**: an always-on thin set (HalfVis, 1.0 per cell) and a thick set (`FXMistLow01Long`, `FXFog01` scale 9 as BM&V does) placed with an enable parent bound to an activator that a one-time quest alias toggles by weather (script). The record-only version keeps the always-on set at the Morthal density and lets the weather fog slots do the time-of-day change.
4. **Community Shaders.** If the owner rules ExponentialHeightFog back in, lay the add-on correctly (INI under `Shaders/Features`, shaders under `Shaders/ExponentialHeightFog`), start at the feature's defaults (density 0.005, falloff 0.2, start distance 0, fogHeight 0; the round-3 notes) with `disableVanillaFog` off, and author per-weather overrides for the three marsh weathers only (density up in Fog and OvercastRain, near zero in Clear) through the CS weather editor; verify by the sky A/B that bisected the round-5 veil. Volumetric (froxel) fog is the expensive part and should stay off. Do not rely on CS for the dawn-to-noon change: it has no time-of-day axis except the weather's own interpolation.

Recommended first step: records only (1), (3 always-on) and the post-rain fog weather from (2i); judge in game; add the script only if the owner wants deterministic "after rain" mist.

## 6. Methods (so every number can be rerun)

- Plugins read with Mutagen 0.54.4 binary overlays, strings suppressed, in the order Skyrim, Update, Dawnguard, HearthFires, Dragonborn, Black Marsh, Black Marsh North, Valenwood, Tropical Skyrim, King of the Murkmire, Depths (BM&V North and Valenwood from `mods/bmv`). "Vanilla" refs: the last version of each REFR from a non-TS, non-Depths plugin; REFRs created by TS or Depths and TS base swaps are excluded and shown separately; base model = the last non-TS, non-Depths record's `Model.File`.
- LAND: VHGT decoded as in `tools/bmv_map/build.py` (the seam test passes: east edge of a cell equals the west edge of the next, mean difference 0.0). Layers: Mutagen `Layers` (check `IAlphaLayerGetter` before `IBaseLayerGetter`: an alpha layer also satisfies the base interface). Layer stack: sorted by quadrant and layer number, weights multiply by (1 - o) and the layer's weight gains o.
- Roads: NIF decode by `nif.py` (header v20.2.0.7, BSTriShape vertex descriptor, positions as float32); road-surface vertices transformed with x' = x cos t + y sin t, y' = -x sin t + y cos t; chosen over the opposite sign by the surface-to-ground z spread (34.8 vs 61.1 units median std).
- Water edge: signed distance transform (scipy) at 128 units; the cell's water level is XCLW else the world default (Tamriel -14000, BM&V 0); bank and depth heights are the median of vertex height minus level.
- Mist: models `effects\ambient\fxmist*` and BM&V FX counted per world; z above LAND by bilinear interpolation of the heightmap.
- Not reproduced here: the earlier `terrain-measurements.md` height numbers (road trough etc.), which stand.

## 7. Recommendations (each with its evidence)

1. **Author BM&V-style base textures but paint three layers per quadrant, never one.** BM&V's quadrants hold 1.2 to 1.7 textures (71% of Black Marsh North quadrants have no alpha layer) and 23 to 34% of the quadrants in each Black Marsh world share one base (section 1.3); vanilla holds 3.15. Use the BM&V LTEX roles of section 1.2 as the palette and add the vanilla edge LTEX (`LRiverMud01`, `LRiverBottom01`, `LRiverbedEdge01`, `LCoastBeach01`, `LCoastOceanFloor01`) to the water bands.
2. **Do not copy BM&V's flat edge; copy vanilla's progression** (section 4): the first 20 m of bank is the only band where the texture changes, so paint it as four to six layers, and add Depths' `TBP*` GRAS through the bed LTEX for the seabed.
3. **Roads: use the Road* meshes plus a dirt LTEX with a 3.5 to 8 m ramp**, not painted cobble (BM&V's cobble is for towns). Dress with `RockPile*` (about 55 per km, median 2 m out), boulders, farm walls/fences only by farms, signs at 0.7 to 1.0 m, trees at least 2.5 m from the surface edge, shrubs allowed to the edge (section 2). TS has no rocks; take rocks from BM&V's `landscape\rocks` (including `moss_rockpiles02/04`, `al_cairn01..03`) and vanilla.
4. **Decide the sea water type before building**: the stack's `DefaultWater` is the Update.esm river-like record (olive/dark), TS's is turquoise; both exist and neither is the BM&V look. `MurkyWater` is BM&V's world water for sea and swamp alike. If the owner wants a distinct green marsh and black swamp, use `DefaultMarshWater` and `MurkyWater` on separate cells with `DefaultMarshWaterTransition` between, and a shared shallow colour (section 3.4).
5. **Flowing rivers need three things, not one**: an `EnableFlowmap` type, a flowmap texture per river cell (`textures\water\<our plugin>\flow.x.y.dds`, 421 of 430 vanilla flow cells have one), and rapids FX statics at drops. KoTM already has the type set (`BlackmarshRiverWaterFlow*`) in green.
6. **Mist: records first** (section 5.4); keep the Morthal density (about 400 per km2 over marsh and 20 m of bank) and scale/height measured above, and use the climate sunrise/sunset window and Night/Day fog slots for the morning/noon/night cycle. Re-enabling Community Shaders' Exponential Height Fog is an owner call (round-5 ruling); evidence for and against is in section 5.3.
7. **Fix the earlier doc's wrong facts when the phase file is edited** (section 0): RoadChunk are patches not stones; paint ramp is 3.5 to 8 m; mist is a regional layer in Hjaalmarch; DefaultWater winner is Update's. 

Covered: `Data/*.esm,*.esp` (all 11 plugins, records and placed refs of Tamriel, BlackMarsh, BlackMarsh2, BlackMarshNorth, Valenwood, ArgoniaWorld; LAND of those plus Solstheim for counts), `Skyrim - Meshes*.bsa` and `Textures*.bsa` (road, mist, fog NIFs; texture lists), `~/.argonia/stack/MO2/mods/bmv` (file list, landscape textures), `~/.argonia/stack/MO2/mods/community-shaders` (INI list, Overrides, DLL strings), `Data/argonia-mesh-lists/*.txt`, repo docs named in section 0 · Skipped: Solstheim, Falmer Valley and the DLC worldspaces' edges (not asked), TS/KoTM/Depths meshes and textures (not on this machine), in-game behaviour (read-only rule), interiors, the vanilla Rift/Falkreath/Pale water edges (only Morthal, Solitude, Dawnstar, White River and Ilinalta were asked), roads in Skyrim's DLC worlds, LOD water.


---

## Appendix A. LTEX tables (query `a1b.py`/`lib.py ltex()`; GRAS lists by source)

```
### A. LTEX used on the ground in Black Marsh worlds (BlackMarsh/BlackMarsh2/BlackMarshNorth), by layer count; BM&V-defined first marked *
uses  LTEX                           origin | diffuse (TXST) | material | GRAS lists by source (van = Skyrim/Update, TS = Tropical Skyrim, Dep = Depths)
 6682  LPineForest03                  Skyrim | Landscape\PineForest03.dds                                     | Grass              | van: FernGrass01,SnowGrass01Forest ; TS: FallForestGrass02,TropicalGrass01,TropicalGrassPlant01
 3332* LPineForest05                  Black  | TEXTUREPACK\landscape\tundramoss01.dds                         | Grass              | Black : FernGrass01,SnowGrass01Forest
 1620* LPineForestDUPLICATE004        Black  | TEXTUREPACK\landscape\grass\rocksgrasswater01.dds              | Grass              | Black : FernGrass01,SnowGrass01Forest
  889  LFieldGrass02                  Skyrim | Landscape\FieldGrass02.dds                                     | Grass              | van: FieldGrass01,FieldGrass02 ; TS: TropicalGrassPlant01,TropicalGrassPlant02,FieldGrass02
  678* LFieldGrassDUPLICATE003        Black  | TEXTUREPACK\landscape\rivermud.dds                             | Grass              | Black : FieldGrass01,FieldGrass02
  557  LTundra01                      Skyrim | Landscape\tundra01.dds                                         | Sand               | van: TundraGrass04,TundraGrass03 ; TS: RockGrass01,TundraGrass04,TundraGrass03
  420* LDirt03                        Black  | vvardenfell\rm\rm_rock02.dds                                   | Dirt               | Black : -
  385  LFieldGrass01                  Skyrim | Landscape\FieldGrass01.dds                                     | Sand               | van: TundraGrass01,TundraGrass04 ; TS: RockGrass01,TundraGrass01
  345* LFieldGrassDUPLICATE002        Black  | landscape\darklandgrassrocks.dds                               | Grass              | Black : TundraGrass01,TundraGrass04
  237* 01road2                        Black  | TEXTUREPACK\landscape\roads\road01.dds                         | Ash                | Black : -
  228  LTundraRocks01                 Skyrim | Landscape\TundraRocks01.dds                                    | BrokenStone        | van: RockGrass01
  197* DarkRock1                      Black  | landscape\Apel_lh_rock_02.dds                                  | Dirt               | Black : -
  194* LDirtDUPLICATE003              Black  | landscape\sand\Sand06.dds                                      | Dirt               | Black : -
  173* LPineForestDUPLICATE005        Black  | landscape\sand\Sand02.dds                                      | Grass              | Black : FernGrass01,SnowGrass01Forest
  171  LVolcanicAsh03                 Dragon | DLC02\Landscape\volcanic_ash_05.dds                            | Ash                | van: -
  146* LTundraRocksDUPLICATE002       Black  | landscape\Rocks\RedRock04.dds                                  | BrokenStone        | Black : RockGrass01
  144  LFallForestGrass01             Skyrim | Landscape\FallForestGrass01.dds                                | Grass              | van: FallForestGrass01,FallForestGrass02 ; TS: TropicalGrassPlant01,FallForestGrass01,FallForestGrass02
  135  LPineForest02                  Skyrim | Landscape\PineForest02.dds                                     | Grass              | van: ForestGrass01,SnowGrass01Forest,ForestGrass02 ; TS: TropicalGrass01,TropicalGrassPlant02,TropicalGrassPlant01
  134* LTundraDUPLICATE002            Black  | landscape\sand\Sand06.dds                                      | Grass              | Black : TundraGrass03,TundraGrass04
  129* Sand                           Black  | landscape\sand\Sand03.dds                                      | Dirt               | Black : -
  112* LDirtDUPLICATE002              Black  | TEXTUREPACK\landscape\roads\road01fallforest01.dds             | Dirt               | Black : -
  108* 01road1                        Black  | TEXTUREPACK\landscape\roads\road01fallforest01.dds             | Gravel             | Black : -
   89  LReachMoss01                   Skyrim | Landscape\ReachMoss01.dds                                      | Grass              | van: - ; TS: TropicalGrass01
   81* lava                           Black  | landscape\lavaflow.dds                                         | Dirt               | Black : -
   74  LRiverBottom01NoGrass          Skyrim | Landscape\RiverBottom.dds                                      | BrokenStone        | van: -
   72* LPineForest04                  Black  | TEXTUREPACK\landscape\grass\rocksgrasswater01.dds              | Grass              | Black : FernGrass01,SnowGrass01Forest
   69  LCoastBeach01                  Skyrim | Landscape\CoastBeach01.dds                                     | Sand               | van: - ; Dep: TBPRockGrassWater02,TBPRockGrassWater03
   54  LReachGrass01                  Skyrim | Landscape\ReachGrass01.dds                                     | Grass              | van: ReachGrass02,ReachGrass01,TundraGrass03
   50  LTundra02                      Skyrim | Landscape\Tundra02.dds                                         | Dirt               | van: - ; TS: RockGrass01
   47  LFallForestGrass01NoGrass      Skyrim | Landscape\FallForestGrass01.dds                                | Grass              | van: -
   42  LPineForest01                  Skyrim | Landscape\PineForest01.dds                                     | Dirt               | van: -
   37* LDirtDUPLICATE004              Black  | landscape\mountains\mountainslab04.dds                         | Dirt               | Black : -
   33  LVolcanicTundraMineralPool01   Skyrim | Landscape\MineralPoolTerrace.dds                               | Dirt               | van: -
   30  LDirt01                        Skyrim | Landscape\Dirt01.dds                                           | Dirt               | van: -
   27  LReachMossyRocks01             Skyrim | Landscape\ReachMossyRocks01.dds                                | BrokenStone        | van: RockGrass01
   25* LFieldDirtGrassDUPLICATE002    Black  | dirtroad01.dds                                                 | Grass              | Black : -
   25  LRiverMud01                    Skyrim | Landscape\RiverMud.dds                                         | Mud                | van: WaterKelpGrass01,WaterKelpGrass02 ; Dep: TBP_Algae01,TBPCoastDriftwood2,TBPCoastDriftwood,TBPSeaweed11,WaterKelpGrass02,TBPRockGrassWater02,TBPRockGrassWater03
   24  LReachGrass01NoGrass           Skyrim | Landscape\ReachGrass01.dds                                     | Grass              | van: -
   22  LVolcanicTundraGravel01        Skyrim | Landscape\VolcanicTundraGravel01.dds                           | Gravel             | van: -
   22  LRiverMud01NoGrass             Skyrim | Landscape\RiverMud.dds                                         | Mud                | van: - ; Dep: TBPCoastDriftwood2,TBPCoastDriftwood,TBP_Algae01,TBPRockGrassWater03,TBPRockGrassWater02
   15  LFallForestLeaves01            Skyrim | Landscape\FallForestLeaves01.dds                               | Grass              | van: - ; TS: TropicalGrassPlant01
   15  LCaveDirt                      Skyrim | Landscape\CaveBaseGround01.dds                                 | Dirt               | van: -
   13  LFieldDirtGrass01              Skyrim | Landscape\FieldDirtGrass01.dds                                 | Grass              | van: -
    9  LRiverbedEdge01                Skyrim | Landscape\RiverbedEdge.dds                                     | Stone              | van: - ; Dep: TBPRockGrass01
    6  LReachMossyRocks01NoRocks      Skyrim | Landscape\ReachMossyRocks01.dds                                | BrokenStone        | van: -
    5  LVolcanicAshRocks01_NoRocks    Dragon | DLC02\Landscape\volcanic_ash_rocks_01_d.dds                    | Gravel             | van: -
    5  LTundraRocks01NoRocks          Skyrim | Landscape\TundraRocks01.dds                                    | BrokenStone        | van: -
    5  LCoastBeachGrass01             Skyrim | Landscape\CoastBeachGrass01.dds                                | Grass              | van: BeachGrass01,BeachGrass02 ; TS: -
    4  LTundra01NoGrass               Skyrim | Landscape\tundra01.dds                                         | Sand               | van: - ; TS: -
    3  LDirt02                        Skyrim | Landscape\Dirt02.dds                                           | Dirt               | van: - ; TS: ForestGrass01
    2  LGrassSnow01NoGrass            Skyrim | Landscape\GrassSnow01.dds                                      | Grass              | van: -

### B. Valenwood ground (top 20)
 4652  LPineForest03                  Skyrim | Landscape\PineForest03.dds                                     | Grass              | van: FernGrass01,SnowGrass01Forest ; TS: FallForestGrass02,TropicalGrass01,TropicalGrassPlant01
 2807* LPineForestDUPLICATE004        Valenw | Landscape\PineForest03.dds                                     | Grass              | Valenw: FernGrass01,SnowGrass01Forest
 2049  LFieldGrass01                  Skyrim | Landscape\FieldGrass01.dds                                     | Sand               | van: TundraGrass01,TundraGrass04 ; TS: RockGrass01,TundraGrass01
 1795  LFallForestGrass01             Skyrim | Landscape\FallForestGrass01.dds                                | Grass              | van: FallForestGrass01,FallForestGrass02 ; TS: TropicalGrassPlant01,FallForestGrass01,FallForestGrass02
 1732  LFieldGrass02                  Skyrim | Landscape\FieldGrass02.dds                                     | Grass              | van: FieldGrass01,FieldGrass02 ; TS: TropicalGrassPlant01,TropicalGrassPlant02,FieldGrass02
 1353  LPineForest02                  Skyrim | Landscape\PineForest02.dds                                     | Grass              | van: ForestGrass01,SnowGrass01Forest,ForestGrass02 ; TS: TropicalGrass01,TropicalGrassPlant02,TropicalGrassPlant01
  908* LFieldGrassDUPLICATE002        Valenw | landscape\sand\Sand06.dds                                      | Grass              | Valenw: TundraGrass01,TundraGrass04
  549* LDirtPathDUPLICATE002          Valenw | Lor\landscape\cobblestone01.dds                                | Dirt               | Valenw: -
  368* LDirtDessert                   Valenw | landscape\sand\Sand06.dds                                      | Dirt               | Valenw: -
  353* LDirtDessertDUPLICATE001       Valenw | landscape\sand\Sand03.dds                                      | Dirt               | Valenw: -
  342  LReachGrass01                  Skyrim | Landscape\ReachGrass01.dds                                     | Grass              | van: ReachGrass02,ReachGrass01,TundraGrass03
  337  LPineForest03NoGrass           Skyrim | Landscape\PineForest03.dds                                     | Grass              | van: -
  217* LPineForestDUPLICATE005        Valenw | Landscape\PineForest03.dds                                     | Grass              | Valenw: FernGrass01,SnowGrass01Forest
  157  LDirt01                        Skyrim | Landscape\Dirt01.dds                                           | Dirt               | van: -
  147  LFallForestLeaves01            Skyrim | Landscape\FallForestLeaves01.dds                               | Grass              | van: - ; TS: TropicalGrassPlant01
  137* LDirtDUPLICATE005              Valenw | TEXTUREPACK\landscape\mountains\mountainslab01.dds             | Dirt               | Valenw: -
  122  LReachMoss01                   Skyrim | Landscape\ReachMoss01.dds                                      | Grass              | van: - ; TS: TropicalGrass01
  118* LDirtDUPLICATE004              Valenw | LERock17.dds                                                   | Dirt               | Valenw: -
  103* LDirtDUPLICATE003              Valenw | LERock06.dds                                                   | Dirt               | Valenw: -
   50  LDirt02                        Skyrim | Landscape\Dirt02.dds                                           | Dirt               | van: - ; TS: ForestGrass01
   48  LFallForestGrass01NoGrass      Skyrim | Landscape\FallForestGrass01.dds                                | Grass              | van: -
   34  LDLC01SoulCairnRock01          Dawngu | DLC01\Landscape\SoulCairnRock01.dds                            | Gravel             | van: RockGrass01
   29  LCoastBeach02                  Skyrim | Landscape\CoastBeach02.dds                                     | Sand               | van: -

### C. King of the Murkmire LTEX (all 23) with layer counts in ArgoniaWorld
 8101  LALPARiverBottom01             King o | Landscape\RiverMud.dds                                         | BrokenStone        | King o: WaterKelpGrass01,WaterKelpGrass02,RockGrassWater01
 3734  LALPAMud01Reeds                King o | argonia\landscape\rivermud.dds                                 | Mud                | King o: ALPAGrassReeds01,ALPAGrassReeds02,ALPAGrassReeds03,ALPAGrassReeds04
14509  LALPAMarshGrass                King o | argonia\landscape\CTQ_Grass_Lush01.dds                         | Grass              | King o: ALPAGrassFern01,ALPAGrassRams01,ALPAGrassNettles01,ALPAGrassLupin01,ALPAGrassLupin02,ALPAGrassFern03
   12  LALPASilt01                    King o | argonia\landscape\dirt02.dds                                   | Sand               | King o: -
  808  LALPAMudSand01                 King o | _ResourcePack\Landscape\SandWet01_d.dds                        | Mud                | King o: BeachGrass01,BeachGrass02
   28  LALPAMud01LongGrass            King o | argonia\landscape\rivermud.dds                                 | Mud                | King o: ALPAGrassLong03B
 4937  LALPAMud01                     King o | argonia\landscape\rivermud.dds                                 | Mud                | King o: -
    1  LALPAMud01WildSaltrice         King o | argonia\landscape\rivermud.dds                                 | Mud                | King o: ALPAGrassWildSaltrice01,ALPAGrassWildSaltrice02,ALPAGrassWildSaltrice03,ALPAGrassWildSaltrice04
  481  LALPARiverBottom01TallGrass    King o | Landscape\RiverMud.dds                                         | BrokenStone        | King o: ALPAGrassLong03B
 1280  LALPARainforest                King o | argonia\landscape\CTQ_Undergrowth_01.dds                       | Grass              | King o: ForestGrass01,ReachGrass01,ALPAGrassFern02
   40  LALPAMarshGrassFern            King o | argonia\landscape\CTQ_Grass_Lush01.dds                         | Grass              | King o: FernGrass01,ReachGrass01,ReachGrass02
  910  LALPARainforestNG              King o | argonia\landscape\CTQ_Undergrowth_01.dds                       | Grass              | King o: -
  721  LALPAMarshGrassNG              King o | argonia\landscape\CTQ_Grass_Lush01.dds                         | Grass              | King o: -
    1  LALPAMud01Ferns                King o | argonia\landscape\rivermud.dds                                 | Mud                | King o: FernGrass01
  163  LALPAMudSand01NG               King o | _ResourcePack\Landscape\SandWet01_d.dds                        | Mud                | King o: -
    0  LALPAANullTexture              King o | Landscape\ReachMoss01.dds                                      | Grass              | King o: ReachGrass01,ALPAGrassButtercup01,ALPAGrassViolet01
    1  LALPAMarshMud01Road            King o | _ResourcePack\Landscape\Roads\Road01MarshMud02_d.dds           | Mud                | King o: -
    4  LALPAMarshMud01                King o | _ResourcePack\Landscape\MarshMud02_d.dds                       | Mud                | King o: -
  546  LALPAMarshMud02                King o | _ResourcePack\Landscape\MarshMud01_d.dds                       | Mud                | King o: -
  220  LALPAMarshGrassHeather         King o | argonia\landscape\CTQ_Grass_Lush01.dds                         | Grass              | King o: ALPAGrassFern01,ALPAGrassHeather01,ALPAGrassHeather02
   80  LALPARainforestLow             King o | argonia\landscape\CTQ_JungleGrass01_d.dds                      | Grass              | King o: ForestGrass01,ReachGrass01,ALPAGrassFern01
   67  LALPARainforestLowNG           King o | argonia\landscape\CTQ_JungleGrass01_d.dds                      | Grass              | King o: -
   11  LALPAMarshGrassLow             King o | argonia\landscape\CTQ_Grass_Lush01.dds                         | Grass              | King o: ForestGrass01,ReachGrass01,ALPAGrassFern01,ALPAGrassFern03

### D. Tropical Skyrim LTEX overrides (22) and Depths LTEX (8)
      LSnowRocks01wGrass             Skyrim | Landscape\SnowRocks01.dds                                      | Snow               | van: RockGrassSnow01 ; TS: RockGrass01
      LCoastOceanFloor01NoGrass      Skyrim | Landscape\CoastOceanFloor01.dds                                | Mud                | van: - ; Dep: TBPRockGrassWater02,TBPWaterCoralGrass02,TBPRockGrassWater03
      LFallForestGrass01NoFern       Skyrim | Landscape\FallForestGrass01.dds                                | Grass              | van: FallForestGrass01 ; TS: TropicalGrassPlant01,FallForestGrass01
      LTundra01NoGrass               Skyrim | Landscape\tundra01.dds                                         | Sand               | van: - ; TS: -
      LRiverMud01NoGrass             Skyrim | Landscape\RiverMud.dds                                         | Mud                | van: - ; Dep: TBPCoastDriftwood2,TBPCoastDriftwood,TBP_Algae01,TBPRockGrassWater03,TBPRockGrassWater02
      LCoastBeachGrass01             Skyrim | Landscape\CoastBeachGrass01.dds                                | Grass              | van: BeachGrass01,BeachGrass02 ; TS: -
      LCoastOceanFloor01             Skyrim | Landscape\CoastOceanFloor01.dds                                | Mud                | van: WaterKelpGrass01,WaterCoralGrass01,RockGrassWater01 ; Dep: WaterKelpGrass01,WaterCoralGrass01,TBPRockGrassWater02,TBPSeaweed02Test,TBPWaterKelpGrass01,TBPSeaweed06Var1,TBP_coralsmall01
      LCoastBeach01                  Skyrim | Landscape\CoastBeach01.dds                                     | Sand               | van: - ; Dep: TBPRockGrassWater02,TBPRockGrassWater03
      LFrozenMarshDirtSlopes01       Skyrim | Landscape\FrozenMarshDirtSlopes01.dds                          | Dirt               | van: - ; TS: CattailGrass01
      LSnow02                        Skyrim | Landscape\Snow02.dds                                           | Snow               | van: - ; TS: FallForestGrass02,TropicalGrassPlant01,TropicalGrassPlant02
      LSnowRocks01                   Skyrim | Landscape\SnowRocks01.dds                                      | Snow               | van: - ; TS: RockGrass01
      LFallForestGrass01             Skyrim | Landscape\FallForestGrass01.dds                                | Grass              | van: FallForestGrass01,FallForestGrass02 ; TS: TropicalGrassPlant01,FallForestGrass01,FallForestGrass02
      LFallForestDirt01              Skyrim | Landscape\FallForestDirt01.dds                                 | Dirt               | van: - ; TS: FallForestGrass02
      LFallForestLeaves01            Skyrim | Landscape\FallForestLeaves01.dds                               | Grass              | van: - ; TS: TropicalGrassPlant01
      LReachDirt01                   Skyrim | Landscape\ReachDirt01.dds                                      | Dirt               | van: - ; TS: TropicalGrassPlant02,TropicalGrassPlant01
      LReachMoss01                   Skyrim | Landscape\ReachMoss01.dds                                      | Grass              | van: - ; TS: TropicalGrass01
      LTundra02                      Skyrim | Landscape\Tundra02.dds                                         | Dirt               | van: - ; TS: RockGrass01
      LFieldGrass01NoGrass           Skyrim | Landscape\FieldGrass01.dds                                     | Sand               | van: - ; TS: -
      LTundra01                      Skyrim | Landscape\tundra01.dds                                         | Sand               | van: TundraGrass04,TundraGrass03 ; TS: RockGrass01,TundraGrass04,TundraGrass03
      LPineForest03                  Skyrim | Landscape\PineForest03.dds                                     | Grass              | van: FernGrass01,SnowGrass01Forest ; TS: FallForestGrass02,TropicalGrass01,TropicalGrassPlant01
      LPineForest02                  Skyrim | Landscape\PineForest02.dds                                     | Grass              | van: ForestGrass01,SnowGrass01Forest,ForestGrass02 ; TS: TropicalGrass01,TropicalGrassPlant02,TropicalGrassPlant01
      LFieldGrass02                  Skyrim | Landscape\FieldGrass02.dds                                     | Grass              | van: FieldGrass01,FieldGrass02 ; TS: TropicalGrassPlant01,TropicalGrassPlant02,FieldGrass02
      LFieldGrass01                  Skyrim | Landscape\FieldGrass01.dds                                     | Sand               | van: TundraGrass01,TundraGrass04 ; TS: RockGrass01,TundraGrass01
      LRiverMud01                    Skyrim | Landscape\RiverMud.dds                                         | Mud                | van: WaterKelpGrass01,WaterKelpGrass02 ; Dep: TBP_Algae01,TBPCoastDriftwood2,TBPCoastDriftwood,TBPSeaweed11,WaterKelpGrass02,TBPRockGrassWater02,TBPRockGrassWater03
      LRiverBottom01                 Skyrim | Landscape\RiverBottom.dds                                      | BrokenStone        | van: WaterKelpGrass01,RockGrassWater01,WaterKelpGrass02 ; Dep: TBPWaterKelpGrass01,TBPRiverKelpGrass02,TBPRiverKelpGrass01,TBPRockGrassWater03,TBPRockGrassWater02,RockGrassWater01
      LRiverbedEdge01                Skyrim | Landscape\RiverbedEdge.dds                                     | Stone              | van: - ; Dep: TBPRockGrass01
      LDirt02                        Skyrim | Landscape\Dirt02.dds                                           | Dirt               | van: - ; TS: ForestGrass01
      LSnow01                        Skyrim | Landscape\Snow01.dds                                           | Grass              | van: - ; TS: TropicalGrass01,RockGrass01,ForestGrass01
      LGrassSnow01                   Skyrim | Landscape\GrassSnow01.dds                                      | Grass              | van: SnowGrass01Light,SnowGrass02 ; TS: TropicalGrassPlant02,TropicalGrassPlant01,SnowGrass02
      TBPCoralForest01Grass          Depths | Landscape\CoastOceanFloor01.dds                                | Mud                | Dep: TBPRockGrassWater02,TBPRockGrassWater03,TBPWaterCoralGrass03,TBP_coralsmall02

```

## Appendix B. Every WATR (64 forms; TS rows shown where TS overrides)

```
name | form | plugins | flags | shallow RGB | deep RGB | reflect RGB | opacity | fog-above near/far amt | fog-under near/far amt | refraction | reflectivity | fresnel | flowmap-scale | linear velocity xy
BlackMarshRiverWaterFlowBlend | 32383B | King of th | EnableFlowmap,BlendNormals | (130,116,34,0) | (61,95,52,0) | (97,130,72,0) | 50 | -10/150 0.7 | -1400/2000 0.9 | 40 | 0.8 | 0.1 | 1 | (2.54,1.35)
BlackmarshRiverWaterFlowNE | 323839 | King of th | EnableFlowmap,BlendNormals | (130,116,34,0) | (61,95,52,0) | (97,130,72,0) | 50 | -10/150 0.7 | -1400/2000 0.9 | 40 | 0.8 | 0.1 | 1 | (2.54,1.35)
BlackmarshRiverWaterFlowNW | 323838 | King of th | EnableFlowmap,BlendNormals | (130,116,34,0) | (61,95,52,0) | (97,130,72,0) | 50 | -10/150 0.7 | -1400/2000 0.9 | 40 | 0.8 | 0.1 | 1 | (-1.96,2)
BlackmarshRiverWaterFlowSE | 323837 | King of th | EnableFlowmap,BlendNormals | (130,116,34,0) | (61,95,52,0) | (97,130,72,0) | 50 | -10/150 0.7 | -1400/2000 0.9 | 40 | 0.8 | 0.1 | 1 | (1.8,-2.2)
BlackmarshRiverWaterFlowSW | 32383A | King of th | EnableFlowmap,BlendNormals | (130,116,34,0) | (61,95,52,0) | (97,130,72,0) | 50 | -10/150 0.7 | -1400/2000 0.9 | 40 | 0.8 | 0.1 | 1 | (-1.8,-2.2)
BlackreachWater | 048C2B | Update.esm | 0 | (40,72,89,0) | (21,104,102,0) | (38,63,74,0) | 100 | 0/290 0.95 | -1300/1880 0.6 | 39 | 0.55 | 0.35 | 0 | (0.168,0.3475)
ClearInteriorWaterAnkleHeightStill | 0CB11F | Update.esm | 0 | (67,80,70,0) | (36,47,38,0) | (44,50,47,0) | 0 | 0/120 0 | 232/1000 0.45 | 27 | 0.58 | 0.05 | 0 | (0,0)
CreekWaterFlow | 015429 | Update.esm | 0 | (71,78,67,0) | (35,35,24,0) | (71,92,116,0) | 0 | 20/160 0.87 | -800/1000 0.75 | 8 | 1 | 0 | 0 | (0,0)
CreekWaterFlowSE | 106A20 | Update.esm | 0 | (71,78,67,0) | (35,35,24,0) | (55,65,80,0) | 0 | 20/160 0.87 | -800/1000 0.75 | 8 | 1 | 0.15 | 0 | (0.6955,-0.7185)
CreekWaterFlowSW | 106A24 | Update.esm | 0 | (71,78,67,0) | (35,35,24,0) | (55,65,80,0) | 0 | 20/160 0.87 | -800/1000 0.75 | 8 | 1 | 0.15 | 0 | (-0.9782,-0.695)
DeepwoodRedoubtWater | 0E3812 | Update.esm | 0 | (32,47,39,0) | (4,17,13,0) | (117,135,138,0) | 50 | 0/110 1 | -2250/1670.001 1 | 9 | 0.58 | 0.2 | 0 | (-0.7282,-0.3313)
DefaultBlackmarshWater | 184260 | King of th | 0 | (130,116,34,0) | (61,95,52,0) | (97,130,72,0) | 30 | 0/110 0.93 | -10000/1000 1 | 9 | 1 | 0.05 | 1 | (0.151,0.285)
DefaultCreekWater | 015427 | Update.esm | 0 | (71,78,67,0) | (35,35,24,0) | (55,65,80,0) | 0 | 10/89.999 0.71 | -800/1000 0.75 | 9 | 1 | 0.02 | 0 | (0.2267,0.3596)
DefaultHistSapWater | 1655DB | King of th | 0 | (162,82,2,0) | (141,60,5,0) | (135,77,12,0) | 100 | 0/140.001 1 | -40/140.001 1 | 42 | 0.79 | 0.07 | 1 | (0,0)
DefaultIchorWater | 3D8711 | King of th | 0 | (37,126,64,0) | (0,64,0,0) | (45,126,20,0) | 100 | 0/140.001 1 | -40/140.001 1 | 42 | 0.79 | 0.07 | 1 | (0,0)
DefaultIntWaterAnkleHeightStill | 0CC7B7 | Update.esm | 0 | (44,58,55,0) | (6,9,9,0) | (0,0,0,0) | 100 | 0/120 0.56 | 0/1000 1 | 50 | 0.6 | 0.05 | 0 | (0,0)
DefaultIntWaterWaistHeightFlow | 033DA7 | Update.esm | 0 | (58,78,73,0) | (6,9,9,0) | (0,0,0,0) | 100 | 0/300 0.56 | 0/1000 1 | 64 | 1 | 0.05 | 0 | (0,0)
DefaultIntWaterWaistHeightStill | 0CC7B4 | Update.esm | 0 | (44,58,55,0) | (6,9,9,0) | (0,0,0,0) | 100 | 0/300 0.56 | 0/1000 1 | 50 | 0.6 | 0.05 | 0 | (0,0)
DefaultMarshWater | 105CC3 | Skyrim.esm | 0 | (37,52,37,0) | (5,16,5,0) | (103,122,117,0) | 30 | 0/110 0.93 | -10000/1000 1 | 9 | 1 | 0.05 | 0 | (0.151,0.285)
DefaultMarshWater | 105CC3 | Update.esm | 0 | (37,52,37,0) | (5,16,5,0) | (103,122,117,0) | 30 | 0/110 0.93 | -10000/1000 1 | 9 | 1 | 0.05 | 0 | (0.151,0.285)
DefaultMarshWater | 105CC3 | Tropical S | 0 | (56,53,37,0) | (77,61,36,0) | (113,91,51,0) | 30 | 0/110 0.93 | -10000/1000 1 | 9 | 0.23 | 0.05 | 1 | (0.151,0.285)
DefaultMarshWaterTransition | 105CC4 | Skyrim.esm | 0 | (37,52,37,0) | (5,16,5,0) | (103,122,117,0) | 30 | 0/110 0.93 | -4000/1200 1 | 9 | 1 | 0.05 | 0 | (0.071,0.37)
DefaultMarshWaterTransition | 105CC4 | Update.esm | 0 | (37,52,37,0) | (5,16,5,0) | (103,122,117,0) | 30 | 0/110 0.93 | -4000/1200 1 | 9 | 1 | 0.05 | 0 | (0.071,0.37)
DefaultMarshWaterTransition | 105CC4 | Tropical S | 0 | (49,56,37,0) | (56,67,46,0) | (103,91,51,0) | 30 | 0/110 0.93 | -4000/1200 1 | 9 | 0.23 | 0.05 | 1 | (0.071,0.37)
DefaultRiverWater | 105CE1 | Update.esm | 0 | (38,39,24,0) | (5,14,18,0) | (119,140,157,0) | 50 | -10/150 0.7 | -1400/2000 0.9 | 40 | 0.8 | 0.11 | 0 | (-0.5,1.29)
DefaultVolcanicWater | 0713C4 | Skyrim.esm | 0 | (130,116,34,0) | (61,95,52,0) | (97,130,72,0) | 93 | 0/160 1 | -40/140.001 1 | 42 | 0.98 | 0.07 | 0 | (0.2619,-0.1462)
DefaultVolcanicWater | 0713C4 | Update.esm | 0 | (130,116,34,0) | (61,95,52,0) | (97,130,72,0) | 93 | 0/160 1 | -40/140.001 1 | 42 | 0.98 | 0.07 | 0 | (0.2619,-0.1462)
DefaultVolcanicWater | 0713C4 | Tropical S | 0 | (111,103,53,0) | (119,101,28,0) | (118,116,84,0) | 93 | 0/140 1 | -40/140.001 1 | 42 | 0.98 | 0.07 | 1 | (0.2619,-0.1462)
DefaultWater | 000018 | Skyrim.esm | 0 | (37,52,37,0) | (5,16,5,0) | (103,122,117,0) | 30 | 0/110 0.93 | -500/1600 0.9 | 9 | 1 | 0.05 | 0 | (0.22,0.22)
DefaultWater | 000018 | Update.esm | 0 | (38,39,24,0) | (5,14,18,0) | (119,140,157,0) | 50 | -10/150 0.7 | -500/1600 0.9 | 40 | 0.8 | 0.1 | 1 | (0.22,0.22)
DefaultWater | 000018 | Tropical S | 0 | (81,174,165,0) | (28,104,140,0) | (103,122,117,0) | 30 | -100/580 1 | -500/1600 0.9 | 9 | 0.5 | 0.05 | 1 | (0.22,0.22)
DefaultWaterCold | 001C18 | Dawnguard. | 0 | (45,94,96,0) | (31,55,58,0) | (103,122,117,0) | 30 | 0/110 0.93 | -500/1600 0.9 | 9 | 1 | 0.05 | 0 | (0.22,0.22)
DefaultWaterColdDUPLICATE000 | 002932 | Dawnguard. | 0 | (45,94,96,0) | (31,55,58,0) | (103,122,117,0) | 30 | 0/110 0.93 | -500/1600 0.9 | 9 | 1 | 0.05 | 0 | (0.22,0.22)
DefaultWaterFlow | 001234 | Update.esm | EnableFlowmap | (37,52,37,0) | (5,16,5,0) | (103,122,117,0) | 30 | 0/110 0.93 | -500/1600 0.9 | 9 | 1 | 0.05 | 1 | (0.22,0.22)
DefaultWaterFlowBlend | 001235 | Update.esm | EnableFlowmap,BlendNormals | (38,39,24,0) | (5,14,18,0) | (119,140,157,0) | 50 | -10/150 0.7 | -500/1600 0.9 | 41 | 0.8 | 0.1 | 1 | (0.22,0.22)
DefaultWaterKatariahWorld | 10CC8E | Update.esm | 0 | (37,52,37,0) | (5,16,5,0) | (103,122,117,0) | 30 | 0/110 0.93 | -1000/1000 1 | 9 | 1 | 0.05 | 0 | (0.22,0.22)
DefaultWaterNW | 10639F | Update.esm | 0 | (37,52,37,0) | (5,16,5,0) | (103,122,117,0) | 30 | 0/110 1 | -500/1600 0.9 | 9 | 1 | 0.05 | 0 | (0.387,0.57)
DLC01DarkFallCaveDarkStillWater | 00C7C2 | Dawnguard. | 0 | (31,33,33,0) | (12,12,12,0) | (10,10,5,0) | 75 | 0/30 1 | -800/1900.001 0.96 | 15 | 0.28 | 0 | 0 | (0,0)
DLC1BloodWater | 0042B7 | Dawnguard. | 0 | (69,18,14,0) | (12,4,3,0) | (33,24,22,0) | 100 | 0/30 1 | -50/-300 1 | 79 | 0.55 | 0.07 | 0 | (0.2,0.2)
DLC1DungeonWaterFlow | 006AEB | Dawnguard. | 0 | (37,52,37,0) | (5,16,5,0) | (102,125,100,0) | 30 | 0/110 0.37 | -1000/1000 1 | 14 | 0.78 | 0.08 | 0 | (0,0)
DLC1FrostreachWaterFlowNE | 00CE72 | Dawnguard. | 0 | (23,41,43,0) | (2,67,70,0) | (119,140,157,0) | 50 | -290/720 0.92 | -7100/3190 0.7 | 40 | 0.8 | 0.1 | 0 | (1.75,0.75)
DLC1FrostreachWaterFlowSE | 00CE71 | Dawnguard. | 0 | (23,41,43,0) | (2,67,70,0) | (119,140,157,0) | 50 | -290/720 0.92 | -7100/3190 0.7 | 40 | 0.8 | 0.1 | 0 | (1.8,-2.2)
DLC1FrostreachWaterNoFlow | 019C98 | Dawnguard. | 0 | (23,41,43,0) | (2,67,70,0) | (119,140,157,0) | 50 | -290/720 0.92 | -7100/3190 0.7 | 40 | 0.8 | 0.1 | 0 | (0,0)
DLC1WaterFastFlow | 006AFD | Dawnguard. | 0 | (61,70,60,0) | (9,11,9,0) | (30,40,37,0) | 81 | 0/530 1 | -2750/2850 0.75 | 62 | 0.52 | 0.22 | 0 | (3,-3)
DLC2_MQDwarven_AnimWaterType | 0173B6 | Dragonborn | 0 | (44,58,55,0) | (6,9,9,0) | (0,0,0,0) | 100 | 0/300 0.56 | 0/1000 1 | 50 | 0.6 | 0.05 | 0 | (0,0)
DLC2ApocryphaWater | 01DFF1 | Dragonborn | CausesDamage | (21,24,20,0) | (1,1,2,0) | (225,244,162,0) | 100 | -10000/-9200 1 | -10000/-9350 1 | 4 | 1 | 1 | 0 | (0.22,0.22)
DLC2ApocryphaWaterSmall | 03731A | Dragonborn | CausesDamage | (20,22,18,0) | (0,0,0,0) | (255,0,255,0) | 100 | 0/110 0 | -500/1600 0.93 | 4 | 1 | 1 | 0 | (0.22,0.22)
DLC2ApocryphaWaterTamriel | 02ADEC | Dragonborn | 0 | (15,15,15,0) | (0,0,0,0) | (0,0,0,0) | 100 | 0/10 1 | -500/1600 0.93 | 4 | 0.18 | 0 | 0 | (0.22,0.22)
DLC2DefaultWater | 028644 | Dragonborn | 0 | (24,35,30,0) | (5,16,5,0) | (103,122,117,0) | 30 | -30/30 0.64 | -500/1600 0.9 | 70 | 1 | 0.05 | 0 | (0.22,0.22)
DLC2dunKolbjornBlood | 01DB5F | Dragonborn | 0 | (69,18,14,0) | (12,4,3,0) | (33,24,22,0) | 100 | 0/30 1 | -50/-300 1 | 79 | 0.55 | 0.07 | 0 | (0.2,0.2)
DLC2StandingStoneWater | 03805D | Dragonborn | 0 | (71,78,67,0) | (35,35,24,0) | (55,65,80,0) | 0 | 20/160 0.87 | -800/1000 0.75 | 8 | 1 | 0.15 | 0 | (0.6955,-0.7185)
dunSleepingTreeCampWater | 0261EA | Update.esm | 0 | (20,31,50,0) | (57,53,113,0) | (53,62,85,0) | 45 | -10/70 0.31 | 0/1450 0.83 | 9 | 0.21 | 0.29 | 0 | (0.19,-0.08)
HelgenWater | 0C1D45 | Update.esm | 0 | (53,49,36,0) | (5,16,5,0) | (131,122,95,0) | 37 | 0/70 0.3 | -1000/-172 1 | 14 | 0.91 | 0.17 | 0 | (0,0)
HorseTroughWater01 | 0F762D | Update.esm | 0 | (55,64,57,0) | (5,16,5,0) | (103,122,117,0) | 100 | 220/4710 0.75 | -1000/1000 1 | 24 | 0.42 | 0.14 | 0 | (0,0)
LavaSettings | 014B86 | Dawnguard. | 0 | (255,255,128,0) | (255,134,13,0) | (253,253,253,0) | 100 | 0/10 1 | 49000/50000 1 | 48 | 1 | 0.23 | 0 | (0.168,0.3475)
LavaSettingsDUPLICATE001 | 014B88 | Dawnguard. | 0 | (221,255,28,0) | (255,134,13,0) | (253,253,253,0) | 100 | 0/0 0.95 | -1300/1880 0.6 | 49 | 1 | 0.86 | 0 | (0.168,0.3475)
LavaWater | 051353 | Update.esm | 0 | (98,0,0,0) | (0,0,0,0) | (242,253,49,0) | 100 | -1000/1000 0.99 | 0/1000 1 | 10 | 0.84 | 0.63 | 0 | (0,0)
MarkarthWater | 07A5F6 | Update.esm | 0 | (37,52,37,0) | (5,16,5,0) | (102,125,100,0) | 30 | 0/110 1 | -1000/1000 1 | 14 | 0.78 | 0.08 | 0 | (0,0)
MarkarthWaterFlow | 10B1D7 | Update.esm | 0 | (37,52,37,0) | (5,16,5,0) | (102,125,100,0) | 30 | 0/120 0.37 | -1000/1000 1 | 14 | 0.78 | 0.08 | 0 | (0,0)
MurkyWater | 062A72 | Update.esm | 0 | (26,19,19,0) | (9,9,6,0) | (32,35,27,0) | 100 | 0/60 0.75 | -1000/1000 1 | 35 | 0.55 | 0.25 | 0 | (0,0)
PuddleWater | 04CC4B | Update.esm | 0 | (11,13,12,0) | (11,15,15,0) | (0,0,0,0) | 100 | 0/10 0.47 | 0/1000 1 | 17 | 0.51 | 0.2 | 1 | (0,0)
PuddleWaterFlow | 0FE092 | Update.esm | 0 | (11,13,12,0) | (11,15,15,0) | (0,0,0,0) | 100 | 0/10 0.47 | 0/1000 1 | 17 | 0.51 | 0.2 | 1 | (0,0)
PuddleWaterLiteFog | 0FD0DB | Update.esm | 0 | (11,13,12,0) | (11,15,15,0) | (0,0,0,0) | 100 | 0/10 0.23 | 0/1000 1 | 17 | 0.71 | 0.2 | 1 | (0,0)
RiftenWater | 0F2407 | Update.esm | 0 | (36,53,39,0) | (16,15,5,0) | (106,120,105,0) | 30 | -10/80 1 | -10000/1600 1 | 9 | 0.58 | 0.05 | 0 | (0.19,0.19)
RiverWaterFlow | 001232 | Update.esm | EnableFlowmap | (38,39,24,0) | (5,14,18,0) | (119,140,157,0) | 50 | -10/150 0.7 | -1400/2000 0.9 | 40 | 0.8 | 0.1 | 1 | (0,0)
RiverWaterFlowBlend | 001233 | Update.esm | EnableFlowmap,BlendNormals | (38,39,24,0) | (5,14,18,0) | (119,140,157,0) | 50 | -10/150 0.7 | -1400/2000 0.9 | 40 | 0.8 | 0.1 | 1 | (2.54,1.35)
RiverWaterFlowNE | 0E717C | Update.esm | 0 | (38,39,24,0) | (5,14,18,0) | (119,140,157,0) | 50 | -10/150 0.7 | -1400/2000 0.9 | 40 | 0.8 | 0.1 | 0 | (2.54,1.35)
RiverWaterFlowNW | 1063AA | Update.esm | 0 | (38,39,24,0) | (5,14,18,0) | (119,140,157,0) | 50 | -10/150 0.7 | -1400/2000 0.9 | 40 | 0.8 | 0.1 | 0 | (-1.96,2)
RiverWaterFlowSE | 108AC7 | Update.esm | 0 | (38,39,24,0) | (5,14,18,0) | (119,140,157,0) | 50 | -10/150 0.7 | -1400/2000 0.9 | 40 | 0.8 | 0.1 | 0 | (1.8,-2.2)
ShadowmereWater | 0F4573 | Update.esm | 0 | (0,0,0,0) | (0,0,0,0) | (0,0,0,0) | 100 | 0/40 1 | -1000/1000 1 | 15 | 0.28 | 0.03 | 0 | (0,0)
WRWaterFlow | 085FC8 | Update.esm | 0 | (34,40,32,0) | (18,27,16,0) | (73,92,71,0) | 0 | -10/130 0.57 | 232/1000 0.45 | 58 | 0.87 | 0.07 | 0 | (0,0)
WRWaterType | 074EEA | Update.esm | 0 | (67,80,70,0) | (36,47,38,0) | (44,50,47,0) | 0 | 0/160 0 | -500/900 0.45 | 65 | 0.9 | 0.2 | 0 | (0,0)
```

## Appendix C. Tropical Skyrim base-model swaps for placed Tamriel refs (refs, base editor ID, vanilla model -> TS model)

```
 12134 TreeThicket01              landscape\plants\thicket01.nif  ->  plants\tropical\manfern.nif
  6193 TreeThicket01Snow          landscape\plants\thicket01snow.nif  ->  plants\tamira\new plants\bush03b.nif
  4755 TreeDeadShrub              landscape\plants\deadshrub01.nif  ->  landscape\trees\tropical\fanpalm4.nif
  4563 TreePineForest05           landscape\trees\treepineforest05.nif  ->  landscape\trees\tropical\gkbtreeofwolene.nif
  4138 TreePineForest03           landscape\trees\treepineforest03.nif  ->  landscape\trees\tropical\gkbjungletreenew8.nif
  3368 TreePineForestSnow05       landscape\trees\treepineforestsnow05.nif  ->  landscape\trees\tropical\gkbtreeaspen05.nif
  3302 TreeDeadShrubSnow          landscape\plants\deadshrub01snow.nif  ->  landscape\trees\tropical\gkbjunipertree.nif
  3209 TreePineForestSnow03       landscape\trees\treepineforestsnow03.nif  ->  landscape\trees\tropical\gkbtreeaspen02.nif
  2933 TreeFallForestShrub01      landscape\plants\fallforestshrub01.nif  ->  plants\citsflorabamboo01.nif
  2868 TreePineForestSnow04       landscape\trees\treepineforestsnow04.nif  ->  landscape\trees\tropical\gkbtreeaspen04.nif
  2764 TreePineForest02           landscape\trees\treepineforest02.nif  ->  landscape\trees\tropical\anvil_palm_trunk.nif
  2702 TreePineForestSnow02       landscape\trees\treepineforestsnow02.nif  ->  landscape\trees\tropical\anvil_palm_trunk.nif
  2323 TreePineForest04           landscape\trees\treepineforest04.nif  ->  landscape\trees\tropical\anvilgianttrunk.nif
  2141 TreeFallForestShrub02      landscape\plants\fallforestshrub02.nif  ->  landscape\trees\tropical\palmtree3.nif
  1967 TreePineShrub02            landscape\plants\pineshrub02.nif  ->  landscape\trees\tropical\gkbtreeaspenbamboo06.nif
  1774 TreePineForestSnowL05      landscape\trees\treepineforestsnowl05.nif  ->  landscape\trees\tropical\gkbtreeaspenred02.nif
  1750 TreeAspen05                landscape\trees\treeaspen05.nif  ->  landscape\trees\tropical\gkbtreeaspenbamboo01.nif
  1586 TreeAspen06                landscape\trees\treeaspen06.nif  ->  landscape\trees\tropical\gkbtreeaspenbamboo04.nif
  1517 TreePineForestSnowL03      landscape\trees\treepineforestsnowl03.nif  ->  landscape\trees\tropical\gkbtreeaspenorange03.nif
  1488 TreePineShrub02Snow        landscape\plants\pineshrub02snow.nif  ->  plants\tamira\new plants\bush04.nif
  1400 TreePineShrub01Snow        landscape\plants\pineshrub01snow.nif  ->  landscape\trees\tropical\gkbjunipertree.nif
  1393 TreeAspen02                landscape\trees\treeaspen02.nif  ->  landscape\trees\tropical\gkbtreeaspenbamboo06.nif
  1393 TreeAspen03                landscape\trees\treeaspen03.nif  ->  landscape\trees\tropical\gkbtreeaspenbamboo05.nif
  1392 TreePineForestSnowL02      landscape\trees\treepineforestsnowl02.nif  ->  landscape\trees\tropical\gkbtreeaspenred03.nif
  1332 TreeFloraSnowberry01Snow   plants\florasnowberry01snow.nif  ->  plants\tamira\new plants\grassplant01.nif
  1326 TreeReachShrub02           landscape\plants\reachshrub02.nif  ->  landscape\trees\tropical\gkbjungletreenew18v2.nif
  1276 TreeVineMaple01Snow        landscape\plants\vinemaple01snow.nif  ->  landscape\trees\tropical\gkbvinemaple01snow.nif
  1268 TreeReachBush02            landscape\plants\reachbush02.nif  ->  landscape\trees\tropical\gkbjungletreenew2v2.nif
  1261 TreePineForestSnowL04      landscape\trees\treepineforestsnowl04.nif  ->  landscape\trees\tropical\gkbtreeaspengreen05.nif
  1167 TreeFloraMountainFlower02Blue plants\floramountainflower02blue.nif  ->  plants\tamira\new plants\bush03b.nif
  1155 TreeFloraMountainFlower02Purple plants\floramountainflower02purple.nif  ->  plants\tamira\new plants\bush03a.nif
  1095 TreeSwordFernCluster02     landscape\plants\swordferncluster02.nif  ->  plants\tamira\new plants\tropicalplant01.nif
  1055 TreeAspen01                landscape\trees\hodaspen01gkb.nif  ->  landscape\trees\tropical\gkbtreeaspenbamboo06.nif
   980 TreeFloraJuniper01         plants\florajuniper01.nif  ->  landscape\trees\tropical\gkbjungletreenew8.nif
   965 TreePineShrub01            landscape\plants\pineshrub01.nif  ->  landscape\trees\tropical\gkbtreeaspenbamboo01.nif
   904 TreeReachCliffTree01       landscape\trees\reachclifftree01.nif  ->  landscape\trees\tropical\gkbreachclifftree01.nif
   882 TreeReachShrub01           landscape\plants\reachshrub01.nif  ->  landscape\trees\tropical\palmtree4.nif
   875 TreeReachBranchPile02      landscape\trees\reachbranchpile02.nif  ->  landscape\trees\tropical\gkbreachbranchpile02.nif
   795 TreeFloraThistle01         plants\florathistle01.nif  ->  plants\tamira\new plants\bush04.nif
   775 TreeReachTree01            landscape\trees\reachtree01.nif  ->  landscape\trees\tropical\gkbjungletreenew27v2weeping.nif
   728 TreeReachTree02            landscape\trees\reachtree02.nif  ->  landscape\trees\tropical\anvil_palm_trunk.nif
   720 TreeAspen04                landscape\trees\treeaspen04.nif  ->  plants\citsflorabamboo01.nif
   626 TreeReachBush01            landscape\plants\reachbush01.nif  ->  plants\tamira\new plants\bush01.nif
   577 TreePineShrub03            landscape\plants\pineshrub03.nif  ->  plants\tamira\new plants\palmplant.nif
   564 TreeSwordFernCluster03     landscape\plants\swordferncluster03.nif  ->  plants\tamira\new plants\tropicalplant02.nif
   536 TreePineShrub03Snow        landscape\plants\pineshrub03snow.nif  ->  plants\tamira\new plants\bush01.nif
   458 TreePineForest01           landscape\trees\treepineforest01.nif  ->  landscape\trees\tropical\mangrovereachtree0gkb8.nif
   441 TreeReachCliffTree02       landscape\trees\reachclifftree02.nif  ->  landscape\trees\tropical\gkbreachclifftree02.nif
   306 TreePineForest05Dead       landscape\trees\treepineforestdead05.nif  ->  landscape\trees\tropical\mangrovereachtree0gkb2.nif
   215 TreePineForest04Dead       landscape\trees\treepineforestdead04.nif  ->  landscape\trees\tropical\mangrovereachtree0gkb3.nif
   201 TreePineForest02Dead       landscape\trees\treepineforestdead02.nif  ->  landscape\trees\tropical\mangrovereachtree0gkb8.nif
   174 TreeReachTreeStump01       landscape\trees\reachtreestump01.nif  ->  landscape\trees\tropical\gkbreachtreestump01.nif
   166 TreePineForestSnow01       landscape\trees\treepineforestsnow01.nif  ->  landscape\trees\tropical\gkbtreeaspenred01.nif
   158 TreeSwordFernCluster06     landscape\plants\swordferncluster06.nif  ->  landscape\trees\tropical\mangrovereachtree0gkb8.nif
   154 TreePineForest03Dead       landscape\trees\treepineforestdead03.nif  ->  landscape\trees\tropical\mangrovereachtree0gkb9.nif
   142 TreeSwordFern06            landscape\plants\swordfern06.nif  ->  landscape\trees\tropical\gkbjungletreenew24v2weeping.nif
    80 TreePineForestSnowL01      landscape\trees\treepineforestsnowl01.nif  ->  landscape\trees\tropical\gkbtreeaspenorange03.nif
    46 TreePineForestSnow03Dead   landscape\trees\treepineforestdeadsnow03.nif  ->  landscape\trees\tropical\gkbtreeaspenred05.nif
    28 TreePineForestSnow05Dead   landscape\trees\treepineforestdeadsnow05.nif  ->  landscape\trees\tropical\gkbtreeaspenred01.nif
    11 TreePineForestSnowL02Dead  landscape\trees\treepineforestdeadsnowl02.nif  ->  landscape\trees\tropical\gkbtreeaspenorange02.nif
    11 TreePineForestSnow02Dead   landscape\trees\treepineforestdeadsnow02.nif  ->  landscape\trees\tropical\gkbtreeaspenred03.nif
     9 TreePineForestSnowL03Dead  landscape\trees\treepineforestdeadsnowl03.nif  ->  landscape\trees\tropical\gkbtreeaspenorange03.nif
     9 TreePineForestSnow04Dead   landscape\trees\treepineforestdeadsnow04.nif  ->  landscape\trees\tropical\gkbtreeaspenred01.nif
     5 TreePineForestSnowL05Dead  landscape\trees\treepineforestdeadsnowl05.nif  ->  landscape\trees\tropical\gkbtreeaspenbrown05.nif
     4 TreePineForestSnowL04Dead  landscape\trees\treepineforestdeadsnowl04.nif  ->  landscape\trees\tropical\gkbtreeaspenorange05.nif
     2 TreePineForest01Dead       landscape\trees\treepineforestdead01.nif  ->  landscape\trees\tropical\mangrovereachtree0gkb8.nif
     1 TreePineForestSnowL01Dead  landscape\trees\treepineforestdeadsnowl01.nif  ->  landscape\trees\tropical\gkbtreeaspenorange01.nif

```

## Appendix D. Water-edge bands (texture weight by band; scatter per 100 m2 by band; areas in m2; top 4 forms)

```
===== Morthal swamp (Hjaalmarch) Tamriel (-16, -3, 13, 24) pixels 172865 (0.58 km2) water 19.1%, water comps>=40 px: 17
  tex water   0-2   m n=6834   med h -0.23 m | LFrozenMarshDirtSlopes01 0.59, LRiverMud01 0.21, LCoastBeach01 0.05, LFrozenMarshIce01 0.05
  tex water   2-5   m n=9523   med h -0.57 m | LFrozenMarshDirtSlopes01 0.41, LRiverMud01 0.41, LCoastBeach01 0.05, LRiverBottom01NoGrass 0.04
  tex water   5-10  m n=10383  med h -0.91 m | LRiverMud01 0.52, LFrozenMarshDirtSlopes01 0.27, LRiverBottom01NoGrass 0.10
  tex water  10-20  m n=2552   med h -3.23 m | LRiverMud01 0.37, LRiverBottom01NoGrass 0.24, LRiverMud01NoGrass 0.15, LFrozenMarshDirtSlopes01 0.15
  tex water  20-40  m n=2435   med h -10.17 m | LRiverBottom01NoGrass 0.42, LRiverMud01 0.25, LRiverMud01NoGrass 0.21, LRiverbedEdge01 0.05
  tex water  40-80  m n=1300   med h -9.37 m | LRiverBottom01NoGrass 0.44, LRiverMud01 0.32, LRiverbedEdge01 0.19, LRiverMud01NoGrass 0.05
  tex land    0-2   m n=6528   med h +0.11 m | LFrozenMarshDirtSlopes01 0.55, LFrozenMarshGrass01 0.13, LRiverMud01 0.10, LFrozenMarshIce01 0.07
  tex land    2-5   m n=7995   med h +0.46 m | LFrozenMarshGrass01 0.37, LFrozenMarshDirtSlopes01 0.33, LFrozenMarshIce01 0.07, LRiverMud01 0.05
  tex land    5-10  m n=14643  med h +1.26 m | LFrozenMarshGrass01 0.46, LFrozenMarshDirtSlopes01 0.17, LFrozenMarshGrass01NoGrass 0.08, LFrozenMarshIce01 0.08
  tex land   10-20  m n=18477  med h +2.97 m | LFrozenMarshGrass01 0.38, LFrozenMarshDirtSlopes01 0.14, LFrozenMarshIce01 0.12, LFrozenMarshGrass01NoGrass 0.09
  tex land   20-40  m n=23731  med h +6.97 m | LFrozenMarshGrass01 0.25, LSnow01 0.15, LFrozenMarshIce01 0.13, LSnowRocks01 0.09
  tex land   40-80  m n=30471  med h +17.60 m | LSnow01 0.29, LSnowRocks01 0.15, LFrozenMarshGrass01 0.14, LFrozenMarshIce01 0.08
  tex land   80-160 m n=30121  med h +34.17 m | LSnow01 0.52, LSnow02 0.16, LSnowRocks01 0.10, LGrassSnow01 0.07
  scat water   0-2   m area   22851 m2  1.13/100m2 | L\trees\reachbranchpile01.nif 0.15; L\trees\coastdriftwood03.nif 0.11; L\trees\reachbranchpile02.nif 0.08; L\trees\coastdriftwood01.nif 0.08
  scat water   2-5   m area   31842 m2  0.54/100m2 | L\ice\frozenmarshicefloefrosts01.nif 0.06; L\ice\frozenmarshicefloechunks03.nif 0.05; L\P\thicket01.nif 0.03; L\trees\coastdriftwood03.nif 0.03
  scat water   5-10  m area   34717 m2  0.65/100m2 | L\ice\frozenmarshicefloechunks03.nif 0.08; L\ice\frozenmarshicefloechunks02.nif 0.07; L\ice\frozenmarshicefloechunks01.nif 0.07; L\ice\frozenmarshicefloefrosts02.nif 0.05
  scat water  10-20  m area    8533 m2  0.36/100m2 | L\ice\frozenmarshicefloefrosts01.nif 0.05; L\ice\frozenmarshicefloechunks02.nif 0.05; L\ice\frozenmarshicefloechunks03.nif 0.05; L\ice\frozenmarshicefloes01.nif 0.04
  scat water  20-40  m area    8142 m2  0.10/100m2 | critters\fchawk\fchawknonest.nif 0.10
  scat water  40-80  m area    4347 m2  0.05/100m2 | critters\fchawk\fchawknonest.nif 0.05
  scat land    0-2   m area   21828 m2  2.56/100m2 | L\P\thicket01.nif 0.26; P\floraswampfungalpod01.nif 0.22; L\trees\reachbranchpile02.nif 0.22; L\trees\reachbranchpile01.nif 0.22
  scat land    2-5   m area   26733 m2  2.77/100m2 | L\P\thicket01.nif 0.37; L\P\deadshrub01.nif 0.25; L\trees\reachclifftree01.nif 0.15; L\trees\reachclifftree02.nif 0.13
  scat land    5-10  m area   48961 m2  2.24/100m2 | L\P\thicket01.nif 0.35; L\P\deadshrub01.nif 0.23; L\trees\reachtree02.nif 0.12; L\trees\reachclifftree01.nif 0.12
  scat land   10-20  m area   61781 m2  1.62/100m2 | L\P\thicket01.nif 0.25; L\P\deadshrub01.nif 0.13; L\trees\reachtree01.nif 0.08; L\trees\reachtree02.nif 0.07
  scat land   20-40  m area   79349 m2  1.39/100m2 | L\P\thicket01.nif 0.18; L\P\deadshrub01.nif 0.10; L\P\thicket01snow.nif 0.07; L\trees\treepineforestdead05.nif 0.06
  scat land   40-80  m area  101885 m2  1.27/100m2 | L\P\thicket01.nif 0.09; L\P\thicket01snow.nif 0.06; L\trees\treepineforestsnow03.nif 0.06; L\trees\treepineforestsnow04.nif 0.05
  scat land   80-160 m area  100715 m2  1.48/100m2 | L\P\thicket01snow.nif 0.17; L\trees\treepineforestsnow05.nif 0.13; L\trees\treepineforestsnow03.nif 0.12; L\P\deadshrub01snow.nif 0.11

===== Solitude coast (sea) Tamriel (-22, -6, 24, 38) pixels 262145 (0.88 km2) water 55.8%, water comps>=40 px: 3
  tex water   0-2   m n=5160   med h -0.23 m | LCoastBeach01 0.57, LCoastOceanFloor01 0.20, LCoastBeach02 0.06
  tex water   2-5   m n=7434   med h -0.57 m | LCoastBeach01 0.52, LCoastOceanFloor01 0.29, LRiverMud01 0.04, LCoastBeach02 0.03
  tex water   5-10  m n=13548  med h -1.49 m | LCoastBeach01 0.47, LCoastOceanFloor01 0.34, LRocks01NoRocks 0.04
  tex water  10-20  m n=15691  med h -3.77 m | LCoastBeach01 0.42, LCoastOceanFloor01 0.31, LRocks01NoRocks 0.07, LRiverMud01NoGrass 0.05
  tex water  20-40  m n=20456  med h -7.77 m | LCoastBeach01 0.44, LCoastOceanFloor01 0.27, LRocks01NoRocks 0.08, LCoastOceanFloor01NoGrass 0.07
  tex water  40-80  m n=27077  med h -15.31 m | LCoastBeach01 0.55, LRocks01NoRocks 0.13, LCoastOceanFloor01NoGrass 0.11, LCoastOceanFloor01 0.10
  tex land    0-2   m n=4667   med h +0.11 m | LCoastBeach01 0.58, LCoastOceanFloor01 0.13, LCoastBeach02 0.08, LRocks01 0.03
  tex land    2-5   m n=5198   med h +0.46 m | LCoastBeach01 0.53, LCoastBeachGrass01 0.13, LRocks01 0.07, LCoastOceanFloor01 0.06
  tex land    5-10  m n=8675   med h +1.49 m | LCoastBeach01 0.49, LRocks01 0.17, LCoastBeachGrass01 0.07, LSnow01 0.04
  tex land   10-20  m n=11861  med h +4.46 m | LCoastBeach01 0.40, LRocks01 0.16, LSnow01 0.10, LCoastBeachGrass01 0.06
  tex land   20-40  m n=18891  med h +10.74 m | LCoastBeach01 0.23, LSnow01 0.19, LRocks01 0.14, LSnowRocks01 0.08
  tex land   40-80  m n=26582  med h +36.69 m | LSnow01 0.30, LSnowRocks01 0.20, LRocks01NoRocks 0.09, LRocks01 0.09
  tex land   80-160 m n=33485  med h +87.89 m | LSnow01 0.36, LSnowRocks01 0.31, LRocks01NoRocks 0.07, LSnow02 0.06
  scat water   0-2   m area   17253 m2  0.55/100m2 | P\slaughterfisheggcluster01.nif 0.06; L\trees\reachbranchpile01.nif 0.03; P\clamthin01.nif 0.03; L\trees\reachbranchpile02.nif 0.03
  scat water   2-5   m area   24857 m2  0.51/100m2 | L\ice\frozenmarshicefloefrosts01.nif 0.09; L\ice\frozenmarshicefloefrosts03.nif 0.05; L\ice\frozenmarshicefloechunks03.nif 0.05; L\ice\frozenmarshicefloefrosts02.nif 0.04
  scat water   5-10  m area   45300 m2  0.62/100m2 | L\ice\frozenmarshicefloechunks03.nif 0.08; L\ice\frozenmarshicefloechunks02.nif 0.06; L\ice\frozenmarshicefloefrosts02.nif 0.05; L\ice\frozenmarshicefloefrosts01.nif 0.04
  scat water  10-20  m area   52466 m2  0.30/100m2 | L\mountains\mountaintrim01.nif 0.02; P\slaughterfisheggcluster01.nif 0.02; L\rocks\rockl03.nif 0.02; L\rocks\rockl01.nif 0.01
  scat water  20-40  m area   68398 m2  0.17/100m2 | L\rocks\rockl01.nif 0.01; L\rocks\rockl02.nif 0.01; P\nordicbarnaclecluster01.nif 0.01; P\slaughterfisheggcluster01.nif 0.01
  scat water  40-80  m area   90537 m2  0.21/100m2 | L\rocks\rockl01.nif 0.02; P\slaughterfisheggcluster01.nif 0.02; L\rocks\rockl03.nif 0.02; P\nordicbarnaclecluster01.nif 0.02
  scat land    0-2   m area   15605 m2  1.13/100m2 | L\trees\reachbranchpile01.nif 0.12; L\P\thicket01.nif 0.10; L\trees\reachbranchpile02.nif 0.08; L\trees\coastdriftwood02.nif 0.08
  scat land    2-5   m area   17380 m2  1.90/100m2 | L\P\thicket01.nif 0.27; L\trees\reachbranchpile01.nif 0.22; L\rocks\rockpilem02.nif 0.14; P\floraspikygrass02.nif 0.12
  scat land    5-10  m area   29006 m2  1.91/100m2 | L\P\thicket01.nif 0.31; L\P\deadshrub01.nif 0.18; L\trees\reachbranchpile01.nif 0.13; P\floraspikygrass02.nif 0.09
  scat land   10-20  m area   39659 m2  1.42/100m2 | L\P\thicket01.nif 0.17; L\P\deadshrub01.nif 0.07; L\trees\reachbranchpile01.nif 0.07; L\trees\treepineforestsnowl03.nif 0.05
  scat land   20-40  m area   63165 m2  1.38/100m2 | L\P\thicket01snow.nif 0.11; L\P\thicket01.nif 0.10; L\trees\treepineforestsnowl03.nif 0.07; L\trees\treepineforestsnowl05.nif 0.07
  scat land   40-80  m area   88882 m2  1.35/100m2 | L\trees\treepineforestsnow05.nif 0.10; L\P\thicket01.nif 0.08; L\P\thicket01snow.nif 0.08; L\trees\treepineforestsnow03.nif 0.08
  scat land   80-160 m area  111963 m2  0.90/100m2 | L\trees\treepineforestsnow05.nif 0.10; L\trees\treepineforestsnow02.nif 0.09; L\trees\treepineforestsnow03.nif 0.08; L\trees\treepineforestsnow04.nif 0.08

===== Dawnstar coast (sea) Tamriel (3, 14, 25, 36) pixels 148225 (0.50 km2) water 71.7%, water comps>=40 px: 1
  tex water   0-2   m n=1773   med h -0.23 m | LCoastOceanFloor01 0.41, LCoastOceanFloor01NoGrass 0.16, LCoastBeach01 0.13, LDirt01 0.13
  tex water   2-5   m n=2534   med h -0.91 m | LCoastOceanFloor01 0.44, LCoastOceanFloor01NoGrass 0.16, LCoastBeach01 0.13, LDirt01 0.11
  tex water   5-10  m n=5698   med h -2.29 m | LCoastOceanFloor01 0.44, LCoastOceanFloor01NoGrass 0.16, LCoastBeach01 0.12, LRocks01NoRocks 0.11
  tex water  10-20  m n=8855   med h -5.03 m | LCoastOceanFloor01 0.32, LCoastOceanFloor01NoGrass 0.19, LCoastBeach01 0.16, LDirt01 0.13
  tex water  20-40  m n=11931  med h -10.06 m | LCoastBeach01 0.30, LCoastOceanFloor01NoGrass 0.20, LCoastOceanFloor01 0.17, LDirt01 0.10
  tex water  40-80  m n=18564  med h -16.57 m | LCoastBeach01 0.34, LCoastOceanFloor01NoGrass 0.25, LRocks01NoRocks 0.16, LCoastOceanFloor01 0.09
  tex land    0-2   m n=1732   med h +0.11 m | LCoastOceanFloor01 0.34, LCoastBeach01 0.25, LCoastOceanFloor01NoGrass 0.12, LDirt01 0.11
  tex land    2-5   m n=2303   med h +0.46 m | LCoastBeach01 0.49, LCoastOceanFloor01 0.14, LSnow01 0.09, NULL(default) 0.05
  tex land    5-10  m n=4919   med h +1.49 m | LCoastBeach01 0.45, LSnow01 0.21, LCoastOceanFloor01 0.07, LCoastBeachGrass01 0.06
  tex land   10-20  m n=7317   med h +4.23 m | LSnow01 0.38, LCoastBeach01 0.33, LSnowRocks01 0.09, LCoastBeachGrass01 0.05
  tex land   20-40  m n=10353  med h +12.23 m | LSnow01 0.61, LCoastBeach01 0.13, LSnowRocks01 0.13, LSnow02 0.05
  tex land   40-80  m n=10453  med h +22.29 m | LSnow01 0.70, LSnowRocks01 0.11, LCoastBeach01 0.08, LSnow02 0.05
  tex land   80-160 m n=4846   med h +36.34 m | LSnow01 0.76, LSnowRocks01 0.12, LSnow02 0.07
  scat water   0-2   m area    5928 m2  0.37/100m2 | P\clam01.nif 0.08; P\clamlarge01.nif 0.05; L\trees\reachbranchpile02.nif 0.03; L\rocks\wetrocks\rockpilel01wet.nif 0.03
  scat water   2-5   m area    8473 m2  0.20/100m2 | P\nordicbarnaclecluster01.nif 0.06; L\mountains\mountaintrim01.nif 0.04; P\clam01.nif 0.02; L\trees\coastdriftwood03.nif 0.01
  scat water   5-10  m area   19052 m2  0.25/100m2 | P\nordicbarnaclecluster01.nif 0.05; P\slaughterfisheggcluster01.nif 0.04; P\clamlarge01.nif 0.02; L\rocks\rockl04.nif 0.02
  scat water  10-20  m area   29608 m2  0.41/100m2 | P\nordicbarnaclecluster01.nif 0.07; P\clam01.nif 0.07; P\clamlarge01.nif 0.04; P\slaughterfisheggcluster01.nif 0.04
  scat water  20-40  m area   39893 m2  0.24/100m2 | P\nordicbarnaclecluster01.nif 0.04; P\clamlarge01.nif 0.03; P\clamthin01.nif 0.03; P\clam01.nif 0.03
  scat water  40-80  m area   62072 m2  0.18/100m2 | L\rocks\rockl02.nif 0.02; P\nordicbarnaclecluster01.nif 0.02; L\rocks\rockl03.nif 0.02; L\ice\icefloes01.nif 0.02
  scat land    0-2   m area    5791 m2  0.85/100m2 | L\trees\reachbranchpile01.nif 0.12; L\trees\coastdriftwood02.nif 0.07; L\trees\reachbranchpile02.nif 0.07; L\trees\coastdriftwood03.nif 0.05
  scat land    2-5   m area    7700 m2  1.27/100m2 | L\trees\coastdriftwood03.nif 0.14; L\trees\reachbranchpile01.nif 0.14; L\trees\coastdriftwood01.nif 0.14; L\trees\reachbranchpile02.nif 0.13
  scat land    5-10  m area   16448 m2  1.28/100m2 | L\P\thicket01.nif 0.14; L\P\thicket01snow.nif 0.10; L\P\deadshrub01.nif 0.09; P\mountainflower01red.nif 0.08
  scat land   10-20  m area   24466 m2  0.84/100m2 | L\P\thicket01snow.nif 0.09; L\rocks\rocks02.nif 0.07; L\P\deadshrub01snow.nif 0.06; P\floraspikygrass02.nif 0.05
  scat land   20-40  m area   34617 m2  1.14/100m2 | L\P\thicket01snow.nif 0.14; L\P\deadshrub01snow.nif 0.11; L\P\thicket01.nif 0.06; L\rocks\rockpiles02.nif 0.05
  scat land   40-80  m area   34951 m2  1.06/100m2 | L\P\thicket01snow.nif 0.19; L\P\deadshrub01snow.nif 0.09; effects\fxambsnowblowingdrifttip.nif 0.08; L\rocks\rockpiles03.nif 0.05
  scat land   80-160 m area   16203 m2  0.86/100m2 | L\P\thicket01snow.nif 0.15; P\florasnowberry01snow.nif 0.09; effects\fxambsnowblowingdrifttip.nif 0.04; L\rocks\rockpilem02.nif 0.04

===== White River Tamriel (3, 30, -6, 12) pixels 546273 (1.83 km2) water 4.5%, water comps>=40 px: 23
  tex water   0-2   m n=4926   med h -0.31 m | LRiverbedEdge01 0.42, LRiverBottom01 0.17, LRiverBottom01NoGrass 0.06, NULL(default) 0.06
  tex water   2-5   m n=6489   med h -0.86 m | LRiverbedEdge01 0.32, LRiverBottom01 0.28, LRiverBottom01NoGrass 0.12, LVolcanicTundraRocks01 0.05
  tex water   5-10  m n=9971   med h -1.53 m | LRiverBottom01 0.37, LRiverBottom01NoGrass 0.20, LRiverbedEdge01 0.18, LRiverMud01 0.06
  tex water  10-20  m n=3040   med h -2.03 m | LRiverBottom01NoGrass 0.32, LRiverBottom01 0.24, LRiverMud01 0.19, LVolcanicTundraRocks01 0.06
  tex water  20-40  m n=132    med h -2.79 m | LRiverBottom01NoGrass 0.55, LRiverMud01 0.25, NULL(default) 0.16, LRiverBottom01 0.04
  tex land    0-2   m n=4913   med h +0.26 m | LRiverbedEdge01 0.38, LRiverBottom01 0.10, NULL(default) 0.06, LRocks01 0.06
  tex land    2-5   m n=6742   med h +0.91 m | LRiverbedEdge01 0.24, LVolcanicTundraDirt01NoGrass 0.08, LRocks01 0.08, NULL(default) 0.07
  tex land    5-10  m n=15243  med h +2.49 m | NULL(default) 0.10, LSnow01 0.10, LRocks01 0.09, LVolcanicTundraDirt01NoGrass 0.09
  tex land   10-20  m n=26396  med h +8.49 m | LSnow01 0.14, NULL(default) 0.14, LVolcanicTundraDirt01NoGrass 0.10, LRocks01 0.07
  tex land   20-40  m n=52056  med h +33.94 m | LSnow01 0.17, NULL(default) 0.13, LVolcanicTundraDirt01NoGrass 0.08, LRocks01 0.08
  tex land   40-80  m n=93671  med h +83.77 m | LSnow01 0.22, NULL(default) 0.09, LFieldGrass01NoGrass 0.07, LRocks01 0.06
  tex land   80-160 m n=123579 med h +138.06 m | LSnow01 0.35, LFieldGrass01NoGrass 0.10, LSnowRocks01 0.10, LTundraRocks01NoRocks 0.06
  scat water   0-2   m area   16471 m2  1.20/100m2 | L\P\thicket01.nif 0.08; P\nordicbarnaclecluster01.nif 0.05; L\rocks\rockpiles01.nif 0.04; L\rocks\wetrocks\rockpilem02wet.nif 0.04
  scat water   2-5   m area   21697 m2  0.92/100m2 | effects\fxrapids.nif 0.05; P\nordicbarnaclecluster01.nif 0.05; effects\fxwaterfallskirtslope.nif 0.04; effects\fxsplashsmallparticleslong.nif 0.03
  scat water   5-10  m area   33340 m2  0.83/100m2 | P\nordicbarnaclecluster01.nif 0.07; effects\fxrapidsfallsline01.nif 0.07; effects\fxrapidsrocks01.nif 0.05; effects\fxrapidsbig01.nif 0.05
  scat water  10-20  m area   10165 m2  0.77/100m2 | P\nordicbarnaclecluster01.nif 0.07; effects\fxrapidsbig01.nif 0.07; L\rocks\rocks03.nif 0.06; effects\fxrapidsfallsline01.nif 0.04
  scat water  20-40  m area     441 m2  0.45/100m2 | L\rocks\wetrocks\rockl02wet.nif 0.23; L\ice\frozenmarshicefloes01.nif 0.23
  scat land    0-2   m area   16427 m2  1.47/100m2 | L\P\thicket01.nif 0.15; L\P\thicket01snow.nif 0.06; L\P\deadshrub01.nif 0.06; L\rocks\wetrocks\rockpilem02wet.nif 0.05
  scat land    2-5   m area   22543 m2  1.99/100m2 | L\P\deadshrub01.nif 0.12; L\trees\treepineforest05.nif 0.11; L\P\thicket01.nif 0.10; L\P\thicket01snow.nif 0.09
  scat land    5-10  m area   50968 m2  2.06/100m2 | L\P\thicket01.nif 0.14; L\P\deadshrub01.nif 0.11; L\trees\treepineforest03.nif 0.07; L\trees\treepineforest05.nif 0.07
  scat land   10-20  m area   88260 m2  2.00/100m2 | L\P\thicket01.nif 0.23; L\P\deadshrub01.nif 0.09; L\P\thicket01snow.nif 0.08; L\trees\treepineforest05.nif 0.06
  scat land   20-40  m area  174058 m2  1.76/100m2 | L\P\thicket01.nif 0.15; L\P\deadshrub01.nif 0.10; L\trees\treepineforest05.nif 0.07; L\trees\treepineforest03.nif 0.06
  scat land   40-80  m area  313205 m2  1.60/100m2 | L\P\thicket01.nif 0.12; L\trees\treepineforest05.nif 0.07; L\P\deadshrub01.nif 0.07; L\trees\treepineforest03.nif 0.07
  scat land   80-160 m area  413208 m2  0.97/100m2 | L\P\thicket01.nif 0.06; L\P\thicket01snow.nif 0.06; L\P\deadshrub01.nif 0.04; L\trees\treepineforestsnow04.nif 0.04

===== Lake Ilinalta Tamriel (5, 12, -27, -20) pixels 66049 (0.22 km2) water 2.0%, water comps>=40 px: 1
  tex water   0-2   m n=143    med h -0.34 m | LRocks01NoRocks 0.44, LRiverbedEdge01 0.44, LRocks01 0.05, LRiverBottom01 0.05
  tex water   2-5   m n=184    med h -1.54 m | LRiverbedEdge01 0.56, LRocks01NoRocks 0.30, LRocks01 0.05, LRiverBottom01 0.05
  tex water   5-10  m n=390    med h -3.94 m | LRiverbedEdge01 0.58, LRocks01NoRocks 0.18, LRiverBottom01 0.09, LRocks01 0.06
  tex water  10-20  m n=480    med h -9.26 m | LRiverbedEdge01 0.55, LRocks01NoRocks 0.14, NULL(default) 0.13, LRiverBottom01 0.07
  tex water  20-40  m n=135    med h -11.20 m | LRiverbedEdge01 0.55, NULL(default) 0.16, LRocks01 0.10, LRocks01NoRocks 0.10
  tex land    0-2   m n=149    med h +0.23 m | LRocks01NoRocks 0.47, LRiverbedEdge01 0.30, LRocks01 0.06, NULL(default) 0.06
  tex land    2-5   m n=215    med h +0.80 m | LRocks01NoRocks 0.47, LRiverbedEdge01 0.20, LRocks01 0.10, NULL(default) 0.06
  tex land    5-10  m n=554    med h +3.31 m | LRocks01NoRocks 0.38, LDirt02 0.13, LSnow01 0.12, LPineForest01 0.08
  tex land   10-20  m n=1106   med h +8.80 m | LRocks01NoRocks 0.32, LSnow01 0.23, LPineForest01 0.15, LDirt02 0.11
  tex land   20-40  m n=2786   med h +388.80 m | LSnow01 0.37, LRocks01NoRocks 0.29, LPineForest01 0.14, NULL(default) 0.08
  tex land   40-80  m n=7870   med h +414.86 m | LSnow01 0.58, LRocks01NoRocks 0.17, NULL(default) 0.10, NULL(default) 0.08
  tex land   80-160 m n=24723  med h +441.26 m | LSnow01 0.65, LRocks01NoRocks 0.13, LSnowRocks01 0.06, LSnow02 0.04
  scat water   0-2   m area     478 m2  0.63/100m2 | L\rocks\rockl05.nif 0.21; L\rocks\rockl04.nif 0.21; L\rocks\rockl02.nif 0.21
  scat water   2-5   m area     615 m2  0.16/100m2 | L\mountains\mountaintrim02.nif 0.16
  scat water   5-10  m area    1304 m2  0.23/100m2 | L\rocks\rockcliff02.nif 0.08; L\rocks\rockcaveentrance02.nif 0.08; L\rocks\rockl04.nif 0.08
  scat water  10-20  m area    1605 m2  0.19/100m2 | L\trees\treepineforestlog01blank.nif 0.06; L\rocks\rockpilel03.nif 0.06; L\mountains\mountaintrim01.nif 0.06
  scat water  20-40  m area     451 m2  0.22/100m2 | L\rocks\rockpilel03.nif 0.22
  scat land    0-2   m area     498 m2  0.60/100m2 | L\trees\treepineforestlogsm01.nif 0.20; L\rocks\rockm04.nif 0.20; L\rocks\rockm02.nif 0.20
  scat land    2-5   m area     719 m2  1.81/100m2 | L\P\thicket01snow.nif 0.83; L\rocks\rockl02.nif 0.42; L\P\deadshrub01.nif 0.14; L\rocks\rockpilem01.nif 0.14
  scat land    5-10  m area    1852 m2  1.78/100m2 | L\P\deadshrub01.nif 0.16; L\P\thicket01snow.nif 0.16; L\trees\treepineforestsnowl04.nif 0.16; L\P\pineshrub01snow.nif 0.11
  scat land   10-20  m area    3698 m2  1.14/100m2 | L\P\pineshrub02snow.nif 0.16; L\trees\treepineforestsnowl02.nif 0.14; L\P\thicket01snow.nif 0.14; L\trees\treepineforestsnowl05.nif 0.08
  scat land   20-40  m area    9315 m2  0.62/100m2 | L\trees\treepineforestsnowl04.nif 0.08; L\trees\treepineforestsnowl02.nif 0.05; L\P\thicket01snow.nif 0.04; L\trees\treepineforestsnowl03.nif 0.03
  scat land   40-80  m area   26315 m2  0.36/100m2 | L\trees\treepineforestsnowl04.nif 0.03; L\rocks\rockpilem02.nif 0.02; L\P\thicket01snow.nif 0.02; L\trees\treepineforestsnow03.nif 0.02
  scat land   80-160 m area   82666 m2  0.50/100m2 | L\P\thicket01snow.nif 0.06; L\trees\treepineforestsnowl04.nif 0.02; L\trees\treepineforestsnow04.nif 0.02; L\trees\treepineforestsnowl02.nif 0.02

===== BlackMarshNorth whole inland BlackMarshNorth (-32, 31, -32, 32) pixels 2798466 (9.36 km2) water 6.2%, water comps>=40 px: 262
  tex water   0-2   m n=26778  med h -0.23 m | LPineForest05 0.59, LFieldGrassDUPLICATE002 0.07, LFieldGrass01 0.07, LDirt03 0.06
  tex water   2-5   m n=32788  med h -0.57 m | LPineForest05 0.59, LFieldGrassDUPLICATE002 0.07, LFieldGrass01 0.07, LDirt03 0.06
  tex water   5-10  m n=54607  med h -1.03 m | LPineForest05 0.54, LFieldGrassDUPLICATE002 0.08, LFieldGrass01 0.08, LFieldGrassDUPLICATE003 0.06
  tex water  10-20  m n=45053  med h -1.94 m | LPineForest05 0.49, LFieldGrass01 0.10, NULL(default) 0.09, LFieldGrassDUPLICATE002 0.09
  tex water  20-40  m n=11751  med h -7.54 m | NULL(default) 0.45, LPineForest05 0.23, LFieldGrass01 0.09, LDirt03 0.08
  tex water  40-80  m n=1683   med h -29.26 m | NULL(default) 0.94, LDirt03 0.06
  tex land    0-2   m n=26316  med h +0.11 m | LPineForest05 0.60, LFieldGrassDUPLICATE002 0.07, LFieldGrass01 0.07, LDirt03 0.06
  tex land    2-5   m n=36145  med h +0.46 m | LPineForest05 0.59, LFieldGrassDUPLICATE002 0.07, LFieldGrass01 0.07, LDirt03 0.06
  tex land    5-10  m n=83909  med h +0.91 m | LPineForest05 0.57, LFieldGrassDUPLICATE002 0.07, LFieldGrass01 0.07, LPineForest03 0.07
  tex land   10-20  m n=140758 med h +1.71 m | LPineForest05 0.54, LPineForest03 0.07, LDirt03 0.07, LFieldGrass01 0.07
  tex land   20-40  m n=228894 med h +1.71 m | LPineForest05 0.49, LPineForest03 0.08, LDirt03 0.08, LFieldGrass01 0.07
  tex land   40-80  m n=287239 med h +1.71 m | LPineForest05 0.41, NULL(default) 0.14, LPineForest03 0.09, LDirt03 0.07
  tex land   80-160 m n=351318 med h +0.11 m | NULL(default) 0.50, LPineForest05 0.18, LPineForest03 0.09, LFieldGrassDUPLICATE003 0.06
  scat water   0-2   m area   89537 m2  0.24/100m2 | P\floraspikygrass02.nif 0.02; vvardenfell\flora\algrass03b.nif 0.02; L\trees\gkblillipad2.nif 0.02; vvardenfell\flora\firefern01.nif 0.01
  scat water   2-5   m area  109632 m2  0.23/100m2 | L\trees\gkblillipad2.nif 0.04; L\trees\cypress3.nif 0.02; vvardenfell\flora\algrass03b.nif 0.02; vvardenfell\flora\firefern01.nif 0.02
  scat water   5-10  m area  182588 m2  0.33/100m2 | L\trees\gkblillipad2.nif 0.13; L\P\kelptallstatic01aaa.nif 0.03; vvardenfell\flora\firefern01.nif 0.02; vvardenfell\flora\algrass03b.nif 0.02
  scat water  10-20  m area  150643 m2  0.57/100m2 | L\trees\gkblillipad2.nif 0.37; L\P\kelptallstatic01aaa.nif 0.07; vvardenfell\flora\algrass03b.nif 0.02; vvardenfell\flora\firefern01.nif 0.02
  scat water  20-40  m area   39292 m2  0.33/100m2 | L\trees\gkblillipad2.nif 0.19; L\P\kelptallstatic01aaa.nif 0.04; vvardenfell\flora\firefern01.nif 0.02; vvardenfell\flora\algrass03b.nif 0.02
  scat land    0-2   m area   87992 m2  0.29/100m2 | vvardenfell\flora\algrass03b.nif 0.02; vvardenfell\flora\firefern01.nif 0.02; L\P\fern01.nif 0.02; vvardenfell\flora\tramaroot01.nif 0.01
  scat land    2-5   m area  120857 m2  0.28/100m2 | vvardenfell\flora\algrass03b.nif 0.03; vvardenfell\flora\firefern01.nif 0.02; L\P\fern01.nif 0.02; P\floraspikygrass02.nif 0.02
  scat land    5-10  m area  280564 m2  0.38/100m2 | P\floraspikygrass02.nif 0.03; vvardenfell\flora\firefern01.nif 0.03; L\stingingnettel_04.nif 0.03; vvardenfell\flora\algrass03b.nif 0.03
  scat land   10-20  m area  470649 m2  0.36/100m2 | P\floraspikygrass02.nif 0.03; vvardenfell\flora\firefern01.nif 0.02; vvardenfell\flora\algrass03b.nif 0.02; L\trees\cypress3.nif 0.02
  scat land   20-40  m area  765347 m2  0.45/100m2 | P\floraspikygrass02.nif 0.04; vvardenfell\flora\algrass03b.nif 0.03; vvardenfell\flora\firefern01.nif 0.03; L\stingingnettel_04.nif 0.03
  scat land   40-80  m area  960433 m2  0.39/100m2 | dlc02\L\trees\treepineforestbroken01.nif 0.04; dlc02\L\trees\treepineforestbroken06.nif 0.03; dlc02\L\trees\treepineforestbroken04_smoking.nif 0.03; dlc02\L\trees\treepineforestbrokencluster01.nif 0.03
  scat land   80-160 m area 1174693 m2  0.19/100m2 | L\trees\gkblillipad2.nif 0.08; P\floraspikygrass02.nif 0.02; L\P\kelptallstatic01aaa.nif 0.01; dlc02\L\trees\treepineforestbroken01.nif 0.01

===== BlackMarshNorth whole sea BlackMarshNorth (-32, 31, -32, 32) pixels 2798466 (9.36 km2) water 45.2%, water comps>=40 px: 2
  tex water   0-2   m n=32065  med h -0.57 m | NULL(default) 0.56, LPineForest05 0.21, LFieldGrassDUPLICATE003 0.07
  tex water   2-5   m n=39836  med h -1.26 m | NULL(default) 0.52, LPineForest05 0.23, LFieldGrassDUPLICATE003 0.08
  tex water   5-10  m n=99379  med h -5.26 m | NULL(default) 0.60, LPineForest05 0.18, LFieldGrassDUPLICATE003 0.06, NULL(default) 0.05
  tex water  10-20  m n=157093 med h -16.23 m | NULL(default) 0.74, LPineForest05 0.11, NULL(default) 0.06, LFieldGrassDUPLICATE003 0.04
  tex water  20-40  m n=244668 med h -26.29 m | NULL(default) 0.91, LPineForest05 0.05
  tex water  40-80  m n=241061 med h -6.74 m | NULL(default) 0.97
  tex land    0-2   m n=20134  med h +0.11 m | LPineForest05 0.34, NULL(default) 0.32, LFieldGrassDUPLICATE003 0.10, LVolcanicAsh03 0.04
  tex land    2-5   m n=26367  med h +0.46 m | LPineForest05 0.34, NULL(default) 0.32, LFieldGrassDUPLICATE003 0.09, LDirt03 0.04
  tex land    5-10  m n=59787  med h +0.91 m | LPineForest05 0.35, NULL(default) 0.33, LFieldGrassDUPLICATE003 0.08, LDirt03 0.04
  tex land   10-20  m n=93967  med h +1.49 m | LPineForest05 0.34, NULL(default) 0.34, LFieldGrassDUPLICATE003 0.07, LDirt03 0.05
  tex land   20-40  m n=165321 med h +1.60 m | NULL(default) 0.34, LPineForest05 0.31, LFieldGrassDUPLICATE003 0.07, LPineForest03 0.06
  tex land   40-80  m n=259214 med h +1.71 m | LPineForest05 0.30, NULL(default) 0.29, LFieldGrassDUPLICATE003 0.07, LPineForest03 0.07
  tex land   80-160 m n=371078 med h +1.71 m | LPineForest05 0.29, NULL(default) 0.21, LTundra01 0.09, LPineForest03 0.08
  scat water   0-2   m area  107215 m2  0.09/100m2 | L\trees\gkblillipad2.nif 0.04; L\trees\cypress3.nif 0.01; L\trees\cypress1.nif 0.01; L\trees\cedartree3.nif 0.01
  scat water   2-5   m area  133199 m2  0.14/100m2 | L\trees\gkblillipad2.nif 0.08; L\trees\cypress3.nif 0.01; L\P\kelptallstatic01aaa.nif 0.01; L\trees\cypress1.nif 0.01
  scat water   5-10  m area  332291 m2  0.20/100m2 | L\trees\gkblillipad2.nif 0.13; L\P\kelptallstatic01aaa.nif 0.02; L\trees\cypress1.nif 0.01; L\trees\cypress3.nif 0.01
  scat water  10-20  m area  525268 m2  0.23/100m2 | L\trees\gkblillipad2.nif 0.17; L\P\kelptallstatic01aaa.nif 0.03; L\trees\cypress1.nif 0.01; L\trees\cedartree3.nif 0.01
  scat water  20-40  m area  818090 m2  0.07/100m2 | L\trees\gkblillipad2.nif 0.02; L\trees\cypress3.nif 0.01; L\trees\cedartree3.nif 0.01; L\trees\cypress1.nif 0.01
  scat water  40-80  m area  806029 m2  0.02/100m2 | L\trees\cypress1.nif 0.01; L\trees\cypress3.nif 0.01; L\trees\cedartree3.nif 0.01; randomresourceships-beds\siege_tower.nif 0.00
  scat land    0-2   m area   67322 m2  0.11/100m2 | L\trees\gkblillipad2.nif 0.04; L\trees\cedartree3.nif 0.01; L\trees\cypress3.nif 0.01; dlc02\L\trees\treepineforestbroken01.nif 0.01
  scat land    2-5   m area   88163 m2  0.12/100m2 | L\trees\cedartree3.nif 0.01; L\trees\cypress3.nif 0.01; L\trees\cypress1.nif 0.01; L\trees\gkbfallforestshrub02.nif 0.01
  scat land    5-10  m area  199908 m2  0.14/100m2 | dlc02\L\trees\treepineforestbroken06.nif 0.01; dlc02\L\trees\treepineforestbroken01.nif 0.01; L\trees\cypress3.nif 0.01; dlc02\L\trees\treepineforestbroken04_smoking.nif 0.01
  scat land   10-20  m area  314195 m2  0.19/100m2 | dlc02\L\trees\treepineforestbroken06.nif 0.02; dlc02\L\trees\treepineforestbroken01.nif 0.02; dlc02\L\trees\treepineforestbrokencluster01.nif 0.02; L\trees\cypress3.nif 0.01
  scat land   20-40  m area  552779 m2  0.25/100m2 | vvardenfell\flora\firefern01.nif 0.03; dlc02\L\trees\treepineforestbroken01.nif 0.03; dlc02\L\trees\treepineforestbroken06.nif 0.02; dlc02\L\trees\treepineforestbroken04_smoking.nif 0.02
  scat land   40-80  m area  866727 m2  0.38/100m2 | P\wheat01.nif 0.08; L\roads\roadchunkl02.nif 0.03; vvardenfell\flora\firefern01.nif 0.03; dlc02\L\trees\treepineforestbroken01.nif 0.02
  scat land   80-160 m area 1240764 m2  0.33/100m2 | L\stingingnettel_04.nif 0.03; P\floraspikygrass02.nif 0.03; L\roads\roadchunkl02.nif 0.02; dlc02\L\trees\treepineforestbroken01.nif 0.02

===== BlackMarsh whole inland BlackMarsh (-35, 35, -39, 18) pixels 1147009 (3.84 km2) water 4.8%, water comps>=40 px: 24
  tex water   0-2   m n=3534   med h -0.91 m | NULL(default) 0.55, LPineForest03 0.20, LFieldGrass02 0.19
  tex water   2-5   m n=4095   med h -2.17 m | NULL(default) 0.54, LPineForest03 0.21, LFieldGrass02 0.18, LReachGrass01 0.03
  tex water   5-10  m n=7675   med h -26.74 m | NULL(default) 0.74, LPineForest03 0.13, LFieldGrass02 0.06, LReachGrass01 0.03
  tex water  10-20  m n=9263   med h -29.26 m | NULL(default) 0.95
  tex water  20-40  m n=16444  med h -29.26 m | NULL(default) 1.00
  tex water  40-80  m n=11471  med h -37.71 m | NULL(default) 1.00
  tex land    0-2   m n=2323   med h +0.11 m | LPineForest03 0.31, NULL(default) 0.31, LFieldGrass02 0.30, LReachGrass01 0.05
  tex land    2-5   m n=3233   med h +0.46 m | LPineForest03 0.32, NULL(default) 0.30, LFieldGrass02 0.30, LReachGrass01 0.05
  tex land    5-10  m n=7810   med h +0.57 m | NULL(default) 0.32, LPineForest03 0.31, LFieldGrass02 0.29, LReachGrass01 0.05
  tex land   10-20  m n=15060  med h +0.57 m | LPineForest03 0.32, NULL(default) 0.32, LFieldGrass02 0.27, LReachGrass01 0.06
  tex land   20-40  m n=34606  med h +0.57 m | NULL(default) 0.35, LPineForest03 0.33, LFieldGrass02 0.22, LReachGrass01 0.07
  tex land   40-80  m n=84043  med h +0.34 m | NULL(default) 0.44, LPineForest03 0.36, LFieldGrass02 0.14
  tex land   80-160 m n=189048 med h +0.00 m | NULL(default) 0.54, LPineForest03 0.38, LFieldGrass02 0.06
  scat water   0-2   m area   11817 m2  5.65/100m2 | L\P\swordferncluster04.nif 1.67; L\P\swordfern03.nif 0.97; L\P\swordferncluster01.nif 0.88; L\P\swordfern06.nif 0.73
  scat water   2-5   m area   13692 m2  6.84/100m2 | L\P\swordferncluster04.nif 2.12; L\P\swordfern03.nif 1.21; L\P\swordferncluster01.nif 0.98; L\P\swordfern06.nif 0.83
  scat water   5-10  m area   25663 m2  5.35/100m2 | L\P\swordferncluster04.nif 1.63; L\P\swordfern03.nif 0.95; L\P\swordferncluster01.nif 0.78; L\P\swordfern06.nif 0.67
  scat water  10-20  m area   30972 m2  0.60/100m2 | L\P\swordferncluster04.nif 0.17; L\P\swordfern03.nif 0.12; L\P\swordferncluster01.nif 0.10; L\P\swordfern06.nif 0.08
  scat land    0-2   m area    7767 m2  8.72/100m2 | L\P\swordferncluster04.nif 2.64; L\P\swordfern03.nif 1.40; L\P\swordferncluster01.nif 1.22; L\P\swordfern06.nif 1.21
  scat land    2-5   m area   10810 m2  8.47/100m2 | L\P\swordferncluster04.nif 2.55; L\P\swordfern03.nif 1.46; L\P\swordferncluster01.nif 1.29; L\P\swordfern06.nif 0.97
  scat land    5-10  m area   26114 m2  6.48/100m2 | L\P\swordferncluster04.nif 1.74; L\P\swordfern03.nif 1.03; L\P\swordferncluster01.nif 0.92; L\P\swordfern06.nif 0.91
  scat land   10-20  m area   50356 m2  4.61/100m2 | L\P\swordferncluster04.nif 1.32; L\P\swordfern03.nif 0.75; L\P\swordferncluster01.nif 0.67; L\P\swordfern06.nif 0.59
  scat land   20-40  m area  115711 m2  3.64/100m2 | L\P\swordferncluster04.nif 0.90; L\P\swordfern03.nif 0.55; L\P\swordferncluster01.nif 0.45; L\P\swordfern06.nif 0.41
  scat land   40-80  m area  281012 m2  1.36/100m2 | L\P\swordferncluster04.nif 0.30; L\P\swordferncluster01.nif 0.18; L\P\swordfern03.nif 0.17; L\P\swordfern06.nif 0.14
  scat land   80-160 m area  632115 m2  0.48/100m2 | L\P\swordferncluster04.nif 0.09; L\P\swordfern03.nif 0.05; L\P\swordferncluster01.nif 0.05; L\P\swordfern06.nif 0.04

===== BlackMarsh whole sea BlackMarsh (-35, 35, -39, 18) pixels 1147009 (3.84 km2) water 51.4%, water comps>=40 px: 2
  tex water   0-2   m n=28373  med h -0.91 m | NULL(default) 0.55, LPineForest03 0.29, LFieldGrass02 0.10
  tex water   2-5   m n=36540  med h -1.71 m | NULL(default) 0.50, LPineForest03 0.33, LFieldGrass02 0.11, NULL(default) 0.03
  tex water   5-10  m n=90151  med h -16.11 m | NULL(default) 0.59, LPineForest03 0.30, LFieldGrass02 0.06, NULL(default) 0.04
  tex water  10-20  m n=132627 med h -29.14 m | NULL(default) 0.72, LPineForest03 0.23, NULL(default) 0.04
  tex water  20-40  m n=172444 med h -29.26 m | NULL(default) 0.79, LPineForest03 0.19
  tex water  40-80  m n=93530  med h -22.06 m | NULL(default) 0.75, LPineForest03 0.24
  tex land    0-2   m n=16662  med h +0.00 m | LPineForest03 0.45, NULL(default) 0.30, LFieldGrass02 0.18
  tex land    2-5   m n=20349  med h +0.23 m | LPineForest03 0.45, NULL(default) 0.32, LFieldGrass02 0.18
  tex land    5-10  m n=43246  med h +0.34 m | LPineForest03 0.44, NULL(default) 0.34, LFieldGrass02 0.17
  tex land   10-20  m n=62878  med h +0.46 m | LPineForest03 0.43, NULL(default) 0.37, LFieldGrass02 0.16
  tex land   20-40  m n=101106 med h +0.46 m | LPineForest03 0.43, NULL(default) 0.42, LFieldGrass02 0.13
  tex land   40-80  m n=132937 med h +0.46 m | LPineForest03 0.49, NULL(default) 0.46
  tex land   80-160 m n=109062 med h +0.46 m | LPineForest03 0.56, NULL(default) 0.38
  scat water   0-2   m area   94870 m2  0.79/100m2 | L\grass\vurt_reeds.nif 0.36; L\trees\gkblillipad2.nif 0.08; L\P\swordferncluster04.nif 0.05; L\P\swordferncluster01.nif 0.03
  scat water   2-5   m area  122178 m2  0.98/100m2 | L\grass\vurt_reeds.nif 0.46; L\trees\gkblillipad2.nif 0.10; L\P\swordferncluster04.nif 0.06; L\grass\waterkelpshort01.nif 0.03
  scat water   5-10  m area  301436 m2  0.95/100m2 | L\grass\vurt_reeds.nif 0.54; L\trees\gkblillipad2.nif 0.12; L\grass\waterkelpshort01.nif 0.05; L\grass\waterkelptall01.nif 0.04
  scat water  10-20  m area  443461 m2  0.96/100m2 | L\grass\vurt_reeds.nif 0.58; L\trees\gkblillipad2.nif 0.14; L\grass\waterkelpshort01.nif 0.05; L\grass\waterkelptall01.nif 0.04
  scat water  20-40  m area  576596 m2  0.39/100m2 | L\grass\vurt_reeds.nif 0.23; L\trees\gkblillipad2.nif 0.05; L\grass\waterkelpshort01.nif 0.02; L\grass\waterkelptall01.nif 0.02
  scat water  40-80  m area  312734 m2  0.25/100m2 | L\grass\vurt_reeds.nif 0.05; L\grass\waterkelpshort01.nif 0.03; L\trees\cypress5.nif 0.02; barrel01cabbages.nif 0.02
  scat land    0-2   m area   55712 m2  1.05/100m2 | L\grass\vurt_reeds.nif 0.36; L\P\swordferncluster04.nif 0.10; L\trees\gkblillipad2.nif 0.08; L\P\swordfern06.nif 0.06
  scat land    2-5   m area   68040 m2  1.14/100m2 | L\grass\vurt_reeds.nif 0.26; L\P\swordferncluster04.nif 0.11; L\P\swordferncluster01.nif 0.09; L\P\swordfern03.nif 0.09
  scat land    5-10  m area  144601 m2  1.19/100m2 | L\P\swordferncluster04.nif 0.21; L\P\swordfern06.nif 0.13; L\P\swordfern03.nif 0.13; L\P\swordferncluster01.nif 0.12
  scat land   10-20  m area  210244 m2  1.34/100m2 | L\P\swordferncluster04.nif 0.27; L\P\swordfern03.nif 0.19; L\P\swordfern06.nif 0.16; L\P\swordferncluster01.nif 0.15
  scat land   20-40  m area  338065 m2  1.81/100m2 | L\P\swordferncluster04.nif 0.43; L\P\swordfern03.nif 0.26; L\P\swordferncluster01.nif 0.21; L\P\swordfern06.nif 0.21
  scat land   40-80  m area  444498 m2  1.98/100m2 | L\P\swordferncluster04.nif 0.55; L\P\swordfern03.nif 0.31; L\P\swordferncluster01.nif 0.25; L\P\swordfern06.nif 0.23
  scat land   80-160 m area  364668 m2  0.63/100m2 | L\P\swordferncluster04.nif 0.16; L\P\swordferncluster01.nif 0.09; L\P\swordfern03.nif 0.08; L\P\swordfern06.nif 0.05

===== BlackMarsh2 whole inland BlackMarsh2 (-32, 31, -30, 31) pixels 3310875 (11.07 km2) water 1.5%, water comps>=40 px: 31
  tex water   0-2   m n=5384   med h -0.11 m | LPineForest03 0.87, NULL(default) 0.06, NULL(default) 0.05
  tex water   2-5   m n=7031   med h -0.23 m | LPineForest03 0.86, NULL(default) 0.06, NULL(default) 0.06
  tex water   5-10  m n=13788  med h -0.34 m | LPineForest03 0.83, NULL(default) 0.08, NULL(default) 0.07
  tex water  10-20  m n=14528  med h -0.34 m | LPineForest03 0.81, NULL(default) 0.09, NULL(default) 0.08
  tex water  20-40  m n=9097   med h -0.34 m | LPineForest03 0.79, NULL(default) 0.13, NULL(default) 0.05, LDirtDUPLICATE002 0.03
  tex water  40-80  m n=1004   med h -0.34 m | LPineForest03 0.65, NULL(default) 0.26, LDirtDUPLICATE002 0.08
  tex land    0-2   m n=5493   med h +0.00 m | LPineForest03 0.88, NULL(default) 0.05, NULL(default) 0.04
  tex land    2-5   m n=7958   med h +0.11 m | LPineForest03 0.89, NULL(default) 0.04, NULL(default) 0.03
  tex land    5-10  m n=19844  med h +0.23 m | LPineForest03 0.91, NULL(default) 0.04
  tex land   10-20  m n=36612  med h +0.34 m | LPineForest03 0.94
  tex land   20-40  m n=77547  med h +0.34 m | LPineForest03 0.96
  tex land   40-80  m n=148679 med h +0.23 m | LPineForest03 0.90, NULL(default) 0.06
  tex land   80-160 m n=257695 med h +0.00 m | LPineForest03 0.65, NULL(default) 0.30
  scat water   0-2   m area   18002 m2  2.73/100m2 | dlc01\P\poisonbloomingredient.nif 0.52; L\P\fernlarge03.nif 0.38; L\P\braken.nif 0.35; L\P\chickweed.nif 0.26
  scat water   2-5   m area   23509 m2  2.63/100m2 | dlc01\P\poisonbloomingredient.nif 0.40; L\P\fernlarge03.nif 0.38; L\P\braken.nif 0.31; L\P\chickweed.nif 0.23
  scat water   5-10  m area   46103 m2  3.65/100m2 | dlc01\P\poisonbloomingredient.nif 0.68; L\P\braken.nif 0.55; L\trees\tropicalplant01.nif 0.46; L\P\fernlarge03.nif 0.38
  scat water  10-20  m area   48577 m2  3.55/100m2 | dlc01\P\poisonbloomingredient.nif 0.75; L\P\braken.nif 0.51; L\trees\tropicalplant01.nif 0.43; L\P\fernlarge03.nif 0.37
  scat water  20-40  m area   30417 m2  0.77/100m2 | dlc01\P\poisonbloomingredient.nif 0.17; L\P\fernlarge03.nif 0.10; L\P\chickweed.nif 0.08; L\P\braken.nif 0.06
  scat water  40-80  m area    3357 m2  0.95/100m2 | L\P\chickweed.nif 0.33; L\P\braken.nif 0.21; traps\pressureplate\trapstonepressureplate02.nif 0.12; L\P\bigshrub2(colorful).nif 0.09
  scat land    0-2   m area   18367 m2 35.90/100m2 | dlc01\P\poisonbloomingredient.nif 6.82; L\P\braken.nif 5.25; L\trees\tropicalplant01.nif 4.43; L\P\fernlarge03.nif 3.71
  scat land    2-5   m area   26609 m2  3.66/100m2 | dlc01\P\poisonbloomingredient.nif 0.52; L\P\braken.nif 0.51; L\trees\tropicalplant01.nif 0.42; L\P\fernlarge03.nif 0.42
  scat land    5-10  m area   66352 m2  1.66/100m2 | L\P\fernlarge03.nif 0.32; L\P\braken.nif 0.16; dlc01\P\poisonbloomingredient.nif 0.16; L\trees\tropicalplant01.nif 0.12
  scat land   10-20  m area  122419 m2  1.65/100m2 | L\P\fernlarge03.nif 0.35; L\P\chickweed.nif 0.15; dlc01\P\poisonbloomingredient.nif 0.15; L\P\braken.nif 0.13
  scat land   20-40  m area  259292 m2  1.59/100m2 | L\P\fernlarge03.nif 0.32; L\P\chickweed.nif 0.14; dlc01\P\poisonbloomingredient.nif 0.13; L\P\braken.nif 0.12
  scat land   40-80  m area  497134 m2  1.45/100m2 | L\P\fernlarge03.nif 0.21; P\wheat01.nif 0.16; L\P\chickweed.nif 0.10; L\P\braken.nif 0.09
  scat land   80-160 m area  861648 m2  0.86/100m2 | dlc01\P\poisonbloomingredient.nif 0.09; L\P\braken.nif 0.07; L\P\chickweed.nif 0.07; L\P\swordfern01.nif 0.06

===== BlackMarsh2 whole sea BlackMarsh2 (-32, 31, -30, 31) pixels 3310875 (11.07 km2) water 72.0%, water comps>=40 px: 1
  tex water   0-2   m n=28643  med h -0.23 m | NULL(default) 0.42, LPineForest03 0.35, LPineForestDUPLICATE004 0.15, LFieldGrass02 0.03
  tex water   2-5   m n=39724  med h -0.34 m | LPineForest03 0.37, NULL(default) 0.36, LPineForestDUPLICATE004 0.17, NULL(default) 0.03
  tex water   5-10  m n=106115 med h -0.46 m | NULL(default) 0.40, LPineForest03 0.34, LPineForestDUPLICATE004 0.18, NULL(default) 0.03
  tex water  10-20  m n=185657 med h -0.91 m | NULL(default) 0.45, LPineForest03 0.31, LPineForestDUPLICATE004 0.17, NULL(default) 0.03
  tex water  20-40  m n=335287 med h -4.57 m | NULL(default) 0.56, LPineForest03 0.25, LPineForestDUPLICATE004 0.14
  tex water  40-80  m n=438877 med h -26.17 m | NULL(default) 0.69, LPineForest03 0.17, LPineForestDUPLICATE004 0.12
  tex land    0-2   m n=21281  med h +0.00 m | LPineForest03 0.46, NULL(default) 0.25, LPineForestDUPLICATE004 0.19, LFieldGrass02 0.04
  tex land    2-5   m n=28011  med h +0.23 m | LPineForest03 0.49, NULL(default) 0.22, LPineForestDUPLICATE004 0.19, LFieldGrass02 0.04
  tex land    5-10  m n=65480  med h +0.57 m | LPineForest03 0.50, NULL(default) 0.21, LPineForestDUPLICATE004 0.19, LFieldGrass02 0.04
  tex land   10-20  m n=101849 med h +1.03 m | LPineForest03 0.51, LPineForestDUPLICATE004 0.20, NULL(default) 0.17, LFieldGrass02 0.05
  tex land   20-40  m n=168821 med h +2.06 m | LPineForest03 0.53, LPineForestDUPLICATE004 0.20, NULL(default) 0.14, LFieldGrass02 0.07
  tex land   40-80  m n=232463 med h +12.23 m | LPineForest03 0.53, LPineForestDUPLICATE004 0.19, NULL(default) 0.18, LFieldGrass02 0.05
  tex land   80-160 m n=184394 med h +8.34 m | LPineForest03 0.68, NULL(default) 0.18, LPineForestDUPLICATE004 0.08, NULL(default) 0.04
  scat water   0-2   m area   95773 m2  0.54/100m2 | dlc01\P\poisonbloomingredient.nif 0.09; L\P\braken.nif 0.06; L\trees\tropicalplant01.nif 0.05; L\P\swordfern01.nif 0.03
  scat water   2-5   m area  132824 m2  0.65/100m2 | dlc01\P\poisonbloomingredient.nif 0.10; L\P\braken.nif 0.07; L\trees\tropicalplant01.nif 0.07; L\P\chickweed.nif 0.04
  scat water   5-10  m area  354814 m2  0.72/100m2 | dlc01\P\poisonbloomingredient.nif 0.11; L\P\braken.nif 0.09; L\trees\tropicalplant01.nif 0.06; L\P\chickweed.nif 0.05
  scat water  10-20  m area  620776 m2  0.76/100m2 | dlc01\P\poisonbloomingredient.nif 0.12; L\P\braken.nif 0.10; L\trees\tropicalplant01.nif 0.08; L\P\chickweed.nif 0.05
  scat water  20-40  m area 1121090 m2  0.71/100m2 | dlc01\P\poisonbloomingredient.nif 0.13; L\P\braken.nif 0.09; L\trees\tropicalplant01.nif 0.07; L\P\chickweed.nif 0.04
  scat water  40-80  m area 1467461 m2  0.48/100m2 | dlc01\P\poisonbloomingredient.nif 0.08; L\P\braken.nif 0.07; L\trees\tropicalplant01.nif 0.05; L\P\chickweed.nif 0.03
  scat land    0-2   m area   71157 m2  0.64/100m2 | dlc01\P\poisonbloomingredient.nif 0.10; L\P\braken.nif 0.07; L\P\chickweed.nif 0.05; L\P\fernlarge03.nif 0.05
  scat land    2-5   m area   93660 m2  0.62/100m2 | dlc01\P\poisonbloomingredient.nif 0.08; L\P\braken.nif 0.08; L\trees\tropicalplant01.nif 0.04; L\P\swordfern01.nif 0.03
  scat land    5-10  m area  218944 m2  0.62/100m2 | dlc01\P\poisonbloomingredient.nif 0.08; L\P\swordfern01.nif 0.05; L\P\braken.nif 0.05; L\P\chickweed.nif 0.05
  scat land   10-20  m area  340550 m2  0.64/100m2 | dlc01\P\poisonbloomingredient.nif 0.07; L\P\braken.nif 0.06; L\P\swordfern01.nif 0.05; L\P\fernlarge03.nif 0.05
  scat land   20-40  m area  564482 m2  0.65/100m2 | L\P\swordfern01.nif 0.07; L\P\braken.nif 0.05; L\P\swordfern03.nif 0.05; L\P\fernlarge03.nif 0.05
  scat land   40-80  m area  777280 m2  0.79/100m2 | L\P\fernlarge03.nif 0.09; P\wheat01.nif 0.09; L\P\swordfern01.nif 0.06; L\P\swordfern03.nif 0.06
  scat land   80-160 m area  616553 m2  2.39/100m2 | dlc01\P\poisonbloomingredient.nif 0.37; L\P\fernlarge03.nif 0.31; L\P\braken.nif 0.30; L\trees\tropicalplant01.nif 0.24

===== Valenwood whole inland Valenwood (-32, 33, -33, 36) pixels 3517790 (11.76 km2) water 2.6%, water comps>=40 px: 122
  tex water   0-2   m n=13413  med h -0.69 m | LPineForest03 0.34, LFieldGrass01 0.16, LFallForestGrass01 0.15, LPineForestDUPLICATE004 0.11
  tex water   2-5   m n=16375  med h -1.83 m | LPineForest03 0.33, LFieldGrass01 0.16, LFallForestGrass01 0.15, LPineForestDUPLICATE004 0.13
  tex water   5-10  m n=29496  med h -3.54 m | LPineForest03 0.30, LFieldGrass01 0.16, LPineForestDUPLICATE004 0.16, LFallForestGrass01 0.15
  tex water  10-20  m n=23149  med h -6.86 m | LPineForestDUPLICATE004 0.22, LPineForest03 0.22, LFallForestGrass01 0.16, LFieldGrass01 0.14
  tex water  20-40  m n=8227   med h -17.60 m | LPineForestDUPLICATE004 0.50, LDirtDUPLICATE004 0.16, LFallForestGrass01 0.08, LDirtDUPLICATE005 0.08
  tex water  40-80  m n=1087   med h -18.86 m | LPineForestDUPLICATE004 0.81, NULL(default) 0.10, NULL(default) 0.06, LDirtDUPLICATE004 0.04
  tex land    0-2   m n=13620  med h +0.57 m | LPineForest03 0.35, LFieldGrass01 0.16, LFallForestGrass01 0.15, LPineForestDUPLICATE004 0.10
  tex land    2-5   m n=19557  med h +2.17 m | LPineForest03 0.36, LFieldGrass01 0.16, LFallForestGrass01 0.15, LPineForestDUPLICATE004 0.10
  tex land    5-10  m n=49735  med h +5.26 m | LPineForest03 0.37, LFieldGrass01 0.16, LFallForestGrass01 0.15, LPineForest02 0.10
  tex land   10-20  m n=100431 med h +9.60 m | LPineForest03 0.37, LFieldGrass01 0.16, LFallForestGrass01 0.14, LPineForest02 0.11
  tex land   20-40  m n=242490 med h +12.00 m | LPineForest03 0.37, LFieldGrass01 0.15, LFallForestGrass01 0.14, LPineForest02 0.11
  tex land   40-80  m n=560459 med h +12.00 m | LPineForest03 0.35, LFallForestGrass01 0.15, LFieldGrass01 0.14, LPineForest02 0.10
  tex land   80-160 m n=978502 med h +12.00 m | LPineForest03 0.31, LFallForestGrass01 0.12, NULL(default) 0.11, LFieldGrass01 0.11
  scat water   0-2   m area   44849 m2  0.21/100m2 | L\dirtcliffs\dirtcliffs03.nif 0.03; effects\fxwaterfallthin2048x128.nif 0.02; L\mountains\mountaincliffslope.nif 0.02; L\dirtcliffs\dirtcliffsisland01.nif 0.02
  scat water   2-5   m area   54753 m2  0.18/100m2 | L\trees\treeaspen04.nif 0.03; L\mountains\mountaintrim01.nif 0.02; L\mountains\mountaincliffslope.nif 0.02; L\dirtcliffs\dirtcliffs03.nif 0.02
  scat water   5-10  m area   98625 m2  0.11/100m2 | L\mountains\mountaintrim01.nif 0.02; L\trees\treeaspen04.nif 0.01; L\mountains\mountaincliffslope.nif 0.01; L\trees\cyrodilsugarmaple.nif 0.01
  scat water  10-20  m area   77403 m2  0.12/100m2 | L\mountains\mountaintrim01.nif 0.02; L\trees\birch-red.nif 0.01; L\P\reachmountainmosscover09.nif 0.01; L\P\reachmountainmosscover07.nif 0.01
  scat water  20-40  m area   27508 m2  0.15/100m2 | L\trees\treeaspen04.nif 0.04; L\trees\birch-red.nif 0.01; telvanni\tel_int_connector_01.nif 0.01; dlc02\architecture\telvannitower\dlc2telvanniroot01.nif 0.01
  scat water  40-80  m area    3635 m2  0.03/100m2 | L\bridges\bridge01.nif 0.03
  scat land    0-2   m area   45541 m2  0.29/100m2 | L\trees\treeaspen04.nif 0.07; L\mountains\mountaincliffslope.nif 0.03; L\dirtcliffs\dirtcliffs03.nif 0.03; effects\fxwaterfallthin2048x128.nif 0.03
  scat land    2-5   m area   65392 m2  0.35/100m2 | L\mountains\mountaincliffslope.nif 0.05; L\dirtcliffs\dirtcliffsisland01.nif 0.05; L\dirtcliffs\dirtcliffs03.nif 0.04; effects\fxwaterfallthin2048x128.nif 0.03
  scat land    5-10  m area  166298 m2  0.36/100m2 | L\dirtcliffs\dirtcliffsisland01.nif 0.06; L\dirtcliffs\dirtcliffs03.nif 0.04; L\P\swordfern01.nif 0.03; L\mountains\mountaincliffslope.nif 0.03
  scat land   10-20  m area  335808 m2  0.32/100m2 | L\P\swordfern01.nif 0.04; L\dirtcliffs\dirtcliffsisland01.nif 0.03; L\trees\treeaspen04.nif 0.02; L\P\swordfern02.nif 0.02
  scat land   20-40  m area  810807 m2  0.37/100m2 | L\P\swordfern01.nif 0.04; P\wheat01.nif 0.03; L\P\swordfern03.nif 0.02; L\trees\treeaspen04.nif 0.02
  scat land   40-80  m area 1873992 m2  0.38/100m2 | L\P\swordfern01.nif 0.04; P\wheat01.nif 0.02; _byoh\P\byohhouseingrdwheat01.nif 0.02; L\P\swordfern03.nif 0.02
  scat land   80-160 m area 3271791 m2  0.33/100m2 | L\P\swordfern01.nif 0.04; L\P\swordfern03.nif 0.02; L\P\swordfern02.nif 0.01; P\wheat01.nif 0.01

===== Valenwood whole sea Valenwood (-32, 33, -33, 36) pixels 3517790 (11.76 km2) water 19.0%, water comps>=40 px: 1
  tex water   0-2   m n=31254  med h -2.29 m | NULL(default) 0.50, LPineForest03 0.12, LFieldGrass01 0.07, LPineForestDUPLICATE004 0.06
  tex water   2-5   m n=37867  med h -5.94 m | NULL(default) 0.47, LPineForest03 0.12, LPineForestDUPLICATE004 0.07, LFieldGrass01 0.07
  tex water   5-10  m n=97121  med h -16.91 m | NULL(default) 0.56, LPineForest03 0.08, LPineForestDUPLICATE004 0.06, NULL(default) 0.06
  tex water  10-20  m n=156632 med h -27.31 m | NULL(default) 0.70, NULL(default) 0.07, LDirtDessertDUPLICATE001 0.04, LPineForestDUPLICATE004 0.04
  tex water  20-40  m n=217599 med h -29.26 m | NULL(default) 0.86, NULL(default) 0.04, LDirtDessertDUPLICATE001 0.03, LDirtDessert 0.03
  tex water  40-80  m n=120745 med h -29.26 m | NULL(default) 0.97
  tex land    0-2   m n=19184  med h +0.80 m | LPineForest03 0.21, NULL(default) 0.20, LFieldGrass01 0.12, LPineForestDUPLICATE004 0.10
  tex land    2-5   m n=25326  med h +3.09 m | LPineForest03 0.23, NULL(default) 0.18, LFieldGrass01 0.12, LPineForestDUPLICATE004 0.11
  tex land    5-10  m n=60707  med h +6.63 m | LPineForest03 0.25, NULL(default) 0.17, LFieldGrass01 0.12, LPineForestDUPLICATE004 0.10
  tex land   10-20  m n=102882 med h +10.51 m | LPineForest03 0.28, NULL(default) 0.16, LFieldGrass01 0.13, LPineForestDUPLICATE004 0.11
  tex land   20-40  m n=198072 med h +11.89 m | LPineForest03 0.29, NULL(default) 0.16, LFieldGrass01 0.13, LPineForestDUPLICATE004 0.11
  tex land   40-80  m n=346415 med h +12.00 m | LPineForest03 0.30, NULL(default) 0.15, LFieldGrass01 0.13, LPineForestDUPLICATE004 0.10
  tex land   80-160 m n=530404 med h +12.00 m | LPineForest03 0.32, LFieldGrass01 0.13, NULL(default) 0.10, LFieldGrass02 0.09
  scat water   0-2   m area  104503 m2  0.02/100m2 | L\mountains\mountaincliffslope.nif 0.00; dlc01\dungeons\castle\rubble\casfloorraised01.nif 0.00; L\P\swordferncluster02.nif 0.00; effects\fxwaterfallbodyslope.nif 0.00
  scat water   2-5   m area  126615 m2  0.01/100m2 | L\dirtcliffs\dirtcliffsisland01.nif 0.00; L\trees\gkbtundrashrub08.nif 0.00; L\mountains\mountaincliffslope.nif 0.00; L\rocks\rockcliff04.nif 0.00
  scat water   5-10  m area  324741 m2  0.02/100m2 | L\trees\treeaspen04.nif 0.00; effects\fxwaterfallbodyslope.nif 0.00; water\dlc2oceanwavecurveouter.nif 0.00; griffon fortress\outerwalltower01.nif 0.00
  scat water  10-20  m area  523726 m2  0.01/100m2 | water\dlc2oceanwavecurveouter.nif 0.00; effects\ambient\fxmistlowsmokey01long.nif 0.00; effects\fxwaterfallbodyslope.nif 0.00; water\dlc2oceanwavesstraight.nif 0.00
  scat water  20-40  m area  727580 m2  0.01/100m2 | water\dlc2oceanwavesstraight.nif 0.00; water\dlc2oceanwavecurveouter.nif 0.00; lor\elven\elvenarch1.nif 0.00; breticships\shipbreticcarrack.nif 0.00
  scat water  40-80  m area  403732 m2  0.01/100m2 | water\dlc2oceanwavesstraight.nif 0.00; dlc02\architecture\ravenrock\docks\dlc2rrdockstr01.nif 0.00; breticships\shipbreticcarrack.nif 0.00; water\dlc2oceanwavecurveouter.nif 0.00
  scat land    0-2   m area   64145 m2  0.04/100m2 | L\mountains\mountaincliffslope.nif 0.01; effects\fxwaterfallthin3096x256.nif 0.01; L\P\swordfern02.nif 0.00; L\dirtcliffs\dirtcliffsisland01.nif 0.00
  scat land    2-5   m area   84682 m2  0.06/100m2 | L\P\swordfern01.nif 0.01; dlc01\dungeons\castle\rubble\casfloorraised01.nif 0.00; L\dirtcliffs\dirtcliffs03.nif 0.00; L\dirtcliffs\dirtcliffsisland01.nif 0.00
  scat land    5-10  m area  202984 m2  0.08/100m2 | L\P\swordfern01.nif 0.01; L\trees\treeaspen04.nif 0.01; L\dirtcliffs\dirtcliffsisland01.nif 0.01; dlc01\dungeons\castle\rubble\casfloorraised01.nif 0.00
  scat land   10-20  m area  344004 m2  0.14/100m2 | P\floranightshade02.nif 0.02; L\P\swordfern01.nif 0.01; L\dirtcliffs\dirtcliffsisland01.nif 0.01; L\trees\treeaspen04.nif 0.01
  scat land   20-40  m area  662288 m2  0.27/100m2 | _byoh\P\byohhouseflorapotato01.nif 0.02; L\trees\treeaspen04.nif 0.02; L\P\swordfern01.nif 0.02; _byoh\P\byohhousefloraleek01.nif 0.01
  scat land   40-80  m area 1158299 m2  0.39/100m2 | _byoh\P\byohhouseflorapotato01.nif 0.03; L\P\swordfern01.nif 0.03; L\trees\treeaspen04.nif 0.03; L\P\swordfern02.nif 0.02
  scat land   80-160 m area 1773498 m2  0.38/100m2 | L\P\swordfern01.nif 0.04; L\P\swordfern02.nif 0.01; P\wheat01.nif 0.01; L\trees\tropicalplant02.nif 0.01
```

## Appendix E. GRAS parameters (density, slope, units from water, position/height/colour range)

```
ALPAGrassButtercup01               King           landscape\grass\EWpShore14.nif                               dens 40 slope 0-28 w:0 AboveAtLeast pos 40 ht 0.35 col 0.2 wavy 
ALPAGrassButtercup02               King           landscape\grass\EWpShore14a.nif                              dens 40 slope 0-28 w:0 AboveAtLeast pos 40 ht 0.35 col 0.2 wavy 
ALPAGrassFern01                    King           landscape\grass\ESuFern01.nif                                dens 40 slope 0-28 w:0 AboveAtLeast pos 40 ht 0.35 col 0.2 wavy 
ALPAGrassFern02                    King           Landscape\grass\ESuFern05.nif                                dens 40 slope 0-28 w:0 AboveAtLeast pos 40 ht 0.35 col 0.2 wavy 
ALPAGrassFern03                    King           Landscape\grass\ESpFern01.nif                                dens 40 slope 0-28 w:0 AboveAtLeast pos 40 ht 0.35 col 0.2 wavy 
ALPAGrassFern04                    King           Landscape\grass\ESpFernBraken01.nif                          dens 40 slope 0-28 w:0 AboveAtLeast pos 40 ht 0.35 col 0.2 wavy 
ALPAGrassHeather01                 King           landscape\grass\ESuHeather01.nif                             dens 40 slope 0-28 w:0 AboveAtLeast pos 40 ht 0.35 col 0.2 wavy 
ALPAGrassHeather02                 King           landscape\grass\ESuHeather02.nif                             dens 40 slope 0-28 w:0 AboveAtLeast pos 40 ht 0.35 col 0.2 wavy 
ALPAGrassLong01A                   King           landscape\grass\TallGrass01.nif                              dens 40 slope 0-28 w:0 AboveAtLeast pos 40 ht 0.35 col 0.2 wavy 
ALPAGrassLong01B                   King           landscape\grass\TallGrass01.nif                              dens 40 slope 0-28 w:0 EitherAtLeast pos 40 ht 0.35 col 0.2 wavy 
ALPAGrassLong02A                   King           landscape\grass\TallGrass02.nif                              dens 40 slope 0-28 w:0 AboveAtLeast pos 40 ht 0.35 col 0.2 wavy 
ALPAGrassLong02B                   King           landscape\grass\TallGrass02.nif                              dens 40 slope 0-28 w:0 EitherAtLeast pos 40 ht 0.35 col 0.2 wavy 
ALPAGrassLong03A                   King           landscape\grass\vactrolswamptall01.nif                       dens 40 slope 0-28 w:0 AboveAtLeast pos 40 ht 0.35 col 0.2 wavy 
ALPAGrassLong03B                   King           landscape\grass\vactrolswamptall01.nif                       dens 40 slope 0-28 w:0 EitherAtLeast pos 40 ht 0.35 col 0.2 wavy 
ALPAGrassLupin01                   King           Landscape\grass\ESuLupins02Blue01.nif                        dens 40 slope 0-28 w:0 AboveAtLeast pos 40 ht 0.35 col 0.2 wavy 
ALPAGrassLupin02                   King           Landscape\grass\ESuLupins02BlueWhite02.nif                   dens 40 slope 0-28 w:0 AboveAtLeast pos 40 ht 0.35 col 0.2 wavy 
ALPAGrassMarsh01                   King           landscape\grass\EWpShore13.nif                               dens 40 slope 0-28 w:0 AboveAtLeast pos 40 ht 0.35 col 0.2 wavy 
ALPAGrassMarsh02                   King           landscape\grass\EWpShore13a.nif                              dens 40 slope 0-28 w:0 AboveAtLeast pos 40 ht 0.35 col 0.2 wavy 
ALPAGrassNettles01                 King           landscape\grass\ESuNettles01.nif                             dens 40 slope 0-28 w:0 AboveAtLeast pos 40 ht 0.35 col 0.2 wavy 
ALPAGrassRams01                    King           landscape\grass\ESuRams.nif                                  dens 40 slope 0-28 w:0 AboveAtLeast pos 40 ht 0.35 col 0.2 wavy 
ALPAGrassReeds01                   King           landscape\grass\EWpShore07.nif                               dens 40 slope 0-28 w:0 EitherAtLeast pos 40 ht 0.35 col 0.2 wavy 
ALPAGrassReeds02                   King           landscape\grass\EWpShore07a.nif                              dens 40 slope 0-28 w:0 EitherAtLeast pos 40 ht 0.35 col 0.2 wavy 
ALPAGrassReeds03                   King           landscape\grass\EWpShore07b.nif                              dens 40 slope 0-28 w:0 EitherAtLeast pos 40 ht 0.35 col 0.2 wavy 
ALPAGrassReeds04                   King           landscape\grass\EWpShore07c.nif                              dens 40 slope 0-28 w:0 EitherAtLeast pos 40 ht 0.35 col 0.2 wavy 
ALPAGrassViolet01                  King           landscape\grass\EWpShore15.nif                               dens 40 slope 0-28 w:0 AboveAtLeast pos 40 ht 0.35 col 0.2 wavy 
ALPAGrassViolet02                  King           landscape\grass\EWpShore17.nif                               dens 40 slope 0-28 w:0 AboveAtLeast pos 40 ht 0.35 col 0.2 wavy 
ALPAGrassViolet03                  King           landscape\grass\EWpShore17a.nif                              dens 40 slope 0-28 w:0 AboveAtLeast pos 40 ht 0.35 col 0.2 wavy 
ALPAGrassWildSaltrice01            King           landscape\grass\EWpShore03.nif                               dens 40 slope 0-28 w:0 AboveAtLeast pos 40 ht 0.35 col 0.2 wavy 
ALPAGrassWildSaltrice02            King           landscape\grass\EWpShore03a.nif                              dens 40 slope 0-28 w:0 AboveAtLeast pos 40 ht 0.35 col 0.2 wavy 
ALPAGrassWildSaltrice03            King           landscape\grass\EWpShore03b.nif                              dens 40 slope 0-28 w:0 AboveAtLeast pos 40 ht 0.35 col 0.2 wavy 
ALPAGrassWildSaltrice04            King           landscape\grass\EWpShore03c.nif                              dens 40 slope 0-28 w:0 AboveAtLeast pos 40 ht 0.35 col 0.2 wavy 
ALPAGrassYarrow01                  King           landscape\grass\ESuYarrow01.nif                              dens 40 slope 0-28 w:0 AboveAtLeast pos 40 ht 0.35 col 0.2 wavy 
ALPASeaGrass01                     King           Landscape\grass\EWpSea01.nif                                 dens 20 slope 0-50 w:155 BelowAtLeast pos 40 ht 0.4 col 0.2 wavy 
ALPASeaGrass02                     King           Landscape\grass\EWpSea02.nif                                 dens 20 slope 0-50 w:155 BelowAtLeast pos 40 ht 0.4 col 0.2 wavy 
ALPASeaGrass03                     King           Landscape\grass\EWpSea03.nif                                 dens 20 slope 0-50 w:155 BelowAtLeast pos 40 ht 0.4 col 0.2 wavy 
ALPASeaGrass04                     King           Landscape\grass\EWpSea04.nif                                 dens 20 slope 0-50 w:155 BelowAtLeast pos 40 ht 0.4 col 0.2 wavy 
BeachGrass01                       Skyr+Upda      Landscape\Grass\BeachGrassObj01.nif                          dens 90 slope 0-42 w:0 AboveAtLeast pos 68 ht 0.3 col 0.2 wavy 
BeachGrass02                       Skyr+Upda      Landscape\Grass\BeachGrassObj02.nif                          dens 80 slope 0-44 w:0 AboveAtLeast pos 29 ht 0.25 col 0.25 wavy 
CattailGrass01                     Trop           Landscape\grass\CattailGrass.nif                             dens 30 slope 0-40 w:0 BelowAtLeast pos 40 ht 0.3 col 0.3 wavy 
DLC01SoulCairnGrass01              Dawn           Landscape\Grass\DLC01SoulCairnGrass01.nif                    dens 80 slope 0-90 w:0 AboveAtLeast pos 24 ht 0.5 col 0.3 wavy 
DLC02VolcanicAshGrass01            Drag           Landscape\Grass\DLC02VolcanicAshGrass01.nif                  dens 60 slope 0-46 w:0 AboveAtLeast pos 45 ht 0.35 col 0.03 wavy 
DLC02VolcanicAshGrass02            Drag           Landscape\Grass\DLC02VolcanicAshGrass02.nif                  dens 60 slope 0-46 w:0 AboveAtLeast pos 45 ht 0.35 col 0.03 wavy 
DLC02VolcanicAshRocks01            Drag           Landscape\Grass\DLC02VolcanicAshRocks01.nif                  dens 10 slope 0-10 w:0 AboveAtLeast pos 16 ht 0.1 col 0.05 wavy 
FallForestGrass01                  Skyr+Upda      Landscape\Grass\FallForestGrassObj01.nif                     dens 65 slope 0-38 w:0 AboveAtLeast pos 30 ht 0.35 col 0.2 wavy 
FallForestGrass02                  Skyr+Upda      Landscape\Grass\FallForestGrassObj02.nif                     dens 45 slope 0-34 w:0 AboveAtLeast pos 34 ht 0.33 col 0.2 wavy 
FernGrass01                        Skyr+Upda+Trop Landscape\grass\ferngrass01.nif                              dens 37 slope 0-50 w:0 AboveAtLeast pos 30 ht 0.33 col 0.2 wavy 
FieldGrass01                       Skyr+Upda      Landscape\Grass\FieldGrass01.nif                             dens 64 slope 0-45 w:0 AboveAtLeast pos 30 ht 0.38 col 0.2 wavy 
FieldGrass02                       Skyr+Upda      Landscape\Grass\FieldGrassFlowers02.nif                      dens 20 slope 0-45 w:0 AboveAtLeast pos 30 ht 0.3 col 0.2 wavy 
ForestGrass01                      Skyr+Upda+Trop Landscape\Grass\ForestGrass01.nif                            dens 25 slope 0-33 w:0 AboveAtLeast pos 41 ht 0.3 col 0.1 wavy 
ForestGrass02                      Skyr+Upda+Trop Landscape\Grass\ForestGrass02.nif                            dens 5 slope 0-33 w:0 AboveAtLeast pos 42 ht 0.3 col 0.1 wavy 
FrozenMarshGrass01                 Skyr+Upda+Trop Landscape\Grass\MarshGrassObj01.nif                          dens 60 slope 0-42 w:0 AboveAtLeast pos 40 ht 0.3 col 0.3 wavy 
ReachGrass01                       Skyr+Upda+Trop Landscape\Grass\ReachGrassObj01.nif                          dens 30 slope 0-35 w:0 AboveAtLeast pos 35 ht 0.35 col 0.2 wavy 
ReachGrass02                       Skyr+Upda+Trop Landscape\Grass\ReachGrassObj02.nif                          dens 30 slope 0-35 w:0 AboveAtLeast pos 35 ht 0.35 col 0.2 wavy 
RockGrass01                        Skyr+Upda+Trop Landscape\Grass\RockGrass01.nif                              dens 10 slope 0-40 w:0 AboveAtLeast pos 32 ht 0.25 col 0.02 wavy 
RockGrassSnow01                    Skyr+Upda      Landscape\Grass\RockGrassSnowObj01.nif                       dens 12 slope 0-36 w:0 AboveAtLeast pos 32 ht 0.25 col 0.05 wavy 
RockGrassWater01                   Skyr+Upda      Landscape\Grass\RockGrassWater01.nif                         dens 20 slope 0-34 w:105 BelowAtLeast pos 32 ht 0.25 col 0.1 wavy 
SnowGrass01                        Skyr+Upda      Landscape\Grass\SnowGrass01.nif                              dens 40 slope 0-48 w:0 AboveAtLeast pos 30 ht 0.33 col 0.2 wavy 
SnowGrass01Forest                  Skyr+Upda      Landscape\Grass\SnowGrass01.nif                              dens 30 slope 0-48 w:0 AboveAtLeast pos 40 ht 0.33 col 0.2 wavy 
SnowGrass01Light                   Skyr+Upda      Landscape\Grass\SnowGrass01.nif                              dens 50 slope 0-45 w:0 AboveAtLeast pos 50 ht 0.33 col 0.2 wavy 
SnowGrass02                        Skyr+Upda      Landscape\Grass\SnowGrass02.nif                              dens 30 slope 0-45 w:0 AboveAtLeast pos 40 ht 0.33 col 0.2 wavy 
TBPCoastDriftwood                  Dept           landscape\grass\TBPcoastdriftwood01.nif                      dens 1 slope 0-45 w:1 BelowAtLeast pos 50 ht 0.2 col 0.5 wavy 
TBPCoastDriftwood2                 Dept           landscape\grass\TBPcoastdriftwood02.nif                      dens 1 slope 0-45 w:1 BelowAtLeast pos 50 ht 0.2 col 0.5 wavy 
TBPEwpSea02                        Dept           landscape\grass\TBPEwpSea02.nif                              dens 30 slope 0-90 w:300 BelowAtLeast pos 32 ht 0.2 col 0.5 wavy 
TBPEwpSea03                        Dept           landscape\grass\TBP_seaweed05.nif                            dens 5 slope 0-75 w:500 BelowAtLeast pos 90 ht 0.5 col 0.5 wavy 
TBPEwpSea06                        Dept           landscape\grass\TBP_seaweed06.nif                            dens 30 slope 0-90 w:500 BelowAtLeast pos 30 ht 0.2 col 0.5 wavy 
TBPEwpSea10                        Dept           landscape\grass\TBPEwpSea10.nif                              dens 1 slope 0-90 w:500 BelowAtLeast pos 32 ht 0.5 col 0.5 wavy 
TBPRiverKelpGrass01                Dept           Landscape\Grass\WaterKelpTall01.nif                          dens 15 slope 0-50 w:390 BelowAtLeast pos 50 ht 0.36 col 0.2 wavy 
TBPRiverKelpGrass02                Dept           Landscape\Grass\WaterKelpShort01.nif                         dens 10 slope 0-55 w:130 BelowAtLeast pos 25 ht 0.25 col 0.2 wavy 
TBPRockGrass01                     Dept           Landscape\Grass\RockGrass01.nif                              dens 10 slope 0-40 w:50 BelowAtLeast pos 32 ht 0.25 col 0.1 wavy 
TBPRockGrassWater02                Dept           Landscape\Grass\RockGrassWater01.nif                         dens 10 slope 0-34 w:105 BelowAtLeast pos 32 ht 0.25 col 0.1 wavy 
TBPRockGrassWater03                Dept           landscape\grass\TBProckgrasswater03.nif                      dens 3 slope 0-45 w:150 BelowAtLeast pos 80 ht 0.25 col 0.1 wavy 
TBPSeaweed02Test                   Dept           landscape\grass\TBP_seaweed02test.nif                        dens 10 slope 0-90 w:700 BelowAtLeast pos 70 ht 0.5 col 0.2 wavy 
TBPSeaweed05                       Dept           landscape\grass\TBP_seaweed05Var1.nif                        dens 3 slope 0-90 w:700 BelowAtLeast pos 70 ht 0.2 col 0.5 wavy 
TBPSeaweed06Var1                   Dept           landscape\grass\TBP_seaweed06.nif                            dens 5 slope 0-20 w:500 BelowAtLeast pos 90 ht 0.5 col 0.5 wavy 
TBPSeaweed11                       Dept           landscape\grass\waterkelptall03.nif                          dens 3 slope 0-55 w:250 BelowAtLeast pos 50 ht 0.2 col 0.5 wavy 
TBPWaterCoralGrass02               Dept           Landscape\Grass\WaterCoralGrass01.nif                        dens 7 slope 0-50 w:200 BelowAtLeast pos 80 ht 0.4 col 0.2 wavy 
TBPWaterCoralGrass03               Dept           Landscape\Grass\WaterCoralGrass01.nif                        dens 15 slope 0-50 w:100 BelowAtLeast pos 50 ht 0.4 col 0.2 wavy 
TBPWaterKelpGrass01                Dept           landscape\grass\waterkelptall02.nif                          dens 5 slope 0-50 w:390 BelowAtLeast pos 80 ht 0.36 col 0.2 wavy 
TBP_Algae01                        Dept           landscape\grass\TBPAlgae01.nif                               dens 12 slope 0-55 w:100 BelowAtLeast pos 50 ht 0.2 col 0.5 wavy 
TBP_coralsmall01                   Dept           landscape\grass\TBP_coralsmall01.nif                         dens 1 slope 0-25 w:1000 BelowAtLeast pos 50 ht 0.2 col 0.5 wavy 
TBP_coralsmall02                   Dept           landscape\grass\TBP_coralsmall01.nif                         dens 1 slope 0-25 w:100 BelowAtLeast pos 50 ht 0 col 0.5 wavy 
TropicalGrass01                    Trop           Landscape\Grass\MarshGrassObj01.nif                          dens 5 slope 0-42 w:0 AboveAtLeast pos 40 ht 0.3 col 0.3 wavy 
TropicalGrassPlant01               Trop           Landscape\grass\GrassFern01.nif                              dens 5 slope 0-50 w:0 AboveAtLeast pos 30 ht 1 col 0 wavy 
TropicalGrassPlant02               Trop           Landscape\grass\GrassPlant01.nif                             dens 3 slope 0-50 w:40 AboveAtLeast pos 30 ht 1 col 0 wavy 
TundraGrass01                      Skyr+Upda+Trop Landscape\Grass\TundraGrass01.nif                            dens 4 slope 0-14 w:0 AboveAtLeast pos 40 ht 0.3 col 0.2 wavy 
TundraGrass03                      Skyr+Upda+Trop Landscape\Grass\TundraGrassObj03.nif                         dens 3 slope 0-19 w:0 AboveAtLeast pos 30 ht 0.2 col 0.25 wavy 
TundraGrass04                      Skyr+Upda+Trop Landscape\Grass\TundraGrassObj04.nif                         dens 5 slope 0-19 w:0 AboveAtLeast pos 36 ht 0.2 col 0.3 wavy 
VolcanicGrass01                    Skyr+Upda      Landscape\Grass\VolcanicGrassObj01.nif                       dens 62 slope 0-36 w:0 AboveAtLeast pos 32 ht 0.25 col 0.3 wavy 
VolcanicGrass02                    Skyr+Upda      Landscape\Grass\VolcanicGrassObj02.nif                       dens 45 slope 0-38 w:0 AboveAtLeast pos 30 ht 0.3 col 0.3 wavy 
WaterCoralGrass01                  Skyr+Upda      Landscape\Grass\WaterCoralGrass01.nif                        dens 20 slope 0-50 w:155 BelowAtLeast pos 40 ht 0.4 col 0.2 wavy 
WaterKelpGrass01                   Skyr+Upda+Dept Landscape\Grass\WaterKelpTall01.nif                          dens 5 slope 0-50 w:390 BelowAtLeast pos 50 ht 0.36 col 0.2 wavy 
WaterKelpGrass02                   Skyr+Upda+Dept Landscape\Grass\WaterKelpShort01.nif                         dens 2 slope 0-55 w:130 BelowAtLeast pos 80 ht 0.25 col 0.2 wavy 

```
