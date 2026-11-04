#!/usr/bin/env bash
# The LOD job for ARG_Province (2.W4 §c, decision 0014 §4), driven from the build VM; lod.ps1 is the machine's half.
# OWNER RULE (2026-11-02): a rebuild is slow (terrain ~26 min, then texgen and DynDOLOD) and agents have rebuilt it
# when nothing needed it. Rebuild only when the deployed ArgoniaWorld's LAND or placed objects changed (deploy's lod
# step says "no LOD archive for this ArgoniaWorld"); and before you rebuild, first make the process faster for this
# run (skip unchanged steps, the lowest LOD texture size the check needs, only the levels the check needs, keep the
# machine's cache) and write the measured time per step in your report, so the next rebuild starts from a faster recipe.
#   lod.sh tools                       the three tool rows (xlodgen, dyndolod, dyndolod-resources in
#                                      data/dependencies.json) fetched, hash-checked, unpacked and laid under
#                                      C:\argonia\tools\<id> (never Data; sent again only when the archive changed)
#   lod.sh survey xlodgen|texgen|dyndolod   start one tool in the desktop session, dump its windows, kill it
#   lod.sh run [step ...]              prepare terrain texgen dyndolod collect (default: all, in that order)
#                                      (resources: re-link DynDOLOD Resources into Data without a prepare, after a restart)
#   lod.sh still <tag>                 the vantage still: the game launched on the laid profile, the base save, the
#                                      highest ground within 8 cells of Claywater (cell -53,3, 440 m; the LAND shards),
#                                      facing north-west over Claywater at noon, after 30 s -> out/lod/vantage-<tag>.png
#   lod.sh archive [terrain|object]    the machine's "Argonia LOD (generated)" mod, per half, as a tar to the private
#                                      bucket (s3://argonia-private-…/lod/<half>-<key>.tar): derived from game data,
#                                      so never the repo (decision 0003)
#   lod.sh ensure                      deploy's step: per half, restore when the machine's key (argonia-lod.key in the
#                                      mod) is not this ArgoniaWorld's; no archive: a WARNING naming that half's steps
#   lod.sh restore [terrain|object]    that half's tar for this out/ArgoniaWorld.esm onto the machine
#                                      and the profile laid again with it: minutes, not 26 of xLODGen. Skyrim is killed.
#   lod.sh key [esm]                   print the two LOD keys of that ESM (default out/ArgoniaWorld.esm)
#   PRESET=Low|Medium (default Medium) sets DynDOLOD's preset.
# Run under the GPU lock (LOD is CPU- and RAM-heavy and must not overlap a timing batch):
#   tooling/job_guard.sh run --gpu lod -- infra/gpu-box/lod.sh run
# Logs and metrics come back to out/lod/ (never committed). The machine is not stopped here.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd); repo=$(cd "$here/../.." && pwd)
run="$here/run.sh"
PY=$(ls "$HOME/.argonia/venv/bin/python" 2>/dev/null || command -v python3)
ROWS=(xlodgen dyndolod dyndolod-resources)
mkdir -p "$repo/out/lod"
# The LOD's two keys (owner ruling 2026-11-04 08:06, #37; decision 0037: a key names its inputs), from
# tools/navmesh/lodkey.py: terrain = the LAND records + xlodgen's pin, object = the placed refs and the forms they draw
# + the master list + dyndolod's two pins and every stack mod's pin; both + lod.ps1, lodsettings.py and the preset.
# A navmesh, water or weather change keeps both; each half rebuilds and archives on its own.
#   s3://<bucket>/lod/terrain-<key>.tar  Meshes/Terrain and Textures/Terrain of the LOD mod
#   s3://<bucket>/lod/object-<key>.tar   the rest of it (DynDOLOD, Meshes/LOD, Textures/LOD, ...)
lodkey() {  # prints "terrain=<12> object=<12>"
  local esm=${1:-$repo/out/ArgoniaWorld.esm} pin common
  pin() { "$PY" -c 'import json,sys; r={m["id"]:m for m in json.load(open(sys.argv[1]))["mods"]}; print(" ".join(r[i]["sha256"] if i in r else i for i in sys.argv[2:]))' "$repo/data/dependencies.json" "$@"; }
  common=(--terrain-salt "preset=${PRESET:-Medium}" --object-salt "preset=${PRESET:-Medium}"
          --terrain-salt-file infra/gpu-box/lod.ps1 --object-salt-file infra/gpu-box/lod.ps1
          --terrain-salt-file infra/gpu-box/lodsettings.py --object-salt-file infra/gpu-box/lodsettings.py)
  (cd "$repo" && "$PY" -m tools.navmesh.lodkey "$esm" "${common[@]}" --terrain-salt "$(pin xlodgen)" \
     --object-salt "$(pin dyndolod dyndolod-resources)" \
     --object-salt "$("$PY" -c 'import json,sys; print(" ".join(sorted(m.get("sha256") or "" for m in json.load(open(sys.argv[1]))["mods"])))' data/dependencies.json)")
}
half_of() { case "$1" in terrain) echo terrain ;; texgen|dyndolod) echo object ;; *) echo both ;; esac; }
key_of() { sed -n "s/.*$1=\([0-9a-f]*\).*/\1/p" <<<"$2"; }

ps1() {  # one lod.ps1 step; the GUI steps in the desktop session, the rest over SSH
  local step=$1; shift
  local line="powershell -ExecutionPolicy Bypass -File C:\\argonia\\infra\\lod.ps1 -Step $step -Preset ${PRESET:-Medium} $*"
  local t0=$SECONDS out
  case "$step" in
    terrain|texgen|dyndolod|survey) out=$(DESKTOP_JOB=lod DESKTOP_WAIT=${DESKTOP_WAIT:-14400} "$run" desktop "$line") ;;  # its own desktop job: the batch's run beside it
    *) out=$("$run" ps "$line") ;;
  esac
  echo "$out"
  echo "== $step: $(( SECONDS - t0 )) s"
  grep -q "$step OK" <<<"$out" || { fetch_back; echo "lod.sh: $step failed" >&2; exit 1; }
}
fetch_back() {
  "$run" get 'C:/argonia/lod/logs' "$repo/out/lod/" >/dev/null 2>&1 || true
  "$run" get 'C:/argonia/lod/metrics' "$repo/out/lod/" >/dev/null 2>&1 || true
}

tools() {
  "$PY" - "$here" "${ROWS[@]}" <<'EOF'
import sys, pathlib, json, subprocess
sys.path.insert(0, sys.argv[1]); import stack
rows = {m["id"]: m for m in stack.manifest()["mods"]}
key = stack.secret("NEXUS_API_KEY")
for rid in sys.argv[2:]:
    m = rows[rid]
    path, how = stack.fetch_one(m, key)
    h = stack.sha256(path)
    if h != m["sha256"]:
        sys.exit(f"{rid}: sha256 {h[:12]} != manifest {m['sha256'][:12]}")
    have = subprocess.run([stack.RUN, "ps", rf"Get-Content C:\argonia\tools\{rid}\.sha256 -EA SilentlyContinue"],
                          capture_output=True, text=True).stdout.strip()
    if have == h:
        print(f"{rid}: laid ({h[:12]})"); continue
    work = stack.STACK / "_lod" / rid
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

case "${1:-}" in tools|survey|run|still|archive|restore|ensure|key) ;; *) sed -n "2,10p" "$0"; exit 2 ;; esac
[ "$1" = key ] && { lodkey "${2:-}"; exit 0; }  # no machine needed
"$run" ps 'New-Item -ItemType Directory -Force C:\argonia\infra, C:\argonia\tools | Out-Null' >/dev/null
"$run" put "$here/lod.ps1" C:/argonia/infra/lod.ps1 >/dev/null
# ARG_Province's LODSettings file, from the land the plugin build wrote (lodsettings.py; lod.ps1 lays it)
"$PY" "$here/lodsettings.py" "$repo/out/terrain/land" "$repo/out/lod/ARG_Province.lod"
"$run" ps 'New-Item -ItemType Directory -Force C:\argonia\lod | Out-Null' >/dev/null
"$run" put "$repo/out/lod/ARG_Province.lod" C:/argonia/lod/ARG_Province.lod >/dev/null
case "${1:-}" in
  tools) tools ;;
  survey) [ -n "${2:-}" ] || { sed -n '2,10p' "$0"; exit 2; }; DESKTOP_WAIT=400 ps1 survey -Tool "$2"; fetch_back ;;
  run)
    shift; steps=("$@"); [ ${#steps[@]} -gt 0 ] || steps=(prepare terrain texgen dyndolod collect)
    tools
    # Per-step markers for this ArgoniaWorld (owner, 2026-11-02: a rerun must pick up where the last attempt got to):
    # prepare, terrain, texgen and dyndolod are skipped when their marker exists for the deployed ESM's sha; collect,
    # archive and resources always run. LOD_FORCE=1 reruns everything. The outputs they stand for live on the machine.
    # a step's marker is under its half's key (terrain: terrain; texgen, dyndolod: object; prepare: both)
    keys=$(lodkey); tk=$(key_of terrain "$keys"); ok=$(key_of object "$keys")
    for s in "${steps[@]}"; do
      case $(half_of "$s") in terrain) sha12=t-$tk ;; object) sha12=o-$ok ;; *) sha12=$tk-$ok ;; esac
      marks="$HOME/.argonia/lod-steps/${ARGONIA_PLAY:-argonia-play}/$sha12"; mkdir -p "$marks"  # per machine: the outputs live there
      case "$s" in prepare|terrain|texgen|dyndolod)
        if [ -z "${LOD_FORCE:-}" ] && [ -f "$marks/$s" ]; then echo "== $s: done before for $sha12 ($(cat "$marks/$s")); skipped"; continue; fi ;;
      esac
      ps1 "$s"
      case "$s" in prepare|terrain|texgen|dyndolod) date -u +%FT%TZ > "$marks/$s" ;; esac
    done
    fetch_back
    echo "LOD OK: ${steps[*]}" ;;
  still)
    [ -n "${2:-}" ] || { echo "still <tag>" >&2; exit 2; }
    B=("$PY" "$repo/tools/bridge.py")
    "${B[@]}" launch --fresh >/dev/null
    "${B[@]}" load argoniabase >/dev/null
    read -t 20 < /dev/zero 2>/dev/null || true
    # cell (-53, 3) south row, column 27: x = -53*4096 + 27*128, y = 3*4096, z = 440.3 m * 70.03 + 2 m of eye room
    for c in 'set gamehour to 12' 'cow ARG_Province -53 3'; do "${B[@]}" console "$c" >/dev/null; done
    read -t 20 < /dev/zero 2>/dev/null || true
    for c in 'player.setpos x -213632' 'player.setpos y 12350' 'player.setpos z 30980' 'player.setangle x 8' \
             'player.setangle z 315' 'tm'; do "${B[@]}" console "$c" >/dev/null; done
    read -t 30 < /dev/zero 2>/dev/null || true
    "${B[@]}" screenshot "$repo/out/lod/vantage-$2.png"
    "${B[@]}" player | head -20
    "${B[@]}" console 'tm' >/dev/null ;;
  ensure)
    # each half laid from its own archive when the machine's half differs; a half with no archive: a loud WARNING
    # naming only that half's steps (the other half is laid, never rebuilt)
    bucket=${ARGONIA_PRIVATE_BUCKET:-argonia-private-050977237313}
    keys=$(lodkey); mod='C:\argonia\MO2\mods\Argonia LOD (generated)'
    have=$("$run" ps "Get-Content '$mod\argonia-lod.key' -EA SilentlyContinue" | tr -d '\r' | tr '\n' ' ' || true)
    lay=() miss=()
    for h in terrain object; do
      k=$(key_of "$h" "$keys")
      if [ "$(key_of "$h" "$have")" = "$k" ]; then echo "LOD $h current ($k)"; continue; fi
      if aws s3 ls "s3://$bucket/lod/$h-$k.tar" >/dev/null 2>&1; then lay+=("$h"); else miss+=("$h"); fi
    done
    [ ${#lay[@]} -eq 0 ] || "$0" restore "${lay[@]}"
    for h in "${miss[@]}"; do
      case $h in terrain) st="run prepare terrain collect" ;; object) st="run prepare texgen dyndolod collect" ;; esac
      printf '\n!!!!!!!! WARNING: no %s LOD archive for this ArgoniaWorld (%s); the machine keeps %s.\n!!!!!!!! Rebuild only that half: lod.sh %s && lod.sh archive %s\n\n' "$h" "$(key_of "$h" "$keys")" "$(key_of "$h" "$have")" "$st" "$h"
    done
    exit 0 ;;
  archive|restore)
    # archive [terrain|object ...] / restore [terrain|object ...]: per half (default both), keyed by this ESM's keys
    bucket=${ARGONIA_PRIVATE_BUCKET:-argonia-private-050977237313}
    keys=$(lodkey); tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
    mod='C:\argonia\MO2\mods\Argonia LOD (generated)'
    op=$1; shift; halves=("$@"); [ ${#halves[@]} -gt 0 ] || halves=(terrain object)
    sel() {  # a PowerShell filter on the mod's files for one half
      case $1 in terrain) echo '$_.FullName.Substring($m.Length + 1) -match "^(meshes|textures)\\terrain\\"' ;;
                 object) echo '$_.FullName.Substring($m.Length + 1) -notmatch "^(meshes|textures)\\terrain\\" -and $_.Name -ne "argonia-lod.key" -and $_.Name -ne "argonia-collect.count"' ;; esac; }
    for h in "${halves[@]}"; do
      k=$(key_of "$h" "$keys"); obj="lod/$h-$k.tar"
      if [ "$op" = archive ]; then
        # this half's file count and bytes (each file rounded to a tar block); skipped when the bucket holds it already
        read -r n bytes < <("$run" ps "\$m = '$mod'; if (Test-Path \$m) { \$f = Get-ChildItem \$m -Recurse -File | ? { $(sel "$h") }; '' + @(\$f).Count + ' ' + ((\$f | % { [math]::Ceiling(\$_.Length / 512) * 512 } | Measure-Object -Sum).Sum) } else { '0 0' }" | tr -d '\r' | tail -1)
        [ "${n:-0}" -gt 0 ] || { echo "no $h LOD in the mod on the machine (lod.sh run ...)"; exit 1; }
        if [ -z "${LOD_FORCE:-}" ] && aws s3api head-object --bucket "$bucket" --key "$obj" 2>/dev/null | "$PY" "$here/lod_skip.py" "$n" "$bytes"; then
          echo "LOD $h archived before: s3://$bucket/$obj ($n files); skipped"; continue
        fi
        "$run" ps "\$m = '$mod'; Set-Location \$m; Get-ChildItem \$m -Recurse -File | ? { $(sel "$h") } | % { \$_.FullName.Substring(\$m.Length + 1) } | Set-Content -Encoding ascii C:\argonia\logs\lod.list; tar -cf C:\argonia\logs\lod.tar -T C:\argonia\logs\lod.list" >/dev/null
        "$run" get 'C:/argonia/logs/lod.tar' "$tmp/lod.tar"
        aws s3 cp "$tmp/lod.tar" "s3://$bucket/$obj" --only-show-errors --metadata "argonia-files=$n,argonia-bytes=$bytes"
        "$run" ps 'Remove-Item C:\argonia\logs\lod.tar, C:\argonia\logs\lod.list' >/dev/null
        echo "LOD $h archived: $n files, $(du -m "$tmp/lod.tar" | cut -f1) MB, s3://$bucket/$obj"; rm -f "$tmp/lod.tar"
      else
        aws s3 cp "s3://$bucket/$obj" "$tmp/lod.tar" --only-show-errors || { echo "no s3://$bucket/$obj (lod.sh ensure names the steps)"; exit 1; }
        "$run" ps "Stop-Process -Name SkyrimSE -Force -EA SilentlyContinue; New-Item -ItemType Directory -Force C:\argonia\MO2\push | Out-Null" >/dev/null
        "$run" put "$tmp/lod.tar" C:/argonia/MO2/push/lod.tar >/dev/null; rm -f "$tmp/lod.tar"
        # only this half's files are replaced; the key file keeps the other half's key
        "$run" ps "\$m = '$mod'; New-Item -ItemType Directory -Force \$m | Out-Null; Get-ChildItem \$m -Recurse -File | ? { $(sel "$h") } | Remove-Item -Force; tar -xf C:\argonia\MO2\push\lod.tar -C \$m; Remove-Item C:\argonia\MO2\push\lod.tar; \$old = (Get-Content \"\$m\argonia-lod.key\" -EA SilentlyContinue) -join ' '; \$kv = @{}; foreach (\$p in (\$old -split ' ')) { if (\$p -match '^(terrain|object)=') { \$kv[\$p.Split('=')[0]] = \$p } }; \$kv['$h'] = '$h=$k'; Set-Content \"\$m\argonia-lod.key\" ((\$kv.Values | Sort-Object) -join ' '); 'LOD $h restored'"
      fi
    done
    [ "$op" = restore ] && "$run" ps "& C:\argonia\infra\bridge.ps1 -Cmd prepare -Fresh | Out-Null; 'profile laid'"
    exit 0 ;;
  *) sed -n '2,13p' "$0"; exit 2 ;;
esac
