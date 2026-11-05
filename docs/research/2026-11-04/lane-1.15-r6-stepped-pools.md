# Lane 1.15-r6-stepped-pools: a hillside river as pools and falls

Status: the measurement and the cause are shipped, along with the probe, the gate reach and this note. The field fix works on the water census, but it breaks the roads census at three step bridges, so it is not shipped. Its patch and its L1 tests are kept beside the lane worktree (see Owed).

## Skyrim.esm (terrain/probes/vanilla_hanging_edges.py, extended; the 77 level steps)
- The upper pool: the bed along the flow (each row's lowest vertex in from the step line) ranges over 3.43 m at p50, 8.04 m at p90 and 17.0 m at most, under the level. The whole cell's thalweg falls 6.7 m at p50, 23.3 m at p90 and 54 m at most.
- The lower thalweg is under the lower level by vertex 0, 6 and 33 (p10, p50, p90). The face falls about 2.0 m per vertex (lane water-edges-2).

## Ours, and the measured cause
- At the 183 far steps on today's ground, the upper cells' bed range is 2.4 m at p50 and 2.6 m at p90, and their cell fall is 13 m at p50 and 25 m at p90. Both are inside vanilla's bars, so the solve's in-cell fall (MAX_DROP_M 21 m against vanilla's p90 of 23.3 m) is not the cause. The solve is unchanged.
- The cause is in terrain/water_field.py. The carve does cut the footprint under its level: on the dump at (-50,46) the carved footprint stands 2.1 m under its level at p50. Then two lifts fill the pool back in:
  - the dry-edge bank lift falls at EDGE_GRADE 0.3 m per sample from line vertices up to 30 m short;
  - the hollow lift raises the under-level ground beside the river (a stepped cell's ground past FLOOD_BAND is a hollow) and spreads onto the footprint.
- At (-50,46) the lift on the footprint is 25 m at p50, and the cell ends 0 % wet.

## The fix measured (not shipped)
- `pool_room(foot)`: no lift raises a sample by more than FACE_GRADE (2.0 m) per sample of distance from the raster water. A clipped line keeps its full need and falls from it at WALL_GRADE (6 m per sample). The rule applies only in cells beside a level step.
- The bank cap in the carve (water-edges-2's second trial) was measured again and made things worse (foot far 73 against 54 without it), so it is dropped.
- Scratch generate, then the census (ground before, then after):

| | before | after |
|---|---|---|
| hanging lines | 0 | 0 |
| kept steps with no lower water within 12 vertices (of 203) | 183 | 82 |
| foot, vertices p10/50/90 | 13/33/33 | 1/4/33 |
| buried held cells | 1654 | 1215 |
| of the buried, blackwater bodies | 1243 | 1021 |

- The three stands, wet share against footprint, before and then after:
  - (-50,47): 0.4 % / 8.1 % before, 13.3 % / 8.1 % after;
  - (-47,16): 0.5 % / 2.8 % before, 6.3 % / 2.8 % after;
  - (-59,-12): 0.7 % / 2.2 % before, 3.5 % / 2.2 % after.
- The brief's bars were not met. Of the 82 far steps, 7 are measure geometry: the river leaves the straight channel-middle line. By a ±4-vertex thalweg measure, 30 remain. The buried bar of 600 cannot be met in this lane, because the blackwater bodies alone are 1021 cells (the separate lane).

## Why it is not shipped
The roads census on the same ground fails 3 roads: bank p99 is 0.70, 1.01 and 1.06 m against the bar of 0.429 m (cartwrights-cross-fig-market, gideon-ridge-runners-post, glenbridge-the-road-nisswo-house). The thorn-step bridge seat is also off by 2.48 m. Today's ground has 1 seat failure. These are the roads at step bridges: the kept pools now sit under the causeway banks. The edges-census ceilings stay at 183 and 1654 until the fix lands with a ground that holds the roads.

## Owed
1. The field patch is saved at ~/argonia-lanes/sp-scratch/pool-keep.diff, and its tests at test_stepped_pools.py in the same folder (5 L1 tests: pool room, the lower pool kept wet, the foot within 12, the face, the line holding its need; 3 of them fail on today's field). It needs one more change: a road core's band, or a step bridge's seat, exempt from `room`. That needs the road mask to reach water_field, or water_field run after the road cones.
2. Then lower FOOT_FAR_MAX and BURIED_MAX to the landed counts.
3. Then the planner's L4 at the three stands. The terrain LOD half is owed at the final step.
