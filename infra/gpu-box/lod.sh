#!/usr/bin/env bash
# The LOD job for ARG_Province (2.W4 §c, decision 0014 §4), driven from the build VM; lod.ps1 is the machine's half.
#   lod.sh tools                       the three tool rows (xlodgen, dyndolod, dyndolod-resources in
#                                      data/dependencies.json) fetched, hash-checked, unpacked and laid under
#                                      C:\argonia\tools\<id> (never Data; sent again only when the archive changed)
#   lod.sh survey xlodgen|texgen|dyndolod   start one tool in the desktop session, dump its windows, kill it
#   lod.sh run [step ...]              prepare terrain texgen dyndolod collect (default: all, in that order)
#   lod.sh still <tag>                 the vantage still: the game launched on the laid profile, the base save, the
#                                      highest ground within 8 cells of Claywater (cell -53,3, 440 m; the LAND shards),
#                                      facing north-west over Claywater at noon, after 30 s -> out/lod/vantage-<tag>.png
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

ps1() {  # one lod.ps1 step; the GUI steps in the desktop session, the rest over SSH
  local step=$1; shift
  local line="powershell -ExecutionPolicy Bypass -File C:\\argonia\\infra\\lod.ps1 -Step $step -Preset ${PRESET:-Medium} $*"
  local t0=$SECONDS out
  case "$step" in
    terrain|texgen|dyndolod|survey) out=$(DESKTOP_WAIT=${DESKTOP_WAIT:-14400} "$run" desktop "$line") ;;
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

case "${1:-}" in tools|survey|run|still) ;; *) sed -n "2,10p" "$0"; exit 2 ;; esac
"$run" ps 'New-Item -ItemType Directory -Force C:\argonia\infra, C:\argonia\tools | Out-Null' >/dev/null
"$run" put "$here/lod.ps1" C:/argonia/infra/lod.ps1 >/dev/null
case "${1:-}" in
  tools) tools ;;
  survey) [ -n "${2:-}" ] || { sed -n '2,10p' "$0"; exit 2; }; DESKTOP_WAIT=400 ps1 survey -Tool "$2"; fetch_back ;;
  run)
    shift; steps=("$@"); [ ${#steps[@]} -gt 0 ] || steps=(prepare terrain texgen dyndolod collect)
    tools
    for s in "${steps[@]}"; do ps1 "$s"; done
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
  *) sed -n '2,13p' "$0"; exit 2 ;;
esac
