# Lane 1.15-r6-stamp-walk: stamps from an import walk; the roads census in the gate

- Cause (owner #42): the ground stamp hashed a hand list; routes' shaping entered generate.py's imports, not the list, so `--plan` said skip on an 11-03 ground; no check set a road against the cell water.
- Now every stage stamp (ground, terrain, water, vegetation, creatures) hashes the hand list unioned with `stage_cover`: an AST walk of its entry's imports (function-level too) through the stage packages under tools/argonia_world and tools/ArgoniaGen, and the schema tables named after FROM/JOIN in those files (tools/ArgoniaGen/pipeline.py).
- A top-level tools/argonia_world module (db, place_build, intermediate, ...) is hashed but not descended: descending fanned out through lazy imports to 87 modules for the ground.
- Cover measured: ground 36 files / 24 tables (entry terrain.generate), terrain 62 / 57, water 26 / 21, vegetation 63 / 60, creatures 64 / 66; the walk takes 0.8 s for all five.
- `pipeline.py stamps` or `make plugin` with `--plan --verbose` prints each stamp's files and tables.
- Tests (tools/ArgoniaGen/test_pipeline.py): an independent regex walk per stage must be inside the cover; the ground covers routes/shape.py and road, road_point, cell_water; the walk is stable and follows a new lazy or relative import.
- Every stamp's key changed once with this commit: the next `make plugin` reruns ground through creatures (honest, not stale).
- `make roads-census` (in `make check`'s PARTS; reach: routes/**, terrain/**, water/**, out/terrain/ground.stamp) runs `routes census` on out/terrain in 1.2 s (measured); it is red on today's ground until the land rebuild carries 6479c080's fixes.
- The pre-batch's `step roads` runs the shape check and then the census.
- For the owner brief: a stage's rebuild key now comes from the code it actually imports and the tables that code reads, and a road standing in water fails the gate.
