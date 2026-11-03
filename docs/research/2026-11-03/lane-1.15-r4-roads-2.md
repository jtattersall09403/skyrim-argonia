# Lane 1.15-r4-roads-2: the roads lane's reds (walls, over-steep points, the gully crossing)

The before is the roads lane's last ground, rebuilt here as `out/r2/gen0` (a province generate; its stats are byte-identical to the roads lane's). The after is `out/r2/gen1`, the second province generate. The final numbers come from a replay of the road pass on generate's road dump (ARGONIA_ROAD_DUMP), with the final re-traced roads. The replay is exact: replaying gen0 reproduced generate's check line for line.

## Wall census by cause (240 walls on gen0; `routes.shape census`; each wall takes the first cause that holds)
- Crossing: 192. These walls have water within the taper on the centreline, a water sample at the edge, or a bank or bed cone holding the ground.
- Pinned place core: 19. None comes from a site pin (lo == hi); all 19 are on a site's disc or blend.
- Step in the land itself: 19.
- Other: 10.
- 173 of the 240 walls were already in the ground before the roads were laid (`h_roads_in`). Most of these are the water's own banks: both samples are water, or the road never moved them.
- 67 walls were made by the road:
  - 24 on dry ground beside water: the road did not fade toward the bank.
  - 22 at a binding cone.
  - 21 on steep side slopes: the 0.4 cross keep had no lateral cap, so the road cut a 2-3 m bench.

## Over-steep points by cause (1120 on gen0)
- 868 are where the land under the road is itself steeper than 0.219 (median 0.39, p90 0.77). They fall in 196 runs with a median length of 11 m. A 1 m cap cannot absorb a 4 m bank, so these need a re-route.
- 225 crossing, 4 pinned, 23 other.

## Changed
- shape.py:
  - `grade_within`: the 0.85 x 0.219 grade limit is held inside its own Lipschitz band of land +-1 m, so the cut cap no longer breaks the grade.
  - A 1 m cap on cut and fill across the road.
  - The fade follows the bank: the weight comes from a chamfer distance to water.
  - The road's change is held inside 0.2 m/sample cones from every sample it may not move (water, off-corridor ground, the lo/hi cones).
  - `TROUGH_GAIN` 1.35 deepens the target trough so the measured fold reaches vanilla.
  - New `census()`. `check` now fails only on walls and steep points away from crossings and places, and lists the ones it exempts. It reads `road-water-u8.npy` and `entrance-sites.json` beside the ground.
- build.py:
  - The tracer pays `GRADE_COST` 1500 per unit of grade over 0.186 on a step, measured on the generated ground.
  - It pays `SIDE_COST` 60 where the land's side slope is over 0.35.
  - Chaikin corner cutting, then a re-simplify to 0.25 m (road_point.jsonl stays under the 1 MB guard).
  - The roads are re-traced (the world/db road tables).
- generate.py: writes `road-water-u8.npy`.
- Tests: three new L2 tests (the cut cap, the bank fade, the census).
- road-look.yaml: vantages re-derived on the new ground (ground + 160 units). The slope vantage moved because the road takes a new line.

## Before (gen0) -> after (final roads)
| measure | before | after | vanilla |
|---|---|---|---|
| walls (old metric) | 240 | 237 | 0 |
| walls the road made (not in the land before) | 67 | 20 | 0 |
| walls: crossing / pinned / land / other | 192/19/19/10 | 166/51/3/17 | |
| dry points over 0.219 | 1120 | 571 | 0 |
| steep: crossing / pinned / land / other | 225/4/868/23 | 118/240/208/5 | |
| grade p95 / max | 0.283 / 2.88 | 0.200 / 1.81 | 0.164 / 0.219 |
| fold at 2 m / 4 m, median | 0.077 / 0.240 | 0.091 / 0.262 | 0.09 / 0.29 |
| water check | green | green (0 cells with two levels, 0 steps without a chain) | |

`make check-reach` is green.

## L3 reader (hillshade stills, before and after, in out/r2/stills)
- Flat window: ACCEPT. No wall, band or causeway; the change is barely visible.
- Slope window: ACCEPT. No wall or banding, and no causeway at the water. The re-traced road now crosses a water body instead of the old gully. The reader flags a small bump at the shore turn.

## Still red and owed
- The check is still red: 20 walls and 213 steep points lie away from crossings and places. Most of the steep points are on roads 9 (Glenbridge-Nisswo), 21, 12 and 11. They sit on short banks that the 7.3 m search grid only partly sees. Next: a finer re-trace of those stretches (STRIDE 2) or switchbacks.
- The 4 m fold is 0.262, under the 0.29 median. A gain of 1.5 meets the median, but the trough's own slope then reads as a wall at the core edge (walls 230 -> 272). The planner's call.
- Owed to bridges: 166 walls and 118 steep points beside crossings (216 crossings).
- Owed to places: 51 walls and 240 steep points on site discs and blends, mostly the climbs onto Gideon and Glenbridge.
- In game: road-look (the existing checks.md row stays owed).
- routes.build check was already red on main (7 roads against the old chain's lengths) and stays red. It is not part of make check.
