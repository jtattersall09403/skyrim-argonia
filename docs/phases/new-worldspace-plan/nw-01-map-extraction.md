# Extracting data and info from the Project Tamriel Black Marsh map

We will aim to create our worldspace based on this map as faithfully as possible: https://images.uesp.net/4/43/PT3-map-Black_Marsh.png.

Goals for phase 01: 
* extract all relevant data/info from that map into a new 3NF database (structure based on our existing DB we are using for the BM&V project). 
* research every place and build out tables for them in our db from that research

Task list
1. Create our own map key. There is a key for an equivalent map (of Hammerfell and High Rock) here: tmp/image copy 3.png. The symbols are the same/similar on our map, but some of what they mean may be different (e.g. 'breton crypt' is likely unique to Hammerfell/High Rock). Infer from our lore what our equivalents are for each symbol. Settlement tiers are the same in both. Places that share an overlay/shaded colour are part of the same culture.
2. Extract regions from https://images.uesp.net/f/f8/PT3-map-Black_Marsh_Regions.png and everything else from https://images.uesp.net/4/43/PT3-map-Black_Marsh.png. The scale is Morrowind's, we should keep that (i.e. cell sizes etc). The maps give us macro grid and cells and a ruler along the edges. We must extract all information from the map in layers in whatever way is most thorough/reliable. E.g. if you think you can extract it all just by reading the image then fine, or if you think you need to divide the image into grid squares and then read each of those one at a time, then fine as well. Just make sure you get everything from it and put it all into the new database in 3NF. Every place must have the same data fields recorded about it. Plan these out, based on what we will need later for building these places and defining how they work-in game and for fitting our story and quests and NPCs etc to them. Roads and paths must also be extracted as well and recorded in the db including their classification (major vs minor) and whatever you will need in order to later be able to paint/build them precisely onto the actual terrain such that their coordinates match the base map exactly. Thick red dash-dot lines are the province border; medium solid red-orange lines are major roads, medium dashed red-orange lines are minor roads/paths. The dashed thick blue lines are region borders within the province.
3. Go through every single place in the database and research it. Look at our lore, our lore extrapolation, and UESP. Save information and prose about it in the linked database (3NF, plan the structure to scale). If no information exists about the specific place, then continue our lore extrapolation process to populate info about it: logically, what can we infer about what this place would be like at the time of our game (4E 201), extrapolating from outher sources and from its region and from known information about similar places, and so on.
3b. Similarly, research all of the regions extracted from 2 and record information consistently about them in the DB as well.
3c. Plan (and save in our database) our 'Danger Bands' and assign every cell a danger band. We did some work on danger bands in the elder-souls-argonia repo. Apply the same kind of logic here. Cities should be safe, major roads should be D1, and generally the edges of the province are safer and the interior is the most dangerous.
4. Convert the base geography of the map into whatever we will need for creating/generating the terrain itself (including relief/slopes/elevation/whatever - i.e. this will be 3D terrain - this should be based on the research from 3b) in a skyrim native way. Remember that water will all be at one height and that height must give the waterways shown on the Project Tamriel map. Look at the places data - which ones have requirements of the terrain (e.g. caves or mines requiring entrances built into the terrain)? Build all of those terrain requirements in all at once. Look at how skyrim does roads and paths in various parts of its map (mine the game files) - do they have terrain requirements (e.g. roads created as slight depressions in the land; slope requirements for terrain roads go over; anything else) and build this in too.
5. Create an interactive browser based version of the map, which reads from (4) for the terrain and from our place records for the places and from our roads data for the roads and paths. Data fields and ids and so on should be converted to human readable and understandable form. Assume I don't know the map or any of the places. Make it accessible to me as a claude Artefact.

Do not do LOD yet. That will come later. And don't deploy anything onto the game machine yet or build the world into the game, that's the next phase.
## Working record (edited as the work goes)

Layout: the new world is its own root, `newworld/`, laid out like this repo so `tools/argonia_world/db.py` loads it
unchanged (`db.open("newworld")`): `newworld/story/data/schema.sql` and `newworld/story/data/db/*.jsonl`. The source
maps (public domain, owner 2026-11-08: kept in the repo) are in `newworld/sources/maps/`. The code is `tools/newworld/`.
Generated rasters (masks, the heightmap) go to `out/newworld/` and the bucket (`s3://argonia-private-050977237313/nw/`),
rebuilt by the code, never hand-edited.

Grid: 40 px per Morrowind cell (8192 units); the edge labels print the absolute value of negative coordinates.

| Step | Status |
|---|---|
| 0 Maps in the repo, grid calibrated (tools/newworld/frame.py) | done |
| 1 Map key (newworld/sources/key.json: 23 symbols with reasons, settlement tiers, 18 cultures) | done |
| 2a Water, land, province (raster.py); region per cell (regions.py, 24 regions, every boundary checked on the regions map) | done |
| 2b Places read tile by tile (6 readers, 48 tiles), checked in circled full-size crops, snapped (consolidate.py): 258 places | done |
| 2c Roads and borders traced to a graph (roads.py) | in progress (round 2: one spurious bridge, shortcuts in squares, hidden-label joins, the south checked by eye) |
| 3 Place research: 258 places, 9 aspects each, tiered and sourced; text-review done | done |
| 3b Region research: 24 regions, 11 aspects and relief numbers | done |
| 3c Danger bands, every cell (danger.py) | done (rerun with the final roads) |
| 4 Terrain (terrain*.py): heightmap at LAND spacing, one water level, roads and place needs built in, water bodies | in progress (round 2: landforms, pads, junctions, entrances, estuaries, owner water overrides) |
| 5 Interactive map (map_page.py), published: https://claude.ai/artifact/HytwbVPXzurvxNZWfvzo6g | in progress (republish with the final roads and terrain) |

Build everything from the sources: `python3 -m tools.newworld.raster`, `tiles`, `glyphs`, `consolidate`, `regions`,
`roads`, `terrain`, `build_db`, `map_page` (each `tools.newworld.<name>`, with the venv's python).
