# Lane 1.15-water: the water solve

Brief: [briefs/1.15-water.md](briefs/1.15-water.md). Code: `tools/argonia_world/water/solve.py` (rules and API),
`steps.py` (piece table and chains), `__main__.py` (`solve`, `check`, `emit`, `records`), tests in
`water/tests/test_solve.py`.

## Result (measured 2026-11-01, `python3 -m tools.argonia_world.water solve` then `check`)

- Solve wall time 0.39 s (raster load to result); `water check` 3.6–6.5 s end to end, exit 0.
- 9,978 water cells: sea 6,313, blackwater 2,605, fresh 983, brackish 77. 0 cells with two levels.
- 2,280 bodies: 1,360 own cells, the ocean is the sea cells, 919 have a recorded drop (their cells hold another
  body or the sea; the reason and levels are in `Result.body_outcome`). 896 cells were contested.
- 615 reaches: 591 `water`, 24 `dry`, all 24 for the same reason: the profile falls more than 20.96 m (the tall
  falls body) inside one cell. None was re-routed (re-routing is owed if the owner wants those as rivers).
- 1,657 `water_step` rows: closed 1,370, falls 202, cascade 72, rapids 13; every row has a chain.
- `emit`: 9,978 cell lines, 920 piece refs, every piece resolved, no cell over its ref slot. No planes.

## The rules (written in solve.py's docstring)

- **Snap rule** for the 1,086 bodies at 0.5–3 m: each snaps to 0 (lowland is a tidal marsh plain,
  50-hydrology-climate.md) unless it shares a cell with a body at 3 m or above, where the one-level cell rule gives
  it that body's level (its basin). Below 0.5 m: 0. 3 m and above: its own `level_m`.
- One level per cell: sea and bodies first, most raster samples wins (tie: the lower level); reaches alone: the
  lowest level (downstream wins). A river entering a lake takes the lake's level in its cells, so the step falls on
  the edge before the lake.
- Rivers: flat in a cell at the profile's midpoint, monotone downstream, drops under 0.5 m carried on (riffles),
  4-connected walk. Steps from the upper cell, the channel's vertex range from the crossing point ± half width.
- Water type: ocean sea; lagoon, mudflat, tidal band brackish; marsh family blackwater (fresh in upland/montane);
  lakes, tarns, ponds fresh; reaches by `tidal`/`water`.
- `section(upper, lower)`: §11's bank and bed numbers for the ground lane (bank ≥ upper, bed at the edge 100–300
  units under it, slope 1–28 vertices).

## Deleted

`plan.py`, `field.py`, `oriented.py`, `design.py`, `migrate.py`, `budget.py`, `classify.py`, `model.py`,
`tests/test_water.py`; the plane activators in `layer.py` (WATR only now; `black` renamed `blackwater`);
`steps.py` reduced to the piece table and chains (ring and skirt added, their sizes not measured).

## Starting state (hand-off)

- Done: contract tables and API (dc320a6), the solve, the check in `make world` (skipped where the raster is
  absent), the pipeline's water stage runs `check` then `emit`.
- Diagnosed: `make check`'s `plugin-check` red in a fresh worktree is the shared `out/terrain/land` missing cells
  (e.g. (-52,-57)), not this change.
- Owed: `tools/world_sample.py` stops 4–5 read `plan.json`'s old `sampleReach` (outside this lane's paths; `emit`
  now writes `sampleStep`); `terrain/water_regrade.py` (ground lane) is no longer fed by the water lane; re-routing
  the 24 dry reaches; L3/L4 stills of piece scale (ring, skirt unmeasured).
