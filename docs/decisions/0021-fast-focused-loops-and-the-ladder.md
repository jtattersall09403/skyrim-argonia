# 0021: Fast focused loops with eyes on the cheapest rung of the ladder; journeys are eyeless

**Status:** decided 2026-10-28. Owner: keep the "fast focused loops with eyes including feature and seams"
approach and its ladder, "updated for our new infrastructure and context"; then: "the lane that builds the
feature subset should test both the feature itself and its joins in the same lane and loop", and "journeys
should only be headless tests, it's super buggy trying to get an agent to actually play the game for more than
a few seconds, and we ended up just having loads of harness and capture issues rather than testing anything
useful".

## Decision

1. The old project's loop doctrine (its `docs/phases/loops.md`, decisions 0155 and 0156) is carried as
   **[docs/loops.md](../loops.md)**: each building block checked once, at the cheapest level that reliably
   proves it, then composed once; many small loops in parallel, each with its own eyes; measure everything,
   diagnose all, fix once, re-measure; the harness tested before use; the planner watching loop speed.
2. **One lane, one loop, the feature and its joins.** The lane that builds a feature subset tests the subset
   itself *and* its joins to what is already built, in the same loop. There are no separate seam lanes. The
   later system owns the join with the earlier one (combat owns combat → HUD bars; magic owns poise break →
   cast interrupted). Each brief lists the joins its lane owns.
3. **Journeys are eyeless.** A journey is a script as data played by two runners with no eyes: the **core
   runner** (L2: our own systems' rules, no game, on the build VM) and the **game runner** (L4: the same
   script inside Skyrim on the GPU box through the agent bridge, reading state and events only). No
   screenshot, clip or reader is part of a journey, and no agent pilots the game by looking. The runner moves
   the player between steps by teleport. Each step is a short action: a real input or the activation call the
   input makes. Both runners green closes a journey; then the owner plays it in the studio (L6).
4. **Eyes are stills, and a clip only with a reason.** A reader judges stills: UI screens at L3; places,
   pieces, poses and states at L4 through bridge stills from fixed vantages. A short clip (L5, 3–8 s) is
   allowed only for a join no still can show (a screen transition, the near-to-distance hand-off, combat feel
   beside DSR). The reason is written in the brief.
5. **Adapted to this infrastructure.** Skyrim cannot run without a GPU. So the old "headless play" rung splits
   into the L2 core runner (no GPU) and the L4 eyeless game runner (GPU box). The old "motion" rung becomes
   L4 event-timestamp checks, plus L5 clips only for how motion looks. RunPod is replaced by the AWS GPU box,
   with a lock and per-pass batching. Every L4 scene starts in the studio (decision 0022), never by playing
   the new-game flow.

## Why

The old 2.10 spent most of its sessions on the filming rig rather than the game (old 0156). Separate seam
loops repeated mechanics their own lanes had proved, and agents driving the game by eye for long stretches
turned every harness defect into a false red. Checking state, not pixels, keeps a journey failing only on the
join it tests.

## Consequences

- Every chunk brief has a **Loops** section: its subsets with their levels, the joins it owns, its journeys
  (both runners), and any L5 reason.
- The journey script format, both runners and the studio's scene staging are built and proved in chunk 0.4
  before any lane uses them.
- The testing levels L1–L6 in ways-of-working and CLAUDE.md are the levels of this ladder.
