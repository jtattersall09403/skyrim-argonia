---
name: quest-build
description: Take Argonia's quest records into the game - compile every form, check them as a set, seed the plugin with the one generic builder, round-trip it, read the built quests back and compare them with the designed forms to zero, run the quest and placement checks, recompile the generic scripts only when they changed, play the built quests on paper, post the owner's walk check and deploy when no stream is live. Use once a quest's dialogue has passed its paper playtest, and whenever a record that is already built changes.
---

# Building quests into the game

Before this: [quest-playtest](../quest-playtest/SKILL.md) after dialogue. After this: quest-playtest on the built
plugin, then the owner's walk. The path is in [quest-system](../quest-system/SKILL.md); how a form becomes records is
[quest-form](../../../docs/design/quest-form.md) "How a form becomes records". No quest has a builder or a script of
its own: what goes wrong in a build is fixed in the record, or reported to the builder's lane, never worked round in
one quest. Every step runs on the build VM, the machine the agents work on, where the game data and the staged
load order are; the seed and the deploy run under `tooling/job_guard.sh`.

## 1. The forms, as one game

1. `python3 -m tools.questform compile --all --out out/<lane>/questform`, then
   `python3 -m tools.questform check --set out/<lane>/questform`: each quest's own rules and the set's (each quest
   started one way, every stage another form names exists).
2. `make questform reach`: the gate's form check against `story/data/questform_owed.json` and every compiled quest
   walked to a completed ending. A quest that now fits leaves the owed list with `python3 -m tools.questform owed
   --write`.

## 2. Seed the plugin

`tooling/job_guard.sh run seed -- bash tools/ArgoniaPlugin/plugin.sh seed`, then `tooling/job_guard.sh wait seed`.
The seed compiles every record that fits, builds every form into `plugin/Argonia` (Spriggit YAML, our source), and
makes every person of ours and of Black Marsh & Valenwood killable. The block test is not in it: `seed --blocktest`
adds it for an in-game diagnosis only, and that tree is never committed or deployed
([block-test](../../../docs/design/block-test.md)).

- **The seed builds the whole tree**, so a lane seeds in its own worktree (main's quests and its own) and a lead
  seeds once more on the merged tree before deploy. Quests the lead has named as being rewritten whole (`rewriting`
  in `plugin.sh`) are left out when refused; every other quest's refusal fails the seed.
- **A refusal** is one line, `questform <quest>: <rule>: <what>`, and fails the seed (the
  [quest-form](../../../docs/design/quest-form.md) "refusals" list says what each rule means). Fix it in the record:
  a spot with no navmesh within 300 units is moved to a measured one (`bash tools/ArgoniaPlugin/plugin.sh inspect
  navnear:<x>:<y>:<z>`, `cellgrid:<cell>:<x>:<y>:<z>:<step>`), a word that resolves to no record is corrected, then
  compile and seed again. `seed --refused-ok` only shows what else would build; nothing seeded that way ships.
- **The build log** says where each person who speaks first stands and how far from the door, and names each person
  who stands with no navmesh near and will not walk. Read both.

## 3. Read the build back

1. `bash tools/ArgoniaPlugin/plugin.sh check`: the plugin serialised back with no difference from `plugin/Argonia`
   (the Spriggit round trip), and every override read back.
2. `bash tools/ArgoniaPlugin/plugin.sh questform-read out/<lane>/built`: every form-built quest turned back into its
   form from the plugin alone.
3. `python3 -m tools.questform diff out/<lane>/questform/<quest>.json out/<lane>/built/<quest>.json` for each quest,
   to zero differences. A difference means the build or the design is wrong: fix the one that is, never both.
4. `bash tools/ArgoniaPlugin/plugin.sh questcheck` and `bash tools/ArgoniaPlugin/plugin.sh placecheck`: 0 failures
   (every quest's stages, starts, endings, offers and doors; every person on navmesh and not inside a static, every
   thing resting on its surface).
5. `bash tools/ArgoniaPlugin/plugin.sh inspect silent`: every person the plugin places has a line.

## 4. The generic scripts

The scripts in `papyrus/` (`ARG_QuestStages`, `ARG_Effects`, `ARG_LineEffects`, `ARG_AliasEffects`) serve every
quest; a quest's results are rows in their properties, so a new or changed quest needs no recompile. Recompile only
when a `.psc` changed (a new operation, a fix): `tooling/job_guard.sh run papyrus -- bash
infra/gpu-box/records_jobs.sh papyrus`, which compiles on the play machine with the Creation Kit's compiler and skips
an unchanged set. A new operation is added to the block test (`tools/questform/blocktest/`), which `plugin.sh
questform-test` builds and reads back off game; in game it is proven by the owner's walk of the first real quest
that uses it. Never compile or deploy while the owner streams.

## 5. Play the built quest

[quest-playtest](../quest-playtest/SKILL.md) moment 3: one careful player on the read-back forms (`--source built`).
Commit `plugin/Argonia`, the records and the runs together, by path.

## 6. The owner's walk check

Add the check to [owner-walk-checks](../../../docs/owner-walk-checks.md) and post it with `python3
tooling/owner_inbox.py --post check`. In plain English, assuming no context: whether a new game is needed, where to
go (the place by the name the game shows), whom to talk to and what to do, what passing looks like (the line, the
journal entry, the marker on the compass and the map, every quoted word copied from the read-back forms), and how to
reply. The walk is real quests only, the fewest that prove what was built: compute from the compiled forms which of
the generic scripts' operations, triggers and conditions each step makes run, choose the shortest walk that runs
every operation any quest uses at least once (a console `coc` to a cell or `setstage` to reach a far step), and end
the section with a two-column table, operation and the step that proves it, naming the operations no quest uses.
The rest rests on the read-back, the comparison and the paper runs.

## 7. Deploy

`tooling/job_guard.sh run deploy -- make deploy`, then `tooling/job_guard.sh wait deploy`. It sends the plugin, its
ini, the start-quest list and the compiled scripts to the play machine, and refuses while a stream is live: wait for
the stream to end and deploy then. Stop the machines when done (`tooling/agent_stop.sh`).
