# The quest record

One YAML file per quest is the only source of truth for that quest. The journal, every dialogue brief and the
world builder's list of things to place are made from it; nothing downstream restates a fact by hand. Write
the sections **in this order**, because each is built from the ones above it.

| # | Section | What it holds | Built from |
|---|---|---|---|
| 1 | `id`, `code`, `title`, `place`, `line`, `shapes`, `foundation`, `status` | identity; `line` is local, faction, main, daedric or detectives; `shapes` from the quest index taxonomy, primary first; `foundation` names the old design it rebuilds and what changed; status is `design`, `reviewed`, `briefed`, `written` | the quest index |
| 2 | `sources` | the place record, culture sheets and roster read, by path | the world data |
| 3 | `actionPlan` | the skill uses the quest is built round (`skill`, `use` from `skill-uses.yaml`), chosen from `action_plan.py` proposals or written, with the reason | the line or faction profile, the place, the shapes |
| 3b | `premise` | one sentence the player could say back after the quest | the place's quest hooks + the action plan |
| 4 | `truth` | what really happened before the player arrives: numbered events with when, who, where, what and why, in physical terms | premise + cast motives |
| 5 | `facts` | the only new world facts the quest adds; each `from` a truth event or an existing fact id | truth |
| 6 | `cast` | each person (roster id) with persona, what they want and fear, and for every fact: `knows`, `believes: <false version>`, `suspects`, `hides: <reason>` or nothing (ignorant); `changes` per stage | truth + culture sheets |
| 7 | `things` | every physical thing the quest uses, with an existing id from the place record or `new` (a provision the world builder places from this row), and its state per stage | truth + clues |
| 8 | `conclusions` | what the player must work out, each with at least three clues | truth |
| 9 | `clues` | each clue's form (line, thing, place, behaviour), carrier (a person or a thing), the facts it gives and the conclusions it supports | cast knowledge + things |
| 10 | `shapeData` | the sections each shape requires (`shapes.yaml`), e.g. lies and accusation for MURDER, source to cure for CONTAMINATION | truth + clues |
| 11 | `stages` | objective, `pre`, `onEnter`, `post` (in the condition vocabulary), `actions` or `approaches` each with actions (`skill`, `use`, optional `target`, `setting`, `note`; `principles/actions.md`), what the player learns (fact ids), directions, fail-forward | conclusions + clues |
| 12 | `endings` | condition, world changes, where the player will see them, rewards | stages |
| 13 | `topics` | per person and stage: topic name, essential or not, intent, facts used, facts hidden, topics granted | cast + stages |

A **line record** (faction, main, Daedric) comes before its quests: `principles/questlines.md` lists its
sections.

**Draft format.** 0.1 §i merges it into the imported quest schema (`world/sources/quests/`, design docs in `docs/design/quests/`), so there is
one quest format, and adds the table of what consumes each machine field in the engine (the 2.12 §a quest
generator, the 1.3 and 2.5 topic store, the condition evaluator, the placement builders (2.W5, 4.2, 4.4), the 2.12 §b journal).

## Rules that make it consistent by construction

- **Truth before trail.** Every clue is a trace a truth event left (a thing, a memory, a lie). No clue exists
  that the truth does not explain, and no truth event the player needs is left without clues.
- **Nobody knows what they could not know.** A cast member's knowledge comes from the truth events they took
  part in or were told of; the record says which.
- **Motives cite the sheets.** Each `wants`, `fears` and hidden reason cites a culture-sheet or persona entry,
  or is flagged `invented` for the reviewer.
- **The world is built from the record.** A `new` thing is a provision row the world builder places; dialogue
  only ever names a thing by its id here. Nothing is described that the record does not hold.
- **Player knowledge is computed.** What the player knows at a stage is the place's common knowledge plus the
  `learns` of every earlier stage; the brief builder hands that list to the dialogue writer.
- **New facts flow up, not sideways.** A dialogue writer who needs a fact asks for it; the quest writer adds it
  here, and the briefs are rebuilt.
