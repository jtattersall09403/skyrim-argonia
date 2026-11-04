# Lane 1.15-r6-batch-one-load: one scene load per group of journeys

## (1) Measured (out/batch/*/*/summary.json, 2026-11-02..04, 15 batches, 52 journey runs run, skips excluded)

| | runs | run median | scene_s median (load + settle + `bat`) | scene_s sum | run sum |
|---|---|---|---|---|---|
| loaded from the base save | 41 | 104.7 s | 10.0 s | 427 s | 4933 s |
| chained (one_load, no load) | 11 | 106.6 s | 3.9 s | 45 s | 1144 s |

The load is ~10 % of a run (10.0 of 104.7 s); a chain saves ~6.1 s, not the ~40 % that lane-1.15-r6-fast-loop-2's sink 1
estimated. The 117 s median per run is steps (the stops, `cow` settles of up to 60 s, stills), not the load. 30 of
the 41 loads followed a failed item (one_load reloaded after any failure) or had no one_load batch.

## (2) one_load today and what changed (tools/run_batch.py `can_chain`, `starts_by_teleport`, `groups`)

Before: a batch's `one_load: true` chained an item onto the last item's game when the last item passed, the save was
the same and the journey did not ask for a load (`needs_load`, `batch_last`, `soak`, a relaunch). Any failure reloaded.
Now: an item chains when the last game is alive and unbroken (no crash, no relaunch, and not a failure of a chained item;
a failure after a fresh load is that journey's own and the next item chains), the save is the same, the journey does
not ask, and its start is a teleport (its scene or its first step to run has moveto/coc/cow/setpos) or the same scene
as the last item. A scene that moves nobody chains only onto itself. Steps of one item (independent or not) already
ran on one load; the pass ledger's per-step skip and whole-item skip are untouched (the first step *to run* is the
one checked for a teleport). `chain: true` keeps its old meaning. The camera and its relaunch retry are untouched.

## (3) Tests (tools/tests/test_run_batch.py)
`test_one_load_groups_by_scene_two_on_one_scene_cost_one_load`: s1, s2 (one non-teleport scene) and good (a coc scene)
cost one load, s1 after good a second (loads == 2; `groups` == [[s1 s2 good], [s1]]).
`test_one_load_chains_past_a_fresh_failure_not_a_chained_one`: bad, good, bad, good -> loaded T F F T.
`pytest tools/tests/test_run_batch.py tools/tests/test_run_journey.py`: 67 passed.

## (4) Plan for round 6 (`python3 tools/run_batch.py --plan tests/journeys/batches/1.15-round-6.yaml`)
```
batch: 13 of 13 journeys, 351 of 351 steps to run
  load 1: sky-ab water-types river-steps ground-materials road-look rock-booth tree-seat creature-spots creatures-kinds navmesh-paths claywater-look claywater-walk world-panel
loads: 1 for 13 journeys; 12 saved, ~73 s (10.0 s a load vs 3.9 s a chained scene, medians 2026-11-02..04), all passing
```
Expected saving ~73 s of a ~1400 s batch (13 x 105 s) when all pass; each failure on a chained item costs one load back.
The planner's round-6 batch is the live measure (summary.json `loaded` per item). For the planner: the larger sink is
inside the steps (per-stop `cow` + settle), not the load.
