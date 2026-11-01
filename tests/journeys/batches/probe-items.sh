#!/usr/bin/env bash
# 1.12-items: Wind UI's inventory icons and each weapon equipped (third and first person), with Wind UI's log.
#   ARGONIA_LANE=1.12-items tooling/job_guard.sh run --gpu=pick pitems -- tests/journeys/batches/probe-items.sh [tag]
#   WEAPONS="<edid or form id> ..." picks the weapons (default: our steel sword and Skyrim's iron sword)
set -x
cd "$(dirname "$0")/../../.."
T=${1:-probe}; O=out/items/$T; mkdir -p $O
R=infra/gpu-box/run.sh
PY="$HOME/.argonia/venv/bin/python"
B="$PY tools/bridge.py"
LOG='$env:USERPROFILE\Documents\My Games\Skyrim Special Edition\SKSE\WindUI.log'
pause() { $PY -c "import time; time.sleep($1)"; }
$R up
ready() { for i in $(seq 1 40); do $B console 'getgamesetting fJumpHeightMin' >/dev/null 2>&1 && return 0; done; return 1; }
$B launch && $B load ${SAVE:-ArgoniaWalk} && ready
$B pad 'LY=1:500'; ready
shot() { $B screenshot $O/$1.png; }
for w in ${WEAPONS:-ARG_Weap_SteelSword 00012EB7}; do
  $B console "player.additem $w 1"; $B console "player.equipitem $w"; pause 2
  $B console "player.GetEquipped $w"
  shot "$w-3p"
  $B input key F 150 engine; pause 2; shot "$w-1p"; $B input key F 150 engine; pause 1
done
for a in ${ARMOUR:-}; do $B console "player.additem $a 1"; $B console "player.equipitem $a"; done
[ -n "${ARMOUR:-}" ] && { pause 2; shot armour-3p; }
$B input key I 150 engine; pause 3; shot inventory
$B input key Escape 150 engine; pause 1
$R ps "Get-Content \"$LOG\" | Select-Object -Last 80 | ForEach-Object { \$_.Line }" > $O/windui-log.txt
[ -z "${KEEP:-}" ] && $R stop
true
