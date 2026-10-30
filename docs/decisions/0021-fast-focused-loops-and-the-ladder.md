# 0021: Fast focused loops with eyes on the cheapest rung of the ladder; one lane tests a feature and its joins; journeys read state and keep stills

**Status:** decided 2026-10-28; §3 and §5 rewritten 2026-10-29 by [0029](0029-part-0-is-one-sequence-not-spikes.md)
§4 (owner: "why is the game runner 'eyeless', that sounds kind of dumb, don't we need eyes?"). The 2026-10-28
rulings stand: keep "fast focused loops with eyes including feature and seams" and its ladder, "updated for our
new infrastructure"; "the lane that builds the feature subset should test both the feature itself and its joins
in the same lane and loop"; and "it's super buggy trying to get an agent to actually play the game for more than
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
3. **Journeys read state and keep stills.** A journey is a script as data (`tests/journeys/<id>.yaml`) played
   by **one runner** in the game through the bridge (0.3 §d). Its pass or fail is read from state and events
   with timestamps; the runner moves the player between steps by teleport; each step is a short action, a real
   input or the activation call the input makes. **The runner takes a still at every step** and keeps it with
   the run as evidence; a failing step's stills go to a reader with the step's expectation. **Agents also check
   interactively** (owner, 2026-10-30): a fast, targeted check is driven by an agent one action at a time, reading
   state after each and looking with stills when needed, so it adapts to fades, NPC movement and other variance;
   what works is kept as a journey, whose waits are on real signals and which an agent re-drives live when it
   goes red. Never long interactive playthroughs (a whole quest or a complicated sequence). Green closes a
   journey; then the owner plays it in the studio (L6).
4. **Eyes are stills, and a clip only with a reason.** A reader judges stills: UI screens at L3; places,
   pieces, poses and states at L4 through bridge stills from fixed vantages; a journey's per-step stills on a
   red. A short clip (L5, 3–8 s) is allowed only for a join no still can show (a screen transition, the
   near-to-distance hand-off, combat feel beside DSR). The reason is written in the brief.
5. **Adapted to this infrastructure.** Skyrim cannot run without a GPU, so the in-game rung is L4 on the game
   machine, from a scene (0022); our own rules are proved at L2 by unit tests of the pure C++ core and the
   Python tools, not by a second runner (the "core runner" of the first draft was harness for its own sake and
   is dropped). The old "motion" rung becomes L4 event-timestamp checks, plus L5 clips only for how motion
   looks. The game machine is one at a time, with a lock and per-pass batching.

## Why

The old 2.10 spent most of its sessions on the filming rig rather than the game (old 0156). Separate seam
loops repeated mechanics their own lanes had proved, and agents driving the game by eye for long stretches
turned every harness defect into a false red. Reading state keeps a journey failing only on the join it tests;
keeping a still per step means a red can be understood without re-running.

## Consequences

- Every chunk brief has a **Loops** section: its subsets with their levels, the joins it owns, its journeys, and
  any L5 reason.
- The journey format, the runner and the scenes are built and proved in chunk 0.3 before any lane uses them.
- The testing levels L1–L6 in ways-of-working and CLAUDE.md are the levels of this ladder.
