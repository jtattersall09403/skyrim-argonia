#!/usr/bin/env bash
# Round 5's close in the right order: the build (pre-batch), the deploy of the final world, THEN the LOD for that
# deployed world (else the LOD carries trees the lists dropped), then the remaining stops (the pass ledger skips the
# passed ones), then the ten saves. Resumable at every step (0037). Run under job_guard --gpu=argonia-play.
set -u; cd /home/ubuntu/skyrim-argonia; export ARGONIA_PLAY=argonia-play
infra/gpu-box/jobs/r5_prebatch.sh || exit 3
~/.argonia/scripts/up_until.sh argonia-play 120 || exit 3
make --no-print-directory deploy || { infra/gpu-box/run.sh ps "echo ok" 2>/dev/null | grep -q ok && { echo "CLOSE: deploy failed with the machine up"; exit 4; }; make --no-print-directory deploy || exit 4; }
echo "CLOSE deploy OK $(date -u +%H:%M)"
ROUND_KEEP_UP=1 infra/gpu-box/jobs/r5_lod.sh || { echo "CLOSE: LOD failed"; exit 3; }
ROUND_KEEP_UP=1 ARGONIA_SHADERS=on infra/gpu-box/round.sh tests/journeys/batches/1.15-round-5-rest.yaml
infra/gpu-box/jobs/r5_saves.sh
echo "CLOSE DONE $(date -u +%H:%M)"
