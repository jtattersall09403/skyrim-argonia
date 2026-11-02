#!/usr/bin/env bash
# Ireland gets the round-3 world now (terrain LOD from the archive); the object-LOD redeploy follows via ireland-finish.
set -u
cd /home/ubuntu/skyrim-argonia
if infra/gpu-box/pool_deploy_resumable.sh argonia-play-ie 12; then
  printf 'Ireland has the round-3 world and the region saves (terrain LOD; the object LOD follows with a later redeploy).\n' > ~/.argonia/ireland-now.md
  python3 tooling/owner_inbox.py --comment "$1" --body-file ~/.argonia/ireland-now.md || true
fi
