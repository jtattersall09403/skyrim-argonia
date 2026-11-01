#!/usr/bin/env bash
# The pool on one build (1.8 §7): deploy main's HEAD to every standby whose build is not it (pool.py behind), one
# after another, each under its own machine lock. Run after a green batch that the owner will play (the deliver
# skill's "ready for the owner's play"), and by the planner's tick when pool.py status shows a standby BEHIND:
#   tooling/job_guard.sh run pool-deploy -- infra/gpu-box/pool_deploy.sh      (or: make pool-deploy)
# From a clean checkout at origin/main, e.g. tooling/worktree.sh's (pool.py stamp marks anything else as behind). A standby AWS cannot start now
# (no spot capacity) is reported and left; the play page meanwhile starts the current one first.
set -uo pipefail
here=$(cd "$(dirname "$0")" && pwd); repo=$(cd "$here/../.." && pwd); cd "$repo"
PY=$(ls "$HOME/.argonia/venv/bin/python" 2>/dev/null || command -v python3)
git fetch -q origin main
[ "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" ] && [ -z "$(git status --porcelain --untracked-files=no)" ] \
  || { echo "pool_deploy: run from a clean checkout at origin/main (tooling/worktree.sh makes one)" >&2; exit 2; }
make --no-print-directory plugin || exit 1
rc=0
for m in $("$PY" "$here/pool.py" behind); do
  echo "== $m: deploying main $(git rev-parse --short=12 HEAD)"
  if ARGONIA_PLAY=$m "$here/run.sh" up; then
    # the machine's own lock, waited for in the foreground (this script already runs under job_guard)
    lock="$HOME/.argonia/jobs/gpu-$m.lock"; [ "$m" = argonia-play ] && lock="$HOME/.argonia/jobs/gpu.lock"
    ARGONIA_PLAY=$m flock -w 7200 "$lock" "$here/deploy.sh" --no-plugin || { echo "== $m: deploy FAILED"; rc=1; }
  else
    echo "== $m: could not start (no capacity?); left behind"; rc=1
  fi
done
"$PY" "$here/pool.py" status
exit $rc
