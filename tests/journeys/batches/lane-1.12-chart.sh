#!/usr/bin/env bash
# Lane 1.12-chart's in-game batch (owner look 1): deploy this tree, then the chart's look, reveal, marker, zoom and
# motion, the camera after the map and the map pane (chart-look), then chart-minimap, whose map steps changed with
# the map key. Stops the machine unless KEEP_UP.
#   ARGONIA_LANE=1.12-chart tooling/job_guard.sh run --gpu=pick chart112 -- tests/journeys/batches/lane-1.12-chart.sh
set -x
cd "$(dirname "$0")/../../.."
PY=~/.argonia/venv/bin/python
[ -n "${NO_DEPLOY:-}" ] || make deploy || exit 1
$PY tools/run_batch.py chart-look chart-minimap; rc=$?
[ -n "${KEEP_UP:-}" ] || infra/gpu-box/run.sh stop
exit $rc
