#!/usr/bin/env bash
# make check's skse part: configure, build and run the pure-C++ tests on Linux. CMake and Ninja come from PATH or the
# build VM's ~/.argonia/buildtools; without them the tests are built straight with c++, so the gate never depends on a
# tool a fresh VM lacks.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$here/../build/skse"
export PATH="$PATH:$HOME/.argonia/buildtools/bin"
if command -v cmake >/dev/null && command -v ninja >/dev/null; then
  # one build folder per run: lanes run make check at once in the same tree, and a shared folder let one run's
  # rebuild remove the test binaries while another ran them ("Not Run")
  cd "$here"; out=$(mktemp -d "$here/../build/skse/run.XXXXXX"); trap 'rm -rf "$out"' EXIT
  cmake --preset linux-core -B "$out" >/dev/null
  cmake --build "$out" >/dev/null
  ctest --test-dir "$out" --output-on-failure
else
  out=$(mktemp -d "$here/../build/skse/plain.XXXXXX"); trap 'rm -rf "$out"' EXIT
  c++ -std=c++23 -Wall -Wextra -Wpedantic -Werror -I"$here/ArgoniaDodgeBuffer/core" \
    "$here/ArgoniaDodgeBuffer/tests/test_buffer.cpp" -o "$out/test_buffer"
  "$out/test_buffer"
  c++ -std=c++23 -Wall -Wextra -Wpedantic -Werror -I"$here/ArgoniaDodgeBuffer/core" \
    "$here/ArgoniaDodgeBuffer/tests/test_backstab.cpp" -o "$out/test_backstab"
  "$out/test_backstab"
fi
