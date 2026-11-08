---
name: quest-review
description: Review an Argonia quest record before dialogue is written, as a player and as a designer, and return findings the quest writer can act on. Use after quest-write produces or revises a record.
---

# Reviewing a quest

The review is design critique of the record (`../quest-write/quest-record.md`: the imported quest object plus the
record's sections), run before any dialogue exists, so problems are fixed where they start. It judges whether the
quest is good, believable and buildable from the proven blocks as written.

## 0. The bar

- **Blocking means only:**
  (a) a path the player cannot finish or a stage that cannot be left;
  (b) a contradiction inside the record, or with the world data (census, story data);
  (c) a contradiction with canon lore or the extrapolation;
  (d) a Nordic element we add, or anything levelled against the player;
  (e) a breach of the skill rule (quest-write §3 item 3, program-checked): a stage (a pure choice stage excepted) not
  won by a skill route that can fail, a main quest without two ways through on different skills, a faction quest
  ignoring its faction's skills, a stage that does not say plainly what to do and where, a route that climbs a tree,
  or a fail-forward demanded for an essential person;
  (f) a stage outside the proven block shapes (quest-write §4): a start on entering a cell or area, a trigger area
  carrying a check beyond its prerequisite stage, an escort without a follow package and a destination area, a kind
  of item instead of one named item, an "all of" without hidden stages, a person removed by killing in a fragment, a
  fight without a fixed-level enemy or a Speech or gold route, standing kept other than as a global, a speaker not
  picked by their placed reference;
  (g) a place, person or thing that is not a real reference or a ledger edit; a people spot off the winning navmesh
  or without a real floor; a thing not on a read surface; a model missing from the load order;
  (h) harder to script than an average Skyrim side quest (stages, aliases, conditions, timers, bespoke scripts);
  (i) a climax or resolution that is a procedure (an arbitration, hearing, trial, ruling, witnessed or spoken
  release, negotiation at a table); procedure may colour a quest, never resolve it.
  Nothing else is blocking: write it as a `note` with its weight (`high`, `low`).
- A failed check that stays closed until the player returns stronger is allowed; so is a quest with no fail-forward
  where failure should not matter. A spot that fails placement is fixed by moving it within its settlement (a row
  edit), not by redesigning the quest.
- **Settled is settled:** never re-raise what `review.settled` holds, or a variant, unless a change reopens it (say how).
- **Prefer subtraction:** a fix cuts or rewrites into a proven shape; it never adds a stage, branch, ending or
  mechanism a cut would answer.
- **Report every finding.** Round 1 reads the whole record. Every later round is a delta: only the rows changed
  since the last review (`git diff <last reviewed sha> -- story/data/db/` read against the export) and every row that
  cites them; the loop ends when a delta round raises nothing blocking. A line outline or premise-level record is
  judged at its own level (spirit, beats, lore, motifs, branching, clashes); place fit (g) is checked on a full record.
- The planner decides which findings are fixed and when the loop ends.

## 1. Set-up

- Run as a fresh agent given only the quest record, the world records it cites and this skill; never the author's
  reasoning. Read the record with `python3 -m tools.argonia_world.quest_record export <quest id>` and the world with
  `python3 -m tools.argonia_world.db query "SELECT ..."` (`fact` by `place_id`, `npc`, `npc_faction`, `stance*`,
  `culture_*`, the place's other quests). The lore: `../../../story/lore/`. Judge the quest against the BM&V place
  it names in `foundation`.
- First run `python3 -m tools.argonia_world.adaptation_check`. Its `record` lines (an id not in the census, an
  unplaced speaker, a needed person neither essential, protected nor failed forward from, an edit to a shared base,
  a vanilla door model, a skill gate walked round, a fact a speaker cannot know) and `wiring` lines (a start on
  entering a place, a trigger area with an extra check, an unreachable stage, no start, a hasItem trigger for an
  item already held, a person or item present before the start, a topicHeardFrom speaker with no topic row) are
  findings already; copy them, do not re-judge them.
- Also binding: the quest index rules and coverage (`../../../story/design/quests/index/README.md` §47b–c,
  `index/coverage.md`), 00-overview §4, the condition vocabulary (`condition_term` rows;
  `../../../story/design/quests/85-condition-vocabulary.md`), the style guide's journal register
  (`../../../story/design/text/style-guide.md`), and the block set (`docs/design/blocks.md`, the rewrite table in
  `docs/design/quests-on-a-world.md` part 5).
- Read the principle files the record routes to (`../quest-write/shapes.yaml`: `principles/general.md`,
  `principles/actions.md`, the group's file, each shape's file); their checklists are part of this review.

## 2. Read it twice

1. **As the player**, knowing only `playerStart` and each stage's `learns`: from dialogue and the journal alone, can
   I tell what to do next and where? Where would I be lost, bored or unrewarded?
2. **As the designer**, below.

## 3. Checklist (yes or no, with the record ids that show it; then each routed principle file's checklist)

Premise and truth
1. Can the premise be said in one sentence, and would a sensible person in Black Marsh act as it requires?
2. Is the truth a timeline of physical events, and does every clue, rumour and lie follow from it?
3. Does each person's every action pass the plausibility test given their wants, fears and knowledge?

Investigation
4. Does each conclusion have at least three clues in at least two forms?
5. Can the player finish after missing any one clue, failing any one check (or coming back stronger), or going in
   another order?
6. Does the player find out or decide something, rather than being told?
7. Where the shape is an investigation, can the player present evidence and accuse, each written as a stage
   condition?

Play
8. Can every stage be followed with no markers, from dialogue and the journal (landmark, direction, distance)?
9. Is there more than one approach somewhere, with different costs?
10. Is it long enough beside comparable quests from Morrowind, Oblivion and Skyrim?
11. Does every stage's `journalText` follow the journal register (first person, "I'm to", full names, re-summarised
    chain, directions by landmark, failure entries flat with their consequence)?

Endings and rewards
12. Does a standalone quest, or a quest line as a whole, have at least two endings with different costs and rewards
    the player will feel in play (a quest inside a line may have one)?
13. Is every reward concrete, fixed, proportionate and tied to the story?

Skills (blocking, item e)
14. Name the skills each stage uses. Does every stage that asks something have a route that can fail; does a main
    quest have two ways through on different skills, a faction quest its faction's skills? Is each fail-forward
    where failure should matter, and is no essential person given one?

Build shapes (blocking, item f)
15. Is every stage in a proven shape: started by an opening line or a chain; trigger areas gated only by their
    prerequisite stage; escorts as a follow package and a destination area; one named item; hidden stages for
    "all of"; disabling, not killing; fixed-level fights or Speech or gold routes; standing as a global; speakers
    picked by their placed reference?

Places (blocking, item g)
16. Is every place, person and thing a real reference or a ledger edit linked to the quest; people spots on the
    winning navmesh with a real floor; things on a read surface; every model in the load order? Does every `new`
    thing have its where and state per stage, and every change to the world written as a row?

Lore and vibe (blocking, item c)
17. Read `../../../story/design/province-vibe.md` and the lore the record names, and check every person, role, job,
    place, institution, object and custom against the lore and the extrapolation (`../../../story/lore/`, first
    `extrapolation/argonia-4e201-state.md`, `settlement-register.md`, `gap-register.md`, the place's dossier). It is
    blocking when the quest:
    - contradicts canon or the extrapolation (a Nordic element, a vanilla Skyrim reference, the wrong era, an office
      the lore says is gone, absent or elsewhere);
    - rests on a claim with no `L<n>` entry, or on a `QA<n>` gap row that is not the least inventive reading of its
      anchor, contradicts the lore, or puts a §9 motif where §9 does not (read every `QA<n>` row cited);
    - gives a person a role the settlement and culture do not have in 4E 201 (`province-vibe.md` §3–4);
    - moves information, authority, law, trade or debt in a way that does not fit the place (§5);
    - uses a §9 motif where §9 does not put it, has more than a third of its stages hollow (quest-write §6b.3), or
      has a central action of delivering, filing, counting or reading a record;
    - otherwise jars with `province-vibe.md`.
    Run `python3 ../dialogue-write/lint.py` over the stages' `journalText` and justify or flag every B10 warning.
    Name the source file and section for each finding. For a long record, split the lore reading across cheap
    subagents, each given the claims and the files to check them in.
17b. Does the quest add to the vibe (`province-vibe.md` §10) rather than only avoid jarring with it?

Fit
18. Do the actions follow from the truth and the place, lean to the line's or faction's profile, and vary from the
    quests around it?
19. Does each shape's principles checklist pass, and is every required `shapeData` section real?
20. Is the quest built on its old design (`foundation`), and is each change from it an improvement?
21. Does it pass the novelty rule (index README §47c), and share no reversal with another quest at the same place?
22. Do the cast match their `npc` rows (race, sex, role) and the roster, with any difference marked `invented`?

Text
23. Will the player understand every name and thing when first met? What needs spelling out?
24. Does each topic's intent only rephrase its listed facts?

## 4. Report

Return every finding, most serious first, blocking ones at the top with `severity: blocking`, each with the record
ids, what is wrong, what the player would experience and a proposed fix (a rewrite into a proven shape, a moved
spot, a cut); in a delta round, only findings on the changed rows and the rows citing them. End with one line of ids
per failed checklist item, marking blocking items `(B)`. The quest writer copies the findings into the record's
`review` section with how each was answered.
