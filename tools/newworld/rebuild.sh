#!/usr/bin/env bash
# The new world's rebuild, one command (tools/newworld/rebuild.py holds the stages, their order, keys and checks; the
# recipe is the skill world-build):
#   tools/newworld/rebuild.sh plan         the order, and which stages are stale (and why) or current
#   tools/newworld/rebuild.sh preflight    everything checkable before the first long stage
#   tooling/job_guard.sh run nw-rebuild -- tools/newworld/rebuild.sh run [--to STAGE] [--force STAGE]
#   tooling/job_guard.sh wait nw-rebuild
set -euo pipefail
repo=$(cd "$(dirname "$0")/../.." && pwd); cd "$repo"
py=$(ls "$HOME/.argonia/venv/bin/python" 2>/dev/null || command -v python3)
exec "$py" -m tools.newworld.rebuild "$@"
