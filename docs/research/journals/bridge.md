# Journal: the bridge (chunk 0.3 §a)

What the agent's hands in the running game are, how each endpoint is called and how each one fails on purpose,
so nothing is lost at a hand-off. DEV ONLY: none of it ships (decision 0003; `skse/dev-only.txt`).

## 2026-10-29: SkyLink AI dropped, our plugin carries the list (lane 0.3-bridge)

**Why ours.** SkyLink AI 1.0.0 (Nexus 175682, its only file) fails on 1.7.104 with "failed to open address
library file": its CommonLib predates Address Library format 5, and the failure raises a modal that blocks
startup (the 0.2 lane, 2026-10-29). Per the brief's fallback, `skse/ArgoniaBridge` carries the whole list with
SkyLink's design as the method: a local endpoint, a token, every game call on the main thread, the console run
the way ConsoleUtilSSE does it (a `Script` form compiled and run, its output read from `ConsoleLog`'s buffer).
SkyLink's archive holds no source, but its source is public (github.com/jarvann/SkryimMCM, MIT by its README):
see the 2026-10-29 lane skylink-rebuild section below for the confirmed cause, the rebuild, and the comparison.

**Shape.**
- `skse/ArgoniaBridge/protocol/` is pure C++, tested on the build VM (`bridge.protocol` in `make check`): the
  line protocol and its refusals, the JSON writer, the console's output delta and refusal words, save names, key
  names and chords, frame statistics, and `nav.h`'s A* over navmesh triangles.
- `src/main.cpp`: the token (128 bits, new per launch, `My Games\...\SKSE\ArgoniaBridge.token`), the named pipe
  `\\.\pipe\argonia-bridge` and the socket `127.0.0.1:47615` (`tcp.cpp`, built without the PCH because
  CommonLib's `<Windows.h>` pulls the old `winsock.h`), one request at a time, the command table, the SKSE
  messages (post-load, save, new game) the endpoints wait on. `ep_*.cpp` hold the endpoints.
- `tools/bridge.py` is the one client: an `ssh -L` tunnel to the socket (started once, left up), the token read
  over SSH and refreshed once on "bad token", one JSON line per call. `infra/gpu-box/bridge.ps1` is the machine's
  half: `health`, `token`, `kill`, `prepare`, `grab`.
- **The dev plugin is laid by copy**, not by 0.2's hard links: `bridge.py launch` runs `bridge.ps1 kill`, then
  `prepare` (`stack.ps1 on` only when the profile is off, then `ArgoniaBridge.dll` copied from
  `MO2\mods\Argonia SKSE (dev only)` into `Data\SKSE\Plugins`), then 0.2's `stack.ps1 menu` with
  `ARGONIA_KEEP=1` in the desktop session, then a `ping`. A copy means a rebuild never meets a locked file;
  `stack.ps1 off` removes it with everything else.

**The endpoints.** Call `python3 tools/bridge.py <command> [args]` (exit 0 ok, 1 refused, 2 game down, 3 no
reply) or `Bridge().call(command, *args)` (the `result`, or `BridgeError` / `GameDown` / `NoReply`).

| Command | Does | Fails on purpose when |
|---|---|---|
| `ping` | answers from the main thread: version, pid, tasks run | the token is wrong |
| `commands` | the command list | - |
| `player` | pos x/y/z, `angle_z` and heading, health/stamina/magicka (current, max), cell and worldspace (id, editor id, name), interior, `in_air`, `swimming`, dead | no player in a world (main menu, loading) |
| `console <line>` | runs it as the console does, on its selected reference; the printed output | the compiler refuses the line ("Script command ... not found", "Missing parameter", ...) |
| `save <name>` | `BGSSaveLoadManager::Save`; ok once `Saves\<name>.ess` exists, newer than the call (30 s cap) | no player in a world; a name outside 1-64 of `A-Za-z0-9 _-` |
| `load <name>` | `Load(name, checkForMods=false)` (no missing-content prompt); ok on SKSE's post-load message (120 s cap), with its time | no such file; the game reports a failed load; no finish in 120 s |
| `teleport cell <edid>` / `ref <id>` / `pos <x y z>` | `coc` as the console does it, `MoveTo`, or `SetPosition`; waits for the load and answers where the player stands | no load starts within 5 s (unknown cell); the player is not at the target |
| `time [hour]` | the calendar; with an hour, sets GameHour and reads it back | an hour outside [0, 24); the hour did not take |
| `weather [id]` | the current and last weather; with one, `ForceWeather` and reads it back | not a weather; the sky did not take it |
| `quest <id/edid>` | stage, running, enabled, completed | not a quest |
| `global <id/edid>` | its value | not a global |
| `av <name> [player/ref]` | current, base, permanent | no such actor value or actor |
| `inventory [player/ref]` | items with count and worn | no such reference |
| `events [since] [kind]` | the ring (4096) of hit, anim (the player's graph), quest (stages) and menu events after `since`, each with `seq`, `t_ms` since load and `game_days` | - |
| `wait_event <kind> <match/*> <ms> [since]` | blocks for the first match (anim tag, quest id, menu name, hit target id), at most 60 s | nothing matching within the timeout |
| `input key <K[+K]> <ms>` | a real keyboard press: `SendInput` scan codes from inside the game process (the desktop session), held and released | over 3000 ms; an unknown key; the game window lacks focus |
| `bridge.py pad '<seq>'` | a real gamepad sequence on `pad.ps1`'s virtual Xbox pad (ViGEm, the XInput path) | a sequence over 3000 ms or malformed (refused before it is sent) |
| `frametime [frames]` | real frame intervals at the player's per-frame `Update` (vtable slot 0xAD by Address Library id): mean, p50, p95, p99, max, fps | frames outside 10-2000; no frames (paused, a menu); a test's budget it misses |
| `nav <x y z / player> <x y z>` | A* over the loaded cells' navmesh triangles (shared edges and edge portals): length, waypoints | either point off every loaded navmesh; no connection; nothing loaded |
| `booth place <id>` / `view <0-5>` / `clear`; `bridge.py booth <id> [dir]` | places a base record ahead of the player, frames it with the free camera from front, right, back, left, top and three-quarter, a still each, then clears | not a bound object |
| `bridge.py screenshot <png>`, `oracle` | a still through Desktop Duplication (`grab.ps1`); the oracle is live only if two stills a second apart differ | two identical stills |
| `crash yes-really` | null dereference on the main thread, for the crash check | without `yes-really` |

**Crash handling.** A call that waits checks `bridge.ps1 health` every 20 s (and at once when the socket closes):
SkyrimSE gone, a `crash-*.log` written since this launch's token, or a window not responding is `GameDown` with
the log's head. `bridge.py launch` (and `bridge.ps1 kill`) end SkyrimSE and the loader, taskkill any survivor
with its tree, and fail if one is still there after 20 s.

**Tests.** L2 on the build VM: `bridge.protocol` (ctest) and `tools/tests/test_bridge.py` (a fake plugin on a
socket: ok, refusal, stale token, closed connection with a dead game, a crash log while waiting, no reply, the pad
cap, frame difference, the release guard). L4 in a game slot: `python3 -m tools.tests.bridge_live --save <base>
[--crash]`, a pass case and a fail-on-purpose case per endpoint, results in `out/bridge/live.json`.

## 2026-10-29: SkyLink AI rebuilt from source, and the two designs compared (lane skylink-rebuild)

**The failure, confirmed.** SkyLink's own log on the game machine (`SKSE\SkyrimMCPPlugin.log`, 21:11:02) says
`[critical] [ID.h:219] failed to open address library file`. The DLL embeds the paths of a CharmedBaryon
CommonLibSSE-NG `main` clone (`X:\_work\skyrim_mcp\SkyrimMCPPlugin\extern\CommonLibSSE-NG\...`; its README
clones it `--depth 1`, last pushed 2024-09). That CommonLib picks the runtime from the minor version (4 VR, 6 AE,
else SE: `REL/Module.h` `load_version`), so 1.7.104 counts as **SE** and it opens `version-1-7-104-0.bin`.
Address Library ships only `versionlib-1-7-104-0.bin` (2,263,132 bytes, header `05 00 00 00 01 00 00 00 07 00
00 00 68 00 00 00`: format 5, v1.7.104). So the first wall is the file name. Behind it is format 5, which that
CommonLib refuses for AE (it expects 2). Behind that is SkyLink's own `patch() < 1130` console id, which is
wrong on 1.7.

**The rebuild.** `skse/third_party/skylink/` fetches the source at `82a0a80d` and applies a five-line patch
(README there). It builds against our alandtse NG v15.2.0. The MSVC build is green (cl 19.51, 0 warnings), and
`SkyrimMCPPlugin.dll` (1,602,560 bytes) is laid in `MO2\mods\SkyLink (dev, rebuilt)` by `skylink_build.ps1`. Its .NET MCP server is not rebuilt: it only maps MCP tools onto the same pipe actions,
`infra/gpu-box/skylink.ps1` speaks the pipe directly, and the machine has no .NET SDK.

**The two designs, piece by piece.** SkyLink was never shown working on 1.7.104, and nothing of its design is
proven here until game-1's slot runs it. So "proven" below means proven on 1.6.1130+ by its 502 downloads, no
more than that.

| Piece | SkyLink AI | ArgoniaBridge | Copy |
|---|---|---|---|
| Threading, main-thread dispatch | One pipe thread started at `kDataLoaded`. Each handler posts a `std::function` with `SKSE::GetTaskInterface()->AddTask`, a `std::promise` shared into the task, `future.wait_for(5 s)`, and a throw on timeout (`TaskQueue.cpp`). Some reads (`ping`, `poll_events`) answer off-thread. | The same pattern (`on_main_thread`, `main.cpp:45`: AddTask, a shared promise, `wait_for(3 s)`, a refusal on timeout), with pipe and socket threads started at `kDataLoaded`. | **Already the same.** Nothing to port. |
| Pipe protocol | `\\.\pipe\SkyrimMCP`, newline JSON `{"id","action","params"}` to `{"id","success","data"\|"error"}`. One client at a time, no auth, 64 KiB buffers, a log line per request. The .NET client connects in 3 s, waits 10 s per answer and serialises sends with a semaphore. | Newline text lines with a per-launch token, on a pipe and a loopback socket (for `ssh -L`). One request at a time. JSON answers with `ok`/`error`. | **Keep ours.** The token stops a stale client acting on a new launch, and the socket lets the build VM call it without a machine-side shim. JSON request bodies are worth copying only if an endpoint ever needs structured arguments. |
| Console | ConsoleUtilSSE's way: a `Script` form, `SetCommand`, then its own `CompileAndRunImpl` relocation inside an SEH `__try`, run on the **player** as target. The output is `ConsoleLog::lastMessage` (the last line only). | CommonLib's `Script::CompileAndRun`, whose id is version-checked (`AE_CHECK(1_6_1130, 21890, 441582)`, right on 1.7), on the console's selected ref. The output is the delta of the console buffer, with the compiler's refusal words read as failure. | **Ours, plus SkyLink's SEH wrapper.** A console line that faults should come back as a refusal, not a crash. Port its `RunScriptSEH` shape (MIT, credited) around our `CompileAndRun`, once game-1 agrees. |
| Screenshot | None. | Desktop Duplication from outside the process (`grab.ps1`), with the two-stills oracle. | **Keep ours.** SkyLink has nothing to copy. |
| Input injection | None. Its nearest is `play_idle` (an idle on an actor), which is no player input. | `SendInput` scan codes from inside the process, plus ViGEm XInput from `pad.ps1`. | **Keep ours.** SkyLink has nothing to copy. |
| Event sinks | 17 `BSTEventSink`s registered once at `kDataLoaded`: combat, death, quest stage and start/stop, location change, cell fully loaded, container, equip, hit, spell cast, activate, open/close, sleep, wait, fast travel, lock, tracked stats. They feed a mutex queue of 500 that `poll_events` drains destructively, with a mute filter for noisy quests. | Hit, quest stage, menu and the player's anim graph (re-attached per load), in a 4096 ring with `seq`, non-destructive, with `wait_event`. | **Ours for the store.** A ring with `seq` and blocking waits is what journeys need, and a destructive drain loses events between two readers. **Copy SkyLink's breadth when a journey needs it:** death, combat, cell fully loaded and activate are the first likely ones, with the same sink pattern it uses. |
| Crash and zombie handling | None in the plugin beyond SEH on the console and a throw on task timeout. The client only reconnects. Nothing detects a dead or hung game. | `bridge.ps1 health` every 20 s (the process, `crash-*.log` since this launch, not-responding), `kill` with taskkill of survivors, and `GameDown` within one interval. | **Keep ours.** SkyLink has nothing to copy. |
| Breadth of reads | 74 tools: inventory, perks, spells, factions, NPC detail, merchants, threats, Papyrus calls by name, form search. | The 20 commands a journey needs. | **Keep ours.** Add a read only when a test needs it. SkyLink's handlers are an MIT source to port from with credit. |

**Recommendation.** Keep ArgoniaBridge as the bridge, with SkyLink's console SEH wrapper ported in. SkyLink
lacks the screenshot, input, frame time, navmesh, booth, save/load waits, token and crash handling the studio
runs on, so "SkyLink as the bridge, ours for the gaps" would leave ours carrying most of the list anyway, with
two pipes to keep alive. The rebuilt SkyLink is a useful **oracle beside ours** in game-1's slot. If its
`get_player_info` or `execute_command` works where ours fails on 1.7.104, that names the bug on our side. The
planner decides on the slot's results.
