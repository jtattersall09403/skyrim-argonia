#!/usr/bin/env bash
# Idempotent build-VM toolchain (decision 0011: tools added at first use). Pins and hashes: toolchain.lock.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCK="$HERE/toolchain.lock"
VENV="$HOME/.argonia/venv"
export PATH="$HOME/.dotnet:$HOME/.dotnet/tools:$HOME/.local/bin:$PATH"
export DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1

ver() { grep -E "^$1=" "$LOCK" | head -1 | sed -E 's/^[^=]+=([^ ]+).*/\1/'; }
sha() { grep -E "^$1=" "$LOCK" | head -1 | sed -E 's/.*sha256=([0-9a-f]+).*/\1/'; }
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT

# apt basics
need=(); for p in jq tmux tree unzip; do command -v "$p" >/dev/null || need+=("$p"); done
if [ ${#need[@]} -gt 0 ]; then sudo apt-get update -qq && sudo apt-get install -y -qq "${need[@]}"; fi

# python venv
if [ ! -x "$VENV/bin/python" ]; then python3 -m venv "$VENV"; fi
pins=(); while IFS= read -r l; do n="${l#py:}"; n="${n%%=*}"; pins+=("$n==$(ver "py:$n")"); done < <(grep '^py:' "$LOCK")
# every py: pin in the lock (pillow, pyyaml, ruff included) is installed; the dry run says whether any is missing or off-version
if [ -n "$("$VENV/bin/pip" install --dry-run -q "${pins[@]}" 2>&1 | grep -i 'would install' || true)" ]; then
  "$VENV/bin/pip" install -q "${pins[@]}"
fi

# .NET 10 SDK (Mutagen 0.54 targets net9/net10 only), user-local via dotnet-install.sh (hash pinned)
if ! { command -v dotnet >/dev/null && dotnet --list-sdks | grep -q '^10\.';  }; then
  curl -fsSL https://dot.net/v1/dotnet-install.sh -o "$tmp/dotnet-install.sh"
  echo "$(sha dotnet-install.sh)  $tmp/dotnet-install.sh" | sha256sum -c - >/dev/null
  bash "$tmp/dotnet-install.sh" --channel "$(ver dotnet-sdk)" --install-dir "$HOME/.dotnet" --no-path
fi

# Node (the pinned version; runs tools/schema_gen with --experimental-strip-types), user-local, hash checked
want="$(ver node)"; ndir="$HOME/.argonia/node/$want"
if [ ! -x "$ndir/bin/node" ]; then
  a="node-v$want-linux-x64.tar.xz"
  curl -fsSL "https://nodejs.org/dist/v$want/$a" -o "$tmp/$a"
  curl -fsSL "https://nodejs.org/dist/v$want/SHASUMS256.txt" -o "$tmp/SHASUMS256.txt"
  (cd "$tmp" && grep " $a\$" SHASUMS256.txt | sha256sum -c - >/dev/null)
  mkdir -p "$ndir"; tar -xJf "$tmp/$a" -C "$ndir" --strip-components=1
fi
mkdir -p "$HOME/.local/bin"; ln -sfn "$ndir/bin/node" "$HOME/.local/bin/node"

# Spriggit CLI: the Spriggit.CLI NuGet tool package is not installable as a global tool; use the GitHub release zip
want="$(ver spriggit-cli)"; sdir="$HOME/.argonia/spriggit/$want"
if [ ! -x "$sdir/Spriggit.CLI" ]; then
  curl -fsSL "https://github.com/Mutagen-Modding/Spriggit/releases/download/$want/SpriggitLinuxCLI.zip" -o "$tmp/sp.zip"
  echo "$(sha spriggit-cli)  $tmp/sp.zip" | sha256sum -c - >/dev/null
  mkdir -p "$sdir"; unzip -q -o "$tmp/sp.zip" -d "$sdir"; chmod +x "$sdir/Spriggit.CLI"
fi
mkdir -p "$HOME/.local/bin"; ln -sfn "$sdir/Spriggit.CLI" "$HOME/.local/bin/spriggit"

# rtk (prebuilt musl binary; the crates.io 'rtk' is a different tool)
want="$(ver rtk)"
if ! { command -v rtk >/dev/null && rtk --version 2>&1 | grep -q "$want"; }; then
  a="rtk-x86_64-unknown-linux-musl.tar.gz"
  curl -fsSL "https://github.com/rtk-ai/rtk/releases/download/v$want/$a" -o "$tmp/$a"
  echo "$(sha rtk)  $tmp/$a" | sha256sum -c - >/dev/null
  mkdir -p "$tmp/x" "$HOME/.local/bin"; tar -xzf "$tmp/$a" -C "$tmp/x"
  install -m 0755 "$(find "$tmp/x" -type f -name rtk | head -1)" "$HOME/.local/bin/rtk"
fi

echo "setup ok. Activate with:"
echo '  export PATH="$HOME/.argonia/venv/bin:$HOME/.dotnet:$HOME/.dotnet/tools:$HOME/.local/bin:$PATH" DOTNET_ROOT="$HOME/.dotnet"'
