# Lane 1.15-r6-terrain-rows: land rows reused when only their own inputs moved

- Finding: the row cache existed (build.row_key) but its shared base (`_terrain_stamp(ground=False)`) hashed the whole road and
  road_point tables, the water_regrade/place_ground stamps and `_cover_key("terrain")` (code and ~55 tables: creatures, place,
  build_cell, weather...). Any change to any of them, e.g. the re-routed arcs, rebuilt all 262 rows (852 s on r6-land4).
- Fix: the base now holds only the build's code (plus cellwater/solve/patches) and land_cover, land_cover_ltex, material_gradient.
  Roads enter each row's key as the segments reaching its window (`build.road_key`); water, regions, ground, patches already did.
- The build prints `rows: N reused, M built`. Tests: test_land_reuse (one-band edit rebuilds only its reach, bytes equal a
  clean build; road key per row, 128 rows keyed in well under 2 s). Terrain tests 69 green, ruff clean.
- Expected saving: a local change (seats, a few cells of road) rebuilds the rows within ~8 cell rows of it, ~10-40 of 262 (about 60-120 s of 850 s). The first build after this commit is a full one (build.py is in the key).
