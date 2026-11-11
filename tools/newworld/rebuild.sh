#!/usr/bin/env bash
# The new world's rebuild, one command (tools/newworld/rebuild.py holds the stages, their order, keys and checks; the
# recipe is the skill world-build):
#   tools/newworld/rebuild.sh plan         the order, and which stages are stale (and why) or current
#   tools/newworld/rebuild.sh small [plan|run|play] [--from <out/newworld>]   the same stages on the small test world
#                                          (one block of the real build, out/newworld-small/): minutes; run it before
#                                          a full run, whose preflight refuses stage code the block has not proved
#   tools/newworld/rebuild.sh preflight    everything checkable before the first long stage
#   tooling/job_guard.sh run nw-rebuild -- tools/newworld/rebuild.sh run [--to STAGE] [--force STAGE]
#   tooling/job_guard.sh wait nw-rebuild
set -euo pipefail
repo=$(cd "$(dirname "$0")/../.." && pwd); cd "$repo"
py=$(ls "$HOME/.argonia/venv/bin/python" 2>/dev/null || command -v python3)
if [ "${1:-}" = small ]; then shift; exec "$py" -m tools.newworld.small "$@"; fi
exec "$py" -m tools.newworld.rebuild "$@"
