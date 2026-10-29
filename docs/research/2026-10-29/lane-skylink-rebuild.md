# Lane skylink-rebuild: report (2026-10-29)

**1. Failure cause, confirmed.** SkyLink's log on the game machine says
`[critical] [ID.h:219] failed to open address library file` (21:11:02). The DLL embeds the paths of a
CharmedBaryon CommonLibSSE-NG `main` clone (its README: `git clone --depth 1`). That CommonLib's `REL/Module.h`
maps minor 6 to AE and anything else to SE, so 1.7.104 counts as SE and it opens `version-1-7-104-0.bin`.
Address Library ships only `versionlib-1-7-104-0.bin` (header `05 00 00 00 ...`: format 5). The layered causes:

1. The wrong file name, which is the error the log shows.
2. Format 5, which that CommonLib refuses.
3. SkyLink's own `patch() < 1130` console id, which is wrong on 1.7.

The earlier line "predates format 5" was half the story. Evidence and byte dumps:
`docs/research/journals/bridge.md`, 2026-10-29 skylink-rebuild section.

**Source and licence.** The source is github.com/jarvann/SkryimMCM at `82a0a80d` (2026-03-27, the 1.0.0
upload). Its README declares MIT; the repo has **no LICENSE file**, which is recorded in the sourcing-register
row. Credit is kept in `skse/third_party/skylink/README.md`.

**2. Rebuilt for 1.7.104: MSVC green.**
- `skse/third_party/skylink/` holds a FetchContent at the pinned commit and a 5-change patch: the console id
  chosen by version, `GetVMRuntimeData().impl`, `GetActiveTarget()`, `EnumSet::underlying()` and
  `SendHUDMessage::ShowHUDMessage`. It also drops `SKSE_SUPPORT_XBYAK=0`. Nothing is vendored.
- It is off in the main build (`ARGONIA_SKYLINK`, which defaults from the environment).
- `infra/gpu-box/skylink_build.ps1` builds only `SkyrimMCPPlugin`, in its own tree `C:\argonia\skylink`
  (no GPU lock, never game-1's tree). It took 6 build rounds; the last had 0 warnings.
- The output is `C:\argonia\MO2\mods\SkyLink (dev, rebuilt)\SKSE\Plugins\SkyrimMCPPlugin.dll`: 1,602,560
  bytes, sha256 `AF2DC7B61F43A0E6DEA07866607D7B474696E670D3200F8DB76121C7AA633EC2`.
- `SkyrimMCPPlugin.dll` is added to `skse/dev-only.txt`, and nlohmann-json to `skse/vcpkg.json`.
- The .NET server is not rebuilt. It is not needed: `skylink.ps1` speaks the pipe, and the server only maps MCP
  onto the same actions. The machine also has no `dotnet` (the brief said .NET 10 was installed; it is not).

**Game-1** (`a0cb55b31cd87b68c`) has the DLL path, how to lay it (a copy into `Data\SKSE\Plugins`, or enabling
the MO2 mod), the `skylink.ps1` calls and what to compare. It will try it if the slot has room. Nothing was
launched; the game was not touched.

**3. Comparison:** the table in `docs/research/journals/bridge.md`. Dispatch is already the same pattern as
SkyLink's. Ours is ahead on the token and socket, the console output delta, screenshots, input, the event ring
with waits, and crash and zombie handling; SkyLink has none of screenshot, input or crash detection. One piece
was copied: **SkyLink's SEH wrapper**, `compile_and_run_guarded` in `skse/ArgoniaBridge/src/bridge.h`, used by
`console` (`ep_state.cpp`) and `teleport cell` (`ep_world.cpp`), credited, with game-1's yes. ArgoniaBridge
compiles green with it under MSVC in the separate tree (822,784 bytes). It is not yet laid; game-1 picks it up
in its next rebuild.

**4. Recommendation:** keep ArgoniaBridge as the bridge, with SkyLink's methods where they are better (the SEH
wrapper now, and its event-sink breadth when a journey needs death, combat, cell-loaded or activate). Use the
rebuilt SkyLink as a second oracle in game-1's slot. The planner decides on the live results.

**Gate.** `make check` is red on `plugin-check` only: "water design rows differ ... ['water_basin']". That comes
from the water lane's uncommitted `tools/argonia_world/water/*` and `world/db/water_*` edits, which none of my
paths reach. Every other part is green, including `skse`, `guard`, `links` and `unit`. Separately,
`core.messages` fails under MSVC in a skse-only tree (fixtures outside `skse/`), as game-1 also reports. That one
is not mine either.
