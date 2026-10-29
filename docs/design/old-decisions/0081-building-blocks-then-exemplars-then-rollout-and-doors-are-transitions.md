<!-- imported unchanged from elder-souls-argonia docs/decisions/0081-building-blocks-then-exemplars-then-rollout-and-doors-are-transitions.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0081 — Doors are transitions; a place touches the frozen world only through typed local patches

**Status:** accepted; superseded in part by
[0099](0099-places-are-built-in-a-loop-until-the-skill-is-proven.md). The
build flow this record first set (building blocks, then exemplars, then
rollout, with owner check-ins per part) is replaced by the place loop of
0099 and [0100](0100-one-place-skill-whole-layout-authoring-lessons-store-and-the-acceptance-freeze.md);
what stands is the door model, the patch kinds and the image-reading rule.
Refines [0062](0062-dungeons-are-places-interiors-are-a-late-phase.md) § 3.

## Decisions

1. **The door model is the TES one.** Interacting with a door moves the
   player into a separate interior cell and back to the door's exterior
   `arrivalMarker`; the exterior stops at the `streamingBoundary`; water
   state, time, ownership and world-state keys survive the move. Every
   enterable shell and every entrance piece has one door record
   (`door.<placeId>.<parcelId>.<n>`: `interiorClaim`, `interiorStatus`,
   `arrivalMarker`, `streamingBoundary`, reachability). An open structure
   with no interior (deck, gate arch, shelter) has no door record and is
   exterior geometry. There are no seamless interiors; a cave mouth is an
   entrance piece with a door. Which cells are claimed and how is
   [0103](0103-tier-a-interiors-ship-in-16k-and-every-promise-is-a-placed-socket.md)
   and [0114](0114-the-plugin-data-is-the-interior-manifest.md).
2. **A place touches the world after the freeze only through local
   patches**, each touching only its own tiles or chunks, carrying a receipt
   with pre-patch counts, `why` and `sources`, and rebuilding nothing above
   `rederive_blueprints`:
   - `settlement-pad` (terrain, the grade pattern of
     [0059](0059-terrain-built-once-frozen-base-and-typed-patches.md));
     a modular run that seats as one rigid chain over falling ground gets one
     under each member more than 0.05 m over the ground
     (`patch.pad.settlement.<placeId>.<runId>`, `terrain-patches.json`
     schema 2, `worldgen/settlement_run_pads.py`), merged cumulatively;
   - `vegetation-clearance` by tier (trees and large plants cleared from
     plots, ways, pads and a margin; ground cover survives between buildings
     and dies on hard surfaces; the fringe thins; `kept` names the shade and
     Hist trees);
   - `dressing-add` (instances added locally by explicit list or by an
     overlay rule on a polygon, emitted through the compiler's own function,
     ordinals appended).
   Layers on an already built place are
   [0140](0140-layers-on-a-built-place-never-rebuild-it.md).
3. **Image readers ingest liberally under a prompt that names what to look
   at and the report format**; the planner reads no images itself. The
   protocol lives in the `visual-look` skill and the `reader` agent.

## Why

Interiors that were both seamless and streamed contradicted the door model,
and a vegetation patch that could clear but not add left a province re-run
as the only additive path. One door model and three typed local patches let
every place change the frozen world locally, with a receipt.

## Consequences

- Evidence and the superseded flow:
  [place-decision-rounds/0081](../research/archive/place-decision-rounds/0081-as-recorded.md);
  the retired briefs are in
  [phase16-retired-briefs](../research/archive/phase16-retired-briefs/).
