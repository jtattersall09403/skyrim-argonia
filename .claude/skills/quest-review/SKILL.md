---
name: quest-review
description: Review an Argonia quest record before dialogue is written, as a player and as a designer, and return findings the quest writer can act on. Use after quest-write produces or revises a record.
---

# Reviewing a quest

The review is design critique of the record (`../quest-write/quest-record.md`: the imported quest object plus
the record's sections), run before any dialogue exists, so problems are fixed where they start. It is not the consistency mechanism (that is the record's build order and the brief
builder); it judges whether the quest is good and believable.

## 1. Set-up

- Run as a fresh agent given only the quest record, the world records it cites and this skill; never the
  author's reasoning, so the reading is not anchored on it. The record is rows in the world database (decision
  0030): read its YAML view with `python3 -m tools.argonia_world.quest_record export <quest id>`. The world
  records, read only through the database (`python3 -m tools.argonia_world.db query "SELECT ..."` or `db show
  <table> <id>`; the tables are described in `../../../docs/design/world/98-data-model.md`): the place's facts
  (`fact` by `place_id`), the people (`npc`, `npc_faction`), the stance and culture sheets (`stance`,
  `stance_chain`, `stance_topic`, `culture_sheet`, `culture_entry`, `culture_opinion`), the other quests at the
  place (`quest` by `settlement`, each exported as above). The lore is not yet a table: read it from the
  import, read-only (`../../../world/sources/lore/`).
- Also binding: the quest index rules and coverage (`../../../docs/design/quests/index/README.md` §47b–c,
  `../../../docs/design/quests/index/coverage.md`), 00-overview §4 (`../../../docs/design/quests/00-overview.md`), the condition
  vocabulary (`condition_term` rows; `../../../docs/design/quests/85-condition-vocabulary.md` explains each term) and the style guide's journal register
  (`../../../docs/design/standards/text/style-guide.md`).
- Read the principle files the record routes to (`../quest-write/shapes.yaml`: always
  `../quest-write/principles/general.md` and `../quest-write/principles/actions.md`, the group's file, each
  shape's file); their checklists are part of this review. The research
  packs behind them are in `../../../docs/research/2026-10-27/`.

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
8. Where the shape is an investigation, can the player present evidence and accuse, and is every
   presentation and accusation written as a stage condition (or listed as needing a decision)?

Play
9. Can every stage be followed with no markers, from dialogue and the journal (landmark, direction, distance)?
10. Is there more than one approach somewhere, with different costs?
11. Is it long enough, vs comparable quests from Morrowind, Oblivion and Skyrim?
12. Does every stage's `journalText` follow the journal register (first person, "I'm to", full names,
    re-summarised chain, directions by landmark, failure entries flat with their consequence)?

Endings and rewards
13. For multi-quest quest *lines* (e.g. for factions), are there at least two endings, with real different costs and rewards? 'real' in terms of in-game outcomes for the player that they will really 'feel'. Individual quests within a questline are allowed to have only one ending (too much branching in multi-quest questlines will get too complicated). For standlone quests - do they have at least two endings, with real different costs and rewards? This goes for even minor quests - e.g. Morrowind's famous Fargoth's ring line is the very first quest most players encounter, and they are faced with real choices that affect their gameplay (e.g. keep the ring for its enchantment, vs give it back and get discounts at the Seyda Neen trader).
14. Is every reward concrete, proportionate and tied to the story?

The world
15. Does every physical thing have an existing id or a `new` row with where and state per stage?
16a. Does anything need the base world to change (a deeper pool, a schedule, a container, anything else), and is that written as a row, not assumed? If something does need to change, are you handing it to the planner to get it delivered?
16b. Does anything during the request require anything in the world to be scripted? e.g. a change to somebody's     schedule (if you need to observe them doing something at a certain place and time); a timed bandit attack the player need to be present for; a tree that changes to a 'sick' appearance until healed; anything else? And if yes,  are you handing it to the planner to get it delivered?
17. Does anything break Black Marsh in 4E 201: a Nordic element, a vanilla Skyrim reference, the wrong era, 
    anything that isn't consistent with our lore dossiers or lore extrapolation? Does it fit the 'vibe' of Black Marsh, per the lore? e.g. we don't want lots of bureaucratic quests if the province is known for being
    wild and mysterious and loosely governed. That's just one example amongst many. Reason about what lore dossiers will be relevant, and dispatch cheap Haiku subagents (giving them *short* briefs) to read them and return a short verdict.

Action and fit
18. Is the quest built round an action plan of real skill uses (i.e. in-game skills: long blade, sneak, alchemy, speechcraft...etc),
    with almost every stage using one? Is it more than a chain of conversations or mundane tasks? Quests are
    only fun if they involve using the character the player is building.
19. Is every condition and action a term of the condition vocabulary, and does every stage that names a
    person have a fail-forward for that person's death (old 0138)? real in-game skills.
20. Do the actions follow from the truth and the place, do they lean to the line's or faction's profile, and
    do they vary from the quests around it (the same skill, use, target and setting not repeated without
    reason)?
21. Does each shape's checklist in its principles file pass, and is every required `shapeData` section real
    rather than filled for form?
22. Is the quest built on its old design (`foundation`), and is each change from it an improvement?
22b. Does it pass the novelty rule (index README §47c): no collision in primary shape with the same packet,
    line, reversal or resolution set; and does it share no reversal with another quest at the same place?
22c. Do the cast match their `npc` rows (race, sex, role) and the roster (36-cast-roster), with any
    difference marked `invented`?

Text
23. Will the player understand every name and thing when first met (the brief's player-knows lists)? What needs to be explained or spelled out for them?
24. Does each topic's intent only rephrase its listed facts?

## 4. Report

Return findings ranked most serious first, each with: the record ids, what is wrong, what a player would
experience, and a proposed fix. End with the answers to the checklist as one line of ids per failed item.
The quest writer copies the findings into the record's `review` section with how each was answered.
