<!-- imported unchanged from elder-souls-argonia docs/decisions/0052-a-published-bundle-obeys-the-runtime-contract.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0052 — A published place bundle obeys every contract the runtime enforces

**Status** accepted · **Extends** [0041](0041-phase11-settlement-decisions.md)
(placement) and the export half of [world/90](../world/90-asset-strategy.md)

A hard runtime contract enforced only when the player stands at one position,
with nothing offline able to predict it, ships a place that draws nothing: a
collider budget that was a bare uncalibrated literal, a two-tier LOD chain
the runtime throws on, a kit texture the site build pruned. Every such
contract therefore gets an offline gate on the artefact that ships.

## The rules

1. **The collider part budget is measured.** Parts are counted as `solidFrom`
   counts them: the measured manifest proxy where an asset has one, else its
   LOD0 mesh primitive count from the built GLB. The budget is derived per
   publish (`collider_part_budget`, round(worst × 1.55)); the per-place
   ceiling is `COLLIDER_PART_CEILING` 400, and `COLLIDER_PART_CEILING_LARGE`
   500 for a place of five or more dwellings, since each brings its clutter
   ring ([0105](0105-setting-class-reserved-doors-lights-band-planned-variety.md)) and a
   static collider is cheap. A placement under 0.3 m in both plan axes and
   height exports no collider (`is_small_piece`) and counts toward no
   ceiling. The check's message names the ceiling and why.
2. **Every runtime contract has an export gate reading the shipped GLB.**
   `export_settlement_bundle` refuses to publish on `collider_budget_errors`
   (the residency refusal), `lod_contract_errors` (`validateLodTriangles`)
   and `texture_cap_errors` (`validateMaterialTextureCap`), reading LOD tiers
   and triangles from the mesh graph and image sizes from the file header,
   never a manifest's claim about itself. The owner's `--ship-with-errors`
   override covers them like every error; the runtime refusals stay as
   backstops.
3. **Only assets that can satisfy the contract are placeable.** `KitShelf`
   offers for placement only assets with at least two `lodRatios`, keyed to
   the contract, never to a kit naming convention; `by_asset` stays complete
   for measurement.
4. **The site build keeps kit files by resolved reference.**
   `tooling/pages-site/kit-reach.mjs` keeps the named kits' files, then every
   file their JSON resolves to, to a fixpoint, and refuses to ship any
   dangling reference.
5. **Preflight runs the refusals before deploy.** Gate `site-refs`
   (`tooling/repo-standards/check_site_refs.mjs`) runs that reach over the
   sources in under a second. Gate `bundle-load`
   (`packages/game-core/src/settlement/publishedLoad.test.ts`, also in
   `npm test`) puts every published bundle through the runtime's own
   file-decidable refusals: schema, collision frame, kit files, manifest
   parse, asset rows, LOD tier count, flame and smoke textures.
6. **A layer's failure stays inside the layer and is readable.** The scene
   build is wrapped so a throw never unmounts the host's tree. A fatal draws
   nothing (fail-closed) and is reported through the layer's injected
   `onError` (the studio HUD's red "SETTLEMENT LAYER FAILED" line) and
   `console.error`. A flame or smoke sprite that fails to load is not fatal:
   the place draws without it and the HUD says so.

## Not covered

Bundle and kit transport failures stay runtime-only, correctly. A GLB that is
present, non-empty and corrupt still fails only in the browser, since staging
checks existence and size, not integrity; queued in the
[polish backlog](../phases/P-polish/backlog.md).
