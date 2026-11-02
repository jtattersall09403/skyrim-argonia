#!/usr/bin/env bash
# One standby, deployed whenever capacity allows, resumable across spot interrupts (owner, 2026-11-02: "interrupts
# are ok if nothing is lost and work can just pick up exactly where it left off"):
#   pool_deploy_resumable.sh <machine> [tries]
# Loop: bring the machine up (retrying while the region has no spot capacity), refuse to touch it while someone
# streams on it, run `make deploy` (every step is incremental: cached plugin, staged mods, per-mod push, SKSE skip,
# LOD from the archive), and stop the machine on success. A deploy that dies with the machine is simply run again:
# what landed stays landed. Idempotent from the first line, so the build VM's job restore may relaunch it.
#   tooling/job_guard.sh run --gpu=<machine> pool-<machine> -- infra/gpu-box/pool_deploy_resumable.sh <machine>
set -u
m=${1:?machine}; tries=${2:-12}
cd "$(dirname "$(readlink -f "$0")")/../.."
export ARGONIA_PLAY=$m
run=infra/gpu-box/run.sh
for i in $(seq 1 "$tries"); do
  echo "== attempt $i $(date -u +%H:%M)"
  ~/.argonia/scripts/up_until.sh "$m" 120 || { echo "no capacity in 2 h; next attempt"; continue; }
  if ARGONIA_PEEK=1 $run ps '. C:\argonia\infra\stream-activity.ps1; (Get-StreamActivity).streaming' 2>/dev/null | grep -q True; then
    echo "someone is streaming on $m: not deploying now"; sleep 600; continue
  fi
  if make deploy; then
    echo "DEPLOY OK on $m $(date -u +%H:%M)"; python3 infra/gpu-box/pool.py status 2>/dev/null | grep "$m" || true
    $run stop; exit 0
  fi
  echo "deploy did not finish (interrupt or error); the next attempt resumes"
  sleep 120
done
echo "gave up after $tries attempts"; exit 3
