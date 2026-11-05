# Lane 1.15-r6-reach-records: a finer pass-ledger reach

- Problem: every look journey reached `esm`, so any record change (a bridge, a road re-route) reran every passed journey (sky-ab 259 s, world-panel 36 stops).
- New reach item `records: <spec>` (tools/pass_ledger.py): `Weathers` (any plugin/Argonia folder), `wrld` (the WRLD record without its persistent refs), `ref EDID` (one persistent ref; they live in the WRLD's one file), `cell X,Y [rN]`.
- A cell spec hashes the cell's plugin folder and its lines in out/terrain/land, vegetation and creatures (the YAML holds only 43 override cells; LAND, plants and spawns are in those shards, one gz JSON line per cell).
- Gap, measured: a cell's water level is in none of them (only the built ESM), so water-types, river-steps and navmesh-paths keep `esm`.
- tools/journeys/reach_records.py writes the lines at the end of `journeys refresh`, from each journey's own steps (cow, setpos, moveto, position bounds): sky-ab and world-panel reach Weathers, ImageSpaces, Climates, Regions, wrld, their marker refs and cells (ring 1); road-look, bridge-look (bridge step refs), junction-dry, ground-materials (LandscapeTextures, TextureSets), rain-look (Weathers, ImageSpaces), rock-booth and tree-seat (Statics), creature journeys (Npcs, LeveledNpcs, EncounterZones) and claywater (Statics, its refs) reach their cells.
- The reach text is part of the step hash, so the first run after this re-keys every touched journey once (`run_batch --plan`: 362 of 362 steps); skipping starts from the next run, and an ESM-only change then leaves them passed (tools/tests/test_pass_ledger.py).
- Old rows cannot be mapped: the 23:40 run recorded no record hashes.
