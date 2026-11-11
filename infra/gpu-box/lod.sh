#!/usr/bin/env bash
# The new world's LOD and native map (nw-02 step 11), the stage after tools/newworld/world/world.sh. lod.ps1 is the
# machine's half; docs/design/lod.md is the recipe. Rerunnable: each machine step has its own key, what that step truly
# reads (tools/newworld/world/lodkeys.py), kept on the machine beside its output; a step whose key stands is skipped.
#   lod.sh map                 off-game: tools/newworld/world/mapdata.py build (markers.json, map.json, the .lod), then
#                              `ArgoniaPlugin nwmap apply` on out/newworld/plugin/ArgoniaNewWorld.esm and `nwmap check`
#   lod.sh tools               the three tool rows of infra/gpu-box/lod-tools.json fetched, hash-checked, laid under
#                              C:\argonia\tools\<id> (never Data; sent again only when the archive changed)
#   lod.sh models              the far-off models of the heavy bases (tools/newworld/world/lodmodels.py) into
#                              out/newworld/lodmodels/, then the plan again (they change it): part of map
#   lod.sh send                the ESM to C:\argonia\ours\newworld\, the .lod, the plan files and the LOD models to
#                              C:\argonia\lod\ (each when changed)
#   lod.sh preflight           every check that needs no long step, one "FAULT ..." line each (exit 1 on any): the
#                              world file settled (rebuild.sh settled), the
#                              plan against the world file and the profile, then tools, send and the machine's own
#                              checks (scripts parsed, tools at their hashes, disk, memory, inputs as sent, DynDOLOD's
#                              preset holding our world alone). Run it after `lod.sh map`, before any run.
#   lod.sh keys                each step's key as wanted and as the machine holds it
#   lod.sh run [step ...]      prepare terrain texgen dyndolod collect (default: all, in that order) on the machine;
#                              prepare runs only when a step will, and keeps the outputs of the steps that stand
#   lod.sh check               the derived folder listed on the machine, then every expected terrain LOD file per level
#                              checked (mapdata.py check): out/newworld/lod/check.txt
#   lod.sh archive             the derived folder as a tar to s3://<private>/nw/lod/<key>.tar (never the repo, 0003)
#   lod.sh survey xlodgen|texgen|dyndolod   start one tool in the desktop session, dump its windows, kill it
#   lod.sh stage [step ...]    map, then (NW_LOD=1) preflight, run [steps], check, archive: the whole stage
#   lod.sh selftest [step ...] the whole stage on the small test world (tools/newworld/rebuild.sh small: one block of
#                              the real build as ArgoniaSmallWorld.esm) in minutes: preflight, run, check, coverage,
#                              under its own names on both machines (out/newworld-small/lod here; C:\argonia\lod-small
#                              there, with a Data folder of its own), so the game's Data, the real LOD's outputs
#                              and keys and the profile are never touched. Each step that
#                              ends green is recorded with its code key (lodkeys.py "proof"); a step recorded for
#                              today's code and standing is skipped. `stage`'s preflight refuses a step whose code
#                              was never run here. SELFTEST_STOP=<s> stops the terrain tool after <s> seconds (the
#                              test of carrying a stopped run on); `selftest pass` runs our pass over the terrain
#                              tool's standing output alone; SELFTEST_KEEP=1 keeps
#                              the small world's game folder after the run.
#   PRESET=Low|Medium (default Medium, the preset of every final run) sets DynDOLOD's preset. LOD_FORCE=1 reruns
#   every machine step; LOD_FORCE="texgen dyndolod" those steps.
# The map stage also writes the teleport cells and the LOD plan (mapdata.py build: teleports.py, lodplan.py) and nwmap
# apply turns them into records and DynDOLOD's files (map/DynDOLOD_SSE_*), which send lays in C:\argonia\lod\ and
# lod.ps1 in Data\DynDOLOD\; the terrain step rewrites the meshes with sheson's xLODGen settings; check ends with
# lodplan.py coverage (every large base planned for LOD has it).
# Run under the machine's lock (LOD is CPU- and RAM-heavy):
#   tooling/job_guard.sh run --gpu nw-lod -- infra/gpu-box/lod.sh stage
# Logs and metrics come back to out/newworld/lod/ (never committed). The machine is not stopped here.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd); repo=$(cd "$here/../.." && pwd); cd "$repo"
run="$here/run.sh"
PY=$(ls "$HOME/.argonia/venv/bin/python" 2>/dev/null || command -v python3)
export DOTNET_ROOT="$HOME/.dotnet" PATH="$HOME/.dotnet:$PATH" DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
SMALL=; [ "${1:-}" = selftest ] && SMALL=1
if [ -n "$SMALL" ]; then
  # the small world: built here under the stage tools' own names (src), sent under the play machine's (plug)
  root=out/newworld-small; src=$root/plugin; plug=$root/play/plugin; WORLD=ArgoniaSmallWorld; ESM=$WORLD.esm
  MWORK='C:\argonia\lod-small'; MESM="$MWORK\\$ESM"; PSX="-World $WORLD -Small"
else
  root=out/newworld; src=$root/plugin; plug=$src; WORLD=ArgoniaBlackMarsh; ESM=ArgoniaNewWorld.esm
  MWORK='C:\argonia\lod'; MESM='C:\argonia\ours\newworld\ArgoniaNewWorld.esm'; PSX=
fi
MW=${MWORK//\\//}   # the machine's work folder with forward slashes, for scp
esm=$plug/$ESM; lod=$plug/map/LODSettings/$WORLD.lod
out=$root/lod; mkdir -p "$out"
data="${ARGONIA_GAME_ROOT:-$HOME/games/skyrimse}/Data"
bin=out/tools/ArgoniaPlugin
PRESET=${PRESET:-Medium}
MOD='C:\argonia\ours\derived-NewWorld\argonia-newworld-lod'; [ -z "$SMALL" ] || MOD="$MWORK\\mod"

lm=$root/lodmodels   # the derived far-off models: manifest.json and a Data-shaped meshes\ tree (never committed)
plan_files() { ls "$plug"/map/DynDOLOD_SSE_* 2>/dev/null; }  # nwmap apply's TexGen billboard and DynDOLOD rule files
KEYS=
keys() {  # each step's key (lodkeys.py), computed once a call of this script
  [ -n "$KEYS" ] || KEYS=$("$PY" -m tools.newworld.world.lodkeys --plugin "$plug" --preset "$PRESET" --lodmodels "$lm/manifest.json" --esm "$ESM" --world "$WORLD")
}
proof() { keys; "$PY" -c 'import json,sys; print(json.loads(sys.argv[1])["proof"][sys.argv[2]])' "$KEYS" "$1"; }
# the code keys the small world's selftest recorded on the machine, one "<step>=<key>" a line
proved() { "$run" ps 'Get-Content C:\argonia\lod-small\proved.txt -EA SilentlyContinue' | tr -d '\r' | grep -oE '(terrain|texgen|dyndolod)=[0-9a-f]+' || true; }
want() { keys; "$PY" -c 'import json,sys; print(json.loads(sys.argv[1])[sys.argv[2]])' "$KEYS" "$1"; }
key() { echo "$(want terrain) $(want texgen) $(want dyndolod)" | sha256sum | cut -c1-16; }   # the whole LOD's (the archive's)
machine_keys() { "$run" ps "powershell -ExecutionPolicy Bypass -File C:\\argonia\\infra\\lod.ps1 -Step keys $PSX" | tr -d '\r' | grep -oE '(terrain-tool|terrain-running|terrain|texgen-tool|texgen|dyndolod)=[0-9a-f]+' || true; }
ps1() {  # one lod.ps1 step; the GUI steps in the desktop session, the rest over SSH
  local step=$1; shift
  local line="powershell -ExecutionPolicy Bypass -File C:\\argonia\\infra\\lod.ps1 -Step $step -Preset $PRESET $PSX $*"
  local t0=$SECONDS o
  case "$step" in
    terrain|texgen|dyndolod|survey) o=$(DESKTOP_JOB=lod DESKTOP_WAIT=${DESKTOP_WAIT:-14400} "$run" desktop "$line") || true ;;
    *) o=$("$run" ps "$line") ;;
  esac
  echo "$o"
  echo "== $step: $(( SECONDS - t0 )) s" | tee -a "$out/timings.txt"
  grep -q "$step OK" <<<"$o" || { "$run" ps 'Stop-Process -Name DynDOLODx64, TexGenx64, xLODGenx64, LODGenx64 -Force -EA SilentlyContinue' >/dev/null || true; fetch_back; echo "lod.sh: $step failed" >&2; exit 1; }
}
fetch_back() {
  "$run" get "$MW/logs" "$out/" >/dev/null 2>&1 || true
  "$run" get "$MW/metrics" "$out/" >/dev/null 2>&1 || true
  # DynDOLOD's own read-back of what got LOD (lodplan.py coverage): billboards used, the object LOD rows
  "$run" get "C:/argonia/tools/dyndolod/DynDOLOD/Logs/DynDOLOD_SSE_BillboardsUsed_$WORLD.txt" "$out/logs/" >/dev/null 2>&1 || true
  "$run" get "C:/argonia/tools/dyndolod/DynDOLOD/Edit Scripts/Export/LODGen_SSE_Export_$WORLD.txt" "$out/logs/" >/dev/null 2>&1 || true
}
put_ps1() {
  "$run" ps 'New-Item -ItemType Directory -Force C:\argonia\infra, C:\argonia\tools, C:\argonia\lod, C:\argonia\lod-small, C:\argonia\ours\newworld | Out-Null' >/dev/null
  "$run" put "$here/lod.ps1" "$here/stack.ps1" "$here/pscheck.ps1" "$here/lod-settings.json" C:/argonia/infra/ >/dev/null
}

do_models() {  # the far-off models, then the plan that names them
  "$PY" -m tools.newworld.world.lodmodels build --plugin "$plug" --out "$lm"
}
do_map() {
  dotnet build -c Release -o "$bin" tools/ArgoniaPlugin >/dev/null
  "$PY" -m tools.newworld.world.mapdata build --plugin "$plug"
  do_models
  "$PY" -m tools.newworld.world.lodplan build --plugin "$plug" --lodmodels "$lm/manifest.json" >/dev/null
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
  for f in "$esm:$MESM" "$lod:$MWORK\\$WORLD.lod"; do
    dst=${f#*:}; f=${f%%:*}
    have=$("$run" ps "(Get-FileHash '$dst' -Algorithm SHA256 -EA SilentlyContinue).Hash" | tr -d '\r' | tr 'A-F' 'a-f' | tail -1)
    if [ "$have" = "$(sha256sum "$f" | cut -c1-64)" ]; then echo "send: $(basename "$f") current"
    else
      "$run" put "$f" "$(sed 's|\\|/|g' <<<"$dst")" >/dev/null; echo "send: $(basename "$f") sent"
      have=$("$run" ps "(Get-FileHash '$dst' -Algorithm SHA256 -EA SilentlyContinue).Hash" | tr -d '\r' | tr 'A-F' 'a-f' | tail -1)
    fi
    # the machine's copy, read back after the send: the verifier's deploy row compares it with the build
    [ -n "$SMALL" ] || case "$f" in *.esm) mkdir -p "$repo/out/newworld/verify"; echo "$have" > "$repo/out/newworld/verify/play-esm.sha256" ;; esac
  done
  # the LOD plan files (small): sent whole each time, old ones removed first
  [ -n "$(plan_files)" ] || { echo "send: no $plug/map/DynDOLOD_SSE_* (lod.sh map)" >&2; exit 1; }
  "$run" ps "Remove-Item $MWORK\\DynDOLOD_SSE_* -EA SilentlyContinue" >/dev/null
  "$run" put $(plan_files) "$MW/" >/dev/null; echo "send: $(plan_files | wc -l) LOD plan files"
  # the derived LOD models: sent whole when their key differs from the machine's copy
  local k; k=$("$PY" -c 'import json,sys; print(json.load(open(sys.argv[1]))["key"])' "$lm/manifest.json" 2>/dev/null || true)
  have=$("$run" ps "Get-Content $MWORK\\lodmodels\\.key -EA SilentlyContinue" | tr -d '\r' | tail -1)
  if [ -z "$k" ]; then "$run" ps "Remove-Item $MWORK\\lodmodels -Recurse -Force -EA SilentlyContinue" >/dev/null; echo "send: no LOD models"
  elif [ "$k" = "$have" ]; then echo "send: LOD models current ($k)"
  else
    local tmp; tmp=$(mktemp -d); tar -cf "$tmp/lodmodels.tar" -C "$lm" meshes; echo "$k" > "$tmp/.key"
    "$run" ps "Remove-Item $MWORK\\lodmodels -Recurse -Force -EA SilentlyContinue; New-Item -ItemType Directory -Force $MWORK\\lodmodels | Out-Null" >/dev/null
    "$run" put "$tmp/lodmodels.tar" "$MW/lodmodels/lodmodels.tar" >/dev/null
    "$run" ps "tar -xf $MWORK\\lodmodels\\lodmodels.tar -C $MWORK\\lodmodels; Remove-Item $MWORK\\lodmodels\\lodmodels.tar" >/dev/null
    "$run" put "$tmp/.key" "$MW/lodmodels/.key" >/dev/null   # last: the key vouches for a whole copy
    echo "send: $(find "$lm/meshes" -name '*.nif' | wc -l) LOD models sent ($k)"; rm -r "$tmp"
  fi
}

# The machine's preflight output (lod.ps1 -Step preflight) read against what it must say: its report lines, then one
# FAULT line for each thing that cannot be read from it, with what the machine said instead. $1 the output; the rest
# the lines wanted of it: "have <file> <sha256>", "tool <id> <sha256>", "have lodmodels <count>". Exit 1 on any fault.
read_machine() {
  local o w k got bad=0
  o=$(tr -d '\r' <<<"$1" | sed 's/^\[[0-9:]*\] //'); shift
  said() { awk -v k="$1" '$0 == k || index($0, k " ") == 1' <<<"$o" | head -1; }
  if ! grep -q '[^[:space:]]' <<<"$o"; then
    echo "FAULT the machine's preflight printed nothing: no answer over SSH, or lod.ps1 never started (infra/gpu-box/run.sh ps hostname)"; return 1
  fi
  grep -E '^(FAULT|disk free|ram free|preset worlds|have lodmodels) ' <<<"$o" || true
  if ! grep -qE '^(FAULT|tool|have|disk free|ram free|preset worlds) ' <<<"$o"; then
    echo "FAULT the machine's preflight ran none of its checks: it printed no tool, have, disk, memory or preset line, only \"$(grep '[^[:space:]]' <<<"$o" | tail -3 | paste -sd'|')\" (lod.ps1's preflight step)"; return 1
  fi
  for k in 'disk free' 'ram free' 'preset worlds at 1:'; do
    [ -n "$(said "$k")" ] || { echo "FAULT the machine's preflight printed no \"$k\" line"; bad=1; }
  done
  for w in "$@"; do
    grep -qxF "$w" <<<"$o" && continue
    k=${w% *}; got=$(said "$k"); got=${got:-no \"$k\" line}; bad=1
    case "$w" in
      tool\ *) k=${k#tool }; echo "FAULT tool $k on the machine is not at its pinned hash $(cut -c1-12 <<<"${w##* }") (the machine printed: $got)" ;;
      have\ lodmodels\ *) echo "FAULT the machine does not hold the ${w##* } LOD models built here (the machine printed: $got)" ;;
      *) echo "FAULT the machine's ${k#have } is not the one built here, ${w##* } (the machine printed: $got)" ;;
    esac
  done
  if ! grep -qx 'preflight OK' <<<"$o"; then
    bad=1; grep -q '^FAULT ' <<<"$o" || echo "FAULT the machine's preflight did not finish: $(grep '[^[:space:]]' <<<"$o" | tail -2 | paste -sd'|')"
  fi
  return $bad
}

do_preflight() {  # every check that needs no long step; one FAULT line per fault
  local f="$out/preflight.txt" o bad=0; : > "$f"
  [ -f "$esm" ] && keys
  fault() { echo "FAULT $*" | tee -a "$f"; bad=1; }
  [ -f "$esm" ] || { fault "no $esm (world.sh)"; return 1; }
  # the world file is settled before a long step reads it: the main tree level with origin/main, no rebuild owed or
  # running, no lane holding a change to its sources (tools/newworld/rebuild.sh settled)
  if [ -z "$SMALL" ]; then
    local why
    while IFS= read -r why; do [ -z "$why" ] || fault "the world file is not settled: $why"; done < <(tools/newworld/rebuild.sh settled | grep -v '^settled:' || true)
  fi
  [ -f "$bin/ArgoniaPlugin.dll" ] || dotnet build -c Release -o "$bin" tools/ArgoniaPlugin >/dev/null
  dotnet "$bin/ArgoniaPlugin.dll" nwmap check "$src/ArgoniaNewWorld.esm" "$src/map" > "$out/map-check.txt" 2>&1 || fault "the map and plan against the world file: $(tail -3 "$out/map-check.txt" | tr '\n' ' ') (lod.sh map)"
  "$PY" -m tools.newworld.world.lodplan preflight --plugin "$src" --lodmodels "$lm/manifest.json" | tee -a "$f" || bad=1
  keys || fault "the step keys cannot be computed"
  do_tools | tee -a "$f" || fault "the tools are not at their pinned hashes"
  do_send | tee -a "$f" || fault "the inputs could not be sent"
  o=$("$run" ps "powershell -ExecutionPolicy Bypass -File C:\\argonia\\infra\\lod.ps1 -Step preflight $PSX" 2>&1) || true
  # the machine holds exactly what was built here: the ESM, the .lod, each plan file, each tool, the LOD models
  local x h need=()
  for x in "$esm" "$lod" $(plan_files); do need+=("have $(basename "$x") $(sha256sum "$x" | cut -c1-64)"); done
  while read -r x h; do need+=("tool $x $h"); done < <("$PY" -c 'import json,sys; [print(m["id"], m["sha256"]) for m in json.load(open(sys.argv[1]))["mods"]]' "$here/lod-tools.json")
  need+=("have lodmodels $(find "$lm/meshes" -name '*_lod_*.nif' 2>/dev/null | wc -l)")
  x=$(read_machine "$o" "${need[@]}") || bad=1
  tee -a "$f" <<<"$x"
  local mk pv s; mk=$(machine_keys); pv=$(proved)
  echo "keys wanted: terrain $(want terrain) texgen $(want texgen) dyndolod $(want dyndolod); on the machine: $(tr '\n' ' ' <<<"$mk")" | tee -a "$f"
  # the small world first: a step that will run has had this very code (scripts, settings, tools, plan writer) run
  # green on the small world; a step whose output stands, or whose code key is the one recorded, asks for nothing
  if [ -z "$SMALL" ]; then
    for s in terrain texgen dyndolod; do
      if [ "${LOD_FORCE:-}" != 1 ] && ! grep -qw "$s" <<<"${LOD_FORCE:-}" && grep -qx "$s=$(want $s)" <<<"$mk"; then continue; fi
      grep -qx "$s=$(proof $s)" <<<"$pv" || fault "the $s step will run, and its scripts, settings, tools or plan writer changed since its last green run on the small world: infra/gpu-box/lod.sh selftest"
    done
  fi
  [ $bad = 0 ] && echo "preflight OK" | tee -a "$f" || { echo "preflight FAILED (see $f)" >&2; return 1; }
}

do_run() {
  local steps=("$@") s have keep="" todo=""
  keys   # once, here: a $(want ...) is a subshell and would compute them again each time
  [ ${#steps[@]} -gt 0 ] || steps=(prepare terrain texgen dyndolod collect)
  have=$(machine_keys)
  # a step stands when the machine's output carries the key wanted now (and it is not forced)
  for s in terrain texgen dyndolod; do
    if [ "${LOD_FORCE:-}" = 1 ] || grep -qw "$s" <<<"${LOD_FORCE:-}"; then grep -qw "$s" <<<"${steps[*]}" && todo="$todo $s"; continue; fi
    if grep -qx "$s=$(want $s)" <<<"$have"; then keep="$keep,$s"; continue; fi
    # the tool's own output may stand while our pass over it is owed: kept, and the step runs only that pass
    [ $s != dyndolod ] && grep -qx "$s-tool=$(want $s-tool)" <<<"$have" && keep="$keep,$s"
    # a terrain run that was stopped part-way for this very key is carried on from the textures it wrote
    [ $s = terrain ] && ! grep -qw terrain <<<"${LOD_FORCE:-}" && [ "${LOD_FORCE:-}" != 1 ] && grep -qx "terrain-running=$(want terrain-tool)" <<<"$have" && keep="$keep,$s"
    grep -qw "$s" <<<"${steps[*]}" && todo="$todo $s"
  done
  echo "== keys: stand:${keep//,/ }; to run:${todo:- none}" | tee -a "$out/timings.txt"
  for s in "${steps[@]}"; do
    case "$s" in
      prepare) if [ -z "$todo" ]; then echo "== prepare: nothing to run; skipped"; continue; fi; ps1 prepare -Keep "none$keep"; continue ;;   # never an empty argument
      terrain|texgen|dyndolod)
        if ! grep -qw "$s" <<<"$todo"; then echo "== $s: its output stands for $(want $s); skipped"; continue; fi
        if [ "$s" = dyndolod ]; then ps1 "$s" -Key "$(want $s)"
        elif [ "$s" = terrain ] && [ -n "$SMALL" ] && [ -n "${SELFTEST_STOP:-}" ]; then ps1 "$s" -Key "$(want $s)" -ToolKey "$(want $s-tool)" -Fresh -StopAfterSec "$SELFTEST_STOP"
        elif [ "${LOD_FORCE:-}" = 1 ] || grep -qw "$s" <<<"${LOD_FORCE:-}"; then ps1 "$s" -Key "$(want $s)" -ToolKey "$(want $s-tool)" -Fresh   # the tool too
        else ps1 "$s" -Key "$(want $s)" -ToolKey "$(want $s-tool)"; fi
        continue ;;
    esac
    ps1 "$s"
  done
  fetch_back
  echo "LOD OK: ${steps[*]} ($(key))"
}

do_check() {
  ps1 list >/dev/null
  "$run" get "$MW/logs/files.txt" "$out/files.txt" >/dev/null
  local logs="$out/logs" files="$out/files.txt"
  if [ -n "$SMALL" ]; then  # the machine's listing and logs under the names the stage tools read them by
    cp "$out/files.txt" "$out/logs/files.txt"; rm -rf "$out/real"
    "$PY" -m tools.newworld.small real-names "$out/logs" "$out/real" >/dev/null; logs="$out/real"; files="$out/real/files.txt"
  fi
  "$PY" -m tools.newworld.world.mapdata check "$files" --plugin "$src" | tee "$out/check.txt"
  # every large base planned for LOD got it (DynDOLOD's own lists, fetched back by the run)
  "$PY" -m tools.newworld.world.lodplan coverage "$logs" --plugin "$src" | tee -a "$out/check.txt"
}
hashes() {  # sha256 and path of every output file on the machine, fetched as $out/hashes-<tag>.txt
  "$run" ps "powershell -ExecutionPolicy Bypass -File C:\\argonia\\infra\\lod.ps1 -Step hashes -Tag $1 $PSX" >/dev/null
  "$run" get "$MW/logs/hashes-$1.txt" "$out/hashes-$1.txt" >/dev/null; echo "hashes: $(wc -l < "$out/hashes-$1.txt") files -> $out/hashes-$1.txt"
}
do_selftest() {
  local steps=("$@") s force="" pv
  tools/newworld/rebuild.sh small play
  put_ps1
  case "${1:-}" in
    pass) keys; ps1 terrain -Key "$(want terrain)" -ToolKey "$(want terrain-tool)"; ps1 unlay; fetch_back; hashes pass; return ;;    # our pass alone: the tool's output stands
    hashes) hashes "${2:-now}"; return ;;
    unlay) ps1 unlay; return ;;
  esac
  do_preflight
  # a step proven for today's code and standing is skipped; one whose code changed runs again, tool and all
  pv=$(proved)
  for s in terrain texgen dyndolod; do grep -qx "$s=$(proof $s)" <<<"$pv" || force="$force $s"; done
  [ -z "$force" ] || echo "== selftest: code not yet proven for:$force (run again, tool and all)"
  LOD_FORCE="${LOD_FORCE:-}$force" do_run "${steps[@]}"
  do_check
  [ -n "${SELFTEST_KEEP:-}" ] || ps1 unlay      # the small world's Data folder goes when the run is done
  # each step that ran or stood is now proven for this code
  printf '%s\n' "terrain=$(proof terrain)" "texgen=$(proof texgen)" "dyndolod=$(proof dyndolod)" > "$out/proved.txt"
  "$run" put "$out/proved.txt" "$MW/proved.txt" >/dev/null
  echo "selftest OK: the LOD stage on the small world ($WORLD); proven: $(tr '\n' ' ' < "$out/proved.txt")"
}

do_archive() {
  local bucket=${ARGONIA_PRIVATE_BUCKET:-argonia-private-050977237313} k obj tmp
  keys; k=$(key); obj="nw/lod/$k.tar"
  if [ -z "${LOD_FORCE:-}" ] && aws s3 ls "s3://$bucket/$obj" >/dev/null 2>&1; then echo "archive: s3://$bucket/$obj there; skipped"; return; fi
  tmp=$(mktemp -d)
  "$run" ps "Set-Location '$MOD'; tar -cf C:\\argonia\\lod\\lod.tar *" >/dev/null
  "$run" get 'C:/argonia/lod/lod.tar' "$tmp/lod.tar"
  aws s3 cp --only-show-errors "$tmp/lod.tar" "s3://$bucket/$obj"
  "$run" ps 'Remove-Item C:\argonia\lod\lod.tar' >/dev/null
  echo "archive: $(du -m "$tmp/lod.tar" | cut -f1) MB -> s3://$bucket/$obj"; rm -r "$tmp"
  if [ -f "$lm/manifest.json" ]; then  # the derived LOD models beside it
    tmp=$(mktemp -d); tar -cf "$tmp/lodmodels.tar" -C "$lm" .
    aws s3 cp --only-show-errors "$tmp/lodmodels.tar" "s3://$bucket/nw/lodmodels/$("$PY" -c 'import json,sys; print(json.load(open(sys.argv[1]))["key"])' "$lm/manifest.json").tar"
    rm -r "$tmp"
  fi
}

cmd=${1:-}; shift || true
case "$cmd" in
  map) do_map ;;
  models) do_models ;;
  preflight) put_ps1; do_preflight ;;
  keys) put_ps1; keys; echo "wanted: terrain=$(want terrain) texgen=$(want texgen) dyndolod=$(want dyndolod)"; echo "machine: $(machine_keys | tr '\n' ' ')"
        echo "code keys: terrain=$(proof terrain) texgen=$(proof texgen) dyndolod=$(proof dyndolod); proven on the small world: $(proved | tr '\n' ' ')" ;;
  selftest) t0=$SECONDS; do_selftest "$@"; echo "== selftest: $(( SECONDS - t0 )) s" | tee -a "$out/timings.txt" ;;
  tools) put_ps1; do_tools ;;
  read-machine) read_machine "$(cat "$1")" "${@:2}" ;;   # a saved preflight output read as the preflight reads it
  send) put_ps1; do_send ;;
  run) put_ps1; do_run "$@" ;;
  check) put_ps1; do_check ;;
  archive) do_archive ;;
  survey) [ -n "${1:-}" ] || { sed -n '2,31p' "$0"; exit 2; }; put_ps1; DESKTOP_WAIT=400 ps1 survey -Tool "$1"; fetch_back ;;
  stage)
    t0=$SECONDS; do_map; echo "== map: $(( SECONDS - t0 )) s" | tee -a "$out/timings.txt"
    if [ "${NW_LOD:-0}" = 1 ]; then put_ps1; do_preflight; do_run "$@"; do_check; do_archive; fi ;;
  *) sed -n '2,31p' "$0"; exit 2 ;;
esac
