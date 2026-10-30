# w3-weather-skip (draft, 2.W3 §a; owed L4)

**Checks:** every region's weather cycles over a 7-day time skip, and only from its own list (the REGN weather lists in
Argonia.esm over the shells' XCLR in ArgoniaWorld.esm).

- **Scene:** the base save, with ArgoniaWorld.esm and Argonia.esm loaded. Step 0 teleports (`cow ARG_Province x y`)
  to the centre cell of one region per weather group. Take the coastal, marsh, jungle, uplands and lowland regions
  with the most cells in `land_region`: five regions. Step 0 sets nothing about weather.
- **Per region:** wait 7 game days in 6-hour steps (`set GameHour`/`wait` through SkyLink, no `fw`). At each step
  read the current weather's FormID (`GetCurrentWeather`) and the cell's region list. Keep a still per step.
- **Pass:** at least 3 distinct weathers in 28 readings; every weather read is in that region's `land_region_weather`
  rows; the region read is the region `cell_region_run` puts the cell in.
- **Season:** repeat one marsh region with GameMonth set to 0 (dry) and 9 (wet), with the season rule applied by
  ArgoniaCore's `on_day` at the day change. Tannin haze shows only in the dry run.
- **Fails if:** a weather outside the list (vanilla's TamrielClimate fallback means XCLR or the WRLD climate is
  missing), the same weather all week, a crash.
- **Join:** the TimeScale override reads 30 (`GetGlobalValue TimeScale`).
