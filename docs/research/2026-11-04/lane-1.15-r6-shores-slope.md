# Lane 1.15-r6-shores-slope: the shore falls through the waterline; one shallow colour at a seam

L1/L2, no game. Evidence: round-6 water-types scans (20261105T040257/02-water-types-1-20261105T040657), read here:
tarn s0 and brackish-rim s0 show a low flat shelf meeting the water in a straight line; sea-far s5 a flat gravel plate
ending in a vertical lip with a rectangular notch; brackish-rim s0 a cyan band at x 0-300, y 600-660 (box mean
99,133,91 against 85,111,65 below it).

## Measured before (out/terrain ground against the solved cell levels; median / p10 m over the level by signed distance)
| stand (cell, type) | -5 m | 0 | +5 m | +10 m | +15 m | +20 m | at exactly +0.30 / -0.31 |
|---|---|---|---|---|---|---|---|
| tarn (-54,8 fresh) | -1.10 | 0.30 | 0.87 / **0.45** | 1.16 / **0.50** | 2.32 / **0.50** | 3.88 / 0.67 | 152 / 275 vertices |
| brackish-rim (-19,58; sea cell east) | -3.60 | 0.30 | 1.54 / 0.96 | 7.95 / 5.29 | | | 9 / 10 |
| sea-far (15,12 dry; sea N and W) | -1.42 | 0.00 | 0.69 / **0.30** | 1.31 / 0.95 | 1.58 / 1.14 | 1.79 / 1.26 | 206 / 94 |

Skyrim.esm (probes/vanilla_shore_profile.py, 15 largest inland levels, dry vertices in the water cells), p10 by vertex:
1: 0.00, 2: 0.23, 3: 0.46, 5: 1.00, 8: 1.77, 10: 2.31, 15: 3.43, 20: 4.51 m; share within 1 m: 0.91 at 1, 0.10 at 5.
So vanilla holds no shelf at the level past one vertex (N = 1 sample, 1.83 m); ours held one flat at +0.3-0.5 m from
5 to 15 m out (the floor plate base + floor, the freeboard snap and lo = level + freeboard) and, on a dry cell's edge,
a lift to +0.3 at 0.6 m a sample, so the water ended one sample inside the cell line: the straight edge and the corner
notch. Vanilla's closed edges stop the upper water a median 9 vertices short (probes/vanilla_level_edges.py).

## The cyan strip, one sentence
The brackish rim (DefaultMarshWaterTransition, Tropical shallow 49,56,37) meets the sea (DefaultWater, Tropical shallow
81,174,165 cyan) at level 0 along a cell line, and at zero depth each cell shows its own shallow colour, so the sea
cell's shallows draw a hard cyan band that stops at the line; Skyrim.esm gives all three of DefaultWater,
DefaultMarshWater and the Transition one shallow 37,52,37 (119 of Tamriel's 21,162 same-level neighbour pairs differ in
type, 34 Transition-to-default or marsh); 286 of our 287 same-level type seams are sea beside brackish.

Posterised shading (tarn s4): the PNG is lossless with 404,566 colours, so not the still's compression; it is the
water's own noise texture under the light, not changed here.

## Fixes (this commit)
- terrain/water_field.py: a shore floor: every dry vertex within 40 samples of the water stands at least the level +
  freeboard + Skyrim.esm's p10 rise at its distance (FLOOR_UP, faded out from 20 to 40 samples; half for brackish and
  blackwater, Morthal's 326 u against Ilinalta's 648 at 10 vertices), held as the vertex's lo bound so later stages keep
  it; the level is carried over a dry cell's edge. A dry cell's edge stands EDGE_UP 2.06 m (vanilla p10 at 9 vertices)
  over the freeboard and falls at 0.3 m a sample, so the water stops inside the cell.
- water/layer.py SHALLOW_FROM + ArgoniaGen WaterRecords.cs `shallowColor`: the brackish type takes the sea's shallow colour.
- Tests: terrain/tests/test_shore_floor.py (no vertex within 0.1 m of the freeboard line past 1 sample; p10 at 5/10/15
  samples at vanilla's; marsh at half; the water at least 4 samples short of a dry cell's line): 4 failed before the
  change, 4 pass. water/tests test_same_level_seam_shares_the_shallow_colour, and read-back checks the DNAM bytes 40-42.

## Owed
- The whole-province terrain generate: the province lock was held (pid 400906, a terrain generate) when this lane
  finished, so the "after" profiles at the three stands are owed with it; `make plugin PLAN=1` names ground, terrain,
  water, vegetation, creatures, world-esm as run; the terrain LOD half owed at the final step.
- L4 in the planner's batch: checks.md 'Shores slope' and 'No hard cyan strip' at tarn, brackish-rim, sea-far.
