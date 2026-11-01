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

## Session 4 (2026-11-01): the Skyrim.esm audit applied (skyrim-does-it-this-way.md §4, §9)

- **Blends (§4):** stops pick one texture per vertex (ties split by per-texture noise), then a 2x2 mean. Synthetic
  shore runs p10/p50/p90 1/1/5. Sample `terrain check`: blend runs p10/p50/p90 1/2/4 (n 2,163), layers_max 6
  (base + 6), layers {0:22, 1:10, 2:6, 3:11, 4:4, 5:1, 6:2}.
- **VCLR (§4):** no slope or aspect term, and the old ground tint is dropped. The darkening is a 256 u water band
  (to ~150) plus wet flats. Province luminance p10 147.3, p50 253.9, 20.7 % under 200 (vanilla 185/255/13.9 %).
- **Sequence (§4):** bed below -384 u, then mud (under water only) and edge from -384 u, the edge on to +128 u,
  then land. Sea beach to +256 u.
- **Apron (§9):** `border` class alone with no blend, one base per quadrant (`quadrant_sets(bare=)`). A province
  quadrant takes its bare neighbours' bases first. Check: apron_layers_max 0.
- **check:** `blend_max_step` is replaced by `blend_runs` (fail p50 > 2 or p90 > 5), `vclr` and `apron_layers_max`.
  Its other fails are the ground lane's: fit 6 dry_edge_below_water, 25 sites_unshaped, 1 overflow cell.
- pytest terrain + water: 51 passed. Sample build: 24 s (was 3.7 s; not profiled).
- **Reader r1 (six windows, main's ground at 19:52):** -63_-63 PASS. -21_-26: narrow strokes, "the most
  marsh-like frame", with a flat lake and an orange stripe in a pond. 0_0, -12_63, -20_57, -38_25 FAIL.
  - Not ours (ground/water lanes, session 4 of the ground lane): rectangular lakes and notches (0_0), lattice
    squares in the lake (-20_57), translucent rectangles on the river (-12_63), the orange line lattice (the base
    map's step lines).
  - Ours, owed: grey rock swathes (ROCK slope >= 34 on -12_63, -20_57); the apron render on -38_25 (layer_rgba
    draws per-vertex weights, not the quadrant bases the build writes); mud blobs on open water beds.

## Session 5 (2026-11-01): rock patches, bed band, VCLR fit, render, build time

- **Vanilla rock by slope (measured, Skyrim.esm, 9,500 LAND):** rock is the dominant texture on 9 % of
  vertices under 10°, 20 % at 20–30° and 24–25 % over 34°. A steep cell carries 3 distinct dominant textures at
  p50 and 6 at p90. Rock is a patch texture, not a threshold. `ROCK`/`CRAG` are now noise-gated patches on their
  own noise field (`Stop.seed`; the seed is not in `material_gradient`). Land stops run on up steep ground. The
  six windows read rock 0.05 / 0.26 / 0.33 / 0.46 / 0.50 at 20–30 / 30–34 / 34–45 / 45–60 / 60–90°. That is above
  vanilla's 25 % because we have no snow.
- **Bed band:** wet vertices beyond `SHORE_BAND` (3) vertices from dry ground read 2.5 m deeper per vertex, so
  an open shallow bed takes the bed texture and never mud. Test `test_open_shallow_bed_takes_the_bed_not_mud`.
- **VCLR:** the band straddles the line (`dshore`) and does not darken the open bed. It is 6 vertices wide, and
  wet flats take 0.2. Six windows: p10 179, p50 255, 14.5 % under 200. `terrain check`'s sample: 203.5 / 255 /
  9.3 %. Vanilla: 185 / 255 / 13.9 %. Session 4 read 147 / 20.7 %.
- **Render:** `built_weights` draws the quadrant sets and seam fix the build writes, so the apron shows one
  base per quadrant.
- **Build time:** 20 s of the 24 s was `png.read` decoding the unused ground tint in every worker. It is now
  cached (`~/.cache/argonia/png`). `nearest_wet` updates only the overlap. Sample build: 3.2 s at load 2.8, and
  7.2 s at load ~10 with other lanes running. Check: layers_max 5, blend runs 1/2/4. Its fails are the ground lane's.
- **Noise scale:** the patches are about half the old size: noise 28/9 vertices, rock 22/8, tie 14, class warp ±30 over 160.
- **Reader verdicts:**
  - Pass 1: 1 PASS of 6. -12_63: "flat green/rust blobs with grey patches; river banks have a good gradient".
    -38_25: "worst: straight-edged rectangular texture zones".
  - Pass 2, after the smaller patches and the wider warp: 2 PASS. -21_-26 PASS: "smooth gradient, no mud on open
    bed". -38_25 FAIL: "hard straight-edged cell blocks". 0_0 FAIL: "dark green covers most of the land".
  - Pass 3 tried a dry-side edge limit and a smoothed far level. It regressed to 1 PASS, and -21_-26 got "a wide
    uniform light-blue shelf rings every shore". **Reverted.** The tree holds pass 2's state.

## Starting state

- **Done (session 6):** -38_25's seams tested on the window. Local water was refuted (`local` is smooth at cell
  lines: 2nd difference 0.003 vs 0.012 off them). The causes were the ground and dry hollows. First, the
  source heights are piecewise linear every 16 vertices, so their 2nd difference is 0.84 on those lines against
  0.05 off them, and slope-gated stops switched there. The slope keys now read a 16-vertex tent (`SLOPE_R`).
  Second, dry ground under a nearby level had dh down to -28 m and took the riverbed. Dry dh is now clamped at 0
  or above. Flooded-forest has 5 land stops, each on its own noise: on 0_0 the shares are 28/25/24/17/4 %.
  The tests are `test_no_texture_boundary_runs_along_a_cell_edge` (fails with SLOPE_R=0),
  `test_flooded_forest_floor_is_patches_not_a_swathe` and `test_dry_ground_is_never_a_bed`.
- **Owed here:** light-blue edge shelves on wide flats; the "cartoonish blobs" read, which the in-game stills
  decide; `make plugin` and the in-game look (the planner's batch).
- **Owed elsewhere:** the ground's straight cliffs on -38_25 (35° bands along cell columns): material follows
  them, so the ground lane must fix them. Also rectangular lakes, square cuts and translucent rectangles
  (ground and water lanes), and the routes' cover read (routes lane).
