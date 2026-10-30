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

- **1.2 polish (2026-10-30).** Chart labels are placed by priority with offset candidates (`placeLabels`); a harness
  check measures label-box overlap in every chart still. Margins are paper plus inline noise, the chart edge feathered.
  The phone type scale keys on device pixels (css x density, at most 2440 wide), not aspect alone: 21:9 monitors keep the
  desktop scale. Reader round 4 failed (gradient margins and a hard seam; a stray "th" of a covered label); round 5 below.

## 2026-10-30: Pelagiad everywhere, the light retheme and the title (lane 1.2-theme)

The lane report is `docs/research/2026-10-30/lane-1.2-theme.md`; the install steps are `installer/steps/ui-theme.md`.

- **Dear Diary's art is in SWFs, not DDS.** Its menus load `interface/deardiary/**/<menu>_BG.swf` at run time (the
  path strings are in each menu's bytecode). Each BG SWF holds one DefineBitsLossless2 bitmap (format 5, ARGB,
  premultiplied). The copies embedded in the menu SWFs are fully transparent placeholders, so treating them changes
  nothing. The SkyUI config panel's copy is the one real exception. The only DDS is `mainmenuwallpaper.dds` (DXT1,
  2048², no mips). It is Skyrim's map (Falkreath Hold, Helgen, a hold emblem) with "The Elder Scrolls V / SKYRIM"
  painted in, and Dear Diary's `logo.nif` shows it as the main menu. So it is replaced, not recoloured.
- **Nordic marks in Dear Diary:**
  - `map_bonus_BG.swf` carries the horned Dragonborn helmet as a watermark;
  - `craftingmenu_enchanting_BG.swf` carries Skyrim's barbed enchanting sigil.

  Both are cleared. The alchemy flask, the wheel's sunburst and the Oblivion-like loading frame's baroque
  cartouche are not Nordic (reader, round 2).
- **The font library.** Dear Diary's `fonts_fritzq.swf` is the working model:
  - its tags are SetBackgroundColor, DefineFont3 (HasLayout, WideCodes), DefineFontName, ExportAssets under the
    font's name, ShowFrame and End;
  - menus import `$Everywhere*` names from `gfxfontlib.swf`, and `fontconfig.txt` maps them.

  Our writer is pure Python. fontTools reads the TrueType outlines (quadratic, so they map 1:1 to SWF curves), at
  a 20× 1024 em. On the laid dear-diary, skyui, wood-and-paper and oblivion-loading-menu folders, no menu imports
  an unmapped name. JPEXS was not needed. Java is not on the VM.
- **The palette map.**
  - Measured: Dear Diary's paper sits at value 0.65 and saturation 0.12. Its frames sit at hue 18, saturation 0.5
    and value 0.29.
  - The first cut tinted everything above saturation 0.18, which turned the paper's warm stains orange and its
    burnt edges into green mould.
  - Final thresholds: dark frames tint to moss from saturation 0.38; bright leather tints to rust from 0.5.
  - The bright loading parchment is held at `--paper`.
- **Not done:** the in-game proof (L4, `tests/journeys/ui-sweep.yaml`). Scaleform may reject a detail of the
  writer's DefineFont3 that the decoder accepts, so the first in-game still is the oracle.

## 2026-10-30, ui-live: binding our views to PrismaUI

- **The archive carries a DLL.** PrismaUI 1.5.1 ships `SKSE/plugins/PrismaUI.dll` and `PrismaUI/libs` (Ultralight).
  The dependency row had said "data only (no DLL)"; it is corrected.
- **The API is the published header at tag 1.5.1** (`src/PrismaUI_API.h`). The plugin calls
  `GetProcAddress(PrismaUI.dll, "RequestPluginAPI")` with V1 or V2. V2 adds `RegisterConsoleCallback`, which we use to
  log page errors to the SKSE log. We call it through our own declaration of the interface (`prisma_api.h`); the
  virtual order is the ABI.
- **Paths.** `CreateView("argonia/dialogue/index.html")` loads `file:///views/<path>` under the PrismaUI base folder
  (`ViewManager.cpp:36`). So the bundle lays at `Data/PrismaUI/views/argonia/`, and the pages' relative links
  (`../core/theme.css`, `../fonts`) hold.
- **Calls in and out.**
  - In: `InteropCall` looks the function up as a property of the global object (`Communication.cpp:333`), so a dotted
    `argonia.push` would not resolve. `window.argoniaPush` is the top-level alias.
  - Out: `RegisterJSListener(view, "argoniaIntent", cb)` puts the function on `window`. Its callback carries no view
    id, which suits us: `ViewIntent` routes by the intent's type. The callback runs on Ultralight's thread, so the
    intent goes to the main thread as an SKSE task.
- **The pad.** Ultralight has no Gamepad API. PrismaUI dispatches `gamepadbuttondown` on `window.prismaUi.controls`,
  with the W3C button index. `nav.ts` maps those to the same actions; the sticks are not forwarded.
- **The journal key.** Our control map binds the "Journal" user event to J and the pad's Back. Escape opens the same
  Journal Menu (its System tab), so the router replaces it only within 1 s of a Journal press (the latch).
- **MSVC found a dangling view.** `Host::open` closed the previous modal through a `string_view` of the very
  `optional<string>` that `close` resets. GCC passed it; MSVC's ctest failed it. It now passes a copy.
