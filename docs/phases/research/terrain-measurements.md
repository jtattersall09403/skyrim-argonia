# Terrain measurements (nw-01 step 4, nw-02 step 4)

Measured 2026-11-08 from LAND records (VHGT decoded as in `tools/bmv_map/build.py`, cells stitched, scipy distance
transforms); metres, 70 units = 1 m, 1.83 m per vertex. Skyrim.esm only (no Update.esm overrides).

## Skyrim roads (365 Road meshes, cells -32..0 x 0..32; all Tamriel, 1571 meshes, in brackets)
- Flat width p50 3.0 m, p95 7.5 m, max 15.5 (all: p50 3.0, p95 7.5). Re-verified.
- Trough below the centre line: 0.10 / 0.42 / 0.75 / 1.03 m at 2 / 4 / 6 / 8 m out (all: 0.11 / 0.40 / 0.70 / 0.96).
- Raised crowned road: 1 of 365 (all: 10 of 1571). Skyrim lays roads in a slight trough, never on a causeway.
- Grade along (earlier probe, not re-run): p50 0.053, p95 0.164, max 0.219.

## Skyrim ground
- Sea level: the Tamriel default water height is -14000 units; 10630 of 11186 cells use it, the rest have their own
  (lakes).
- Vertex slopes over 30 / 45 / 55 / 65 deg, land steps only: 26.3 / 10.3 / 4.7 / 1.2 % (16.8M steps). Land slope p50 /
  p90 / p99: 17.4 / 46.7 / 66.0 deg.
- VHGT: the int8 step peaks at 127 (1016 units, 82.9 deg) along a row. Row-to-row steps reach 2632 units, because only
  column 0 accumulates down the rows.
- Sea shore, inland height p50 / p90: 0 m 0.11 / 0.69; 4 m 0.69 / 2.86; 8 m 1.83 / 7.89; 16 m 4.91 / 19.5; 32 m 12.9 /
  33.4; 64 m 28.9 / 65.8 (n 16k to 37k each).
- Sea bed depth offshore p50 / p90: 0 m 0.23 / 0.80; 4 m 0.91 / 2.63; 8 m 2.06 / 6.06; 16 m 5.26 / 14.5; 32 m 10.5 /
  26.4; 64 m 19.2 / 45.5.
- Rivers (187 bodies under 60 m wide): bed depth at the centre p50 / p90 is 1.03 / 2.5 m at 10 m wide; 1.86 / 3.7 at
  20 m; 2.09 / 4.2 at 40 m. Bank height p50: 1.5 m at 4 m from the water; 3.9 at 8 m; 12.7 at 16 m.

## BM&V Black Marsh (Black Marsh.esm with Black Marsh North.esp; water at 0 in every world)
- Land height above the water p10 / p50 / p90 / p99: BlackMarshNorth 0.57 / 1.71 / 8.9 / 61.8 (1.36M vertices);
  BlackMarsh 0 / 0.46 / 12.2 / 193; BlackMarsh2 0 / 2.06 / 75.9 / 127.
- Slopes over 30 / 45 / 55 / 65 deg: BlackMarshNorth 5.6 / 3.3 / 2.2 / 1.1 %; BlackMarsh 7.0 / 4.7 / 3.6 / 2.4 %;
  BlackMarsh2 19.3 / 9.8 / 5.7 / 2.0 %.
- Shore, inland height p50 / p90 (BlackMarshNorth): 0 m 0.11 / 0.57; 4 m 0.46 / 1.71; 8 m 1.03 / 3.09; 16 m 1.71 / 8.6;
  32 m 1.71 / 16.5. Marsh ground is flat about 1.7 m above the water from 16 m inland.
- Sea bed (BlackMarshNorth): 4 m 0.69 / 2.74; 8 m 1.26 / 7.9; 16 m 2.97 / 24. Depths past 29.3 m are its -2048 default
  land, not shaped terrain.
- Channels (767 under 60 m): bed depth at the centre p50 / p90 is 0.57 / 1.6 m at 10 m wide; 1.03 / 2.7 at 20 m;
  2.06 / 5.9 at 40 m.

## What the terrain build takes from these numbers
- One water level at 0, as BM&V does. Land meets the water at 0.3 m (both games give about 0.1 m at the shore). The
  sea bed falls 0.3 m in every metre near the shore. A channel bed falls 0.10 m in every metre from each bank, so a
  channel is about 0.05 m deep for every metre of width, BM&V's ratio.
- Road trough as measured: flat 1.5 m each side, then 0.10 / 0.42 / 0.75 / 1.03 m down at 2 / 4 / 6 / 8 m out. Grade
  held under the class's grade_max with 10% headroom. No causeways.
- Low ground (marsh, swamp, bayou, basin, washes, lake, bight) ramps from the shore over 6 m, not 12 to 15: BM&V's
  marsh is level by 10 to 16 m inland (see Quality against Skyrim).
- LAND steps held to 1016 units on both axes. This is stricter than the format needs, since the format allows larger
  steps between rows.

## Quality against Skyrim (nw-02 step 4)

Measured 2026-11-08 by `tools/newworld/terrain_quality.py` (method in its docstring; results in
out/newworld/terrain_quality.json). Same grid on both sides (128 units, 1.83 m). Land only, more than 10 m from water,
split by local relief (4 x the height spread under a 100 m Gaussian: flat < 5 m, low 5-20, hilly 20-60, mountain
60+). Ours leaves out the map's northern strip above map row 80 (a raster fault fixed there during the measure).
"our_marsh" and "our_upland" are our low-form and upland-form regions. Before: build 20261108T192016Z (nw-01);
after: 20261108T213548Z.

| side | class | km2 | slope p50 / p90 / p99 deg | flat share (< 0.5 deg) | rough 20 / 100 / 500 m | ratio 20:100 / 100:500 | curvature sd | hollow share | hollows / km2 |
|---|---|---|---|---|---|---|---|---|---|
| Skyrim | hilly | 1.1 | 11.8 / 28.1 / 50.9 | 0.015 | 0.47 / 2.10 / 6.53 | 0.22 / 0.32 | 0.071 | 0.090 | 385 |
| Skyrim | mountain | 25.0 | 30.0 / 55.7 / 70.5 | 0.004 | 0.88 / 5.18 / 20.5 | 0.17 / 0.25 | 0.113 | 0.040 | 155 |
| BM&V north | flat | 0.1 | 0 / 0 / 2.5 | 0.96 | 0.04 / 0.13 / 0.69 | 0.27 / 0.19 | 0.003 | 0.013 | 54 |
| BM&V north | low | 0.7 | 0 / 4.0 / 30.0 | 0.73 | 0.21 / 0.59 / 2.53 | 0.35 / 0.23 | 0.026 | 0.002 | 92 |
| BM&V north | hilly | 2.0 | 0 / 21.8 / 67.0 | 0.66 | 0.67 / 2.13 / 4.34 | 0.32 / 0.49 | 0.073 | 0.002 | 140 |
| BM&V south | hilly | 0.4 | 12.5 / 47.5 / 73.7 | 0.32 | 1.18 / 4.12 / 3.88 | 0.29 / 1.06 | 0.124 | 0.022 | 463 |
| ours before | low | 19.2 | 5.1 / 10.6 / 18.6 | 0.10 | 0.18 / 0.61 / 1.22 | 0.30 / 0.50 | 0.025 | 0.049 | 341 |
| ours before | hilly | 9.8 | 7.3 / 19.3 / 40.7 | 0.05 | 0.34 / 1.39 / 4.45 | 0.24 / 0.31 | 0.059 | 0.024 | 160 |
| ours before | mountain | 1.8 | 10.3 / 33.3 / 77.7 | 0.02 | 1.09 / 3.15 / 9.42 | 0.35 / 0.33 | 0.202 | 0.048 | 107 |
| ours before | our_marsh | 17.9 | 5.1 / 10.3 / 17.4 | 0.09 | 0.18 / 0.67 / 2.50 | 0.27 / 0.27 | 0.027 | 0.054 | 396 |
| ours before | our_upland | 6.6 | 6.4 / 17.4 / 65.8 | 0.08 | 0.65 / 1.73 / 5.39 | 0.38 / 0.32 | 0.124 | 0.045 | 181 |
| ours after | low | 24.1 | 2.5 / 8.9 / 20.1 | 0.25 | 0.11 / 0.58 / 1.27 | 0.19 / 0.46 | 0.019 | 0.002 | 10 |
| ours after | hilly | 11.9 | 5.6 / 18.1 / 35.1 | 0.09 | 0.19 / 1.08 / 5.20 | 0.18 / 0.21 | 0.044 | 0.001 | 17 |
| ours after | mountain | 2.2 | 14.1 / 38.6 / 67.7 | 0.04 | 0.54 / 2.30 / 8.65 | 0.24 / 0.27 | 0.153 | 0.012 | 98 |
| ours after | our_marsh | 21.2 | 2.5 / 8.0 / 21.6 | 0.26 | 0.12 / 0.70 / 2.82 | 0.17 / 0.25 | 0.020 | 0.001 | 10 |
| ours after | our_upland | 8.6 | 6.4 / 23.7 / 53.8 | 0.12 | 0.31 / 1.34 / 5.11 | 0.23 / 0.26 | 0.088 | 0.005 | 41 |

(After covers the widened scope: the hatched northern province land is in, so its areas are larger.)

What the numbers say:
- Before, the ground was value noise: closed hollows covered 5% of the marsh (BM&V: 0.2 to 1.3%) and there were 2 to
  4 times Skyrim's hollow count on hills; marsh slopes p50 5 deg where BM&V's marsh is level (p50 0, flat share 0.73);
  the 20 m band was too strong against the 100 m band on uplands (0.38 against Skyrim's 0.22), the "even bumpiness"
  that reads as noise.
- After (terrain_erode: drainage erosion, slope detail, talus, low-ground smoothing, hollows filled): hollows are at
  or below both games (0.1% of marsh; uplands 0.5%); the uplands' spectrum matches Skyrim's hills (20:100 0.23
  against 0.22; 100:500 0.26 against 0.25 to 0.32); hill curvature and the mountain slope tail sit between Skyrim's
  and BM&V's; marsh slopes halved (p50 2.5 deg) and its flat share went 0.09 to 0.26.
- Left: our marsh is still less flat than BM&V's (flat share 0.26 against 0.73). Measured by distance from water,
  BM&V is level from 10 m inland (flat 0.51 at 10-20 m, 0.91 past 80 m); ours ramps up from the shore for 40 m and
  more (flat 0.05 at 10-20 m, 0.45 past 80 m), because the region table sets marsh floors at 3 to 5 m (BM&V's marsh
  lies at 1.7 m) and our marsh is threaded with channels, so most of it is shore ramp. The low-ground ramp is now
  6 m; lowering the marsh floors is the region research's call, not the terrain's.
- Our hills are gentler than Skyrim's (slope p50 5.6 against 11.8): Black Marsh's researched summits are 14 to 110 m,
  far below Skyrim's; the shape numbers, not the steepness, are what we match.

Hillshade crops (before, after, reference; 1.1 km each): out/newworld/terrain_quality/marsh-tulmek-washes.png (against
BM&V north), upland-aunike-ridge.png and upland-chixathe-mesa.png (against Skyrim's hills), city-helstrom.png (a
metropolis core settled), seam-north-stormhold.png (across the old northern scope line: no seam). Seen: the noise
"orange peel" is gone; valleys run dendritic to the water; one long straight gorge cuts the Chixathe mesa top where
drainage gathers along a plateau edge.

Preserved (out/newworld/terrain_quality_preserve.json and the build's check.json, after): map water and land exact at
every pixel (1.0 / 1.0, 10,003,161 px); shore land one sample inland p5 / p50 0.46 / 0.69 m, the same as before
(0.46 / 0.69); pads (132) height spread over the inner half radius p50 0.63 m (before 0.69); roads grade p95 0.137,
0 points over a class limit, 4 m trough p50 0.36 m, 99.7% in band (before 0.127 / 0 / 0.36 / 99.7%); entrances 49 open,
0 bad; LAND step max 1016 units (the limit).

Room to build (terrain_erode.settle_places): towns and up keep a core of radius 110 m (town), 160 (small city), 220
(large city), 300 (metropolis), 450 (megalopolis) where the 98th-percentile slope is at most 8 deg, with 35% of the
natural fine relief kept (less only where needed to meet the slope), faded out over half the radius. Built: 15
places, core slope p98 1.3 to 8.0 deg, core relief 1.5 to 15.8 m.
