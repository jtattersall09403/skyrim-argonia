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
# ready: a console call runs on the main thread, and WindUI.log has the layout loaded and a calm frames line after it
for i in $(seq 1 40); do
  $B console "getgs fJumpHeightMin" >/dev/null 2>&1 || continue
  $R ps "\$t = Get-Content \"$SK\WindUI.log\" -Tail 60; \$k = (\$t | Select-String 'window layout loaded from the save' | Select -Last 1).LineNumber; if (\$k -and (\$t[\$k..(\$t.Count)] | Select-String ', 0 over 100 ms')) { 'READY' }" | grep -q READY && { echo "ready after $i"; break; }
done
$B input key I 150 engine; $R ps "Get-Content \"$SK\WindUI.log\" -Tail 8" > $O/after-I.txt; $B screenshot $O/01-menu-mode.png
$B input key I 150 engine
$B input key ESC 150 engine; $B screenshot $O/06-system.png; $B input key ESC 150 engine
$R ps "Select-String -Path \"$SK\WindUI.log\" -Pattern 'menu art|menu opened' | Select -Last 4 | Out-String -Width 300" > $O/windui-art.txt
