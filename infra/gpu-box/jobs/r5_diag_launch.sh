#!/usr/bin/env bash
# Round 5: why did the sky-on launch fail twice (game alive, the bridge closed the connection)? Up, read the game's
# logs, fetch the menu grab, leave the machine up for the planner's next step (idle-stop guards it).
# Run under tooling/job_guard.sh run --gpu=argonia-play r5-diag2 -- infra/gpu-box/jobs/r5_diag_launch.sh
set -u; cd /home/ubuntu/skyrim-argonia; export ARGONIA_PLAY=argonia-play
~/.argonia/scripts/up_until.sh argonia-play 120 || { echo "DIAG: no machine"; exit 3; }
infra/gpu-box/run.sh ps '$s="$env:USERPROFILE\Documents\My Games\Skyrim Special Edition\SKSE"; "== crashes"; Get-ChildItem "$s\crash-*.log" -EA SilentlyContinue | Sort LastWriteTime | Select -Last 3 | % { "$($_.LastWriteTime) $($_.Name)" }; $c = Get-ChildItem "$s\crash-*.log" -EA SilentlyContinue | Sort LastWriteTime | Select -Last 1; if ($c -and $c.LastWriteTime -gt (Get-Date).AddHours(-3)) { "== latest crash head"; Get-Content $c.FullName -TotalCount 60 }; "== skse64.log tail"; Get-Content "$s\skse64.log" -EA SilentlyContinue | Select -Last 8; "== logs by time"; Get-ChildItem "$s\*.log" | Sort LastWriteTime | Select -Last 10 | % { "$($_.LastWriteTime) $($_.Name) $($_.Length)" }; "== bridge/core"; Get-ChildItem "$s\ArgoniaBridge*.log","$s\ArgoniaCore*.log" -EA SilentlyContinue | % { "--- $($_.Name)"; Get-Content $_.FullName | Select -Last 15 }; "== menu grab"; (Get-Item C:\argonia\logs\menu.png -EA SilentlyContinue).LastWriteTime; "== game running"; [bool](Get-Process SkyrimSE -EA SilentlyContinue)'
mkdir -p ~/.argonia/round; infra/gpu-box/run.sh get 'C:/argonia/logs/menu.png' ~/.argonia/round/diag-menu.png 2>/dev/null && echo "DIAG: menu.png fetched to ~/.argonia/round/diag-menu.png"
echo "DIAG DONE $(date -u +%H:%M)"
