# Lane 1.15-r6-road-profile: the causeway reads a pale slab

Brief: docs/research/2026-11-04/briefs/1.15-r6-road-profile.md. L1/L2; the L4 read is the planner's batch.

## The evidence, read
chain27 05-road-look-1: blackwood-20 a wide pale edge-less band; flat-46-s0 a tapering pale lane with a pink spike at
the right edge, s1 a hard straight edge and a torn stair edge; slope-57 a pale bank. Read frame by frame: flat-46's
spike and s1's straight edge and torn stair are a tree trunk and its root base at the camera's near plane (s1 is the
camera inside the trunk), not the LAND: the LAND's steepest second difference across at that point is 0.03 m. That is
row 167 (the vegetation lane's tree on the lane), not the road pass.

## Measured (out/terrain, ground 03:23; Blackwood Road, height relative to the centre, -12..+12 m every 1 m)
| stand | before | after (the road pass replayed on generate's dump) |
|---|---|---|
| b20 | tilt -0.18..+0.20, fold 4 m 0.02 (a site's blend: Onkobra field station 51 m) | -0.16 at -4, +0.30 at +4 (fold 0.07): unchanged, not pinned |
| f46 | lo == hi across all 24 m: Fort Greenditch's flat pad (17 m off, r 45 m) pins it; flat +-0.05 | +0.22 at -4, +0.06 at +4, centre the low line (fold 0.14) |
| s57 | uphill cut 1.9 m at 5-8 m, downhill flat | unchanged: a bench on the slope |

Province, roads at 50 m steps (507 points; census.profile_census): flat width (|dz| < 0.1 m) p95 17.4 m, 15.8 % of
points wider than 7.5 m; by cause: 43 of 50 pinned points, 22 of 237 in a site's blend, 23 of 241 on a causeway, 5 of
47 other. After (replay, without the slope limit): p95 8.0 m, 5.3 %, fold 4 m p50 0.285 (band 0.18..0.45), second
difference p95 0.235.

## Bethesda's road (0034; probes/vanilla_road_profile.py on Tamriel cells -32..0 x 0..32, 365 Road* meshes)
Flat width p50 3.0 m, p95 7.5 m; fold p50 0.10 at 2 m, 0.42 at 4 m, 0.75 at 6 m, 1.03 at 8 m; second difference
across p95 0.487, p99 0.911. Through the Hjaalmarch marsh (9 meshes with marsh paint beyond 8 m) the same trough
(0.43 at 4 m); 0 meshes stand raised with both sides under the centre (1 of 365 overall). Bethesda has no crowned
raised road: a road through wet ground is the same trough, so ours keeps the trough on the causeway's floor. Paint:
the marsh road's dirt holds its weight to 5 m from the centre and is gone by 7 m.

## Fixes (routes/shape.py, terrain/material.py, terrain/build.py)
1. A causeway's floor under the centre: the centreline is lifted to the floor before the trough is added, so the
   trough rises from the dry top (before: the centre's set clipped up to the floor flattened +-3.5 m).
2. A place's pin (lo == hi) inside a road's core has its floor lowered by the centre's set (half the core's trough,
   0.27 m for the 5 m core), never raised: the trough shows through a site's pad.
3. Paint full over the flat half width + ROAD_FULL_M 2 m, blending over 2 m (was 0 + 4 m): the measured 5 m / 7 m.
   Built weights at the Blackwood Road's 43 points: lane-edge (+-3 m) samples with grass-growing weight >= 0.25 from
   0.37 / 0.05 to 0.02 / 0.02 (row 163: the ferns on the lane are GRAS by the ltex). The road's reuse key reach follows.
4. Gate: `routes check` fails on more than 5 % of road points wider than 7.5 m or a second-difference p95 over 0.487
   (census.profile_fails); census.lane_grass counts lane samples on the built LAND (before: 388 of 3567 at >= 0.25,
   46 won by a grass ltex).

Tests: routes/tests/test_road_profile.py (20 sampled causeway points in the 4 m band, flat width <= 7.5 m, second
difference under the bar, pad trough and never raised, the slab flagged, paint widths); 113 routes+terrain tests
pass; ruff clean; `make plugin PLAN=1`: ground, terrain, water, vegetation, creatures, world-esm run.

## Owed
The whole-province generate (coordinator, memory: no second generate; the chain's land pass rebuilds) and then
`routes check` on it (the 5.3 % replay sits just over the 5 % bar: the slope limit may move it), the lane_grass
after count, the terrain LOD half at the final step, and the road-look rerun (rows 149, 163). The spike and torn edge
are row 167's tree.
