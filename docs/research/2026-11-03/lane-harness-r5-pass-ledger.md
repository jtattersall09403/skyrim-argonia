# Lane harness-r5-pass-ledger (2026-11-03)

Owner rulings (owner-brief 2026-11-03 17:1x, 17:2x): a passed check is not run again until its own inputs change;
a batch shrinks as items pass. Round 5 re-ran menus-look five times (21 steps; only Settings/Load/lockpick needed
re-proof) and chart after it had passed.

## Built

- `tools/pass_ledger.py`: reach, reach hash, the ledger `~/.argonia/round/passes.jsonl` ($ARGONIA_PASSES), the plan.
  Hash = tracked blob ids (`git ls-files -s`) of the reach paths + both ESM sha256 when `esm` is named + the scene file
  + the journey's settings + the step's own definition. No `reach:`: round.sh's whole-build inputs.
- `tools/run_journey.py`: `Runner.run(skip=)` records a skipped step as passed with the ledger's still and run and
  restores its kept values; `main` writes the ledger.
- `tools/run_batch.py`: per item plan; a journey whose every step passed is skipped whole; `--all` forces; `--plan`
  prints "batch: N of M journeys, K of S steps to run" (exit 3: nothing left); summary `steps_run`/`steps_skipped`.
  Steps hand state on (menus-look's open/close pairs), so a journey runs up to its last step that must run and skips
  the passed suffix; `independent_steps: true` skips each passed step, `needs:` keeps a dependency.
- Reader verdict: `python3 -m tools.journeys ledger pass <journey> <step>` (a `reader:` step is `reader`, not `pass`,
  until then). `tools.journeys refresh` keeps each generated journey's `reach:` line.
- `infra/gpu-box/round.sh`: the plan before `up`; nothing left: `ROUND DONE nothing to run`, no machine. `ROUND_ALL=1`.
- `infra/gpu-box/lod.sh archive`: counts the mod (files, block-rounded bytes) first; skips when
  `s3://…/lod/<sha12>.tar` holds that mod (`lod_skip.py`: metadata `argonia-files/argonia-bytes`, or for older tars a
  size within the tar bounds); uploads now carry the metadata. `lod.ps1 collect` skips when the source and mod file
  counts equal `argonia-collect.count` from the last collect.
- `journey_lint`: `reach:` (list, each matching a tracked file), `independent_steps`, `needs:`.
- Tests: `tools/tests/test_pass_ledger.py` (10), `test_journey_lint.py::test_reach_and_needs`;
  `tools/tests/conftest.py` keeps every test's ledger in tmp. `make check-reach`: 162 passed, REACH GREEN (79 files).

## Default reach (67 journeys)

UI = ui/**, tools/ui_theme/**, skse/ArgoniaCore/**, skse/core/**, data/dependencies.json.
CORE = esm, skse/ArgoniaCore/**, skse/core/**, data/quarantine/**, data/dependencies.json.

- UI: menus-look, menu-sweep, lockpick-look, ui-review, ui-sweep, ui-probe, ui-handoffs, pad-panes, menus-quit.
- UI + esm: hud-look, magic-pane, system-perks, journal-dialogue, dialogue-intercept, items-look;
  + tools/chart/**: chart-look, chart-minimap, chart-zoom, hud-minimap-edge; + data/loading-screens.json: loading-look.
- CORE: attributes, cosave, suspend-save, spot-watch, rest-is-the-only-save, grow-at-rest, die-and-recover,
  rest-respawn(-cleared), fight-*, combat-trial-a/b/b2, w3-crime, livia-sleep, quest-board, lf83-*, first-place,
  claywater-talk, croc-den, quarantine; walk-save + infra/gpu-box/base_save.py.
- player-look: esm, data/quarantine/**, base_save.py, dependencies. bmv-look-1..10: dependencies.json only.
- claywater-look/walk: esm, place_build.py, pieces.py, pieces-preference.json, mesh-textures.json, dependencies.
- water-types: esm, argonia_world/water/**, deps; river-steps + terrain/**. tree-seat: esm, vegetation/**,
  tree-seat.json, leaf-hue.json, deps; rock-booth: esm, vegetation/**, deps. creature-spots, creatures-kinds: esm,
  creatures/**, creature-kind-bars.json, deps. road-look: esm, routes/**, terrain/**, deps. ground-materials: esm,
  terrain/**, mesh-textures.json, deps. w3-interior-sun: esm, plugin/Argonia/ImageSpaces/**, deps.
- Whole build (no reach): smoke, world-sample, broken, soak; drafts untouched (sky-ab, water-budget, w4-veg-densest,
  world-panel).

## Open

- The ledger starts empty: the next batch runs everything once, then shrinks. Seeding from today's summaries was not
  done (their inputs cannot be proved equal to the current hashes).
- lod.ps1's collect skip and lod.sh's archive skip are unproven on the machine (no machine touched by this lane).
