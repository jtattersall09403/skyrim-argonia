# Journal: the parchment chart (chunk 2.W4 §c)

What was tried, measured and learned for `tools/chart/`, so nothing is lost at a hand-off. The lane report is
`docs/research/2026-10-29/lane-2.W4-chart.md`.

## 2026-10-29: the first renderer (lane 2.W4-chart)

- **Orientation.** Database positions run x east and y south of the north-west corner (intermediate.py's mirror
  rule), and the terrain arrays have row 0 at the north (grid.py), so a chart pixel needs no flip: col = x/S, row =
  y/S. Measured: all seven cities land on land (on road paint, classes 29/30) this way. Mirrored, Thorn falls in the
  sea (cover 35). `meta.json`'s "row 0 is the southernmost sample" is wrong for the arrays the grid reads.
- **The canvas.** 4096^2 = the 4032-sample province at 1 px per sample plus a 32 px (one cell) margin. Cells and
  256 px tiles both sit on the 32 px lattice, so each cell lies in exactly one tile.
- **Thresholds.** Major rivers: Strahler >= 2 (20 of 101). Major roads: route class trunk or road (8 of 23 legs).
  Sea = cover {33, 35}. Marsh = cover {3, 4, 5, 7, 8, 11, 15}. The rest (minor rivers, tracks, paths, the 560 other
  placed places) goes in the revealed layer.
- **Drawing.** Line features (coast, water lines, contours) are iso-lines of blurred fields, |f - t| / |grad f|,
  which gives antialiased lines for free. Strokes are drawn into 8-bit masks at 2x and box-reduced. A hand's wobble is
  smoothed normal noise, clipped to 2 amplitudes. All randomness comes from sha256-named seeds.
- **Memory.** The first full-canvas version peaked at 565 MB at 2048, which projects to about 2.2 GB at 4096. With
  the fields, noise and compositing computed in 512-row bands (noise as separable smoothstep value noise, so any band
  equals the whole), the 4096 master peaks at 976 MB in 87-101 s.
- **Libraries.** The venv had no Pillow and no cairo; Pillow 13.0.0 (FreeType 2.14.3) was pinned in
  `infra/build-vm/toolchain.lock`. The sample hash is of raw pixels, not PNG bytes, so it does not depend on zlib.
- **Font.** Pelagiad comes from its author's repo (isaskar/Pelagiad @ f9813019), sha-pinned, into
  `$ARGONIA_PRIVATE/fonts/pelagiad/` with its OFL licence. Current OpenMW master no longer carries it; 5389ce08 did.
- **Reader (L3).** Round 1 FAILED: rivers and roads were too thin and alike at phone size, the border was faint, and
  the tufts were sparse. Fixes: thicker tapering teal rivers, a dark sepia double-line road, a heavy red-brown border
  dash with an ochre band, denser and larger tufts, cities about 20% larger. Round 2 PASSED.
- **Gate trap.** `test_unit_facts_live_only_in_the_units_module` greps tools/ for the literal 4096. The chart's
  pixel size is `MASTER = 1 << 12`.
- **Open polish** (the reader's round 2, none of them blockers): clip roads at the city ring, keep tufts clear of the
  glyphs and labels, more road weight at 512, vary the tufts in the dense south-west.

## 2026-10-29: the old project's chart style (lane chart-old-style)

The owner asked whether the hand-drawn map was the old repo's and ruled that it follow it. It was not: the first
renderer came from the brief. The old map the owner liked is the **"Chart" treatment** of the old map window (it
had three: Faithful, Chart, Waterways). The owner called it "gorgeous" (old `lanes/2.5x/map-report.md`). Read from
`jtattersall09403/elder-souls-argonia` at `b581910f` through `gh api` (no clone; only the files below were
fetched). Its rendering code was read for the look (0026); our renderer reproduces it over our own data.

- **Where it lives (paths at `b581910f`):**
  - `packages/ui/src/tokens/map.ts`: `MAP_CHART`, the palette, and `MAP_SIZE`, the weights.
  - `packages/ui/src/map/shade.ts`: the per-pixel base (paper, land tint, water wash and ripples, contours), plus
    `treeMarks` and `marshTufts`.
  - `packages/ui/src/map/draw.ts`: the ink (coast, hachure, trees, rivers, roads, tufts). Last changed `b283f411`.
  - `packages/ui/src/map/map.css`: the labels and compass.
  - `packages/ui/src/map/pins.ts`: kind to glyph.
  - `packages/ui/src/map/icons/argonia/`: the glyphs.
  - The one committed still: `lanes/2.4/u-shots/pause-deck__desktop__chart.png` (`5a4b969d`).
- **Palette (`MAP_CHART`):** paper 222,210,172 and paper-dark 196,182,140. Land 204,186,138 and canopy
  170,170,118. Water open 238,234,214 and water wash 198,212,204. Ink 43,46,28 (olive-black), water ink 40,62,60
  (slate) and lane ink 92,46,28 (red-brown). The order is land darkest, unexplored paper between, water lightest.
- **Paper (shade.ts):** paper is mixed toward paper-dark by a smoothstepped coarse grain (x 0.35) plus a fine grain
  (x 0.25). There is no burnt edge and no frame: the UI window framed it.
- **Water (shade.ts):** water mixes from open toward the wash by exp(-shore distance / 5 px). It carries three
  ripples in water ink at 2.4, 5 and 8 px from shore (strengths 0.42, 0.26, 0.14), which read as broken dashes.
- **Coast (draw.ts):** one ink line, `inkCoast` 1.6 css px (x 0.75-1.3 with zoom), alpha 0.92. The **hachure** is
  ticks every 4 css px along the shore into the land: length 4.4 x 0.55-1, width 0.8, ink alpha 0.5.
- **Explored land (shade.ts):** paper mixed 0.72 toward land, the canopy tint at up to 0.45, times hillshade
  0.8-1.06, with contours every 50 m (every 200 m bolder, ink 0.28 / 0.5). **Unexplored is plain paper**, reached
  by a long gradual fade.
- **Trees (draw.ts `drawTrees`):** two-lobed crowns (two arcs) on a short stem, radius 3 css x zoom factor x
  (0.7 + 0.6 canopy), ink 0.66. A dot stipple (ink 0.45) thins into the clearings. Placement is on a jittered 4 px
  grid, gated by a clump field, so woods read as groves.
- **Marsh tufts (draw.ts):** a base stroke and three blades (the centre leaning, two splayed), 7 css px, ink 0.7,
  on a jittered 7 px grid.
- **Rivers:** water ink 0.9, 0.9-4 css px. A river wide enough to be open water is drawn by its banks.
- **Roads (`CHART_ROADS`):** trunk and road are lane ink 0.9 over a paper casing (+2 px, 0.85). Tracks are dashed
  [5,3], footpaths dotted [1.5,3], and boardwalks and causeways a hairline crossed by rungs.
- **Labels (map.css):** Pelagiad (the old `packages/ui/src/assets/Pelagiad.woff`, the same face we pin) in the map
  ink, with a soft paper glow (text-shadow). The top tier is title size, letter-spaced (tracking x 5). Water names
  are in the water ink, spaced.
- **Compass (map.css):** a small inked rose in a hairline ring on a paper disc.
- **Place glyphs:** the chart's default pins were the bone-recoloured **Skyrim** sprite, which we cannot use (0012).
  The old repo also had its own **Argonia** set: a Fal sheet traced to vector paths (`icons/argonia/glyphs.json`).
  We imported that file (provenance in `tools/chart/glyphs-SOURCE.md`, with a sourcing-register row).
- **Our mapping onto the layers:**
  - **base** holds the paper and the water treatment, shown everywhere.
  - **ink** (the sketch) holds the coast and hachure, the major rivers, the major roads with their casing, the land
    border, the compass and the cities.
  - **revealed** holds everything the old chart showed only when explored: the land tint, canopy, hillshade,
    contours, crowns, stipple, tufts, minor rivers and roads, and places.
  - Unexplored land is therefore plain paper, as in the old chart.
- **Scale.** The old weights were in css px at any zoom, while ours is a static image. A master px is half an old
  css px, so the 2048 copy (desktop) shows the old screen weights. The old still is at about 3 css px per pack px.
- **Our data, not the old map's:**
  - **Canopy.** We have no canopy raster, so `data.CANOPY` weights the cover classes: forest floors 1, peat, moss
    and scrub 0.5-0.6, grasses 0.2-0.25.
  - **Labels.** Labels are drawn for magnitude 2 and up (163 places), where there is room. The view names the rest
    from `index.places`.
  - **Border.** The land border on N and W is kept (thinner, in lane ink), because the old map simply faded where
    its data ended.
