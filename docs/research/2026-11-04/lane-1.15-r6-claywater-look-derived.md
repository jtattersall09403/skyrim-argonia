# Lane 1.15-r6-claywater-look-derived (round 6)

## Cause
r6-chain23's claywater-look stops were hand-pinned movetos onto refs (B1Door, B6Door, B5Door) or fixed offsets. Lane
claywater-water re-seated the pads and huts, and the stands never moved. A moveto onto a door ref puts the camera
inside the door's own collision, against the house wall. 01-road-in had no forced weather. I did not re-read the
stills: the lane takes the brief's reading of them.

## Rule (tools/journeys/__init__.py)
- `Build.statics()`: one box per placed exterior static. It is the AABB of the collision triangles in
  out/navmesh/province/in/objects.f32 that lie nearest that ref (within 15 m). navmesh/placed.py read those
  triangles from each piece's own Havok collision on a machine with the meshes. The ref's xy comes from build_ref.
  Markers, actors and loose items get no box. Pieces with no collision get no box either, as in game. The build gives
  90 boxes, 89 of them at Claywater.
- `static_hits(b, x, y, subj, own)`: `stand` lists the boxes within 1.5 m of the body (feet to eye). `aim` lists the
  boxes the eye line enters within 3 m. `line` lists the boxes it crosses further on. The subject's own boxes do not
  count, and neither does any box within 1 m of the subject (the poler's deck).
- Caveat: the triangles' z dates from the navmesh input of 2026-11-04 22:47. The re-seated pads may have moved by up
  to 0.8 m since then. The xy is current, except for the moved ford barrel, whose box is wide (8 x 10 m).

## Generator (gen.claywater_look; refresh --only claywater-look)
- Each stop names its subject refs, its own pieces and its preferred side, all from build_ref. The stand is 8-15 m
  off the bounds (nearest 10 m first), on 10-degree bearings out from the preferred side. It is aimed at the
  subject's middle with look.score's numbers, so the subject is at the middle of the frame. Ranking order: soaked,
  static stand, static aim, eye-ray bad, plants on the line, canopy, statics on the line, off-side (45-degree steps),
  tall grass.
- Each stop arrives by a moveto to the QuestBoard marker, then setpos x/y/z, the three angles, the clear-dry weather
  forced and read back, and `scan: 6`. The interior stop keeps its door approach and `weather: any`, plus
  `{settle: {cap: 30, min: 3}}` for the cell load. The header holds the reader checklist for each stop.

## Stops (stand x y z, subject middle, distance off the bounds / to the middle, bearing, clearance)
Every stop has 0 statics in the stand, the aim and the line, 0 plants on the line, 0 canopy, 0 bad and is dry.
The tall-grass count is never 0 in the yard, so refresh reports "not clear" for all 10.
| stop | stand | subject | off bounds / middle | bearing | grass |
|---|---|---|---|---|---|
| road-in | -229197 42575 4834 | -229120 43306 4855 | 10.0 / 10.5 m | 186 | 8 |
| well-junction | -231065 48876 4829 | -231333 47824 4857 | 11.1 / 15.5 m | 14 | 16 |
| station-house-front | -230813 48754 4843 | -231754 47361 4977 | 13.9 / 24.0 m | 34 | 21 |
| huts-row | -233168 51369 4824 | -231505 52764 5128 | 14.2 / 31.0 m | 230 | 34 |
| family-hut | -230205 55509 4814 | -230205 54459 5089 | 9.8 / 15.0 m | 0 | 42 |
| landing-and-raft | -231741 51298 4834 | -230143 51495 4825 | 12.2 / 23.0 m | 263 | 17 |
| clay-cut-and-pool | -233193 47870 4822 | -234239 47963 4781 | 14.5 / 15.0 m | 95 | 18 |
| ford-ambush-road | -236054 52693 4851 | -238077 52876 4865 | 10.1 / 29.0 m | 95 | 5 |
| livia-full-body | -230563 47658 4848 | -231193 47690 4894 | 8.5 / 9.0 m | 93 | 14 |
| signs-full-body | -230728 52344 4821 | -229974 51717 4885 | 13.3 / 14.0 m | 310 | 13 |

## Checks
- `python3 -m tools.journeys refresh --only claywater-look` regenerates the file; `check`: 0 stale.
- journey_lint: ok. `run_journey.py --dry`: 11 steps, ok.
- tools/tests/test_journeys.py: 24 passed. Two tests are new: the placed-static rule (inside rejected, 1 m off
  rejected, 2 m outside clear, own box exempt, aim at 2.5 m, line behind) and the generator (11 stops, each 8-15 m
  off its bounds, outside every box, aimed at the middle, the interior settle).
- ruff: clean. The lane ran no game; L4 is in the planner's batch (claywater-look).
