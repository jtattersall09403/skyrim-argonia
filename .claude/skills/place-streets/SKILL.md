---
name: place-streets
description: Judge and mend a place's walkable network - streets and walkways joining every door, the landing and every camp; decks, bridges, steps, flights, gangways and door arrivals; patrols on the built navmesh. Use when reading a draft's streets, when a streets check or reach check fails, and when a deck, bridge or door has no way to it.
---

# Streets, decks and doors

Step 4 of the place path ([place-system](../place-system/SKILL.md)). Stage: `streets` (also `join`), which lays
the network, builds the place, reads its navmesh and joins what is cut off, in at most six rounds; its last round
lays every street, stop and patrol on the network as built.

## What the stage lays

- **Streets** join every door, the landing and every camp into one network. Where the source drew a street, ours
  keeps to its line; where it drew none, the link is the easiest going on our ground, winding round trees and rocks,
  in the middle of gaps between buildings, never steeper than the source's streets.
- **What is walked on**: a piece whose model names a walkway (dock, boardwalk, bridge, pier, plank, steps, stair)
  or a flat floor plate (box no taller than 32 units, at least 192 across). A town on a floor has its streets on
  the floor. Decks count as ground.
- **Bridges**: water no deeper than a wade (64 units, `check.WADE`) is waded; deeper water is crossed, where
  nothing else joins the two ends and where it is narrowest, on the source's own walkway pieces (else the style's,
  `io.walkway_base`), each at least 96 across, its deck a hand's breadth over the water.
- **Steps and flights** hang on their deck as Skyrim's dock steps do: square to it, the top tread at the deck's
  height, seated `on` it. A deck the town reaches only by swimming gets one flight from a free edge down to where the
  network walks; a deck below the town's (a ship under its quay) gets one flight down onto it, carried by the
  ship; a deck below a steep bank gets one flight up to the bank's top. Steps come from the source, else the deck
  pieces' own kit (`place.json` `steps.kit`).
- **Gangways**: a door still on an island is joined by level walkway pieces along a clear line to the nearest point
  of the network, at most 768 units. A first draft leaves out a door no join reaches whose room has no resident or
  worker; on a drafted place the stage lists such an island and never takes a room out.
- **Door arrivals** stand on the network at their own level; work stops and outdoor day stops are moved onto it.
- **A door and its arrival are one thing**: an arrival moved by hand or with its door keeps its partner door's landing (`to_pos`) at the same point; a door moved by an edit carries both, and `streets` re-seats the arrival on the walkable ground before it.
- **Patrols** are taken from the streets, each point on the network and out of the water, at least two points.

## Read the network

Every walked span's ends first: `python -m tools.places units <place> --joints` gives one row per end (foot and head,
or two ends) with what its end line meets, the gap past it (`along`) and in height (`dz`) and the verdict (meets,
rests on ground, on its own legs, short of, step to, buried end, mid-air), then any house or stair standing on a
span, spans of two structures overlapping and walls crossing a span. An end not meeting is a walk that breaks.

1. Look at every street close up, not only the whole-town render: `look walk <door> <door>` along it, `look at`
   on each bridge, flight and gangway, `look section` across each deck end.
2. A straight run longer than a few houses, a line beside a deck and not on it, a bridge ending on an empty bank,
   many bridge pieces where the source had none, or a bridge with one support means the anchor, the turn or a
   cluster's spot is wrong. Put that right (`place-site`) and run `streets` again; never accept the line.
3. A crossing whose banks have no deck (a ford between steep banks) is named in the hand-over and the world's
   ground changed first (skill `world-build`).

## A failed streets check

`draft check` and the build's `streets`, `doors` and `navmesh` checks list a street or patrol point off the
network, a door off a path, a stretch that moved when mended again. Read the list in
`out/places/shards/<place_id>/check_failures/<check>.txt` and `python3 -m tools.places check <place_id> --reach
[person]` (what is cut off from what). Mend the cause: a cluster's spot (`place-site`), a missing walkway piece, a
door's room; then one `streets` run. The stage takes 10 to 40 minutes: commit first, run it under
`tooling/job_guard.sh`, and edit nothing of the place (look session, quest spots) until it ends, since it rewrites
those files.

A door or deck the check calls an island: `look <place> probe --mesh <door> <x,y,z on the street>` names the
island its door triangle is on and, when a walk does not join the two, where the mesh breaks (a height step, a
missing strip, the pieces there); `look <place> at <structure> --top --mesh` and a `section ... --mesh` across the
deck edge show it. A door whose triangle is on a roof island while its deck is green (the main network) has its
arrival off the deck: put the door's `arrival` on the deck (the build lands one there); a deck that is its own
island needs a flight or a gangway; a flight whose top stands a step over or under the deck is seated again.

Enforced by the checks: streets clear of buildings and open water, every door on a path, every arrival clear and on
dry ground or a deck, every street and patrol point on the main walked network (`draft check`; the build's
`streets` check); the overlap rule for laid pieces (`overlap`).
