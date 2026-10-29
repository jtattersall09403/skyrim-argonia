# Lane 0.2-stack: report and hand-off (2026-10-29, ~20:40 UTC)

## Hand-off (the context mark was reached; the planner relaunches 0.2 fresh)

**Done, committed** (`0ddb29d` plus the hand-off commit that carries this file):
- `infra/gpu-box/stack.py`: `fetch` (Nexus API, GitHub, the S3 private cache, the old R2 vault; sha256 recorded or
  checked), `stage` (unpack, `pick` paths, a FOMOD interpreter with step visibility and condition flags, nested
  archives, `drop`, ini edits, masters check over every plugin, profile files, `installed.json` with every file's
  hash; a re-stage skips rows whose archive and manifest entry are unchanged, keys in `~/.argonia/stack/staged/`),
  `push` (changed mod folders as tars over scp, the profile, a portable `ModOrganizer.ini` for houseCARL), `install`,
  `menu`, `verify`, `masters`. Sets: `"set"` takes a name or a list; `--set combat=souls-0.0|dsc-b|dsc-b2`.
- `infra/gpu-box/stack.ps1` (was `combat-mode.ps1`): `off` (bare vanilla Data), `on` (hard links from
  `C:\argonia\MO2\mods\<id>` in modlist order: no second copy, exact undo by `off`), `pandora` (output into the
  `pandora-output` mod), `menu` (SKSE launch, data-loaded message `dispatch message (8)`, a still, plugin lines, crash
  check), `verify` (every recorded file's hash, and no unrecorded file in Data). `sunshine-apps.json` and
  `splash.ps1` point at it. None of it has run on the machine yet.
- `infra/gpu-box/saves.sh`: backup to `s3://argonia-saves-050977237313/saves/<stamp>.zip` + `latest.zip`, restore
  (keeps the machine's current saves as a zip first); `run.sh stop` calls backup; `run.sh get` added.
  **Round trip proved**: 8 save files hashed, backed up (9.0 MB), restored, hashed again: identical.
- `infra/gpu-box/pad.ps1`: ViGEm virtual Xbox 360 pad sequences (Nefarius.ViGEm.Client 1.21.256, MIT, NuGet
  sha256 ff460031…fdb55e; DLL on the machine at `C:\argonia\tools\vigem`). Proved: a press reached the bus.
- `infra/gpu-box/skylink.ps1`: SkyLink's pipe `\\.\pipe\SkyrimMCP`, newline JSON `{"id","action","params"}`
  (read from its `Protocol.cpp`; actions include `get_player_info`, `execute_command`, `teleport`, `poll_events`,
  `save_game`, `get_loaded_skse_plugins`). Untested in game.
- `infra/gpu-box/housecarl.ps1`: an MCP stdio client for houseCARL's `housecarl-mcp.exe`; .NET 10.0.14 runtime
  installed on the machine at `C:\argonia\tools\dotnet`. Untested.
- `infra/gpu-box/controlmap.py`: RT added to Right Attack/Block; Toggle POV unbound (R3 is TDM's lock key).
- `data/dependencies.json`: 98 rows in load order, groups core, combat (sets souls-0.0 / dsc-b / dsc-b2 per
  `docs/research/2026-10-29/combat-mod-28567.md` §5, DSC 28567/104449 added, not trialled), traversal, soul-ui,
  land, pipeline (7 Skyrim LE sources, fetched, never laid), dev (SkyLink 175682, houseCARL 181738 as a tool).
  Every archive fetched and its sha256 recorded (15 GB in `~/.argonia/mods`; BM&V 9.65 GB also cached at
  `s3://argonia-private-050977237313/mods/vault-bmv.tar`). Fields still missing: `permission_summary`,
  `ai_clause`, `licence`, `runtime`, `conflicts`, `linked_or_forked_by`.

**Running now:** `stack-stage` (`tooling/job_guard.sh status stack-stage`; log `~/.argonia/jobs/stack-stage.log`,
already started with `python3 -u` under `systemd-run --scope -p MemoryMax=3G /usr/bin/time -v`). It re-stages
housecarl as a tool, bmv (unrar of 9 GB, about 6 min), and any rows whose manifest entry changed, then writes the
profile. Earlier passes: 9 min 35 s cold, peak RSS 998 MB. The permission child writes
`/tmp/claude-1000/-home-ubuntu-skyrim-argonia/00aec70d-9f88-4179-b6de-7faca8084fef/scratchpad/perms.json` (keyed
`<game>-<modid>`, with licence, permission_summary, ai_clause in four fixed forms, ask, evidence); merge it into the
manifest rows when it lands. The game machine is running (skse-build lane on it too); do not stop it.

**Left, in order:**
1. When the stage finishes green: `stack.py push`, then on the machine `stack.ps1 off`, `stack.ps1 pandora`
   (desktop session), `stack.py menu`. Expect fixes: FOMOD defaults (`stack.py` `fomod()`), and any DLL that does
   not load on 1.7.104 (each DLL's line comes from `stack.ps1 menu`). Brief §a: replace or drop with the loss written.
2. The dodge fix (§c). **Finding: AMR is not missing.** 0.0 installed the 1.7.104 AMR DLL (191697) and SKSE logged
   `AnimationMotionRevolution.dll ... loaded correctly`; the brief's cause is unproved. AMR 50258's base is now in
   the stack as well (the brief asks for it). Seen in the 0.0 logs: `TK_Dodge_RE.log` "On Dodge spell lookup failed"
   and "PerkEntryPointExtender.dll not found" (soft requirements). TK Dodge's own key was `uDodgeKey = 274` (LB),
   which is the "shadowed LB"; the manifest now sets `bUseSprintKey = true`, `uDodgeKey = 255` (unused) so B's tap
   dodges and its hold runs. Dynamic Dodge's clips carry `animmotion` annotations (AMR's format). Measure a roll's
   distance with `skylink.ps1` (`get_player_info` before and after) driven by `pad.ps1`; if it is 0, try without
   Dynamic Dodge (TK Dodge SE's own clips) to split AMR from OAR.
3. RT heavy (§c): OCPA's config already said 281; its hook is `AttackBlockHandler::ProcessButton`, which sees only
   buttons bound to an attack, and 0.0's controlmap left RT unbound. Fix made in `controlmap.py` (RT on Right
   Attack/Block); regenerate `C:\argonia\controls\controlmap.txt` from the player's Interface archive and prove a
   power attack. LB block: unchanged. Lock-on: TDM's `uTargetLockKey = 273`, `bTargetLockUsePOVSwitchGamepad = 0`
   set in the manifest.
4. houseCARL conflict report (`housecarl.ps1 -List`, then its load-order and conflict tools), the smoke scene twice
   (§c), Dear Diary stills, frame time and latency (§d; not while the `skse-build` job runs), `stack.py verify`,
   `stack.py masters` (to `$ARGONIA_GAME_ROOT` = `~/games/skyrimse` on the build VM), permission drafts under
   `$ARGONIA_PRIVATE/permission-drafts/` (`ARGONIA_PRIVATE` is unset on the build VM: choose and record it), the
   sourcing register rows, `infra/README.md`, decision 0007's numbers, the journal, 0.2's Outcome, 0.3's Starting
   state, PROGRESS row 0.2, then `combat_test_stage.py` and `combat-test-mods.json` deleted (superseded; two docs
   cite them: `docs/phases/1-core-loop/1.6-fight-on-the-stack.md:12`, `docs/decisions/0019…:47`).

**Reds and decisions taken:**
- **AWS month-to-date is $357.47** (`tools/cost_report.py`: EC2 compute $273.65, tax $59.58), against the $100
  budget of decision 0008. For the planner and the owner now.
- The machine's role cannot write S3 and the build role may not change IAM (refused), so saves are carried by the
  build VM (`saves.sh`, on `run.sh stop`). A stop by the play-switch Worker after an owner session does not back up.
  Owner step that would close it: give `argonia-play-ssm` `s3:PutObject`/`GetObject` on `argonia-saves-*`.
- Plugins needing USSEP (Xalfek, Seashells) are laid as assets only; Boats Operational's ferry ESP dropped (needs an
  ESP the FOMOD did not install); BM&V lays `Black Marsh.esm` and its loose data, not Valenwood or Black Marsh North.
- SkyParkour, SSE Engine Fixes and USSEP are not in the stack (coexistence untested; Engine Fixes for 1.7.x is a beta).
