#!/usr/bin/env bash
# Round 5's sky A/B on Paris (owner 2026-11-03 08:55, #37): one deploy of main, the sky-ab journey under the
# shaders-on launch and again under the shaders-off launch, so a reader can tell the shaders' veil from the records'.
# Each half is round.sh (resumable by build; the machine is stopped on every exit); the second half's deploy is a no-op.
# Run under tooling/job_guard.sh run --gpu=argonia-play r5-sky-ab -- infra/gpu-box/jobs/r5_sky_ab.sh
set -u
cd /home/ubuntu/skyrim-argonia
B=tests/journeys/batches
ARGONIA_SHADERS=on  infra/gpu-box/round.sh $B/1.15-round-5-sky-on.yaml  || echo "SKY-AB on: round failed (see above)"
ARGONIA_SHADERS=off infra/gpu-box/round.sh $B/1.15-round-5-sky-off.yaml || echo "SKY-AB off: round failed (see above)"
ls -t ~/.argonia/round/1.15-round-5-sky-*.state 2>/dev/null | head -2
echo "SKY-AB DONE $(date -u +%H:%M)"
