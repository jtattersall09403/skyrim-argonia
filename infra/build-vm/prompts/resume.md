The build VM stopped while work was in progress (Claude Code died, or the machine was stopped while an agent or a
job was active; it is on demand, so not a spot reclaim). Resume from where the work got to, following CLAUDE.md.

1. First: `cat ~/.argonia/state/agent-wake-pending` (a background job that ended while no session was alive leaves its line there); act on it, then delete the file.
2. Read docs/PLAN.md and docs/PROGRESS.md, `git log -10` and `git status`, and run `python3 tooling/owner_inbox.py --unread` for owner comments since the last stop.
3. Continue the current phase from the last commit and the uncommitted files in the tree. Long jobs resume under `tooling/job_guard.sh`.
4. Stop only when the work is complete or a blocker needs the owner; then post to the owner (`tooling/owner_inbox.py --post`) and run `tooling/agent_stop.sh "<why>"`.
