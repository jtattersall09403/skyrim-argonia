# Lane 1.15-r6-water-stands-3: the frustum, not the line; the stop's own type in frame; the river along its flow

Commits: d420363d (measures, generator, 2 tests), 3b1c13d8 (river-steps re-derived). water-types.yaml NOT committed
(check red on stream); the tree keeps the round-6 file.

## What changed
- `frustum_cover` (tools/journeys/__init__.py): each placed plant (seated OBND cylinder) and tall-grass vertex in the
  frustum (+-32 across, +-20 up/down, 0-25 m) as the angular rectangle at its nearest distance over the frame area;
  near (plants 0-10 m), upper (above the aim), all, grass (reported, not gated), nearest_m. `cover_ok`: near < 5 %,
  nearest >= 2.5 m, sea upper < 10 %. `frame_read` + `type_share`: lower-frame wet rays by DB cell type, >= 70 % own.
- gen.py `_fit`: river aim within 30 deg of the reach centreline's downstream heading (hard); key (frame/type miss,
  cover penalty, clearance hits, -share); `step_stand` gates on cover too. tools/tests/test_journeys.py: 17 passed.

## Water stands
| stop | stand, heading | line/canopy/grass | near | upper | nearest | type | frame | verdict |
|---|---|---|---|---|---|---|---|---|
| sea | -254563 -98187, 85 | 0/0/0 | 0.0 % | 8.2 % | 24.1 m | 100 % | 50 % | ok |
| green-marsh | -115689 118247, 90 | 0/0/1 | 0.0 % | 0.0 % | 5.9 m | 99 % | 100 % | 1 grass vertex |
| black-swamp | -186543 -146953, 1 | 15/0/48 | 0.3 % | 208 % | 4.4 m | 100 % | 100 % | cover ok; line hits 10-25 m |
| river | 64982 -30059, 86 | 9/0/33 | 3.7 % | 175 % | 0.8 m | 99 % | 100 % | OVER: plant at the eye |
| stream | -172433 -30783, 105 p19 | 2/0/47 | 0.0 % | 43.6 % | 2.7 m | 100 % | 60 % | check STALE: near field 2 % |
| tarn | -228098 39366, 78 | 0/0/0 | 0.0 % | 7.3 % | 10.5 m | 100 % | 83 % | ok |
| brackish-rim | -76553 241233, 177 | 0/0/34 | 3.6 % | 33.8 % | 0.8 m | 100 % | 79 % | OVER: plant at the eye |

Round-6 black-swamp turquoise: every black-swamp stand reads 100 % own type by the cell rows, so not a neighbouring
body; the type's application in game is the suspect (not proven here).

## River-steps (line/canopy/grass; near cover; nearest; pieces)
step-1 -201794 192204: 0/0/41, 3.8 %, 3.4 m, 100 %. step-2 -193453 68115: 1/0/43, 110 %, 0.1 m, 100 % (OVER).
step-3 -237331 -50093: 1/1/43, 113 %, 0.0 m, 100 % (OVER): no side stand 15-25 m off steps 2-3 clears the frustum.

## Open
- Refresh 346 s measured (needs 270 s): per-candidate frustum and frame reads; next a per-stand cache by build.
- check red (stream near field 2 %); river, brackish-rim, step-2/3 fail the 2.5 m eye rule within 600 m.
