The owner replied on an owner issue, which woke the build VM. Following CLAUDE.md:

1. Run `python3 tooling/owner_inbox.py --unread` and read every new owner comment, whatever it says.
2. Read docs/PROGRESS.md and the hand-off note of the chunk that was waiting on the owner.
3. Record any ruling (decision record and owner brief), close every answered issue at once with `owner_inbox.py --close N --commit SHA`, and continue
   the work the reply unblocks. Stop only when it is complete, when a critical blocker needs the owner, or at a
   handover the owner asked for; then post the owner issue and run `tooling/agent_stop.sh "<why>"`.
