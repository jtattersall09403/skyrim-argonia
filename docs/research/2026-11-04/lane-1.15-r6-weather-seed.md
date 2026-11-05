# lane 1.15-r6-weather-seed: the seed level with the database
- Diff method: copied world/ to a temp root, ran `weathers_1_15` in memory, compared every weather table row by row. Only `weather_colour` differed (21 rows each side); weather, weather_sky, image_space, realisation, region lists, mist and climate were already equal.
- Folded into weather_seed.py: tannin-haze horizon/fogNear/fogFar now the grey-brown DB values (all four times of day); monsoon-overcast fogFar sunrise 807E6F; montane-haze fogFar day 8A9490 (the 68 m copy follows); clear-dry fogNear day 7B9498, horizon day C7D6CB, fogFar sunrise 8C755B.
- One DB value moved by 1 unit: clear-dry (and the neutral twin) fogFar sunrise 8C755A to 8C755B, because 8C755A read as a derived mix and failed test_regions' no-derived-colour test; the seed and DB agree on 8C755B. Form ids untouched.
- The seed also carries the uncommitted clear-dry-neutral twin and image space day-neutral (770331cb, grade-ab lane); their DB rows (weather, weather_colour, weather_sky, image_space jsonl) are committed with it so HEAD stays consistent.
- Test: regions/tests/test_weather_seed_reproduces.py seeds a temp copy of the DB and compares 11 tables row by row. Result: it, all 33 regions tests, `db check` and ruff are green.
- A full `migrate --weathers-1-15` on the real DB now needs no 11-slot-error workaround; its output equals the DB.
