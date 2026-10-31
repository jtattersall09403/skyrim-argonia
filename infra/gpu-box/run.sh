#!/usr/bin/env bash
# Drive a Windows game machine from the build VM over SSH (chunk 0.0 §b).
#   run.sh [--machine argonia-play-N] <cmd> ...   or ARGONIA_PLAY=argonia-play-N; default argonia-play
#   run.sh machine                  print the machine's name and instance id (no SSH): the dry run
#   run.sh ip                       print its private IP
#   run.sh ps '<powershell>'        run a command
#   run.sh setup [stage]            copy infra/gpu-box/*.ps1 over and run setup.ps1, rebooting when it asks
#   run.sh put <local>... <remote>  copy files or directories to the machine (several: one scp, <remote> a directory)
#   run.sh get <remote> <local>     copy a file or directory back
#   run.sh desktop '<powershell>'   run in the logged-in desktop session (GUI apps, display settings); waits
#   run.sh start | stop             start or stop the instance
#   run.sh up                       start it whatever its state: waits out a stop still in progress first
set -euo pipefail
case "${1:-}" in --machine) export ARGONIA_PLAY=$2; shift 2 ;; --machine=*) export ARGONIA_PLAY=${1#--machine=}; shift ;; esac
M=${ARGONIA_PLAY:-argonia-play}
case "$M" in argonia-play|argonia-play-[0-9a-z]*) ;; *) echo "no such game machine: $M" >&2; exit 2 ;; esac
export PATH="$HOME/.local/bin:$PATH"
here=$(cd "$(dirname "$0")" && pwd)
KEY="$HOME/.argonia/keys/argonia-play"
# Region and address from machines.conf (#27).
read -r R ADDR < <(awk -v m="$M" '$1==m {print $2, $3; f=1} END {if (!f) print "eu-west-2 private"}' "$here/machines.conf")
[ "$ADDR" = public ] && IPQ=PublicIpAddress || IPQ=PrivateIpAddress
# The address is cached for 5 min (a describe-instances is ~1.5 s, and an agent makes hundreds of calls); start, stop
# and up drop it, since a public address changes at every start.
C="$HOME/.argonia/cache"; mkdir -p "$C"
# A public-address machine allows SSH only from the build VM, whose public IP changes at every start (no Elastic
# IP): open port 22 to today's address on the machine's security group (idempotent; a duplicate is refused).
open_ssh() {
  [ "$ADDR" = public ] || return 0
  local me sg; me=$(curl -s -m 5 https://checkip.amazonaws.com) || return 0
  [ "$(cat "$C/sg-$M" 2>/dev/null)" = "$me" ] && return 0  # already opened to this address (saves ~3 s a call)
  sg=$(aws ec2 describe-instances --region $R --filters Name=tag:Name,Values="$M" \
    --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId' --output text)
  aws ec2 authorize-security-group-ingress --region $R --group-id "$sg" \
    --ip-permissions "IpProtocol=tcp,FromPort=22,ToPort=22,IpRanges=[{CidrIp=$me/32,Description=build-vm}]" >/dev/null 2>&1 || true
  echo "$me" > "$C/sg-$M"
}

ip() {
  local f="$C/ip-$M" a
  if [ -n "$(find "$f" -mmin -5 2>/dev/null)" ]; then cat "$f"; return; fi
  a=$(aws ec2 describe-instances --region $R --filters Name=tag:Name,Values="$M" \
    Name=instance-state-name,Values=pending,running,stopping,stopped \
    --query "Reservations[0].Instances[0].$IPQ" --output text)
  [[ "$a" =~ ^[0-9]+(\.[0-9]+){3}$ ]] && echo "$a" > "$f"
  echo "$a"
}
id() {
  aws ec2 describe-instances --region $R --filters Name=tag:Name,Values="$M" \
    Name=instance-state-name,Values=pending,running,stopping,stopped \
    --query 'Reservations[0].Instances[0].InstanceId' --output text
}
SSH_OPTS=(-i "$KEY" -o StrictHostKeyChecking=accept-new -o ConnectTimeout=8 -o BatchMode=yes -o ServerAliveInterval=30)
# Every command refreshes the machine's busy flag, so idle-stop.ps1 never stops it between an agent's commands.
ps() {  # a connection failure (255) with a cached address re-reads it once: the machine was restarted elsewhere
  local rc=0; ssh "${SSH_OPTS[@]}" "Administrator@$(ip)" "New-Item -ItemType File -Force C:\argonia\state\busy | Out-Null; $*" || rc=$?
  if [ $rc = 255 ] && [ -f "$C/ip-$M" ]; then rm -f "$C/ip-$M"
    rc=0; ssh "${SSH_OPTS[@]}" "Administrator@$(ip)" "New-Item -ItemType File -Force C:\argonia\state\busy | Out-Null; $*" || rc=$?; fi
  return $rc
}
wait_ssh() {
  local i; for i in $(seq 1 24); do ps 'hostname' >/dev/null 2>&1 && return 0; read -t 10 < /dev/zero 2>/dev/null || true; done
  echo "no SSH after 4 minutes" >&2; return 1
}

case "${1:-}" in
  start|stop|up) rm -f "$C/ip-$M" ;;
esac
case "${1:-}" in
  machine|stop) ;;
  *) open_ssh ;;
esac
# No address (no such machine in its region, or stopped with a public address) fails here by name, not as ssh's
# "Could not resolve hostname none" (paris-card2, 2026-10-31).
case "${1:-}" in
  ps|put|get|desktop|setup) a=$(ip); [[ "$a" =~ ^[0-9]+(\.[0-9]+){3}$ ]] || { echo "run.sh: $M has no address in $R (got '$a'): not running, or not named so" >&2; exit 3; } ;;
esac
case "${1:-}" in
  machine) echo "$M $(id)" ;;
  ip) ip ;;
  ps) shift; ps "$*" ;;
  desktop)
    # DESKTOP_JOB names the job (default "job"): its task, script, log and done flag are its own, so a long GUI job
    # (lod.sh's, hours) and the bridge's short ones (launch, stills, the pad) run side by side (game-12).
    shift; j=${DESKTOP_JOB:-job}
    case "$j" in *[!a-z0-9-]*|'') echo "DESKTOP_JOB: [a-z0-9-] only" >&2; exit 2 ;; esac
    printf '%s\n' "$*" > "${TMPDIR:-/tmp}/argonia-desktop-$M-$j.ps1"
    scp "${SSH_OPTS[@]}" "${TMPDIR:-/tmp}/argonia-desktop-$M-$j.ps1" "Administrator@$(ip):C:/argonia/desktop-$j.ps1" >/dev/null
    ps '$o="C:\argonia\logs\desktop-'"$j"'.log"; Remove-Item $o -EA SilentlyContinue
$a=New-ScheduledTaskAction -Execute powershell.exe -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -Command try { & C:\argonia\desktop-'"$j"'.ps1 *> $o } finally { New-Item C:\argonia\logs\desktop-'"$j"'.done -Force }"
Remove-Item C:\argonia\logs\desktop-'"$j"'.done -EA SilentlyContinue
Register-ScheduledTask -TaskName argonia-desktop-'"$j"' -Action $a -User Administrator -RunLevel Highest -Force | Out-Null
Start-ScheduledTask argonia-desktop-'"$j"'
for ($i=0; $i -lt '"${DESKTOP_WAIT:-240}"' -and -not (Test-Path C:\argonia\logs\desktop-'"$j"'.done); $i++) { Start-Sleep 1 }
Get-Content $o -EA SilentlyContinue' ;;
  get) scp "${SSH_OPTS[@]}" -r "Administrator@$(ip):$2" "$3" ;;
  put) shift; dst=${!#}; scp "${SSH_OPTS[@]}" -r "${@:1:$#-1}" "Administrator@$(ip):$dst" ;;
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
  # stop names its machine first: GPU_NAME=... (not ARGONIA_PLAY) once stopped argonia-play silently (1.8, 2026-10-31)
  stop) echo "stopping $M ($R)"; "$here/saves.sh" backup || echo "saves backup failed" >&2; aws ec2 stop-instances --region $R --instance-ids "$(id)" >/dev/null; echo "stopping $M" ;;
  *) sed -n '2,10p' "$0"; exit 2 ;;
esac
