# Lane 2.W1-terrain: hand-off at the context marker (commit c8638c1)

## Hand-off (read first)
Done and committed: `tools/argonia_world/terrain/` (grid, quantize, paint, landcover, edges, build, png, vault,
tests: 5 L1 tests green on a synthetic 4x4-cell grid with an apron and a 60 m cliff: VHGT round trip, seams 0,
height error < 0.06 m, layers <= 6, composite = weights within 0.02). `skyrim_units.py` gained the province grid
and LAND layout facts. NOT yet done: `__main__.py` CLI (`build [--cells x0,y0,x1,y1]`, `check`), the full
15,876-cell run with `/usr/bin/time -v`, the L1 checks on real data (1,000 random points, seams, normals,
overflow survey numbers), the WRLD/REGN intermediate record (edges.py has the border polygon and gate plan),
`tools/ArgoniaGen/Land.cs` + its 4-cell test, the schema block, db rows, tests/scenes|journeys terrain-* drafts,
the journal, 2.W1 Outcome and 2.W2 Starting state, `make check`.

## Findings that bind the rest (all measured 2026-10-29)
- **Imported records' y runs SOUTH** from the province's NW corner (old 0003 "X east, Z south"; route-grade
  profiles sit on the heightfield at row = y/1.82784, median error 0.23 m vs 21 m flipped; Tear Road Stage
  y=238 is the north exit, Gideon x=1551 the west one). The heightfield's row 0 is the north edge.
  `intermediate._pos` (metres_to_units on y) mirrors any province layout N-S: exteriors must use
  `su.province_to_skyrim`; the 0.4 pipeline lane should be told (interiors mirror too).
- Sample = 1.82784 m (hydrology `mpp`) = 128 units on the grid. Province cells -62..63 both axes (old ESP
  export's meta.json); near apron 68 cells each side (cells -130..131).
- VHGT on 42 vanilla Tamriel cell pairs: 0 seam with offset in 8-unit steps, Mutagen HeightMap[x, y] (x east,
  y north-from-south). VTXT position = x + 17*y (0.003 mean quadrant-edge mismatch vs 0.22). Vanilla max 6
  alpha layers/quadrant. VNML signed bytes (flat ~ 0,0,127).
- Old chain hash chain verified: frozen 4a74.. -> terrain patches (119 applied, 47 refused) -> 0248.. ->
  route-grade (118 applied) -> `refined-height-f32.npy` 638c..; it differs from frozen in 47,084 samples, all
  inside patch regions. The generator uses that file as frozen + patch layer (grid.py docstring).
- Overflow survey (raw, adjacent samples > 127 steps = 14.5 m): 14,126 x-pairs, 9,810 y-pairs; 5,715 x-pairs
  on land; 658 cells; steps up to 133 m. "Re-base per row" is impossible in VHGT (one offset per cell); the
  limiter (quantize.limit, envelope midpoint) is the cure. DEFECT to fix first: the midpoint spreads a cliff's
  error far from it (a 1000-step jump moves vertices 5 samples away by 182 steps); replace with a local spread
  (e.g. only move vertices whose envelopes differ, ramp centred on the cliff), then re-measure max error.
- Inputs fetched by `python3 -m tools.argonia_world.terrain.vault` (pinned sha256, `$ARGONIA_DATA/terrain/`):
  landcover-i16 (37 classes; 4/25/30/36 = BLACK_MUD/SALT/BC_ROAD/DIRT_CLIFF by measured height/slope),
  apron-source-near (Transbot9, 8385^2, same orientation as the heightfield, r=0.84), ground-tint.png (1009^2
  RGBA, same orientation), receipts. Transbot9 is present; record it in the sourcing register (CC BY-NC 4.0).
- LTEX: Skyrim.esm has 68; Tropical Skyrim (vault 33017 LE file list) replaces 66 (not LMineFloorDirt01,
  LScrub01). Mapping in landcover.SEED; re-check against SE 78044 when 0.2 syncs it.
- Apron: 17,654 near-ring cells have ground above -2 m (of 52,768); the far ring would be ~76k cells (skip).
- Plugin size: 15,876 + 17,654 LAND cannot go through Spriggit YAML into git; proposed: a separate derived
  plugin (`ArgoniaWorld.esm`, build.LAND_PLUGIN) not serialised, cell/LAND FormIDs computed from a reserved
  base (build.Builder.keys); a planner call. Hence the brief's 4-cell writer-test path.
- Border: Mutagen Region has MajorFlag.BorderRegion: the closed edge is one border REGN over the province
  outline (edges.border_polygon); its engine message is a vanilla string for the immersion inventory.
- Planner: schema block goes below "-- == End of the 0030 migration's tables ... ==" (tables: terrain_input,
  land_cover, land_cover_ltex, terrain_patch_outcome; terrain_patch keys from the receipts).

## Continuation (2026-10-29, second context): L1 done on all 15,876 cells; ArgoniaWorld.esm built by `make plugin`

**Acceptance, measured.**
| Check | Result |
|---|---|
| Height error at 1,000 random province vertices (seeded) | 995 unlimited points: max **0.057 m** (rounding to an 8-unit step). 5 limiter-moved points, reported apart: max 30.2 m |
| Every province vertex (16.26 M) | unlimited max 0.0571 m; 53,748 limited (0.33 %), max 60.4 m |
| Seams | **0** of 66,667 shared cell edges, heights and normals |
| Layers per quadrant | max **6**: histogram 0:69,567, 1:22,263, 2:13,567, 3:8,335, 4:6,798, 5:5,558, 6:9,012 |
| Full terrain build (33,775 cells) under `systemd-run MemoryMax=3G /usr/bin/time -v` | 3 min 51 s, peak RSS **684 MB** |
| L1 check over every cell | 17 s, 109 MB |
| ArgoniaWorld.esm, `ArgoniaGen world` | 113,402,485 bytes, 24 s, peak **1.08 GB** (it was 3.2 GB with Mutagen's parallel writer; `.SingleThread()` plus a 1.5 GB heap limit and GCConserveMemory 9 fixed it) |
| Determinism | sha256 **d7f6cb48b93f9b06..** on four builds: parallel, single-threaded twice, and `make plugin` (3 min 19 s, peak 1.08 GB) |
| 4-cell writer test (`terrain/tests/test_land_writer.py`) | passes. The ESM is read back from its bytes (`terrain/esm.py`): WRLD, the CELL grids, VHGT, VNML, VCLR, DATA 0x1F, BTXT/ATXT/VTXT opacities, and two writes giving the same bytes |
| Gate sample (`plugin-check`) | 13 cells in 4 boxes (the worst cliff, the SW corner into the apron, the middle, the Tear gate cell), ~11 s; sha256 e8ccae70.. in `terrain/sample-manifest.json`; the sample's lines equal the full build's |
| `make check` (venv on PATH, as setup.sh exports it) | **CHECK GREEN**, 40 s |

**1. Limiter (fixed first).** Both ends of every overflowing pair are pinned to the L-infinity midpoint, and
every other vertex is clamped into the cone those pins allow. A 1000-step jump now becomes a centred ramp at the
full 127 steps per sample: 0 0 0 0 0 0 55 182 309 436 | 563 690 817 944 1000. Vertices 5 samples away do not
move. The result is never worse than the midpoint at any vertex (tested on rough random ground).
**Overflow survey** (province, raw): 23,880 pairs. 3,660 lie wholly under the sea, 8,940 are sea cliffs and
11,280 are on land, in 674 cells. The steepest is 135.1 m in one sample. The worst cell is (-19, 58): 177 pairs,
-106..159 m. Province vertices moved by the limiter: 47,637 by more than 0.5 m, 41,424 by more than 2 m,
33,374 by more than 5 m, 24,902 by more than 10 m. Those are the cliff faces, which VHGT cannot store steeper
than 82.9 degrees. Whether they look right is the terrain-vantage L4 still.
**2. CLI.** `python3 -m tools.argonia_world.terrain build [--cells=x0,y0,x1,y1 | --sample]`, `world`, `check`.
`check` also writes `out/terrain/probe-points.json` for the L4 probe.
**3. Apron.** The near ring has 17,899 cells with ground above -2 m. Its 34,869 open-sea cells get no LAND and
take the WRLD default land of -2048 units under water 0. The far ring is left to LOD, as accepted.
**5. WRLD and border.** `terrain/world.py` writes the WRLD intermediate. Its ids are computed: WRLD 0x800,
the top cell 0x801, then a CELL and LAND pair per grid position from 0x810. Climate, music and water are left to
an Argonia.esm override, because ArgoniaWorld.esm cannot link to its dependant. Per 0031 §2 the border REGN
belongs in Argonia.esm, so 2.W3 (ae2c4c34ad361d116) writes it. I sent them the polygon, the vanilla
BorderRegionSkyrim layout (one area, falloff 0, a Map entry) and the two provisional gates: Tear road at cell
-12,63 and Blackwood Road at cell -62,11. No reply yet.
**6. LandWorld.cs** (`ArgoniaGen world`) streams the cell shards and builds blocks and sub-blocks in number
order. pipeline.py: `make plugin` also builds out/ArgoniaWorld.esm, rebuilding the terrain only when a stamp
changes (the terrain code, the land-cover rows, the input sizes and times). `check` rebuilds the sample and
compares its hash.
**7. Mirror.** `intermediate._pos` is replaced by `_pos_exterior` (through `su.province_to_skyrim`) and
`_pos_interior` (y negated). Its only callers today are the holding cell's two refs at 0,0, so plugin/Argonia/
is unchanged. The round trip and regenerate-twice are green. Tests are in `terrain/tests/test_mirror.py`.
**8. Schema and rows.** The terrain block went in below the end marker: `terrain_input`, `land_cover`,
`land_cover_ltex`, `terrain_patch_outcome`. 2.W3's commit 3dc6052/d5ee035 swept it into HEAD with their working
copy of schema.sql; the text is mine and unchanged. Rows by `terrain/migrate.py`: 6 inputs, 37 classes,
37 LTEX, and 284 patch keys and outcomes (166 terrain: 119 applied, 47 refused; 118 route-grade applied). The
build now reads the classes from the database. The patch definitions stay unmigrated, because the generator
reads the post-patch array.
**9.** Drafts: `tests/scenes/terrain-{heights,vantage,edges}.json` and `tests/journeys/terrain-border-push.json`.
The journal is `docs/research/journals/terrain.md`.
**10.** The 2.W1 Outcome is written. 2.W2's Starting state is rewritten with the heights API
(`grid.Sources.heights`, `build.game_heights_m`, the cell lines), and I sent the same to 2.W2 (ab3bc8eb83faf19fc).

**Owed:** L4 (probe heights, 20 vantage stills, border push); the TS LTEX re-check against SE 78044; the WRLD
override in Argonia.esm (climate, music, water); the border REGN and gates (2.W3).
**Note for the planner:** the gate needs `~/.argonia/venv/bin` on PATH, as setup.sh prints it. System python3
has no numpy. With the venv on PATH, ruff runs and reports 76 findings in other lanes' files, none in mine.
