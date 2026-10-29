# Accounting: every detail from the founding conversation, and where it went

The owner asked that every detail from the planning conversation and its research be **accounted for**: either
put into the plan or deliberately left out, with the reason. This ledger is that check. Each row names where the
item is handled (file and section) or why it is excluded. The planner re-reads this file at every part close
and adds rows for new owner rulings.

Legend: **In** = handled where named. **Out** = deliberately excluded (reason given). **Open** = an owner call.

## A. The owner's requirements (owner-brief §1–2)

| # | Item | Status | Where / why |
|---|---|---|---|
| A1 | Set in Argonia with the stories, quests, places from the three.js version | In | 0009; 0.1 import; source-map §1; 2.W5; 2.17; 4.2 |
| A2 | Morrowind engine for dialogue, quests, inventory, UI, adapted (content, colour themes, stats/progression changes) | In (as Morrowind's soul on Skyrim) | 0001 explains why not the Morrowind engine itself; 0005 C1–C15; Part 1 (first rungs) and Part 2 (whole) |
| A3 | Weapon and item classes matching Morrowind | In | 0005 C5; 2.3 |
| A4 | UI like Morrowind's; colour themes | In | 0005 C10; 2.2; palette import (1.2) |
| A5 | Dialogue like Morrowind's: branching topics, UI, writing style | In | 0005 C1; 0.2 G5; 1.3; 2.5; style guide import |
| A6 | Attributes and stats like Morrowind's | In | 0005 C2; 1.3 (27-skill mapping table) |
| A7 | Levelling with resting and vastei | In | 0005 C3; 1.5; 2.8 |
| A8 | Open to merging vastei with Skyrim attributes/levelling/perks; perks would need auditing | In / Open | 0005 C4; 2.1 perk audit; O-4 |
| A9 | No quest markers; directions written into the journal, followed like verbal directions | In | 0005 C7; 2.12 (directions generator + validator); 2.W3 route graph |
| A10 | Morrowind-style journal | In | 0005 C8; 2.12 |
| A11 | Morrowind-style map | In | 0005 C9; 2.W4 map image; 2.12 |
| A12 | Cuirass, pauldrons etc. (nice to have) | In | 0005 C6; 2.3; O-9 for split meshes |
| A13 | Custom HUD | In | 0005 C11; 2.2 |
| A14 | Dark Souls combat hooked to Morrowind-based stats | In | 0004, 0019; 2.7 §a wiring spec, 2.7 §c state machine |
| A15 | Use the existing thinking in the argonia repo for combat/stats | In | imported 76-stats-progression and combat docs; 1.3, 1.6, 2.7, 2.8 read lists |
| A16 | ds3-open-re as a reverse-engineering example | Out (as a tool) | it is netcode only (engine-feasibility §3, um-ghidra-lens §3.1); DSR data tools used instead (0004) |
| A17 | Ghidra, universal-modder, Ghidrust for RE and extraction | In | 0010 (route order, scalpel use, vendored skills); 0.1/0.4; 2.7 §b; Ghidrust Out as experimental (um-ghidra-lens §2.2) |
| A18 | "Anything else from Skyrim" from Mudcrab | Out (for now) | Mudcrab is a world viewer, not playable (0001 table); Skyrim itself is the host; watch as S4 |
| A19 | Free climbing (Mirror's Edge parkour-in-Skyrim reference; anything like free climbing) | In | 2.13 (FreeClimb + SkyParkour); the "one day" video is a second-hand report (um-ghidra-lens §4) |
| A20 | Player-controlled boats; research best source | In | 0.2 G3; 2.15 (Sailable Ship base, Wind Waker model, ownership) |
| A21 | Skyrim SE or DS3 level graphics | In | Skyrim host; 0.3 Community Shaders; 4.6 |
| A22 | Modern features: volumetric or pseudo-volumetric fog, lighting | In | 0.3; 2.W2 (mist); 4.6 |
| A23 | Minimal new art; extract/adapt from Morrowind, Skyrim SE, DS1/3 and community mods | In / partly Out | 0006 §6; Skyrim and mod assets used at runtime; **Morrowind and DS assets Out** (licences, 0003/0004; Morrowind assets cannot run in Skyrim without conversion, which Bethesda's terms bind to Morrowind) |
| A24 | Reuse as far as possible; don't sink hundreds of dollars | In | 0010; 0008 budget; PLAN §2 |
| A25 | Playable only if you own the base games; ship nothing we shouldn't (Mudcrab model) | In | 0003; 3.4 |
| A26 | Owns Skyrim SE, Morrowind GOTY, DS3 (and DSR) on Steam | In | 0.1 downloads; legal §1 |
| A27 | Playable on Honor Magic V5 and MacBook Air M2; nothing installed on the Mac | In | 0007 streaming; VS Code tunnel for development (0008) |
| A28 | Streaming from a GPU VM for seamless saves | In | 0007 §4; 0.3 |
| A29 | Not wedded to RunPod; research others with good Claude Code/MCP compatibility | In | hosting-streaming §2; 0008 §3–4 (AWS CLI/MCP; RunPod out for play due to UDP; Vast.ai fallback) |
| A30 | Claude Code on an affordable AWS instance, ≤ $100/month | In | 0008: $100 is a **hard cap**; per-part budgets; weekly projection with a stop-and-ask rule (T-COST) |
| A31 | Autonomous testing loops on AWS or a GPU service | In | ways-of-working §3; 0.2 G8; 0.4 |
| A32 | Not Hetzner | In | 0008 §4 |
| A33 | 20x (parallel, ~60 h/wk) vs 5x (~120 h/wk) plan; usage arithmetic | In / Open | 0013; O-2 |
| A34 | As cheaply as possible | In | 0008 levers; idle-stop everywhere |
| A35 | Free; no commercial use | In | owner-brief; legal §1; 3.4 |
| A36 | Pelagiad font throughout | In | 0006 §4; 2.2 |
| A37 | New music | In / Open | 0006 §5; 2.16; O-8 |
| A38 | Full audit of UI and art; overhaul or tweak to fit Black Marsh; no Nordic elements | In | 0006; 0012; T-IMM; 0.5; 2.17 §b; 4.1 at scale |
| A39 | Agentic approach to cover everything 100% | In | 0006 §1–3 (enumerated inventory, coverage gate); 4.1 |
| A40 | Fal MCP for minor new art | In | 0006 §6–7; legal §4 |
| A41 | New public repo; old repo untouched; may continue three.js separately | In | 0003; 0009 §1; source-map |
| A42 | Plan for the future agent; bootstrap its own structure and ways of working from the old repo | In | 0.1/0.2; ways-of-working; source-map §3 |
| A43 | Plan complete, no petering out in later phases | In | every chunk brief has goal, starting state, re-check/read-first, deliverables with acceptance, Loops, owner check, risks, out of scope, with design detail written now and steps rewritten just in time (0023 §7); an independent audit (68 findings, all fixed: section I) |
| A44 | Tropical Skyrim (SSE 78044) as the source for any base-Skyrim assets | In | 0006 §8; 0.3; 2.W1; 2.W4; 4.1; legal §2 |
| A46 | "Other games if relevant" the owner owns | In | 0010 §2 (study owned games); none needed beyond Skyrim SE, Morrowind, DSR, DS3 so far; the planner asks the owner's library when a system lacks a reference |
| A45 | Use the universal-modder/Ghidra perspective as a primary lens across every system, water included | In | 0010; um-ghidra-lens §6 per-system table; 0.2 G7 (water question as the first Ghidra use); 2.7 §b |

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
| B12 | Crossbows and thrown weapons back in | 0016 |
| B13 | Our own original UI for major screens and our own HUD, like the old repo's; use mod-scene or OpenMW UI only if it saves work | 0017 (port of the old React design system; OpenMW as structural reference; no Morrowind UI exists in the Skyrim mod scene) |
| B14 | The $100 cap is AWS infrastructure only | 0008 |
| B16 | The owner can get the Creation Kit; "isn't that how mods normally get made?" | 0018 (CK as a scripted tool; records by code; Papyrus compiler and base scripts come from the CK); 0.1; 0.5; 2.W4 |
| B17 | Study OpenMW's window layouts and contents to improve our UI | 0017 §8; 2.2 §a |
| B40 | 2026-10-29: the order of importance (world and places; quests, story, people; combat; progression; UI) and licence to change the plan | 0027; PLAN §2, §5; phases/README; Part 1 re-cut (1.2, 1.4, 1.6, 1.7); 2.W1 after G4; 2-slice order |
| B41 | 2026-10-29: critical review of the old ways of working; adopt rtk and some agent types; the cheaper 0.0 way of working | 0027 §7–9; ways-of-working §1, §6; CLAUDE.md; `.claude/settings.json` (rtk hook); 0.1 §b |
| B42 | 2026-10-29: Morrowind-like mods welcome (Magic Expanded 133435); permissive UI mods as a foundation (Dear Diary 23010, Wood and Paper 44174, Oblivion-like Loading Menu 38708); an easy early UI, the big overhaul later | 0027 §5; 1.2 §a; 0.2 G3, G11; the reuse audit (0.1 §j) |
| B43 | 2026-10-29: October's AWS overspend explained; the $100 cap binds from November | 0008 note; owner-brief |
| B18 | Holistic UI design; "eyes on" transitions in focused loops; no jarring vanilla screens (e.g. constellations) | 0017 §7; 2.2 §a (UI map), 2.2 (transition loop); 3.1; perk constellations hidden (2.1) |
| B19 | Load Skyrim's own symbols (sneak eye) from the player's files | 0017 §5; 0014 §8; 1.2 |
| B20 | Trim flourishes are the owner's ChatGPT art | 0017 §5; sourcing register |
| B21 | Do not reproduce the old project's buggy combat and animations; DS1R numbers, system and feel, wired to our stats | 0019; combat written around DSR (1.6 the tuned stack on the sheet; 2.7 §0 the map, §a wiring spec, 2.7 §c DS1 state machine in a tested core, 2.7 §e movesets chosen for fidelity, 2.7 §h side-by-side with DSR); inherited-rulings 0037/0040/0090 |
| B22 | Use universal-modder / Ghidra agent skills and methods wherever useful | 0020 (full skill set, agents, `um` CLI, field-note reading list per chunk, ReVa and pyghidra-mcp, "Prior art" brief field, O-19 giving back); 0.1/0.4; 0.2, 2.5, 2.7, 2.13, 2.15, 3.4 read lists; vendored one skill at a time (0027 §7) |
| B23 | Carry the "fast focused loops with eyes" way of working and its ladder, updated for the new infrastructure | 0021; docs/loops.md (ladder rebuilt: L2 core runner + L4 game runner from a studio scene); a Loops section in every chunk brief; ways-of-working §3; CLAUDE.md |
| B24 | The lane that builds a feature tests the feature and its joins in the same loop; no separate seam loops | 0021 §2; loops.md rule 2; every brief's "Joins owned" |
| B25 | Journeys are headless only: no agent plays the game by looking; no harness or capture rigs | 0021 §3; loops.md rule 5; 0.4 §c (the two runners, schema refuses stills and clips in a journey) |
| B26 | A studio for agents and the owner: drop in, teleport, test, without the new-game flow | 0022; 0.4 §b; every owner check names a studio scene or place |
| B28 | Critical review: test the joins and combat feel early; the old project gives goals and content, every system built natively (owner, 2026-10-28) | 0023 (Part 1 core loop and verdict); 0026; 0.1 §f goals list; 0.2 G10 native map |
| B29 | Stream vanilla Skyrim to the phone and Mac first, with touch and GameSir controls; stop if unplayable | 0.0 (G0); phases/README dependency table; PLAN §6 |
| B30 | Review and overhaul the old dialogue and quest tests (many bad) | 0.1 test review; 0.2 G10 counts only keep tests; 2.5 and 2.12 tests built from the review |
| B31 | Is the one-place core loop actually cheaper than the alternatives? | 0023 "Why the thread is worth its cost" (an insurance cost of about 2–3 weeks; trimmed to the host-risky systems) |
| B27 | Work in parts like the old repo, reviewed critically: slice places and systems first, then the new-game flow, then the sideways build-out; rewrite the plan holistically | 0023 (five parts; the core loop as the host go/no-go; the slice in two tracks; immersion as a gate; briefs just in time); phases/README.md; PLAN §5; this rewrite replaced the first plan's eleven phases |
| B32 | Dialogue reads as Morrowind's; old written lines not used; skill from scratch (2026-10-27) | 0024 §6–7; `dialogue-write` brought in at 0.1 §b, fitted at §i; lines written in 1.3, 2.5, 3.3, 4.2 |
| B33 | Banned constructions (personification, verbless fragments, dangling modifiers, opaque references), British English, disposition hints (2026-10-27) | `dialogue-write/bans.yaml` and `lint.py`; 0024; 2.5 owner check feeds new bans |
| B34 | Any of ten races as speaker or player; address by race, faction, rank (2026-10-27) | `dialogue-write/voices.md`, SKILL §2; 2.4 persona fields; 2.5 §b listener variants |
| B35 | Consistent first time across quests, places, dialogue, characters, facts; quest writer and reviewer skills; per-type principles from research (2026-10-27) | 0024; `quest-write`, `quest-review`; the nine `docs/research/2026-10-27/quest-*` and `questline-design` packs (0.1 §b) |
| B36 | Quests have varied skill-based action, by faction profile; output fits the engine; old quest design is the foundation (2026-10-28) | 0024 §8–9; `quest-write/principles/actions.md`; 0.1 §i (catalogue, profiles, engine mapping table); 2.12 §a, 4.2 step 5, 4.3 |
| B37 | A detectives' faction rival to Shadowscales and Night-Reed, escalating to a murder-mystery finale (2026-10-27) | 0025; 0.1 §i coverage check; 2.4 §c lore pass and record; 2.5 §a, 2.12 §a investigation support; 4.1 §d line record; 4.2, 4.3 |
| B38 | Bring in the side branch's writing skills and build their use into the later chunks (2026-10-28) | 0.1 §b (port list, adaptations, acceptance), §i (fit to the import); 1.3, 2.4, 2.5, 2.12, 3.3, 4.1–4.3; source-map §5 |
| B15 | FaceGen and distant terrain: "surely handled by Skyrim's engine" | 0014 §3–4 explains: the engine draws them, but from per-NPC face files and per-worldspace LOD files that a new worldspace and new NPCs lack; templates reuse existing faces; terrain LOD meshes are ours and may ship |

## C. Engine and approach research

| # | Finding | Status | Where / why |
|---|---|---|---|
| C1 | OpenMW 0.51: Morrowind systems native, Lua combat partly hardcoded, water one level per cell, Skyrim ESM4 load-and-view only, no maintained Android build | Out (as host) | 0001 table; engine-feasibility research; fallback trigger 0001 §3 |
| C2 | OpenMW mods (dodge, lock-on, parry, sailing ship, climbing compilation, NCGD, Surefire…) and their permissions | Out (as host) | engine-feasibility §4; used only if the fallback triggers |
| C3 | Morrowind/OpenMW asset coverage for Black Marsh is thin (5–15% of the Argonian core) | In (as evidence) | 0001 rationale |
| C4 | OpenMW modern-physics fork (ragdolls, carry/throw) | Out | AI-written, unreviewed, Windows-only; ragdolls come from XP32 + Precision (2.7 §i) |
| C5 | openmw-web (WASM), Android community builds | Out | Skyrim host; no native phone (0007) |
| C6 | Mudcrab: converter + world viewer, not playable | Out (now) | 0001 S4 |
| C7 | Bandai Namco EULA: no RE, no derivative works, DMCA history | In | 0004; legal §1 |
| C8 | DS combat feel lives in timing data and animations; extraction of animations fragile and forbidden | In | 0004 §5; 2.7 §e (the animation side) |
| C9 | Clean-room spec: mechanics as knowledge, own implementation | In | 0004 §2; 2.7 §b parity table |
| C10 | DS1 wiki says 11 i-frames for fast/mid/fat rolls vs old 13/11/9 | In | 0004 context; 0.2 G6; 2.7 §b settles; owner ruled DS1 wins |
| C11 | DSR tools: soulstruct (Linux), Paramdex DS1R, DSAnimStudio, UXM, DSR Gadget (archived), debug menu mod 266; exe packed on disk (dump at runtime); servers live since Nov 2022, no anti-cheat; offline only | In | 0004 §3; 0.2 G6; 2.7 §b |
| C12 | DSR has no HKS player script; DS3 secondary for input buffering/hyper-armour | In | 0004 §4 |
| C13 | universal-modder method: cheapest route first, the running game is the oracle, trace replay, byte round trips, circuit breaker, journal, parity documents, safety rules | In | 0010; ways-of-working §3 |
| C14 | universal-modder field notes: DSR→Elden Ring port (4 days, ~46 tests), Skyrim generated quest (~30 builds), White Knuckle climbing (~2 weeks) | In | 0010 §6 vendoring; 0.2 budgets; 0013 pacing |
| C15 | Hype vs evidence: viral clips; verified ports take days–weeks with a human checking builds | In | PLAN §5 estimates; 0013 |
| C16 | Ghidra 12.2 (JDK 25, PyGhidra 3.2, Docker headless); no AI skills in the NSA repo; MCP bridges (GhidraMCP, pyghidra-mcp, ReVa) fragile; Faith Runner's targeted headless scripts are the pattern | In | 0010 §4; 0.1 |
| C17 | Faith Runner, AC1 Movement Rewritten as reference reimplementations | In | 0010 §2; 2.13 |
| C18 | Sea of Thieves (EAC), BotW/Wind Waker (console IP): knowledge only from talks | In | PLAN §7; legal |
| C19 | AC4 ship controller via Ghidra: costly; arcade model from footage cheaper | In | 2.15 uses the Wind Waker model, no AC4 RE |
| C20 | "Users supply their own files" is a re-architecture for the old Pages build | In / Open | not this repo's problem (0003); old Pages exposure flagged O-12 |

## D. Skyrim-as-host research

| # | Finding | Status | Where |
|---|---|---|---|
| D1 | Runtime churn 1.7.99/1.7.104; rollback to 1.6.1170; SKSE versions; contradictory "1.9.32" line | In | 0002; 0.2 G3 |
| D2 | Actor values fixed (164; Variable01–10 free; ~40 obsolete) | In | 1.3 AV audit |
| D3 | Biped slots 30–61, 15 free | In | 2.3 slot table |
| D4 | Skywind (topics as prompts), Enderal (own DLL hooks dialogue menu), Dialogue History, Dynamic Dialogue Replacer, Classic Dialogue Menu, EZ2C | In | 0.2 G5; 2.5 |
| D5 | No persuasion menu, no 0–100 disposition in Skyrim | In | 2.5 |
| D6 | Custom Skills Framework (MIT), Sleep to Gain Experience, Sleep to Level Up, E.S.L.A., Classic Classes and Birthsigns, Experience, Skill Uncapper, Gold Is XP, Enderal progression | In | 1.3; 1.5; 2.8 |
| D7 | Respawn – Soulslike (grave + last bed, permissive), Respawn – Death Overhaul | In | 2.8 |
| D8 | Animated Armoury, Armory Extended, Throwable Weapons SKSE, crossbows vanilla | In | 2.3; 0.3; crossbows/thrown in (0016, owner ruling) |
| D9 | Split L/R armour meshes are an asset gap; body mesh conflicts | In / Open | 2.3; O-9 |
| D10 | Wayfinder, No Google Maps Skyrim (GPL), Compass Navigation Overhaul, quest-marker settings, Flat World Map Framework, A Quality World Map, Atlas Map Markers | In | 2.12 |
| D11 | SkyUI 6, Infinity UI, TrueHUD, PrismaUI (licence: dependency fine; forks need permission; Ultralight licence), dMenu NG, full SWF skins; Scaleform authoring poor on Linux | In | 1.2; 2.2 |
| D12 | Encounter zones min=max, Morrowloot, carriages pattern for travel, EnableFastTravel, training game setting, merchant gold | In | 2.6; 2.7 §j |
| D13 | Beyond Skyrim: Argonia dormant; name overlap | In / Open | O-13 |
| D14 | Precision (API callbacks), TDM (no distance setter), TrueHUD, OAR (custom conditions), BFCO (active; conflicts with MCO), SCAR (MIT), CPR, UND, Wait Your Turn, Distance Based Combat, TK Dodge SE (restrictive) vs RE/Redux, Valhalla (BSD-3), Elden Parry, Rim Parry, zxlice, Blade and Blunt, Poisebreaker, Chocolate Poise (MIT), Archery Locational Damage, AMR/AMF, LoreRim/Elder Souls modlists | In | 1.6; 2.7 §0, §c, §d; 0.3 conflict list |
| D15 | No melee hit-zone mod; buildable from Precision's hit rigid body | In | 2.7 §d (per-hitbox rates as DS1 data defines them, 0019) |
| D16 | ArgoniaCombat design (pre-hit ignore for i-frames, OAR burden-tier roll, parry window, riposte paired anims, backstab angle, poise fork, 20 m lock-on ≈ 1,400 units) | In (adapter mechanics) / replaced (numbers) | 2.7 §d adapter; numbers and rules now from DSR (0019): lock-on from `LockCamParam`, per-hitbox rates instead of head ×2, poise in our core (Chocolate Poise as reference only) |
| D17 | ±1-frame test dummy at 30/60 fps; tunnelling check | In | 2.7 §f |
| D18 | FromSoft-derived movesets on Nexus (e.g. Cathedral Knight) | Out | 0004 §5 |
| D19 | FreeClimb (GPL-3.0-only; Mixamo/Threepeat clips), SkyParkour, SkyClimb (superseded), EVG Animated Traversal (ladders), climbing stamina add-on | In | 0.2 G3; 2.13 |
| D20 | Underwater NG, swim sprint mod, vanilla diving | In | 2.13 |
| D21 | Sailable Ship (scripted helm, issues: deck instability, unanimated sails, save at helm, 60 fps), Sailboats (mount race, restrictive), L.V.X Boats, Rowboats (CC BY-SA), rowboat spell, Animated Ships | In | 0.2 G3; 2.15 |
| D22 | PLANCK VR-only; XP32 True Ragdoll; Precision impulses; Skyrim Delirium unverified | In / Out | 2.7 §i (PLANCK Out: VR only) |
| D23 | Pandora under Proton fragile; generate on the playing machine | In | 0.2 G3; 0.3 risks |
| D24 | Mutagen, Spriggit, Synthesis (not needed), xEdit under Wine (read-only), plugin2text (lossy) | In | 0.5; 0.1 |
| D25 | Terrain maps exactly (126×126 cells at one sample per vertex); VHGT re-basing; ≤6 layers per quadrant | In | 2.W1 |
| D26 | Navmesh: no generator outside the CK; Recast→NVNM, CK under Wine macro, or Windows | In | 0.2 G4; 2.W4 |
| D27 | FaceGen for new NPCs (dark faces) | In | 0.2 G4 options; 2.4; 4.2 |
| D28 | xLODGen/DynDOLOD under Proton; Texconv random failure; 32–64 GB RAM | In | 2.W4 |
| D29 | Papyrus compilers: CK PapyrusCompiler under Wine, Caprica (MSVC), russo-2025 compiler (V, MIT) | In | 0.5 |
| D30 | Lip generation not needed (unvoiced); silent voice files needed for text-only vanilla-path lines | In | 0012 §4 |
| D31 | BSArch; no GLB conversion needed | In | 0.5; source-map §4 |
| D32 | CK under Proton: render works, linking/triggers crash; no headless | In | 0.2 G4 fallback only |
| D33 | SKSE from Linux: msvc-wine first, clang-cl + xwin second (link.exe export issue) | In | 0.2 G1 |
| D34 | Address Library names DB; no shared Ghidra/IDA databases; skyretk RTTI dumps | In | 0010 §4 |
| D35 | Running Skyrim + SKSE under Proton headless; skip MO2; write plugins.txt; SteamAppId; DXVK on headless X | In | 0.2 S0, G1; 0.3 |
| D36 | Steamworks DRM: log in once, offline mode; no Goldberg | In | 0.2 S0; legal §1 |
| D37 | SkyrimNet MCP pattern; ConsoleUtil Extended; AutoTest (crash = stuck "started"); Crash Logger | In | 0.2 G1; 0.4 |
| D38 | Performance: T4 for light lists, A10G/L4 for heavy; CPU-bound on cloud Xeons; benchmark per instance | In | 0.2 G2 |
| D39 | CK EULA: non-commercial, owners only, ZeniMax licence, required notice; Enderal precedent | In | legal §1; 3.4 |
| D40 | Distribution: Nexus mod + FOMOD + Wabbajack + Jackify | In | 3.4 |
| D41 | Mapping table JSON → WRLD/CELL/REFR/NPC_/PACK/QUST/DIAL/INFO; ~60% of conditions native; the rest need ArgoniaCore | In | 2.5; 2.12; 0009 |
| D42 | Cell water is one plane; rivers as placed water | In | 0.2 G7; 2.W2 |
| D43 | Day-locked doors need script | In | 2.4 (shops lock) |
| D44 | Owing ledger needs Papyrus/SKSE (crime per hold faction) | In | 2.11 |
| D45 | Morrowind topic dialogue is the weakest fit; HTML menu is S3 | In | 0001; 0.2 G5; 2.5 |
| D46 | Levitate needs SKSE | In | 2.9 (time-boxed; drop if infeasible) |

## E. Hosting, streaming, infrastructure

| # | Item | Status | Where |
|---|---|---|---|
| E1 | AWS prices (CPU, GPU spot/on-demand, gp3, snapshots, IPv4, egress) | In | hosting-streaming §1; 0008 table |
| E2 | Graviton cheaper but Wine needs x86 | In | 0008 §1 |
| E3 | Spot with stop on interruption | In | 0008; infra/README |
| E4 | AWS MCP servers with least-privilege IAM | In | 0008 §3; 0.1 |
| E5 | RunPod (MCP, no UDP: WebRTC fails), Vast.ai (UDP, Selkies template), Azure, GCP, Lambda, Modal, Paperspace, Shadow (no browser), GeForce NOW (catalogue only) | In | hosting-streaming §2; 0008 §4 |
| E6 | Selkies (WebRTC + WebSocket/TCP 443), Moonlight-Web + Sunshine, Neko, KasmVNC, Parsec web | In | 0007 §2 |
| E7 | Corporate networks may block UDP (work Mac) | In | 0007 §2; 0.2 G2 |
| E8 | Software rendering for CI not usable for Skyrim | In | hosting-streaming §4; L4 on GPU box |
| E9 | Steam SSA personal use; no others on the stream | In | legal §1; 0007 §3 |
| E10 | Latency estimates table; parry on Wi-Fi workable, on 4G unreliable; compression smears foliage; 3–4 GB/h | In | hosting-streaming §6; 0007 §6 |
| E11 | Native phone vs streaming comparison (native impossible with Skyrim) | In | 0007 context |
| E12 | Two machines (build VM without GPU, GPU box on demand) | In | 0008; PLAN §3 |
| E13 | Budget estimate and levers; at the $100 limit | In | 0008 table |
| E14 | Old m7i.2xlarge box costs ~$23/month stopped | Open | O-1 |
| E15 | Old infra lessons: idle-stop, R2 vault restore, Wine prefix fragility, /tmp wiped at stop, wineboot hang with a display | In | 0.1 (idle-stop, two Wine versions, wineboot without DISPLAY, /tmp rule), 0.1 (R2 restore steps); source-map §3 |
| E16 | AWS step-by-step setup (budget, instance, IAM role glitch, spot settings, Session Manager, VS Code tunnel, Claude Code, gh) | In | infra/README "What the owner did by hand" |

## F. The old project's content, designs and lessons

| # | Item | Status | Where |
|---|---|---|---|
| F1 | Every old decision record | In | inherited-rulings.md (carry/adapt/drop per record) |
| F2 | Content counts (827 places, 959 NPC rows, 733 quests/38 staged, ~2,000 lines, 32 factions, 508 items, 42 species, hydrology) | In | 0009; 4.2 inventory table |
| F3 | Only ~20 places built, 5 accepted; content thin vs plan | In | 2.W5 (the sixteen in two waves); 4.1 (Helstrom, cities); 4.2 |
| F4 | Heightfield origin: Tamriel Worldspaces – Argonia (118678); vault not in repo | In | 0009 §5; legal §2 |
| F5 | Seasonal water levels (old 0049) | Out | static water planes; 2.W2 records the drop |
| F6 | Mist volumes (old 0124) | In (adapted) | 2.W2; 4.6 |
| F7 | Phone frame rate/load-time chase, three.js performance architecture | Out | three.js-specific; inherited-rulings |
| F8 | Old Pages build exposes converted assets publicly | Open | O-12 (outside this repo) |
| F9 | Licence waiver in old 0152 ("private, undistributed") | Out | does not carry; permissions asked (0003, O-5) |
| F10 | Agent doctrine and failure modes | In | 0011; ways-of-working §1–9 |
| F11 | Cuts: mounts, fire spread, tide gating, river pirates, drifting settlements, survival, bleedout, boat chases, voice acting | Out | PLAN §7 (old 0026/0039/0042/0139) |
| F12 | Old reds (three climb visual checks, 60 fps on phone, 90 s load) | Out | three.js-specific; climbing re-done on FreeClimb |
| F13 | Polish backlog (~470 rows) | In | source-map §2; triaged once in 0.1 |
| F14 | Dialogue on Sonnet (owner ruling in old 0079) | In | `dialogue-writer` frontmatter (0.1 §b); 0024 consequences |
| F15 | Content targets: 450–550 quests (0027) vs 550–740 (quest docs) | Open (minor) | 4.2 inventory table; O-18 at 4.1: 450–550 baseline, 550–740 stretch, owner confirms |
| F16 | 4 creature species without a source | In | 4.2 inventory (redesign or replace) |
| F17 | Morrowind exemplar dialogue corpus (Bethesda text, a UESP pull; Morrowind not owned on Steam) | Open | private only, never committed (source-map §1, legal-and-sourcing §1); O-21 confirms at 0.1 |
| F18 | Old TS dialogue/narrative runtime reusable in PrismaUI? | Out | 0026: old code is goal evidence only; G5 tries tes4skyrim's MorrowindRuntime first |

## G. Licensing and permissions

| # | Item | Status | Where |
|---|---|---|---|
| G1 | Tropical Skyrim terms (ask; bundled third-party assets) and SSE port | In / Open | legal §2; O-5 |
| G2 | Black Marsh & Valenwood: no stated permissions; Sniper: Ghost Warrior 2 mesh | In / Open | legal §2; O-5 (that mesh to be checked and excluded if confirmed) |
| G3 | King of the Murkmire: free mods only, **no AI use** | In / Open | 0006 §7; legal §2; O-5 |
| G4 | Mihail: conversion to other games forbidden (not our case) | In | legal §2 |
| G5 | Xanmeer authors, Sign of Cipactli URL unknown | Open | O-5 |
| G6 | Nexus AI disclosure since 2026-07-31 | In | 0006 §7; 3.4 |
| G7 | Mixamo: free in games, no raw-file redistribution | In | we require FreeClimb rather than copy its clips (2.13) |
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
| H5 | Touch-only controls on the phone | the stream client's touch overlay or a pad, whichever G2 records (0.2 G2, 3.1); a native touch UI is not a goal (0007 §5) |
| H6 | Native Android build | impossible on Skyrim (0007) |
| H7 | Codespaces | superseded in the old project; not used |
| H8 | A second GPU box for parallel L4 | only if measured queueing justifies it within budget (4.2 risks; loops.md rule 10) |

## I. The independent audit (2026-10-27): 68 findings, each fixed

| # | Finding | Fixed in |
|---|---|---|
| I1 | Re-timing animations "with annotations" would ship modified clips | decision 0014 §2; 0.2 G9; 2.7 fixed rules, 2.7 §d, 2.7 §e, 2.7 §l; CLAUDE.md |
| I2 | FaceGen, LOD, silent voice files are derived assets | 0014 §3–6; 0003 §7; 0.2 G4; 0.3; 2.W4; Fuz Ro D-oh |
| I3 | Crossbows/thrown reintroduced against old 0031 | decision 0016; the owner confirmed them on 2026-10-27; inherited-rulings 0031 row |
| I4 | Budget at the cap; costs unbudgeted | 0008 hard cap, per-part budgets, stop-and-ask rule |
| I5 | 0002 named the wrong spike | 0002 → 0.2 G3 |
| I6 | Vanilla SWF reskins and the font SWF | 0014 §7; 2.2; 3.1; FFDec in 0.1 |
| I7 | No repo licence; GPL untracked | decision 0015, O-14; 0.1; 0.3 licence columns |
| I8 | Old registries without consumers | 2.12 §c and 2.14; source-map §1 |
| I9 | Movement formulas missing | 1.3; 2.13 |
| I10 | Disposition details; Speechcraft in base | 2.5 |
| I11 | Waking from death counts as a rest; respawn classes | 2.8 |
| I12 | Vastei tutorial scene | 3.3, 2.17 |
| I13 | Old 0147 open calls | O-16; 2.8 |
| I14 | Skyrim dialogue-engine facts | 2.5, 2.12 |
| I15 | Steam re-login every couple of weeks | 0.2 S0 steam_check |
| I16 | G3 list missing combat mods; Precision 1.7.x port | 0.2 G3 union list |
| I17 | River flowmaps need the CK | 0.2 G7; 2.W2 |
| I18 | Kit-id → base record mapping | 0.2 G4; 0.5 |
| I19 | Assembled interiors unproven | 2.W5 §d |
| I20 | Owner-held permissions from 2026-09 | O-17; 0.3; legal §2 |
| I21 | Phone aspect ratios and readability | 0.2 G2/S5; 1.2 |
| I22 | Inventory with paperdoll had no WP | 2.2 |
| I23 | PrismaUI fallback | 0001 §2; 0.2 and 2.5 risks; 0014 §7 |
| I24 | Dependency plugins on the build VM | 0.3 build-VM masters |
| I25 | UXM, Paramdex, DSAnimStudio, tes3conv | 0.1 |
| I26 | Old backlog triage | 0.1 |
| I27 | Spike ordering vs dependencies | 0.2 order section; S1 `/input` and `make deploy` |
| I28 | Bridge exposure | 127.0.0.1 + token + SSH tunnel (0.2 G1, 0.4) |
| I29 | Brief fields | 0.1 |
| I30 | Wine versions | 0.1 two pinned versions |
| I31 | Training rules | 2.6; 0005 C13 |
| I32 | Levelling curve and rules | 2.8 |
| I33 | Brief template gaps | every chunk brief: out of scope, risks, acceptances |
| I34 | Spike time budgets | 0.2 (every spike) |
| I35 | Guard WP reference | 0003 §5 |
| I36 | Where 13/11/9 is settled | 0004, 0.2 G6, 2.7 §b |
| I37 | Burden thresholds | 0004; 1.3 sheet; 2.7 §a |
| I38 | Tier labels; RaceMenu | 0005 C3, C12; 0.2 G3 |
| I39 | Check-ins on a public repo | ways-of-working §5; CLAUDE.md (scenes named, never machine links); 3.4 |
| I40 | Bridge capabilities used later | 0.4 (path query, music/sound events, booth mode) |
| I41 | Navmesh/LOD per packet | 4.2 packet step 10 |
| I42 | Windows machine for release tests | 3.4 |
| I43 | Owner-step instructions | 0.1 (R2), 0.3 (gist drafts), 0.3 (manual downloads) |
| I44 | Stale research re-checks | "Re-check before starting" in every chunk brief |
| I45 | Optimistic estimates | PLAN §5 re-estimates at 0.2 (G8), 1.7, 2.17 and 4.1 |
| I46 | Hand-off and review numbers | ways-of-working §2 (300k/100k; 1,500 lines) |
| I47 | One game worker; per-port journals | ways-of-working §3; job_guard `--gpu` |
| I48 | KotM needs CC/AE archives | 0002 §2; 0.2 G3 |
| I49–I61 | Nits: soft requirement cap, underwater contract, climb numbers, stale counts, magic/alchemy/lock formulas, 0040 parries, class bonuses, tree, wording, backlog path, socket activities | 1.3; 2.1; 2.4; 2.9; 2.10; 2.11; 2.13; 2.7 §d; PLAN §3; 0006 §7; 0.1 |
| I63–I68 | Other games row; bleedout wording; S3 redefinition; /tmp; in-place reads; private-repo access | A46; 2.8; 0001 §2; 0.1; source-map; 0.1 |

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
| Encounter zone "Match PC below minimum" flag | must stay **off** (fixed danger); noted in 2.7 §j by min = max |
| RenderDoc | used only for look questions (4.6) |
