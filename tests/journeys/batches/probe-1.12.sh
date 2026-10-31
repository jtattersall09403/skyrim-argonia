#!/usr/bin/env bash
# 1.12 §1-§2 probe (L4, one batch): Wind UI's facts in game. Its log and files, a still of each window it draws
# (menu mode, inventory, magic with Magic Expanded's spells, stats, map, journal, the System page), the pad's Start,
# FreeClimb's and Magic Expanded's load lines. Read-only: nothing is asserted here; windui.md records what it shows.
#   ARGONIA_LANE=1.12 tooling/job_guard.sh run --gpu=argonia-play-ie p112 -- tests/journeys/batches/probe-1.12.sh
set -x
cd "$(dirname "$0")/../../.."
O=out/p112; mkdir -p $O
R=infra/gpu-box/run.sh
PY=~/.argonia/venv/bin/python
B="$PY tools/bridge.py"
SK='$env:USERPROFILE\Documents\My Games\Skyrim Special Edition\SKSE'
$R ps "Get-ChildItem \"$SK\" | Select Name,Length,LastWriteTime | Format-Table -Auto | Out-String -Width 200" > $O/skse-dir.txt
$B load ArgoniaWalk
$B pad 'LY=1:600'
$B screenshot $O/00-play.png
$R ps "Get-Content \"$SK\WindUI.log\" -Tail 200" > $O/windui-log-0.txt
$R ps "Get-ChildItem -Recurse 'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\Data\SKSE\Plugins\WindUI' | Select FullName,Length | Out-String -Width 300" > $O/windui-files.txt
$R ps "Select-String -Path \"$SK\skse64.log\" -Pattern 'WindUI|FreeClimb|Magic|CustomSkills' | Out-String -Width 300" > $O/skse-lines.txt
$R ps "Get-ChildItem \"$SK\" -Filter *FreeClimb* | ForEach-Object { \$_.FullName; Get-Content \$_.FullName -Tail 60 }" > $O/freeclimb-log.txt
# Magic Expanded: its spells by name, a few added so the magic pane shows its schools
for s in Mark Recall Levitate Telekinesis "Soul Trap" Dispel "Detect" "Fire Bite"; do $B console "help \"$s\" 4" ; done > $O/magic-help.txt 2>&1
$B key "TAB 120"; $B screenshot $O/01-tab.png
$B key "TAB 120"
$B key "I 120"; $B screenshot $O/02-inventory.png; $B key "I 120"
$B key "P 120"; $B screenshot $O/03-magic.png; $B key "P 120"
$B key "M 120"; $B screenshot $O/04-map.png; $B key "ESC 80"
$B key "J 120"; $B screenshot $O/05-journal.png; $B key "ESC 80"
$B key "ESC 80"; $B screenshot $O/06-esc.png; $B key "ESC 80"
$B pad 'START:150'; $B screenshot $O/07-pad-start.png
$B pad 'RB:150'; $B screenshot $O/08-pad-rb.png
$B pad 'DOWN:150'; $B screenshot $O/09-pad-down.png
$B pad 'B:150'; $B pad 'B:150'
$R ps "Get-Content \"$SK\WindUI.log\" -Tail 300" > $O/windui-log-1.txt
$R ps "Get-ChildItem -Recurse \"$SK\WindUI*\",'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\Data\SKSE\Plugins\WindUI' -Include *.txt,*.json,*.ini | ForEach-Object { '== ' + \$_.FullName; Get-Content \$_.FullName -TotalCount 40 }" > $O/windui-txt.txt
$B screenshot $O/10-end.png
