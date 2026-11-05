#!/usr/bin/env bash
# Argonia.esp from plugin/Argonia (Spriggit YAML is the source; decision 0018).
#   plugin.sh build    plugin/Argonia -> out/Argonia.esp (Spriggit deserialize)
#   plugin.sh check    build, then serialize it back and diff with plugin/Argonia (round trip clean), then read the
#                      ESP back (tools/ArgoniaPlugin list): every override carries its change; writes the records table
#   plugin.sh seed     regenerate plugin/Argonia from shutdown.json and the load order's winners (game data needed:
#                      $ARGONIA_GAME_ROOT/Data or ~/games/skyrimse/Data, the staged profile ~/.argonia/stack/MO2)
set -euo pipefail
repo=$(cd "$(dirname "$0")/../.." && pwd); cd "$repo"
export DOTNET_ROOT="$HOME/.dotnet" PATH="$HOME/.dotnet:$PATH" DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
spriggit=("$HOME/.argonia/spriggit/0.41.0/Spriggit.CLI")  # pinned in infra/build-vm/toolchain.lock
spr=(-p Spriggit.Yaml -v 0.41.0)
yaml=plugin/Argonia; esp=out/Argonia.esp; bin=out/tools/ArgoniaPlugin
tool() { dotnet build -c Release -o "$bin" tools/ArgoniaPlugin >/dev/null && dotnet "$bin/ArgoniaPlugin.dll" "$@"; }
build() { mkdir -p out; "${spriggit[@]}" deserialize -i "$yaml" -o "$esp" "${spr[@]}" >/dev/null; echo "built $esp ($(stat -c %s "$esp") bytes)"; }
loadorder() {  # the staged profile's plugins after the game's, as stack.py lays them
  local data="${ARGONIA_GAME_ROOT:-$HOME/games/skyrimse}/Data" mo2="$HOME/.argonia/stack/MO2" p f c
  lo=("$data"/{Skyrim,Update,Dawnguard,HearthFires,Dragonborn}.esm)
  for c in ccBGSSSE001-Fish.esm ccQDRSSE001-SurvivalMode.esl ccBGSSSE037-Curios.esl ccBGSSSE025-AdvDSGS.esm _ResourcePack.esl; do
    [ -f "$data/$c" ] && lo+=("$data/$c"); done
  while read -r p; do p=${p#\*}; [ -n "$p" ] || continue
    f=$(compgen -G "$mo2/mods/*/$p" | head -1) || true; [ -n "$f" ] || { echo "not staged: $p" >&2; exit 1; }; lo+=("$f")
  done < <(tr -d '\r' < "$mo2/profiles/Argonia/plugins.txt" | grep -v -i '^\*\?argonia\.esp$')
}
case "${1:-}" in
  build) build ;;
  check)
    build
    rt=$(mktemp -d); trap 'rm -rf "$rt"' EXIT
    "${spriggit[@]}" serialize -i "$esp" -o "$rt/y" -g SkyrimSE "${spr[@]}" >/dev/null
    diff -r "$yaml" "$rt/y" && echo "round trip clean: $(find "$yaml" -name '*.yaml' | wc -l) yaml files"
    lo=(); [ -d "$HOME/.argonia/stack/MO2" ] && loadorder  # the winners comparison needs the game data
    tool list "$esp" docs/research/skyrim/argonia-esp-records.md "${lo[@]}" ;;
  seed)
    loadorder
    tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
    tool seed "$tmp/Argonia.esp" "${lo[@]}"
    "${spriggit[@]}" serialize -i "$tmp/Argonia.esp" -o "$tmp/y" -g SkyrimSE "${spr[@]}" >/dev/null
    rm -rf "$yaml"; mkdir -p plugin; mv "$tmp/y" "$yaml"; echo "seeded $yaml" ;;
  *) sed -n '2,8p' "$0"; exit 2 ;;
esac
