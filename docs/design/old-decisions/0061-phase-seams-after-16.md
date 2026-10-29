<!-- imported unchanged from elder-souls-argonia docs/decisions/0061-phase-seams-after-16.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0061 — The seams after the foundation phase

**Status** superseded: the dungeon and interior split by
[0062](0062-dungeons-are-places-interiors-are-a-late-phase.md), the exemplar
bar by [0099](0099-places-are-built-in-a-loop-until-the-skill-is-proven.md),
the phase order by [0134](0134-four-parts-de-risk-first.md). Two rulings
stand.

1. **One interior mechanism.** The building-interior path (portal and
   foundation records, the interior cell behind each shell from plugin data,
   the door transition, the interior load contract in `packages/`) is built
   once; dungeon portals plug into the same mechanism, so nothing is built
   twice.
2. **No later work touches terrain or water except through typed local
   patches** that fail when they would move a level, a body or a channel
   ([0057](0057-phase16-terrain-once-water-once-places-on-a-frozen-world.md),
   [0059](0059-terrain-built-once-frozen-base-and-typed-patches.md)); there is
   no per-packet terrain or hydrology refinement.
