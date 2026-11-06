#!/usr/bin/env bash
# Start the play machine, retrying while its region has no spot capacity (run.sh up exits 3 for that), every
# RETRY_S seconds (default 300) for up to TRIES tries (default 48: four hours), then run the given command.
# Run under tooling/job_guard.sh; resumable: a relaunch simply starts retrying again.
#   infra/gpu-box/up_retry.sh [-- command...]
set -uo pipefail
here=$(cd "$(dirname "$0")" && pwd)
tries=${TRIES:-48}; wait_s=${RETRY_S:-300}
[ "${1:-}" = -- ] && shift
for i in $(seq 1 "$tries"); do
  "$here/run.sh" up; rc=$?
  [ $rc = 0 ] && break
  [ $rc = 3 ] || exit $rc
  echo "no capacity (try $i of $tries); next try in ${wait_s}s"
  read -r -t "$wait_s" < /dev/zero || true   # the wait run.sh uses (a read that times out)
done
[ $rc = 0 ] || { echo "no spot capacity after $tries tries"; exit 3; }
[ $# -gt 0 ] && exec "$@"
