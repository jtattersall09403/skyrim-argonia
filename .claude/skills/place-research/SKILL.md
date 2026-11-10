---
name: place-research
description: Research places and regions of the new world (Project Tamriel's Black Marsh, newworld/) as they stand in 4E 201 and write their records for the database. Use for a batch of places or regions, whenever a place is added or its research redone.
---

# Research places and regions of the new world

The records are JSON under `newworld/sources/research/` and are built into the database by
`python3 -m tools.newworld.build_db` (each record fills the row its `id` names). The exact record formats, the
grounding sources and the tiers are in `newworld/sources/research/FORMAT.md`; read it first. The record is the
first step of the work on a place: the order is at the top of the skill `place-build`.

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
   what threatens it, what a player finds there. No place is invented from nothing: where canon is silent, the
   place follows by extrapolation from the lore, its kind, its culture, its region and its neighbours on the map.
   A neighbouring province may be drawn on with the reason (a wreck out of Morrowind, Cyrodiil, Elsweyr or
   Valenwood). Every extrapolation agrees with the one story and timeline in `story/lore/extrapolation/`.
4. Write the record: every field, every aspect FORMAT.md requires, and its terrain needs. Each note is about this
   place alone, drawn from what is particular to it; no sentence is shared with another place, with only the
   names changed. The overview adds what the summary does not. An unnamed place gets a name in its culture's
   style, unique in the province. Importance: 5 shapes the province, 4 major, 3 regional, 2 local, 1 local colour.
5. Carry Argonian life in what Black Marsh's own lore uses: the Hist, eggs, trade by water, raiding, ruins,
   beasts, kin, memory kept in speech and carving. Black Marsh is not a place of ledgers, rolls, registers,
   tallies and counts, and no place's life or play turns on them; a document appears only where it is natural (an
   outsider's papers).
6. List what the place gives the player as `gives` (FORMAT.md, Gives): hard gameplay, never local colour, from
   the whole range Skyrim's places give, several kinds and several of a kind where the place has them. A fight
   always names its reward. A note or a give promises only what Skyrim's own systems deliver (FORMAT.md,
   Deliverable in Skyrim).
7. Give a settlement no hostile occupants and no other place (a village, a camp, a ruin) folded inside it: its
   extent contains only its own people and buildings. Danger inside a city or town lives in a dungeon-like
   interior of it: a cellar, a sewer, a vault, a drowned under-layer, as Riften keeps its thieves in the Ratway.
   Threats outside it (raiders on the road, beasts in the channels beyond) belong to the ground round it or to the
   neighbouring place that holds them. A separate village or ruin near a settlement is its own place record, or
   nothing. A settlement's own fight names where it lives (`setting`: `interior`, or `provoked` for its own people
   who fight only when provoked); wildlife in its waters is a creature fight and needs none. An outpost or camp
   whose people attack on sight is a hostile place, not a settlement with foes.
8. Set the danger as fixed geography (`docs/design/danger.md`). A place has four danger facts: its ground, its
   disposition, the strength inside and its reward band. You write one field, `danger_band_id`, the strength of
   what lives inside: for a lived place, the band of the country round it (people of lethal land are formidable),
   never calmer because the place is settled; for a ruin, camp or lair, at least that band and one worse for a
   boss or foes in a dungeon, cave or wreck; a city or town D0, the safe band. `build_db` derives the ground, the disposition,
   the way in and the reward band from the record and the ground, each with its reason
   (`python3 -m tools.newworld.place_danger show <place>`). A loot give's detail says where and what kind of store
   it is, never its tier: the tier is the reward band's.
9. Travel is the network's (`docs/design/travel-network.md`, which holds how a network is authored). A place
   promises travel only as a stop of it: a `boat-stop`, `coach-stop` or `rootworm-stop` give whose detail says who
   serves it and where (raft-masters at the city landing), with the stop and its routes in
   `newworld/sources/travel/network.json`; a stop only where the ground carries the mode (navigable water, a major
   road, a Hist) and the place's trade or lore runs it. No place promises map fast travel. A place that is no stop
   promises no travel; the network says how one reaches it, or why it is remote.
10. Tier and source every note honestly: canon only where a source states it.

## Finish

1. Save after every few places; on a restart continue from what the file holds.
2. Build (`python3 -m tools.newworld.build_db`) and check: no note text appears twice across all research files,
   nor the same sentence with only names swapped; the build runs with no place left unresearched;
   `python3 -m tools.newworld.place_danger check` and `python3 -m tools.newworld.travel check` show 0 problems.
3. Text review (the `text-review` skill) by someone other than the writer: reader passes over the exported prose,
   the rewrites applied, then the linter at 0 hard hits.

## Change a record narrowly

A record that is already built on (a drafted or stocked place) is edited fact by fact: change the one field, note
or give, with the reason in the commit, and rebuild. A promise the place's builders cannot deliver is dropped or
changed only here, case by case, as the owner rules, never to avoid the work. After a change, the skills that
read the fact apply it by their own narrow step (`place-build` section 7, `place-people`, `place-stock`).
