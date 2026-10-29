# SkyLink AI, rebuilt for 1.7.104 (dev only)

SkyLink AI 1.0.0 (Nexus SSE 175682) is an SKSE plugin, `SkyrimMCPPlugin.dll`, plus a .NET MCP server over the
named pipe `\\.\pipe\SkyrimMCP`. Source: https://github.com/jarvann/SkryimMCM. Its README declares the MIT
licence (the repo has no LICENSE file) and credits ConsoleUtilSSE by VersuchDrei (MIT) for its console method.
Credit for everything this folder fetches goes to its author. It is dev only and never ships (`skse/dev-only.txt`).

**Why the Nexus DLL fails on 1.7.104.** It was built against a shallow clone of CharmedBaryon/CommonLibSSE-NG
`main` (its README; the DLL's embedded paths are `...\extern\CommonLibSSE-NG\include\REL/ID.h`). That CommonLib
maps the runtime from the minor version: 4 is VR, 6 is AE, anything else is SE (`REL/Module.h`, `load_version`).
On 1.7.104 that gives SE, so it opens the SE file name `Data/SKSE/Plugins/version-1-7-104-0.bin`. Address
Library ships only `versionlib-1-7-104-0.bin`, so the open fails: "failed to open address library file"
(`ID.h:219`, its `SkyrimMCPPlugin.log`). Had the open worked, the file's header is format 5 (`05 00 00 00`), and
that CommonLib accepts only format 2 for AE.

**What the build changes.** `CMakeLists.txt` fetches the source at commit `82a0a80d` and compiles its `src/`
the way its own CMake does. It uses our pinned CommonLib (alandtse CommonLibSSE-NG v15.2.0, which has
`RUNTIME_SSE_1_7_104` and reads format 5) and nlohmann-json from our `vcpkg.json`. `skylink-1.7.104.patch`
holds our changes, each marked `// Argonia:`:

- `Helpers.h`: the console's `CompileAndRun` relocation picks the post-1.6.1130 id by version, not by
  `patch() < 1130`. That test is true on 1.7.104 (patch 104), so the unpatched code would call the pre-1130 id.
- `PapyrusBridge.cpp`: `vm->impl` becomes `vm->GetVMRuntimeData().impl`. In this CommonLib the field's offset
  depends on the runtime (0x210 from 1.7.99).
- `NPCManager.cpp`: `pickData->target` becomes `GetActiveTarget()`.
- `PlayerQueries.cpp`: `GetSlotMask()` is an `EnumSet`, read with `.underlying()`.
- `UtilityManager.cpp`: `RE::DebugNotification` becomes `RE::SendHUDMessage::ShowHUDMessage`.
- `CMakeLists.txt` drops its `SKSE_SUPPORT_XBYAK=0`, because this CommonLib tests that macro with `#ifdef`.

**Build.** It is off in the main build. `infra/gpu-box/skylink_build.ps1` builds it with `ARGONIA_SKYLINK=1`,
in its own tree `C:\argonia\skylink`, and lays it in `MO2\mods\SkyLink (dev, rebuilt)`. Its .NET server is not
rebuilt: `infra/gpu-box/skylink.ps1` speaks the pipe directly, and the Nexus archive's server works over the
unchanged protocol if an MCP client is ever wanted.
