# Lane 1.15-r4-light: the sky-blocking fog and the low mist (round 4)

Owner play test 3, findings 18 and 9: "can't see the sky... too much of the bad kind, not enough of the good kind
(low-lying, below eye level, drifting volumetric mist)". Proven at L1. The in-game proof is owed (ledger row below).

## Measured first (0034)

Skyrim.esm WTHR records (`tools/argonia_world/vanilla/measure.py` q7, re-run 2026-11-02):

| class (n) | fog far day p50 | fog far night p50 | fog day max p10/p50/p90 | zenith (skyUpper) min spread p10 |
|---|---|---|---|---|
| pleasant (36) | 85,000 | 50,000 | 0.8 / 0.9 / 0.9 | 9 |
| cloudy (16) | 30,000 | 30,000 | 0.9 / 0.9 / 1.0 | 11 |
| rain (12) | 20,000 | 15,000 | 0.9 / 0.9 / 1.0 | 8.6 |

Named weathers: SkyrimFog 0/25,000/0/15,000 u at max 0.95, FogMA 50,000/35,000 at 0.95, StormRain max 0.92, Clear
max 0.85. No vanilla weather in a region list uses fog max 1.0: only the 16 unclassified effect weathers do.
Play camera: the human skeleton's `Camera3rd [Cam3]` node is 121.0 u above the feet (NPCEyeBone 124.1), read from
skeleton.nif in Skyrim - Meshes0.bsa. It is now `skyrim_units.EYE_HEIGHT_UNITS`.

## Causes

1. Fog max 1.0 on mist, sea-fog, squall and storm (`regions/weather_seed.py` SKY, lines 73–85 before this lane).
   At fog max 1.0 the sky dome beyond the fog's far distance is pure fog colour, so the sky disappears. Vanilla caps
   region weathers at 0.95.
2. Fog far below the class median. Mist's night far was 215 m (15,050 u) and sea fog's was 300 m (21,000 u), against
   a cloudy median of 30,000 u. Clear-dry's night far was 49,000 u, below the pleasant median of 50,000 u. Mist's
   near was 0, so its fog started at the eye (`weather_seed.py:49,52,41`). The old check (`checks.py:245`) held
   only vanilla's p10–p90 band plus SkyrimFog's floor, so the thickest legal fog passed.
3. Grey zeniths: monsoon-overcast's sunset skyUpper was 6B6A6A (spread 1), and storm, wet-rain, mist and sea fog
   were all below vanilla's p10 spread at some hour. The grey zenith reads as fog even where the fog is thin.
4. The Community Shaders height fog was laid as a slab, not a bank (`data/dependencies.json`,
   Argonia_ExponentialHeightFog.json). In ExponentialHeightFog.hlsli, density is fogDensity/1000 ·
   2^(−falloff/1000 · (z − fogHeight)). With fogHeight 350 (5 m above sea), falloff 0.35 and density 0.012, the
   fog was full density up to 5 m and halved only every 2,860 u. That made a faint, uniform haze that included
   the eye at every lowland place: no visible bank, and the view still went flat. (In round 3 the feature was not
   loaded at all; lane-1.15-r3-machine §3.)

## What changed

- Weathers (records, not shaders; still authored, no colour ladder): mist near is now 2/2 m and its night far
  430 m; sea fog's night far is 430 m; clear-dry's night far is 714 m; fog max is 0.95 on mist, sea-fog, squall and
  storm. Five skyUpper values were re-authored with the same hue and luma and more spread. The world DB was
  re-seeded (`regions.migrate --weathers-1-15`).
- `skyrim_units`: FOG_MEDIAN_U, FOG_MAX_CAP 0.95, SKY_CHROMA_MIN, EYE_HEIGHT_UNITS (all measured).
- `checks.fog_outside_vanilla` now also fails a far distance below the class median and a near distance of 0.
  The new `checks.sky_blocked` (wired into weather-slots) fails fog max above 0.95 and a grey zenith. The DB gate
  enforces both.
- Height fog: fogHeight 0 (sea level), falloff 30, density 0.5, volumetric on (distance 20,000 u). The bank's top,
  where density is 1/10, is at 111 u. On the flattest panel ground (0.3 m = 21 u above sea-level water) the eye is
  at 142 u, so the top lies below the eye. Looking upward the column's optical depth is about 0.001, so the sky
  stays clear.
- Tests (`regions/tests/test_regions.py`): `test_no_weather_hides_the_sky` (every weather; the old mist and grey
  dusk fail) and `test_height_fog_lies_below_the_eye` (it parses the file the stack lays).

## Before / after (fog in thousands of units)

| weather | class | day near/far | night near/far | fog max | zenith min spread |
|---|---|---|---|---|---|
| clear-dry | Pleasant | 1.1/98.0 → 1.1/98.0 | 0.4/49.0 → 0.4/50.0 | 0.55 → 0.55 | 19 → 19 |
| monsoon-overcast | Cloudy | 1.1/49.0 → 1.1/49.0 | 0.7/33.6 → 0.7/33.6 | 0.8 → 0.8 | 1 → 15 |
| wet-rain | Rainy | 1.1/28.0 → 1.1/28.0 | 0.7/19.6 → 0.7/19.6 | 0.95 → 0.95 | 4 → 10 |
| mist | Cloudy | 0.0/49.0 → 0.1/49.0 | 0.0/15.1 → 0.1/30.1 | 1.0 → 0.95 | 7 → 11 |
| sea-fog | Cloudy | 0.3/31.5 → 0.3/31.5 | 0.1/21.0 → 0.1/30.1 | 1.0 → 0.95 | 9 → 12 |
| montane-haze | Cloudy | 1.1/49.0 → 1.1/49.0 | 0.7/33.6 → 0.7/33.6 | 0.85 → 0.85 | 19 → 19 |
| tannin-haze | Cloudy | 1.1/49.0 → 1.1/49.0 | 0.7/33.6 → 0.7/33.6 | 0.8 → 0.8 | 11 → 11 |
| squall | Rainy | 0.7/31.5 → 0.7/31.5 | 0.4/19.6 → 0.4/19.6 | 1.0 → 0.95 | 10 → 10 |
| storm | Rainy | 0.6/26.6 → 0.6/26.6 | 0.4/17.5 → 0.4/17.5 | 1.0 → 0.95 | 4 → 10 |
| CS height fog | — | fogHeight 350 u, falloff 0.35, density 0.012: top (1/10) ≈ 9,840 u | → fogHeight 0, falloff 30, density 0.5: top 111 u (eye 142 u) | volumetric on → on | — |

## Limits, for the planner

- The CS height fog height is an absolute Z, set once. It sits on the sea-level lowland (coast, delta, lagoon).
  Inland shores stand 5–57 m up (panel: interior-swamp 5 m, deep-sink 11 m, rootland 17 m, western-frontier 57 m),
  and there it is effectively absent. CS 1.9.1 registers per-weather height-fog variables
  (`ExponentialHeightFog::RegisterWeatherVariables` and `WeatherManager::LoadPerWeatherSettingsFromDisk` in
  CommunityShaders.dll). A follow-up could give the mist weathers their own density, which would make
  region_mist decide where the bank is dense. Its file format still needs reading from the CS source.
- "Drifting": CS's Exponential Height Fog has no wind or noise term. Its settings list
  (`feature.exp_height_fog.*`) has none, and the volumetric part is homogeneous apart from temporal jitter. A
  drifting bank would need another mod. That is not done here.
- The density of 0.5 is computed, not seen. The dawn panel judges it.

## Owed in game

Ledger row: docs/phases/1-core-loop/checks.md, "Sky visible and low mist banks" (owed). The planner's round-4 batch
runs the dawn steps of tests/journeys/world-panel.yaml (already written), and a reader judges "sky visible" and "low
mist banks present below eye level" at each dawn still.

## Per-weather height fog: the water-level bands (planner's decision, round 4)

**Format** (CS v1.9.1 source on GitHub, tag v1.9.1: `src/WeatherManager.cpp:50-93`, `src/Utils/Form.cpp:23,117`,
`src/Features/ExponentialHeightFog.cpp:605-660`, `src/WeatherVariableRegistry.h:129-170`). There is one file per weather,
`SKSE/Plugins/CommunityShaders/Weathers/0x<local FormID>~<plugin>.json`, whose body is `{"featureSettings":
{"ExponentialHeightFog": {...}}}`. A value the weather leaves out falls back to the global setting, values are lerped
across a weather transition, and nothing clamps a value on load.

**Falloff within the menu's 2.0 cap: not possible.** At falloff 2, density halves every 500 u (7 m), so the bank's top
(a tenth of its density) is 1,661 u (24 m) above fogHeight. That is a slab the player stands in at any density, never a
bank below the eye. Each mist weather's own file therefore carries falloff 30 and density 0.5 as well as its height,
so those weathers keep their bank even if someone moves the global slider. The global file is also still 30.

**What was built:**
- A new table `weather_mist_band` (`world/schema.sql`).
- `regions/migrate.py` gained `region_water_m` and `mist_bands`. They take the median `cell_water` level per region,
  sort the regions of each regime by it, and close a band when it would span more than 1.6 m. The lowest band keeps
  the regime's weather; every other band is a copy (the same colours, sky and fog distances, a new EditorID). Each
  region's list swaps in its band's copy, keeping the parent's chance and season global.
- The fog height is the middle of the heights that keep the bank top (fogHeight + 110.7 u) between the band's highest
  water and its lowest water + 121 u.
- `regions/api.py` gained `cs_fog_files` and `sync_cs_fog` (`python3 -m tools.argonia_world.regions.api cs-fog
  --write`). They write the ten files into community-shaders' `files` in `data/dependencies.json`, and the stack lays
  them.
- `checks.py` now treats a band copy as its regime's mist weather, and `panel_weather.py` makes the dawn draw the
  region's own band.
- The FormIDs of the seven copies were allocated (`world/db/formid.jsonl`).

| weather | regime | regions | water (m) | fogHeight (u) | bank top (u) |
|---|---|---|---|---|---|
| sea-fog | sea_fog | 13 | 0.0 | −50.2 | 60.5 |
| mist | radiation | 20 | 0.0–1.37 | −2.3 | 108.4 |
| mist-2m | radiation | 4 | 2.2–2.46 | 112.9 | 223.6 |
| mist-6m | radiation | 2 | 5.7–5.9 | 355.9 | 466.6 |
| mist-20m | radiation | 1 | 20.21 | 1,365.1 | 1,475.8 |
| mist-25m | radiation | 1 | 25.33 | 1,723.6 | 1,834.3 |
| mist-49m | radiation | 1 | 49.48 | 3,414.9 | 3,525.6 |
| montane-haze | montane | 3 | 0.0 | −50.2 | 60.5 |
| montane-haze-11m | montane | 1 | 11.0 | 720.1 | 830.8 |
| montane-haze-68m | montane | 1 | 68.02 | 4,713.2 | 4,823.9 |

That is seven copies, not the six priced: the 20.2 m and 25.3 m regions are 5.1 m apart, so they cannot share one
height. The test `test_every_mist_region_has_a_bank_between_its_water_and_eye` checks all 47 regions with a mist
regime (the bank top lies between the region's median water and its eye) and checks that the laid files match the
bands. A region's own water varies around its median, so the dawn stills judge the off-median shores.
