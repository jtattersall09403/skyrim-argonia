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
  `make navmesh` took about 26 min. ArgoniaWorld.esm now has 12,085 NAVM (sha256 d47d9ab3…). Deploy took 112 s.
- **After the deploy:**
  - `nav` finds 25 meshes at Claywater.
  - Livia in combat now closes 300 units on the player within 6 s. The people leave their placements by day.
  - claywater-walk steps 1-7 are green twice.
- **The night step stays red, for a second cause:**
  - At 23:00 Livia takes her sleep package (10000885) but does not move for 78 s.
  - Her bed is KotM's 088933BE, inside the station house. The house's load door (10000892, z 2675) is on its stilt
    porch, and `nav` puts that door, and the porch's foot, on no loaded navmesh.
  - Moved onto the bed by the console, she sleeps (GetSleeping 2).
  - So the package works and the path does not. The navmesh has no porch, stair or door-link triangles: the
    2.W4 navmesh's open "door triangles at load doors" item.
  - The step is marked `owed` with that reason, and the planner is told it needs a navmesh lane.

## 3. Smoke
- `smoke.py pad` green in 75 s (not reproduced: the timeout did not recur).
- The controlmap binds Quick Stats to 0x35 (SLASH), so the key exists.
- `smoke.py scene` twice: no crash. Inventory and Magic open. Journal, Tween and Stats do not open, and Map opens
  in one run of two. The roll is not seen (roll_units null).
- **Reader on the 12 menu stills:**
  - Inventory and Magic open as named.
  - The other stills lag one menu behind their names. Map-scene1 shows the Journal, and Stats shows the Tween hub.
  - Every menu panel that opens is in the parchment theme.
  - **Blocker:** the Map is Skyrim's own world map. It labels "Whiterun" (with its emblem) and shows a triskelion
    icon. Our chart view is not registered yet ("our view chart is not registered yet"), so the vanilla map
    reaches the player.
  - The Journal's Level bar keeps small knotwork flourishes (polish).
- **The cause of the lag.** ArgoniaCore's pause-hub suspend save (life.cpp LifeMenuSink:
  "saves: ArgoniaSuspend written (pause hub)") runs as the Journal or Tween opens. The save's LoadWaitSpinner then
  closes the Journal, and the menu opens late. The smoke now waits 8 s for each menu and 2 s after each close.
  The save closing the player's own pause menu is a 1.5 finding, for the life lane (outside this lane's
  ArgoniaCore scope).
- **The compass:** the reader confirms it is gone in 11 of 11 gameplay stills (claywater-walk 055541, first-place
  060102). The stills also show black polygon artefacts on the water at Claywater.

## 2. first-place
- **Camp spot:** placed; the still shows the bedroll by the road.
- **E on the camp spot runs nothing.** Data\Scripts holds no ARG_* .pex, because the Papyrus compile is owner #15.
  ArgoniaCore logs no rest. So make-camp is owed, and so is everything that needs a rest: retrieve-vastei (the
  same perk's Fragment_1), rest-at-camp, spend, rise, load-rest-save and every-family.
- **The talk steps are owed for the same reason.** E on a person runs ARG_PRKF_DialogueIntercept (OpenDialogue),
  which is also not compiled. Those steps are talk-to-takes through ask-signs, and terms-with-livia and
  terms-with-signs.
- **Side effect of the people walking:** the face-and-press-E pose can now catch a passer-by. One still targeted
  Gaius, not Takes.
- **croc-fight-1 was red:** the clay-bend ref puts the player in the water, so they swim and cannot swing, and the
  crocodile was 340 units away on land. The fight now starts on the bank, 200 units south of the crocodile and
  facing it.

## 5. Weather
- Nine Argonia scenes now `fw ARG_Weather_tannin_haze` (ours, dry-haze, realised in every group), not Skyrim's
  0000081A. Riverwood (a vanilla control place) keeps it. In game `fw 10000812` took (`weather` read).

## Runner
- `owed: <reason>` on a step: not run, listed in the report's `owed`, the journey goes on (test_run_journey).
