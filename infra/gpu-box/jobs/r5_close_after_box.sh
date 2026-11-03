#!/usr/bin/env bash
# Round 5's close on Paris once the box has archived the object LOD (r5_lod_box.sh): Paris up, deploy (lod ensure lays
# the archived LOD for this ESM), the stops not yet passed, the ten saves made once. Every end wakes the agent.
# Under job_guard --gpu=argonia-play.
set -u; cd /home/ubuntu/skyrim-argonia; export ARGONIA_PLAY=argonia-play
job=${JOB_NAME:-r5-close10}
fail() { echo "CLOSE: $1 $(date -u +%H:%M)"; infra/build-vm/agent-wake.sh "round 5 close chain FAILED: $1. Read ~/.argonia/jobs/$job.log, diagnose, resume; the owner waits on #37 for the ten saves."; exit 3; }
while [ ! -f ~/.argonia/jobs/r5-lod-box.rc ]; do tooling/job_guard.sh wait r5-lod-box >/dev/null 2>&1 || true; sleep 20; done
rc=$(cat ~/.argonia/jobs/r5-lod-box.rc); echo "box rc=$rc $(date -u +%H:%M)"; [ "$rc" = 0 ] || fail "the LOD box failed (rc $rc); nothing to lay"
~/.argonia/scripts/up_until.sh argonia-play 240 || fail "Paris never came up"
make --no-print-directory deploy || fail "deploy (lays the archived LOD)"
echo "CLOSE deploy OK $(date -u +%H:%M)"
ROUND_KEEP_UP=1 ARGONIA_SHADERS=on infra/gpu-box/round.sh tests/journeys/batches/1.15-round-5-rest.yaml || echo "CLOSE: the rest batch returned $? (its rows carry their own verdicts)"
infra/gpu-box/jobs/r5_saves.sh || fail "the saves"
echo "CLOSE DONE $(date -u +%H:%M)"
infra/build-vm/agent-wake.sh "round 5 close chain DONE: the ten saves are made (job $job). Post the hand-over on #37 with what the stills proved, and move the records."
