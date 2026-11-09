#!/usr/bin/env bash
# The new world's LOD and native map (nw-02 step 11), the stage after tools/newworld/world/world.sh. lod.ps1 is the
# machine's half. Rerunnable: each step skips what already matches (markers keyed by the ESM's sha and the tools).
#   lod.sh map                 off-game: tools/newworld/world/mapdata.py build (markers.json, map.json, the .lod), then
#                              `ArgoniaPlugin nwmap apply` on out/newworld/plugin/ArgoniaNewWorld.esm and `nwmap check`
#   lod.sh tools               the three tool rows of infra/gpu-box/lod-tools.json fetched, hash-checked, laid under
#                              C:\argonia\tools\<id> (never Data; sent again only when the archive changed)
#   lod.sh send                the ESM to C:\argonia\ours\newworld\, the .lod to C:\argonia\lod\ (when changed)
#   lod.sh run [step ...]      prepare terrain texgen dyndolod collect (default: all, in that order) on the machine
#   lod.sh check               the derived folder listed on the machine, then every expected terrain LOD file per level
#                              checked (mapdata.py check): out/newworld/lod/check.txt
#   lod.sh archive             the derived folder as a tar to s3://<private>/nw/lod/<key>.tar (never the repo, 0003)
#   lod.sh survey xlodgen|texgen|dyndolod   start one tool in the desktop session, dump its windows, kill it
#   lod.sh stage [step ...]    map, then (NW_LOD=1) tools, send, run [steps], check, archive: the whole stage
#   PRESET=Low|Medium (default Low) sets DynDOLOD's preset. LOD_FORCE=1 reruns every machine step.
# Run under the machine's lock (LOD is CPU- and RAM-heavy):
#   tooling/job_guard.sh run --gpu nw-lod -- infra/gpu-box/lod.sh stage
# Logs and metrics come back to out/newworld/lod/ (never committed). The machine is not stopped here.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd); repo=$(cd "$here/../.." && pwd); cd "$repo"
run="$here/run.sh"
PY=$(ls "$HOME/.argonia/venv/bin/python" 2>/dev/null || command -v python3)
export DOTNET_ROOT="$HOME/.dotnet" PATH="$HOME/.dotnet:$PATH" DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
plug=out/newworld/plugin; esm=$plug/ArgoniaNewWorld.esm; lod=$plug/map/LODSettings/ArgoniaBlackMarsh.lod
out=out/newworld/lod; mkdir -p "$out"
data="${ARGONIA_GAME_ROOT:-$HOME/games/skyrimse}/Data"
bin=out/tools/ArgoniaPlugin
PRESET=${PRESET:-Low}
MOD='C:\argonia\ours\derived-NewWorld\argonia-newworld-lod'

key() {  # the LOD's inputs: the mapped ESM, the .lod, the machine script, the tools' archives, the preset
  { sha256sum "$esm" "$lod" "$here/lod.ps1" | cut -c1-64; "$PY" -c 'import json,sys; [print(m["sha256"]) for m in json.load(open(sys.argv[1]))["mods"]]' "$here/lod-tools.json"; echo "$PRESET"; } | sha256sum | cut -c1-16
}
ps1() {  # one lod.ps1 step; the GUI steps in the desktop session, the rest over SSH
  local step=$1; shift
  local line="powershell -ExecutionPolicy Bypass -File C:\\argonia\\infra\\lod.ps1 -Step $step -Preset $PRESET $*"
  local t0=$SECONDS o
  case "$step" in
    terrain|texgen|dyndolod|survey) o=$(DESKTOP_JOB=lod DESKTOP_WAIT=${DESKTOP_WAIT:-14400} "$run" desktop "$line") ;;
    *) o=$("$run" ps "$line") ;;
  esac
  echo "$o"
  echo "== $step: $(( SECONDS - t0 )) s" | tee -a "$out/timings.txt"
  grep -q "$step OK" <<<"$o" || { "$run" ps 'Stop-Process -Name DynDOLODx64, TexGenx64, xLODGenx64, LODGenx64 -Force -EA SilentlyContinue' >/dev/null || true; fetch_back; echo "lod.sh: $step failed" >&2; exit 1; }
}
fetch_back() {
  "$run" get 'C:/argonia/lod/logs' "$out/" >/dev/null 2>&1 || true
  "$run" get 'C:/argonia/lod/metrics' "$out/" >/dev/null 2>&1 || true
}
put_ps1() {
  "$run" ps 'New-Item -ItemType Directory -Force C:\argonia\infra, C:\argonia\tools, C:\argonia\lod, C:\argonia\ours\newworld | Out-Null' >/dev/null
  "$run" put "$here/lod.ps1" "$here/stack.ps1" C:/argonia/infra/ >/dev/null
}

do_map() {
  dotnet build -c Release -o "$bin" tools/ArgoniaPlugin >/dev/null
  "$PY" -m tools.newworld.world.mapdata build
  dotnet "$bin/ArgoniaPlugin.dll" nwmap apply "$esm" "$plug/map" "$data"
  dotnet "$bin/ArgoniaPlugin.dll" nwmap check "$esm" "$plug/map" | tee "$out/map-check.txt"
  if [ "${NW_UPLOAD:-1}" = 1 ]; then
    id=$("$PY" -c 'import json,sys; print(json.load(open(sys.argv[1]))["build_id"])' "$plug/land/manifest.json")
    aws s3 cp --only-show-errors "$esm" "s3://argonia-private-050977237313/nw/plugin/$id/"
  fi
}

do_tools() {
  "$PY" - "$here" <<'EOF'
import sys, json, subprocess
sys.path.insert(0, sys.argv[1]); import stack
rows = json.load(open(f"{sys.argv[1]}/lod-tools.json"))["mods"]
key = stack.secret("NEXUS_API_KEY")
for m in rows:
    rid = m["id"]
    path, how = stack.fetch_one(m, key)
    h = stack.sha256(path)
    if h != m["sha256"]:
        sys.exit(f"{rid}: sha256 {h[:12]} != lod-tools.json {m['sha256'][:12]}")
    stack.cache(path, h)
    have = subprocess.run([stack.RUN, "ps", rf"Get-Content C:\argonia\tools\{rid}\.sha256 -EA SilentlyContinue"],
                          capture_output=True, text=True).stdout.strip()
    if have == h:
        print(f"{rid}: laid ({h[:12]})"); continue
    work = stack.STACK / "_lod" / rid
    subprocess.run(["rm", "-rf", str(work)], check=True)
    stack.unpack(path, work)
    (work / ".sha256").write_text(h)
    tar = stack.STACK / "_lod" / f"{rid}.tar"
    subprocess.run(["tar", "-cf", str(tar), "-C", str(work), "."], check=True)
    stack.run("ps", rf"Remove-Item -Recurse -Force C:\argonia\tools\{rid} -EA SilentlyContinue; New-Item -ItemType Directory -Force C:\argonia\tools\{rid}, C:\argonia\MO2\push | Out-Null")
    stack.run("put", str(tar), f"C:/argonia/MO2/push/{rid}.tar")
    stack.run("ps", rf"tar -xf C:\argonia\MO2\push\{rid}.tar -C C:\argonia\tools\{rid}; Remove-Item C:\argonia\MO2\push\{rid}.tar")
    tar.unlink(); subprocess.run(["rm", "-rf", str(work)], check=True)
    print(f"{rid}: {how}, laid under C:\\argonia\\tools\\{rid} ({h[:12]})")
EOF
}

do_send() {  # each file only when the machine's copy differs
  local f dst have
  for f in "$esm:C:\\argonia\\ours\\newworld\\ArgoniaNewWorld.esm" "$lod:C:\\argonia\\lod\\ArgoniaBlackMarsh.lod"; do
    dst=${f#*:}; f=${f%%:*}
    have=$("$run" ps "(Get-FileHash '$dst' -Algorithm SHA256 -EA SilentlyContinue).Hash" | tr -d '\r' | tr 'A-F' 'a-f' | tail -1)
    if [ "$have" = "$(sha256sum "$f" | cut -c1-64)" ]; then echo "send: $(basename "$f") current"; continue; fi
    "$run" put "$f" "$(sed 's|\\|/|g' <<<"$dst")" >/dev/null; echo "send: $(basename "$f") sent"
  done
}

do_run() {
  local steps=("$@") k marks s
  [ ${#steps[@]} -gt 0 ] || steps=(prepare terrain texgen dyndolod collect)
  k=$(key); marks="$HOME/.argonia/lod-steps/nw-${ARGONIA_PLAY:-argonia-play}/$k"; mkdir -p "$marks"
  for s in "${steps[@]}"; do
    case "$s" in prepare|terrain|texgen|dyndolod)
      if [ -z "${LOD_FORCE:-}" ] && [ -f "$marks/$s" ]; then echo "== $s: done before for $k ($(cat "$marks/$s")); skipped"; continue; fi ;;
    esac
    ps1 "$s"
    case "$s" in prepare|terrain|texgen|dyndolod) date -u +%FT%TZ > "$marks/$s" ;; esac
  done
  fetch_back
  echo "LOD OK: ${steps[*]} ($k)"
}

do_check() {
  ps1 list >/dev/null
  "$run" get 'C:/argonia/lod/logs/files.txt' "$out/files.txt" >/dev/null
  "$PY" -m tools.newworld.world.mapdata check "$out/files.txt" | tee "$out/check.txt"
}

do_archive() {
  local bucket=${ARGONIA_PRIVATE_BUCKET:-argonia-private-050977237313} k obj tmp
  k=$(key); obj="nw/lod/$k.tar"
  if [ -z "${LOD_FORCE:-}" ] && aws s3 ls "s3://$bucket/$obj" >/dev/null 2>&1; then echo "archive: s3://$bucket/$obj there; skipped"; return; fi
  tmp=$(mktemp -d)
  "$run" ps "Set-Location '$MOD'; tar -cf C:\\argonia\\lod\\lod.tar *" >/dev/null
  "$run" get 'C:/argonia/lod/lod.tar' "$tmp/lod.tar"
  aws s3 cp --only-show-errors "$tmp/lod.tar" "s3://$bucket/$obj"
  "$run" ps 'Remove-Item C:\argonia\lod\lod.tar' >/dev/null
  echo "archive: $(du -m "$tmp/lod.tar" | cut -f1) MB -> s3://$bucket/$obj"; rm -rf "$tmp"
}

cmd=${1:-}; shift || true
case "$cmd" in
  map) do_map ;;
  tools) put_ps1; do_tools ;;
  send) put_ps1; do_send ;;
  run) put_ps1; do_run "$@" ;;
  check) put_ps1; do_check ;;
  archive) do_archive ;;
  survey) [ -n "${1:-}" ] || { sed -n '2,20p' "$0"; exit 2; }; put_ps1; DESKTOP_WAIT=400 ps1 survey -Tool "$1"; fetch_back ;;
  stage)
    t0=$SECONDS; do_map; echo "== map: $(( SECONDS - t0 )) s" | tee -a "$out/timings.txt"
    if [ "${NW_LOD:-0}" = 1 ]; then put_ps1; do_tools; do_send; do_run "$@"; do_check; do_archive; fi ;;
  *) sed -n '2,20p' "$0"; exit 2 ;;
esac
