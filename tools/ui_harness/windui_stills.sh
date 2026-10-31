#!/usr/bin/env bash
# 1.12 §3 (L4): stills of Wind UI's panes with the frame retint, after a deploy. Engine-route keys only.
#   ARGONIA_LANE=1.12-design tooling/job_guard.sh run --gpu=argonia-play wu -- tools/ui_harness/windui_stills.sh
set -x
cd "$(dirname "$0")/../.."
make deploy || exit 1
O=out/windui-stills; mkdir -p $O
R="infra/gpu-box/run.sh"
B="$HOME/.argonia/venv/bin/python tools/bridge.py"
SK='$env:USERPROFILE\Documents\My Games\Skyrim Special Edition\SKSE'
$B health || $B launch
$B load ArgoniaWalk
$B input key TAB 150 engine; $B screenshot $O/01-menu-mode.png; $B input key TAB 150 engine
$B input key I 150 engine; $B screenshot $O/02-inventory.png; $B input key I 150 engine
$B input key P 150 engine; $B screenshot $O/03-magic.png; $B input key P 150 engine
$B input key ESC 100 engine; $B screenshot $O/04-system.png; $B input key ESC 100 engine
$R ps "Select-String -Path \"$SK\WindUI.log\" -Pattern 'menu art' | Select -Last 3 | Out-String -Width 300" > $O/windui-art.txt
