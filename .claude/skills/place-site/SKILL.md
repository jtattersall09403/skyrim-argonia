---
name: place-site
description: Put a place's source onto our real ground - the anchor and turn, the fit of whole clusters, seating by sinking, plant clearance, land patches and which source pieces are kept, swapped or dropped (Nordic pieces judged case by case). Use when judging a draft's fit, when a house or structure sits badly or must move, and when a piece must be replaced or dropped.
---

# Site and seat the place

Step 3 of the place path ([place-system](../place-system/SKILL.md)). Stages: `fit`, `pieces`, `seating`,
`clearance`, `primitives` (the collision boxes, in `place-dressing`).

## 1. Choose where it sits

1. Look at `draft.png` (`draft render`) and the overview in the studio scene: our rivers, banks and dry ground round
   the record's position.
2. The landing goes on our real bank of real water; the dry ground of the town on our dry ground; the whole source
   at its true size. If the record's position does not serve, set `draft.anchor` `[x, y]` to the point the
   source's middle should take. Set `draft.rot_deg` only when the search turns the town against the way it faces
   its water.
3. Our water never changes to fit the source, and our land changes only inside the place's footprint (below).
   Ground a place needs beyond its footprint (a pad, a landing) is asked for in the record and shaped by the world's
   terrain (skill `world-build`).

## 1b. Carry the source's ground, then plan the units on it

The source's builder shaped the land under the town and built on it, so the town fits only the ground it stood on.
`python -m tools.places draft ground <place_id>` (`--dry` first: read the relief, the band, the source-water area
and the largest change) carries the source's relief under the place's footprint (the hull of the carried pieces,
grown 256) as land rows `by` "ground", blended into our ground over a band no steeper than the source's own
steepest slope (or 35 degrees), each cluster reading the source through its own map from the fit. Nothing outside
the footprint and band changes, no point crosses our water line, no change exceeds 600, the source's water is not
brought (its area is reported: pieces that stood in it need a decision), and no cell of another place is touched.
Then put the carried pieces at the source's own levels (source height minus the source's reference level, plus
ours), run `draft sap` again (its hollow is dug on top), and plan the units on the carried ground (section 3). The
look tool, `units`, the seat and the build all read the patched ground from `land.jsonl`.

## 2. Read the fit

The `fit` stage moves each cluster (one building or one group) as one body: dry-land clusters on our dry land,
water clusters (jetties, stilt houses, boats) on our water; a cluster whose spot fails slides, turns or steps to the
next ground of its kind; a door moves with its building; pieces that stand in each other in the source share a
cluster. Clashes are stepped clear or the smaller piece dropped (`fit.separated`). Land patches ease the ground under
a building by at most 1.5 m and never across the waterline; a building on a slope first takes the rise the source's
builders built on (`fit.relief_norm`).

1. Compare `side-by-side.png`: the same cluster ids in the same order, facing their street and their water.
2. A cluster with a high `cost_after` in `place.json` `fit.clusters` sits badly. Pieces dropped in `ledger.jsonl`
   for want of water or land, doors above all, mean the anchor or the turn is wrong: move them and draft again.
   Losses are not accepted.
3. Keep the patches as near nothing as you can (`draft check`'s `measures` line).

## 3. Seat by sinking, move structures whole

A structure is a **unit** (`python -m tools.places units <place_id>`, `tools/places/units.py`), read from the
source's own arrangement, where every piece rests on what it should, and carried to the draft by each row's `src`:

- A **house** is its body with the platform or deck it stands on, the posts under them, the steps and railings at
  its deck, the doors set in its walls (and the room behind them) and what rests on, hangs on or is fixed to it. It
  is named by its room: `house.SeekhatEldersHut`.
- A **walkway**, **bridge** or **dock** is a unit of its own; its joins name the units its ends rest on (a house, a
  dock, the ground).
- A boat, a rack, a stall is a small unit. Trees, rocks, roots and ground cover belong to the ground and are judged
  against it, never moved with a building; a plant standing on a deck is part of that deck's unit.
- A **Hist** is one unit (`hist.01`): its trunk with its roots, glands, flowers, vine floors, the lights and chimes in
  its crown and its sap pool, in the source's arrangement about the trunk (a Hist the draft swapped stands in for the
  source's). Its row flags a root that stood on the source's ground and hangs over ours, and anything off its height
  on the trunk; `units apply <place> hist.01` seats it by that rule. Keep the source's own Hist model where there is
  a placeable one (`HistTree01` is `ArgoniaTreeHist01`'s), so what hung on it meets its limbs.

Each unit is measured on our ground: its standing level (floor or deck) against the highest ground under its
footprint, each foot against the ground under it and its leg (how far it reaches below the standing level in the
source), its body against its own deck (as in the source), each door sill against its floor and the ground before
it, each join against the source's relative height. The units table flags each fault by name.
`units <place> --joints` lists every stair, ramp, bridge, walkway and boardwalk end against what it meets (a deck, the
ground, another span), with the gap along and in height, and whatever stands on a span that is not its own: read it
after moving a structure that carries or meets a span, and mend each end that is not `meets`, `rests on ground` or
`on its own legs`.

- A piece is seated by sinking it into the ground until it stands; nothing is stretched or extended to reach the
  ground.
- A unit is sunk, moved or turned whole: in the studio scene, name it by its unit id (`look sink
  house.SeekhatEldersHut 40`, `look move walkway.04 dx dy dz`), check with `probe` and `section`, then `look commit`
  (`place-look`). A house's body is never moved without its deck; `--piece` moves the one piece named.
- The layout is planned for the place as a whole (`units plan <place>`: each unit put back together at the source's
  levels within it, then one offset) and written unit by unit with `units apply <place> <unit> ...`, through the
  same path as `look commit`: what lay on the source's ground by or under a house (a net, a fire pit) lies on ours,
  and every tree, fern, rock and root an earlier edit of a building moved goes back to its own seat on the ground.
  Commit the place files by path, then look: the pictures draw what is committed. Apply one house at a time and
  survey it before the next; the spans follow the houses.
- What an agent's edit or the owner's save placed stays where it was put: its seat is pinned to its height
  (`seat.pin`) and the `seating` stage keeps it (`draft.stages.placed_rows`).
- `draft check` refuses a house moved apart from its platform (its body's gap to its own deck changed by more than
  8 units from the source's) and a tree or root moved by an edit of a building.
- A walked level with its own flights stands as one body: the `seating` stage keeps the source's relative heights of
  a yard of floor plates and the flights that reach it (`seating.levels`).
- A sunk filler block or a low platform (top within a step of the ground) is walked over.

Buried is physical, one rule for `draft check` and `look probe` (`look/geom.is_buried`): a piece is buried when
nothing of it shows (its top under the lowest ground beneath it), a plant or a door, window or floor when most of it
is under; stilt posts and rock feet in the ground are fine, and a house moved down whole by hand is judged by what
shows, not by the source's seat.

Overlap is inside the solid: a rock, cliff, tree or Hist is judged by the vertical profile of its collision
(`check.stands_in_solid`), so open ground in a cliff's box or beside a trunk is outside; every other piece is its box,
so a house inside a house is still caught.

Enforced by the checks: nothing floating along its true outline beyond its source seat, nothing buried (`draft check`;
`look probe --all`), the build's `seat` and `overlap` checks, `seat <place_id>` reporting 0 refs moved.

## 4. Clear the world's plants

The `clearance` stage clears a plant rooted closer to a building, street or door than the source's own plants
came, anything rooted inside a placed thing, and a world thing whose body lies across a street or a door front
(`clear.jsonl`; the build's `clear` check). Run it again whenever buildings, doors or streets move.

## 5. Keep, swap or drop pieces

- **The source's own pieces are kept as they come**, from its own mods, Tropical Skyrim or the base game, lit or
  unlit as the source has them.
- **Nordic pieces are judged case by case.** Keep one that is nearly fine; where a Tropical Skyrim version or an
  easy swap exists, take it; never laboriously replace. Nordic signs never stand (`place-plan`). What we add from
  elsewhere comes from non-Nordic bases (the catalogue's folder rule, `newworld/places/nordic_review.jsonl`); the
  build's `nordic` check fails a Nordic base added from outside the source.
- **A piece that cannot stand as it is** (a door that does not fit its wall, a piece whose function ours lacks) is
  swapped by `draft.replace` `{old: new}` or `{old: {base, turn_deg}}`, for a piece of like size and use
  (`python3 -m tools.places search query "<what it is>"`, or `out/places/catalogue/bases.jsonl`). A replaced
  walkway keeps the original's walking height. The tools align a replaced door or directional piece to the
  original's plane and turn a door to face its arrival; `draft check` proves both.
- **Anything else our place must not have**: `draft.drop` `{source ref id: reason}` (the `pieces` stage; a room
  whose way in is dropped goes with it).
- **Nothing levelled is ever placed** (decision 0035): the tools drop it and list it; the build's `levelled` check.
