# Lane 0.3-bridge: report and hand-off (2026-10-29, ~22:15 UTC)

## Hand-off (context mark reached before the game slot; the planner relaunches for the L4 slot)

**Done, committed** (`50817e0` and the hand-off commit carrying this file):
- `skse/ArgoniaBridge`: the whole endpoint list (SkyLink AI does not load on 1.7.104), by its method: token,
  named pipe plus a loopback socket 127.0.0.1:47615 (`tcp.cpp`, no PCH: CommonLib's `<Windows.h>` clashes with
  `<winsock2.h>`), main-thread tasks, one request at a time. Endpoints and their fail-on-purpose cases:
  `docs/research/journals/bridge.md`. **MSVC build green** (`skse_build.sh build windows-dev`, cl 19.51, no
  warnings in our sources; ArgoniaBridge.dll 818,688 bytes in `MO2\mods\Argonia SKSE (dev only)`).
- Pure parts tested on the build VM: `bridge.protocol` ctest (protocol, JSON, console delta and refusals, save
  names, key chords, frame stats, `nav.h` A* with portal and failure causes): 17/17 ctest pass.
- `tools/bridge.py` (one client; SSH tunnel; token refresh; GameDown within one 20 s health interval; launch with
  zombie kill; pad with the 3 s cap; screenshot, oracle, booth) and `tools/tests/test_bridge.py`: 10 pass in
  0.94 s (fake plugin socket: ok, refusal, stale token, dead game, crash log while waiting, no reply, pad cap,
  frame difference, the release guard via `cmake -P` with ARGONIA_RELEASE=ON).
- `infra/gpu-box/bridge.ps1`: health, token, kill (taskkill of survivors), prepare [-Fresh] (copy the DLL into
  Data after `stack.ps1 on`), grab.
- 0.3 §a rewritten (our bridge carries the list), its SkyLink risk line replaced; PLAN §4 studio row.

**Not yet run: every L4 case.** The game slot never came (0.2's CS shader compile, then `stack.py verify`
hashing 69k files, still running at hand-off). One slot runs them all, under the GPU lock:

    tooling/job_guard.sh run --gpu bridge-live -- python3 -m tools.tests.bridge_live --save argoniariverwood --fresh --crash

(`--fresh` re-lays the profile so 0.2's seeded Community Shaders first-run setting is in; results to
`out/bridge/live.json`, stills to `out/bridge/`). It covers: ping and bad token; main-menu refusals of player and
save; load of a missing save; load of the base; player; console with output and a refused line; save then load;
teleport pos, cell QASmoke, an unknown cell; time 13.5 and 25; weather read, force, not-a-weather; quest, global,
av, inventory with their refusals; hit event (Flames on self), quest stage (setstage MQ101 5), W walk with anim
events, input over the cap and an unknown key, a wait_event that never comes; pad walk and pad cap; frametime
120, 5, and a missed budget; nav near and off-mesh; booth six views and a non-bound form; screenshot oracle and a
frozen frame; forced crash reported (must be <= 60 s) and a relaunch that kills the zombie. Expect fixes; the
riskiest: booth's free-camera fields, coc arrival detection, `PlayerCharacter::Update` slot 0xAD, SendInput
focus in the desktop session, whether cells are in the editor-id map.

**Still open after the slot:** the journal's results table and measured times; message 0.2 the call pattern
(below, sent unproved); `make check` (the `skse` part was red at hand-off from another lane's season globals,
`tools.argonia_world.regions.season --check`: not ours); the dev-only guard on a real `windows-release` build.
PLAN lines 49, 74, 103 and 249 still name SkyLink as the hands; outside this lane's paths, for the planner.

**Call pattern for 0.2:** `python3 tools/bridge.py player` (JSON to stdout; exit 0/1/2/3), `console <line>`,
`save <name>`, `load <name>`, `launch [--fresh]`, `health`, `pad '<seq>'`; in Python `from tools.bridge import
Bridge; Bridge().call("player")`. On the machine, `ping.ps1 -Command "player"` speaks the same protocol on the pipe.
