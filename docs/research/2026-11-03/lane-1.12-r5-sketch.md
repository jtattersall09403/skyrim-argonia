# Lane 1.12-r5-sketch (owner 2026-11-03 #37: the sketch always visible)

## Measured before
Harness stills at zoom 1, 1080p and v5-folded, nothing revealed (fixture `unexplored`) and ten revealed cells (`whole` state, first 10), read by a reader: all seven cities named and legible, coast with hachure, red-brown roads, dashed border, compass (faint, tiny), no veil, fog, vignette or plate over any land; the ten-cell patch shows faint extra detail round the player only. Verdict yes on all four. So main.ts already drew the sketch tiles everywhere (r4-chart a2d8b8ce); the owner read the hand-over words, not the screen. Nothing was wrong in the view.
Polish seen (P2): compass faint; Thorn tight to the top edge; the detail in the ten-cell disc is subtle; land fills a middle column.
Note: a pushed state needs a player (schema), so "no player marker" stills carry the arrow at home.

## Changed
- ui/views/chart/geom.ts `compositePlan`: sketch whole and unmasked first; `full` only when cells are revealed and only through the mask. main.ts draw() executes that plan (same pixels: before/after stills byte-identical).
- ui/views/tests/views.test.ts: pins the order (mask on `full` only; cities are DOM over both). node tests 16/16.
- infra/gpu-box/deploy.sh: before the views step, `tools.chart render --if-stale` and the 4k `--level` one, so a deploy never ships a render older than its source (stamp check 0.25 s when current).

## Round-4 deploy
Carried the sketch. Main tree out/ui/views/chart: main.js, chart.css and the sketch and full tiles were built 06:00:37-40 from the 05:59/06:00 renders (sketch-*.png present, main.js draws "sketch"), before the 06:06 deploy commit 9eb4dbd. Not provable from a deploy log (none kept). The stamp now differs from the 05:59 one (ESM/db changed since): out/chart and out/chart4k were re-rendered, same render hash 1fcc68cd for the master.

## Owed
checks.md row added (L4). Journey chart-zoom.yaml step chart-zoomed-out already covers it.
