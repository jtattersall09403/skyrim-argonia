#!/usr/bin/env bash
# Build nifconv against ousnius/nifly at the commit infra/build-vm/toolchain.lock pins (the objects tools/places/assets/
# nifdump/build.sh made are reused); out: ~/.argonia/bin/nifconv.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
bash "$here/../../../tools/places/assets/nifdump/build.sh" >/dev/null
src="$HOME/.argonia/src/nifly"; obj="$HOME/.argonia/src/nifly-build"
g++ -std=c++20 -O2 -I"$src/include" -I"$src/external" "$here/nifconv.cpp" "$obj"/*.o -o "$HOME/.argonia/bin/nifconv"
echo "built $HOME/.argonia/bin/nifconv"
