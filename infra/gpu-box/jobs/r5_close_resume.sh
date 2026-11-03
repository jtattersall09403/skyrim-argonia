#!/usr/bin/env bash
# Round 5's close, resumed after close-8 (2026-11-03 20:39): the build 7f4d0004 is deployed on Paris and xLODGen's
# terrain output is complete there (14545 files, the count of the proven runs; the LODGen log ended code 0), but the
# driver's read of the tool's window failed and it called the step failed. This links that output into Data, marks
# terrain done for this ESM, and runs the rest of the close once: TexGen, DynDOLOD, collect and archive, the stops not
# yet passed, the ten saves. Every end, good or bad, wakes the agent (infra/build-vm/agent-wake.sh): nothing sits
# silently again. Under job_guard --gpu=argonia-play.
set -u; cd /home/ubuntu/skyrim-argonia; export ARGONIA_PLAY=argonia-play
job=${JOB_NAME:-r5-close9}
fail() { echo "CLOSE: $1 $(date -u +%H:%M)"; infra/build-vm/agent-wake.sh "round 5 close chain FAILED: $1. Read ~/.argonia/jobs/$job.log, diagnose, resume; the owner waits on #37 for the ten saves."; exit 3; }
~/.argonia/scripts/up_until.sh argonia-play 120 || fail "Paris never came up"
sha12=$(sha256sum out/ArgoniaWorld.esm | cut -c1-12); [ "$sha12" = d40c2553505c ] || fail "out/ArgoniaWorld.esm is $sha12, not the deployed d40c2553505c"
marks=~/.argonia/lod-steps/argonia-play/$sha12
if [ ! -f "$marks/terrain" ]; then
  n=$(infra/gpu-box/run.sh ps '(Get-ChildItem C:\argonia\lod\out\terrain -Recurse -File -Include *.btr,*.dds).Count' | tr -dc 0-9)
  [ "${n:-0}" -ge 14545 ] || fail "terrain output has ${n:-0} files, not the 14545 of a finished run"
  infra/gpu-box/run.sh put infra/gpu-box/jobs/link_terrain.ps1 C:/argonia/infra/ || fail "put link_terrain.ps1"
  infra/gpu-box/run.sh ps 'powershell -ExecutionPolicy Bypass -File C:\argonia\infra\link_terrain.ps1' | tee /dev/stderr | grep -q "^linked" || fail "linking terrain into Data"
  date -u +%FT%TZ > "$marks/terrain"; echo "terrain: accepted (output complete, linked into Data) $(date -u +%H:%M)"
fi
ROUND_KEEP_UP=1 infra/gpu-box/jobs/r5_lod.sh || fail "LOD"
ROUND_KEEP_UP=1 ARGONIA_SHADERS=on infra/gpu-box/round.sh tests/journeys/batches/1.15-round-5-rest.yaml || echo "CLOSE: the rest batch returned $? (its rows carry their own verdicts)"
infra/gpu-box/jobs/r5_saves.sh || fail "the saves"
echo "CLOSE DONE $(date -u +%H:%M)"
infra/build-vm/agent-wake.sh "round 5 close chain DONE: the ten saves are made (job $job). Post the hand-over on #37 with what the stills proved, and move the records."
