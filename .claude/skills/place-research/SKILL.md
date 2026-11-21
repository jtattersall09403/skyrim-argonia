---
name: place-research
description: Research places and regions of the new world (Project Tamriel's Black Marsh, newworld/) as they stand in 4E 201 and write their records for the database. Use for a batch of places or regions, whenever a place is added or its research redone.
---

# Research places and regions of the new world

The records are JSON under `newworld/sources/research/` and are built into the database by
`python3 -m tools.newworld.build_db` (each record fills the row its `id` names). The exact record formats, the
grounding sources and the tiers are in `newworld/sources/research/FORMAT.md`; read it first. The record is the
first step of the work on a place: the order is in the skill `place-system`.

## Batch

One researcher per batch of about 30 places, grouped by neighbouring regions, each writing only its own two files:
`places/<batch>.json` and `regions/<batch>.json`. List the batch from the database (`db.open("newworld")`,
`place.region_id` in the batch's regions); read the neighbours outside it for context only.

## For each place

1. Look its name up on UESP (FORMAT.md's API recipe) and in the lore dossiers; a canon page is cited, no page is
   cited as a finding in the overview's sources.
2. Look at its spot on the map (`newworld/sources/maps/PT3-map-Black_Marsh.png`, 40 px a cell; cell (x, y) spans
   px left = 1640 + 40x, top = -1920 - 40(y + 1)): the river or coast, the roads, the neighbours.
3. Read its source places before writing a word (`python3 -m tools.newworld.place_card --mined <place>`): what the
   main source and its alternates hold (buildings, each interior by what it is, doors, water, containers) and their
   rough layout. The place is built from them, so the record describes what they can become.
4. Read its culture (`research/cultures.json`), its region and its kind (`key.json`), and reason from all of them
   to what it is in 4E 201: who holds it, how many live there, what they live on, what they believe, how it looks,
   what threatens it, what a player finds there. No place is invented from nothing: where canon is silent, the
   place follows by extrapolation from the lore, its kind, its culture, its region and its neighbours on the map.
   A neighbouring province may be drawn on with the reason (a wreck out of Morrowind, Cyrodiil, Elsweyr or
   Valenwood). Every extrapolation agrees with the one story and timeline in `story/lore/extrapolation/`.
5. Write the record: every field, every aspect FORMAT.md requires (its `source` note among them), and its terrain
   needs. Every sentence of the summary, notes and gives passes the deliverability test (FORMAT.md, Deliverable in
   Skyrim): Skyrim and our mods can show or do it with at most a small addition (a thing placed, a person, a lock);
   every structure it names is in the sources or named in the `source` note as added, from which mod's pieces; it
   agrees with the record's `siting` and with the ground: a water word (river, creek, lake, sea, docks, boats,
   fishing) names water the ground has within a few hundred metres of the place, and the `siting` names the water
   nearest it. A Hist pool is always a pool of Hist sap, never of water. The population is the researched estimate
   inside the tier's range and, for a village or larger, in order with its peers (FORMAT.md, Population). A source holds a structure when its placed pieces or interiors show it, not
   when its style tags suggest it, and the `source` note says so as a plain sentence naming the source and the
   evidence ("Bonestrewn Grove, from King of the Murkmire, has cypress walkways on posts and two hide tents"),
   never a command or an id. The `source` note is a first-idea build plan that agrees with the allocated source
   (rank 0 of the place card): it names that source and what it gives (layout, which interior serves as what),
   what is dropped, what is replaced with which pieces (a Nordic piece where an easy swap exists), and ends "Still to add: ...". When
   the allocated source gives little, the note says the place is built "from the pool", what the source still
   gives, and which pieces of the pool make the rest. It never says the source does not fit or that another
   source fits better; a better source is taken by `python -m tools.places sources-match --pin` (its `JUDGED`
   table) or its pieces are named as pool pieces. A source may serve several places; each is adapted
   differently, and the note says how this place differs from the others built from the same source. Sharing
   a source is never counted against it; each place on it is adapted to feel its own (place-plan, "Choose the
   source by looking"), and the cheapest change that makes a place fit is made first. Check: `pytest tools/tests/test_newworld_source_note.py`. Each note is about this
   place alone, drawn from what is particular to it; no sentence is shared with another place, with only the
   names changed. The overview adds what the summary does not. An unnamed place gets a name in its culture's
   style, unique in the province. Importance: 5 shapes the province, 4 major, 3 regional, 2 local, 1 local colour.
6. Carry Argonian life in what Black Marsh's own lore uses: the Hist, eggs, trade by water, raiding, ruins,
   beasts, kin, memory kept in speech and carving. Black Marsh is not a place of ledgers, rolls, registers,
   tallies and counts, and no place's life or play turns on them; a document appears only where it is natural (an
   outsider's papers).
7. List what the place gives the player as `gives` (FORMAT.md, Gives): hard gameplay, never local colour, from
   the whole range Skyrim's places give, several kinds and several of a kind where the place has them. A fight
   always names its reward. A note or a give promises only what Skyrim's own systems deliver (FORMAT.md,
   Deliverable in Skyrim). The gives fit the place: a hostile or abandoned place offers no service (no trader,
   bed, trainer, blessing or fence); a place holds one loot store, and a further store only as the reward of its
   own fight; a trade or an inn needs people to run it; an ore vein needs a mine, quarry, pit or seam the record
   names.
8. Give a settlement no hostile occupants and no other place (a village, a camp, a ruin) folded inside it: its
   extent contains only its own people and buildings. A friendly settlement gives no fight against people, inside
   or near it: the raiders at its landing, the robbers on its road and the haunted cellar under it are named in
   its `dangers` note, and a quest that needs the fight brings it. A wary settlement's fight inside lives in a
   dungeon-like interior of it: a cellar, a sewer, a vault, a drowned under-layer, as Riften keeps its thieves in
   the Ratway. A wary settlement's fight just outside it is an encounter near it: the combat give
   names `setting: nearby`, the `spot` in the record's own words, and a `bearing_deg` and `distance_m` from the
   place's centre that put it beyond its footprint (the footprint plus about 80 m, toward the water, road, pass or
   neighbour the spot names), and its reward give is marked `nearby` too. A separate village or ruin near a
   settlement is its own place record, or nothing. A settlement's own fight names where it lives (`setting`:
   `interior`, or `provoked` for its own people who fight only when provoked); wildlife in its waters is a
   creature fight and needs none. An outpost or camp
   whose people attack on sight is a hostile place, not a settlement with foes.
9. Set the danger as fixed geography (`docs/design/danger.md`). A place has four danger facts: its ground, its
   disposition, the strength inside and its reward band. You write one field, `danger_band_id`, the strength of
   what lives inside: for a lived place, the band of the country round it (people of lethal land are formidable),
   never calmer because the place is settled; for a ruin, camp or lair, at least that band and one worse for a
   boss or foes in a dungeon, cave or wreck; a city or town D0, the safe band. `build_db` derives the ground, the disposition,
   the way in, the reward band and each nearby encounter's band (at least the ground where it stands, one worse
   for a boss) from the record and the ground, each with its reason
   (`python3 -m tools.newworld.place_danger show <place>`). A loot give's detail says where and what kind of store
   it is, never its tier: the tier is the reward band's.
10. Travel is the network's (`docs/design/travel-network.md`, which holds how a network is authored). A place
   promises travel only as a stop of it: a `boat-stop`, `coach-stop` or `rootworm-stop` give whose detail says who
   serves it and where (raft-masters at the city landing), with the stop and its routes in
   `newworld/sources/travel/network.json`; a stop only where the ground carries the mode (navigable water, a major
   road, a Hist) and the place's trade or lore runs it. No place promises map fast travel. A place that is no stop
   promises no travel; the network says how one reaches it, or why it is remote.
11. Tier and source every note honestly: canon only where a source states it.

## Finish

1. Save after every few places; on a restart continue from what the file holds.
2. Build (`python3 -m tools.newworld.build_db`) and check: no note text appears twice across all research files,
   nor the same sentence with only names swapped; the build runs with no place left unresearched;
   `python3 -m tools.newworld.place_danger check`, `python3 -m tools.newworld.travel check` and
   `python3 -m tools.newworld.record_check` (the consistency checker's place rules: population against its tier and, for villages and up, its peers, water words and siting against the
   ground, Hist pools as sap, and the gives against the disposition: no fight against people at a friendly lived
   place, no service at a hostile or abandoned one, a second loot store only as a fight's reward, a trade only
   with people, an ore vein only with a mine) show 0 problems. A water fault is fixed in the record's words, never by moving the place.
3. Text review (the `text-review` skill) by someone other than the writer: reader passes over the exported prose,
   the rewrites applied, then the linter at 0 hard hits.
4. Whenever the places or the travel network changed, rebuild the Atlas
   (`~/.argonia/venv/bin/python -m tools.newworld.map_page`), publish `out/newworld/map/index.html` to
   the url in `tools/newworld/atlas.json` with the Artifact tool (index.html alone unless the terrain or water
   changed), then `python3 -m tools.newworld.atlas_state mark-published`.

## Change a record narrowly

A record that is already built on (a drafted or stocked place) is edited fact by fact: change the one field, note
or give, with the reason in the commit, and rebuild. A promise the place's builders cannot deliver is dropped or
changed only here, case by case, as the owner rules, never to avoid the work. After a change, the skills that
read the fact apply it by their own narrow step (`place-change`, `place-people`, `place-stock`).
