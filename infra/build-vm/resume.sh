#!/usr/bin/env bash
# Run once at every boot by argonia-resume.service (chunk 0.0 §a). Opens tmux session `argonia` in the repo and
# decides what Claude Code does there, from the clean-stop marker:
#
#   no marker, work was live     the session did not stop itself cleanly (idle-stop or the CPU alarm while an agent
#                                waited, a manual stop, Claude Code dying): resume; prompts/resume.md says only that
#   no marker, nothing for 15 min the machine stopped while idle (the CloudWatch CPU alarm, a manual stop): as marker
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

# A plugin-* or deploy-* job of today with a log but no rc was cut off (spot reclaim): name it for the planner,
# which relaunches it (the land build resumes from its kept rows). Never relaunched here.
JOBS="${JOBS_DIR:-$HOME/.argonia/jobs}"
today=$(date +%F)
for log in "$JOBS"/plugin-*.log "$JOBS"/deploy-*.log; do
  [ -f "$log" ] || continue
  n=$(basename "$log" .log)
  [ -f "$JOBS/$n.rc" ] || [ "$(date -r "$log" +%F)" != "$today" ] || echo "interrupted: $n"
done

if [ $DRY = 0 ] && tmux has-session -t argonia 2>/dev/null; then exit 0; fi

CLAUDE="claude --permission-mode auto"
mode=idle
# No marker is not proof of an interrupted task: the CloudWatch backstop alarm (an hour under 3% CPU) and a manual
# stop from the console write none (2026-11-05 19:31: an idle stop by the alarm read as a cut-off). The build VM is
# on demand (0008), so there are no spot reclaims. Work counts as live only if a transcript or a job log was written
# within 15 minutes of the previous boot's end; otherwise the stop was idle and is treated as a clean one.
if [ ! -f "$STATE/clean-stop" ]; then
  # the previous boot's last entry: "... Thu 2026-11-05 19:31:48 UTC" -> "2026-11-05 19:31:48"
  prev_end=$(journalctl --list-boots --no-pager 2>/dev/null | tail -2 | head -1 | awk '{print $(NF-2)" "$(NF-1)}')
  pe=$(date -u -d "$prev_end" +%s 2>/dev/null || echo 0)
  newest=$(find "$HOME/.claude/projects" "$HOME/.argonia/jobs" -type f \( -name '*.jsonl' -o -name '*.log' \) -printf '%T@\n' 2>/dev/null | cut -d. -f1 | awk -v pe="$pe" '$1 <= pe' | sort -n | tail -1)
  if [ "$pe" -gt 0 ] && [ -n "$newest" ] && [ $(( pe - newest )) -gt 900 ]; then
    idle_min=$(( (pe - newest) / 60 ))
    [ $DRY = 1 ] && echo "previous stop: idle for $idle_min min before it (no marker)"
    [ $DRY = 1 ] || printf '{"at": "%s", "reason": "stopped while idle (no activity for %s min before the stop)"}\n' \
      "$(date -u -d "@$newest" +%FT%TZ)" "$idle_min" > "$STATE/clean-stop"
  else
    mode=resume
  fi
fi
if [ -f "$STATE/clean-stop" ] && [ "$mode" != resume ]; then
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

# Parallel lanes (owner, 2026-10-29): --continue resumes only the newest session. Every other session that wrote
# its transcript within 30 minutes of the newest was working too; each gets its own window and the same prompt.
if [ "$mode" != idle ]; then
  prompt=infra/build-vm/prompts/$([ "$mode" = wake ] && echo wake || echo resume).md
  dir="$HOME/.claude/projects/$(echo "$REPO" | tr '/' '-')"
  newest=$(ls -t "$dir"/*.jsonl 2>/dev/null | head -1)
  [ -n "$newest" ] && find "$dir" -maxdepth 1 -name '*.jsonl' ! -path "$newest" -newermt "$(date -u -d "$(stat -c %y "$newest") - 30 min" +%FT%TZ)" |
    while read -r f; do
      id=$(basename "$f" .jsonl)
      tmux new-window -t argonia -n "lane-${id:0:8}" -c "$REPO" "bash -lc '$CLAUDE --resume $id \"\$(cat $prompt)\"; exec bash'"
      logger -t argonia-resume "also resumed session $id"
    done
fi
