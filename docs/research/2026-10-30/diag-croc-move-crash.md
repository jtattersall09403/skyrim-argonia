# Diagnosis: croc-den, combat-trial-a, world-sample crash (batch game-12, 20261030T133637)

Read-only. Evidence: out/batch/game-12/20261030T133637 item folders, a reader pass over the stills, the crash log
fetched from the game machine (`SKSE/crash-2026-10-30-13-50-26.log`, 651 lines).

## 1. croc-den: the crocodile never fights (journey, plus one data doubt)

- Cause: the step tests the walk den with the shallows creature. `tests/journeys/croc-den.yaml:15-18` puts the player
  at `moveto croc 0 -400 0`, "on the bank 4 m south". That was written for the bank den (way walk). cf11cb0 made way
  `shallows` the default (`world/db/creature_hunt.jsonl:1`). The creature is KotM's CrocodileWaterRace, swim-only
  (DATA 0x02504040, no Walks, same row). A swim-only actor cannot path to a target on land, so it never starts
  combat. The reader confirms the player stands on dry sand in both runs (07/02, 08/02), with no enemy bar and no
  drawn weapon. AI data is not the cause: Aggression VeryAggressive, aggro 2000/1500, and AIData is not templated
  (`plugin/Argonia/Npcs/ARG_Npc_EcoCrocodile - 000876_Argonia.esm.yaml`).
- Doubt (data): the placed croc and DenShallows are at z 2328 (= 33.26 m; `.../ARG_Province - 000800_ArgoniaWorld.esm/RecordData.yaml:160,893`).
  That is above the 32.84 m surface over a floor of about 31.8 m (`world/db/build_ref.jsonl:74` has no z_m).
  The water there is about 1 m deep, which may be too shallow to count as swimming for a swim-only race. In 08/02 a
  croc-like shape sits next to the player on the shore.
- Fix: in the journey, put the player in the pool, where a swim-only ambusher can reach them:
  `player.moveto ARG_Ref_ClaywaterStationCrocodile 0 400 0`, the pool centre about 6 m north at a 2.5 m depth. Rewrite
  the comment. Optional data fix: set the shallows den's z_m to about 31.9 and move it 2-3 m into the pool so the
  creature starts submerged.
- Re-prove: on the game machine, run croc-den step attacks-near with the new moveto. Read
  `ARG_Ref_ClaywaterStationCrocodile.GetPos z` and `IsSwimming` in the same step.

## 2. combat-trial-a pandora-wired: moved 0 (game/world load, not input)

- The pad reaches the game. Expectations run in order and stop at the first failure (`tools/run_journey.py:441-446`).
  The event check `TKDR_DodgeStart` came first and passed, so the roll fired. In the same batch, smoke's roll moved
  more than 300 units.
- Cause: the duel ring was not loaded. The reader sees both stills (01-ready, 02-pandora-wired) as a flat grey void
  with black untextured terrain slivers, the player standing, and the opponent a black T-posed figure. With no
  ground or Havok under the player, the engine does not move them, so the moved check reads exactly 0 (the check
  is at `run_journey.py:317-321`). The stills are 381 KB and 478 KB, against 2.7 MB for a loaded scene.
  `tests/scenes/duel-ring.txt` ends with `player.moveto 10000961`, and the steps start after scene_s 7.4 s with no
  check that the cell has loaded.
- Fix: in the journey, have step `ready` expect the world loaded, for example `read [player] path cell...` plus a
  `wait` until the 3D is attached. If the proving-ground cell or its terrain is missing in the plugin, the fix is
  in the world; check that `tools/argonia_world/fixtures.py` generated the cell's LAND/navmesh. The 300 ms stick only
  gave 11 units in game-11 (combat.md:174), so also raise it to 500 ms as smoke does.
- Re-prove: `bat duel-ring` alone, a still after 10 s, and `player.GetPos`. Then run pandora-wired once.

## 3. world-sample: crash during `cow ARG_Province -19 58` (engine cell change; not our DLL, not memory)

- The log shows EXCEPTION_ACCESS_VIOLATION, executing at 0x01FC00000000 (a dangling heap function pointer).
  - RBP holds "cow ARG_Province -19 58", R12 is ConsoleLogPrinter, and RDI/RCX/R13 are BSMultiBoundAABB.
  - The first frame is SkyrimSE+0EAE206 (id 69036).
  - The game-6 crashes have the same signature: SkyrimSE+0EAE206, BSMultiBoundAABB
    (`docs/research/2026-10-30/lane-game-6.md:38`).
- On the stack: Livia Varinius and Signs-For-The-Cargo, the stop-1 Claywater actors whose cells were unloading.
  Stack frames are EngineFixes.dll and SkyrimSE only. There is no ArgoniaCore or ArgoniaBridge frame (both are only
  in the module list).
- Memory was not the cause: physical 5.36/15.71 GB, GPU 1.27/13.98 GB, private 6.36 GB.
- The cow was the last line of `tests/scenes/world-sample-02-cliff.txt`, so the game-6 rule (travel line last) was
  kept. The crash is in cow itself, unloading stop 1's cells. Stop 1's last steps had moved the player with the
  bridge's `teleport pos`, which is a raw `SetPosition` (`skse/ArgoniaBridge/src/ep_world.cpp:93`). That leaves the
  loaded grid out of step with the player's cell. The next `cow` then detaches a multibound that is already freed.
  This is a likely mechanism (engine use-after-free on BSMultiBound during the cell detach), not yet proved.
- Fix (code/journey): travel between stops without `cow` from a raw-SetPosition state. Either move to an interior
  holding cell first (`coc ARG_HoldingCell`, then `cow`), or make `teleport pos` use `MoveTo` with a placed marker.
  Change `tools/world_sample.py:185-191` (cow) and regenerate the scenes.
- Re-prove: world-sample s01 to s02 alone, three times (the crash has come twice in about 10 cows).

### Lead checked: "Controller Disconnected"
- The pad is not lost; the toast is the design. Each `pad` call connects a fresh ViGEm pad and disconnects it at the
  end (`infra/gpu-box/pad.ps1:14,58`), so every call raises a disconnect toast. That includes lf83's draw.
- combat-trial-a ran as item 2, before any relaunch (`relaunched_before: false`). Its B press produced
  TKDR_DodgeStart, so the input arrived.
- Minor risk: the first stick input of a call can land while XInput is still enumerating the new pad. Hold the pad
  connected for about 300 ms before the first step, or keep one pad for the whole batch.
- This does not explain moved = 0. The unloaded ring does.
