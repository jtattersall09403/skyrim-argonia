# Accounting: every detail from the founding conversation, and where it went

The owner asked that every detail from the planning conversation and its research be **accounted for**: either
put into the plan or deliberately left out, with the reason. This ledger is that check. Each row names where the
item is handled (file and section) or why it is excluded. The planner re-reads this file at every phase close
and adds rows for new owner rulings.

Legend: **In** = handled where named. **Out** = deliberately excluded (reason given). **Open** = an owner call.

## A. The owner's requirements (owner-brief §1–2)

| # | Item | Status | Where / why |
|---|---|---|---|
| A1 | Set in Argonia with the stories, quests, places from the three.js version | In | 0009; P0-WP0.6 import; source-map §1; P3-WP3.9; P7; P9 |
| A2 | Morrowind engine for dialogue, quests, inventory, UI, adapted (content, colour themes, stats/progression changes) | In (as Morrowind's soul on Skyrim) | 0001 explains why not the Morrowind engine itself; 0005 C1–C15; P4 |
| A3 | Weapon and item classes matching Morrowind | In | 0005 C5; P4-WP4.11 |
| A4 | UI like Morrowind's; colour themes | In | 0005 C10; P4-WP4.10; palette import (P2-WP2.8) |
| A5 | Dialogue like Morrowind's: branching topics, UI, writing style | In | 0005 C1; P1-S5; P4-WP4.6, 4.7; style guide import |
| A6 | Attributes and stats like Morrowind's | In | 0005 C2; P4-WP4.1 (27-skill mapping table) |
| A7 | Levelling with resting and vastei | In | 0005 C3; P4-WP4.2, 4.4 |
| A8 | Open to merging vastei with Skyrim attributes/levelling/perks; perks would need auditing | In / Open | 0005 C4; P4-WP4.3 perk audit; O-4 |
| A9 | No quest markers; directions written into the journal, followed like verbal directions | In | 0005 C7; P4-WP4.8 (directions generator + validator); P3-WP3.6 route graph |
| A10 | Morrowind-style journal | In | 0005 C8; P4-WP4.9 |
| A11 | Morrowind-style map | In | 0005 C9; P3-WP3.8 map image; P4-WP4.9 |
| A12 | Cuirass, pauldrons etc. (nice to have) | In | 0005 C6; P4-WP4.11; O-9 for split meshes |
| A13 | Custom HUD | In | 0005 C11; P4-WP4.10 |
| A14 | Dark Souls combat hooked to Morrowind-based stats | In | 0004; P5-WP5.3 damage formula on the sheet |
| A15 | Use the existing thinking in the argonia repo for combat/stats | In | imported 76-stats-progression and combat docs; P4/P5 read lists |
| A16 | ds3-open-re as a reverse-engineering example | Out (as a tool) | it is netcode only (engine-feasibility §3, um-ghidra-lens §3.1); DSR data tools used instead (0004) |
| A17 | Ghidra, universal-modder, Ghidrust for RE and extraction | In | 0010 (route order, scalpel use, vendored skills); P0-WP0.2/0.4; P5-WP5.1; Ghidrust Out as experimental (um-ghidra-lens §2.2) |
| A18 | "Anything else from Skyrim" from Mudcrab | Out (for now) | Mudcrab is a world viewer, not playable (0001 table); Skyrim itself is the host; watch as S4 |
| A19 | Free climbing (Mirror's Edge parkour-in-Skyrim reference; anything like free climbing) | In | P6-WP6.1 (FreeClimb + SkyParkour); the "one day" video is a second-hand report (um-ghidra-lens §4) |
| A20 | Player-controlled boats; research best source | In | P6-WP6.4/6.5 (Sailable Ship base, Wind Waker model, ownership) |
| A21 | Skyrim SE or DS3 level graphics | In | Skyrim host; P2-WP2.9 Community Shaders; P8-WP8.6 |
| A22 | Modern features: volumetric or pseudo-volumetric fog, lighting | In | P2-WP2.9; P3-WP3.3 (mist); P8-WP8.6 |
| A23 | Minimal new art; extract/adapt from Morrowind, Skyrim SE, DS1/3 and community mods | In / partly Out | 0006 §6; Skyrim and mod assets used at runtime; **Morrowind and DS assets Out** (licences, 0003/0004; Morrowind assets cannot run in Skyrim without conversion, which Bethesda's terms bind to Morrowind) |
| A24 | Reuse as far as possible; don't sink hundreds of dollars | In | 0010; 0008 budget; PLAN §2 |
| A25 | Playable only if you own the base games; ship nothing we shouldn't (Mudcrab model) | In | 0003; P10 |
| A26 | Owns Skyrim SE, Morrowind GOTY, DS3 (and DSR) on Steam | In | P0-WP0.5 downloads; legal §1 |
| A27 | Playable on Honor Magic V5 and MacBook Air M2; nothing installed on the Mac | In | 0007 streaming; VS Code tunnel for development (0008) |
| A28 | Streaming from a GPU VM for seamless saves | In | 0007 §4; P2-WP2.10 |
| A29 | Not wedded to RunPod; research others with good Claude Code/MCP compatibility | In | hosting-streaming §2; 0008 §3–4 (AWS CLI/MCP; RunPod out for play due to UDP; Vast.ai fallback) |
| A30 | Claude Code on an affordable AWS instance, ≤ $100/month | In | 0008: $100 is a **hard cap**; per-phase budgets; weekly projection with a stop-and-ask rule (T-COST) |
| A31 | Autonomous testing loops on AWS or a GPU service | In | ways-of-working §3; P1-S8/G8; P2-WP2.4 |
| A32 | Not Hetzner | In | 0008 §4 |
| A33 | 20x (parallel, ~60 h/wk) vs 5x (~120 h/wk) plan; usage arithmetic | In / Open | 0013; O-2 |
| A34 | As cheaply as possible | In | 0008 levers; idle-stop everywhere |
| A35 | Free; no commercial use | In | owner-brief; legal §1; P10 |
| A36 | Pelagiad font throughout | In | 0006 §4; P4-WP4.10 |
| A37 | New music | In / Open | 0006 §5; P8-WP8.4; O-8 |
| A38 | Full audit of UI and art; overhaul or tweak to fit Black Marsh; no Nordic elements | In | 0006; 0012; T-IMM; P2-WP2.7; P7-WP7.4; P8 |
| A39 | Agentic approach to cover everything 100% | In | 0006 §1–3 (enumerated inventory, coverage gate); P8-WP8.2 |
| A40 | Fal MCP for minor new art | In | 0006 §6–7; legal §4 |
| A41 | New public repo; old repo untouched; may continue three.js separately | In | 0003; 0009 §1; source-map |
| A42 | Plan for the future agent; bootstrap its own structure and ways of working from the old repo | In | P0-WP0.1/0.2; ways-of-working; source-map §3 |
| A43 | Plan complete, no petering out in later phases | In | every phase file has goal, starting state, re-check/read-first, WPs with acceptance, exit gate, risks, out of scope; an independent audit (68 findings, all fixed: section I) |
| A44 | Tropical Skyrim (SSE 78044) as the source for any base-Skyrim assets | In | 0006 §8; P2-WP2.1; P3-WP3.1/3.7; P8-WP8.2; legal §2 |
| A46 | "Other games if relevant" the owner owns | In | 0010 §2 (study owned games); none needed beyond Skyrim SE, Morrowind, DSR, DS3 so far; the planner asks the owner's library when a system lacks a reference |
| A45 | Use the universal-modder/Ghidra perspective as a primary lens across every system, water included | In | 0010; um-ghidra-lens §6 per-system table; P1-S7 (water question as the first Ghidra use); P5-WP5.1 |

## B. Owner rulings during planning (owner-brief §3)

| # | Ruling | Where |
|---|---|---|
| B1 | Earlier three.js goals are context, not constraints | inherited-rulings verdicts |
| B2 | Skyrim as host acceptable if Morrowind's soul is kept | 0001, 0005 |
| B3 | Distinguish Skyrim sub-options | 0001 §2 (S1–S4) |
| B4 | DS1 Remastered preferred; **match DS1 timings** | 0004 |
| B5 | Pin the Skyrim version | 0002 |
| B6 | Pelagiad, new music, full immersion audit, Fal for minor art | 0006 |
| B7 | New public repo `skyrim-argonia` ("holds us to account") | 0003 |
| B8 | AWS London; old box stopped | 0008; infra/README; O-1 |
| B9 | Native phone was an option, streaming acceptable | 0007 |
| B10 | Tropical Skyrim SSE for base assets | 0006 §8 |
| B11 | VS Code in the browser for working on the VM | 0008 §1; infra/README |
| B12 | Dialogue reads as Morrowind's; old written lines not used; skill from scratch | 0017 §6–7; `.claude/skills/dialogue-write`; P4-WP4.7 |
| B13 | Banned constructions (personification, verbless fragments, dangling modifiers, opaque references), British English, disposition hints | `dialogue-write/bans.yaml` and `lint.py`; 0017 |
| B14 | Any of ten races as speaker or player; address by race, faction, rank | `dialogue-write/voices.md`, SKILL §2 |
| B15 | Consistent first time across quests, places, dialogue, characters, facts; quest writer and reviewer skills; per-type principles from research | 0017; `.claude/skills/quest-write`, `quest-review`; `docs/research/2026-10-27/quest-*.md`, `questline-design.md` |
| B17 | Quests have varied skill-based action, by faction profile; output fits the engine; old quest design is the foundation | 0017 §8–9; `quest-write/principles/actions.md`; P4-WP4.0 |
| B16 | A detectives' faction rival to Shadowscales and Night-Reed, escalating to a murder-mystery finale | 0018; P4-WP4.8, WP4.18; P7-WP7.6; P9 |

## C. Engine and approach research

| # | Finding | Status | Where / why |
|---|---|---|---|
| C1 | OpenMW 0.51: Morrowind systems native, Lua combat partly hardcoded, water one level per cell, Skyrim ESM4 load-and-view only, no maintained Android build | Out (as host) | 0001 table; engine-feasibility research; fallback trigger 0001 §3 |
| C2 | OpenMW mods (dodge, lock-on, parry, sailing ship, climbing compilation, NCGD, Surefire…) and their permissions | Out (as host) | engine-feasibility §4; used only if the fallback triggers |
| C3 | Morrowind/OpenMW asset coverage for Black Marsh is thin (5–15% of the Argonian core) | In (as evidence) | 0001 rationale |
| C4 | OpenMW modern-physics fork (ragdolls, carry/throw) | Out | AI-written, unreviewed, Windows-only; ragdolls come from XP32 + Precision (P5-WP5.8) |
| C5 | openmw-web (WASM), Android community builds | Out | Skyrim host; no native phone (0007) |
| C6 | Mudcrab: converter + world viewer, not playable | Out (now) | 0001 S4 |
| C7 | Bandai Namco EULA: no RE, no derivative works, DMCA history | In | 0004; legal §1 |
| C8 | DS combat feel lives in timing data and animations; extraction of animations fragile and forbidden | In | 0004 §5; P5 animation side |
| C9 | Clean-room spec: mechanics as knowledge, own implementation | In | 0004 §2; P5-WP5.1 parity table |
| C10 | DS1 wiki says 11 i-frames for fast/mid/fat rolls vs old 13/11/9 | In | 0004 context; P1-S6; P5-WP5.1 settles; owner ruled DS1 wins |
| C11 | DSR tools: soulstruct (Linux), Paramdex DS1R, DSAnimStudio, UXM, DSR Gadget (archived), debug menu mod 266; exe packed on disk (dump at runtime); servers live since Nov 2022, no anti-cheat; offline only | In | 0004 §3; P1-S6; P5-WP5.1 |
| C12 | DSR has no HKS player script; DS3 secondary for input buffering/hyper-armour | In | 0004 §4 |
| C13 | universal-modder method: cheapest route first, the running game is the oracle, trace replay, byte round trips, circuit breaker, journal, parity documents, safety rules | In | 0010; ways-of-working §3 |
| C14 | universal-modder field notes: DSR→Elden Ring port (4 days, ~46 tests), Skyrim generated quest (~30 builds), White Knuckle climbing (~2 weeks) | In | 0010 §6 vendoring; P1 budgets; 0013 pacing |
| C15 | Hype vs evidence: viral clips; verified ports take days–weeks with a human checking builds | In | PLAN §5 estimates; 0013 |
| C16 | Ghidra 12.2 (JDK 25, PyGhidra 3.2, Docker headless); no AI skills in the NSA repo; MCP bridges (GhidraMCP, pyghidra-mcp, ReVa) fragile; Faith Runner's targeted headless scripts are the pattern | In | 0010 §4; P0-WP0.4 |
| C17 | Faith Runner, AC1 Movement Rewritten as reference reimplementations | In | 0010 §2; P6-WP6.1 |
| C18 | Sea of Thieves (EAC), BotW/Wind Waker (console IP): knowledge only from talks | In | PLAN §7; legal |
| C19 | AC4 ship controller via Ghidra: costly; arcade model from footage cheaper | In | P6-WP6.4 uses the Wind Waker model, no AC4 RE |
| C20 | "Users supply their own files" is a re-architecture for the old Pages build | In / Open | not this repo's problem (0003); old Pages exposure flagged O-12 |

## D. Skyrim-as-host research

| # | Finding | Status | Where |
|---|---|---|---|
| D1 | Runtime churn 1.7.99/1.7.104; rollback to 1.6.1170; SKSE versions; contradictory "1.9.32" line | In | 0002; P1-S3 |
| D2 | Actor values fixed (164; Variable01–10 free; ~40 obsolete) | In | P4-WP4.1 AV audit |
| D3 | Biped slots 30–61, 15 free | In | P4-WP4.11 slot table |
| D4 | Skywind (topics as prompts), Enderal (own DLL hooks dialogue menu), Dialogue History, Dynamic Dialogue Replacer, Classic Dialogue Menu, EZ2C | In | P1-S5; P4-WP4.6 |
| D5 | No persuasion menu, no 0–100 disposition in Skyrim | In | P4-WP4.6 |
| D6 | Custom Skills Framework (MIT), Sleep to Gain Experience, Sleep to Level Up, E.S.L.A., Classic Classes and Birthsigns, Experience, Skill Uncapper, Gold Is XP, Enderal progression | In | P4-WP4.1/4.2 |
| D7 | Respawn – Soulslike (grave + last bed, permissive), Respawn – Death Overhaul | In | P4-WP4.4 |
| D8 | Animated Armoury, Armory Extended, Throwable Weapons SKSE, crossbows vanilla | In | P4-WP4.11; P2-WP2.1; crossbows/thrown provisional (0016, O-15) |
| D9 | Split L/R armour meshes are an asset gap; body mesh conflicts | In / Open | P4-WP4.11; O-9 |
| D10 | Wayfinder, No Google Maps Skyrim (GPL), Compass Navigation Overhaul, quest-marker settings, Flat World Map Framework, A Quality World Map, Atlas Map Markers | In | P4-WP4.8/4.9 |
| D11 | SkyUI 6, Infinity UI, TrueHUD, PrismaUI (licence: dependency fine; forks need permission; Ultralight licence), dMenu NG, full SWF skins; Scaleform authoring poor on Linux | In | P2-WP2.8; P4-WP4.10 |
| D12 | Encounter zones min=max, Morrowloot, carriages pattern for travel, EnableFastTravel, training game setting, merchant gold | In | P4-WP4.12–4.14 |
| D13 | Beyond Skyrim: Argonia dormant; name overlap | In / Open | O-13 |
| D14 | Precision (API callbacks), TDM (no distance setter), TrueHUD, OAR (custom conditions), BFCO (active; conflicts with MCO), SCAR (MIT), CPR, UND, Wait Your Turn, Distance Based Combat, TK Dodge SE (restrictive) vs RE/Redux, Valhalla (BSD-3), Elden Parry, Rim Parry, zxlice, Blade and Blunt, Poisebreaker, Chocolate Poise (MIT), Archery Locational Damage, AMR/AMF, LoreRim/Elder Souls modlists | In | P5-WP5.2/5.3; P2-WP2.1 conflict list |
| D15 | No melee hit-zone mod; buildable from Precision's hit rigid body | In | P5-WP5.3 |
| D16 | ArgoniaCombat design (pre-hit ignore for i-frames, OAR burden-tier roll, parry window, riposte paired anims, backstab angle, poise fork, 20 m lock-on ≈ 1,400 units) | In | P5-WP5.3 |
| D17 | ±1-frame test dummy at 30/60 fps; tunnelling check | In | P5-WP5.4 |
| D18 | FromSoft-derived movesets on Nexus (e.g. Cathedral Knight) | Out | 0004 §5 |
| D19 | FreeClimb (GPL-3.0-only; Mixamo/Threepeat clips), SkyParkour, SkyClimb (superseded), EVG Animated Traversal (ladders), climbing stamina add-on | In | P6-WP6.1/6.2 |
| D20 | Underwater NG, swim sprint mod, vanilla diving | In | P6-WP6.3 |
| D21 | Sailable Ship (scripted helm, issues: deck instability, unanimated sails, save at helm, 60 fps), Sailboats (mount race, restrictive), L.V.X Boats, Rowboats (CC BY-SA), rowboat spell, Animated Ships | In | P6-WP6.4/6.5 |
| D22 | PLANCK VR-only; XP32 True Ragdoll; Precision impulses; Skyrim Delirium unverified | In / Out | P5-WP5.8 (PLANCK Out: VR only) |
| D23 | Pandora under Proton fragile; generate on the playing machine | In | P1-S3; P2 risks |
| D24 | Mutagen, Spriggit, Synthesis (not needed), xEdit under Wine (read-only), plugin2text (lossy) | In | P2-WP2.5; P0-WP0.4 |
| D25 | Terrain maps exactly (126×126 cells at one sample per vertex); VHGT re-basing; ≤6 layers per quadrant | In | P3-WP3.1 |
| D26 | Navmesh: no generator outside the CK; Recast→NVNM, CK under Wine macro, or Windows | In | P1-S4; P3-WP3.4 |
| D27 | FaceGen for new NPCs (dark faces) | In | P1-S4 options; P9 |
| D28 | xLODGen/DynDOLOD under Proton; Texconv random failure; 32–64 GB RAM | In | P3-WP3.8 |
| D29 | Papyrus compilers: CK PapyrusCompiler under Wine, Caprica (MSVC), russo-2025 compiler (V, MIT) | In | P2-WP2.5 |
| D30 | Lip generation not needed (unvoiced); silent voice files needed for text-only vanilla-path lines | In | 0012 §4 |
| D31 | BSArch; no GLB conversion needed | In | P2-WP2.5; source-map §4 |
| D32 | CK under Proton: render works, linking/triggers crash; no headless | In | P1-S4 fallback only |
| D33 | SKSE from Linux: msvc-wine first, clang-cl + xwin second (link.exe export issue) | In | P1-S1 |
| D34 | Address Library names DB; no shared Ghidra/IDA databases; skyretk RTTI dumps | In | 0010 §4 |
| D35 | Running Skyrim + SKSE under Proton headless; skip MO2; write plugins.txt; SteamAppId; DXVK on headless X | In | P1-S0/S1; P2-WP2.3 |
| D36 | Steamworks DRM: log in once, offline mode; no Goldberg | In | P1-S0; legal §1 |
| D37 | SkyrimNet MCP pattern; ConsoleUtil Extended; AutoTest (crash = stuck "started"); Crash Logger | In | P1-S1; P2-WP2.4 |
| D38 | Performance: T4 for light lists, A10G/L4 for heavy; CPU-bound on cloud Xeons; benchmark per instance | In | P1-S2 |
| D39 | CK EULA: non-commercial, owners only, ZeniMax licence, required notice; Enderal precedent | In | legal §1; P10-WP10.3 |
| D40 | Distribution: Nexus mod + FOMOD + Wabbajack + Jackify | In | P10-WP10.2 |
| D41 | Mapping table JSON → WRLD/CELL/REFR/NPC_/PACK/QUST/DIAL/INFO; ~60% of conditions native; the rest need ArgoniaCore | In | P4-WP4.6/4.8; 0009 |
| D42 | Cell water is one plane; rivers as placed water | In | P1-S7; P3-WP3.3 |
| D43 | Day-locked doors need script | In | P4-WP4.19 (shops lock) |
| D44 | Owing ledger needs Papyrus/SKSE (crime per hold faction) | In | P4-WP4.17 |
| D45 | Morrowind topic dialogue is the weakest fit; HTML menu is S3 | In | 0001; P1-S5; P4-WP4.6 |
| D46 | Levitate needs SKSE | In | P4-WP4.15 (time-boxed; drop if infeasible) |

## E. Hosting, streaming, infrastructure

| # | Item | Status | Where |
|---|---|---|---|
| E1 | AWS prices (CPU, GPU spot/on-demand, gp3, snapshots, IPv4, egress) | In | hosting-streaming §1; 0008 table |
| E2 | Graviton cheaper but Wine needs x86 | In | 0008 §1 |
| E3 | Spot with stop on interruption | In | 0008; infra/README |
| E4 | AWS MCP servers with least-privilege IAM | In | 0008 §3; P0-WP0.7 |
| E5 | RunPod (MCP, no UDP: WebRTC fails), Vast.ai (UDP, Selkies template), Azure, GCP, Lambda, Modal, Paperspace, Shadow (no browser), GeForce NOW (catalogue only) | In | hosting-streaming §2; 0008 §4 |
| E6 | Selkies (WebRTC + WebSocket/TCP 443), Moonlight-Web + Sunshine, Neko, KasmVNC, Parsec web | In | 0007 §2 |
| E7 | Corporate networks may block UDP (work Mac) | In | 0007 §2; P1-S2 |
| E8 | Software rendering for CI not usable for Skyrim | In | hosting-streaming §4; L4 on GPU box |
| E9 | Steam SSA personal use; no others on the stream | In | legal §1; 0007 §3 |
| E10 | Latency estimates table; parry on Wi-Fi workable, on 4G unreliable; compression smears foliage; 3–4 GB/h | In | hosting-streaming §6; 0007 §6 |
| E11 | Native phone vs streaming comparison (native impossible with Skyrim) | In | 0007 context |
| E12 | Two machines (build VM without GPU, GPU box on demand) | In | 0008; PLAN §3 |
| E13 | Budget estimate and levers; at the $100 limit | In | 0008 table |
| E14 | Old m7i.2xlarge box costs ~$23/month stopped | Open | O-1 |
| E15 | Old infra lessons: idle-stop, R2 vault restore, Wine prefix fragility, /tmp wiped at stop, wineboot hang with a display | In | P0-WP0.4 (idle-stop, two Wine versions, wineboot without DISPLAY, /tmp rule), P0-WP0.5 (R2 restore steps); source-map §3 |
| E16 | AWS step-by-step setup (budget, instance, IAM role glitch, spot settings, Session Manager, VS Code tunnel, Claude Code, gh) | In | infra/README "What the owner did by hand" |

## F. The old project's content, designs and lessons

| # | Item | Status | Where |
|---|---|---|---|
| F1 | Every old decision record | In | inherited-rulings.md (carry/adapt/drop per record) |
| F2 | Content counts (827 places, 959 NPC rows, 733 quests/38 staged, ~2,000 lines, 32 factions, 508 items, 42 species, hydrology) | In | 0009; P9 inventory table |
| F3 | Only ~20 places built, 5 accepted; content thin vs plan | In | P3-WP3.9; P9 |
| F4 | Heightfield origin: Tamriel Worldspaces – Argonia (118678); vault not in repo | In | 0009 §5; legal §2 |
| F5 | Seasonal water levels (old 0049) | Out | static water planes; P3-WP3.3 records the drop |
| F6 | Mist volumes (old 0124) | In (adapted) | P3-WP3.3; P8-WP8.6 |
| F7 | Phone frame rate/load-time chase, three.js performance architecture | Out | three.js-specific; inherited-rulings |
| F8 | Old Pages build exposes converted assets publicly | Open | O-12 (outside this repo) |
| F9 | Licence waiver in old 0152 ("private, undistributed") | Out | does not carry; permissions asked (0003, O-5) |
| F10 | Agent doctrine and failure modes | In | 0011; ways-of-working §1–9 |
| F11 | Cuts: mounts, fire spread, tide gating, river pirates, drifting settlements, survival, bleedout, boat chases, voice acting | Out | PLAN §7 (old 0026/0039/0042/0139) |
| F12 | Old reds (three climb visual checks, 60 fps on phone, 90 s load) | Out | three.js-specific; climbing re-done on FreeClimb |
| F13 | Polish backlog (~470 rows) | In | source-map §2; triaged in P7 |
| F14 | Dialogue on Sonnet (owner ruling in old 0079) | In | P4-WP4.7 |
| F15 | Content targets: 450–550 quests (0027) vs 550–740 (quest docs) | Open (minor) | P9 inventory table: 450–550 baseline, 550–740 stretch, owner confirms |
| F16 | 4 creature species without a source | In | P9 inventory (redesign or replace) |
| F17 | Morrowind exemplar dialogue corpus (Bethesda text) | In | kept private (source-map §1) |
| F18 | Old TS dialogue/narrative runtime reusable in PrismaUI? | In | P1-S5 evaluation |

## G. Licensing and permissions

| # | Item | Status | Where |
|---|---|---|---|
| G1 | Tropical Skyrim terms (ask; bundled third-party assets) and SSE port | In / Open | legal §2; O-5 |
| G2 | Black Marsh & Valenwood: no stated permissions; Sniper: Ghost Warrior 2 mesh | In / Open | legal §2; O-5 (that mesh to be checked and excluded if confirmed) |
| G3 | King of the Murkmire: free mods only, **no AI use** | In / Open | 0006 §7; legal §2; O-5 |
| G4 | Mihail: conversion to other games forbidden (not our case) | In | legal §2 |
| G5 | Xanmeer authors, Sign of Cipactli URL unknown | Open | O-5 |
| G6 | Nexus AI disclosure since 2026-07-31 | In | 0006 §7; P10-WP10.3 |
| G7 | Mixamo: free in games, no raw-file redistribution | In | we require FreeClimb rather than copy its clips (P6-WP6.1) |
| G8 | Pelagiad OFL; Transbot9 CC BY-NC 4.0 | In | legal §1 |
| G9 | Nexus Premium for scripted downloads | Open | O-6 |
| G10 | Repo public; no assets ever; screenshots not committed | In | 0003 |

## H. Things raised once and deliberately set aside

| # | Item | Why |
|---|---|---|
| H1 | Building on OpenMW with a mod stack ("Option A") | Superseded by Skyrim as host (0001); kept as the fallback |
| H2 | Forking OpenMW ("Option B") and animation sourcing for it | as H1 |
| H3 | Staying on three.js | owner wants an alternative; may continue separately |
| H4 | Steam Deck / Windows PC for local play | not owned/requested; noted as a future option (0007 §6) |
| H5 | Touch-only controls on the phone | not a goal; evaluated in P10 if the owner asks (0007 §5) |
| H6 | Native Android build | impossible on Skyrim (0007) |
| H7 | Codespaces | superseded in the old project; not used |
| H8 | A second GPU box for parallel L4 | only if measured queueing justifies it within budget (P9 risks) |

## I. The independent audit (2026-10-27): 68 findings, each fixed

| # | Finding | Fixed in |
|---|---|---|
| I1 | Re-timing animations "with annotations" would ship modified clips | decision 0014 §2; P1-S9/G9; P5 constants, WP5.2, WP5.9; CLAUDE.md |
| I2 | FaceGen, LOD, silent voice files are derived assets | 0014 §3–6; 0003 §7; P1-S4; P2-WP2.3; P3-WP3.8; Fuz Ro D-oh |
| I3 | Crossbows/thrown reintroduced against old 0031 | decision 0016 (provisional), O-15; inherited-rulings 0031 row |
| I4 | Budget at the cap; costs unbudgeted | 0008 hard cap, per-phase budgets, stop-and-ask rule |
| I5 | 0002 named the wrong spike | 0002 → P1-S3/G3 |
| I6 | Vanilla SWF reskins and the font SWF | 0014 §7; P4-WP4.10; P8-WP8.3; FFDec in P0-WP0.4 |
| I7 | No repo licence; GPL untracked | decision 0015, O-14; P0-WP0.1; P2-WP2.1 licence columns |
| I8 | Old registries without consumers | P4-WP4.21; source-map §1 |
| I9 | Movement formulas missing | P4-WP4.1; P6-WP6.3 |
| I10 | Disposition details; Speechcraft in base | P4-WP4.6 |
| I11 | Waking from death counts as a rest; respawn classes | P4-WP4.4 |
| I12 | Vastei tutorial scene | P7-WP7.1, WP7.3 |
| I13 | Old 0147 open calls | O-16; P4-WP4.2 |
| I14 | Skyrim dialogue-engine facts | P4-WP4.6, WP4.8 |
| I15 | Steam re-login every couple of weeks | P1-S0 steam_check |
| I16 | G3 list missing P5 mods; Precision 1.7.x port | P1-S3 union list |
| I17 | River flowmaps need the CK | P1-S7; P3-WP3.3 |
| I18 | Kit-id → base record mapping | P1-S4; P2-WP2.5 |
| I19 | Assembled interiors unproven | P3-WP3.9b |
| I20 | Owner-held permissions from 2026-09 | O-17; P2-WP2.2; legal §2 |
| I21 | Phone aspect ratios and readability | P1-S2/S5; P2-WP2.8 |
| I22 | Inventory with paperdoll had no WP | P4-WP4.10 |
| I23 | PrismaUI fallback | 0001 §2; P1/P4 risks; 0014 §7 |
| I24 | Dependency plugins on the build VM | P2-WP2.3 build-VM masters |
| I25 | UXM, Paramdex, DSAnimStudio, tes3conv | P0-WP0.4 |
| I26 | Old backlog triage | P7-WP7.5b |
| I27 | P1 ordering vs dependencies | P1 order section; S1 `/input` and `make deploy` |
| I28 | Bridge exposure | 127.0.0.1 + token + SSH tunnel (P1-S1, P2-WP2.4) |
| I29 | Brief fields | P0-WP0.2 |
| I30 | Wine versions | P0-WP0.4 two pinned versions |
| I31 | Training rules | P4-WP4.12; 0005 C13 |
| I32 | Levelling curve and rules | P4-WP4.2 |
| I33 | Phase template gaps | all phases: out of scope, risks, acceptances |
| I34 | Spike time budgets | P1 (every spike) |
| I35 | Guard WP reference | 0003 §5 |
| I36 | Where 13/11/9 is settled | 0004, P1-S6, P5-WP5.1 |
| I37 | Burden thresholds | 0004; P5 constants |
| I38 | Tier labels; RaceMenu | 0005 C3, C12; P1-S3 |
| I39 | Check-ins on a public repo | ways-of-working §5; P2 risks; P10-WP10.5 |
| I40 | Bridge capabilities used later | P2-WP2.4 (path query, music/sound events, booth mode) |
| I41 | P9 navmesh/LOD per packet | P9 packet step 10 |
| I42 | Windows machine for P10 | P10-WP10.2 |
| I43 | Owner-step instructions | P0-WP0.5 (R2), P2-WP2.2 (gist drafts), P2-WP2.3 (manual downloads) |
| I44 | Stale research re-checks | "Re-check before starting" in P0–P6 |
| I45 | Optimistic estimates | PLAN §5 re-estimate at P1 close from G8 |
| I46 | Hand-off and review numbers | ways-of-working §2 (300k/100k; 1,500 lines) |
| I47 | One game worker; per-port journals | ways-of-working §3; job_guard `--gpu` |
| I48 | KotM needs CC/AE archives | 0002 §2; P1-S3 |
| I49–I61 | Nits: soft requirement cap, underwater contract, climb numbers, stale counts, magic/alchemy/lock formulas, 0040 parries, class bonuses, tree, wording, backlog path, socket activities | P4-WP4.1/4.5/4.15/4.16/4.17/4.19; P6-WP6.1/6.3; P5-WP5.3; PLAN §3; 0006 §7; P0-WP0.1 |
| I63–I68 | Other games row; bleedout wording; S3 redefinition; /tmp; in-place reads; private-repo access | A46; P4-WP4.4; 0001 §2; P0-WP0.4; source-map; P0-WP0.5 |

## J. Research items noted and deliberately not used (audit I62)

| Item | Why not |
|---|---|
| Smithbox, WitchyBND | soulstruct covers DSR on Linux; Smithbox is Windows-only and DS3-focused |
| Cheat Engine / TGA tables | live memory editing not needed; offline capture + TAE reading suffice (0004) |
| Pyro (Papyrus build wrapper) | the reference compiler is called directly |
| SkyUILib | only needed by AutoTest, which we replace with our bridge |
| Vigilant, Skyblivion | precedents only (content on vanilla mechanics) |
| Horizon Zero Dawn fast travel mod | no fast travel at all (0005 C13) |
| Rowboat spell, Animated Ships | NPC/ambient boats; ours are ArgoniaBoats |
| reversedwithai.com list | no Morrowind/Skyrim/Souls entry |
| Morroblivion precedent | informs 0014 (install-time derivation); nothing to adopt |
| "Funny-Bones" Elden Ring controller in Skyrim | human-made report, source not found |
| Encounter zone "Match PC below minimum" flag | must stay **off** (fixed danger); noted in P4-WP4.14 by min = max |
| RenderDoc | used only for P8 look questions (P8-WP8.6) |
