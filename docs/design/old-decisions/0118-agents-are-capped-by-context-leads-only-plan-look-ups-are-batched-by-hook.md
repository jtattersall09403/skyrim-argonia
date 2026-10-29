<!-- imported unchanged from elder-souls-argonia docs/decisions/0118-agents-are-capped-by-context-leads-only-plan-look-ups-are-batched-by-hook.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0118 — Work is chunked to one context and monitored; look-ups are batched by hook

Status: accepted (2026-10-01); rewritten in place 2026-10-14 (the lead tier
and child polling removed, the hand-off marker raised; see
[0079](0079-cheap-hands-expensive-head-agent-cost-controls.md)). Evidence:
[method review r6](../research/archive/phase16-evidence/method-review-r6.md) and
[the 2026-10-14 review](../research/archive/agent-process-reviews/instruction-and-agent-tree-review-2026-10-14.md).

## Context

What lands in an agent's context is paid at write price once, then at read
price on every later turn, at that agent's model rate (0079). Method review r6 found Opus agents running
past 200 turns at 160k-290k context, look-up and heredoc turns at 19-28 % of
Opus turns, poll loops slipping past the guard, and untimed fix rounds.
Fourteen days later, the lead tier and child polling showed themselves to
be relay cost without matching benefit.

## Decisions

1. **Chunking, never a cap.** Every brief is one deliverable an agent
   finishes in one context: one mechanism, one place or one tool. It names
   the hand-off note the agent writes when it returns. The next chunk starts
   a fresh agent from that note. The planner monitors elapsed time against
   expected; a lane that is over is a diagnosis (CLAUDE.md § Gate and jobs).
2. **Hand-off marker** at 300k for every non-Haiku agent, 100k for Haiku;
   agents only (the planner runs its phase to the deploy, 0083). Session
   cost grows with the square of its length, so a chunk is sized to finish
   well inside the marker. The one-hour
   cache expiry is a cliff: an idle wait over an hour re-reads the whole
   context at full price.
3. **Look-ups are batched by hook, for the planner.** `shell_guard.py`
   refuses the planner's searches across many files; workers search
   directly. For every agent it refuses a heredoc that writes a tracked
   file (the Edit tool exists).
4. **Cost awareness, no limit tracking.** `session_tokens.py` reports
   dollars per window, per model and per agent type, priced per model. No
   script estimates a weekly limit or a pace.
5. **One close per batch.** Inside an open review batch the reviewer does
   not fire again; review fires go to an append-only log that
   `workflow_drift.py` counts.
6. **No polls, no sleeps.** A parent waiting on children ends its turn with
   `waiting: <labels>` and is woken by each report. A subagent runs its own
   jobs in the foreground with a timeout up to 600 s, or waits on its own
   job's done-marker with `lane_wait.py --files`. It never ends its turn on
   a background job, because that job's end does not wake it.
7. **Fix rounds are timed.** `wb.py round --walk N` opens the round in the
   build ledger; `--end-walk` ends it.

## Where each lives

`shell_guard.py` (3, 6), `agent_guard.py` (2's notice), `session_tokens.py`
(4), `review_gate.py` + `workflow_drift.py` (5), `wb.py` `walk_clock` (7);
tests beside each.
