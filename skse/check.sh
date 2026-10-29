#!/usr/bin/env bash
# make check's skse part: configure, build and run the pure-C++ tests (core and the bridge protocol) on Linux.
# CMake and Ninja come from PATH or the build VM's ~/.argonia/buildtools venv; without them the tests are built
# straight with c++, so the gate never depends on a tool a fresh VM lacks.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
export PATH="$PATH:$HOME/.argonia/buildtools/bin"
if command -v cmake >/dev/null && command -v ninja >/dev/null; then
  cd "$here"
  cmake --preset linux-core >/dev/null
  cmake --build --preset linux-core >/dev/null
  ctest --preset linux-core
else
  out="$here/../build/skse/plain"; mkdir -p "$out/generated/argonia/core"
  v=$(sed -n 's/^project(ArgoniaSKSE VERSION \([0-9.]*\).*/\1/p' "$here/CMakeLists.txt"); IFS=. read -r M m p <<<"$v"
  sed -e "s/@PROJECT_VERSION_MAJOR@/$M/;s/@PROJECT_VERSION_MINOR@/$m/;s/@PROJECT_VERSION_PATCH@/$p/;s/@PROJECT_VERSION@/$v/" \
    "$here/core/include/argonia/core/version.h.in" > "$out/generated/argonia/core/version.h"
  f=(-std=c++23 -Wall -Wextra -Wpedantic -Werror -I"$here/core/include" -I"$out/generated" -I"$here/core/tests")
  c++ "${f[@]}" "$here/core/src/cosave.cpp" "$here/core/tests/test_cosave.cpp" -o "$out/core_tests"
  c++ "${f[@]}" -I"$here/ArgoniaBridge/protocol" "$here/ArgoniaBridge/protocol/bridge_protocol.cpp" \
    "$here/ArgoniaBridge/tests/test_protocol.cpp" -o "$out/protocol_tests"
  "$out/core_tests" && "$out/protocol_tests"
fi
