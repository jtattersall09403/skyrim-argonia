#!/usr/bin/env bash
# Land a lane: its branch onto origin/main, then its worktree and branch gone. The lead's one command per lane.
#   tooling/lane_land.sh <worktree>
# Steps, each skipped when already done, so a rerun after an interrupt carries on from where it stopped:
#   1. refuse a dirty lane worktree (uncommitted or untracked files: the lane commits or deletes them first)
#   2. rebase the lane's branch on origin/main (a conflict stops here, the rebase undone: resolve it in the lane)
#   3. the gate in the lane's worktree (`make check GATE_BASE=origin/main`, scoped to what the
#      branch changed; LANE_GATE overrides the command); red refuses
#   4. push to origin/main (main moved meanwhile: back to 2, up to three times)
#   5. level the main tree (tooling/level_main.sh --auto): stale leftovers cleared, real work and the owner's edits kept,
#      fast-forwarded; while a job runs from it (a job that only waits does not count), job_guard levels it at that job's end
#   6. remove the worktree and delete its branch, once everything in it is on main (tooling/tidy.py's content rule)
# The only way a lane lands; its gate is the scoped one, never a full run (`make check-all WHY=deploy|phase-close` is for a
# deploy and a phase's close only; owner, 2026-11-21).
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
  # The gate reads the shared built outputs (the Atlas page, each place's built check): a worktree
  # sees them through a link to the main tree's out/, put there for the gate and removed after.
  linked=""
  if [ "$wt" != "$main" ] && [ ! -L "$wt/out" ]; then
    [ -e "$wt/out" ] && die "refused: $wt/out is a real directory; delete it (generated) so the gate can link the shared out/"
    ln -s "$main/out" "$wt/out"; linked=1
  fi
  grc=0; (cd "$wt" && ${LANE_GATE:-make check GATE_BASE=origin/main}) || grc=$?
  [ -n "$linked" ] && rm -f "$wt/out"
  [ $grc -eq 0 ] || die "refused: the gate is red in $wt; nothing pushed"
  if git -C "$wt" push -q origin HEAD:main 2>/dev/null; then
    landed=1; echo "pushed: origin/main is at $(git -C "$wt" rev-parse --short HEAD)"; break
  fi
  echo "push refused (main moved); rebasing again"
done
[ -n "$landed" ] || die "push still refused after three tries; $branch is rebased and kept"

# The main tree (the studio serves it) follows: tooling/level_main.sh clears its provably stale leftovers and
# fast-forwards it; while a job runs from it, job_guard levels it when that job ends. It never fails the landing.
"$here/level_main.sh" --tree "$main" --auto || true

"$PY" "$here/tidy.py" remove "$wt"
