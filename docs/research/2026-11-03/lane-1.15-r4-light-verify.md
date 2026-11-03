# Lane 1.15-r4-light-verify

Cause: a mix. (1) Three panel vantages forced stale band weathers (deep-sink-basin-high ARG_Weather_mist vs
mist_49m; interior-swamp-shore mist vs mist_2m; western-frontier both montane_haze vs montane_haze_68m); fixed
in tests/journeys/world-panel.yaml, pinned by test_panel_journey_forces_each_regions_own_current_weather.
(2) The ten... nine CS per-weather fog files were laid and pushed: ~/.argonia/jobs/round-r4.log lines 46-54 wrote
the 5 overrides and 9 Weathers files (0x80F, 0xED4-8, 0xE9D, 0xEDA, 0xE9E); line 98 pushed community-shaders;
round-r4b pushed 0 changed (nothing new). The files in data/dependencies.json match cs_fog_files (cs-fog in step).
(3) Yellow-olive noon: clear-dry (the noon weather everywhere) day fogNear 8D9A7F, fogFar BCC4A5, horizon CDD2A5
(hue ~70 deg olive-yellow), fog day 15 m to 1400 m, power 1.2, max 0.55; skyLower/zenith were already blue.
Re-authored in world/db/weather_colour.jsonl: fogNear 7B9498, fogFar B0C4C6, horizon C7D6CB (weather-slots check green).
Owed in game: the panel's noon and dawn stills (checks.md row 142).
