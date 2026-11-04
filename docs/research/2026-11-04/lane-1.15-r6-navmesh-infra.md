# Lane 1.15-r6-navmesh-infra: the route infrastructure's collision in the navmesh

- `tools/navmesh/placed.py` now also reads the WRLD override's `persistentRefs` (gates, landings, the three bridges; routes/infra.py), and takes a base's mesh from the intermediate's own STAT/ACTI record (the gate, signs) or from its plugin (the KotM bridge).
- Test: `test_placed_collects_infrastructure_persistent_refs`; navmesh tests 21 green, ruff clean.
- Real data (collector only, no navmesh run): refs 1293, 17260 triangles; each of the three bridges adds 692 deck triangles at its position, deck top +47 u over the ref origin (0.67 m, as the lane-bridges OBND).
- The 4-cell sample (0,0,1,1) holds no bridge or other infra ref, so the sample hash and sample-manifest.json are unchanged (not re-pinned). The bridge cells (-35,12), (-31,17), (33,39) are proved by the province navmesh (r6-land3).
- 509 refs have no base mesh (map markers, border walls): counted `no_base`, as before for markers.
