---
name: place-research
description: Research places and regions of the new world (Project Tamriel's Black Marsh, newworld/) as they stand in 4E 201 and write their records for the database. Use for a batch of places or regions, whenever a place is added or its research redone.
---

# Research places and regions of the new world

The records are JSON under `newworld/sources/research/` and are built into the database by
`python3 -m tools.newworld.build_db` (each record fills the row its `id` names). The exact record formats, the
grounding sources and the tiers are in `newworld/sources/research/FORMAT.md`; read it first.

## Batch

One researcher per batch of about 30 places, grouped by neighbouring regions, each writing only its own two files:
`places/<batch>.json` and `regions/<batch>.json`. List the batch from the database (`db.open("newworld")`,
`place.region_id` in the batch's regions); read the neighbours outside it for context only.

## For each place

1. Look its name up on UESP (FORMAT.md's API recipe) and in the lore dossiers; a canon page is cited, no page is
   cited as a finding in the overview's sources.
2. Look at its spot on the map (`newworld/sources/maps/PT3-map-Black_Marsh.png`, 40 px a cell; cell (x, y) spans
   px left = 1640 + 40x, top = -1920 - 40(y + 1)): the river or coast, the roads, the neighbours.
3. Read its culture (`research/cultures.json`), its region and its kind (`key.json`), and reason from all of them
   to what it is in 4E 201: who holds it, how many live there, what they live on, what they believe, how it looks,
   what threatens it, what a player finds there.
4. Write the record: every field, every aspect FORMAT.md requires, and its terrain needs. Each note is about this
   place alone, drawn from what is particular to it; no sentence is shared with another place, with only the
   names changed. The overview adds what the summary does not. An unnamed place gets a name in its culture's
   style, unique in the province. Importance: 5 shapes the province, 4 major, 3 regional, 2 local, 1 local colour.
5. Tier and source every note honestly: canon only where a source states it.

## Finish

1. Save after every few places; on a restart continue from what the file holds.
2. Check: no note text appears twice across all research files, nor the same sentence with only names swapped;
   the build runs with no place left unresearched.
3. Text review (the `text-review` skill) by someone other than the writer: reader passes over the exported prose,
   the rewrites applied, then the linter at 0 hard hits.
