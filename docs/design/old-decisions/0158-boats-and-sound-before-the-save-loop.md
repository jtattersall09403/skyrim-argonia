<!-- imported unchanged from elder-souls-argonia docs/decisions/0158-boats-and-sound-before-the-save-loop.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0158 — Boats and sound before the save loop

Status: accepted (owner, 2026-10-23). Reorders the end of Part 2 set by
[0134](0134-four-parts-de-risk-first.md); replaces "the boat controller
last and droppable" ([0034](0034-build-sequence-rework.md)).

## The problem

The plan ran 2.13 (save, load, the coverage gate, the owner's
playthrough) before 2.14 (sound) and the boat controller (2.15c), with
only the boat records and moorings (2.15b) ahead of it. The Part 2 exit
would then save and test a slice that still lacked the boats and the
sound, and the owner would play it without them.

## The rulings

1. **Order: 2.12, 2.9c, 2.15 whole, 2.14, then 2.13.** 2.13 is last in
   Part 2 and covers every system that landed before it.
2. **Boats are tried in full.** All of 2.15 runs, controller and crew
   included. If a few attempts fail, the owner may call a revert and
   drop them. Only the owner makes that call.
3. **Each system saves itself as it lands.** Boats register their save
   family with the 2.1 contract in 2.15, as every system has done in
   `packages/save/src/families/`. 2.13 adds the coverage gate, the
   scripted loop (which now sails) and the playthrough, not the first
   serialisers.
4. **Sound runs after boats** so that boats are heard, and before 2.13
   so that the owner's playthrough has sound. It no longer runs as a
   side lane beside other phases.

## Consequences

- 2.13's Starting state is written by the agent that closes 2.14.
- The phase chain still needs one owner ask per phase; this record sets
  the order, not the queue.
