#!/usr/bin/env bash
# Build niflod against ousnius/nifly at the commit infra/build-vm/toolchain.lock pins; out: ~/.argonia/bin/niflod.
# nifly's source and objects are the ones tools/places/assets/nifdump/build.sh fetches and compiles (run it first).
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
src="$HOME/.argonia/src/nifly"; obj="$HOME/.argonia/src/nifly-build"
ls "$obj"/*.o >/dev/null 2>&1 || { echo "no nifly objects in $obj: run tools/places/assets/nifdump/build.sh" >&2; exit 1; }
g++ -std=c++20 -O2 -I"$src/include" -I"$src/external" "$here/niflod.cpp" "$obj"/*.o -o "$HOME/.argonia/bin/niflod"
echo "built $HOME/.argonia/bin/niflod"
