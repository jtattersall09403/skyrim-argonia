---
name: place-change
description: Change a drafted place narrowly - run only the draft stage that owns the change on the place files as they stand, bring a place level after a world rebuild or single-thing edits, and answer the owner's studio notes, never moving what the owner changed. Use for every change to a place after its first draft, and for the owner's notes.
---

# Change a drafted place

Step 13 of the place path ([place-system](../place-system/SKILL.md)).

## The stage that owns it

`python3 -m tools.places draft <stage> <place_id>` runs one stage on the place files as they stand. It changes only
the rows it owns, leaves every other row byte for byte, never changes a row a finalised studio save touched, and
prints the rows changed per file; a stage that would write outside what it owns fails. A single piece or structure
that must move, turn or sink is done by hand in the studio scene and `look commit` (`place-look`).

| Stage | Run it when | Skill |
|---|---|---|
| `fit` | a piece belongs in another cluster | `place-site` |
| `pieces` | `draft.replace` or `draft.drop` changed; the record named or stopped naming a source site | `place-site` |
| `seating` | a seat rule changed | `place-site` |
| `clearance` | buildings, doors or streets moved; the world's plants were placed again | `place-site` |
| `streets` (`join`) | pieces, doors or stations changed | `place-streets` |
| `add` | `draft.add` changed | `place-rooms`, `place-story` |
| `names` | who lives or works in a room changed; `draft.room_names` changed | `place-rooms` |
| `people` | the people source or the promises changed; a person has no fit base | `place-routines` |
| `jail` | the law, the jail room or its door, the landing or the streets changed | `place-routines` |
| `lights` | stations were added; a room's lights changed | `place-dressing` |
| `stations` | the record promises a station the files lack | `place-dressing` |
| `hang` | trees round a Hist moved, turned or were swapped | `place-dressing` |
| `sap` | a Hist was added, moved, swapped or died | `place-dressing` |
| `primitives` | the source bundle, the kept pieces or the primitive classes changed | `place-dressing` |
| `quests` | a quest placement at the place was added or changed | `place-story` |

1. Make the change (`place.json` `draft`, the people source, a rule of the tools).
2. Run the stage and read its counts: they are the whole change. Run `streets` when what the network is built from
   changed, then the checks (`place-check`).
3. A whole draft on a place holding the owner's finalised saves is refused; it needs `--force "<why no stage can be
   correct>"`, once, with the reason in the commit.
4. After a world rebuild, bring a place level only when `python3 -m tools.places worldparts <place_id>` names world
   records that moved under it, in the order of skill `world-build`, section 7.
5. After edits of single placed things, `tools/newworld/rebuild.sh plan` names each place they reach: a place whose
   `clear.jsonl` holds a row for an edited thing loses that row and is built again; a place whose cells hold an edit
   has its ground bundle extracted again and is built.

## The owner's notes and edits

The owner edits the built place in the studio, saves and finalises a save; finalise applies it, builds, checks and
runs `place-lessons`.

1. Read sent, open notes with `python3 -m tools.places notes` (notes he has not sent are his still). A note about the
   place or selected things is answered with a narrow change by the stage or skill that owns it, and closed with
   `python3 -m tools.places notes done <place_id> <note id> --reply "<what was done>"` in plain English. A question,
   or a change larger than a narrow one, is closed with a reply saying what it would take, and nothing changes.
2. A note on changes travels in its save and is answered by the lessons step when the save is finalised.
3. What the owner changed stays as he left it: no stage or later pass moves, renames or removes a row a finalised
   save touched.
