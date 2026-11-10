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


Figure out and implement some smart and super fast way for us to test/prove the core functionality of this tooling, and try it out with me first before we dive into all of the above. I'm pretty confident we can build most of it, so just think about what the riskiest functionalities are and let's prove those as simply and rapidly as possible first before building the rest.


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
| W | Studio front end: every feature in the owner's list, for a tablet and stylus | `tools/places/studio/web` | round 2a done: real Helstrom loads without freezing the page (guide dismissible in under 1 s, place usable in 3 to 5 s, land streams in nearest first; terrain read in a worker; path splat 5.3 s to near nothing; one plain material per look, 10 to 13 shader programs instead of dozens; empty instanced meshes hidden; models switched on a few per frame); opens framed on the town; panel beside the views; missing textures fall back quietly; effects meshes (mist, waterfalls: the pale rings) left undrawn; walkways, seat modes clear and stilts, stations, align, arrival, the innkeeper's bed rule, cleared plants' why; the worth-a-look list from `needs_look`. 20 browser tests (one on a 961-cell, 36,000-ref fixture). Open: on software WebGL (no parallel shader compile) each new shader link still blocks 1 to 7 s; the tablet's GPU compiles in parallel. Next: the real-data end-to-end run |
| D | Draft: source bundle and our ground into place files (fit, seating, clearance, paths, people and routines, interiors); the skill `place-build`; Helstrom's first draft | `tools/places/draft`, `tools/places/seat.py`, `.claude/skills/place-build`, `newworld/places/helstrom` | | done (round 5): Nordic by look, not folder: `newworld/places/nordic_review.jsonl` (36 bases looked at, 17 nordic, 19 neutral) read by the drafter, `draft check` and (to wire) the build check; Nordic pieces replaced or dropped inside interior copies by the same path as outdoors; door arrivals by the build's own body test (true mesh and record bounds, standing on low roads and decks), checked in `draft check`; plants inside any placed solid, rocks included, cleared and checked; one guard to a bed; the jail's enchanter stands on the floor one walks in on; a young Hist added as the shrine; population 62 and radius 525 m in the record; PASS incl. `build --plan`. Owed: the 10 replaced doors in `needs_look`; overlap of added smithy-yard stations |
| B | Build: place files into the place layer plugin (refs, interiors, doors, people, packages, guards, crime, services, land patches, clearance, paths, navmesh) and the checks | `tools/ArgoniaPlaces/Build`, `tools/places/build.py`, `tools/places/check.py` | round 2: the room rule (the room is the island reached from its door on the cell's own Recast mesh; no hand numbers; 6 beds in each of Helstrom's nine house rooms, 2,093-unit minimum margin) and `build <id> --plan` (every problem listed; Helstrom 113 s -> 5 s cached) landed; patrols by linked ref; fixture 11/11 green. Helstrom builds (6,282 refs, 13 interiors, 28 LAND, 548 cleared, 193 NAVM, 63 NPCs; plan 7 s, build ~90 s, unresolved 0 bar PlayerRef); check 3/11 green, failures being triaged (seat check to call seat.py next). Next: check green, renting (RentRoomScript on the innkeeper base), shrine blessing (TempleBlessingScript), boat travel owed |
| F | Edits and finalise: applying a save, the finalise chain, the skill `place-lessons`, the report | `tools/places/edits.py`, `tools/places/finalise.py`, `.claude/skills/place-lessons` | done: edits, fixtures, finalise (kill-resume proven in each step), skill `place-lessons`; lessons proof on a synthetic place found the general lessons at $0.26 to $0.49 a run; the proof on Helstrom's real draft waits for lane D |
| I | Integration (the lead): Helstrom end to end; save, load and finalise proven with test edits; the studio at its URL; the owner check posted | all | todo |
