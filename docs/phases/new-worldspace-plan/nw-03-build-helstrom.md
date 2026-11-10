# Build Helstrom

In its entirety, including NPCs (and their routines) and services and guards (and their patrols) and crime and everything else, but no quests yet.

Do not rebuild LOD at this point.

Flow is: agent has a go at building based on the sourced place, then I edit it, in tooling that you create for me.

Start with the exact Helstrom build from the BM&V mod (including extent of vegetation/ground cover clearance, and all decorative scatter and everything). Aim to replicate it in the chosen spot on our worldspace as faithfully as possible, using all the same assets, keeping the layout as close as possible (adapting as necessary to our specific land/locale and geographical features), seating everything correctly, and tweaking land (as local patches *without* regenerating the whole terrain or anything else) if necessary but as little as possible. Every building must come with its paired interior if the building was designed to be 'enterable' (i.e. to have a door that 'teleports' you to a paired interior). NPCs must also be placed, and all navmesh delivered. Turn this into an agent Skill that we will then iterate.

Studio Tooling: I want to access it in a browser so I can use it from my tablet. It must be tablet friendly (I will be using my Huawei Matepad Pro with the stylus primarily). I don't mind whether this is streamed or deployed or browser native or whatever, you decide the best approach. What I want is:
* See and 'navigate' (rotate, zoom, pan etc) the 3D terrain and vegetation and the agent's first draft of the built place
* Simultaneously see and navigate the 'source place' (in this case, BM&V's Helstrom) on *its* original terrain
* Select objects in our place, move them in 3D space, rotate them, manipulate them.
* Select objects in the source place, see info about it, and be able to tap on our place to add one to it. Also be able to remove objects and buildings and NPCs etc from our place.
* Be able to search (semantic embeddings-based indexed vector text search) through all the assets used in the source place, and choose something to add to our place, then tap where to put it and then be able to manipulate it in 3D space. Also optionally expand out search to all assets from across all sources available to us (Tropical Skyrim + mods).
* Undo, redo, etc, all the usual types of controls
* See all NPC placements in our place and their routine paths and what times they will be at each spot. I want to be able to optionally edit their placements and waypoints and so on if I want to.
* All of this be super modern and user friendly and intuitive and not messy on the screen! Applying UI and UX design best practices for this kind of tooling
* Make minor terrain edits (e.g. levelling or raising small patches of land) that will get implemented as patches without requiring terrain rebuild
* be able to draw on paths and streets and so on with the stylus, and them to automatically be textured and styled and dressed nicely in a Skyrim native way (and vegetation cleared). And edit existing paths and streets (e.g. 'erase' them and have them replaced with normal land textures for that place).
* For all edits, the default should be that the change I made is recorded as an agent 'fault' (we'll come back to this later), but I should be able to optionally mark something as a 'taste' call instead (i.e. the agent didn't necessarily do anything wrong, I just have a preference for a different option).
* Do interim saves to my edits and be able to reload them and continue working another time
* When I'm finished, do a final save of my edits ("save and finalise" or "save and export" or something) and everything be automatically updated in our database and in all the places that it needs to be such that the build will use my edited version not the agent's original. Navmesh automatically updated.
* An agent looks at the edits I've made (after I 'finalise' or 'export' or whatever) and reasons about what they mean for our place builder agent Skill - what did it get wrong and why (that it can infer from the things I changed that were marked as 'faults' rather than 'taste calls'); what should change in the skill's recipe such that the next agent building a place gets it right first time - what is the generalisable pattern/lesson from this set of faults (rather than the hyper-specific lessons); apply those to the skills, leaving the skills reading simply as a clean recipe for how to do the thing correctly (not read as a patchwork or a history referencing feedback and decisions). 


---

## Agreed in the interview of 2026-11-09 (added by the agent; the owner's text above is unchanged)

The rulings are recorded in [owner-rulings](../../owner-rulings.md) under 2026-11-09. They change or add to the
text above as follows.

- **No core-first trial.** The whole of this phase is built in one overnight run and delivered complete.
- **Nothing reaches the play machine yet.** The first deploy of Helstrom follows the owner's nw-02 walk and
  first real finalise. Save-and-load and save-and-finalise are both proven end to end off the game.
- **Built for every place.** A place is a row that points at a source place in any plugin we hold. Helstrom on
  BM&V's Helstrom is the first row. The source pane is a chooser, ready for nw-04's allocated source and three
  similar places and for nw-06's drop-down.
- **The real world, in the draft and in the studio.** Heights, water level, trees, plants, ground cover and
  scatter are read from the built game file, checked identical to the deployed one. The studio shows every
  height point. The studio shows the build's fingerprint and warns when it differs from the deployed one.
- **Seating.** The draft seats every placed thing correctly in or on the terrain.
- **Vegetation.** The agent clears vegetation while drafting, following the source place's own clearance. The
  owner clears more, or un-clears, in the studio; un-clearing restores the plant the world had at that spot.
- **Terrain edits.** Each becomes a patch to that cell's land record, read back point for point, seams included.
- **Extent.** All of BM&V's Helstrom at its true size, landing included, with the landing on our real
  riverbank. The layout adapts to our terrain wherever possible; a land patch is the last resort and each one
  is listed in the studio. The place record's radius is corrected to what was built.
- **People.** Every service person the place record promises, working, with a bed and a routine. Guards and a
  crime faction. Residents only up to the bed count of the copied homes. Each of the nine houses has its own
  interior. Placeholder names until nw-05. No talk beyond services.
- **Interiors in the studio.** Tap a door to step inside, on either side. The same tools work there, and
  routines run unbroken from street to room.
- **Hosting.** Drawn in the tablet's browser, served from the build machine behind the owner's Cloudflare
  login. The machine stays awake while a studio tab is open and stops itself after the last one closes.
- **Interim save and load.** Named saves of work in progress, reloadable in a later session, separate from
  finalise.
- **Finalise.** One tap runs four steps unattended: record the edits in the database, build the place and its
  navmesh and run the checkers, learn (an agent turns fault edits into a cleaner skill recipe, as its own
  revertible commit; taste edits stay preferences for that place), and report in the studio in plain English.
- **Places are a layer.** Places are built as a separate layer over the world file. Layouts are stored relative
  to the place and re-seated automatically when the ground changes, so a world rebuild and a place build never
  touch each other.
- **Wide search.** The all-sources search shows Nordic pieces clearly marked (decision 0006).

## The work (the agent's lanes; status moves in the commit that changes it)

The design and the contracts every lane builds to: [place-studio](../../design/place-studio.md). A fresh session
resumes from this table: a lane not `done` is relaunched with its row as the starting point.

| Lane | What | Paths | Status |
|---|---|---|---|
| X | Extract: any place out of any plugin into a bundle; our real ground, plants and water the same way; `bmv.helstrom` declared at its true extent; ground-check against the deployed file | `tools/ArgoniaPlaces/Extract`, `tools/places/extract*`, `xform.py`, `ground_check.py`, `newworld/places/sources.jsonl` | done: src.bmv.helstrom (108 cells, 6 spaces, 8,883 refs), ground.helstrom (949 cells, 37,616 world refs), skyrim.riverwood by a row only; xform proven (`xform prove`) |
| A | Assets: meshes and textures converted for the browser on demand and cached; the catalogue of every base form across every source we hold | `tools/places/assets` | done: nifdump (nifly) to GLB with levels and placeholders, DDS to WebP, NewWorld resolution, LRU cache (4 GB cap), warm, land textures, catalogue (39,280 bases); both Helstrom bundles warmed (728 of 735 meshes, 7 placeholders: models the profile lacks) |
| V | Studio server: the API, saves, runs, search (embedding index), hosting behind the owner's Cloudflare login, awake while a tab is open | `tools/places/studio` (not `web/`), `tools/places/search`, `infra/build-vm/studio*` | done: the studio is at https://studio.jacktat-play.stream (owner's Cloudflare login), systemd units `argonia-studio` and `argonia-studio-tunnel`; every API endpoint; saves committed by path; search index built by `python -m tools.places search build` once lane A's catalogue lands |
| W | Studio front end: every feature in the owner's list, for a tablet and stylus | `tools/places/studio/web` | round 2c: driven end to end on real Helstrom from a scratch clone (its own saves, autosave, runs and plugin output; the test run refuses any server whose autosave is outside its clone). 18 of 19 real-data browser tests pass (`STUDIO_URL=<clone server> pytest tools/places/studio/web/test/test_browser.py`); the governor timing test fails only under software GL on a loaded VM; 22 of 22 pass on the fixture. Fixed: the people panel crashed on the contract's patrol `{points, loop}`, so patrols, 2D stops, first-furniture stops, the contract's activity kinds and services lists are now read; a tap on a selection handle while placing logged moves that re-seated things where they stood; saved work is never applied silently: an opening sheet offers the builder's draft, or Continue for each save (the autosave shows as "Unsaved work from <time>, <n> edits", with Discard), and marks saves made on an older draft. Water: none where the land is above it, a quad where it is deep, and at the shore a sheet shaded by depth, so the waterline follows the land; people have short name labels near the camera or when selected. Named save, reload into the same edits and scene digest: pass. Finalise on real data stops at its first step (lane F: `edits.py` `_find`, about line 152, rejects a `ref.move` of a copied room's unlisted ref, `Black Marsh North.esp:054608` in `01cellDUPLICATE002`); the studio shows the red step, the report and "Your changes are saved". Open: lane F's copy-room move; screenshots under out/places/proof/studio need a pass on the GPU tablet |
| D | Draft: source bundle and our ground into place files (fit, seating, clearance, paths, people and routines, interiors); the skill `place-build`; Helstrom's first draft | `tools/places/draft`, `tools/places/seat.py`, `.claude/skills/place-build`, `newworld/places/helstrom` | | done (round 6): overlaps by the build's own rule (origin within 0.8 of another solid's record box; exempt one cluster, seated-on) tested in `draft check` outside and for added pieces inside rooms: Helstrom 54 -> 0 (32 bridge pieces laid one per route step -> one per piece length, slid clear, decks lifted over drowned mounds; 7 smithy stations -> a yard laid as Riverwood's, measured from Skyrim.esm, each on clear ground by true box; 10 cross-cluster pairs -> the fit's last pass steps the smaller cluster, 22 steps, 3 small pieces dropped with reasons; the jail's enchanter slid off its door); stations by the crafting keyword the game keys on (vanilla base as fallback, said in `why`), a forge doing the anvil's work; replaced walkways keep the original's walking top (the inn ship's dock now meets its deck). Reachability in `draft check`: every copied room entered through a door pair named both ways with its outside arrival on ground or a walkway a street reaches, every person's stops each reached from the one before (ground and streets outside, the builder's room island inside); sunk filler blocks and low platforms are walked over; the guards' camp gets a street to its edge. Helstrom redrafted: seat 0 moved, `build --plan` 0 problems, draft check 1 problem: door 8GXDM (into 01Exit2) arrives on a caravel's deck 428 above the ground on no walkway (the source boarded it from Solitude dock steps; owed: a gangway or the deck's own walk surface). Owed: the 10 replaced doors in `needs_look` |
| B | Build: place files into the place layer plugin (refs, interiors, doors, people, packages, guards, crime, services, land patches, clearance, paths, navmesh) and the checks | `tools/ArgoniaPlaces/Build`, `tools/places/build.py`, `tools/places/check.py` | round 4: navmesh seams fixed at their cause: tools.navmesh.stitch snapped a neighbour's seam point to a vertex of another surface at the same plan spot (a deck over ground on a cell line) and linked only one of two edges with the same ends; `stitch.STACKED` splits and links by height too, on for the place window only (world off: 18 world cells rebuilt byte-equal to the deployed NAVM, round Helstrom and elsewhere); join proof: last ring equal to the world at reach 4, 0 one-way links, 0 left for join_seams. Check's seam rule is the world's seam audit (overlap at a like height; a corner touch is a boundary); check_nordic reads nordic_review.jsonl for every ref incl. interior copies and passes a model-less light (72 -> 0). verify's places rows: built over this ESM, and each built place's check read this build (51 PASS, helstrom 7/11). Deploy recipe infra/gpu-box/places_deploy.sh (not run): plugin, SEQ (the boatman's start-game quest), TIF_ARG_BoatTravel.pex; stack.ps1 lays the plugin last in NewWorld. check 7/11: navmesh 4 (houses .5/.6 door islands), people 221 (01Ship has no door pair; 7 guards' stops in building 5B9NGP7N's walled-in floor), overlap 21, doors 4: lane D. |
| F | Edits and finalise: applying a save, the finalise chain, the skill `place-lessons`, the report | `tools/places/edits.py`, `tools/places/finalise.py`, `.claude/skills/place-lessons` | done: edits, fixtures, finalise (kill-resume proven in each step), skill `place-lessons`; lessons proof on a synthetic place found the general lessons at $0.26 to $0.49 a run; round 3: a copied room's unlisted refs (kept from the source) are moved and removed by override rows `{id=src, src}` checked against the source row (draft_bundle.copy_space), dropped again when moved back; fixtures `tools/tests/places_edits/copy_refs/` (owed by the JS mirror); finalise on real Helstrom in a scratch clone: record 16 edits ok, seat ok, build ran and stopped on the clone lacking the world ESM, learn $0.67, report in plain English |
| I | Integration (the lead): Helstrom end to end; save, load and finalise proven with test edits; the studio at its URL; the owner check posted | all | todo |
