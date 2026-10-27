# The universal-modder / Ghidra-first lens for Argonia

Research date 2026-10-27. Everything cloned was read as data and nothing was executed. The clones are under
`/tmp/claude-0/-home-claude/4eae515a-2cd9-5a49-b7da-638a25d58e2a/scratchpad/ext/`:
- `universal-modder` @ c1dff21 (2026-10-20)
- `ghidra`, a sparse checkout of the docs only, @ 1b9e58a (2026-10-27)
- `Ghidrust` @ d2c42b6 (2026-08-23)
- `ds3-open-re` @ 91855b8 (2021-03-12)
- `faith-runner` (2026-10-15)
- `AC1-Movement-Rewritten` (2026-10-21)
- `GhidraMCP` (2026-10-10)
- `pyghidra-mcp` (2026-10-09)
- `reverse-engineering-assistant` (ReVa, 2026-10-27)
- `Paramdex` (2026-03-06)

The GitHub API was blocked in this session, so there are no star or release counts. Maturity is judged from
the code and the dates.

Evidence labels follow universal-modder's own scale (`knowledge/techniques/evidence-levels-for-mashup-claims.md`):
- **report**: the creator says it works;
- **source**: code or docs were read here;
- **run**: someone ran it and looked.

Nothing was run for this report.

---

## 0. Two framing facts before anything else

1. **The live Argonia repo is not OpenMW.** `/home/claude/elder-souls-argonia` is a Three.js 0.184 + R3F +
   Rapier 0.20 browser game (`apps/game/package.json`). It already has a "we never make art, source it"
   rule and a "take assets, never Papyrus/SKSE code" rule (`docs/world/90-asset-strategy.md` §71).
   - OpenMW as "candidate engine" would be a re-platform, not a lens. The lens itself (study the source
     game, then reimplement in your own engine) works for either engine.
   - Section 6 gives both targets where they differ.
2. **universal-modder is a mod-the-game-you-own toolkit, not an engine-building method.** Its strongest,
   best-verified results are:
   - data and loader mods inside the original game;
   - single mechanics transplanted into another host.

   "Build a new game from extracted mechanics" maps onto two of its seven routes: *subsystem transplant*
   and *engine recreation*. The evidence for those two is thinner, and the toolkit itself is candid about
   that.

---

## 1. universal-modder: what it is

MIT-licensed. It has:
- 12 Agent Skills (`skills/`);
- 3 subagents (`agents/`);
- the Python `um` CLI (`um/`);
- 122 game folders and 85 technique notes in `knowledge/` (about 40k lines in total);
- 9 worked examples (`examples/`).

It was released on 2026-09-30, rode the September 2026 "AI mashup" wave (SkyCraft and others), and was
covered by vidaextra, hardware.com.br and EverythingEdinburgh.

### 1.1 The loop (`skills/mod-any-game/SKILL.md`)
1. Intake, with an agreed "done" (usually "works in game + a 20–45 s clip").
2. `MODLOG.md` as the journal: "anything not in the journal is lost at the next context compaction".
3. Recon. First `um kb search` over prior field notes, then `um scan`, which fingerprints the engine,
   managed vs native code, anti-cheat, loaders, save folders and ranked routes.
4. **Pick the cheapest route**: data/assets → loader API → managed patching → native hooks →
   reimplement/decomp/recomp → mashup/passthrough.
5. Lab: `um backup`, lab profiles, windowed mode, decompiles kept outside the repo.
6. **Read the source of truth**: decompile, dump data, inspect live. "Check what the executable enforces
   as well as what the data says."
7. Vertical slice with placeholder art.
8. Assets: study the game's own, then generate with fal.
9. **Verify in the real game. "The running game is the oracle; your reading of the code is not."**
   Repeatable scripted tests, screenshots read at 0.33 scale, and a circuit breaker after 3 identical
   failures.
10. Clip, then `um publish check`, then a field note PR.

### 1.2 The routes for cross-game work (`skills/mashup-mods/SKILL.md`, `knowledge/techniques/choosing-a-mashup-route.md`)
Seven routes:
- live passthrough (state exchange);
- frame compositing;
- native geometry transfer;
- shared neutral simulation;
- **engine recreation** (one rebuilt engine reading the owner's data: IW4L, benilla, HL2-RS, SK8-ENGINE);
- **asset/map conversion**;
- **rebuilt guest mechanic in a real host** (Faith Runner, BullySkate, ER Mario, AC1 movement).

The mashup skill names five patterns:
1. Port the content (lightest). Read numbers from the decompile or the wiki, reimplement in the host's API,
   and convert assets from the user's install.
2. Passthrough.
3. Embed a decomp as a library (libsm64).
4. Reimplement, then fuse. IW4L: Rust/Bevy reading MW2 FastFiles, D3D9 shaders translated to WGSL.
5. Reimplement the guest's rules headless and keep the host as the view.

The advice that matters for Argonia:
- "Running the whole second game for one mechanic" is a named anti-pattern. A transplant is usually smaller.
- "Numbers matching is not behaviour matching." Faith Runner's doubled gravity is inferred, not found.
- List every substitution next to its feature.
- Write a parity document.
- "A shared language doesn't reconcile world IDs, coordinate systems, physics, input, entity lifecycle,
  animation, saves" (`engine-recreation-measures-and-fidelity.md`).

### 1.3 How it verifies (`knowledge/techniques/oracles-how-agents-know-a-mod-works.md`, `reverse-engineering/SKILL.md`)
- **Trace replay.** Record positions and velocities per tick in the real game and replay them against the
  port. In the Terraria Eye of Cthulhu port, velocity matched 99.9% once the t+1 action offset and float32
  constants were fixed. A hidden buff (x1.21) showed up only under replay.
- **Byte round trips for every format writer.** The AoE2 SLD writer passed at 0.9/255 mean error. In the
  DSR→ER port, the PARAM writer and the Wwise bank parser reproduce vanilla byte for byte.
- **Fitted visual models against reference captures.** White Knuckle's damage shader was fitted at
  rms 2.8/255, then confirmed by disassembly.
- **Headless game tests** (Fabric gametests) and a human ticking a numbered checklist per build.
- Evidence levels are kept strictly apart: a README, a design doc, a synthetic peer or a green test is not
  a run.

### 1.4 Capture and testing in a running game (`skills/game-automation`, `um win`)
- `um win launch/shot/record/drive/kill`: gfxcapture plus process-loopback audio, and input sent only to
  the game window.
- Mod-side command files and in-game agent bridges.
- RenderDoc (renderdoc-mcp) for view/projection matrices and depth.
- Cheat Engine, Frida and x64dbg MCP servers. Their advice: bind them to 127.0.0.1, because some default
  to 0.0.0.0.
- The agent split (`agents/mod-orchestrator.md`): one game worker, the only one that touches the running
  game, plus one offline worker that studies dumps and writes generators against stubs. The orchestrator
  checks every "DONE" against logs and files.

### 1.5 What it won't do (`skills/mod-any-game/references/safety.md`)
- No injection into online clients with anti-cheat. EAC, BattlEye and the like are "a stop sign".
- No bypassing anti-cheat, DRM or ownership checks.
- No cheats against other players.
- **No redistribution of game files, extracted assets, decompiled source, or retail offsets and decompiler
  names baked into code.**
- It publishes code, its own assets, patches and **converters that run on the user's install**.
- It backs up saves, kills processes by PID only, and asks before driving input, installing loaders or
  publishing.
- It cites the re3/reVC takedown and lawsuit and the H2M cease-and-desist: "takedowns happen even without
  assets".

### 1.6 Engine playbooks relevant here
- **Bethesda** (`references/engines/bethesda.md`, 46 lines): xEdit and generated ESPs, Papyrus, SKSE with
  CommonLibSSE-NG and Address Library, NIF and PyNifly, BSArch. "Animation uses Havok behavior files (hard),
  so mods reuse existing behaviors."
- **FromSoft** (`big-frameworks.md` §FromSoftware): ModEngine2/me3 offline with EAC off, Smithbox,
  WitchyBND, DLL mods. It notes that the method behind "Minecraft in ER" and "creepers in DS" "wasn't
  published".
- **Havok** (`knowledge/techniques/havok-hkx-chunked-packfile-family.md`): Skyrim SE = Havok 2010.2.0-r1
  classic packfile; FO4 2014.1; Starfield physics 2019.02 tagfile. Converting between versions needs the
  matching `hkCompatFormats.dll`, which is where projects get stuck.
- **OpenMW, Morrowind or NIF v4**: not one word in the repo (grep: zero hits).
- **Water, sailing, buoyancy**: no field note.
- **Climbing**: one note, White Knuckle → Minecraft (below).

### 1.7 Field notes that bear on Argonia
- **`knowledge/games/elden-ring/porting-dark-souls-remastered-enemies-into-elden-ring.md`** is the most
  relevant document in the repo. Opus 5.5, 4 days, about 46 in-game tests, status working.
  - The DS1 Hollow was moved into ER as its own character: skeleton, animations, TAE, params, AI Lua, sounds.
  - Facts it records:
    - DS1 TAE JumpTable IDs = ER FlagTypes (5 hit, 23 AI combo window, 78/79/86 cancel windows).
    - SpEffect 30 = "parry-broken (throwable)".
    - BehaviorParam row = `(200000+variation)*1000+judge` → AtkParam.
    - Poise = NpcParam `superArmorDurability`, stagger level = AtkParam `dmgLevel`.
    - ThrowParam is keyed by the defender's model ID.
    - DS1 AI is plain Lua 5.0 with local names intact: `Approach_Act`, `GOAL_COMMON_ComboAttack`, odds
      and distances.
  - Gotchas: Havok physics re-serialised by HKLib crashes ER (patch bytes in place), and a sound bank was
    silent for 15 tests because of the loader build.
  - **For Argonia this is the proof that DS-family combat data can be decoded to the timing-window level
    by an agent, with tools that already exist.** The same data also reimplements cleanly.
- **`knowledge/games/skyrim-special-edition/rebuilding-a-cut-gatekeeper-...md`**: Opus 5.5, about 30
  builds, working.
  - Python-generated ESL plugin with dialogue branches, shared INFOs, voice-file naming rules and
    force-greets.
  - Records hard facts about Skyrim's dialogue (DLBR flags, the 25-character EDID rule for voice files).
- **`knowledge/games/white-knuckle/climbing-...md`**: Opus 5.5, about two weeks, "mostly verification".
  - Unity C# decompiled (kept private), climbing reimplemented in Java at the game's 50 Hz step in game
    units.
  - The art comes from a per-player converter.
  - Oracles: the real game, FMOD decode bit-identity, a 3.5-minute Fabric gametest.
- **`knowledge/games/starfield/starfield-animation-af-rig-and-havok-physics.md`**: Starfield uses Havok
  for physics but its own .af/.rig for animation.
- **`knowledge/techniques/rebuilt-guest-engine-inside-a-host.md`**: placement options and contracts.
  BullySkate's 6,184-byte fixed shared block, axes defined once, a guest fixed clock, NaN recovery.
- **`knowledge/techniques/engine-recreation-measures-and-fidelity.md`**: byte match, coverage, trace
  parity and benchmarks are separate numbers, and scripts are part of fidelity.
- Also useful: `bridge-contracts-ownership-units-and-lifecycle.md` (units: Skyrim 70 units/m),
  `collision-and-combat-bridging.md`, `reading-source-engine-models-and-animations.md`.

The 122 game folders include:
- relevant here: Elden Ring, DS2, DSR, Skyrim SE, Fallout 4/NV, Starfield, AC, AC4, AC Rogue, Witcher 3,
  Black Myth Wukong, Ghostrunner, Half Sword, Valheim, Dragon's Dogma 2, Gothic II;
- also: Hogwarts Legacy, Kenshi, Mount & Blade II, Tomb Raider Legend, Just Cause 3, Batman Arkham,
  Dishonored 1/2, and many more (see `knowledge/INDEX.md`).

There is no Morrowind, DS3, BotW, Sea of Thieves or Wind Waker note.

### 1.8 Hype vs evidence for universal-modder
- **Real.** Its notes are unusually honest:
  - each records status, exact versions, test counts and open questions;
  - it has a whole technique note on not over-claiming.
  
  The DSR→ER, Skyrim and White Knuckle notes describe genuine multi-day engineering with real oracles.
- **Hype.** Most of the viral output is clips.
  - EverythingEdinburgh (2026-10-04) describes most mashups as "unplayable… tech demos for viral engagement".
  - chasm, the SkyCraft author, calls many AI mods cheap social-media content (via Shazoo, 2026-10-05).
  - Nexus tightened AI-disclosure tagging on 2026-07-31 (PC Gamer).
- **Cost.**
  - A single mechanic port to a working state: **4 days to 2 weeks of agent time with a human
    play-testing every build.**
  - Not "a weekend".
  - The "Mirror's Edge parkour in Skyrim in one day" claim is a second-hand report about an unnamed
    Discord member (Shazoo).

---

## 2. Ghidra and the Ghidra MCP ecosystem

### 2.1 The NSA Ghidra repo itself
- **There are no AI skills, `.claude/`, `AGENTS.md`, `CLAUDE.md`, MCP or LLM modules** in the tree.
  - Checked with `git ls-tree` over the whole HEAD.
  - The only "agent" paths are debugger connectors (gdb, lldb, dbgeng, x64dbg, drgn trace-RMI).
- The current release is **Ghidra 12.2 (October 2026)**. It needs **JDK 25**, and Python 3.9–3.14 for the
  Debugger. What matters for agents:
  - PyGhidra 3.2.0 (GP-6664);
  - GhidraDev 5.1.0 with a PyGhidra Headless run configuration (GP-6659);
  - a Server Allow List and enforced TLS for servers;
  - Dockerized Ghidra since 12.0, with `headless`/`pyghidra` entrypoints (GP-3579);
  - Python scripts default to PyGhidra rather than Jython since 12.0.
- So the agent-facing surface is **headless analyzeHeadless + PyGhidra scripting**. MCP is third-party.

### 2.2 MCP bridges, by maturity (source reading plus web)
| Bridge | Shape | State observed |
|---|---|---|
| **LaurieWired/GhidraMCP** | Ghidra GUI plugin with an HTTP server, plus a Python MCP bridge | v2.0.0 (`pyproject.toml`), targets Ghidra 12.1.4, now has headless integration tests; last commit 2026-10-10. The best-known one; many forks (themixednuts, 13xforever, bethington…). |
| **clearbluejar/pyghidra-mcp** | headless-first PyGhidra, optional `--gui`; project-wide analysis; ChromaDB semantic search over decompiled functions | "beta", CI tests; streamable HTTP or stdio. universal-modder recommends it ("code-capable tools beat hundreds of tiny ones"). |
| **cyberkaida/ReVa** | Ghidra extension; small, LLM-tolerant tools designed against "context rot" | supports Ghidra 12.0+ (12.2 needs Java 25); ships its own `CLAUDE.md`/`AGENTS.md`; committed today. The most agent-engineered. |
| GhidrAssistMCP | used in the Quesma Chromatron port | the author calls the setup "painstaking and fragile" |
| **oofz/Ghidrust** | not Ghidra: a from-scratch Rust RE toolkit (CLI, stdio MCP, egui), about 106k lines of Rust | **one commit**; its README calls "surpass Ghidra" a *target*; the GPU decompile is "often correct but slower". Treat as experimental. |

Practitioner verdicts:
- **Quesma, River Raid.** Claude found the lives decrement, a one-byte NOP. But it misidentified the game
  as Centipede, could not rebase the image, tool calls took about 30 s, and the author's verdict was
  "experimental phase".
- **Quesma, Chromatron.** Opus 4.6 produced a pixel-perfect Rust port (307,199 of 307,200 pixels
  identical). Earlier attempts with Opus 4.5 needed heavy hand-holding and invented fonts. The models
  "insisted they were correct" and were poor at visual inspection, and **pixel-diff oracles were what
  made it converge**.
- **Faith Runner** (`tools/me-extract/ghidra/README.md`) uses *plain headless Ghidra scripts*
  (`DecompileTargets.java`, `DumpAsm.java`) on named addresses, with no MCP. It skips full auto-analysis of
  a 31 MB exe, finds natives through the UTF-16 name→pointer table, and keeps the output out of the repo.
  **That is the pattern to copy:** targeted headless decompiles of specific functions, not a chat over a
  whole binary.

---

## 3. ds3-open-re and the FromSoftware data ecosystem

### 3.1 ds3-open-re: what is actually in it
**Netcode only, abandoned since 2021-03.** It contains:
- protobuf definitions reverse-engineered from the client (`proto/Frpg2RequestMessage.proto`,
  `proto/dks3/common.proto`);
- a Rust port of the CWC cipher;
- a server-emulator skeleton (`packages/dks3_server`), a launcher/patcher, and a config crate;
- one Cheat Engine table (`tools/tables/protobuf-logger.ct`) that hooks hard-coded addresses to dump
  messages;
- a pointer to a (presumably dead) Ghidra 9.2 shared server.

**Nothing about combat, animation, AI or physics.** It is irrelevant to Argonia except as a historical
example of a community shared Ghidra server.

### 3.2 What does carry DS3 mechanics precisely (data, not code)
- **soulsmods/Paramdex** (read here). `DS3/Defs` has 92 param definitions and `DS3/Names` 99 row-name
  files. The combat ones:
  - `BEHAVIOR_PARAM_ST`
  - `ATK_PARAM_ST` (190 fields, among them `AtkStam`, `AtkSuperArmor` = poise damage, `GuardBreakRate`,
    `GuardRate`, `GuardStaminaCutRate`, `disableGuard`)
  - `NPC_PARAM_ST` (262 fields, among them `superArmorDurability` = poise pool, `SuperArmorRecoverCorrection`,
    `stamina`, `staminaRecoverBaseVal`, `weight`)
  - `SP_EFFECT_PARAM_ST`
  - `TOUGHNESS_PARAM_ST`
  - `KNOCKBACK_PARAM_ST`
  - `MOVE_PARAM_ST`
  - `NPC_THINK_PARAM_ST`
  - `NPC_AI_ACTION_PARAM_ST`
  - `EQUIP_PARAM_WEAPON_ST`
  - `REINFORCE_PARAM_WEAPON_ST`
  - `THROW_INFO_BANK`
  
  The row names cover AtkParam_Npc, AtkParam_Pc and the rest. **This is the schema for "DS3 combat as
  data".**
- **Smithbox** (vawser; successor to DSMapStudio and DSParamStudio). Edits params, maps, text and models
  for DES through ER/NR. It reads the user's unpacked game, and it is where you export param CSVs.
- **WitchyBND**: unpacks BND/DCX/BDT/TPF, and TAE to XML with templates.
- **DSAnimStudio** (Meowmaritus): plays the chr animations with their **TAE** events overlaid. TAE events
  carry:
  - attack-behaviour windows (InvokeAttackBehavior → BehaviorParam judge);
  - i-frames (JumpTable/invincibility flags);
  - cancel windows (the ER-numbered 78/79/86 family);
  - SpEffects, sounds and SFX on dummy polys.
  
  **This is the frame data**, per animation and to the frame (30 fps TAE time). The community wiki is
  soulsmodding.com (formerly soulsmodding.wikidot.com).
- **HKS** (`action/script/c0000.hks`, Havok script Lua): the player's state machine (which input goes to
  which animation under which TAE flag). It decompiles readably with community tools. **This is the
  "feel" logic**: buffering, cancels, roll and backstep selection by equip load.
- **Cheat Engine tables.** The Grand Archives (TGA) DS3 table is the standard. Its debug flags, hitbox
  view, animation-ID readout and speed controls are useful *for capturing reference traces offline*.
- **Frame-data compilations.** Fextralife and r/opensouls3 (roll i-frame percentages: the DS3 medium roll
  is about 63% i-frames per that thread) are secondary. Derive the numbers from TAE instead.
- **Souls-like frameworks in other engines.** BlueBrainOrg/SoulsLikeDemo, fruitiestpunch's Godot 4
  souls-like template, and several Godot asset-library "Souls-Like-Controller" entries.
  - None found that cite Paramdex or TAE data. They are hand-tuned imitations.
  - The data-faithful precedents are all *inside FromSoft hosts* (DSR→ER, Convergence).
  - The other precedent is the reported "Funny-Bones" Rust ER player controller dropped into Skyrim
    (GamesRadar). It is human-made and its source was not located. **Report.**

---

## 3A. Dark Souls Remastered: the primary combat source (owner scope update)

The owner owns DSR (Steam app 570940) and wants it as the main reference for combat, poise and AI. DS3
stays secondary. This also matches Argonia's existing poise design, which is DS1-based
(`docs/research/combat-and-systems/dark-souls-poise-mechanics.md`).

### 3A.1 What the DSR data ecosystem gives you (source reading in Paramdex)
- **Paramdex `DS1R/`**: 51 defs and 143 row-name files. Compare DS1 PTDE (48 defs, 143 names) and DS3
  (92 defs, 99 names, 1 tdf). There are fewer defs because DS1 has fewer param types, not because coverage
  is worse.
- The combat defs are present: `AtkParam`, `BehaviorParam`, `NpcParam`, `NpcThinkParam`, `ThrowParam`,
  `KnockBackParam`, `MoveParam`, `AiStandardInfo`, `CharaInitParam`.
- The row names cover `AtkParam_Npc`, `AtkParam_Pc`, `BehaviorParam`, `BehaviorParam_PC`, `Bullet`,
  `CalcCorrectGraph`, `EquipParamWeapon`, `EquipParamProtector`, `LockCamParam`, `RagdollParam`,
  `SpEffectParam`, `ThrowParam`, `ReinforceParamWeapon`, plus `default_EnemyBehaviorBank` and
  `default_AIStandardInfoBank`.
- **Per-row names exist** for the PC behaviour and attack tables, so "R1 light attack, straight sword" can
  be looked up by name. DS3's names are sparser in places.
- **Key fields** (from the um DSR→ER note, which used DSR as its source):
  - poise pool = NpcParam `superArmorDurability`;
  - stagger tier = AtkParam `dmgLevel` (DS1 "ImpactLevel");
  - SpEffect 30 = parry-broken (throwable), SpEffect 35 = throws disabled;
  - ThrowParam is keyed by the defender's model ID.

### 3A.2 Tooling maturity: DSR vs DS3
| Need | DSR (primary) | DS3 (secondary) |
|---|---|---|
| Unpack archives to loose files | UXM Selective Unpack (Nordgaren fork, v2.5, maintained); DSR support "partly confirmed" in its changelog. DSR has shipped many files loose since release, and the um DSR→ER note used "loose files unpacked" | UXM fully supported |
| Mod loader (offline) | **none of the modern ones.** ModEngine2's README lists DSR as unsupported, and me3 doesn't list it (um DSR note). Loose-file overrides after UXM, or a `dinput8.dll` proxy | ModEngine2 and me3 both supported |
| Param editing / export | Smithbox (DS1 listed; DSR via the DS1 project type; Windows-only), DSMapStudio (legacy), DSParamStudio, **soulstruct** (Python: DS1R GameParam, EMEVD to and from Python, MSB maps, AI script decompile/edit/recompile). soulstruct is the most agent-friendly: a script, not a GUI | Smithbox, WitchyBND |
| Animation + TAE viewer | DSAnimStudio supports DS1 and DSR (its oldest target; the TAE templates started there) | DSAnimStudio |
| AI scripts | **best of the series for study**: Lua 5.0 with local names kept, so it disassembles readably (um DSR→ER note); soulstruct decompiles it | Lua bytecode, names mostly stripped |
| Player state machine | DS1 has **no HKS**. Player action logic lives in ESD/`chr` TAE + native code, so "feel" rules (buffer, cancels) come more from TAE JumpTable flags and in-game measurement than from a readable script | HKS (`c0000.hks`), readable after decompile: a richer source here |
| Live debug / capture | DSR Gadget (JKAnderson; DSR 1.01–1.03; flags, no-gravity, no-collision, camera store, event flags; **archived 2025-05-26**, GPL-3.0); Nexus DSR mod 266 (restored debug menu, Lua/ESD console, FreeCam; installs as `dinput8.dll`); community CE tables exist but no single TGA-grade table was confirmed | TGA table (comprehensive, maintained) |
| Executable RE | **the exe is packed/protected on disk.** Static Ghidra gives "mostly garbage"; the um DSR note dumped the decrypted image from the running process and analysed that (headless Ghidra 12.1.4 + RTTI), without stripping the protection. It also lists a verified memory map for 1.03.1 (BulletMan, player, camera offsets). Keep it to analysis only, per universal-modder's DRM rule | DS3 exe also protected; larger community Ghidra history (ds3-open-re's shared server, now dead) |
| Havok | Havok 2015 (DSR); the hk2015 classes are readable with soulstruct-havok / HKLib; round-trip writes risky | Havok 2014 |

**Net:** for *studying combat*, DSR is as good as DS3 and better for AI, because of its readable Lua.
- It is weaker for player-input "feel", because it has no HKS.
- It is weaker for live tooling: Gadget is archived, and there is no ME2/me3 loader.
- None of the gaps blocks the R1 route (study, then reimplement). Only an in-game mod route would suffer.

### 3A.3 Offline and anti-cheat
- DSR has **no client anti-cheat** (the um DSR note's `um scan` found none). But its **PC servers are live
  again (since November 2022)**.
- Modified params or memory edits in an online session reach other players and risk a soft ban, so treat
  DSR as **offline-only while anything is loaded**:
  - Steam Offline Mode, or firewall-block `DarkSoulsRemastered.exe`;
  - remove `dinput8.dll` and any loose overrides before going online;
  - keep a separate backed-up save (`um backup`).
- Reading files with Smithbox, soulstruct or DSAnimStudio touches nothing at runtime, so it carries no ban
  risk at all. Most of the study can happen there.

### 3A.4 Proton / Linux
- DSR runs under Proton. The um ecosystem has Proton field notes, and protondb lists DSR, though the rating
  could not be read here (the fetch returned an empty shell). Treat "works" as a report until the owner
  launches it.
- The study tools are mostly Windows .NET: Smithbox (Windows-only per its README), DSAnimStudio, UXM,
  DSR Gadget.
  - They generally need Wine/Proton with .NET runtimes, which is unverified.
  - DSAnimStudio needs DirectX/XNA-era graphics and is the most likely to fail.
- **soulstruct is Python and runs natively on Linux.** That makes it the natural agent-side tool: params,
  AI, EMEVD and maps without a GUI.
- Running Cheat Engine or a proxy DLL inside the Proton prefix is possible but fiddly.
- Recommended: do live capture on a Windows box if one exists. Otherwise record the screen and read frame
  timing off video at 30/60 fps, cross-checked with TAE.

### 3A.5 The DSR-first combat recipe
1. Unpack with UXM (or use the existing loose files).
2. With soulstruct and Paramdex DS1R names, export to JSON:
   - `BehaviorParam_PC` → `AtkParam_Pc` (damage, `AtkStam`, poise damage, `dmgLevel`, guard break);
   - `EquipParamWeapon` (stamina cost, weight class);
   - `NpcParam` (`superArmorDurability`, stamina, regen);
   - `NpcThinkParam`, `ThrowParam`.
3. In DSAnimStudio, read the player's `c0000` TAE per action:
   - InvokeAttackBehavior windows;
   - invincibility (roll at <25% / <50% / >50% equip load);
   - JumpTable cancel flags (the same numbers ER uses: 23/78/79/86, per the um note);
   - SpEffects.
4. AI: decompile the target enemies' Lua with soulstruct and write *our own* goal-tree versions of the
   same shape and odds (Hollow, Balder Knight, Black Knight).
5. Oracle: DSR offline plus the debug-menu mod or Gadget (no-gravity and camera lock for stable captures),
   with 20 scripted repeats per action recorded at 60 fps. Compare against Argonia's sandbox at ±1 frame.
6. DS3 is the secondary source only where DS1 lacks something: HKS input-buffer rules, toughness/hyperarmor,
   weapon arts. Mark each value `DSR:` or `DS3:` with its provenance.

---

## 4. Real-world experience reports (with evidence level)

| Project | What | Agent / time | Level | Lesson |
|---|---|---|---|---|
| DSR Hollow → Elden Ring (um note) | full enemy port via data | Opus 5.5, 4 days, ~46 in-game tests | run (human-played) | DS data decodes to timing windows; loader versions and Havok re-serialisation are the traps |
| Skyrim cut gatekeeper (um note) | generated ESL dialogue/quest | Opus 5.5, ~30 builds | run | plugin data is agent-friendly when written by script and checked in the CK and SSEEdit |
| White Knuckle climbing → Minecraft (um note; github.com/Fizz12215/White-Knuckle-Climbing) | decompiled C# → Java reimplementation + per-user asset converter | Opus 5.5, ~2 weeks, "mostly verification" | run | climbing = small set of methods + scene values; the oracle work dominates |
| **Faith Runner** (github.com/tnrjns/faith-runner) | Mirror's Edge movement in Rust (`faith_move`, glam-only) + Bevy greybox; loads Faith's body, animations and sounds from your install | not stated in repo | source | values tagged `ME:` from `TdGame.u` vs `guess`; native physics ported from Ghidra decompiles of `ATdPawn::GetSprintAcceleration`, `CalcVelocity`, wallrun gravities; Skyrim (SKSE) hosting is reported in um's index, not in the repo |
| Mirror's Edge parkour in Skyrim "in one day" | — | unnamed Discord member | second-hand report (Shazoo) | don't plan on it |
| **AC1 Movement Rewritten** (github.com/Banned445/AC1-Movement-Rewritten) | clean-room Rust/Bevy recreation of Altaïr's locomotion, ledges, climbing, wall runs; streams Damascus from the user's AC1 install | — | source | "early and unfinished", `PORT:` placeholders; the closest public analogue to "BotW-like climbing from an owned PC game" |
| SkyCraft, ER Mario, BullySkate, IW4L, benilla | passthrough / rebuilt engines | various | reports + some source | rebuilt engines exist; fusing them is still design, not done |
| Quesma Chromatron | 1990s game → pixel-exact Rust | Opus 4.6; about a month of calendar time | run (author) | pixel oracles beat model judgement |
| Quesma River Raid | 1-byte patch via GhidraMCP | Claude | run | fragile setup, slow calls, confident misidentification |
| reversedwithai.com list | 245 AI decomp, recomp and port projects (100 "works", 121 "partial") | Claude, mostly | mixed reports | N64/PS2 decomps are the AI sweet spot (byte-match oracle); **no Morrowind, OpenMW or Dark Souls entry** |
| "Elden Ring combat in Skyrim" (GamesRadar) | ER controller rebuilt in Rust, hosted in Skyrim | presented as human-made | report | the transplant pattern works, but this one is not AI evidence |
| openmw-tonalarchitect | OpenMW fork with Claude NPC dialogue | — | source (not read) | the only OpenMW + Claude project found |

**The common failure modes:**
- confident misidentification;
- "numbers match ≠ behaviour matches";
- synthetic green tests;
- loader and version drift;
- Havok tool round trips that crash the game;
- models judging their own visuals.

**The common success factor:** an oracle that can fail, such as byte match, trace replay, pixel diff, or
a human checklist per build.

---

## 5. Legal line (applies to every row in section 6)

Not legal advice. This is the line universal-modder draws plus the community norm.

- **Knowledge** (numbers, timings, algorithms, formats learned by reading your own copy) can be
  reimplemented in your own code. Ideas and facts are not copyrightable.
- Keep the decompiled text itself private, and don't paste it into the codebase. Faith Runner's
  `ME:`-tagged constants are the model: provenance without copied code.
  - EULA anti-RE clauses still exist, and interoperability exceptions vary by jurisdiction.
  - The EU Software Directive art. 6 is narrow; US fair use covers RE for interoperability, per Sega v.
    Accolade and Sony v. Connectix.
  - The risk rises sharply with publishing or monetising (re3).
- **Data** (param tables, TAE, AI scripts) is the publisher's expressive data.
  - Read it at install time from the user's files, through a converter, or hand-transcribe *derived*
    numbers.
  - Don't ship the tables.
- **Assets** (meshes, animations, textures, audio): only converted on the user's machine from their own
  install.
  - Never redistributed, never in the repo, never on the Pages build.
  - **This conflicts with Argonia's current model.** It deploys a public Pages build that carries
    converted Skyrim and mod assets (kits under `apps/world-studio/public/kits/`). A "users supply their
    own files" design means the deployed web build cannot contain them.
  - For a streamed or browser game, the conversion must run client-side or on the user's own machine.
  - That is a hard re-architecture of the kit pipeline, and needs an owner call.
- **Online/anti-cheat.** DS3 and ER only offline via ModEngine2/me3, with EAC never running. Sea of
  Thieves (online-only, EAC): **do not attach anything**. Study it from footage and public talks only.
- **Console titles** (BotW, Wind Waker). Universal-modder permits dumps of cartridges or discs you own, but
  this is the riskiest category, given Nintendo's enforcement record.
  - Prefer published GDC talks and community docs (ZeldaMods, decomp wikis) as knowledge.
  - Never take Nintendo assets.
- **Mod assets.** Nexus permissions are per mod. The project's own rule ("take assets, never SKSE/Papyrus
  code") already matches this lens.

---

## 6. Argonia's systems through the lens

The target is either an **OpenMW fork** (C++ engine + Lua) or the existing **Three.js/Rapier app**. The
routes in the table mean:
- **R1**: study, then reimplement in our own code. Knowledge only.
- **R2**: convert the user's files at install time. Data and assets.
- **R3**: passthrough, running the source game. Rejected for a shipped game.

| System | Study (owned games) | Extract | Route | Notes / legal |
|---|---|---|---|---|
| **Combat (DS-style)** | **DSR primary** (§3A); DS3 secondary for HKS input-buffer rules and hyperarmor; ER for deltas. *(The DS3-specific items below, such as HKS and TGA, apply only to the secondary source.)* | **Knowledge:** player HKS state machine (input buffer length, cancel rules, roll selection by equip load), TAE windows per action (startup, active, recovery, i-frames, cancel frames) via DSAnimStudio; BehaviorParam→AtkParam chains; stamina costs and regen; guard math (`GuardRate`, `GuardStaminaCutRate`, `GuardBreakRate`). **Oracle:** offline DS3 with the TGA table, recording animation ID and frame per action; replay the same inputs in Argonia's sandbox and compare window timings frame by frame | R1. OpenMW: new C++ combat controller exposed to Lua (OpenMW's Lua has no hitbox or animation-event control fine enough; 0.51 added only an "animation end" event). Three.js: already `PlayerMovementController`-centred | Ship a JSON of *derived* timings ("light attack: 13 f windup, 4 f active, cancel at 22 f") with provenance tags; never ship TAE or param dumps |
| **Poise / stagger** | DS1/DSR (the adopted model), DS3 for the toughness rework | **Knowledge:** NpcParam `superArmorDurability`, `SuperArmorRecoverCorrection`, AtkParam `AtkSuperArmor`, `dmgLevel` → reaction animation tier; DS3 `TOUGHNESS_PARAM_ST`, hyperarmor windows from TAE | R1 | Already researched from wikis (`docs/research/combat-and-systems/dark-souls-poise-mechanics.md`); Paramdex lets you confirm the numbers against real rows instead of wikis |
| **Enemy AI** | DSR (AI Lua keeps local names, per the um DSR note), DS3 AI luabnds; Morrowind for the AI-package schedule | **Knowledge:** goal trees (Approach → ComboAttack → Damaged_Step), odds by distance band, NpcThinkParam (eye/ear ranges, `battleGoalID`), NPC_AI_ACTION_PARAM | R1: write our own goal-tree runtime with the same *shape*; tune per enemy by hand | DS1 AI scripts are FromSoft code: read, don't transcribe |
| **Climbing (BotW-like)** | BotW is Switch-only (use GDC talks and decomp docs as knowledge only); **AC1 PC** (AC1 Movement Rewritten is an open reference), Mirror's Edge (Faith Runner), White Knuckle (um note), Skyrim mods (FreeClimb, SkyParkour) for clips | **Knowledge:** ledge/wall detection sweeps, stamina drain, grab rules (Faith Runner's vault-type heights 48 cm / 1.48 m / 1.92 m and wall checks; AC1's climbable-edge model). **Assets:** clips stay mod-sourced, as decided in 0152 | R1, with a `faith_move`-style engine-free crate: host supplies only box sweeps and overlaps | The best-evidenced lens: two open reimplementations to read (both licensed; check each LICENSE) |
| **Swimming / diving + sloping rivers** | Skyrim SE (it has flowing, sloped river water); Morrowind/OpenMW (flat water plane per cell); Subnautica/Valheim for diving feel | **Knowledge, to verify:** how Skyrim gets submersion depth on placed sloped water (WATR records + water-type activators/meshes; flow maps). Read CK data first, use Ghidra only if the data doesn't answer it. **Data:** river paths and flow from Skyrim placed water, as a pattern | R1. OpenMW: **an engine change**: OpenMW water is a single height per cell (verified by reading OpenMW source is still owed); sloped rivers need per-water-volume height queries in physics + the renderer. Three.js: already free to do volumes | The largest engine gap if OpenMW is chosen; nothing in um covers water |
| **Boats / sailing** | Wind Waker (knowledge only: wind-direction sail model, from talks); AC4 Black Flag PC (um has 5 AC4 notes on player transforms and spawning, none on ship physics); Sea of Thieves: **no hooks** (EAC) | **Knowledge:** sail force vs wind angle, turning rate vs speed, buoyancy sample points | R1. Reading AC4's ship controller offline in Ghidra is legal-ish for knowledge but costly on AnvilNext; a hand-written arcade model matched to footage is cheaper | Already designed as "boats as horses" (`docs/research/combat-and-systems/player-boats-as-horses.md`); the lens adds little here |
| **Physics** | Skyrim (Havok 2010), DS3 (Havok 2014-ish) | Knowledge only: ragdoll limits and capsule sizes as numbers | R1 on Bullet (OpenMW) or Rapier (current) | Never round-trip Havok files (um DSR gotcha 2); Havok's licence bars using its runtime |
| **Animation sourcing / retargeting** | Skyrim + mods (current), DS3 (for souls timing) | **Assets: R2 only.** A DS3→Skyrim-skeleton retarget at install time is possible in principle (the DSR→ER note did Havok 2015→2018 with spline re-encoding) but heavy: FLVER/HKX parsers, bone maps, TAE re-timing | Default: keep Skyrim/mod clips and **re-time them to DS3 TAE windows** (the project's "fix timing on the animation side" rule). Installer-time conversion from the user's DS3 only if mod clips can't read as souls-like | The largest legal and engineering load; avoid unless the owner rules otherwise |
| **Terrain / world rendering** | Morrowind (cell grid, LAND records), Skyrim (LOD, BTO/BTR) | Data formats (public: UESP, OpenMW source, NifTools) | OpenMW reads ESM/ESP natively, plus partial ESM4/Skyrim support | Formats are already open-documented: no RE needed. **Ghidra adds nothing here** |
| **Graphics (fog / volumetrics)** | Skyrim ENB/Community Shaders (mod code, open), DS3 via RenderDoc frame captures | Knowledge: pass order, fog parameters, captured with RenderDoc offline | R1 shaders of our own | RenderDoc is the right tool, not Ghidra; OpenMW 0.51 exposes sun direction to post-processing |
| **UI** | Morrowind (journal/topic UI), DS3 (HUD, menus) | Layout knowledge only | R1 | No RE needed; screenshots suffice |
| **Dialogue / quests** | Morrowind (topic-keyword system), Skyrim (um gatekeeper note gives DLBR/INFO rules) | Formats are public (UESP, OpenMW `components/esm3`) | OpenMW: native; Three.js: own schema | No Ghidra; OpenMW already *is* the decompiled Morrowind dialogue engine |
| **Saving** | Morrowind ESS / OpenMW omwsave; DS3 SL2 | Knowledge of layout only | R1 | Nothing to extract |
| **Mobile (Android + stream)** | OpenMW Android port | — | — | OpenMW on Android is a community build of uneven state; streaming to a browser means a cloud GPU per player (cost). The current browser build already runs on phones. **RE gives nothing here** |

### 6.1 Where the lens pays and where it doesn't
- **Pays:**
  - DS combat timing, poise, AI shape, through Paramdex, TAE, HKS, Smithbox and DSAnimStudio, which are
    data tools, not Ghidra;
  - climbing and parkour, with two open Rust reimplementations to read and an um note;
  - one targeted question: Skyrim's sloped-water submersion.
- **Ghidra specifically** is needed only where the data stops: native movement and physics constants
  (Faith Runner's case) and engine-side water queries.
  - For FromSoft combat, almost everything that matters is in params, TAE and HKS.
  - For Bethesda, it is in plugin records and OpenMW's source.
- **Doesn't pay:** terrain, dialogue, saving, UI, mobile, rendering.
  - Morrowind is already fully open via OpenMW.
  - Skyrim's formats are documented.
  - Rendering wants RenderDoc.

### 6.2 A concrete first slice in um style
**Superseded by §3A.5 (DSR first).** The steps below are the DS3 variant, kept as the secondary path.
1. Pick one DS3 player action (light attack, straight sword) and the medium roll.
2. Offline DS3 with ModEngine2/me3 (EAC off, separate save) plus the TGA table.
3. Record animation ID per frame for 20 scripted repeats.
4. Read the same actions' TAE in DSAnimStudio, and AtkParam/BehaviorParam rows in Smithbox, with Paramdex
   names.
5. Write `combat-timings.json` with derived numbers and an `ME:`-style provenance tag per value
   ("DS3 TAE a000_003000 ev 0 InvokeAttackBehavior 0.433–0.567 s"). Write no game bytes.
6. Implement in Argonia's combat sandbox and drive identical inputs.
7. Oracle: per-action window starts and ends within ±1 frame (30 fps TAE time), recorded in a parity
   document listing every substitution.
8. Budget: um's evidence says **days per mechanic with human checks**, not hours.

---

## 7. Candid verdict
- **As a lens, "study the owned original, reimplement with provenance, verify with a failing oracle" is
  sound.** Argonia already half-does it (wiki-based poise, mod clips).
  - Paramdex, TAE and HKS make DS3 combat measurable to the frame.
  - That upgrade is cheap and worth taking.
- **"Ghidra-first" is the wrong emphasis.** The FromSoft and Bethesda answers are mostly in data and
  open-source engines. Ghidra is a scalpel for the few native constants.
  - MCP bridges are real but fragile (Quesma).
  - Targeted headless scripts (Faith Runner) beat chatty MCP sessions.
- **"Users supply their own files" is a re-architecture, not a tweak**, for a deployed browser and Pages
  build that currently ships converted assets. It is the single biggest decision this lens forces. It is
  also the only legally clean way to use Skyrim, DS3 or Morrowind assets in a distributed build.
- **OpenMW as engine** makes Morrowind systems free. But it adds C++ engine work for:
  - souls combat;
  - sloped water;
  - climbing;
  - boats;
  - a mobile/stream story.
  
  The lens doesn't remove any of that.
- **Hype check.**
  - Viral mashups are mostly clips.
  - The serious, verified ports in um took 4 days to 2 weeks per mechanic, with a human in the loop on
    every build.
  - No AI-built Morrowind, OpenMW or Dark Souls reimplementation exists in public evidence.
