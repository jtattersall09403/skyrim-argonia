# nw-01 acceptance: each requirement and its evidence

Measured on the final build (database `newworld/story/data/`, terrain `20261108T190052Z`, commit after 63e17f12).
The plan README sets no checks of its own; the acceptance is the task list of `nw-01-map-extraction.md`.

| Requirement (nw-01) | Evidence |
|---|---|
| 1. Our own map key from the Hammerfell/High Rock key, inferred from our lore; tiers as in the key; shared colour = one culture | `newworld/sources/key.json` → table `symbol`: 23 symbols, each with the key's name for the glyph (or none), its meaning and its reason (23/23); 8 settlement tiers; 18 cultures by shared square colour, all named from the lore (`research/cultures.json`) |
| 2. Regions from the regions map; everything else from the base map; Morrowind scale kept | 24 regions over 3348 cells, every boundary drawn over the regions map and matching (regions.py); frame 40 px = one Morrowind cell of 8192 units (frame.py, table `map_frame`) |
| 2. Every symbol extracted, in layers, thoroughly | 48 tiles read by 6 readers; every read circled on full-size crops of the whole province and checked by eye (1 miss added); 258 places snapped to their glyphs (`sources/reads/`, `corrections.json`) |
| 2. 3NF database; every place the same fields | schema.sql, loaded by db.py with keys and foreign keys checked (green); every place has every field; the only empty ones are meaningful: `map_label` 102 (unlabelled on the map), `culture_id` 93 (all icons: ruins, camps, wrecks, landmarks carry no culture square; `held_by` is filled for all 258), `lore_page` 245 (no UESP page, recorded in each overview's sources) |
| 2. Roads with class and coordinates matching the map; borders | 129 major and 245 minor roads as a node graph with px and world vertices (14215); 97.3 % (major) and 98.0 % (minor) of road-ink pixels lie within 2 px of a traced line, and 99.8 % of traced points lie on ink or a bridged gap (labels, glyphs, water); province border 3 parts and region borders 13 parts |
| 3. Every place researched (lore, extrapolation, UESP), prose in the linked database | 258/258 places with 9 aspect notes (2322), every note sourced (0 without a source) and tiered (canon 96, extrapolated 1855, invented 371); every name looked up on UESP; text-review done (4 reader passes, linter 0 hard hits); no duplicated or templated notes |
| 3b. Every region researched | 24/24 regions with 11 aspect notes and the relief numbers the terrain reads |
| 3c. Danger bands, every cell: cities safe, major roads D1, edges safer, interior worst | 3348/3348 cells banded (danger.py, its rules in the docstring); 21/21 city and town cells D0; 295/295 major-road cells D0 or D1; mean band by depth from the edge 1.9 (0-3 cells), 2.7, 3.1, 3.3, 4.3, 4.6 (20+); D5 only in Murkwood's heart |
| 4. Terrain inputs, Skyrim-native, one water height giving the map's waterways | heightmap 5377 x 3841 at 128 units, water level 0: 100 % of map water pixels under it and 100 % of land above (8,064,000 px, 0 exceptions); LAND format fits (largest step 1016); relief from the researched regions (mesa cliffs, ridge spine) |
| 4. Places' terrain requirements built in, all at once | 368 needs over 258 places (flat pads, 49 entrances, rises, islands, seabed, shores); 49/49 entrances face dry open ground; pads blended, banks as knolls |
| 4. Roads as Skyrim builds them (game files mined) | measured on Skyrim.esm (`research/terrain-measurements.md`): trough 0.42 m at 4 m, flat 3 m, no raised roads; built: trough at 4 m p50 0.36 m, 0 of 87,141 road points over the class grade |
| 5. Interactive browser map from the terrain, places and roads, human readable, as an Artifact | https://claude.ai/artifact/HytwbVPXzurvxNZWfvzo6g (map_page.py): terrain, original map, regions, danger, roads, borders, places; every id shown as words |
| Not LOD, not deployed | no LOD built, nothing on the game machine |
| In parallel with the Phase 4 agent | every nw-01 commit names only `newworld/`, `tools/newworld/`, `docs/phases/new-worldspace-plan/` and two new tests, plus one line each in `docs/PROGRESS.md`, `docs/owner-rulings.md` and the guard allowlist, each checked free of the other agent's edits before committing |

Water-body kinds and flow are defaults derived from the map; authoring them is nw-02's ("water everywhere there
should be water (all at once level, correct water types authored and implemented)"), by the owner's overrides in
`newworld/sources/water_overrides.json`.

Kaochalit's dark line in the hillshade is a designed cliff: Kaochalit stands in Chixathe Mesa (researched landform
"flat-topped mesas with cliff sides"); the line drops from about 32 m to 5 m, and 337 of its 394 samples steeper
than 45 deg lie in the generator's cliff mask.
