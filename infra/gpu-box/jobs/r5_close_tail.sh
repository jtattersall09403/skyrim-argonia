#!/usr/bin/env bash
# Round 5's close, the tail (2026-11-04 00:2x): r5-close10 made nine of the ten saves (the game crashed in d3d11.dll at
# the Claywater stop, 00:16:36) and stopped Paris without pushing them. This brings Paris up, remakes Claywater alone,
# pushes the ten saves to the pool, then runs the camera diagnosis (the rest batch's two 'never became first' stops)
# and the rest batch again (the pass ledger carries only the failed and re-aimed steps). Every end wakes the agent.
# Under job_guard --gpu=argonia-play.
set -u; cd /home/ubuntu/skyrim-argonia; export ARGONIA_PLAY=argonia-play
job=${JOB_NAME:-r5-close11}
PY=$HOME/.argonia/venv/bin/python
fail() { echo "CLOSE: $1 $(date -u +%H:%M)"; infra/build-vm/agent-wake.sh "round 5 close tail FAILED: $1. Read ~/.argonia/jobs/$job.log; the owner waits on #37 for the ten saves."; exit 3; }
~/.argonia/scripts/up_until.sh argonia-play 240 || fail "Paris never came up"
$PY tools/bridge.py launch || fail "no main menu"
if $PY infra/gpu-box/region_saves.py --only claywater; then echo "CLAYWATER SAVE OK $(date -u +%H:%M)"
else
  echo "CLAYWATER SAVE FAILED AGAIN $(date -u +%H:%M)"; infra/gpu-box/run.sh ps 'Get-ChildItem "C:\Users\Administrator\Documents\My Games\Skyrim Special Edition\SKSE\crash-*.log" | sort LastWriteTime | select -last 1 | % { Get-Content $_.FullName -TotalCount 60 }' | cut -c1-200
  $PY tools/bridge.py launch || fail "no main menu after the second Claywater crash"
fi
infra/gpu-box/jobs/saves_push.sh && echo "SAVES PUSHED $(date -u +%H:%M)" || echo "SAVES PUSH FAILED $(date -u +%H:%M)"
infra/build-vm/agent-wake.sh "round 5 close tail: the saves are pushed (see ~/.argonia/jobs/$job.log for Claywater); the camera diagnosis and the rest rerun follow on the same boot."
$PY tools/bridge.py load argoniabase >/dev/null 2>&1 || true
DIAG_OUT=out/diag/camera-20261104 $PY /tmp/claude-1000/-home-ubuntu-skyrim-argonia/cf1889f7-e3d4-4c3e-b54d-b0eb57769241/scratchpad/camera_diag.py 2>&1 | tail -40
ROUND_KEEP_UP=1 ARGONIA_SHADERS=on infra/gpu-box/round.sh tests/journeys/batches/1.15-round-5-rest.yaml || echo "CLOSE: the rest rerun returned $?"
infra/gpu-box/run.sh stop
echo "CLOSE TAIL DONE $(date -u +%H:%M)"
infra/build-vm/agent-wake.sh "round 5 close tail DONE (job $job): saves, camera diagnosis in out/diag/camera-20261104, rest rerun. Post the hand-over on #37."
