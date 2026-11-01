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

## Session 3 (2026-11-01): outlines, rain, normal maps, retirements

- **The thin outlines, by cause (measured on w4, w5 of SAMPLE_1_15):**
  - *VCLR waterline cut (ours, fixed).* The wet shade applied only where `dh > -0.5`, so it peaked on the shore: ring
    pixels had VCLR 208–217 against 227–247 either side. The shade is now continuous (`vclr`). Reader: w5 rings
    17+ → 2–3, w4 6 → 3–4.
  - *The far-switch ring and cell lattice (ours, fixed).* Local water was a 60 m box mean switching to the cell
    rule at a fixed reach. It is now the nearest wet vertex's level (`nearest_wet`, jump flooding), smoothed ~30 m,
    easing into `nearest_level` over 40–64 vertices. Reader: w4's wedge lake became a smooth blob.
  - *The solve's one-level footprint (not ours).* Of the wet-mask edge, 103 px (w4) and 355 px (w5) are cuts where
    dry ground lies below the neighbouring cell's level. These are w5's rectangles, for the water and ground lanes.
    The ground lane's footprint fix (96e7247) landed after these renders.
- **Rain:** `rain_field` is climatology §3 R = 0.5 + 0.3 windward + 0.2 coast. The wind is from the south-east
  (§4), with a mid-slope maximum. The 40 km coastal decay is scaled to a quarter of the 7.4 km province. Province
  percentiles 0/10/50/90/100 are 0.55/0.63/0.70/0.86/0.97 (1.3 s). It lifts dry wetness by up to 0.25.
- **Normal maps: none (TX01 empty).** Black Marsh.esm's own landscape TXSTs leave TX01 empty on 8 of 11, and the
  other 3 name the diffuse. Tropical Skyrim ships `_n` for all 19 slots, but each is drawn to TS's own diffuse.
  The in-game look is the planner's batch check.
- **Measured:** `build --sample`: 3.7 s, layers {0:5, 1:14, 2:19, 3:12, 4:1, 5:9}. `check`: layers_max 5,
  blend_max_step 0.145 (was 0.396). Its 2 fails are the ground lane's place sites. pytest terrain: 34 passed (3
  new). Render per window: 0.1–9 s (w0 9 s, w4 5 s).
- **Reader pass 4 (r4, ≥1,000 px), not yet met:**
  - w3 PASS.
  - w0 FAIL: "a diagonal stair-stepped dark edge along the bank".
  - w1 FAIL: "flat deep navy", all sea.
  - w2: "swathe of deep blue, gradient visible".
  - w4 FAIL: "rectangular pond, 3–4 rings, grey band x 0–190".
  - w5 FAIL: "lattice of straight brown/orange bands, square blue rectangles, wedges, perfect circles".
- **Land-cover raster:** not retired, by measurement. Routes `Surface` reads it for existing roads and tracks. A
  swap to `routes/paint` agrees on 3,081 of 6,749 road and 2,316 of 20,896 track search cells (paths are not in
  the paint), which changes the route search. That is for the routes lane, not a small edit. Navmesh reads it
  only on its old-sculpt fallback, and `grid.Sources` loads it (ground lane).

## Starting state

- **Done:** e29ac9a (material.py `nearest_wet`, `rain_field`, continuous VCLR wet shade; texture_sets why; 3 tests).
- **Diagnosed, owed elsewhere:** the footprint rectangles (water/ground fit); routes' cover read (routes lane);
  `grid.Sources.cover` (ground lane).
- **Owed here:**
  1. Re-render on the ground after 96e7247. The script is the scratchpad `r6.py`: render.render with nearest-neighbour
     upscaling.
  2. w5's straight brown/orange lattice and perfect circles. Check the road paint (`_road`) and the place edits
     before the stops.
  3. The w4 left grey band and w0's stair-step bank.
  4. Fifth reader pass.
  5. `make plugin` and the in-game look (the planner's batch).
