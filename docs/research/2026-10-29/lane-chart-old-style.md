# Lane chart-old-style: the parchment chart follows the old project's map

**Outcome: done.** The owner asked whether the hand-drawn map was the old repo's (it was not) and ruled that it
follow the old one. The map he liked is the old map window's **"Chart" treatment** (the old 2.5x report records him
calling it "gorgeous"). `tools/chart` now draws that style over our own data. The journal
(`docs/research/journals/chart.md`, 2026-10-29 old-style entry) lists each element with its source path at old
commit `b581910f`.

## Finding the old map

- **Access.** I read the old repo through `gh api` tree and contents calls. An early `--depth 50` clone into the
  scratchpad hit 2.4 GB RSS; it was deleted and not used. The files read:
  - `packages/ui/src/tokens/map.ts` (`MAP_CHART`, `MAP_SIZE`);
  - `packages/ui/src/map/shade.ts`, `draw.ts`, `map.css` and `pins.ts`;
  - `packages/ui/src/map/icons/argonia/` (SOURCE.md, glyphs.json, sheet.png, trace.py);
  - the lane reports `lanes/2.5x/map-report.md` and `lanes/2.15x-map/report.md`;
  - the stills `lanes/2.4/u-shots/pause-deck__desktop__chart.png` and the faithful-style shots.
- **What he liked:**
  - bone paper, with the water the lightest ground: a pale blue-grey shore wash and three broken ripples;
  - one olive-black ink for the coast and its land-side hachure, the tree crowns and stipple, and the tufts;
  - slate river ink, and red-brown roads over a paper casing (tracks dashed, paths dotted);
  - explored land in a warm tint with soft relief, and unexplored land as plain paper;
  - Pelagiad labels on a paper glow, with letter-spaced top-tier names;
  - a hairline compass rose.

## What changed (tools/chart)

- **render.py, reworked.**
  - **Palette and weights.** The old tokens are used, and the ink weights are set so the 2048 copy shows the old
    screen weights.
  - **Base.** Paper mottled toward paper-dark, and the sea's wash plus three broken ripples.
  - **Ink, the sketch.** Hachure, coast, major rivers, major roads with casing, land border, compass, and cities.
  - **Revealed.** Land tint and canopy tint, hillshade, 50 m contours, crowns and stipple, tufts, minor rivers,
    tracks, paths and boardwalks, and places.
  - **Dropped.** The burnt edge, the frame and the double-line roads.
- **Glyphs imported** (our own Fal-made UI art): `tools/chart/glyphs.json`, byte-identical to the old
  `icons/argonia/glyphs.json`, sha256 `b15c6042…`. Provenance is in `tools/chart/glyphs-SOURCE.md`, with one
  `data/sourcing-register.json` row. The kind-to-glyph table comes from the old pins.ts, and cities use pin-city.
  The old chart's default pins were the Skyrim sprite, which is not used (0012).
- **data.py.** Roads carry their class. `CANOPY` weights the cover classes into a wood density, because we have no
  canopy raster.
- **Labels.** Labels are drawn for magnitude 2 and up where there is room; the view names the rest from
  `index.places`.
- **__main__.py.** The demo reveal matches "Claywater Station", the db name, with the old chart's wider fade.
  Before this, explored-demo was silently skipped.

## Checks

- **L1 (4096, `checks.json`):** all green.
  - cities 7/7 at the db pixel, on land and inked (mirrored: 1 in the sea);
  - rivers 20/20 (min 1.0);
  - roads 8/8 (min 1.0);
  - no player key.
- **Determinism:** `python -m tools.chart twice` made two processes, both with render `3ceaf0ea3c6cf745`
  (identical).
- **Memory and time:** peak RSS 1,304,124 KB (`/usr/bin/time -v`, 4096 render, ≤ 1.5 GB) in 45-61 s.
- **Gate part:** the sample hash was re-pinned on purpose to `df224843…` (sample-manifest.json). The sample gained
  a wood and a footpath. `tools/chart/tests` 5 passed (1.1 s), and ruff is clean.
- **`make check`: RED, but not from this lane.** Three reds, all in another lane's uncommitted water work:
  - guard: no-assets refuses `world/db/water_regrade.jsonl` (1.39 MB);
  - unit: `water/tests/test_water.py::test_steep_reach_keeps_steps_at_least_step_min_long`;
  - plugin-check: db LoadError, unknown column `floor_m` in water_regrade.jsonl.

  Nothing in tools/chart reaches them. The chart tests and the unit-facts test pass on their own.

## L3 (reader, round 1 of at most 3): PASS

- **Stills** (`out/chart/stills/`):
  - `r1-desktop-old-vs-new.png` and `r1-desktop-old-vs-new-sw.png`: the old still vs the new full-2048, at the same
    px size;
  - `r1-detail-old-vs-new.png` and `r1-detail2-old-vs-new.png`: the same at x3;
  - `r1-sketch-and-explored-1024.png`.
- **Verdict by element:**
  - **MATCH:** coastline, hachure, marsh tufts, rivers, labels, compass.
  - **CLOSE:**
    - paper: the mottle is coarser than the old;
    - water: the open sea reads near-white;
    - land: the western uplands add contours and darker shading;
    - trees: denser and more uniform;
    - roads: the casing is hard to see;
    - glyphs: the city pyramid is a little heavy.
  - **Overall:** "Someone who liked OLD would recognise the same family." No Nordic or Skyrim element.
- **Polish the reader suggested (not done; P2 rolling):**
  1. a cooler sea, and ripples further out;
  2. softer upland contours and shading (the old code has 50 m contours; the old still's ground was flat);
  3. a finer paper mottle, with grain on the sea;
  4. a more visible road casing;
  5. a crisper explored edge in the demo;
  6. fewer labels at full-1024;
  7. larger, more irregular crowns.
