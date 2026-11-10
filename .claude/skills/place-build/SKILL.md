---
name: place-build
description: Draft one place of the new world from its source place (any plugin we hold) onto our real ground - fit, seating, vegetation clearance, streets, interiors, people - as the place files the studio and the build read. Use for each place's first draft, and to redraft after the ground or the recipe changes.
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
smaller piece with the reason (`fit.separated`). A sunk filler block or a low platform (its top within a step of the
ground) is walked over, never an obstacle. Land
patches only ease the ground under a building, at most 1.5 m at any point and never across the waterline; a
building on a slope first takes the rise the source's own builders commonly built on (`fit.relief_norm`).

1. `python -m tools.places draft <place_id>` then `draft render <place_id>`; compare `side-by-side.png`: the same
   cluster ids sit in the same order, facing their street and their water.
2. In `place.json` `fit.clusters`, a cluster with a high `cost_after` sits badly. In `ledger.jsonl`, pieces dropped
   for want of water or land, and doors above all, say the anchor or the turn is wrong: move them and redraft
   rather than accept the losses.
3. Streets (orange in the render) come from the source's painted roads, walkways and preferred navmesh, laid on
   our ground round buildings and water at no steeper climb than the source's streets made. A link to a door on
   the water is a walkway (brown). A street that will not route without crossing our water is carried on bridges
   of the source's own walkway pieces, one piece per piece length along the route, each slid along it clear of
   any solid there (a deck lifted a hand's breadth over a drowned thing just under it); look at each one. A camp
   (beds in the open) is a stop like a door: a street reaches its edge.

## 4. Settle what the cost cannot

- **Nordic bases are judged by look** (decision 0006). The folder flag only sorts; the verdict is the Nordic
  review, `newworld/places/nordic_review.jsonl` (contract: Bundles). For every flagged base the source uses that
  the review lacks, look at its thumbnail (`tools.places.assets.thumb(model)`): a carved Nordic door, a Solitude
  planter or a Nord sword is `nordic`; leaves, moss, plain posts, planks and docks are `neutral`. Write its row,
  with the standard replacement for a Nordic one; the tools then replace it in the exterior and in every interior
  copy, or drop it with a ledger reason. `ledger.jsonl` lists each dropped one. For a Nordic base with no `replace`, find a piece of like
  size and use from a non-Nordic source we deploy (`python -m tools.places search query "<what it is>"`, or the
  catalogue `out/places/catalogue/bases.jsonl`), and set `draft.replace` `{old: new}`, or
  `{old: {base, turn_deg}}`. A replaced walkway keeps the original's walking height (its top where the original's
  was), so a door or a deck that met it still does. The tools line a replaced door or directional piece up with the original's plane
  from both meshes (the turn and the shift, `align` on the ref) and `draft check` proves it, with every door's arrival point where one stands (our ground, a low road or deck one steps onto, or the thing a door stands on), outside every placed thing's body by the build's own test, clear of
  collision and in front of its plane. Which face of a new door mesh is its front cannot be read from geometry:
  the tools list each such door in `place.json` `needs_look`; carry that list to the owner check. A door that leads
  indoors is always replaced, never dropped. Drop decorative pieces with no equal.
- **Leftovers**: `draft.drop` `{source ref id: reason}` for anything the source placed that our place must not have.
- **What the record promises and the source lacks is added in the source's own style.** The tools add each
  missing crafting station by the person who works it, the way Skyrim's towns do (the smith's yard outside the
  smithy; the alchemy lab with the apothecary; the enchanter with the spell trader; the cooking pot at the inn).
  A station's base is one whose record carries the station's crafting keyword (what the game keys on), from the
  plugins whose style the place already uses; where no non-Nordic base carries it, the vanilla working base, said
  in its `why`. One piece doing two stations' work counts for both (Skyrim's forge is its anvil). The smith's yard
  is laid as Riverwood's (the forge, the grindstone beside it, the workbench and tanning rack across the yard, each
  facing it): the forge on the nearest clear ground to its worker with room for the yard, the rest in that layout
  or the nearest clear ground round the forge within the worker's reach. Clear means: dry under its outline, its
  body clear of every placed solid by true record box (on a road or a deck only by its edge), 256 units from any
  door, off the streets. A station added indoors stands on the walked-in floor clear of the room's things. Check each in the render (`stations.added`); move one with `draft.add` and `draft.roles`
  when it stands wrong. Traders work where the source's own trader of that trade worked.
  A promised shrine blessing needs a thing to carry it: the source's own Hist or shrine, else the tools add a
  young Hist in the town's middle, clear of buildings and streets (`stations` `shrine`); look at it in the render.
- **People follow Skyrim's days** (`docs/research/skyrim/town-life.md`): an innkeeper keeps the inn day and
  night and owns no bed; guards keep two 12-hour shifts on the streets. Never bend a day to satisfy a check;
  if a check disagrees with how Skyrim does it, the check is wrong.
- **Beds decide the people.** A house copied from a cell several houses share keeps only its own room, by the
  builder's room rule (the drafter calls it, so the beds counted are the beds built). Every promised service
  person works; residents fill the homes' remaining beds.
- **Who sleeps where, the vanilla way.** An inn that rents a room keeps one of its beds unowned: that is the
  rented bed (`stations.rent_bed`). Guards sleep in a barracks or their camp's own beds (tents and bedrolls
  outdoors), one guard to a bed, never in the inn's rooms or a family's home. Each house holds one household: a family, headed by
  the working person who lives there, then a partner, then their kin; never strangers thrown together.
- Nothing levelled is ever placed (decision 0035); the tools drop it and list it.

## 5. Check and iterate

1. `python -m tools.places draft check <place_id>` must PASS: every source ref accounted for, seated by its
   rule, buildings on ground no steeper than the source's, water and land as the source had them, patches within
   bound, streets clear of buildings and open water, every door on a path, every promised service and station
   given and worked, a bed for every sleeper, an unowned bed to rent at the inn, guards out of the inn,
   every resident in one household under one roof, replaced pieces in the original's plane, nothing floating or buried
   along its true outline beyond how it sat in the source, every door's arrival clear, nothing standing in another
   by the build's overlap rule (inside a room, nothing added in the room's things), every copied room entered
   through a door pair both sides name with its outside arrival on our ground or a walkway a street reaches, and
   every person's stops each reached from the one before (our ground and streets outside, the builder's room
   island inside, the door pair between), each on walkable ground or a piece of furniture; and the build's own
   `build <place_id> --plan` when it exists. Its `measures` line gives
   the patched cells and points and the streets' length: keep the patches as near nothing as the land allows.
2. Render again and look: does it read as the same town sitting naturally on our land? If not, go back to 2.
3. `python -m tools.places seat <place_id>` must report 0 refs moved.

## 6. Record

1. Correct the record's radius to what was built: `place.json` `radius_m` into the place's research record
   (`newworld/sources/research/places/*.json`, `footprint_radius_m`), then `python -m tools.newworld.build_db`.
2. Commit `newworld/places/<place_id>/` and the record change by path.
