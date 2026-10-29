# Lane 2.W4-chart: the parchment chart (2.W4 §c, for 1.2 §e)

Outcome: done. `tools/chart/` renders the chart deterministically from our own data: the world db through
`db.open()`, and the heightfield and land cover through `grid.Sources`. It uses no game asset and no Fal. The
journal is `docs/research/journals/chart.md`.

## What it makes (out/chart/, gitignored)

- **Layers**, 4096^2 master, with 2048 and 1024 copies (and a 512 copy of the sketch). The view stacks them in
  this order:
  - `base` (RGB): paper, burn and sea wash;
  - `revealed` (RGBA): NW hillshade, 20 m contours (every 100 m bolder), forest, marsh and rock washes, minor rivers
    and tracks, and the other 560 places with glyphs by class and labels where there is room;
  - `ink` (RGBA): the sketch.

  `sketch` (base + ink) and `full` (all three) come flattened. `explored-demo-2048.png` reveals only the cells
  round Claywater (1.2 §e's walk).
- **The sketch shows:**
  - the coast as a doubled wobbling ink iso-line, with four water lines offshore;
  - the land border on N and W as a red-brown dash with an ochre band;
  - a frame;
  - marsh tufts;
  - the 20 major rivers (Strahler >= 2), teal and tapering to the mouth;
  - the 8 major roads (trunk or road), a sepia double line;
  - the seven cities, each a rough ring round three domed stilt-houses, labelled in Pelagiad.

  There is no player marker (C9).
- **Revealed format.** I chose a full-resolution layer that the view masks per discovered cell. It is cheapest for
  either PrismaUI (a CSS mask from a 126^2 bitmap) or Scaleform (one masked bitmap), and it costs no per-cell assets.
  For neutrality the layer is also cut into 256 px tiles, `tiles/revealed/{tx}-{ty}.png`: 206 non-empty of 256.
  Cells and tiles share the 32 px lattice, so each cell lies in exactly one tile.
- **The index** is `index.json`: size, margin, px_per_m, tile, layer order, `cells` ("cx,cy" -> [tx, ty, x, y, w,
  h]) and `places` (id -> name, px, cell, kind, city, label box). `hashes.json` holds per-layer and render sha256 of
  the raw pixels. `checks.json` holds the L1 results.

## Checks

- **L1 (`checks.json`, the 4096 render):**
  - **Cities:** all 7 cities are at their db pixel (|d| < 0.01 px), on land at their terrain sample, and inked.
    The mirror test discriminates: mirrored north-south, 1 city (Thorn) lands in the sea.
  - **Rivers:** 20 of 20 major rivers have ink within 8 px along at least 95% of their length (minimum 0.998).
  - **Roads:** 8 of 8 major roads, at least 90% (minimum 1.000).
  - No player key.
- **Determinism:** `python -m tools.chart twice` ran two 4096 renders in separate processes. Both gave render
  `fbf205a3548199c5…`, identical (2:51 wall time).
- **Gate:** `tools/chart/tests/test_chart.py` has 5 tests on a synthetic 512^2 sample. Its hash
  `945a89f1…` is pinned in `tools/chart/sample-manifest.json`, and the tests cover two renders identical, city
  position, no flip, cell-in-one-tile and the layer shapes (5 passed, 6 s, 95 MB). The tests skip with a reason if
  Pillow or the font is missing.
- **L3, `reader`:**
  - **Round 1: FAIL.** Rivers and roads were thin and alike at phone 1024, the border was faint, the tufts were
    sparse, and the lines looked GIS-like.
  - **Fixes:** heavier, tapering teal rivers; a darker, thicker double-line road; a heavy border dash with an ochre
    band; denser tufts; cities about 20% larger.
  - **Round 2: PASS.** Items 1-10 all pass, including Nordic tells: none. In the reader's words: "This now reads as
    a rough explorer's chart of a swamp province, and the parchment theme fits."
  - **Polish left (P2 rolling):** clip roads at the city rings, keep tufts clear of the glyphs and labels, more
    road weight at 512, vary the dense south-west tufts.
  - **Stills:** `out/chart/stills/r{1,2}-sketch-{desktop-2048,phone-1024,phone-512,detail-*}.png`.
- **Memory:** the 4096 render peaked at 976 MB RSS (`/usr/bin/time -v`) in 87-101 s. The 2048 render peaked at
  472 MB. The first unbanded version would have been about 2.2 GB, so the fields, noise and compositing run in
  512-row bands.

## Decisions and side effects

- **Orientation measured:** col = x/S and row = y_south/S, with no flip. `meta.json`'s "row 0 is the southernmost"
  contradicts grid.py and the measurement, so 2.W1 should correct it.
- **Pillow:** pinned as `py:pillow=13.0.0` in `infra/build-vm/toolchain.lock`, a one-line addition outside the
  lane's listed paths. The brief's prior art named that pin, and the venv had neither Pillow nor cairo.
- **Pelagiad:** OFL, from isaskar/Pelagiad @ f9813019, sha256 `b282ea04…`. `python -m tools.chart fetch-font`
  puts it in `$ARGONIA_PRIVATE/fonts/pelagiad/` with its LICENSE.txt. It is not committed, and it has one row in
  `data/sourcing-register.json`.
- **Makefile:** `make chart` renders and runs L1. It is not in the gate.
- **Unit-facts gate:** the pixel size is `MASTER = 1 << 12`, so it does not trip
  `test_unit_facts_live_only_in_the_units_module`.
- **For 1.2 §e:** the view masks `revealed` per cell from `index.cells`. Discovered places are baked into
  `revealed`, so revealing a cell shows its places. `index.places` gives each place's pixel and label box if the
  view wants per-place reveal instead.
