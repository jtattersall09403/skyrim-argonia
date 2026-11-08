#!/usr/bin/env bash
# Argonia.esp from plugin/Argonia (Spriggit YAML is the source; decision 0018).
#   plugin.sh build    plugin/Argonia -> out/Argonia.esp (Spriggit deserialize, then the conditions fixup, which
#                      needs the game data and staged profile), plugin/Argonia.ini -> out/Argonia.ini
#   plugin.sh check    build, then serialize it back and diff with plugin/Argonia (round trip clean), then read the
#                      ESP back (tools/ArgoniaPlugin list): every override carries its change; writes the records table
#   plugin.sh blocktest  build, then Phase 3's agent check of ARG_BlockTest from the ESP and out/gpu/papyrus (the .pex)
#   plugin.sh mqcheck  build, then the read-back of MQ04 and MQ05 from the ESP and out/gpu/papyrus against the record (MQCheck.cs)
#   plugin.sh cleancheck  build, then read the slice's clean-ups back from the ESP (CleanUp.cs)
#   plugin.sh bccheck  build, then read the Chainbreakers quests back from the ESP and the .pex (ChainbreakersCheck.cs)
#   plugin.sh seed     regenerate plugin/Argonia from shutdown.json and the load order's winners (game data needed:
#                      $ARGONIA_GAME_ROOT/Data or ~/games/skyrimse/Data, the staged profile ~/.argonia/stack/MO2)
set -euo pipefail
repo=$(cd "$(dirname "$0")/../.." && pwd); cd "$repo"
export DOTNET_ROOT="$HOME/.dotnet" PATH="$HOME/.dotnet:$PATH" DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
spriggit=("$HOME/.argonia/spriggit/0.41.0/Spriggit.CLI")  # pinned in infra/build-vm/toolchain.lock
spr=(-p Spriggit.Yaml -v 0.41.0)
yaml=plugin/Argonia; esp=out/Argonia.esp; bin=out/tools/ArgoniaPlugin
tool() { dotnet build -c Release -o "$bin" tools/ArgoniaPlugin >/dev/null && dotnet "$bin/ArgoniaPlugin.dll" "$@"; }
build() {
  mkdir -p out; "${spriggit[@]}" deserialize -i "$yaml" -o "$esp" "${spr[@]}" >/dev/null
  loadorder; tool fixup "$esp" "${lo[@]}"  # the conditions Spriggit's YAML cannot carry (shutdown.json)
  cp plugin/Argonia.ini out/Argonia.ini      # the plugin's own ini, loaded beside it
  echo "built $esp ($(stat -c %s "$esp") bytes) and out/Argonia.ini"
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
  mapprobe) loadorder; tool mapprobe "${lo[@]}" ;;
  cleancheck) build; tool cleancheck "$esp" "${lo[@]}" ;;
  musicprobe) loadorder; tool musicprobe "${lo[@]}" ;;
  blocktest) build; tool blocktest "$esp" out/gpu/papyrus "${lo[@]}" ;;
  localcheck) build; tool localcheck "$esp" out/gpu/papyrus "${lo[@]}" ;;
  bccheck) build; tool bccheck "$esp" out/gpu/papyrus "${lo[@]}" ;;
  mqcheck) build; tool mqcheck "$esp" out/gpu/papyrus "${lo[@]}" ;;
  seed)
    loadorder
    tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
    tool seed "$tmp/Argonia.esp" "${lo[@]}"
    "${spriggit[@]}" serialize -i "$tmp/Argonia.esp" -o "$tmp/y" -g SkyrimSE "${spr[@]}" >/dev/null
    rm -rf "$yaml"; mkdir -p plugin; mv "$tmp/y" "$yaml"; echo "seeded $yaml" ;;
  *) sed -n '2,10p' "$0"; exit 2 ;;
esac
