#!/usr/bin/env bash
# A lane's own clean worktree at origin/main, ready to build and deploy: the main tree's untracked build inputs
# (out/navmesh, out/terrain, ... made by long jobs) are linked in, so `make plugin` neither rebuilds them nor drops
# the province navmesh (game-15; ui-review2 lost ~30 min rebuilding them, 2026-10-31).
#   tooling/worktree.sh <path>          create (or refresh to origin/main) and link
set -euo pipefail
main=$(cd "$(dirname "$0")/.." && pwd)
wt=${1:?usage: worktree.sh <path>}
git -C "$main" fetch -q origin
if [ -d "$wt/.git" ] || [ -f "$wt/.git" ]; then
  git -C "$wt" checkout -q --detach origin/main
else
  git -C "$main" worktree add -q --detach "$wt" origin/main
fi
mkdir -p "$wt/out"
for d in "$main"/out/*/; do
  n=$(basename "$d")
  case "$n" in batch|runs|check|resume|build) continue ;; esac  # per-run outputs stay the worktree's own
  [ -e "$wt/out/$n" ] || ln -s "$d" "$wt/out/$n"
done
echo "worktree $wt at $(git -C "$wt" rev-parse --short HEAD), $(find "$wt/out" -maxdepth 1 -type l | wc -l) build inputs linked"
