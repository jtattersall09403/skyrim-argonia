# Water kinds, flow and the water's edge (nw-02 walk 5, lane W)

Measured 2026-11-10 with `ArgoniaPlugin waterstudy` (tools/ArgoniaPlugin/WaterStudy.cs) on Skyrim.esm + Update.esm,
King of the Murkmire.esp, Tropical Skyrim.esp, BM&V and the built ArgoniaNewWorld.esm (terrain build 20261109T204317Z).

## How Skyrim makes a water read as its kind

- **Per-cell type is honoured in exteriors.** Tamriel: 11,186 cells, all flagged has-water with their own XCLW;
  XCWT on 678 of them (613 Update.esm `RiverWaterFlow`, 39 `DefaultVolcanicWater`, 14 `DefaultWaterFlowBlend`,
  7 `RiverWaterFlowNE`, 2 `MurkyWater`, ...), the rest the world's `DefaultWater`. No placed water activators.
- **Colour, clarity:** shallow, deep and reflection colours, opacity, fog distances. Vanilla's river and sea share
  every colour (DefaultWater 38,39,24 / 5,14,18); DefaultMarshWater has the sea's noise layers exactly
  (270/210/225 at 0.019/0.013/0.096), so marsh and sea move alike.
- **Flow direction:** the three noise layers. A layer's wind direction is the compass bearing the ripples come
  from; they drift toward it + 180 (RiverWaterFlowNE 233/267/252 with current (2.54, 1.35) = heading 62;
  RiverWaterFlowNW 141/106/177, current heading 316; CreekWaterFlowSE 360/309/256, SW 33/67/120). The current (DNAM
  linear velocity, x east, y north) matches. King of the Murkmire's BlackmarshRiverWaterFlowSW reuses SE's noise,
  so it drifts SE. Update.esm's SSE rivers instead read per-cell flow textures,
  `textures\water\skyrim.esm\flow.<x>.<y>.dds` (641 files): art, which we do not make.
- **Still water:** no current, layers that disagree (MurkyWater 22/150/0 at 0.016/0.02/0.02; Tropical Skyrim's
  marsh 0.007 on every layer).

## Why the built world's water all looked the same (the bytes, before the fix)

- 18,605 water cells; every cell's XCWT written and honoured. But 5,811 seam records from a 29 x 29-cell tent left
  0% of green marsh, river, stream and estuary cells and 0.5% of black swamp cells on their own record: the means
  as seen were within 8.5 to 27 of 255 of each other (green marsh 41,50,37; river 45,48,37; estuary 43,47,34).
- The base records were near-identical anyway (river = sea colours; marsh = sea motion).
- Flow: surface drift within 22.5 degrees of the channel graph in 983 of 2,670 flowing cells (median error 33,
  p90 81): the SW, NE and NW copies changed only the current, never the noise.
- 13,962 of 15,928 still cells carried a current (DefaultWater 0.22, 0.22; DefaultMarshWater 0.151, 0.285;
  DefaultCreekWater 0.23, 0.36): sea, marsh and pond all drifted north-east.

## After the fix (in memory, `waterstudy plan`, the writer's own code)

Own WATR per kind and heading (world/water_types.py), seams by an 11-cell tent with motion never mixed:
own record in 81% of sea, 45% of pond, 20% of green marsh and 15% of black swamp cells (rivers, streams and
estuaries are one to three cells wide, so every cell is near a seam and is graded, keeping its own motion);
nearest two kinds' mean looks 19 of 255 (pond and stream, which differ most in motion) to 67 (sea);
2,670 of 2,670 flowing cells within 22.5 degrees (current p90 10, drift p90 11); 0 still cells with a current;
the look's step at a changing cell edge p50/p99/max 4/22/34 of 255 (the 29-cell tent: 3/9/14, one look);
5,401 WATR records.

## The water's edge in loaded cells

Land vertices against each cell's water plane, in cells the shore crosses (`waterstudy shore`):

| | shore cells | on the plane | within 4 units | within 8 | rise across a crossing edge p10/median/p90 (units per 128) | straight shores |
|---|---|---|---|---|---|---|
| Skyrim.esm, sea level | 703 | 5.8% | 5.8% | 18.1% | 8 / 32 / 104 | 0.0% |
| Hjaalmarch marsh (cells -16..-1, 12..26) | 117 | 6.2% | 6.3% | 20.4% | 8 / 24 / 48 | 0.0% |
| Skyrim.esm, rivers at their own level | 419 | 2.5% | 6.9% | 14.2% | 16 / 40 / 128 | 0.0% |
| ArgoniaNewWorld.esm | 10,428 | 0.0% | 0.0% | 5.6% | 24 / 40 / 96 | 3.0% |

Skyrim leaves vertices on the plane; ours never sits within one height step (8 units) of it (terrain_shape
SHORE_M 0.12 m, and now quantize.off_plane guards the rounding), so loaded land does not fight the water. Its shore
slope is Skyrim's (median 40 against 32 at sea level and 24 in Hjaalmarch). A straight shore (crossing points within
8 units of one line over half a cell) is 0% in Skyrim; ours are 311 cells, nearly all on the world's frame
(x = -83, y = -237 to -239, y = -97), where the land is cut along the map's edge. The flicker and straight lines
seen from the air are therefore not the loaded land: they are the distant (LOD) terrain and water.
