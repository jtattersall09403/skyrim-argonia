#!/usr/bin/env bash
# A clean worktree at origin/main for a parallel agent.
#   tooling/worktree.sh <path>          create (or refresh to origin/main)
set -euo pipefail
main=$(cd "$(dirname "$0")/.." && pwd)
wt=${1:?usage: worktree.sh <path>}
git -C "$main" fetch -q origin
if [ -d "$wt/.git" ] || [ -f "$wt/.git" ]; then
  git -C "$wt" checkout -q --detach origin/main
else
  git -C "$main" worktree add -q --detach "$wt" origin/main
fi
echo "worktree $wt at $(git -C "$wt" rev-parse --short HEAD)"
