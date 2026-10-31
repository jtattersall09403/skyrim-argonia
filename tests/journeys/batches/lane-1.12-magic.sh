#!/usr/bin/env bash
# lane-1.12-magic (L4, one batch): deploy, then tests/journeys/magic-pane.yaml (Magic Expanded restated at data load,
# Wind UI's magic pane over a spread of its spells), the pass's log lines and a still of the open pane.
#   ARGONIA_LANE=1.12-magic tooling/job_guard.sh run --gpu=argonia-play-ie l112magic -- tests/journeys/batches/lane-1.12-magic.sh
set -x
cd "$(dirname "$0")/../../.."
O=out/l112magic; mkdir -p $O
R=infra/gpu-box/run.sh
$R up || exit $?
PY=~/.argonia/venv/bin/python
B="$PY tools/bridge.py"
SK='$env:USERPROFILE\Documents\My Games\Skyrim Special Edition\SKSE'
[ -n "${NO_DEPLOY:-}" ] || make deploy || exit 1
$PY tools/run_journey.py tests/journeys/magic-pane.yaml; echo "journey rc=$?"
$R ps "Select-String -Path \"$SK\ArgoniaCore.log\" -Pattern 'magic:' | Out-String -Width 300" > $O/core-magic.txt
$B input key P 150 engine; $B screenshot $O/magic-open.png
$B input key P 150 engine
[ -n "${KEEP_UP:-}" ] || $R stop
