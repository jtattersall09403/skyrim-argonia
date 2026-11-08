#!/usr/bin/env bash
# ArgoniaNewWorld.esm from the current terrain build (out/newworld/terrain/build.json names it), then its read-back
# and the upload. Masters: Skyrim.esm, Update.esm (+ Black Marsh.esm and its masters when linked); records of
# asset-only mods are copied as ours (ArgoniaPlugin ForeignCopy.cs). Rerun after any terrain rebuild: Rerun after any terrain rebuild; each stage skips what already matches:
#   tooling/job_guard.sh run nw-world -- tools/newworld/world/world.sh
#   tooling/job_guard.sh wait nw-world
# Stages: land shards (tools/newworld/world/land.py, keyed on build id + heightmap + code; resumes by row) ->
# landcover (tools/newworld/landcover.py, keyed) -> ground paint (world/texture.py, keyed, resumes by row) ->
# cells, water types, regions and mist refs (world/cells.py) ->
# navmesh (python -m tools.navmesh build -> out/newworld/plugin/navmesh, attached by NewWorldNavmesh.cs) ->
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
# one writer at a time: a pid file checked with kill -0 (no flock); a second run refuses
mkdir -p "$out"; pidf="$out/world.sh.pid"
if [ -f "$pidf" ] && kill -0 "$(cat "$pidf")" 2>/dev/null; then
  echo "world.sh: another run (pid $(cat "$pidf")) is writing $out; wait for it (tooling/job_guard.sh status)" >&2; exit 2
fi
# the native map (nw-02 step 11): settlement markers and MNAM/ONAM, applied whenever the ESM lacks this build's map
"$py" -m tools.newworld.world.mapdata build >/dev/null
dotnet "$bin/ArgoniaPlugin.dll" nwmap check "$esm" "$out/map" >/dev/null || dotnet "$bin/ArgoniaPlugin.dll" nwmap apply "$esm" "$out/map" "$data"
dotnet "$bin/ArgoniaPlugin.dll" nwmap check "$esm" "$out/map" | tee "$out/map-check.txt"
echo $$ > "$pidf"; trap 'rm -f "$pidf"' EXIT
"$py" -m tools.newworld.world.land --out "$out"
"$py" -m tools.newworld.landcover
"$py" -m tools.newworld.world.texture --out "$out"
"$py" -m tools.newworld.world.cells --out "$out"
# navmesh (tools/navmesh, per-cell cached; NW_NAVMESH=0 skips): red checks are reported, never block the land
if [ "${NW_NAVMESH:-1}" = 1 ]; then "$py" -m tools.navmesh build --plugin "$out" --out "$out/navmesh" || echo "navmesh: checks red (see $out/navmesh/check.json)"; fi
dotnet build -c Release -o "$bin" tools/ArgoniaPlugin >/dev/null
key=$("$py" -c 'import json,sys; print(json.load(open(sys.argv[1]))["key"])' "$man")
key="$key:${NW_REF_PRODUCERS:-all}:$(cat "$out/tex/manifest.json" "$out/cells.json" $(find "$out/refs" -name '*.jsonl' | sort) | sha256sum | cut -c1-16)"
codekey=$(cat tools/ArgoniaPlugin/NewWorld.cs tools/ArgoniaPlugin/ForeignCopy.cs tools/ArgoniaPlugin/NewWorldNavmesh.cs $(ls "$out"/navmesh/navi.json "$out"/navmesh/navm/cy*.jsonl.gz 2>/dev/null) | sha256sum | cut -c1-16)
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
"$py" -m tools.newworld.world.texcheck --out "$out" | tee -a "$out/check.txt"
if [ "${NW_UPLOAD:-1}" = 1 ]; then
  id=$("$py" -c 'import json,sys; print(json.load(open(sys.argv[1]))["build_id"])' "$man")
  for f in "$esm" "$stamp" "$out/check.txt" "$man"; do aws s3 cp --only-show-errors "$f" "s3://argonia-private-050977237313/nw/plugin/$id/"; done
  echo "uploaded to s3://argonia-private-050977237313/nw/plugin/$id/"
fi
