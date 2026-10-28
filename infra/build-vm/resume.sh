#!/usr/bin/env bash
# Run once at every boot by argonia-resume.service (chunk 0.0 §a). Opens tmux session `argonia` in the repo and
# decides what Claude Code does there, from the clean-stop marker:
#
#   no marker                    the machine stopped mid-task (spot reclaim, manual stop): resume the work
#   marker + a new owner comment woken by a reply: read the owner's comments and act on them
#   marker, nothing new          the owner started the machine: Claude waits at its prompt, nothing resumes
#
# An agent that stops on purpose writes the marker with tooling/agent_stop.sh; idle-stop.sh writes it when the
# machine goes idle; the UserPromptSubmit hook in .claude/settings.json clears it when any work starts.
#   resume.sh --dry   print the mode it would choose, start nothing
set -euo pipefail
DRY=0; [ "${1:-}" = "--dry" ] && DRY=1

REPO="$HOME/skyrim-argonia"
STATE="$HOME/.argonia/state"
export PATH="$HOME/.local/bin:$PATH"
mkdir -p "$STATE"
[ $DRY = 1 ] || rm -f "$STATE/last-active"

if [ $DRY = 0 ] && tmux has-session -t argonia 2>/dev/null; then exit 0; fi

CLAUDE="claude --permission-mode auto"
mode=idle
if [ ! -f "$STATE/clean-stop" ]; then
  mode=resume
else
  since=$(python3 -I -c 'import json,sys; print(json.load(open(sys.argv[1]))["at"])' "$STATE/clean-stop" 2>/dev/null || echo "")
  # Wait briefly for the network, then look for owner comments on owner issues since the stop.
  for _ in 1 2 3 4 5 6; do gh api rate_limit >/dev/null 2>&1 && break; sleep 5; done
  if [ -n "$since" ] && python3 -I "$REPO/tooling/owner_inbox.py" --new-since "$since" --quiet; then
    mode=wake
  fi
fi

case "$mode" in
  resume) cmd="$CLAUDE --continue \"\$(cat infra/build-vm/prompts/resume.md)\" || $CLAUDE \"\$(cat infra/build-vm/prompts/resume.md)\"" ;;
  wake)   cmd="$CLAUDE --continue \"\$(cat infra/build-vm/prompts/wake.md)\" || $CLAUDE \"\$(cat infra/build-vm/prompts/wake.md)\"" ;;
  idle)   cmd="$CLAUDE" ;;
esac
if [ $DRY = 1 ]; then echo "mode: $mode"; exit 0; fi
printf '%s %s\n' "$(date -u +%FT%TZ)" "$mode" >> "$STATE/boots.log"
logger -t argonia-resume "boot mode: $mode"
tmux new-session -d -s argonia -c "$REPO" "bash -lc '$cmd; exec bash'"
