# Lane 1.2-views: the four screens as web views at L3 (report)

Dated 2026-10-30. Chunk 1.2 §b–e, the build-VM side. Test level L3. Route: our own HTML views over `ui/schema`,
which the PrismaUI working assumption allows (1.2 §0 has not chosen yet).

## Hand-off (the context marker was reached)

**Done and committed.** Commits 858b0f1, 9b44b6c, 96637d1 and 1d94b88:
- the dialogue window, journal, HUD and chart in `ui/views/`, render-only over the schema;
- the L1 tests;
- the L3 harness;
- `ui/DESIGN.md` and the pins;
- the chart fixture, made from the index;
- the gate smoke.

**Reader verdict so far.**

| Round | Dialogue | Journal | HUD | Chart |
|---|---|---|---|---|
| 1 | FAIL (phone scale) | PASS | FAIL (bars small, breath and grip unlabelled) | FAIL (framing, labels) |
| 2 (after the fixes) | PASS | PASS | PASS (polish) | FAIL |
| 3 (chart only) | | | | FAIL |

Round 3's one blocker: on `chart/unexplored@v5-folded`, the Blackrose plate covers Lilmoth, so it reads "lmoth". Its
polish findings:
- the revealed area reads as a brown smudge, with little detail at this scale;
- the sides beyond the square province are flat cream, so the sheet does not read as one paper;
- city glyphs are tiny at zoom 1 on the phone.

**Left, in order.**
1. Chart label collisions. In `ui/views/chart/main.ts`, `draw()`: after placing the labels, nudge a label that
   overlaps an earlier one vertically, or shrink its cover plate to its text.
2. The chart's margins. Tile the paper treatment (`.paper` mottle) behind the canvas instead of the flat `#eeead6`,
   or use the margin on wide screens for a places list.
3. Reader round 4, on the chart stills only.
4. Polish, for 2.2: the revealed layer's look at zoom 4 belongs to the 2.W4 renderer. The river through the
   "Cartwright's Cross" label is also the renderer's.
5. From the code review, not fixed:
   - a 21:9 desktop monitor gets the phone's type scale (`scale.ts`, aspect ≥ 2);
   - the root font size is duplicated in `theme.css` as the pre-script fallback.

**Reds in `make check`.** Run once, 95 s, peak 0.93 GB. It was CHECK RED with two parts, `plugin-check` and `unit`.
Neither is this lane's:
- `plugin-check`: "cells over the plane budget 32 … 141" and "the world db's water design rows differ from the plan
  in ['water_basin']". These come from the uncommitted world and water work in `tools/argonia_world/water/*` and
  `world/db/*` (writing-3's paths).
- This lane's parts are green: `make ui` (16 TS tests) and `pytest tools/ui_harness tools/chart` (7 passed).

## What exists

| Piece | Where |
|---|---|
| Views | `ui/views/{dialogue,journal,hud,chart}/{render.ts,main.ts,<view>.css}`. `render` is a pure state-to-HTML function; `main` is the DOM glue. |
| Core | `ui/views/core/bridge.ts`: `window.argonia.push` in; `window.argoniaIntent` out, after `encodeIntent`. |
| | `ui/views/core/nav.ts`: keyboard, pad and touch, with spatial focus. |
| | `ui/views/core/scale.ts`: 1rem set from the viewport. |
| | `ui/views/core/html.ts`; `ui/views/core/theme.css`. |
| Tokens | `ui/DESIGN.md` |
| Build | `tools/ui_harness/build.py`: esbuild to `out/ui/views/`. Pelagiad is copied from `$ARGONIA_PRIVATE`; the chart layers and a compact index come from `out/chart`. |
| L3 harness | `tools/ui_harness/harness.py`: `make ui-stills` runs everything (112 stills); `--smoke` runs the gate subset. |
| Chart fixture | `tools/ui_harness/chart_fixture.py`. The gate test fails if `ui/fixtures/chart.json` drifts from `out/chart/index.json` (the planner's request). |
| Pins | `infra/build-vm/toolchain.lock`: `py:playwright=1.55.0`, `chromium-headless-shell=140.0.7339.16`, `npm:esbuild=0.25.10` (binary sha256). |
| Journal | `docs/research/journals/ui.md` |

## Acceptance, measured

- **All four views render at the four viewports from every fixture.** 112 stills, 0 harness fails, 67–128 s:
  - the viewports are 1920×1080, 1280×720, V5 folded 2376×1060 and unfolded 2352×2172, at 1:1, because 0.2 §d
    records no stream scale;
  - each still is checked for Pelagiad loaded, text off screen, clipped button text, page scroll and refused pushes;
  - the smallest text on the folded V5 is 40.8 px, which is 2.56 mm at 404 ppi (bar 2.5 mm).
- **The reader.** Rounds 1–3 are in the hand-off table. Dialogue, journal and HUD pass. The chart fails on one label
  collision.
- **The L1 tests pass.** `ui/views/tests/views.test.ts` has 8 tests in `make ui`:
  - every push renders through its view, and every schema push has a view;
  - each view shows what the push carried;
  - every intent a view can send passes `encodeIntent`, and every fixture intent is one a view produces;
  - 300 topics give 300 buttons with unique intents;
  - bars grow with their maximum, text is escaped, there is no Nordic word, and the type-scale arithmetic holds;
  - the chart geometry, edge stop and lettering are tested.
  - Proven able to fail: with a broken page turn, it names `nextPage … is never sent`.
- **The 300-topic layout holds at all four viewports.** The checks:
  - the list scrolls inside its column;
  - the rows are in order, each at least a line tall;
  - the window and Goodbye stay on screen;
  - the conversation keeps at least 45% of the width;
  - the last topic can be scrolled to.
  - Visible rows: 11 (1080p), 11 (720p), 12 (folded), 19 (unfolded).
- **The wiring, in the browser on the folded V5.**
  - Dialogue: a click on a topic, a keyword, Persuasion → Admire, Goodbye, and Escape send exactly the fixture
    intents. A forced conversation ignores Escape. Pad down, down, accept sends the third topic.
  - Journal: Next, PageDown, Escape and a quest pick send what the fixtures say.
  - Chart: + sends `chart.pan` at zoom × 1.5, then `view.close`.
- **The gate stays within budget.** The smoke runs in pytest in 5–6 s: 5 stills, the wiring and the 300 topics.
- **Memory.** The harness's Python peaked at 135–150 MB. The headless shell reached about 2.2 GB RSS summed with four
  pages open; the harness now closes each viewport's page when that viewport is done.

## Polish

- **Label collisions.** `placeLabels` (`ui/views/chart/geom.ts`): labels are placed by priority (cities first, larger plate
  first); each tries its own spot, then 8 offsets above, below and diagonal, and is dropped if none is free. A displaced
  plate leaves a paper patch over the chart's own small lettering (`.label.moved::before`). Checks: a unit test in
  `views.test.ts`, and the harness measures every shown label's box in every chart still (`labelOverlaps`). Made to fail
  once: with the pass off, `chart/unexplored@v5-folded` failed with "Lilmoth / Blackrose"; on, 0 fails in 112 stills.
- **Margins.** The sheet carries `.paper` plus an inline fibre-noise mottle (no texture file); the canvas no longer fills
  flat cream, and the chart's straight edges are feathered into the paper.
- **Type scale.** `scale.ts` `isPhoneLandscape`: aspect 2:1 or wider and at most 2440 device px wide (css px x density).
  2560x1080, 3440x1440 and a 2560x1080 css retina keep the desktop scale; the fold keeps the phone's. The duplicated
  root font size and its media query are removed from `theme.css`.
- **Gate.** `make ui` and `pytest tools/ui_harness tools/chart` green. `make check` reds, none from this lane: `lint`
  (unused `budget` import in `tools/argonia_world/water/__main__.py`), `skse` (`skse/core/generated` stale against
  uncommitted db rows, 2 new forms), `unit` (`test_job_guard::test_locks_are_per_machine`, gpu lock busy from another lane).
- **Reader, chart stills.** Rounds 4 to 6 (two fix iterations, the cap): round 4 failed (gradient margins, a "th" fragment),
  round 5 failed (ghost Lilmoth, tile seams), round 6 failed on the 1080p, 720p and folded unexplored stills: faint ghost
  Lilmoth under the displaced label (patch then made opaque, not re-judged), margin noise seams, a value step at the
  map edge. The claywater stills and v5-unfolded labels pass. Left for the next pass: re-judge the opaque patch; make
  the margins from the base layer's own paper (not CSS noise) so no step shows.
