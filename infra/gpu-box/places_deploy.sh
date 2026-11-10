#!/usr/bin/env bash
# The place layer onto the game machine's NewWorld profile (docs/design/place-studio.md, Build): the plugin
# out/places/plugin/ArgoniaNWPlaces.esp (over ArgoniaNewWorld.esm, which lod.sh send lays), its SEQ file (the boatman's
# dialogue quest is Start Game Enabled: the engine starts the quests a SEQ lists before a new game's first frame, as
# Argonia.seq does for Argonia.esp) and the compiled scripts it names (TIF_ARG_BoatTravel.pex, TIF_ARG_NoSurrender.pex, compiled with the rest
# of papyrus/ by records_jobs.sh papyrus into out/gpu/papyrus), then stack.ps1 -World NewWorld on.
#   places_deploy.sh [--dry-run]   --dry-run: check and stage only (the SEQ built, every file named), nothing sent
# Refuses a plugin built over another world ESM than out/newworld/plugin's, or a place whose check read another
# build (PLACES_FORCE=1 overrides). Rerunnable: every file is replaced, nothing else is touched.
#   C:\argonia\ours\newworld\ArgoniaNWPlaces.esp   stack.ps1's NewWorld ours plugins (after ArgoniaNewWorld.esm)
#   C:\argonia\ours\newworld\SEQ\ArgoniaNWPlaces.seq  laid into Data\SEQ in the NewWorld profile only
#   C:\argonia\ours\scripts\TIF_ARG_*.pex  laid into Data\Scripts (deploy.sh sends all of out/gpu/papyrus too)
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd); repo=$(cd "$here/../.." && pwd); cd "$repo"
dry=0
for a in "$@"; do case "$a" in --dry-run) dry=1 ;; *) sed -n '2,13p' "$0"; exit 2 ;; esac; done
esp=out/places/plugin/ArgoniaNWPlaces.esp; esm=out/newworld/plugin/ArgoniaNewWorld.esm
seq=out/places/plugin/SEQ/ArgoniaNWPlaces.seq; pex=(out/gpu/papyrus/TIF_ARG_BoatTravel.pex out/gpu/papyrus/TIF_ARG_NoSurrender.pex)
[ -f "$esp" ] || { echo "no $esp: run python -m tools.places build" >&2; exit 1; }
for p in "${pex[@]}"; do [ -f "$p" ] || { echo "no $p: run infra/gpu-box/records_jobs.sh papyrus" >&2; exit 1; }; done
python3 - "$esm" "$esp" <<'PY' || [ -n "${PLACES_FORCE:-}" ]
import hashlib, json, sys
from pathlib import Path
esm, esp = Path(sys.argv[1]), Path(sys.argv[2])
b = json.loads((esp.parent / "build.json").read_text())
bad = []
if b.get("world_sha256") != hashlib.sha256(esm.read_bytes()).hexdigest():
    bad.append(f"{esp.name} was built over another {esm.name}: rebuild it")
for pid in sorted(b.get("places") or {}):
    c = Path("out/places/shards") / pid / "check.json"
    r = json.loads(c.read_text()) if c.exists() else {}
    if r.get("esp_sha256") != b.get("esp_sha256"):
        bad.append(f"{pid}: its check did not read this build: python -m tools.places check {pid}")
    else:
        red = [f"{k} {v['n']}" for k, v in sorted(r["results"].items()) if not v["ok"]]
        print(f"{pid}: {len(r['results']) - len(red)}/{len(r['results'])} checks green" + (f" (red: {', '.join(red)})" if red else ""))
if bad:
    print("\n".join(bad))
sys.exit(1 if bad else 0)
PY
export DOTNET_ROOT="$HOME/.dotnet" PATH="$HOME/.dotnet:$PATH" DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
bin=out/tools/ArgoniaPlugin
dotnet build -c Release -o "$bin" tools/ArgoniaPlugin >/dev/null
dotnet "$bin/ArgoniaPlugin.dll" seq "$esp" "$seq" || { echo "no start-game quest in $esp: no SEQ needed"; rm -f "$seq"; }
echo "stage: $esp ($(stat -c %s "$esp") bytes), ${seq} ($( [ -f "$seq" ] && stat -c %s "$seq" || echo none)), ${pex[*]}"
[ $dry = 1 ] && { echo "dry run: nothing sent"; exit 0; }
run="$here/run.sh"
"$run" up
"$run" ps 'New-Item -ItemType Directory -Force C:\argonia\ours\newworld\SEQ, C:\argonia\ours\scripts, C:\argonia\infra | Out-Null' >/dev/null
"$run" put "$esp" C:/argonia/ours/newworld/ArgoniaNWPlaces.esp >/dev/null
"$run" ps 'Remove-Item C:\argonia\ours\newworld\SEQ\*.seq -Force -EA SilentlyContinue' >/dev/null
[ -f "$seq" ] && "$run" put "$seq" C:/argonia/ours/newworld/SEQ/ >/dev/null
"$run" put "${pex[@]}" C:/argonia/ours/scripts/ >/dev/null
"$run" put "$here/stack.ps1" C:/argonia/infra/ >/dev/null
"$run" ps 'powershell -ExecutionPolicy Bypass -File C:\argonia\infra\stack.ps1 -World NewWorld on; if ($LASTEXITCODE) { exit $LASTEXITCODE }'
echo "PLACES DEPLOY OK"
