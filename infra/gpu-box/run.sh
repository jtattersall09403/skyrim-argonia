#!/usr/bin/env bash
# Drive the Windows game machine from the build VM over SSH (chunk 0.0 §b).
#   run.sh ip                       print its private IP
#   run.sh ps '<powershell>'        run a command
#   run.sh setup [stage]            copy infra/gpu-box/*.ps1 over and run setup.ps1, rebooting when it asks
#   run.sh put <local> <remote>     copy a file or directory to the machine
#   run.sh start | stop             start or stop the instance
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
ps() { ssh "${SSH_OPTS[@]}" "Administrator@$(ip)" "$@"; }
wait_ssh() {
  local i; for i in $(seq 1 24); do ps 'hostname' >/dev/null 2>&1 && return 0; read -t 10 < /dev/zero 2>/dev/null || true; done
  echo "no SSH after 4 minutes" >&2; return 1
}

case "${1:-}" in
  ip) ip ;;
  ps) shift; ps "$*" ;;
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
  start) aws ec2 start-instances --region $R --instance-ids "$(id)" >/dev/null; wait_ssh; echo "running at $(ip)" ;;
  stop) aws ec2 stop-instances --region $R --instance-ids "$(id)" >/dev/null; echo stopping ;;
  *) sed -n '2,8p' "$0"; exit 2 ;;
esac
