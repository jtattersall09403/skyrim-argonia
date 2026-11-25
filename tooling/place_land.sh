#!/usr/bin/env bash
# Land a place lane: every drafted place whose built check is stale against the lane's committed files is built and
# checked, then the lane lands (tooling/lane_land.sh), all in one job; a refused landing (main moved) rebases and
# goes round again, up to three times. The one command a place lane (or the lead) runs to land place work.
#   tooling/place_land.sh <worktree>     starts the job place-land.<worktree name> under job_guard and says how to wait
# Inside the job, in order:
#   1. refuse a dirty lane worktree; rebase its branch on origin/main (a conflict stops here, the rebase undone)
#   2. the drafted places whose built check does not stand for this worktree's files (tools.places.handover's rule,
#      by content: a check another tree built from identical files counts)
#   3. each built and checked (python -m tools.places build, then check): the build takes the machine-wide heavy lock,
#      so no two place builds ever run at once, from any tree
#   4. the consistency stage (python -m tools.newworld.consistency); red stops
#   5. tooling/lane_land.sh: gate, push, the main tree levelled (the studio serves it), worktree and branch removed
# Env (tests): PLACE_LAND_STALE, PLACE_LAND_BUILD (with {pid}), PLACE_LAND_CONSISTENCY override steps 2 to 4.
set -euo pipefail
die() { echo "place_land: $*" >&2; exit 1; }
[ $# -eq 1 ] || die "usage: place_land.sh <worktree>"
here=$(cd "$(dirname "$0")" && pwd)
wt=$(cd "$1" 2>/dev/null && pwd) || die "no such worktree: $1"
main=$(dirname "$(git -C "$wt" rev-parse --path-format=absolute --git-common-dir)")
[ "$wt" != "$main" ] || die "that is the main tree: place work is done and landed from a lane's own worktree"
PY=$(ls "$HOME/.argonia/venv/bin/python" 2>/dev/null || command -v python3)
name="place-land.$(basename "$wt")"

if [ -z "${PLACE_LAND_IN_JOB:-}" ]; then
  cd "$HOME"   # never from the worktree (its removal at the end waits for no job) nor the main tree (its level would wait)
  PLACE_LAND_IN_JOB=1 "$here/job_guard.sh" run "$name" -- "$here/place_land.sh" "$wt"
  echo "wait with: tooling/job_guard.sh wait $name"
  exit 0
fi

stale() {
  if [ -n "${PLACE_LAND_STALE:-}" ]; then (cd "$wt" && bash -c "$PLACE_LAND_STALE"); return; fi
  (cd "$wt" && "$PY" -c 'import sys
from pathlib import Path
from tools.places import handover, variant
root = Path.cwd()
for pid in variant.game_places(root / "newworld/places"):
    if not handover.built_check_current(root, handover.out_root(root), pid)[0]:
        print(pid)')
}
build() {
  if [ -n "${PLACE_LAND_BUILD:-}" ]; then (cd "$wt" && bash -c "${PLACE_LAND_BUILD//\{pid\}/$1}"); return; fi
  (cd "$wt" && "$PY" -m tools.places build "$1" && "$PY" -m tools.places check "$1")
}
consistent() {
  (cd "$wt" && bash -c "${PLACE_LAND_CONSISTENCY:-$PY -m tools.newworld.consistency --summary}")
}

for round in 1 2 3; do
  [ -z "$(git -C "$wt" status --porcelain)" ] || { git -C "$wt" status --short | head -10 >&2
    die "refused: $wt has uncommitted or untracked files; commit the place work by path first"; }
  git -C "$wt" fetch -q origin || die "fetch failed"
  if ! git -C "$wt" rebase -q origin/main >/dev/null 2>&1; then
    git -C "$wt" rebase --abort >/dev/null 2>&1 || true
    die "refused: $(git -C "$wt" branch --show-current) conflicts with origin/main (rebase undone); rebase it in the lane"
  fi
  # the builds and checks read and write the shared out/ through a link, put there for them and removed after
  linked=""
  if [ ! -e "$wt/out" ] && [ ! -L "$wt/out" ]; then ln -s "$main/out" "$wt/out"; linked=1; fi
  [ -L "$wt/out" ] || die "refused: $wt/out is a real directory; delete it (generated) so the shared out/ is used"
  rc=0; todo=$(stale) || rc=$?
  for pid in $todo; do
    [ $rc -eq 0 ] || break
    echo "round $round: $pid's built check is stale against this worktree: building and checking it"
    build "$pid" || rc=$?
  done
  [ $rc -eq 0 ] && { consistent || rc=$?; }
  [ -n "$linked" ] && rm -f "$wt/out"
  [ $rc -eq 0 ] || die "refused: a build, check or the consistency stage failed in $wt (round $round); nothing pushed"
  [ -z "$(git -C "$wt" status --porcelain)" ] || { git -C "$wt" status --short | head -10 >&2
    die "refused: the build or check wrote tracked files in $wt; look at them, commit what is right, land again"; }
  if "$here/lane_land.sh" "$wt"; then exit 0; fi
  [ -d "$wt" ] || exit 0
  echo "round $round: the landing was refused; rebasing and going round again"
done
die "the landing was still refused after three rounds; the lane is kept"
