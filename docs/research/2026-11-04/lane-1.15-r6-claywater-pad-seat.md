# Lane 1.15-r6-claywater-pad-seat: a place's pad sits in the slope as Bethesda seats a house

## Before (out/terrain of 2026-11-05 05:04, read through GameGround, the LAND's numbers)
- The plate was not generate.py's: it was `terrain/patches.py`'s `common` pad (r 28 m, blend 4 m), one flat disc
  for the whole yard at its ground's mean (72.07 m). It stood 0.5 m under the site's own flat on its north rim and
  fell 4.1-5.4 m off its east and west rims (second difference 0.40-0.52 m at 0.5 m steps, over the road-profile bar
  0.487 m). It also held the river's shelf in its disc (28 bed and 75 shore samples), so the signpost p1 and a reed
  stood "dry" only on the plate.
- Each footprint pad inside it was levelled on the raw ground, not the plate: the station house's pad stood
  0.88-0.99 m proud of the plate on all four sides, the stable 0.5-0.57 m, the well 0.59 m: plinths on a plate.
- Pad edges at Claywater, all sides, 0-12 m out: second difference p95 0.095 m, max 0.523 m.

## Bethesda (Skyrim.esm, probe in the scratchpad: the LAND around every Farmhouse01-06 and FarmhouseSmith01 ref)
- 65 houses, 58 on a rim slope >= 4 deg (Whiterun's farms 4..5,-12..-21, Pelagia's 5,-12, Riverwood's 3..4,-19..-21
  among them; footprint from each STAT's OBND, rotated).
- Under the footprint the LAND is not flat: relief p50 1.9 m (0.55-5.31 m); the ref's origin sits below the
  highest ground under it, so the house's own stone plinth takes up the slope. No retaining piece is placed.
- Beside the footprint the slope simply runs on: flat (|dz| < 0.15 m) p50 2 m, p90 8.5 m beyond the footprint;
  gradient 0-3 m p50 5.0 deg, p90 16.7 deg; 6-12 m p50 6.5 deg; second difference p50 0.008 m, p95 0.079 m.
- So Bethesda flattens no yard; a flat is at most a house's own seat.

## The fix (patches.py, terrain_patch rows, schema)
- New kind `lift`: a yard or a hut group is raised as a whole (relief kept) by the least that sets the 5th
  percentile of its dry ground PAD_FREEBOARD_M (1.0 m) over its cells' water; the river's bed and shelf are not
  counted. Claywater's `common` and `south-huts` are lifts (lift 0.0 m and 0.87-0.96 m by the water of the day).
- A `pad` is a footprint (station house, stable, well, hut b6), levelled on the ground the lifts leave, its blend
  widened until its rim step eases away no steeper than SEAT_FALL_DEG 16.7 deg (Skyrim's p90) over the slope's own
  fall (`seat_blend`, capped at 12 m). The paint fade follows the widened blend (it reads blend_m).
- p1, its two boards and node-marshweed moved off the river's shelf onto the yard (y 3049/3055 -> 3058/3058.5).
- The foundation question: no kit piece is needed; the KotM house and the huts stand on a footprint pad.

## After (same ground)
- Pad and lift edges, all sides, 0-12 m out: second difference p95 0.062 m (bar 0.487); footprint pads p95
  0.029-0.043 m, max 0.098 m. The station house's edge now follows the slope (-0.12..+0.44 m at 6 m, no plinth).
- Remaining maxima (common E 0.765 m, well 1.262 m at 10 m out) are the generated river bank north and east of
  the yard: the site's flat (generate.py, r 65 m, 72.7 m) meets the river's 67.7 m shelf over ~3 m.
- Flat runs beyond a footprint: 21 of 24 sides <= 8.5 m; 3 sides (station house N 9.5 m, well 11.5 m, stable 12 m)
  run on generate.py's site flat (FLAT_KEEP 0.35, core std 0.4 m), not a patch.

## Owed (not this lane)
- generate.py's flat site beside the river: a 5 m wall to the shelf and flat runs past Skyrim's p90; needs a
  province generate (chain28's land pass) and a rule from Riverwood's banks.
- Today's out/terrain sits ~4.5 m above the ground the station's explicit z_m were set on (b1 3.9 m under):
  test_place_seating's two Claywater tests fail at HEAD too, independent of this lane.
- L4 in the planner's batch: the claywater-look stills 02-04 retaken after the land pass.
