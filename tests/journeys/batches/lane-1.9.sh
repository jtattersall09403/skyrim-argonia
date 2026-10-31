#!/usr/bin/env bash
# lane-1.9: every in-game 1.9 row in one batch, crash-prone (the phone drives) last. Run:
#   ARGONIA_LANE=lane-1.9 tooling/job_guard.sh run --gpu=argonia-play-2 l19-batch -- tests/journeys/batches/lane-1.9.sh
set -x
cd "$(dirname "$0")/../../.."
mkdir -p out/l19
infra/gpu-box/run.sh up || exit $?
infra/gpu-box/run.sh put infra/gpu-box/prewarm.ps1 C:/argonia/infra/prewarm.ps1
infra/gpu-box/run.sh ps '& C:\argonia\infra\prewarm.ps1'
PY=~/.argonia/venv/bin/python
make deploy || exit 1
infra/gpu-box/run.sh ps 'Test-Path C:\argonia\MO2\mods\oblivion-loading-menu; Get-ChildItem C:\argonia\MO2\mods\tropical-skyrim-sse\Meshes -Name'
$PY tools/bridge.py load argoniabase
$PY tools/bridge.py player; $PY tools/bridge.py pad 'LY=1:2500'; $PY tools/bridge.py player
$PY tools/bridge.py screenshot out/l19/argoniabase.png
$PY tools/run_journey.py tests/journeys/walk-save.yaml --save argoniabase
$PY -m tools.ui_theme.front_door --out out/l19/front-door
for d in desktop v5-unfolded v5-folded; do
  ARGONIA_FORCE=1 ARGONIA_DEVICE=$d infra/stream-client/e2e/drive.sh infra/stream-client/e2e/steps/load-stills.json out/l19/drive-$d
done
infra/gpu-box/run.sh stop
