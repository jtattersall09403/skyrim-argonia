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
