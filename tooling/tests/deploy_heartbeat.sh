#!/usr/bin/env bash
# deploy.sh's heartbeat must not outlive the deploy holding the job's lock fd (game-21: a `sleep 300` held gpu.lock).
# Runs deploy.sh's own heartbeat lines (with run.sh stubbed) under flock, then checks the lock is free at once.
set -euo pipefail
here=$(cd "$(dirname "$0")/../.." && pwd); d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
{ echo 'run=true'; sed -n '/^( trap .kill \$s/,/^trap .kill \$hb/p' "$here/infra/gpu-box/deploy.sh"; echo 'read -t 1 <> <(:) || true'; } > "$d/hb.sh"  # 1 s: the loop's sleep must have started
grep -q 'hb=\$!' "$d/hb.sh" || { echo "FAIL: heartbeat block not found in deploy.sh"; exit 1; }
flock "$d/lock" bash "$d/hb.sh"
if flock -w 2 "$d/lock" true; then echo "ok: lock free after the deploy's exit"; else echo "FAIL: heartbeat still holds the lock"; exit 1; fi
