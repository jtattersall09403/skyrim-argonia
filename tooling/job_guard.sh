#!/usr/bin/env bash
# Long jobs in the background with a log, and a wait that returns within 270 s (CLAUDE.md). The idle-stop never
# stops the machine while a job's pid is alive. 0.1 extends this; the interface stays.
#   job_guard.sh run [--gpu[=<machine>]] <name> -- <command...>   start; --gpu takes that game machine's lock
#     (default $ARGONIA_PLAY, else argonia-play; the job runs with ARGONIA_PLAY set to it, so run.sh, stack.py,
#     skse_build.sh and bridge.py inside it drive that machine). Locks are per machine: two machines' jobs run side
#     by side; a second job on one machine queues for the lock (up to $GPU_WAIT s, default 7200; GPU_WAIT=0 exits at
#     once) and `status` shows it as queued behind the holder. argonia-play keeps the old gpu.lock.
#   job_guard.sh reserve [--gpu[=<machine>]] <lane> [--minutes N]   hold a machine for a whole slot (default 90 min;
#     call again to renew): writes <lock>.slot. `run --gpu` with ARGONIA_LANE=<lane> queues (up to GPU_WAIT) behind
#     another lane's live slot, printing "queued behind slot of <lane> until <time>"; an expired slot is ignored.
#   job_guard.sh release [--gpu[=<machine>]] <lane>   free the slot (only its own lane's)
#   job_guard.sh wait <name>                          wait up to 270 s; exit 0 done-ok, 1 done-failed, 3 still running
#   job_guard.sh status [<name>] | log <name>
set -euo pipefail
JOBS="$HOME/.argonia/jobs"; mkdir -p "$JOBS"
cmd=${1:-}; shift || true
# Parses an optional --gpu[=machine] from "$@" (sets gpu, ARGONIA_PLAY, lock, and shifts via $shiftn).
parse_gpu() {
  gpu=0; shiftn=0
  case "${1:-}" in
    --gpu) gpu=1; shiftn=1; export ARGONIA_PLAY="${ARGONIA_PLAY:-argonia-play}" ;;
    --gpu=*) gpu=1; shiftn=1; export ARGONIA_PLAY="${1#--gpu=}" ;;
  esac
  if [ $gpu = 1 ]; then
    case "$ARGONIA_PLAY" in argonia-play|argonia-play-[0-9]*) ;; *) echo "no such game machine: $ARGONIA_PLAY" >&2; exit 2 ;; esac
    lock="$JOBS/gpu.lock"; [ "$ARGONIA_PLAY" = argonia-play ] || lock="$JOBS/gpu-$ARGONIA_PLAY.lock"
  fi
}
# Slot file: "<lane> <expiry epoch>". Prints the other lane's live slot as "<lane> <epoch>", else nothing.
foreign_slot() { # lock lane
  local l e; read -r l e < "$1.slot" 2>/dev/null || return 0
  [ -n "${l:-}" ] && [ "${e:-0}" -gt "$(date +%s)" ] && [ "$l" != "$2" ] && echo "$l $e" || true
}
case "$cmd" in
  _slotwait) # internal: lock lane wait_s; exit 0 when no other lane's live slot, 1 on giving up
    lock=$1; lane=$2; end=$((SECONDS + $3)); said=0
    while :; do
      fs=$(foreign_slot "$lock" "$lane"); [ -z "$fs" ] && exit 0
      [ $said = 0 ] && { echo "queued behind slot of ${fs% *} until $(date -d "@${fs#* }" +%H:%M:%S)"; said=1; }
      [ $SECONDS -ge $end ] && exit 1
      sleep 1
    done ;;
  reserve|release)
    parse_gpu "$@"; shift $shiftn
    [ $gpu = 1 ] || { export ARGONIA_PLAY="${ARGONIA_PLAY:-argonia-play}"; parse_gpu --gpu; }
    lane=${1:?lane required}; shift; mins=90
    [ "${1:-}" = "--minutes" ] && mins=${2:?}
    if [ "$cmd" = reserve ]; then
      fs=$(foreign_slot "$lock" "$lane")
      if [ -n "$fs" ]; then echo "slot held by ${fs% *} until $(date -d "@${fs#* }" +%H:%M:%S)" >&2; exit 1; fi
      echo "$lane $(( $(date +%s) + mins * 60 ))" > "$lock.slot"
      echo "reserved $ARGONIA_PLAY for $lane for $mins min"
    else
      read -r l e < "$lock.slot" 2>/dev/null || l=""
      if [ -z "$l" ] || [ "$l" = "$lane" ]; then rm -f "$lock.slot"; echo "released $ARGONIA_PLAY"
      else echo "slot belongs to $l, not $lane" >&2; exit 1; fi
    fi ;;
  run)
    parse_gpu "$@"; shift $shiftn
    name=$1; shift; [ "${1:-}" = "--" ] && shift
    if [ -f "$JOBS/$name.pid" ] && kill -0 "$(cat "$JOBS/$name.pid")" 2>/dev/null; then echo "job $name already running" >&2; exit 2; fi
    rm -f "$JOBS/$name.rc" "$JOBS/$name.started"
    if [ $gpu = 1 ]; then
      wait_s=${GPU_WAIT:-7200}; lane=${ARGONIA_LANE:-}; me=$(readlink -f "$0"); holder=$(cat "$lock.holder" 2>/dev/null || echo "?")
      # The holder file names the job inside the lock; `started` marks that this one got it (queued until then).
      setsid nohup bash -c 'echo "queued for '"$ARGONIA_PLAY"' behind '"$holder"' (up to '"$wait_s"' s)"
        if [ -n "'"$lane"'" ]; then bash "'"$me"'" _slotwait "'"$lock"'" "'"$lane"'" '"$wait_s"' || { echo 1 > "'"$JOBS/$name.rc"'"; echo "slot wait gave up"; exit 1; }; fi
        flock -w '"$wait_s"' "'"$lock"'" bash -c '"'"'echo '"$name"' > "'"$lock"'.holder"; touch "'"$JOBS/$name.started"'"
          echo "got the lock"; "$@"; echo $? > "'"$JOBS/$name.rc"'"'"'"' _ "$@" || { rc=$?; [ -f "'"$JOBS/$name.rc"'" ] || echo "$rc" > "'"$JOBS/$name.rc"'"; echo "lock wait gave up (rc $rc)"; }' _ "$@" > "$JOBS/$name.log" 2>&1 &
    else
      setsid nohup bash -c '"$@"; echo $? > "'"$JOBS/$name.rc"'"' _ "$@" > "$JOBS/$name.log" 2>&1 &
    fi
    echo $! > "$JOBS/$name.pid"; echo "started $name (pid $!), log $JOBS/$name.log" ;;
  wait)
    name=$1; end=$((SECONDS + 270))
    while [ $SECONDS -lt $end ]; do
      if [ -f "$JOBS/$name.rc" ]; then rc=$(cat "$JOBS/$name.rc"); tail -5 "$JOBS/$name.log"; [ "$rc" = 0 ] && exit 0 || exit 1; fi
      if ! kill -0 "$(cat "$JOBS/$name.pid" 2>/dev/null || echo 0)" 2>/dev/null; then
        # The job may have written its result and exited between the two checks: look once more before calling it dead.
        if [ -f "$JOBS/$name.rc" ]; then continue; fi
        echo "job $name died without a result (gpu lock busy?)"; tail -5 "$JOBS/$name.log"; exit 1; fi
      read -t 5 < /dev/zero 2>/dev/null || true
    done
    echo "job $name still running"; tail -3 "$JOBS/$name.log"; exit 3 ;;
  status)
    for f in "$JOBS"/${1:-*}.pid; do [ -e "$f" ] || continue; n=$(basename "$f" .pid)
      if [ -f "$JOBS/$n.rc" ]; then echo "$n done rc=$(cat "$JOBS/$n.rc")"; elif kill -0 "$(cat "$f")" 2>/dev/null; then
        if grep -q '^queued' "$JOBS/$n.log" 2>/dev/null && [ ! -f "$JOBS/$n.started" ]; then echo "$n queued ($(head -1 "$JOBS/$n.log"))"; else echo "$n running"; fi; else echo "$n dead"; fi; done
    for f in "$JOBS"/gpu*.lock.slot; do [ -e "$f" ] || continue; read -r l e < "$f" || continue
      if [ "${e:-0}" -gt "$(date +%s)" ]; then echo "slot $(basename "$f" .lock.slot): $l until $(date -d "@$e" +%H:%M:%S)"
      else echo "slot $(basename "$f" .lock.slot): $l expired"; fi; done ;;
  log) tail -n 50 "$JOBS/$1.log" ;;
  *) sed -n '2,15p' "$0"; exit 2 ;;
esac
