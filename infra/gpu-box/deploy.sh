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
# Pre-flight before any step: the stage unpacks BM&V (26 GB) on the build VM, and a deploy that dies there costs a whole
# restart (2026-11-02, deploy-r3q); stack.py's room() is the same rule, asked first.
# 1.15 build speed: the room asked is what this stage will unpack (stack.py plan: rows whose stage key changed), so a
# deploy that re-stages nothing big runs on a full disk too; nothing to re-stage and no derived UI change skips nothing
# else (the stage's own keys and push's digests already send only changed mods).
if [ $stage = 1 ]; then
  "$PY" -c 'import sys, argparse; sys.path.insert(0, "infra/gpu-box"); import stack
a = argparse.Namespace(set=[], dev=False, through=stack.CURRENT_PART, into=None, group=None)
todo, need = stack.cmd_plan(a); stack.room(need, "deploy pre-flight (unpack " + ", ".join(m["id"] for m in todo) + ")")' || exit 3
fi
step "machine up" "$run" up
# Heartbeat (game-19's gap): idle-stop.ps1 counts the busy flag, which only commands refresh; a long single step
# (stage push, skse build) could outlast it. Touch it every 5 min while the deploy runs; stopped on exit.
# The loop's sleep is its own child: killing the loop alone left `sleep 300` holding the job's inherited gpu.lock fd
# for up to 5 min after DEPLOY OK (game-21). The TERM trap kills the sleep too; `wait` lets TERM in at once.
( trap 'kill $s 2>/dev/null; exit 0' TERM
  while :; do sleep 300 & s=$!; wait $s; "$run" ps 'hostname' >/dev/null 2>&1 || true; done ) & hb=$!
trap 'kill $hb 2>/dev/null || true' EXIT
# the game down before the push: a running game holds argonia-views open and the tar unpack fails (game-17, after uireview)
step "game down" "$run" ps 'powershell -ExecutionPolicy Bypass -File C:\argonia\infra\bridge.ps1 -Cmd kill'
# The derived UI, built from this tree's source before the stage copies it (1.11: a deploy shipped a HUD built hours
# before the redesign, because nothing rebuilt out/ui/views and worktrees linked the main tree's copy): the views
# (esbuild, seconds) and the theme overlay (the retheme recipe over the staged mods; cleared first so a dropped file goes).
if [ $stage = 1 ]; then
  # The chart's render is re-made when its source stamp changed (r4 shipped a render dated days before the terrain; the
  # sketch layer is the map's first look, owner 2026-11-03 #37); a fresh one costs a stamp check.
  step "chart" "$PY" -m tools.chart render --if-stale
  step "chart 4k" "$PY" -m tools.chart render --if-stale --level --size 4096 --out out/chart4k
  step "views" "$PY" -m tools.ui_harness.build
  step "theme" bash -c 'rm -rf out/ui_theme/argonia-theme && "$0" -m tools.ui_theme.build --mods "$HOME/.argonia/stack/MO2/mods" \
    --ttf "${ARGONIA_PRIVATE:-$HOME/argonia-private}/fonts/pelagiad/Pelagiad.ttf" --out out/ui_theme/argonia-theme' "$PY"
  step "perks" bash -c 'rm -rf out/perks/argonia-perks && "$0" -m tools.argonia_world.perk_plugin --out out/perks/argonia-perks' "$PY"
  step "stack stage" "$PY" "$here/stack.py" stage; step "stack push" "$PY" "$here/stack.py" push
fi
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
  "$run" put out/gpu/papyrus/*.pex C:/argonia/ours/scripts/ >/dev/null  # one scp, not one per file (~3 s each)
  echo "$(ls out/gpu/papyrus/*.pex | wc -l) .pex sent"
  local ps  # the machine-side helpers too: a --no-stage deploy left an old stack.ps1 there (no compass line, game-6)
  "$run" put "$here"/{stack.ps1,bridge.ps1,idle-stop.ps1,spot-watch.ps1,stream-activity.ps1,saves-sync.ps1,vanilla-data-files.txt} C:/argonia/infra/ >/dev/null
  # the pool's saves (1.8 §7): pulled at boot, pushed every 5 minutes; registered here so every standby has them
  "$run" ps '$r="C:\argonia\infra\saves-sync.ps1"
if (-not (Get-ScheduledTask -TaskName argonia-saves-pull -EA SilentlyContinue)) { Register-ScheduledTask -TaskName argonia-saves-pull -Action (New-ScheduledTaskAction -Execute powershell.exe -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File $r pull") -Trigger (New-ScheduledTaskTrigger -AtStartup) -User SYSTEM -RunLevel Highest | Out-Null }
if (-not (Get-ScheduledTask -TaskName argonia-saves-push -EA SilentlyContinue)) { Register-ScheduledTask -TaskName argonia-saves-push -Action (New-ScheduledTaskAction -Execute powershell.exe -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File $r push") -Trigger (New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(5) -RepetitionInterval (New-TimeSpan -Minutes 5)) -User SYSTEM -RunLevel Highest | Out-Null }' >/dev/null
  # Moonlight's cards (owner, 2026-10-31: a machine from an old image still listed vanilla and souls-like): the
  # repo's apps.json and cards laid each deploy; Sunshine reads apps.json when a client asks for the list.
  "$run" put "$here"/{sunshine-apps.json,make-cards.ps1} C:/argonia/infra/ >/dev/null
  # Sunshine reads apps.json only at its start (game-21: the old list stayed until a restart), so a changed list
  # restarts it; an unchanged one leaves a live stream alone.
  "$run" ps "& C:\\argonia\\infra\\make-cards.ps1; \$a='C:\\Program Files\\Sunshine\\config\\apps.json'; \$n='C:\\argonia\\infra\\sunshine-apps.json'; if ((Get-FileHash \$n).Hash -ne (Get-FileHash \$a -EA SilentlyContinue).Hash) { Copy-Item \$n \$a -Force; Restart-Service SunshineService; 'sunshine: app list changed, restarted' } else { 'sunshine: app list unchanged' }"
}
send_scenes() {  # after the launch: a ref is named by its runtime id, the plugin's prefix read from the game (game-7)
  rm -rf out/scenes; "$PY" tools/ref_ids.py render out/scenes
  "$run" put out/scenes/*.txt "C:/Program Files (x86)/Steam/steamapps/common/Skyrim Special Edition/" >/dev/null  # one scp: 31 puts took 98 s
  echo "$(ls out/scenes/*.txt | wc -l) scenes sent"
}
step "send ESMs and helpers" send_esms
# The ground's derived textures (decision 0014; lane 1.15-r6-ground-roads): BM&V's diffuses with mips and normals at
# Skyrim.esm's own tilt and specular alpha, made here from the stack's BM&V (`terrain derive-textures`, --dry-run lists
# them), sent to ours\derived\argonia-ground; stack.ps1 on lays every ours\derived\<name> over the mods (the TXSTs
# in Argonia.esm name them). Other derived folders take the same road (one folder per tool).
ground_textures() {
  local d=out/derived/argonia-ground/textures/argonia/landscape m='C:\argonia\ours\derived\argonia-ground'
  "$PY" -m tools.argonia_world.terrain derive-textures | tail -1 || return 1
  "$run" ps "Remove-Item $m -Recurse -Force -EA SilentlyContinue; New-Item -ItemType Directory -Force $m\textures\argonia\landscape | Out-Null" >/dev/null
  "$run" put "$d"/*.dds C:/argonia/ours/derived/argonia-ground/textures/argonia/landscape/ >/dev/null  # one scp
  echo "$(ls "$d"/*.dds | wc -l) derived ground textures sent"
}
step "ground textures" ground_textures
step "lod" "$here/lod.sh" ensure   # nothing lives only on a machine: the archived LOD for this ArgoniaWorld
# The pad layout follows controlmap.py on every machine (b112b: argonia-play kept Select = Journal, so the pad's Select
# opened the journal, not Wait): the machine's made controlmap.txt fetched, GAMEPLAY re-applied, sent back; the launch's
# prepare lays it in Data (stack.ps1). No file there (a machine set up before controlmap.py) is left to setup.
controls() {
  local t; t=$(mktemp -d)
  if "$run" get 'C:/argonia/controls/controlmap.txt' "$t/was.txt" 2>/dev/null; then
    "$PY" "$here/controlmap.py" --remap "$t/was.txt" "$t/controlmap.txt" && "$run" put "$t/controlmap.txt" 'C:/argonia/controls/controlmap.txt'
  else echo "controls: no C:\argonia\controls\controlmap.txt on the machine; setup makes it"; fi
  rm -rf "$t"
}
step "controls" controls
# Community Shaders' compiled cache by its key (1.15-r4-fast-loop): laid from the archive on a machine without it, so
# only a real shader change compiles (~11 min); archived after the launch that compiled it. Never fails the deploy.
step "shader cache" bash -c '"$0" ensure || echo "shader cache: ensure failed; the launch compiles"' "$here/shader_cache.sh"
step "launch" "$PY" tools/bridge.py launch --fresh
step "shader cache save" bash -c '"$0" save || echo "shader cache: save failed (next deploy retries)"' "$here/shader_cache.sh"
step "send scenes" send_scenes
[ $base = 1 ] && { step "base save" "$PY" "$here/base_save.py" || { echo "base save: retry once (a first boot or shader warm-up can miss the 3 s main-thread window; game-20, game-21)"; step "base save (retry)" "$PY" "$here/base_save.py"; }; }
# the pool keeps one build (1.8 §7): tag what this machine now runs, so the play page and pool.py know who is behind
"$PY" "$here/pool.py" stamp "${ARGONIA_PLAY:-argonia-play}" || echo "pool stamp failed (the play page may treat this machine as behind)" >&2
echo "DEPLOY OK in $(( SECONDS - t0 )) s"
