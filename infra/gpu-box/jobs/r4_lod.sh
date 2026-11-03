#!/usr/bin/env bash
# Round 4 of 1.15, the owner's last step: the LOD rebuilt on Paris for the round-4 world (terrain by xLODGen, TexGen,
# the object LOD by DynDOLOD, collected and archived to S3 so every deploy of this ESM lays it). Resumable: lod.sh keeps
# a marker per step per ESM sha, so a rerun after an interrupt skips what is done. Run under job_guard --gpu=argonia-play.
set -u
cd /home/ubuntu/skyrim-argonia
export ARGONIA_PLAY=argonia-play
run=infra/gpu-box/run.sh
~/.argonia/scripts/up_until.sh argonia-play 120 || exit 3
$run put infra/gpu-box/stack.ps1 infra/gpu-box/bridge.ps1 infra/gpu-box/lod.ps1 C:/argonia/infra/ || { $run stop; exit 3; }
$run ps 'Get-Process SkyrimSE,skse64_loader,TexGen*,LODGen*,Texconv* -EA SilentlyContinue | Stop-Process -Force; "clean"' || true
if timeout 9000 infra/gpu-box/lod.sh run && infra/gpu-box/lod.sh archive; then
  mkdir -p ~/.argonia/lod-steps/argonia-play; date -u +%FT%TZ > ~/.argonia/lod-steps/argonia-play/objlod-archived-r4
  echo "LOD OK $(date -u +%H:%M) $(sha256sum out/ArgoniaWorld.esm | cut -c1-12)"
else echo "LOD FAILED $(date -u +%H:%M)"; $run stop; exit 3; fi
$run stop
