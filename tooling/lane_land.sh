#!/usr/bin/env bash
# Land a lane: its branch onto origin/main, then its worktree and branch gone. The lead's one command per lane.
#   tooling/lane_land.sh <worktree>
# Steps, each skipped when already done, so a rerun after an interrupt carries on from where it stopped:
#   1. refuse a dirty lane worktree (uncommitted or untracked files: the lane commits or deletes them first)
#   2. rebase the lane's branch on origin/main (a conflict stops here, the rebase undone: resolve it in the lane)
#   3. the gate in the lane's worktree (`make check`; LANE_GATE overrides the command); red refuses
#   4. push to origin/main (main moved meanwhile: back to 2, up to three times)
#   5. fast-forward the main tree, keeping its uncommitted edits; skipped, and said, while a job runs from it
#   6. remove the worktree and delete its branch, once everything in it is on main (tooling/tidy.py's content rule)
# Never runs stash, reset --hard or a checkout of paths; never touches another lane's worktree.
set -euo pipefail
die() { echo "lane_land: $*" >&2; exit 1; }
[ $# -eq 1 ] || die "usage: lane_land.sh <worktree>"
here=$(cd "$(dirname "$0")" && pwd)
wt=$(cd "$1" 2>/dev/null && pwd) || die "no such worktree: $1"
main=$(dirname "$(git -C "$here" rev-parse --path-format=absolute --git-common-dir)")
[ "$(git -C "$wt" rev-parse --path-format=absolute --git-common-dir)" = "$main/.git" ] || die "$wt is not a worktree of $main"
[ "$wt" != "$main" ] || die "that is the main tree, not a lane"
branch=$(git -C "$wt" symbolic-ref -q --short HEAD) || die "$wt is on no branch"
PY=$(ls "$HOME/.argonia/venv/bin/python" 2>/dev/null || command -v python3)

[ -z "$(git -C "$wt" status --porcelain)" ] || { git -C "$wt" status --short | head -10 >&2
  die "refused: $wt has uncommitted or untracked files; the lane commits its work and deletes its scratch first"; }

landed=""
for _ in 1 2 3; do
  git -C "$main" fetch -q origin || die "fetch failed"
  if [ -z "$(git -C "$wt" rev-list -n1 origin/main..HEAD)" ] || "$PY" "$here/tidy.py" landed "$wt" >/dev/null 2>&1; then
    landed=1; echo "nothing left to land: $branch is on origin/main"; break
  fi
  if ! git -C "$wt" rebase -q origin/main >/dev/null 2>&1; then
    git -C "$wt" rebase --abort >/dev/null 2>&1 || true
    die "refused: $branch conflicts with origin/main (rebase undone); rebase it in the lane, then land again"
  fi
  (cd "$wt" && ${LANE_GATE:-make check}) || die "refused: the gate is red in $wt; nothing pushed"
  if git -C "$wt" push -q origin HEAD:main 2>/dev/null; then
    landed=1; echo "pushed: origin/main is at $(git -C "$wt" rev-parse --short HEAD)"; break
  fi
  echo "push refused (main moved); rebasing again"
done
[ -n "$landed" ] || die "push still refused after three tries; $branch is rebased and kept"

git -C "$main" fetch -q origin
if [ "$(git -C "$main" symbolic-ref -q --short HEAD)" != main ]; then
  echo "main tree left as is: it is not on main"
elif job=$("$PY" -c 'import sys; sys.path.insert(0, sys.argv[1]); import tidy
print(next((n for n, c in tidy.job_cwds() if tidy._inside(c, tidy.Path(sys.argv[2]))), ""))' "$here" "$main") && [ -n "$job" ]; then
  echo "main tree left as is: job $job runs from it; fast-forward it when the job ends (git merge --ff-only origin/main)"
elif git -C "$main" merge -q --ff-only origin/main 2>/dev/null; then
  echo "main tree is at $(git -C "$main" rev-parse --short HEAD)"
else
  echo "main tree NOT moved: an uncommitted file there collides with what landed; it is behind origin/main"
fi

"$PY" "$here/tidy.py" remove "$wt"
