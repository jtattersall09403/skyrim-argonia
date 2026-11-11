#!/usr/bin/env bash
# The world file's own steps: ArgoniaNewWorld.esm from the shards under out/newworld/plugin, its map data, its check
# and its upload. tools/newworld/rebuild.sh runs them as its `esm` and `upload` stages, after the stages that write
# the shards; the order of the whole rebuild, its keys and its checks are tools/newworld/rebuild.py's, and the recipe
# is the skill world-build.
#   world.sh write    the ESM from land/, tex/, cells.json, atmosphere.json, refs/<producer>/ and navmesh/
#                     (ArgoniaPlugin `newworld write`); skipped when the stamp ArgoniaNewWorld.json holds this key
#   world.sh current  exit 0 when the ESM and its stamp hold the key `write` computes today (writes nothing)
#   world.sh map      the map data of map/ applied when the ESM lacks it (`nwmap apply`), then read back -> map-check.txt
#   world.sh check    the file read back (`newworld check`: cells, height error, seams, overflow, water, the start
#                     marker) -> check.txt
#   world.sh upload   the ESM, its stamp, check.txt and the land manifest -> s3://argonia-private-050977237313/nw/plugin/<build id>/
#   world.sh          the whole rebuild: tools/newworld/rebuild.sh run
# Masters: Skyrim.esm, Update.esm, Black Marsh.esm; records of asset-only mods are copied as ours (ForeignCopy.cs).
# Out: out/newworld/plugin/ (never git). Env: ARGONIA_GAME_ROOT (default ~/games/skyrimse) for Data;
# NW_REF_PRODUCERS (default all) limits the refs written; NW_UPLOAD=0 skips the upload.
set -euo pipefail
repo=$(cd "$(dirname "$0")/../../.." && pwd); cd "$repo"
[ $# -gt 0 ] || exec tools/newworld/rebuild.sh run
export DOTNET_ROOT="$HOME/.dotnet" PATH="$HOME/.dotnet:$PATH" DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
py=$(ls "$HOME/.argonia/venv/bin/python" 2>/dev/null || command -v python3)
data="${ARGONIA_GAME_ROOT:-$HOME/games/skyrimse}/Data"
out=out/newworld/plugin; esm=$out/ArgoniaNewWorld.esm; man=$out/land/manifest.json; stamp=$out/ArgoniaNewWorld.json
bin=out/tools/ArgoniaPlugin
plugin() { dotnet "$bin/ArgoniaPlugin.dll" "$@"; }
# one writer of the ESM at a time: a pid file checked with kill -0 (no flock); a second writer refuses
writer() {
  mkdir -p "$out"; pidf="$out/world.sh.pid"
  if [ -f "$pidf" ] && kill -0 "$(cat "$pidf")" 2>/dev/null; then
    echo "world.sh: another run (pid $(cat "$pidf")) is writing $out; wait for it (tooling/job_guard.sh status)" >&2; exit 2
  fi
  echo $$ > "$pidf"; trap 'rm -f "$pidf"' EXIT
}
# the ESM's key: the land's key, the producers written, the shards' and specs' bytes, the writer's code, the navmesh
esm_key() {
  key=$("$py" -c 'import json,sys; print(json.load(open(sys.argv[1]))["key"])' "$man")
  key="$key:${NW_REF_PRODUCERS:-all}:$(cat "$out/tex/manifest.json" "$out/cells.json" "$out/atmosphere.json" $(find "$out/refs" -name '*.jsonl' | sort) | sha256sum | cut -c1-16)"
  codekey=$(cat tools/ArgoniaPlugin/NewWorld.cs tools/ArgoniaPlugin/WaterBlend.cs tools/ArgoniaPlugin/ForeignCopy.cs tools/ArgoniaPlugin/NewWorldNavmesh.cs tools/ArgoniaPlugin/NewWorldAtmosphere.cs $(ls "$out"/navmesh/navi.json "$out"/navmesh/navm/cy*.jsonl.gz 2>/dev/null) | sha256sum | cut -c1-16)
}
esm_current() { [ -f "$esm" ] && [ -f "$stamp" ] && grep -q "\"key\": \"$key:$codekey\"" "$stamp"; }
case "$1" in
  current)
    esm_key
    if esm_current; then echo "esm: its key is today's"; else echo "esm: its key is not today's"; exit 1; fi ;;
  write)
    writer
    dotnet build -c Release -o "$bin" tools/ArgoniaPlugin -v q -nologo >/dev/null
    esm_key
    if esm_current; then
      echo "esm current ($key)"
    else
      t0=$(date +%s.%N)
      plugin newworld write "$man" "$data" "$esm"
      t1=$(date +%s.%N)
      "$py" -c 'import json,sys,os; k,e,t=sys.argv[1:4]; json.dump({"key":k,"esm":e,"bytes":os.path.getsize(e),"write_s":round(float(t),1)},open(sys.argv[4],"w"),indent=1)' \
        "$key:$codekey" "$esm" "$(echo "$t1 - $t0" | bc)" "$stamp.tmp"
      mv "$stamp.tmp" "$stamp"
    fi ;;
  map)
    writer
    plugin nwmap check "$esm" "$out/map" >/dev/null || plugin nwmap apply "$esm" "$out/map" "$data"
    plugin nwmap check "$esm" "$out/map" | tee "$out/map-check.txt" ;;
  check)
    plugin newworld check "$esm" "$man" "$data" | tee "$out/check.txt" ;;
  upload)
    [ "${NW_UPLOAD:-1}" = 1 ] || { echo "upload skipped (NW_UPLOAD=0)"; exit 0; }
    id=$("$py" -c 'import json,sys; print(json.load(open(sys.argv[1]))["build_id"])' "$man")
    for f in "$esm" "$stamp" "$out/check.txt" "$man"; do aws s3 cp --only-show-errors "$f" "s3://argonia-private-050977237313/nw/plugin/$id/"; done
    echo "uploaded to s3://argonia-private-050977237313/nw/plugin/$id/" ;;
  *) echo "usage: world.sh [write|current|map|check|upload]" >&2; exit 2 ;;
esac
