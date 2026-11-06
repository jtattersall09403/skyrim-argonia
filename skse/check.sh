#!/usr/bin/env bash
# make check's skse part: configure, build and run the pure-C++ tests on Linux. CMake and Ninja come from PATH or the
# build VM's ~/.argonia/buildtools; without them the tests are built straight with c++, so the gate never depends on a
# tool a fresh VM lacks.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
export PATH="$PATH:$HOME/.argonia/buildtools/bin"
if command -v cmake >/dev/null && command -v ninja >/dev/null; then
  cd "$here"
  cmake --preset linux-core >/dev/null
  cmake --build --preset linux-core >/dev/null
  ctest --preset linux-core
else
  out="$here/../build/skse/plain"; mkdir -p "$out"
  c++ -std=c++23 -Wall -Wextra -Wpedantic -Werror -I"$here/ArgoniaDodgeBuffer/core" \
    "$here/ArgoniaDodgeBuffer/tests/test_buffer.cpp" -o "$out/test_buffer"
  "$out/test_buffer"
fi
