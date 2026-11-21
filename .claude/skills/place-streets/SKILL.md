---
name: place-streets
description: A place's walking - the source's own walking mesh carried by the build, what each hand change (delete, move, add, land brush) does to it, spurs and flights to what is added, carried walks and patrols, and how to read a streets, doors, navmesh or reach failure. Use when a walk, door arrival or patrol is judged, when a streets, doors or navmesh check fails, and when something added needs a way to it.
---

# Walks and the walking mesh

Step 6 of the place path ([place-system](../place-system/SKILL.md)).

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
  to its arrival (a `paths.jsonl` row the drafter adds, its points on the walked surface).
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
point on the main walked network (`draft check`; the build's `streets`, `doors`, `navmesh` and `people` checks).
