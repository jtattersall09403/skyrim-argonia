# skse
Our SKSE plugins on CommonLibSSE-NG (alandtse's maintained line, v15.2.0, pinned in `cmake/CommonLib.cmake`;
why in `docs/research/journals/skse-build.md`), Address Library ids only. Never decompiled code or retail offsets.

- `core/`: pure C++ rules, no Skyrim types; unit-tested on the build VM by `make check` (`check.sh`).
- `ArgoniaCore`: all new state in versioned co-save families (`core/include/argonia/core/cosave.h`), Papyrus
  natives (`papyrus/ArgoniaCore.psc`). Ships.
- `ArgoniaBridge`: DEV ONLY (`dev-only.txt`), what SkyLink AI lacks: a named pipe with a token, handlers on the
  main thread; `protocol/` is pure and tested on Linux. A `windows-release` build refuses it.
- Later: `ArgoniaCombat`, `ArgoniaBoats` (PLAN §3).

Build: Linux `cmake --preset linux-core` (tests only); the plugins on the game machine with MSVC through
`infra/gpu-box/skse_build.sh [tools|build|all] [windows-dev|windows-release]`.
