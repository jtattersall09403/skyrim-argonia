# Lane 1.15-r6-storm-grey: the storm, squall and wet-rain weathers neutral grey

Owner, 19:05 #41: "I don't want that smoggy yellow ever"; 17:49 #41: keep Tropical Skyrim's sky.

## 1. The evidence (chain27, 09-rain-look-1, read here)
- 02-rock-1-storm-s4: flat olive-khaki sky and fog, about RGB 112,120,104 (hue 90, sat 0.13). Rain streaks, no
  horizon, the ground a darker olive. s0/s3/s5 the same cast.
- 01-rock-1-wet-rain-s4: grey with a sage-green lean, no yellow (borderline).
- What the frame shows is the fog: at storm fog distances the sky and the far ground are the fog colour.

## 2. The measure (every colour slot drawn, the four times of day, read from the DB rows and the load order's winner)
Drawn source per slot: a clear (Pleasant) weather takes every colour from its template; every other weather draws the
template's sky paint (upper, lower, horizon, sun) and cloud layers, and our rows for fog, ambient, directional ambient,
sunlight and cloud LOD. Slots with hue 40-100 deg and saturation over 0.12, before this lane:

| weather | slot@tod (drawn rgb, hue, sat) |
|---|---|
| storm (ours) | fogNear@sunset 4B463C (40,.20); fogFar@sunrise 515045 (55,.15), @day 5D6355 (86,.14), @night 131B08 (85,.70); ambient@sunrise 363E31 (97,.21), @day 44503C (96,.25), @sunset 38362F (47,.16); sunlight@sunrise 9F9671 (48,.29), @day 8E8F71 (62,.21), @night 555240 (51,.25); cloudLodDiffuse@sunrise 4F5348 (82,.13); dalcSide/dalcDown all day olive (363A2C, 434B3A, 2B2B1F, 38352D) |
| storm, squall (template SkyrimStormRain, Update.esm) | skyUpper@sunset 4A4E41 (78,.17); horizon@sunset 635F53 (45,.16) |
| squall (ours) | none over 0.12 but fogNear@sunset 54554B (66,.12) at the edge |
| wet-rain (template OvercastRainFF, Tropical) | skyLower@sunrise 71713C (60,.47); horizon@sunrise 35321A (53,.51); cloud layer 9@sunrise 636549 (64,.28) |
| wet-rain (ours) | fogNear@sunrise 606755 (83,.17); fogFar@sunrise 636659 (74,.13), @night 1C2316 (92,.37); sunlight@sunrise 9F9578 (45,.25), @day 959881 (68,.15) |
| clear-dry, clear-dry-neutral (template) | fogNear@day 888A44 (62,.51); cloud layer 28@sunset 494A34 |
| mist x6 (ours) | ambient@sunrise 8A8777; dalcSide@sunrise 847F6C; dalcDown@sunrise 736E5A, @night 191D17 |
| monsoon-overcast (ours) | fogFar@sunrise 807E6F; ambient@sunrise/sunset; dalcUp@sunset; dalcSide@sunrise/day; dalcDown@sunrise/day |
| montane-haze x2 (ours) | ambient@sunrise/sunset; dalcUp@sunset; dalcSide@sunrise/sunset; dalcDown@sunrise/night |
| tannin-haze (ours) | ambient@sunrise/day; cloudLod@day; dalc day/night (the brown-gold air, by design) |
| sea-fog | none |

- **The storm's noon olive is ours**: fog near 51614C (hue 106, sat .22: just outside the brief's 40-100 band),
  fog far 5D6355, ambient 44503C, sunlight 8E8F71, directional ambient 434B3A. Its sky paint at noon is Update's
  slate (677C83 / 475A6D).
- **The storm image space** (marsh_storm, template StormRainDAY 0C8217, Tropical): written with our grade
  0.86/0.92/1.08 and tint amount 0 (gradeFromTemplate false; test_sky_writer reads the written IMGS TNAM = 0). The
  image space is not the cause this time.

## 3. The fix
- `api.NEUTRAL_SKY = {storm, squall, wet-rain}`: these draw our sky rows (`skyFromTemplate` false), the rest as before.
- weather_seed P[storm/squall/wet-rain] and the DB (migrate.weathers_1_15 through db.py): every sky, fog, ambient,
  directional ambient, sunlight and cloud LOD slot replaced, per slot and time, in the brief's order:
  1. **Skyrim.esm's own record** (SkyrimStormRain 0C8220 for storm and squall; SkyrimOvercastRainFF 10A23D for
     wet-rain, its template) for fog, ambient and directional ambient (DALC z+, x+, z-), kept where grey (sat < 0.10)
     or slate (hue 180-240, sat <= 0.35);
  2. else **the same record desaturated to 0.08 at its own value**;
  3. the sky paint from **the resolved template** (Update.esm's SkyrimStormRain; Tropical's OvercastRainFF, the sky
     the owner keeps) by the same rule; the sun disc unchanged;
  4. **our own slate** (hue 200, sat 0.12-0.13 at the source's value) where a desaturated zenith fell under vanilla's
     Rainy sky spread floor (9): storm/squall skyUpper sunset and night, wet-rain skyUpper night; wet-rain dalcUp night
     taken to 0.87 of the source (vanilla's luma band 56-68);
  5. sunlight a **warm-neutral grey** (hue 35, sat 0.10, the source's value) at sunrise, noon and sunset; at night
     the moonlight desaturated to 0.08;
  6. cloud LOD: ours, desaturated where olive.
  Slots that the weather-slots check read as a scaled copy or mix of another (greys are collinear) were nudged at most
  3 units per channel (marked "nudged" below).
- checks.weather_slots judges a NEUTRAL_SKY weather's sky on its own rows.
- Tests: `test_no_yellow_sky.py::test_no_weather_we_write_draws_an_olive_sky_fog_ambient_or_cloud_slot` (every weather
  we write, every drawn sky, fog, ambient, directional ambient, cloud LOD and enabled cloud layer slot at the four
  times; hue 40-100 at sat over 0.12 fails; the rain/storm sunlight sat under 0.15; an unused exception fails too);
  `test_sky_writer` checks a neutral weather's written NAM0 sky against our rows.

### The exception list (named in the test)
- clear-dry and clear-dry-neutral: fogNear@day 888A44, cloud layer 28@sunset: the template's own (Tropical's
  SkyrimClear, lightFromTemplate); the owner's A/B #43 rules it.
- wet-rain cloud layer 9@sunrise 636549: SkyrimOvercastRainFF's own dawn layer, on every vanilla overcast rain; the
  writer copies cloud layers whole, and a per-layer override is a generator change (rekeys every stage).
- mist x6, monsoon-overcast, montane-haze x2: our warm dawn and ground light (ambient, dalc), sat 0.12-0.26. Not a rain
  family and outside this lane's paths: **owed to the planner** (a follow-on lane, same method).
- tannin-haze: the brown-gold air by design (climatology §4).

## 4. Before and after (our rows; for the sky slots "before" is our unused row, the drawn value was the template's)
| weather | slot | sunrise | day | sunset | night | source (per changed time) |
|---|---|---|---|---|---|---|
| storm | skyUpper | 35403B→434950 | 424E48→677C83 | 3E3437→444B4E | 060E10→434B4E | sun: Update.esm as is; day: Update.esm as is; sun: Update.esm desat 0.08, our slate; nig: Update.esm desat 0.08, our slate |
| storm | skyLower | 504D43→8D8582 | 595E56→475A6D | 524A3A→7A7470 | 150F0C→151919 | sun: Update.esm desat 0.08; day: Update.esm as is; sun: Update.esm desat 0.08, nudged ≤3 (weather_slots); nig: Update.esm desat 0.08, nudged ≤3 (weather_slots) |
| storm | horizon | 62594C→151515 | 71705D→1F2323 | 61534A→63615B | 111B0B→151817 | sun: Update.esm as is; day: Update.esm desat 0.08, nudged ≤3 (weather_slots); sun: Update.esm desat 0.08; nig: Update.esm desat 0.08, nudged ≤3 (weather_slots) |
| storm | fogNear | 464D43→484B4E | 51614C→53585B | 4B463C→474542 | 0C1615→252727 | sun: Skyrim.esm desat 0.08; day: Skyrim.esm desat 0.08, nudged ≤3 (weather_slots); sun: Skyrim.esm desat 0.08, nudged ≤3 (weather_slots); nig: Skyrim.esm desat 0.08, nudged ≤3 (weather_slots) |
| storm | fogFar | 515045→374042 | 5D6355→4A585E | 584A46→373B3C | 131B08→222F33 | sun: Skyrim.esm as is; day: Skyrim.esm as is; sun: Skyrim.esm as is, nudged ≤3 (weather_slots); nig: Skyrim.esm as is |
| storm | ambient | 363E31→58646C | 44503C→434549 | 38362F→20292C | 09100A→0F0E0E | sun: Skyrim.esm as is; day: Skyrim.esm as is; sun: Skyrim.esm as is; nig: Skyrim.esm desat 0.08 |
| storm | sunlight | 9F9671→A6A096 | 8E8F71→9E968E | 685346→BFB7AC | 555240→ACB4BB | sun: Skyrim.esm warm-neutral h35 s0.10, nudged ≤3 (weather_slots); day: Skyrim.esm warm-neutral h35 s0.10, nudged ≤3 (weather_slots); sun: Skyrim.esm warm-neutral h35 s0.10; nig: Skyrim.esm desat 0.08 |
| storm | sun | 7A7356→000000 | 8C9376→000000 | 7A6750→000000 | 252925→000000 | sun: Update.esm as is; day: Update.esm as is; sun: Update.esm as is; nig: Update.esm as is |
| storm | cloudLodDiffuse | 4F5348→51534C | 66655E | 514944→504D4B | 101013 | sun: ours desat 0.08; sun: ours desat 0.08, nudged ≤3 (weather_slots) |
| storm | cloudLodAmbient | 2F2F2D | 384137→3C413C | 2E2929→2E2A2A | 08070A→07090B | day: ours desat 0.08; sun: ours desat 0.08; nig: ours desat 0.08, nudged ≤3 (weather_slots) |
| storm | dalcUp | 3D4339→1A2626 | 495549→53616C | 3F3B37→4B5158 | 1F4234→313C44 | sun: Skyrim.esm as is; day: Skyrim.esm as is; sun: Skyrim.esm as is; nig: Skyrim.esm as is |
| storm | dalcSide | 363A2C→5F666B | 434B3A→575F68 | 3A3427→4D505B | 091307→424653 | sun: Skyrim.esm as is; day: Skyrim.esm as is; sun: Skyrim.esm as is; nig: Skyrim.esm as is |
| storm | dalcDown | 2B2B1F→BFD2D5 | 38352D→B9D2DB | 2D231D→878E96 | 080803→597073 | sun: Skyrim.esm as is; day: Skyrim.esm as is; sun: Skyrim.esm as is; nig: Skyrim.esm as is |
| squall | skyUpper | 3C4A50→434950 | 4B5C62→677C83 | 40404A→444B4E | 081015→434B4E | sun: Update.esm as is; day: Update.esm as is; sun: Update.esm desat 0.08, our slate; nig: Update.esm desat 0.08, our slate |
| squall | skyLower | 56575B→8D8582 | 66746A→475A6D | 584F4F→7A7570 | 0F121A→141918 | sun: Update.esm desat 0.08; day: Update.esm as is; sun: Update.esm desat 0.08; nig: Update.esm desat 0.08, nudged ≤3 (weather_slots) |
| squall | horizon | 686B5F→151515 | 788182→202222 | 6A5D5A→63615B | 191F10→151719 | sun: Update.esm as is; day: Update.esm desat 0.08, nudged ≤3 (weather_slots); sun: Update.esm desat 0.08; nig: Update.esm desat 0.08, nudged ≤3 (weather_slots) |
| squall | fogNear | 4C595D→484B4E | 5B6C6A→53585B | 54554B→484442 | 0B161A→262727 | sun: Skyrim.esm desat 0.08; day: Skyrim.esm desat 0.08, nudged ≤3 (weather_slots); sun: Skyrim.esm desat 0.08; nig: Skyrim.esm desat 0.08, nudged ≤3 (weather_slots) |
| squall | fogFar | 4C5251→374042 | 657479→4A585D | 575452→373B3C | 17171F→222F33 | sun: Skyrim.esm as is; day: Skyrim.esm as is, nudged ≤3 (weather_slots); sun: Skyrim.esm as is, nudged ≤3 (weather_slots); nig: Skyrim.esm as is |
| squall | ambient | 3C4843→58646C | 4A5B55→434549 | 3E403B→20292C | 0D1810→0F0E0E | sun: Skyrim.esm as is; day: Skyrim.esm as is; sun: Skyrim.esm as is; nig: Skyrim.esm desat 0.08 |
| squall | sunlight | 969684→A6A096 | 859087→9E968E | 6D6356→BFB7AC | 4F5156→ACB4BB | sun: Skyrim.esm warm-neutral h35 s0.10, nudged ≤3 (weather_slots); day: Skyrim.esm warm-neutral h35 s0.10, nudged ≤3 (weather_slots); sun: Skyrim.esm warm-neutral h35 s0.10; nig: Skyrim.esm desat 0.08 |
| squall | sun | 848378→000000 | 9BA79E→000000 | 84796A→000000 | 2B3135→000000 | sun: Update.esm as is; day: Update.esm as is; sun: Update.esm as is; nig: Update.esm as is |
| squall | cloudLodDiffuse | 5B605F→5A605F | 6A797A→69797A | 5A5758 | 111520→1E1E20 | sun: ours as is, nudged ≤3 (weather_slots); day: ours as is, nudged ≤3 (weather_slots); nig: ours desat 0.08, nudged ≤3 (weather_slots) |
| squall | cloudLodAmbient | 32393D→32393C | 404D4F | 343335→343235 | 050F0D→0E0F0E | sun: ours as is, nudged ≤3 (weather_slots); sun: ours as is, nudged ≤3 (weather_slots); nig: ours desat 0.08, nudged ≤3 (weather_slots) |
| squall | skyStatics | 4A5651 | 5D6567→5D6667 | 4C474A | 191E1A | day: ours, nudged ≤3 (weather_slots) |
| squall | waterMultiplier | 46584F | 536761 | 474A48→484C4A | 1E2B22 | sun: ours, nudged ≤3 (weather_slots) |
| squall | dalcUp | 45514A→1A2626 | 53665C→53616C | 454545→4B5158 | 283F3B→313C44 | sun: Skyrim.esm as is; day: Skyrim.esm as is; sun: Skyrim.esm as is; nig: Skyrim.esm as is |
| squall | dalcSide | 3C4237→5F666B | 48524C→575F68 | 3C3A34→4D505B | 131A0D→424653 | sun: Skyrim.esm as is; day: Skyrim.esm as is; sun: Skyrim.esm as is; nig: Skyrim.esm as is |
| squall | dalcDown | 2D342B→BFD2D5 | 3B3F3B→B9D2DB | 342929→878E96 | 0D0A0D→597073 | sun: Skyrim.esm as is; day: Skyrim.esm as is; sun: Skyrim.esm as is; nig: Skyrim.esm as is |
| wet-rain | skyUpper | 4D5258→546565 | 5E666C→8BA3A3 | 564C55→51727B | 081411→4B5356 | sun: Tropical Skyrim.esp as is; day: Tropical Skyrim.esp as is; sun: Tropical Skyrim.esp as is; nig: Tropical Skyrim.esp desat 0.08, our slate |
| wet-rain | skyLower | 66635B→717168 | 787D77→708C8D | 685955→505757 | 131913→263534 | sun: Tropical Skyrim.esp desat 0.08; day: Tropical Skyrim.esp as is; sun: Tropical Skyrim.esp desat 0.08; nig: Tropical Skyrim.esp as is, nudged ≤3 (weather_slots) |
| wet-rain | horizon | 777361→343531 | 8A8F80→383C3C | 75675C→1A1B1C | 131F1C→152020 | sun: Tropical Skyrim.esp desat 0.08, nudged ≤3 (weather_slots); day: Tropical Skyrim.esp desat 0.08, nudged ≤3 (weather_slots); sun: Tropical Skyrim.esp desat 0.08; nig: Tropical Skyrim.esp as is |
| wet-rain | fogNear | 606755→3F4243 | 6E7D6B→37393C | 5F5A52→2F3334 | 0F1E14→2E363E | sun: Skyrim.esm desat 0.08, nudged ≤3 (weather_slots); day: Skyrim.esm desat 0.08; sun: Skyrim.esm desat 0.08, nudged ≤3 (weather_slots); nig: Skyrim.esm as is |
| wet-rain | fogFar | 636659→474E4B | 727A71→5B7881 | 665B4F→47585F | 1C2316→253130 | sun: Skyrim.esm as is; day: Skyrim.esm as is; sun: Skyrim.esm as is; nig: Skyrim.esm as is, nudged ≤3 (weather_slots) |
| wet-rain | ambient | 434B44→323436 | 586759→2C2E32 | 48463F→455053 | 12181B→131113 | sun: Skyrim.esm desat 0.08; day: Skyrim.esm desat 0.08, nudged ≤3 (weather_slots); sun: Skyrim.esm as is, nudged ≤3 (weather_slots); nig: Skyrim.esm desat 0.08 |
| wet-rain | sunlight | 9F9578→B5AFA5 | 959881→D3CABD | 80695A→D7CEC2 | 4D534A→A5B3B3 | sun: Skyrim.esm warm-neutral h35 s0.10, nudged ≤3 (weather_slots); day: Skyrim.esm warm-neutral h35 s0.10, nudged ≤3 (weather_slots); sun: Skyrim.esm warm-neutral h35 s0.10; nig: Skyrim.esm as is, our slate |
| wet-rain | sun | 988D6E→000000 | ADB398→000000 | 988168→405355 | 2F3735→000000 | sun: Tropical Skyrim.esp as is; day: Tropical Skyrim.esp as is; sun: Tropical Skyrim.esp as is; nig: Tropical Skyrim.esp as is |
| wet-rain | stars | 000000 | 000000 | 000000 | 3B453E→3B453F | nig: ours, nudged ≤3 (weather_slots) |
| wet-rain | cloudLodDiffuse | 6A6B62→6A6C62 | 7C8980 | 72605B→726B69 | 1A1D22 | sun: ours as is, nudged ≤3 (weather_slots); sun: ours desat 0.08 |
| wet-rain | cloudLodAmbient | 3E413B→3C413B | 4C5751→505753 | 403B39→3F3C3B | 060E12→111112 | sun: ours as is, nudged ≤3 (weather_slots); day: ours desat 0.08; sun: ours desat 0.08, nudged ≤3 (weather_slots); nig: ours desat 0.08, nudged ≤3 (weather_slots) |
| wet-rain | dalcUp | 4C5450→425053 | 5D6F68→586F7C | 514D49→344141 | 243F44→3A4040 | sun: Skyrim.esm as is; day: Skyrim.esm as is; sun: Skyrim.esm as is; nig: Skyrim.esm desat 0.08, our slate |
| wet-rain | dalcSide | 44463A→4B5A5F | 545D4E→546A81 | 464038→4A5055 | 141B10→39474A | sun: Skyrim.esm as is; day: Skyrim.esm as is; sun: Skyrim.esm as is, nudged ≤3 (weather_slots); nig: Skyrim.esm as is |
| wet-rain | dalcDown | 39372B→7A8585 | 48473E→C6D4DF | 3B3129→98B1BC | 0F0D0D→738789 | sun: Skyrim.esm as is; day: Skyrim.esm as is; sun: Skyrim.esm as is; nig: Skyrim.esm as is |

## 5. Gate and reach
- `pytest tools/argonia_world/regions/tests`: 35 passed (the lint, the writer against the built generator, the reseed).
- `make plugin PLAN=1`: records and yaml run; **terrain also runs, and this lane cannot stop it**. The terrain
  stage's cover (`pipeline.py stamps`) holds tools/argonia_world/regions/api.py and the weather_colour table, because
  terrain/world.py imports regions.api for the region shells. Any weather record change re-keys terrain (the fog-yellow
  lane's did too). Other lanes' live terrain edits were moving the key on every run as well. Fix at source (planner's
  call; terrain files are another lane's): move the shell functions (shell_keys, shell_records, cell_region_runs,
  border_*) out of regions/api.py into regions/shells.py and point terrain/world.py at it.
- Planner's L4 (batch): the rain-look journey again, rock-1 storm and wet-rain s0-s5: sky and fog grey or slate, no
  olive. The look is darker than before at noon: vanilla's storm and rain fog values sit below ours.
