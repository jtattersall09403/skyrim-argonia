# Textures, plants, roads, scatter, water: A walkable worldspace.

Goal: at the end of this phase, have a walkable worldspace that we can load in-engine and walk around, and that is textured nicely and has proper textures, tree/plant coverage (including regional variation/research-derived local biome/ecology, plus variety within-region), scatter (rocks etc, built properly with no 'hollow backs'), everything seated properly (taking inspiration from the rules we learned in this repo previously where appropriate), water everywhere there should be water (all at once level, correct water types authored and implemented), and navmesh sorted across the whole province.

I don't mind how I get to it at this stage, e.g. could be an additional loaded worldspace in our current BM&V game that I can teleport to with a console command. Whatever you think will be easiest and cause least hassle.

# Quick fixes to the map from phase 01 first
Map: https://claude.ai/artifact/HytwbVPXzurvxNZWfvzo6g

* There are a few bits of the road network that are recorded in our data as major road that should be minor roads/paths (that's how they are shown on the original source map). I am guessing these were image reader misreads. Look at an image of our road network on our terrain map yourself: you should be able to see that there are some patches of major road in the middle of a span of minor road/path; and some bits of major road that only come at the end of a stretch of minor road (e.g. connecting up a minor place to the minor road network). You should be able to measure these and correct them in our roads and paths data.
* There are also one or two small gaps in the major road network that are errors, e.g. just north of Guj-Tei. FIx these too.
* Something weird at the top of the map - see tmp/image copy 5.png. Compare with the top of the source map, tmp/image copy 6.png

# General notes

* Use Black Marsh & Valenwood mod textures (the ones that automatically generate groundcover and grass etc) as much as possible; Tropical Skyrim textures if there is something we need that BM&V doesn't have.
* build and implement the skyrim native map such that it comes up in the map menu when you are in the new worldspace in game. (Does this depend on LOD? If so, do it after LOD below).
* Give the owner cheat codes/console commands for flying around so I can review what you've built.
* The earlier version of this repo did a pretty good (if imperfect) job of a lot of this. Go back through the git history and see what you can salvage. The major things it got right and struggled with are recorded in docs/phases/new-worldspace-plan/README.md. 

# Trees, vegetation, ground cover, scatter

Each region should feel both internally varied and consistently different from the other regions.
So, author a set of plant and tree types for each region (record in the DB), logically derived from the region research (which will already be in the DB by this point), and using a large variety of tree types and meshes from across the mods (full list in the elder-souls-argonia repo; prioritise BM&V and KoTM) and Tropical Skyrim. Each region's set should be different from every other region. And within each region, there should be an interesting variety of plant and tree types. In the sea areas, there should be a wide variety of ocean floor plants and scatter from Depths of Skyrim and any other relevant mods from the list. 
Rules about where and how to place each type of tree and plant (and in what combinations with one another) should be mined from game files and mod files. Pay attention to seating - previously agents placed trees with the lowest point of their mesh touching the ground, which usually was the tip of a root actually designed to be sunk into the ground so the base of the trunk sits on/just under the ground.
Trees and plants and groundcover should not be placed on roads. Road textures should use BM&V textures if they exist or Tropical Skyrim otherwise. For roads and paths, mine the skyrim game files, looking at several examples from several regions: how does Skyrim 'dress' and texture roads? By dressing I mean are there things like small rocks, crumbling walls, any other roadside markers or decorative elements? Apply them to our roads and paths too, using their Tropical Skyrim versions.
Cliffs: should be done the native skyrim way, useing the appropriate Tropical Skyrim cliff meshes/pieces, appropriately seated
Trees should not be placed in any flowing water.
Trees may be placed in some shallow standing water types if consistent with the region research (e.g. 'drowned forest' areas) but by default should not generally stand in water.

# Water

I would like to be able to draw on/directly edit myself which bodies of water on our map should flow (and in what direction), which should be still, what type of water they are (e.g. blackwater swamp vs green water marsh vs ponds vs estuary vs ocean). And then agents use 
You must infer from (a) visually inspecting the map and (b) the region research results data: which areas of water should be flowing and which should be still; which areas are inland vs estuary vs shallow coast vs ocean (all water is sea level so classification must not be based on level); for inland water, which are ponds vs greenwater marsh vs blackwater swamp. Then implement them with the correct shaders and colours and water types, the native skyrim way. (If the native skyrim way doesn't provide absolutely all of the water types we want then simplify our requirements).

Water's edge textures: this requires careful planning, rule setting and generation. Mine the skyrim game files for several examples from different regions (including the swamp around Morthal). Infer how skyrim does the progression of textures and scatter/rocks and ground cover and vegetation etc from underwater to water's edge to bank to land, and how this varies for different types of water (e.g. ocean -> beach -> coastal land, vs swamp -> swamp edge -> boggy land, vs riverbed/streambed -> bank -> land; lakes, ponds etc too). Implement our own sensible set of texture and scatter progression rules inspired by these but using BM&V and Tropical Skyrim textures and meshes and so on.

# Atmosphere, fog, natural lighting

Use whatever BM&V use. I don't think it's the Tropical Skyrim atmosphere/climate. 
Add atmospheric low-lying below eye-level drifting clouds of volumetric fog/mist (community shaders) in marshy and swampy areas and over inland water (derive from the region research about which areas should have more or less of this). It should be stronger in the mornings; on sunny days it should 'burn off' by noon, then regather at night. It should be thicker after rain.

# Elevation/heightmap

Assess the raw output from phase nw-01. How good is its heightmap/terrain relief? Mine the skyrim game files and compare. Note the quality differences between the two. Implement whatever you think best to make our terrain's elveation/heightmap/relief etc as high quality as the one used for Skyrim. (e.g. you could use erosion simulation but *without* adding any actual new water courses; reason about the best approaches to get high quality terrain and apply those you think most appropriate that won't mess with the shape of our map, water courses, or locations of roads or built places).
For large built places (like cities), make sure you 'leave space' in the terrain for them - i.e. don't make those locations so sloped or topographically complex that it will be a huge pain to build on them. But don't completely bulldoze them either. Use your judgment.

# Loops

Do not try to walk the world in game and take stills yourself. Instead, loop off game. Read the files the game will consume and verify that everything intended is there and correct. If not, diagnose, fix and repeat. Never run the game; then pass to the owner. You may also choose to architect other loops earlier on if you think appropriate (e.g. visually inspecting images of textures or trees/plants etc - but be smart with these, we have many many models and we don't want to spend forever going over all of them).

# Updating the owner
Post an issue when the above work is done and ready to deploy. Your goal for delivering this phase is complete at that point. Don't do the LOD until the owner says so.

# LOD
*After* you have delivered the above and done all the off-game checks you need to be confident that you have achieved the goals of this phase, *then* (and not before) build the LOD (skyrim native way) and get that deployed too.


## Working record (edited as the work goes)

Owner, 2026-11-08: the LOD is built in this phase too, before the walk (supersedes "LOD" above). The world map
in the game's map menu is drawn from the terrain LOD, so it is built with the LOD.

How the owner gets there: the new world is its own plugin, `ArgoniaNewWorld.esm`, written by Mutagen from the
generated data (too big for Spriggit YAML, as the old ArgoniaWorld.esm was), played from its own MO2 profile and
Moonlight card ("Argonia: New World": the BM&V stack plus the assets of King of the Murkmire, Tropical Skyrim, Depths of Skyrim
and the other world-asset mods, their plugins off; our plugin copies the base records it uses and masters none of
them); the BM&V card is unchanged.
The owner reaches the world with `coc ArgoniaNWStart`. Built artefacts live in `out/newworld/` and the
bucket, never in git.

| Step | What | Status |
|---|---|---|
| 0 | Map quick fixes: 53 road edges major→minor by measured ink, the gap north of Gul-Tej joined, the top strip drawn from the source (1f689739); the hatched province land in the north and a 4-cell margin beyond the border join the terrain in step 4 | done |
| 1 | Study: what to salvage from the old pipeline (research/nw-02-salvage.md) | done |
| 2 | Study: ground, water, roads, mist rules from the game and mod files (research/nw-02-ground-water-rules.md) | done |
| 3 | Study: flora, rocks, seabed, cliffs catalogue, seating and placement rules (research/nw-02-flora-rules.md; catalogue of 1,287 bases in out/newworld/research/) | done; KoTM, TS and Depths meshes being copied from the play machine |
| 4 | Terrain quality: nw-01's relief against Skyrim's, the improvement pass, room for large places; scope widened to the hatched northern province land plus a 4-cell margin (cell.margin), map rulers masked (research/terrain-measurements.md, build 20261108T213548Z) | done |
| 5 | (reopened 2026-11-08 on owner faults: closed bodies as stream, split marshes, river as swamp, flow directions; fixing with a chunked visual loop) Water: kinds and flow inferred (tools/newworld/water_kinds.py, rerun after every terrain build), the owner's water editor in the atlas (tap a body: kind, still/flowing, speed, name, a drawn direction; paint a kind over an area; edits in the atlas's shared store, pulled by tools/newworld/water_overrides_pull.py into newworld/sources/water_overrides.json and water_paint.json), each kind's WATR in the db (water_kind: editor id, form key, flow handling; provisional until research/nw-02-ground-water-rules.md lands, from docs/research/skyrim/water-types.md and a read of the plugins) | done; WATR table to recheck against step 2 |
| 6 | Region flora sets in the DB, seabed sets: tools/newworld/flora.py (pull, build, report) from newworld/sources/flora/; 534 bases in 40 families, 19 habitats, 8 companion guilds, 5,465 region_flora rows; summary and similarity in research/nw-02-region-flora.md (land max weighted Jaccard 0.29, sea 0.45) | done; rerun `flora pull` if the catalogue changes |
| 7 | The world plugin: worldspace, land, textures without hard edges, water, regions, BM&V weather | in progress: core landed (WRLD ArgoniaBlackMarsh, 20,160 LAND cells, `coc ArgoniaNWStart`; rerun `tools/newworld/world/world.sh` under job_guard; read-back PASS); textures, water types, regions to do |
| 8 | Trees, plants, rocks, cliffs, road dressing, water edges, placed and seated | in progress (on landcover a6520785) |
| 9 | Ground mist over marsh and water, by hour and weather | in progress (with step 7's agent) |
| 10 | Navmesh across the province | in progress (pipeline restored on the bare terrain; obstacles when step 8 lands) |
| 11 | LOD (terrain, objects, trees) and the world map | todo |
| 12 | Off-game read-back loop over the built files, then deploy and the owner's walk check | todo |

Owner faults to carry into the skills once each fix is verified on the owner's next look (CLAUDE.md, Updating Skills):
water classification (shape and connectivity decide kind, one kind per closed body; flow follows the channel graph to
its outlet); texture edges (measured and
looked at, never assumed from old code).
