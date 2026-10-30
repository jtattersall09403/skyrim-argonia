# diag5: game-17's batch g17all (read-only)

Evidence: /home/ubuntu/wt-game17/out/batch/g17/20261030T225900/ (NN-<journey>-1-*), log ~/.argonia/jobs/g17all.log.
wt-game17 HEAD 28a9a5a (includes lane-code-fix 1aa3444). 31 journeys; reds below, each with one cause and one re-prove.

## 1. grow-at-rest CRASH (crash-2026-10-30-23-18-37) - our code, same bridge frame, not the guard
- Fault ArgoniaBridge.dll+5E543 `jmp [rax+0x30]`, rax 0; probable frames bridge +46C9A/+478A2/+5962 then skse64 +199AF
  (the SKSE task); RSI/R14 Character "Deserter" 1000088C, R13 Steel Sword. Same shape as diag4's +5DC33 (the build grew).
- Steps 1-4 passed; it died in step 5 `pending-level` (`dev-grow 1000088C 1 2000`), 11 s after the rest load.
- The guard took: the deserter was moved beside the player and enabled (grow-at-rest.yaml:58-59), so it is alive,
  loaded and has a process, and `actor_unready` (ep_world.cpp:292) passes. The crash is past the guard, inside the
  blow loop: `target->RestoreActorValue` / `target->DamageActorValue` (Actor's inherited ActorValueOwner helpers)
  use the static SE base offset; on 1.7.104 ActorValueOwner is at +0xB8, so the vtable read is 0 and the tail call
  through slot 6 (+0x30, RestoreActorValue, which DamageActorValue forwards to) faults.
- Fix (already uncommitted in wt-game17, skse/ArgoniaBridge/src/ep_dev.cpp:105-108): call through
  `avo = target->AsActorValueOwner()` for Restore/Damage. Also grep both DLLs for any other `actor->XxxActorValue(`
  outside `AsActorValueOwner()` (same class). Build the bridge, deploy.
- Re-prove: grow-at-rest alone, past pending-level.

## 2. w3-weather-stills CRASH at 16.8 s and water-swim CRASH at 18.5 s - engine, our travel line
- Both: exec 0x022300000000, stack scan 69036+0x56 (SkyrimSE+0EAE206), 21891, 442669; R12 ConsoleLogPrinter, RCX
  BSMultiBoundAABB. Identical to diag4 Case 1/2 (the culling job on a console-driven grid change). No mod frame.
- Not `fw` or `set gamehour`: steps were empty; the crash is during the scene, whose last line is the travel
  `cow ARG_Province -13 25` (tests/scenes/world-sample-06-marsh.txt:9; water-swim's scene: `cow ARG_Province -33 14`).
  ArgoniaCore logged `weather: season 0` 0.8 s before (the GameMonth set landing), then the grid load crashed.
- diag4 fix 1 (f4d8056) moved the probes and smoke to placed markers but left every generated stop scene on `cow`:
  tools/world_sample.py:243 `travel_line` still returns `cow ARG_Province {cx} {cy}`; 17 scenes in tests/scenes start so.
- Fix: world_sample.py:243 returns `player.moveto <stop marker>` (one XMarker per stop in the world DB, the same
  mechanism as the probes and CLAYWATER_REF at :264), regenerate the scenes; same for water-swim's scene source.
- Re-prove: w3-weather-stills and water-swim, 3 runs each, 0 crashes.

## 3. lf83-components stage-20 - the check
- The notice was sent: ArgoniaCore.log `journal notice 3: quest.local.lf83 clue 11` 23:20:44.792 and `entry 20 merged
  into the last (event still sent)` 44.975 (views.cpp:313-335, the new build). The sink works in the same run:
  talk-takes and hear-station passed their ArgoniaJournalNotice expects, and lf83-endings passed all four.
- But both came in step 7 `hear-landing`: the two-charges topic at the landing completes objective 11 (log 104
  `objective 11 completed (topic heard)`, 105 `SetStage 20`). Stage 20 is entered when hear-station and hear-landing
  are done (quest_stage/quest_objective rows for quest.local.lf83). Step 8's clay-bend topic (51.44) changes no
  journal, so its 4 mod events hold no notice. GetStage >> 20 passed in step 8 only because it was already 20.
- Fix: tests/journeys/lf83-components.yaml: move step stage-20's GetStage 20, JournalEntries `20 0` and
  ArgoniaJournalNotice expects into `hear-landing` (:69-72); stage-20 keeps the KnowsTopic reads.
- Re-prove: lf83-components alone.

## 4. quest-board fail-forward-92 - our stage logic (the expectation is right)
- Stage 92 is `ending: failed` (quest_stage.jsonl, id 92). ArgoniaCore set it (23:13:10.676) and logged entry 92 kind 2.
- The generated fragment for an ending stage is AddJournalEntry, the ending actions, Complete/FailAllObjectives and
  UnwatchQuest (tools/argonia_world/quest_gen.py:174-180) - never `Stop()`, so the QUST stays running. Nothing in
  the record keeps it running: our dialogue runs from ArgoniaCore's state, and GetStage still reads 92 after Stop.
- Fix: quest_gen.py:179-180 append `Stop()` after `ArgoniaCore.UnwatchQuest(self)`; a test in
  tools/argonia_world/tests/test_quest_gen.py that every ending fragment ends with Stop(); regenerate + `make plugin`.
- Risk: post-ending topics conditioned on the engine quest; check lf83-endings still passes.
- Re-prove: quest-board alone, then lf83-endings.

## 5. Further reds
- attributes mirrors-equal (our code): `core GetAttribute speed` returned -1 (kept -1, mirror 60). The bridge arg is
  made a BSFixedString (natives.cpp:333) and read back by Str(); the engine's string pool is case-insensitive and
  hands back the first-interned casing ("Speed", a behaviour-graph/AV name), so `attribute_named` (skse/core/src/
  seam.cpp:398-402, exact compare) misses. Fix: compare case-insensitively in attribute_named and the skill lookup
  (seam.cpp:223-224), or take the bridge arg as std::string; unit test with "Speed". Re-prove: attributes.
- fight-archetype its-light-hit (check, likely): 0 hit events in 8 s. Reader on 03-its-light-hit.png: the deserter is
  1.5-2 m away, turned away, no weapon drawn, not attacking. `startcombat` is issued before `player.moveto` (yaml:20),
  so the AI had started combat at the old distance. Fix: moveto first, then startcombat, `within: 12`. Re-prove: alone.
- ui-sweep favorites and ui-probe frames-open (candidate, one class): no FavoritesMenu after Q, and 0 frames
  ("paused or in a menu?"); the log shows PrismaUI_FocusMenu and Cursor Menu opening after the chart step, so a focus
  menu left by the chart (28a9a5a: the chart stays over the hidden MapMenu) still holds input. Check: the `menus`
  read right after `chart ready closed`; fix the chart close to close its focus menu. Re-prove: ui-sweep, ui-probe.
- die-and-recover take-pile (candidate): the raw `teleport pos` to the pile landed the player at the rest wake point
  (-3381.3, 752.2), so ArgoniaCore's recovery moved him after the bridge's SetPosition. Fix: wait for recovery's done
  line before the move, and use moveto to a ref placed at the pile. Re-prove: die-and-recover.
- suspend-save in-combat-drop (candidate): the croc is moved and `startcombat` sent, yet the player is not in combat;
  earlier rests log the croc rows as disabled (`respawn: ... is disabled; not reset`), so the ref may be disabled.
  Fix: `enable` it before moveto (as grow-at-rest does). Re-prove: suspend-save.
- menus-quit quit-confirmed (unproven): no `ArgoniaSuspend written (quit)`; no Core line shows the confirm reached.
  Needs the step's still read to see where the pad path stopped.
