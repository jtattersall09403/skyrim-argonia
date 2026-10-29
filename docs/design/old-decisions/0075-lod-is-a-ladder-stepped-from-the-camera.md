<!-- imported unchanged from elder-souls-argonia docs/decisions/0075-lod-is-a-ladder-stepped-from-the-camera.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0075 — LOD is a ladder stepped from the camera; a copy's edge closes only against a copy that exists

**Status:** accepted (owner: "just have one system that works"; "how does
Skyrim do it? copy their approach"). **Extends:**
[0071](0071-every-placed-thing-steps-down-through-bands-and-collides-as-itself.md)
and [0073](0073-one-copy-per-pixel-a-card-is-baked-from-its-own-mesh-and-the-writer-is-not-the-rule.md).
The cell renderer that emits the copies is
[0082](0082-vegetation-cells-are-built-once-and-the-gpu-picks-the-rung.md);
the reaches are sized to [0084](0084-the-frame-is-a-triangle-budget.md)'s
frame budget; the part-aware tiers and impostors are
[0108](0108-performance-architecture-fixture-light-field-ready-materials-view-gated-streaming-fading-tiers.md) § 5.

## Decisions

1. **The rule is Skyrim's: a hard step between levels by camera distance.**
   Skyrim holds full models inside the loaded cell grid and swaps to LOD
   meshes and tree cards beyond it by fixed distance bands, with no
   dissolve between levels. Ours: a species has a ladder of camera-distance
   intervals tiling [0, draw distance), one kit level each (`lodLadder`);
   the shader keeps the level whose interval holds the live camera distance.
   Every rung edge, every ground-cover tier edge and the vanish at the end
   of a ladder is a step in distance (`LOD_BAND_M` 0, `TIER_BAND_M` zeroes,
   `LOD_CULL_BAND_M` 0). Ground cover keeps a dithered fade between its
   tiers (0084 decision 8).
2. **A rung edge fades in time, not in distance** (`lodFade.ts`,
   `LOD_FADE_S` 0.4 s, `LOD_FADE_SAMPLES` 8). Each copy's factor is the
   distance step averaged over the camera's last 0.4 s of positions
   (`esLodHist`, offsets from `esLodViewPos`). Both copies hold the same
   factor, so the partition of 0073 decision 1 is exact every frame; both
   are drawn only for 0.4 s after a crossing, and a still camera draws one
   copy. Tested in `lodFadeTemporal.test.ts`.
3. **A copy's edge closes only against a copy that exists.** Every instance
   is emitted into every rung of its ladder when its cell is built, both band
   edges closed (0082 decision 2), so the copies always tile the distance
   line whatever the camera does; rungs a cell cannot need at its distance
   are switched off per cell, never re-emitted. The invariant (every
   distance kept by exactly one rung, for every species shape and preset) is
   `ladderCoverage.test.ts`.
4. **An identical level is not a level.** `floraKit.ts` drops a level that is
   not smaller than the one before; `build_kit.py` no longer exports one.
5. **An alpha-tested part is never decimated.** Plant parts are many small
   islands (leaf cards, twig cards, bark strips) that collapse decimation
   shreds into empty slivers. `floraKit.ts` gives an alpha-tested part its
   base geometry at every mesh level and `build_kit.py` exports no decimated
   level for an alpha-tested asset; only an opaque part steps down by
   decimation. Lower tiers for heavy trees are made part-aware (whole source
   cards and whole bark islands kept), never decimated (0108 § 5).
6. **A species' ladder follows the mesh levels its kit carries**
   (`floraKit.speciesRings`, levels surviving the dedupe). One level
   (`folded`): the full mesh to the folded reach, then the card. Two or
   three: hand-over by projected screen size at a 1080 px, 60° reference view
   (`HANDOVER_PX`), never nearer than the distances the part-aware tiers
   were validated at.
7. **Every tree cards by one rule** (`treeCardDistance`): card distance =
   min(distanceAtPx(height × crownBulk, `CARD_PX` 20 px), `TREE_MESH_MAX_M`
   low 250 / medium 400 / high 600 m, the fog hide distance where
   transmittance falls to 0.35), with crownBulk = max(1, footprint /
   height). The mesh cap is 0084's frame budget. Every tree of 6 m or more is
   a mesh through the 100 to 150 m band. A tree with an impostor draws it in
   place of the card (0108 § 5).
8. **Non-tree plants hold their full mesh by size class**, not scaled by the
   draw scale: small plants 35 / 45 / 65 m (low / medium / high,
   `SMALL_PLANT_TOP_TIER_M`); large plants (height or half the widest
   footprint at least 2.5 m, `isLargePlant`) 80 / 100 / 260 m
   (`LARGE_PLANT_TOP_TIER_M`), drawn as cards to 1.5 times that
   (`plantDrawDistance`). The folded reach of other one-level species is
   band-aware (`LOD_REACH_BY_BAND`: low height × 5 in 50–140 m, medium × 7
   in 60–200 m, high × 9 in 80–280 m), and a light single-level tree's reach
   is raised by `treeReachBoost` = clamp(√(1500 / full-mesh triangles), 1,
   2.4).
9. **Every scatter type's chain is audited from the shipped kit**
   (`pipeline/kit_lod_audit.py`, both kits): rocks are one level with no
   card; every land asset outside rocks carries a textured card; no level
   lacks a part its base has. The underwater kit carries no cards by design
   (its ladders end at 120 m under water) and is exempt by name.
10. **Screen-space water reflections stop at 260 m**, fading from 160 m; the
    march is per water pixel, so the range is frame time.
11. **Rocks are seated by 0073's base plane, and a boulder or pile whose
    lower half still hangs is cut.** `rock_bottom_profiles.py` mines each
    rock's lower half (one vertex per 0.25 m voxel, both kits) into
    `world/sources/placement/rock-bottom-profiles.json`;
    `compile_scatter.cut_hanging_rocks` poses each rock exactly as the bundle
    carries it and drops a boulder or pile whose lower half stands more than
    0.75 m off the ground anywhere under it. Cliff shells are never cut:
    their hollow sits against the hill. Seating a rock on its own underside
    was tried and rejected: it buried rocks Skyrim leaves showing their
    bellies on hillsides.
12. **Sun shadows are stable and continuous.** The CSM light direction
    follows the sun every frame (`WorldSky.tsx` `stabiliseCascades`); each
    cascade's shadow camera covers the fixed bounding sphere of its frustum
    slice (`cascadeSphere`, `game-core/render/stableShadow.ts`), so its
    texel size does not change as the camera turns; the cascade origin is
    snapped to whole texels in a rotation-only light basis
    (`snapToTexel`, `stableShadow.test.ts`). Which rung casts is 0082
    decision 7.

## Why

Four rounds of crossfades in distance each moved the symptom (copies chosen
from the character and faded from the camera, merged rungs that kept a
ring edge, correctness that depended on rebuild timing). A hard step in
distance with every rung emitted cannot leave a gap, and a short fade in
time hides the step without smearing a still view.

## Consequences

- One mechanism, one attribute layout; the ground ring and the scatter
  share the shader.
- `rock_mesh_census.py` reports what the cut counts; `rock_census.py` keeps
  the float, tilt, scale, swallow and open-back checks.
- Evidence and the measured numbers:
  [rendering-decision-rounds/0075](../research/archive/rendering-decision-rounds/0075-as-recorded.md)
  and the [16f ledger](../research/archive/phase16-evidence/16f-ledger.md).
