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
| 4 | Terrain quality: statistics matched to Skyrim and scope widened (22588c97: northern province land + 4-cell margin, 26,936 cells; ruler bands masked; buildable cores for 15 large places); reworked for look and promoted as live build 20261109T005246Z (a9cd9b9b, b4ce5351, d4c35fa6; clean build from code, 2.5 min with numba: roads 0 over the grade limit, 49 entrances 0 bad, water 0.982 / land 0.995 held, coast blocks4 0.998, LAND format ok, `terrain check` 0). Done: smooth coast (terrain_coast.py: 4 px blocks 0.993, 32 split bodies against 60), marsh at BM&V's 1.7 m floor and 7 m ramp, pads fitted to the land's lie, dry places get no shore dish, cut-only road shoulders, no checkerboard from the erosion mask. Left, from an independent reader's A/B read (ours picked in 12 of 12): wide coast smoothing that keeps 3-9 px streams, flat plains needing larger landforms, uniform dimple texture, mesa risers following a single noise contour, contour-ribbon terraces; addressed in look pass 2 (shores as smoothed polylines, domain-warped relief, single escarpment faces, rain erosion). Relief against Skyrim's mountains is the owner's call in the walk | done |
| 5 | Water: kinds by shape and whole connected water (a channel-shaped body, centreline 150 m or more and 8 widths long or branching, runs whether or not the map joins it; only a compact closed piece is one still body; wide stretches stay in their channel unless 120 m+ across and 3x the channel, then pond or lake) and flow down the channel graph to its outlet, stopping at still water (tools/newworld/water_kinds.py, with a 4 x 4 visual check `--chunks`; rerun after every terrain build); the owner's water editor in the atlas (tiled terrain to the heightmap's resolution, water drawn as outlines from the full-resolution bodies, flow arrows along every channel; edits keyed by a point inside the body, pulled by tools/newworld/water_overrides_pull.py into newworld/sources/water_overrides.json and water_paint.json); each kind's WATR in water_kind, from research/nw-02-ground-water-rules.md 3.4, and per-cell flow in out/newworld/water_flow_cells.json for the world plugin | done (b93cfecf; rerun on 20261109T005246Z: 2,273 bodies, 1,385 flowing, every owner edit found its body; atlas v14) |
| 6 | Region flora sets in the DB, seabed sets: tools/newworld/flora.py (pull, build, report) from newworld/sources/flora/; 534 bases in 40 families, 19 habitats, 8 companion guilds, 5,465 region_flora rows; summary and similarity in research/nw-02-region-flora.md (land max weighted Jaccard 0.29, sea 0.45) | done; rerun `flora pull` if the catalogue changes |
| 7 | The world plugin: worldspace, land, textures without hard edges, water, regions, BM&V weather | done on terrain build 20261109T005246Z: 26,936 cells with LAND, seams 0 mismatches, texcheck PASS (step p99 0.16, max 0.61, seam 0.0105, swathe 0.379, 5.09 textures per land quadrant); ESM 290.6 MB at s3://argonia-private-050977237313/nw/plugin/20261109T005246Z/ (rerun `tools/newworld/world/world.sh` under job_guard after any terrain build; one run at a time). Landcover (tools/newworld/landcover.py: habitat per sample, canopy field with glades, stands and clearings, water kind, shore, road and sea distances). Ground (world/texture.py): 26 materials, each our own LTEX + TXST copied from BM&V, vanilla or KoTM with a grass list (18 grassy; GRAS share of land 0.87), base + up to 6 layers, a seam fade so a shared vertex reads the same from every quadrant; world/texcheck.py measures the edges (step p99 0.16, max 0.54, seam 0.010), the swathe (max 0.375 of any 1 km of land) and 5.1 textures per land quadrant, and renders crops as the game blends them. Water (world/cells.py): XCWT per cell by kind; rivers and streams flow only where water_kinds.py says, in 4 directions, our SW/NE/NW copies; no flowmaps. 24 REGN linked per cell with weather mixes; ANW_BlackMarshClimate. Masters Skyrim, Update, Black Marsh only, ForeignCopy.cs copies asset-only records. Placed-refs hook: refs/<producer>/cy*.jsonl | |
| 8 | Trees, plants, rocks, cliffs, road dressing, water edges, placed and seated: `python -m tools.newworld.place run|check|render` (tools/newworld/place/, seeded per cell, keyed on the landcover build, about 100 s) writes out/newworld/plugin/refs/flora/ in the shared refs hook (world/cells.py; the writer copies non-master bases with ForeignCopy); density calibrated per habitat (three pilot passes on every 4th row scale each habitat's rows so its refs per hectare, over the strata its regions furnish, hit habitat.density_per_ha; manifest density_by_habitat); a base is dropped when its model or a diffuse (texture set slot 0, the only slot that shows purple) does not resolve in the NewWorld profile (manifest region_flora_dropped, per region by reason); a missing other slot is a warning (bases.json missing_non_diffuse: 62); a wrong path whose file is in the same mod (one match by file name, a doubled .dds.dds read as .dds, ambiguity refused) is repaired with alternate textures on our copy (place/texsets.py -> bases.json alt_textures -> the writer adds a TXST of ours and the model's MODS entry; the mesh untouched): 5 bases repaired, 39 of the 43 once dropped now placed, 4 left (diffuse not in their mod); ForeignCopy names a copy ANW_<plugin initials>_<edid>, drops KotM's alternate textures into the missing 000028:Skyrim.esm, and copies DLC records, so the masters are Skyrim, Update, Black Marsh; on build 20261108T213548Z after the repair: 525,335 refs, 471 bases, 6,463 trees in standing water within rule, every region at least 24 bases, Jaccard max 0.412; before it: 521,850 refs, 433 bases, every habitat within 20 % of its target, natural refs a cell p50 12 / p99 80 / max 131 (cap 162 unchanged, never reached); ESM written with the refs (NW_REF_PRODUCERS=flora,mist) and the verifier's refs rows all pass (0 on roads, 0 trees in flowing water, 5,750 in standing water within rule, seating max 0.438 m, 0 open undersides, open sides 100 %, 0 cliffs over their hill, 0 pairs under 1 m, 418/418 models and every texture resolve, Jaccard max 0.438, every region at least 22 bases) | done on 20261109T005246Z: 530,656 refs, 470 bases, all 19 habitats within 20 % of target (worst 18 %), 0 on roads, 0 trees in flowing water, 6,981 in standing water all within rule (placement now tests habitat and depth on the rounded position and the deeper triangulation, as the check does), seating max 0.384 m, 0 open undersides, 0 cells over budget, Jaccard max 0.364 |
| 9 | Ground mist over marsh and water, by hour and weather | done (records only): about 9,000 FXMistLow refs (9,026 on 20261109T005246Z) Morthal's way, kept out of the sea; Clear/Cloudy copies with a dense night fog and a 05:00-12:00 sunrise window (mist at dawn, gone by noon, back at night); ANW_AfterRainFog listed beside the rain; to judge in game |
| 10 | Navmesh across the province: pipeline restored (tools/navmesh, NewWorldNavmesh.cs; ff1205f1), proven on 256 cells round Lilmoth (all land cells covered, 0 seam faults, 99% connected, 5/5 paths, codec byte-exact on Skyrim); full province on 20261109T005246Z (508 s): 12,246 NAVM, NAVI 12,246, every non-margin land cell covered (11,570), 20/20 settlement paths, main landmass 0.9993 connected (4 true islands apart), 0 height faults; 0 seam faults over 88,938 seam links. Seams are audited from both sides (tools/navmesh/province.py seam_audit): a fault is an open seam edge that overlaps the neighbour's and cannot link; 192 open seam edges with nothing across them are boundaries (the neighbour's voxels there are eroded beside a steep bank, so walkable ground ends at the seam), not faults | done |
| 11 | LOD and the world map, final (2026-11-09, terrain build 20261109T005246Z, DynDOLOD Medium): terrain LOD 5,244 / 1,440 / 429 / 126 files expected and found, tree LOD 1,752 files and object LOD 1,661 files for ArgoniaBlackMarsh, no other world's LOD laid; 5,208 s (terrain 1,614, TexGen 283, DynDOLOD 2,944); archive 852 MB at s3://argonia-private-050977237313/nw/lod/ec1dfca30b427a3c.tar, laid in the NewWorld profile only; the map (116 markers, Stormhold known) is a world.sh stage | done |
| 12 | Off-game read-back (`~/.argonia/venv/bin/python -m tools.newworld.verify`): 50 PASS, 0 FAIL of 50 (out/newworld/verify/report.md), the ESM (2c3e9f58…) deployed to the NewWorld profile on argonia-play, its `stack.ps1 verify -World NewWorld` 73,413 files 0 bad; the owner's walk check posted from nw-02-walk.md | done |

The new-world card (2e3215a5, d64744de): 10 asset-only rows (KotM, Tropical Skyrim, Depths, HTBM + Cipactli, Xanmeer,
CC Ayleid, Sleeping Hist Tree, Mud Mother Grove, SIRENROOT) marked `profile: newworld`, their BSAs unpacked to loose
files in stage and their plugins off; stack.py stages two profiles (Argonia unchanged; NewWorld = it + the 10 + our
world plugin); Sunshine lists "Argonia: New World"; masters check 0 missing. On the build VM the assets are hard-linked
under ~/games/skyrimse/newworld-assets/<id>; 110 of 3,368 flora model paths do not resolve (62 are Tropical Skyrim's
LE tree meshes) and are never placed.

Owed on the reworked terrain (one pass, in this order): water_kinds → landcover → textures → place (with each habitat's
refs per hectare calibrated to the measured source density within ±20%, and every texture named inside a
placed model resolving in the NewWorld profile (25 KotM/TR texture paths do not): BM&V swamp ground 198/ha, KotM rainforest and
mud 130–150/ha, marsh grass 39/ha, river bottom 27/ha, table in the report) → world.sh (ESM with refs) → navmesh full
run → LOD full run → the off-game read-back (step 12).

Owner faults to carry into the skills once each fix is verified on the owner's next look (CLAUDE.md, Updating Skills):
water classification (shape and connectivity decide kind, one kind per closed body; flow follows the channel graph to
its outlet); texture edges (measured and
looked at, never assumed from old code).
