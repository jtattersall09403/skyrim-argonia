# Lane 1.15-r6-water-stands-3: the frustum, not the line; the stop's own type in frame; the river along its flow

Commits: d420363d, 6903326b (no 2.5 m rule, stream floor 30 % with the aim along the channel, check on the same
frame-share floors, per-stand cache in out/journeys/cache), 0c28058f (stand or aim 3x3 cell carries the stop's
cell_water type), 38bfd52f + d3616280 (cache key by content and sizes: mtimes moved on every boot), then water-types.yaml.
Measured: refresh 153 s resumed from the cache after a reboot; `check` 0 stale; `--dry` ok; 17 tests passed.

| stop | stand, heading | line/canopy/grass | near | upper | type | frame (floor) | stand cell / aim cell |
|---|---|---|---|---|---|---|---|
| sea | -254563 -98187, 85 | 0/0/0 | 0.0 % | 8.2 % | 100 % | 50 % (50) | dry / (-56,-24) sea |
| green-marsh | -115689 118247, 90 | 0/0/1 | 0.0 % | 0.0 % | 99 % | 100 % (50) | (-29,28) marsh / marsh |
| black-swamp | -196453 -156267 | 12/0/39 | 0.4 % | 247 % | 100 % | 54 % (50) | (-48,-39) black / (-45,-34) black |
| river | 64982 -30059, 86 | 9/0/33 | 3.7 % | 175 % | 99 % | 100 % (50) | (15,-8) river-se / river-se |
| stream | -178131 -26983 | 1/0/31 | 1.5 % | 13.9 % | 100 % | 31 % (30) | (-44,-7) creek-se / creek-se |
| tarn | -228098 39366, 78 | 0/0/0 | 0.0 % | 7.3 % | 100 % | 83 % (50) | (-56,9) cold / (-52,10) marsh |
| brackish-rim | -76553 241233 | 0/0/34 | 3.6 % | 33.8 % | 100 % | 79 % (50) | (-19,58) brackish / (-19,54) sea |

River-steps: step-1 near 3.8 % ok; step-2 110 %, step-3 113 % near cover: no side stand 15-25 m off clears the frustum.
Open: tarn's and brackish-rim's aim cells carry a neighbouring type (the frame rays read 100 % own type); step-2/3.
