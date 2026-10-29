#!/usr/bin/env bash
# Run drive.mjs with a fresh Moonlight-Web (a finished or failed WebRTC session can leave its UDP socket held,
# an upstream bug, so every later stream start fails until it restarts).
#   drive.sh <steps.json>      run under: tooling/job_guard.sh run drive -- infra/stream-client/e2e/drive.sh <steps>
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
"$here/../../gpu-box/run.sh" ps 'Start-ScheduledTask argonia-moonlight-web; Start-Sleep 6' >/dev/null
# headful on a virtual screen: pointer lock and mobile touch emulation behave as on a real device
PUPPETEER_CACHE_DIR="$here/../build/e2e/.cache" ARGONIA_HEADFUL=1 xvfb-run -a -s "-screen 0 2560x1600x24" \
  node "$here/drive.mjs" "$here/../build/e2e" webrtc "$1"
