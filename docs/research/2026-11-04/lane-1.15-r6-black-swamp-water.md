# Lane 1.15-r6-black-swamp-water: the black swamp's water reads black, not bright blue

L1/L2, no game. The retake is the planner's (checks.md row 159).

## (1) Cause: the cells and the record are right; the surface mirrors the sky
- Stop (tests/journeys/water-types.yaml `black-swamp`): player at -196453,-156267 (cell -48,-39), yaw 39 (NE), pitch 0, subject -181292,-137776 (cell -45,-34), clear-dry at 13:00.
- out/water/cells.jsonl over x -49..-43, y -40..-29 (84 cells): every cell's XCWT is `100003:ArgoniaWorld.esm` = ARG_WATR_black, except -46,-39 (`10000A`, creek-se, a creek's own cell, outside the subject). Levels 172.27 / 299.73 / 380.96 / 541.33 units (the stepped swamp). No neighbouring body's type is in the frame.
- The built out/terrain/esm/ArgoniaWorld.esm (2026-11-04 16:49) ARG_WATR_black DNAM is byte-equal to Update.esm MurkyWater: shallow 26,19,19, deep 9,9,6 (HSV V 0.035), opacity 100.
- So the black record itself renders blue. Its reflectivity is 0.55 and fresnel 0.25. With pitch 0 the view grazes the water, Fresnel goes towards 1, and the surface shows the reflected clear-dry sky (cubemap/SSR), not its own colour. Still 03 shows the sky's pale blue and the reflected trees on the water, not a body colour. In Skyrim, MurkyWater lies under dim sky, so the issue never shows there.

## (2) Colours tabled (read from the plugins with layer.top_group, 2026-11-04)
| record | shallow | deep (V) | reflection | ANAM | fog above | reflectivity / fresnel / spec |
|---|---|---|---|---|---|---|
| Update MurkyWater (our black, before) | 26,19,19 | 9,9,6 (0.035) | 32,35,27 | 100 | 0-60 | 0.55 / 0.25 / 3838 |
| Dawnguard DLC01DarkFallCaveDarkStillWater (r5 table) | 31,33,33 | 12,12,12 | 10,10,5 | 75 | 0-30 | 0.28 / 0.00 / 1373 |
| Tropical DefaultMarshWater (darkest Tropical natural) | 56,53,37 | 77,61,36 (0.302) | 113,91,51 | 30 | 0-110 | 0.23 / 0.05 / 1021 |
| Tropical DefaultMarshWaterTransition | 49,56,37 | 56,67,46 (0.263) | 103,91,51 | 30 | 0-110 | 0.23 / 0.05 / 1021 |
| KotM DefaultBlackmarshWater | 130,116,34 | 61,95,52 (0.373) | 97,130,72 | 30 | 0-110 | 1.00 / 0.05 / 1021 |
| **ARG_WATR_black (after)** | 26,19,19 | 9,9,6 (0.035) | 32,35,27 | 100 | 0-60 | **0.28 / 0.00** / 3838 |

The body colours are already the darkest in the stack, and so is the fog (0-60, opaque). The only lever left is the reflection. Bethesda's own dark still water reflects 0.28 with no fresnel term, so no sky boost at grazing angles. Rule 0034: `layer.REFLECT_FROM` takes those two measured floats (DNAM 20/24) from that winner. There is no number of ours. Everything else stays MurkyWater's. The writer takes `set` fields `waterReflectivity` and `waterFresnel` (tools/ArgoniaGen/WaterRecords.cs).

Not tried, and why: no shader or ENB change (that is a stack change and would need its own L4 run). If the retake still reads grey-blue, the next lever is CS DynamicCubemaps "SSR on water" (r5 black-water §3).

Lore (0032): world/sources/lore/black-marsh-province.md:72-75 (peat bogs, the Great Burn) is all the lore there is. No dossier gives a water colour, so "black = tannin-dark swamp" stays EXTRAPOLATED (r5).

## (3) Tests
tools/argonia_world/water/tests/test_water_writer.py: the written black WATR's DNAM is the winner's apart from reflectivity/fresnel (0.28/0.0), and its deep colour has V under 0.2. `test_black_swamp_stop_cells_carry_the_black_type` checks the stop's frame (x -48..-45, y -39..-34, less the creek cell): every cell's XCWT is the black type.

## (4) Gate and plan
`pytest tools/argonia_world/water/tests`: 39 passed (124.7 s), including the ArgoniaGen write-and-read-back. `pipeline.py plugin --plan`: ground and terrain skip; water runs (key e4e710cce520), and vegetation, creatures and world-esm run downstream of it. No terrain stage is reached.
