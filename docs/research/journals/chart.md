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
