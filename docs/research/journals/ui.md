# Journal: our own screens (chunk 1.2)

This journal records what was tried, measured and learned for `ui/views/` and `tools/ui_harness/`, so nothing is lost
at a hand-off. The lane report is `docs/research/2026-10-30/lane-1.2-views.md`.

## 2026-10-30: the four views as web views, and the L3 harness (lane 1.2-views)

- **The shape.** Each view has a pure `render(state) -> HTML string` and a thin `main.ts`.
  - `main.ts` sets `innerHTML` once per push and delegates clicks.
  - Every control is a `<button>` that carries its intent as `data-intent` (JSON). `core/bridge.ts` validates the
    intent with the schema's `encodeIntent` before it leaves.
  - Because rendering is pure, the L1 tests run in Node with `--experimental-strip-types` and no DOM.
  - View-local state is presentational only: the open persuasion panel, the focused control, a chart drag in
    progress. Game state stays out.
- **The host seam (PrismaUI's, assumed).**
  - In: ArgoniaCore calls `window.argonia.push(text)` (Invoke).
  - Out: the view calls `window.argoniaIntent(text)`, the JS listener the SKSE side registers.
  - Pad input: `window.argonia.input(action)` serves a web view without the Gamepad API. Where the web view has the
    Gamepad API, the views read it once per animation frame while a pad is connected.
  - What the web view must support is listed in `ui/DESIGN.md`. 1.2 §0's probe should confirm Ultralight handles
    CSS columns, `min()` and canvas `source-in`.
- **Escape is `view.close` for the dialogue too.** The schema says close comes from "Escape, the pad's B, the close
  button", and the dialogue fixture carries a `view.close`. Goodbye is the button. A forced conversation (no Goodbye)
  ignores Escape.
- **Type scale.** 1rem is `min(H/34, W/52)`, and `H/26` at an aspect of 2:1 or wider (a phone held landscape). No text
  is set below 1rem.
  - Round 1 had 31.2 px on the fold closed, 1.96 mm at 404 ppi. The reader failed it: about 1.4 mm cap height, and the
    phone showed the desktop layout shrunk.
  - With the phone rule: 40.8 px, 2.56 mm.
  - The 10-foot guidance is at least 28 px at 1080p. Our 1080p rem is 31.8 px.
  - The 0.2 §d stream scale is not in `infra/README.md`, so the views are judged at 1:1.
- **The Magic V5's screens.**
  - Cover: 6.43", 2376×1060, 404 ppi.
  - Inner: 7.95", 2352×2172 (some sources give 2353×2172 or 2344×2156), 403 ppi.
  - Sources: the Neowin review, gsmfind, mobiledokan.
- **The chart.**
  - The view stacks `base`, `revealed` (masked) and `ink` from `out/chart/*-2048.png`.
  - The mask has one pixel per cell from `index.json`'s rects, smoothed up in two steps (×4, then to 2048) for a
    soft edge about a cell wide, then drawn with `source-in` over the revealed layer.
  - The transform keeps the paper filling the sheet. A centre near the west edge, such as Claywater, stops at the
    edge instead of showing blank.
  - The cell map is linear (`px = x0 + 32u`, `py = y0 + 32 - 32v` from cell 0,0). Cell y grows north.
- **The chart fixture was wrong.** 1.1's mock put Claywater at cell (−0.5, 0.25). The index has it at (−57, 11).
  - `tools/ui_harness/chart_fixture.py` now makes the place ids and positions, the 13×13 walk and the views from the
    index.
  - The gate's test fails if the fixture drifts from the index (owner of the fixtures: this lane, since 1.1 closed).
- **The harness.**
  - Tools: Playwright 1.55.0 (py) and its headless shell 140.0.7339.16 (build v1187). The system libraries were
    already present; no Wine.
  - The build uses esbuild 0.25.10 from `~/.argonia/npm`.
  - One browser, and one page per viewport. A page is closed when its viewport is done. Plain pushes reuse the
    loaded page.
  - Fonts: `document.fonts.ready` is awaited after the push. Pelagiad loads lazily, so checking before the first text
    reported it missing.
  - **Time:** the full run took 177 s with a reload per still, and 98–159 s with reuse.
  - **Memory:** the Python peak was 135–150 MB. While all four pages were open, the headless shell's processes
    summed to about 2.2 GB RSS, about 840 MB of it in the chart page's renderer (its three 2048² canvases). Closing
    each viewport's page bounds this.
  - The smoke subset takes 6 s in pytest.
