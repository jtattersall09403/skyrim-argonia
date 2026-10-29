#!/usr/bin/env bash
# Drive the Windows game machine from the build VM over SSH (chunk 0.0 §b).
#   run.sh ip                       print its private IP
#   run.sh ps '<powershell>'        run a command
#   run.sh setup [stage]            copy infra/gpu-box/*.ps1 over and run setup.ps1, rebooting when it asks
#   run.sh put <local> <remote>     copy a file or directory to the machine
#   run.sh desktop '<powershell>'   run in the logged-in desktop session (GUI apps, display settings); waits
#   run.sh start | stop             start or stop the instance
#   run.sh up                       start it whatever its state: waits out a stop still in progress first
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
here=$(cd "$(dirname "$0")" && pwd)
KEY="$HOME/.argonia/keys/argonia-play"
R=eu-west-2

ip() {
  aws ec2 describe-instances --region $R --filters Name=tag:Name,Values=argonia-play \
    Name=instance-state-name,Values=pending,running,stopping,stopped \
    --query 'Reservations[0].Instances[0].PrivateIpAddress' --output text
}
id() {
  aws ec2 describe-instances --region $R --filters Name=tag:Name,Values=argonia-play \
    Name=instance-state-name,Values=pending,running,stopping,stopped \
    --query 'Reservations[0].Instances[0].InstanceId' --output text
}
SSH_OPTS=(-i "$KEY" -o StrictHostKeyChecking=accept-new -o ConnectTimeout=8 -o BatchMode=yes -o ServerAliveInterval=30)
# Every command refreshes the machine's busy flag, so idle-stop.ps1 never stops it between an agent's commands.
ps() { ssh "${SSH_OPTS[@]}" "Administrator@$(ip)" "New-Item -ItemType File -Force C:\argonia\state\busy | Out-Null; $*"; }
wait_ssh() {
  local i; for i in $(seq 1 24); do ps 'hostname' >/dev/null 2>&1 && return 0; read -t 10 < /dev/zero 2>/dev/null || true; done
  echo "no SSH after 4 minutes" >&2; return 1
}

case "${1:-}" in
  ip) ip ;;
  ps) shift; ps "$*" ;;
  desktop)
    shift
    printf '%s\n' "$*" > "${TMPDIR:-/tmp}/argonia-desktop.ps1"
    scp "${SSH_OPTS[@]}" "${TMPDIR:-/tmp}/argonia-desktop.ps1" "Administrator@$(ip):C:/argonia/desktop-job.ps1" >/dev/null
    ps '$o="C:\argonia\logs\desktop-job.log"; Remove-Item $o -EA SilentlyContinue
$a=New-ScheduledTaskAction -Execute powershell.exe -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -Command try { & C:\argonia\desktop-job.ps1 *> $o } finally { New-Item C:\argonia\logs\desktop-job.done -Force }"
Remove-Item C:\argonia\logs\desktop-job.done -EA SilentlyContinue
Register-ScheduledTask -TaskName argonia-desktop-job -Action $a -User Administrator -RunLevel Highest -Force | Out-Null
Start-ScheduledTask argonia-desktop-job
for ($i=0; $i -lt '"${DESKTOP_WAIT:-240}"' -and -not (Test-Path C:\argonia\logs\desktop-job.done); $i++) { Start-Sleep 1 }
Get-Content $o -EA SilentlyContinue' ;;
  put) scp "${SSH_OPTS[@]}" -r "$2" "Administrator@$(ip):$3" ;;
  setup)
    stage="${2:-all}"
    ps 'New-Item -ItemType Directory -Force C:\argonia\infra | Out-Null'
    scp "${SSH_OPTS[@]}" "$here"/*.ps1 "Administrator@$(ip):C:/argonia/infra/" >/dev/null
    for pass in 1 2 3; do
      out=$(ps "powershell -ExecutionPolicy Bypass -File C:\\argonia\\infra\\setup.ps1 -Stage $stage" 2>&1) || { echo "$out"; exit 1; }
      echo "$out"
      grep -q REBOOT-NEEDED <<<"$out" || exit 0
      echo "rebooting (pass $pass)"; ps 'Restart-Computer -Force' >/dev/null 2>&1 || true
      read -t 45 < /dev/zero 2>/dev/null || true; wait_ssh
    done ;;
  up)
    for i in $(seq 1 60); do
      s=$(aws ec2 describe-instances --region $R --instance-ids "$(id)" --query 'Reservations[0].Instances[0].State.Name' --output text)
      [ "$s" = running ] && { wait_ssh; echo "running at $(ip)"; exit 0; }
      [ "$s" = stopped ] && break
      read -t 10 < /dev/zero 2>/dev/null || true
    done
    # A spot instance reads "stopped" a few seconds before its spot request settles; a start in that gap fails
    # with IncorrectSpotRequestState (seen 2026-10-29), so retry for a minute.
    for i in $(seq 1 12); do
      aws ec2 start-instances --region $R --instance-ids "$(id)" >/dev/null 2>&1 && break
      read -t 5 < /dev/zero 2>/dev/null || true
    done
    wait_ssh; echo "running at $(ip)" ;;
  start) aws ec2 start-instances --region $R --instance-ids "$(id)" >/dev/null; wait_ssh; echo "running at $(ip)" ;;
  stop) aws ec2 stop-instances --region $R --instance-ids "$(id)" >/dev/null; echo stopping ;;
  *) sed -n '2,8p' "$0"; exit 2 ;;
esac
