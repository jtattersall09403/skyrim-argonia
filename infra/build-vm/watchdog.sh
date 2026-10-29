#!/usr/bin/env bash
# Every 2 minutes (argonia-watchdog.timer): if no Claude Code process is alive and no clean-stop marker is set,
# the work died without a reboot (2026-10-29: two OOM kills took the whole tmux scope), so resume as at boot.
set -euo pipefail
STATE="$HOME/.argonia/state"
[ -f "$STATE/clean-stop" ] && exit 0
pgrep -u "$(id -u)" -f '(^|/)claude( |$)' >/dev/null && exit 0
tmux kill-session -t argonia 2>/dev/null || true
logger -t argonia-watchdog "no claude process and no clean-stop marker: resuming"
printf '%s watchdog\n' "$(date -u +%FT%TZ)" >> "$STATE/boots.log"
exec "$(dirname "$0")/resume.sh"
