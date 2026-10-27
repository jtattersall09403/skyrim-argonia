# P1: Nine go/no-go spikes

**Goal.** Prove, on samples, every assumption the architecture rests on before building on it. Each spike has a
gate (G1–G9) with a pass condition, a time budget (working days of lane time), listed workarounds and a
consequence if it fails. Spike code lives in `spikes/<id>/` unless the spike says its output becomes the real
component.

**Starting state.** P0 exit gate passed: toolchain, guards, gate, world imported, game files on the build VM.

**Re-check before starting:** Skyrim's current Steam version and SKSE builds (silverlock), the Address Library
version, each candidate mod's latest file and supported runtimes, Proton and Selkies versions, GPU spot prices in
eu-west-2. Record what changed in `docs/research/`.

**Read first.** Decisions 0001, 0002, 0004, 0007, 0008, 0010, 0014; research
[skyrim-tooling](../research/2026-10-27/skyrim-tooling.md) (§0–3, §5–7),
[skyrim-morrowind-soul](../research/2026-10-27/skyrim-morrowind-soul.md) §1, §5,
[skyrim-combat-traversal](../research/2026-10-27/skyrim-combat-traversal.md) §0–1, §4,
[um-ghidra-lens](../research/2026-10-27/um-ghidra-lens.md) §3A, §1.3–1.4,
[hosting-streaming](../research/2026-10-27/hosting-streaming.md).

**Order and dependencies.** S0 first (it creates the GPU box). Then **S1** (bridge) while the build-VM-side
spikes **S4** and **S6** run in parallel. **S3** needs S1's bridge with its input endpoint. **S2**, **S5**, **S7** and
**S9** need S3's stack. **S8** composes everything and runs last. With the 5x plan run at most two lanes at once,
and only one lane drives the GPU box at a time (`job_guard.sh --gpu`).

## S0: The GPU box (prerequisite, not a gate; budget 3 days)
- `infra/gpu-box/create.sh`: launch template for `argonia-play` (g6.xlarge spot, persistent, stop on
  interruption; fallbacks g4dn.xlarge, g5.xlarge), Ubuntu 24.04, NVIDIA driver, 150 GiB gp3, same VPC/AZ as the
  build VM; security group: SSH from the build VM only, the Selkies port from the owner's IPs (or behind auth on
  443). Tag `project=argonia`.
- `infra/gpu-box/setup.sh`: Steam client (Linux), Proton (pinned in the lock file), protontricks, headless X
  (Xorg with the NVIDIA driver and a virtual display, or gamescope headless), PipeWire for audio, Selkies
  (linuxserver.io build) with authentication, Crash Logger SSE, aws cli for save backup, an idle-stop timer
  (15 minutes with no stream client and no GPU lock held).
- **Owner step (O-7):** log in to Steam through the Selkies stream once and approve Steam Guard; then set Steam
  offline and disable updates for Skyrim SE. Install Skyrim SE and Dark Souls Remastered on the box.
- **Steam refresh:** Steam's offline mode needs an online login every couple of weeks. `infra/gpu-box/steam_check.sh`
  runs at each box start; if Steam refuses an offline launch, the agent loop stops GPU work, posts an owner
  check-in asking for a re-login through the stream, and continues with build-VM work.
- Record the Skyrim depot manifest ids in `infra/README.md` (decision 0002).

## S1 → G1: SKSE plugin built on Linux, loading under Proton, with a minimal agent bridge (budget 6 days)
- Build a hello-world CommonLibSSE-NG plugin from the build VM: route (a) msvc-wine (`cl`/`link` under Wine,
  CMake + Ninja, vcpkg cross triplet); if blocked, route (b) clang-cl + xwin + **MSVC `link.exe`** (NG's wiki:
  `lld-link` loses the exports), or explicit `.def` exports with lld-link. Address Library for the candidate
  runtime(s).
- The plugin is the seed of `ArgoniaBridge`. It binds an HTTP server to **127.0.0.1 only** on the GPU box, with a
  per-boot token; the build VM reaches it through an SSH tunnel (`ssh -L`), never over an open port. Endpoints:
  `/ping`, `/console` (a console command on the main thread via the SKSE task interface), `/teleport`
  (`coc`/`setpos`), `/state` (position, cell, frame counter), `/screenshot` (D3D11 backbuffer copy → PNG + hash),
  `/input` (queue keyboard/gamepad events: move, attack, block, dodge, activate, menu). Patterns: SkyrimNet's MCP
  server; universal-modder's command-file bridge as the fallback.
- Launch `skse64_loader.exe` under Proton directly (no launcher, `SteamAppId=489830`, ini files pre-written),
  with `plugins.txt`/`loadorder.txt` written by script (no MO2).
- A minimal `make deploy` (rsync the built DLL/plugin to the box, restart the game, wait for `/ping`).
- **G1 passes when:** from the build VM, a script starts the GPU box, deploys, launches the game to a test cell,
  calls every endpoint (an `/input` walk changes `/state` position), gets two screenshots whose hashes differ while
  the camera turns, and stops the box, with no human action.
- **If it fails:** try both build routes and two Proton versions; then a temporary Windows spot instance (costed
  first, within P1's budget in decision 0008) to separate "build" from "run". If running under Proton is the
  failure, decision 0001's fallback applies (owner re-plan).

## S2 → G2: Streaming and performance (budget 4 days)
- Install the S3 stack and stand in a busy test scene (dense Tropical Skyrim/BM&V trees, water, 10 NPCs).
- Benchmark 1080p frame times on g6.xlarge (L4), g4dn.xlarge (T4) and g5.xlarge (A10G) with Community Shaders on
  and off: median and 1% lows, CPU vs GPU bound (Skyrim is often CPU-bound on cloud Xeons).
- **Owner session (20–30 min):** play the scene through Selkies on the phone (home Wi-Fi, then 5G; folded and
  unfolded) and on the work Mac (WebSocket/TCP-443 mode if UDP is blocked). Record Selkies' RTT/stats overlay,
  bitrate and codec, the owner's verdict on input feel (walk, swing, roll; a parry timing test against a scripted
  enemy), and **readability**: can the owner read the dialogue window's text, the HUD and a menu list on the phone
  in both screen shapes (the Magic V5 folded is ~21:9, unfolded near square).
- **G2 passes when:** one instance type holds ≥ 60 fps median and ≥ 45 fps 1% lows in the scene, within budget,
  and the owner rates streaming "playable" and text "readable" on Wi-Fi on both devices. Record the instance,
  codec, bitrate, UI scale and the per-hour cost in `infra/README.md` and decision 0007.
- **If it fails:** Moonlight-Web + Sunshine; 900p and AV1 on L4; lighter shader settings; a larger UI scale. If
  the owner still rejects the feel, stop and re-plan with the owner.

## S3 → G3: Runtime pin and the full dependency stack under Proton (budget 6 days)
- The candidate list is the **union of every phase's dependencies**, not just the core:
  - Core: SKSE, Address Library, an engine-fixes mod for the runtime, PapyrusUtil, po3 Papyrus Extender,
    ConsoleUtil Extended, Crash Logger, Fuz Ro D-oh (silent lines, decision 0014 §6).
  - Behaviour/animation: Pandora Behaviour Engine Plus, OAR (+ its Math plugin, + Animation Queue Fix), AMR/AMF,
    Payload Interpreter, XPMSSE.
  - Combat: Precision (on 1.7.x only through the unofficial third-party port, Nexus 189664: a separate manifest row
    with its own permission), TDM, TrueHUD, BFCO (+ MCM Helper), SCAR, CPR, Ultimate NPC Dodging, Wait Your Turn,
    TK Dodge RE/Redux (+ I-Frame Generator), Elden Parry, XP32 True Ragdoll.
  - Traversal: FreeClimb, SkyParkour (check coexistence with FreeClimb), EVG Animated Traversal, Underwater NG,
    Sailable Ship, Throwable Weapons SKSE (+ NPC add-on).
  - Soul/UI: Custom Skills Framework, Sleep to Gain Experience (pattern/reference), Respawn – Soulslike
    (pattern), SkyUI 6, Infinity UI, PrismaUI (pin the version), Flat World Map Framework, No Google Maps
    Skyrim, Wayfinder (pattern), RaceMenu (only if P4 chargen needs it), Community Shaders.
  - Assets: Tropical Skyrim SSE (78044), Black Marsh & Valenwood, King of the Murkmire (needs the Creation Club/AE
    archives: a 1.5.97 pin would drop it), the Xanmeer tileset, the other P2-WP2.1 asset mods.
- For each candidate runtime (1.6.1170 via depot rollback, 1.7.104 current): install, run Pandora under Proton
  (`protontricks 489830 dotnetdesktop8`, d3dcompiler_47/43; generate behaviours on the GPU box itself, never copy
  Windows-generated output), launch, and run the smoke scenario through the bridge (load a cell, walk, swing,
  dodge, climb a wall, swim, open each menu). Read Crash Logger output.
- **G3 passes when:** one runtime loads the whole stack with no crash and the smoke scenario passes. That runtime
  is the pin (decision 0002; owner confirms O-3). Mods that fail on the pinned runtime are dropped or replaced and
  the loss is written into the affected phase.

## S4 → G4: A world sample without the Creation Kit (budget 8 days)
Sample: an 8×8-cell block containing an owner-accepted place from the old repo (Claywater Station or
Greenspring) and a road.
- **Terrain:** heightfield → LAND (VHGT offsets + int8 deltas, re-based per row for cliffs), VNML, VCLR, up to 6
  texture layers per quadrant from the land-cover classes (Tropical Skyrim textures first, decision 0006 §8), via
  ArgoniaGen + Mutagen.
- **Kit-id mapper:** the old layouts name GLB kit pieces and composites, not plugin records. Build
  `tools/argonia_world/kit_to_base.py`: kit piece id → source plugin + base record FormID (from the old kit
  manifests and mined placement data), composites → several REFRs (or an SCOL), mod meshes without a base record →
  a new STAT of ours pointing at the mod's mesh path. L1 check: every layout op resolves.
- **Place:** layout ops → REFRs (metres ×70.03, ZYX Euler, NIF root rotation rules from old 0135); its interior
  through the plugin's load door (old 0114); a sea/river water plane.
- **Navmesh:** (a) convert a Recast bake of the generated geometry into NAVM records (vertices, triangles, edge
  links, door and water flags, cross-cell portals) and NAVI; (b) if (a) is not walkable, the Creation Kit's
  navmesh generator under Wine on Xvfb driven by a GUI macro, captured to Spriggit; (c) a Windows box with the CK,
  costed.
- **Faces (decision 0014 §3):** three new NPCs (two Argonians, one Imperial). (a) template NPCs (TPLT) reusing
  existing face data; (b) the CK's FaceGen export under Wine *for development only*, plus a design for the
  installer to do the same on players' machines; (c) our own FaceGen generator from the race's head parts, run by
  the installer. Argonian heads are the critical case.
- NPCs get a sandbox package at the place and a sleep package at night.
- **G4 passes when:** in game, the player walks the road into the place and its interior, ground heights match
  the heightfield within 0.5 m at sampled points, NPCs path between two spots (no standing still), faces are not
  dark, every layout op resolved, and regenerating twice gives identical Spriggit output.
- **If it fails:** navmesh or faces unsolved after (a)–(c) → decision 0001's fallback re-plan with the owner.

## S5 → G5: The Morrowind dialogue window (budget 6 days)
- PrismaUI view `ui/views/dialogue/`: NPC text with hyperlinked keywords, a topic list on the right, greeting on
  open, persuasion button, Goodbye; Pelagiad; the old palette; gamepad, mouse and keyboard navigation; tested at
  1920×1080, 1280×720 and the phone's two aspect ratios.
- ArgoniaCore stub: on talking to an NPC, intercept vanilla dialogue (study Enderal's DialogueMenu hook, Dialogue
  History and Dynamic Dialogue Replacer), open the view, supply topics and responses from a small JSON, evaluate
  three condition kinds (disposition ≥ N, knows-topic, quest stage), learn a topic when its keyword is clicked,
  persist the learned set in the SKSE co-save.
- Evaluate whether the old repo's TypeScript dialogue runtime (`packages/dialogue`, `packages/narrative`) can run
  inside the view's JavaScript context as the evaluator, with C++ providing only game state. Choose the simpler
  of the two for P4 and record why.
- **G5 passes when:** the view passes L3 tests against mock JSON, and in game a topic learned from NPC A appears
  when talking to NPC B; disposition changes which response shows; save/load keeps the learned set; it works
  through the stream with a gamepad.
- **If it fails:** the Skywind approach (topics as Skyrim player prompts gated by conditions in the vanilla menu,
  restyled per 0014 §7) with a written loss of the hyperlink feel, agreed with the owner.

## S6 → G6: Measuring Dark Souls Remastered (budget 4 days)
- With soulstruct on the build VM (unpack with UXM under Wine if the files soulstruct needs are not loose):
  export `BehaviorParam_PC`, `AtkParam_Pc`, `EquipParamWeapon`, `EquipParamProtector`, `NpcParam` (poise
  `superArmorDurability`), `ThrowParam` rows with Paramdex DS1R names to JSON in `$ARGONIA_PRIVATE` (never
  committed).
- Roll i-frames: read the c0000 TAE invincibility events for the fast, mid and fat rolls and the ninja flip with
  DSAnimStudio (wow64 Wine on the build VM, or a temporary Windows spot instance if it fails under Wine).
- Live capture plan: DSR under Proton on the GPU box, Steam offline, a backed-up separate save, no proxy DLLs
  online; 60 fps video of 20 rolls, window read from frames (the fallback if TAE reading fails).
- **G6 passes when:** the golden table has measured rows (with provenance) for roll i-frames at each equip tier,
  the parry window of one small and one medium shield, a straight sword R1's startup/active/recovery, and the
  poise pool and poise damage of one armour set and one weapon. G6 gives the **first answer** to the 13/11/9
  question (written to decision 0004); P5-WP5.1 confirms it with the full table.
- **If it fails:** soulsmodding.com and frame-data compilations as `WIKI:` provenance, flagged for re-measurement;
  this does not block the plan.

## S7 → G7: Swimmable stepped rivers (budget 4 days)
- In the S4 block, one river reach dropping 4 m over 200 m modelled as Skyrim does: placed water planes or meshes
  stepped along the reach with a small vanilla waterfall/rapids piece at each step (old 0064), plus the cell's own
  water height where the river is flat.
- Check: the player and an NPC swim in each plane; diving and breath work (Underwater NG); no z-fighting at steps.
- **Flow:** Skyrim's flowing water uses a per-water-type flowmap painted in the Creation Kit (one flow worldspace
  per plugin). Try to generate a flowmap ourselves from the reach directions; else accept still water on rivers
  and record the visual loss.
- If submersion on a placed plane misbehaves and records do not explain it, this is the first allowed Ghidra
  question (decision 0010 §4): find how the engine resolves which water a point is in.
- **G7 passes when:** swim checks pass and flow is either generated or its loss recorded. **If it fails:** keep
  rivers flat per cell segment (one water height per cell, terrain re-graded at cell borders) and record the loss.

## S8 → G8: The agentic loop, end to end (budget 3 days)
- A `deliver-small` agent, given only a brief, changes one record (an NPC's greeting), regenerates the plugin,
  deploys it (`make deploy`), runs a scenario (talk to the NPC, read the response through the bridge), and reports
  pass/fail, without human help.
- **G8 passes when:** the loop runs unattended three times in a row and the median cycle (edit to verdict) is
  under 10 minutes including GPU-box start; cost per cycle is recorded. **This cycle time feeds the
  re-estimate of every later phase (PLAN §5).**

## S9 → G9: DS1 timing without shipping edited animations (budget 5 days)
- Decision 0014 §2. On one roll, one straight-sword light attack and one shield parry: drive timing at runtime
  (our plugin changes playback speed inside windows through graph variables / Payload Interpreter / AMR and opens
  our i-frame/parry/active windows from animation events), measure with an early version of the P5 test dummy.
- If a window cannot be met at runtime, prototype the **install-time patcher**: our annotation/timing delta applied
  to the player's own copy of the clip, never committed or shipped.
- **G9 passes when:** the three actions hit their (G6) windows within ±1 DS1 frame at 60 fps with runtime control,
  or with the patcher, and the method is written into decision 0014. **If it fails:** the owner decides between
  looser timing (recorded deviations) and a different moveset source.

## Exit gate
All of G1–G9 pass, or a gate's documented fallback is accepted by the owner in writing. Decisions 0001, 0002,
0004, 0007 and 0014 are updated with the measured facts. The P1 owner check-in reports each gate with evidence
(frame times, screenshots, the stream verdict, golden-table rows), the costs so far, the re-estimate of P2–P10,
and the O-3/O-6 asks.

## Risks and fallbacks
- **PrismaUI** (single author, restrictive licence) fails or breaks: pin its version in S3; each S3 screen keeps a
  fallback (decision 0001 §2, 0014 §7).
- **Steam offline refresh** interrupts unattended GPU work: the S0 check script and owner re-login step.
- **Windows-only tools** (DSAnimStudio, UXM, the CK) fail under Wine: a temporary Windows spot instance within the
  P1 budget, stopped after use.

## Deliberately out of scope
Polishing spike code beyond what P2 adopts; content beyond the samples; combat implementation beyond G9 (P5).
