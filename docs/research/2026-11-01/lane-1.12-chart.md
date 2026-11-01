# Lane 1.12-chart (owner look 1)

Batch: out/batch/adhoc/20261101T132518 (argonia-play-ie, deploy of 98d7917); chart-look 8/8 and chart-minimap 14/14 passed their state checks. The view logged `chart: reveal ok` (its own pixel check of the mask and of canvas destination-in). One reader read the stills with each row's claim and the feel question.

| Row | Verdict | Root cause in 1.12 | Fix |
|---|---|---|---|
| Marker | proven | it was our red ink arrow in a ring, 1.7rem | ui/views/core/player-marker.svg, a gilt arrowhead (our drawing), 0.75rem; the HUD imports it |
| Camera after the map | proven | M opened the engine's MapMenu, which moved the camera to the world map; we hid it under the chart, and closing it brought back the first-person hands | views.cpp: the map key's user event is swallowed in the world and our chart opens directly, so MapMenu never opens |
| Map pane | proven (reader: the pane is small) | Wind UI has no hook for our map in a window; nothing docked it | new non-modal `chartpane` view (chart/pane.html), shown while WindUIMenu is open, but not with trade, container or crafting windows open |
| Look | RED | the reveal was invisible, so only the sketch showed | reveal and sharpness fixed. Reader still fails it: blank paper margins at full zoom, heavy plate labels, a weak province outline |
| Reveal | RED (partial) | the native side marks only the cell you stand in (1–3 cells, 7 px at full zoom). The journey read the native log line `revealed (cell change)`, never the pixels | a soft disc of REVEAL=4 cells round each walked cell, plus an in-view pixel check. Reader: the patch shows, but the sketch (coast, rivers, cities) is still drawn everywhere. That follows the 2.W4 layer design. Hiding the sketch would need a ruling from the owner |
| Sharp + smooth | sharp yes, smooth RED | the view stretched one 2048 px image up to zoom 24 (11x), and each key press jumped | a tile pyramid up to 8192 (out/chart8k, `python -m tools.chart render --size 8192 --out out/chart8k`, 6m41s, 3.4 GB), ZOOM_MAX 8, a glide toward a target each frame. The burst frames show no motion, and a PowerShell window covered two of them: the burst missed the pad input. Owed: a re-run with the pad input landing inside the burst |

Not in scope / for others: the minimap row is lane 1.12-hud's (the marker is ready). out/chart8k is copied to the main tree's out/ so the main tree's builds take the 8192 level.

## Round 2 (planner's three rows), batch out/batch/adhoc/20261101T143408, e37e84f; make check GREEN
- **Reveal: proven.** Every layer, including the coast, rivers, cities and their names, now shows only through the seen-land mask, so unexplored land is blank parchment. The reader passed it. The minimap still draws the whole sketch: lane 1.12-hud's `ui/views/hud/minimap.ts` must clip its layers by `revealDiscs` (`ui/views/chart/geom.ts`) the same way.
- **Look: RED.**
  - Done: hand-lettered italic labels on a soft glow with no plates; a bolder province border (`render.py`: 5u dash, wider band), re-rendered at 8192. Under fog the blank margins now read as parchment.
  - The reader says only a small patch shows, so the border, labels and coast are not in view. It also says the flat ink strokes clash with the soft relief, and the pane strip is mostly empty.
  - Next: a scene that has walked farther, or a larger reveal radius, so the treatment fills the view; centre the disc on the player; a taller pane.
- **Smooth: RED.**
  - The d-pad pans now, because PrismaUI does not pass the right stick. The view logs `chart: input`, and the journey expected both `chart: input right` and `chart: glide`.
  - The 4 fps burst shows the pan in jumps of 28–125 px with no frame mid-glide, and no zoom change. A 90 ms glide finishes between two frames 250 ms apart, so this capture cannot show it. The zoom presses may also not have landed.
  - Next: capture at 15 fps or more (the burst tool flashes a PowerShell window; that is infra's), and log the glide line into the report.

## Round 3 (fixes ready for the planner's look-1 round; no in-game run of my own)
Two batches started (chart112r3, r3c-e). r3 failed at `walk` because I had cut it to one 3 s push (now restored to three). The others queued, lost the machine or hit an ssh timeout. Under the owner's new method, the planner runs chart-look in look-1.yaml. Both rows stay **owed** until that run's stills and clip are read.
- **Look, root cause of the ink clash.** The pyramid downsampled one 8192 render whose strokes scale with size. At zoom 8 every line drew 4x its desktop weight, while the old chart's canvas strokes kept about 1.6 css px. Fix: `render.Renderer(ink=)` and `chart_level_ink(size) = (2048/size)^0.75` on every stroke width (coast, hachure, rivers, roads and casing, border, contours, tracks), set with `--level`. out/chart4k (`render --level --size 4096`) and out/chart8k (`--level --size 8192`) are cut per level (pyramid.tiles takes per-side sources; build.py takes only each close dir's top render). With the default ink=1 the sample hash is unchanged. Off-game crop: lines about 2 px at 4096, like the old still (lanes/2.4/u-shots/pause-deck__desktop__chart.png @5a4b969d, fetched to $ARGONIA_PRIVATE/work/oldchart/old-chart.png for the side-by-side). Both level renders are copied to the main tree's out/.
- **Look, the walked state.** chart-look now has a `route` step: 33 `cow ARG_Province` travels (Claywater, Gideon, south, west, the south-west coast at -57,-13, the west border, the middle). Each arrival is recorded by the game's own cell event, and the step expects the last cell's `cell -48,2 revealed (cell change)`. The journey has `relaunch_before: true`.
- **Opening view.** With no remembered view (the native default {1,1,1}), the chart opens centred on the player at zoom 3, where the old chart opened on your land.
- **Disc centring.** The mask adds a disc at the player's exact position. Before, the disc sat at the cell's centre, which gave the offset of about 27 px.
- **Pane.** Now 63.6-91.6vh (was 64.4-90.8vh) with a slimmer title bar. Taller needs Wind UI's magic window shorter, which is lane 1.12-menus' layout.
- **Smooth.** The burst is now 60 frames at 15 fps (the planner's clip burst, 291197f) for the pan and for the zoom. Zoom presses log `chart: input zoomIn/zoomOut`, and the journey expects both.
- **Right stick (route 6).** padcursor.cpp's input sink forwards right-stick events, while our chart is the modal, by a task to views.cpp `ChartStick`. That logs `chart: the pad's right stick forwarded to the chart` and invokes `window.argoniaStick(x, y)`. The view pans by the stick's lean at 0.9 sheet heights a second (dead zone 0.2) and glides after it. The journey expects both log lines. Unproven in game.
