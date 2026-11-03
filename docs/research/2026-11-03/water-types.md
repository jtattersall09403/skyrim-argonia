# Water types: what we author, what Skyrim does, what we can implement (1.15 round 5, owner #37)

Read-only study, 2026-11-03. Method: `tools/argonia_world/terrain/esm.py` records() over the game's ESMs in /home/ubuntu/games/skyrimse/Data
($ARGONIA_PRIVATE is unset and no xEdit dump exists on this box; every number below is read straight from the plugins by scripts kept in the session scratchpad),
plus `out/ArgoniaWorld.esm` (09:20 build), `world/db/*.jsonl`, `tools/argonia_world/water/`, `tools/ArgoniaGen/WaterRecords.cs`.
DNAM float indices are the 228/232-byte layout; labelled ones are confirmed (4 sun specular, 5 reflectivity, 6 fresnel, 8/9 fog above near/far, 10-12 colours,
28-30 noise wind speeds [layer.py:32 cites them], 33/35 fog amounts, 36/37 fog under near/far [lane-1.15-r4-water-look.md]); 25-27 = wind directions and NAM0 = flow vector are my reading, unverified in game.

## Live docs
Covering this: `docs/research/2026-11-03/lane-1.15-r4-water-colours.md` (reverted our 7 WATR to their template), `lane-1.15-r4-water-look.md` (field diff, WRLD NAM3/NAM4), `lane-1.15-r4-water.md`, decisions 0033/0034, layer.py docstring.
Confirmed: our 7 WATR equal their Skyrim.esm templates bar EDID/FULL (read from out/ArgoniaWorld.esm below); WRLD carries NAM2/NAM3.
**Contradicted / superseded:**
1. "Vanilla" in those docs means the **Skyrim.esm** record. It is not what the game draws. Update.esm and Tropical Skyrim.esp override `DefaultWater` (below). We never see that, because WaterRecords.cs:70 opens only the named master.
2. lane-1.15-r4-water-look.md:11 "No mod in the stack lays anything under textures/water/": FALSE. `mods/tropical-skyrim-sse/textures/water/defaultwater.dds` (699,192 bytes, 2013) is laid.
3. lane-1.15-r4-water-colours.md reads "marbled, blotchy black and green" as our overrides. The values it reverted to are Skyrim.esm's dark green (37,52,37)/(5,16,5), a record the game replaces. The cause is unproven at L4, but it is now the better suspect (finding A).
**One doc to edit:** `tools/argonia_world/water/layer.py` docstring/TYPES comment (lines 1-41) plus its brief `docs/research/2026-11-03/briefs/1.15-r4-water-colours.md` Why. No new file.

## Findings first
A. **Template is the wrong plugin (VERIFIED, L1).** Winning DefaultWater (formid 000018) per plugin, same fields:
| plugin | opacity | shallow / deep / reflection RGB | fog above near,far | refl | wind speeds |
|---|---|---|---|---|---|
| Skyrim.esm (what we copy) | 30 | 37,52,37 / 5,16,5 / 103,122,117 | 0,110 | 1.00 | .019,.013,.096 |
| Update.esm (SSE override) | 50 | 38,39,24 / 5,14,18 / 119,140,157 | -10,150 | 0.80 | same |
| Tropical Skyrim.esp (last wins) | 30 | **81,174,165 / 28,104,140** / 103,122,117 | -100,580 | 0.50 | .017,.013,.096 |
The sea, lakes and every still type in `out/ArgoniaWorld.esm` (0F100000-0F100003, read back) carry the first row; the game's own sea is the third. Our `ARG_WATR_*_flow` copies match DefaultRiverWater exactly (38,39,24...).
B. **Our seven WATR are four visually identical still waters and three identical flowing ones (VERIFIED).** Sea, brackish, blackwater, fresh: byte-equal DNAM. The three `_flow` types differ from the stills only by the river template. So today the owner cannot see any class.
C. **Skyrim varies water by parameters only (VERIFIED).** All 34 Skyrim.esm WATR use the one noise texture `DefaultWater.dds` x3 (NNAM); the look differs by colours, opacity, fog, reflectivity/fresnel, noise wind speed/direction, specular. 4 flow directions are baked as separate records (NAM0 vector).
D. **Rivers use a per-cell flow map in SSE (VERIFIED correlation).** Update.esm adds `RiverWaterFlow` (01001232, FNAM 08, NAM5 `riverflow.dds`) and `RiverWaterFlowBlend`/`DefaultWaterFlowBlend` (FNAM 18). 613 Tamriel cells take XCWT RiverWaterFlow; Skyrim - Textures7.bsa holds 641 `textures/water/skyrim.esm/flow.X.Y.dds` (X -43..47, Y -26..26, ~5-10 KB each); 605 of the 613 cells have a matching file, 14/14 blend cells too. A flow-map record needs a per-cell derived texture (0014: made at install).
E. **Placed planes carry their own type inside a cell (VERIFIED).** In Skyrim.esm, 133 placed ACTI-with-WNAM refs in Tamriel exterior cells all stand in cells with **no XCWT**: 61 `Water1024RiverFlowNE`, 30 `Water1024Creek`, 27 `TundraStream*` (CreekWaterFlow), 19 Volcanic, 11 CreekFlowSW. Streams are placed pieces, not cells.
F. **KotM already ships a green-olive Black Marsh water** (DefaultBlackmarshWater 08184260, plus 5 flowing twins) but no CELL/ACTI in the plugin uses them: ready templates, unreferenced.

## 1. Our authored types
| class | defined | cells | reaches the ESM? |
|---|---|---|---|
| sea / brackish / blackwater / fresh | world/schema.sql:6582 CHECK on `cell_water.water_type`; solve.py:70 WATER_TYPES; body_type solve.py:165, reach_type :177, one_type_per_sheet :499, salinity :538 | sea 6862, blackwater 2925, fresh 681, brackish 139 (cell_water.jsonl) | yes: XCWT via WaterRecords.cs:104 from layer.cell_type (layer.py:56) |
| flowing twin of the three non-sea | layer.py:35 EMIT_TYPES, cell_type = reach cell without body | 395 flow cells (218 fresh + 177 blackwater) | yes, 3 `_flow` WATR (0F100004-06), DefaultRiverWater body |
| body kind (hydrology_body.kind) | schema.sql:5185; marsh-fringe 735, marsh-deep 674, swamp 656, pond 82, mudflat 28, pool 24, backswamp 22, lagoon 20, tarn-upland 16, plunge-pool 15, lake-lowland 7, ocean 1; altitude_band lowland/montane/upland/tidal | per cell via cell_water.body_id | **no**: only folds into water_type |
| river class (hydrology_river.water, reach.water) | schema.sql:5423/5455; whitewater 344 reaches, clearwater 237, blackwater 34; strahler 1: 81 rivers, 2: 15, 3: 5 | flow cells: strahler 1 = 213, 2-3 = 165, tidal 3 reaches | **no** (blackwater reach maps to blackwater; white/clear collapse to fresh) |
| tidal | reach.tidal (3 reaches), bodies in band tidal (62) | brackish within 3 cells of the sea | as brackish only |
Distinctions the DB makes but the ESM drops: black vs green swamp (marsh-deep 957+ swamp 944 + fringe 650 all "blackwater"), stream vs river (strahler), mountain (tarn-upland 90 + montane pond 127 + montane pool 20 = ~240 fresh cells) vs lowland pond/lake (pond 12, lake-lowland 10 fresh, 9 blackwater), clear vs white vs black rivers. Sea 6862 includes 3 lagoon cells. Lore (world/sources/lore/regions/waters.md) names bays, Panther/Keel-Sakka rivers, Lake Blackwood; it gives no colour spec, so any black/green split is a 0032 call to cite from the dossier or flag as extrapolation.

## 2. Skyrim's mechanism (0034)
- Count: Skyrim.esm 34 WATR; Update.esm 38 (adds RiverWaterFlow, RiverWaterFlowBlend, DefaultWaterFlow, DefaultWaterFlowBlend, overrides the rest with INAM image space 01000946); Dawnguard 11; Dragonborn 7.
- Assignment: WRLD NAM2 = worldspace default (Tamriel 00000018) + NAM3 LOD type + NAM4 LOD height (-14000 = default water height DNAM); CELL `XCLW` level, FLT_MAX = use default (sea) ; CELL `XCWT` overrides the type for that cell; placed ACTI `WNAM` gives a plane its own type.
- Tamriel census (11,187 CELL records, Skyrim.esm alone): **10,742 have no XCWT** (the sea and the 83 cells with their own lake level, = DefaultWater; I did not pin Lake Honrich by name); 173 RiverWaterFlowNE, 75 NW, 23 SE (White River etc.; clusters x[1,18] y[-14,0]), 25 CreekWaterFlowSW + 1 SE + 5 DefaultCreekWater (streams), 72 DefaultMarshWater + 19 DefaultMarshWaterTransition (Hjaalmarch, x[-14,-3] y[14,23], XCLW=FLT_MAX so at sea level), 39 DefaultVolcanicWater (the north-east hot-spring cluster, x[26,35] y[-9,-4]), 3 DefaultRiverWater, 7 DefaultWaterNW, 2 MurkyWater. With Update.esm: 613 cells RiverWaterFlow + 14 DefaultWaterFlowBlend.
- Lakes and the sea are the **same** WATR; vanilla has no mountain-lake/pond type. Rivers = flowing WATR per cell (4 baked directions; in SSE a flow map); creeks = CreekWaterFlow* cells plus placed TundraStream/Water1024Creek pieces; marsh = DefaultMarshWater with a Transition type at its rim.
- Fields that differ (Skyrim.esm): DefaultMarshWater = DefaultWater except displacement (idx 18-22), fog-under amount 1.0, near -10000; Creek (CreekWaterFlow) op 0, 71,78,67/35,35,24/71,92,116, fog 20,160, spec 1600, speeds .035,.083,.178; MurkyWater op 100, 26,19,19/9,9,6/32,35,27, fog 0,60, fresnel .25; WRWaterFlow 34,40,32; DefaultVolcanic 130,116,34/61,95,52/97,130,72 op 93.
- Flow vectors NAM0 (x,y): NE (2.54,1.35), NW (-1.96,2.0), SE (1.8,-2.2), SW (-0.98,-0.69) with speeds .09/.04/.2-.3 (river), .025/.062/.065-.098 (creek).
- Constraint (engine, from the record shape): one XCWT and one XCLW per cell, one LOD type per worldspace (NAM3). Distant water therefore reads as the sea type everywhere (lane-1.15-r4-water-look.md:18; xLODGen builds it, worldspace-building-guides.md:17). A different type in a cell is a placed plane (finding E), which re-opens the plane-budget problem 0033 retired; avoid.

## 3. Tropical Skyrim and the rest of the stack
| plugin | WATR | what it changes |
|---|---|---|
| Tropical Skyrim.esp | 4: DefaultWater, DefaultMarshWater, DefaultMarshWaterTransition, DefaultVolcanicWater | sea/lake turquoise 81,174,165 / 28,104,140, fog -100,580, refl .50; marsh brown-olive 56,53,37 / 77,61,36 / 113,91,51, refl .23, winds .007 (calm); transition 49,56,37 / 56,67,46; volcanic 111,103,53 / 119,101,28. Rivers and creeks untouched (Update.esm values). Cells: 44 marsh, 36 volcanic, 39 NE, 25 NW, 15 SW, 12 transition XCWT re-listed. Texture: 1 loose `textures/water/defaultwater.dds`. |
| King of the Murkmire.esp | 8: DefaultBlackmarshWater (130,116,34 / 61,95,52 / 97,130,72, op 30, refl 1), BlackmarshRiverWaterFlow SE/NW/NE/SW + Blend (same colours, op 50, FNAM 18, speeds .09-.095/.04/.16-.3), DefaultHistSapWater (162,82,2...), DefaultIchorWater (37,126,64...) | no cell uses the Blackmarsh ones; its cells use Volcanic 26, WaistHeightStill 26, RiverWaterFlow 6. Textures: none under water/ (BSA has 18 water-named meshes, lily/wheel). |
| Black Marsh & Valenwood (Black Marsh.esm), HTBM + Cipactli, Depths of Skyrim, Ferries, Sailable Ship, ccFish, Xanmeer, ArgonianLakeHouse | 0 | none |
| evgSIRENROOT.esm | 2 interior waist-height | interiors only |
| ccBGSSSE025-AdvDSGS.esm (in Data, not in argonia-plugins.txt) | 2 MurkyWaterFlow | a murky flowing type, unused by us |
| Dawnguard | DefaultWaterCold (45,94,96 / 31,55,58, op 30), DLC1WaterFastFlow (61,70,60, op 81, speeds .17/.09/.13, fog 0,530), Frostreach flows | cold clear teal, fast rapids |
| Vanilla textures/water (Textures7.bsa, 646) | defaultwater.dds, riverflow.dds, waterrainripples.dds, waterrainlut.dds, dlc2tenticletile_n.dds + 641 flow maps | |
Per their docs (dependencies.json): TS is a climate overhaul with tropical sea colours; KotM is the Argonian Murkmire world; no stack mod is a water overhaul (Community Shaders only adds `WaterEffects/watercaustics.dds` and `meshes/water/WaterMesh.nif`).

## 4. The implementable set (per cell XCWT, one level per cell, as ruled)
Template to read from the **winner** (Update.esm then Tropical Skyrim.esp), not Skyrim.esm. Colours are record fields; set them as our own numbers (0003), citing the template.
| authored type | cells | WATR to define | template / fields to set | cost |
|---|---|---|---|---|
| sea | 6862 | ARG sea (also WRLD NAM2/NAM3) | TS DefaultWater: 81,174,165 / 28,104,140 / 103,122,117, fog -100,580, refl .5, op 30 | records only |
| brackish (tidal, mudflat, lagoon-edge) | 139 | brackish | TS DefaultMarshWaterTransition 49,56,37 / 56,67,46 / 103,91,51 (Skyrim's own sea-to-marsh blend) | records only |
| blackwater swamp (marsh-deep, backswamp) | ~1000 | blackwater | TS DefaultMarshWater 56,53,37 / 77,61,36 / 113,91,51, refl .23, winds .007; darken deep for "black" | records only |
| green swamp (swamp, marsh-fringe) | ~1600 | swamp-green | KotM DefaultBlackmarshWater 130,116,34 / 61,95,52 / 97,130,72 (or Skyrim.esm DefaultWater green 37,52,37), winds as TS marsh | records + layer.py picks by body kind (no schema change: cell_water.body_id -> kind) |
| lowland pond / lake | ~22 fresh | pond | Update.esm DefaultWater (op 50, 38,39,24 / 5,14,18); keep still winds | records only |
| mountain lake / tarn / pool | ~240 | mountain | Dawnguard DefaultWaterCold 45,94,96 / 31,55,58, fog 0,110; same still winds | records only |
| river (strahler >= 2, 165 cells) | 165 | river-flow (+ black river twin) | Update.esm RiverWaterFlow (op 50, 38,39,24 / 5,14,18 / 119,140,157, speeds .09/.04/.3); blackwater river = RiverWaterFlow with TS marsh colours (KotM Blackmarsh river is olive-green) | records only if legacy FNAM 0 + 4 baked directions (NAM0 NE/NW/SE/SW chosen by reach heading, as Skyrim.esm); flow-map FNAM 08 needs a derived `textures/water/<plugin>/flow.X.Y.dds` per cell: **not cheap**, 641 files in vanilla, inferred path |
| stream (strahler 1, 213 cells) | 213 | creek-flow | CreekWaterFlow: op 0, 71,78,67 / 35,35,24 / 71,92,116, fog 20,160, spec 1600, speeds .035,.083,.178 | records only; vanilla also places TundraStream pieces |
| falls/rapids | 7 falls, 158 rapids | none | Water1024 + falls kit already the 1.15 step rule | placed pieces, already built |
Not possible per cell: two types inside one cell (stream entering a pond, river meeting sea in a shared cell) other than a placed plane (finding E, avoid) or a Blend type (DefaultWaterFlowBlend at the edge); distinct LOD colour for swamp vs lake (one NAM3). Skyrim's own answer to an edge is a Transition/Blend record at the rim cells, copyable for green-to-black.
Existing machinery: `layer.cell_type` (layer.py:56) and `EMIT_TYPES` (:35) become a table keyed (water_type, body kind, strahler); the CHECK at schema.sql:6582 stays; WaterRecords.cs:66-78 stops duplicating Skyrim.esm and writes the per-type numbers (the test at test_water_writer.py:86 that asserts template equality is replaced by one asserting the numbers in the table).

## 5. Order and checks
1. **Sea + lakes on the real DefaultWater (TS)**. L1: WATR sea DNAM colours == TS values and WRLD NAM2/NAM3 -> it; L4: still at the Claywater shore + one far vantage (LOD NAM3); proves finding A.
2. **Black vs green swamp.** L1: counts of cells by type (blackwater ~1000, swamp-green ~1600) and DNAM colours differ; L4: two stills, a marsh-deep cell and a swamp cell, same time of day.
3. **River vs stream.** L1: flow cells split by strahler (165/213), NAM0 vector by heading, creek colours; L4: river-steps journey stops on one strahler-2 reach and one strahler-1 reach, upstream-facing still.
4. **Mountain tarn vs lowland pond.** L1: 240 vs 22 cells, DNAM; L4: one tarn (montane) and one lowland pond still.
5. **Brackish/tidal rim** (Transition template). L1: 139 cells; L4: delta mouth still. Defer flow maps (D) and sap/ichor.
Owner ask "figure out what's easy" answered: all of 1-5 are records-only plus a layer.py lookup; flow-map rivers are the one costly item.

## Recommendations
- Re-point the template read to the load-order winner (Update.esm, Tropical Skyrim.esp), evidence finding A; this alone may clear the "black-and-green" shores. Prove on the round-5 sky A/B deploy by one extra still pair (old vs new sea).
- Correct the "no textures/water mod" line in lane-1.15-r4-water-look.md:11 and note TS's loose defaultwater.dds is laid (check that it is the file loaded: the stack is MO2, and bsa defaultwater.dds is 2.4 MB compressed against its 699 KB).
- Ask whether any cell sheet could mix; `one_type_per_sheet` (solve.py:499) already keeps one type per lake, which matches Skyrim; keep it.
- Defer flow maps until step 3 reads as river vs stream: the legacy NE/NW/SE/SW records give flow direction without textures.

Covered: tools/argonia_world/water + terrain/esm.py, tools/ArgoniaGen/WaterRecords.cs, world/schema.sql, world/db (cell_water, hydrology_*), out/ArgoniaWorld.esm, Skyrim/Update/Dawnguard/Dragonborn/HearthFires ESMs, Tropical Skyrim, KotM, Black Marsh.esm, HTBM, Depths, SIRENROOT, ccFish/AdvDSGS, Skyrim Textures7/Meshes1 BSA indexes, MO2 mods water files, docs/research 2026-11-03, decisions 0033/0034, lore waters.md · Skipped: xEdit dumps (none on box), DDS content of flow maps, in-game look (no game machine), LOD water generation internals (xLODGen), old-decisions archive.
