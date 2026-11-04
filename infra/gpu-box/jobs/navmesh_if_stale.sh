#!/usr/bin/env bash
# Pre-batch step after `make plugin`: rebuild the province navmesh when its terrain stamp is not the current ground's
# (the plugin stage only warns, pipeline.province_navmesh), then write the plugin again so the ESM carries the new
# navmesh (the esm-write stage is 30 s; ground and terrain skip by key). In a worktree (shared out/) it refuses, as the
# land does: the planner runs `make navmesh` in the main tree. Round 6, 2026-11-04 20:4x: the batch would have run
# navmesh-paths on the old navmesh.
set -u; cd "$(git rev-parse --show-toplevel)"
PY=${PY:-$HOME/.argonia/venv/bin/python}
s=out/navmesh/province/terrain.stamp
t=$("$PY" -c "from tools.ArgoniaGen.pipeline import _terrain_stamp; print(_terrain_stamp())") || exit 1
[ -f "$s" ] && [ "$(cat "$s")" = "$t" ] && { echo "navmesh current for the ground"; exit 0; }
if [ "$(git rev-parse --git-dir)" != "$(git rev-parse --git-common-dir)" ]; then echo "navmesh stale: run make navmesh in the main tree"; exit 1; fi
make navmesh && make plugin
