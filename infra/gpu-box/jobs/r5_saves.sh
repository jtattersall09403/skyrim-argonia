#!/usr/bin/env bash
# Round 5 of 1.15, after the round job's deploy and batch: the ten region saves (nine shores and Claywater) made
# fresh on Paris in third person with the 5,000-gold kit, pushed to the shared pool copy, the machine stopped.
# Resumable: reruns remake only what is missing. Run under tooling/job_guard.sh run --gpu=argonia-play r5-saves -- ...
set -u
cd "${ARGONIA_REPO:-$(cd "$(dirname "$(readlink -f "$0")")/../../.." && pwd)}" || exit 2
export ARGONIA_PLAY=argonia-play
run=infra/gpu-box/run.sh
~/.argonia/scripts/up_until.sh argonia-play 120 || exit 3
# the deploy's own launch path (bridge.py launch: kills any zombie, lays the DLL, starts to the main menu and waits for it;
# a bare stack.ps1 menu over SSH started nothing and the bridge wait ran out, 04:05)
$HOME/.argonia/venv/bin/python tools/bridge.py launch || { echo "SAVES FAILED: no main menu"; $run stop; exit 3; }
if $HOME/.argonia/venv/bin/python infra/gpu-box/region_saves.py --fresh; then
  infra/gpu-box/jobs/saves_push.sh && echo "SAVES OK $(date -u +%H:%M)"
else echo "SAVES FAILED"; $run stop; exit 3; fi
$run stop
