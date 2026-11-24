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
- A structure (a house with its porch and door, a ship with its masts, a tent with its bedding) is moved, turned or
  raised whole as its unit, one `unit.move` that carries its doors' arrivals, its people's spots and its quest spots
  (`docs/design/place-studio.md`, Units). A piece the unit rule leaves out or takes in wrongly is put right with the
  piece's `unit` (Add to this unit, Take out of this unit), never by moving the pieces one by one.
- A person's spot is moved by dragging the person in the studio (or the stop's Put on map): a stop naming a bed or a
  station moves that thing and every routine naming it follows; a routine is never edited to chase a moved bed.
- In the studio a thing slides along the ground by its middle handle, along one axis by E–W or N–S, up or down by
  Height alone; a nudge of 1, 10 or 50 units is the panel's Move a little.
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
- An owner's row is changed by an agent only to answer him: his note asks for it ("you should fix ..."), or the lead
  decides it. Commit those strokes with `look commit --answers <note id>` (or `--lead "<decision>"`); the studio shows
  him each as changed in answer to that note. Any other stroke on his rows is refused.
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

The owner edits the place in the studio; his work is autosaved as he goes and stays his, open, until he chooses to
save and finalise it (finalise applies it, builds, checks and runs `place-lessons`). Saving and finalising are his
alone: an agent never saves or finalises for him, and nothing an agent does waits for either.

1. Read submitted notes with `python3 -m tools.places notes` (the studio's "submit for agent"; notes he has not
   submitted are his still). Answer each at once with a narrow change by the skill that owns it, landed on main at
   once, and close it with `python3 -m tools.places notes done <place_id> <note id> --reply "<what was done>"` in
   plain English. A question, or a change larger than a narrow one, is closed with a reply saying what it would
   take, and nothing changes. A note still open past its answer time is named by `notes` and fails `handover`.
2. The notes on his changes (the g-notes in his autosave, `notes --changes`) are answered the same way, at once, over
   his open session: work out the change on a copy of his autosave applied to the place (`edits.apply_save` in a
   scratch checkout, never his file, never committed as his), then land it on main as agent edits; a stroke on a row
   his session touched carries the note it answers (`look commit --answers g8`). When he reloads the tab his session
   replays over the new draft: an op of an answered note keeps the answer, any other op of his wins
   (`edits._rebased`, the studio's mirror). A change of his own that a check needs on main (a row he removed or
   moved off a way) is delivered the same way: an answer naming his note makes on the draft what his session makes,
   and his op replays as no change. Nothing is left owed until he finalises.
   - His session is the autosave (`out/places/autosave/<place_id>.json`), which runs on past his last named save.
   - An answer's row is the row as his session leaves it plus the fix. A row his ops touched under several notes is
     answered once per note (`look commit --answers <note>` each; the real change rides the last, the others keep
     the row as it stands), or his ops of an unanswered note replay over it.
   - A person's, path's, walk's or quest spot's row is answered with `look <place> op <file.json>` (the studio's own
     `person.edit` and kin, `before` the row as it is now), then `look commit --answers <note>`.
   - The studio shows the committed place files: commit them by path before judging what he will see.
   - Prove it: `python3 -m tools.places replay <place_id>` replays his autosave over the draft as the studio does;
     it must show no conflict and no row of his moved without an answer, and the rows changed by answers are
     exactly the ones meant. Look at the replayed scene (a scratch worktree with his autosave applied over the new
     draft), never at the draft alone.
3. What the owner changed stays as he left it, his ground paint (`paint.jsonl` rows `by: owner`) too: a stage never
   writes paint, and an agent's repaint is a new stroke over his, never an edit of his rows.

In the studio the owner paints the ground with **Paint ground**: a texture from the palette (pictures and plain names,
the most used here first), a brush (soft round, hard round, scatter, eraser) with its size, softness and strength,
pen pressure widening and strengthening the mark. Each stroke is a `paint.add` op, undone and saved like every edit;
the land in the studio and in `look` captures shows it as the build will lay it.
