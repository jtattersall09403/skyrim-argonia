---
name: place-build
description: Draft one place of the new world from its source place (any plugin we hold) onto our real ground - fit, seating, vegetation clearance, streets, interiors, people, lights - as the place files the studio and the build read; then build and check it. Holds the order of work on a place across the place skills. Use for each place's first draft, and to change a drafted place by the one stage that owns the change.
---

# Draft a place from its source

## The order of work on a place

| Step | What | Skill |
|---|---|---|
| 1 | The place's record in the database: what it is, what it promises the player, its danger | `place-research` |
| 2 | The first draft of the place files, whole, once | this skill, sections 1 to 6 |
| 3 | Who each placed person is | `place-people` |
| 4 | What the place holds, and every promise delivered | `place-stock` |
| 5 | Build and check | this skill, section 8 |
| 6 | The owner edits the place in the studio and leaves notes | this skill, section 9 |
| 7 | The owner finalises a save: record, build, lessons, report | `place-lessons` (run by the finalise chain) |

After the first draft every change is narrow: the step that needs changing is applied to the committed files and
every other row stays as it is (section 7 here, and the narrow-change section of each skill). Section 7 names the one case in which a place is drafted whole again.

## What you decide

The tools do the measuring; you make the calls they cannot. Everything you decide goes in the `draft` block of
`newworld/places/<place_id>/place.json`; the tools write every other place file. The contract (file shapes,
seat rules, ids) is `docs/design/place-studio.md`. Never write mod record or asset content into a place file.

## Inputs

- `place.json`: `place_id`, `source_id`, `similar`. The source is the place's allocated source in the database:
  table `place_source` rank 0 (ranks 1-3 are the next most similar, `similar`), described in `source_place`;
  `python3 -m tools.places source <place_id>` writes its bundle. A source place is a row of
  `newworld/places/sources.jsonl` (hand-written) or `sources_mined.jsonl` (written by `tools.places sources-match`).
  Our record: `db.open("newworld")`, tables `place` (position, siting, population, summary) and `place_give` (what
  the place promises the player).
- The bundles under `out/places/bundles/`: `src.<source_id>` (`python3 -m tools.places extract <source_id>`) and
  `ground.<place_id>` (`python3 -m tools.places extract --ground <place_id>`). The ground bundle must stand on
  the deployed world file: `python3 -m tools.places ground-check <place_id>` passes. The world file is settled and
  on the play machine first (the skill `world-build`, section 7).
- What a place stands on in the world. The ground bundle and the build each keep a stamp of the world records
  they read: the LAND, the navmesh and the placed references of their cells (the bundle's whole reach; the
  build's own cells and the two-cell ring its navmesh joins), the bases those references name, the worldspace
  record, the land textures, the world file's masters and description, and the form ids of the map markers the
  place's travel lines land on. The place is current while those are the world file's, whatever else of the file
  is rewritten: `extract --ground` and `build` then say up to date and write nothing, and `place.json`'s ground
  key stays. `python3 -m tools.places worldparts <place_id>` names what moved when something did.
- Skyrim's town rules: `docs/research/skyrim/town-life.md`.

## 1. Read the source's character

1. `python3 -m tools.places draft <place_id>` once with an empty `draft` block, then
   `python3 -m tools.places draft render <place_id>` and look at `out/places/renders/<place_id>/source.png`.
2. Name in a few lines: where its water is and what stands in it (the landing, stilt houses, shallows); how its
   streets run between the doors; which buildings are entered and where they lead (`place.json` `fit.clusters_info`, and `ledger.jsonl`, one row per source piece saying what became of it); how close its plants come to buildings, streets and doors (`place.json` `clearance`).

## 2. Choose where it sits on our land

1. Look at `draft.png`: our rivers, banks and dry ground round the record's position.
2. The landing goes on our real bank of real water; the town's dry ground on our dry ground; the whole source at
   its true size. If the record's position does not serve, set `draft.anchor` `[x, y]` (game units) to the
   point the source's middle should take, on the ground that does. Set `draft.rot_deg` only when the search
   turns the town against the way it faces its water.

## 3. Draft and read the fit

What the tools hold to, so you can judge their output:

- Our water and land are never changed to fit the source. Ground a place needs (a pad, a rise, a landing) is asked
  for in its record and shaped by the world's terrain, which holds a built place's ground from then on (the skill
  `world-build`, section 2). A cluster is the pieces of one building or one group, moved as one. A cluster that stood on dry land goes on our dry land,
  one in or over water (jetties, stilt houses, shallows, boats) on our water. A cluster whose spot fails slides,
  turns or steps to the next ground of its kind, and a door moves with its whole building. A single piece that
  still has no ground of its kind is dropped and listed.
- No piece of one cluster stands in another's (the build's overlap rule: an origin within 0.8 of another solid's
  record box). The fit's last pass steps the smaller cluster the least distance clear, and a clash no step clears
  drops the smaller piece with the reason (`fit.separated`). A cluster or a piece stepped afterwards to its side of the waterline is never stepped into another cluster.
- Pieces that stand in each other in the source (a mud dome over its entrance, windows set in it), compared in the
  source's own frame with full rotation, are one body and share a cluster. A tilted piece turns about the world's
  axis with its cluster (one transform).
- A sunk filler block or a low platform (its top within a step of the ground) is walked over, never an obstacle.
- The world's plants give way to the town. A plant rooted closer to a building, a street or a door than the
  source's own plants came is cleared, and so is anything rooted inside a placed thing. A thing of the world whose
  body lies across a street's walking width or a door front is cleared wherever it is rooted (a great root, a rock
  piece many metres wide): its body is its solid collision at walking height, the same columns the navmesh is cut
  round it by.
- Land patches only ease the ground under a building, at most 1.5 m at any point and never across the waterline.
  A building on a slope first takes the rise the source's own builders commonly built on (`fit.relief_norm`).

1. `python3 -m tools.places draft <place_id>` then `draft render <place_id>`; compare `side-by-side.png`: the same
   cluster ids sit in the same order, facing their street and their water.
2. In `place.json` `fit.clusters`, a cluster with a high `cost_after` sits badly. In `ledger.jsonl`, pieces dropped
   for want of water or land, and doors above all, mean the anchor or the turn is wrong: move them and draft again. The losses are not accepted.

## 4. Read the streets, decks and doors

Streets (orange in the render) and walkways (brown) join every door, the landing and every camp into one network.
Look at every street close up, not only in the whole-town render. A straight run longer than a few houses, a line
beside a deck and not on it, a bridge that ends on an empty bank, or many bridge pieces where the source had none
each mean the anchor, the turn or a cluster's spot is wrong: put that right and draft again; never accept the line.
The tools lay the network by these rules.

- **Where a street runs.** Where the source drew a street (a painted road, walkway pieces, its navmesh's preferred
  paths) ours keeps to that line. Where it drew none, the link between two doors is the easiest going on our
  ground, never a ruled line: it winds with the ground underfoot, goes round the trees and rocks in its way, keeps
  to the middle of a gap between buildings, and shares a stretch with a path already laid. No street climbs
  steeper than the source's streets did. A camp (beds in the open) is a stop like a door: a street reaches its
  edge.
- **Decks count as ground.** Every link is routed on our ground with our decks counting as ground, a link to a
  door on the water included, so a boardwalk's line runs along its decks (over the water a step of the route
  stands where the deck is, its middle on the deck or on the deck's long middle line, never beside it) and a ship's
  hatch is reached over its own ship. The landing's shore end is where the landing's own pieces meet our dry
  ground, never a bank it does not touch.
- **Bridges.** Open water is crossed only where nothing else joins the two ends, and then where it is narrowest,
  on bridges of the source's own walkway pieces: one piece per piece length along the route, each slid along it
  clear of any solid there, its deck a hand's breadth over the water. A walkway's deck is the top of its collision
  at its centre, read per piece, never its record's top, which is the rail.
- **Steps.** Steps hang on their deck the way Skyrim's dock steps do (measured on Skyrim.esm's DockStepsDown01 and
  02): square to the deck, the top end against its edge, the top tread at the deck's own height, the piece seated `on` the deck piece (resting on it and carried with it). A flight of the source's that abuts a deck a little off its height (within 64 units; a step
  the navmesh does not climb) is seated so in the draft, and deck and flight are one walked surface: a ship the
  source moored beside its pier with steps between them is joined by those steps.
- **Flights for decks above our bank.** After the draft the tools build the place and read its navmesh. A deck
  that carries a door or a street and that the town reaches only by swimming (a pier or quay the source met at its
  bank's height, standing above ours) gets one flight of the source's own steps, hung as above off a free edge of
  one of its deck pieces and running down until its treads meet our ground where the town's network walks. The
  bank may bury the rest of the run, as steps set into a slope; no tread stands under the ground before that, and
  the flight's body is clear of every solid by the build's overlap rule. Of the flights that fit, the one the bank
  buries least is laid, then the one nearest the deck's streets and doors. A deck nothing of the town uses (a
  rowing boat, a bridge deck high overhead) gets none. Look at each flight in the render.
- **Flights for decks below our bank.** Where a street leaves a deck for a bank that stands over it by more than
  a step and too steep for the mesh to walk (a low bridge ending against a bank face), one flight of the source's
  own steps is hung on the deck piece there, square to it: its top tread at the height of the bank's top where
  the town's network walks, running down over the deck until its treads meet the deck, which hides the rest of
  the run. No tread stands under the ground and the flight's body is clear of every solid but its deck. Of the
  flights that fit, the one the deck hides least, then the one whose top is nearest where the street reaches the
  bank's top. A crossing whose banks have no deck (a ford between steep banks) is not joined by this: name it in
  the hand-over and change the world's ground first (the skill `world-build`).
- **Gangways and joins.** A door whose walkable ground is still an island is joined to the town by level walkway
  pieces laid from the island to the nearest point of the network at its height (never across a height the
  navmesh does not climb: that is a flight's work). A piece laid for a door that stands on a thing (a ship's
  hatch) rests on that thing as its gangway and names it as its `carrier`; a piece that continues a walkway stands
  `on` it. The build's overlap check lets a piece rest on what its seat names, by the same rule the drafter lays
  it with. A door whose island no join reaches and whose room has no resident or worker is left out with its room
  and the links that led to it, with the reason in the ledger.
- **Door arrivals.** Every door's arrival outside stands on the built walkable network at its own level (the deck or the ground where the door lands a person): an arrival more than 16 units over or under the mesh is put at the mesh's
  height where it is; one off the network is moved to the nearest point of it, on the same side of its door and
  outside every placed thing's body, at the mesh's height there. A person's outdoor work stop named by a thing the
  network does not reach (a Hist's trunk) becomes the nearest point of the network beside it.
- **Streets and patrols lie on the built walkable network.** Once the doors are joined, every street, path and
  walkway is walked along its whole line (a point every 64 units) on the town's main network of the built navmesh
  (ours and the world's own round the place). A point stands on a dry triangle at a level where a person can stand:
  a deck's or a flight's own surface (within 48 units of it), the ground or a ford, or, over water too deep to
  wade with no deck, a dry triangle right over it; never the seabed. Each point is taken at the level a walker reaches from the point before, never by a drop or a climb steeper than a walked slope (a step off a deck's edge
  onto the ground under it), so a line under a pier stays on the ground and a line down a flight stays on the
  flight. A stretch off the network (where a big static's true collision cuts the mesh, where a deck stands above
  its bank) is laid again along the way the mesh itself walks from a little before it to a little after, never
  through water deeper than a ford: through the middles of the triangle edges it crosses, pulled straight and
  eased only where the line still walks the same way. Stretches close together are laid again as one. The
  street's `laid` says so, and the world's plants the new line reaches are cleared by the draft's own measure.
  Guards' patrols are then taken from those streets, each point on the network (a patrol keeps at least two). One
  pass settles every line: `draft check` mends each street again on the built mesh and fails if any stretch moves.
  `draft check` and the build's `streets` check list any street or patrol point still off the network.

## 5. Settle what the cost cannot

- **The source's own pieces are accepted as they come.** A piece the source place itself uses, from its own mods,
  Tropical Skyrim or the base game, is never judged by its look, replaced for it or dropped for it: a Solitude
  door, a High Hrothgar fire pit or a Dawnguard runner the source set there stands in ours, lit or unlit as the
  source has it. Decision 0006 governs only what we add from elsewhere (a station, a replacement, a laid piece):
  the tools take those from non-Nordic bases, by the catalogue's folder rule, or the looked-at verdict in
  `newworld/places/nordic_review.jsonl` where a base has one (contract: Bundles). `draft check` and the build's
  `nordic` check fail a Nordic base added from outside the source place.
- **A piece that cannot stand in our place as it is** (a door whose model does not fit the wall we give it, a piece
  whose function ours lacks) is swapped by `draft.replace` `{old: new}` or `{old: {base, turn_deg}}`, for a piece of
  like size and use from a non-Nordic source we deploy (`python3 -m tools.places search query "<what it is>"`, or
  the catalogue `out/places/catalogue/bases.jsonl`). A replaced walkway keeps the original's walking height (its top
  where the original's was), so a door or a deck that met it still does. The tools line a replaced door or
  directional piece up with the original's plane from both meshes (the turn and the shift, `align` on the ref) and
  `draft check` proves it. A replaced door faces out by construction: its front is read from its mesh (a door
  modelled in place has its origin inside, off the leaf, so its front is the face away from the origin) and it is
  turned half round about its leaf when that front would face away from where one arrives outside it (the source's
  own arrival marker). A door's `to_pos` is where using it lands you: the exterior door's partner holds the arrival
  outside, and `draft check` proves each replaced door faces it.
- **A light belongs to its fixture.** A light has no body; the lantern, sconce, window or fire it was placed for
  is the nearest one within 128 units of it in the source. The light shares that fixture's cluster, stands at its
  source offset from it (turned with the cluster), is seated `on` it, and is left out when the fixture is.
  `draft check` fails a light more than 16 units off that place.
- **What we add is lit as Skyrim lights it** (measured on Skyrim.esm's exteriors). An added forge carries
  LightForgeFire01 in the forge's own frame, where 15 of 24 vanilla forges carry it (median offset x -16, y 167,
  z 84). An added smelter carries none (0 of 21) and an added alchemy lab none (3 of 16). The streets,
  bridges and steps we lay carry no light unless the source lit its own walkways: count the source's walkway pieces
  with a light within 256 units and light ours at that rate, rounded: where 1 source piece in 63 is lit, ten laid
  pieces carry no light. The torch a guard carries is stock (the skill `place-stock`).
- **Hanging things hang from a limb.** A place's Hist and the trees within 15 m of it carry King of the Murkmire's
  rope lanterns (`DLC2DarkElfLantern05Rope`, `04Rope`; self-lit, so no light goes with them): each carrier takes a
  count drawn from the mod's own counts per carrier (1 to 5, `newworld/sources/dressing/kinds.json`
  `hanging-hist-lanterns.per_carrier`), each lantern on its own hang point of the tree's mesh (a limb underside 2.5 to
  7 m up, measured by `tools/newworld/dressing/hang_points.py`), hung by its rope's top, never tilted, seated `on` the
  tree. None hangs with under 60 units of air over the ground or inside another solid row. The whole draft adds them;
  on a drafted place `draft hang <place>` makes them again from the standing trees (its dry run:
  `python3 -m tools.places.draft.hang <place>`), and `draft check` fails a lantern not on a limb of its tree, so a
  tree moved, turned or swapped in the studio shows its lanterns in the air. A source's own hanging lanterns come
  with their cluster like any piece.
- **A copied room keeps the source's own lights**, shadow casters among them, each on the base the source placed.
  There is no cap on shadow-casting lights in a room: the player's renderer settings decide how many it draws.
- **Leftovers**: `draft.drop` `{source ref id: reason}` for anything the source placed that our place must not have.
- **What the record promises and the source lacks is added in the source's own style.** The tools add each
  missing crafting station by the person who works it, the way Skyrim's towns do (the smith's yard outside the
  smithy; the alchemy lab with the apothecary; the enchanter with the spell trader; the cooking pot at the inn).
  A station's base is one whose record carries the station's crafting keyword (what the game keys on), from the
  plugins whose style the place uses: the marsh's own mods unless the place is of another people, in which case
  name its mods, first choice first, in `draft.style_order`. Where no non-Nordic base carries the keyword, the
  vanilla working base, said in its `why`. One piece doing two stations' work counts for both (Skyrim's forge is
  its anvil). The smith's yard is laid as Riverwood's (the forge, the grindstone beside it, the workbench and
  tanning rack across the yard, each facing it): the forge on the nearest clear ground to its worker with room for
  the yard, the rest in that layout or the nearest clear ground round the forge within the worker's reach. Clear
  means: dry under its outline, its body clear of every placed solid by true record box (on a road or a deck only
  by its edge), 256 units from any door, off the streets. A station added indoors stands on the walked-in floor
  clear of the room's things. Check each in the render (`stations.added`); move one with `draft.add` and
  `draft.roles` when it stands wrong. Traders work where the source's own trader of that trade worked.
- **A travel stop is a person's service like a trade.** A `boat-stop`, `coach-stop` or `rootworm-stop` promise is
  kept by the operator the place's people name (a boatman, a carter, a root-tender), given the stop's give by its
  seq, working at the landing: a boat's at the water's edge or on a deck over it, a coach's at the gate on the major
  road, a rootworm's at the place's Hist, whose roots the worms run in. Where they go and for what fare is the
  travel network's (`docs/design/travel-network.md`), never the person's.
- **A promised shrine blessing needs a thing to carry it**: the source's own Hist or shrine, else the tools add a
  young Hist in the town's middle, clear of buildings and streets (`stations` `shrine`); look at it in the render.
- **The sentence follows the place's law** (`place_law` in the database, the one source of the fact;
  `docs/design/law.md`). A place where no one keeps law has no sentence and its guards speak no arrest lines.
  A foreign law jails: the jail is the copied room holding the jail kit (bars, jail walls, jail doors), never a
  room known by its name alone; the tools put the prisoner in a bed by a door that locks, else a bed behind the
  bars, else behind the bars where they enclose most (adding a bedroll there), stand the jail marker beside that
  bed, the release point at the arrival outside the jail's town door, and the two evidence chests by the way in,
  owned by the crime faction and empty. Look at the cell in the render. A native law has no cell: its sentence is
  the Owing, the engine's jail served outside. The tools stand the work spot where the place's labour is done (the
  landing where the boatman works, else the work stop most of its people share) on the deck or walkway built there,
  with a bedroll beside it (lying down on it serves the sentence); the return spot on the street nearest it, at
  least 384 units off; and the stolen goods chest out of reach under the ground. The return spot's prison marker is
  the faction's JAIL and WAIT, and its teleport leads to the work spot's and back. The guards are in the arrest
  dialogue, so pay, the Owing and resist are all offered; the Owing's line is ours, first in vanilla's "go to jail"
  topic and said only by the place's guards, running vanilla's own fragment that keeps the player's belongings
  (`draft jail`). Resisting a native place's guards is fought to the death: the builder puts a resist line of ours
  first in vanilla's resist topic for the place's guards, whose fragment (`TIF_ARG_NoSurrender`) makes the place's
  guard faction the player's enemy, so no surrender is taken; this needs the place's guards to share one guard
  faction of the place (`<place>.guard` in `people.jsonl`). A foreign law keeps vanilla's resist and its yield.
  Look at both spots in the render.
- **A source's primitives keep their work.** A collision marker's box (an invisible wall or floor the source's
  builders placed) is kept when it belongs to a piece we keep: its box touches or holds a kept building, static,
  furniture, door, activator or container (a wall on a balcony, a plug in a doorway, a cap on a roof). It
  then travels with that piece at its source offset, seated on it, as a light with its fixture (in the studio too:
  moving, turning, resizing, copying or removing the piece takes its walls along), and the navmesh is
  built round it as the solid it is. A box that met only the source's ground (its trees and rocks included) is
  dropped with that reason: our ground is not the source's. Where our own ground needs a wall (a hole the fit left,
  a ledge people would fall from), that is drafted with its own reason, never inherited. A room or portal marker,
  an acoustic space and any other volume are copied with their primitive. A trigger with a script whose
  activation reaches nothing the place keeps (the source's quest or scene) is dropped with its reason in the
  ledger; a trap's trigger stays with its trap (`draft primitives`).
- **People follow Skyrim's days** (`docs/research/skyrim/town-life.md`): an innkeeper keeps the inn day and
  night and owns no bed; guards keep two 12-hour shifts on the streets. Never bend a day to satisfy a check: a check that disagrees with how Skyrim does it is a fault of the tool, to be reported and mended there.
- **Beds decide the people.** A house copied from a cell several houses share keeps only its own room, by the
  builder's room rule (the drafter calls it, so the beds counted are the beds built). Every promised service
  person works; residents fill the homes' remaining beds. A promise a townsman keeps beside his own life (a rootworm stop's handler, a follower) makes no person of its own: it is given to a resident (the skill `place-people` chooses which, by the trade it writes; until it has chosen, the first resident who has no service to give). A stop's handler works at it through the service hours.
- **Who sleeps where, the vanilla way.** An inn that rents a room keeps one of its beds unowned: that is the
  rented bed (`stations.rent_bed`). Guards sleep in a barracks or their camp's own beds (tents and bedrolls
  outdoors), one guard to a bed, never in the inn's rooms. A guard whose camp bed the town's network does not
  reach (a tent shut in by blocks) sleeps in a home's free bed instead; with none free, the last resident gives up
  theirs. Each house holds one household: a family, headed by the working person who lives there, then a partner,
  then their kin; never strangers thrown together. The one other sleeper a home takes is such a guard, as its lodger.
- **Who the people are comes after the draft.** The draft gives each person a placeholder name. Their names,
  households, trades, wealth and backstories are the skill `place-people`; its last step carries them into the
  place files.
- **Nothing levelled is ever placed** (decision 0035); the tools drop it and list it. A person's base is never a
  levelled character nor one that takes anything from a template (stats, inventory, spells) unless that template is
  itself a fitting base of the source: the next fitting base of the same people and role is taken, and `draft check`
  fails a person built on such a base.

## 6. Check and iterate

1. `python3 -m tools.places draft check <place_id>` must PASS. It proves, on the place files: every source ref
   accounted for, seated by its rule, buildings on ground no steeper than the source's, water and land as the
   source had them, patches within bound, streets clear of buildings and open water, every door on a path, every
   promised service and station given and worked, a bed for every sleeper, an unowned bed to rent at the inn,
   guards out of the inn, every resident in one household under one roof, replaced pieces in the original's plane,
   nothing floating or buried along its true outline beyond how it sat in the source, every door's arrival clear
   and on dry ground or a deck over the water, every replaced door facing its arrival, every light within 16
   units of its place by its fixture, every added forge lit, nothing Nordic
   added and nothing levelled placed, no world plant left standing in what we placed, the sentence as section 5 has it
   (a jail where the law jails and the town has a jail room, the Owing where the law is native), every source primitive built or dropped with its reason, and the files in the
   contract's order. It then builds the draft and runs every check of the build on it (section 8), so a draft that
   passes here passes there. Its `measures` line gives the patched cells and points and the streets' length: keep
   the patches as near nothing as you can.
2. Render again and look: does it read as the same town sitting naturally on our land? If not, go back to section 2 for a first draft; a place already drafted is changed by section 7.
3. `python3 -m tools.places seat <place_id>` must report 0 refs moved.
4. Correct the record's radius to what was built: `place.json` `radius_m` into the place's research record
   (`newworld/sources/research/places/*.json`, `footprint_radius_m`), then `python3 -m tools.newworld.build_db`.
5. Commit `newworld/places/<place_id>/` and the record change by path. The place is ready for the skill
   `place-people`.

## 7. Change a drafted place narrowly

A drafted place is changed by the stage that owns what must change, run alone on the place files as they stand:
`python3 -m tools.places draft <stage> <place_id>`. A stage changes only the rows it owns, leaves every other row
byte for byte as it was, never changes a row a finalised studio save touched, and prints the rows changed, added
and removed per file; a stage that would write outside what it owns changes nothing and fails.

| Stage | Run it when | It owns |
|---|---|---|
| `fit` | a piece belongs in another cluster (a light with its fixture) | the cluster, place and turn of the exterior rows that move; their ledger rows |
| `pieces` | `draft.replace` or `draft.drop` changed | the base, place, `align` and seat of the rows they name, in the exterior and every copied room; their ledger rows |
| `seating` | a seat rule changed | the seat and height of exterior rows |
| `clearance` | buildings, doors or streets moved; the world's plants were placed again | `clear.jsonl`: which of the world's plants go |
| `streets` (also `join`) | pieces, doors or the join's rules changed | flights, joins, arrivals, work stops, streets, patrols |
| `people` | the people source or the place's promises changed | names in `people.jsonl`, and each person's services as the record promises them (kind, detail, the network's destinations) |
| `lights` | stations were added, a room's lights changed | the lights of added stations; each room's lights on the source's own bases; `place.json` `lights` |
| `stations` | the record promises a station the files lack | the added station, its worker's stop, `place.json` `stations` |
| `jail` | the place's law, the jail room, its door or its arrival, the landing or the streets changed | the jail's or the Owing's prison markers, bedroll and chests; `place.json`'s crime row `law`, `law_why`, `jail` and `owing` |
| `primitives` | the source bundle, the kept pieces or the primitive classes changed | each exterior row's `primitive`, and a kept collision box's place, turn, seat and cluster by its piece; a dropped box's or trigger's row and its ledger row |

1. Make the change that calls for it (`place.json` `draft`, the people source, a rule of the tools).
2. Run the stage and read its counts: they are the whole change. Then run `streets` when what the network is built
   from changed (a piece, a door, a station), and section 6's checks.
3. Where a cluster sits on our land is the whole draft's search. `python3 -m tools.places draft <place_id>` on a
   place that holds the owner's finalised studio saves is refused and names the stages; a whole draft there needs
   `--force "<why no stage can be correct>"`, once, the reason kept in the commit.
4. After a world rebuild a place is brought level only when `python3 -m tools.places worldparts <place_id>`
   names world records that moved under it, in the order of the skill `world-build`, section 7, step 5.
5. After edits of single placed things, `tools/newworld/rebuild.sh plan` names each place they reach. A place
   whose `clear.jsonl` holds a row for an edited thing: take that row out and build the place again. A place
   whose cells hold an edit: extract its ground bundle again and build it. No other place changes.

## 8. Build and check

1. `python3 -m tools.places build <place_id>` builds the place layer plugin with the place's navmesh, from the
   place files and the database. The navmesh is cut round the place's own pieces and round everything the world has
   placed there (the world's refs shards) but the plants the place clears, so it meets the world's own navmesh edge
   for edge: the world file, its refs shards and its navmesh must be of one build, and the build fails when the
   shards do not hold every world ref the place clears. The build keeps, in `out/places/shards/<place_id>/world.json`,
   the stamp of the world records it stands on (Inputs): a place whose records the world file no longer holds is
   stale, the read-back's `places` row names what moved, and `infra/gpu-box/places_deploy.sh` refuses it. The
   world's own stages read of the place only who gives which promise, the stations found and the cells its plan
   covers, so a build that changes none of those leaves the world current (the skill `world-build`,
   [changes.md](../world-build/changes.md)). It is a long job: run `build <place_id> --plan` first (it plans only and lists every problem), then the build under
   `tooling/job_guard.sh`.
2. `python3 -m tools.places check <place_id>` reads the built plugin back. All seventeen checks are green: `plugin`,
   `seat`, `overlap`, `doors`, `people`, `navmesh`, `streets`, `land`, `clear`, `services`, `nordic`, `rooms`,
   `levelled`, `jail`, `primitives`, `stock`, `promises`. A place that fines only passes `jail` with a
   note saying why (no one keeps law there, or a foreign law with no jail room); a native place passes only with
   its Owing and its resist line whole. Each failure's full list is in
   `out/places/shards/<place_id>/check_failures/<check>.txt`. `check <place_id> --reach [person]` says what is cut
   off from what.
3. A failure is mended at its cause by the stage or the skill that owns it (a street by `streets`, a promise by
   `place-stock`). The place is never bent to pass a check, and a check is never loosened to pass a place. A
   finding beyond the checks is weighed by what the player would notice (the skill `world-build`, section 6).
4. `python3 -m tools.places navexport <place_id>` writes the built walking mesh the studio draws people's routes
   on.

## 9. The owner's studio edits and notes

The owner edits the built place in the studio (the browser editor of `docs/design/place-studio.md`), saves, and finalises a save with one tap. Finalise applies the save
to the place files and sources, builds, checks and runs the lessons agent (the skill `place-lessons`).

1. At the start of a session read the owner's notes: `python3 -m tools.places notes` (every open note, every
   place). A note about the place or about selected things is answered with a change: the narrow stage of section
   7, or the narrow change of the skill that owns the fact. Close it with
   `python3 -m tools.places notes done <place_id> <note id> --reply "<what was done>"`.
2. A note on changes travels in its save with the changes it covers. It is answered when the owner
   finalises that save: the lessons step reads it.
3. What the owner changed stays as the owner left it. No stage and no later pass moves, renames or removes a row a
   finalised save touched, and no draft is run over a place to bring a change in.
