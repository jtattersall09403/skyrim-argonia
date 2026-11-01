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

## Starting state
- Done: schema (`weather_colour`, `weather_sky`, `mist_regime`, `mist_regime_season`, tint CHECK, fog_tint dropped),
  rows via `migrate.py --weathers-1-15`, api.py, season.py tables, CS override, panel table; session 2 applied the
  Skyrim.esm audit (§7): fog inside vanilla's ranges, lists of 6 summing to 100 per season, marsh fog 28–35 %,
  hour gate and its C++ removed. Measured: `make world` green (weather-slots 0, image-tint 0, region-weather 0);
  regions pytest 18 passed; skse/check.sh 36/36.
- Owed: `make plugin` to allocate the six new WTHR and four IMGS form ids (the WChance globals for the mist weathers
  are new names too); the L4 dawn and noon stills (`panel_weather`); tuning of colours and CS numbers from them.
