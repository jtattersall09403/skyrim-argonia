# Lane 1.15-weather: authored weathers, seasons, mist regimes

Brief: [1.15-weather](briefs/1.15-weather.md). Levels proven: L1 (make world), L2 (skse/check.sh, pytest).
L4 is owed to the planner's batch (the panel's dawn stills).

## The weather set and each palette's source
- **BM&V has no WTHR or IMGS.** `Black Marsh.esm` (read with terrain/esm.py) holds three CLMT and five REGN;
  its `BlackMarshClimate` draws Skyrim.esm's SkyrimFog 40, SkyrimStormRain 20, SkyrimOvercastRain 20, SkyrimCloudy 10,
  SkyrimClear 10. So BM&V's look is kept by reference to those forms (Tropical Skyrim's restyles), which stay in the
  group lists (`weather_realisation`); nothing to copy.
- **Ours, nine, every slot authored** (`weather_colour`: 17 NAM0 slots plus 3 directional-ambient faces x 4 times
  of day = 80 colours each, 720 rows, each with a why): clear-dry, monsoon-overcast, wet-rain, mist, sea-fog,
  montane-haze, tannin-haze, squall, storm. Sources: the climatology (§2 two fog regimes, §3 the M field, §4 the
  regions) and 55-light-sky-time §97–98, cited in each weather's why (`regions/weather_seed.py`). Drafted by hand per
  weather, each slot given its own hue character, residual copy-path coincidences nudged a few units (stated in
  the seed's docstring).
- The LADDER and the one-tint derivation are gone from `regions/api.py`; the sky's motion and fog curve moved from
  the per-state table to `weather_sky`. Fog distances: see below.
- Image spaces: 10, tint amount 0 (CHECK caps it at 0.03); saturation and contrast per weather with a why.

## Mist regimes (`region_mist`, 48 rows)
Rule (`migrate.regime_of`): mountains and hills >= half the cells -> montane; coastal group -> sea_fog; misty eco
class -> radiation; else none; border -> none. Result: radiation 29, sea_fog 13, montane 5, border none.
Realised the vanilla way (skyrim-does-it-this-way §7, session 2): the region's mist weather (`mist` / `sea-fog` /
`montane-haze`) sits in its list at the regime's season chance (`mist_regime_season`), ungated by hour; its own fog
curve does the dawn work. Radiation 35/32/28 (dry/hatching/wet: marsh lists hold fog at 28–35 % as
WeatherTundraMarshNoPrecip's FogMA 28 and Falkreath's Fog 35), sea fog 30/25/20, montane 20/30/35. The hour-gated
`ARG_WMist_*` globals, `mist_regime`'s hours and global, `region_mist.hours` and the C++ `mist_settings` rule are gone.

## Seasons and lists
Each region list: the group's synoptic weathers (`REALISE`, at most five) plus its mist weather = 6 entries (282 rows),
chances summing to exactly 100 in the base list and in every season (largest remainder, `season.group_lists`).
Seasons stay on per-(group, weather) `ARG_WChance_*` globals, the one thing a global carries (seasons are new to
vanilla, §7); a group whose regions draw two mist regimes is refused. The ground-mist state's vanilla fog forms
(FogMA, FogCO...) left the region lists; the mist weathers realise it.

## Fog distances (session 2, §7)
Inside Skyrim.esm's measured ranges per classification (`skyrim_units.FOG_RANGES_U`, `checks.fog_outside_vanilla`
in `weather-slots`), a mist regime's fog no thicker than SkyrimFog (>= 25,000 u day, 15,000 u night).
Metres, day near/far, night near/far: mist 0/360/0/215; sea-fog 4/450/2/300; montane-haze 15/700/10/480;
monsoon-overcast 15/700/10/480; tannin-haze 15/700/10/480 (Cloudy: its 1,100 m day far was over the 50,000 u p90);
clear-dry 15/1400/5/700; wet-rain 15/400/10/280; squall and storm unchanged.

## Community Shaders (pinned 1.9.1)
Its Exponential Height Fog (v1.9.1 source, src/Features/ExponentialHeightFog.*) with volumetric fog. Laid by the
`files` entry on the community-shaders row of `data/dependencies.json`:
`SKSE/Plugins/CommunityShaders/Overrides/Argonia_ExponentialHeightFog.json` (enabled, volumetric on, vanilla fog
kept so per-weather WTHR distances rule, original fog colour 1.0 so the authored slots colour it, fogHeight 350
units, falloff 0.35, density 0.012). Per-weather CS settings exist (`CommunityShaders\Weathers\0x<local>~<plugin>.json`,
`featureSettings`) and are not used yet.

## Checks (all in `make world`)
`weather-slots` (0 derived; scaled copy along the same slot or same time of day, or a mix within a time of day, to
half a byte; fog inside vanilla's ranges), `image-tint` (0 above 0.03), `region-weather` (1–6 entries, 100 in the
base list and every season, marsh fog 28–35 %, every season different, season windows >= 7 days). Measured: 0 / 0 / 0.

## What the panel's dawn stills must show
At 06:30 under the region's dawn weather (`python3 -m tools.argonia_world.regions.panel_weather`): radiation regions
a low milky mist over water, sea-fog regions a grey-white bank, montane a haze belt with clear summits; no
yellow-green screen tint; the noon still under the commonest clear without a tint wash. Also check CS's Overrides
tab lists Argonia_ExponentialHeightFog.

## Session 3: round 1's stills diagnosed (2026-11-02)
Reader on panel 02, 03, 11, 15, 31, 33, 35, 36, the mist strip and creature spots 01, 04: no light shaft in any;
coast noon (02, vanilla SkyrimCloudyCO) sky near white; dawn fog grey-green uniform, not height-banded; strip flat
(about 55 luma every frame); water-day fog mustard (150,135,40) over the whole frame; marsh-night about 12 luma.
- **No god rays: our WTHR had no HNAM.** Skyrim SE's volumetric lighting (WTHR HNAM -> four VOLI) lives only in
  Update.esm's overrides (Skyrim.esm: 84 WTHR, 0 HNAM, 0 VOLI; Update.esm: 69 WTHR all with HNAM, 36 VOLI; VLClear
  sunrise intensity 4.0, VLFog 2.25). `RegionWeather.cs` read templates from Skyrim.esm only; it now takes the HNAM
  link from the Update.esm override. Measured in out/Argonia.esm: all nine weathers carry HNAM (mist and sea-fog the
  VLFog set, clear-dry and tannin-haze VLClear). CS 1.9.1 sets the engine's VL flag from its own ExteriorEnabled
  (VolumetricLighting.cpp SetupVL), and `Shaders/Features/VolumetricLighting.ini` is present, so no ini is needed.
- **Height fog never ran.** CS reads `SKSE/Plugins/CommunityShaders/Overrides` (its README; stack.py's
  `apply_files` lays our five there), but Exponential Height Fog is not core: Feature::Load disables any feature
  without `Data/Shaders/Features/<Name>.ini`, and the 1.9.1 archive has no `ExponentialHeightFog.ini` nor its
  shaders. Our EHF override is inert; the low, banded mist needs the EHF feature as its own dependency row (owed:
  find its Nexus file, register it, then tune). The uniform grey is vanilla distance fog alone.
- **Light slots outside vanilla's range.** Measured luma over Skyrim's 33 region weathers (Update.esm): fog near by
  day 31-151, night sunlight 79-184, night up-light 56-68. Ours: fog near by day to 220 (blown coast haze, flat grey
  dawn), night sunlight 38 and up-light 26 (black marsh). New `skyrim_units.LUMA_RANGES` and a weather-slots check;
  70 slots rescaled in hue to the nearest bound, 30 then nudged a few units to stay underived.
- **No burn-off:** the mist's day far was 360 m against 215 m at night, so sunrise barely opened it. Now 700 m
  (FogMA's 50,000 u) by day: the fog lifts through sunrise inside the one weather. The strip also forced the weather,
  so no transition to clear could show (harness).
- **Tidal delta** dawn is `sea-fog` (panel_weather; sea_fog chance 30/25/20): the class is right; its day fog was
  the over-bright grey that read as plain haze. **Yellow day fog:** the weather at that spot was not recorded;
  tannin-haze is our only brown-gold one and is now inside vanilla's luma; a creature-spot weather read is owed.
- **Coast noon** is vanilla CloudyCO (Tropical Skyrim's restyle), not ours: its blown sky is that mod's or the
  exposure, to judge after the light fixes. Western-frontier dawn is montane-haze over a dark canopy (35 luma 45).

## Starting state
- Done: the weather set, lists, seasons, fog ranges (sessions 1-2); session 3: HNAM from Update.esm, vanilla luma
  bands with a check, mist burn-off range. Measured: `make world` green; regions pytest 18 passed; `make plugin`
  built (Argonia.esm, nine WTHR with HNAM); panel_weather 47 regions consistent.
- Owed: the EHF feature dependency (not in CS 1.9.1) before any height-fog tuning; the planner's next batch re-shoots
  panel dawn/noon, the mist strip without a forced weather, and creature spots with a weather read
  (GetCurrentWeather) at water-day; then shafts, burn-off and night brightness judged by a reader.

## Session 4: the sun was hidden by the weather (2026-11-02, from lane-1.15-r3-machine §3)
- **Cloud alpha.** Every authored weather wrote alpha 1.0 on all 29 cloud layers, so even clear-dry was a full deck.
  Skyrim's SkyrimClear / ClearFF keep 0.2-0.8 on their upper layers (Skyrim.esm JNAM, measured) with sun glare 191/166 of
  255 (ours 0.9) and sun damage 100 %. A Pleasant weather now takes its template's per-layer alphas (`alphaFromTemplate`,
  api.py, RegionWeather.cs; builds with dotnet, game-side stills owed). HNAM is set (session 3).
- **Lists.** Every group's list holds clear-dry (dry-season chance 15-18 %); SkyrimClearCO/MA no longer in coastal/marsh.
  `ARG_Climate_black_marsh` drew SkyrimClear (0x00081A) and SkyrimCloudy (0x012F89), vanilla forms Tropical Skyrim does
  not restyle (it adds CO/MA/FF variants); replaced by clear-dry and cloudy-ma (the TS marsh restyle), so the fallback
  list is ours (climate why, decision 0012).
- **Panel.** Noon is clear-dry in every region; dawn is the region's mist weather (clear-dry with none). Each step
  moves, settles 60 s, sets the hour, then `sw <edid>` and reads the bridge `weather` back (`current.editor_id`, within
  20 s; a null read is a menu open) before the still. `fw` had been replaced by the region's list after the moveto.
