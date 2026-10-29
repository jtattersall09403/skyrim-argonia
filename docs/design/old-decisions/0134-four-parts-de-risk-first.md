<!-- imported unchanged from elder-souls-argonia docs/decisions/0134-four-parts-de-risk-first.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0134: Four parts, de-risk first: the vertical slice before the world is full

**Status:** accepted.
**Supersedes:** the phase queue of 0034 and 0062 (order only; their
rulings stand), the seam policy of 0038 (the build-out register is
archived; game systems are no longer deferred past the world build),
the 16k exit as Phase 16's close (0099: the exit bar moves to Part 4).
**Plan:** [docs/phases/README.md](../phases/README.md).

## Why

Building the world and then the game defers every game-system risk to the
end. The owner is confident in the world build: the remaining place work is
leg-work. The unconfident part is everything parked in the build-out
register: dialogue, people, items, crime, quests, magic, saves, the UI,
the shell. Risk should be retired in the order of remaining uncertainty,
and a game whose systems are proven on a thin slice can be built out
sideways with the same tools that populate the studio and the shipped
app alike.

## Decision

1. **Four parts.** Part 1 de-risks world building (closed by
   [0135](0135-phase-16-closes-the-world-is-leg-work-now.md)). Part 2 de-risks every gameplay
   system as a vertical slice played in the studio on the Part 1 places.
   Part 3 makes the shipped app (boot, menus, character creation, the
   opening). Part 4 builds out sideways in region packets with polish at
   three fixed moments.
2. **Package-shaped from the first line; the seam first.** Part 2 opens
   by extracting the studio's renderer and scene orchestration into
   packages and booting `apps/game` on them, so nothing built after is
   studio-only. Save and load are a Part 2 contract from 2.1 and are
   proven end to end in 2.13; Part 3 adds only the slot UI.
3. **Scaled shapes, thin content, complete instances.** Every record is
   designed for Morrowind-scale counts and joined to the world record
   set; it is filled with what the slice touches; what the player meets
   in the slice is complete (every socket, every NPC's dialogue, every
   item). Wide loads are named per brief.
4. **Polish is three queues and a rule.** A defect that breaks immersion
   or blocks a slice action is a blocker in its phase, never polish.
   Otherwise `P1 before-scale` (4.1), `P2 rolling` (inside the packet),
   `P3 final` (4.6, `optional` allowed).
5. **Loops are planned, cheap and sparse.** Measure everything, diagnose
   everything, fix once, re-measure; no GPU, no local studio; harnesses
   in [loops.md](../phases/loops.md); each phase README names its loop
   or has none.
6. **Interiors are measured before they are built.** No interiors phase
   runs on its old plan; 4.1c counts the dungeon-kind records no linked
   furnished cell can serve, prefers re-typing, and the owner rules on
   the remainder's shape (4.4).
7. **Ids.** New phases are `<part>.<phase>` and chunks
   `<part>.<phase><letter>`; Part 1 keeps 16k and 16x. The old ids map
   in the master plan's "where the old ids went" table; decision records
   citing them are read through it and are not rewritten.

## Consequences

- The old plan lives under `docs/research/archive/plan-2026-10-pre-derisk/`;
  `docs/phases/README.md` is the plan.
- The polish backlog has three queues and keeps no struck history.
- Helstrom and the remaining 16k proofs wait for 4.1b.
- PROGRESS.md lists the parts; CLAUDE.md § Goal and § Session start read
  the plan.
