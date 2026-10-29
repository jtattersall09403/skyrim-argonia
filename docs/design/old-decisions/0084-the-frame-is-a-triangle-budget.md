<!-- imported unchanged from elder-souls-argonia docs/decisions/0084-the-frame-is-a-triangle-budget.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0084 — The frame is a triangle budget: 4 M triangles per frame, all passes, on the reference card; every band is sized to it

**Status:** accepted (owner: "we are only aiming for Skyrim-era graphics;
this should be almost trivial on an M2"). **Extends:**
[0075](0075-lod-is-a-ladder-stepped-from-the-camera.md) (the reaches are
sized here) and [0082](0082-vegetation-cells-are-built-once-and-the-gpu-picks-the-rung.md)
(the container is settled here). The rest of the performance architecture
is [0108](0108-performance-architecture-fixture-light-field-ready-materials-view-gated-streaming-fading-tiers.md).

## Context

The reference card is an Apple M2 (Chrome, ANGLE over Metal). It draws
roughly 400 million triangles a second in the browser: at 60 fps about 4
million a frame, counting every pass. Skyrim draws one to two million a
frame. The jungle at rest once drew 6.4 million, because each ladder, band
and ring was set on its own visual merits and the sum was never checked.

## Decisions

1. **The frame triangle budget is 4.0 M per frame on the reference card,
   all passes included.** `FRAME_TRIANGLE_BUDGET` in `packages/game-core`
   is the number; HUD line 3 prints the frame total against it. A change
   that adds geometry to the frame states where the triangles come from.
2. **Bands are sized to the budget in the shipped world, at rest in the
   densest site (the jungle).** Working split: vegetation up to 1.5 M
   including shadow, terrain 0.6 M including shadow, ground cover 0.8 M,
   everything else 0.6 M. The split is a guide; the total is the rule.
3. **Plants hand over to the card at Skyrim distances; trees by the tree
   card rule.** The reaches are 0075 decisions 6 to 8; the tree mesh cap
   `TREE_MESH_MAX_M` (low 250, medium 400, high 600 m) is this budget, since
   with the pixel term alone the tree views drew 7 to 14 M triangles, most
   of the vegetation share from trees past 400 m. Small plants (not trees,
   under 2.5 m) cast no shadow. Skyrim keeps full tree meshes only inside
   its ~140 m loaded grid and treats plants under two metres as grass.
4. **Terrain detail is chosen per sub-tile inside the fine bands.** LOD 1
   (1.8 m) to 150 m, LOD 2 to 400 m, LOD 4 to 1 400 m, LOD 8 beyond; a chunk
   within 400 m is sixteen sub-tiles that pick LOD 1 or 2 on their own edge
   distance, with the skirts that hide cracks between chunks.
5. **The border apron is frustum-culled** by tile or sector.
6. **The foliage shadow cascade reaches 120 m** (Skyrim's exterior shadow
   distance is about 114 m).
7. **Far terrain hidden behind terrain is not drawn.** Whole chunks at
   LOD 4 or 8 and apron sectors are tested every 0.5 s, or after a 10 m move
   or a 10° turn, by marching rays from the camera (raised 5 m) to the five
   top points of the piece's box over the resident LOD 8 heights; a piece
   hides only when every point is behind terrain, and missing data never
   blocks (`packages/game-core/src/terrain/terrainOcclusion.ts`, `&occl=0`,
   HUD `hidden <chunks>c/<sectors>s`). No baked visibility map: the runtime
   test cannot go stale and serves the flyover too.
8. **Ground cover fades between its tiers** (owner: "I preferred it");
   vegetation rung edges stay steps in distance (0075).
9. **The budget is necessary, not sufficient: the frame is also bound by
   submission.** Draw calls cost the main thread and the GPU process, so
   vegetation is drawn as real instanced draws (0082 decision 3), never a
   `BatchedMesh`, whose per-instance multi-draw ranges ANGLE on Metal loops
   one draw at a time. Ground cover's mid and far tiers share one card mesh
   and material, so a species, bucket and part is one mesh; `&gcquad=1|2|4`
   (default 1) is the measuring switch for splitting it.
10. **Ground cover never rebuilds a tile for an input that cannot change it.**
    The small once-fetched inputs (clearance patches, region and tint
    rasters, water depth proxy) gate generation until each has settled, with
    a 10 s ceiling; the optional settlement exclusions do not. A content
    change after tiles exist marks only the tiles the changed shapes can
    reach as stale (tile half-diagonal plus the widest species radius), and a
    stale tile draws until rebuilt, so no content change blanks the ring;
    only the two geometry sliders clear the cache. The HUD counts `built`,
    `staled` and `retiled`. The road-margin clearance is applied on the
    first build.
11. **The opaque pass never samples what it draws into.** Above water the
    water surface's scene-colour and scene-depth samplers are cleared for the
    opaque pass and re-pointed after it (ANGLE validates framebuffer
    feedback per draw); submerged they stay, because that pass reads the
    other ping-pong target.
12. **The body is drawn at the interpolated physics pose.** The studio steps
    physics at 1/60 s; the body, the camera and the foot support plane read
    the pose interpolated between the last two steps (alpha = accumulator /
    step) through `PlayerMovementController.applyVisualPose`.
13. **The HUD says what its GPU line is.** ANGLE on Metal answers a timer
    query with wall time, so on an Apple or Metal renderer the line reads
    `gpu(wall, not work on Metal)` and its figure carries a `~`. The CPU by
    stage and GPU by pass lines, with `&water=0`, `&pmrem=0`, `&veg=0` and
    `&gc=0`, are the attribution tools.

## What was not the cause

Resolution and shader cost (a quarter of the pixels moved the frame by
under a millisecond), the water's own geometry (one field mesh, about 0.2 M
triangles, no planar reflection), and the owner's earlier calls ("no
decimated foliage", "jump between rungs"): none added triangles.

## Consequences

- The water README describes the seven `render` calls the pipeline issues
  (three full scene traversals: opaques to the HDR target, the water layer,
  the overlay layer; plus ripple twice, foam, blit, precipitation).
- The streaming and budget work inherits the budget as its per-frame
  geometry gate.
- Evidence, the owner's HUD readings and the round numbers:
  [rendering-decision-rounds/0084](../research/archive/rendering-decision-rounds/0084-as-recorded.md).
