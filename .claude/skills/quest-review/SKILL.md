---
name: quest-review
description: Review an Argonia quest record before dialogue is written, as a player and as a designer, and return findings the quest writer can act on. Use after quest-write produces or revises a record.
---

# Reviewing a quest

The review is design critique of the record (`../quest-write/quest-record.md`: the imported quest object plus
the record's sections), run before any dialogue exists, so problems are fixed where they start. It is not the consistency mechanism (that is the record's build order and the brief
builder); it judges whether the quest is good and believable.

## 0. The bar, and what you are not asked to do (owner, 2026-11-06, binding)

- **Blocking means only:** (a) a path the player cannot finish or a stage that cannot be left; (b) a
  contradiction inside the record, or with the world data (census, story data); (c) a contradiction with canon lore
  or the extrapolation; (d) a breach of 0006 (a Nordic element we add) or 0035 (anything levelled); (e) the quest
  breaks the skill rule (ruling #50, quest-write §2 item 4, program-checked): a stage (a pure choice stage excepted) is not won by a skill route that can fail (25+ check, fight, lock, spell), a
  main quest lacks two ways through on different skills, a faction quest ignores its faction's skills, a stage
  does not say plainly what to do and where, or the route climbs a tree; (f) it would
  be harder to script than an average Skyrim quest (more stages, aliases, conditions, timers or bespoke scripts than a
  typical vanilla side quest needs); (g) the climax or the resolution is a procedure: an arbitration, a hearing, a
  trial, a ruling, a witnessed or spoken release, a negotiation at a table (owner, 2026-11-06: "the classic boring
  bureaucracy issue"); procedure may colour a quest, never resolve it. Nothing else is
  blocking, however much you would change it: write it as a `note` with its weight (`high`, `low`).
- **Settled is settled:** never re-raise what `review.settled` holds, or a variant, unless a change reopens it (say how).
- **Prefer subtraction:** a fix cuts or rewrites; it never adds a stage, branch, ending or mechanism a cut would answer.
- **No cap: report every finding**, blocking and notes alike. Round 1 reads the whole record. Every later round is a
  delta: only the rows changed since the last review (`git diff <last reviewed sha> -- story/data/db/` read against
  the export) and every row that cites them; the loop ends when a delta round raises nothing blocking. A line outline
  or a premise-level record is judged at its own level (spirit, beats, lore, motifs, branching, clashes); place fit
  (cells, doors, navmesh, placements) is checked when the quest is written as a full record.
- The planner, not you, decides which findings are fixed and when the loop ends.

## 1. Set-up

- Run as a fresh agent given only the quest record, the world records it cites and this skill; never the author's
  reasoning. The story database (`story/data`: `schema.sql` and `db/*.jsonl`, through `db.py`) is the one source of
  truth: read the record with `python3 -m tools.argonia_world.quest_record export <quest id>` and the world with
  `python3 -m tools.argonia_world.db query "SELECT ..."` (`fact` by `place_id`, `npc`, `npc_faction`, `stance*`,
  `culture_*`, the place's other quests). The lore: `../../../story/lore/`. Judge the quest against the BM&V place
  it names in `foundation`.
- First run `python3 -m tools.argonia_world.adaptation_check`: its `record (warning)` lines (an id not in the
  census, an unplaced speaker, a needed person with no essential, protected or fail-forward, an edit to a shared
  base, a vanilla door model, a skill gate walked round; `wiring` lines: unreachable stage, no start, a hasItem trigger for an item already held, a person or item present before the start, a topicHeardFrom speaker with no topic row; who knows what, every fact learnable) are findings already; copy them, do not re-judge them.
- Also binding: the quest index rules and coverage (`../../../story/design/quests/index/README.md` §47b–c,
  `../../../story/design/quests/index/coverage.md`), 00-overview §4 (`../../../story/design/quests/00-overview.md`), the condition
  vocabulary (`condition_term` rows; `../../../story/design/quests/85-condition-vocabulary.md` explains each term) and the style guide's journal register
  (`../../../story/design/text/style-guide.md`).
- Read the principle files the record routes to (`../quest-write/shapes.yaml`: always `principles/general.md` and
  `principles/actions.md`, the group's file, each shape's file); their checklists are part of this review.

## 2. Read it twice

1. **As the player**, knowing only `playerStart` and each stage's `learns`: from dialogue and the journal alone, can
   I tell what to do next and where? Where would I be lost, bored or unrewarded? 2. **As the designer**, below.

## 3. Checklist (answer each yes or no, with the record ids that show it; then each routed principle file's checklist)

Premise and truth
1. Can the premise be said in one sentence, and would a sensible person in Black Marsh act as it requires?
2. Is the truth a timeline of physical events, and does every clue, rumour and lie follow from it?
3. Does each person's every action pass the plausibility test given their wants, fears and knowledge?

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
15. (The program checks ids and placements, §1.) Does every `new` thing have its where and state per stage?
16. Is every change to the base world (a deeper pool, a schedule, a container) and every scripted event (a timed
    attack, a tree that sickens) written as a row, not assumed, and handed to the planner?
17. **Lore and vibe (blocking).** Read `../../../story/design/province-vibe.md` and the lore the record names,
    then check every person, role, job, place, institution, object and custom in the record against the lore
    dossiers and the extrapolation (`../../../story/lore/`, first `extrapolation/argonia-4e201-state.md`,
    `settlement-register.md`, `gap-register.md`, the place's dossier and the topics it touches). A finding is
    **blocking** when the quest:
    - contradicts canon or the extrapolation (a Nordic element, a vanilla Skyrim reference, the wrong era, an
      office or institution the lore says is gone, absent or elsewhere);
    - rests on a claim with no source that has no `L<n>` lore-check entry, or whose gap-register `QA<n>` row is
      not the least inventive reading of its anchor, contradicts the lore, or puts a §9 motif where §9 does not
      (read every `QA<n>` row the record cites);
    - gives a person a role or job that settlement and culture do not have in 4E 201 (`province-vibe.md` §3–4);
    - moves information, authority, law, trade or debt in a way that does not fit the place (`province-vibe.md`
      §5: spoken and carried by people in tribal ground; coin, barter or owed work by the place's tier);
    - uses a motif from `province-vibe.md` §9 (couriers, letters, ledgers, accounts, tallies, rolls, records,
      clerks, officials, permits, licences, passes, papers, fines, prisons) where §9 does not put it, or has more than a third of its stages hollow
      (quest-write §4b.3), or a central action of delivering, filing, counting or reading
      a record;
    - otherwise jars with `province-vibe.md` (its register, tensions or the place's fringe).
    Run `python3 ../dialogue-write/lint.py` over the stages' `journalText` and justify or flag every B10 warning.
    Name the source file and section for each finding. For a long record, split the lore reading across cheap
    subagents with short briefs (the claims to check and the files to check them in), each returning a verdict.
17b. Does the quest add to the vibe (`province-vibe.md` §10) rather than only avoid jarring with it?

Action and fit
18. Does it meet the skill rule (quest-write §2 item 4)? Name the skills each stage uses (a pure choice stage is exempt); a main quest needs two
    ways through on different skills, a faction quest its faction's skills, and every stage's text a plain next action.
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

Return every finding, most serious first, blocking ones (item 17) at the top, each with `severity: blocking` in the
record's `review.findings`, each with: the record ids, what is wrong, what a player would experience, and a proposed
fix; in a delta round, only findings on the changed rows and the rows citing them. End with the answers to the checklist as one line of ids per failed item, writing item 17 as `17(B)`.
The quest writer copies the findings into the record's `review` section with how each was answered.
