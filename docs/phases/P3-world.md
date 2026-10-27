# P3: The Argonia worldspace

**Goal.** The whole province exists in game as a Skyrim worldspace generated from the imported data: terrain,
apron, sea, rivers and lakes, navmesh, LOD, regions and weather, roads and travel docks, vegetation, and the
places the old project had already built, walkable end to end with NPCs who can path.

**Starting state.** P2 exit gate passed: pipeline, bridge, installer, inventory v1. G4 and G7 proved terrain,
one place, navmesh, faces and stepped rivers on a sample block.

**Read first.** Decisions 0009, 0010; [audit-world](../research/2026-10-27/audit-world.md) §1, §3, §4;
[skyrim-tooling](../research/2026-10-27/skyrim-tooling.md) §1, §5; imported design docs: `docs/design/world/00-core.md`
(in full), `20-province-design.md`, `60-water-traversal.md`, `72-navigation-ai.md`, `97-placement-principles.md`,
`98-data-model.md`, old decisions 0015, 0047, 0049, 0058–0069, 0102, 0114, 0128, 0137, 0140 (via
[inherited-rulings.md](../inherited-rulings.md)).

**Fixed facts** (from the import; the units module owns them): province 7.37 km square, ~34 km² land, 4033²
samples at 1.828 m = 128 Skyrim units, so **126×126 exterior cells** of 4096 units (58.5 m) with 33×33
vertices; summit target 650 m; sea at 0; era 4E 201. The apron is the Transbot9 All-Tamriel heightmap at 1:1
beyond the border (old 0067; CC BY-NC 4.0, credited): the map ends 16.4 km N, 6.2 km S, 21.5 km W, 8.5 km E of
the border; the haze is opaque by about 10 km.

## Work packages

### WP3.1 Terrain
- Worldspace `ArgoniaWorld` (WRLD: no parent, own map data, default water height 0, land data, music type and
  climate set to ours, "no fast travel" handled by our system).
- All 126×126 cells' LAND from the frozen heightfield plus the old terrain and route-grade patches; VHGT
  quantisation (float offset + int8 deltas per row) re-based where a row's delta exceeds the int8 range; VNML
  computed; VCLR from wetness/soil tint.
- Land textures: map the old land-cover classes and ground-material system (old 0011; 40–60 texture library)
  to LTEX/TXST using sourced ground textures in the decision 0006 §8 order: Black Marsh mods (BM&V), then
  **Tropical Skyrim** (SSE 78044), then Aendemika if usable, and vanilla only where none has an equivalent. Max
  6 layers per quadrant: a per-quadrant layer reducer keeps the strongest; grass types attach to LTEX.
- **Acceptance (L1+L4):** sampled ground heights within 0.5 m of the heightfield at 1,000 random points (bridge
  `GetPositionZ` after placing a probe); no cell seams (height and normal continuity across every cell edge
  checked in data); a reader agent's look at 20 vantage screenshots finds no texture tiling artefacts flagged
  "obvious".

### WP3.2 Apron and edges
- Apron cells beyond the border from the Transbot9 map: coarse terrain (every Nth vertex meaningful, flat
  texture), mostly reached only as LOD; the sea covers it at 0.
- Closed playable edges: the border is closed except the canon exit roads (Blackwood Road, Tear road) which end
  at a gate or ferry with a "the road beyond is closed" message; physical blockers sourced from kit pieces
  (no invisible walls where avoidable).
- **Acceptance:** the player cannot leave the province (scenario walks to each border segment); views from the
  coast show the apron through haze, with no hard edge.

### WP3.3 Water (decision 0006/old 0047–0065; G7 method)
- Sea: the worldspace default water at 0. Coast and lagoon water classes as WATR types (salt vs fresh visuals).
- Lakes and flat river segments: cell water height where the whole cell's water is one level; else placed water
  planes.
- Rivers: 101 rivers, 615 reaches, 202 junctions from `hydrology-graph.json`: each reach becomes placed water
  plane segments stepped at the graph's grade, with a vanilla waterfall/rapids piece at each step (old 0064:
  waterfalls are the vanilla kit) and flow direction set where the water type supports it. 2,280 bodies are
  classified (sea, lagoon, lake, pond, river, rapids, falls, spring) into placement rules.
- The old project's "the water line is high water" (old 0063) holds: one static level per body. **Seasonal
  water levels (old 0049) are not modelled**: Skyrim water planes are static; flood seasons survive only as
  weather and text (decided here; noted in ACCOUNTING).
- Marsh mist, waterfall mist and cap clouds (old 0124, raymarched in three.js) become Community Shaders
  volumetric fog plus weather fog and placed mist emitters from vanilla/mod particle effects.
- **Acceptance:** a scenario swims the length of three sample rivers (one per class) without falling out of
  water; NPC swim paths work; screenshots at 30 river steps show no z-fighting; the hydrology graph's every body
  has a placed water record or a cell water height (data check).

### WP3.4 Navmesh
- Production version of the G4 converter for all exterior cells and every interior: walkable triangles from
  the generated terrain and placed collision (Recast on our geometry), door triangles linked to load doors,
  water triangles flagged, cross-cell edge links, NAVI master data, cover data where cheap.
- **Acceptance:** 200 random NPC path requests between reachable points succeed (bridge path query); 20 NPCs
  with sandbox packages do not stand still for more than 60 s in a 10-minute sim.

### WP3.5 Regions, climate, weather, sky, light
- REGN per catalogue region packet (8) and ecological class (tidal delta, coastal lagoon, deep river corridor,
  flooded forest, interior swamp, seasonal floodplain, rootland, northern transition, western frontier, deep
  sink basin, karst/root cavern belt); CLMT and WTHR from `climate/weather-states.json` (rain, storm, haze,
  mist, clear), sky and the star catalogue (13 Patrons, the Serpent) as far as Skyrim's sky allows; image spaces
  restyled to a humid green-gold marsh light (no Nordic blue-grey).
- Time scale 30 (one game hour per 2 real minutes) as the old design.
- **Acceptance:** every cell belongs to one region; weather cycles per region in a 7-day time-skip scenario;
  a reader panel judges 12 weather screenshots against the old weather references.

### WP3.6 Roads, routes, travel infrastructure
- The road network (old 0069: six legs and two exits; 0068 graded by patches; 0115 no crossings): road
  surfaces as land textures plus kit road pieces where the old layouts had them; bridges from kit pieces;
  signposts with sign text; harbour stations, ferry and rootworm stations as placed docks and NPC stations
  (travel dialogue is P4-WP4.13).
- Write the **route graph** used by the directions generator (P4-WP4.8): nodes (junctions, places, stations),
  edges (road legs with length and landmarks).
- **Acceptance:** a scenario walks each leg end to end on the road surface; the route graph's distances match the
  terrain within 5%.

### WP3.7 Vegetation
- Convert the flora and groundcover rules (old 0036, 0048, 0070, 0082) into: tree and shrub REFRs from
  BM&V and **Tropical Skyrim** (SSE 78044; the base-asset layer, decision 0006 §8; and Project Rainforest),
  grass through LTEX grass types using Tropical Skyrim's grass, rocks and debris REFRs; a vanilla tree, plant or
  rock is used only where neither has an equivalent.
- Density by region class with a performance budget per cell measured on the chosen GPU instance (draw calls
  and frame time), not guessed.
- **Acceptance:** frame time in the densest 10 cells stays within the G2 bar; reader panel on 20 vantage
  screenshots: no Nordic flora (pines, snow, heather) anywhere.

### WP3.8 LOD and the world map image
- xLODGen (terrain LOD) and DynDOLOD (object and tree LOD) under Wine with the documented Texconv workaround
  (plain Wine 9.22, retries); 32–64 GB RAM advised, so run on a temporary larger spot instance, costed first.
- A painted-look world map image rendered from our own heightfield, hydrology and land cover (the UI
  exception), consumed by the paper map in P4-WP4.9.
- **Acceptance:** distant views show terrain and tree LOD with no missing tiles; the LOD build is a scripted job.

### WP3.9 The already-built places
- Port the old layouts (`world/sources/blueprints/*.layout.json`, ~20 places: Greenspring, Helstrom (layout
  only), Chasepoint, Riverwalk, Claywater Station, Bog-Iron Workings, The Broke Column, Rose-Bone Waystation,
  Voriplasm Vault, The Wamasu Shrine, Teeth of Sithis, Lighter Flotilla, Pearl Lots, Jungle Root Hollow,
  Upriver Hist Village, Opening Work Camp, Naga Highway Camp and two routes) to REFRs; owner-accepted first
  (Broke Column, the two routes, Greenspring, Claywater Station).
- Each place carries its own ground (old 0102): its pad patches become terrain edits in its cells; interiors via
  the plugin load-door manifest (old 0114, `exterior-interior-links.json`, 38 kit interiors).
- Sockets (containers, beds, seats, stations, shrines, plants, moorings) become CONT/FURN/IDLM/FLOR/ACTI REFRs
  with owners (XOWN) and locks (XLOC) from the frozen loot and lock records.
- New skill `world-builder` (from the old `place` skill and place-builder agent): the recipe for porting and
  later building a place in Skyrim records, its checks and its walk packet.
- **Acceptance (L4 + L6):** each ported place passes its scenario (enter every building, every promised socket
  is usable, NPCs reach their spots); a P3 **walk packet**: the owner walks Greenspring and Claywater Station
  and one road leg through the stream and rules blocker/polish.

### WP3.10 Performance pass
- Measure frame time across a grid of 100 sampled cells on the chosen instance; fix the worst 10 (vegetation
  density, light counts, LOD settings).
- **Acceptance:** 95% of sampled cells hold ≥ 60 fps median at 1080p on the chosen instance.

## Exit gate
The province is walkable border to border; water, navmesh, LOD and weather pass their checks; the ported places
pass; performance bar met; the owner walk packet has no open blocker.

## Risks and fallbacks
- **Navmesh scale-up** breaks on cases the sample did not have (cliffs, docks, water): survey all failures
  first, fix in one batch; CK under Wine for residual cells.
- **Too many objects** for Skyrim's cell budgets in dense jungle: thin by region class; move density into grass
  and LOD.
- **A key asset mod refused (O-5)**: re-kit the affected places from cleared sources; record the substitution.

## Deliberately out of scope
New places beyond the ported ones (P9); NPC dialogue and quests (P4/P9); seasonal water (dropped above).
