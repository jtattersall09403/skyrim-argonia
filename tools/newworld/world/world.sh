#!/usr/bin/env bash
# ArgoniaNewWorld.esm from the current terrain build (out/newworld/terrain/build.json names it), then its read-back
# and the upload. Rerun after any terrain rebuild; each stage skips what already matches:
#   tooling/job_guard.sh run nw-world -- tools/newworld/world/world.sh
#   tooling/job_guard.sh wait nw-world
# Stages: land shards (tools/newworld/world/land.py, keyed on build id + heightmap + code; resumes by row) ->
# ESM write (tools/ArgoniaPlugin `newworld write`, skipped when the stamp's key matches) -> read-back
# (`newworld check`: cells, height error, seams, overflow, water, the coc marker) -> bucket
# s3://argonia-private-050977237313/nw/plugin/<build id>/. Out: out/newworld/plugin/ (never git).
# Env: ARGONIA_GAME_ROOT (default ~/games/skyrimse) for Data; NW_UPLOAD=0 skips the upload.
set -euo pipefail
repo=$(cd "$(dirname "$0")/../../.." && pwd); cd "$repo"
export DOTNET_ROOT="$HOME/.dotnet" PATH="$HOME/.dotnet:$PATH" DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
py=$(ls "$HOME/.argonia/venv/bin/python" 2>/dev/null || command -v python3)
data="${ARGONIA_GAME_ROOT:-$HOME/games/skyrimse}/Data"
out=out/newworld/plugin; esm=$out/ArgoniaNewWorld.esm; man=$out/land/manifest.json; stamp=$out/ArgoniaNewWorld.json
bin=out/tools/ArgoniaPlugin
"$py" -m tools.newworld.world.land --out "$out"
dotnet build -c Release -o "$bin" tools/ArgoniaPlugin >/dev/null
key=$("$py" -c 'import json,sys; print(json.load(open(sys.argv[1]))["key"])' "$man")
codekey=$(cat tools/ArgoniaPlugin/NewWorld.cs | sha256sum | cut -c1-16)
if [ -f "$esm" ] && [ -f "$stamp" ] && grep -q "\"key\": \"$key:$codekey\"" "$stamp"; then
  echo "esm current ($key)"
else
  t0=$(date +%s.%N)
  dotnet "$bin/ArgoniaPlugin.dll" newworld write "$man" "$data" "$esm"
  t1=$(date +%s.%N)
  "$py" -c 'import json,sys,os; k,e,t=sys.argv[1:4]; json.dump({"key":k,"esm":e,"bytes":os.path.getsize(e),"write_s":round(float(t),1)},open(sys.argv[4],"w"),indent=1)' \
    "$key:$codekey" "$esm" "$(echo "$t1 - $t0" | bc)" "$stamp.tmp"
  mv "$stamp.tmp" "$stamp"
fi
dotnet "$bin/ArgoniaPlugin.dll" newworld check "$esm" "$man" "$data" | tee "$out/check.txt"
if [ "${NW_UPLOAD:-1}" = 1 ]; then
  id=$("$py" -c 'import json,sys; print(json.load(open(sys.argv[1]))["build_id"])' "$man")
  for f in "$esm" "$stamp" "$out/check.txt" "$man"; do aws s3 cp --only-show-errors "$f" "s3://argonia-private-050977237313/nw/plugin/$id/"; done
  echo "uploaded to s3://argonia-private-050977237313/nw/plugin/$id/"
fi
