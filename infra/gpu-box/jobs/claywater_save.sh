#!/usr/bin/env bash
# The tenth save, Claywater, made fresh (2026-11-04 00:5x): ArgoniaCore blocks the engine's saving once a save is
# loaded (life.cpp SavingBlocked(true) in the load hook: the core's own slots are the only saves), so region_saves
# without --fresh loads ArgoniaWalk and every save is refused; --fresh starts a new game and saves cleanly, as the nine
# did at 00:16-00:22. Then the push to the pool and the machine stopped. Under job_guard --gpu=argonia-play.
set -u; cd /home/ubuntu/skyrim-argonia; export ARGONIA_PLAY=argonia-play
PY=$HOME/.argonia/venv/bin/python
~/.argonia/scripts/up_until.sh argonia-play 120 || { infra/build-vm/agent-wake.sh "Claywater save: Paris never came up"; exit 3; }
$PY tools/bridge.py ping >/dev/null 2>&1 || $PY tools/bridge.py launch || { infra/build-vm/agent-wake.sh "Claywater save: no main menu"; exit 3; }
if $PY infra/gpu-box/region_saves.py --fresh --only claywater; then
  infra/gpu-box/jobs/saves_push.sh && echo "CLAYWATER SAVED AND PUSHED $(date -u +%H:%M)"
  infra/gpu-box/run.sh ps "Get-ChildItem 'C:\Users\Administrator\Documents\My Games\Skyrim Special Edition\Saves\Argonia *.ess' | % { \$_.LastWriteTime.ToString('MM-dd HH:mm') + ' ' + \$_.Name }"
  infra/gpu-box/run.sh stop
  infra/build-vm/agent-wake.sh "Claywater save DONE and pushed; Paris stopped. Post the hand-over on #37."
else
  echo "CLAYWATER SAVE FAILED $(date -u +%H:%M)"
  infra/gpu-box/run.sh ps 'Get-ChildItem "C:\Users\Administrator\Documents\My Games\Skyrim Special Edition\SKSE\crash-*.log" | sort LastWriteTime | select -last 1 | % { $_.Name; Get-Content $_.FullName | Select-String -Pattern "Unhandled|RSP\+|\.nif|\.dds|TESObjectCELL|TESWorldSpace" | select -first 30 | % { $_.Line.Trim().Substring(0,[Math]::Min(160,$_.Line.Trim().Length)) } }'
  infra/build-vm/agent-wake.sh "Claywater save FAILED (fresh): read ~/.argonia/jobs/claywater-save.log; the machine is left up."
  exit 3
fi
