# tooling

| File | What it does |
|---|---|
| `guards/no_assets.py` | Refuses game or mod files, retail magic bytes, files over 1 MB and decompiler text (`--staged`, `--tree`; decision 0003) |
| `guards/allowlist.txt` | The only paths allowed over 1 MB |
| `guards/install_hooks.sh` | Installs the guard as the git pre-commit hook (`make hooks`) |
| `shell_guard.py` | Claude Code Bash hook: no sleep or polling, no destructive git, no pkill, no reading secrets |
| `lane_commit.sh` | Commits exact paths and lands them on main; never stashes or checks out |
| `job_guard.sh`, `job_resume.sh` | Long jobs in the background that survive a spot reclaim and resume at boot (decision 0037); the play-machine lock |
| `agent_stop.sh` | Stops idle machines when the agent is done |
| `worktree.sh` | A clean worktree at origin/main for a parallel agent |
| `lane_land.sh` | Lands a lane: rebase on main, the gate, push, the main tree fast-forwarded, the worktree and branch removed |
| `disk.sh`, `tidy.py` | What fills the build VM's disk, and the one tidy of disk, lane worktrees and bucket; runs by itself (docs/machine-moves.md) |
| `owner_inbox.py` | The only way to post to, ack and close owner issues |
| `session_tokens.py` | Tokens and list-price dollars per model from the transcripts (`--brief`, `--last N`) |
| `brief_template.py` | Writes and checks a short brief for a delegated agent (`--write`, `--check`) |
| `check_links.py` | Every relative markdown link under docs/, story/ and CLAUDE.md resolves |
| `tests/` | Unit tests for the above; run by `make check` |
