#!/usr/bin/env bash
# The planner's default round chain (1.15-r6-fast-loop-2; owner 2026-11-04 08:06 #37, decision 0021's amendment):
# the fast loops and the in-game batch on the existing LOD first; the slow derived steps (LOD, saves) last and only for
# what moved; the round's retrospective appended to its record. One job:
#   tooling/job_guard.sh run --gpu=argonia-play <round> -- infra/gpu-box/jobs/chain.sh <batch.yaml> <round record .md> [log glob]
# Resumable (0037): each stage is its own keyed script (r5_prebatch's state, round.sh's state, lod.sh's key, deploy's
# keyed steps, region_saves' remake-what-is-missing), so a rerun after an interrupt goes on where it stopped.
# No AWS beyond the authorised game machine: the machine starts only after the pre-batch (no idle minutes during the
# build) and stops on every exit; the Paris on-demand box is never started here (LOD on it is a separate defined job).
# CHAIN_DRY=1 prints the stages and the LOD verdict without running them.
set -u
batch=${1:?batch.yaml}; record=${2:?round record .md}; logs=${3:-$(basename "$batch" .yaml)*}
cd /home/ubuntu/skyrim-argonia; export ARGONIA_PLAY=${ARGONIA_PLAY:-argonia-play}
g=infra/gpu-box; t0=$SECONDS
run() { echo "CHAIN $1 $(date -u +%H:%M:%S)"; shift; [ -n "${CHAIN_DRY:-}" ] && { echo "  would run: $*"; return 0; }; "$@"; }
trap '[ -n "${CHAIN_DRY:-}" ] || $g/run.sh stop >/dev/null 2>&1; echo "CHAIN end in $(( SECONDS - t0 )) s"' EXIT
# 1. fast loops, no machine: plugin, L1 checks, journeys refresh, the gate (each skipped when its key is done)
run prebatch $g/jobs/r5_prebatch.sh || exit 3
# 2. the in-game batch on the machine's existing LOD (deploy's lod step keeps the old LOD when none is archived for
#    this ESM: a loud warning, never a rebuild); the machine stays up for stage 3
ROUND_KEEP_UP=1 run batch $g/round.sh "$batch" || exit 4
# 3. the LOD and the saves only after the whole loop: CHAIN_FINAL=1 is set by the planner when the ledger shows nothing
#    open (owner, 2026-11-04 08:29, #37: "after all the rounds/loop iterations have finished and everything has been
#    verified as completed"); an intermediate round ends here with the retrospective.
if [ -z "${CHAIN_FINAL:-}" ]; then
  echo "CHAIN intermediate round: no LOD, no saves (CHAIN_FINAL unset)"
  run retro python3 tooling/round_retro.py "$logs" --append "$record"
  exit 0
fi
# the LOD only when this ESM's key has no archive (lod.sh's keyed ensure: current or restored is minutes)
if [ -n "${CHAIN_DRY:-}" ]; then ens="(dry: lod.sh ensure not asked)"; else ens=$($g/lod.sh ensure 2>&1); fi; echo "$ens" | tail -3
if echo "$ens" | grep -q 'no LOD archive'; then
  run lod bash -c "$g/lod.sh run && $g/lod.sh archive" || exit 5
  run deploy-lod make --no-print-directory deploy || exit 5   # keyed steps skip; ensure now restores the new LOD
fi
# 4. the saves last, on the final deploy
run saves $g/jobs/r5_saves.sh || exit 6
# 5. where the time went, for the next round
run retro python3 tooling/round_retro.py "$logs" --append "$record"
