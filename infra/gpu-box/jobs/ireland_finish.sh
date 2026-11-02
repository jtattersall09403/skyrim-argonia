#!/usr/bin/env bash
# Ireland, after Paris has archived the object LOD (so the deploy lays the full LOD): the resumable deploy, then a
# comment on the check-in issue. Idempotent; relaunchable after any interrupt.
#   ireland_finish.sh <issue-number>
set -u
issue=${1:?issue}
cd /home/ubuntu/skyrim-argonia
while [ ! -f ~/.argonia/lod-steps/argonia-play/objlod-archived ]; do echo "waiting for Paris's object LOD $(date -u +%H:%M)"; sleep 300; done
if infra/gpu-box/pool_deploy_resumable.sh argonia-play-ie 12; then
  printf 'Ireland ready: the second standby carries the same round-3 world and LOD; the play page can start either.\n' > ~/.argonia/ireland-ready.md
  python3 tooling/owner_inbox.py --comment "$issue" --body-file ~/.argonia/ireland-ready.md || true
else
  printf 'Ireland: the deploy job gave up (no capacity or a failed deploy); the play page still starts Paris first.\n' > ~/.argonia/ireland-failed.md
  python3 tooling/owner_inbox.py --comment "$issue" --body-file ~/.argonia/ireland-failed.md || true
  exit 3
fi
