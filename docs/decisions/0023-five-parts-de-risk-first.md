# 0023: Five parts, de-risk first: foundation, the core loop, the slice in two tracks, the shell, the build-out

**Status:** decided 2026-10-28; adapted 2026-10-29 by [0027](0027-build-in-the-order-of-the-usps.md): Part 1 is the
first place (people, talk, a quest, the sheet, rest and death, combat on the tuned stack), not the host-risky
systems; the world track starts after 0.4 beside Part 1; the five parts and the gates stand. Adapted again by
[0029](0029-part-0-is-one-sequence-not-spikes.md): Part 0 has no spikes (each proof is the first step of the chunk
that builds the thing) and no time estimates; the cost paragraph below keeps its reasoning as history only. The owner asked for a critical review of the old project's four parts and of
this repo's first plan (P0–P10), and for the best approach from here: "ok that's what we were *going* to do,
what do I think we *should* do now".

## What the two plans got right and wrong

**The old plan** (its `docs/phases/README.md`, old 0134): world build, then a slice of every system in the
studio, then the game shell, then a build-out in packets.
- **Right:**
  - de-risk before scale;
  - systems whole, content thin, and what the player meets complete;
  - play in a studio on shipping code (old 0149);
  - the real front door built only once the slice works;
  - three polish queues, and a blocker is never polish.
- **Wrong here:** world first. In three.js the world *was* the risk (a renderer, terrain, water and kits built
  from nothing). On Skyrim the engine renders, so the world is mostly data conversion. Its two hard parts,
  navmesh and LOD, are tested on a sample by 0.4's block.

**This repo's first plan** (P0–P10, by system).
- **Right:** go/no-go spikes up front, and the guardrails (nothing shipped, a pinned runtime, DSR as the combat
  spec, the immersion gate).
- **Wrong, three ways:**
  - **Late joins.** Every system was built in isolation and joined only at P7. In Skyrim modding the costly
    failures are the joins: conflicts in the mod stack, script lag, crashes where combat frameworks, PrismaUI
    views, dialogue interception and the co-save meet.
  - **Untested feel.** Nobody felt DS1 combat through the stream until P5, after the world and the soul were
    built. The old combat was bad, a DS1 parry window is a few frames, and the stream adds tens of
    milliseconds. That is the host risk most likely to change the whole plan, and its fallback (0001: OpenMW)
    is cheap only before the world and systems exist.
  - **Porting the old rule code at all.** It planned to port the old project's rule code to C++. Decision 0026
    (2026-10-28) settles this the other way: the old code is goal evidence only, and each goal is met with
    Skyrim's own systems first (1.1 §a's native map).

## Decision

1. **Five parts, ordered by remaining uncertainty:**

   | Part | De-risks | Ends when the owner can say |
   |---|---|---|
   | 0 Foundation | that agents can build, test and stream Skyrim from AWS; the go/no-go spikes | "I dropped into the studio on my phone and teleported around" |
   | 1 The core loop | that every system can join on the host, and that DS1 combat feels right through the stream | "this is the game I want; it is worth building" (the last cheap moment to change host) |
   | 2 The slice, two tracks | that the province can be generated and every system exists whole on the slice places | "I played the slice in the studio; every system is real; the world is leg-work" |
   | 3 The game shell | that a player installs, starts a new game and lands in the slice | "I started a new game and reached the open world; a stranger installed it" |
   | 4 Build out sideways | nothing new: packets scale what is proven | "the whole province is populated, every quest completes, and it is released" |

2. **Part 1 is a thin thread through every system that is risky on this host, on one place.** It uses Claywater Station (G4's sample block)
   and the proving ground. Each of those systems gets its first rung at its final interface, so later chunks deepen it
   and never replace it. Barter and quests are left to Part 2 as well-trodden ground:
   - talk with topics;
   - carry, equip and read;
   - one weapon class against one archetype with measured DS1 numbers;
   - die and recover vastei; rest, level and save;
   - climb, swim, and sail one boat.

3. **Part 2 runs two tracks side by side.** They share the GPU box well, because the world track checks
   mostly at L1 on the build VM and the systems track checks mostly at L2 and L4.
   - **The world track (2.W):** the whole worldspace generated once, then the slice places ported in waves.
   - **The systems track (2.1–2.17):** every system made whole on those places, in dependency order.

4. **The rules decided by the old plan hold:**
   - **Final-shaped from the first line:** the studio only observes and teleports (0022).
   - **Scaled data shapes, thin content**, with wide loads where they are cheap.
   - **What the player meets is complete.**
   - **Three polish queues:** `P1 before-scale`, `P2 rolling`, `P3 final`.
   - **Cities and the opening's places are built with the owner.**

5. **The slice is the old slice.** That means the sixteen places the old project built and walked, its two
   routes and the wild between them. Helstrom and the cities wait for chunk 4.1.

6. **Immersion is a gate, not a late phase.** Every reachable element has a verdict from Part 2's close. Each
   packet's elements enter compliant. Unreachable rows never block.

7. **Briefs are written just in time, with nothing dropped.** Design content (formulas, rules, counts, rulings)
   is written now, in the brief that will build it. The steps and Starting state of a later chunk are rewritten
   when the chunk before it closes. ACCOUNTING maps every owner requirement to its chunk.

8. **Ids are `<part>.<chunk>`** (0.4, 1.3, 2.8, 2.W3). The part README holds the chunk table.

## Why the thread is worth its cost (owner: "will testing stuff at one location then doing the part 2 slice actually be any cheaper?")

It is not cheaper when nothing goes wrong; it is insurance, priced like this.
- **The cost, if everything works:** about 2–3 weeks on a project of roughly 18–30 months (PLAN §5). Every rung
  is final-shaped, so Part 2 deepens it rather than redoing it. The real extra is the second visit to each
  system (context, a second brief), the core-loop journey, the soak and the verdict.
- **The saving, if something is wrong with the host:** combat that cannot feel like DS1 here, dialogue
  interception that breaks, or a mod stack that crashes once our pieces meet. Without the thread, these surface
  at the slice's close, about 6–9 months in. With it, they surface about 3 months in. That saves roughly 3–6
  months of building on a failing base, while switching hosts is still cheap.
- **The odds:** at the planner's judgement of a 15–30% chance of such a finding for a conversion this ambitious,
  the expected saving (about 0.5–1.5 months) exceeds the cost. Smaller integration bugs found early are also
  cheaper, because less is built on them.
- **How to keep the cost down:**
  - the thread holds only the host-risky systems; barter and quests went to Part 2;
  - Claywater Station costs nothing extra, because 0.4 builds that block anyway;
  - the cheapest de-risk of all runs first, in 0.0: whether the game can be played through the stream at all,
    for a few dollars and days.
- **What dominates total cost** is not the part order. It is the time per in-game check and the owner's
  turnaround, which is why the studio's scene-switch targets (0.4) are numbers.

## Consequences

- The P0–P10 phase files are replaced by `docs/phases/0-foundation/` to `4-buildout/`. Every P-number
  reference is rewritten in place.
- The native map (where each rule lives, decision 0026) is 1.1 §a's first step and sets how 1.1 builds ArgoniaCore.
- The planner reads the measured cycle times at each part's close (no estimates, 0029 §6).
