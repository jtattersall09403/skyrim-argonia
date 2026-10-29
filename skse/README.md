# skse
Our SKSE plugins on CommonLibSSE-NG (alandtse's maintained line, v15.2.0, pinned in `cmake/CommonLib.cmake`;
why in `docs/research/journals/skse-build.md`), Address Library ids only. Never decompiled code or retail offsets.

- `core/`: pure C++ rules, no Skyrim types; unit-tested on the build VM by `make check` (`check.sh`).
- Core modules (`core/include/argonia/core/`), each pure and tested:
  `json` strict JSON for the view messages; `router` the menu router registry and verdicts; `roundtrip` the
  save-contract L2 round trip against `schema/families.json`; `messages` the generated view-message twin;
  `families` the co-save family registry with migrations; `weather` the seasonal weather chances.
  The 13 rule modules: `carriers` perk-entry carrier values; `conditions` the condition-vocabulary evaluator;
  `curve` the skill curve; `death` death and the vastei pile; `disposition` per-person disposition bands;
  `effects` the one effect stack; `items` item condition and wear; `journal` the journal log; `progression` use,
  vastei and levels; `respawn` respawn on rest; `rest` camping and waiting rules; `sheet` the derived character
  sheet; `sitting` the level sitting.
- `ArgoniaCore`: all new state in versioned co-save families (`core/include/argonia/core/cosave.h`), Papyrus
  natives (`papyrus/ArgoniaCore.psc`). Ships.
- `ArgoniaBridge`: DEV ONLY (`dev-only.txt`), what SkyLink AI lacks: a named pipe with a token, handlers on the
  main thread; `protocol/` is pure and tested on Linux. A `windows-release` build refuses it.
- Later: `ArgoniaCombat`, `ArgoniaBoats` (PLAN §3).

Build: Linux `cmake --preset linux-core` (tests only); the plugins on the game machine with MSVC through
`infra/gpu-box/skse_build.sh [tools|build|all] [windows-dev|windows-release]`.
