# Lane 1.15-r6-water-edges: hanging sheet edges at cell lines

Status: census and Skyrim.esm bar shipped; the root fix is diagnosed but not shipped (a trial made it worse); the gate item and the generate are owed.

## Census (tools/argonia_world/water/edges_census.py, 2 s, L1 tests in water/tests/test_edges_census.py)
For each line between a wet cell at level L and a drier neighbour: the metres of the 33 shared vertices more than 0.3 m under L, split into a kept step's channel (with its two side walls) and everything else.
Ground on 2026-11-05 03:23 (the chain27 batch's): 4876 lines; 203 hang. Channels: 2632 m (Bethesda's notch, generate.py STEP_BED_M, 2.86 m under the upper water). Everything else: 1.8 m on 1 line ((33,39) s, 2.86 m deep, beside a channel).
So the edge of the line itself is held. The banks at the line stand at L+0.3 (step-2 line: 0.3 m outside the channel, -2.9 m in it).

## Skyrim.esm (terrain/probes/vanilla_hanging_edges.py)
Out of 497 explicit-level Tamriel cells, 762 wet/dry lines hang 2.0 % (872 m). The 77 level steps hang 24 % (1075 m, the channels and falls). The step line stands over the upper level by -0.85/+1.09/+7.55 m (p10/50/90). At the channel the lower ground over the lower level by vertex in (p50) is 6.2, 5.4, 4.0, 3.5, 3.4, 1.6, 0.3 m. The lower water reaches the channel foot at vertex 0/8/33 (p10/50/90).
So vanilla keeps the channel notch and puts a lip everywhere else, which matches our rule. The step pieces stay as they are.

## The real cause of the round-6 frames (measured on a scratch generate dump, water_field on it)
The three lower cells, (-48,16), (-59,-13) and (-50,46), are 0.0 % wet after water_field, although the raster footprint covers 22 %, 17 % and 8 % of them and the carve cuts it under the level.
The lift buries them. They are level cells on a hillside: the pre-ground falls about 30 m across a cell, with dry cells or much lower cells downhill. The bank lift at those lines (touch: need = L + 0.3 + EDGE_UP, falling at EDGE_GRADE 0.3 m per sample; a step line: LIFT_GRADE 0.6) is an amount cone. Shortfalls of 30-70 m therefore spread 100-200 samples across neighbouring cells. Measured lift: 21-35 m over the lower cells and 53-70 m at its sources.
The channel's join digs a one-vertex foot to lower-0.5 at k=4. Past that point the ground stands 10-17 m above the lower water, which accounts for the "no lower water meets the foot" and the "upper sheet hanging" in step-1/2/3.
The cream sheet in gully-2 is the same class of fault: a level plane over lifted ground.
Profiles: step-1 [389.1 .. 387.3 | 384.7 380.4 376.1 371.8 367.5 | 374.3 381.1 386.3 385.8 ...] with the lower level at 367.96; step-2 and step-3 have the same shape (in this note's scratch probe p2.py output, 6 samples before the line to the lower cell's far line).

## The fix that was tried and withdrawn
A lift whose fall-off steepens with the shortfall: it falls to the ground within 6 vertices, at most 5.4 m per vertex, in binned cones. On the dump it left the lower cells 0.0-0.6 % wet and raised the lift maximum to 55 m, because more vertices became sources. It is not shipped.

## Owed (next round)
1. The rule at source belongs to the solve, not the field. A reach cell whose ground falls more than about a step across the cell beside a dry or lower downhill cell should be split there as a step, with the lower cell's level taken from its own raster water. Otherwise the dry downhill neighbour must be made wet at the reach's next level. Raising the line cannot be the answer, because it builds the dam.
   A second census is owed with it: the lower water meeting the foot, i.e. the vertices from a channel's foot to the lower cell's first wet vertex, against vanilla's p50 of 8.
2. Add the census to make check (edges-census, red on the other metres) when the Makefile is free of other lanes' uncommitted edits.
3. A whole-province generate, which the chain's land pass does.
