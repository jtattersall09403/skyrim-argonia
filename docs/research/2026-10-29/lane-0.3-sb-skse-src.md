# Lane 0.3-sb-skse-src: our SKSE build, the source side

**Outcome.** The `skse/` tree builds and tests on the build VM. The plugins and the MSVC driver are written but
not compiled, because the 0.2 lane holds the game machine. Evidence and the CommonLib choice are in
[the journal](../journals/skse-build.md).

## What landed
- `skse/CMakeLists.txt`, `CMakePresets.json` (`linux-core`, `windows-dev`, `windows-release`), `vcpkg.json`
  (CommonLib's dependencies, baseline ee12231b), `cmake/CommonLib.cmake` (alandtse/CommonLibSSE-NG v15.2.0,
  FetchContent, the commit dec1be18 enforced, prebuilt bundle on, and `argonia_plugin()`, which installs a plugin
  as either the dist or the dev component).
- `skse/core/`: pure C++23. Holds the co-save family contract (`cosave.h`: `FamilySpec`, the `upgrade()`
  migration chain, the little-endian Writer and Reader, family META v1 {save_count, written_by}, unique id
  `ARGN`) and the generated `version.h` from the project VERSION 0.3.0. Its test `core.cosave` has 9 cases.
- `skse/ArgoniaCore`: `SKSE_PLUGIN_LOAD`, natives `ArgoniaCore.Version()` and `ArgoniaCore.SaveCount()`
  (`papyrus/ArgoniaCore.psc`), and META save, load and revert callbacks through `core::cosave::upgrade`.
- `skse/ArgoniaBridge` (DEV ONLY): the named pipe `\\.\pipe\argonia-bridge`, which rejects remote clients; a
  128-bit token per launch in `ArgoniaBridge.token` beside the SKSE log; handlers on the main thread through
  `TaskInterface::AddTask` with a 3 s timeout; the `ping` endpoint; and `ping.ps1`. The pure `protocol/` has its
  own test, `bridge.protocol`, with 5 cases including bad-token and over-long refusals.
- Dev-only marking, in four places:
  - `skse/dev-only.txt` names the DLL.
  - CMake refuses a dev plugin that is not listed, and a listed one installed as dist.
  - `windows-release` skips the bridge; a `FATAL_ERROR` and an `#error` back that up.
  - `skse_build.ps1` fails if a listed DLL appears in the dist output, and deploys to separate MO2 mods: `Argonia SKSE` and `Argonia SKSE (dev only)`.
- `infra/gpu-box/skse_build.sh` (the build VM driver) and `skse_build.ps1` (the game machine). Windows OpenSSH
  has no rsync, so the driver sends one tar that keeps file times, over scp.
- The Makefile gains a `skse` part running `skse/check.sh`. It uses CMake and Ninja (pip, in `~/.argonia/buildtools`) and falls back to plain c++.

## Measured
- `skse/check.sh` takes 1.3 s and 2/2 tests pass; the fallback without CMake passes both too.
- Fail-on-purpose: with the check broken to `b.size() == 9`, the output is
  `test_cosave.cpp:17: CHECK failed`, `core.cosave (Failed)`, rc=2. Restored, it passes 2/2.
- `make check` at 19:3x UTC: `skse` green. The only red is `unit`, from another lane's uncommitted
  `tools/immersion/test_inventory.py` (missing `ArgoniaFixture.esp`), which is not this lane's.

## For the planner (0.3 lane, game machine)
```
tooling/job_guard.sh run skse-build -- infra/gpu-box/skse_build.sh all windows-dev
tooling/job_guard.sh wait skse-build      # repeat until done; the first run installs VS 2026 Build Tools, MinGit, vcpkg
```
Later builds: `infra/gpu-box/skse_build.sh build windows-dev`. Success prints `SKSE-BUILD OK windows-dev` and the
paths of the DLLs. The log is `C:\argonia\logs\skse-build.log`.

## MSVC build (19:45 and 19:53 UTC)
- **First run:** the link failed (`fmt::v12::detail::allocate` unresolved in the prebuilt CommonLibSSE.lib), because
  our vcpkg baseline ee12231b gave fmt 12.1.0 while the bundle was built at NG's `vcpkg-configuration.json`
  baseline 00c57752 (fmt 12.2.0#1).
- **Fix:** `skse/vcpkg.json` moved to baseline 00c57752.
- **Second run:** `SKSE-BUILD OK windows-dev` in 2 min 20 s; ctest under MSVC passed 2 of 2;
  `ArgoniaCore.dll` is 629,248 bytes and `ArgoniaBridge.dll` 588,800 bytes, both in their MO2 mod folders.

## Unverified, and the risks
- Both DLLs link, but neither has loaded in the game yet: SKSE's log, the natives and the co-save round trip are untested.
- If VS 2026's current cl is newer than 19.51, the build falls back to a CommonLib source build (~16 min).
- `ArgoniaCore.psc` needs compiling to .pex with the CK's compiler before `Version()` can be called.
- The MO2 profile must enable both mod folders.
