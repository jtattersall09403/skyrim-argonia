#!/usr/bin/env bash
# Relaunches the job_guard queue after an interrupt (1.15). Run once per boot by the systemd --user unit
# argonia-job-resume.service (lingering keeps the user manager up from boot, no login needed).
#   job_resume.sh             relaunch, in .seq order, every spooled job whose .state is queued or running, whose
#                             .rc is absent or a signal's (>= 128; `stop` sets .state stopped) and whose pid is not alive, through `job_guard.sh run` (same locks,
#                             queueing, cwd, ARGONIA_*/PATH env, argv, seq); writes $JOBS/RESUMED-<boot-id>
#   job_resume.sh --install   lay and enable the unit under ~/.config/systemd/user (the planner runs this once)
# JOBS_DIR is passed on to the relaunched jobs only when the caller set it: the default spool needs no variable, and a
# job that inherited the real spool's path made every test it ran (the gate) read and write the real spool.
# Once per boot: a second run in the same boot finds RESUMED-<boot-id> and does nothing. Jobs older than
# $RESUME_MAX_AGE s (default 43200) are left alone: a job dead half a day is the planner's call, not a resume.
set -euo pipefail
here=$(dirname "$(readlink -f "$0")")
JOBS="${JOBS_DIR:-$HOME/.argonia/jobs}"; mkdir -p "$JOBS"
if [ "${1:-}" = --install ]; then
  d="$HOME/.config/systemd/user"; mkdir -p "$d"
  cat > "$d/argonia-job-resume.service" <<EOF
[Unit]
Description=Relaunch the job_guard queue after a reboot or spot interrupt (Argonia 1.15)

[Service]
Type=oneshot
ExecStart=$here/job_resume.sh

[Install]
WantedBy=default.target
EOF
  systemctl --user daemon-reload && systemctl --user enable argonia-job-resume.service
  echo "laid $d/argonia-job-resume.service ($(loginctl show-user "$USER" -p Linger))"; exit 0
fi
boot=${RESUME_BOOT_ID:-$(cat /proc/sys/kernel/random/boot_id)}
mark="$JOBS/RESUMED-$boot"
[ -e "$mark" ] && { echo "already resumed this boot: $mark"; exit 0; }
t0=$(date +%s.%N); now=${t0%.*}; maxage=${RESUME_MAX_AGE:-43200}
list=()
for f in "$JOBS"/*.cmd; do [ -e "$f" ] || continue; n=$(basename "$f" .cmd)
  rc=$(cat "$JOBS/$n.rc" 2>/dev/null || echo ""); [ -z "$rc" ] || [ "$rc" -ge 128 ] 2>/dev/null || continue  # signal-killed: the reboot's
  st=$(cat "$JOBS/$n.state" 2>/dev/null || echo ""); [ "$st" = queued ] || [ "$st" = running ] || continue
  # still alive: not interrupted (by its unit when it has one: after a reboot a bare pid may be someone else's)
  if u=$(cat "$JOBS/$n.unit" 2>/dev/null) && [ -n "$u" ]; then systemctl --user is-active -q "$u" 2>/dev/null && continue
  else kill -0 "$(cat "$JOBS/$n.pid" 2>/dev/null || echo 0)" 2>/dev/null && continue; fi
  [ $((now - $(stat -c %Y "$JOBS/$n.state"))) -le "$maxage" ] || continue
  list+=("$(cat "$JOBS/$n.seq" 2>/dev/null || echo 0) $n")
done
{ echo "boot $boot at $(date -Is)"
  printf '%s\n' "${list[@]}" | sort -n | while read -r seq n; do [ -n "${n:-}" ] || continue
    mapfile -d '' argv < "$JOBS/$n.cmd"; mapfile -d '' envs < "$JOBS/$n.env" 2>/dev/null || envs=()
    gpu=(); [ -f "$JOBS/$n.gpu" ] && gpu=(--gpu="$(cat "$JOBS/$n.gpu")")
    cwd=$(cat "$JOBS/$n.cwd" 2>/dev/null || echo "$HOME"); [ -d "$cwd" ] || cwd=$HOME
    # the log is kept: job_guard appends "== RESUMED <time>" and the relaunch's output (1.15-r6-resume-costs)
    if out=$(cd "$cwd" && env -u ARGONIA_PLAY -u ARGONIA_LANE "${envs[@]}" JOB_SEQ="$seq" JOB_RESUMED=1 ${JOBS_DIR:+JOBS_DIR="$JOBS_DIR"} \
        bash "$here/job_guard.sh" run "${gpu[@]}" "$n" -- "${argv[@]}" 2>&1); then
      echo "relaunched $n (seq $seq${gpu:+, ${gpu[0]}}) +$(echo "$(date +%s.%N) - $t0" | bc)s: $out"
    else echo "FAILED $n (seq $seq): $out"; fi
  done; } > "$mark.tmp"
mv "$mark.tmp" "$mark"; cat "$mark"
