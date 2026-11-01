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
  the per-state table to `weather_sky`. Fog near > 0 for all but the true mist (mist 0/150 m).
- Image spaces: 10, tint amount 0 (CHECK caps it at 0.03); saturation and contrast per weather with a why.

## Mist regimes (`region_mist`, 48 rows)
Rule (`migrate.regime_of`): mountains and hills >= half the cells -> montane; coastal group -> sea_fog; misty eco
class -> radiation; else none; border -> none. Result: radiation 29, sea_fog 13, montane 5, border none. No region
falls to none today (the north's transition is 70% mountains/hills).
Realised as one weather-list entry per region (`ARG_Weather_mist` / `_sea_fog` / `_montane_haze`) whose global
`ARG_WMist_<regime>` the SKSE rule sets to the season's chance inside the regime's hours (radiation 04–09, sea fog
03–11, montane 05–20) and 0 outside; `mist_regime`, `mist_regime_season` hold hours, chances and whys.

## Seasons
Kept the existing per-(group, weather) `ARG_WChance_*` globals rather than one `ARG_Season_*` per season: an RDWT
global *replaces* the entry's chance, so a 0/1 season global would flatten every chance to 1. Every entry carries
a global (418 entries). Check `region-weather`: each region's list differs in every season, nothing empty, every
season window >= 7 days (128/54/183).
L2: `skse/core` `mist_settings(Season, hour)` with tests in test_weather.cpp (in hours = chance, outside = 0,
radiation is a dawn regime peaking dry); adapter `ArgoniaCore/src/engine.cpp` SeasonCheck writes them (Windows
build not run here).

## Community Shaders (pinned 1.9.1)
Its Exponential Height Fog (v1.9.1 source, src/Features/ExponentialHeightFog.*) with volumetric fog. Laid by the
`files` entry on the community-shaders row of `data/dependencies.json`:
`SKSE/Plugins/CommunityShaders/Overrides/Argonia_ExponentialHeightFog.json` (enabled, volumetric on, vanilla fog
kept so per-weather WTHR distances rule, original fog colour 1.0 so the authored slots colour it, fogHeight 350
units, falloff 0.35, density 0.012). Per-weather CS settings exist (`CommunityShaders\Weathers\0x<local>~<plugin>.json`,
`featureSettings`) and are not used yet.

## Checks (all in `make world`)
`weather-slots` (0 derived; scaled copy along the same slot or same time of day, or a mix within a time of day, to
half a byte), `image-tint` (0 above 0.03), `region-weather` (as above). Measured: 0 / 0 / 0.

## What the panel's dawn stills must show
At 06:30 under the region's dawn weather (`python3 -m tools.argonia_world.regions.panel_weather`): radiation regions
a low milky mist over water, sea-fog regions a grey-white bank, montane a haze belt with clear summits; no
yellow-green screen tint; the noon still under the commonest clear without a tint wash. Also check CS's Overrides
tab lists Argonia_ExponentialHeightFog.

## Starting state
- Done: schema (`weather_colour`, `weather_sky`, `mist_regime`, `mist_regime_season`, tint CHECK, fog_tint dropped),
  rows via `migrate.py --weathers-1-15`, api.py, season.py tables, C++ rule and tests, CS override, panel table.
- Owed: `make plugin` to allocate the six new WTHR, four IMGS and three ARG_WMist GLOB form ids; the L4 dawn and
  noon stills; tuning of colours and CS numbers from those stills; the hourly mist only refreshes when ArgoniaCore's
  facts change (load, wait, sleep...), not on a game-hour tick — add an hour tick if the stills show it is late.
