Work stopped while in progress (a spot reclaim, a manual stop, or Claude Code dying without a reboot, such as an
OOM kill; no clean-stop marker was written). Resume, following CLAUDE.md:

1. Read docs/PROGRESS.md, every `in progress` row and its lane hand-off note, `git log -10`, and
   `python3 tooling/owner_inbox.py --unread` for owner comments since the last stop.
2. Revive the lanes: `~/.argonia/planner-lanes.md` lists each running lane's agent id; SendMessage each id to resume
   it from its transcript (say what happened and that its uncommitted files are still in the tree). Relaunch from
   the lane's hand-off note and last commit only if its transcript is gone. Recreate the 20-minute planner tick if the goal
   asked for one: its first job is to ship one concrete optimisation per tick (a tool, a pattern, an approach, a root
   fix) and only then check health; and the memory and disk watcher (`python3 -u ~/.argonia/memwatch.py` under Monitor). A GPU-box job that was
   interrupted reruns from its last checkpoint under tooling/job_guard.sh.
3. Close any owner issue whose answer is already recorded (`owner_inbox.py --close N --commit SHA`).
4. Continue the work. Stop only when it is complete, when a critical blocker needs the owner, or at a handover the
   owner asked for; then post the owner issue and run `tooling/agent_stop.sh "<why>"`.
