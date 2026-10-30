# Journal: the vegetation (chunk 2.W4 §a)

What was tried, measured and learned for `tools/argonia_world/vegetation/` and the vegetation in ArgoniaWorld.esm, so
nothing is lost at a hand-off. The lane report is `docs/research/2026-10-30/lane-2.W4-veg.md`.

## 2026-10-30: our own placement from the region rules (lane 2.W4-veg)

- **Why not the CK.** The Creation Kit is not on the game machine (owner issue #15), so 0.4's fallback applies:
  our own placement from the same region rules, writing the same REFRs. The rules stay the data
  (`land_region_object`, 866 rows over 34 forms). When the CK arrives, a reader compares the two on stills and the
  better one wins.
- **The method** (`place.py`): seeded per cell and form; a jittered grid of clump centres at the row's density
  (stems per hectare x 0.342 ha a cell, exact in expectation; L1 within 6% over 400 cells); `clustering` stems a
  clump within `radius_m`, mirrored back into the cell at an edge; random yaw; scale from `vegetation_form` (by
  role, ours); ConformToSlope rocks tilted onto the quad's normal. The rules then refuse a stem by slope (from the
  game's ground, the LAND's quantised and limited vertices), height band, water posture, road (traced centreline
  half width + 1.5 m, and any painted BC_ROAD or TRACK corner), a built place's footprint (its refs' bounds +
  20 m), and spacing (1.5 m, trunk on trunk). z is the mean of the quad's two triangulations (the navmesh's
  convention). A point where the two differ by more than 0.45 m is refused.
- **The water posture.** The rows' water_min/max are the old palette's `water_depth_m`: standing water over the
  ground, and negative is the height above the local water table. Water is what ArgoniaWorld.esm places (navmesh
  `inputs.water_levels`: the default 0, cell heights, planes). The table is the level of the nearest water on a
  14.6 m map (505^2), grown ring by ring. A form with no posture is dry-land flora and never stands in water.
  Consequence measured: the many rows at [-6, x] leave ground more than 6 m above the nearest water bare. That is
  the old data's own band, applied as written (the palette warns against tightening dry-tolerant species; none of
  2.W3's rows for those regions carry -99). It is a 2.W3 data call if the stills read sparse.
- **A bug found by the L1 check, fixed at source.** 5 of 942,063 refs failed the slope and posture checks. Each
  lay within 0.005 units of a vertex line, so the writer's 2-decimal rounding moved it onto the neighbouring
  quad. The candidates are now rounded to the emitted precision before the rules judge them.
- **Counts, before calibration:** 942,052 refs; vegetated cells mean 98, p95 203, max 274.
- **Vanilla Tamriel, measured** (Skyrim.esm, streaming, 1.5 s): 11,187 exterior cells. Over the 3,449 forested
  cells (10 or more TREE refs), TREE plus rock STAT refs a cell run median 34, p95 83, max 162. Over the 4,709 cells
  with trees, TREE refs alone run median 18, p95 64, max 132. Ours ran about 2.5x vanilla.
- **Calibration (planner, 2026-10-30):** each region's keep (`vegetation_region_budget`) is the largest share that
  brings its p95 to 83 or less, its max to 162 or less, and every cell under the cap (400, owed its L4 frame-time
  measurement). 23 of 47 regions are thinned (keep 0.32 to 0.72). After: **470,508 refs**; the province's cells
  have mean 29.6, p95 82, max 107. Densest cells: (-49,27) 107, (-26,8) 106, (-37,-44) 105. A region's p95 lands at
  84 to 88 (the thinning is a binomial draw).
- **Writing the refs.** Mutagen's object model for 942k PlacedObjects ran out of memory: OOM at a 1.5 GB heap
  limit (RSS 1.70 GB) and again at 2.25 GB (RSS 2.49 GB), with one shard row held at a time. The cost is
  Mutagen's per-object model, not the JSON. The planner approved a streaming splice instead (`ArgoniaGen
  vegetation`, VegetationRecords.cs). It runs after `ArgoniaGen world` and appends each cell's REFRs to the end of
  its Temporary group in Mutagen's own REFR layout (header flags 0, VCS 0, form version 44; NAME, XSCL when not 1,
  DATA). It grows every enclosing group's size and raises HEDR's record count. On 942k refs it took 2.7 s at
  285 MB peak. Guards: a Mutagen read-back (`ArgoniaGen vegcheck`, binary overlay, every cell's Temporary group)
  with the per-cell counts equal to the shards' (470,508 in 9,538 cells), and two builds with the same sha256.
- **FormIDs:** computed, never allocated: 0x620000 + cell index x 512 + k (past the NAVMs at 0x600000..0x610C24;
  the last slot ends at 0xDE07FF).
- **Navmesh decision: trees do not cut the navmesh.** NPCs path around trunks by local avoidance; the CK's own
  navmesh generator ignores most tree collision too. `tools/navmesh/placed.py` takes only the built places'
  layers, so the vegetation refs never reach it. If the L4 path requests show NPCs stuck on a trunk cluster, the fix
  is a cut for the clump (a box per clump), not per tree.
- **Opt-in.** `pipeline.py vegetation` builds out/ArgoniaWorld.esm with the vegetation (placement 94-119 s, peak
  0.43-0.51 GB; the whole job 3:34 at 1.12 GB, which is the world writer's own peak). `make plugin` and the
  gate's sample hash are unchanged until the planner wires it into the default path. When that happens, the
  sample manifest is re-pinned deliberately.

## Owed

- L4: `tests/journeys/w4-veg-densest.yaml` (stop 8: frame time with and without, the cap; the three vanilla rocks'
  stills; a reader on Nordic flora). The conform rotation's sign convention is unproven until a rock still on a
  slope.
- The CK comparison when the CK is on the game machine.
