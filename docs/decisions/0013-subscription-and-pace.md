# 0013: Claude subscription and pace: start on 5x, move to 20x for parallel content

**Status:** recommendation 2026-10-27; owner call O-2 confirms.

## Context

The owner is choosing between a 20x plan (lots in parallel, ~60 h/week) and a 5x plan spread over ~120 h/week
(cheaper VM and subscription, less done per week). The 20x plan has 4x the 5-hour-window usage of 5x but only
about double the weekly usage. Universal-modder's evidence: a verified mechanic port takes 4 days to 2 weeks of
agent time with a human checking builds, and in-game iteration (one GPU box, one game instance) is the
bottleneck, not tokens.

## Decision

1. **Parts 0–3 run on 5x.** They are spike- and oracle-bound: one GPU box runs one game at a time, and most
   work is sequential (a plugin waits for its in-game check). Parallelism beyond 2–3 lanes would queue on the
   GPU box. Part 2's two tracks (the world on the build VM beside the systems on the GPU box) may justify
   20x earlier: the planner measures it at 1.8 and asks O-2 with the numbers.
2. **Part 4 (the build-out) is where 20x pays**: many independent region packets, dialogue rounds and
   places, mostly checked at data and still-image levels, with GPU checks batched.
3. Re-evaluate at each part close from measured numbers: tokens per week used vs the plan's weekly cap,
   lanes waiting on the GPU box, owner check-in turnaround.
4. The build VM size follows the plan: `m7i.xlarge` on 5x; `m7i.2xlarge` only if measured memory or CPU
   queueing blocks parallel lanes on 20x (cost-checked first, decision 0008).
