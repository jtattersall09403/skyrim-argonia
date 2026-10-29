<!-- imported unchanged from elder-souls-argonia docs/decisions/0154-the-build-gates-the-deploy-the-checks-run-beside-it.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0154 The build gates the deploy; the checks run beside it as a signal

**Decision (owner, 2026-10-21).** On a push to `main`, the Pages deploy
waits only for the studio and game build. The gate matrix (vitest,
python, placement, regen, docs, typecheck) runs in parallel and no longer
stands in front of the deploy; when a gate reds, a `gate-signal` job posts
one comment on the owner inbox issue with the run URL, and the planner
fixes forward on the next push.

**Why.** The owner walks only the deployed build, minutes after a push.
Locally we run only the checks affected since the last green stamp
(owner rule), so the CI gates are the one full-tree sweep: on this day
they caught three rounds of reds (key item ids against the item schema,
a tool with no scope row, a derived key id test, the PROGRESS word
budget, a standards gate on zone-owner references) that the local
subset could not see. Dropping them loses that sweep; keeping them in
front of the deploy cost three twelve-minute loops before anything could
be walked. A red gate is a defect to fix forward, never a reason to
withhold a build that compiled.

**What stays.** The build is a gate: a build that fails deploys nothing.
The pre-deploy phone check runs locally before every merge (the recipe
in `phase_chain.json`). A blocker red found by a gate is fixed before
the owner is told a round is deliverable; the packet names it.
