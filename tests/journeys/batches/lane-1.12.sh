#!/usr/bin/env bash
# 1.12's in-game batch on one deploy of main: the lanes' journeys (lane-1.12.yaml), then FreeClimb's bindings read from
# its log (the owner's climbing: jump at a wall) and Wind UI's windows with the retint, a still each. Stops the machine.
#   ARGONIA_LANE=1.12 tooling/job_guard.sh run --gpu=argonia-play-ie b112 -- tests/journeys/batches/lane-1.12.sh
set -x
cd "$(dirname "$0")/../../.."
O=out/b112; mkdir -p $O
R=infra/gpu-box/run.sh
PY=~/.argonia/venv/bin/python
B="$PY tools/bridge.py"
[ -n "${NO_DEPLOY:-}" ] || make deploy || exit 1
$PY tools/run_batch.py tests/journeys/batches/lane-1.12.yaml; rc=$?
# FreeClimb: the entry chords it parsed (W+Space; the pad's Y), and a press at the ground reaching it
$B launch && $B load ArgoniaWalk
for i in $(seq 1 40); do $B console 'getgamesetting fJumpHeightMin' >/dev/null 2>&1 && break; done
$B pad 'LY=1:400'; $B input key W+SPACE 300 os
$B input key I 150 engine; $B screenshot $O/windui-menu-mode.png
$B input key ESC 150 engine
$R ps 'powershell -ExecutionPolicy Bypass -File C:\argonia\infra\bridge.ps1 -Cmd kill'
$R ps 'Get-Content "C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\Data\SKSE\FreeClimb.log" | Select-String "climb entry=|Experimental controller|Entry input|Climb entry|Grab request" | Select-Object -First 8 | ForEach-Object { $_.Line }' > $O/freeclimb.txt
cat $O/freeclimb.txt
[ -n "${KEEP_UP:-}" ] || $R stop
exit $rc
