---
name: place-site
description: Put a place's source onto our ground - decide how much of the source's ground to bring, choose the one transform and height from sections, lay the baseline (every source piece in the footprint, the carried ground, rooms, walks and the source's walking mesh) with draft wholesale, then fit it to our ground by hand (mounds with the land brush, units sunk or moved whole, steep banks dressed with rock) and clear the world's plants. Use for a place's baseline, when a structure sits badly on our ground, and when a post or leg stops short of it.
---

# Ground, baseline and fit

Step 3 of the place path ([place-system](../place-system/SKILL.md)). Before: the source pinned (`place-plan`).
After: the adaptation (`place-adapt`).

## The first draft, in order

1. `python3 -m tools.places draft <place_id>` once, on a place with no draft: the frame (people rows, quest spots,
   `place.json` `fit`); its exterior pieces are replaced in step 3.
2. The transform in `fit` (section 1) and the ground (section 2).
3. `draft wholesale` (section 3): the pieces, then `--rooms`, then `--walks`. The plain run re-lays every exterior
   piece and clears paths, land rows and agent edits, so it is refused on a place holding hand edits (re-carry with
   `--rooms` or `--walks`, or change by hand or by a stage; `--discard-hand-edits` only to lose them deliberately).
4. Commit, then hand work: fit to our ground (section 4), the adaptation (`place-adapt`), rooms (`place-rooms`),
   people on the furniture (`place-routines`), quest spots (`place-story`).
5. The rule stages on the place as it stands: `draft sap`, `draft stations`, `draft hang` where a Hist's trees lack
   lanterns, `draft primitives`, `draft clearance`, `draft names`, `draft jail` (`place-dressing`, `place-routines`),
   each looked at.
6. Verify once (`place-check`).

## 1. The frame the baseline is laid over
 The source bundle must exist
(`python3 -m tools.places source <place_id>`) and the ground bundle stand on the deployed world
(`extract --ground <place_id>`, `ground-check <place_id>` passes; the world is settled first, skill `world-build`).

Set the transform in `place.json` `fit`: `pivot` the source point that becomes the place's middle, `anchor` the point
of ours it lands on (the record's position unless the record's siting needs another point inside it), `rot_deg` the
turn. Choose the turn so the source faces our water and banks as it faced its own, and so our ground fits the
source's best: compare sections of our ground and the source's (`look --source <id> section`, `look <place>
section`) across two or three axes at each turn worth trying: set `rot_deg`, run `draft wholesale <place_id> --offset
<u> --dry` (it reads `fit`) and section the carried relief against ours.

## 2. How much of the source's ground to bring

The source's builders shaped their ground and built on it, so their place fits the ground it stood on. Decide by
sections, per part of the place:

- **All of it**: the source's whole relief inside the footprint (a town on its own mound, a marsh onto a marsh).
- **Only a structure's own platform or a district's own terrace**: `--carry-radius <u>` round the middle, and
  `--cap <u>` on the change (a district's terrace capped at about 300 units and eased to our level, never a whole
  hill brought into a flat site).
- **None**: a flat source onto flat ground (`--cap 0`). A pond's bed brought as mud: `--keep-wet`.

Our water line never moves and the source's water is never brought (its bed may come as mud with `--keep-wet`);
nothing outside the footprint changes. A steep bank inside the place is allowed where it is dressed with rock and
cliff pieces (Tropical Skyrim's among them); bare stretched ground is a fault.

## 3. Lay the baseline

1. Choose the one height offset (z, in game units, added to every source height) from sections: the source's walked levels over our ground where the place is
   entered, its posts' feet in our ground, not on it.
2. `python -m tools.places draft wholesale <place_id> --offset <u> [--carry-radius u] [--cap u] [--keep-wet] --dry`:
   read the pieces laid, the band, the largest raise and lower, the source water area and what our water holds;
   then run it without `--dry`. Every source piece inside the footprint lands at the one transform and height; only
   actors, the source's water plane and levelled bases are left out (`ledger.jsonl` says why). A place that takes one
   part of its source (its plan's `differs`) adds `--take <u>`: only the pieces within u of the pivot are laid, and the
   ground and the source's walking mesh are carried for that part alone; the rest of the footprint stays ours.
3. `draft wholesale <place_id> --offset <u> --rooms`: the source's rooms with their door pairs and arrivals, landing
   where the source landed them (`place-rooms`).
4. `draft wholesale <place_id> --offset <u> --walks <x,y>` (the hub: the place's middle or its landing): the source's
   walks carried as path rows.
5. Set `place.json` `wholesale.navmesh` to `"source"`: the build writes the source's own walking mesh inside the
   footprint (`place-streets`).
6. Commit the place files by path and look: `look <place> overview`, `survey`, sections across the edge band. The
   place should read at once as its source on our land.

## 4. Fit it to our ground by hand

A structure is a **unit** (`python -m tools.places units <place_id>`): a house with its platform, posts, steps and
what hangs on it, named by its room (`house.SeekhatEldersHut`); a walkway, bridge or dock; a small unit (a boat, a
rack, a stall); a Hist with its roots, glands and crown (`hist.01`). Trees, rocks and roots belong to the ground.
The units table measures each on our ground (standing level against the ground under it, each foot against its leg,
each door sill, each join) and flags each fault by name; `units <place_id> --joints` lists every stair, ramp, bridge
and walkway end against what it meets.

- **Posts short of our ground**: a mud mound under them with the land brush, `look <place> land <x,y> <radius> <dz>
  --why "<why>"` (eased to nothing at the radius, inside the footprint, within the land bound `fit.patch_max`;
  carried ground is bounded by `draft.ground_cap`). Where a mound would need more, bring the unit down instead.
- **A unit too high or too low**: sink or move it whole (`look sink <unit> [u | --until-feet-buried]`, `look move
  <unit> dx dy dz`); a house's body never moves without its deck. Seat by sinking: nothing is stretched to reach the
  ground.
- After each change read `units --joints` again: every end that met before still meets.
- A flag that faithfully copies the source's own arrangement and reads as built is accepted with what was seen, in
  `place.json` `draft.accepted` `[{unit, flag, why}]` (a probe fault in `draft.accepted_faults`, `place-look`).
- Buried is physical: a piece is buried when nothing of it shows; posts and rock feet in the ground are fine.

- **Change the ground as little as possible.** The world's ground is generated with care; repaint or reshape it only
  where a check, a walk fault or a plain visible fault needs it, in the smallest area that does the job. Never paint
  over the world's ground to tidy it, and where a record's wording is only cosmetic, change the wording
  ([consistency](../../../docs/design/consistency.md)).
- **Ground that reads wrong** (a dry flat still painted as riverbed, a yard that should be bare earth): paint it,
  `look <place> paint textures` for the palette (the land textures the world and the source use here, most used
  first), then `look <place> paint <texture> --polygon x,y;x,y;x,y... [--size 384 --softness 0.6]` for an area,
  `--circle x,y,r` for a patch or `--stroke x,y;x,y;...` along a line, `[--brush soft|hard|scatter] [--strength f]`,
  always `--why "<why>"`; `paint --erase ...` gives the world's own ground back. A texture is named by key, editor id
  or one word of it (`river_mud`, `silt`). Each call is one stroke of the session (`undo` takes it back; `--view
  <view verb>` for a before/after; `commit` writes it to `paint.jsonl`). Choose the source's own texture for what the
  source shows there, else the world's nearest; no more than six textures meet in one 2048-unit quadrant.

Enforced by the checks: nothing floating, nothing buried (`draft check`; `look probe --all`), the build's `seat`,
`overlap` and `land` checks, `seat <place_id>` reporting 0 refs moved.

## 5. Clear the world's plants

`python3 -m tools.places draft clearance <place_id>` clears a world plant rooted inside a placed thing, closer to a
building or door than the source's own plants came, or lying across a walk (`clear.jsonl`; the build's `clear`
check). Run it again after buildings or doors move, then look.

## 6. Pieces kept as they come

The source's own pieces stay as they come, lit or unlit as the source has them. Nordic pieces are judged case by
case: keep one that is nearly fine, take a Tropical Skyrim version or an easy swap where there is one (a piece of
like size and use, `search query "<what it is>"`, swapped by hand: `look delete` the old, `look place` the new at its
pose), never laboriously replace; a piece added from elsewhere that is judged fine gets its looked-at verdict in
`newworld/places/nordic_review.jsonl` (`neutral`, with what was seen), which a copied room and the build's `nordic`
check both follow; Nordic signs (a Doomstone, a word wall, a shrine of Talos) never stand (the build's `nordic` check).
Nothing levelled is ever placed (decision 0035; the build's `levelled` check).
