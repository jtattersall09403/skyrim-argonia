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
#     An idle slot yields: when the holder lane has no running job and its newest job ended more than $SLOT_IDLE s
#     ago (default 600; a holder that never ran a job counts from the slot's creation), other lanes' jobs pass it
#     and `status` shows "(idle Nm, yielding)". `run` with ARGONIA_LANE records the job's lane in <name>.lane.
#   job_guard.sh release [--gpu[=<machine>]] <lane>   free the slot (only its own lane's)
#   job_guard.sh wait <name>                          wait up to 270 s; exit 0 done-ok, 1 done-failed, 3 still running
#   job_guard.sh status [<name>] | log <name>
#   job_guard.sh stop <name>                          end the job and everything it started (its process group)
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
    case "$ARGONIA_PLAY" in argonia-play|argonia-play-[0-9a-z]*) ;; *) echo "no such game machine: $ARGONIA_PLAY" >&2; exit 2 ;; esac
    lock="$JOBS/gpu.lock"; [ "$ARGONIA_PLAY" = argonia-play ] || lock="$JOBS/gpu-$ARGONIA_PLAY.lock"
  fi
}
# Slot file: "<lane> <expiry epoch>". Prints the other lane's live slot as "<lane> <epoch>", else nothing.
# Prints the idle seconds of lane $2's slot holder (slot file $1) when it has no running job and its newest job
# ended more than ${SLOT_IDLE:-600} s ago; nothing when it is busy or recently active.
slot_idle() { # lock lane
  local last f n now; now=$(date +%s); last=$(stat -c %Y "$1.slot" 2>/dev/null) || return 0
  for f in "$JOBS"/*.lane; do [ -e "$f" ] || continue
    [ "$(cat "$f" 2>/dev/null)" = "$2" ] || continue; n=$(basename "$f" .lane)
    if [ -f "$JOBS/$n.rc" ]; then t=$(stat -c %Y "$JOBS/$n.rc"); [ "$t" -gt "$last" ] && last=$t
    elif kill -0 "$(cat "$JOBS/$n.pid" 2>/dev/null || echo 0)" 2>/dev/null; then return 0; fi
  done
  [ $((now - last)) -gt "${SLOT_IDLE:-600}" ] && echo $((now - last)) || true
}
# Slot file: "<lane> <expiry epoch>". Prints the other lane's live, non-idle slot as "<lane> <epoch>", else nothing.
foreign_slot() { # lock lane
  local l e; { read -r l e < "$1.slot"; } 2>/dev/null || return 0
  [ -n "${l:-}" ] && [ "${e:-0}" -gt "$(date +%s)" ] && [ "$l" != "$2" ] || return 0
  [ -z "$(slot_idle "$1" "$l")" ] && echo "$l $e" || true
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
    rm -f "$JOBS/$name.rc" "$JOBS/$name.started" "$JOBS/$name.lane"
    [ -n "${ARGONIA_LANE:-}" ] && echo "$ARGONIA_LANE" > "$JOBS/$name.lane"
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
      # A bare `status` lists finished jobs from the last 6 h only (hundreds of old ones filled every lane's context);
      # `status <name>` always answers.
      if [ -f "$JOBS/$n.rc" ]; then [ -n "${1:-}" ] || [ -n "$(find "$JOBS/$n.rc" -mmin -360)" ] && echo "$n done rc=$(cat "$JOBS/$n.rc")"; elif kill -0 "$(cat "$f")" 2>/dev/null; then
        if grep -q '^queued' "$JOBS/$n.log" 2>/dev/null && [ ! -f "$JOBS/$n.started" ]; then echo "$n queued ($(head -1 "$JOBS/$n.log"))"; else  # how long it has run, and how long its log has been quiet: a long quiet log is a hang to look at
          now=$(date +%s); st=$(stat -c %Y "$JOBS/$n.started" 2>/dev/null || stat -c %Y "$f"); lw=$(stat -c %Y "$JOBS/$n.log" 2>/dev/null || echo "$now")
          echo "$n running $(( (now - st) / 60 ))m, log quiet $(( (now - lw) / 60 ))m"; fi; else echo "$n dead"; fi; done
    for f in "$JOBS"/gpu*.lock.slot; do [ -e "$f" ] || continue; read -r l e < "$f" || continue
      if [ "${e:-0}" -gt "$(date +%s)" ]; then idle=$(slot_idle "${f%.slot}" "$l"); sfx=""
        [ -n "$idle" ] && sfx=" (idle $((idle / 60))m, yielding)"
        echo "slot $(basename "$f" .lock.slot): $l until $(date -d "@$e" +%H:%M:%S)$sfx"
      else echo "slot $(basename "$f" .lock.slot): $l expired"; fi; done ;;
  log) tail -n 50 "$JOBS/$1.log" ;;
  stop)  # the whole job (its setsid process group), never only the top pid: a bare kill left a job's script running (1.8)
    p=$(cat "$JOBS/$1.pid" 2>/dev/null) || { echo "no job $1" >&2; exit 2; }
    kill -- -"$(ps -o pgid= -p "$p" | tr -d ' ')" 2>/dev/null || kill "$p" 2>/dev/null || true
    echo 143 > "$JOBS/$1.rc"; echo "stopped $1" ;;
  *) sed -n '2,18p' "$0"; exit 2 ;;
esac
