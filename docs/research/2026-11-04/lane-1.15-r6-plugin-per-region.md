# Lane 1.15-r6-plugin-per-region: the province plugin build keyed and timed per stage

Status: (1), (2), (5) done and measured; (4) partial (the round trip is green inside `make plugin`; the regenerate-twice check, `make plugin-check`, was cut off by the 09:23 reboot); (3) not done: no per-block split of terrain generate, measured below.

## What changed (tools/ArgoniaGen/pipeline.py; the Makefile hunk landed in b9da736e)
- Every stage runs in `stage(name, key, outputs)`. The stage prints `plugin: stage <name> run|skip <s> key <12>`, and `make plugin` ends with a `plugin: times` table. Keys are written atomically to out/stages/<name>.key, and only after the stage succeeds (0037). A stage cut off by an interrupt keeps its old key, so it reruns.
- Keys name their inputs, never HEAD:
  - ground: generate.py, cellwater.py, the GROUND_TABLES jsonl, the apron.
  - terrain: its code, tables, roads, vault, regrade, place ground, patches and ground.
  - water: its code, the hydrology_/water_ tables and the pieces index.
  - vegetation: its code, VEG_TABLES, water cells and navmesh inputs.
  - creatures (new): creatures/*.py, regions/api.py, the 22 tables it reads and the veg stamp.
  - world-esm (new): world.json, terrain stamp, water cells and records, navmesh build, the generator's .cs sources, the masters by size and time, veg and creatures. When it matches, it reuses out/terrain/esm/ArgoniaWorld.final.esm and skips the ESM write, the vegetation splice and the creature splice.
  - yaml, yaml-copy, round-trip (new): Argonia.esm's sha256.
- Stamps are memoised per process. `make plugin PLAN=1` (or `pipeline.py plugin --plan`) dropped from 129 s to 20 s. It takes no lock, builds nothing, and prints run/skip and the key for each stage.
- Fix found while measuring: input_hash and the generator key used ArgoniaGen.dll's mtime. Every `dotnet build`, the gate's included, rewrites that mtime, so the whole-build skip moved with no input changed. Both now key on the generator's sources.

## Measured (build VM, r6-ppr-plugin1, rc 0, 2026-11-04 09:05)
ground skip 0.2 s | terrain (cell rows, row-keyed) 1508.7 s | world-json 2.1 | water skip 0.0 | esm-write 35.3 | vegetation (band-cached) 182.6 | creatures 12.7 | world-esm total 246.5 | records 11.9 | yaml 13.1 | yaml-copy 0.3 | round-trip 3.3 (green). The wall time was about 1840 s; the 2018 s "total" counts world-esm's nested stages twice. The logs give 232 s median and 1752 s p90. The terrain row build is the sink: 82 % of the run.
Plan straight after: ground, terrain, water, vegetation and creatures all skip. world-esm showed run because of the dll mtime (fixed above).
ArgoniaWorld.esm sha256 66be65e603c9…, equal to the final.esm cache. Argonia.esm 1b46c02030f0….

## Remains
- (3) terrain generate is a province-wide raster solve: blurs, chamfers and Lipschitz sweeps whose reach is unbounded. A per-block split would change bytes, which the brief rules out. Land rows (row_key) and vegetation bands are already cached per block. The 1508 s terrain stage was row-keyed but still slow: the next cut is a profile of the row build. The one-place versus province-wide before/after seconds were not measured (two reboots).
- (4) rerun `make plugin-check` (regenerate twice identical) on this pipeline.
- records and world-json stay unkeyed (12 s and 2 s).
- plugin/Argonia/ YAML from this build is uncommitted and outside this lane's paths.
