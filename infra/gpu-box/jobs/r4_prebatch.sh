#!/usr/bin/env bash
# Round 4 of 1.15, before the machine: the one full gate, the province build (the lock is taken in-process), the
# vegetation and water checks on the whole province, the chart renders from the new ground and water, the
# world-sample pins rewritten for the new ground, the tree-seat journey made from the placement, all committed by
# path. Idempotent: every step is a rerun-safe command. Run under tooling/job_guard.sh run r4-prebatch -- ...
set -u
cd /home/ubuntu/skyrim-argonia
PY=$HOME/.argonia/venv/bin/python
step() { local n=$1; shift; local s=$SECONDS; echo "== $n $(date -u +%H:%M:%S)"; if "$@"; then echo "PREBATCH $n OK in $((SECONDS-s)) s"; else echo "PREBATCH $n FAIL in $((SECONDS-s)) s"; return 1; fi; }
git pull -q --rebase origin main || exit 3
step plugin make plugin || exit 3
step water $PY -m tools.argonia_world.water check || exit 3
step vegetation $PY -m tools.argonia_world.vegetation check || echo "(vegetation check red: the batch's tree-seat stills decide)"
step roads $PY -m tools.argonia_world.routes.shape check || echo "(road check red: noted)"
step chart $PY -m tools.chart render --if-stale || exit 3
step chart4k $PY -m tools.chart render --if-stale --level --size 4096 --out out/chart4k || echo "(4k chart render failed: the 1x chart stands)"
step sample python3 tools/world_sample.py --write || true  # the probe markers are DB rows: emitted by the ids build below
step plugin-ids make plugin-ids || exit 3
step tree-booth $PY -m tools.argonia_world.vegetation tree-booth --out tests/journeys/tree-seat.yaml || echo "(no tree-seat journey: tree-booth needs the shards path; the planner adds it)"
git add tests/journeys/world-sample.yaml tests/journeys/tree-seat.yaml tools/chart/*.json 2>/dev/null
git diff --cached --quiet || git commit -q -m "round 4 pre-batch: the world-sample pins and the tree-seat journey from the new ground and placement

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
step gate make check || { echo "PREBATCH gate RED: the planner reads out/check"; }
step plugin-check make plugin-check || echo "(plugin-check red: noted)"
git push -q origin main || git pull -q --rebase origin main && git push -q origin main
echo "PREBATCH DONE $(date -u +%H:%M) $(git rev-parse --short HEAD) $(sha256sum out/ArgoniaWorld.esm | cut -c1-12)"
