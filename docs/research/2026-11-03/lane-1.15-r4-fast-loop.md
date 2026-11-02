# Lane 1.15-r4-fast-loop: the in-game round made one job, and much faster

Lane of round 4 of 1.15, 2026-11-02 ([brief](briefs/1.15-r4-fast-loop.md)); owner: "any loops involving checks in the
game need to be massively optimised and sped up". Measured from the logs; no game machine used.

## Before (from the logs)

Round 3 ran no batch (owner's scope cut; Paris interrupted at 10:57), so the batch costs are round 2's.

| step | seconds | source |
|---|---|---|
| machine up / stop | 32 / 18 | ~/.argonia/jobs/r3up.log, r3stop.log |
| failed deploys before one held (capacity, archive, disk pre-flight, a syntax error, ping during the shader compile) | ~2,300 (6 attempts, 09:47–10:26) | deploy-r3, r3p–r3t .log |
| deploy that held, ESM-only, --no-stage | 110 | deploy-r3u.log |
| deploy with BM&V re-staged: stage / push / SKSE build | 446 / 207 / 135 (1,011 total) | deploy-r2c.log; r3r 377 / 185 |
| shader compile after a shader change | ~660 (3,484 shaders) | briefs/1.15-round-3-driver.md, bridge.py ping_through_shader_compile |
| launch to menu / base save | 61–91 / 24–26 | deploy-r3u, deploy-r2c |
| world panel: 37 stills | 949 (25.7 per still; 14 s of each fixed `wait`) | r2-panel4.log, world-panel.yaml |
| world panel attempts before the pass | ~480 (05:14–05:22, three fails) | round-2.md |
| claywater 2 journeys | 278 | r2-clay.log |
| batch wall time, round 2 (4 journeys) | ~3,600, of which ~1,300 run | job logs 05:13–06:13 |

## The five largest costs and what was done

1. **Failed deploys and hand-offs (~38 min in round 3; ~38 min of round 2's batch hour).** Causes already fixed by
   other lanes (pre-flight `stack.py plan`, ping through the shader compile, deploy.sh syntax). New: the round is one
   job, `infra/gpu-box/round.sh` (up, deploy with one in-job retry, batch, stills.txt, stop on every exit; resumable per
   build; verdict line per step). tooling/tests/test_round.py: 4 passed.
2. **Shader compile, ~11 min per machine per shader set.** CS keeps `Data\ShaderCache` (stack.ps1 never touches it),
   but a new machine or image compiled again. New: `infra/gpu-box/shader_cache.{py,sh}`: key = hash of the laid
   shader sources, the CS DLL and its settings/overrides (installed.json; today 9aeccfd1a9d8); deploy.sh lays the
   archived cache before the launch and archives it after the launch that compiled it (s3://…/shadercache/<key>.tar).
   A world or texture change keeps the key (test_shader_cache.py: 5 passed). Unproven in game: whether CS accepts a
   laid cache (it may compare file times); the first round's `shader cache` and `launch` lines show it.
3. **Fixed waits before stills (14 of 25.7 s per panel still; 2,965 s of fixed waits over 61 runnable journeys).**
   New action `settle` (tools/run_journey.py `_settle`): returns once no Loading/Fader Menu is open since the step
   began and two player reads 0.5 s apart agree, at least `min` s, capped. The world panel uses
   `settle: {cap: 14, min: 3}` (panel.py and world-panel.yaml); a batch's `settle_waits: true` turns any run of waits
   after a move into a settle (`settled_do`): the floor over all journeys falls from 2,965 s to 1,717 s.
4. **BM&V re-stage and push (446 + 207 s) on a deploy.** Verified it only happens when the bmv manifest row changes:
   `stack.py plan` on today's tree is `{"restage": [], "need_bytes": 0}`; the derived mods are deterministic (theme
   built twice: 82 of 82 files identical; perks twice: identical), so a world-only or UI-only deploy pushes only the
   changed derived mod. Gap left: the theme rebuilds every deploy (19–36 s here).
5. **A save load per journey.** `one_load: true` in a batch chains every item on the same save after a pass (one load
   per batch; a fail, a relaunch or a journey's `needs_load`/relaunch/batch_last loads again). test_run_batch.py.

Tests: tools/tests/test_run_journey.py + test_run_batch.py 58 passed; tooling/tests 9 passed.

## After (predicted for a 10-journey batch; the machine run is the planner's)

up 0.5 + deploy ~3 (cache hit) + launch 1.5 + base save 0.5 + batch ~20 (panel ~8: 37 × ~13 s) + stop 0.3 ≈ **30–35 min**,
against ~75–100 min before (target ≤ 45).

## Owed in game (the planner's batch)

- The round itself: `tooling/job_guard.sh run --gpu=argonia-play round-r4 -- infra/gpu-box/round.sh tests/journeys/batches/<round-4 batch>.yaml`
  with `one_load: true` and `settle_waits: true` in the batch file; then `tooling/job_guard.sh wait round-r4`.
- Read from its log: `ROUND <step> OK in N s` for each step, `shader cache` (laid/current/compiles) and the launch's
  seconds, the panel's per-still seconds (run report), `ROUND DONE`. Stills: the stills.txt path to a `reader`; any
  still judged unsettled is the settle floor too short (raise `min`, never a fixed wait).
