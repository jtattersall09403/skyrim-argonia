#!/usr/bin/env bash
# Build nifdump against ousnius/nifly at the commit infra/build-vm/toolchain.lock pins; out: ~/.argonia/bin/nifdump.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
lock="$here/../../../../infra/build-vm/toolchain.lock"
want="$(grep '^nifly=' "$lock" | cut -d= -f2 | cut -d' ' -f1)"
src="$HOME/.argonia/src/nifly"
[ -d "$src/.git" ] || git clone -q https://github.com/ousnius/nifly "$src"
git -C "$src" fetch -q origin 2>/dev/null || true
git -C "$src" -c advice.detachedHead=false checkout -q "$want"
obj="$HOME/.argonia/src/nifly-build"; mkdir -p "$obj" "$HOME/.argonia/bin"
for f in "$src"/src/*.cpp; do
  o="$obj/$(basename "$f" .cpp).o"
  [ "$o" -nt "$f" ] || g++ -std=c++20 -O2 -w -I"$src/include" -I"$src/external" -c "$f" -o "$o"
done
g++ -std=c++20 -O2 -I"$src/include" -I"$src/external" "$here/nifdump.cpp" "$obj"/*.o -o "$HOME/.argonia/bin/nifdump"
echo "built $HOME/.argonia/bin/nifdump (nifly $want)"
