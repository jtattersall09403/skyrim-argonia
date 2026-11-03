# 1.15 r4 salinity lane

Cause: `one_type_per_sheet` (solve.py) gave the whole level-0 sheet (6,476 raster-sea cells plus the marsh at 0, one 4-joined sheet of 6,990 cells) the type most of its *body* cells held; the sea cells carry no body, so the 140 marsh body cells outvoted the sea and every sea cell became blackwater.

Rule (solve.py `salinity`, after the sheet vote): sea stays sea (and is its own sheet); level-0 water joined to it by 4-connected level-0 cells: lagoon body = sea; distance <= 3 cells = brackish; beyond = its body's type (blackwater). Water above 0 is untouched. Reach = 3 cells = `DELTA_CELLS` in tools/argonia_world/regions/classify.py (the tidal delta limit); lore waters.md item 4 ("tidal reach is long") and 50-hydrology-climate.md step 9; 0033 section 1.

Cells per type (cell_water), before -> after: sea 9 -> 6,862; brackish 3 -> 139; blackwater 9,914 -> 2,925 (level-0: 6,990 -> 1); fresh 681 -> 681; total 10,607 unchanged.
Water check: 0 with two levels, 0 steps without a chain, 0 bodies with neither (0 reds). Test: test_salinity_by_distance_to_the_sea_on_a_synthetic_coast; `make check-reach` green.
Owed in game: coastal-lagoon and tidal-delta panel stills in the planner's next batch (reader: water reads as water, not black); needs plugin rebuild.
Note: nearly all level-0 marsh lies within 3 cells of the sea, so only 1 level-0 cell stays blackwater; the reach is a one-constant change if the planner wants it shorter.
