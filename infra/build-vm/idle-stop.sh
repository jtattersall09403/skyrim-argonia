#!/usr/bin/env bash
# Stop the build VM after IDLE_MINUTES with all three of: no Claude Code activity, no job_guard job, and no
# VS Code tunnel client (chunk 0.0 §a). Run every minute by argonia-idle-stop.timer. The CloudWatch alarm
# (an hour under 2% CPU) stays as the backstop. Before it stops, it stops every running game-machine clone
# (argonia-play-N): clones serve only agents, so with no agent left they are idle, and their own idle-stop.ps1 has no
# Cloudflare watchdog behind it the way argonia-play has. argonia-play is left to its own idle-stop and the play switch,
# since the owner may be playing on it.
#
#   idle-stop.sh          check once; stop the machine if idle long enough
#   idle-stop.sh --status print each signal and the idle time, never stop
set -euo pipefail

IDLE_MINUTES="${IDLE_MINUTES:-20}"
STATE="$HOME/.argonia/state"
JOBS="$HOME/.argonia/jobs"
export PATH="$HOME/.local/bin:$PATH"
mkdir -p "$STATE"

# 1. Claude Code: a transcript written recently, or a tool shell still running under a claude process.
claude_active() {
  if find "$HOME/.claude/projects" -name '*.jsonl' -mmin "-$IDLE_MINUTES" 2>/dev/null | grep -q .; then
    echo "transcript written in the last $IDLE_MINUTES min"; return 0
  fi
  local p
  for p in $(pgrep -x claude || true); do
    if pgrep -P "$p" -f 'shell-snapshots' >/dev/null; then echo "tool running under claude $p"; return 0; fi
  done
  return 1
}

# 2. job_guard: any job whose pid is alive.
job_active() {
  local f
  for f in "$JOBS"/*.pid; do
    [ -e "$f" ] || continue
    if kill -0 "$(cat "$f")" 2>/dev/null; then echo "job $(basename "$f" .pid)"; return 0; fi
  done
  return 1
}

# 3. VS Code tunnel client: the tunnel process holds a unix socket to a VS Code server process only while a
# browser is attached (the server's own disconnect log can lag by its 3-hour reconnection grace).
tunnel_client() {
  local tpid
  tpid=$(pgrep -f 'code .*tunnel service internal-run' | head -1 || true)
  [ -n "$tpid" ] || return 1
  ss -xpH 2>/dev/null | python3 -I -c '
import re, sys
tpid = sys.argv[1]
owner, mine = {}, []
for line in sys.stdin:
    f = line.split()
    if len(f) < 8:
        continue
    pids = set(re.findall(r"pid=(\d+)", line))
    owner.setdefault(f[5], set()).update(pids)
    if tpid in pids:
        mine.append(f[7])
servers = {p for ino in mine for p in owner.get(ino, ()) if p != tpid}
sys.exit(0 if servers else 1)' "$tpid" && echo "VS Code client attached"
}

reason=""
if r=$(claude_active); then reason="$r"
elif r=$(job_active); then reason="$r"
elif r=$(tunnel_client); then reason="$r"
fi

# The CloudWatch backstop (argonia-build-idle-stop: an hour under 3% CPU) must never stop the VM while a job waits on
# AWS at low CPU (it did during a 2-hour snapshot wait, 2026-11-05): its stop action is off while a job runs, on again
# when none does. The state is cached so the API is called only on a change.
if [ "${1:-}" != "--status" ]; then
  want=on; job_active >/dev/null && want=off
  if [ "$(cat "$STATE/alarm-actions" 2>/dev/null)" != "$want" ]; then
    # the role may put the alarm but not call enable/disable-alarm-actions, so the alarm is written whole
    tok=$(curl -s -m 3 -X PUT http://169.254.169.254/latest/api/token -H 'X-aws-ec2-metadata-token-ttl-seconds: 60')
    iid=$(curl -s -m 3 -H "X-aws-ec2-metadata-token: $tok" http://169.254.169.254/latest/meta-data/instance-id)
    [ $want = off ] && act=--no-actions-enabled || act=--actions-enabled
    [ -n "$iid" ] && aws cloudwatch put-metric-alarm --region eu-west-2 --alarm-name argonia-build-idle-stop \
      --alarm-description "Stop the build VM after an hour under 3% CPU: a backstop to its idle timer; idle-stop.sh turns its action off while a job_guard job runs" \
      --namespace AWS/EC2 --metric-name CPUUtilization --dimensions "Name=InstanceId,Value=$iid" --statistic Average \
      --period 300 --evaluation-periods 12 --threshold 3 --comparison-operator LessThanThreshold \
      --treat-missing-data notBreaching --alarm-actions "arn:aws:automate:eu-west-2:ec2:stop" $act 2>/dev/null &&
      echo $want > "$STATE/alarm-actions"
  fi
fi

now=$(date +%s)
if [ -n "$reason" ]; then
  echo "$now" > "$STATE/last-active"
  [ "${1:-}" = "--status" ] && echo "active: $reason"
  exit 0
fi

last=$(cat "$STATE/last-active" 2>/dev/null || echo "$now")
[ -f "$STATE/last-active" ] || echo "$now" > "$STATE/last-active"
idle=$(( (now - last) / 60 ))
if [ "${1:-}" = "--status" ]; then echo "idle for $idle min (stops at $IDLE_MINUTES)"; exit 0; fi
[ "$idle" -ge "$IDLE_MINUTES" ] || exit 0

# Idle means nothing was mid-task: record a clean stop so the next boot does not resume (resume.sh).
if [ ! -f "$STATE/clean-stop" ]; then
  printf '{"at": "%s", "reason": "idle-stop after %s min"}\n' "$(date -u +%FT%TZ)" "$idle" > "$STATE/clean-stop"
fi
rm -f "$STATE/last-active"
logger -t argonia-idle-stop "stopping after $idle idle minutes"
repo=$(cd "$(dirname "$0")/../.." && pwd)
for r in $(awk '!/^#/ && NF {print $2}' "$repo/infra/gpu-box/machines.conf" | sort -u); do
  for m in $(aws ec2 describe-instances --region "$r" \
      --filters 'Name=tag:Name,Values=argonia-play-*' Name=instance-state-name,Values=running \
      --query 'Reservations[].Instances[].Tags[?Key==`Name`].Value' --output text 2>/dev/null || true); do
    logger -t argonia-idle-stop "stopping game machine $m"
    timeout 300 "$repo/infra/gpu-box/run.sh" --machine "$m" stop >/dev/null 2>&1 || true
  done
done
id=$(aws ec2 describe-instances --region eu-west-2 \
  --filters Name=tag:Name,Values=argonia-build Name=instance-state-name,Values=running \
  --query 'Reservations[].Instances[].InstanceId' --output text 2>/dev/null || true)
if [ -n "$id" ]; then
  aws ec2 stop-instances --region eu-west-2 --instance-ids "$id" >/dev/null
else
  sudo -n shutdown -h now
fi
