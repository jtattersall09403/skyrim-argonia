<!-- imported unchanged from elder-souls-argonia docs/decisions/0155-journeys-are-staged-scenes.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0155 Journeys are staged scenes, looped until they pass

**Decision (owner, 2.10 run).**

## Context

A phase closed on a last cross-lane shoot: its journeys walked real slice
places, then played once more on the deployed build before the packet.
Each run spent most of its time on what a real place happens to hold at
an hour (who wanders into sight, which prompt wins, a loading screen
over a far teleport), not on the transitions the journey exists to
prove; and the shoot repeated seams the building lanes had already
judged.

## Decision

1. **A journey is a staged scene.** Each phase names a few end-to-end
   journey types. Each is a scene that sets its state once, at step 0
   (the place or fixture, the hour, who stands where, carried items,
   skills, the dice, and later lock, zone and standing state), then
   plays the player's real inputs, films strips and measures.
2. **It runs after the focused loops and loops until green.** Journeys
   start when every feature-and-seam loop of the phase is judged; each
   journey reruns, its findings fixed at source, until it passes. Then
   the phase's journeys are done: no further shoot follows.
3. **Nothing plays on real slice places or the deployed build as a
   gate.** A staged scene may stand on a slice place's ground; what it
   proves comes from what it set and what it played, never from the
   place's state at that hour.
4. **Shipped pieces only.** A staged scene is built from the components,
   systems and data the game and studio ship, through the setters the
   game itself calls; no stub stands in for a system. That is why a
   green scene is evidence for the studio.
5. **A script never sets what it tests.** A stage kind that decides an
   expected key (staging an observer's suspicion and expecting the eye,
   staging a lock open and expecting it opened) proves nothing; state
   is set at step 0 only, and every later state is reached by play.

## Consequences

The journey schema gains a typed `stage` block on step 0
(`packages/scene/src/interact/journey.ts` `JourneyStage`, `STAGE_NEEDS`);
the preflight's c9 reds a stage kind that decides an expect key of the
same script, a kind no runner sets, and a stage after step 0
(`tooling/gpu-lane/preflight/script-checks.mjs` `checkStage`,
`journey-keys.mjs` `STAGE_READS`). A state kind no runner can set yet is
listed in the `journey-author` skill and built by the lane that owns
that system. [loops.md](../phases/loops.md) § Rules holds the rule; the
phase briefs and the GPU lane route to it. The owner still plays the
finished build (a brief's § Owner play); that is play, never a gate.
