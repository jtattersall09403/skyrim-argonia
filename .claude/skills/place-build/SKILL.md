---
name: place-build
description: Draft one place of the new world from its source place (any plugin we hold) onto our real ground - fit, seating, vegetation clearance, streets, interiors, people, lights - as the place files the studio and the build read. Use for each place's first draft, and to change a drafted place by the one stage that owns the change.
---

# Draft a place from its source

The tools do the measuring; you make the calls they cannot. Everything you decide goes in the `draft` block of
`newworld/places/<place_id>/place.json`; the tools write every other place file. The contract (file shapes,
seat rules, ids) is `docs/design/place-studio.md`. Never write mod record or asset content into a place file.

## Inputs

- `place.json`: `place_id`, `source_id`, `similar` (nw-04 fills these). Our record: `db.open("newworld")`, tables
  `place` (position, siting, population, summary) and `place_give` (what the place promises the player).
- The bundles `out/places/bundles/src.<source_id>` and `ground.<place_id>`
  (`python -m tools.places extract ...`). The ground bundle's stamp must match the deployed world file.
- Skyrim's town rules: `docs/research/skyrim/town-life.md`.

## 1. Read the source's character

1. `python -m tools.places draft <place_id>` once with an empty `draft` block, then
   `python -m tools.places draft render <place_id>` and look at `out/places/renders/<place_id>/source.png`.
2. Name in a few lines: where its water is and what stands in it (the landing, stilt houses, shallows); how its
   streets run between the doors; which buildings are entered and where they lead (`place.json` `fit.clusters_info`,
   `ledger.jsonl`); how close its plants come to buildings, streets and doors (`place.json` `clearance`).

## 2. Choose where it sits on our land

1. Look at `draft.png`: our rivers, banks and dry ground round the record's position.
2. The landing goes on our real bank of real water; the town's dry ground on our dry ground; the whole source at
   its true size. If the record's position does not serve, set `draft.anchor` `[x, y]` (game units) to the
   point the source's middle should take, on the ground that does. Set `draft.rot_deg` only when the search
   turns the town against the way it faces its water.

## 3. Draft and read the fit

What the tools hold to, so you can judge their output: our water and land are never changed to fit the source.
A cluster that stood on dry land goes on our dry land, one in or over water (jetties, stilt houses, shallows,
boats) on our water; a cluster whose spot fails slides, turns or steps to the next ground of its kind, and a door
moves with its whole building. A single piece that still has no ground of its kind is dropped and listed. No
piece of one cluster stands in another's (the build's overlap rule: an origin within 0.8 of another solid's record
box): the fit's last pass steps the smaller cluster the least distance clear, and a clash no step clears drops the
smaller piece with the reason (`fit.separated`); a cluster or a piece stepped afterwards to its side of the waterline
never steps into another. Pieces that stand in each other in the source (a mud dome over its entrance, windows
set in it), compared in the source's own frame with full rotation, are one body and share a cluster; a tilted
piece turns about the world's axis with its cluster (one transform). A sunk filler block or a low platform (its top within a step of the
ground) is walked over, never an obstacle. Land
patches only ease the ground under a building, at most 1.5 m at any point and never across the waterline; a
building on a slope first takes the rise the source's own builders commonly built on (`fit.relief_norm`).

1. `python -m tools.places draft <place_id>` then `draft render <place_id>`; compare `side-by-side.png`: the same
   cluster ids sit in the same order, facing their street and their water.
2. In `place.json` `fit.clusters`, a cluster with a high `cost_after` sits badly. In `ledger.jsonl`, pieces dropped
   for want of water or land, and doors above all, say the anchor or the turn is wrong: move them and redraft
   rather than accept the losses.
3. Streets (orange in the render) and walkways (brown) join every door, the landing and every camp into one
   network. Where the source drew a street (a painted road, walkway pieces, its navmesh's preferred paths) ours
   keeps to that line. Where it drew none, the link between two doors is the easiest going on our ground, never a
   ruled line: it winds with the ground underfoot, goes round the trees and rocks in its way, keeps to the middle
   of a gap between buildings, and shares a stretch with a path already laid. No street climbs steeper than the
   source's streets did.
   Every link is routed on our ground with our decks counting as ground, a link to a door on the water included,
   so a boardwalk's line runs along its decks (over the water a step of the route stands where the deck is, its
   middle on the deck or on the deck's long middle line, never beside it) and a ship's hatch is reached over its
   own ship. The landing's shore
   end is where the landing's own pieces meet our dry ground, never a bank it does not touch. Open water is
   crossed only where nothing else joins the two ends, and then where it is narrowest, on bridges of the source's
   own walkway pieces: one piece per piece length along the route, each slid along it clear of any solid there,
   its deck a hand's breadth over the water (a walkway's deck is the top of its collision at its centre, read per
   piece, never its record's top, which is the rail).
   Look at every street close up, not only in the whole-town render. A straight run longer than a few houses, a
   line beside a deck and not on it, a bridge that ends on an empty bank, or many bridge pieces where the source
   had none each say the anchor, the turn or a cluster's spot is wrong: put that right and redraft; never accept
   the line.
   Steps hang on their deck the way Skyrim's dock steps do (measured on Skyrim.esm's DockStepsDown01 and 02):
   square to the deck, the top end against its edge, the top tread at the deck's own height, the piece seated `on`
   the deck piece. A flight of the source's that abuts a deck a little off its height (within 64 units; a step
   the navmesh does not climb) is seated so in the draft, and deck and flight are one walked surface: a ship the
   source moored beside its pier with steps between them is joined by those steps.
   After the draft the tools build the place and read its navmesh. A deck that carries a door or a street and
   that the town reaches only by swimming (a pier or quay the source met at its bank's height, standing above
   ours) gets one flight of the source's own steps, hung as above off a free edge of one of its deck pieces and
   running down until its treads meet our ground where the town's network walks. The bank may bury the rest of
   the run, as steps set into a slope; no tread stands under the ground before that, and the flight's body is
   clear of every solid by the build's overlap rule. Of the flights that fit, the one the bank buries least is
   laid, then the one nearest the deck's streets and doors. A deck nothing of the town uses (a rowing boat, a
   bridge deck high overhead) gets none. Look at each flight in the render.
   A door whose walkable ground is still an island is joined to the town by level walkway pieces laid from the
   island to the nearest point of the network at its height (never across a height the navmesh does not climb:
   that is a flight's work). A piece laid for a door that stands on a thing (a ship's hatch) rests on that thing
   as its gangway and names it as its `carrier`; a piece that continues a walkway stands `on` it. The build's
   overlap check lets a piece rest on what its seat names, by the same rule the drafter lays it with. A door whose
   island no join reaches and whose room nobody lives or works in is left out with its room and the links that led
   to it, with the reason in the ledger. A guard whose camp bed the town's network does not reach (a tent shut in
   by blocks) sleeps in a home's free bed instead; with none free, the last resident gives up theirs. A camp (beds
   in the open) is a stop like a door: a street reaches its edge.
   Every door's arrival outside stands on the built walkable network at its own level (the deck or the ground the
   door lands one on): an arrival more than 16 units over or under the mesh is put at the mesh's height where it
   is; one off the network is moved to the nearest point of it, on the same side of its door and outside every
   placed thing's body, at the mesh's height there. A person's outdoor work stop named by a thing the network
   does not reach (a Hist's trunk) becomes the nearest point of the network beside it.
   Streets and patrols lie on the built walkable network. Once the doors are joined, every street, path and
   walkway is walked along its whole line (a point every 64 units) on the town's main network of the built navmesh
   (ours and the world's own round the place). A point stands on a dry triangle at a level one may stand at there:
   a deck's or a flight's own surface (within 48 units of it), the ground or a ford, or, over water too deep to
   wade with no deck, a dry triangle right over it; never the seabed. Each point is taken at the level one reaches
   it by from the point before, never by a drop or a climb steeper than a walked slope (a step off a deck's edge
   onto the ground under it), so a line under a pier stays on the ground and a line down a flight stays on the
   flight. A stretch off the network (where a big static's true collision cuts the mesh, where a deck stands above
   its bank) is re-laid along the way the mesh itself walks from a little before it to a little after, never
   through water deeper than a ford: through the middles of the triangle edges it crosses, pulled straight and
   eased only where the line still walks the same way. Stretches close together are re-laid as one. The street's
   `laid` says so, and the world's plants the new line reaches are cleared by the draft's own measure. Guards'
   patrols are then taken from those streets, each point on the network (a patrol keeps at least two). One pass
   settles every line: `draft check` mends each street again on the built mesh and fails if anything is re-laid.
   `draft check` and the build's `check` (its `streets` check) list any street or patrol point still off the
   network.

## 4. Settle what the cost cannot

- **The source's own pieces are accepted as they come.** A piece the source place itself uses, from its own mods,
  Tropical Skyrim or the base game, is never judged by its look, replaced for it or dropped for it: a Solitude
  door, a High Hrothgar fire pit or a Dawnguard runner the source set there stands in ours, lit or unlit as the
  source has it. Decision 0006 governs only what we add from elsewhere (a station, a replacement, a laid piece):
  the tools take those from non-Nordic bases, by the catalogue's folder rule, or the looked-at verdict in
  `newworld/places/nordic_review.jsonl` where a base has one (contract: Bundles). `draft check` and the build's
  `nordic` check fail a Nordic base added from outside the source place.
- **A piece that cannot stand in our place as it is** (a door whose model does not fit the wall we give it, a piece
  whose function ours lacks) is swapped by `draft.replace` `{old: new}` or `{old: {base, turn_deg}}`, for a piece of
  like size and use from a non-Nordic source we deploy (`python -m tools.places search query "<what it is>"`, or the
  catalogue `out/places/catalogue/bases.jsonl`). A replaced walkway keeps the original's walking height (its top
  where the original's was), so a door or a deck that met it still does. The tools line a replaced door or
  directional piece up with the original's plane from both meshes (the turn and the shift, `align` on the ref) and
  `draft check` proves it. It also proves every door's arrival point is where one stands (our ground, a low road or
  deck one steps onto, or the thing a door stands on), outside every placed thing's body by the build's own test,
  clear of collision and in front of the door's plane. A replaced door faces out by construction: its front is read from its mesh
  (a door modelled in place has its origin inside, off the leaf, so its front is the face away from the origin)
  and it is turned half round about its leaf when that front would face away from where one arrives outside it
  (the source's own arrival marker). A door's `to_pos` is where using it lands you: the exterior door's partner
  holds the arrival outside, and `draft check` proves each replaced door faces it.
- **A light belongs to its fixture.** A light has no body; the lantern, sconce, window or fire it was placed for
  is the nearest one within 128 units of it in the source. The light shares that fixture's cluster, stands at its
  source offset from it (turned with the cluster), is seated `on` it, and is left out when the fixture is.
  `draft check` fails a light more than 16 units off that place.
- **What we add is lit as Skyrim lights it** (measured on Skyrim.esm's exteriors). An added forge carries
  LightForgeFire01 in the forge's own frame, where 15 of 24 vanilla forges carry it (median offset x -16, y 167,
  z 84). An added smelter carries none (0 of 21) and an added alchemy lab none (3 of 16). The streets,
  bridges and steps we lay carry no light unless the source lit its own walkways: count the source's walkway pieces
  with a light within 256 units and light ours at that rate, rounded: where 1 source piece in 63 is lit, ten laid
  pieces carry no light.
- **No room holds more than four shadow-casting lights**, the number the engine draws at once. In a copied room
  over that, the four of the largest radius, then nearest the room's middle, keep their shadows; each other
  switches to its no-shadow twin base as Skyrim names them (`<name>NS`, or the name without `Shadow`, or `NS` on
  the name before its `_` suffix), written as a row of the room with `twin_of`. A caster with no twin in the load
  order cannot switch, so it is one of the four that keep their shadows; `draft check` fails a room that still
  exceeds four.
- **Leftovers**: `draft.drop` `{source ref id: reason}` for anything the source placed that our place must not have.
- **What the record promises and the source lacks is added in the source's own style.** The tools add each
  missing crafting station by the person who works it, the way Skyrim's towns do (the smith's yard outside the
  smithy; the alchemy lab with the apothecary; the enchanter with the spell trader; the cooking pot at the inn).
  A station's base is one whose record carries the station's crafting keyword (what the game keys on), from the
  plugins whose style the place uses: the marsh's own mods unless the place is of another people, in which case
  name its mods, first choice first, in `draft.style_order`. Where no non-Nordic base carries the keyword, the
  vanilla working base, said in its `why`. One piece doing two stations' work counts for both (Skyrim's forge is its anvil). The smith's yard
  is laid as Riverwood's (the forge, the grindstone beside it, the workbench and tanning rack across the yard, each
  facing it): the forge on the nearest clear ground to its worker with room for the yard, the rest in that layout
  or the nearest clear ground round the forge within the worker's reach. Clear means: dry under its outline, its
  body clear of every placed solid by true record box (on a road or a deck only by its edge), 256 units from any
  door, off the streets. A station added indoors stands on the walked-in floor clear of the room's things. Check each in the render (`stations.added`); move one with `draft.add` and `draft.roles`
  when it stands wrong. Traders work where the source's own trader of that trade worked.
  A travel stop (`boat-stop`, `coach-stop`, `rootworm-stop`) is a person's service like a trade: the operator the
  place's people name (a boatman, a carter, a root-tender), given the stop's give by its seq, working at the
  landing (a boat's at the water's edge or on a deck over it, a coach's at the gate on the major road, a rootworm's
  at the Hist's root pool). Where they go and for what fare is the travel network's, never the person's.
  A promised shrine blessing needs a thing to carry it: the source's own Hist or shrine, else the tools add a
  young Hist in the town's middle, clear of buildings and streets (`stations` `shrine`); look at it in the render.
- **People follow Skyrim's days** (`docs/research/skyrim/town-life.md`): an innkeeper keeps the inn day and
  night and owns no bed; guards keep two 12-hour shifts on the streets. Never bend a day to satisfy a check;
  if a check disagrees with how Skyrim does it, the check is wrong.
- **Beds decide the people.** A house copied from a cell several houses share keeps only its own room, by the
  builder's room rule (the drafter calls it, so the beds counted are the beds built). Every promised service
  person works; residents fill the homes' remaining beds. A promise a townsman keeps beside his own life (a
  rootworm stop's handler, a follower) makes no person of its own: it is given to the resident whose trade in the
  people source (`newworld/sources/people/<place_id>.json`) says the most of it, else to the first resident who
  gives nothing yet. A stop's handler works at it through the service hours; a rootworm stop is at the place's
  Hist, whose roots the worms run in.
- **Who sleeps where, the vanilla way.** An inn that rents a room keeps one of its beds unowned: that is the
  rented bed (`stations.rent_bed`). Guards sleep in a barracks or their camp's own beds (tents and bedrolls
  outdoors), one guard to a bed, never in the inn's rooms; a family's home only when the camp bed cannot be
  walked to (see the joins above). Each house holds one household: a family, headed by
  the working person who lives there, then a partner, then their kin; never strangers thrown together.
- Nothing levelled is ever placed (decision 0035); the tools drop it and list it. A person's base is never a
  levelled character nor one that takes anything from a template (stats, inventory, spells) unless that template is
  itself a fitting base of the source: the next fitting base of the same people and role is taken, and `draft check`
  fails a person built on such a base.

## 5. Check and iterate

1. `python -m tools.places draft check <place_id>` must PASS: every source ref accounted for, seated by its
   rule, buildings on ground no steeper than the source's, water and land as the source had them, patches within
   bound, streets clear of buildings and open water, every door on a path, every promised service and station
   given and worked, a bed for every sleeper, an unowned bed to rent at the inn, guards out of the inn,
   every resident in one household under one roof, replaced pieces in the original's plane, nothing floating or buried
   along its true outline beyond how it sat in the source, every door's arrival clear and on dry ground or a deck
   over the water, every replaced door facing its arrival, nothing standing in another
   by the build's overlap rule (inside a room, nothing added in the room's things), every copied room entered
   through a door pair both sides name with its outside arrival on our ground or a walkway a street reaches, and
   every person's stops each reached from the one before (our ground and streets outside, the builder's room
   island inside, the door pair between), each on walkable ground or a piece of furniture, every light within 16
   units of its place by its fixture, every added forge lit, no room over four shadow casters; and the build's own
   `build <place_id> --plan` when it exists. Its `measures` line gives
   the patched cells and points and the streets' length: keep the patches as near nothing as the land allows.
2. Render again and look: does it read as the same town sitting naturally on our land? If not, go back to 2
   for a first draft; a place already drafted is changed by section 6.
3. `python -m tools.places seat <place_id>` must report 0 refs moved.

## 6. Change a drafted place narrowly

A drafted place is changed by the stage that owns what must change, run alone on the place files as they stand:
`python -m tools.places draft <stage> <place_id>`. A stage changes only the rows it owns, leaves every other row
byte for byte as it was, never changes a row a finalised studio save touched, and prints the rows changed, added
and removed per file; a stage that would write outside what it owns changes nothing and fails.

| Stage | Run it when | It owns |
|---|---|---|
| `fit` | a piece belongs in another cluster (a light with its fixture) | the cluster, place and turn of the exterior rows that move; their ledger rows |
| `pieces` | `draft.replace` or `draft.drop` changed | the base, place, `align` and seat of the rows they name, in the exterior and every copied room; their ledger rows |
| `seating` | a seat rule changed | the seat and height of exterior rows |
| `clearance` | buildings, doors or streets moved | `clear.jsonl`: which of the world's plants go |
| `streets` (also `join`) | pieces, doors or the join's rules changed | flights, joins, arrivals, work stops, streets, patrols |
| `people` | the people source or the place's promises changed | names and promises in `people.jsonl` |
| `lights` | stations were added, a room's lights changed | the lights of added stations; each room's `twin_of` rows; `place.json` `lights` |
| `stations` | the record promises a station the files lack | the added station, its worker's stop, `place.json` `stations` |

1. Make the change that calls for it (`place.json` `draft`, the people source, a rule of the tools).
2. Run the stage, read its counts: they are the whole change. Then `streets` when what the network is built from
   changed (a piece, a door, a station), and section 5's checks.
3. Where a cluster sits on our land is the whole draft's search. `python -m tools.places draft <place_id>` on a
   place that holds the owner's finalised studio saves is refused and names the stages; a whole draft there needs
   `--force "<why no stage can be correct>"`, once, the reason kept in the commit.

## 7. Record

1. Correct the record's radius to what was built: `place.json` `radius_m` into the place's research record
   (`newworld/sources/research/places/*.json`, `footprint_radius_m`), then `python -m tools.newworld.build_db`.
2. Commit `newworld/places/<place_id>/` and the record change by path.
