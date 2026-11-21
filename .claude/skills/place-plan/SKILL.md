---
name: place-plan
description: Start a place draft of the new world - read the place record as the brief, choose the source place, read the source's character, write draft.plan (look, gives, structures) and judge each source structure kept or dropped against the record. Use before a place's first draft, and again when its source or plan changes.
---

# Choose the source and write the plan

Step 2 of the place path ([place-system](../place-system/SKILL.md)). Before: the record (`place-research`). After:
the whole draft, judged stage by stage (`place-site` onwards).

## Inputs

- The record, read whole before any draft and before any change: `python3 -m tools.newworld.place_card
  <place_id>` (summary, `look`, people, `gives`, dangers, hooks, the `source` note). In the database
  (`db.open("newworld")`): `place`, `place_give`, `place_source` (rank 0 is the allocated source, 1 to 3 the next
  most similar), `source_place`.
- `place.json`: `place_id`, `source_id`, `similar`. A source place is a row of `newworld/places/sources.jsonl`
  (hand-written) or `sources_mined.jsonl` (`tools.places sources-match`).
- The bundles under `out/places/bundles/`: `python3 -m tools.places source <place_id>` (or `extract
  <source_id>`) writes `src.<source_id>`; `extract --ground <place_id>` writes `ground.<place_id>`, which must
  stand on the deployed world file (`ground-check <place_id>` passes; the world is settled first, skill
  `world-build`). The ground bundle and the build stamp the world records they read; `worldparts <place_id>` names
  what moved under a place.
- Skyrim's town rules: `docs/research/skyrim/town-life.md`.

## 1. Choose the source

The record's `source` note and the allocated source are a first idea, not a ruling.

1. Look at the best three or four candidates as places (the card's `source 0..3`, `python3 -m tools.places
   sources-match`, the catalogue search), each in its own ground with the place's footprint drawn:
   `python -m tools.places look --source <source_id> survey --ring <radius_m>` (the whole-place sheet), `section`
   through its relief, and `units --ring <radius_m>` for what it holds inside the ring. Judge each against the
   record: style and materials, layout (water, banks, streets), buildings and interiors, size, what would be pruned
   and added, how much of its ground to bring. Take the one that already looks most like the record, so the draft is
   mostly kept pieces: within the footprint, over half its pieces kept as built, and the quests' rooms present or
   cheap from one other source. A place the main quest uses always gets its closest match.
2. A source may serve several places, each taking a different part, layout or adaptation; the plan says how this
   one differs. Many places on one source are not fine; where another good source of the kind fits after a light
   re-authoring of one record, the second place moves to it.
3. When something must change to fit, change the cheapest thing with the fewest knock-on effects: a source note,
   then a minor record, before a main-quest text or a drafted place. Where the record clashes with the ground, the
   record changes; the place is not moved.
4. When no source is close (most buildings would be replaced), build from the whole asset pool, taking only what a
   source gives cheaply (a street layout, interiors with furniture and navmesh), and say so in the plan.
5. Pin the choice with `python -m tools.places sources-match --pin <place>` (its `JUDGED` table), never by hand;
   the reason goes in the plan.

## 2. Read the source's character

1. `python3 -m tools.places draft <place_id>` once with an empty `draft` block, then `draft render <place_id>`;
   look at `out/places/renders/<place_id>/source.png`, and at the source in the studio scene (`place-look`).
2. Name in a few lines: where its water is and what stands in it; how its streets run between the doors; which
   buildings are entered and where they lead (`place.json` `fit.clusters_info`, `ledger.jsonl`); how close its
   plants come to buildings, streets and doors (`place.json` `clearance`).

## 3. Write draft.plan

Write `draft.plan` before the first stage runs. Its one shape (`tools/places/draft/plan.py`):

```
{source, look: [{line, by}], gives: [{kind, by}],
 structures: [{cluster | structure, what, verdict: kept|dropped, why}]}
```

- `source`: which source and why.
- `look`: a row for each thing the record's look names (each building kind, the water and what stands in it, the
  market, the shrine, the racks, the materials), with the source or added pieces that deliver it. The `source`
  note's replacements are done whole ("houses replaced with stilt huts" swaps every house shell).
- `gives`: a row for each promise of the record, by its kind.
- `structures`: a row for each major source structure (by its class from `draft structures`) and each source
  cluster with a standing building (by its cluster ids, comma-separated).

`python -m tools.places draft plan <place_id>` prints the plan's faults; `draft check` and the consistency checker
fail on the same ones.

## 4. Judge each source structure

`python -m tools.places draft structures <place_id>` lists each major structure (walls, terraces, keeps, mines,
caves, harbours, temples, forts) with its pieces. Keep one only when the record names it or it is an ordinary part
of such a place; otherwise drop it with its doors, rooms and pieces (`draft.drop` `{source ref id: reason}`, the
`pieces` stage). A source site the record never names (a mine, a cave, a crypt) is left out by the tools with its
door, room and mouth. A kept structure stays whole: body, deck, steps, what hangs on it and the bridges that bind
it.

The source brings nothing the record does not promise: the `pieces` stage drops traps and hazards a friendly
place's dangers do not name, loot containers beyond the record's treasure count, and every Nordic sign (a
Doomstone, a word wall, a shrine of Talos); `draft check` and the build's `nordic` check fail one that stands. A
source piece the record needs, or that such a place plainly has (a town's general trader), stays.

## 5. Plan the layout

Once the source sits on our ground, plan every unit's height for the place as a whole before seating any by hand:
`python -m tools.places units plan <place_id>` (the units are in `place-site`). It first puts each unit back
together at its source's own relative levels (its `reassemble` per piece), then gives each one vertical offset so
that its floor or deck stands over the highest ground under it (30 units; a stilt house's deck 60), every foot is in
the ground by at least 16 units and never deeper than its leg, every door stays on its floor, every walkway end
meets what it rests on within a step and steps reach the ground. Joined units are solved together for the least
movement. Where no offset seats a unit on its ground, the plan says so and gives, in order, a spot within the place
where it fits and keeps its joins, else the joins it would give up; it never changes terrain or water, moves the
place or stretches a piece.

Apply the plan unit by unit in the studio (`look move <unit> 0 0 <dz>`), look at each, and decide each unit the plan
could not seat: a better spot, a dropped join, or a structure left out.

## 6. The draft is finished only when it reads as the record

A check that passes on a place that does not look like its record is not finished. The look is judged in
`place-look`.
