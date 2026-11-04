# Lane 1.15-r6-look-journeys-standard: report

## The rule
`tools/journey_lint.py` `look()`, run by `run_journey.py --dry` (the lint) and `python3 -m tools.journeys check`.
Marker: `look: world` at a journey's head (a still of the world for a reader; `reader:` alone also marks UI screens,
so it could not be the marker). A marked journey needs `camera: first`; `hud: off` in its first step (and in every stop
with `independent_steps`); per stop (a step that runs cow/coc/setpos/moveto) `fw <plugin>|0x<hex>` and
`{read: [weather], path: current.editor_id, eq: ..., within: <=20}`, or `weather: any  # why`.
At HEAD (marked) it fails: ground-materials 8 errors, road-look 8, rock-booth 19 (`fw` by editor id, no HUD, no read),
tree-seat 37, claywater-look 32. After: 0 each. Tests: tools/tests/test_journey_lint.py (rule + the five), 24 passed
with test_journeys.py; `tools.journeys check` 0 stale; `--dry` ok for all five.

## The stands (`tools/journeys/look.py`, run by refresh)
Numbers per stand: plants on the eye line to the subject / canopy over the eye (10 m) / tall-grass vertices
(water-stands-2's `grass_hits`, near the eye and under the first 20 m) / stand faults. The search: the subject fixed,
bearings every 15 deg, a distance band; ordered line, then canopy, then grass. Every stand has line 0 (nothing between
eye and subject); 1 of 17 is fully clear: grass is near every stand in these biomes, and canopy remains at 9.

| journey / stop | line canopy grass | dist, pitch | the reader must see |
|---|---|---|---|
| ground-materials pebble-field (-9 27) | 0 0 33 | 8 m, 14 | varied forest floor, pebble edge only in a strip by water, no wet sheen |
| ground-materials hillside (-50 8) | 0 0 20 | 15 m, 7 | matte ground with relief, no sheen on sunlit slopes |
| road-look blackwood-20 / flat-46 / slope-57 | 0 1 16 / 0 1 32 / 0 0 1 | 15-22 m, 7-13 | the road a shallow worn trough along the frame's middle, dirt blending ~4 m, no spike/wall/step, no Nordic piece |
| rock-booth rock-1..6 | 0 0 3; 0 0 0; 0 1 3; 0 0 43; 0 0 32; 0 1 6 | 4-17 m | rock sunk, no gap under the downhill lip, no hollow back, leans with the slope |
| tree-seat tree-1..6 | canopy 1,4,3,1,30,4; grass 17-35 | 2.4-7 m | trunk base meets the ground, natural bark and leaf colour |
| tree-seat class-* (6) | reframe only (no subject) | level | trees and plants named; six classes not one forest |
| claywater-look (9 stops) | moveto stands (gen.claywater's place) | | header checklist; station-house-inside `weather: any` (interior) |

## Gaps (honest)
- Pitch: on flat ground a 1.83 m eye meets the ground at 20 deg only ~5 m off; at 8-15 m the pitch is 7-14 deg. The
  patch is aimed at, so it sits mid-frame; the brief's "20 deg at 8-15 m" cannot both hold.
- claywater-look stands are moveto offsets from refs and are not re-searched by the clearance measure (place() only).
- tree-5 (hist trunk) sits under 30 canopy volumes from 6 m: its own crown family; a reader should judge it.
- Grass counts depend on lane water-stands-2's `grass_hits` (uncommitted when measured).
- L4 owed: the planner's rerun.
