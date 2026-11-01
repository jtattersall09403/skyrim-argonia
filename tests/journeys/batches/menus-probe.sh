#!/usr/bin/env bash
# lane 1.12-menus: what the player meets on Tab, Esc, T and the panes' Journal (diagnosis stills and a Tab burst).
#   ARGONIA_LANE=1.12-menus tooling/job_guard.sh run --gpu=pick mp0 -- tests/journeys/batches/menus-probe.sh
set -x
cd "$(dirname "$0")/../../.."
O=out/menus/${TAG:-probe}; mkdir -p $O
R=infra/gpu-box/run.sh
PY=~/.argonia/venv/bin/python
B="$PY tools/bridge.py"
w() { $PY -c "import time, sys; time.sleep(float(sys.argv[1]))" "$1"; }
[ -n "${NO_DEPLOY:-}" ] || make deploy || exit 1
$B kill; $B launch && $B load ArgoniaWalk; w 6
burst() {  # $1 name, $2 key: a 20 fps still loop over 2 s while the key is pressed
  $R desktop "Start-Process powershell -WindowStyle Hidden -ArgumentList '-ExecutionPolicy Bypass -File C:\argonia\infra\grab.ps1 C:\argonia\logs\b-$1.png -Frames 40 -Fps 20'" ; w 1.2
  $B input key $2 120 engine; w 3
  $R ps "Compress-Archive -Force C:\argonia\logs\b-$1_*.png C:\argonia\logs\b-$1.zip; Remove-Item C:\argonia\logs\b-$1_*.png"
  $R get 'C:\argonia\logs\b-'$1'.zip' $O/; (cd $O && unzip -oq b-$1.zip -d b-$1 && rm b-$1.zip)
}
burst tab TAB; $B screenshot $O/01-tab.png
$B input key ESC 120 engine; w 2
burst esc ESC; $B screenshot $O/02-esc.png
$B input key ESC 120 engine; w 2; $B input key ESC 120 engine; w 2; $B screenshot $O/02b-after-esc.png
$B input key T 120 engine; w 2; $B screenshot $O/03-wait.png
$B input key TAB 120 engine; w 2
$B input key J 120 engine; w 2; $B screenshot $O/04-j.png
$B input key J 120 engine; w 2
$R ps "Select-String -Path \"\$env:USERPROFILE\\Documents\\My Games\\Skyrim Special Edition\\SKSE\\ArgoniaCore.log\" -Pattern 'menu|pad:|router|views' | Select -Last 120 | Out-String -Width 300" > $O/log.txt
[ -n "${KEEP_UP:-}" ] || $R stop
