# Lane 1.12-r5-chart-zoom (round 5 batch 20261103T111231, step 02-chart-zoom)

## Measured (why the game showed a crop and a no-op zoom)
- Viewport: the chart is full screen, 1920x1080 (still dimensions), the same as the harness's 1080p. Not a viewport difference.
- Opening view: ArgoniaCore's pushed chart.state carried `view {centre -55.938,10.573, zoom 8}` (a remembered view from an earlier session/step). main.ts kept any non-"whole" pushed view, so the chart opened at zoom 8 (a crop). OPEN_ZOOM = 3 applied only when the native view was exactly {1,1,1}.
- Zoom-out: the journey sent 4 LT triggers; log shows 4 `input zoomOut`. Each is /1.5: 8 / 1.5^4 = 1.58, never the clamp at ZOOM_MIN 1, so a crop of the west (the player is at the western edge). Zoom-in: 6 RT from 1.58 reached ZOOM_MAX 8 = the opening zoom, hence the pixel-identical still.
- Glide: about 7 frames in 0.8-1.2 s per step; the journey's 0.4 s waits were shorter than the glide, steps ran ~2.5-3 s apart in wall time anyway.

## Changed
- ui/views/chart/main.ts: the chart opens on the whole province ({1,1,1}) whatever view the native side remembers (owner #37: sketch first, detail on foot); later pushes keep the player's current view. The pane is unchanged (zoom 8 round the player).
- tests/journeys/chart-zoom.yaml: order open (whole) -> zoom in (6 RT, 1.5 s waits) -> zoom out (7 LT, 1.5 s waits, 1.5^7 > 8), each with a reader line and a log expect for the input.
- tools/ui_harness/harness.py: the wiring check expects the first "+" to send zoom 1.5 (opens at 1).

## Stills
Harness 1080p (= the game's viewport) zoom1 and zoom8: see Reader verdict below.
Reader (1080p): zoom1 shows the whole province uncropped (coast, dashed border, roads, all seven cities); the two ~475 px side strips are parchment mottle (not a cream column or veil) but read as a seam against the map's tan interior (feathered edge, chart.css .paper vs the map paper): P2 polish, the sheet is wider than the square chart. zoom8 is clearly closer, no blank bands. Harness run exit 0 (the listed fails are the pre-existing hud text sizes, unrelated).

## Owed
checks.md rows 219-222 stay owed: the planner's chart-zoom run of the new journey (open whole, zoom in, zoom out equals the opening).
