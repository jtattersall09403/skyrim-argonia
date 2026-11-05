# Lane 1.15-r6-water-look-2: black swamp olive, stream murky, yellow-green cast

L1/L2, no game. Evidence: r6-chain23 water-types scans (20261105T005149/02-water-types-1-...), road-look scans
(05-road-look-1-...). Colours are box means of the PNGs (hex, HSV).

## Measured (before)
| stop | region sampled | rendered | note |
|---|---|---|---|
| black-swamp s0 | water band (x .45-.95, y .6-.7) | 323F27 (93°, .38, .25) | canopy above it 25321B (94°, .46, .20): same hue |
| black-swamp s0/s1 | whole frame | 344725 / 2D4022 (94-98°, .47) | |
| green-marsh s0 | whole frame | 566C56 (120°, .20, .42) | |
| stream s1 | water (x .2-.8, y .65-.95) | 2B382B (120°, .23, .22) | |
| road-look blackwood s0 (3 stops) | whole frame | 7C8C6F / 7D8C71 / 687454 (82-93°, .19-.28) | the same cast off the marsh |

Records (layer.winners, the load order's winner, DNAM 40/44/48 colours, 20/24 reflectivity/fresnel):
| record | shallow | deep (V) | reflection colour | refl / fres | fog | ANAM | NAM0 |
|---|---|---|---|---|---|---|---|
| MurkyWater (Update; our black before, refl from DarkFall) | 26,19,19 | 9,9,6 (.035) | **32,35,27 olive** | 0.28/0.00 | 0-60 | 100 | 0 |
| DLC01DarkFallCaveDarkStillWater (Dawnguard; black after) | 31,33,33 | 12,12,12 (.047) | **10,10,5** | 0.28/0.00 | 0-30 | 75 | 0 |
| RiftenWater (Update) | 36,53,39 | 16,15,5 | 106,120,105 | 0.58/0.05 | -10-80 | 30 | .19,.19 |
| BlackreachWater (Update) | 40,72,89 | 21,104,102 (.41) | 38,63,74 | 0.55/0.35 | 0-290 | 100 | |
| CreekWaterFlowSE/SW (Update; our creeks) | 71,78,67 | 35,35,24 | 55,65,80 | 1.0/0.15 | 20-160 | **0** | .7,-.72 / -.98,-.69 |
| DefaultCreekWater (Update) | 71,78,67 | 35,35,24 | 55,65,80 | 1.0/0.02 | 10-90 | 0 | .23,.36 |

Image space of clear-dry's day (one WTHR for every region; `day` -> template 10A1EE, gradeFromTemplate since r6-light):
| plugin | CNAM sat/bright/contrast | TNAM amount x colour |
|---|---|---|
| Skyrim.esm ISSkyrimClearDAY_FF | 1.3/1.1/1.25 | 0.56 x DBCCBA (warm neutral) |
| Update.esm | 1.9/1.2/1.4 | 0.56 x DBCCBA |
| **Tropical Skyrim.esp (winner)** | 1.3/1.1/1.25 | **0.56 x DCE1AE (66°, .23) yellow-green** |
Clear-dry also draws its template's (Tropical SkyrimClear) day fogNear 888A44 (62°, .51) (lightFromTemplate; lane fog-yellow table).

## Causes, one sentence each
1. Black swamp olive: the water's rendered hue equals the canopy's (93° vs 94°) and its V (.25) is far above the body
   colour (.035), so it is the reflection of the lit canopy, tinted by MurkyWater's olive reflection colour 32,35,27 and
   then by the frame's yellow-green grade; reflectivity (0.28) is already Bethesda's lowest dark-still value.
2. Stream murky and still: not the record, which is Update's CreekWaterFlowSE whole (opacity 0, Skyrim's clearest; NAM0
   0.7,-0.72 flowing); a still cannot show flow, and the dark grey-brown is the bed and depth seen through it under the
   same grade. GameGround along the stop's view line (yaw 125) reads the ground 0.2-1.2 m above the creek-se plane
   (8231.33 u) while the still shows water: the stop's geometry needs the planner's state read.
3. Yellow-green cast (marsh stops and the Blackwood Road, one source): every clear-dry frame takes Tropical Skyrim's own
   day image-space tint 0.56 x DCE1AE under saturation 1.3 (Skyrim.esm's same record tints a warm-neutral DBCCBA), plus
   Tropical's day fogNear 888A44. It is Tropical's template, so per the brief the owner rules; this lane changes nothing there.

## Fix (commit below)
- layer.py: the black type copies DLC01DarkFallCaveDarkStillWater whole (Bethesda's darkest still water, reflection colour
  10,10,5); REFLECT_FROM is gone (no borrowed fields remain). Streams unchanged.
- test_water_writer.py: black deep and reflection colours V < 0.2, reflectivity < 0.3, fresnel 0; every creek type flows
  (|NAM0| > 0.9) with opacity 0. The marsh/rain image spaces' no-tint test already exists (test_no_yellow_sky.py).
- `pytest water/tests + test_no_yellow_sky`: 42 passed (110 s). `make plugin PLAN=1`: water skip (rebuilt in this tree at
  01:11 with the new record: records.json names DLC01DarkFallCaveDarkStillWater); vegetation, creatures, world-esm run;
  terrain also shows run, from another lane's inputs, not this change.

## Owner call (planner posts)
Keep Tropical Skyrim's clear-day grade (yellow-green tint 0.56 x DCE1AE, fog 888A44), or take Skyrim.esm's own 10A1EE
(warm-neutral DBCCBA) for clear weathers: one switch in api._image_records / the clear template.

## Next scan must show
Black swamp water near-black (V < .15) and grey, not olive; the stream reads clear over its bed, with flow judged on a
clip; the cast row stays open until the owner rules.

## The owner's A/B for the cast (coordinator, after the first hand-back)
- One source on the road too: the Blackwood Road frames (r6-chain23 05-road-look) read 7C8C6F / 7D8C71 / 687454
  (82-93°); every region's noon is the one clear-dry WTHR and its `day` IMGS (Tropical's 10A1EE).
- `clear-dry-neutral` (ARG_Weather_clear_dry_neutral, 000F03:Argonia.esm): clear-dry's DB rows copied (db.py; the
  seed carries it too); its day image space `day-neutral` (ARG_ImageSpace_day_skyrim, 000F04). `api.SKYRIM_PINNED`
  names both: their templatePlugin is Skyrim.esm, so the writer takes SkyrimClear's light (fog near included) and
  ISSkyrimClearDAY_FF's grade and tint (1.3/1.1/1.25, 0.56 x DBCCBA). No region list draws it. The DB's tint_amount
  check (at most 0.03) is why it is the pinned template, not our own row. Reseeding with `migrate --weathers-1-15`
  is refused: the seed is behind the DB for monsoon-overcast, montane-haze and tannin-haze (11 slot errors), so the
  rows went in directly.
- Journey `grade-ab` (gen.grade_ab, DERIVED, batch after road-look): coastal-lagoon-shore at sky-ab's marker and aim
  (yaw 154, pitch 0) and road-look's blackwood-20 stand, each `-tropical` and `-skyrim` at 12:00, scan 6, with
  position and weather read back. refresh, check (0 stale), lint and dry all ok.
- Tests: test_no_yellow_sky (the twin differs from clear-dry only in its day image, Skyrim.esm pinned, not in any
  list); test_sky_writer judges each record against its own plugin's template.
- Owed before deploy: `make plugin` (plugin/Argonia/ gains the two records' YAML).
