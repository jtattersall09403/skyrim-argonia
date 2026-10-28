# 0021: Fast focused loops with eyes, for features and seams, on the cheapest rung of the ladder

**Status:** decided 2026-10-28 (owner: "Has our 'fast focused loops with eyes including feature and seams'
approach been carried over… with the idea of the ladder where you use the cheapest/fastest approach possible that
can reliably prove what needs proving. I liked it as a conceptual way of working. It will need updating for our
new infrastructure and context").

## Decision

1. The old project's loop doctrine (old `docs/phases/loops.md`, decisions 0155 and 0156) is carried whole as
   **[docs/loops.md](../loops.md)**: each block checked once at the cheapest level that reliably proves it,
   composed once; many small feature loops and seam loops in parallel, each with its own eyes; staged scenes that
   set state at step 0 and never set what they test; filmed seams only with a stated reason; journeys last, looped
   until green, then the owner plays; measure everything, diagnose all, fix once, re-measure; the harness tested
   before use; the planner watching loop speed and fixing slow methods first.
2. **Adapted to this infrastructure:** Skyrim cannot run headless, so the old "headless play" rung splits into L2
   core simulations (our own systems' joins, seconds, no GPU) and L4 staged in-game scenes on the AWS GPU box
   (engine joins); the old "motion" rung becomes L4 event-timestamp checks plus L5 clips only for how motion
   looks; RunPod is replaced by the GPU box with a lock and per-pass batching.
3. **Every phase file has a Loops section** naming its feature loops, its seam loops (each with two owners) and
   its journeys, each with its level.
4. The testing levels L1–L6 in ways-of-working and CLAUDE.md are the levels of this ladder.
