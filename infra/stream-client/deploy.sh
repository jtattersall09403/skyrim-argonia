#!/usr/bin/env bash
# Deploy our client page to the game machine (chunk 0.0 §c): build, copy static\ + the marker and collector
# sources + install.ps1 to C:\argonia\stream-client\, run install.ps1 there.
#   deploy.sh              build and install
#   deploy.sh --restore    put upstream's original static\ back
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
run="$here/../gpu-box/run.sh"
if [ "${1:-}" = "--restore" ]; then
  "$run" ps 'powershell -ExecutionPolicy Bypass -File C:\argonia\stream-client\install.ps1 -Restore'; exit
fi
"$here/build.sh"
"$run" ps 'Remove-Item -Recurse -Force C:\argonia\stream-client\static -ErrorAction SilentlyContinue; New-Item -ItemType Directory -Force C:\argonia\stream-client\marker, C:\argonia\stream-client\collector | Out-Null'
"$run" put "$here/build/static" 'C:/argonia/stream-client/static' >/dev/null
"$run" put "$here/marker/marker.cs" 'C:/argonia/stream-client/marker/marker.cs' >/dev/null
"$run" put "$here/collector/collector.cs" 'C:/argonia/stream-client/collector/collector.cs' >/dev/null
"$run" put "$here/install.ps1" 'C:/argonia/stream-client/install.ps1' >/dev/null
"$run" ps 'powershell -ExecutionPolicy Bypass -File C:\argonia\stream-client\install.ps1'
