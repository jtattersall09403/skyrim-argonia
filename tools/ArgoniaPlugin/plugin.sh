#!/usr/bin/env bash
# Argonia.esp from plugin/Argonia (Spriggit YAML is the source; decision 0018).
#   plugin.sh build    plugin/Argonia -> out/Argonia.esp (Spriggit deserialize, then the conditions fixup, which
#                      needs the game data and staged profile), plugin/Argonia.ini -> out/Argonia.ini
#   plugin.sh check    build, then serialize it back and diff with plugin/Argonia (round trip clean), then read the
#                      ESP back (tools/ArgoniaPlugin list): every override carries its change; writes the records table
#   plugin.sh mqcheck  build, then the read-back of MQ04 and MQ05 from the ESP and out/gpu/papyrus against the record (MQCheck.cs)
#   plugin.sh cleancheck  build, then read the slice's clean-ups back from the ESP (CleanUp.cs)
#   plugin.sh bccheck  build, then read the Chainbreakers quests back from the ESP and the .pex (ChainbreakersCheck.cs)
#   plugin.sh nightreedcheck  build, then read TG01/TG02 back from the ESP and the .pex (NightReedCheck.cs)
#   plugin.sh questcheck  build, then ask of every ARG_ quest whether it can happen: walks, starts, shapes, reachable stages,
#                      endings, zones, people, offers, doors (QuestCheck.cs; --selftest runs its rules on hand-made models)
#   plugin.sh placecheck build, then check every actor and object the plugin places against the winning navmesh, the
#                      surface under it and the statics round it (PlaceCheck.cs)
#   plugin.sh questform-read <dir>  build, then turn every quest of ours built from a quest form back into its form,
#                      from the ESP alone (QuestFormRead.cs): <dir>/<quest id>.json
#   plugin.sh questform-test  the generic builder end to end, off game: the block test's forms and the example opening's
#                      pier copy (tools/tests/data/questform) seeded into a scratch plugin, read back, compared with the
#                      forms (apart from resolved positions), the read-back forms checked, questcheck run on it
#   plugin.sh seed     regenerate plugin/Argonia from shutdown.json, the load order's winners and the quest forms (every
#                      quest record that fits, compiled fresh to out/questform, and tools/questform/blocktest); game data
#                      needed: $ARGONIA_GAME_ROOT/Data or ~/games/skyrimse/Data, the staged profile ~/.argonia/stack/MO2
set -euo pipefail
repo=$(cd "$(dirname "$0")/../.." && pwd); cd "$repo"
export DOTNET_ROOT="$HOME/.dotnet" PATH="$HOME/.dotnet:$PATH" DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
spriggit=("$HOME/.argonia/spriggit/0.41.0/Spriggit.CLI")  # pinned in infra/build-vm/toolchain.lock
spr=(-p Spriggit.Yaml -v 0.41.0)
yaml=plugin/Argonia; esp=out/Argonia.esp; bin=out/tools/ArgoniaPlugin
py=$(ls "$HOME/.argonia/venv/bin/python" 2>/dev/null || echo python3)
forms() { rm -rf out/questform; "$py" -m tools.questform compile --all --out out/questform --owed-ok >/dev/null; }  # every record that fits
tool() { mkdir -p "$HOME/.argonia"; flock -o "$HOME/.argonia/dotnet-build.lock" dotnet build -c Release -o "$bin" tools/ArgoniaPlugin >/dev/null && dotnet "$bin/ArgoniaPlugin.dll" "$@"; }
build() {
  mkdir -p out; "${spriggit[@]}" deserialize -i "$yaml" -o "$esp" "${spr[@]}" >/dev/null
  loadorder; tool fixup "$esp" "${lo[@]}"  # the conditions Spriggit's YAML cannot carry (shutdown.json)
  cp plugin/Argonia.ini out/Argonia.ini      # the plugin's own ini, loaded beside it
  tool seq "$esp" out/SEQ/Argonia.seq        # its start-game quests, started before a new game's first frame (Seq.cs)
  echo "built $esp ($(stat -c %s "$esp") bytes), out/Argonia.ini and out/SEQ/Argonia.seq"
}
loadorder() {  # the staged profile's plugins after the game's, as stack.py lays them
  local data="${ARGONIA_GAME_ROOT:-$HOME/games/skyrimse}/Data" mo2="$HOME/.argonia/stack/MO2" p f c
  lo=("$data"/{Skyrim,Update,Dawnguard,HearthFires,Dragonborn}.esm)
  for c in ccBGSSSE001-Fish.esm ccQDRSSE001-SurvivalMode.esl ccBGSSSE037-Curios.esl ccBGSSSE025-AdvDSGS.esm _ResourcePack.esl; do
    [ -f "$data/$c" ] && lo+=("$data/$c"); done
  while read -r p; do p=${p#\*}; [ -n "$p" ] || continue
    # the copy that wins in MO2: modlist.txt lists the highest priority first (rim-parry-ctd-fix's
    # RimExecutionHitSA.esp over rim-parry's; a glob took the alphabetical first)
    f=""; while read -r m; do [ -f "$mo2/mods/$m/$p" ] && { f="$mo2/mods/$m/$p"; break; }; done < <(tr -d '\r' < "$mo2/profiles/Argonia/modlist.txt" | sed -n 's/^+//p')
    [ -n "$f" ] || { echo "not staged: $p" >&2; exit 1; }; lo+=("$f")
  done < <(tr -d '\r' < "$mo2/profiles/Argonia/plugins.txt" | grep -v -i '^\*\?argonia\.esp$')
}
case "${1:-}" in
  build) build ;;
  check)
    build
    rt=$(mktemp -d); trap 'rm -rf "$rt"' EXIT
    "${spriggit[@]}" serialize -i "$esp" -o "$rt/y" -g SkyrimSE "${spr[@]}" >/dev/null
    diff -r "$yaml" "$rt/y" && echo "round trip clean: $(find "$yaml" -name '*.yaml' | wc -l) yaml files"
    tool list "$esp" docs/research/skyrim/argonia-esp-records.md "${lo[@]}" ;;
  surface) loadorder; tool surface "$2" "$3" "${lo[@]}" ;;
  mapprobe) loadorder; tool mapprobe "${lo[@]}" ;;
  cleancheck) build; tool cleancheck "$esp" "${lo[@]}" ;;
  inspect) loadorder; [ -f "$esp" ] && lo+=("$esp"); tool inspect "$2" "${lo[@]}" ;;  # the load order, our built ESP last
  musicprobe) loadorder; tool musicprobe "${lo[@]}" ;;
  localcheck) build; tool localcheck "$esp" out/gpu/papyrus "${lo[@]}" ;;
  bccheck) build; tool bccheck "$esp" out/gpu/papyrus "${lo[@]}" ;;
  mqcheck) build; tool mqcheck "$esp" out/gpu/papyrus "${lo[@]}" ;;
  questcheck) build; tool questcheck "$esp" papyrus "${lo[@]}" ;;
  nightreedcheck) build; tool nightreedcheck "$esp" out/gpu/papyrus "${lo[@]}" ;;
  placecheck) build; tool placecheck "$esp" "${lo[@]}" ;;
  questform-read) build; tool questform-read "$esp" "$2" "${lo[@]}" ;;
  questform-test)
    loadorder
    tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
    cp plugin/questform-formids.json "$tmp/ids.json"
    QUESTFORM_DIRS=tools/questform/blocktest:tools/tests/data/questform QUESTFORM_IDS="$tmp/ids.json" tool seed "$tmp/Argonia.esp" "${lo[@]}" | grep -E "^questform|^mortality"
    tool questform-read "$tmp/Argonia.esp" "$tmp/read" "${lo[@]}"
    for f in tools/questform/blocktest/*.json tools/tests/data/questform/*.json; do "$py" -m tools.questform diff "$f" "$tmp/read/$("$py" -c "import json,sys; print(json.load(open(sys.argv[1]))[\"quest\"][\"id\"])" "$f").json"; done
    "$py" -m tools.questform check "$tmp"/read/*.json
    tool questcheck "$tmp/Argonia.esp" papyrus "${lo[@]}" | tail -3 ;;
  seed)
    forms; loadorder
    tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
    tool seed "$tmp/Argonia.esp" "${lo[@]}"
    "${spriggit[@]}" serialize -i "$tmp/Argonia.esp" -o "$tmp/y" -g SkyrimSE "${spr[@]}" >/dev/null
    rm -rf "$yaml"; mkdir -p plugin; mv "$tmp/y" "$yaml"; echo "seeded $yaml" ;;
  *) sed -n '2,10p' "$0"; exit 2 ;;
esac
