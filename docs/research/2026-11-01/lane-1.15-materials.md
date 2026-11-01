# Lane 1.15-materials: the ground's material

## The texture set (measured 2026-11-01)

- **BM&V's landscape pack is not where the brief assumed.** Its files are `textures/TEXTUREPACK/landscape/`
  (the 118-entry listing comes from the vault's `manifest.txt` inside `s3://…/mods/vault-bmv.tar`, read with
  ranged GETs, nothing extracted). There are 55 base diffuses, dirtcliff, mountains, roads and 23 grass
  billboards. It covers every vanilla landscape name Tropical Skyrim covers, minus TS's `beach.dds` and
  `tropical\rivergravel.dds`. It ships **no normal maps**.
- **Black Marsh.esm does not override any vanilla TXST** (0 of its 144). Its own 3 LTEX point their TXSTs at
  `TEXTUREPACK\landscape\…`. Its 4,357 LAND records paint vanilla LTEX mostly: LPineForest03 has 6,079 layers,
  its rocksgrasswater LTEX 1,619, and LFieldGrass02 909. So BM&V's look reaches the ground only through
  TXST records that point at `TEXTUREPACK\landscape\<file>`. **Our plugin has to write those TXSTs.**
- The build VM's `bmv` folder is trimmed to 36 files with no TEXTUREPACK, because stack.py keeps only the
  textures that kept meshes name. **The stack trim has to keep `textures/TEXTUREPACK/landscape/**`** (infra's
  scope).
- The other Black Marsh mods ship no ground diffuses. Depths of Skyrim has 5 underwater grass textures and
  HTBM-Cipactli 3 shore grasses. Their GRAS forms belong to the vegetation lane.
- The chosen set is `material.TEXTURES`: 19 vanilla-named LTEX, each with its BM&V file and a `why`. Each
  `STOPS[class]` uses 4–6 of them. Grass lists stay the existing `ltex_grass` plan, and every chosen LTEX is
  already in it.

## The gradient

The keys are `dh` (height above local water), slope, northness, wet (a two-scale low-pass of the water mask)
and two-octave position-seeded noise. Stops are soft trapezoids. Uplands read a noise-banded height. Classes
blend over about 30 m and materials over 6–11 vertices. A quadrant keeps its base plus up to 5 textures, and
seams are restricted to the textures both sides keep. The water edge is bed → waterline → mud → land, after
vanilla's three stages. VCLR carries slope/aspect shade and wet darkening times the old tint.

## Measured

- `terrain build --sample`: 13 cells in 1.3 s. Layer histogram {0:15, 1:10, 2:10, 3:6, 4:7, 5:4}.
- `terrain check`: no failures; layers_max 5; blend_max_step 0.212 (fails above 0.5).
- Render time per 8×8-cell window: 0.27–0.75 s.
- pytest terrain + water + vegetation: 39 passed, 2 skipped.
- Reader verdicts (L3, iteration 1), **the L3 acceptance is not met**:
  - mat0: "lake edge convincing … polygon outlines and straight block borders around the red patches"
  - mat1 (SW apron corner): "one dark-blue swathe … vertical stripes … no shoreline"
  - mat2 (0,0): "best of the four … no hard edges … blue -> light blue -> mud -> green around all three water bodies"
  - mat3 (N border): "strong streaking … hard horizontal edge where green meets red earth"
- Suspected causes, not yet proven: the streaks sit where the render window met the grid rim and was
  edge-padded, and the apron's own heights; the block borders come from the per-cell region map or from the
  old body raster's level steps reaching `dh`. The next session first tests each cause on a single window.

## Starting state

- **Done:** material.py, which replaces paint.py (deleted); build.py and the CLI paint from it; the check's
  blend metric; test_material.py (7 tests); the render_layer for render.py.
- **Owed:**
  1. TXST records (TX00 = BM&V's file, TX01 = TS/vanilla normal) and LTEX TNAM overrides in ArgoniaGen. dotnet
     is not on this VM.
  2. The `material_gradient` table: `gradient_rows()` is ready, but the schema and db.py rows are not written.
  3. Swap OldWater for `water/solve.nearest_level` (landed in dc320a6). The fixture misses stepped rivers.
  4. The climatology rainfall field in `wet`.
  5. The sourcing register rows.
  6. Retire the land-cover raster from vegetation, routes and navmesh (their lanes).
  7. The stack trim fix for TEXTUREPACK.
