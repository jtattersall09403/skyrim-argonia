# Lane 1.15-r6-creatures-state: creature checks are state reads, not stills

Brief: docs/research/2026-11-04/briefs/1.15-r6-creatures-state.md. Owner 19:05 #41, decision 0036 amended: "check in the
backend that their spawn code has been loaded in correctly". This lane ran no game. The planner's batch runs both journeys.

## What changed
- `tests/journeys/creature-spots.yaml` (generator `tools/argonia_world/creatures/journey.py`) and
  `tests/journeys/creatures-kinds.yaml` (generator `tools/journeys/gen.py` `creatures_kinds`): `stills: false` at the
  head. They have no `camera`, no `hud: off`, no weather forcing or read-back, and no `setangle`. Each stop teleports to
  dry ground 15-25 m from its spawn point and waits. The scene sets god mode only.
- `tools/run_journey.py`: the runner now honours a journey's `stills: false` (one line). Before this, only the CLI's
  `--no-stills` turned stills off. A failed step still takes its still, as it does under `--no-stills`. The line went to
  main inside 1.15-r6-scan-retake's commit 6d2ed788, which committed the same file.
- `python3 -m tools.argonia_world.creatures journey` and `... kinds` regenerate the journeys. They run through
  `tools.journeys refresh`, which keeps the `reach:` lines and runs `journeys check`.
- The spawn's reference is its form id in ArgoniaWorld.esm (`records.ref_id`: the k-th ref of its cell, numbered the way
  `write_shards` numbers them). All 10 generated ids were checked against the province shards (out/terrain/creatures).
  Each one is an ACHR at its stop's subject x, y.

## What each stop reads (bridge `actors [radius] [ref]`)
Spawn stops (creature-spots water-a/b, marsh-a/b, upland-a/b; creatures-kinds coastal-lagoon, northern-transition,
western-frontier):
1. `player pos`, kept as `<stop>_arrive` or `<stop>_stand`.
2. The spawn's own reference. `refs.0` must not be null (kept as `<stop>_spawn`: base, name, dist, dead, 3D state),
   `disabled` must be false and `loaded_3d` must be true. Its actor must be a kind of the spot's own list, kept as
   `<stop>_spawn_kind`. That list is the one for the region class and band in `creature_list_entry`: a fixed list,
   never a levelled one (0035).
3. Actors within the radius (40 m for creature-spots, 8192 u for creatures-kinds), kept whole as `<stop>`.
   creature-spots needs at least one actor (`listed.0`) and at least one of the list's kinds (`<stop>_kinds`).
   creatures-kinds needs at least 4 distinct kinds of the class's lists.

Den stop: the same reads on the predator's reference, whose kind must be the den's creature. Guar pen: both kept guar
are read by editor id: not dead, not disabled, within 1500 u. The actors near them are kept.

## What a failure looks like
The step's reason names the read that failed. Examples:
- `actors 2801 ArgoniaWorld.esm|0xEABAC0 refs.0.loaded_3d = False, wanted eq True`: the spawn is not loaded.
- `refs.0 = None`: the bridge found no actor ref, so either the plugin lacks the record or the id has moved.
- `listed: 0 distinct kinds of the list [], wanted at least 1`: none of the list's kinds is near. The kept list names
  whatever was there (a Skyrim animal, or nothing).

A failed step alone takes a still for diagnosis.

## Measured
- Regenerating: creature-spots took 7.5 s (7 stops, 0 moved). creatures-kinds took 15.8 s (4 stops, 2 moved 5 m off plants).
- `run_journey.py --dry`: creature-spots 7 steps, 42 kept values ok. creatures-kinds 4 steps, 17 kept values ok.
- `journey_lint` is clean for both. `journeys check` shows no stale creature journey. Its 30 stale stands are in
  other lanes' journeys.
- `creatures plan-check`: 3 of 3 stops green.
- pytest: 77 passed in tools/argonia_world/creatures/tests (including the new test_state_journeys.py: no still, no
  reader, and every stop has a spawn-ref read and an actors read with a kind assertion) plus tools/tests/test_run_journey.py.
  103 passed in tools/tests journey/batch/kinds. ruff is clean.
- tooling/tests/test_round.py::test_a_rerun_skips_what_is_done fails. My change does not reach it: it fails on an
  unexpected machine `up` call.

## Not done
- "No Skyrim animal" is not asserted. The kept actor lists show it, but the runner's `kinds` only counts matches, and an
  `only` assertion would fail on the people and the guar near a stop.
- checks.md rows 150, 152 and 153 are reworded and their status is owed. Row 150 had a stray extra `proven` cell; it
  is removed.
