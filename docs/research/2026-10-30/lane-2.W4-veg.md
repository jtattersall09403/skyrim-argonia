# Lane 2.W4-veg: vegetation by our own placement from the region rules (2.W4 §a fallback)

**Why:** the CK is not on the game machine (owner issue #15). Method, findings and numbers are in
`docs/research/journals/vegetation.md`; the brief's Outcome §a has the summary.

## Delivered
- `tools/argonia_world/vegetation/`. `place.py` holds the rules per cell and form; `build.py` covers the province
  in bands of 4 cell rows and writes shards per row; `checks.py` holds the L1 checks and the Mutagen read-back;
  `__main__.py` takes build, check and readback; `tests/` has 9 L1 tests on hand-made cells.
- `world/schema.sql`: `vegetation_form` (34 rows, scale ranges by role) and `vegetation_region_budget` (47 rows,
  each region's keep).
- `tools/ArgoniaGen/VegetationRecords.cs`: `vegetation` (the streaming REFR splice) and `vegcheck` (the read-back
  through Mutagen's overlay), registered in Program.cs.
- `tools/ArgoniaGen/pipeline.py`: `pipeline.py vegetation`, opt-in, with its stamp. `make plugin` and the gate's
  sample hash are unchanged (planner: unwired until it fits). So `terrain/sample-manifest.json` is not re-pinned.
- `tests/journeys/w4-veg-densest.yaml`: the L4 draft for stop 8.
- The vegetation journal, and the brief's Outcome §a.

## Measured
| | before calibration | after (committed rows) |
|---|---|---|
| refs | 942,052 | 470,508 |
| per province cell: mean / p95 / max | 59.3 / 189 / 274 | 29.6 / 82 / 107 |
| vanilla Tamriel, forested cells (n = 3,449): median / p95 / max | 34 / 83 / 162 | |
| placement time, peak RSS | 119 s, 428 MB | 94-120 s, 514 MB (with --budget) |
| ESM write | Mutagen model: OOM at a 1.5 GB heap (RSS 1.70 GB) and at 2.25 GB (RSS 2.49 GB) | splice 2.7 s at 285 MB; whole `pipeline.py vegetation` 3:34 at 1.12 GB |
| ArgoniaWorld.esm | 115.2 MB without | 150.0 MB with, sha256 da7e3b82… (two builds identical) |
| read-back (Mutagen overlay) | | 470,508 refs in 9,538 cells, equal per cell to the shards, 356 MB |

- **L1, full province:** ground (decoded LAND, both triangulations, 0.5 m), slope, height, water posture, road,
  places, budget and ids all have 0 failures. The first run found 5 refs judged on the wrong quad (the rounding
  at vertex lines), fixed at source. Shard determinism: two builds give sha256 21bb91fe… (before calibration).
- **Gate:** `make check` CHECK GREEN in 1:31.6 at a peak RSS of 1.26 GB (305 tests; the plugin-check sample hash is unchanged).

## Open calls and findings
- **Posture sparsity:** rows at water_min -6 leave ground more than 6 m above the nearest water bare. That is the
  old palette's band, applied as written. If the stills read sparse, it is a 2.W3 data call (-99 for the
  dry-tolerant forms).
- **The cap** (400) is a starting value; frame time at stop 8 sets it (L4 draft).
- **Wiring into `make plugin`** needs a planner call; then re-pin the sample manifest deliberately.
- **The conform rotation's sign** is unproven until a rock still on a slope.
- **Navmesh:** trees do not cut it (NPC avoidance; `navmesh/placed.py` reads only the place layers).
