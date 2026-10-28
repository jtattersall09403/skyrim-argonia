---
name: quest-write
description: Design or rewrite an Argonia quest or questline as a record (hidden truth, cast knowledge, things, clues, actions, stages, endings, topics) from the place, culture and quest data, routed to the principles for its shape and line, then build the dialogue briefs from it. Use before any quest dialogue is written, and to rework a quest after review.
---

# Writing a quest

**Draft, started 2026-10-27 before the old project was imported.** P4-WP4.0 finishes it against the imported
quest system (decision 0017). Quests, their dialogue and the world are consistent because they are built
from one record in a fixed order, not because they are checked afterwards. The record format is
[quest-record.md](quest-record.md); a worked example is [examples/lh38.yaml](examples/lh38.yaml).

## 1. Start from the foundation

- The old project's quest design is the base (0017 §8): an existing quest's premise, cast and beats are kept
  and improved, with what changed and why in the record's `foundation`. New quests follow the quest index's
  novelty rule and shape budget.
- Read: the place record (facts, people, things, routes, landmarks, hooks); the culture sheets to each
  household; the other quests at the place and its neighbours; the region's danger band; for a line, its line
  record first.

## 2. Route to the principles

Read `shapes.yaml`: always `principles/general.md` and `principles/actions.md`; the file for the line type
(`questlines.md`); the file for each shape (primary first). Each shape names the `shapeData` sections the
record must hold.

| Shapes | File |
|---|---|
| MURDER, MISSING, RECKONING, and THEFT or FRAUD to solve | `principles/investigation.md` |
| THEFT, FRAUD, SMUGGLING | `principles/crime-and-deceit.md` |
| DISPUTE, NEGOTIATION, SUCCESSION, BONDAGE | `principles/social.md` |
| PREDATOR, CONTAMINATION, EXPEDITION | `principles/threat-and-journey.md` |
| HAUNTING, RITE, WONDER, Daedric | `principles/otherworldly.md` |

## 3. Write the record in order

1. **Action plan** (`principles/actions.md`): run `action_plan.py` with the line's or faction's profile, the
   shapes, the band and the ledger of quests already in the line or packet; choose, adapt or write the skill
   uses the quest is built round.
2. **Premise**, one sentence the player could say back afterwards, and the **truth**: numbered physical
   events (who, where, when, what, why), written so the planned actions follow from them.
3. **Plausibility pass**, person by person: would a sensible person with these wants, fears and knowledge do
   this? If not, change the truth, never the person.
4. **Facts** the truth creates, each `from` a truth event or a culture-sheet entry.
5. **Cast and knowledge**: for every person and fact, knows, believes, suspects, hides (with the reason) or
   ignorant, and how that changes by stage.
6. **Things**: every trace and object, with an existing id or a `new` row the world builder places.
7. **Conclusions and clues**: three clues per conclusion, two forms at least, each a trace of the truth.
8. **`shapeData`** for each shape, as its principles file says.
9. **Stages** with conditions in the condition vocabulary, **actions** from the plan (skill and use from
   `skill-uses.yaml`, with target and setting), approaches,
   directions, what the player learns, and fail-forward.
10. **Endings**: two or more with real costs, where the player sees each, and the rewards.
11. **Topics**: per person and stage, the intent, the facts it may state and hide, the links it grants. An
    intent only rephrases its listed facts; anything else becomes a fact first.

## 4. Hand on

1. `quest-review` by the `quest-reviewer` agent, which has not seen your reasoning.
2. Revise the record for every finding, or answer it in the record.
3. `python3 .claude/skills/quest-write/brief.py QUEST.yaml OUT_DIR --place-facts PLACE.json` builds one brief
   per person; it writes nothing while any reference, required `shapeData` section, stage action or
   catalogue skill and use is missing, and each brief lists what the player does at each topic's stages so
   the lines set it up.
4. `dialogue-write` (the `dialogue-writer` agent) per brief. A fact request comes back here; add the fact and
   rebuild the briefs.
