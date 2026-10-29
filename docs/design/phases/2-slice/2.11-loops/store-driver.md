<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.11-loops/store-driver.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Store driver and quest panel (2.11 b)

Code: `packages/narrative/src/driver/` (driver.ts, fixtureHost.ts, scripts.ts, cli.ts) and `packages/scene/src/narrative/` (questPanel.ts, QuestPanel.tsx).

## The driver (standard 5)

- `driveQuest(record, script, makeHost, extra?)` starts the quest in a new host (or runs the script's `opening` asks, for a quest its giver's line starts), then runs the script's steps. A step is `{ atStage, facts?, actions?, asks? }`: outside-world facts the host answers from, authored actions, then topics asked through the host's `ask(speaker, topic)` (a real dialogue session; the one host `driver/worldHost.ts` plays `data/scripts/<code>.json`); each runs once, on the stage it names, and the narrative ticks after it.
- A script fails (`DriveError`) when the quest is left running, a step names a stage the quest lacks or never reaches, or the ending differs from `expectEnding` / `expectStage`.
- `makeHost(extra)` builds a fresh host (`DriveHost`: narrative, `setFact`, `serialisers()`). `extra` is a list of `{ id, make(world) }`; `make` runs once per host and gets the host's facts and `setFact`, so a sibling family (inventory, standing, crime) slots in and no two hosts share state. `fixtureHostFor(records, onCall)` is the stock host (knowledge family, fixture world terms, recording handlers).
- `driveFromEverySavePoint` replays to each point (start, then after each step), snapshots through `createSaveRegistry`, checks the replay equals the uninterrupted run's save, restores the JSON-round-tripped save into a fresh host, checks snapshot-restore-snapshot is equal, plays the rest, and checks stage, state, journal and final save equal the uninterrupted run's. Outside facts are the world's, not the save's: they are re-set on the fresh host before the restore, as a loaded game rebuilds the world.
- CLI: `npx tsx packages/narrative/src/driver/cli.ts` reports `world quests driven: 0` (no records authored; `WORLD_SCRIPTS` is where the quest lanes add theirs) and runs the fixture's two scripts.

## Measured

- `npx vitest run packages/narrative/src/driver packages/scene/src/narrative`: 2 files, 12 tests green (driver 8, panel 4).
- Driver runs on FIXTURE_QUEST: complete ending 3 save points (stages 10, 20, 40), failed ending 2 (10, 30); each resumes to the same state, journal and save. With an extra inventory family: the save holds `inventory-fixture, journal, knowledge, quests` and the family reads `{items: 1}` at the end.
- Family round trips (snapshot, restore, snapshot equal): quests, journal, knowledge, and the extra mirror family at every point.
- Failure tests: a script that never unblocks stage 10, a missing stage, an unreached step, a wrong expected ending, and a quests restore that loses the flags (the save-point run catches it).

## The panel (0149)

- `questPanelModel(source)` reads quests, journal and record lookups only (the source type has `get()` on the stores, no `set`), and returns running and ended quests with stage, state, objectives with done marks, journal lines, plus flags and counters.
- `QuestPanel` takes one prop, `narrative` (that read side); no callbacks. The test asserts no buttons or inputs render and the stores are byte-equal after render.
- Seam: the studio registry is `DevSlot` in `apps/world-studio/src/hud/DevPanel.tsx` (groups are a closed union `DevGroup`); mounting needs a group and the session's narrative in `App.tsx`, both outside this lane's paths.
