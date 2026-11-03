# Lane 1.15-r4-fog-bank (round 4): the height-fog bank and the mist fog colours

## What was wrong
- The bank was a slab: `HEIGHT_FOG` (tools/argonia_world/regions/weather_seed.py) laid fogDensity 0.5, 100x the feature's default 0.005. The CS integral (ExponentialHeightFog.hlsli, 1.9.1) is 2^(-density/1000 x path); even at a tenth of the bank's density (the eye, by the band heights), a level ray over the mist weathers' 49,021 u day fog far was 1 - 2^(-2.45) = 82 % fogged: the uniform fog hiding the sky and the white horizon of batch two. startDistance 0 fogged the ground at the feet.
- The mist weathers' fog was olive: mist fogNear@day 92968F (hue 94), fogFar@sunrise/sunset 8F887F/958976 (hue 34-37), sea-fog and montane-haze sunrise/sunset fog hue 27-75; montane-haze and sea-fog fog far at noon within 4 % and 8 % of the horizon's luma.

## The feature's documented ranges (CS v1.9.1 src/Features/ExponentialHeightFog.h/.cpp)
Defaults: fogDensity 0.005, fogHeightFalloff 0.2, startDistance 0, fogHeight 0. Sliders: density 0-1, falloff 0.001-2.0, startDistance 0-100000, fogHeight +-22000.

## What changed (before -> after, why)
- fogDensity 0.5 -> 0.1 (in range): eye-level ray over the fog far 82 % -> 29 % fogged (bound a third); inside the bank light halves every 10,000 u (143 m): drifts, not a wall.
- startDistance 0 -> 700 u (10 m, in range): the near ground clear.
- fogHeightFalloff 30 kept, above the 2.0 cap: a tenth within one 121 u eye height needs >= 27.5; at 2.0 the tenth lies 1,661 u up. The slider only writes when dragged; each mist weather's file carries the value. Bank top (tenth) 111 u above fogHeight; the band heights keep it below every region's eye (the existing bank test).
- Laid: the global override and all 9 per-weather files (data/dependencies.json via `api cs-fog --write`).
- Fog colours (weather_seed.P and 42 weather_colour rows incl. band copies), sunrise/day/sunset/night:
  mist fogNear 818C8B/8A9996/879290/283533, fogFar 7F888A/BBC2BB/808987/27302C;
  sea-fog fogNear sunset 949C9C, fogFar 858C8F/AAB5BB/848A92 (noon gap 8 % -> 13.5 %);
  montane-haze fogNear sunset 8E9692, fogFar 818989/A3AFAB/838A8D (noon gap 4 % -> 11 %). Horizons and skies untouched.

## Checks added
- checks.py `mist_fog_cast` in weather-slots, for every mist-bearing weather: fogNear/fogFar hue 120-230 or saturation <= 0.04, every hour; noon horizon luma not within 10 % of fog far.
- test_regions.py: test_height_fog_laid_values_are_low_drifts_not_a_slab, test_mist_fog_cast_flags_the_olive_mist_and_white_horizon. make check-reach: 228 passed, 6 skipped.

## Every weather's horizon line (planner's follow-up)
`horizon_line` (checks.py, in weather-slots) holds for every weather at sunrise, noon and sunset (night exempt: at luma 20-50 a 10 % step cannot read white). Eleven fog far colours darkened to clear it (gap after): clear-dry day B0C4C6->A7BABB (13.3 %); monsoon-overcast day ABB4A2->9FA795 (11.9 %), sunset 99876F->8E7D66 (11.6 %); squall sunrise 5C6364->4C5251 (23.5 %), sunset 5D5A58->575452 (11.6 %); storm sunrise 56544A->515045 (11.7 %), day 62685A->5D6355 (12.7 %); tannin-haze day B8A88B->AFA083 (13.5 %); wet-rain sunrise 696C60->636659 (12.3 %), day 7C847C->727A71 (15.1 %), sunset 6E6357->665B4F (12.1 %). Horizons untouched; every new colour within vanilla's fog far luma band and derived from no other.

## Owed in game
checks.md row (1-core-loop, sky visible / soft low mist): the world panel's dawn and noon stills (tests/journeys/world-panel.yaml), reader: sky visible, soft low mist, no white horizon line, no yellow cast.
