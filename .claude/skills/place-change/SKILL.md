---
name: place-change
description: Change a drafted place narrowly - by hand in the studio scene or by the one stage that owns the change, on the place files as they stand, never moving what a hand placed; bring a place level after a world rebuild; and answer the owner's studio notes. Use for every change to a place after its first draft, and for the owner's notes.
---

# Change a drafted place

Step 14 of the place path ([place-system](../place-system/SKILL.md)). The agent that drafted the place makes its
changes (the lead continues it); a change is as narrow as it can be correct.

## By hand, or by the stage that owns it

- A thing to move, turn, sink, prune, add or relabel is done by hand in the studio scene and `look commit`
  (`place-look`), by the recipe of the step that owns it (`place-site`, `place-adapt`, `place-story`).
- A raise or lower of a seated thing (a door on its house, a box on a deck) is the seat's own `dz`: the studio's lift
  handle and Up and Down buttons write it in every seat mode, so `python3 -m tools.places seat <place_id>` keeps it.
- A rule's output is changed by its stage alone: `python3 -m tools.places draft <stage> <place_id>` changes only the
  rows the stage owns, leaves every other row byte for byte and prints the rows changed per file.

| Stage | Run it when | Skill |
|---|---|---|
| `clearance` | buildings or doors moved; the world's plants were placed again | `place-site` |
| `add` | `draft.add` changed | `place-adapt`, `place-rooms` |
| `names` | who lives or works in a room changed; `draft.room_names` changed | `place-rooms` |
| `people` | the people source or the promises changed; a person has no fit base | `place-routines` |
| `jail` | the law, the jail room or its door changed | `place-routines` |
| `lights` | a station was added; a room's lights changed | `place-dressing` |
| `stations` | the record promises a station the files lack | `place-dressing` |
| `hang` | trees round a Hist moved, turned or were swapped | `place-dressing` |
| `sap` | a Hist was added, moved, swapped or died | `place-dressing` |
| `primitives` | kept or pruned pieces changed what a collision box touches | `place-dressing` |
| `quests` | a quest placement at the place was added or changed | `place-story` |

A place drafted before the carried method has further stages of its own until it is redrafted
(`docs/design/place-studio.md`, Stages kept only for drafts awaiting redraft).

Then verify what the change reaches (`place-check`): a hand change to a structure, a door or the ground is followed
by the build and its checks; a stage's counts are the whole change.

## Variants: drafts the owner compares

A place may hold other drafts beside it, `newworld/places/<place_id>@<variant>/`, which the owner opens, edits and
saves in the studio as places and chooses with "Use this version". `python -m tools.places variant list [<place>]`,
`variant use <place> <variant>` (the current draft becomes `previous`), `variant drop <place> <variant>`. A variant
never reaches the built plugin or a gate count. A second way of drafting a place for him to compare is made as a
variant, never over the place.

## A hand's placement is authoritative

- A row a committed agent edit (`agent-edits/`, place.json `agent_saves_applied`) or an owner's finalised save
  moved, turned, sank, dropped, added or edited stands as the hand left it after every stage. A stage that would
  write it otherwise logs one line per row (`<row> (<file>) is placed by hand (<whose edit>): kept as the hand left
  it; the stage would have ...`): look at the row and decide which is right.
- A stroke on an added thing rewrites its `draft.add` row, so the `add` stage places it there.
- `look <place> release <row id> [--space <space>] -m "<why>"` gives a row back to the stages. An owner's row is
  never released by an agent.
- An edit made straight in a refs file is no hand: every placement goes through `look commit`.
- A whole draft on a place holding the owner's finalised saves is refused; it needs `--force "<why no stage can be
  correct>"`, once, with the reason in the commit. A whole redraft only when a narrow change cannot be correct.

## After a world rebuild or single-thing edits

The province's ground is a fixed base that no world rebuild regenerates (skill `world-build`), so a rebuild leaves a
place's ground as it stands; every change to a place's ground is the place's own patch (`land.jsonl`,
`paint.jsonl`, its carried ground), made here and laid by its build. Bring a place level only when
`python3 -m tools.places worldparts <place_id>` names world records that moved under it (a world patch in its
cells, plants placed again, a navmesh rule), in the order of skill `world-build`. After edits of single placed
things, `tools/newworld/rebuild.sh plan` names each place they reach.

## The owner's notes and edits

The owner edits the built place in the studio, saves and finalises a save; finalise applies it, builds, checks and
runs `place-lessons`.

1. Read sent, open notes with `python3 -m tools.places notes` (notes he has not sent are his still). A note about the
   place or selected things is answered with a narrow change by the skill that owns it, and closed with
   `python3 -m tools.places notes done <place_id> <note id> --reply "<what was done>"` in plain English. A question,
   or a change larger than a narrow one, is closed with a reply saying what it would take, and nothing changes.
2. A note on changes travels in its save and is answered by the lessons step when the save is finalised.
3. What the owner changed stays as he left it, his ground paint (`paint.jsonl` rows `by: owner`) too: a stage never
   writes paint, and an agent's repaint is a new stroke over his, never an edit of his rows.

In the studio the owner paints the ground with **Paint ground**: a texture from the palette (pictures and plain names,
the most used here first), a brush (soft round, hard round, scatter, eraser) with its size, softness and strength,
pen pressure widening and strengthening the mark. Each stroke is a `paint.add` op, undone and saved like every edit;
the land in the studio and in `look` captures shows it as the build will lay it.
