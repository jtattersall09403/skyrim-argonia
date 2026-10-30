# Lane game-12: the batch runner, combat A restored, LOD unblocked to generation, and a batch starved by LOD (2026-10-30, ~11:58 to 12:55 UTC; hand-off at the context marker)

## Done (commits 31e99f3, 6692ce5, cca0fe9)
- **tools/run_batch.py** (with tools/tests/test_run_batch.py, 8 tests). It runs journeys and scenes in order under
  one `job_guard --gpu` job and keeps going past failures. It relaunches the game when SkyrimSE's private memory is
  past `relaunch_mb` (default 6000), every N items, or after a crash. A `chain: true` item skips the save load. It
  writes `out/batch/<id>/<stamp>/summary.json` after every item: pass/fail, the failing step and its reason, the
  seconds, the scene apply's seconds, MB before and after, and the time per step class (launch, scene apply,
  steps). The batch file is tests/journeys/batches/game-12.yaml.
- **run_journey.py**
  - An unchanged scene is not put on the machine again.
  - A chained run can skip the load.
  - New expectations: `event {..., absent: true}`, and `log {name, contains}` (SKSE log lines written since the
    step began).
- **run.sh desktop jobs are named (`DESKTOP_JOB`)**, so LOD's hours-long GUI job and the bridge's launch, stills
  and pad can run side by side. Before this, they shared one scheduled task.
  - While making this change, I edited run.sh under a running `run.sh`. Bash reads a script lazily, so the edit
    broke the first combat-A run ("syntax error near done"). Never edit run.sh while a job uses it.
- **Journeys**
  - New: w3-crime (strike Livia; GetCrimeGold on her crime faction moves) and menus-quit (Tween and our journal
    stay open for 5 s; the System tab's Quit by the pad writes ArgoniaSuspend (quit)).
  - lf83-components asserts the ArgoniaJournalNotice mod event at each stage and clue. It also checks the thing
    hooks: the perk, E on the well head and on the mortar tub, and the ledger read sets ledger-read.
  - lf83-endings asserts the notice at endings 41, 90, 92 and 93.
  - smoke's journal step reads our journal view.
- **Combat A restored: `stack.py verify` 22,573 recorded, 0 bad, 0 unrecorded, VERIFY OK.**
  - Cause of two failed tries: going back to A after B2 kept `MO2/tools/nemesis` in the local stage. The push sent
    it, and A's Pandora step ran Nemesis, which hung at 0 CPU.
  - Fix (6692ce5): the stage prunes the tool folder of any row outside the set. Test in test_stack_combat.py.
- **Deploy** from a HEAD worktree (692edc4 plus my commits; the plugin was regenerated identical to the committed
  plugin/, with 12,085 NAVM). `DEPLOY OK`.
  - Timings: send 18 s, launch 52 s, scenes 35 s, base save 14 s. The SKSE build took 225 s, with ctest 33/33.
  - 2dab64e works on a load: "new character: argonian male marsh-guide (health 44)", then carriers written.
  - The base save itself has no sheet. A `coc` from the main menu sends neither kNewGame nor kPostLoadGame, so
    every journey that loads argoniabase makes the character at its load.
- **bridge.ps1 prepare** lays a DLL or ESM only when its length or write time changed. A relaunch had been copying
  the 229 MB world ESM every time.
- **LOD unblocked up to generation.**
  - The tools are laid and all three surveys are OK (window dumps in out/lod/logs). The vantage still "without" is
    out/lod/vantage-without.png.
  - Blocker found: xLODGen lists a worldspace only if `Data\LODSettings\<WRLD>.lod` exists. Ours had none, and
    terrain failed with "ARG_Province not in the worldspace list".
  - Fix: infra/gpu-box/lodsettings.py makes the file from the land cells: SW -160,-96, stride 256, levels 4..32,
    aligned to 32 so FWMF's block 32.0.0 keeps its cell. lod.ps1 lays it through the LOD mod (test_lodsettings.py).
  - Also fixed in lod.ps1:
    - Start-Tool returned [string, process];
    - the pop-up watch stopped on the VCL's own blank windows;
    - prepare now kills a tool that a failed step left open, which held Data's BSAs.
  - **ARG_Province is now selected and xLODGen is generating terrain** (job g12-lod4: prepare, terrain, texgen,
    dyndolod; collect is not in it).

## Red, with cause
- **The batch (out/batch/game-12/20261030T124735) is void, so it must run again after LOD.** xLODGen holds all
  4 vCPUs at 100%.
  - The game starved: "main thread did not run the task within 3000 ms" in smoke's scene, lf83-components'
    talk-takes and lf83-endings' scene.
  - combat-trial-a failed at pandora-wired (no TKDR_DodgeStart in 39 anim events).
  - ui-probe failed at hud: "vanilla-hud hidden 4/4, **0 out of HudElements** (22 listed)". fixes-2's locks did
    not take out a member.
  - Both of these may be real, not starvation: re-prove each by its one test after LOD.
  - The rule I took from this: **LOD must not run beside a batch on a 4-vCPU g4dn.xlarge.** Run it alone, or
    accept a void batch.
- I stopped the batch at 12:53. The game's kill left a zombie child (taskkill could not end PID 6516's child).

## Not done (for the next game lane, in order)
1. Let g12-lod4 finish (`tooling/job_guard.sh wait g12-lod4`). Then run `lod.sh run collect` and
   `lod.sh still with`, and give the two vantage stills to a reader. Write the time and RAM from
   out/lod/metrics/*.json into installer/steps/lod.md and 2.W4 §c.
2. Re-run `run_batch.py tests/journeys/batches/game-12.yaml` with the machine to itself. Then re-run ui-probe for
   the frame times (decision 0017 1.2 §0).
3. The DSC verdict on B2: game-11's script, which sets `MO2\tools\nemesis` aside. Then `stack.py combat A` and
   verify.
4. memclimb.py, the shader cards (copy apps.json; each card launches; the CS log reads on or off), and the reader
   pass on the stills.
5. Not done: PROGRESS rows, the Outcomes and decision 0017's 1.2 §0 numbers. No item closed in game. 0.3's timings
   are recorded (journals/bridge.md, game-11), and the deploy timings above add to them.

## Machine state
argonia-play is running for LOD (xLODGen terrain). The game is down (one zombie child). Combat set A is laid, and
our build from 692edc4+ is deployed. Stop the machine when LOD and the next batch end.
