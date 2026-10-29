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
