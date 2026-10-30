#!/usr/bin/env bash
# Long jobs in the background with a log, and a wait that returns within 270 s (CLAUDE.md). The idle-stop never
# stops the machine while a job's pid is alive. 0.1 extends this; the interface stays.
#   job_guard.sh run [--gpu[=<machine>]] <name> -- <command...>   start; --gpu takes that game machine's lock
#     (default $ARGONIA_PLAY, else argonia-play; the job runs with ARGONIA_PLAY set to it, so run.sh, stack.py,
#     skse_build.sh and bridge.py inside it drive that machine). Locks are per machine: two machines' jobs run side
#     by side, two jobs on one machine do not (the second exits at once). argonia-play keeps the old gpu.lock.
#   job_guard.sh wait <name>                          wait up to 270 s; exit 0 done-ok, 1 done-failed, 3 still running
#   job_guard.sh status [<name>] | log <name>
set -euo pipefail
JOBS="$HOME/.argonia/jobs"; mkdir -p "$JOBS"
cmd=${1:-}; shift || true
case "$cmd" in
  run)
    gpu=0
    case "${1:-}" in
      --gpu) gpu=1; shift; export ARGONIA_PLAY="${ARGONIA_PLAY:-argonia-play}" ;;
      --gpu=*) gpu=1; export ARGONIA_PLAY="${1#--gpu=}"; shift ;;
    esac
    if [ $gpu = 1 ]; then
      case "$ARGONIA_PLAY" in argonia-play|argonia-play-[0-9]*) ;; *) echo "no such game machine: $ARGONIA_PLAY" >&2; exit 2 ;; esac
      lock="$JOBS/gpu.lock"; [ "$ARGONIA_PLAY" = argonia-play ] || lock="$JOBS/gpu-$ARGONIA_PLAY.lock"
    fi
    name=$1; shift; [ "${1:-}" = "--" ] && shift
    if [ -f "$JOBS/$name.pid" ] && kill -0 "$(cat "$JOBS/$name.pid")" 2>/dev/null; then echo "job $name already running" >&2; exit 2; fi
    rm -f "$JOBS/$name.rc"
    if [ $gpu = 1 ]; then
      setsid nohup flock -n "$lock" bash -c '"$@"; echo $? > "'"$JOBS/$name.rc"'"' _ "$@" > "$JOBS/$name.log" 2>&1 &
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
      if [ -f "$JOBS/$n.rc" ]; then echo "$n done rc=$(cat "$JOBS/$n.rc")"; elif kill -0 "$(cat "$f")" 2>/dev/null; then echo "$n running"; else echo "$n dead"; fi; done ;;
  log) tail -n 50 "$JOBS/$1.log" ;;
  *) sed -n '2,10p' "$0"; exit 2 ;;
esac
