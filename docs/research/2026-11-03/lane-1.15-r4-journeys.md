# Lane 1.15-r4-journeys: every journey derived from the build it runs on

Brief: docs/research/2026-11-03/briefs/1.15-r4-journeys.md. L1/L2 here; L4 at the planner's next batch.

## What was wrong
- The data-driven journeys were written once against earlier ground and never re-derived: on the current build
  39 stands were stale (river-steps 8 dropped from z 20000 or ~40 m up, gully-3 35 m *under* the ground; road-look 3
  at 2.3 m up; creature-spots 7 at 11 m up; tree-seat 12 and rock-booth 6 at 1.7 m up; claywater-look 3 in water,
  1.0-2.9 m deep: landing-and-raft, clay-cut-and-pool, signs-full-body). Nothing checked a journey against the build.
- No step was checked for plants on its eye line: before, 19 of 36 setpos stills had a plant within 2 m of it
  (tree-seat 11/12, river-steps 3/8, creature-spots 3/7, rock-booth 2/6).
- The camera mode was a per-step action (tools/run_journey.py had no journey-level declaration).

## What changed
- `python3 -m tools.journeys refresh` (tools/journeys/): runs the generators that exist (panel.py, creatures/journey.py,
  vegetation/tree_booth.py, vegetation/booth.py) and the new ones (tools/journeys/gen.py: river-steps from water_step
  (3 steepest kept steps) and the cells of the water lane's gullies and still bodies; road-look from road_point of
  route.road.gideon-blackwood-road at 20/46/57 %; claywater-look/-walk from build_ref, moveto beside each ground-placed
  ref with dx dy dz), then re-seats every stand on the game's ground (LAND heights, +16 u) and moves it along the
  approach line (2 m steps, 30 m back, 2 m nearest; other bearings for a named subject) until dry and the eye line keeps
  2 m (0.5 m over a top) off any placed plant (vegetation shards, object_form bounds). Exit 1 if anything is still stale.
- L1: tools/tests/test_journeys.py (5 unit tests + the build test: every setpos within 0.5 m of the ground, every
  moveto target dry, studio markers on the ground; interiors and porch refs trusted). `python3 -m tools.journeys check`.
- `camera: first|third` at a journey's top, applied once after the load (run_journey.py, validated; L2 test). Panel,
  creature-spots, tree-seat and rock-booth say `camera: first`; river-steps `camera: third`.
- infra/gpu-box/jobs/r4_prebatch.sh: step `journeys` (refresh, red stops the job) before `plugin-ids` (the panel's
  vantage markers are build_ref rows), and commits all the derived journeys, scenes and build_ref.jsonl.

## Measured
- After: 0 stale stands; 60 vantages, 28 moved (22 out of foliage, 6 out of water: gully-1 30 m, still-1 18 m,
  Claywater raft 16 m and Signs 20 m, creature water-night, tree-seat class-tidal-delta); 15 still have 1-7 plants on
  the line after the search (dense flooded forest; the fewest-plant dry stand is kept, listed by refresh).
- Found for the water lane: gully-1's bed (cell -19,58, reach.1375-169) lies 19.8 m under its cell's water level, so
  in game the "dry gully" is under water; the still shows it.

## Owed in game
The existing owed rows (river-steps, road-look, claywater-look/-walk, creature-spots, tree-seat, world-panel) at the
next batch after the pre-batch job (which must rebuild the plugin for the panel's moved markers).
