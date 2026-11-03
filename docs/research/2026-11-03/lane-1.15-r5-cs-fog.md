# Lane 1.15-r5-cs-fog: Community Shaders height fog back to the feature's defaults

Evidence: the round-5 sky A/B on Paris. Shaders off: blue noon sky, clouds, soft horizon. Shaders on: flat grey-cyan veil, no clouds, hard white horizon, solid cream dawn. Same records. The r5-sky audit found one setting above its documented default: fog density 0.1 vs 0.005.

## Values, before and after (data/dependencies.json, community-shaders files)

| File | density | falloff | startDistance | fogHeight |
|---|---|---|---|---|
| Overrides/Argonia_ExponentialHeightFog.json (global) | 0.1 -> 0.005 | 30.0 -> 0.2 | 700 -> 0 | 0.0 -> 0.0 |
| Weathers/*.json, nine files (0x80F, 0xE9D, 0xE9E, 0xED4-0xEDA ~Argonia.esm) | 0.1 | 30.0 | 700 | -50.2 to 4713.2 (per band) |
| after: the nine files | removed; a weather with no file takes the global (CS 1.9.1 LoadPerWeatherSettingsFromDisk) | | | |

enabled, volumetric (distance 20000) and disableVanillaFog 0 are unchanged. The weather records' fog near/far colours and distances are untouched, as are the weather_mist_band rows (the records' per-band variants).

## Why round 4's bank was the veil

The bank maths bounded a level ray at the eye: density 0.1 x a tenth (the bank top is a tenth of full) over the 49,021 u day fog far = 29 % fogged. That held only at the eye and above the bank top. Density 0.1 is full strength at fogHeight and below (a ray along the ground: 1 - 2^(-0.1e-3 x 49021) = 97 % fogged), and the sky dome and far terrain lie beyond every fog distance, so the height fog's inscatter, volumetric and lit by the fog slots, washed over them. The grey-cyan veil, the missing clouds and the hard line where the dome meets the terrain's fogged ground match that. The 20x density and the falloff of 30 (15x the 2.0 slider cap) were the only settings out of range. At the defaults the same ray is 16 % fogged over the same distance and the density is the author's own.

## Test

tools/argonia_world/regions/tests/test_regions.py: test_height_fog_is_the_features_shipped_defaults (global file equals the defaults, inside slider ranges, no per-weather file, cs_fog_files empty) and test_no_mist_weather_file_is_laid_and_sync_is_in_step. Removed as moot: test_height_fog_lies_below_the_eye, test_every_mist_region_has_a_bank_between_its_water_and_eye, test_height_fog_laid_values_are_low_drifts_not_a_slab. make check-reach: green (4 files).

## Owed in game

checks.md row: the sky-ab journey with shaders on, a reader looking for a blue zenith, clouds visible, no hard horizon line, no cream wash at dawn. If the low mist is then too thin, it is the records' fog near/far (weather_seed) to change, not the shader.
