# 1.15 build-speed lane: the province build and the deploy made incremental

Lane 1.15-build-speed, 2026-11-02 ([brief](briefs/1.15-build-speed.md)). Owner ruling 11:30: the before figures come
from the logs, not from a new whole-province build; only the after is measured, on a one-region sample.

## Before (from today's logs and outputs)

| stage | seconds | source |
|---|---|---|
| `terrain generate` (the ground, whole province) | 116 | out/terrain/generate.json `seconds` |
| land rows (205 rows, 35,259 cells, 4 workers) | 1,484 | out/terrain/stats.json `seconds` |
| world step (Mutagen, LAND + water + NAVM) | 98–125 | lane-1.15-pipeline.md (1:38, 2:05 with navmesh) |
| vegetation place + splice + readback | ~70 + 5 | out/terrain/vegetation shard mtimes 09:39:17–09:40:35; pipeline report |
| creatures plan + splice + readback | ~60 | out/terrain/creatures mtimes, plugin-r3g |
| whole `make plugin` after a ground change | up to ~2 h | owner, brief (repeated reruns today) |
| deploy: stack stage (BM&V re-staged) | 377 | deploy-r3r.log |
| deploy: stack push (5 mods incl. BM&V) | 185 | deploy-r3r.log |
| deploy: skse build | 124 | deploy-r3s.log |
| deploy: launch / base save | 61 / 24 | deploy-r3u.log |
| deploy: ESM-only (r3u, ESMs unchanged, --no-stage) | 110 total | deploy-r3u.log |
| deploy-r3q: stopped at the pre-flight | 0 (failed) | 26 GB demanded though BM&V was already staged |

Everything else in the deploy already skipped by stamp before this lane: the SKSE build (tools/skse_stamp.py), the
ESM send (sha256 on both ends), push (per-mod digest, sent.json), stage (per-row key), LOD (`lod.sh ensure` lays the
S3 archive keyed by ArgoniaWorld's sha256 when one exists).

## What reuses what (after)

- **Land rows** (tools/argonia_world/terrain/build.py `row_key`, `reuse_row`): each row's key is the land stamp
  without the ground (`pipeline._terrain_stamp(ground=False)`: code, tables, vault, roads, places) plus every input
  raster cut to the row's window, ROW_MARGIN = 256 vertices each side (the quantiser's and the material's halos, a
  quadrant, the class warp and blend, ~170, rounded up): apron, ground, land cover, and the cell grids of water level,
  nearest level, rain and eco class; the ground's four edges and the tint whole. Keys live in land/_keys, row stats in
  land/_stats; a row whose key equals the last finished land's is hard-linked, not rebuilt. Proven by
  test_land_reuse.py: unchanged → 10 of 10 rows reused; a hill in one band → the far rows reused, the rest rebuilt,
  and the shards byte-identical to a from-scratch build (L1); a changed shared key reuses nothing.
- **Vegetation bands** (vegetation/build.py `band_key`): the placement code, the rules of each cell's region and
  every CellInputs field (heights, levels, table, painted, roads, footprints) per 4-row band; equal key → the placed
  stems reload from _bands/. The region tree keep (a whole-region loop) is recomputed and the shards rewritten each
  run (seconds); unchanged cells give unchanged bytes. test_band_cache.py.
- **Creature rows** (creatures/build.py `row_key`): code, rules and every cell's planner inputs; plans reload from
  _rows/. test_row_cache.py.
- **Deploy pre-flight** (deploy.sh, `stack.py plan`): asks for the room the rows to re-stage need (3x their archives),
  not a fixed 26 GB; `stage` and `plan` share `stage_key`/`staged_ok`. test_stack_plan.py.

## Still whole, and why

- `terrain generate` (116 s) is whole-province by method (a solve over the province); see the locality probe below.
- The world step writes the whole ArgoniaWorld.esm (~2 min): Mutagen builds the worldspace as one object graph and
  has no partial group write; Spriggit serialises, it does not patch binaries. Cheapest whole write kept.

## After (measured on the build VM, 4 CPUs)

The one-region edit: `dunmer-north.deep-sink-basin` summit_m +6 in region_relief, `terrain generate` run before and
after into a sample dir (the worktree db restored after).

| measure | value |
|---|---|
| `terrain generate`, before / after the edit | 134 s / 147 s (whole province by method) |
| ground samples changed | 82,133 of 16.3 M; cliff and role masks unchanged |
| province cell rows changed | 25 of 126 (rows 4–32 from the north): the ground solve is local |
| land, 40 x 84 cell box over the edit, first keyed build | 99 s, 0 of 84 rows reused |
| same, rebuilt with nothing changed | 3 s, 84 of 84 reused |
| same, rebuilt after the edit | 58 s, 41 of 84 reused, 43 built |
| same, from scratch on the edited ground | 104 s |
| L1: the cached rebuild's shards vs the from-scratch build's | identical, 84 rows |

Whole-province projection from these (not measured end to end): the edit reaches 25 changed rows + 2 x 8 margin
= 41 of 205 rows, so land ≈ 41/205 x 1,484 s ≈ 300 s instead of 1,484 s; `make plugin` after a one-region ground
edit ≈ generate 147 + land ~300 + world ~120 + vegetation ~75 + creatures ~60 + Argonia.esm, about 12–15 min
against up to 2 h. Owed: the first main-tree `make plugin` after this merges builds every row once (the existing
land has no keys); its next one-region rebuild is the end-to-end after figure.

## Deploy (the planner measures)

Change: the pre-flight asks `stack.py plan` (prints `{"restage": [...], "need_bytes": N}`). On this VM now:
`{"restage": [], "need_bytes": 0}`, so an ESM-only deploy no longer needs 26 GB free and unpacks nothing. Measure on
the next machine that is up: touch nothing but the plugin, `make plugin`, then
`tooling/job_guard.sh run --gpu deploy-bs -- infra/gpu-box/deploy.sh` and read the `== <step>` / `== N s` pairs and
`DEPLOY OK in N s` from its log; compare with deploy-r3u (110 s, --no-stage) and deploy-r3r (stage 377 s, push 185 s).

## Hazards found

- `material.rain_field` reads `generated_ground()` (the shared out/terrain ground), not the run's frozen copy: a
  concurrent `terrain generate` in another tree can change a build's rain mid-run. The row key hashes the rain grid
  the build actually used, so reuse stays correct; the coupling itself belongs to the ground lane.
- Pre-existing reds on main, not from this lane: test_check_records (PROGRESS 1.15 links a missing
  docs/research/2026-11-0 path) and test_world_sample (world-sample.yaml stale).
