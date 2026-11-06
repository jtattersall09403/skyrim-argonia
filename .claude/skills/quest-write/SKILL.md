---
name: quest-write
description: Design or rewrite an Argonia quest or questline as a record (hidden truth, cast knowledge, things, clues, actions, stages, endings, topics) from the place, culture and quest data, routed to the principles for its shape and line, then build the dialogue briefs from it. Use before any quest dialogue is written, and to rework a quest after review.
---

# Writing a quest

Quests, their dialogue and the world are consistent because they are built from one record in a fixed order
(decision 0024). The world is Black Marsh & Valenwood's (BM&V, an existing mod), not our old generated places:
a quest is written as a record here, then built as Creation Kit/xEdit-style records (quest, dialogue, aliases,
placed or changed NPCs, items, creatures) on top of BM&V. The record is the imported quest object plus the record's sections:
[quest-record.md](quest-record.md), which also holds the engine-mapping table. The record lives as rows in the
story data in `story/data` (`quest` and its `quest_*` tables, decision 0030); you write its YAML view and import it. Worked
examples, exported from the database: [examples/lh38.yaml](examples/lh38.yaml) (local) and
[examples/mr01.yaml](examples/mr01.yaml) (faction).

Read the world only through the database: `python3 -m tools.argonia_world.db query "SELECT ..."` or `db show <table> <id>` (the tables and their comments are in `../../../story/data/schema.sql`). A data file is never opened directly.

## 1. Start from the foundation

- The old quest design is the base (0024 §8). Start from the quest's rows: `python3 -m
  tools.argonia_world.quest_record export <quest id> -o <quest>.yaml` gives the quest object (and the record,
  once one is written) as the YAML view; the `quest_line` row gives its line. Then its design:
  `../../../story/design/quests/30-main-quest.md`, `../../../story/design/quests/40-factions.md` (the line's
  section), `../../../story/design/quests/50-side-quests.md`, or the generated view in
  `../../../story/design/quests/index/`. Keep its premise, cast and beats; say what changed and why in `foundation`.
- Read the world records the quest stands on: the place's facts (`fact` where `place_id` is the place, in
  `ord` order), the place row (`place` and its `place_*` tables, its people in `place_person`),
  the people (`npc`, `npc_faction`), their stance (`stance`, `stance_chain`, `stance_topic`) and the culture
  sheets it chains (`culture_sheet`, `culture_entry`, `culture_opinion`), and the other quests at the place and
  its neighbours (`quest` by `settlement`). The lore dossiers and extrapolation are read from
  `../../../story/lore/`, and the province's vibe from `../../../story/design/province-vibe.md`: the quest
  adds to that vibe and must not jar against it (§4b). The old places are design intent: map each onto the BM&V place that will host the quest,
  and name that place (its cell or editor id) in `foundation`.
- **Cast:** a recurring or principal person comes from `../../../story/design/quests/36-cast-roster.md` (the
  line's desks and its argument, §56; the principal cast, §55; oddities, §58), under the rules of
  `../../../story/design/quests/35-cast.md`; a placed person is an `npc` row. A person the quest needs who
  exists in neither, nor in BM&V, is an `invented` persona to add, never silently made up.
- For a line, its line record first (`principles/questlines.md`).

## 2. The novelty rule and the shape budget (old 55 §47c, binding)

Before the record is written:

1. **Scan** `../../../story/design/quests/index/coverage.md` (the commissioning brief: thin shapes, regions
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
   their argument shapes; `../../../story/design/quests/85-condition-vocabulary.md` explains each term; a missing
   term is added as a row first), plus `actions` or `approaches`, `learns`, `directions` and `journalText` (style guide § journal,
   `../../../story/design/text/style-guide.md`).
10. **Endings**: two or more with real costs, as actions, and where the player sees them.
11. **Topics**: `topic.` ids of `topic` rows or marked `new`; per person
    and stage, the intent, the facts it may state and hide, the links it grants.

## 4b. Check the record against the lore and the vibe (before review)

Run the three checks on the whole record. Every lore source read goes in `recordSources.lore`, a list of
`"<path> §<section>"`. Every claim's
verdict goes in `review.findings` as a lore-check entry before the reviewer's: `id: L<n>`, `severity: lore`, `ids` (the record ids
that carry the claim), `finding` (the claim, and for a §9 motif the motif and the place that licenses it),
`answer` (`sourced: <file §>`, `gap: <QA id>`, or `changed: <what to>`). A record that fails any check is
not handed on to §5. A `QA<n>` id is the next free one in the gap register, re-read just before commit.

1. **Lore check.** List every person, role, job, place, institution, object, custom, belief, price and way of
   doing things the record names. Check each against the lore dossiers and the extrapolation
   (`../../../story/lore/`: the city and province dossiers, `tribes.md`, `regions/`, `topics/`, and
   `extrapolation/`, first `argonia-4e201-state.md`, `settlement-register.md` and `gap-register.md`) and against
   `province-vibe.md`. Each claim is one of three:
   - **sourced**: canon or the extrapolation says it; cite the file and section;
   - **gap**: nothing says it, but it is the least inventive reading of what does; add a row under the gap
     register's `Quest assumptions` section (`../../../story/lore/extrapolation/gap-register.md`): id `QA<n>`,
     the claim, status `ASSUMED`, the quest id, and the anchor it extends (file and section). A gap may not
     contradict the lore or put a §9 motif where `province-vibe.md` §9 does not;
   - **unsourced or contradicted**: change it. Never keep a claim because the quest needs it.
2. **Society check.** For each cast member: is the role or job one this settlement and culture has in 4E 201
   (`province-vibe.md` §3–4, the place's dossier, the settlement register)? An Argonian village has the
   offices in `topics/material-culture.md`, not clerks or wardens. Then trace how the quest's information,
   authority, law, trade and debt move: who tells whom, who decides, who pays in what (coin, barter or owed
   work, by the tier of the place: settlement register §7), and whether anything is written down. It must fit
   `province-vibe.md` §5 for that place.
3. **Motifs only where the lore and the vibe put them.** Couriers, letters, dispatches, ledgers, accounts,
   tallies, rolls, registers, records, clerks, officials, permits, licences, passes, papers, fines and prisons
   are used only where `province-vibe.md` §9 puts them (the state and its agents, Gideon, the ports and their
   customs, the ex-Archein estates and hiring offices, the Rose, foreigners at a foreign foothold), and the
   record's `L<n>` entry names the place and the institution (a port, Gideon, the Collections, the Veiled Reed).
   Anywhere else, use what Argonian ground uses instead (§9's third column). Every record is measured: a stage
   whose `actions` hold no skill use (only supporting `{system, use}` acts, or none, or a skill use whose only point is to receive, hand over or
   read a message or document) counts as hollow; a quest with
   more than a third of its stages hollow, or whose central action (judged from the stages' `learns`, `directions`
   and `journalText`, not the `centrepiece` tag) is delivering, filing, counting or reading a record, is rewritten round a real action.

## 5. Hand on

1. Once §4b passes, `quest-review` by a `quest-reviewer` agent that has not seen your reasoning; its findings go in `review`.
2. Revise the record for every finding, or answer it there; set `recordStatus: reviewed`.
3. `python3 -m tools.argonia_world.quest_record import QUEST.yaml` writes the record into the database; it
   refuses the whole record on any unknown field, wrong type, dangling key or unknown lookup value, and writes nothing then. `--dry-run` checks without writing. Then
   `python3 .claude/skills/quest-write/brief.py <quest id> OUT_DIR` builds one brief per person and a
   journal brief. It reads the record, people, stance, culture sheets, place facts, topics and vocabulary from
   the database, and writes nothing while any reference, vocabulary term, stage field, `shapeData` section,
   catalogue use, fail-forward or ending is missing.
4. `dialogue-write` (the `dialogue-writer` agent) per brief. A fact request comes back here; add the fact and
   rebuild the briefs.
5. The record's rows are the quest's rows (same `id`): there is no second copy to update.
