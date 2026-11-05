#!/usr/bin/env bash
# The planner's in-game round as ONE job (1.15-r4-fast-loop; owner 2026-11-02: "loops involving checks in the game
# need to be massively optimised"): machine up, deploy, the batch, the stills listed for the reader, machine stop.
# Nobody polls: the job's exit notifies the planner, whose next act is handing stills.txt to a `reader`.
#   tooling/job_guard.sh run --gpu=argonia-play round-<id> -- infra/gpu-box/round.sh <batch.yaml> [machine]
# Resumable and idempotent (the build VM is a spot instance; the job restore relaunches it): each step writes its
# verdict to ~/.argonia/round/<batch id>.<build>.state, and a step whose verdict is OK is not run again for the same
# build (git HEAD + ESM hashes). The deploy is incremental by itself (cached plugin, staged rows, per-mod push, SKSE
# stamp, LOD and shader-cache archives). The machine is stopped on every exit, pass or fail.
# The batch shrinks by the pass ledger (tools/pass_ledger.py): the plan line "batch: N of M journeys, K of S steps to
# run" comes before the machine starts, and a batch with nothing left starts no machine.
# Each step prints `ROUND <step> OK|FAIL in N s`; the last line is `ROUND DONE <passed>/<items> in N s; stills: <file>`.
set -u
batch=${1:?batch.yaml}; m=${2:-${ARGONIA_PLAY:-argonia-play}}
cd "$(dirname "$(readlink -f "$0")")/../.."
export ARGONIA_PLAY=$m
PY=$(command -v "$HOME/.argonia/venv/bin/python" || command -v python3)
id=$("$PY" -c 'import sys, yaml; print(yaml.safe_load(open(sys.argv[1])).get("id") or sys.argv[1].rsplit("/", 1)[-1].rsplit(".", 1)[0])' "$batch")
# the build key is what the deploy and the batch depend on (the two ESMs, the deploy inputs' tracked blobs: the stack,
# data, UI, SKSE, journeys and scenes), never HEAD: a planner commit during a round made a resumed round redeploy and
# restart its batch (decision 0037, 2026-11-03)
build=$( { sha256sum out/Argonia.esm out/ArgoniaWorld.esm 2>/dev/null; git ls-files -s infra/gpu-box data ui skse tools/ArgoniaGen tests/journeys tests/scenes; } | sha256sum | cut -c1-12)
state="$HOME/.argonia/round/$id.$build.state"; mkdir -p "$(dirname "$state")"; touch "$state"
t0=$SECONDS
done_ok() { grep -qx "$1 OK" "$state"; }
step() {  # step <name> <cmd...>: skipped when OK for this build; verdict line and state either way
  local name=$1 s=$SECONDS; shift
  if done_ok "$name"; then echo "ROUND $name OK (done earlier for build $build)"; return 0; fi
  echo "== $name $(date -u +%H:%M:%S)"
  if "$@"; then echo "$name OK" >>"$state"; echo "ROUND $name OK in $(( SECONDS - s )) s"; return 0; fi
  echo "ROUND $name FAIL in $(( SECONDS - s )) s"; return 1
}
# ROUND_KEEP_UP=1: a chained caller (r5_sky_ab.sh) runs another round on the same boot, so a round that passed leaves
# the machine up (a stop and start between two halves cost ~4 min, 2026-11-03); a failed round still stops it.
stop_machine() { if [ "${ROUND_KEEP_UP:-}" = 1 ] && [ "${round_rc:-1}" = 0 ]; then echo "ROUND kept up (ROUND_KEEP_UP)"; return; fi
  infra/gpu-box/run.sh stop >/dev/null 2>&1 && echo "ROUND stop OK" || echo "ROUND stop FAIL (stop $m by hand)"; }
# the pass ledger's shrink (owner, 2026-11-03: a passed check is not run again until its own inputs change), before
# the machine is started; nothing left to run starts no machine. ROUND_ALL=1 runs every step (run_batch --all).
all=(); [ "${ROUND_ALL:-}" = 1 ] && all=(--all)
if ! done_ok batch; then
  "$PY" tools/run_batch.py --plan "${all[@]}" "$batch"; prc=$?
  if [ $prc = 3 ]; then echo "ROUND DONE nothing to run: every step passed on the same inputs (ROUND_ALL=1 forces)"; exit 0; fi
  [ $prc = 0 ] || { echo "ROUND plan FAIL (rc $prc)"; exit 6; }
fi
trap stop_machine EXIT
round_rc=1

# the machine's "up" is never a state to reuse: a reclaim between two resumes stops it (17:20: the batch ran against a dead
# machine because up and deploy read "done earlier"); up runs every time (seconds when it already answers)
~/.argonia/scripts/up_until.sh "$m" 120 || exit 3
# a deploy that dies with the machine is run again once (what landed stays landed)
# a deploy that dies with the machine is run again once (what landed stays landed); a deploy that failed with the
# machine still answering (a launch red, 09:41) is not: the second try cost 4 min and failed the same way
mkdir -p out; step deploy bash -c '{ make --no-print-directory deploy || { infra/gpu-box/run.sh ps "echo ok" 2>/dev/null | grep -q ok && { echo "deploy: failed with the machine up; not retried"; exit 1; }; echo "deploy: again (resumes)"; make --no-print-directory deploy; }; } | tee out/.deploy-last.log; exit ${PIPESTATUS[0]}' || exit 4
# a held deploy (the machine already runs this build) launched nothing: the bridge's ping, else a launch to the menu
grep -q '^DEPLOY held' out/.deploy-last.log 2>/dev/null && { $PY tools/bridge.py ping >/dev/null 2>&1 && echo "ROUND game answers (held build)" || { $PY tools/bridge.py launch || exit 4; }; }
# the batch: a resumed round goes on from the first item its last run did not reach (run_batch --from), never the top
last=$(sed -n 's/^batch-dir //p' "$state" | tail -1)
if ! done_ok batch; then
  from=()
  if [ -n "$last" ] && [ -f "$last/summary.json" ]; then
    item=$("$PY" -c 'import json, sys, yaml
n = len(json.load(open(sys.argv[1])).get("items", [])); it = yaml.safe_load(open(sys.argv[2]))["items"]
x = it[n] if n < len(it) else None
print("" if x is None else (x if isinstance(x, str) else (x.get("journey") or x.get("scene"))).split(":")[0])' "$last/summary.json" "$batch")
    [ -n "$item" ] && from=(--from "$item")
  fi
  s=$SECONDS; echo "== batch $(date -u +%H:%M:%S) ${from[*]:-}"
  before=$(ls -td "out/batch/$id"/*/ 2>/dev/null | head -1)
  # each journey's done.json goes to the planner's reader queue the moment it finishes (0036 amendment: judged in the run)
  hook=(); [ -x "$HOME/.argonia/scripts/journey_done.sh" ] && hook=(--on-done "$HOME/.argonia/scripts/journey_done.sh")
  "$PY" tools/run_batch.py "${hook[@]}" "${from[@]}" "${all[@]}" "$batch"; rc=$?
  last=$(ls -td "out/batch/$id"/*/ 2>/dev/null | head -1)
  [ "$last" != "$before" ] && echo "batch-dir $last" >>"$state"
  if [ $rc -le 1 ]; then echo "batch OK" >>"$state"; fi
  echo "ROUND batch $([ $rc -le 1 ] && echo OK || echo FAIL) in $(( SECONDS - s )) s (rc $rc: 0 all passed, 1 some failed, 2 no game)"
  [ $rc -le 1 ] || exit 4   # no game / machine gone: a partial batch is never a finished round; the planner relaunches
fi
[ -n "$last" ] || { echo "ROUND DONE no batch run"; exit 5; }
# the stills for the reader: every still of this round's batch runs (a resumed round has several), one per line
dirs=$(sed -n 's/^batch-dir //p' "$state")
find $dirs -name '*.png' | sort >"${last}stills.txt"
passed=$("$PY" -c 'import json, sys
i = [x for d in sys.argv[1:] for x in json.load(open(d + "summary.json")).get("items", [])]
n = sum(json.load(open(d + "summary.json")).get("planned", 0) for d in sys.argv[1:])
print(str(sum(x["passed"] for x in i)) + "/" + str(max(n, len(i))))' $dirs 2>/dev/null || echo "?/?")
round_rc=0
echo "ROUND DONE $passed in $(( SECONDS - t0 )) s; stills: $(wc -l <"${last}stills.txt") in ${last}stills.txt"
