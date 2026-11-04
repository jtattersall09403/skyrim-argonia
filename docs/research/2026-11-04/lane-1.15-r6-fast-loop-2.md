# Lane 1.15-r6-fast-loop-2: where the edit-to-test time goes

Owner 2026-11-04 08:06 and 08:11 (#37). L1 from the job logs, L2 from dry runs and a test. Nothing ran on the game machine.

## (1) Stage table, 2026-11-02..04 (386 logs in ~/.argonia/jobs; `tooling/round_retro.py '*' --since 2026-11-02`)

Sources: deploy's `== <step>` / `== N s` pairs, `== <step>: N s` (LOD), `ROUND|PREBATCH <step> OK|FAIL in N s`,
`DEPLOY OK in N s`, run_batch's `run N: PASS in X s` (per stop run: scene load, stops, stills), `up after N tries`,
the LOD `metrics:` lines. Share is of the summed leaf stages; rows marked (sum) contain others.

| stage | n | median s | p90 s | total s | share |
|---|---|---|---|---|---|
| round total | 15 | 672 | 1756 | 12890 | (sum) |
| batch: per journey run | 72 | 117 | 206 | 10240 | 19.2 % |
| deploy total | 23 | 275 | 895 | 9167 | (sum) |
| round: deploy | 20 | 312 | 900 | 8582 | (sum) |
| prebatch: plugin | 16 | 232 | 1752 | 7722 | 14.5 % |
| round: batch | 15 | 385 | 1174 | 7008 | (sum) |
| capacity wait ((tries-1) x 60 s) | 52 | 0 | 0 | 6240 | 11.7 % |
| lod: dyndolod | 3 | 1853 | 2366 | 4824 | 9.1 % |
| prebatch: gate | 9 | 330 | 361 | 2873 | 5.4 % |
| deploy: make plugin | 39 | 3 | 228 | 2776 | 5.2 % |
| lod: terrain | 3 | 1097 | 1118 | 2681 | 5.0 % |
| lod metrics: terrain | 3 | 1069 | 1076 | 2570 | (sum) |
| deploy: stack stage | 32 | 2 | 441 | 2238 | 4.2 % |
| lod metrics: dyndolod | 1 | 1941 | 1941 | 1941 | (sum) |
| deploy: launch | 23 | 91 | 110 | 1802 | 3.4 % |
| deploy: stack push | 32 | 19 | 185 | 1482 | 2.8 % |
| prebatch: plugin-check | 9 | 123 | 129 | 1237 | 2.3 % |
| round: up | 20 | 7 | 31 | 1160 | 2.2 % |
| deploy: skse build | 9 | 132 | 152 | 1135 | 2.1 % |
| lod: texgen | 4 | 209 | 219 | 840 | 1.6 % |
| lod: collect | 4 | 80 | 449 | 658 | 1.2 % |
| lod metrics: texgen | 3 | 171 | 177 | 507 | (sum) |
| prebatch: chart | 11 | 45 | 53 | 474 | 0.9 % |
| deploy: base save | 23 | 22 | 26 | 472 | 0.9 % |
| deploy: lod | 31 | 6 | 11 | 461 | 0.9 % |
| prebatch: chart4k | 11 | 45 | 51 | 460 | 0.9 % |
| prebatch: journeys | 10 | 20 | 48 | 410 | 0.8 % |
| deploy: theme | 36 | 9 | 17 | 374 | 0.7 % |
| deploy: send ESMs and helpers | 31 | 9 | 13 | 299 | 0.6 % |
| prebatch: vegetation | 11 | 22 | 25 | 225 | 0.4 % |
| deploy: chart | 16 | 1 | 47 | 223 | 0.4 % |
| deploy: chart 4k | 16 | 0 | 48 | 216 | 0.4 % |
| prebatch: plugin-ids | 9 | 20 | 34 | 211 | 0.4 % |
| lod: resources | 10 | 10 | 63 | 204 | 0.4 % |
| deploy: views | 36 | 1 | 11 | 194 | 0.4 % |
| deploy: machine up | 39 | 3 | 5 | 175 | 0.3 % |
| deploy: perks | 36 | 3 | 6 | 138 | 0.3 % |
| lod: prepare | 4 | 32 | 41 | 120 | 0.2 % |
| lod: from scratch, ground b | 1 | 104 | 104 | 104 | 0.2 % |
| lod: keyed build, ground a | 1 | 99 | 99 | 99 | 0.2 % |
| lod: survey | 1 | 76 | 76 | 76 | 0.1 % |
| deploy: game down | 73 | 1 | 2 | 71 | 0.1 % |
| prebatch: water | 12 | 5 | 8 | 67 | 0.1 % |
| lod: rebuild after the one-region edit | 1 | 58 | 58 | 58 | 0.1 % |
| deploy: send scenes | 23 | 2 | 3 | 55 | 0.1 % |
| deploy: shader cache save | 19 | 2 | 5 | 54 | 0.1 % |
| prebatch: roads | 14 | 2 | 7 | 45 | 0.1 % |
| deploy: controls | 31 | 1 | 2 | 36 | 0.1 % |
| prebatch: sample | 11 | 2 | 3 | 25 | 0.0 % |
| deploy: shader cache | 25 | 1 | 1 | 16 | 0.0 % |
| lod: rebuild, nothing changed | 1 | 3 | 3 | 3 | 0.0 % |
| deploy: papyrus | 32 | 0 | 0 | 1 | 0.0 % |
| prebatch: tree-booth | 1 | 1 | 1 | 1 | 0.0 % |

| wait or LOD half | lines |
|---|---|
| capacity: no spot capacity lines | 324 |
| interrupts | 4 |
| locks: queued behind | 160 |
| lod: current | 5 |
| lod: no archive (rebuild owed) | 23 |
| lod: restored | 4 |

Capacity: 324 `no spot capacity` lines, 60 s apart in up_until.sh, so up to 5.4 h; the `up after` lines account for 6240 s.
Locks: 160 `queued ... behind` lines (jobs serialised on the one GPU lock).

## (2) The five largest sinks, with their cause in the code

1. In-game batch, 117 s median per journey run (p90 206; 10240 s): run_batch.py loads a scene per journey from the base
   save (load + settle waits per stop). Cut: group journeys sharing a cell into one load; expected ~40 % of 10240 s.
   Not in this lane's paths (journeys harness lane); named for the planner.
2. Pre-batch plugin build, 232 s median, p90 1752 (7722 s): `make plugin` in r5_prebatch.sh rebuilds the province
   when world inputs move; p90 is the navmesh/terrain rebuild. Cut: per-region keyed plugin build; expected 1 to 25 min per edit.
3. Spot capacity waits, 6240 s counted (up to 19440 s): up_until.sh retries every 60 s. Cut: the pool's other standbys
   (pool.py) or another AZ inside the same budget; no extra AWS spend. Named for the planner.
4. LOD: DynDOLOD 1853 s median, terrain 1097 s, texgen 209 s, collect 80 s (~9000 s): lod.sh run, all halves together.
   Cut: chain.sh runs it only when ensure finds no archive for the key, and last; lod.sh's per-half keys (lodkey lane).
5. The gate inside the pre-batch, 330 s median (2873 s), plus plugin-check 123 s (1237 s): r5_prebatch.sh runs `make check`
   every keyed run. Cut: `make check` only on what the change reaches (the planner's rule); expected ~4 min a round.

## (3) Cuts made, before and after

| cut | before (logs) | after | proof |
|---|---|---|---|
| deploy theme keyed (tools/ui_theme, the mods dir, the font) | 9 s median, 36 runs, 374 s; 17 s on the VM today | skipped, 0 s | `deploy.sh --plan`: `theme: unchanged (7618535ddbe4), skipped`; an edit to build.py gives `would run (key e672…, stamp 7618…)` |
| deploy perks keyed (perk_plugin.py, db.py, world/db, schema, ArgoniaGen) | 3 s median, 36 runs, 138 s; 7 s today | skipped | `perks: unchanged (ac0ada3b9d25), skipped` |
| base save keyed (ESMs, .pex, skse, stack, deps, scenes, bridge); the stamp on the machine beside the saves, written only after a save that succeeded | 22 s median, 23 runs, 472 s | skipped when the machine's stamp matches and both .ess exist | `deploy.sh --plan` prints the key (`d6f7edd58e7b`, stable over two runs); first real check: the planner's next deploy |

The keys were first too broad (all of tools/argonia_world and data: other lanes' live edits moved them between two plan
runs); narrowed to the real inputs. `DEPLOY_FORCE=1` runs every step.

## (4) The default chain: infra/gpu-box/jobs/chain.sh

prebatch (no machine) -> round.sh batch on the existing LOD (ROUND_KEEP_UP) -> `lod.sh ensure`; only on `no LOD archive`
-> lod.sh run + archive + a deploy that lays it -> saves -> round_retro appended to the round record. Machine stops on
every exit; no Paris box. `CHAIN_DRY=1` prints the stages.

## (6) Retrospective tool

`tooling/round_retro.py <log glob> [--since] [--append record.md]`, test tests/test_round_retro.py (1 passed); chain.sh calls it last.

## (7) The loop's architecture

- Once per build, not per round: the base save (now keyed), the journeys refresh and the gate (pre-batch keyed by inputs
  already; the gate should key on the touched paths), theme and perks (now keyed).
- Overlap: machine start while the plugin builds would save ~7 s median but costs idle GPU minutes when the build is long
  (p90 1752 s): not done (no extra AWS); start it when the pre-batch reaches the gate instead (saves the up step, 31 s p90).
  Readers judging stills while later stops run: run_batch writes stills per item; the planner can hand each item's
  stills as they land (~1 reader pass per round off the critical path).
- Lanes wait on the game machine only through the planner's batch; the lock queue (160 queued lines) is the cost of one machine.
- Structural changes: (a) chain.sh as the one job (done); (b) one scene load per cell group in run_batch (~4000 s over these logs);
  (c) a per-region keyed plugin build (p90 1752 s to minutes). (b) and (c) are other lanes' paths.

## Hand-off: what remains

Batch per-run 10240 s, plugin p90 1752 s, capacity 6240 s+, LOD ~9000 s when owed, gate 2873 s, deploy launch 91 s median
(1802 s; tools/bridge.py, not this lane), stack stage p90 441 s, skse build 132 s when skse moves.
