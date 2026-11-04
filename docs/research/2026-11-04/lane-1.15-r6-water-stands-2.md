# Lane 1.15-r6-water-stands-2: water stands clear of grass, water in frame, clear-dry; river-steps from the side

Commits: 04dd3b75 (generator, measures, tests), then the journeys and this report.

## What changed
- `tools/journeys/__init__.py`: `Grass` reads the LTEX blend under each LAND vertex from out/terrain/land (base + 17x17
  alpha layers; a texture at >= 0.3 of the blend grows its list), each LTEX's list from `ltex_grass`, each GRAS's model
  from out/ltex-scan.json. `grass_hits` counts tall grass (>= 0.5 m, not submerged) within 6 m of the eye or under the
  first 20 m of the eye line; `clearance3` = (line, canopy, grass). `frame_share` marches the lower half of the still
  (+-30 deg across, 25 deg down from the pitch, 0-60 m) over the ground and water heights.
- Caveat: `GRASS_HEIGHT_M` is a height class per grass mesh (the scan carries no bounds), not a measurement. Measured:
  93 % of 3000 random province points grow a tall grass, so 0 grass hits is rare away from beaches and rivers.
- `tools/journeys/gen.py`: every water and step stop forces clear-dry (`sw`/`fw Argonia.esm|0x000E9B`, settle) at 13:00
  and reads `ARG_Weather_clear_dry` back within 20 s. Water stands: a strict pass (0/0/0 and frame share >= 50 %, 4 m
  grid to 60 m, 40 shores), else a widened pass (2 m to 60 m, 25 m to 600 m, 2.5 m round the best, the 6 best shores)
  that keeps the stand meeting the share with the fewest hits. River-steps: first person, HUD off on every stop, the
  step seen from its side 15-25 m off (perpendicular to the flow, up to +-45 deg), the rapids line and the foot inside
  +-35/+-28 deg of the aim and in sight (>= 60 %); each still body is shot twice (a, b) from one stand 5 s apart.
- Refresh (water-types + river-steps): 185 s measured (11:15:16-11:18:21), progress printed per stop.

## The seven water stands (clearance line/canopy/grass; frame share; near-field share)
| stop | stand x y | facing, pitch | clearance | frame | near | meets |
|---|---|---|---|---|---|---|
| sea | -71226 41083 | 8, 0 | 0/0/0 | 82 % | 98 % | yes |
| green-marsh | -115689 118247 | 90, 2 | 0/0/1 | 100 % | 86 % | no: 1 grass vertex |
| black-swamp | -221093 -91088 | 157, 0 | 0/5/20 | 88 % | 100 % | no: canopy and grass |
| river | 93976 -43175 | 316, 0 | 0/0/0 | 76 % | 92 % | yes |
| stream | -179111 -26703 | 122, 7 | 1/3/16 | 57 % | 14 % | no: plants and grass |
| tarn | -227818 39192 | 91, 1 | 0/0/0 | 76 % | 99 % | yes |
| brackish-rim | 70662 59005 | 317, 1 | 1/1/3 | 82 % | 99 % | no: plants and grass |

The stops that cannot meet the brief within 600 m on the 6 best shores: green-marsh, black-swamp, stream, brackish-rim.
Every one meets the 50 % frame share; what fails them is grass/canopy. Next lever (planner's call): suppress grass at
stands (a no-grass LTEX patch at the viewpoint) or relax the grass rule for marsh bodies, since marsh is grass by lore.

## River-steps stands (clearance; step pieces in frame)
| stop | stand x y | facing, pitch | clearance | pieces |
|---|---|---|---|---|
| step-1 | -204094 192820 | 105, 37 | 0/0/41 | 60 % |
| step-2 | -193453 68115 | 45, 26 | 1/0/43 | 100 % |
| step-3 | -237331 -50093 | 315, 30 | 1/1/43 | 100 % |
Every step stand frames the step but stands in tall grass (no stand 15-25 m from any of the three is grass-free).

## Checks
`refresh --only water-types,river-steps` ok; `check` 0 stale; `run_journey.py --dry` ok (7 and 10 steps);
tools/tests/test_journeys.py 15 passed (new: grass clearance, frame share). L4 in the planner's rerun.
