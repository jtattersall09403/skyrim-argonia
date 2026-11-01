#!/usr/bin/env bash
# 1.12 §8 (L4, one job): the pad on Wind UI's windows. The Select->Wait controlmap laid, our build deployed, the dev
# mouse's routes probed with stills, then pad-panes at 1080p and at the Magic V5's folded and unfolded desktops
# (sunshine-prep.ps1 sizes the desktop as the stream client would), the desktop put back to 1920x1080 at the end.
#   ARGONIA_LANE=1.12-pad tooling/job_guard.sh run --gpu=argonia-play-ie pad112 -- tests/journeys/batches/pad-1.12.sh
set -x
cd "$(dirname "$0")/../../.."
O=out/pad112; mkdir -p $O
R=infra/gpu-box/run.sh
PY=~/.argonia/venv/bin/python
B="$PY tools/bridge.py"
w() { $PY -c "import time, sys; time.sleep(float(sys.argv[1]))" "$1"; }  # a menu's open or close settling
# the gamepad layout: Select is Wait (controlmap.py's remap over the machine's own made file; never committed)
$R get 'C:/argonia/controls/controlmap.txt' $O/controlmap-was.txt && \
  $PY -c "import sys; sys.path.insert(0,'infra/gpu-box'); import controlmap as c; t=open('$O/controlmap-was.txt',encoding='latin-1').read(); open('$O/controlmap.txt','w',encoding='latin-1',newline='').write(c.remap(t.replace(chr(13)+chr(10),chr(10))))" && \
  $R put $O/controlmap.txt 'C:/argonia/controls/controlmap.txt'
make deploy || exit 1
# Wind UI's takeover on: a vanilla.txt left in Data from before e62ac40 turns it off (every menu Skyrim's)
novanilla() { $R ps "Remove-Item -EA SilentlyContinue 'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\Data\SKSE\Plugins\WindUI\vanilla.txt'; Test-Path 'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\Data\SKSE\Plugins\WindUI\vanilla.txt'"; }
novanilla; $B kill; $B launch
size() { $B kill; $R desktop "\$env:SUNSHINE_CLIENT_WIDTH='$1'; \$env:SUNSHINE_CLIENT_HEIGHT='$2'; & C:\\argonia\\infra\\sunshine-prep.ps1"; novanilla; $B launch; }
probe() {  # the dev mouse's routes: which one moves Wind UI's cursor (stills), then each pad button
  local p=$O/$1; mkdir -p $p
  $B load ArgoniaWalk; w 3
  $B input key TAB 120 engine; w 2; $B screenshot $p/00-windows.png
  $B input cursor > $p/cursor-0.json
  $B input mouse 300 300 event > $p/move-event.json; $B screenshot $p/01-event.png
  $B input mouse 1500 300 cursor > $p/move-cursor.json; $B screenshot $p/02-cursor.png
  $B input mouse 900 800 both > $p/move-both.json; $B screenshot $p/03-both.png
  $B pad 'LX=-1:500 LY=1:500'; $B input cursor > $p/cursor-pad.json; $B screenshot $p/04-pad-stick.png
  $B pad 'RB:150'; w 1; $B input cursor > $p/cursor-rb1.json; $B screenshot $p/05-rb1.png
  $B pad 'RB:150'; w 1; $B screenshot $p/06-rb2.png
  $B pad 'RB:150'; w 1; $B screenshot $p/07-rb3.png
  $B pad 'A:150'; w 1; $B screenshot $p/08-a.png
  $B pad 'RY=-1:800'; $B screenshot $p/09-rstick.png
  $B pad 'B:150'; w 3; $B screenshot $p/10-b.png
  $B pad 'START:150'; w 2; $B screenshot $p/11-start.png
  $B pad 'START:150'; w 3; $B screenshot $p/12-start-closed.png
  $B pad 'BACK:150'; w 2; $B screenshot $p/13-select.png
  $B input key ESC 80 engine; w 2
  $R ps "Select-String -Path \"\$env:USERPROFILE\\Documents\\My Games\\Skyrim Special Edition\\SKSE\\ArgoniaCore.log\" -Pattern 'pad:' | Select -Last 80 | Out-String -Width 300" > $p/pad-log.txt
}
probe p1080
$PY tools/run_journey.py tests/journeys/pad-panes.yaml > $O/journey-1080.txt 2>&1
size 2376 1058; probe folded; $PY tools/run_journey.py tests/journeys/pad-panes.yaml > $O/journey-folded.txt 2>&1
size 2352 2160; probe unfolded; $PY tools/run_journey.py tests/journeys/pad-panes.yaml > $O/journey-unfolded.txt 2>&1
size 1920 1080
echo PAD112 DONE
