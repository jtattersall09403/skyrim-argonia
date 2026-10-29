<!-- imported unchanged from elder-souls-argonia docs/decisions/0047-water-one-physical-model.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0047 — Water: one physical model, one grid, one definition shared by carve and compile

**Status** accepted · **Follows** [0046](0046-water-overhaul-retired.md) ·
**Refined by** [0058](0058-the-hydrology-graph-is-the-water-record.md) (levels
come from the hydrology graph), [0063](0063-water-once-the-line-is-high-water.md)
and [0065](0065-the-compile-realises-the-graphs-classification.md) (season,
fetch, classification), [0064](0064-waterfalls-are-the-vanilla-kit.md)
(waterfall meshes)

Every inland water defect the owner found (surfaces ending in mid-air,
hovering blobs, holes in rivers, plates lifting in the wet season, brown strips
flowing uphill, falls on ordinary slopes, zigzag trenches, jagged shores) was
one mistake seen from different sites: a level asserted where water could not
stand. Local patches produced tunables and no invariant. The measured root
causes are in the [archived record](../research/archive/water-round-2-2026-09/0047-as-recorded.md)
and the [round evidence](../research/archive/water-round-2-2026-09/water-round2-evidence.md).

## Rules

- **Full-resolution terrain is the truth.** The compile runs on the refined
  grid the studio renders (1.828 m). Exported rasters sample that solution at
  the texel centres the runtime uses (`(i+0.5)·mpp`); a test asserts the
  registration against `game-core/terrain/heightfield.ts`.
- **Every level is a level water can stand at.** Sea is 0 on ocean-connected
  ground below 0; standing water is a flood of the raw terrain, its extent the
  flood extent, never a mask; a river is a monotone long profile along a smooth
  centreline, never above the bank it would overtop. Tested: no wet cell has a
  lower dry neighbour, pools are flat, no wet cell stands deeper than its
  body's real flood depth. The levels themselves are recorded once in the
  hydrology graph (0058).
- **A channel is one object.** `worldgen/channels.py` owns the centreline,
  long profile, cross-section carve, reach classification (field, steep strip,
  fall) and rasterisation; the terrain carve and the water compile both call
  it, so the trench and the water filling it are the same curve.
- **A river that drains to the sea reaches the sea**: a sea-draining terminus
  above sea level extends down `flow_to` to the first ocean cell.
- **A waterfall is a cliff.** A fall run is built from the face angle
  (`FALL_FACE_SLOPE`, 70°) and drops at least 3 m; anything steeper than the
  field raster carries but short of a cliff is a steep strip. Strips end at a
  lip and resume at the plunge; the field is masked under both. A fall may land
  in a standing body (a plunge pool); a pooled lip or interior is refused. A
  plunge pool is scoured by its fall: `PLUNGE_MIN_DEPTH_M` + 0.06 m per metre
  of drop, capped at 8 m.
- **Signed depth ships.** The surface raster carries signed `W − ground`
  (`surface.depthMinM`, `surface.depthSpanM`), so the runtime decides wetness
  as `signedDepth + lift > 0` and the season floods and drains physically.
- **The terrain cuts the shoreline.** The visible edge is the surface plane
  meeting the terrain mesh under the depth test, softened by a vertical depth
  fade from the unrefracted scene depth; the raster discard is only a coarse
  buried guard.
- **Whitewater is a look, not a colour.** Strips render aerated (albedo and
  opacity from slope × speed, streak noise along the ribbon's own arc length,
  no refraction). Lowland rivers get a speed floor by band and an along-flow
  undulation with a CPU twin in `waves.ts`, so buoyancy agrees.
- **Authored minor waterways** (`worldgen/authored_waterways.py`) are carved
  by the terrain stage and joined to the water they meet.
- **Gates test the defects.** Compiled-data invariants (hovering edges, flat
  bodies, registration, strips inside their trench, falls on cliffs, every
  river cell wet along its centreline, monotone season growth) are the gate. A
  brink is not a hole: the hovering check knows each sheet's corridor and
  counts what it excuses as `brinkEdgeCells`. A gate is proved by making it fail
  on the defect it exists for.

The live defect ledger is
[audit-water-runtime](../research/phase16/audit-water-runtime.md).
