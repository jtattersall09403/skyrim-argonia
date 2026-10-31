#!/usr/bin/env bash
# lane-1.11: the HUD in play (checks.md 1.11, the reader row at L4), one batch: calm, a hit with its damage trail as a
# temporal strip, regeneration, low health, a vastei gain. Dev tools deal the damage (damageav), never a mode.
# Owed until the machines move to Stockholm; start nothing by hand. Run:
#   ARGONIA_LANE=lane-1.11 tooling/job_guard.sh run --gpu=argonia-play-2 l111-batch -- tests/journeys/batches/lane-1.11.sh
set -x
cd "$(dirname "$0")/../../.."
O=out/l111; mkdir -p $O
infra/gpu-box/run.sh up || exit $?
PY=~/.argonia/venv/bin/python
B="$PY tools/bridge.py"
make deploy || exit 1
$B load argoniabase
$B pad 'LY=1:800'                                # a game action, so play has started and the HUD shows
$B console 'player.setav health 200'          # setup: a known maximum, so the hit and low states are fixed shares
$B screenshot $O/calm.png
$B console "player.damageav health 70"
for i in 0 1 2 3 4 5; do $B screenshot $O/fight-$i.png; done   # the strip: the trail holds ~0.9 s, then falls in 0.5 s
$B console 'player.restoreav health 1000'; $B screenshot $O/regen.png
$B console "player.damageav health 90"; $B pad 'LY=1:400'
$B screenshot $O/low.png
$B dev-set SetVastei 180
$B screenshot $O/vastei-gain.png
$B console 'player.restoreav health 1000'
infra/gpu-box/run.sh stop
