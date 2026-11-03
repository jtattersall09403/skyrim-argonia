# Lane 1.15-r5-sky: what paints the sky at noon under clear-dry

L1, measured from the bytes: Skyrim.esm (`~/games/skyrimse/Data`) against our written Argonia.esm. "Before" is
round 4's deployed `out/Argonia.esm` (06:00). "After" is this lane's build, made by `intermediate` + `ArgoniaGen generate` in the scratchpad. Fog distances and the height-fog bank were not touched (proven in round 4).

## Causes (ours; fixed at source)

1. **A cream veil over the whole sky: every cloud layer, including the full-sky fill, had one colour.**
   `tools/ArgoniaGen/RegionWeather.cs:213-226` (before) gave every textured cloud layer the weather's single
   `cloudLodDiffuse` colour (`api.py:262`). SkyrimClearFF draws `SkyrimCloudsFill.dds`, which covers the whole sky, at a
   noon alpha of 0.5. Vanilla tints that layer the zenith's dark blue `114E77`, and ours drew it cream `ECEBD9`. Its
   eight upper layers get blue-white tints in vanilla (`A3C0D1`, `B1CAD8`...); ours were all `ECEBD9`. The result is half-opaque cream over the sky at noon: a pale yellow-grey sheet that fog settings cannot remove.
   Fix: a Pleasant weather now takes its template's per-layer colours, as it already took its alphas (`coloursFromTemplate`).
2. **The image space blew the sky out.** `api.py:239` (before) gave every IMGS our own HDR: sky scale 1.6
   (Skyrim.esm's ISSkyrimClearDAY_FF has 0.30, and every vanilla IMGS sits between 0.00 and 0.38) and white 4.0 (vanilla 0.82-1.05).
   Other fields were also far off: eye-adapt speed 1 (vanilla 20-50), strength 0.3 (vanilla 1.5-30) and bloom scale 0.4 (vanilla 2.2-5). The sky rendered about 5x brighter
   than vanilla's, flattening to a pale sheet. Fix: each IMGS now carries its template's HDR (`hdrFromTemplate`), as
   WATR carries its template's body (b5a6907b, 0034).
   - That exposed a hidden error: the image_space templates were off by one. "day" pointed at ISSkyrimClearDAWN_MA,
     "dawn" at NIGHT_MA and "night" at DAY_MA. Re-pointed through db.py (`world/db/image_space.jsonl`, `weather_seed.py`):
     day 10A1EE ClearDAY_FF, dawn 10A1EB ClearDAWN_FF, night 10A1EC ClearNIGHT_FF, haze 10A1C2, overcast 10A1CE,
     montane 10A1FE, mist 10A1CA, seafog 10A1D6, rain 10A1C6, storm 0C8217.
3. (Cloudy, fog and rain weathers, not clear-dry) **Layers the template switches off were drawn.** Before, NAM1 was 0
   on all 17 of our weathers: every textured layer was on. SkyrimCloudy and SkyrimFog switch some off: NAM1 has bits 0, 1
   and 3 set, so OblivionCloudCloudyUpper01, WastelandCloudHorizon01 and SkyrimClouds04 stay off. With all on, extra
   overcast sheets stacked. Fix: `Enabled = tpl.Clouds[i].Enabled`. After the fix, ours has NAM1 0xB where the template has 0xB.

## Table (day; the sunrise and sunset fields are in the same rows, sr/day/ss)
| weather | cloud layers drawn; fill alpha (sr/day/ss) and colour | cloud speed | skyUpper sr/day/ss | skyLower | horizon | DALC Z+ | fog day near/far, power, max | sun | IMGS day HDR |
|---|---|---|---|---|---|---|---|---|---|
| SkyrimClear | 12 on: SkyrimCloudsFill.dds, SkyrimCloudsHorizon01.dds, SkyrimCloudsUpper01.dds, SkyrimCloudsUpper02.dds, SkyrimCloudsUpper04.dds; fill a=0.2/0.3/0.2 c=4A6379/145373/494A34 | qx -88 | 425A79/39779B/32464A | 9DA1B5/649FBC/816554 | BA8167/7DA3B7/5B4C46 | 50515A/4D8188/50535A | 1200/80000 p0.4000000059604645 max0.8500000238418579 | glare 1.00 dmg 0.00 | sky 0.23 white 1.0 |
| SkyrimClearFF | 12 on: SkyrimCloudsFill.dds, SkyrimCloudsHorizon01.dds, SkyrimCloudsUpper01.dds, SkyrimCloudsUpper02.dds, SkyrimCloudsUpper04.dds; fill a=0.2/0.5/0.2 c=4D7082/114E77/67391E | qx -88 | 425A79/0C5A86/323F4A | 9DA1B5/5894B8/8D6247 | BA8167/6499B5/5E4945 | 50515A/558D95/50535A | 1200/60000 p0.4000000059604645 max0.8399999737739563 | glare 1.00 dmg 0.00 | sky 0.3 white 1.02 |
| SkyrimCloudy | 8 on: SkyrimCloudsFill.dds, SkyrimCloudsHorizon01.dds, SkyrimCloudsLower01.dds; fill a=0.5/0.4/0.4 c=334548/2F6C84/2E2E2F | qx 127 | 2C4045/296175/363A43 | 718386/5E95B3/695D5B | 81847C/97C1E1/C0553A | 525852/59687B/4F5051 | 0/100000 p0.4000000059604645 max0.875 | glare 0.80 dmg 0.00 | sky 0.19 white 1.05 |
| SkyrimCloudyMA | 8 on: SkyrimCloudsFill.dds, SkyrimCloudsHorizon01.dds, SkyrimCloudsLower02.dds; fill a=1.0/0.4/0.4 c=1A3E46/306176/364343 | qx 127 | 07242C/1E5162/293941 | 658B86/5E8395/767976 | 60A0AC/B1CADC/FB5800 | 3A4B3F/6C747D/475258 | 0/80000 p0.375 max0.8999999761581421 | glare 0.80 dmg 0.00 | sky 0.19 white 0.98 |
| **ours (before)** |||||||||| 
| ARG_Weather_clear_dry | 12 on: SkyrimCloudsFill.dds, SkyrimCloudsHorizon01.dds, SkyrimCloudsUpper01.dds, SkyrimCloudsUpper02.dds, SkyrimCloudsUpper04.dds; fill a=0.2/0.5/0.2 c=DBAA79/ECEBD9/D38C61 | qx -110 | 577FAC/4B86C8/676E9E | C99A6A/91B5CD/C38057 | E4B174/C7D6CB/DF8E4B | 5E554A/7D8465/685447 | 1050/98042 p1.2000000476837158 max0.550000011920929 | glare 1.00 dmg 0.00 | sky 1.6 white 4.0 |
| **ours (after)** |||||||||| 
| ARG_Weather_mist | 6 on: SkyrimClouds01.dds, SkyrimCloudsFill.dds; fill a=1.0/1.0/1.0 c=D0C6B6/E0E8D2/CFB7A5 | qx -123 | 97A0A5/B1C0BF/A3969F | CDBCAE/D1D9C3/C8B5A0 | E1C8B1/DBDFC8/DABAA0 | 5B544F/7B827A/5E564F | 140/49021 p0.6000000238418579 max0.949999988079071 | glare 0.00 dmg 0.00 | sky 0.38 white 0.9 |
| ARG_Weather_squall | 9 on: SkyrimClouds01.dds, SkyrimCloudsFill.dds, SkyrimCloudsHorizon01.dds, SkyrimCloudsLower03.dds; fill a=1.0/1.0/1.0 c=5B605F/6A797A/5A5758 | qx -27 | 3C4A50/4B5C62/40404A | 56575B/66746A/584F4F | 686B5F/788182/6A5D5A | 45514A/53665C/454545 | 700/31514 p0.800000011920929 max0.949999988079071 | glare 0.00 dmg 0.10 | sky 0.2 white 0.88 |
| ARG_Weather_storm | 9 on: SkyrimClouds01.dds, SkyrimCloudsFill.dds, SkyrimCloudsHorizon01.dds, SkyrimCloudsLower03.dds; fill a=1.0/1.0/1.0 c=4F5348/66655E/514944 | qx -40 | 35403B/424E48/3E3437 | 504D43/595E56/524A3A | 62594C/71705D/61534A | 3D4339/495549/3F3B37 | 560/26611 p0.800000011920929 max0.949999988079071 | glare 0.00 dmg 0.10 | sky 0.2 white 0.88 |
| ARG_Weather_tannin_haze | 13 on: SkyrimCloudsFill.dds, SkyrimCloudsHorizon01.dds, SkyrimCloudsLower04.dds, SkyrimCloudsUpper01.dds, SkyrimCloudsUpper02.dds, SkyrimCloudsUpper04.dds; fill a=1.0/1.0/1.0 c=CFA679/D2CDA6/CB9065 | qx -104 | 777A8A/7992A9/7B6E7C | C4A070/B6AD8F/C08965 | DBA976/CDBA85/D7985D | 605544/85816B/665445 | 1050/49021 p1.2999999523162842 max0.800000011920929 | glare 0.50 dmg 0.00 | sky 0.3 white 1.0 |
| ARG_Weather_clear_dry | 12 on: SkyrimCloudsFill.dds, SkyrimCloudsHorizon01.dds, SkyrimCloudsUpper01.dds, SkyrimCloudsUpper02.dds, SkyrimCloudsUpper04.dds; fill a=0.2/0.5/0.2 c=4D7082/114E77/67391E | qx -110 | 577FAC/4B86C8/676E9E | C99A6A/91B5CD/C38057 | E4B174/C7D6CB/DF8E4B | 5E554A/7D8465/685447 | 1050/98042 p1.2000000476837158 max0.550000011920929 | glare 1.00 dmg 0.00 | sky 0.3 white 1.02 |
| ARG_Weather_monsoon_overcast | 8 on: SkyrimCloudsFill.dds, SkyrimCloudsHorizon01.dds, SkyrimCloudsLower02.dds; fill a=1.0/1.0/1.0 c=989588/BBC1B1/94857A | qx -91 | 6A7379/879695/726A62 | 8D8880/AFAFA6/8E7B71 | A99B8A/B9BCAC/A58C75 | 5A554F/7A8377/5C574D | 1050/49021 p1.0 max0.800000011920929 | glare 0.20 dmg 0.00 | sky 0.19 white 0.98 |
| ARG_Weather_montane_haze | 8 on: SkyrimCloudsFill.dds, SkyrimCloudsHorizon01.dds, SkyrimCloudsLower01.dds; fill a=1.0/1.0/1.0 c=BFB6A5/D6DBD1/BBA695 | qx -97 | 6782A4/6994C1/6F789C | A9A49A/A6BABA/A89486 | C1B69F/BDC4BE/BDA28D | 55574F/76837F/5B5850 | 1050/49021 p1.100000023841858 max0.8500000238418579 | glare 0.30 dmg 0.00 | sky 0.19 white 1.0 |
| ARG_Weather_sea_fog | 6 on: SkyrimClouds01.dds, SkyrimCloudsFill.dds; fill a=1.0/1.0/1.0 c=B2B3AE/CAD1CB/AFA99F | qx -104 | 89969D/A3B2B7/8B8A99 | B3AEA6/C3C5C4/AE9FA1 | C5BAB0/CDD0CD/C1AEA1 | 535752/76867D/575756 | 280/31514 p0.699999988079071 max0.949999988079071 | glare 0.00 dmg 0.00 | sky 0.38 white 0.9 |
| ARG_Weather_wet_rain | 9 on: SkyrimCloudsFill.dds, SkyrimCloudsHorizon01.dds, SkyrimCloudsLower03.dds; fill a=1.0/1.0/1.0 c=6A6B62/7C8980/72605B | qx -66 | 4D5258/5E666C/564C55 | 66635B/787D77/685955 | 777361/8A8F80/75675C | 4C5450/5D6F68/514D49 | 1050/28012 p0.8999999761581421 max0.949999988079071 | glare 0.00 dmg 0.20 | sky 0.25 white 0.88 |
| ARG_Weather_mist_20m | 6 on: SkyrimClouds01.dds, SkyrimCloudsFill.dds; fill a=1.0/1.0/1.0 c=D0C6B6/E0E8D2/CFB7A5 | qx -123 | 97A0A5/B1C0BF/A3969F | CDBCAE/D1D9C3/C8B5A0 | E1C8B1/DBDFC8/DABAA0 | 5B544F/7B827A/5E564F | 140/49021 p0.6000000238418579 max0.949999988079071 | glare 0.00 dmg 0.00 | sky 0.38 white 0.9 |
| ARG_Weather_mist_25m | 6 on: SkyrimClouds01.dds, SkyrimCloudsFill.dds; fill a=1.0/1.0/1.0 c=D0C6B6/E0E8D2/CFB7A5 | qx -123 | 97A0A5/B1C0BF/A3969F | CDBCAE/D1D9C3/C8B5A0 | E1C8B1/DBDFC8/DABAA0 | 5B544F/7B827A/5E564F | 140/49021 p0.6000000238418579 max0.949999988079071 | glare 0.00 dmg 0.00 | sky 0.38 white 0.9 |
| ARG_Weather_mist_2m | 6 on: SkyrimClouds01.dds, SkyrimCloudsFill.dds; fill a=1.0/1.0/1.0 c=D0C6B6/E0E8D2/CFB7A5 | qx -123 | 97A0A5/B1C0BF/A3969F | CDBCAE/D1D9C3/C8B5A0 | E1C8B1/DBDFC8/DABAA0 | 5B544F/7B827A/5E564F | 140/49021 p0.6000000238418579 max0.949999988079071 | glare 0.00 dmg 0.00 | sky 0.38 white 0.9 |
| ARG_Weather_mist_49m | 6 on: SkyrimClouds01.dds, SkyrimCloudsFill.dds; fill a=1.0/1.0/1.0 c=D0C6B6/E0E8D2/CFB7A5 | qx -123 | 97A0A5/B1C0BF/A3969F | CDBCAE/D1D9C3/C8B5A0 | E1C8B1/DBDFC8/DABAA0 | 5B544F/7B827A/5E564F | 140/49021 p0.6000000238418579 max0.949999988079071 | glare 0.00 dmg 0.00 | sky 0.38 white 0.9 |
| ARG_Weather_mist_6m | 6 on: SkyrimClouds01.dds, SkyrimCloudsFill.dds; fill a=1.0/1.0/1.0 c=D0C6B6/E0E8D2/CFB7A5 | qx -123 | 97A0A5/B1C0BF/A3969F | CDBCAE/D1D9C3/C8B5A0 | E1C8B1/DBDFC8/DABAA0 | 5B544F/7B827A/5E564F | 140/49021 p0.6000000238418579 max0.949999988079071 | glare 0.00 dmg 0.00 | sky 0.38 white 0.9 |
| ARG_Weather_montane_haze_68m | 8 on: SkyrimCloudsFill.dds, SkyrimCloudsHorizon01.dds, SkyrimCloudsLower01.dds; fill a=1.0/1.0/1.0 c=BFB6A5/D6DBD1/BBA695 | qx -97 | 6782A4/6994C1/6F789C | A9A49A/A6BABA/A89486 | C1B69F/BDC4BE/BDA28D | 55574F/76837F/5B5850 | 1050/49021 p1.100000023841858 max0.8500000238418579 | glare 0.30 dmg 0.00 | sky 0.19 white 1.0 |

Reading it: after the fix, clear-dry's clouds, fill and HDR are the template's, so they sit at vanilla. The remaining differences from vanilla clear are all authored, and none can hide the sky:
- skyUpper `4B86C8` against vanilla `0C5A86`-`39779B`: bluer and brighter.
- horizon `C7D6CB` against `6499B5`-`7DA3B7`: paler.
- DALC Z+ `7D8465` (olive) against `4D8188`-`558D95`.
- fog power 1.2 against 0.4, and fog max 0.55 against 0.84 (round 4's proven fog, left alone).
- sun glare 1.0 and sun damage 0, both equal to vanilla.

The olive DALC and ambient slots (`7A8367`) are the one remaining candidate for a yellow-olive cast on the ground. They are the owner's authored slots, so they are named here and not changed. The A/B stills decide.

Cloudy-class weathers keep their full fill (alpha 1.0, their own colour) where vanilla's cloudy has 0.4. That is the deck their class means. **tannin-haze** is Cloudy-class on a clear template, so its fill draws cream `D2CDA6` at alpha 1.0: a deliberate brown-gold haze, and a yellow veil wherever it is current. Flagged for the planner, not changed.

## Climate and worldspace (bytes)
- The WRLD override ARG_Province (14000800) has CNAM 15000813, ARG_Climate_black_marsh.
- Its WLST: clear_dry 13, SkyrimCloudyMA 13 (a vanilla reference, the jungle group's fallback), monsoon_overcast 27, storm 20, wet_rain 27. Sum 100.
- The journeys force 0x000E9B (sw + fw), so the forced weather is ours.

## Community Shaders settings laid (data/dependencies.json)
| feature | value | can it veil the sky? |
|---|---|---|
| ExponentialHeightFog (global) | density 0.1, **20x the CS default 0.005**; fogHeight 0, falloff 30, start 700 u, volumetric on 20,000 u, originalFogColorAmount 1.0 | Yes, below the bank. This is round 4's proven bank. clear-dry has no per-weather file, so the global applies under it |
| per-weather height fog (0x80F, 0xED4-0xED8, 0xE9D, 0xEDA, 0xE9E) | the same density, with fogHeight per band | mist, montane and sea-fog only |
| VolumetricLighting | exterior and interior on, quality 1 (Medium) | adds shafts, no veil |
| CloudShadows | opacity 0.5 (the default) | ground only |
| TerrainShadows | on | ground only |
| GrassLighting | specular 0.3, below the 0.5 default | no |

## Proof and what is owed
- `tools/argonia_world/regions/tests/test_sky_writer.py` writes our WTHR and IMGS through ArgoniaGen and reads the bytes against
  Skyrim.esm. It uses `checks.sky_clouds` and `checks.sky_image`, which test each layer drawn as the template draws it, a clear sky's layer colours, the HDR, and the image template's time of day.
  The synthetic tests show the checks flag the round-4 bytes.
- `make check-reach`: 384 passed, 5 skipped, REACH GREEN.
- Plugin YAML: the WTHR and IMGS files were regenerated from this build.
- L4 owed (new `checks.md` row): `tests/journeys/sky-ab.yaml` (dry-run ok), with five steps: the coastal-lagoon shore and the
  western-frontier high vantage, each at noon and at dawn 06:30, clear-dry forced, first person, HUD off, pitched 12 degrees up. The planner runs it under both
  launches, shaders on and shaders off, on one deploy. A reader answers: blue zenith visible, no grey veil, no yellow or olive cast, and how the two launches compare.

## Coordinator rulings, 2026-11-03 (applied; bytes before → after)
1. **Fill layer from a clear template, on every weather.** `RegionWeather.cs` copies slot 28's colour and alpha (`SkyrimCloudsFill`) whenever the template carries the Pleasant flag (`api.py` `fillFromClearTemplate`).
   - tannin-haze fill: `CFA679/D2CDA6/CB9065/2C312D` at alpha 1.0 → `61738A/277697/2C2832/0E274C` at 0.2/0.5/0.2/0.2 (SkyrimClearMA's).
   - monsoon-overcast fill: `989588/BBC1B1/94857A/262B2E` at 1.0 → `1A3E46/306176/364343/08262D` at 1.0/0.4/0.4/0.5. SkyrimCloudyMA's DATA byte 11 also carries the Pleasant flag, so the rule covers it too.
   - tannin-haze's fogNear, fogFar and horizon are now warm greys: HSV saturation ≤ 0.04, at about the old luma, nudged until weather-slots passes. Examples: fogFar day `AFA083` → `A6A5A6`, horizon day `CDBA85` → `B5BAB6`. They are re-pointed through db.py. `checks.HAZE_GREY` now holds tannin-haze to `mist_fog_cast`. `weather_seed.py` still records the first authoring.
2. **clear-dry's ambient and directional ambient (DALC) come from the template** (`ambientFromTemplate`, Pleasant).
   - ambient: `6C6351/7A8367/685745/1A281F` → `94A1B6/98B3CC/6A6C7A/4C6990`.
   - DALC Z+: `5E554A/7D8465/685447/2C3F38` → `50515A/558D95/50535A/32434E`.
- `checks.sky_fill_and_ambient` is called from `test_sky_writer.py`. The Weathers YAML is regenerated.
