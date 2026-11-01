#!/usr/bin/env bash
# lane 1.12-hud (owner look 1; L4 stills, L5 bursts, one batch): deploy this worktree, then tests/journeys/hud-look.yaml.
#   ARGONIA_LANE=1.12-hud tooling/job_guard.sh run --gpu=pick l112hud -- tests/journeys/batches/lane-1.12-hud.sh
set -x
cd "$(dirname "$0")/../../.."
R=infra/gpu-box/run.sh
$R up || exit $?
PY=~/.argonia/venv/bin/python
[ -n "${NO_DEPLOY:-}" ] || make deploy || exit 1
$PY tools/run_journey.py tests/journeys/hud-look.yaml; rc=$?
echo "journey rc=$rc"
[ -n "${KEEP_UP:-}" ] || $R stop
exit $rc
