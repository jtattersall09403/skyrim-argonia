<!-- imported unchanged from elder-souls-argonia docs/decisions/0071-every-placed-thing-steps-down-through-bands-and-collides-as-itself.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0071 — Every placed thing steps down through quality bands, and collides as itself

**Status:** accepted. **Extends:** [0070](0070-vegetation-and-dressing-read-the-record.md)
(vegetation reads the record). **Supersedes:** the rule that rocks collide
as their bounding box. The step between levels is
[0075](0075-lod-is-a-ladder-stepped-from-the-camera.md); the cell renderer
that draws them is [0082](0082-vegetation-cells-are-built-once-and-the-gpu-picks-the-rung.md);
the distances are sized to the frame budget of
[0084](0084-the-frame-is-a-triangle-budget.md).

## Decisions

1. **Every placed thing has a card tier, rendered from its own mesh.** The
   kit builder bakes one per asset (`bakeCards`: two orthographic views
   under flat white light, packed into per-kit atlases; `cardSource:
   "baked"`). A card rendered from the asset is a derived LOD in the
   DynDOLOD sense, not new art. Rocks get no card and no decimated levels
   (`lodRatiosByCategory {"rock": []}`): decimation opens the open-shell
   cliff pieces and shows holes at distance. Why a card is never taken from
   a source mod is [0073](0073-one-copy-per-pixel-a-card-is-baked-from-its-own-mesh-and-the-writer-is-not-the-rule.md).
2. **Levels change by camera distance, one copy per pixel.** The ladder,
   its hard steps and its short fade in time are 0075.
3. **The ground ring has bands.** Full mesh near the player, a
   camera-facing card to the ring radius, a sparser card to a far radius per
   preset. Ground cover never ends at a hard line; its tiers fade into one
   another (0084 decision 8) and each species' full-mesh reach is sized to
   its mesh cost (0082).
4. **Ground cover close up is 3D where the vault has 3D.** The lush covers
   carry at least one true 3D clump at 40 percent or more of their density,
   sourced (DrJacopo's 3D Grass Library, Hoddminir, 3D Grass for Vanilla,
   vanilla `plants/` clusters) and credited in the root README.
5. **Rocks collide as their own triangles.** A rock's collider is a Rapier
   trimesh of its LOD0 geometry, scaled per instance
   (`floraSolids.trimeshFromGeometry`), never a bounding box. Kit pieces
   reuse the same path for their convex and trimesh colliders.
6. **Rocks do not sway.** Wind is applied by species category; rocks,
   deadfall, containers, ruins, architecture and clutter carry stiffness 0.
7. **A rock is seated by its footprint, not by one number.** After the
   slope tilt the base plane is sampled against the ground on the footprint
   ellipse and the sink is raised by any exposure, capped at 0.6 of the
   piece's height; an open-backed piece's yaw is `downhill + 180° −
   openBackYawDeg`, so its open side faces uphill for any authored back
   angle. How the seating survives the writer, and which rocks are refused
   or cut, is 0073 decision 4 and 0075 decision 7.
8. **Terrain occludes.** Instances beyond 120 m that the ground hides from
   the camera are not drawn. The test is a one-texel-per-32-m-cell mask
   refreshed a few cells per frame from the live camera, read by the vertex
   shader (0082 decision 6); far terrain chunks hidden behind terrain are
   culled by 0084 decision 7.
9. **Terrain chunks step down by distance, not by ring.** A chunk's level
   is chosen from the camera's distance to the chunk rectangle's nearest
   edge, with hysteresis (up the moment it is inside a band, down only 15
   percent past it), re-evaluated once the camera has moved 8 m. The bands
   and the per-sub-tile choice inside the fine bands are 0084 decision 4.
   LOD 8 is no new download: the published LOD 4 raster with every second
   sample kept. The two fine levels cast sun shadows; the coarse two never
   do.
10. **The sea is the record's `ocean` body and nothing else.** No raster
    reads salt water. The compiled `ocean` label reaches about 56 ha into
    tidal creeks; the owner ruled that no refreeze will run and accepted it
    as it is (the polish backlog row records the cost: sea class and
    sea-bed dressing on shallow tidal creek within 700 m of the open sea).
11. **The sea bed is dressed from the shoreline out, under `ocean` only.**
    Pebbles, stones, shells, real coral, starfish, sponges, debris and wet
    rocks, gated by the record kind and a coastline density ramp sized for
    a swimmer's sight line (0073 decision 6); no flat coral card fans; the
    depth floor measures the top of a piece above the bed.
12. **Roads keep their surface in every state of repair.** Condition
    changes the material mix (cobbles, dirt, track), the width, fine
    potholes and the grass on it; it never erases the line. The track
    texture is Tropical Skyrim's road, chosen by measured contrast.
13. **The province rasters publish per group.** Five release assets; only
    the changed groups upload.

## Why

The same defect kept appearing in six places: something derived from a
proxy (a bounding box, a source mod's card list, a scalar sink, a region
class, a connected water piece, a hard ring) standing in for the thing
itself. Reading the real geometry and the real record once costs a build
step; every proxy cost a round.

## Consequences

- A new vegetation asset gets a card, a collider and a seating rule from
  the kit build and the scatter; nothing is hand-typed per species.
- Kit pieces reuse the trimesh collider path and the card bake.
- Evidence and the measured numbers:
  [rendering-decision-rounds/0071](../research/archive/rendering-decision-rounds/0071-as-recorded.md).
