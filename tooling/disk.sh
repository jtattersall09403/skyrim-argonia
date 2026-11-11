#!/usr/bin/env bash
# The build VM's disk and the private bucket stay lean, by themselves (docs/machine-moves.md, "Tidying is automatic").
#   tooling/disk.sh report              what fills the disk, by kind, and the state of each lane worktree
#   tooling/disk.sh tidy [--dry-run] [--quiet] [--disk-only] [--bucket]
#                                       the one tidy: deletes, never archives; safe to interrupt and to run twice.
#       worktrees   a lane worktree goes with its branch when nothing works in it, nothing in it changed for IDLE_H
#                   hours (default 3) and all its content is on origin/main, compared by content; one with content
#                   that is not on main is kept and named, loudly once idle TIDY_LOUD_H hours (default 24)
#       disk        job spools ended over two days ago, scratch untouched for two days (a session's only once the session has ended), superseded LOD step markers,
#                   cached mod archives the bucket holds (stack.py evict)
#       bucket      under nw/terrain, nw/plugin and nw/lod only what is referenced, or the newest, stays; once a day
#                   (--bucket: now; --disk-only: never). mods/ and every other prefix are never touched.
#       --dry-run prints exactly what would go and why, and what is kept and by which reference.
#   tooling/disk.sh landed <worktree>   is everything in this worktree on origin/main? lists what is not
# Runs unasked at session start (.claude/settings.json), at a deliberate stop (agent_stop.sh), when a lane lands
# (lane_land.sh) and before a job when free disk is under the floor (job_guard.sh run). The rules: tooling/tidy.py.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
export PATH="$HOME/.local/bin:$PATH"
PY=$(ls "$HOME/.argonia/venv/bin/python" 2>/dev/null || command -v python3)
gb() { du -sb "$@" 2>/dev/null | awk '{s+=$1} END {printf "%.1f GB", s/2^30}'; }

case "${1:-}" in
report)
  main=$(dirname "$(git -C "$here" rev-parse --path-format=absolute --git-common-dir)")
  df -h / | tail -1 | awk '{print "disk: " $3 " used of " $2 " (" $5 "), " $4 " free; AWS bills the size, not the use"}'
  echo "staged mods (~/.argonia/stack; stack push reads it): $(gb "$HOME/.argonia/stack")"
  echo "owned games (~/games: Skyrim SE data read for vanilla records): $(gb "$HOME/games")"
  echo "Claude transcripts (~/.claude/projects): $(gb "$HOME/.claude/projects")"
  echo "main tree out/: $(gb "$main/out")   lane worktrees: $(gb "$main/.claude/worktrees")"
  echo "mod archives (~/.argonia/mods): $(gb "$HOME/.argonia/mods")   job spool (~/.argonia/jobs): $(gb "$HOME/.argonia/jobs")"
  "$PY" "$here/tidy.py" tidy --dry-run --disk-only ;;
tidy|landed) exec "$PY" "$here/tidy.py" "$@" ;;
*) sed -n 2,17p "$0"; exit 2 ;;
esac
