---
name: quest-write
description: Design or rewrite an Argonia quest or questline as a record (hidden truth, cast knowledge, things, clues, actions, stages, endings, topics) from the place, culture and quest data, routed to the principles for its shape and line, then build the dialogue briefs from it. Use before any quest dialogue is written, and to rework a quest after review.
---

# Writing a quest

Quests, their dialogue and the world are consistent because they are built from one record in a fixed order
(decision 0024). The record is the imported quest object plus the record's sections:
[quest-record.md](quest-record.md), which also holds the engine-mapping table. The record lives as rows in the
world database (`quest` and its `quest_*` tables, decision 0030); you write its YAML view and import it. Worked
examples, exported from the database: [examples/lh38.yaml](examples/lh38.yaml) (local) and
[examples/mr01.yaml](examples/mr01.yaml) (faction).

Read the world only through the database: `python3 -m tools.argonia_world.db query "SELECT ..."` or `db show <table> <id>` (decision 0030; the tables are described in `../../../docs/design/world/98-data-model.md`). A world file is never opened directly.

## 1. Start from the foundation

- The old quest design is the base (0024 §8). Start from the quest's rows: `python3 -m
  tools.argonia_world.quest_record export <quest id> -o <quest>.yaml` gives the quest object (and the record,
  once one is written) as the YAML view; the `quest_line` row gives its line. Then its design:
  `../../../docs/design/quests/30-main-quest.md`, `../../../docs/design/quests/40-factions.md` (the line's
  section), `../../../docs/design/quests/50-side-quests.md`, or the generated view in
  `../../../docs/design/quests/index/`. Keep its premise, cast and beats; say what changed and why in `foundation`.
- Read the world records the quest stands on: the place's facts (`fact` where `place_id` is the place, in
  `ord` order), the place row (`place` and its `place_*` tables), its last build (`place_build`, `place_person`),
  the people (`npc`, `npc_faction`), their stance (`stance`, `stance_chain`, `stance_topic`) and the culture
  sheets it chains (`culture_sheet`, `culture_entry`, `culture_opinion`), and the other quests at the place and
  its neighbours (`quest` by `settlement`). Two families are not yet tables and are read from the import,
  read-only, until their chunks migrate them: the place's blueprint (`../../../world/sources/blueprints/`, the
  place builds) and the lore dossiers and extrapolation (`../../../world/sources/lore/`).
- **Cast:** a recurring or principal person comes from `../../../docs/design/quests/36-cast-roster.md` (the
  line's desks and its argument, §56; the principal cast, §55; oddities, §58), under the rules of
  `../../../docs/design/quests/35-cast.md`; a placed person is an `npc` row. A person the quest needs who
  exists in neither is an `invented` persona for 2.4 to add, never silently made up.
- For a line, its line record first (`principles/questlines.md`).

## 2. The novelty rule and the shape budget (old 55 §47c, binding)

Before the record is written:

1. **Scan** `../../../docs/design/quests/index/coverage.md` (the commissioning brief: thin shapes, regions
   short of quests), then the index view for the quest's primary shape and region.
2. **Collision test:** the quest collides if it shares its primary shape with an existing quest and any of:
   the same region packet; the same faction line; the same reversal (the twist is the same twist); the same
   resolution set (the same choices). Check secondary shapes and the same place too: LH38 and MR01 share a
   spring, so they may not share a misdiagnosis.
3. **On a collision:** differentiate (the reversal, the claimants, the resolution or the verb), merge it into
   the other quest as a stage or variant, or drop it for something coverage.md shows is missing.
4. **Declare `touches`** (shared people, places, flags, items, variables, read or write) and keep tier
   direction (40-factions §30b): a quest may not write what a higher tier owns.
5. **Shape budget** (strong default; a recorded one-line reason may depart from it): no primary shape over
   about 20% of a line, or of a packet for a quest with no line, and not in consecutive M or L quests. A
   departure goes in the data file's `budgetExceptions`.
6. **Cover the board:** each packet brings a shape new to its region or one from coverage.md's gaps, and at
   least one `WONDER`.
7. **Verb variety:** the `centrepiece` verb tag (00-overview §4) is weighed across the line or packet;
   `SOCIAL` and `INVESTIGATE` may not exceed two thirds of its M and L quests.

## 3. Route to the principles

Read `shapes.yaml`: always `principles/general.md` and `principles/actions.md`; the file for the quest's
`group` (`principles/questlines.md`); the file for each shape (primary first). Each shape names the
`shapeData` sections the record must hold.

| Shapes | File |
|---|---|
| MURDER, MISSING, RECKONING, and THEFT or FRAUD to solve | `principles/investigation.md` |
| THEFT, FRAUD, SMUGGLING | `principles/crime-and-deceit.md` |
| DISPUTE, NEGOTIATION, SUCCESSION, BONDAGE | `principles/social.md` |
| PREDATOR, CONTAMINATION, EXPEDITION | `principles/threat-and-journey.md` |
| HAUNTING, RITE, WONDER, Daedric | `principles/otherworldly.md` |

Also binding from the import: 00-overview §4 (cost tiers S/M/L and their design dimensions, the dramatic
register, the wonder budget, deliverability tiers D-A/D-B/D-C and the cheap patterns, the boredom test),
20-world-provisions (what a quest may ask of the world), and the old ruling that nothing is unkillable (old
0138: every stage that names a person has a fail-forward).

## 4. Write the record in order

1. **Action plan** (`principles/actions.md`): `python3 .claude/skills/quest-write/action_plan.py --profile
   <line key> --shapes <SHAPE,...> --band <D0..D5> --ledger <dir of records in the line or packet>`; choose,
   adapt or write the uses the quest is built round, and the `centrepiece` tag.
2. **Premise** and **truth**: numbered physical events, written so the planned actions follow from them.
3. **Plausibility pass**, person by person; change the truth, never the person.
4. **Facts** the truth creates, each `from` a truth event, a place fact or a culture-sheet entry.
5. **Cast and knowledge** (registry ids; `persona` only for what the registry lacks).
6. **Things**: an existing id or a `new` row the world-builder places.
7. **Conclusions and clues**: three clues per conclusion, two forms at least.
8. **`shapeData`** for each shape.
9. **Stages** in the imported shape (`place`, `journal`, `onEnter`, `objectives`, `successors`,
   `failForward`, `ending`) with conditions and actions only from the vocabulary (`condition_term` rows, with
   their argument shapes; `../../../docs/design/quests/85-condition-vocabulary.md` explains each term; a missing
   term is added as a row first, with its chunk), plus `actions` or `approaches`, `learns`, `directions` and `journalText` (style guide § journal,
   `../../../docs/design/standards/text/style-guide.md`).
10. **Endings**: two or more with real costs, as actions, and where the player sees them.
11. **Topics**: `topic.` ids of `topic` rows or marked `new`; per person
    and stage, the intent, the facts it may state and hide, the links it grants.

## 5. Hand on

1. `quest-review` by a `quest-reviewer` agent that has not seen your reasoning; its findings go in `review`.
2. Revise the record for every finding, or answer it there; set `recordStatus: reviewed`.
3. `python3 -m tools.argonia_world.quest_record import QUEST.yaml` writes the record into the database; it
   refuses the whole record on any unknown field, wrong type, dangling key, unknown lookup value or failing
   named check, and writes nothing then. `--dry-run` checks without writing. Then
   `python3 .claude/skills/quest-write/brief.py <quest id> OUT_DIR` builds one brief per person and a
   journal brief. It reads the record, people, stance, culture sheets, place facts, topics and vocabulary from
   the database, and writes nothing while any reference, vocabulary term, stage field, `shapeData` section,
   catalogue use, fail-forward or ending is missing.
4. `dialogue-write` (the `dialogue-writer` agent) per brief. A fact request comes back here; add the fact and
   rebuild the briefs.
5. The record's rows are the quest's rows (same `id`): there is no second copy to update.
