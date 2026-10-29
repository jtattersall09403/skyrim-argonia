<!-- imported unchanged from elder-souls-argonia docs/decisions/0034-build-sequence-rework.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0034 — Build sequence rulings: freeze-gates, Morrowind ferries, performance at every gate

**Status** the phase order is superseded by
[0134](0134-four-parts-de-risk-first.md) (four parts, de-risk first; the old
phase ids map in the [plan](../phases/README.md)); the rulings below stand.

These are the rulings that outlived the risk-first phase order they were
written with.

1. **Risk first.** Order work by the risk it retires: vegetation at scale and
   place quality were the dealbreakers, so they ran before well-understood
   sourcing work. 0134 applies the same principle to the whole game.
2. **Freeze-gates, not start-gates.** Combat-space probes and compiled
   numbers gate a packet's *freeze*, not the start of its authoring. This is
   safe because content is authored semantically
   ([module 76](../world/76-stats-progression.md) §128) and compiled to
   absolutes later.
3. **Ferries and boat travel are Morrowind-style**: talk to the ferryman,
   pay, arrive, over a geographically sensible service graph; NPC passengers
   are set dressing. Player-boat cargo, passengers, repair, ownership and boat
   combat wait until a quest brief or playtest demands them.
4. **Sound is authored from the ecology**: creature calls and ambience are
   placed from the fauna data, so they follow it, and land before the voice
   and memory budgets lock.
5. **A phase may split** when risk ordering favours it; ecology splits into
   flora (with the vegetation system) and fauna and content (behind combat
   and stats).
6. **The asset catalogue spans the whole permitted pool** (BM&V, Tropical
   Skyrim, the Xanmeer kit, vanilla and candidate tables, creatures
   included): catalogue wide, kit-compile deep on demand.
7. **Mine the shipped worlds for rules**: plugin placement, grass, region
   and ecology statistics become compiler defaults; rules, never lifted
   places ([00-core](../world/00-core.md) rule 6).
8. **The province rolls out by region packet**, exemplar first, each
   placement round proposing its contrast set at the start.
9. **Performance cannot wait for a late phase.** Every placement round ships
   through the tiered streaming and LOD architecture as content lands, and
   the province stays loadable and playable in the owner's browser at every
   gate; late-phase items (draw rings, impostors, caps, compression) are
   pulled forward when scale strains it.
10. **Loot and traps are authored semantically** like actors (module 76
    §128.2).
