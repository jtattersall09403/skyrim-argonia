# Lane 1.15-r6-fog-yellow: the yellow smog sky in rain

Owner, 19:05 #41: "I don't want that smoggy yellow ever". The still is
docs/research/2026-11-04/stills/round-6-selection/13-rock-booth-1.jpg: noon, rain, and a pale yellow-green sky and
fog over cell (-55,63).

**The cause:** since 971f0eee (lane 1.15-r6-light, 07:58, before the 10:36 batch), every image space took its
template's cinematic grade and tint (`gradeFromTemplate: True` on every IMGS). Tropical Skyrim's rain image space
RainDAY 10A1C6 tints the screen A3B185 (hue 79, sat 0.25) at amount 0.75, with saturation 1.5 and brightness 1.225.
That turned our slate wet-rain fog (6E7D6B / 727A71) into the yellow-green smog.

## 1. The weather of the still
- The step forced `sw/fw Argonia.esm|0x000E9B` (clear-dry), but the still shows rain, and clear-dry carries no
  precipitation (it takes its template SkyrimClear's: none). The run ended before report.json, so no weather was
  read.
- The rock lies in dunmer-north.northern-transition (weather group lowland). Its list is clear-dry 16, clear-ff 15,
  cloudy-ma 15, montane-haze 29, tannin-haze 6 and wet-rain 19. The only rain weather in it is **wet-rain**
  (ARG_Weather_wet_rain, template SkyrimOvercastRainFF 10A23D, which Tropical Skyrim overrides). Its day and dawn
  image space is `rain`.
- wet-rain's own fog and sky rows are not yellow anywhere (§2). The yellow came from the image space.

## 2. Our weathers against their templates (read from the plugins with api.template_colours, the load order's winner)
Slots listed are those where ours or the template is yellow or olive (hue 30-80°, saturation over 0.25). "!" means
ours is yellow and the template is not. Every other slot of every weather is neither.

| weather (template, winner) | slot | tod | ours (h,s,v) | template (h,s,v) |
|---|---|---|---|---|
| clear-dry (SkyrimClear, Tropical) | fogNear/fogFar/skyLower/horizon/sunlight | sunrise | 9F8664 (35,.37,.62)! etc. | 2F4E5B blue |
| clear-dry | fogNear | day | 7B9498 | **888A44 (62,.51,.54)** |
| wet-rain (OvercastRainFF, Tropical) | skyLower / horizon | sunrise | 66635B / 777361 grey | 71713C / 35321A olive |
| monsoon-overcast (CloudyMA, Tropical) | fogFar | sunset | 706250 (34,.29,.44)! | 65727A slate |
| tannin-haze (ClearMA, Tropical) | skyLower, ambient | sunrise/sunset | C4A070, 6C6149 gold! | lavender/grey |
| mist, sea-fog, montane-haze | fogNear | day | grey 8A9996 / 8D9893 / 8B9890 | B19C49 / B6B944 / 688107 olive |
| storm, squall (SkyrimStormRain, Update) | skyLower sunset, sunlight sunrise | | 524A3A, 9F9671 ! | 7A5A3D, 92A3B8 |

- Line 132's 9F8664 (clear-dry sunrise fogNear) is not drawn. clear-dry is Pleasant and takes every colour from its
  template (`lightFromTemplate`, r6-light), so the suspect slot never reaches the game.
- The sky paint (upper, lower, horizon, sun) of every weather is the template's (`skyFromTemplate`). Ours on those
  slots is not drawn.
- Two Tropical Skyrim weathers that the region lists drew by reference were yellow on their own records:
  **SkyrimStormRainTU** (storm-rain, 10A241: day fogNear D7BC22 (51,.84,.84), fogFar 666242, horizon 535026, ambient
  635527; 13 yellow slots; coastal and uplands storm, 17 regions) and **SkyrimCloudyFF** (cloudy-ff, 10A23F: day
  fogNear 688107 (72,.95,.51); uplands clear-humid, 4 regions).

### Image spaces (template CNAM sat/bright/contrast, TNAM amount x colour)
| ours | template (winner) | template grade | template tint | written before -> after |
|---|---|---|---|---|
| day | 10A1EE (Tropical) | 1.3/1.1/1.25 | 0.56 x DCE1AE (66°,.23) | template -> template (clear-dry) |
| dawn | 10A1EB (Update) | 1.5/1.2/1.5 | 0.42 x A4A363 (59°,.40) | template -> template (clear-dry) |
| night | 10A1EC (Update) | 1.5/1.35/1.5 | 0.79 x 566772 blue | template -> template |
| **rain** | 10A1C6 (Tropical) | 1.5/1.225/1.35 | **0.75 x A3B185 (79°,.25)** | template -> ours 0.9/0.96/1.02, no tint |
| **storm** | 0C8217 (Tropical) | 1.15/1.125/1.45 | **0.75 x A9BA65 (72°,.46)** | template -> ours 0.86/0.92/1.08, no tint |
| **overcast** | 10A1CE (Tropical) | 1.9/1.07/1.4 | 0.65 x DADFB6 (68°,.19) | template -> ours 0.95/1.0/0.98, no tint |
| mist, haze, seafog, montane | 10A1CA, 10A1C2, 10A1D6, 10A1FE | 1.15-2.0 | 0.6-0.75, hue 66-96 | template -> ours, no tint |

## 3. The fix
- `api.template_graded`: only the image spaces a clear (Pleasant) weather draws (day, dawn, night) take the
  template's grade and tint. Every other image space keeps its seeded grade with tint off (FFFFFF x 0), as it was
  before r6-light. HDR stays the template's everywhere.
- weather_seed REALISE and the DB, through db.py: the coastal and uplands storm state is now our `storm` (on
  SkyrimStormRain, grey), not storm-rain. The uplands' cloudy day is now cloudy-ma, not cloudy-ff. Chances are
  unchanged: 17 storm rows and 4 cloudy rows are re-pointed, with their season globals
  ARG_WChance_{coastal,uplands}_storm and ARG_WChance_uplands_cloudy_ma (FormIDs 0xEFE and 0xEFF are new).
- monsoon-overcast fogFar at sunset changes from 706250 to 5C686F, the template's slate one step darker. The template's
  own 65727A sat within 10% of the horizon's luma (checks.weather_slots).
- Derived, regenerated: skse tables_weather.h (season.py) and the seven world-sample scenes' weather lists.
- Tests:
  - `regions/tests/test_no_yellow_sky.py`: every listed weather and time of day, with no fog or sky slot drawn yellow
    unless the template's slot is; a referenced weather with no yellow slot by day; rain, storm and overcast images
    untinted.
  - `test_sky_writer`: the template grade is judged only where it is taken. Elsewhere the written TNAM amount is 0.

## 4. After
- wet-rain at noon draws fog 6E7D6B / 727A71 and sky 708C8D / 21353D (template) through an untinted grade at
  saturation 0.9. No region list draws storm-rain or cloudy-ff.
- No rain, wet, overcast or storm weather has a yellow fog or sky slot at noon.
- Left, and left as the template's own:
  - wet-rain's sunrise skyLower and horizon (71713C / 35321A). Every vanilla overcast rain has them (OvercastRain,
    RainMA, RainVT, RainRE), so this is Bethesda's dawn (0034).
  - clear-dry's noon fogNear 888A44 (Tropical's SkyrimClear, taken whole by r6-light), under a blue fogFar 3995F9.
  - the template's dawn tint on montane-haze and tannin-haze dawn.

  If the retake shows any of these, the planner should take them to the owner.
- tannin-haze's gold sunrise and sunset sky and ambient are ours and are kept by design ("brown-gold air",
  climatology §4). It is a dry haze, not a rain family.

## 5. Gate and reach
- `make plugin PLAN=1`: terrain and ground skip. Water, vegetation, creatures and world-esm run on other lanes'
  uncommitted work in the tree. This change reaches records only (WTHR, IMGS, GLOB).
- The planner's retake is checks.md row 158 (rock-booth in wet-rain at noon). plugin/ yaml for the GLOBs refreshes
  at the next `make plugin`.
