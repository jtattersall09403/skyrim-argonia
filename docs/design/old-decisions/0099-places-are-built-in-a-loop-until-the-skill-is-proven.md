<!-- imported unchanged from elder-souls-argonia docs/decisions/0099-places-are-built-in-a-loop-until-the-skill-is-proven.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0099 — Places are built in a loop, one real place at a time, until the place skill is proven per type

**Status:** accepted; superseded in part. Supersedes the build flow of
[0081](0081-building-blocks-then-exemplars-then-rollout-and-doors-are-transitions.md).
[0100](0100-one-place-skill-whole-layout-authoring-lessons-store-and-the-acceptance-freeze.md)
sets the procedure inside the loop; [0106](0106-how-we-work-fix-at-source-one-preflight-per-batch-scoped-for-real.md)
and [0131](0131-one-check-gate.md) replace its speed rules;
[0134](0134-four-parts-de-risk-first.md) moves the exit bar to Part 4, and
[0135](0135-phase-16-closes-the-world-is-leg-work-now.md) closes Phase 16
on what the loop proved. The loop itself is
[16k](../phases/16-foundation-and-places/16k-place-loop.md) and the `place`
skill.

## Decisions

1. **Place work is a loop on real places, not a sequence of phases.** The
   unit is one real place (a slice): the builder runs the place skill on the
   frozen world, then the automatic gates, then **the owner walks it**; every
   defect becomes a rule, a gate and a skill improvement in one fix round
   (causes grouped across all defects); the owner walks again, until the
   owner says it looks right. Only then the next slice: a place of a
   different type in a contrasting region. The owner is in the loop at the
   walk, at the type list and exit bar, and at world-level decisions.
2. **Exit bar.** For each place type on the owner's signed list, a fresh
   place passes unattended with no defect from the walk, two in a row per
   type. The bar is met in Part 4 (0134). Minor types (camps, small holds,
   waystations) may become **templates**: one designed instance varied per
   placement, once a type's two passing places differed only along the
   template's variation axes.
3. **Breadth is set now, hit later.** Skyrim-like breadth bars come from the
   research (`building-asset-breadth.md`, `building-depth-and-variety.md`,
   [0098](0098-variety-is-measured-per-settlement-not-by-a-template-cap.md))
   as numbers the skill reads (`world/sources/placement/breadth-bars.json`).
   Places in the loop are varied inside themselves and between one another,
   grounded in lore and culture, within what the pools allow; the full bars
   are met when the province is built out.
4. **"Good enough" is the place-completeness checklist** (16k § The
   checklist); the rows marked Gate are gates in the loop. People, navmesh,
   interiors and ambience gate on their sockets as data; their systems fill
   the sockets later.
5. **The proving ground is the regression fixture.** It is never walked
   again; every defect found there is an automatic gate on it.
6. **No long tail.** A red that arrives with a lane's diagnosis has its
   cause verified before any brief acts on it; parallel lanes taper towards
   the session's end, and the last lane runs alone and finishes every red it
   meets.
7. **The old exemplar layouts are dropped.** Their types keep the committed
   built-ground footprints through
   `author_type_siting.CARRIED_BUILT_GROUND_M`, so the frozen plot does not
   move; the site dossiers stay as ground evidence. Lilmoth returns as an
   owner-guided whole-city slice.

## Why

Three planned chunks of exemplars and rollout would have had the owner steer
layouts about to be discarded, while the time audit showed most wall clock
went to slow builders and idle waits. A loop on real places, where every
owner defect becomes a rule and a gate, converges on a skill that is proven
type by type.

## Consequences

- The place skill, its lessons and the acceptance receipt are 0100; layers
  on an accepted place are [0140](0140-layers-on-a-built-place-never-rebuild-it.md);
  edits are [0128](0128-places-are-edited-in-place-never-rebuilt.md).
- Evidence (the time and place audits) and the superseded speed rules:
  [place-decision-rounds/0099](../research/archive/place-decision-rounds/0099-as-recorded.md).
