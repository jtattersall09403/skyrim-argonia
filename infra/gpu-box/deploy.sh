#!/usr/bin/env bash
# make deploy (chunk 0.3 §e): our build onto the game machine, the game restarted, the base save rebuilt.
#   deploy.sh [--no-plugin] [--no-papyrus] [--no-skse] [--no-stage] [--no-base]      run: `make plugin` first, outside the lock (an unchanged build is skipped by its input hash), then
#   tooling/job_guard.sh run --gpu <name> -- make deploy  (step 1 then hits the skip: the machine never idles on a plugin build)
#   From a fresh worktree, make it with `tooling/worktree.sh <path>`: it links the main tree's build inputs (out/navmesh,
#   out/terrain, ... are untracked; without them the plugin drops the province navmesh and rewrites committed YAML).
# 1. make plugin: out/Argonia.esm and out/ArgoniaWorld.esm (skipped with --no-plugin);
# 1b. records_jobs.sh papyrus: every .psc we have compiled with the CK's compiler into out/gpu/papyrus (--no-papyrus
#    lays the last compile);
# 2. stack.py stage + push: the profile with the db's mod settings and the deferred rows our ESMs master;
# 3. the game killed, then skse_build.sh: ArgoniaCore.dll and ArgoniaBridge.dll built with MSVC into MO2;
# 4. the ESMs to C:\argonia\ours (sent only when their hash changed), the .pex to C:\argonia\ours\scripts;
# 5. bridge.py launch --fresh: the profile laid again, our DLLs and ESMs copied in (bridge.ps1 prepare), main menu;
#    then the scenes (tests/scenes/*.txt, refs as runtime ids by tools/ref_ids.py) to the game's folder for `bat <id>`;
# 6. base_save.py: a new game, the quarantine start, the studio character in the holding cell, saved as argoniabase.
# Every step prints its seconds; the last line is DEPLOY OK.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd); repo=$(cd "$here/../.." && pwd); cd "$repo"
PY=$(ls "$HOME/.argonia/venv/bin/python" 2>/dev/null || command -v python3)
plugin=1 papyrus=1 skse=1 stage=1 base=1
for a in "$@"; do case "$a" in --no-plugin) plugin=0 ;; --no-papyrus) papyrus=0 ;; --no-skse) skse=0 ;; --no-stage) stage=0 ;; --no-base) base=0 ;;
  *) sed -n '2,10p' "$0"; exit 2 ;; esac; done
run="$here/run.sh"; t0=$SECONDS
step() { local s=$SECONDS; echo "== $1"; shift; "$@"; echo "== $(( SECONDS - s )) s"; }

[ $plugin = 1 ] && step "make plugin" make --no-print-directory plugin
for f in Argonia.esm ArgoniaWorld.esm; do [ -f "out/$f" ] || { echo "no out/$f: make plugin first" >&2; exit 1; }; done
# A province without NAVM is a province where no one walks (game-8: every deploy since 2.W4 shipped none).
"$PY" -c 'import sys; n = open("out/ArgoniaWorld.esm", "rb").read().count(b"NAVM"); print(f"ArgoniaWorld.esm: {n} NAVM"); sys.exit(n == 0)' \
  || [ "${ARGONIA_NO_NAVMESH:-}" = 1 ] || { echo "out/ArgoniaWorld.esm has no navmesh: make navmesh (or ARGONIA_NO_NAVMESH=1)" >&2; exit 1; }
step "machine up" "$run" up
# Heartbeat (game-19's gap): idle-stop.ps1 counts the busy flag, which only commands refresh; a long single step
# (stage push, skse build) could outlast it. Touch it every 5 min while the deploy runs; stopped on exit.
( while sleep 300; do "$run" ps 'hostname' >/dev/null 2>&1 || true; done ) & hb=$!
trap 'kill $hb 2>/dev/null || true' EXIT
# the game down before the push: a running game holds argonia-views open and the tar unpack fails (game-17, after uireview)
step "game down" "$run" ps 'powershell -ExecutionPolicy Bypass -File C:\argonia\infra\bridge.ps1 -Cmd kill'
if [ $stage = 1 ]; then step "stack stage" "$PY" "$here/stack.py" stage; step "stack push" "$PY" "$here/stack.py" push; fi
if [ $papyrus = 1 ]; then step "papyrus" "$here/records_jobs.sh" papyrus; fi
ls out/gpu/papyrus/*.pex >/dev/null 2>&1 || { echo "no out/gpu/papyrus/*.pex: records_jobs.sh papyrus" >&2; exit 1; }
step "game down" "$run" ps 'powershell -ExecutionPolicy Bypass -File C:\argonia\infra\bridge.ps1 -Cmd kill'
if [ $skse = 1 ]; then
  # unchanged skse/ (clean tree, stamp and both DLLs on the machine) skips the 124 s build; tools/skse_stamp.py decides
  skse_tree=$(git rev-parse HEAD:skse); skse_dirty=0; [ -z "$(git status --porcelain -- skse)" ] || skse_dirty=1
  probe=$("$run" ps 'foreach($n in "ArgoniaCore.dll","ArgoniaBridge.dll"){ if(Get-ChildItem C:\argonia\skse\out\windows-dev -Recurse -Filter $n -ErrorAction SilentlyContinue){"dll=$n"} }; $s="C:\argonia\skse\out\windows-dev\skse.stamp"; if(Test-Path $s){"stamp=" + (Get-Content $s -Raw).Trim()}' 2>/dev/null || true)
  if "$PY" "$repo/tools/skse_stamp.py" "$skse_tree" windows-dev "$skse_dirty" <<<"$probe"; then
    echo "skse build: unchanged ($skse_tree)"
  else
    step "skse build" "$here/skse_build.sh" --worktree build windows-dev
  fi
fi

send_esms() {
  "$run" ps 'New-Item -ItemType Directory -Force C:\argonia\ours | Out-Null' >/dev/null
  for f in Argonia.esm ArgoniaWorld.esm; do
    local want have
    want=$(sha256sum "out/$f" | cut -c1-64)
    have=$("$run" ps "if (Test-Path C:\\argonia\\ours\\$f) { (Get-FileHash C:\\argonia\\ours\\$f).Hash.ToLower() }" | tr -d '\r\n')
    if [ "$want" = "$have" ]; then echo "$f unchanged"; else "$run" put "out/$f" "C:/argonia/ours/$f" >/dev/null; echo "$f sent ($want)"; fi
  done
  # Our compiled Papyrus (game-9): bridge.ps1 prepare copies them into Data\Scripts.
  "$run" ps 'Remove-Item C:\argonia\ours\scripts -Recurse -Force -EA SilentlyContinue; New-Item -ItemType Directory -Force C:\argonia\ours\scripts | Out-Null' >/dev/null
  local pex; for pex in out/gpu/papyrus/*.pex; do "$run" put "$pex" C:/argonia/ours/scripts/ >/dev/null; done
  echo "$(ls out/gpu/papyrus/*.pex | wc -l) .pex sent"
  local ps  # the machine-side helpers too: a --no-stage deploy left an old stack.ps1 there (no compass line, game-6)
  for ps in stack.ps1 bridge.ps1 vanilla-data-files.txt; do "$run" put "$here/$ps" "C:/argonia/infra/$ps" >/dev/null; done
}
send_scenes() {  # after the launch: a ref is named by its runtime id, the plugin's prefix read from the game (game-7)
  rm -rf out/scenes; "$PY" tools/ref_ids.py render out/scenes
  local sc
  for sc in out/scenes/*.txt; do
    "$run" put "$sc" "C:/Program Files (x86)/Steam/steamapps/common/Skyrim Special Edition/$(basename "$sc")" >/dev/null
  done
  echo "$(ls out/scenes/*.txt | wc -l) scenes sent"
}
step "send ESMs and helpers" send_esms
step "launch" "$PY" tools/bridge.py launch --fresh
step "send scenes" send_scenes
[ $base = 1 ] && step "base save" "$PY" "$here/base_save.py"
echo "DEPLOY OK in $(( SECONDS - t0 )) s"
