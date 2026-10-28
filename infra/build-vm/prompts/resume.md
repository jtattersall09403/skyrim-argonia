The build VM restarted while work was in progress (a spot reclaim or a manual stop; no clean-stop marker was
written). Resume, following CLAUDE.md:

1. Read docs/PROGRESS.md, every `in progress` row and its lane hand-off note, `git log -10`, and
   `python3 tooling/owner_inbox.py --unread` for owner comments since the last stop.
2. Subagents cannot be revived: relaunch each lane from its hand-off note and last commit. A GPU-box job that was
   interrupted reruns from its last checkpoint under tooling/job_guard.sh.
3. Continue the work. Stop only when it is complete, when a critical blocker needs the owner, or at a handover the
   owner asked for; then post the owner issue and run `tooling/agent_stop.sh "<why>"`.
