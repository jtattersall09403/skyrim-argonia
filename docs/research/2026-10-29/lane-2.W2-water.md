# Lane 2.W2-water: hand-off at the context marker (commit 6c5e198)

## Hand-off (read first)
**Done and committed (6c5e198):**
- The hydrology family is in the world database. `hydrology_body` was expanded in place: it was 2.W2's key-only
  placeholder, and the migrator keeps the live block of any table it does not own. The other 11 tables sit below
  the 0030 marker. Rows came from `tools/argonia_world/water/migrate.py` through db.py: 2,280 bodies, 615 reaches,
  12,034 centreline points, 202 junctions and 101 rivers, plus child tables and `hydrology_setting`. The
  allowlist line for `hydrology_body.jsonl` (1.34 MB) is in the same commit. `world/sources/hydrology/` is still
  there; delete it once nothing reads it (the migration takes the path from `--graph`).
- `tools/argonia_world/water/` holds model, classify, steps, field, oriented, plan, layer, `__main__`
  (`python3 -m tools.argonia_world.water plan`, which needs numpy, so run it with `~/.argonia/venv/bin/python`) and
  4 L1 tests that pass under the system python.
- **Shared-file warning:** `git commit -- world/schema.sql` also committed the other lanes' uncommitted schema
  blocks: regions, weather, roads, routes and terrain (eco_class ... terrain_patch_outcome). `db check` was green.
  Those lanes should check their blocks.

**Measured (full province, 2026-10-29; peak RSS 0.66 GB, 9 s):**
- Classes. Bodies: sea 1, lagoon 20, lake 70, pond 2,189. Reaches: river 492, rapids 105, falls 18. Springs: 101.
  Water types: sea, brackish, fresh, black (layer.py).
- `plan` covers 2,276 of 2,280 bodies. 15 of those stand inside other water and their level differences are
  listed (`checks.bodies.standsInOtherWater`). The Blackrose lake (body.1290-3508) is covered because the graph
  says another body realises it. **4 bodies are uncovered**, all carve-made backswamps whose ground is above their
  level on the patched ground: body.1188-2927, body.1511-2642, body.1523-2643, body.1902-3267. They need a ruling:
  terrain lane or loss.
- No wet sample is left without water. Overlaps of two planes at the same height: 0. Planes at their cell's own
  level: 0. Plane samples floating over lower water or open ground: 0. 62,306 samples sit under a lower plane
  hidden by the bed of higher water.
- Steps: 2,052 on 281 stepped reaches, no grade violations. The largest drop is 13.7 m on a chute; drops are 0.5 m
  where the reach length allows. Pieces, all resolved to vanilla bases: rapids 567 (FXrapidsFallsLine01),
  cascade 1,408 (FXWaterfallBodySlope_static), falls 18 (FXWaterfallBodyTallnoLOD, Dawnguard), mist 18.
- Banks: 111 of 281 reaches are flagged, at 534 of 5,821 centreline points, for water above the bank top (ground,
  or the water standing beside it). The excess has a median of about 0.3 m and a tail up to 9.8 m (plan.json
  `checks.banks.flagged`).
- Cells with water work: 4,197 (height 919, planes 3,230, default 48). **There are 56,310 plane references**,
  23,987 of them a single sample (128 units). The median cell has about 10, the 95th percentile 62, the maximum
  264. Cell (12,-5) is over its 256-id FormID slot. This is the open problem; the causes and the options are below.
- Sample reach: reach.949-1591 (river.352-503, horizontal-channel, 156 m, drop 4.38 m, width 11.4 m). It has 9
  steps of 0.487 m about 17 m long and 9 rapids pieces. It starts at east 1734.6, south 2908.1 m, which is Skyrim
  (-132481, 58496).

**Left, in order:**
1. The plane count. The causes are measured: steep reaches put up to 9 steps in one cell (axis blocks staircase
   along diagonal step lines), and the marsh has 9 to 14 interleaved levels per cell. Turned step planes
   (oriented.py) placed 486. Things tried: snapping levels within 0.2 m saved 5% but buried 18 bodies, so it is
   off (plan.py:31 `SNAP_M = 0.0`). Skipping films under 0.1 m saved 10% but left 1,400 bodies' edges bare, so it
   is off (`SHALLOW_M`). Leak tolerance up to 0.5 m saved 20%. Options: a per-cell plane budget with the loss
   measured, or the brief's fallback (one height per cell plus regrading the terrain). The 2.W2 L4 proof should
   time a 60-plane cell in game before anything is chosen.
2. `tools/ArgoniaGen/WaterRecords.cs`, not written: WATR and ACTI writers from `layer.records()` and
   `ApplyCell(cell, line)`, which sets WaterHeight, Water and Cell.Flag.HasWater and adds the refs. Then one
   `case` line each in Generate (or LandWorld.cs per 0031) and "WATR","ACTI" in intermediate.TYPE_ORDER. The
   terrain lane agreed the `out/water/cells.jsonl` stream. The cell water belongs in ArgoniaWorld.esm: talk to
   the terrain owner (a0ec3e8963eb3a659) or the planner first. Its WRLD is 000800:ArgoniaWorld.esm. The water
   FormID range in layer.py starts at 0x100000, clear of the cells.
3. Writer unit test, `tests/journeys/water-*.yaml` drafts (swim three reaches by class, NPC swim paths, 30 step
   stills, Community Shaders tuning), the journal at `docs/research/journals/water.md`, and the 2.W2 Outcome.
4. Use `build.game_heights_m` (quantised LAND ground) in the banks and float checks instead of
   `refined-height-f32`. It differs only on cliffs.

**Reds:** `make check` fails on `unit` and `plugin-check`: `ModuleNotFoundError: numpy` in
`terrain/tests/test_land_writer.py` and `test_terrain.py`, and in the pipeline under the system python3. The
terrain lane's numpy needs to reach the gate's python (the venv on PATH, or importorskip). The water tests are
green.

# Continuation (lane 2.W2-water, second context, 2026-10-29)

## Acceptance
- **The plan at budget 32 covers every body:** 2,280/2,280. Each body has a plane, a cell height, the default
  water, or a recorded loss: 6 buried and 3 others. 0 unrealised wet samples, 0 same-height overlaps, 0 floating
  plane samples, 0 step violations, no cell over 32 planes (max 32, p95 27).
- **ArgoniaWorld.esm carries the water:** 4 WATR, 4 ACTI, the WRLD's NAM2 set to the sea, 1,150 cells with
  XCLW and XCWT, and 33,745 REFRs (32,214 planes and 1,531 pieces), read back from the bytes. It is 116,095,472
  bytes.
- **`make plugin` is deterministic.** A second write gives the same sha256, 89b6331a..e8d9a939. The plugin step
  peaks at 1.15 GB and the full build took 224 s.
- **The writer test passes:** `water/tests/test_water_writer.py`, 4 tests.
- **`make check` is green:** 157 passed, 64 s, 0.29 GB. The sample manifest was regenerated deliberately: 653896d8.
- **Peak RSS:** water plan 1.34 GB, make plugin 1.15 GB.

## The plane budget (the ruling), as built (`water/budget.py`)
1. **The greedy cover** (lossless, `plan.greedy_cover`): non-overlapping squares, largest first, at any offset.
   It is used where the quadtree passes the budget. In the 828 cells over 16 it needs 27,818 plane references
   against the quadtree's 41,261.
2. **Merges, smallest loss first** (loss = samples x cm), re-estimated per candidate:
   - interleaved non-river levels within 0.25 m merge in that cell only;
   - consecutive steps of one reach whose levels both stand in the cell merge into one step. The whole step
     moves, so there is no seam. A merged drop may be up to max(2.0 m, 2 x the grade's step).
   After each round (3 to 4 rounds) the field is rebuilt.
3. **The fallback.** The cell stands at one height, the weighted median of its water levels. Its low ground is
   flooded and its higher water dried. Border vertices are raised 0.1 m above both the height and the water
   beyond, unless the same water continues across the border.
   - The regrade is the `water_regrade` table, applied by `terrain/water_regrade.py` through
     `grid.Sources.heights`; the planner told me to add it there once the terrain lane closed.
   - The losses are `water_loss` rows (entity, cell, kind, samples, max cm, mean cm), and the reduced cells are
     `water_budget_cell` rows.
   - `water plan --write-db` writes the rows. Every other run fails if they differ from the plan.

| budget | cells over | merged | fallback | regraded vertices | ring cuts | bodies with loss | reaches with loss | plane refs | cell heights |
|---|---|---|---|---|---|---|---|---|---|
| 16 | 731 | 107 | 624 | 23,639 | 13,836 | 393 | 214 | 18,932 | 1,519 |
| 32 | 344 | 85 | 259 | 11,243 | 6,903 | 153 | 154 | 32,214 | 1,150 |
| 64 | 103 | 34 | 69 | 4,139 | 1,988 | 53 | 64 | 47,441 | 960 |

Loss in samples by kind (one sample is 1.83 m square):

| budget | fallback-flooded | fallback-raised | fallback-dried | fallback-lowered | step-merge | snap | dried | flooded | buried |
|---|---|---|---|---|---|---|---|---|---|
| 16 | 88,581 | 45,285 | 31,309 | 13,780 | 2,536 | 6,343 | 1,456 | 586 | 569 |
| 32 | 38,397 | 25,383 | 17,848 | 9,906 | 5,183 | 3,825 | 2,327 | 892 | 282 |
| 64 | 16,307 | 9,857 | 4,346 | 4,983 | 4,183 | 918 | 610 | 413 | 82 |

- **Worst bodies at 32** (max cm moved): body.6-629 (25.4 m, 86 samples), body.951-323 (20.8 m, 317),
  body.1031-1148 (17.0 m), body.56-1206 (16.0 m). These are small bodies inside steep fallback cells.
- **The stepped-river proof's reach** (reach.949-1591) is merged at 32, from 9 steps to 5. Its banks are not
  flagged.
- **The 4 backswamps.** Three are recorded losses: body.1188-2927 and body.1902-3267 are `buried`, and
  body.1511-2642 is `buried` plus `fallback-dried`. body.1523-2643 is realised on the game ground. The terrain
  lane had closed, and the planner said nobody owns terrain/ now. No one-line terrain patch was made, so the
  ruling's default (record the loss) stands.
- **The next lever, not taken (my call: it is outside the ruling).** Turned step planes fail on 1 to 13 samples
  of the lower step's water under the square. Letting a step's plane overhang the lower step by up to one sample
  under its rapids piece, which is how vanilla rivers hide their step lines, would save most of the step bands'
  staircase and so most of the fallback. It needs the L4 stills to judge.

## Owed items 2-4, done
- **WaterRecords.cs** is a separate file. The hook in LandWorld.cs is 3 lines (Load, ApplyCell, CheckAllApplied);
  Program.cs gained `--water`; terrain/world.py's load order gained Dawnguard.esm for the falls piece. The order
  with 2.W3 was agreed by message: 2.W3 committed 7e34247 first, then I built on it.
- **pipeline.py** runs the water plan under a stamp: the water and terrain code, the hydrology and water tables,
  and the piece index. The sample build gets the sample cells' lines, and `_terrain_stamp` covers the regrade.
- **Checks on the LAND's ground.** The whole plan now stands on `build.game_heights_m`, not only the bank and
  float checks. Checked against the refined plan, the game ground found 2,342 floating samples (quantisation of
  0.114 m against a 0.05 m tolerance); planning on it gives 0. Banks are flagged on 110 reaches.
- **Journey drafts:** `tests/scenes/water-budget-32.json`, `water-budget-64.json`, `water-reaches.json`, and
  `tests/journeys/water-budget.yaml`, `water-swim.yaml`, `water-npc-swim.yaml`, `water-steps-stills.yaml`,
  `water-look.yaml`.
- **The journal** is `docs/research/journals/water.md`. The 2.W2 Outcome and 2.W4's Starting state are written.
- **world/sources/hydrology/.** Only `hydrology-graph.json` is deleted, with its allowlist line. A grep found no
  readers, but `names.json` (152 water names) is not in the database, so the directory was not deleted whole; its
  README says so. The chunk that names water should migrate it.

## Bugs found and fixed
- Step codes rounded in float64 against the field's float32: off by 1 cm, so they hid most step merges.
  `plan.code_of` is now the one conversion.
- The C# `sea ??= Type(...)` wrote only one WATR. The writer test caught it.
- My regrade call landed in `Sources.classes` too, and 2.W3 caught it: height floors were written as class ids
  (index 92). The test now asserts classes are unchanged.
