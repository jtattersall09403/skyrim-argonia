# Lane fixes-1: the world map, the menu lag, the crocodile (2026-10-30; hand-off after the 08:20 spot reclaim)

## 1. The world map: FWMF shows our chart (Nordic blocker from game-8)
- `flat-world-map` (Nexus 29932, 1.9.990) now lays (its `from: 2.12` removed); permission recorded as the owner's
  (2026-10-30) in data/dependencies.json and data/sourcing-register.json.
- How FWMF works (measured from its files): its Tamriel `tamriel.32.0.0.btr` holds a 4-vertex paper quad
  (+-400,000 units, node scale 0.655, z 180,000, texture `skyrim.dds` = Aesoterik's Skyrim map), a background quad
  (z 162,000, `back.dds`) and Tamriel's own land/water chunk; its plugin sets Tamriel's map camera to
  269,488-435,000 units at pitch 90 and ONAM z 184,072.97; Flat Map Markers whitelists worldspaces at height 180,000.
- `tools/chart/fwmf.py` (`python -m tools.chart fwmf --fwmf <mods>/flat-world-map --out <mods>/argonia-map`), made
  at install (installer/steps/world-map.md): our `arg_province.32.0.0.btr` derived from the player's FWMF block
  (paper re-centred at 4096,4096 and scaled to the chart's 262,144-unit half side, both quads retargeted to our
  textures, 3 Tamriel shapes hidden; a changed FWMF stops the install), `argonia-chart.dds` (sketch layer, 4096 px
  DXT1, north up), our `back.dds`, `FlatMapMarkersSSE.json` (ARG_Province only). Built on the VM into
  out/argonia_map/argonia-map: block 710,800 bytes, verify ok. stack.py stages it above the LOD as `argonia-map`.
- Argonia.esm's WRLD override now carries FWMF's camera and ONAM (read back: MNAM 269488/435000/90, ONAM z 184072.97;
  LandWorld.cs takes an optional `mapOffset`).
- L1/L2: tools/chart/tests/test_fwmf.py (4: retarget and hide on a synthetic FWMF-shaped block, a changed FWMF
  stops, the chart extent, the whitelist). Owed L4: open the Map in an Argonia scene.
- Needs on the game machine: stack restage (FWMF fetched from cache) and xLODGen's terrain LOD for ARG_Province
  (the map loads the level-32 blocks; ours replaces 0,0).

## 2. Menu lag: the suspend save no longer fires on a menu opening
- Cause: LifeMenuSink saved on Tween/Journal open (`SuspendWhy::pause_hub`); the save's spinner closed the Journal.
- Rule (skse/core life): `pause_hub` removed; the interval save never runs with a menu open (`suspend_due(...,
  menu_open)`); `QuitWatch::on_menu(opening, quit_requested)` returns `quit` once, on the first menu close after the
  engine's quit/reset flag is set (the player confirmed Quit), never on an opening. Stream drop stays the bridge call.
- Adapter: menu events feed QuitWatch with `Main::quitGame || resetGame`; the quit save is written synchronously
  on the main thread (before the reset); interval checks `UI::GameIsPaused()`.
- L2: test_life (the old pause-hub asserts replaced; QuitWatch sequence); ctest 30/30; MSVC windows-dev OK
  (ArgoniaCore.dll 1,491,968 bytes). tests/journeys/suspend-save.yaml updated. Owed L4: menus open without lag;
  quit from the Journal writes ArgoniaSuspend (unknown: whether the flag is set by the confirmation's close).

## 3. The crocodile: its den off the pool
- Measured on our navmesh and ground (out/navmesh/province): the den (the clay-cut lip) stood 8 units above the
  pool's water; its 20 m sandbox was 523/1249 samples (42%) below water, the pool 2.86 m deep; bank-to-pool paths go
  12 m round (1203 u walked for 500 straight). So it swam in the pool, out of reach on foot.
- Data: a den marker owned by the crocodile (`ref.claywater-station.crocodile-den`, 282.5, 3061.5, z 33.62 m) on
  the bank 2.9 m south of the lip; the crocodile at 282.5, 3062.0; sandbox 2.5 m (LF83 <= 20 m); place_build takes a
  creature's den as the marker it owns (the LF83 hardcode gone). Pool and ford unchanged.
- Check: the circle is 7/1249 below water (max 0.15 m: a shallow lip); den and crocodile on the bank's navmesh;
  path from the journey's staging (croc - 200 y) to the den 2 tris, 213 u; from 10 m south 971 u.
  L1: tools/argonia_world/tests/test_creature_dens.py (old data fails it).
- Found, not fixed: exterior refs with no z sit on the 2.W1 ground before the river regrade (the clay-bend at 35.2 m
  over ground at 33.3 m); first-place's to-the-clay-cut teleport lands at the lip.

## Gate
- make plugin twice identical (Argonia.esm run 2 = run 3; run 1 differed by another lane's PerkRecords.cs edit
  mid-run); ArgoniaWorld.esm unchanged (400696...). make check died in the 08:20 reclaim; re-run after: pytest of
  the touched tests 20 passed, ctest 30/30. The full `make check` is owed by the next lane.
