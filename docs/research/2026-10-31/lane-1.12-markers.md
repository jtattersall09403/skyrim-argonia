# Lane 1.12-markers: the province's map markers

Ledger row (1.12): "A place's marker is absent before its discovery and shown after; no fast travel from the map".

## What was built
- `tools/argonia_world/map_markers.py`: one persistent REFR per place with a placed position (`place.position_m_x/y`
  not null): base `skyrim_units.MAP_MARKER` (000010:Skyrim.esm), z on the final ground (`GameGround`), XMRK
  `{name: place.name, type: by classification, flags: []}` (neither Visible nor CanTravelTo: hidden until Skyrim's
  discovery). EditorID `ARG_MapMarker_<Name>` (e.g. `ARG_MapMarker_ClaywaterStation`); a name two regions share
  carries its region (`ARG_MapMarker_HistHeartland_MarshGiantGroundBasin`). FormIDs allocated append-only.
- They ride in the WRLD override's persistent cell (`regions/api.py` `persistentRefs`, beside the gates and
  landings); `tools/ArgoniaGen/RegionWeather.cs` writes the `mapMarker` block (Mutagen `MapMarker.MarkerType`,
  `MapMarker.Flag`). They are in **Argonia.esm** (the place-reference plugin), not ArgoniaWorld.esm (terrain only).
- Type mapping (class/family): major-city City, mixed-settlement Town, other settlement Settlement, lair Cave
  (hazard-ground Clearing, open-water Landmark), camp Camp, sacred Shrine (hist Grove), martial and imperial-ruin
  Fort, lone-dwelling Shack, landing Docks, road/elevated Pass, extraction Mine, aquaculture Farm, festivity
  Clearing, else Landmark. No Nordic/civil-war type is used.
- The "no marker shown before it is reached" rule: `quest_gen.check_records` now also reads a record's
  `persistentRefs`; `check_yaml`'s regex (catastrophic backtracking on the 16.5k-line WRLD YAML with 567 blocks: it
  hung) replaced by a linear indent-block scan (`_yaml_marker_shown`).

## Measured
- Mutagen parse of out/Argonia.esm: **567 map markers, 0 with any flag**; 567 placed places; join by EditorID and
  name: 0 orphan markers, 0 unmarked places, 0 name mismatches. Claywater: `ARG_MapMarker_ClaywaterStation`,
  "Claywater Station", Settlement, at (-232873.56, 47914.31, 2621.47).
- Types: Landmark 180, Settlement 71, Cave 59, Camp 49, Shrine 47, Fort 46, Clearing 20, Pass 19, Town 16, Shack 14,
  Grove 13, Mine 10, Docks 10, City 8, Farm 5.
- `check_yaml(plugin/Argonia)` = [] in 3.9 s. tests: test_map_markers 6 passed, test_quest_gen passed.
- `make check`: every part green but `world`, red on world-reads for three perk_text mentions from c18f7d6
  (intermediate.py:289, test_perk_text.py:1, perk_extract.py:5): another lane's, not touched here.

## For the coordinator's L4 (tests/journeys/chart-minimap.yaml, step place-marked-after-discovery)
- Expect the marker `ARG_MapMarker_ClaywaterStation` (name "Claywater Station"); after reaching it, "chart places 1"
  and the log "chart: discovered Claywater Station in ARG_Province".
- No XRDS radius is set, so the engine's default discovery distance applies (not measured here; read it in game).
  `bat claywater` may already stand inside that radius, so "chart places 0" at arrival may flip at once: if so,
  the arrival point must be moved out, or the step order reconsidered.
- Owed: the `owed:` line of that step can be replaced by its expectations.
