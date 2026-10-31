#!/usr/bin/env bash
# lane-1.10: the player character's in-game rows in one batch. make deploy remakes argoniabase and ArgoniaWalk with
# base_save.py (a new game, Argonian from our plugin's Player override, no setrace); then the player-look journey's
# front, side and back stills from ArgoniaWalk and argoniabase's race read, for a `reader`. Run:
#   ARGONIA_LANE=lane-1.10 tooling/job_guard.sh run --gpu=argonia-play-2 l110-batch -- tests/journeys/batches/lane-1.10.sh
set -x
cd "$(dirname "$0")/../../.."
mkdir -p out/l110
infra/gpu-box/run.sh up || exit $?
infra/gpu-box/run.sh put infra/gpu-box/prewarm.ps1 C:/argonia/infra/prewarm.ps1
infra/gpu-box/run.sh ps '& C:\argonia\infra\prewarm.ps1'
PY=~/.argonia/venv/bin/python
make deploy || exit 1   # its last step: base_save.py (argoniabase, then ArgoniaWalk); fails if the player is not Argonian
$PY tools/bridge.py oracle out/l110
$PY tools/run_journey.py tests/journeys/player-look.yaml --save ArgoniaWalk
$PY tools/bridge.py load argoniabase; $PY tools/bridge.py player; $PY tools/bridge.py console "player.GetIsRace ArgonianRace"
ls -d out/runs/player-look/*/ | tail -2
infra/gpu-box/run.sh stop
