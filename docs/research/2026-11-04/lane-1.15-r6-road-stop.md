# Lane 1.15-r6-road-stop: the road stops on the road, the build's freshness, a far-sea stop

Brief: docs/research/2026-11-04/briefs/1.15-r6-road-stop.md. No game was run (L1/L2). The L4 check is in the planner's batch.

## 1. The road-look stops measured against the Blackwood Road's DB centreline

The line is `road_point` for `route.road.gideon-blackwood-road` (297 points, 2083 m), read through db.py. The measure is
`gen.road_measure`: the eye point's distance to the polyline, the direction of the nearest segment, and the heading's
difference from it either way along the road.

| stop | as committed (old) | cell | off line | road dir / heading | off dir | re-derived | off line | road dir / heading | off dir | trough in frame | tall-grass hits | slid along line |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| blackwood-20 | -166732 30816 | (-41,7) | 10.3 m | 236 / 282 | 46 deg | -177511 30569 | 0.0 m | 313 / 320 | 8 deg | within 3.4 deg | 2 | +178 m (to 28.5 %) |
| blackwood-flat-46 | -196507 40413 | (-48,9) | 7.5 m | 273 / 303 | 30 deg | -198301 41024 | 0.0 m | 270 / 268 | 2 deg | within 1.9 deg | 4 | +38 m (to 48 %) |
| blackwood-slope-57 | -209841 41826 | (-52,10) | 3.6 m | 217 / 186 | 31 deg | -209686 41582 | 0.0 m | 205 / 194 | 11 deg | within 3.6 deg | 4 | +6 m |

All three old stops failed the bar (> 2 m off or > 20 deg off). The cause is `tools/journeys/__main__.py`'s re-aim pass for
road-look (`look.reaim`, band 15-30 m, spread 30 deg). It moved each stand off the line to wherever fewer tall-grass hits
were. Tall grass grows on the road's centreline almost everywhere: 535 dry samples every 2 m read 5.4 hits on average, and
only 23 read 0. So the "clearest" stand was always beside the road. The fix is `gen.road_stand`. It stands on the line,
faces the point 25 m on, and slides along the line in 2 m steps to the nearest stand that passes all of these: dry
footing, standable, `look.score` line, canopy and bad all 0, within 2 m and 20 deg of the line, and the trough (the line
8-30 m ahead) inside the middle third of the frame (+-11.7 deg). Within 30 m of that stand it picks the one with the least
tall grass. The re-aim pass now runs with band (d, d) and spread 0, so it keeps the stand and still writes the angles and
the scan lane's `scan:`. That is a one-line change in `__main__.py`, which is outside the brief's Paths: without it no
on-line stand survives the refresh.

**The slope stop (57 %, still 12, owner #41 "doesn't look like road at all").** It was off the road. The eye stood 3.6 m
beside the line, 1.6 m below the road's surface, on a 36 deg bank, facing 31 deg across a bend. The road ahead runs across
a 30-51 deg side slope, 1.3-2.3 m above the feet. The lane was at eye height and seen edge-on, so the still showed the
bank and no trough. The new stand is on the line itself (still the steep stretch: line slope 36 deg there). If the
trough still does not read, the cause is the road's shape across that side slope, not the camera.

**Findings for the road (not fixed here, not this lane's paths).** (a) From 10 % to 26 % of the road the centreline lies
under its cells' water, 1-5 m below level 4774.65 u (ground 4243-4677 u). No dry stand exists there, so blackwood-20 slid
178 m to the first dry stretch. (b) The road carries tall grass along almost its whole length (above). The stills will
show it, and the reader should judge it as a road defect.

## 2. The build's freshness

`pipeline.py plugin --plan` in the main tree (19:3x): ground skip 5d0fe1629f7e, terrain skip b9984b9b5e7d. Water run
e4e710cce520, vegetation run dd73026e1592, creatures run c3752e405c35 and world-esm run 3f9f4f5872f6 are stale, and so
is the whole build bcaec7d23e5c. They are stale against the working tree, not main. The tree holds other lanes'
uncommitted edits (tools/argonia_world/water/layer.py, water tests, regions/weather_seed.py, land_region_weather and
weather_colour rows, WaterRecords.cs). These feed `_water_stamp`, and the stale stages cascade down from water. Nothing
was rebuilt.

When the courses last changed on main: the land (tools/argonia_world/terrain) at 382d5d42 (11-04 10:24). The river
(tools/argonia_world/water) at b162efb2 (11-04 07:56), and the hydrology rows at 18b22ac7 (11-02 22:04). The road
(tools/argonia_world/routes) at 27dc2617 (11-04 08:25), and the road and route rows at 0d47abf9 (11-03 00:11).

r6-chain13's pre-batches ran at e6d4815d (18:09, 18:22) and a270ae4e (18:29), all on build key 93e9fc62f83f
(r5_prebatch.sh's key over world/db, schema, tools/argonia_world, ArgoniaGen, chart and data). Every course commit above
comes before e6d4815d, so that build carries them. Since then the key has moved once, to 66307aea15e3, through 076d7cf1
(creatures journey code and tests only; no course input).

## 3. The far-sea stop

`sea-far` in water-types (`gen.sea_far`). It uses a light search: sea shore cells with 4 or more sea cells straight out,
most first, at least 6 cells from the near sea stop. Stands are 5-40 m back on dry footing, facing straight out +-20 deg,
level. The aim is the farthest wet point out to 400 m. The bar: clearance 0/0/0, upper-frame cover under 10 %, near cover
under 5 %, at least 70 % of the lower half's wet rays out to 300 m on sea cells, and at least 30 of the 72 rays wet. When
no shore meets the bar, the refresh writes no sea-far stop and logs it as stale. It never raises.

| stop | stand | cell | heading | clearance | upper cover | near cover | sea share to 300 m | wet rays | frame share 0-60 m |
|---|---|---|---|---|---|---|---|---|---|
| sea-far | -9540 228064 | (-3,55) | 0 | 0/0/0 | 0.0 % | 0.0 % | 100 % | 69 | 88 % |
| sea (near, kept) | -254563 -98187 | (-63,-24) | 85 | 0/0/0 | 8.2 % | 0.0 % | 100 % (to 300 m) | 36 | 50 % |

It has the same weather (sw/fw clear-dry by form id, read back) and the same position read as the others.

## 4. Gate

`refresh --only road-look,water-types`: 8.5 s with a warm cache. A cold cache takes 262-390 s (the last cold run took 324 s). The cache key hashes gen.py,
so every edit to gen.py re-runs the six existing water stops' strict and widened searches. Those take almost all of the
time; sea-far takes about 2 s. Lanes running refreshes at the same time also evict each other's entries in
out/journeys/cache. After this lands, the planner's refresh runs cold once and then warm. `check`: 0 stale. `run_journey
--dry`: road-look 4 steps ok, water-types 8 steps ok. tools/tests/test_journeys.py and test_pass_ledger.py: 31 passed,
including the new `test_road_measure_is_the_distance_and_heading_against_the_centreline`.
