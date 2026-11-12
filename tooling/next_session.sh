#!/usr/bin/env bash
# Start the session an owner asked to be queued behind this one: a new Claude Code window in tmux session
# `argonia`, on the model given, with the prompt kept in ~/.argonia/state/next-session-prompt.md. Run it as the
# last step of the session that queues it; the prompt file is moved aside so it starts once.
#   tooling/next_session.sh [model]      default model: claude-fable-5-2
set -euo pipefail
P="$HOME/.argonia/state/next-session-prompt.md"
[ -s "$P" ] || { echo "next_session: no queued prompt at $P" >&2; exit 1; }
MODEL="${1:-claude-fable-5-2}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
RUN="$HOME/.argonia/state/next-session-prompt.started.md"
mv "$P" "$RUN"
tmux has-session -t argonia 2>/dev/null || tmux new-session -d -s argonia -c "$REPO"
tmux new-window -t argonia -n next -c "$REPO" "bash -lc 'claude --permission-mode auto --model $MODEL \"\$(cat $RUN)\"; exec bash'"
rm -f "$HOME/.argonia/state/clean-stop"
echo "next session started in tmux window argonia:next on $MODEL"
