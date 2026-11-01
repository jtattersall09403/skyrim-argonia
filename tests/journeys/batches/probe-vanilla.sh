#!/usr/bin/env bash
# 1.12 diagnosis: does Wind UI take over the inventory with and without SKSE/Plugins/WindUI/vanilla.txt? (the
# merged build's batches saw Skyrim's menus; the first probe's inventory test ran before vanilla.txt was laid)
#   ARGONIA_LANE=1.12 tooling/job_guard.sh run --gpu=argonia-play pv -- tests/journeys/batches/probe-vanilla.sh
set -x
cd "$(dirname "$0")/../../.."
O=out/pv; mkdir -p $O
R=infra/gpu-box/run.sh
B="$HOME/.argonia/venv/bin/python tools/bridge.py"
D='C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\Data\SKSE\Plugins\WindUI'
LOG='$env:USERPROFILE\Documents\My Games\Skyrim Special Edition\SKSE\WindUI.log'
$R up
ready() { for i in $(seq 1 40); do $B console 'getgamesetting fJumpHeightMin' >/dev/null 2>&1 && return 0; done; return 1; }
try() {  # $1: tag
  $B launch && $B load ArgoniaWalk && ready
  $B pad 'LY=1:500'; ready
  $B input key I 150 engine; $B screenshot $O/$1-inv.png
  $R ps "Get-Content \"$LOG\" | Select-String 'intercept|menu opened|Skyrim.s own|passthrough' | Select-Object -Last 8 | ForEach-Object { \$_.Line }" > $O/$1-log.txt
  cat $O/$1-log.txt
}
$R ps "Get-Content '$D\vanilla.txt'"
try with-vanilla
$R ps "Remove-Item '$D\vanilla.txt'"
try without-vanilla
$R stop
