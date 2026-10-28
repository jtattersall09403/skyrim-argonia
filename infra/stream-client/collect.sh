#!/usr/bin/env bash
# Pull the stream metrics from the game machine (chunk 0.0 §c) to ~/.argonia/stream-metrics/ and print a summary
# per setup, device shape and network type (medians and p95s), plus press-to-screen by input source.
#   collect.sh                    pull everything, summarise all sessions
#   collect.sh --session <id>     summarise one session (and exit 1 if it lacks ticks or press-to-screen samples)
#   collect.sh --no-pull ...      summarise what is already here
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
dest="$HOME/.argonia/stream-metrics"
mkdir -p "$dest/marker"
pull=1; [ "${1:-}" = "--no-pull" ] && { pull=0; shift; }
if [ $pull = 1 ]; then
  ip=$("$here/../gpu-box/run.sh" ip)
  opts=(-i "$HOME/.argonia/keys/argonia-play" -o BatchMode=yes -o ConnectTimeout=8 -q)
  scp "${opts[@]}" "Administrator@$ip:C:/argonia/logs/stream-metrics/*.jsonl" "$dest/" 2>/dev/null || echo "no stream-metrics logs on the box yet"
  scp "${opts[@]}" "Administrator@$ip:C:/argonia/logs/marker/*" "$dest/marker/" 2>/dev/null || true
fi
python3 -I "$here/summarize.py" "$dest" "$@"
