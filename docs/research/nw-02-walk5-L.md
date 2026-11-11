# Walk 5, lane L: what is seen from afar (LOD, the map, far water edges), teleports, the crash

Measured 2026-11-10 on terrain build 20261109T204317Z, its ESM (sha c9d4a1acdd90, the one deployed) and the LOD of the
run of 2026-11-09 (s3 nw/lod/1226fd7bc37f0257.tar; DynDOLOD and TexGen logs read on the play machine). Tools in
the scratch of the session; the durable ones are `tools/newworld/teleports.py`, `tools/newworld/world/lodplan.py`,
`tools/newworld/world/mapdata.py` (map_box, camera).

## 1. Water against land far off, and flicker on land

How Skyrim does it, measured in `Skyrim - Meshes1.bsa` (Tamriel's 3,060 .btr) against ours (LOD32, vertex heights
times the chunk scale, minus the water shape's height):

| land vertex height above the LOD water | Tamriel LOD32 | ours LOD32 |
|---|---|---|
| below -512 | 44.1 % | 78.6 % |
| -128 to -1 | 0.96 % | 7.1 % |
| -1 to +1 | 0.03 % | 0.00 % |
| +1 to +128 | 0.76 % | 4.7 % |
| above +512 | 46.2 % | 5.0 % |

- Both draw LOD water as one quad per cell (water triangle extent 4,096 units in every chunk, ours and Tamriel's): the
  "water as whole cell squares" on the map and from the air is Skyrim's own mechanism. Bethesda's land is almost never
  within 128 units (1.8 m) of the water plane, so the squares hide under steep shores. Ours is: over the whole
  heightmap 42 % of samples lie within 32 units (0.46 m) of the water (0-8 above: 4.0 %, 8-16: 10.0 %, 16-32: 15.2 %,
  -32-0: 12.9 %); Helstrom's ground stands 9 to 14 units (0.13-0.2 m) above it (BTR chunk 4.-8.-148). At distance
  the depth buffer cannot part two surfaces 10 units apart: the cell's water quad and the land fight (the flicker,
  changing as the view moves), and a wet cell's quad shows as a square with straight edges against the dry cell next
  to it. This is the relief at the water line (lanes W and T), not the LOD; reported to the lead.
- Worldspace header (WRLD) against Bethesda's: Tamriel NAM4 LOD water height = DNAM water = -14000, land default
  -27000; Solstheim NAM4 = water = 256, land -4590; ours NAM4 = water = 0, land -2048. Same rule (LOD water at the
  water height); nothing to change.
- xLODGen: the run used the GUI's defaults (its log: LOD4 quality 10, LOD8 15, LOD16 20, LOD32 25, Protect Borders
  False, Optimize Unseen off/on/on/on, no options file). sheson's recipe (dyndolod.info Help/xLODGen): LOD4 quality
  0-5 with Protect Borders; LOD8/16 quality 0-8 with Optimize Unseen 550 "in case there is visible z-fighting of water
  in the distance"; LOD32 quality 0-10 with Optimize Unseen 550 "to improve coastlines on the map"; and
  `bEnableLandFade=0` (Skyrim.ini [Display]) for terrain "briefly flickering when new areas are loading in". LODGen's
  keys (its input file and its exe's strings): ProtectCellBorders, QualityLODn, WaterDeltaLODn (-1 off, 0 on,
  550). Now: lod.ps1 Set-TerrainMeshes (4/6/8/10, borders protected, 550 at LOD8-32) and stack.ps1 bEnableLandFade=0.
- Ruled out for the flicker on land: a second LOD set (files.txt: one terrain folder, ArgoniaBlackMarsh only, levels
  4/8/16/32 = 5,244/1,440/429/126 as expected); object LOD duplicating full models (DynDOLOD reference rule
  "Unchanged": the LOD model unloads as the full one loads). Engine keys that bear on it (SkyrimSE.exe strings):
  fLODLandDropAmount and fLODLandVerticalBias [LOD], bEnableLandFade [Display]; only the last is changed (sheson).

## 2. The map's water, edges and light squares

- Water squares, missing water, flicker as you pan: the mechanism of section 1, seen from the map camera at 50,000 to
  80,000 units.
- "Weird light coloured square land textures": in a mosaic of the LOD16 diffuse textures 3,222 of 107,744 land
  quadrants are 40+ levels lighter than the quadrants round them; 2,660 of them (83 %) carry 7 textures (base + 6
  layers), against 36 % of all quadrants: a 7-texture quadrant is light 6.8 % of the time, any other 0.8 %. Skyrim.esm:
  textures per quadrant 1-6 in 99.1 % of its 39,520 quadrants, 7 in 337 (0.85 %); ours: 7 in 39,183 quadrants (36 %)
  (`texture.py` MAXL 7). The cap belongs to the ground textures (lane T or the texture owner): six per quadrant as
  Bethesda's land; reported to the lead.
- The 25 LOD16 textures at 128 px (row y -80 and column x 112) are chunks beyond the built cells: xLODGen's default
  size for no land; never seen.

## 3. The map's pan and zoom

- Tamriel (Skyrim.esm WRLD MNAM): usable 0,0; NW(-30,15) SE(40,-40), a 70 x 55-cell box; camera 50,000 / 80,000,
  pitch 50; its LAND x -57..61, y -43..50: the box sits 3 to 36 cells inside the land. Solstheim: NW(8,17) SE(17,1),
  31,000 / 48,000, pitch 70.
- Ours was NW(-38,-132) SE(50,-204): "a quarter in from each side" of the land (MapFix.cs's reading of Tamriel), an
  89 x 73-cell box in a 178 x 144-cell land, so the camera could not reach the west, south or east (Topal Bay).
- Now (mapdata.map_box, camera): the box is the whole province (out/newworld/scope_cells.json less margin_cells.json,
  land, sea and islands: x -76..87, y -232..-103), held at least 3 cells inside the built cells (Tamriel's least
  margin); camera max height Tamriel's 80,000 scaled by the box's longer side against Tamriel's, at most twice:
  160,000. Computed from the scope at every build, so lane R's widened scope widens it.
- Map-menu keys the engine reads ([MapMenu], SkyrimSE.exe strings): fMapWorldMaxPitch, fMapWorldMinPitch,
  fMapWorldYawRange, fMapWorldZoomSpeed, fMapWorldTransitionHeight, fMapMenuNearClipPlane, uLockedTerrainLOD,
  uLockedObjectMapLOD; no height key: the heights are the WRLD's.

## 4. Trees, rocks and plants appearing from nothing

Read back from the run (DynDOLOD_SSE_BillboardsUsed_ArgoniaBlackMarsh.txt, LODGen_SSE_Export_ArgoniaBlackMarsh.txt,
TexGen_SSE_Tree_Billboards.txt) for the 472 placed bases:

| got | bases | refs |
|---|---|---|
| tree billboard | 113 | 82,355 |
| object LOD (own LOD models) | 52 | 23,686 |
| nothing | 307 | 450,826 |

Why nothing: tree LOD needs a billboard, and TexGen makes one only for a TREE (or a STAT with "Has Tree LOD") whose
bounds reach 512 (diagonal) and 256 (height) and whose model path holds "tree" (dyndolod.info TexGen-Configuration;
TexGen_SSE.ini MinTreeModelMagnitude 512, MinTreeModelHeight 256): 44 of our TREE bases were listed ",False" (King
of the Murkmire's plants live under argonia\trees\Greguire, Landscape\plants\...), and every tree kept as a STAT (BM&V,
KotM cypresses, palms) had no flag. Object LOD needs LOD models: logs, boulders, mushrooms and cliffs from KotM and
BM&V have none, and DynDOLOD's Medium preset gives \rockl, \rockm, \rockpile none. Billboards are keyed by plugin and
form id; ours are made from our own records (TexGen ran on ArgoniaNewWorld.esm), so that was never the fault.

The plan for the next build (lodplan.json, read back by `lodplan coverage` after the run):

| mechanism | bases | refs |
|---|---|---|
| tree billboard (TexGen forced by DynDOLOD_SSE_TexGen_Billboards_*.txt; Has Tree LOD on our 45 STAT trees) | 158 | 124,776 |
| tree billboard, Black Marsh.esm's static trees (an override of ours carries Has Tree LOD) | 14 | 24,074 |
| object LOD, own LOD models (unchanged) | 50 | 22,571 |
| object LOD, full model at LOD4 (LOD8 for cliffs), rule file DynDOLOD_SSE_argonianewworldesm.ini, within the budget | 10 | 3,877 |
| none: full model too heavy for the per-block budget (logs, stumps, rocks; no LOD mesh of the shape exists) | 33 | 28,755 |
| none: Skyrim's own None families (RockL/M/S, rock piles) and rocks under 1,500 units | 37 | 34,361 |
| none: harvestable flora (FLOR) | 31 | 40,070 |
| none: small (bounds under 512 units: reeds, ferns, herbs, small rocks, small plants) | 115 | 247,702 |
| none: low and wide ground cover (under 256 units high) | 24 | 30,681 |

The budget: a full model is used as is (DynDOLOD does not decimate it), so a rule may add to each LOD block at most
what Tamriel's own object LOD carries there: measured on the 517 LOD4 and 152 LOD8 .bto of Skyrim - Meshes1.bsa,
p50 3,864 / p90 9,327 / max 18,141 triangles a LOD4 block, p90 14,263 a LOD8 block; the p90 is the budget. Models are
taken largest first; uprooted logs (4,562 triangles x 2,206 refs) and large logs (3,409 x 1,740) are refused. 172
billboards in all, under the 256 a world.

DynDOLOD's own rules, measured: rules apply top to bottom, first match wins; a `plugin;form id` mask is a
reference's, never a base's (dyndolod.info Mesh-Mask-Reference-Rules), so ours are mesh masks; a plugin's rule file
is Data\DynDOLOD\DynDOLOD_SSE_<plugin, letters and digits>.ini with [Skyrim LODGen] LODGen1.. (Mod-Authors). Tree
atlas limit 256 billboards a world (Tree-LOD): 158 planned.

Distances (the game's own presets, SkyrimSE folder): the machine ran High's LOD switch (fBlockLevel0Distance 35000,
fBlockLevel1Distance 70000) with fLODFadeOutMultObjects 27.5, Items 6, Actors 9; Bethesda's Ultra is 60000, 90000,
30, 10, 15, grass fade 7000 (also the slider's maximum), tree load 75000. stack.ps1 now writes Ultra's values.

## 5. Teleports

Helstrom's place record: world -32174, -605839, cell (-8, -148) in the plugin's grid (cells x -84..97, y -95..-242).
`cow ArgoniaBlackMarsh -8 -148` landed "in the sea miles north outside the map": cell y -148 + 256 = 108 lies 256 cells
(a million units) north, where the world has no LAND (default land -2048 under water 0). Every walk command with y
below -128 was affected (all but Thorn -125 and the estuary -115); `coc ArgoniaNWStart` (cell -7,-128) worked. The
native way, as Skyrim's `coc Riverwood`: a named exterior cell with a COCMarkerHeading (Skyrim.esm 000032). 266
teleports (258 places, 8 walk checks) in 265 named cells, 0 faults in `teleports check` (land at least 8 units above
the water and all its neighbours, gentle, 96 units clear of placed objects and clear of a built place's buildings
by their footprints, on the ground with the place's land patches (newworld/places/<id>/), inside its own cell: 11 places stand on
water and land in the nearest cell with dry ground, 5 seabed ruins and wrecks with no land within 3 cells land on the
water above them).

## 6. The crash of 2026-11-10 16:34

`crash-2026-11-10-16-34-31.log` (CrashLoggerSSE 1.27, Skyrim 1.7.104, process up 34 min), the relevant lines:

```
Unhandled exception "EXCEPTION_ACCESS_VIOLATION" at 0x7FF652B2E715 SkyrimSE.exe+02BE715	mov rax, [rax+0x160]
Access Violation: Tried to read memory at 0x00000202015F
	RDI: (TESObjectREFR*) [0x00000000] ("ArgoniaNewWorld.esm")      FormType: Static (34), ParentCell: ---, FormID 0
	R15: (BSLightingShaderProperty*)
	RSP+F0: (TESObjectCELL*) [0x0A103C32] ("ArgoniaNewWorld.esm")
	RSP+190: (TESWorldSpace*) "Black Marsh (Argonia)" [0x0A000800]
	RSP+2E0: (CellLoaderTask*)
CALL STACK: SkyrimSE.exe+02BE715 <- +0300ADC <- +02BFE78 <- +02D710D <- +0310AE9 <- +030D2EE <- +02A1323 (CellLoaderTask)
```

Cell 0x103C32 is cell k = 7705 of NewWorld.cs's numbering, (-23, -137) (read back with `ArgoniaPlugin cell`): it holds
LAND, water and a navmesh and no placed object of ours. The reference being drawn has form id 0 and no parent cell:
it was already freed when the background cell loader set up its shader, so no mesh or base of ours is named. A
background-loader race while moving fast (the owner flew with `tcl` and a raised speed); nothing in our files to fix.
