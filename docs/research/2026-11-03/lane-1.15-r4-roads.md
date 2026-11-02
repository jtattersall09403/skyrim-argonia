# Lane 1.15-r4-roads: roads laid in the Skyrim way (owner play test 3, finding 21)

## Vanilla measured (Skyrim.esm, Tamriel cells 1..9 x -13..0, Whiterun-Riverwood; probes/vanilla_roads*.py)
- Ground across: no crown and no ditch. The road is the low line of a shallow trough: the ground rises (median, both sides folded) 0.02/0.09/0.19/0.29/0.40/0.55/0.69/0.83 m at 1..8 m out. The p25..p75 band is 0.03..0.13 m at 2 m and 0.18..0.45 m at 4 m.
- Grade along (8 m baseline, n=71): p50 0.053, p90 0.144, p95 0.164, max 0.219.
- Paint: LDirt02 plus the default dirt give about 0.70 at the centre, 0.62 at 5 m and 0.53 at 8 m. Grass rises from 3 m to 8 m, so the blend is about 4 m each side. LDirtPath01 covers only 380 vertices.
- Statics: there are no edge posts or stones at a spacing. There are 79 Road* surface meshes (about 18 m apart, covering about 2.2 km). RoadChunk stones sit on the road (lateral p50 2.8 m, about 15 per 100 m where present). Rocks (p50 10.5 m off) and fences (10.4 m) belong to the land. There are 9 posts and 4 bridges in the box.
- BM&V (Black Marsh.esm, BlackMarsh2, 3228 cells) has no road system to measure: 9 LTEX, no road paint, and only 14 DweRoad meshes.

## Changed (commit 930fd94)
- routes/shape.py (new): measures the profile and grade on any ground and lays each road in (the centreline smoothed over ±15 m and grade-limited to 0.85 x 0.219, the trough across, a 4 m blend). Its `check` is the L1.
- generate.py: the road step now runs after the water field and the sites, inside their cones (lo/hi).
- material.py and paint.py: the road paint blends over 4 m, replacing the hard one-vertex stripe.
- The two probes, a unit test, the road-look journey and the ledger row.

## Before (round-3 out/terrain) -> after (sample out/terrain-sample-roads in the lane worktree)
- Dry road points steeper than 0.219: 1421 -> 287 (of 16338). Grade p95 0.316 -> 0.186; max 3.08 -> 1.36.
- Trough fold on roads at 2 m: -0.001 -> 0.086 m; at 4 m: -0.006 -> 0.265 m. Both are in the vanilla band (it was flat before).
- The 287 left: 130 are at pinned site cores, 103 beside water crossings and 55 elsewhere. There are 221 crossings (runs on the wet raster); bridges are not built.
- L3 reader (two stills): the soft paint edge passes in both. The flat marsh window's trough is too shallow (~0.1 m). The slope window has the road lifted 0.5-1 m and a wall of more than 1 m on the right where it crosses a gully: a defect.

## Not done / owed
- Bridges at the 221 crossings; site cores re-graded to meet their roads; RoadChunk-style scatter on the road (a non-Nordic piece must be chosen first).
- In game: journey road-look (3 Blackwood Road vantages), a checks.md row, owed.
