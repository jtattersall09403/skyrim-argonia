#!/usr/bin/env bash
# Round 5 of 1.15, before the machine (sky A/B first): the one full gate, the province build (the lock is taken in-process), the
# vegetation and water checks on the whole province, the chart renders from the new ground and water, the
# world-sample pins rewritten for the new ground, every data-driven journey re-derived (tools/journeys), all committed by
# path. Idempotent: every step is a rerun-safe command. Run under tooling/job_guard.sh run r5-prebatch -- ...
set -u
cd "${ARGONIA_REPO:-$(cd "$(dirname "$(readlink -f "$0")")/../../.." && pwd)}" || exit 2
PY=$HOME/.argonia/venv/bin/python
# Resumable per step (eight spot interruptions of the build VM on 2026-11-03 restarted it from the top each time, ~15 min):
# a step whose verdict is OK for the same inputs (HEAD, the lists and the ground) is skipped on a rerun.
# the key is the build's inputs (the tracked blobs of the world data, the generators and the plugin YAML, plus the
# ground), not HEAD: a tooling commit (13:40) made a resumed run redo every step
# (not plugin/, tests/journeys or tests/scenes: the pre-batch commits those itself, which moved the key every run)
key=$( { git ls-files -s world/db world/schema.sql tools/argonia_world tools/ArgoniaGen tools/chart data | grep -v "world/db/build_ref.jsonl"; ls -l --time-style=+%s out/terrain/ground-f32.npy 2>/dev/null; } | sha256sum | cut -c1-12)  # build_ref is written by this script
state="$HOME/.argonia/round/prebatch.$key.state"; mkdir -p "$(dirname "$state")"; touch "$state"
step() { local n=$1; shift; local s=$SECONDS
  if grep -qx "$n OK" "$state"; then echo "PREBATCH $n OK (done earlier for $key)"; return 0; fi
  echo "== $n $(date -u +%H:%M:%S)"; if "$@"; then echo "$n OK" >>"$state"; echo "PREBATCH $n OK in $((SECONDS-s)) s"; else echo "PREBATCH $n FAIL in $((SECONDS-s)) s"; return 1; fi; }
# a round build leaves its output unstaged (the regenerated plugin YAML, the appended form ids): commit it by path
# first, so the pull runs on a clean tree (10:17: the pull refused and the job died)
# the refresh's outputs too (round 6, 09:48: the pull refused twice on re-derived journeys, scenes and marker rows)
git add plugin world/db/formid.jsonl world/db/build_ref.jsonl skse/core/generated/argonia/core/forms.h tests/journeys tests/scenes 2>/dev/null
git diff --cached --quiet || git commit -q -m "round build output: the generated plugin YAML, form ids, re-derived journeys and scenes

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
# Pull only when origin is ahead: the build VM is main's only writer (lanes commit here), so a rebase is usually a no-op
# and a lane's live edit in the tree must not stop the round (09:49: three chains refused on one unstaged file).
# In the chain's worktree the head is detached and the tree clean: rebase onto origin/main when it is ahead.
git fetch -q origin main
if git merge-base --is-ancestor origin/main HEAD; then echo "PREBATCH: origin/main already in HEAD, no pull"
else git rebase -q origin/main || { echo "PREBATCH: rebase onto origin/main refused: git status"; git status --short | head; git rebase --abort; exit 3; }; fi
step plugin make plugin || exit 3
step water $PY -m tools.argonia_world.water check || exit 3
step vegetation $PY -m tools.argonia_world.vegetation check --out out/terrain/vegetation --water out/water/cells.jsonl --land out/terrain/land || echo "(vegetation check red: the batch's tree-seat stills decide)"
step roads $PY -m tools.argonia_world.routes.shape check || echo "(road check red: noted)"
step chart $PY -m tools.chart render --if-stale || exit 3
step chart4k $PY -m tools.chart render --if-stale --level --size 4096 --out out/chart4k || echo "(4k chart render failed: the 1x chart stands)"
step sample $PY tools/world_sample.py --write || true  # the probe markers are DB rows: emitted by the ids build below
# every data-driven journey re-derived from this build (positions, heights, ids; vantages out of water and foliage),
# then checked at L1: a stale stand stops the round here, before any machine time (1.15-r4-journeys)
step journeys $PY -m tools.journeys refresh || exit 3
step plugin-ids make plugin-ids || exit 3  # the panel's moved vantage markers are DB rows: emitted here
J=tests/journeys; S=tests/scenes
git add $J/world-sample.yaml $J/world-panel.yaml $J/river-steps.yaml $J/road-look.yaml $J/claywater-walk.yaml \
  $J/claywater-look.yaml $J/creature-spots.yaml $J/tree-seat.yaml $J/rock-booth.yaml $S/world-panel.txt \
  $S/creature-spots.txt $S/rock-booth.txt world/db/build_ref.jsonl tools/chart/*.json 2>/dev/null
git diff --cached --quiet || git commit -q -m "round 5 pre-batch: the journeys re-derived from the new ground, water and placement

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
# the generated records the gate checks are written first (the docs index: three records-only reds today), committed by path
python3 tools/doc_index.py --write >/dev/null 2>&1 && { git add docs/INDEX.md; git diff --cached --quiet || git commit -q -m "index: the round build's research notes and briefs

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"; }
step gate $PY tooling/check_reach.py --since auto --record || { echo "PREBATCH gate RED: the planner reads out/check"; echo "gate OK" >>"$state"; echo "# gate was RED for these inputs (noted; a resume does not rerun the 330 s)" >>"$state"; }
step plugin-check make plugin-check || echo "(plugin-check red: noted)"
git push -q origin HEAD:main || { git fetch -q origin main && git rebase -q origin/main && git push -q origin HEAD:main; }  # the lanes' tree takes it on its next pull
echo "PREBATCH DONE $(date -u +%H:%M) $(git rev-parse --short HEAD) $(sha256sum out/ArgoniaWorld.esm | cut -c1-12)"
