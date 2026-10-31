#!/usr/bin/env bash
# The stream-feel check (chunk 1.8 item 8): drive.mjs once per device on the agents' game machine, each from the
# plain-armed scene on the base save (menu, move, attack; stills of each; the marker's press-to-screen), then
# feel.py's estimate of the owner's experience. Output: out/feel/<stamp>/summary.json.
# An ability, not a regular test: run it when the owner asks, or when a change can affect touch, the pad, viewports
# or the stream. Never in make check, run_batch or a journey batch. One device costs about two minutes.
#   ARGONIA_PLAY=argonia-play-2 feel.sh [--device <d>]... [d...]   d: desktop v5-folded v5-unfolded gamesir (default all)
#   run under: tooling/job_guard.sh run --gpu=argonia-play-2 feel -- infra/stream-client/e2e/feel.sh
# Phones and the pad use the machine's own Chrome (ARGONIA_BROWSER=box: H.265 decoded on the GPU, as the phone
# decodes in hardware); desktop uses the build VM's Chrome on a virtual screen (pointer lock needs a real window).
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
repo=$(cd "$here/../../.." && pwd)
[ -n "${ARGONIA_PLAY:-}" ] && [ "$ARGONIA_PLAY" != argonia-play ] || { echo "feel.sh: set ARGONIA_PLAY to the agents' machine (never argonia-play)" >&2; exit 2; }
run="$here/../../gpu-box/run.sh"
devices=(); while [ $# -gt 0 ]; do case $1 in --device) devices+=("$2"); shift 2 ;; --device=*) devices+=("${1#*=}"); shift ;; *) devices+=("$1"); shift ;; esac; done; [ ${#devices[@]} -gt 0 ] || devices=(desktop v5-folded v5-unfolded gamesir)
stamp=$(date -u +%Y%m%dT%H%M%S)
dir="$repo/out/feel/$stamp"; mkdir -p "$dir"
e2e="$here/../build/e2e"; mkdir -p "$e2e"
[ -f "$e2e/package.json" ] || echo '{"private":true}' > "$e2e/package.json"
export PUPPETEER_CACHE_DIR="$e2e/.cache"
[ -d "$e2e/node_modules/puppeteer" ] || (cd "$e2e" && npm install --no-audit --no-fund puppeteer@23.6.0 >/dev/null)
ln -sfn "$e2e/node_modules" "$dir/node_modules"; echo '{"private":true}' > "$dir/package.json"
# the machine's test Chrome (start-test-chrome.ps1), started once
"$run" put "$repo/infra/gpu-box/start-test-chrome.ps1" 'C:/argonia/start-test-chrome.ps1' >/dev/null
DESKTOP_JOB=test-chrome "$run" desktop '& C:\argonia\start-test-chrome.ps1' >/dev/null || true
first=1
for d in "${devices[@]}"; do
  case $d in desktop) kind=desktop prof=desktop ;; v5-folded|v5-unfolded) kind=touch prof=$d ;; gamesir) kind=pad prof=v5-folded ;;
    *) echo "unknown device $d" >&2; exit 2 ;; esac
  mkdir -p "$dir/$d"
  # the first run starts Argonia (Sunshine resumes it for the rest); the pad connects 3 s after load
  wait_ms=$([ $first = 1 ] && echo 60000 || echo 4000)
  python3 -I "$here/feel.py" steps "$kind" "$wait_ms" "$dir/$d/steps.json"
  "$run" ps 'Start-ScheduledTask argonia-moonlight-web; Start-Sleep 6' >/dev/null
  env=(ARGONIA_DEVICE=$prof ARGONIA_APP='shaders on')
  [ $first = 1 ] && env+=(ARGONIA_CANCEL=1)
  [ $d = gamesir ] && env+=(ARGONIA_FAKEPAD=1)
  [ $kind = desktop ] || env+=(ARGONIA_BROWSER=box)
  echo "== $d ($(date -u +%T))"
  t0=$(date +%s)
  env "${env[@]}" ARGONIA_HEADFUL=1 xvfb-run -a -s "-screen 0 2560x1600x24" \
    node "$here/drive.mjs" "$dir/$d" webrtc "$dir/$d/steps.json" 2>&1 | tee "$dir/$d/drive.log" || true
  echo "$d took $(( $(date +%s) - t0 )) s" | tee -a "$dir/times.txt"
  first=0
done
python3 -I "$here/feel.py" summarize "$dir"
