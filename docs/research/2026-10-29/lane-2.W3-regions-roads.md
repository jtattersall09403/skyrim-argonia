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
