The build VM has been started (by the owner from the AWS console, or by the wake workflow). The previous session did
not stop itself cleanly, so its work may be part-way: it may have been stopped as idle (the idle timer, or the
CloudWatch CPU backstop while it waited on a long AWS step), stopped by hand, or Claude Code may have died. The VM is
on demand, so it was not a spot reclaim. Nothing is assumed lost: pick the work up from where the tree and the jobs
show it got to, following CLAUDE.md.

1. `cat ~/.argonia/state/agent-wake-pending` (a background job that ended while no session was alive leaves its line there); act on it, then delete the file.
2. Read docs/PLAN.md and docs/PROGRESS.md, `git log -10` and `git status`, `tooling/job_guard.sh status`, and run `python3 tooling/owner_inbox.py --unread` for owner comments since the last stop.
3. Continue the current phase from the last commit, the uncommitted files in the tree and the jobs. Long jobs resume under `tooling/job_guard.sh`.
4. Stop only when the work is complete or a blocker needs the owner; then post to the owner (`tooling/owner_inbox.py --post`) and run `tooling/agent_stop.sh "<why>"`.
