# Terrain measurements (nw-01 step 4)

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
- LAND steps held to 1016 units on both axes. This is stricter than the format needs, since the format allows larger
  steps between rows.
