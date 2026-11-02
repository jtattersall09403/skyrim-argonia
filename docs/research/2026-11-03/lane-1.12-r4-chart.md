# Lane 1.12-r4-chart (round 4): play test 3 #26, #14, #12, #30

## Causes
- #26, the map pane over the dialogue: `ChartPaneWanted` (skse/ArgoniaCore/src/views.cpp ~79) checked only WindUIMenu and the trade menus. During Barter from a conversation, Wind UI closes the BarterMenu within 0.3 s and draws its barter window in WindUIMenu, so the docked pane counted as wanted. It was read again only on WindUIMenu events. Nothing hid it when a modal view opened (skse/core/src/views.cpp Host::open).
- #14, the zoom: the city names and glyphs were baked into the tiles (tools/chart/render.py `sketch`, the ring labels), so they grew with the zoom. The view's cover plates (geom.ts labelAt, `cover`) were sized as label rect × scale and switched on and off at a threshold.
- #12, the sketch: main.ts drew only the `full` layer, through the reveal mask, so the unexplored land was blank parchment. The `sketch` tiles were never drawn. City names were also hidden under the fog (seenAt).
- #30, the rivers: the out/chart render was dated 10-29, older than the current terrain and DB. The river lines are the hydrology reach polylines, and 3% of their points lay more than one cell from any cell_water cell.

## Changes (commits b191862, 03e3e15, e8fa73e, 071b6a8, rebased on origin/main)
- core `pane_wanted(windui, trade, dialogue_menu, modal)`. Host::open hides docked views before it shows a modal. The adapter reads DialogueMenu and our modal, and is read again on DialogueMenu, Barter and Container events and after a modal closes.
- The renderer's ink is now the coast and its hachure, the major roads, the border and the compass. The rivers moved to the revealed layer. The cities' art is in a separate `cities` layer, flattened only into map-<size>.png, which fwmf.py now reads.
- data.py cuts each river to its runs within one cell of the cell_water rows. checks `rivers_on_water`. `render --if-stale` works on a source stamp of the ESM sha, the ground, world.sqlite and the code.
- The view draws the sketch tiles everywhere and the full tiles through the mask. Undiscovered major cities are DOM dots, and every name is lettered in screen space at 1rem.

## Evidence
- L2: skse ctest 36/36, including pane_never_over_dialogue. tools/chart pytest 9 passed, sample re-pinned to 6db1f974. make check-reach green (10 files).
- L1, the real render at 4096: L1 ok, rivers_on_water 11468/11468 points, rivers 25 major at minimum coverage 1.0, roads 8 at 1.0. Rendered in the worktree, out/chart and out/chart4k with `--level`.
- L3: harness chart_zoom over the zooms 1→8→1 at four viewports. Maximum drift 0.008–0.015 px over 9 marks. No mark or label changed size. No before number was measured.
- A reader on the zoom1 and zoom8 stills: outline, roads and all seven cities show as named dots; the unexplored land is a sketch; sizes look constant.
  Polish open (P2): the Lilmoth and Blackrose labels read swapped at 1080p and 720p; Thorn is clipped at the top on v5-folded; Claywater Station collides with roads; roads are doubled near Gideon (data); the coast is clipped at 720p.
- Full harness: 16 fails, all HUD smallest-text, in files this lane did not touch.

## Owed
- journey tests/journeys/chart-zoom.yaml and 4 owed rows in docs/phases/1-core-loop/checks.md.
- The deploy needs the chart re-rendered on the build machine: `python -m tools.chart render`, plus `--level --size 4096 --out out/chart4k` and the 8k render if used. The main tree's out/chart is still the 10-29 render.
