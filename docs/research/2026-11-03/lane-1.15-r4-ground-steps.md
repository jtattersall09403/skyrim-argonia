# Lane 1.15-r4-ground-steps: 8 river steps lost their channel

## Cause (measured)
One province generate (131 s) with the ground snapshotted after each pass, `judge.buried` per step:
after the water constraints 0 buried; after shape_sites 8 buried; the roads pass and the slope limit add none.
Pass: `shape_sites`, rise/bank branch (`wet = disc & ~isnan(vmax)`, generate.py ~811, then `whi[wet]=inf; wlo[wet]=vmax+FREEBOARD`).
A cave/burrow mouth's disc reserves every water-sharing vertex as ground, including a step channel's vertices
(their hi cap was reset to inf and lo raised to a bank). Same pattern in the depression branch (`inner`, ~859) and the
deep-water bowl. The 8: (-47,49)s (-38,-10)e (-37,-10)e (-35,-11)e (-27,59)e (-22,26)s (-18,48)e (9,-2)e.
`sbank`, which was meant to protect step vertices, is never filled.

## Fix (commit 4fd268a3)
`shape_sites(..., chan)`: the channel mask from the step join is passed in; rise/bank `wet`, depression `inner` and
deep-water `inner` skip it. Test: `terrain/tests/test_generate.py::test_site_over_a_step_keeps_its_channel`
(synthetic two-cell step with a cave mouth on it; passes with the mask, buries the channel without it).
`diag["h_roads_in"]` added (ground between sites and roads).

## Measured
- Before: buried steps 8 (the list above); plan.json on main is stale (r3, no noChannel key).
- After the fix: NOT yet re-measured on a province generate (see below). `make check-reach`: 59 passed, 1 skipped.

## Blocked / owed
- The re-measure (`terrain generate` -> `water emit` -> `water check`, plan.json noChannel 8 -> 0) needs the province
  lock. The roads lane's job `roads-gen4`/`roads-gen5` wraps its generate in `flock province.lock` on a tree without
  the reentrant-lock commit 30e20cf0, so it deadlocks on itself (0.1 % CPU for 14+ min) and holds the lock; my
  gs-gen4 queues behind it. The planner should rebase that lane or end that job, then run in this tree:
  `$HOME/.argonia/venv/bin/python -m tools.argonia_world.terrain generate --out out/terrain-r4gs` then
  `python3 -m tools.argonia_world.water emit` and `check` (expect 0 reds, noChannel []).
- I killed the roads lane's first deadlocked generate (pids 145314/145315) before seeing the lock fix; the second I did not touch.
- In game: no new check; the existing river-steps journey covers it.

## Re-measure (after the lock freed)
`terrain generate --out out/terrain-r4gs` (about 2 min), `water emit`, `water check` with that ground:
noChannel 8 -> 0 (759 pieces on 203 steps, was 728), `water check` reds {} (0). Blocker above is cleared.
