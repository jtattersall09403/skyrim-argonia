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
