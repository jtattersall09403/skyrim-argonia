<!-- imported unchanged from elder-souls-argonia docs/decisions/0082-vegetation-cells-are-built-once-and-the-gpu-picks-the-rung.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0082 — Vegetation cells are built once; every rung is emitted; the GPU picks the rung; tiles are gated, never instances

**Status:** accepted (owner: walking must not stutter when the character
crosses into new ground; every walk is judged on a renderer that does not
rebuild itself as the camera moves). **Extends:**
[0071](0071-every-placed-thing-steps-down-through-bands-and-collides-as-itself.md)
(occlusion) and [0075](0075-lod-is-a-ladder-stepped-from-the-camera.md)
(the ladder). The container is the one [0084](0084-the-frame-is-a-triangle-budget.md)
settled; the culling and startup rules are
[0108](0108-performance-architecture-fixture-light-field-ready-materials-view-gated-streaming-fading-tiers.md).

## Decisions

1. **A cell is a vegetation chunk (468 m), built once.** Its buffers are
   built when its chunk decodes and its terrain is at the settled LOD the
   cell needs (`cellRegistry.ts`, `LOD_SETTLE_MS`); it is rebuilt alone
   when that terrain LOD changes, when a quality tier's `drawScale` changes,
   or when a kit arrives holding a species the cell skipped
   (`skippedSpecies`). A camera move never marks a cell dirty
   (`CellRegistry.cameraMoved` is a no-op the unit test asserts). A cell
   further than ring + 1 from the focus chunk gives its rows back; a
   geometry with no rows left is pruned from the scene.
2. **Every rung is emitted for every instance**, both band edges closed;
   the shader keeps the rung for the camera distance (0075). The card rung
   is emitted like any other.
3. **The container is one `THREE.InstancedMesh` per (batch key, kit
   geometry)** whose visible copies are a compact prefix: a copy keeps a
   permanent slot; switching a copy on appends it, switching one off swaps
   the last copy into its row, `mesh.count` is the draw, and one merged
   upload range covers a frame's touched rows. The requirement is
   instancing (WebGL2 core). `BatchedMesh` is not used: it submits one
   multi-draw range per visible instance, which ANGLE on Metal expands into
   one Metal draw each (0084).
4. **The batch key** is `material | depth material | attribute signature |
   near/far | card/mesh | casts`. Near and far are separate because the near
   batch casts shadows; card and mesh are separate because a card never
   sways or receives shadow. Materials are owned per batch key and patched
   once; a capacity growth re-creates only the mesh and its data texture.
5. **Per-instance data rides a `DataTexture` per batch**, two RGBA32F texels
   per slot (the LOD band; stiffness − 1, sink, plant height), indexed by an
   `esSlot` instanced attribute. Shader branches key on the `ES_BATCH_SLOTS`
   define; every material patch that reads an instance's placement
   (`lodFade.ts`, `windSway.ts`, `sky/aerial.ts`, `causticReceiver.ts`)
   carries both the slot and the plain instancing branch, and appends to
   the program cache key rather than replacing it. Wind is patched onto
   every batch material; stillness is per instance (stiffness −1 for a
   non-swaying species and every card).
6. **Terrain occlusion is a shader mask** (`occlusionMask.ts`): a 128² R8
   texture over 32 m cells, anchored on the focus chunk, a few occupied
   cells re-rayed per frame from the live camera under the frame budget;
   the vertex shader collapses an instance whose cell is hidden beyond
   `OCCLUSION_MIN_DISTANCE_M`. Only an anchor move wipes the mask; a dropped
   cell clears its own texels.
7. **The sun shadow is cast by one rung**: the highest non-card kit level at
   or below 1 (level 1 where the species has a mesh there, else level 0);
   cards never cast. A level-1 caster's depth material takes
   `shadowBandFromZero` so it casts from distance 0 while its outer edge is
   unchanged (`world-render/src/vegetation/shadowRule.ts`). `&vegshadow=0`
   disables casting.
8. **Gating is per cell, then per tile, never per instance.** Each
   species' instances are sorted at build into a 16 × 16 grid of tiles
   (about 29 m) with per-tile extents, so a tile's copies are one
   contiguous run; a cell wholly outside or inside a band answers for all
   its tiles in one test. A tile is on when its band (widened by
   `GATE_MARGIN_M` 8 m, measured to the pivots) holds the camera and its box
   meets the view frustum widened by 15° to switch on and 25° to switch off
   (`cellGating.viewPlanesFor`, `GateView`); a casting rung's tile is also
   kept when its box swept along the sun's shadow (capped 120 m, none at
   night) touches the view. The pass runs on a 2 m move or an 8° turn, a
   cell built or dropped, or every 120 frames, resumes across at most four
   frames (`GatePass`), and applies flips under a 1.5 ms drain; switch-ons
   the shader needs now drain first, up to 6 ms. Standing still costs
   nothing.
9. **Colliders are derived at cell build**; the published list is the
   concatenation of live cells.
10. **Ground cover sizes its full-mesh reach to the mesh's cost**
    (`world-render/src/vegetation/Groundcover.tsx`): `nearReachM =
    NEAR_FRACTION × radiusM × clamp(NEAR_TRI_REF / meshTris,
    NEAR_REACH_MIN, 1)` with `NEAR_TRI_REF` 250 and `NEAR_REACH_MIN` 0.25,
    where `meshTris` is the coarsest non-card level under `NEAR_TRI_MAX`
    1 000, else level 0. No species is card-only: a heavy species draws its
    own mesh to the floored reach and hands over to its card there.
    Clearance polygons carry a segment index (8 m cells, 4 m z-bands) whose
    answers equal the brute-force test (`vegetationPatches.test.ts`).
11. **The jungle site is the measuring site**: the densest region with the
    most species, so what meets its numbers meets every other site.

## Why

A rebuild per 16 m of camera travel walked every instance of every loaded
chunk on the CPU; that pass was 83 to 99 percent of the rebuild and the
cause of the walking stutter. Per-instance culling on the CPU costs a
thousand times what per-cell culling does at ring size. Building once and
letting the GPU pick the rung moves all of it off the walk.

## Consequences

- `VegetationCells.tsx` is the renderer (`world-render/src/vegetation/`),
  with its parts in `packages/game-core/src/vegetation/` (`cellBuild.ts`,
  `cellGating.ts`, `cellRegistry.ts`, `occlusionMask.ts`) and
  `fx/batchData.ts`. The old per-rebuild rule survives in
  `cellBuild.test.ts` as the parity oracle.
- The HUD vegetation line prints `draws N (ranges M)`; `probe-frame-work.mjs`
  fails on any shader compile message (`shaderErrors`), because a program
  that fails to compile is silent in every CPU counter.
- Measured with `packages/world-render/src/vegetation/__measure__/`
  (`VEG_MEASURE=1`). Evidence and the round numbers:
  [rendering-decision-rounds/0082](../research/archive/rendering-decision-rounds/0082-as-recorded.md)
  and [renderer-rewrite-baseline.md](../research/vegetation/renderer-rewrite-baseline.md).
