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
