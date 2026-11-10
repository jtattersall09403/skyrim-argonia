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
  interior. Light identities in this phase (see Stocking); nw-05 may recast anyone for the story. No talk beyond
  services.
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
- **Stocking (owner, 2026-11-10): building Helstrom in its entirety includes what is in it.** Its own skill,
  `place-stock`, run after `place-build`. Nothing is random and nothing is levelled (decision 0035).
  - *Set dressing stays as the source has it*: food, crockery, cheap clutter, furniture, a crate of apples.
  - *Anything more significant is authored and placed on purpose*, each item with its reason: weapons, armour,
    jewellery, gems, gold, soul gems, potions, skill and spell books, keys, anything enchanted or of real value,
    and every chest, strongbox, safe or corpse. What the source held of that kind is taken out, never kept as a
    flattened levelled list.
  - *A person's possessions* follow from who they are: role, rank, household, wealth, fixed level, backstory.
  - *A container's contents* follow from what it is, where it stands and whose it is. Value and protection agree:
    what is valuable is locked, hidden or guarded, and what lies open is ordinary.
  - *Loose things* follow from what the place is and its record.
  - *Value, level and strength are derived, on one fixed scale for the whole game*, from: the danger of the
    ground (the six danger bands and their foe levels); the place (kind, settlement tier, population,
    importance, culture, who holds it, its roads and water, the economy and hooks notes of its record); the
    owner; the security of the container; the effort to obtain it; where the thing would have come from (made
    here is common and cheap, carried in is rarer and dearer with distance along the roads). Danger alone does not
    set it: a city is safe ground and still holds fine and costly things, gated by their price and by how hard
    they are to steal. The exceptional (uniques, the best gear) is authored by story and counted in one ledger
    for the whole game. The scale is checked against what vanilla towns yield and fitted to the soulslike
    collection's combat.
  - *Everything the place record promises the player is delivered.* A promise is dropped or changed only by
    editing the record, case by case, with the reason; never to avoid the work.
  - *In the studio*, a container's or a person's contents are shown with their reasons and can be changed;
    optional, saved and finalised like any other edit, and a lesson for the recipe.
  - *Light identities come first (owner, 2026-11-10).* Every person of the place gets a name, a household, a
    trade, a wealth band and a line or two of backstory before stocking, grounded in the lore; no dialogue. nw-05
    may recast anyone for the story; a recast person is stocked again by the same rules.
  - *The split is mechanical.* What counts as significant is decided from record data (type, keywords, value,
    enchantment, container kind), never by eye, and the list of what it catches in a place is shown before
    anything is taken out.
  - *The scale is ours.* How valuable, strong or high a thing should be is derived and authored on purpose;
    vanilla's yields are a check on the numbers, not their source. A place's wealth is derived from its facts and
    its economy note and stored with its reason, so the owner can overrule it for a place. The danger bands were
    set for foes: they are read across all the places before loot leans on them.
  - *Variety comes from facts, never from dice.* Archetypes by role, wealth band and culture give the baseline;
    differences come from trade, family and backstory; notable people and containers are written by hand.
  - *What stocking never breaks.* A thing a quest names is the quest's and is never moved or removed. Ownership
    is set so that stealing is stealing. A lock is a fixed level. An authored container does not respawn. A
    trader restocks from a fixed authored list.
  - *In the database from the start (owner, 2026-11-10).* The world facts of people, economy and stock live in
    the new world's database in third normal form, fed from its source files: people, households, wealth bands,
    notes with their sources, relations, factions; the scale's tiers and numbers, each place's wealth with its
    reason and who set it, goods and what each place makes, trades and needs, the catalogue of item forms; stock
    by holder, the ledger of the exceptional, and which thing delivers each promise. Helstrom is populated now;
    the shapes are built to be filled across the game later (nw-05). A place's own folder holds only placement.
  - *The owner's own words rank above an agent's.* What the owner writes in the studio is stored as the owner's
    statement, and an agent's later pass keeps it and reports where it would have differed.
- **Services (owner, 2026-11-10).** Every service the place record promises is built and working as part of the
  place: traders with their stock and gold, the rented room, trainers, travel, crafting stations, the shrine's
  blessing, guards and the crime faction.
- **What a city holds (owner, 2026-11-10).** A city has no hostile occupants unless it has dungeon-like interiors
  (a dangerous cellar, a sewer), and no extra place, such as a whole village, sits inside a city's own extent.
  Helstrom's record loses the drowned Third Era villages and their boat-robbers. Helstrom is the capital: its
  levy wears the Argonian guard armour and its smith sells Argonian arms and armour.
- **Travel (owner, 2026-11-10).** Fast travel from the map will be removed in time (not yet), so no place promises
  it. Every place record's fast-travel promise is rewritten as a promise about the travel network: boat, coach or
  rootworm, authored sensibly for that place, and delivered by the place build as a service.
- **The studio draws exactly what will be in the game (owner, 2026-11-10).**
  - Everything placed is seen whole at any zoom, fully zoomed out included: buildings, plants, trees, rocks and
    everything else. No stand-in shapes; nothing the game does not draw (editor markers, effect shells).
  - Grass and ground cover show, close up and at the distance one views a town from.
  - Paths and roads look as the build paints them: the real land texture, soft edges, never flat and harsh.
  - People's routes are the ways they take in the game, found on the built place's own walking mesh, outside and
    indoors; never a ruled straight line.
  - Streets wind with the ground as a person would walk it; streets, guard patrols and door arrivals lie on the
    built walkable network; a deck, a pier or a ship that carries a door or a street can be walked to and from the
    bank.
  - The view tilts; a compass in each view shows where the camera points; the Selected panel gives a thing's
    in-world coordinates, and its text is never squeezed on the tablet.
  - The source pane can be put away and brought back.
  - The Atlas opens inside the studio, on request, showing the place in the wider world, from the built Atlas
    page with no copied code.
  - The owner leaves notes for the agent in the studio, about the place or about selected things; agents read
    them at session start and answer them.
  - The studio starts reliably on the tablet and says plainly what is wrong when it cannot.
- **Lighting (owner, 2026-11-10).** Every man-made light of the place is covered on purpose, not only inherited:
  torches, lanterns, braziers, candles, fires, their lights and flames kept with their fixtures, night and day
  switching, each room's own lighting, lights for what the draft adds where Skyrim's towns would light it, and
  the torches people carry.
- **Nothing levelled, people included.** A person is never built on a levelled base or one templated on a
  levelled character; a container never holds a levelled list.
- **The review (owner, 2026-11-10).** All the code of this phase is reviewed in full (drafter, builder, C# tools,
  extractor, assets, server, studio), its faults fixed, its speed improved by reasoning (on the tablet above all)
  and never by timing runs; nothing proven is proved again; no "worth a look" lists. The skills are kept current
  with everything found, as clean recipes.
- **Lanes and models (owner, 2026-11-10).** The lead plans and orchestrates. Delivery lanes run on Opus 5.5 at
  medium effort, code review on Fable 5.2 at medium effort.
- **After this phase.** The owner's walk feedback on the built world (water edges, level of detail, the map,
  roads, grass, atmosphere, water kinds and flow, relief) is handed over to its own session with the dependencies
  on this phase written down: a change of relief or water near a built place means a redraft of that place.

## The work (the agent's lanes; status moves in the commit that changes it)

The design and the contracts every lane builds to: [place-studio](../../design/place-studio.md). A fresh session
resumes from this table: a lane not `done` is relaunched with its row as the starting point.

| Lane | What | Paths | Status |
|---|---|---|---|
| X | Extract: any place out of any plugin into a bundle; our real ground, plants and water the same way; `bmv.helstrom` declared at its true extent; ground-check against the deployed file | `tools/ArgoniaPlaces/Extract`, `tools/places/extract*`, `xform.py`, `ground_check.py`, `newworld/places/sources.jsonl` | done: src.bmv.helstrom (108 cells, 6 spaces, 8,883 refs), ground.helstrom (949 cells, 37,616 world refs), skyrim.riverwood by a row only; xform proven (`xform prove`) |
| A | Assets: meshes and textures converted for the browser on demand and cached; the catalogue of every base form across every source we hold | `tools/places/assets` | done: nifdump (nifly) to GLB with levels and placeholders, DDS to WebP, NewWorld resolution, LRU cache (4 GB cap), warm, land textures, catalogue (39,280 bases); both Helstrom bundles warmed (728 of 735 meshes, 7 placeholders: models the profile lacks) |
| V | Studio server: the API, saves, runs, search (embedding index), hosting behind the owner's Cloudflare login, awake while a tab is open | `tools/places/studio` (not `web/`), `tools/places/search`, `infra/build-vm/studio*` | done: the studio is at https://studio.jacktat-play.stream (owner's Cloudflare login), systemd units `argonia-studio` and `argonia-studio-tunnel`; every API endpoint; saves committed by path; search index built by `python -m tools.places search build` once lane A's catalogue lands |
| W | Studio front end: every feature in the owner's list, for a tablet and stylus | `tools/places/studio/web` | round 2c: driven end to end on real Helstrom from a scratch clone (its own saves, autosave, runs and plugin output; the test run refuses any server whose autosave is outside its clone). 18 of 19 real-data browser tests pass (`STUDIO_URL=<clone server> pytest tools/places/studio/web/test/test_browser.py`); the governor timing test fails only under software GL on a loaded VM; 22 of 22 pass on the fixture. Fixed: the people panel crashed on the contract's patrol `{points, loop}`, so patrols, 2D stops, first-furniture stops, the contract's activity kinds and services lists are now read; a tap on a selection handle while placing logged moves that re-seated things where they stood; saved work is never applied silently: an opening sheet offers the builder's draft, or Continue for each save (the autosave shows as "Unsaved work from <time>, <n> edits", with Discard), and marks saves made on an older draft. Water: none where the land is above it, a quad where it is deep, and at the shore a sheet shaded by depth, so the waterline follows the land; people have short name labels near the camera or when selected. Named save, reload into the same edits and scene digest: pass. Finalise on real data stops at its first step (lane F: `edits.py` `_find`, about line 152, rejects a `ref.move` of a copied room's unlisted ref, `Black Marsh North.esp:054608` in `01cellDUPLICATE002`); the studio shows the red step, the report and "Your changes are saved". Open: lane F's copy-room move; screenshots under out/places/proof/studio need a pass on the GPU tablet |
| D | Draft: source bundle and our ground into place files (fit, seating, clearance, paths, people and routines, interiors); the skill `place-build`; Helstrom's first draft | `tools/places/draft`, `tools/places/seat.py`, `.claude/skills/place-build`, `newworld/places/helstrom` | | done (round 7): Helstrom `draft check` PASS (21 -> 0) and the real `build`/`check helstrom` 11 of 11 green (4,792 refs, 12 interiors, 195 navmeshes). Arrivals over water stand on a deck laid over it; a walkway's deck is read from its collision (`seat.walk_top`, the ref's `walk`), bridges stand 16 over the water; a cluster or piece stepped to its side of the waterline never steps into another; replaced load doors face out by construction (front from the mesh, turned about the leaf; `needs_look` removed); a door island no level join reaches whose room nobody uses is left out with its room (the ship hold 01Exit2, ledger reason); guards whose camp bed the network does not reach sleep in a home (4 guards, 4 residents left out). Tests `test_places_draft_walk.py` |
| B | Build: place files into the place layer plugin (refs, interiors, doors, people, packages, guards, crime, services, land patches, clearance, paths, navmesh) and the checks | `tools/ArgoniaPlaces/Build`, `tools/places/build.py`, `tools/places/check.py` | done (round 5): `check` reads a walkway's deck (`walk`) for arrivals and stops (one on the deck is on it, not in it); Helstrom 11 of 11 green on the main build output; `tools.newworld.verify` 52 PASS, 0 FAIL |
| F | Edits and finalise: applying a save, the finalise chain, the skill `place-lessons`, the report | `tools/places/edits.py`, `tools/places/finalise.py`, `.claude/skills/place-lessons` | done: edits, fixtures, finalise (kill-resume proven in each step), skill `place-lessons`; lessons proof on a synthetic place found the general lessons at $0.26 to $0.49 a run; round 3: a copied room's unlisted refs (kept from the source) are moved and removed by override rows `{id=src, src}` checked against the source row (draft_bundle.copy_space), dropped again when moved back; fixtures `tools/tests/places_edits/copy_refs/` (owed by the JS mirror); finalise on real Helstrom in a scratch clone: record 16 edits ok, seat ok, build ran and stopped on the clone lacking the world ESM, learn $0.67, report in plain English |
| S | Stocking: the scale and its derivation; the skill `place-stock`; contents built as fixed containers, inventories and placed things; the check that every significant thing traces to an authored row; contents shown and editable in the studio; Helstrom stocked, every promise of its record delivered | `tools/places/stock*`, `.claude/skills/place-stock`, `tools/places/build.py`, `tools/places/studio` | done 2026-11-10 in the sources, the builder, the check and the studio (S0 scale, contract, split, skill, database; S1 identities; S2 build, check, Helstrom stocked; S3 contents in the studio); owed: the stocked Helstrom in the committed build (with the final redraft); the drowned villages out of the record (lane T) and the levy in Argonian armour (lane L2), both ruled by the owner |
| R | Review: the full code review of every lane's code, with fixes and tests | all | done 2026-11-10: builder navmesh, people and checks; C# build and extract tools and the extraction side; assets, search, seating, finalise, the studio server, routes and notes |
| O | The owner's studio feedback: everything placed at any zoom, grass, paths as the build paints them, compass, coordinates, tilt, notes for the agent, the World map, routes on the built walking mesh, streets and patrols on the walkable network | `tools/places/studio`, `tools/places/draft`, `tools/places/navexport.py`, `tools/places/notes.py` | done 2026-11-10 except the landing: a pier and a ship that can be walked to and from the bank (lane D4, in progress) |
| T | Travel: the network (boat, coach, rootworm) as data in the database; every place record's fast-travel promise rewritten on it; the builder's travel service built from it; Helstrom's delivered | `newworld/sources`, `tools/newworld`, `tools/places/build.py` | in progress (2026-11-10) |
| L | Lighting: the audit of man-made light in the source, the draft and the built place, then the fixes and the rule in `place-build` | `tools/places/draft`, `tools/places/build.py`, `tools/ArgoniaPlaces`, `tools/places/studio` | in progress (2026-11-10): the audit is running |
| K | Skills: every skill this phase touched brought up to date as a clean recipe, with a recipe for a place's light identities | `.claude/skills` | todo: after lanes D4 and L land |
| I | Integration (the lead): Helstrom end to end; save, load and finalise proven with test edits; the studio at its URL; the owner check posted | all | in progress (2026-11-10): the studio is live for the owner (issue #58); a real save-and-finalise ran end to end on Helstrom through the studio's API (record, seat, build, check 11 of 11, report; run helstrom.end-to-end-proof, no edits); the lead's review of the studio, the edit and finalise chain and the drafter's streets is done (one renderer for both views, pen previews once a frame, grass, the source pane hidden or shown, a sign-in that ran out says so, streets routed on our ground and decks, people's routes walked round buildings and water); owed: the owner's try of the studio on the tablet, their answer on footpaths to every hut group, the deploy of Helstrom after the nw-02 walk (`infra/gpu-box/places_deploy.sh`) |
