---
name: quest-review
description: Review an Argonia quest record before dialogue is written, as a player and as a designer, and return findings the quest writer can act on. Use after quest-write produces or revises a record.
---

# Reviewing a quest

Draft (finished in P4-WP4.0 with the imported quest system). The review is design critique of the record, run before any dialogue exists, so problems are fixed
where they start. It is not the consistency mechanism (that is the record's build order and the brief
builder); it judges whether the quest is good and believable.

## 1. Set-up

- Run as a fresh agent given only the quest record, the place record, the culture sheets and this skill;
  never the author's reasoning, so the reading is not anchored on it.
- Read the principle files the record routes to (`quest-write/shapes.yaml`: always `general.md` and
  `actions.md`, the line's file, each shape's file); their checklists are part of this review. The research
  packs behind them are in `docs/research/2026-10-27/`.

## 2. Read it twice

1. **As the player**, using only what the player knows at each stage (the record's `playerStart` and each
   stage's `learns`): can I tell what to do next and where to go, from dialogue and the journal alone? Where
   would I be lost, bored or unrewarded?
2. **As the designer**, against the checklist below.

## 3. Checklist (answer each yes or no, with the record ids that show it; then each routed principle file's checklist)

Premise and truth
1. Can the premise be said in one sentence, and would a sensible person in Black Marsh act as it requires?
2. Is the truth a timeline of physical events, and does every clue, rumour and lie follow from it?
3. Does each person's every action pass the plausibility test given their wants, fears and knowledge?
4. Does each person know only what events they took part in or were told of?

Investigation
5. Does each conclusion have at least three clues in at least two forms?
6. Can the player finish after missing any one clue, failing any one check, or going in another order?
7. Does the player find out or decide something, rather than being told?
8. Is there a false lead that a clue refutes?

Play
9. Can every stage be followed with no markers, from dialogue and the journal (landmark, direction, distance)?
10. Is there more than one approach somewhere, with different costs?
11. Is it long enough: a hook, two lines of enquiry, a revelation, a decision, a consequence?
12. Is the danger fixed and warned of?

Endings and rewards
13. Are there at least two endings with real costs, none presented as the right one?
14. Does each ending change something the player will meet, and say where?
15. Is every reward concrete, proportionate and tied to the story?

The world
16. Does every physical thing have an existing id or a `new` row with where and state per stage?
17. Does anything need the world to change (a deeper pool, a schedule, a container), and is that written as a
    row, not assumed?
18. Does anything break Black Marsh in 4E 201: a Nordic element, a vanilla Skyrim reference, the wrong era?

Action and fit
19. Does almost every stage make the player use a skill, across at least two families, with one stage
    offering approaches from different families? Is it more than a chain of conversations?
20. Do the actions follow from the truth and the place, and does a faction quest lean to its profile?
21. Does each shape's checklist in its principles file pass, and is every required `shapeData` section real
    rather than filled for form?
22. Is the quest built on its old design (`foundation`), and is each change from it an improvement?

Text
23. Will the player understand every name and thing when first met (the brief's player-knows lists)?
24. Does each topic's intent only rephrase its listed facts?

## 4. Report

Return findings ranked most serious first, each with: the record ids, what is wrong, what a player would
experience, and a proposed fix. End with the answers to the checklist as one line of ids per failed item.
