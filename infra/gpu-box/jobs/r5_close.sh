#!/usr/bin/env bash
# Round 5's close, one job on Paris after the batch's stills passed: the LOD rebuilt for the final ESM (terrain,
# TexGen, DynDOLOD; archived), the final deploy that lays it, the ten region saves remade on it, the machine stopped.
# Each step is its own resumable script. Run under tooling/job_guard.sh run --gpu=argonia-play r5-close -- infra/gpu-box/jobs/r5_close.sh
set -u; cd /home/ubuntu/skyrim-argonia; export ARGONIA_PLAY=argonia-play
infra/gpu-box/jobs/r5_lod.sh || { echo "CLOSE: LOD failed"; exit 3; }
if ARGONIA_PEEK=1 infra/gpu-box/run.sh ps '. C:\argonia\infra\stream-activity.ps1; (Get-StreamActivity).streaming' 2>/dev/null | grep -q True; then echo "CLOSE: the owner is streaming: not deploying"; exit 4; fi
~/.argonia/scripts/up_until.sh argonia-play 120 || exit 3
if make deploy; then echo "CLOSE DEPLOY OK $(date -u +%H:%M) $(sha256sum out/ArgoniaWorld.esm | cut -c1-12)"; else echo "CLOSE DEPLOY FAILED"; infra/gpu-box/run.sh stop; exit 3; fi
infra/gpu-box/jobs/r5_saves.sh || { echo "CLOSE: saves failed"; exit 3; }
echo "CLOSE DONE $(date -u +%H:%M)"
