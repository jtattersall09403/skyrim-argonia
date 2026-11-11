#!/usr/bin/env bash
# Record a deliberate stop (work complete, waiting on the owner, or a handover the owner asked for), so the next
# boot does not resume (infra/build-vm/resume.sh). The machine then idle-stops by itself.
#   tooling/agent_stop.sh "waiting on the owner: issue #12"
# Before the marker, the tidy (tooling/disk.sh): landed lane worktrees, old job spools and scratch, and once a day
# the bucket. It never fails the stop.
set -euo pipefail
[ $# -ge 1 ] || { echo "usage: agent_stop.sh <reason>" >&2; exit 2; }
"$(dirname "$0")/disk.sh" tidy --quiet 2>&1 | tail -20 || true
mkdir -p "$HOME/.argonia/state"
python3 -I -c 'import json,sys,datetime
print(json.dumps({"at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "reason": sys.argv[1]}))' "$1" \
  > "$HOME/.argonia/state/clean-stop"
echo "clean stop recorded: $1"
