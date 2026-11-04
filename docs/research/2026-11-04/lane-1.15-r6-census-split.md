# Lane 1.15-r6-census-split
- Moved every measure-only function and constant (census, profile, wet_census, wet_main, census_main, main, load_roads, frame, corridor_reach, edge_walls, grade_along, _at; TROUGH_BAND, VANILLA_ROADS, BANK_*, WALL_M, ...) from routes/shape.py to routes/census.py; `routes/__main__.py` imports main from there. shape.py keeps the road pass and ROAD_RAISED/ROAD_WATER (generate imports them).
- Census output byte-identical before/after (`cmp` of `routes census`, both red as expected); routes + terrain tests 92 passed; ruff clean; the census tests moved to routes/tests/test_census.py.
- vanilla_road_banks.py does not import shape.py.
- The import walk (walk_imports) no longer reaches census.py, but pipeline.py `_hand("ground")` still globs `routes/*.py`, so census.py stays in stage_cover("ground") until that glob excludes it (pipeline.py is outside this lane's paths: left to the planner).
- The same glob keeps routes/infra.py and build.py in the ground cover.
