# tooling

| File | What it enforces |
|---|---|
| `guards/no_assets.py` | Refuses game or mod files, retail magic bytes, files over 1 MB and decompiler text (`--staged`, `--tree`; 0003) |
| `guards/allowlist.txt` | The only paths allowed over 1 MB |
| `guards/install_hooks.sh` | Installs the guard as the git pre-commit hook (`make hooks`) |
| `shell_guard.py` | Claude Code Bash hook: no sleep or polling, no destructive git, no pkill, no reading secrets |
| `brief_template.py` | Writes and checks briefs (`--write`, `--check`) and prints a chunk's table row (`--chunk`) |
| `session_tokens.py` | Tokens and list-price dollars per model from the transcripts (`--brief`, `--last N`) |
| `check_links.py` | Every relative markdown link under docs/ and CLAUDE.md resolves |
| `job_guard.sh` | Long jobs in the background, waits within 270 s, the GPU-box lock |
| `agent_stop.sh` | Stops idle machines when the agent is done |
| `owner_inbox.py` | The only way to post to, ack and close owner issues |
| `tests/` | Unit tests for the above, including the word budget for CLAUDE.md; run by `make check` |
