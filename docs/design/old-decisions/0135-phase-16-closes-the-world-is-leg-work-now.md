<!-- imported unchanged from elder-souls-argonia docs/decisions/0135-phase-16-closes-the-world-is-leg-work-now.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0135: Phase 16 closes: the world will get built, it is leg-work now

**Status:** accepted.
**Closes:** Phase 16 and Part 1 of [0134](0134-four-parts-de-risk-first.md);
[0129](0129-walk-12-contracts-facts-motion-light-plan-door-pairs.md)'s
open rows. **Evidence:** the [16x brief](../phases/16-foundation-and-places/16x-closing-fix-round.md)
§ Outcome and the lane reports under `lanes/16x/`.

## Why

0134 made Part 1's exit the owner's confidence that the world can be
built, not the 16k exit bar. The 16x round took the owner's essentials
from the last walk as one fix table and closed each by its own gate. What
the round proved, ruled and left over is recorded here so Part 2 starts
from it and 4.1b resumes from it without re-reading the round.

## What Part 1 proved

1. **The frozen world.** Hydrology, terrain, water, the apron, routes,
   vegetation and the macro plot were built once and frozen (16a to 16g);
   places adapt to the ground through their own typed overlays
   ([0102](0102-a-place-carries-its-own-ground-and-hands-over-nothing-it-can-check-itself.md)).
2. **The place types passed.** Sixteen places published from the build
   ledger across the signed types (settlements, camps, shrines, works,
   water villages, dungeon entrances and a lair), each walked and fixed
   by the 16k loop; cities are hand-built by district
   ([0133](0133-cities-are-hand-built.md)).
3. **The loop works.** Walk, one diagnosis across all findings, one fix
   batch, gates and renders re-measure, walk again
   ([0099](0099-places-are-built-in-a-loop-until-the-skill-is-proven.md),
   [0128](0128-places-are-edited-in-place-never-rebuilt.md)).
4. **The gates that now exist.** Besides the walk-12 set (facts,
   published sockets, water motion, `doors.open`, `interiors.dark`, the
   sign host rule), these also gate: `cliffWay.connected` (a way from
   the camp path to the water with no block and steps under 0.45 m),
   `mount.deckPatch` (a mounted piece rests on a contact patch of its
   parent's up face), `water.record` (buoyant rest, tethers, moored hulls,
   `water.buoyantFit`), `lights.deck` (every walkable deck point within
   6 m of a light), `solid_check` (every shell placement yields a runtime
   solid), the groundcover texel scan (the build fails over 2 percent
   near-black opaque texels), `endFaceRule`, `cutDatumRule`, the laid fit
   (a pitched lying piece judged on its underside ends, within 0.05 m),
   province budgets printed before design (`wb.py next` step 0 and
   `session start`; `es.check("all")` runs the province gates),
   `breadth.province` counted per region, and the lair light lint (a lair
   is lit by natural sources only).

## Rulings

1. **Breadth per region.** The top shell family cap (3) counts per
   region, because regional sameness is what a walker sees.
2. **Root rotation dropped by plugin base type.** The kit import drops
   a NIF root's rotation for the record types the engine draws as
   statics (STAT, FLOR and kin) and keeps it for MSTT, MISC, INGR, ALCH
   and WEAP (`build_kit.root_rotation_ignored`); the affected kits were
   rebuilt and the mounts, sink and abuts re-mined incrementally.
3. **Hanging plants never mount parents.** A `plants/hanging*` piece is
   never a mount parent; a merge keeps only pairs whose parent still
   qualifies.
4. **Paths mean ownership.** A lane's Paths are what it owns and others
   keep out of; it edits what the job needs and names the rest shared.
5. **A lane waits only on child agents.** It ends the turn with
   `waiting: <child labels>`; jobs run foreground in parts, and it never
   polls.

## What 4.1b inherits

- Helstrom's three houses fail `pathReach`; the city resumes by
  district ([4.1](../phases/4-buildout/4.1-before-scale.md) Starting state).
- The `P1` rows in the [polish backlog](../phases/P-polish/backlog.md):
  the `ayleidkit:` ids without pairs; shoring along the Gang Ground way
  down and the Voriplasm Vault threshold and ground read; dock corner
  laying once the corner pair is confirmed; deck children riding buoyant
  hulls; the root scale and translation check; 0129 item 9; the combined
  tooling row (a door in a kit, `commit_hunks.py`, `whatchanged`).
- The 16k exit bar (two unattended passes per type) unchanged.

## Consequences

- PROGRESS holds Phase 16 and 16x status.
- Side lanes belong to the chunk that owns their work (2.7, 2.8, 2.14,
  the Part 2 performance section); ledgers of the 16a to 16h briefs live in
  `research/phase16/`.
