<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.11-loops/overlay.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 2.11 narrative: markers and the local-state overlay

Code: `packages/narrative/src/markers/markers.ts`, `packages/narrative/src/overlay/overlay.ts` (tests beside each).

## Survey

- Variant shapes. The blueprint (`worldgen/blueprint.py` ~352) and the
  bundle (`settlement.variants`, typed `Record<string, unknown>[]` at
  `game-core/src/settlement/types.ts:265`) ship
  `{id, changedRefs, serviceOverrides, ambience?}`; Helstrom also ships
  `stateRef`. Quests/80 §60 `LocalStateVariant` adds `enableRefs`,
  `disableRefs`, `actorScheduleOverrides` and an array `serviceOverrides`.
  `OverlayVariant` is the bundle shape plus the optional §60 fields
  (`enableRefs`, `disableRefs`, `scheduleOverrides` as actor to schedule).
  The array form of `serviceOverrides` is not read; nothing ships it.
- The 21 published place bundles: 19 ship exactly one variant, `*.base`, with
  `changedRefs: []`, empty `serviceOverrides` and an ambience. Helstrom ships
  two non-base variants (`assembly-open`, `grove-withdrawn`, each with a
  `stateRef`, `changedRefs` naming parcels). Pearl Lots ships none. So a base
  is optional, at most one (`variantProblems`), and the test loads all 21.
- `changedRefs` lists the refs a variant flips; each is also in `enableRefs`
  or `disableRefs`, which carry the direction (blueprint validator and
  `variantProblems` refuse a changed ref with none; Helstrom's two variants
  are migrated).
- Order, last wins: base, active variants in the order applied, then the
  direct `enableRef` / `disableRef` / `moveRef` / `setSchedule` /
  `setAmbience` overrides. A direct override lands on the place whose variant
  names the ref (or actor); `placeOfRef` places the rest; a ref nobody places
  is an `OverlayError`.
- Markers: a catalogue row (`MarkerDef`) targets a place or a socket and
  carries the `MapPlace` fields (`textId`, `kind`, `tier`). The host's
  `MarkerPorts` give the position in the map pack frame, so `grantedMarkers()`
  returns `MapPlace`-shaped pins (`MapView`). Nothing shows unless granted
  (0137). Journal entries keep `pinId` / `directionsId`; the host shows a pin
  only when its id is granted or its place discovered.

## Save families

- `markers` v1: `{schemaVersion:1, granted: {markerId: epochMinute}}`.
- `overlay` v1: `{schemaVersion:1, active, refs, moved, schedules, ambience}`
  (maps sorted; `active` lists keep application order).
- Both restore after `NARRATIVE_RESTORE_AFTER`.

## Wiring (the host's, not done here)

- Handlers: spread `createMarkers(..).handlers()` and `createOverlay(..).handlers()`
  into `createNarrative({handlers})`; add
  `extend: [() => ({ localVariantActive: overlay.localVariantActive })]`.
- Renderer: call `overlay.resolve()` where the settlement reach picks the
  resident placements, `packages/game-core/src/settlement/settlementReach.ts:33`
  (`residentPlacementIdsAt(bundle.settlements, focus)`; same call at
  `refocusRing.ts:72`), dropping `disabledRefs`; people schedules at
  `packages/scene/src/people/PeopleLayer.tsx:222`; services and ambience from
  the same `ResolvedPlace`.
- Index exports: both modules and their types and `*_SYSTEM_ID`s.
