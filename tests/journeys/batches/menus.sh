#!/usr/bin/env bash
# lane 1.12-menus' in-game batch: deploy this tree, run the named batch yaml (default menus.yaml), stop the machine.
#   ARGONIA_LANE=1.12-menus tooling/job_guard.sh run --gpu=pick mb -- tests/journeys/batches/menus.sh [batch.yaml]
set -x
cd "$(dirname "$0")/../../.."
[ -n "${NO_DEPLOY:-}" ] || make deploy || exit 1
~/.argonia/venv/bin/python tools/run_batch.py "${1:-tests/journeys/batches/menus.yaml}"; rc=$?
[ -n "${KEEP_UP:-}" ] || infra/gpu-box/run.sh stop
exit $rc
