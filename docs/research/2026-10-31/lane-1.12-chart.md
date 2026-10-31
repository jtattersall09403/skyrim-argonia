# Lane 1.12-chart: the chart and the minimap (1.12 §5)

Test levels: L2 rules (skse/core), L3 stills (tools/ui_harness), L4 owed (tests/journeys/chart-minimap.yaml, the coordinator's batch).

## What was built
- **Art:** confirmed it is the old project's chart treatment. tools/chart/render.py re-renders that look over our own data (the owner ruled on it 2026-10-29; the glyphs are the old map's own art, glyphs-SOURCE.md). The revealed layer no longer draws any place except the seven cities, so the paper never shows a place before it is discovered. Sample hash re-pinned to 94f1fa8c…
- **Zoom:** zoom 1 now fits the whole sheet (contain, not cover), so the province shows top to bottom with nothing cut off (owner play test 1 item 9). The maximum zoom went from 16 to 24. Zooming in goes to the player (geom.ts `toward`).
- **Player marker:** chart.state v2 adds `player {x, y, heading}`. The native side reads the player reference's position and angle in ARG_Province; the cell units come from `gen::units::cell_units`, a new line in the units module.
- **Place markers:** chart.state places are only the discovered ones. Mechanism: Skyrim's own map-marker discovery, read from the CanTravelTo flag on the engine's `PlayerCharacter::currentMapMarkers` (the flag is set by discovery and kept in Skyrim's save, so no new state). `LocationDiscovery` events refresh the minimap. Rules (`chart::marker_discovered`, `marker_kind`) are in skse/core.
- **Reveal:** the existing CHRT co-save family, which marks cells on BGSActorCellEvent and holds after save/load (1.2 §e). The minimap reads `chart::near` (reach 5 cells).
- **No fast travel:** `Game.EnableFastTravel(false)` is dispatched natively at every load and new game (views.cpp FastTravelOff). Places on the chart are not travel buttons.
- **Minimap:** new push `hud.minimap`, sent on a move of 0.05 cell, a turn of 2°, a discovery or a cell change. A heading-up parchment disc sits top right in the frame trim, with the player's arrow and a compass rose turned by -heading. The effects stack moved below it, clear of the bottom corners.
- **Coordinator's item:** our HUD (minimap included) hides while `WindUIMenu` is open (router::kWindowsOverHud → covers_hud, SheetOpen) and shows again on close.
- **Window:** the chart is our own window in the frame style, using the --frame-* tokens.

## Evidence
- `make skse`: 33/33. `make ui`: green. `make check`: all green except `budget` (CLAUDE.md is 1134 words; that file is not mine and the check was already failing). Unit time was 255 s on a busy box.
- `python -m tools.ui_harness`: 156 stills, 0 fails, under out/ui/stills/ (gitignored; rebuild with `make chart && make ui-stills`):
  - chart/whole@{1080p,720p,v5-folded,v5-unfolded}.png: full zoom-out, uncut, with the player marker
  - chart/walked@*.png: zoomed to the player before discovery, revealed walk, no marker
  - chart/claywater@*.png: the same after discovery, with the marker
  - chart/unexplored@*.png: nothing revealed
  - hud/minimap0@*.png and hud/minimap135@*.png: the minimap with its rose at two headings
- out/chart was re-rendered in the worktree (not the main checkout); the main checkout needs `make chart`.

## Not done here
- ArgoniaCore (views.cpp) is not compiled on Linux. The CommonLib APIs used are `GetPlayerRuntimeData().currentMapMarkers`, `ExtraMapMarker`, `LocationDiscovery::GetEventSource`, `DispatchStaticCall`. They need the game machine's build.
- The plugin places no map markers yet, so the "marked after discovery" journey step is owed to the world track.
- Paths edited outside the brief: tools/argonia_world/core_tables.py (one units line), tools/ui_harness/{build,harness,chart_fixture}.py, ui/fixtures/{chart,hud}.json, skse/core router (the WindUIMenu rule).
