# Lane 1.15-r6-resume-costs: a resumed chain holds the deploy, keys the refresh by its inputs, keeps its log

Owner ruling #39 (2026-11-04): a restart costs no pre-batch and no deploy.

## What changed
1. **Deploy held** (`infra/gpu-box/deploy.sh`, 940bf671). `held()` keys the whole build: the two ESMs, the .pex, the
   theme and perks keys, and the tracked blobs plus the dirty diff of world/db, schema, plugin, tools, infra/gpu-box,
   data, ui, skse and tests/scenes. The base key's inputs are all inside it. A green full deploy re-keys at the end and
   writes `C:\argonia\state\deployed.key`. A non-held deploy first removes the old key, so a half-laid build is never
   held. If the machine answers with the same key, the deploy prints `DEPLOY held: <key>, skipped in N s` and exits
   before `make plugin`, the launch or the base save. Flags or `DEPLOY_FORCE=1` never hold. `--plan` prints the key.
2. **round.sh** (940bf671). The deploy's output is teed to `out/.deploy-last.log`. On a held deploy the script only
   runs `bridge.py ping`, and runs `bridge.py launch` only if the ping fails. Covered by 2 new tests in
   `tooling/tests/test_round.py`; 7 pass.
3. **Journeys key** (`infra/gpu-box/jobs/r5_prebatch.sh`). It has its own state,
   `~/.argonia/round/prebatch-journeys.<jkey>.state`. The key covers tools/journeys, panel.py, the world/db and
   schema blobs, and the stat lines of water cells.jsonl, ground-f32 and the vegetation and land folders. It leaves out
   out/world.sqlite, which a plugin build rewrites. An interrupted refresh resumes stand by stand from gen.py's
   existing `out/journeys/cache` (`_cached`; gen.py was not edited). This edit landed inside e1127099, another
   committer's path commit.
4. **job_guard resume log** (1cdeaf2b). `job_resume.sh` no longer moves the log aside: it passes `JOB_RESUMED=1`.
   `job_guard run` then appends `== RESUMED <UTC>` and the relaunch's output. Under systemd it uses `append:`, and
   `>>` without systemd. A fresh run now uses `truncate:`: `file:` overwrote the log in place and left stale tail
   lines, which the new test caught. The new test is `test_resumed_run_appends_to_its_log`, run in both modes; 10 pass.

## Measured
- Before: r6-chain6's resumed deploy at 12:36 took 296 s (make plugin alone 41 s).
- After, off-machine: computing the key and running `--plan` took 0.65 s. A held deploy adds one `run.sh ps` read
  plus the round's bridge ping. The live figure waits on the next reboot (acceptance 4).
- Open: measure the resume end to end on the next reboot, from job start to the first batch step. The first deploy
  after this commit still lays the build in full, because no machine holds a key yet.
- r6-chain7.log had no `== RESUMED` line at 13:4x. That resume ran before job_guard's append landed.
