---
name: place-adapt
description: Adapt a carried source place to what our record says the place is - relabel what serves a new use, prune what only makes sense for the source's kind, move what belongs elsewhere on our ground (boats to our real water), and add what the record and stories need that the source lacks (a building with its rooms from one other source, placed where it can be walked to). Use after the baseline is laid and whenever a source thing does not fit the record.
---

# Adapt to the record

Step 4 of the place path ([place-system](../place-system/SKILL.md)). Before: the baseline fitted to our ground
(`place-site`). After: rooms, walks, people and quest spots (`place-rooms`, `place-streets`, `place-routines`, `place-story`).

The source already works as a place; the adaptation makes it **our** place. Go round it group by group, looking
(`look survey <unit>`, `at`, `at --stand x,y` at eye level), with the record open, and give each group one verdict; record it in `draft.plan` as `kept` (as built, relabelled
or moved, the `why` saying which) or `dropped`.
Write the reason per group in the place's notes.

Work from the promise list (`promises.jsonl`, made by `place-plan`): each row shown `kept`, `relabelled` or
`added` is delivered here, and its `verdict` turns `built` with the refs that show it.

## The verdicts

- **Keep as built**: what the record's look and promises name, or what such a place plainly has. Most of the source.
- **Relabel**: a thing that serves a new use keeps its pieces and gets the new use with its clutter and people's
  spots (a dock across dry mud kept as a low boardwalk; a dock that serves as a market platform). Nothing moves.
- **Prune**: what only makes sense for the source's kind or the record does not support: boats afloat on dry ground,
  fishing markers over mud, a mine, a smelter where the record has no smith, a lived camp's traps, a quest dungeon's
  scripted things, a piece standing inside something we add. `look delete <thing>`; a whole structure goes with its
  doors, rooms and what hangs on it.
- **Move**: what belongs on our ground somewhere else in the place: boats, jetty and weirs to our creek; a shell that
  hides the Hist's pool. A unit moves whole (`look move <unit> dx dy dz`), then is seated (`place-site`).
- **Add**: what the record and stories need that the source lacks: a building and its rooms, a cage, a jar stack, a
  trophy pole, market stalls, a footing rock, a flight of steps (`look steps <deck> <point>`), a single piece (`look
  place <base> <x,y[,z]> [--scale s] --why "<why>"`, `look duplicate <thing> --why "<why>"`). Take additions from the place's own
  source first, then one other source of the same culture; nothing levelled, no Nordic sign. A thing its source
  makes of several models (a ship's hull and its masts and rigging) is added as the source sets it: every model at
  the source's offsets turned with the first, and moved as one after (`draft check` holds them together).

Every keep, move and addition stands off the world's road and the place's walks (`place-streets`, Walks first):
what the source pitched on a line our road now takes moves off it as the unit it is; an addition is sited beside a
walk, never in it.

## A place sharing its source

A place laid after another on the same source carries out its plan's `differs` entry (`place-plan`): its prunes,
additions, dressing and people's spots; `look <place> versus <other>` at hand-over only confirms it.

## An added building

A building the record or a story needs (with its rooms) comes whole from one other source that has it, laid as that
source lays it: a `draft.add` row per piece, the body first and each piece set on it with `on` and `dz` at the
source's offsets and turn, the door carrying its `room` (`place-rooms`).

**Site it by whether it can be walked to**, beside the place and joined to it: its door faces the place, the ground
from its arrival to the nearest walk is no steeper than a walk (a ramp graded with `look land` where a short rise
needs it, its banks dressed with rock), never flat ground the walks cannot reach. After placing it, `look walk
<its door> <the place's middle>` and look from the place at eye level: it reads as part of the place, not out on its
own.

## Every change is tested

After each verdict ask what it could break: a joint that met (`units --joints`), a door that landed, a walk across
it, a person's spot on it, a quest spot by it, the plants it now stands in (`draft clearance`), a road or walk it now
stands in (`look probe --all`, `ways`). Look again from two sides. Commit the session (`look commit -m "<why>"`) group by group.
