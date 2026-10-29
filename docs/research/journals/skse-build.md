# Journal: our SKSE build (chunk 0.3 §b)

What was tried, measured and learned for `skse/`, so nothing is lost at a hand-off.

## 2026-10-29: the source side, built VM only (lane 0.3-sb-skse-src)

**Which CommonLib, and why.** Four lines were checked on GitHub (2026-10-29):

| Repo | Last push | Licence | 1.7.104 |
|------|-----------|---------|---------|
| CharmedBaryon/CommonLibSSE-NG | 2024-09-04 | MIT | no; stalled before 1.7 |
| powerof3/CommonLibSSE (dev) | 2026-10-26 | GPL-3.0 | AE-only line; "Fix 1.7 IDs" 2026-10-25 |
| eddoursul/CommonLibSSE-GG | 2026-08-30 | MIT | "support Skyrim SE 1.7.104" (3aa704e, 2026-08-27); one author, 0 stars |
| **alandtse/CommonLibSSE-NG (ng)** | 2026-10-29 | GPL-3.0-or-later | `RUNTIME_SSE_1_7_104` in `include/SKSE/Version.h`, `RUNTIME_SSE_LATEST_AE = 1_7_104`; Address Library format 5 (1.7.99+) read in `src/REL/IDDB.cpp` |

Chosen: **alandtse/CommonLibSSE-NG v15.2.0, commit dec1be18b1880c1f643afedc0d01db0118d648f9**. It is the
maintained NG line (syncs powerof3's dev, regular 1.7.99+ fixes: #401, #403, #441, #451 in Sept–Oct 2026),
multi-runtime as decision 0002 §1 asks, and GPL-3.0-or-later as our `LICENSE` is, so linking it costs us nothing.
GG is the fallback if NG regresses on 1.7.104 (MIT, the same API). The vcpkg port in colorglass's registry is
the old, unmaintained one (the NG README says so), so CommonLib comes by CMake FetchContent at the tag and the
CMake refuses any other commit; its dependencies (spdlog, fmt, directxtk, directxmath, rapidcsv) come from our
`skse/vcpkg.json` at the baseline the bundle was built with (see the second entry below).

**The prebuilt bundle.** v15.2.0 publishes `commonlibsse-ng-prebuilt-v15.2.0-all-msvc-cmake.zip` (128 MB, sha256
c0394512…599f verified); `COMMONLIB_PREBUILT=ON` links it instead of a ~16 min source build when the consumer's
cl has the same major.minor as its `TOOLSET_VERSION.txt`: **msvc19.51.36260.0**, which is VS 2026 (18.x). So
`skse_build.ps1` installs VS 2026 Build Tools (`aka.ms/vs/18/stable/vs_buildtools.exe`, resolved 301 today).
A newer 19.5x falls back to a source build: slower, not broken.

**Not taken:** NG's clang-cl + xwin Linux cross-compile presets would build the DLLs on the build VM, but the
brief and PLAN §3 put the build on the game machine with MSVC; worth a look if the MSVC round trip proves slow.

**Measured on the build VM:** `skse/check.sh` (CMake 4.4.4 and Ninja 1.13.2 from pip in `~/.argonia/buildtools`,
g++ 13.3) configures `linux-core`, builds and runs 2 tests in 1.3 s; without CMake it compiles the tests with c++
directly. The plugins were not compiled here (they need MSVC and the Windows SDK).

**Open for the 0.3 lane on the game machine:** `infra/gpu-box/skse_build.sh all windows-dev` (first run installs
the tools), then the §b acceptance: SKSE's log shows ArgoniaCore loading on 1.7.104.0; `ArgoniaCore.Version()`
answers through the bridge (compile `ArgoniaCore.psc` with the CK's compiler first); `SaveCount()` survives a
save and load; `ArgoniaBridge/ping.ps1` returns ok and `-Token bad` fails. Address Library's
`versionlib-1-7-104-0.bin` must be in the profile (0.2's core row).

## 2026-10-29: the first MSVC build (game machine, 19:45 and 19:53 UTC)

- **First run** (`skse_build.sh all windows-dev`; installed the tools): 15/16 steps compiled, then the link failed.
  The error was `LNK2001: unresolved external symbol fmt::v12::detail::allocate(unsigned __int64)`, from
  `API.cpp.obj` and `Trampoline.cpp.obj` in the prebuilt `CommonLibSSE.lib`, and it took down ArgoniaBridge.dll.
- **Cause:** I had copied NG's `vcpkg.json` `builtin-baseline` ee12231b (fmt 12.1.0, spdlog 1.16.0). NG's
  `vcpkg-configuration.json` overrides it with the default-registry baseline **00c57752** (fmt 12.2.0#1, spdlog
  1.17.0, directxtk 2026-05-07, directxmath 2026-06-12, rapidcsv 8.99), and its prebuilt workflow keys on both
  files. So the bundle's objects use fmt 12.2 symbols that 12.1 lacks. Versions read from
  `versions/baseline.json` at both commits.
- **Fix:** `skse/vcpkg.json` moves to baseline 00c57752 with those versions as minimums, so the bundle stays
  usable (no ~16 min source build). Rule: our baseline is whatever CommonLib's `vcpkg-configuration.json` names
  at the pinned tag, and it moves whenever the tag moves.
- **Second run** (`skse_build.sh build windows-dev`): finished in 2 min 20 s with cl 19.51.36260 and CMake
  4.3.1-msvc1. Under MSVC, ctest passed 2 of 2. Outputs: `ArgoniaCore.dll` 629,248 bytes (dist) and
  `ArgoniaBridge.dll` 588,800 bytes (dev), copied into MO2 `mods\Argonia SKSE` and `mods\Argonia SKSE (dev only)`.
  The game and Data were not touched.
