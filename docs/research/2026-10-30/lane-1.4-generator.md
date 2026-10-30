# Lane 1.4-generator: the quest generator's first rung (2026-10-30)

## Delivered
- `tools/argonia_world/quest_gen.py`: LF83's rows → QUST intermediate (stages 0 + 10/20/30/40/41/42/90/92/93 with log
  entries, 7 objectives with text and no targets, 15 Optional aliases, fragments per stage, priority 40 from tier 3)
  → `tools/ArgoniaGen/QuestRecords.cs` (registered in `Generate.cs`; `intermediate.build` adds the layer) → ARG_Q_LF83
  (000852:Argonia.esm), `plugin/Argonia/Quests/ARG_Q_LF83 - 000852_Argonia.esm.yaml`.
- `papyrus/generated/ARG_QF_LF83.psc`: begin fragments only. The native calls are listed in
  `docs/research/journals/quests.md`.
- Planner ruling applied: the stage graph is data (`skse/core/generated/argonia/core/quests.h`), and the pure-C++
  `quest_runtime` steps it on a fact change; no condition is evaluated in Papyrus.
- `quest_state` and the QSTA family in `skse/core/schema/families.json` (flags, counters, deeds per faction and class),
  bound in `test_roundtrip` (green).
- Tier protection (`check_tiers`) and the dead-NPC fail-forward (stage_walk's 0138 rule run on the generated graph).

## Measured
- L2 `core.quest_runtime` on LF83: the start; from 10, 20 and 30 each keeper's death → 92/93, the wet season → 90,
  the bribe → 41, both dead → 92; main path 10→20→30→40, 30→42; death overrides progress; completed objectives
  kept; an unanswered fact never holds; endings rest. ctest 25/25.
- L2 `test_quest_gen`: the generated graph's walk equals the record's (edges, reached, no errors). L1: the records
  check is clean on LF83 and fails on purpose for an objective target, a visible map marker (intermediate and YAML),
  placeholder text, an Essential alias, a higher-tier touch, a missing poler fail-forward and an If in a fragment.
  The test file has 10 tests.
- `make plugin` run twice: identical out/Argonia.esm sha256 and identical plugin/Argonia/ tree. One stage text
  changed in the intermediate gives one differing Spriggit file (`Quests/ARG_Q_LF83 - 000852_Argonia.esm.yaml`).
  The round trip is green in plugin-check. `make plugin` took 2:18 at a 1.14 GB peak RSS.
- `make check`: CHECK GREEN in 1:46 at a 290 MB peak; unit 226 passed.

## Commits
a9428a7 (core), b45f233 (generator), f3e1cde, 7ccb595 (1.3 items + LF83 + plugin, at the planner's request).
- **Incident:** a9428a7 swept 1.3-rules' uncommitted topics hunks into four shared files. I then built b45f233
  from a stale view after 1.3-rules committed 9be2520, and it dropped that registration again. f3e1cde restores
  it. HEAD is green.

## Owed
- Declare the ten natives in `skse/ArgoniaCore/papyrus/ArgoniaCore.psc` and implement them in ArgoniaCore; the
  fragments do not compile without them. Also owed in ArgoniaCore: the adapter that calls `quest_runtime::step`
  on fact changes for watched quests and applies SetObjectiveCompleted/SetStage.
- Compile the .psc on the game machine (`infra/gpu-box/records_jobs.sh`).
- Fill the aliases (ForcedReference) once people and things are placed (2.W5).
- The records check runs in `unit` through pytest; `skse/check.sh` does not run `quest_gen --check` (a path I do
  not own). Changing LF83's conditions makes quests.h stale until `python3 -m tools.argonia_world.quest_gen` is run.
- L4 from `bat quest-board` (1.4 acceptance) waits on the natives and the adapter.
