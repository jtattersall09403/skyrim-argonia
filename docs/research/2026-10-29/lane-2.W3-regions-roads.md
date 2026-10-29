# Lane report: 2.W3 regions, weather, light, roads and the route graph (hand-off at the context mark)

## Hand-off

**Done (this commit):** the data side of §a and §b in the world database, through db.py.
- Schema: one appended block at the end of `world/schema.sql` ("Regions, weather, light, roads and the route graph"),
  27 tables.
- `tools/argonia_world/regions/`: `migrate.py` (weather-states, the authored override, the per-class role totals of
  flora/palettes.json; plus the 2.W3 seed), `cells.py` (per-cell fields), `classify.py` (cells -> regions, the weather
  and object lists, the L1 check), `vault.py` (fetches ground-control.png and the old route reports to `$ARGONIA_DATA/regions`).
- `tools/argonia_world/routes/build.py`: roads and tracks traced off their land-cover paint, the route graph, joins,
  landmarks, signposts, structure windows, and the L1 check.
- `docs/research/2026-10-29/interior-sun.md`: the findings.

**Measured (2026-10-29, build VM):**
- Cells: 15,876 province cells, each in exactly one region (`classify check`: 0 errors).
- REGN: 48 (47 packet x eco-class regions plus the border). 310 weather entries, 866 object entries, 34 object forms.
- Weather: 21 weathers (17 restyled by Tropical Skyrim, 4 of ours), 6 image spaces, 1 climate (time scale 30).
- Reconstructed raster class: 0.758 leave-one-out agreement against the 567 measured places, k=5. The old
  `hydro-regions.png` is not in the vault, so each cell's class is reconstructed.
- Route graph: 46 nodes in 1 component.
  - 23 traced land legs and 9 joins to the main network.
  - 11 routes skipped: their end names resolve to no place or station (listed by `build`).
  - Edge length vs the 3D length over the 2.W1 heights: worst 0.43%.
- Peak RSS: classify 302 MB, routes 323 MB, migrate 54 MB.

**Red / finding:** the old chain's own road lengths (`major-routes-report.json`) run 4–26% longer than the traced
legs (stormhold-thorn −25.6%).
- What was ruled out:
  - frame: the patch profile heights match ours to 0.01 m;
  - vertical exaggeration: k = 5 still falls short;
  - search margin;
  - simplification: a full-resolution trace adds only 3%.
- The paint itself is continuous for only 72% of the full-resolution path. Either the old geometry wandered where no
  paint was laid, or its chainage counts more than the ground.
- Next: decide which length is the truth. The old route-grade patch chainages (`source.fromM`) against ours are the
  instrument.

**Left, in order:**
1. ArgoniaGen writers `tools/ArgoniaGen/RegionWeather.cs` for REGN (incl. `border`, `areas` from 2.W1), CLMT, WTHR
   (duplicate the template, then set fog and image spaces) and IMGS. Register them with one line in `Generate.Run`'s
   switch.
2. `regions/api.py`, per the agreements with 2.W1:
   - `cell_region_keys(world, alloc)`;
   - `climate_form_key(alloc)`;
   - `layers(alloc, world)` returning REGN/CLMT/WTHR/IMGS plus a GLOB override of TimeScale 00003A:Skyrim.esm (value
     30) and the `ARG_WChance_*` season globals;
   - TYPE_ORDER lines plus one `build` line in `intermediate.py`.
3. `routes/paint.py override_classes(classes, r0, c0)`, in grid space g with PAD 2176, painting 30 and 29 from
   road/road_point.
4. Tests on small fixtures:
   - `migrate.rows_from`;
   - `classify.runs`, `majority`, `in_polygon`, `object_list`;
   - `routes.build.simplify`, `sub_polyline`, `components`, `join`.
5. Docks and exit gates:
   - the docks (travel_station pieces) are only nodes so far;
   - place the gate pieces at `route_node` `exit.*`, which sits where the road paint meets the edge.
6. Season-switch rule (ArgoniaCore): set the `ARG_WChance_*` globals from `season_factor`.
7. Draft L4 journeys `tests/journeys/w3-weather-skip.md`, `w3-weather-stills.md`, `w3-road-hops.md` and
   `w3-interior-sun.md` (the interior-sun check is specified in interior-sun.md). The journal comes after that.
8. Run text-review over the map names (owing_region.region_name) and the signpost arms (they read place names).
9. `make check`.

**Not yet measured:** RDOT density units against the CK generator (2.W4). Seasonal floodplain gets no cells (the
reconstruction never predicts it from 9 labels). The karst belt has no exterior REGN by design.

Interfaces agreed with 2.W1 (reply of 2026-10-29): XCLR from `cell_region_keys`; `override_classes` in
`terrain/build.py` after `src.classes()`; WRLD climate from `climate_form_key`; the border REGN (BorderRegion, the
province square from `terrain/edges.py border_polygon`) is written by 2.W3.

Rebuild: `~/.argonia/venv/bin/python3 -m tools.argonia_world.regions.vault`, then `regions.migrate --weather
--overrides --palettes` (source paths), `regions.classify build`, `routes.build build`.

## Continuation (2026-10-29, second agent): the records, the gates, the season rule, the gate green

Commits: 7e34247, 95069d6 and 0f360a3, plus the docs commit.

**1. Writers (Argonia.esm).** `tools/ArgoniaGen/RegionWeather.cs` writes REGN, CLMT, WTHR, IMGS and the WRLD
override, registered by one line in `Generate.Run`. The intermediate is `regions/api.py layers()`. Records written:
- 6 IMGS, 4 WTHR (ours), 1 CLMT;
- 33 GLOB: 32 `ARG_WChance_*` and the TimeScale override `00003A:Skyrim.esm`, which is a GlobalShort (measured), set
  to 30;
- 48 REGN: 47 overrides plus the border;
- the WRLD override, with the climate set.

The intermediate has 2,024 records. `generate` peaks at 152 MB and Spriggit's round trip is byte-identical.
- **Shell pattern** (found here; approved by the planner; 0031 gets a line):
  - ArgoniaWorld.esm's cells cannot link to Argonia.esm, their dependant, yet the engine reads a cell's regions from
    XCLR.
  - So ArgoniaWorld.esm holds 47 REGN shells (EditorID and worldspace). Their ids run from 0x080000, append-only in
    the formid table under that plugin; `formids check` now covers that plugin too.
  - LandWorld.cs writes the shells and each province cell's XCLR from world.json (`regions`, `cellRegions`).
  - Argonia.esm overrides each shell with areas (2,181 cell rectangles), the weather list, the object list and the
    map name.
  - The border REGN (BorderRegion flag, the province square, falloff 0) is wholly in Argonia.esm.
- **Weather values are ours** (decision 0003). Copying a vanilla or Tropical Skyrim WTHR would put their values in
  committed YAML.
  - Colours: our fog tint carried towards the image-space tints, then spread over the 17 colour slots × 4 times of
    day by a fixed ladder (`api.LADDER`). Directional ambient is derived from them.
  - From the template only references are taken: cloud texture paths (GivenPath), precipitation, the visual effect,
    sounds, sky statics, volumetric lighting, the aurora, the lens flare, LNAM, and the climate's sun textures and sky
    model.
  - The IMGS HDR values are ours too.
  - All of these are starting points for 4.6.
- Mutagen facts measured:
  - RDOT entries are 52 bytes, so `Unknown2` is 6 bytes; with 4, Spriggit's read fails.
  - WTHR `WindDirectionRange` is a fraction of a turn.
  - AssetLink must be built from `GivenPath`; `DataRelativePath` writes a `Textures/` prefix.
  - Spriggit needs no data folder for the new master.
- `.gitignore`'s `*.esm` ignored Spriggit's `ArgoniaWorld - 000800_ArgoniaWorld.esm/` record directory. It is
  re-included.

**2. api.py and intermediate.py.** intermediate.py gets the TYPE_ORDER line, the layers line and ArgoniaWorld.esm
appended to the load order. `wrld_record()` takes the cell range from the memory-mapped array shape alone.

**3. Road paint.** `routes/paint.py override_classes(classes, r0, c0)` is called in `terrain/build.py` after
`src.classes()`. It paints the 23 legs at half their flat width, roads over tracks, never over SEABED_SAND or
OCEAN_FLOOR. It changed 36,463 province samples and took 0.8 s for the whole province. The terrain stamp in
pipeline.py now hashes paint.py and the road rows. sample-manifest.json was regenerated deliberately (a0245b90).

**4. Tests.** regions/tests (9) and routes/tests (6) cover:
- `rows_from`, `runs`, `majority`, `in_polygon`, `vote`, `object_list`;
- `rectangles`, `area`, the weather colours;
- `simplify`, `sub_polyline`, `components`, `join`, the paint, the gate walk-back.

**5. Gates and docks.** `routes/infra.py` puts the gates 20 m inside the border on the traced road at `exit.*`:
Blackwood at cell -62,12 and Tear road at cell 47,63. This supersedes edges.py's provisional -62,11 and -12,63; the
2.W1 sample cell -12,63 is no longer the gate cell. The two piece-bearing ferry landings face their berth.
- They are written as persistent refs in the WRLD override's persistent cell, so no exterior CELL is overridden.
- The path was proved with an injected ref (generate, then Spriggit round trip byte-identical).
- **All 4 are pending:** `landing-argonian` and the gate piece do not resolve until the Black Marsh plugins sync.
- The gate's activator ("The road beyond is closed.") still needs its trigger: a message on contact, which is 2.W5's
  place machinery or a small ArgoniaCore rule. Owed.
- **Finding:** Tear Road Stage (the place) stands 3.4 km west of where the traced Tear road meets the border. The
  w3-road-hops still at that hop decides which of the two is off.

**6. Season rule.**
- `regions/season.py` generates `skse/core/generated/argonia/core/tables_weather.h`:
  - windows dry 0–127, hatching 128–181, wet 182–364 (SEASON_ORDER from day 0; a reversible choice, since the
    imported seasons have shares but no months);
  - 32 globals × 3 seasons, normalised per group (dry haze is 0 in the wet season).
- The skse/core `weather` module (`day_of_year`, `season_of`, `settings`, `on_day`) has test_weather; ctest passes
  17/17.
- skse/check.sh diffs the header. `skyrim_units.MONTH_DAYS` is new.
- The SKSE adapter that writes the globals at the day change is owed with ArgoniaCore's game side.

**7. Journeys.** `tests/journeys/w3-weather-skip.md`, `w3-weather-stills.md`, `w3-road-hops.md` and
`w3-interior-sun.md`.

**8. Text review.** One reader pass over the 8 map names, 16 signposts and the gate message: no hard defects. It
first exposed a real defect: arms read junction ids and repeated destinations. The arms now name the first place
beyond any junction, one per destination. Exit nodes carry the city beyond (`route_node.name`: Leyawiin, Tear).
The reader doubted some canon names (Dead-Water, Middle Argonia, Oliis Bay, Bogmother, Gang Ground); they are left
as the rows hold them.

**9. Gate.** `make check` reports CHECK GREEN (1:17 wall, 532 MB peak), and the plugin part reports "regenerate
twice identical; plugin/ current; round trip byte-identical; sample hash as the manifest". `make plugin` peaks at
1.09 GB (the terrain rebuild) and takes 3:49. Ruff style findings remain in the first agent's regions/routes files;
they do not gate.

### The open finding: the old roads' extra length (measured, 25 minutes)

- **Instrument.** The old route-structure placements carry both an old chainage (`fromM`) and a position. Projected
  onto our traced legs, most sit within 20 m of our line, so the two roads pass the same ground points.
- **Between consecutive on-line placements** (15 pairs over 5 roads), the old chainage totals 8,116 m against our
  6,310 m: **1.286×**. That is local, not uniform.
  - On stormhold-thorn, the old 1,975 m between two shared points is 1,245 m on ours.
  - On thorn-tear, the old 86 m is 31 m on ours.
  - Its last 4 old placements (old chainage 7,844–8,195) sit 95–139 m off our line, where the old road went round
    and ours runs straight to the end.
- **Mechanism.** The old roads were graded to an 8° cap (`route-grading-stretches.json` capDeg 8). A path held to
  8° over our heights between the same points comes out 1.200× ours. So most of the excess is the old road
  detouring and switchbacking round steep ground. Our trace follows the paint's straighter line.
- **Consequence.** 8.6% of our BC_ROAD 10 m steps (280 of 3,254) are steeper than 8°. stormhold-thorn has 1.17 km of
  them, gideon-blackwood 0.41 km, gideon-stormhold 0.40 km.
- **Recommendation.**
  - Keep our lengths as the route graph's truth: they are the ground the player walks, within 0.43% of the terrain.
  - Treat the steep stretches as the defect. Add a slope term to the trace cost in `routes/build.py` (a cost above
    8°, so the search takes the old grade line where the paint allows), then re-measure the 8° share and the old-vs-
    ours ratio.
  - Tag it `P1 before-scale`: it touches navmesh slopes (2.W4) and NPC travel times (2.12). It is not blocking.

### Owed
- L4: the four w3 journeys.
- The gate trigger, the gate pieces and the landing pieces (after the dependency sync).
- The season adapter (SKSE).
- The RDOT density unit (2.W4).
- The slope-cost re-trace above.
- The Tear Road Stage position check.
