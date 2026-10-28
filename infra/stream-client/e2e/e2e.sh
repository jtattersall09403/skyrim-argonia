#!/usr/bin/env bash
# The end-to-end check (chunk 0.0 §c): headless Chrome streams the Desktop through our page, presses keys and the
# touch pad, then the collector's JSONL on the box must hold per-second stats and press-to-screen samples.
#   e2e.sh [webrtc|websocket]     run under: tooling/job_guard.sh run stream-e2e -- infra/stream-client/e2e/e2e.sh
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
out="$here/../build/e2e"
mkdir -p "$out"
[ -f "$out/package.json" ] || echo '{"private":true}' > "$out/package.json"
export PUPPETEER_CACHE_DIR="$out/.cache"
[ -d "$out/node_modules/puppeteer" ] || (cd "$out" && npm install --no-audit --no-fund puppeteer@23.6.0 >/dev/null)
res=$(node "$here/e2e.mjs" "$out" "${1:-webrtc}" | tee /dev/stderr | tail -1)
session=$(python3 -I -c 'import json,sys; print(json.loads(sys.argv[1])["session"])' "$res")
"$here/../collect.sh" --session "$session"
