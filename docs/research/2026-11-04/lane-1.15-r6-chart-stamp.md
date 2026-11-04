# 1.15-r6 chart stamp: the chart's own inputs

- The chart reads (data.py `Features.load`): world DB tables hydrology_body (ocean), cell_water, hydrology_river, hydrology_river_reach, hydrology_reach_point, route, road, road_point, place (id, name, class, magnitude, position); plus the generated ground and landcover npy files. It reads no ESM record and no out/water/cells.jsonl.
- `source_stamp()` (tools/chart/__main__.py) is now a sha256 over those ordered selects (`STAMP_QUERIES`, through db.py), the ground and landcover by size+mtime, and tools/chart/*.py. The built ESM and the world DB file's size/mtime are dropped.
- A creature, water-record or other ESM-only build change leaves the stamp alone: `render --if-stale` printed "is current" in 1.2 s after touching out/ArgoniaWorld.esm.
- Tests: tools/chart/tests/test_stamp.py (place and road row changes move the stamp; a creature-table write leaves it); 12 chart tests pass, ruff clean.
- Saved per round build that does not move a place, road, river, water cell or the ground: the whole chart pre-batch step, about 95 s plus the 4k render, replaced by a ~1 s check.
