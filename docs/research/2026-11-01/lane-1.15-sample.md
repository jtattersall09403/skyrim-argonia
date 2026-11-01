# 1.15 lane sample (round 2): the panel, the round's batch, the gate

The integration lane of [1.15](../../phases/1-core-loop/1.15-the-world-tracks-close.md) round 2.

## Built

- **The world panel**, `tools/argonia_world/panel.py` (`python3 -m tools.argonia_world.panel [--write]`, 26 s):
  per eco class with land regions (9 exterior classes populated, not 12: karst-cavern-belt is interior-only;
  seasonal-floodplain has no land region), a **shore** vantage (dry ground 0.3 to 3 m above its cell's
  `cell_water` level, within 4 samples of water of the class's commonest `water_type`, nearest the class centroid,
  facing the water) and a **high** vantage (the class's highest sample, facing the 45° direction whose ground 300 to
  1500 m out is lowest), both at least 3 cells inside the province edge. 18 vantages, noon and dawn each under the
  land region's weathers from `regions.panel_weather` (by EditorID: `fw` takes it, as the claywater scenes do).
  Writes `tests/scenes/world-panel.txt` (hour, then `cow` last) and `tests/journeys/world-panel.yaml` (37 steps:
  F to first person and `tm`, then per still `cow` with settle 60, `teleport pos`, `setangle`, `set gamehour`,
  `fw`, 14 s wait; expects only GetInWorldspace and the player within 300 units of the vantage). `--write` refuses
  to move vantages once runnable (`--force` after a ruling). `run_journey.py --dry`: 37 steps ok.
- **Reader brief** for the stills: the 1.15 §0 checklist and feel question, with
  `docs/design/world/vibe-board.md` as the vibe check (not the bar), plus "god rays and volumetric fog where the weather has them (dawn mist over
  water; light shafts through canopy)" (owner, 2026-11-01); the look board is retired.
- **Batch** `tests/journeys/batches/1.15-round-1.yaml`: world-panel, rock-booth, claywater-walk, claywater-look
  (last: crash-prone and expected red until re-seating). `run_batch.py --dry`: 4 items ok.

## The den test (diagnosed; the fix is the ground lane's)

`test_shallows_den_sits_in_water_at_least_2_5_m_deep` now reads the den's water from `cell_water` (cell -58,11:
33.23 m; the old 32.84 m constant was the retired water plan's). It stays red: the ground there is 68.31 m.
Cause: `terrain/generate.py` `shape_sites`, a `flat` site (Claywater Station: entrance `door`, footprint 65 m,
5.5 m from water) reserves every wet sample in its disc as bank above the water (`wet = disc & ~isnan(vmax)`, lo
raised to vmax + freeboard) and levels the core to the window's median, so the river and its scour pool under
the station are buried in a 68 m plateau. Fix at source (ground lane): a flat site keeps wet samples as water
(reserve only the dry disc) and takes its level from the dry core. Not loosened.

## Pipeline

`make plugin` on the sample (formid table for the six weathers, four image spaces, three mist globals):
**failed after 54:37 wall** (user 2235 s, 2.5 GB peak RSS in Python), exit 2: `plugin: ArgoniaWorld.esm failed /
Out of memory.` The C# `world` step (pipeline.py:274, under `CAP` MemoryMax=3G, pipeline.py:43) runs out of memory on
the whole province with the new inputs (water emit, ground). Argonia.esm's generate (which allocates the weathers'
FormIDs) runs after `master_world` (pipeline.py:353), so no formid row was added and `plugin-check` stays red on
`ARG_ImageSpace_montane`. Fix (pipeline owner/planner): raise the world step's cap or stream the world write, or
let `generate` run before/without `master_world` when only Argonia.esm's ids are wanted. Then one `make plugin`.

## Starting state

- Done: panel.py, scene, journey, batch, den test reading cell_water (pushed: 4241d56, af9182b, f582247).
- Diagnosed: den red = ground lane's flat-site rule (above).
- Owed: `make plugin` green and the formid table committed (blocked: the OOM above); the panel must be rewritten (`--write --force`) once after the ground is regenerated on main, since the
  vantages were picked from the round-1 ground; then never moved. `make plugin-check` and full `make check`
  after the plugin build (see the return).
