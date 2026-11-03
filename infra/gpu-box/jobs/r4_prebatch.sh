#!/usr/bin/env bash
# Round 4 of 1.15, before the machine: the one full gate, the province build (the lock is taken in-process), the
# vegetation and water checks on the whole province, the chart renders from the new ground and water, the
# world-sample pins rewritten for the new ground, every data-driven journey re-derived (tools/journeys), all committed by
# path. Idempotent: every step is a rerun-safe command. Run under tooling/job_guard.sh run r4-prebatch -- ...
set -u
cd /home/ubuntu/skyrim-argonia
PY=$HOME/.argonia/venv/bin/python
step() { local n=$1; shift; local s=$SECONDS; echo "== $n $(date -u +%H:%M:%S)"; if "$@"; then echo "PREBATCH $n OK in $((SECONDS-s)) s"; else echo "PREBATCH $n FAIL in $((SECONDS-s)) s"; return 1; fi; }
git pull -q --rebase origin main || exit 3
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
git diff --cached --quiet || git commit -q -m "round 4 pre-batch: the journeys re-derived from the new ground, water and placement

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
step gate make check || { echo "PREBATCH gate RED: the planner reads out/check"; }
step plugin-check make plugin-check || echo "(plugin-check red: noted)"
git push -q origin main || git pull -q --rebase origin main && git push -q origin main
echo "PREBATCH DONE $(date -u +%H:%M) $(git rev-parse --short HEAD) $(sha256sum out/ArgoniaWorld.esm | cut -c1-12)"
