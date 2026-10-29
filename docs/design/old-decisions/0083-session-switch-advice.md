<!-- imported unchanged from elder-souls-argonia docs/decisions/0083-session-switch-advice.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0083 — A planner session runs its phase to the deploy and never hands off for cost

Extends 0079 (the bill is turns x context). Subagents keep their hand-off
marker (0118: 100k Haiku types, 300k every other agent).

## Decision

The planner session that starts a phase drives it to its deploy. It never
ends itself to save cost: no session-cost line, no hand-off note, no
queued successor within a phase. A fresh planner session starts only at a
phase boundary (`phase_chain.py --queue`, on the owner's ask) or after a
crash; it resumes from `lanes/handoff/STATE.md`, the phase's
`docs/PROGRESS.md` row and `lane_status.py`.

- The queued goal's completion clause is one sentence
  (`phase_chain.CLAUSE`): complete when everything is deployed and Pages
  is green.
- The planner's per-turn hook prints the lanes line only
  (`lane_status.py --line`: running lanes, those past their hand-off
  context, the `lane_watch` findings).
- `agent_guard.py` nudges agents past their marker; the planner gets no
  nudge.

## Why

A measured audit of ten planner hand-offs (lanes/2.10b-handoff-audit/report.md)
found the saving small: a well-timed hand-off nets about 2 to 4 USD over
the next 100 steps, against 1.1 to 2.6 USD of orientation, and mistimed
ones cost more than they saved. The larger cost was unmeasured by that
model: a planner near a hand-off stops launching lanes in parallel and
waits for live ones to finish, so the phase runs slower. Parallel lanes
are worth more than the re-read saving.

## Owner check-ins

Plain English, one check per bullet, studio URLs with coordinates, and how
to reply; posted with `owner_inbox.py --post`.
