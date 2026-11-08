---
name: quest-write
description: Design or rewrite an Argonia quest or questline as a record (hidden truth, cast knowledge, things, clues, actions, stages, endings, topics) from the place, culture and quest data, routed to the principles for its shape and line, then build the dialogue briefs from it. Use before any quest dialogue is written, and to rework a quest after review.
---

# Writing a quest

A quest is written as one record, then built as quest, dialogue, alias and world-edit records on top of Black
Marsh & Valenwood (BM&V, the world mod). The record is the imported quest object plus its sections:
[quest-record.md](quest-record.md), with the engine-mapping table. The story database (`story/data`: `schema.sql`
and `db/*.jsonl`, through `db.py`) is the one source of truth: every write and fix goes into its rows (import the
YAML view, or edit rows through `db.py`), never into a generator, an export or a doc copy. Read it only through
`python3 -m tools.argonia_world.db query "SELECT ..."` or `db show <table> <id>`. Examples:
[examples/lh38.yaml](examples/lh38.yaml) (local), [examples/mr01.yaml](examples/mr01.yaml) (faction). The method
this skill carries is `docs/design/quests-on-a-world.md` (parts 3 to 5) and the block set `docs/design/blocks.md`.

## 1. Start from the foundation

- The old quest design is the base. Start from the quest's rows: `python3 -m tools.argonia_world.quest_record
  export <quest id> -o <quest>.yaml` gives the quest object (and the record, once one is written) as the YAML view;
  the `quest_line` row gives its line. Then its design: `../../../story/design/quests/30-main-quest.md`,
  `40-factions.md` (the line's section) or `50-side-quests.md`. Keep its premise, cast and beats; say what changed
  and why in `foundation`.
- Read the world records the quest stands on: the place's facts (`fact` by `place_id`, in `ord` order), the place
  row and its `place_*` tables, its people (`place_person`), the people (`npc`, `npc_faction`), their stance
  (`stance`, `stance_chain`, `stance_topic`), the culture sheets it chains (`culture_*`) and the other quests at the
  place and its neighbours (`quest` by `settlement`). The lore is in `../../../story/lore/`, the province's vibe in
  `../../../story/design/province-vibe.md`: the quest adds to that vibe and does not jar against it (§4b). Map each
  old place onto the BM&V place that hosts the quest and name it (cell or editor id) in `foundation`.
- A room or home without a load door is a walk-in building from `bmv_shell` (by `settlement`, class A first).
- **Cast:** a recurring or principal person comes from `../../../story/design/quests/36-cast-roster.md` under the
  rules of `35-cast.md`; a placed person is an `npc` row. A person the quest needs who exists in neither, nor in
  BM&V, is an `invented` persona to add.
- For a line, its line record first (`principles/questlines.md`).

## 2. Novelty and the shape budget

1. **Scan** `../../../story/design/quests/index/coverage.md` (thin shapes, regions short of quests), then the index
   view for the quest's primary shape and region.
2. **Collision test:** the quest collides if it shares its primary shape with an existing quest and any of: the same
   region packet, faction line, reversal or resolution set. Check secondary shapes and the same place too.
3. **On a collision:** differentiate (reversal, claimants, resolution or verb), merge it into the other quest, or
   drop it for something coverage.md shows is missing.
4. **Declare `touches`** (shared people, places, flags, items, variables, read or write) and keep tier direction
   (40-factions §30b): a quest does not write what a higher tier owns.
5. **Shape budget:** no primary shape over about 20% of a line (or packet), and not in consecutive M or L quests; a
   departure goes in `budgetExceptions` with a one-line reason.
6. **Cover the board:** each packet brings a shape new to its region or one from coverage.md's gaps, and at least
   one `WONDER`.
7. **Verb variety:** `SOCIAL` and `INVESTIGATE` centrepieces stay at or under two thirds of a line's M and L quests.

## 3. Keep it simple, true and played with skills

1. **Action, danger and discovery drive the quest.** Law, custom, debts and bargaining are background colour; at
   most one stage turns on a formal procedure, and never the climax or the resolution.
2. **Branching budget:** at most two real choices and three endings per quest; about 8 stages for an M quest, 12 for
   an L. A later quest in a line works the same whichever choice the player made earlier (a line of dialogue, a
   reward or a greeting may differ); only a line's planned finale choices carry forward.
3. **Skills win the stages** (checked by `skill_routes`). Each stage that asks something of the player names the
   game skill it uses (One-Handed, Two-Handed, Archery, Block, Heavy/Light Armor, Destruction, Alteration, Illusion,
   Conjuration, Restoration, Alchemy, Sneak, Lockpicking, Pickpocket, Speech, Mysticism); climbing and swimming are
   movement, not skills, and nothing climbs a tree. A stage is won by a route that can fail (a check of 25 or more,
   a lock level, a theft the crime engine can see, a fight that can be lost); a pure choice stage and an ending are
   exempt. Every main quest has two ways through on different skills; a faction quest leans on its faction's.
   A failed check may simply stay closed until the player returns stronger. A fail-forward is written only where
   failure should matter; a person the quest must not lose is essential and needs none.
4. **Plain next steps:** each stage's journal or objective says what to do and where.
5. **Grounded:** every person, role, institution, custom and object comes from the lore, the extrapolation, the
   census or the story data, cited as written. Where none gives it, leave it vague or add it to the extrapolation
   with its gap-register row first. Never invent an institution or a law to make a plot work.

## 4. Build shapes and places

Every stage is written only in the proven block shapes (`docs/design/blocks.md`; the rewrite table in
`docs/design/quests-on-a-world.md` part 5), so the record builds as written:
- **Starts** by the giver's opening line or another quest's stage, never on entering a cell or area.
- **Trigger areas** are gated only by their prerequisite stage; a time, detection or presence check goes on a
  line's condition, a package schedule, a death trigger's fail-forward or the crime engine.
- **Escorts** are a follow package plus a trigger area at the destination.
- **Items** are one named item (N of it), never a kind of thing.
- **"All of"** is one hidden stage per part, each checking the others before setting the joint stage.
- **Removing people** is disabling them through their enable parents, never killing them in a fragment.
- **Fights** are a fixed-level enemy and a death trigger, or a Speech or gold route.
- **Standing** is a global the endings add to; **a chosen speaker** is a condition on their placed reference.
A step that fits none of these is rewritten into them; only when no rewrite keeps the quest's point is it handed to
the planner as a new block.

Places, people and things:
- Each is a real reference in the loaded world (form key) or a world edit in the ledger, linked to the quest.
- A spot for people lies on the winning navmesh with a real floor; a thing rests on a read surface; every model the
  quest uses (and the building it calls a place) exists in the load order.
- A spot that fails is moved to the nearest usable ground in the same settlement by editing its row; the quest is
  not redesigned for it.

## 5. Route to the principles

Read `shapes.yaml`: always `principles/general.md` and `principles/actions.md`; the group's file
(`principles/questlines.md`); each shape's file (primary first). Each shape names the `shapeData` sections the
record must hold.

| Shapes | File |
|---|---|
| MURDER, MISSING, RECKONING, and THEFT or FRAUD to solve | `principles/investigation.md` |
| THEFT, FRAUD, SMUGGLING | `principles/crime-and-deceit.md` |
| DISPUTE, NEGOTIATION, SUCCESSION, BONDAGE | `principles/social.md` |
| PREDATOR, CONTAMINATION, EXPEDITION | `principles/threat-and-journey.md` |
| HAUNTING, RITE, WONDER, Daedric | `principles/otherworldly.md` |

Also binding: 00-overview §4 (cost tiers, register, wonder budget, deliverability tiers, the boredom test) and
20-world-provisions.

## 6. Write the record in order

1. **Action plan** (`principles/actions.md`): `python3 .claude/skills/quest-write/action_plan.py --profile
   <line key> --shapes <SHAPE,...> --band <D0..D5> --ledger <dir of records in the line or packet>`; choose, adapt
   or write the uses the quest is built round, and the `centrepiece` tag.
2. **Premise** and **truth**: numbered physical events, written so the planned actions follow from them.
3. **Plausibility pass**, person by person; change the truth, never the person.
4. **Facts** the truth creates, each `from` a truth event, a place fact or a culture-sheet entry.
5. **Cast and knowledge** (registry ids; `persona` only for what the registry lacks).
6. **Things**: an existing id or a `new` row the world-builder places.
7. **Conclusions and clues**: three clues per conclusion, two forms at least.
8. **`shapeData`** for each shape.
9. **Stages** in the imported shape (`place`, `journal`, `onEnter`, `objectives`, `successors`, `failForward`,
   `ending`) in the §4 shapes, with conditions and actions only from the vocabulary (`condition_term` rows;
   `../../../story/design/quests/85-condition-vocabulary.md` explains each; a missing term is added as a row first),
   plus `actions` or `approaches`, `learns`, `directions` and `journalText` (style guide § journal,
   `../../../story/design/text/style-guide.md`).
10. **Endings**: two or more with real costs, as actions, and where the player sees them.
11. **Topics**: `topic.` ids of `topic` rows or marked `new`; per person and stage, the intent, the facts it may
    state and hide, the links it grants.

## 6b. Check the record against the lore and the vibe

Every lore source read goes in `recordSources.lore` (`"<path> §<section>"`). Every claim's verdict goes in
`review.findings` as `id: L<n>`, `severity: lore`, `ids`, `finding`, `answer` (`sourced: <file §>`,
`gap: <QA id>` or `changed: <what to>`). A record that fails a check is not handed on.

1. **Lore check.** Check every person, role, job, place, institution, object, custom, belief, price and way of
   doing things against the lore and the extrapolation (`../../../story/lore/`, first
   `extrapolation/argonia-4e201-state.md`, `settlement-register.md`, `gap-register.md`) and `province-vibe.md`.
   Each is **sourced** (cite it), a **gap** (the least inventive reading of what is sourced: a `QA<n>` row under
   the gap register's `Quest assumptions`, status `ASSUMED`, with its anchor; the next free id, re-read before
   commit), or **changed**.
2. **Society check.** Each cast member's role exists in this settlement and culture in 4E 201 (`province-vibe.md`
   §3–4, the place's dossier, the settlement register; an Argonian village has the offices in
   `topics/material-culture.md`). Information, authority, law, trade and debt move as `province-vibe.md` §5 says for
   the place (coin, barter or owed work by its tier).
3. **Motifs only where §9 puts them.** Couriers, letters, ledgers, tallies, records, clerks, officials, permits,
   papers, fines and prisons appear only where `province-vibe.md` §9 puts them, and the `L<n>` entry names the
   place and institution; elsewhere use §9's third column. A stage with no skill use is hollow; a quest with more
   than a third of its stages hollow, or whose central action is delivering, filing, counting or reading a record,
   is rewritten round a real action.

## 7. Hand on

1. `quest-review` by a `quest-reviewer` agent that has not seen your reasoning; its findings go in `review`.
2. Revise the record for every finding, or answer it there; set `recordStatus: reviewed`.
3. `python3 -m tools.argonia_world.quest_record import QUEST.yaml` (`--dry-run` to check) writes the record; it
   refuses the whole record on any unknown field, wrong type, dangling key or unknown lookup value. Then
   `python3 .claude/skills/quest-write/brief.py <quest id> OUT_DIR` builds one brief per person and a journal
   brief; it writes nothing while any reference, vocabulary term, stage field, `shapeData` section, catalogue use
   or ending is missing, or a stage needs someone alive who is neither essential nor protected and has no
   fail-forward.
4. `dialogue-write` (the `dialogue-writer` agent) per brief. A fact request comes back here; add the fact and
   rebuild the briefs.
5. **A fact lives in one row; a cut is a search.** To change or cut a thing, `grep -rn` its id, name and words over
   `story/data/db/` and change every hit. Before every commit run that search and
   `python3 -m tools.argonia_world.adaptation_check`; a fix adds no `record` or `wiring` line.
