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

## Measured (session 2, 2026-11-01)

- `terrain build --sample` (15 cells, generated ground, solved water): 1.3 s build. Layer histogram
  {0:5, 1:17, 2:16, 3:15, 4:3, 5:4}. `terrain check`: fails [], layers_max 5, blend_max_step 0.396.
- Render time per 10×10-cell window (321² vertices): 0.36–0.96 s.
- pytest terrain + water + vegetation: 49 passed (27 in terrain).
- ArgoniaGen built here (`~/.dotnet`). A generate run on the texture-set layer wrote 19 TXST and 19 LTEX, read back
  with `terrain/esm.py`. All 19 LTEX TNAM name our TXST, and its TX00 is `TEXTUREPACK\landscape\…`.

## The render diagnosis (one window per cause, measured)

- **mat3's hard horizontal edge: proven, fixed.** The class map put the `border` class on every apron vertex, so the
  rim was a straight class line with a 30 m blend. Now the apron carries on the nearest province class.
- **mat0's block borders: proven, fixed in the class map.** Classes came per cell (coastal and northern cells
  alternate in cell-shaped patches). The lookup is now domain-warped by noise (±14 vertices), and the class blend
  widened to ~45 m.
- **mat3's vertical streaks: proven, not ours.** In the apron rows north of the rim, heights vary 7–8× more across
  columns than down rows (mean |dx| 0.63–0.68 m against |dy| 0.08–0.09 m; inside the province 0.41 against 0.30).
  `grid.py`'s `_edge` clamps to the nearest province sample, so the edge row is smeared outward. The fix belongs
  to the ground lane's apron blend. The material follows the ground faithfully.
- **mat1's dark-blue swathe: legitimate.** The window is all apron sea (h −4.9…−0.5 m). Readers 2–3: "clean …
  legitimate sea swathe".
- **Thin rings round water, wedge and rectangle outlines (mat0, mat2): not resolved.** The suspected cause is
  the solve's one level per cell. The wet footprint `ground < cell level` ends at a cell edge where neighbours
  differ, so the water outline itself is cell-stepped. dh no longer takes the exact cell level, but the outlines
  stayed. Owed: test on one mat2 window whether the outline follows the cell grid of differing levels (then it
  is the water and ground lanes' fit, not paint).
- Reader verdicts, third pass (r4). **The L3 acceptance is still not met:**
  - mat0: "heavily blotchy, with wedge, rectangle and ring outlines and no believable shoreline gradient"
  - mat3: "the apron is not sea and shows strong vertical striping" (the ground's apron, above)
  - mat2: "mostly sensible gradients, spoiled by hard polygon/rectangle outlines and a flat pale blob"
  - mat1: "clean and natural, and only the sub-water shallow gradient (mid/light blue band) is missing"

## Starting state

- **Done this session:** the world-reads guard fix (14e389b). Water from the solve (`material.Water`: cell levels
  via `terrain/cellwater.py`, local level via `solve.nearest_level` bilinear between cell centres; OldWater gone).
  The class warp and the apron inheritance. `render_layer(w)` now takes render.py's Window (`layer_rgba` for grid
  windows). TXST + LTEX overrides: `terrain/texture_sets.py` and `ArgoniaGen/TextureSets.cs`, with the grass
  layer leaving those LTEX to it; tests are in `test_texture_sets.py`. The `material_gradient` table (66 rows,
  `terrain gradient` writes it; a test keeps it equal to STOPS). The bmv `keep` in `data/dependencies.json`
  now holds `textures/texturepack/landscape/*` (stack.py reads that row; stack.py itself is unchanged). The BM&V
  sourcing-register row names the 19 files.
- **Owed:**
  1. The water-outline diagnosis above, then a 4th reader pass on the four windows. The render script is in the
     scratchpad: four 10×10-cell windows around world.SAMPLE through `material.layer_rgba`.
  2. The apron streaks: the ground lane (`grid.py` `_edge` clamp).
  3. The climatology rainfall field in `wet`.
  4. TXST normal maps: BM&V ships none. Decide whether to name TS's or vanilla's `_n` (needs the file list).
  5. A full `make plugin` with the texture-set layer, and the in-game look (the planner's batch).
  6. Retire the land-cover raster from vegetation, routes and navmesh (their lanes).
