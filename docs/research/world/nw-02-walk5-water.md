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

Own WATR per kind and heading (world/water_types.py). Seams: a 5 x 5 tent, then per colour channel the mean of the
greatest and least 13-Lipschitz envelopes (Chebyshev distance, so corners too), rounded, so no edge steps more than
14 of 255 and the ramp widens with the contrast; motion (noise layers, falloff, displacement, current) never mixed.
- Seams: the look's step at a changing edge p50/p99/max 7/13/13, 0 edges over 14 (the 29-cell tent: 3/9/14 with one
  look; the 11-cell tent of the first fix: 4/22/34).
- Own record: sea 71%, pond 55%, green marsh 27%, black swamp 23%, river 5%, stream 1%, estuary 0%.
- Within 14 of its own look: sea 80%, pond 76%, swamp 49%, marsh 46%, estuary 36%, river 33%, stream 24%;
  reads as its own kind (nearer its own look than any other kind's): 90, 91, 77, 72, 85, 77, 66%.
- Flow 2,670 of 2,670 flowing cells within 22.5 degrees (current and drift); 0 of 15,935 still cells with a current.
- 6,801 WATR records.
- Channels pinned to their own colour (tried and dropped): rivers 100% within 14, but black swamp fell to 54% read
  as swamp, marsh to 54%, estuary to 39%: the swamp round every river was graded toward the river's olive.

## How the read-back's thresholds were set

- Seam step p99 and max 14 of 255: the owner's ruling (2026-11-09), smooth and gradual seams; the cap the old
  29-cell blend met (max 14) before it erased the kinds.
- Two kinds' own looks at least 40 of 255 apart (largest channel of shallow, deep and reflection colour and opacity):
  the closest pair Skyrim ships as two different waters a player tells apart, DefaultWater against
  DefaultMarshWater (reflection 119,140,157 against 103,122,117; Update.esm). Our nearest pair: pond and stream, 42.
- Each kind read as itself in at least half its cells (the cell's look nearer its own kind's than any other's): a
  player standing in a typical cell of a kind sees that kind. Replaces a pure-record share, which a kind one to
  three cells wide can never meet and which says nothing of what the player sees.
- Flow within 22.5 degrees: half a step of Skyrim's eight directional river and creek records.
- The drift convention within 45 degrees on Update.esm's RiverWaterFlowNE/NW and CreekWaterFlowSE/SW (their drift
  sits 7, 20, 22 and 23 degrees off their own current); a misread convention puts them 90 to 180 apart.
- Land within 8 units of the plane: one VHGT height step.

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
