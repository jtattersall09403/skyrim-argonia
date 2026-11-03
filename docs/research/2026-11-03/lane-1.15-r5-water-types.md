# Lane 1.15-r5-water-types: water types the Skyrim way (owner #37)

L1 lane, 2026-11-03. Brief: docs/research/2026-11-03/briefs/1.15-r5-water-types.md; study: water-types.md.

## What was wrong
`tools/ArgoniaGen/WaterRecords.cs:70` (round 4) opened only the plugin named in the template, and `layer.py`
named `Skyrim.esm:DefaultWater` / `Skyrim.esm:DefaultRiverWater`. Update.esm and Tropical Skyrim.esp override
those records, so every one of our seven WATR copied a record the game never draws. Four of them were byte-equal
stills and three byte-equal flows, so no authored class reached the screen (study findings A, B).

## What changed
- `water/layer.py`: `winners(data)` reads every plugin's WATR top group in load order (`intermediate.load_order`,
  seeking past the other groups, 0.1 s) and keeps the last plugin carrying each editor id. `TYPES` holds 14 types,
  each copying one editor id from its winner. `cell_type` keys on cell_water's class, the body's kind and altitude
  band, the river strahler and the reach heading (centreline first point to last, quantised to NE/NW/SE/SW). No
  schema change.
- `WaterRecords.cs`: copies the named winner whole. The only fields of ours are EDID and FULL, plus a named `set`
  (`linearVelocity` = NAM0, `windDirections` = DNAM floats 25-27) on the three directions vanilla never baked. Those
  three are the opposite record turned half a circle: river SW from RiverWaterFlowNE, creek NW from SE, creek NE
  from SW. An unknown `set` field throws.
- `judge.py`: rule 3 (still/flow) now goes by the type's flow flag. New rule 4 (`types`) prints the cell count per
  type and fails on a water cell with no type of ours or a template that is not the winner. Both run in
  `water check`.
- `fixtures.py`: the Proving Ground water is now the lake type. `plugin/Argonia` YAML: the 29 Argonia.esm
  world-cell overrides and the Proving Ground now carry the new type keys (16 changed), taken from the new emit's
  cells.jsonl. This matches what the planner's `make plugin` will write; its Spriggit round trip re-proves it.
- `data/dependencies.json`: lineage rows on Tropical Skyrim and King of the Murkmire for the WATR records we copy.
- Journey `tests/journeys/water-types.yaml` (generator `tools/journeys/gen.py water_types`, added to `DERIVED`) and
  two `owed` rows in docs/phases/1-core-loop/checks.md.
- Doc corrections: the Why of the 1.15-r4-water-colours brief, and lane-1.15-r4-water-look.md:7 (Tropical Skyrim
  does lay `textures/water/defaultwater.dds`).

## Types, templates (the winner), cells (`water check types`, emit of the current DB)
| type | template | flow | cells |
|---|---|---|---|
| ARG_WATR_sea (WRLD NAM2/NAM3) | Tropical Skyrim.esp DefaultWater 000018 | still | 6862 |
| ARG_WATR_lake | Tropical Skyrim.esp DefaultWater 000018 | still | 137 (37 lowland pond/pool/lake + 100 fresh cells with no body or reach) |
| ARG_WATR_marsh (green) | Tropical Skyrim.esp DefaultMarshWater 105CC3 | still | 1035 (marsh-deep, backswamp) |
| ARG_WATR_black | King of the Murkmire.esp DefaultBlackmarshWater 08184260 (load id) | still | 1777 (swamp, marsh-fringe, 137 blackwater cells with no body or reach) |
| ARG_WATR_cold | Dawnguard.esm DefaultWaterCold 02001C18 | still | 255 (tarn-upland, plunge-pool, montane/upland pond and pool) |
| ARG_WATR_brackish | Tropical Skyrim.esp DefaultMarshWaterTransition 105CC4 | still | 146 (brackish 139 + 7 tidal mudflat) |
| ARG_WATR_river_ne/nw/se/sw | Update.esm RiverWaterFlowNE 0E717C / NW / SE; SW = NE turned | flowing | 12 / 4 / 94 / 72 = 182 (strahler 2-3 = 165, plus 17 reach cells of no river) |
| ARG_WATR_creek_se/sw/nw/ne | Update.esm CreekWaterFlowSE / SW 106A24; NW = SE turned, NE = SW turned | flowing | 42 / 70 / 21 / 80 = 213 (strahler 1) |
Total 10,607 cells, 0 without a type, 0 templates off the winner. Placement reds: none.

## Measured: the sea's DNAM before and after
- Before (Skyrim.esm DefaultWater): 228 bytes, sha1 93593567a3d3; colours `2534250005100500677a7500`
  (37,52,37 / 5,16,5 / 103,122,117); fog above 0, 110.
- After (Tropical Skyrim.esp DefaultWater): 232 bytes, sha1 1bd54c7927a4; colours `51aea5001c688c00677a7500`
  (81,174,165 / 28,104,140 / 103,122,117); fog above -100, 580; opacity 0x1e in both.
- test_water_writer.py writes the ESM with ArgoniaGen and reads its bytes back with esm.py. Each of the 14 WATR's
  subrecords equal its winner's byte for byte, except EDID and FULL. The turned types differ only in NAM0 and DNAM
  bytes 100-111, and those equal `set`. Each flowing type has NAM0 nonzero; no still type sets FNAM's flow-map bit
  0x08. WRLD NAM2 = NAM3 = the sea. Every cell keeps one XCLW/XCWT, and no plane activator is written.
  `water/tests`: 37 passed.

## Owed in game (planner's batch)
`tests/journeys/water-types.yaml`, scene creature-spots, 13:00, one shore still each: sea (-62,-13), green marsh
(-62,9), black swamp (-52,-28), river-nw (-62,43), creek-nw (-62,50), tarn (-62,20), brackish rim (-19,57). The
brackish rim found no stand clear of plants within 30 m (refresh log), so its still may show reeds. Ledger rows:
"Water types read distinct" and "The sea is Tropical Skyrim's", both owed. The planner's round build must run
`make plugin`: the water stamp changes, so the emit and the world ESM rebuild.

## Open
- Lore (0032): world/sources/lore/regions/waters.md names the waters but gives no colours. Which body kinds read
  green and which read black is the brief's mapping, flagged as extrapolation.
- KotM's "black" record is olive-yellow (130,116,34). If the stills read it as green rather than black, the fix is a
  darker template, decided after the L4 still.
- Flow maps (FNAM 08, per-cell `flow.X.Y.dds`) are deferred; we use legacy baked directions only.
