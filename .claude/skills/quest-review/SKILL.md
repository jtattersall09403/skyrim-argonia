---
name: quest-review
description: A fresh reader's review of one Argonia quest record (or a line's record) against the quest ceiling, the owner's bar and the design principles' checklists, as a player and as a designer, with one shared bar for what is blocking. Use after quest-write produces or revises a record, before the paper playtest and before any dialogue is written; run by a quest-reviewer agent that has not seen the author's reasoning.
---

# Reviewing a quest

Before this: [quest-write](../quest-write/SKILL.md) leaves a record whose form passes `check` and `reach`. After
this: the writer answers every finding, then [quest-playtest](../quest-playtest/SKILL.md) plays the designed form.
The path is in [quest-system](../quest-system/SKILL.md). The review judges whether the quest is good, believable,
true of the built world and buildable inside the ceiling, while changing it is cheap.

## 1. The bar

**Blocking** means only:

- **(a) Cannot be finished**: a stage that cannot be reached or left; a way forward that a new character cannot take
  and that has no other way on a different skill, a price or a fight; a check on hearing a task, a hand-over or a
  report; a death that leaves the quest stuck with no failed ending.
- **(b) Contradiction**: inside the record, with the world data (census, story data), or between the record and its
  compiled form.
- **(c) Lore**: against canon or the extrapolation, or resting on an unsourced claim (checklist 19).
- **(d) A Nordic element** we add, or anything levelled against the player.
- **(e) The skill rule**: a step that asks something of the player and names no skill, or whose only way cannot go
  wrong; a main quest without two ways through on different skills; a faction quest that ignores its faction's
  skills; a step whose entry, objective and target do not say what to do and where.
- **(f) Outside the ceiling**: anything [quest-system](../quest-system/SKILL.md) does not list, even where the form
  would compile it (a line or journal entry that implies a person walks for the quest, an event staged in view, a
  stage that waits on the player reaching a place); a switch on or off not away from the player; more than one person
  speaking first.
- **(g) Untrue of the built world**: a place, person or thing that is neither a placement row nor in the census; a
  spot not measured; a line, prompt or journal entry that describes what is not there, work the person is not seen
  to do, or something the game's systems do not do; a place named for what nothing built reads as.
- **(h) A procedure as the play**: a climax or resolution that is a hearing, ruling, trial, witnessed release or
  negotiation at a table; a central action of delivering, filing, counting or reading a record.
- **(i) A new player cannot tell what is going on**: a name or local word used before it is given; a choice whose
  options are not named before it is made; a join with nothing said of what it is, whom it serves, what it wants,
  what it pays and why to hesitate.
- **(j) An outcome that is only words**: an ending or a choice's outcome that differs from another only in what is
  said or in a standing (a stored number, regard, rank) with nothing it opens or shuts that the player can use; one
  outcome better in play than another in every column of its outcome table; an outcome table row with no form result
  that builds it ([choices.md](../quest-write/principles/choices.md)).

Nothing else is blocking: write it as a note with its weight (`high`, `low`), ranked by what a player would notice.

- A failed check that stays closed until the player returns stronger is allowed.
- **Settled is settled**: never re-raise a finding the record's `review` already answers with a reason, or a
  variant of it, unless a change reopens it (say how).
- **Prefer subtraction**: a fix cuts, or rewrites a step with [principles/general.md](../quest-write/principles/general.md)'s
  table of dramatic jobs; it never adds a stage, branch, ending or mechanism a cut would answer.
- **Rounds.** Round 1 reads the whole record. A later round reads only the rows changed since the last review
  (`git diff <last reviewed sha> -- story/data/` read against the export) and every row that cites them; the loop
  ends when a round raises nothing blocking. A line record or outline is judged at its own level (spirit, arc, lore,
  motifs, branching, clashes); placements (g) are checked on a full record.
- The lead decides which notes are acted on and when the loop ends.

## 2. Set-up

- You are a fresh agent given only the quest id, the world data and this skill; never the author's reasoning.
- The record: `python3 -m tools.argonia_world.quest_record export <quest id>`. The world:
  `python3 -m tools.argonia_world.db query "SELECT ..."` (`fact` by `place_id`, `npc`, `npc_faction`, `stance*`,
  `culture_*`, `bmv_*`, the place's other quests). The lore: `story/lore/`; the vibe:
  [province-vibe](../../../story/design/province-vibe.md); the bar: [owner-bar](../../../story/design/owner-bar.md).
- Run first, and copy every line about this quest as a finding without re-judging it:
  `python3 -m tools.questform compile <quest id> --out out/<review dir>`, then `python3 -m tools.questform check`
  on the form (each failed rule is blocking (a) or (f)); `python3 -m tools.playtest reach` on it (each unreached
  stage is blocking (a)); `python3 -m tools.argonia_world.adaptation_check` (its `record` and `wiring` lines).
- A built quest: also read it back (`bash tools/ArgoniaPlugin/plugin.sh questform-read <dir>`) and run
  `python3 -m tools.questform diff <designed> <built>`; every difference is blocking (b).
- Read the principle files the record routes to ([shapes.yaml](../quest-write/shapes.yaml): `general.md`,
  `actions.md`, the group's file, each shape's file, and `choices.md` for a quest or line with a choice or more than
  one ending). Each principle is part of this review: a record that breaks one
  is a finding, citing the principle's source tag. The skill catalogue and each line's leaning:
  [skill-uses.yaml](../quest-write/skill-uses.yaml), [profiles.yaml](../quest-write/profiles.yaml).
- A quest of a line: read its outline in `story/design/quests/lines/<line>.md`; a difference from it is a finding.

## 3. Read it twice

1. **As a new player**, knowing only `playerStart` and each stage's `learns`, the entries, objectives and the
   topics' intents: what do I think is going on, what do I do next and where, whom do I trust? Where would I be lost,
   bored or unrewarded? What would I retell?
2. **As a designer**, with the checklist below.

## 4. Checklist (yes or no, with the record ids that show it; then each routed principle file's checklist)

Premise and truth
1. Can the premise be said in one sentence, and would a sensible person in Black Marsh act as it requires?
2. Is the truth a timeline of physical events, and does every clue, rumour and lie follow from it?
3. Does each person's every action pass the plausibility test given their wants, fears and knowledge?

The trail
4. Does each conclusion have at least three clues in at least two forms?
5. Can the player finish after missing any one clue, failing any one check, or going in another order?
6. Does the player find out or decide something, rather than being told?

Play
7. Is each thing to do next its own stage, with an entry that tells that step only (first person, past tense, "I'm
   to ..."), an objective in the imperative and a target switched on at it? Can the step also be followed from the
   entry's words (landmark, direction, a word for how far)?
8. Can the player say each prompt with what they know at that stage, and is each a sentence? Does every question a
   speaker asks have reply topics, and every offer the result that delivers it? Does any line refuse while it moves
   the quest?
9. Is every hand-in gated on the thing held, however it was got, and does a thing held early still move the quest?
10. Does each check have its own fallback line naming what would change it, and is no threshold written in a prompt?
11. Is any task still offered or described after the quest has ended? Does each ending leave its people a greeting
    true of that ending, and does a line shared by several endings say only what is true of all?
12. Is any fact given to two speakers in one place and stage window?
13. Is there more than one approach somewhere, with different costs, and is the quest long enough beside comparable
    Morrowind, Oblivion and Skyrim quests?

Who can die
14. Does every line read sensibly with each named person dead, or is that person a who-must-live row with a window
    and a failed ending that says so? Does a main or faction quest's row show its message, and a minor quest's not?
15. Does each death that moves the quest belong to a hostile person (fixed level, a reward in proportion), a
    who-must-live person or a killing marked the player's choice?

Endings and rewards
16. Does a standalone quest, or a line as a whole, have at least two endings with different costs the player will
    feel? Does each choice and ending carry its outcome table, and does each row give and cost something the player
    can use the next day (a power, a thing, a recipe, a trader, a trainer, a door, a bed, a group's peace), built by
    a form result? (j)
17. Would a player who chooses only for the reward still have a real decision: are the outcomes different in kind,
    with none better in every column and none that only punishes? Is the trade told before the choice? (j)
18. Is every reward concrete, fixed, proportionate and tied to the story?

Lore and vibe (blocking, c)
19. Check every person, role, job, place, institution, object and custom against `story/lore/` (first
    `extrapolation/argonia-4e201-state.md`, `settlement-register.md`, `gap-register.md`, the place's region file in
    `story/lore/regions/`) and
    province-vibe. Blocking where the quest contradicts canon or the extrapolation; rests on a claim with no `L<n>`
    entry or on a `QA<n>` gap row that is not the least inventive reading of its anchor; gives a person a role the
    settlement does not have in 4E 201 (§3 and §4); moves information, law, trade or debt against §5; or uses a §9
    motif where §9 does not put it. Run `python3 .claude/skills/dialogue-write/lint.py <file> --race argonian` over the journal texts and
    justify or flag every B10 warning. For a long record, split the lore reading across cheap subagents, each given
    the claims and the files to check them in.
20. Does the quest add to the vibe (province-vibe §10) rather than only avoid jarring with it?

Fit
21. Do the actions follow from the truth and the place, lean to the line's profile, and vary from the quests around
    it? Is each `shapeData` section real (what the drama turns on, never a register of records)?
22. Is the quest built on its foundation or its outline, and is each change an improvement?
23. Do the cast match their `npc` rows (race, sex, role) and the roster, with any difference marked `invented`?
24. Will the player understand every name and thing when first met?

## 5. Report

Return every finding, most serious first, blocking ones at the top with `severity: blocking` and their letter, each
with the record ids, what is wrong, what the player would meet and a proposed fix (a cut, a rewrite with a dramatic
job from general.md, a measured spot); in a later round, only findings on the changed rows and the rows citing them.
End with one line of ids per failed checklist item, marking blocking ones `(B)`. The writer copies the findings into
the record's `review` section with how each was answered.
