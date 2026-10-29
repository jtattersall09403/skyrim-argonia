<!-- imported unchanged from elder-souls-argonia docs/decisions/0120-kits-stream-per-piece-spawn-ring-first.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0120 — Kits stream per piece, spawn ring first

Status: accepted. Builds on the tier and band ladder of decisions 0075 and
0082 and the download budget of standard 16. The scene-complete bar and its
measured value are
[0108](0108-performance-architecture-fixture-light-field-ready-materials-view-gated-streaming-fading-tiers.md)
§ 3: under 10 s where that is cheap, 15 to 18 s acceptable.

## Context

Whole-kit fetches made the scene arrive late: the 29 top-level settlement
kit GLBs (about 343 MB) were fetched whole as soon as any placement that
used one was inside the draw cap, so one boat pulled the whole watercraft
kit. Transcoding was not the cost. No scene-complete target is reachable
while whole kits are fetched.

## Decisions

1. **Kit meshes and textures are fetched per piece, or per kit section, on
   demand.** The unit is one piece (or a named section of a kit), not the
   kit file. `InteriorDoors.tsx` already loads `${kit.id}#${assetId}` per
   part; exterior kits use the same addressing. A pool texture
   (`kits/tex/<sha16>.ktx2`) is owned once per renderer, on its kit decoders
   (`decoders.textures`, built in `createKitDecoders` and used by every part
   loader through `createKitPartLoader`), so it uploads once whichever layer
   names it.
2. **Requests are ordered by distance from the spawn.** The spawn ring (the
   pieces inside the near band of the player's start) and the pieces in view
   load before `ready`. Everything else streams after `ready`, nearest
   first.
3. **The existing tier and band ladder (0075, 0082) decides what is
   requested.** No new quality tier, and no default is lowered (0108 section
   6). A piece is requested when its band says it is drawn, and not before.
4. **The warm gate opens when the spawn ring is complete and the build queue
   is empty.** Pieces beyond the ring never hold the gate.

## Ownership

dev (performance lane): `SettlementLayer.tsx` and the kit loader implement
the per-piece fetch and the spawn-distance ordering, plus the per-piece or
per-section publish format and its manifest rows. The program warm is the
performance lane's.

## Download budget (standard 16)

Nothing new ships. The same compressed bytes (UASTC/KTX2 and meshopt via
`pipeline/kit_compress.py`) arrive later, per piece. The splitting step
runs inside the kit publish and is measured by the existing
`kit_compress --check` and the site-size budget; either failing blocks the
change.

## Measured

Every kit is parts-only (schema 4; `loadKitParts`, `useKitParts`).
`tooling/gpu-lane/measure.mjs` reports per-URL resource timing, kit bytes
before ready and `sceneCompleteS`; the measured value is recorded in 0108
§ 3.
