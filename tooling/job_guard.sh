#!/usr/bin/env bash
# Long jobs in the background with a log, and a wait that returns within 270 s (CLAUDE.md). The idle-stop never
# stops the machine while a job's pid is alive. 0.1 extends this; the interface stays.
#   job_guard.sh run [--gpu[=<machine>|=pick]] <name> -- <command...>   start; --gpu takes that game machine's lock
#     (default $ARGONIA_PLAY, else argonia-play; =pick: the pool's choice, infra/gpu-box/pool.py pick, which in-game
#     batches use; the job runs with ARGONIA_PLAY set to it, so run.sh, stack.py,
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
# Spool (1.15): run also writes <name>.cmd (argv, NUL-separated), .cwd, .env (ARGONIA_*, PATH; NUL-separated),
#   .seq (launch order), .gpu (the machine, gpu jobs only) and .state (queued|running|done|stopped; a signal-killed job, rc >= 128, stays running). At boot
#   tooling/job_resume.sh relaunches, in .seq order, every job left queued or running (no .rc, or rc >= 128). Jobs on one
#   machine take its lock in .seq order. JOBS_DIR overrides the spool directory (tests).
set -euo pipefail
JOBS="${JOBS_DIR:-$HOME/.argonia/jobs}"; mkdir -p "$JOBS"
cmd=${1:-}; shift || true
# Parses an optional --gpu[=machine] from "$@" (sets gpu, ARGONIA_PLAY, lock, and shifts via $shiftn).
parse_gpu() {
  gpu=0; shiftn=0
  case "${1:-}" in
    --gpu) gpu=1; shiftn=1; export ARGONIA_PLAY="${ARGONIA_PLAY:-argonia-play}" ;;
    # the pool's pick (1.8 §7), the same rule as the owner's play page: never a machine someone streams on
    --gpu=pick) gpu=1; shiftn=1
      ARGONIA_PLAY=$("${PY:-python3}" "$(dirname "$(readlink -f "$0")")/../infra/gpu-box/pool.py" pick) || exit 2
      echo "pool pick: $ARGONIA_PLAY" >&2; export ARGONIA_PLAY ;;
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
# launch <script> <args...>: runs `bash -c script _ args` detached, output to the job's log; sets jpid. Under a user
# systemd it is a transient unit (its own cgroup, outside the caller's session scope), because setsid nohup jobs were
# all killed when the harness session died (2026-11-02, three 20-minute builds). Without one: setsid nohup.
launch() {
  local script=$1; shift
  if [ -z "${JOB_GUARD_NO_SYSTEMD:-}" ] && command -v systemd-run >/dev/null && case $(systemctl --user is-system-running 2>/dev/null) in running|degraded|starting|initializing) true ;; *) false ;; esac; then
    local unit="jg-$name-$(date +%s)" env=() v
    for v in $(compgen -e); do [[ $v =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] && env+=(--setenv="$v"); done
    if systemd-run --user --quiet --collect --unit="$unit" --working-directory="$PWD" "${env[@]}" \
        --property=StandardOutput="$logmode:$JOBS/$name.log" --property=StandardError=inherit \
        bash -c "$script" _ "$@"; then
      echo "$unit" > "$JOBS/$name.unit"
      local i; jpid=0  # the main pid, once the unit has one; a unit already gone finished (its rc says so)
      for i in $(seq 40); do jpid=$(systemctl --user show -p MainPID --value "$unit" 2>/dev/null || echo 0)
        [ "${jpid:-0}" != 0 ] || ! systemctl --user is-active -q "$unit" 2>/dev/null && break; read -t 0.1 < /dev/zero 2>/dev/null || true; done
      jpid=${jpid:-0}; return 0
    fi
  fi
  if [ "$logmode" = append ]; then setsid nohup bash -c "$script" _ "$@" >> "$JOBS/$name.log" 2>&1 &
  else setsid nohup bash -c "$script" _ "$@" > "$JOBS/$name.log" 2>&1 & fi
  jpid=$!
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
  _turn) # internal: machine seq wait_s; waits while an earlier-seq job on the machine is still queued (FIFO lock order)
    m=$1; seq=$2; end=$((SECONDS + $3))
    while :; do ahead=""
      for f in "$JOBS"/*.gpu; do [ -e "$f" ] || continue; n=$(basename "$f" .gpu)
        [ "$(cat "$f")" = "$m" ] && [ ! -f "$JOBS/$n.rc" ] && [ "$(cat "$JOBS/$n.state" 2>/dev/null)" = queued ] || continue
        s2=$(cat "$JOBS/$n.seq" 2>/dev/null || echo 0); [ "$s2" -lt "$seq" ] || continue
        kill -0 "$(cat "$JOBS/$n.pid" 2>/dev/null || echo 0)" 2>/dev/null && { ahead=$n; break; }
      done
      [ -z "$ahead" ] && exit 0; [ $SECONDS -ge $end ] && exit 1; sleep 1
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
    # a pid is live only if it was written this boot (.boot beside it) and the process exists: a reboot kills every job,
    # and its pid is reused after (r6-chain29, 2026-11-05); an old-boot pid file is cleared. No .boot file: pre-change job.
    if [ -f "$JOBS/$name.pid" ]; then
      if [ -f "$JOBS/$name.boot" ] && [ "$(cat "$JOBS/$name.boot")" != "$(cat /proc/sys/kernel/random/boot_id)" ]; then rm -f "$JOBS/$name.pid" "$JOBS/$name.boot"
      elif kill -0 "$(cat "$JOBS/$name.pid")" 2>/dev/null; then echo "job $name already running" >&2; exit 2; fi
    fi
    rm -f "$JOBS/$name.rc" "$JOBS/$name.started" "$JOBS/$name.lane" "$JOBS/$name.machine" "$JOBS/$name.unit" "$JOBS/$name.gpu"
    # The spool a relaunch needs (job_resume.sh). JOB_SEQ keeps a resumed job's place; else the next number.
    if [ -n "${JOB_SEQ:-}" ]; then seq=$JOB_SEQ; else
      seq=$( { flock 9; n=$(( $(cat "$JOBS/.seq" 2>/dev/null || echo 0) + 1 )); echo $n > "$JOBS/.seq"; echo $n; } 9>"$JOBS/.seq.lock" ); fi
    # a boot resume (job_resume.sh sets JOB_RESUMED) appends to the job's log after a "== RESUMED" line: truncating
    # it lost every earlier resume's lines (r6-chain7, 2026-11-04); a fresh run starts the log anew
    logmode=truncate; if [ -n "${JOB_RESUMED:-}" ]; then logmode=append; echo "== RESUMED $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$JOBS/$name.log"; fi; unset JOB_RESUMED
    echo "$seq" > "$JOBS/$name.seq"; printf '%s\0' "$@" > "$JOBS/$name.cmd"; echo "$PWD" > "$JOBS/$name.cwd"
    export PYTHONUNBUFFERED=1  # a job's python prints as it goes: r6-navmesh ran 20 min with an empty log (2026-11-04)
    for v in $(compgen -e); do [[ $v == ARGONIA_* || $v == PATH || $v == PYTHONUNBUFFERED ]] && printf '%s=%s\0' "$v" "${!v}"; done > "$JOBS/$name.env"
    if [ $gpu = 1 ]; then echo "$ARGONIA_PLAY" > "$JOBS/$name.gpu"; echo queued > "$JOBS/$name.state"; else echo running > "$JOBS/$name.state"; fi
    [ -n "${ARGONIA_LANE:-}" ] && echo "$ARGONIA_LANE" > "$JOBS/$name.lane"
    if [ $gpu = 1 ]; then
      echo "$ARGONIA_PLAY" > "$JOBS/$name.machine"  # stop ends the machine too (below)
      wait_s=${GPU_WAIT:-7200}; lane=${ARGONIA_LANE:-}; me=$(readlink -f "$0"); holder=$(cat "$lock.holder" 2>/dev/null || echo "?")
      # The holder file names the job inside the lock; `started` marks that this one got it (queued until then).
      launch 'echo "queued for '"$ARGONIA_PLAY"' behind '"$holder"' (up to '"$wait_s"' s)"
        if [ -n "'"$lane"'" ]; then bash "'"$me"'" _slotwait "'"$lock"'" "'"$lane"'" '"$wait_s"' || { echo 1 > "'"$JOBS/$name.rc"'"; echo "slot wait gave up"; exit 1; }; fi
        bash "'"$me"'" _turn "'"$ARGONIA_PLAY"'" '"$seq"' '"$wait_s"' || { echo 1 > "'"$JOBS/$name.rc"'"; echo done > "'"$JOBS/$name.state"'"; echo "turn wait gave up"; exit 1; }
        flock -w '"$wait_s"' "'"$lock"'" bash -c '"'"'echo '"$name"' > "'"$lock"'.holder"; touch "'"$JOBS/$name.started"'"; echo running > "'"$JOBS/$name.state"'"
          echo "got the lock"; "$@"; rc=$?; echo $rc > "'"$JOBS/$name.rc"'"; [ $rc -ge 128 ] || echo done > "'"$JOBS/$name.state"'"'"'"' _ "$@" || { rc=$?; [ -f "'"$JOBS/$name.rc"'" ] || echo "$rc" > "'"$JOBS/$name.rc"'"; [ $rc -ge 128 ] || echo done > "'"$JOBS/$name.state"'"; echo "lock wait gave up (rc $rc)"; }' "$@"
    else
      launch '"$@"; rc=$?; echo $rc > "'"$JOBS/$name.rc"'"; [ $rc -ge 128 ] || echo done > "'"$JOBS/$name.state"'"' "$@"
    fi
    cat /proc/sys/kernel/random/boot_id > "$JOBS/$name.boot"; echo $jpid > "$JOBS/$name.pid"; echo "started $name (pid $jpid), log $JOBS/$name.log" ;;
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
    [ "${2:-}" = --keep-machine ] && KEEP_MACHINE=1
    p=$(cat "$JOBS/$1.pid" 2>/dev/null) || { echo "no job $1" >&2; exit 2; }
    if u=$(cat "$JOBS/$1.unit" 2>/dev/null) && [ -n "$u" ]; then systemctl --user stop "$u" 2>/dev/null || true  # the unit's whole cgroup
    else kill -- -"$(ps -o pgid= -p "$p" | tr -d ' ')" 2>/dev/null || kill "$p" 2>/dev/null || true; fi
    echo 143 > "$JOBS/$1.rc"; echo stopped > "$JOBS/$1.state"; echo "stopped $1"
    # A machine job's machine stops with it, unless someone streams on it: a stopped job left argonia-play-ie running
    # idle 40 min, its idle-stop held busy by the job's last SSH and busy flag (1.8, 2026-10-31).
    # Only a job that had the machine stops it: a queued job never held it, and stopping one stopped the job running
    # on it (the planner, 2026-11-01).
    # ...and never when another job is queued for or running on that machine (2026-11-02: stopping a queued job
    # stopped Paris twice under a running chain, and the on-demand LOD box once), nor with --keep-machine.
    others=""
    if m=$(cat "$JOBS/$1.machine" 2>/dev/null) && [ -n "$m" ]; then
      for f in "$JOBS"/*.machine; do
        o=$(basename "$f" .machine); [ "$o" = "$1" ] && continue
        [ "$(cat "$f" 2>/dev/null)" = "$m" ] || continue
        st=$(cat "$JOBS/$o.state" 2>/dev/null); [ -f "$JOBS/$o.rc" ] && [ "$st" != running ] && continue
        case "$st" in queued|running) others="$others $o" ;; esac
      done
    fi
    if [ -n "$others" ]; then echo "not stopping $m: still held or queued by$others"
    elif [ "${KEEP_MACHINE:-0}" = 1 ]; then echo "not stopping $m: --keep-machine"
    elif [ -f "$JOBS/$1.started" ] && [ -n "${m:-}" ]; then
      run="$(dirname "$(readlink -f "$0")")/../infra/gpu-box/run.sh"
      r=$(awk -v m="$m" '$1==m {print $2}' "$(dirname "$run")/machines.conf"); r=${r:-eu-west-2}  # run.sh's default
      st=$(aws ec2 describe-instances --region "$r" --filters "Name=tag:Name,Values=$m" \
        --query 'Reservations[0].Instances[0].State.Name' --output text 2>/dev/null)
      if [ "$st" != running ]; then :
      elif ARGONIA_PEEK=1 "$run" --machine "$m" ps '. C:\argonia\infra\stream-activity.ps1; (Get-StreamActivity).streaming' 2>/dev/null | grep -q True; then
        echo "$m: someone is streaming; left running"
      else
        "$run" --machine "$m" stop
      fi
    fi ;;
  *) sed -n '2,18p' "$0"; exit 2 ;;
esac
