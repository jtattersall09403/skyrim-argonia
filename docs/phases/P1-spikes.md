# P1: Eight go/no-go spikes

**Goal.** Prove, on samples, every assumption the architecture rests on before building on it. Each spike has a
gate (G1–G8) with a pass condition, a time budget, listed workarounds and a consequence if it fails. Spikes
are throwaway-quality code in `spikes/<id>/` unless the spike says its output becomes the real component.

**Starting state.** P0 exit gate passed: toolchain, guards, gate, world imported, game files on the build VM.

**Read first.** Decisions 0001, 0002, 0004, 0007, 0008, 0010; research
[skyrim-tooling](../research/2026-10-27/skyrim-tooling.md) (§1–3, §5–7),
[skyrim-morrowind-soul](../research/2026-10-27/skyrim-morrowind-soul.md) §1, §5,
[um-ghidra-lens](../research/2026-10-27/um-ghidra-lens.md) §3A, §1.3–1.4,
[hosting-streaming](../research/2026-10-27/hosting-streaming.md).

**Order.** S0 first (it creates the GPU box). Then S1 and S3 in parallel with S4 and S6 (build-VM-side work),
then S2, S5, S7, and S8 last (it composes the others). With the 5x plan run at most two lanes at once.

## S0: The GPU box (prerequisite, not a gate)
- `infra/gpu-box/create.sh`: launch template for `argonia-play` (g6.xlarge spot, persistent, stop on
  interruption; fallbacks g4dn.xlarge, g5.xlarge), Ubuntu 24.04, NVIDIA driver, 150 GiB gp3, same VPC/AZ as the
  build VM, security group allowing only the build VM (SSH, bridge port) and the owner's stream port. Tag
  `project=argonia`.
- `infra/gpu-box/setup.sh`: Steam client (Linux), Proton (pin a version in the lock file), protontricks,
  headless X (Xorg with the NVIDIA driver and a virtual display, or gamescope headless), PipeWire for audio,
  Selkies (linuxserver.io build) with basic auth, Crash Logger SSE, rclone/aws for save backup, an idle-stop
  timer (15 min with no stream client and no bridge job).
- **Owner step (O-7):** log in to Steam through the Selkies stream once and approve Steam Guard; then set Steam
  offline and disable updates for Skyrim SE. Install Skyrim SE and Dark Souls Remastered on the box.
- Record the Skyrim depot manifest ids in `infra/README.md` (decision 0002).

## S1 → G1: SKSE plugin built on Linux, loading under Proton, with a minimal agent bridge
- Build a hello-world CommonLibSSE-NG plugin from the build VM: route (a) msvc-wine (`cl`/`link` under Wine,
  CMake + Ninja, vcpkg cross triplet); if blocked, route (b) clang-cl + xwin + **MSVC `link.exe`** (NG's wiki: `lld-link`
  loses the exports), or explicit `.def` exports with lld-link. Address Library for the pinned runtime(s).
- The plugin is the seed of `ArgoniaBridge`: on load it opens a localhost HTTP server on the GPU box and serves
  `/ping`, `/console` (run a console command on the main thread via the SKSE task interface), `/teleport`
  (`coc`/`setpos`), `/state` (player position, cell, frame counter), `/screenshot` (D3D11 backbuffer copy,
  returning a PNG and its hash). Pattern: SkyrimNet's MCP server; command-file fallback from universal-modder.
- Launch `skse64_loader.exe` under Proton directly (no launcher, `SteamAppId=489830`, ini files pre-written),
  with `plugins.txt`/`loadorder.txt` written by script (no MO2).
- **G1 passes when:** from the build VM, a script starts the GPU box, launches the game to a test cell, calls
  every endpoint, gets two screenshots whose hashes differ while the camera turns, and stops the box, with no
  human action. Time budget 6 working days.
- **If it fails:** try both build routes and two Proton versions; then try building on a temporary Windows
  EC2 instance (spot g4dn Windows, costed first) to separate "build" from "run". If run under Proton is the
  failure, decision 0001's fallback applies (owner re-plan).

## S2 → G2: Streaming and performance
- Install the candidate dependency stack (from S3) and stand in a busy test scene (dense trees, water, 10 NPCs).
- Benchmark 1080p frame times on g6.xlarge (L4), g4dn.xlarge (T4) and g5.xlarge (A10G) with Community Shaders
  on and off: median and 1% lows, CPU vs GPU bound (Skyrim is often CPU-bound on cloud Xeons).
- **Owner session (20–30 min):** play the scene through Selkies on the phone (home Wi-Fi, then 5G) and on the
  work Mac (WebSocket/TCP-443 mode if UDP is blocked). Record Selkies' RTT/stats overlay, the bitrate and codec,
  and the owner's verdict on input feel (walk, swing, roll; a parry timing test against a scripted enemy).
- **G2 passes when:** one instance type holds ≥ 60 fps median, ≥ 45 fps 1% lows in the scene within budget,
  and the owner rates streaming "playable" on Wi-Fi on both devices. Record the chosen instance, codec,
  bitrate and the per-hour cost in `infra/README.md` and decision 0007.
- **If it fails:** try Moonlight-Web + Sunshine; lower resolution (900p) and AV1 on L4; lighter Community
  Shaders settings. If the owner still rejects the feel, stop and re-plan with the owner (options: a Windows PC
  or Steam Deck for local play later; streaming only for checks).

## S3 → G3: Runtime pin and the dependency stack under Proton
- Candidate stack (research skyrim-combat-traversal §5 and skyrim-morrowind-soul): SKSE, Address Library,
  Engine Fixes (or equivalent for the runtime), PapyrusUtil, po3 Papyrus Extender, ConsoleUtil Extended,
  Pandora Behaviour Engine Plus, OAR (+ Animation Queue Fix), Precision, TDM, TrueHUD, BFCO (+ AMR, Payload
  Interpreter, MCM Helper, XPMSSE), SCAR, CPR, TK Dodge RE/Redux, Elden Parry, FreeClimb, SkyParkour (check its
  compatibility with FreeClimb), EVG Animated Traversal, Underwater NG, Custom Skills Framework, Sleep to Gain
  Experience, SkyUI 6, Infinity UI, PrismaUI, Flat World Map Framework, No Google Maps Skyrim, Community
  Shaders, XP32 True Ragdoll, Crash Logger.
- For each candidate runtime (1.6.1170 via depot rollback, 1.7.104 current): install, run Pandora under Proton
  (`protontricks 489830 dotnetdesktop8`, d3dcompiler_47/43; generate behaviours on the GPU box itself, never
  copy Windows-generated output), launch, and run the smoke scenario (load a cell, swing, dodge, climb a wall,
  swim, open each menu) through the bridge. Read Crash Logger output.
- **G3 passes when:** one runtime loads the whole stack with no crash and the smoke scenario passes. That runtime
  is the pin (decision 0002, owner confirms O-3). Mods that fail on the pinned runtime are dropped or replaced
  and the loss is written into the affected phase.

## S4 → G4: A world sample without the Creation Kit
Sample: an 8×8-cell block containing an owner-accepted place from the old repo (Claywater Station or
Greenspring) and a road.
- **Terrain:** heightfield → LAND (VHGT offsets + int8 deltas, re-based per row for cliffs), VNML, VCLR, up to
  6 texture layers per quadrant from the land-cover classes, via ArgoniaGen + Mutagen.
- **Place:** layout ops → REFRs (metres ×70.03, ZYX Euler, base records from the source plugins); its interior
  through the plugin's load door (old 0114); a sea/river water plane.
- **Navmesh:** (a) convert the old Recast bake (or a fresh Recast bake from the generated geometry) into NAVM
  records (vertices, triangles, edge links, door and water flags, cross-cell portals) and NAVI; (b) if (a) is
  not walkable, the Creation Kit's navmesh generator under Wine on Xvfb driven by a GUI macro, with the result
  captured to Spriggit; (c) as a last resort, a Windows box with the CK, costed.
- **Faces:** three new NPCs (two Argonians, one Imperial). Try in order: (a) template NPCs (TPLT) from vanilla or
  mod NPCs with matching looks; (b) the CK's FaceGen export under Wine; (c) generating FaceGen NIF and tint
  ourselves from the race's head parts (research first). Argonian heads are the critical case.
- NPCs get a sandbox package at the place and a sleep package at night.
- **G4 passes when:** in game, the player walks the road into the place and its interior, the terrain matches the
  heightfield within 0.5 m at sampled points (bridge reads `GetPositionZ` on ground), NPCs path between two
  spots (no standing still), faces are not dark, and regenerating the plugin twice gives identical Spriggit
  output. Time budget 8 working days.
- **If it fails:** navmesh or faces unsolved after (a)–(c) → decision 0001's fallback re-plan with the owner.

## S5 → G5: The Morrowind dialogue window
- PrismaUI view `ui/views/dialogue/`: NPC text with hyperlinked keywords, a topic list on the right, greeting on
  open, persuasion button, Goodbye; Pelagiad font; the old palette; gamepad, mouse and keyboard navigation.
- ArgoniaCore stub: on talking to an NPC, intercept the vanilla dialogue (study Enderal's DialogueMenu hook and
  Dialogue History / Dynamic Dialogue Replacer for the pattern), open the view, supply topics and responses from
  a small JSON for that NPC, evaluate three condition kinds (disposition ≥ N, knows-topic, quest stage), learn a
  topic when its keyword is clicked, persist the learned set in the SKSE co-save.
- Evaluate whether the old repo's TypeScript dialogue runtime (`packages/dialogue`, `packages/narrative`) can run
  inside the view's JavaScript context as the condition evaluator, with C++ providing only game state. Choose the
  simpler of the two for P4 and record why.
- **G5 passes when:** the view passes L3 tests in headless Chrome against mock JSON, and in game a learned topic
  from NPC A appears when talking to NPC B; disposition changes which response shows; the save/load round trip
  keeps the learned set; it works through the stream with a gamepad.
- **If it fails:** the fallback is the Skywind approach (topics as Skyrim player prompts gated by conditions in
  the vanilla menu, reskinned) with a written loss of the hyperlink feel, agreed with the owner.

## S6 → G6: Measuring Dark Souls Remastered
- With soulstruct on the build VM (native Python): export `BehaviorParam_PC`, `AtkParam_Pc`, `EquipParamWeapon`,
  `EquipParamProtector`, `NpcParam` (poise `superArmorDurability`), `ThrowParam` rows with Paramdex DS1R names to
  JSON in `$ARGONIA_PRIVATE` (never committed).
- Roll i-frames: read the c0000 TAE invincibility events for the fast, mid, fat rolls and the ninja flip with
  DSAnimStudio (under Wine on the build VM, or on the GPU box, or a Windows instance if neither works).
- Live capture plan: DSR under Proton on the GPU box, Steam offline, a backed-up separate save, no proxy DLLs
  online; record 60 fps video of 20 rolls and read the window from frames (the fallback if TAE reading fails).
- **G6 passes when:** the golden table has measured rows (with provenance) for roll i-frames at each equip tier,
  the parry window of one small and one medium shield, a straight sword R1's startup/active/recovery, and the
  poise pool and poise damage of one armour set and one weapon; the 13/11/9 question is answered (decision 0004
  updated). Time budget 4 working days.
- **If it fails:** use the soulsmodding.com wiki and frame-data compilations as `WIKI:` provenance, flagged for
  re-measurement; this does not block the plan.

## S7 → G7: Swimmable stepped rivers
- In the S4 block, model one river reach dropping 4 m over 200 m as Skyrim does: placed water planes or meshes
  stepped along the reach with a small waterfall at each step (old 0064: waterfalls are the vanilla kit), plus the
  cell's own water height where the river is flat.
- Check: the player and an NPC swim in each plane, diving and breath work (Underwater NG), the surface renders
  without z-fighting at steps, and flowing-water visuals follow the reach direction.
- If the submersion test on a placed plane misbehaves and records do not explain it, this is the first allowed
  Ghidra question (decision 0010 §4): find how the engine resolves the water a point is in.
- **G7 passes when:** all checks pass in game. **If it fails:** keep rivers flat per cell-segment (one water
  height per cell, terrain re-graded at cell borders) and record the visual loss.

## S8 → G8: The agentic loop, end to end
- A `deliver-small` agent, given only a brief, changes one record (an NPC's greeting), regenerates the plugin,
  deploys it to the GPU box (`make deploy`: rsync the built plugin and DLLs, restart the game), runs a scenario
  (talk to the NPC, read the response through the bridge), and reports pass/fail, without human help.
- **G8 passes when:** the loop runs unattended three times in a row and the median cycle (edit to verdict) is
  under 10 minutes including GPU box start; cost per cycle is recorded.

## Exit gate
All of G1–G8 pass, or a gate's documented fallback is accepted by the owner in writing. Decisions 0001, 0002,
0004 and 0007 are updated with the measured facts. The P1 owner check-in reports each gate with evidence (frame
times, screenshots, the stream verdict, the golden-table rows), the costs so far, and O-3/O-6 asks.

## Deliberately out of scope
Any polish of spike code beyond what P2 adopts; any content beyond the samples; combat implementation (P5).
