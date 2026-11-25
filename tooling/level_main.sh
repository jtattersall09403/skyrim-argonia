#!/usr/bin/env bash
# Bring the main tree, the one the studio serves, level with origin/main: the sanctioned way to level it (in place of
# git restore, checkout of paths, stash or reset --hard). Clears only provably stale leftovers; real unlanded work and
# the owner's edits folders are never touched. Modes and exit codes: tooling/level_main.py.
here=$(cd "$(dirname "$0")" && pwd)
PY=$(ls "$HOME/.argonia/venv/bin/python" 2>/dev/null || command -v python3)
exec "$PY" "$here/level_main.py" "$@"
