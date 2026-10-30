# Lane game-8: the people's AI, the camp, the smoke (2026-10-30, from 06:10 UTC; in progress)

## 1. The people "have no AI": the console read was the wrong oracle; the province has no navmesh
- **New bridge read `actors [radius] [ref...]`** (ep_world.cpp): the engine's process switches, every actor in the
  four process lists near the player, and named refs: process level, own AI flag (kProcessMe), current package.
- **(a) the vanilla control** (`claywater-control`, Golldir 00019FE8 placed at Livia's work spot), noon:
  - switches all on (high, middle, low, schedules, movement, detection): AI was not toggled off;
  - Golldir (FF00083C), Livia (100008DB), the Livia copy (FF000D75): all high process, AI on, a package each
    (Golldir 000A9595, Livia 10000884); Signs, Takes and Gaius the same (10000878, 10000880, 1000087C);
  - **the console's GetCurrentAIPackage and GetCurrentAIProcedure read -1 for vanilla Golldir too**: the -1 that
    game-7 and npc-ai read is the console on a template (PKCU) package, not a missing AI. Not an oracle.
  - StartCombat on Livia and Golldir: both in combat (state 1, weapon out); Golldir fled 1,200 units, Livia stood
    (65 units in 20 s), 310 units from the player.
  - `nav` at Claywater: **"no navmesh in the loaded cells"**; out/ArgoniaWorld.esm holds **0 NAVM, 0 NAVI**.
- **(b) not run:** it asks whether ArgoniaCore stops the AI, and the engine shows every person with a process,
  AI on and a package. ArgoniaCore installs no hook (event sinks only) and calls nothing that stops AI.
- **Cause:** `make plugin` (pipeline.master_world) rebuilt ArgoniaWorld.esm without the navmesh. Only
  `make navmesh` (26 min) writes NAVM, and the next `make plugin` (every full deploy) dropped them. The province
  has never had a navmesh in game, so the people stand where placed, and none can reach a bed at night.
- **Fix at source:** master_world carries out/navmesh/province (the last `make navmesh`), and warns when there is
  none or when it predates the ground (`make navmesh` now writes its terrain stamp). L2 test_pipeline (failed on the
  old line). deploy.sh refuses an ArgoniaWorld.esm with no NAVM (ARGONIA_NO_NAVMESH=1 overrides).
  `make navmesh` running; the L4 re-run of claywater-walk follows.

## 3. Smoke
- `smoke.py pad` green in 75 s (not reproduced: the timeout did not recur).
- The controlmap binds Quick Stats to 0x35 (SLASH), so the key exists.
- `smoke.py scene` twice: no crash. Inventory and Magic open. Journal, Tween and Stats do not open, and Map opens
  in one run of two. The roll is not seen (roll_units null). A probe after the smoke showed the Journal still open
  (J's event was a close), so the menu chain falls out of step after Magic. Being diagnosed.

## 5. Weather
- Nine Argonia scenes now `fw ARG_Weather_tannin_haze` (ours, dry-haze, realised in every group), not Skyrim's
  0000081A. Riverwood (a vanilla control place) keeps it. In game `fw 10000812` took (`weather` read).

## Runner
- `owed: <reason>` on a step: not run, listed in the report's `owed`, the journey goes on (test_run_journey).
