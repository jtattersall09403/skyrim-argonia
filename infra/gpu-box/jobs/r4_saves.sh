#!/usr/bin/env bash
# Round 4 of 1.15, after the round job's deploy and batch: the ten region saves (nine shores and Claywater) made
# fresh on Paris in third person with the 5,000-gold kit, pushed to the shared pool copy, the machine stopped.
# Resumable: reruns remake only what is missing. Run under tooling/job_guard.sh run --gpu=argonia-play r4-saves -- ...
set -u
cd /home/ubuntu/skyrim-argonia
export ARGONIA_PLAY=argonia-play
run=infra/gpu-box/run.sh
~/.argonia/scripts/up_until.sh argonia-play 120 || exit 3
$run ps 'powershell -ExecutionPolicy Bypass -File C:\argonia\infra\stack.ps1 menu' >/dev/null 2>&1 || true
# the launch returns at once: wait for the bridge (Steam's post-boot restart and the shader compile can take 15 min;
# the first saves job called the bridge before the game was up, 03:40)
infra/gpu-box/jobs/ping_until.sh 45 || { echo "SAVES FAILED: no bridge after 15 min"; $run stop; exit 3; }
if $HOME/.argonia/venv/bin/python infra/gpu-box/region_saves.py --fresh; then
  infra/gpu-box/jobs/saves_push.sh && echo "SAVES OK $(date -u +%H:%M)"
else echo "SAVES FAILED"; $run stop; exit 3; fi
$run stop
