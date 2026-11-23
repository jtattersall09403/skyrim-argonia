---
name: place-streets
description: A place's walking - the world's road and every walk kept clear, the source's own walking mesh carried by the build, what each hand change (delete, move, add, land brush) does to it, spurs and flights to what is added, carried walks and patrols, and how to read a streets, doors, navmesh or reach failure. Use when a walk, door arrival or patrol is judged, when something stands in a road or a walk, when a streets, doors or navmesh check fails, and when something added needs a way to it.
---

# Walks and the walking mesh

Step 6 of the place path ([place-system](../place-system/SKILL.md)).

## Walks first, then everything keeps off them

A place's ways are laid first and kept clear: the world's road through it as the ground paints it, each street,
path, walkway, boardwalk and gangplank of its own (`paths.jsonl`), and the way from each door's arrival to the
nearest of them. Everything else (buildings, tents, fires and cooking gear, stalls, furniture, crates, reed and
wood stacks, rigging, trees, a creature's quest spot, a person's fixed stop) stands off them, across the way's
walking width and a shoulder, from a step's height to a head's (`tools/places/ways.py`). A thing stands in a way
only when it is meant to stop traffic, and then it says so: `blocks_way` on the ref ("a toll gate that stops the
road"), or the path's `blocked_by` {id: reason} ("a barricade the quest clears", "the jetty's mooring posts either
side of its deck").

- A thing stands in a way where the built walking mesh runs under it: a fence, rail or post the mesh goes round is
  the walk's edge, a surface the mesh runs on is walked on, a tree blocks with its trunk and roots only, and hanging
  things, ground pieces, moss, ferns and vines never block. `look <place> probe --all` lists what stands in a way
  under `ways` (before a build, by the way's width alone), each with the point to look at; the build's `streets`
  check (and so `draft check`) fails it.
- The blockers found when the check came in are owed (`newworld/places/ways_owed.jsonl`): reported, not failing,
  until the place's agent clears each (the row then goes: a row that names no blocker fails until deleted, and no
  row is added). `handover` passes only with none owed, or each with its reason (`why`).
- Move a blocker off as the unit it is: a tent with what is in it (its bedrolls, chests, rugs, lights, markers and
  floor platforms), a camp's fire with its spit, pot, seats and the stall that serves it, a stack with its pieces.
  Move them by the same shift, onto dry ground level enough for them, out of every other solid thing, as near as
  it can be to where it stood (or where the owner left it), and keep what the record says of it true (a cook still
  at her fire, the fire still among the tents); when the words cannot stay true, they follow (the consistency
  ladder). A world tree or rock in the way is cleared (`clear.jsonl`); never repaint or reshape the road to suit.
- A walk that a stack, a fire or a tent now fills is laid again round it, over clear ground, never through it; a
  walk to a door starts at the door's own arrival.
- A way over a ship's rail, a jetty's end or a stair keeps the walk the source gives it (a jetty laid level with a
  ship's rail as the source moors it); where a source's own pieces stand at a way's edge (posts either side of a
  jetty), they are allowed on the path with that reason.

## The source's mesh is the place's

With `place.json` `wholesale.navmesh: "source"` (`place-site`), the build writes the source's own walking mesh
inside the footprint at the place's one transform and generates only round it and where the place was changed by
hand (`docs/design/place-studio.md`, Build, Navmesh). The walks carried with `draft wholesale --walks` and the
source's patrols run on it, so nothing is laid for them. A hand change does this to it:

- **The owner's walking zones** (`walk.jsonl`: No walking here, Walk here, Join these) are authoritative, like hand
  placement: the build applies them on every rebuild; never route a street, patrol or arrival through a block zone,
  nor move or delete a zone.
- **Delete a source piece**: the build drops the triangles over its outline (grown by 64) and meshes that spot from
  what stands there now.
- **Move a piece or a unit**: its own triangles go with it when they meet the mesh round its new spot; else the
  build meshes it where it stands.
- **Add something** (a building, a flight, a deck): the build meshes its outline and joins it to the carried mesh.
  Give it a way to the walk it serves: a flight from its deck (`look steps <deck> <point>`), a ramp graded with
  `look land`, a short walkway; an added door's arrival on that way.
- **Brush the land** (a mound, a bank): carried ground vertices follow our ground; a triangle made steeper than 45
  degrees is meshed again (the build's `nav.seam.carried.steep` counts them).

A door's triangle is the carried one under its arrival; the build notes an arrival more than a step (64) from the
mesh.

## Walks, patrols and spots

- Walks are the source's, carried as path rows; a walk to an added building is a spur from the nearest carried walk
  to its arrival (a `paths.jsonl` row the drafter adds, its points on the walked surface). Where the source's own mesh
  is unlinked patches and gives no walk, route each door's walk over the place's BUILT mesh (after a build), from the
  door's landing along the mesh's own portals, and key the row's `from` as the check keys the door (its `src`, else
  its id). A walk is painted onto the ground by its style; `trodden` paints nothing: the world's ground is repainted
  only where a check, a walk or a plain fault needs it, never to tidy it.
- Patrols are the source's own marker chains, kept where they still run on our place; a chain across water or a
  pruned part is redrawn by hand along the walks (`people.jsonl` `patrol`, at least two points).
- Work stops and day spots stand on the mesh (`place-routines`).

## Read it

After the build: `look <place> probe --mesh` (islands, doors and street points off the main network, by the build
check's own rule), `look <place> probe --mesh <a> <b>` (why two points do not join: the height step, the missing
strip, the pieces there), any view with `--mesh`, `look <place> playwalk`. `units <place> --joints` names every span
end that does not meet.

## A failed check

The build's `streets`, `doors`, `navmesh` and `people` checks list a walk or patrol point off the network, a door off
a path, an island. Full lists: `out/places/shards/<place_id>/check_failures/<check>.txt`; `python3 -m tools.places
check <place_id> --reach [person]` says what is cut off from what. Mend the cause: a flight or ramp missing to an
added thing, an arrival off its deck (put it on the deck), a moved unit whose ends no longer meet, a patrol point
over pruned ground. A finding seen to be right is accepted (`place-check`).

Enforced by the checks: every door on a path, every arrival clear and on ground or a deck, every walk and patrol
point on the main walked network, and the road and every walk clear of solid things and spots
(`draft check`; the build's `streets`, `doors`, `navmesh` and `people` checks).
