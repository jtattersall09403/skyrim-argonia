#!/usr/bin/env bash
# Every 2 minutes (argonia-owner-wake.timer): an owner comment nobody has read wakes the agent, whatever it armed.
# 2026-11-02: the owner's reply on #37 sat 50 minutes because the session's 30-minute reply watcher (a Monitor)
# had lapsed at the hand-over and nothing else on the build VM reads GitHub while a session is alive.
#   claude alive   the wake prompt is typed into the tmux session's first window (queued behind a running turn)
#   none           resume.sh (its own rules: resume, or wake when the clean-stop marker is set and the owner wrote)
# One wake per comment: the newest unread comment's time is kept in state/owner-wake-sent.
#   owner-wake.sh --dry   print what it would do, send nothing
set -euo pipefail
DRY=0; [ "${1:-}" = "--dry" ] && DRY=1
REPO="$HOME/skyrim-argonia"; STATE="$HOME/.argonia/state"
export PATH="$HOME/.local/bin:$PATH"
cd "$REPO"
latest=$(python3 -I tooling/owner_inbox.py --unread --peek 2>/dev/null | grep -oE '\(20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9:]{8}Z\)' | tr -d '()' | sort | tail -1 || true)
sent=$(cat "$STATE/owner-wake-sent" 2>/dev/null || echo "")
if [ -z "$latest" ] || [ ! "$latest" \> "$sent" ]; then [ $DRY = 1 ] && echo "nothing new (latest '$latest', sent '$sent')"; exit 0; fi
if pgrep -u "$(id -u)" -f '(^|/)claude( |$)' >/dev/null && tmux has-session -t argonia 2>/dev/null; then
  what="wake prompt typed into tmux argonia:0"
  if [ $DRY = 0 ]; then
    tmux send-keys -t argonia:0 -l "$(tr '\n' ' ' < infra/build-vm/prompts/wake.md)"; tmux send-keys -t argonia:0 Enter
  fi
else
  what="no Claude Code: resume.sh"
  [ $DRY = 0 ] && "$REPO/infra/build-vm/resume.sh"
fi
[ $DRY = 0 ] && echo "$latest" > "$STATE/owner-wake-sent"
logger -t argonia-owner-wake "owner comment $latest: $what"
echo "owner comment $latest: $what"
