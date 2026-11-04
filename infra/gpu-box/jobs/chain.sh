#!/usr/bin/env bash
# The planner's default round chain (1.15-r6-fast-loop-2; owner 2026-11-04 08:06 #37, decision 0021's amendment):
# the fast loops and the in-game batch on the existing LOD first; the slow derived steps (LOD, saves) last and only for
# what moved; the round's retrospective appended to its record. One job:
#   tooling/job_guard.sh run --gpu=argonia-play <round> -- infra/gpu-box/jobs/chain.sh <batch.yaml> <round record .md> [log glob]
# Resumable (0037): each stage is its own keyed script (r5_prebatch's state, round.sh's state, lod.sh's key, deploy's
# keyed steps, region_saves' remake-what-is-missing), so a rerun after an interrupt goes on where it stopped.
# No AWS beyond the authorised game machine: the machine starts only after the pre-batch (no idle minutes during the
# build) and stops on every exit; the Paris on-demand box is never started here (LOD on it is a separate defined job).
# CHAIN_DRY=1 prints the worktree and sha, the stages and the LOD verdict without running them.
set -u
batch=${1:?batch.yaml}; record=${2:?round record .md}; logs=${3:-$(basename "$batch" .yaml)*}
export ARGONIA_PLAY=${ARGONIA_PLAY:-argonia-play}
# The chain runs on a committed tree of its own (1.15-r6-chain-worktree): a detached git worktree of the launch commit
# at ~/.argonia/round/tree, never the lanes' live tree (09:4x-10:5x: four chains refused or killed by lanes' edits).
# out/ (every keyed cache, the province lock, the LOD markers) and the ignored build inputs are symlinks to the main
# tree's, so nothing rebuilds for the move. The sha is the resume key (0037): ~/.argonia/round/chain.<batch>.sha,
# kept until the chain ends well; a rerun keeps the tree when its HEAD descends from that sha (the pre-batch's commits).
# The round record is appended in the main tree (the planner commits it); batch.yaml is read from the committed tree.
src=${ARGONIA_REPO:-$(cd "$(dirname "$(readlink -f "$0")")/../../.." && pwd)}
case $record in /*) ;; *) record="$src/$record";; esac
if [ -z "${CHAIN_IN_TREE:-}" ]; then
  tree=${CHAIN_TREE:-$HOME/.argonia/round/tree}; keyf="$HOME/.argonia/round/chain.$(basename "$batch" .yaml).sha"
  sha=${CHAIN_SHA:-$(cat "$keyf" 2>/dev/null || git -C "$src" rev-parse HEAD)}; sha=$(git -C "$src" rev-parse "$sha^{commit}") || exit 2
  echo "CHAIN tree $tree sha $sha"
  if [ -n "${CHAIN_DRY:-}" ]; then echo "  would run on: $tree at $sha (out/ -> $src/out)"
  else
    s0=$SECONDS; mkdir -p "$(dirname "$keyf")"; echo "$sha" >"$keyf"
    ex="$(git -C "$src" rev-parse --path-format=absolute --git-common-dir)/info/exclude"; mkdir -p "$(dirname "$ex")"
    grep -qx /out "$ex" 2>/dev/null || echo /out >>"$ex"   # the symlink: out/ in .gitignore matches directories only
    if [ ! -e "$tree/.git" ]; then git -C "$src" worktree prune; git -C "$src" worktree add -q --detach "$tree" "$sha" || exit 2
    elif ! git -C "$tree" merge-base --is-ancestor "$sha" HEAD 2>/dev/null; then
      git -C "$tree" checkout -q -f --detach "$sha" && git -C "$tree" clean -fdq || exit 2; fi
    ln -sfn "$src/out" "$tree/out" 2>/dev/null || { rm -rf "$tree/out"; ln -s "$src/out" "$tree/out"; }
    # ignored files the build hashes or reads (data/immersion/inventory.jsonl): linked, not copied
    git -C "$src" ls-files -oi --exclude-standard -- data world plugin | while read -r f; do
      [ -e "$tree/$f" ] || { mkdir -p "$(dirname "$tree/$f")"; ln -s "$src/$f" "$tree/$f"; }; done
    echo "CHAIN tree ready in $(( SECONDS - s0 )) s: $(git -C "$tree" rev-parse --short HEAD)"
    CHAIN_IN_TREE=1 ARGONIA_REPO="$tree" bash "$tree/infra/gpu-box/jobs/chain.sh" "$batch" "$record" "$logs"; rc=$?
    [ "$rc" = 0 ] && rm -f "$keyf"; exit "$rc"
  fi
fi
cd "${ARGONIA_REPO:-$src}" || exit 2
g=infra/gpu-box; t0=$SECONDS
run() { echo "CHAIN $1 $(date -u +%H:%M:%S)"; shift; [ -n "${CHAIN_DRY:-}" ] && { echo "  would run: $*"; return 0; }; "$@"; }
trap '[ -n "${CHAIN_DRY:-}" ] || $g/run.sh stop >/dev/null 2>&1; echo "CHAIN end in $(( SECONDS - t0 )) s"' EXIT
# 0. a game machine already up for this round is kept up through the pre-batch: its idle-stop stops it after 15 minutes
#    with no agent command, and a build-VM reboot plus the pre-batch is longer (2026-11-04: Paris stopped at 14 of 14 reboots)
if [ -z "${CHAIN_DRY:-}" ] && $g/run.sh ps "echo ok" >/dev/null 2>&1; then echo "CHAIN machine up: busy flag touched"; fi
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
