#!/usr/bin/env bash
# Start the play machine, retrying while its region has no spot capacity (run.sh up exits 3 for that), every
# RETRY_S seconds (default 300) for up to TRIES tries (default 48: four hours), then run the given command.
# Run under tooling/job_guard.sh; resumable: a relaunch simply starts retrying again.
#   infra/gpu-box/up_retry.sh [-- command...]
set -uo pipefail
# Wait N seconds without CPU: read on a private FIFO opened read-write blocks until the timeout (a read on /dev/zero spun a core).
idle_wait() { local f; f=$(mktemp -u); mkfifo "$f" && { read -r -t "$1" <> "$f" 2>/dev/null; rm -f "$f"; }; return 0; }
here=$(cd "$(dirname "$0")" && pwd)
tries=${TRIES:-48}; wait_s=${RETRY_S:-300}
[ "${1:-}" = -- ] && shift
for i in $(seq 1 "$tries"); do
  "$here/run.sh" up; rc=$?
  [ $rc = 0 ] && break
  [ $rc = 3 ] || exit $rc
  echo "no capacity (try $i of $tries); next try in ${wait_s}s"
  idle_wait "$wait_s"   # the wait run.sh uses (a read that times out)
done
[ $rc = 0 ] || { echo "no spot capacity after $tries tries"; exit 3; }
[ $# -gt 0 ] && exec "$@"
