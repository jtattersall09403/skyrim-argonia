# The plan: Elder Souls: Argonia on Skyrim SE

Written 2026-10-27 and restructured 2026-10-28 for the Claude Code planner that will build this, from a long
founding conversation with the owner, twelve research reports and a review of the old project's plan. Read this
file in full at the start of every planning session, then [PROGRESS.md](PROGRESS.md), then
[phases/README.md](phases/README.md), then the current part's README and chunk brief.

## 1. What we are building

A free **Skyrim Special Edition total conversion** set in **Argonia (Black Marsh)**, built from the world,
stories, quests and places authored in `jtattersall09403/elder-souls-argonia`, with:

- **Morrowind's soul**: topic-hyperlink dialogue, seven attributes and 27 skills, rest-and-vastei levelling,
  Morrowind item classes and armour pieces, no quest markers (directions in the journal), a Morrowind journal,
  map, UI and HUD, Pelagiad everywhere ([decision 0005](decisions/0005-the-morrowind-soul-contract.md));
- **Dark Souls 1 combat** measured from Dark Souls Remastered and wired to Argonia's Morrowind-based stats
  ([0004](decisions/0004-ds1-remastered-is-the-combat-oracle.md));
- **free climbing, swimming and diving, sailable and ownable boats**;
- **Skyrim SE-level graphics** with modern lighting and fog;
- **no Nordic element anywhere** ([0006](decisions/0006-black-marsh-immersion-no-nordic-element-survives.md),
  [0012](decisions/0012-vanilla-skyrim-is-quarantined.md));
- **nothing shipped that the player does not own** ([0003](decisions/0003-nothing-shipped-that-players-do-not-own.md)):
  players need Skyrim SE plus a pinned list of free mods; the repo is public and holds only our code and data.

The owner plays it streamed to a browser on an Honor Magic V5 phone and a MacBook Air M2
([0007](decisions/0007-the-owner-plays-by-browser-streaming.md)). Everything is built by Claude Code agents on
AWS for under $100 a month of infrastructure ([0008](decisions/0008-infrastructure-aws-london-under-100-a-month.md)).
The owner's own words are in [owner-brief.md](owner-brief.md). Every detail from the founding conversation is
traced to where it is handled in [ACCOUNTING.md](ACCOUNTING.md).

## 2. The four rules of this plan

1. **De-risk first** ([0023](decisions/0023-five-parts-de-risk-first.md)). Prove each class of work on a real,
   fully realised sample before scaling it. Order the work by what is still uncertain, not by system. The
   joins between systems and the feel of combat are tested in Part 1, before the world and the systems are
   built at scale.
2. **Reuse first, in route order** ([0010](decisions/0010-reuse-first-and-the-running-game-is-the-oracle.md)):
   data → existing mod (player-downloaded) → fork of an open mod → Papyrus → our SKSE code → our deep hook or
   HTML screen → ask the owner. That includes our own old code: the old project's engine-neutral rule packages
   run as they are if spike G10 says they can. We never make art beyond UI and minor Fal-made 2D elements,
   never ship others' files, and never copy decompiled code.
3. **The running game is the oracle; the studio is how we reach it.** Nothing is done until it passes in game
   with a check that can fail. Every in-game check and owner check starts in the studio, the real game that
   boots into any place ([0022](decisions/0022-the-studio-boots-into-any-place.md)), never through the
   new-game flow.
4. **Systems whole, content thin, what the player meets complete.** Build each piece to its final interface even
   when the slice uses only a corner of it (old 0134/0144).

## 3. Architecture

```
world/ (imported JSON: places, NPCs, quests, dialogue, hydrology, routes, stats tables, lore)  ── 0.1 import
   │  tools/argonia_world  (Python: validate, plan, convert units, flatten dialogue, plan water, plan placement,
   │                        generate directions, emit intermediate JSON)
   ▼
build/intermediate/*.json ──► tools/ArgoniaGen (C# .NET 8 + Mutagen: write records) ──► plugin/ (Spriggit YAML,
   committed)  ──► out/Argonia.esm + ArgoniaUI/Argonia - Main.bsa (our own files only)
skse/  (CMake, CommonLibSSE-NG, built from Linux)
   core/      pure C++ logic, no Skyrim types, unit-tested natively on Linux
   ArgoniaCore    all new state and the co-save families; calls the rules (stats, vastei, topics, conditions,
                  disposition, Owing, directions, journal); the menu router; PrismaUI bindings
rules/     the rules host chosen by spike G10: the old project's TypeScript rule packages bundled for an
           embedded engine, or their C++ port in skse/core/ (combat is always new C++)
   ArgoniaCombat  DS1 timing windows, i-frames, parry/riposte, backstab, poise, hit zones, stamina table,
                  boss phases; consumes Precision/TDM/OAR/TK Dodge APIs
   ArgoniaBoats   helm sailing (Wind Waker model), boat ownership/moorings/recovery
   ArgoniaBridge  DEV ONLY: localhost API for agents (scene, teleport, time, weather, input, activate, read, nav,
                  events, still, booth, frametime)
   ArgoniaStudio  DEV ONLY: the studio boot and the owner's panel (decision 0022)
papyrus/   our scripts (quest fragments generated + hand-written systems glue)
ui/        our own original UI as PrismaUI views (React/TypeScript), ported from the old repo's design system
           (decision 0017): HUD and every major screen; a mock harness runs them in headless Chrome
data/      golden combat table, dependency manifest (pinned mods), immersion inventory, sourcing register,
           FormID allocator, parity tables
installer/ modlist manifest + install/verify scripts; later a Wabbajack/Jackify list
infra/     build VM and GPU box scripts, Selkies, idle-stop, budgets, Steam/Proton setup
tests/     scenes/ (studio scenes), journeys/ (eyeless scripts for both runners); Python/C++/TS unit tests
tooling/   guards (no_assets, shell, job), brief template, session tokens, owner inbox
spikes/    0.2 spike code (throwaway unless a spike adopts it)
private/   gitignored: decompiles, dumps, Morrowind/DS reference text, drafts ($ARGONIA_PRIVATE)
```

Top-level directories: `world/ tools/ plugin/ skse/ rules/ papyrus/ ui/ data/ installer/ infra/ tests/ tooling/
spikes/ docs/` plus gitignored `out/ build/ private/`.

**Derived files** (FaceGen, LOD, behaviours, animation timing, menu patches) are made at runtime or by the
installer on the player's machine, never shipped ([0014](decisions/0014-derived-files-are-made-on-the-players-machine.md)).

**The Creation Kit** is installed and used only as a scripted tool (Papyrus compiler, load checks, navmesh,
FaceGen, flowmaps); records are written by code ([0018](decisions/0018-the-creation-kit-is-a-tool-not-the-workflow.md)).

**Machines.**
- **The build VM** (`argonia-build`, x86, no GPU) runs Claude Code, the generators and the compilers (Wine for the
  Windows-only ones), and the L1–L3 checks, including the core runner.
- **The GPU box** (`argonia-play`, started on demand) runs Skyrim under Proton with the pinned stack, the studio,
  ArgoniaBridge and Selkies for the owner, and the L4–L6 checks, including the game runner.

**Loops and the ladder** ([loops.md](loops.md), [0021](decisions/0021-fast-focused-loops-and-the-ladder.md)):
- fast focused loops with eyes;
- one lane tests a feature subset and its joins to what is already built;
- each block at the cheapest level that reliably proves it, composed once.

The levels:
- **L1** data;
- **L2** logic and the core runner (our systems' joins, no game);
- **L3** off-game stills (the UI harness);
- **L4** in game from a studio scene (state, timestamps, fixed-vantage stills);
- **L5** a short clip, only with a stated reason;
- **L6** the owner plays.

**Journeys are eyeless:** one script, played by the core runner and by the game runner through the bridge. They
use no screenshots, and no agent pilots the game by looking.

## 4. Every system, where it lives, and where it is built

Route numbers follow 0010:
1. data;
2. existing mod;
3. open-mod fork;
4. Papyrus;
5. our SKSE;
6. deep hook or HTML screen.

"Deps" are player-downloaded mods (pinned in 0.3). Source designs are in the old repo (`76` =
`docs/design/world/76-stats-progression.md`; numbers like `0152` are old decision records). The first-rung
column is Part 1's thread; "whole" is the chunk that completes it.

| System | Design source | Route | Deps / references | Our component | First rung → whole |
|---|---|---|---|---|---|
| Worldspace terrain (126×126 cells) + apron | old heightfield, 0067 apron | 1 | — | tools + ArgoniaGen | 0.2 G4 → 2.W1 |
| Rivers, lakes, waterfalls, sea | hydrology graph, 0064 waterfalls vanilla kit | 1 (+5 if needed) | vanilla water records/meshes | water planner | 0.2 G7 → 2.W2 |
| Navmesh | the world's own collision (0026 §3) | 1 (+CK check and fallback) | tes4skyrim's navmesh method | navmesh job | 0.2 G4 → 2.W4 |
| LOD, distant terrain, the map image | — | 1 | xLODGen, DynDOLOD (tools, Wine) | lod job | 2.W4 |
| Regions, weather, climate, sky | climate/weather-states, star catalogue | 1 | — | ArgoniaGen | 2.W3 |
| Roads, routes, the route graph | routes/*.json | 1 | — | route generator | 2.W3 |
| Places, interiors, doors | blueprints, 0114 interior manifest | 1 | BM&V, Xanmeer, KotM, others; **Tropical Skyrim SSE** for any base-Skyrim asset | piece resolver, `world-builder`, rebuilt natively (0026) | 0.2 G4 → 2.W5 → 4.2, 4.4 |
| Vegetation | flora rules, groundcover rules | 1 | BM&V, **Tropical Skyrim SSE (78044)** (0006 §8) | scatter converter | 2.W4 |
| The studio, scenes, the two runners | old 0149, 0155, 0156 | 5 + 6 | PrismaUI | ArgoniaBridge, ArgoniaStudio, `tools/run_journey.py` | 0.4 |
| Game state, co-save, message schema, menu router | old 2.1 seam | 5 | — | ArgoniaCore | 1.1 |
| Where the rules run | old `packages/*` (engine-neutral TS) | 5 | QuickJS-ng (if chosen) | `rules/` or `skse/core/` | 0.2 G10 → 1.1 |
| NPCs, whole-body templates, schedules, factions | the old people carried over (0026 §6), 0138 lamp clock, 0028 | 1 (+FaceGen for unique faces) | — | ArgoniaGen, AI packages | 0.2 G4 → 2.4 |
| Fixed danger D0–D5, roaming bands, respawn on rest | 0004, 0142, 76 §128 | 1 + 4 | — | encounter zones, spawner | 1.4 → 2.7 §j |
| Attributes, 27 skills, formulas | 76 §116–122 | 2 + 5 | Custom Skills Framework | ArgoniaCore stats | 1.3 (whole) |
| Races, birthsigns, classes, effect stack, perks | 76 §116–119, owner C4 | 1 + 5 | — | records, perk audit | 2.1 |
| Skill use, vastei, levels at rest, the sitting | 76 §120, 0147 | 3 + 5 + 6 | Sleep to Gain XP (pattern), Skill Uncapper | ArgoniaCore + sitting view | 1.5 → 2.8 |
| Death pile, wake at last rest, rest = only save | 76 §126, 0031, 0144 | 3 + 5 | Respawn – Soulslike (pattern) | ArgoniaCore | 1.5 → 2.8 |
| Dialogue: topics, hyperlinks, disposition, persuasion | 0139, 0143, 0145, dialogue data | 2 or 5 + 6 | tes4skyrim's MorrowindRuntime (OpenMW's engine in SKSE; audited in 0.1 §j), PrismaUI | topic store + dialogue view | 0.2 G5 → 1.3 → 2.5 |
| Quests as data, conditions | 0153, condition vocabulary | 1 + 4 + 5 | — | quest generator + evaluator | 2.12 → 4.3 |
| Writing quests, dialogue and text (one source of truth, generated briefs; [0024](decisions/0024-content-is-written-from-one-source-of-truth.md)) | old quest design, culture sheets | tool | — | skills `quest-write`, `quest-review`, `dialogue-write`; agents `quest-reviewer`, `dialogue-writer`, `corpus-find` | 0.1 §b, §i → 1.3 → 2.5, 2.12 → 3.3 → 4.2, 4.3 |
| Investigation support and the detectives' faction ([0025](decisions/0025-a-detectives-faction.md)) | condition vocabulary, 40-factions, lore extrapolation | 1 + 4 + 5 | — | evaluator predicates, journal clues, faction record, line record | 0.1 §i → 2.4, 2.5, 2.12 → 4.1 → 4.2, 4.3 |
| Journal, directions, no markers | 0137 | 2 + 5 + 6 | Wayfinder (pattern), No Google Maps | directions generator + journal view | 2.12 |
| World map, local map | old map styles | 2 + 6 | Flat World Map Framework | map views | 2.12 |
| Our own UI and HUD, Pelagiad, the UI map, transitions | old `packages/ui`, 0017 | 6 (port) | PrismaUI; TrueHUD/Infinity UI only to save engineering | ported views, font library | 1.2 → 2.2 → 3.1 |
| Weapon classes (incl. crossbows/thrown, 0016), armour slots, condition | 76 §118, 0040 | 1 + 2 + 5 | spear/throwing mods, animation sets | keywords, slot data, rating hook | 1.3 → 2.3 |
| Economy, barter, training, services, travel | 0141, 76 §124 | 1 + 4 (+5) | — | data, price hook | 2.6 |
| Magic | 0146, 0148, 76 §123 | 1 + 4 + 5 | Skyrim magic | magic rules | 2.9 |
| Crafting | 0150, 76 §124 | 1 + 4 | Skyrim crafting | recipes, stations | 2.10 |
| Stealth, crime, Owing, locks, pickpocket | 0151, 0092 | 1 + 4 + 5 | Skyrim detection | Owing ledger, lock threshold | 2.11 |
| **Combat: DS1's whole system** | **DSR measured** (0004, 0019); nothing from the old combat | 5 | Precision, BFCO, TK Dodge, TDM, OAR as I/O only | ArgoniaCombat: core + adapter | 0.2 G6, G9 → 1.4 → 2.7 |
| Wiring DS1 to our stats | 76 sheet + DSR | 5 | — | the wiring spec | 1.4 draft → 2.7 §a |
| Movesets | chosen for DS1 fidelity (0019 §4) | 2 (+5) | permitted Skyrim movesets, AMR, Payload Interpreter, XPMSSE | runtime timing control (0014 §2) | 0.2 G9 → 1.4 → 2.7 §e |
| Enemy AI, bosses | DSR AI shape, 0142 | 2 + 5 | SCAR (MIT), CPR, UND, Wait Your Turn | AI config; boss phases | 1.4 → 2.7 → 4.3 |
| Ranged (shoulder aim, recoverable arrows), thrown | 76 §121.1 | 1 + 2 | Skyrim archery, TDM aim, Throwable Weapons SKSE | tuning | 2.7 §i |
| Climbing, ladders | 0152 BotW | 2 (+3) | FreeClimb (GPL), SkyParkour, EVG Animated Traversal | rule tuning | 1.6 → 2.13 |
| Swimming, diving, breath | 76 §122 | 1 + 2 | Underwater NG | breath formula | 1.6 → 2.13 |
| Boats: sail, own, moor, recover | 0158, 0159 | 3 + 5 | Sailable Ship (modify with credit), Sailboats (pattern), Rowboats (CC BY-SA) | ArgoniaBoats | 1.6 → 2.15 |
| Marsh specials: hazards, harvests, effect arrows, materials | 0157, old registries | 1 + 4 + 5 | — | data + ArgoniaCore | 2.14 |
| Ragdolls (nice to have) | — | 2 | XP32 True Ragdoll, Precision impulses | — | 2.7 §i |
| Graphics: lighting, fog, volumetrics | owner | 2 | Community Shaders, weather mods restyled | presets | 0.3 → 2.W3 → 4.6 |
| Music, ambience, UI sound | owner | 1 + Fal/CC | — | music records | 2.16 |
| Vanilla quarantine | 0012 | 1 + 4 | Fuz Ro D-oh (silent lines) | start quest, overrides | 0.5 → 2.17 → 3.3 |
| Immersion inventory and gate | 0006 | tool | — | inventory generator | 0.5 → gate from 2.17 → 4.1 at scale |
| Main menu, loading, settings, controls | 0017 | 6 | Infinity UI if needed | views, own SWF if any | 3.1 |
| Character creation, the opening | 76, 0026 | 5 + 6 | RaceMenu only if needed | chargen view, opening quest | 3.2, 3.3 |
| Install, pin, distribute | 0002, 0003 | — | SKSE, Address Library, Pandora, PrismaUI | installer, modlist | 0.3 → 3.4 → 4.6 |

## 5. The parts

The schedule is [phases/README.md](phases/README.md); this table is its summary. The estimates are calendar
weeks on the 5x plan, with the owner answering check-ins within a day or two. They are guesses: universal-modder's
evidence is 4 days to 2 weeks per mechanic with a human checking builds. The planner re-estimates from measured
cycle times at 0.2 (G8), at Part 1's close, at Part 2's close and at 4.1.

| Part | What | Ends when the owner can say | Owner involvement | Est. |
|---|---|---|---|---|
| [0 Foundation](phases/0-foundation/README.md) | first: can vanilla Skyrim be played through the stream on the phone and Mac, with touch and a GameSir pad (G0); then repo, toolchain, import; spikes G1–G10; pinned stack and installer; the bridge, **the studio** and the two runners; the record pipeline | "I dropped into the studio on my phone and teleported around" | infra steps, Steam login (O-7), stream test, O-1–O-3, O-5, O-6, O-14, O-17 | 6–10 wk |
| [1 The core loop](phases/1-core-loop/README.md) | one thin thread through the host-risky systems at Claywater Station: talk, carry, fight (DS1), grow, die, rest, save, climb, swim, sail | "this is the game I want; it is worth building" (host go/no-go) | the verdict packet; O-4, O-9, O-11, O-16 | 5–8 wk |
| [2 The slice](phases/2-slice/README.md) | world track: the whole worldspace and the slice places; systems track: every system whole | "I played the slice in the studio; every system is real; the world is leg-work" | wave and world walks, a packet per few systems, the playthrough, O-8 | 5–8 months |
| [3 The game shell](phases/3-shell/README.md) | main menu, settings, controls, character creation, the opening, install paths, first playable | "I started a new game and reached the open world; a stranger installed it" | the opening (hands-on), O-10, O-13, O-20 | 5–8 wk |
| [4 Build out sideways](phases/4-buildout/README.md) | before scale, region packets, narrative lines, interiors, systems depth, final look and release | "the whole province is populated, every quest completes, and it is released" | cities (hands-on), a walk per region, O-2, O-18 | many months (20x) |

**The cross-cutting tracks**, run by the planner in every part:
- **T-IMM, immersion:** every new element enters the inventory with a verdict (0006). The gate binds on
  reachable rows from 2.17.
- **T-COST, cost:** month-to-date AWS spend and Claude usage in every owner check-in; stop the machines; the
  stop-and-ask rule and per-part budgets in decision 0008.
- **T-LEGAL, sourcing:** every dependency and asset has a sourcing-register row before it is used.
- **T-OWN, owner check-ins:** plain English, one check per bullet, studio scenes named, how to reply.
- **T-DOCS, docs:** the repo holds the current state and git the history; briefs are rewritten just in time
  (0023 §7).
- **T-WRITE, writing:** every quest, line of dialogue, journal entry and book is written through the writing
  skills in decision 0024's order; no text is written outside it.

## 6. Gates

A part closes only when:
- its exit passes (each part README);
- its PROGRESS rows are `done` with evidence;
- its risks are re-assessed;
- the next part's Starting state is written.

A failed gate is never waved through. The planner diagnoses, tries the brief's listed fallbacks, and only then
brings the owner a re-plan.

The three go/no-go moments:
- **0.0's gate G0**, before anything else is built: if the stream or the controls are not playable after the
  listed fallbacks, the owner re-plans (a local PC or Steam Deck, a native engine, a different combat shape).
- **0.2's gates G1–G10.** If G1 or G4 fails, decision 0001's fallback applies.
- **1.7's verdict.** A "no" on combat or the host triggers decision 0001's re-plan, while switching is still cheap.

## 7. What is deliberately not in this plan

- **Native phone or browser builds** (Skyrim is PC-only; 0007). A future native path would be Mudcrab or
  OpenMW ESM4 maturing (S4), or a Steam Deck/Windows PC.
- **Voice acting** (unvoiced text dialogue, old 0139/0143; O-11).
- **Mounts, fire spreading, tide gating, the river-pirate system, drifting settlements, survival needs,
  bleedout** (cut in the old project, 0039/0042) and **boats chasing boats** (cut in 0026).
- **The old three.js renderer, streaming, LOD, light-field, kit-compression, Pages deploy and phone-frame
  work** (three.js-specific; see [inherited-rulings.md](inherited-rulings.md)). The old rule packages are
  not in this list: spike G10 decides whether they run here as they are.
- **Multiplayer, monetisation, crowdfunding** (EULAs and the owner's "free" rule).
- **Any FromSoftware asset or moveset** (0004) and **any decompiled code** (0003).
- **Sea of Thieves, BotW, Wind Waker binaries**: studied only from talks and public docs (anti-cheat,
  console IP).

## 8. Lessons carried, and the gotchas of this host

From the old project:
- **Build the game, not the tools.** The old 2.10 spent most of its sessions on a filming rig. Here, journeys
  read state and never pixels, a still is the default eye, and a clip needs a written reason (0021).
- **Checks start from a known state in seconds.** The studio applies a scene instead of replaying the game.
- **Find everything, fix once.** One survey, one diagnosis, one batch, re-measure (loops.md rule 7).
- **The owner plays; the owner never does QA.**

From Skyrim modding, each owned by a rule or a chunk:
- **Script lag and save bloat** come from Papyrus: logic lives in SKSE, Papyrus only for fragments (1.1).
- **Saves rot across builds:** the co-save is versioned with migrations from day one (1.1). The studio always
  starts from a fresh base save (0.4). The owner's long-lived save starts only in Part 3.
- **The mod stack is the fragile part:** one pinned runtime, pinned file hashes, a conflict list, re-test after
  each addition (0.3). A 60-minute soak closes Part 1 (1.7).
- **Never restart the game per check:** keep it running and apply scenes (≤ 20 s each, 0.4).
- **Steam's offline mode needs an online login every few weeks:** checked at every box start (0.2 S0).
- **Stream latency is measured, not guessed,** and written beside every feel verdict. DS1 numbers are never
  retuned to suit the stream (0.2 G2).
- **Navmesh is the classic world-building sink:** survey every failure first, fix in one batch, keep the CK as a
  scripted fallback (2.W4).
- **Single-author dependencies** (PrismaUI, FreeClimb) are pinned and have a written fallback.
