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
- **Dark Souls 1 combat**, DS1 Remastered's whole system as the target, wired to Argonia's Morrowind-based
  stats: each behaviour either a souls-like mod, tuned, or our own build of DS1's system, as the combat map decides
  ([0019](decisions/0019-combat-maps-each-ds1-behaviour-to-a-tuned-mod-or-our-own-ds1-build.md),
  [0004](decisions/0004-ds1-remastered-is-the-combat-oracle.md));
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

1. **De-risk first, in the order of what the game is for** ([0023](decisions/0023-five-parts-de-risk-first.md),
   [0027](decisions/0027-build-in-the-order-of-the-usps.md)). Prove each class of work on a real, fully realised
   sample before scaling it. After the foundations every piece of content is written against (the pipeline, the
   sheet, the dialogue and quest models, the quarantine, the save contract, the seam), the order is the owner's
   ranking: the world and its places; quests, story and people; combat closer to DS1; the progression model; the
   UI. Part 1 is the first place, complete; the world track starts after 0.4 and never stops.
2. **Reuse first, in route order** ([0010](decisions/0010-reuse-first-and-the-running-game-is-the-oracle.md)):
   data → existing mod (player-downloaded) → fork of an open mod → Papyrus → our SKSE code → our deep hook or
   HTML screen → ask the owner. The old project is the guide to goals and the source of content, never of
   machinery: each goal is met with Skyrim's own systems and existing tools first, used better
   ([0026](decisions/0026-everything-is-built-natively-the-skyrim-way.md)). We never make art beyond UI and minor Fal-made 2D elements,
   never ship others' files, and never copy decompiled code.
3. **The running game is the oracle; a scene is how we reach it.** Nothing is done until it passes in game
   with a check that can fail. Every in-game check and owner check starts from a scene applied to the dev
   profile's base save ([0022](decisions/0022-the-studio-boots-into-any-place.md): SkyLink and the console are
   the hands; no panel of ours), never through the new-game flow. Existing tools before our own harness
   ([0029](decisions/0029-part-0-is-one-sequence-not-spikes.md)).
4. **Systems whole, content thin, what the player meets complete.** Build each piece to its final interface even
   when the slice uses only a corner of it (old 0134/0144).

## 3. Architecture

```
world/ schema.sql (the relational world, 3NF, keys; decision 0030) + db/<table>.jsonl (one row per line) ── 0.4 §0
       sources/ (the 0.1 import, read-only, shrinking as families migrate)
   │  tools/argonia_world  (Python: validate, plan, convert units, flatten dialogue, plan water, plan placement,
   │                        generate directions, emit intermediate JSON)
   ▼
build/intermediate/*.json ──► tools/ArgoniaGen (C# .NET 8 + Mutagen: write records) ──► plugin/ (Spriggit YAML,
   committed)  ──► out/Argonia.esm + ArgoniaUI/Argonia - Main.bsa (our own files only)
skse/  (CMake, CommonLibSSE-NG, built on the Windows game machine with MSVC, driven from the build VM)
   core/      pure C++ logic, no Skyrim types, unit-tested natively on Linux
   ArgoniaCore    all new state and the co-save families; calls the rules (stats, vastei, topics, conditions,
                  disposition, Owing, directions, journal); the menu router; PrismaUI bindings
skse/core/ the rules Skyrim's own systems cannot carry (1.1 §a's native map), pure C++, unit-tested;
           written fresh, never ported (decision 0026)
   ArgoniaCombat  the combat map's "build from DS1" rows (decision 0019): DS1's state machine, windows, poise,
                  i-frames by load and the like where a mod cannot carry them, over the mods' APIs
   ArgoniaBoats   helm sailing (Wind Waker model), boat ownership/moorings/recovery
   ArgoniaBridge  DEV ONLY: only what SkyLink AI lacks (input, frametime, nav, booth, our reads); SkyLink is the
                  bridge (0.3 §a, decision 0029)
papyrus/   our scripts (quest fragments generated + hand-written systems glue)
ui/        our own UI, one design system (`ui/DESIGN.md`), in the approach 1.2 §0 chose with the owner
           (decision 0017): HUD and every major screen; a mock harness runs them in headless Chrome
data/      golden combat table, dependency manifest (pinned mods), immersion inventory, sourcing register (each
           a table of the world database where it refers to world rows),
           FormID allocator, parity tables
installer/ modlist manifest + install/verify scripts; later a Wabbajack/Jackify list
infra/     build VM and Windows game machine scripts, the stream client page, idle-stop, budgets, Steam setup
tests/     scenes/ (console batch files), journeys/ (state-and-events scripts with stills); unit tests beside code
tooling/   guards (no_assets, shell, job), brief template, session tokens, owner inbox
private/   gitignored: decompiles, dumps, Morrowind/DS reference text, drafts ($ARGONIA_PRIVATE)
```

Top-level directories: `world/ tools/ plugin/ skse/ papyrus/ ui/ data/ installer/ infra/ tests/ tooling/
docs/` plus gitignored `out/ build/ private/`.

**Derived files** (FaceGen, LOD, behaviours, animation timing, menu patches) are made at runtime or by the
installer on the player's machine, never shipped ([0014](decisions/0014-derived-files-are-made-on-the-players-machine.md)).

**The Creation Kit** is installed and used only as a scripted tool (Papyrus compiler, load checks, navmesh,
FaceGen, flowmaps); records are written by code ([0018](decisions/0018-the-creation-kit-is-a-tool-not-the-workflow.md)).

**Machines.**
- **The build VM** (`argonia-build`, Linux, no GPU) runs Claude Code, the generators (Python, .NET with Mutagen
  and Spriggit) and the L1–L3 checks. Tools arrive at first use (decision 0027 §7).
- **The game machine** (`argonia-play`, a Windows spot GPU instance started on demand; owner ruling 2026-10-28)
  runs Skyrim natively with the pinned stack, every Windows-only tool (MSVC for our SKSE plugins, Pandora, the
  Creation Kit, xEdit, DynDOLOD), the dev profile with SkyLink and ArgoniaBridge, and the stream (Sunshine and Moonlight-Web behind the
  owner's sign-in gate; 0.0), and the L4–L6 checks, including the game runner. The build VM drives it over SSH.

**Loops and the ladder** ([loops.md](loops.md), [0021](decisions/0021-fast-focused-loops-and-the-ladder.md)):
- fast focused loops with eyes;
- one lane tests a feature subset and its joins to what is already built;
- each block at the cheapest level that reliably proves it, composed once.

The levels:
- **L1** data;
- **L2** logic (unit tests of our rules and tools, no game);
- **L3** off-game stills (the UI harness);
- **L4** in game from a scene (state, timestamps, fixed-vantage stills);
- **L5** a short clip, only with a stated reason;
- **L6** the owner plays.

**Journeys read state and keep stills:** one script, played in the game through the bridge; pass or fail from
state and events, a still per step as evidence; no agent pilots the game by looking (0021 §3).

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
| Worldspace terrain (126×126 cells) + apron | old heightfield, 0067 apron | 1 | — | tools + ArgoniaGen | 0.4 → 2.W1 |
| Rivers, lakes, waterfalls, sea | hydrology graph, 0064 waterfalls vanilla kit | 1 (+5 if needed) | vanilla water records/meshes | water planner | 2.W2 (its first step is the stepped-river proof) |
| Navmesh | the world's own collision (0026 §4) | 1 (+CK check and fallback) | DotRecast + Mutagen; tes4skyrim as the binary spec | navmesh job | 0.4 → 2.W4 |
| LOD, distant terrain, the map image | — | 1 | xLODGen, DynDOLOD (on the game machine) | lod job | 2.W4 |
| Regions, weather, climate, sky | climate/weather-states, star catalogue; 0028 | 1 | Tropical Skyrim's weathers; Community Shaders | ArgoniaGen (REGN, WTHR, CLMT) | 2.W3 |
| Roads, routes, the route graph | routes/*.json | 1 | — | route generator | 2.W3 |
| Places, interiors, doors | blueprints, 0114 interior manifest | 1 | BM&V, Xanmeer, KotM, others; **Tropical Skyrim SSE** for any base-Skyrim asset | piece resolver, `world-builder`, rebuilt natively (0026) | 0.4 → 2.W5 → 4.2, 4.4 |
| Vegetation | flora rules as region object lists (0028) | 1 | **Tropical Skyrim SSE (78044)** over the vanilla forms; the CK's region generator | region records; the generator job | 2.W3 → 2.W4 |
| The studio: scenes, the bridge, the journey runner | old 0149, 0155, 0156; 0022, 0029 | 2 (+5) | SkyLink AI (dev only), the console | `tools/bridge.py`, `ArgoniaBridge` for what SkyLink lacks, `tools/run_journey.py` | 0.3 |
| Game state, co-save, message schema, menu router | old 2.1 seam | 5 | — | ArgoniaCore | 1.1 |
| Where each rule lives | the goals list (old designs as goals, 0026) | 1 → 5 | Skyrim's native systems, tes4skyrim's runtimes, PLAN §4 mods | the native map, `skse/core/` for what is left | 1.1 §a |
| NPCs, whole-body templates, schedules, factions | the old people carried over (0026 §6), 0138 lamp clock, 0028 | 1 (+FaceGen for unique faces) | — | ArgoniaGen, AI packages | 0.4 → 2.4 |
| Fixed danger D0–D5, roaming bands, respawn on rest | 0004, 0142, 76 §128 | 1 + 4 | — | encounter zones, spawner | 1.6 (one zone) → 2.7 §j |
| Attributes, 27 skills, formulas | 76 §116–122 | 2 + 5 | Custom Skills Framework | ArgoniaCore stats | 1.3 (whole) |
| Races, birthsigns, classes, effect stack, perks | 76 §116–119, owner C4 | 1 + 5 | — | records, perk audit | 2.1 |
| Skill use, vastei, levels at rest, the sitting | 76 §120, 0147 | 3 + 5 + 6 | Sleep to Gain XP (pattern), Skill Uncapper | ArgoniaCore + sitting view | 1.5 → 2.8 |
| Death pile, wake at last rest, rest = only save | 76 §126, 0031, 0144 | 3 + 5 | Respawn – Soulslike (pattern) | ArgoniaCore | 1.5 → 2.8 |
| Dialogue: topics, hyperlinks, disposition, persuasion | 0139, 0143, 0145, dialogue data | 2 or 5 + 6 | tes4skyrim's MorrowindRuntime (OpenMW's engine in SKSE; audited in 0.1 §j), PrismaUI | topic store + dialogue view | 1.3 §b → 2.5 |
| Quests as data, conditions | 0153, condition vocabulary | 1 + 4 + 5 | — | quest generator + evaluator | 1.4 (one quest) → 2.12 → 4.3 |
| Writing quests, dialogue and text (one source of truth, generated briefs; [0024](decisions/0024-content-is-written-from-one-source-of-truth.md)) | old quest design, culture sheets | tool | — | skills `quest-write`, `quest-review`, `dialogue-write`; agents `quest-reviewer`, `dialogue-writer`, `corpus-find` | 0.1 §b, §i → 1.3 → 2.5, 2.12 → 3.3 → 4.2, 4.3 |
| Investigation support and the detectives' faction ([0025](decisions/0025-a-detectives-faction.md)) | condition vocabulary, 40-factions, lore extrapolation | 1 + 4 + 5 | — | evaluator predicates, journal clues, faction record, line record | 0.1 §i → 2.4, 2.5, 2.12 → 4.1 → 4.2, 4.3 |
| Journal, directions, no markers | 0137 | 2 + 5 + 6 | Wayfinder (pattern), No Google Maps | directions generator + journal view | 1.2, 1.4 (first rung) → 2.12 |
| World map, local map | old map styles | 2 + 6 | Flat World Map Framework | map views | 2.12 |
| Our own UI and HUD, Pelagiad, the UI map, transitions | 0017's four goals; old `packages/ui` as one candidate | 2 then 6 | chosen in 1.2 §0 with the owner (PrismaUI the working assumption; SkyUI-style Scaleform, MorrowindRuntime's menu, OpenMW layouts); stage one on a permissive paper skin (Dear Diary family) if its permissions allow | stage one: the font, the theme, the dialogue window, the journal; stage two: the design system, `ui/DESIGN.md`, the windows, the HUD, every view | 1.2 §0 → 1.2 (stage one) → 2.2 (stage two) → 3.1 |
| Weapon classes (incl. crossbows/thrown, 0016), armour slots, condition | 76 §118, 0040 | 1 + 2 + 5 | spear/throwing mods, animation sets | keywords, slot data, rating hook | 1.3 → 2.3 |
| Economy, barter, training, services, travel | 0141, 76 §124 | 1 + 4 (+5) | — | data, price hook | 2.6 |
| Magic | 0146, 0148, 76 §123 | 1 + 2 + 4 + 5 | Skyrim magic; Magic Expanded (133435) checked in 1.2 | magic rules | 2.9 |
| Crafting | 0150, 76 §124 | 1 + 4 | Skyrim crafting | recipes, stations | 2.10 |
| Stealth, crime, Owing, locks, pickpocket | 0151, 0092 | 1 + 4 + 5 | Skyrim detection | Owing ledger, lock threshold | 2.11 |
| **Combat: DS1's system, each behaviour a tuned mod or our build** | DSR measured (0004, 0019); nothing from the old combat | 1 + 2 + 5 | the 0.0 stack (SkySA, Precision, TDM, TrueHUD, TK Dodge RE with Dynamic Dodge, Elden Parry, Rim Parry and Execution, One Click Power Attack NG, Modern Stagger Lock, MaxsuBlockOverhaul), BFCO, SCAR, CPR | the combat map; tuned settings; small tweaks (single-press backstab); ArgoniaCombat for the built rows | 1.6 the tuned stack on the sheet → 2.7 §0 the map, then every row (2.7 §b and §e when the map needs them) |
| Wiring the mods to our stats | 76 sheet | 1 + 5 | game settings, perk entry points, mod settings | the wiring spec | 1.6 draft → 2.7 §a |
| Movesets | chosen for DS1 fidelity (0019 §6) | 2 (+5) | permitted Skyrim movesets, AMR, Payload Interpreter, XPMSSE | runtime timing control (0014 §2) | 2.7 §e |
| Enemy AI, bosses | DSR AI shape, 0142 | 2 + 5 | SCAR, CPR and Modern Stagger Lock (the 2026 SkyHorizon3 forks, GPL-3; the MIT originals are stale), UND, Wait Your Turn | AI config; boss phases | 2.7 → 4.3 |
| Ranged (shoulder aim, recoverable arrows), thrown | 76 §121.1 | 1 + 2 | Skyrim archery, TDM aim, Throwable Weapons SKSE | tuning | 2.7 §i |
| Climbing, ladders | 0152 BotW | 2 (+3) | FreeClimb (GPL), SkyParkour, EVG Animated Traversal | rule tuning | 0.2 (loads and runs) → 2.13 |
| Swimming, diving, breath | 76 §122 | 1 + 2 | Swimming Extensions (189821); Underwater NG if needed | breath formula | 0.2 → 2.13 |
| Boats: sail, own, moor, recover | 0158, 0159 | 3 + 5 | Sailable Ship (modify with credit), Sailboats (pattern), Rowboats (CC BY-SA) | ArgoniaBoats | 0.2 → 2.15 |
| Marsh specials: hazards, harvests, effect arrows, materials | 0157, old registries | 1 + 4 + 5 | — | data + ArgoniaCore | 2.14 |
| Ragdolls (nice to have) | — | 2 | XP32 True Ragdoll, Precision impulses | — | 2.7 §i |
| Graphics: lighting, fog, volumetrics | owner | 2 | Community Shaders, weather mods restyled | presets | 0.2 → 2.W3 → 4.6 |
| Music, ambience, UI sound | owner | 1 + Fal/CC | — | music records | 2.16 |
| Vanilla quarantine | 0012 | 1 + 4 | Fuz Ro D-oh (silent lines) | start quest, overrides | 0.4 §b → 2.17 → 3.3 |
| Immersion inventory and gate | 0006 | tool | — | inventory generator | 0.4 §c → gate from 2.17 → 4.1 at scale |
| Main menu, loading, settings, controls | 0017 | 6 | Infinity UI if needed | views, own SWF if any | 3.1 |
| Character creation, the opening | 76, 0026 | 5 + 6 | RaceMenu only if needed | chargen view, opening quest | 3.2, 3.3 |
| Install, pin, distribute | 0002, 0003 | — | SKSE, Address Library, Pandora, PrismaUI | installer, modlist | 0.2 (our own machine) → 3.4 (players) → 4.6 |

## 5. The parts

The schedule is [phases/README.md](phases/README.md); this table is its summary. The planner reads the measured cycle times (0.3's loop record) at each part's
close; nothing is estimated in advance (decision 0029 §6).

| Part | What | Ends when the owner can say | Owner involvement |
|---|---|---|---|
| [0 Foundation](phases/0-foundation/README.md) | first: can vanilla Skyrim be played through the stream (G0); then the repo, toolchain and import; our stack on the game machine; the agent's hands (SkyLink, our SKSE build, scenes, the journey runner, the timed loop); the pipeline, the quarantine, the inventory and the Claywater block walked in game | "I dropped into Claywater on my phone and walked around" | the play sessions, O-1, O-3, O-5, O-17 |
| [1 The first place](phases/1-core-loop/README.md) | Claywater Station complete: talk, carry, one quest through the journal, grow, die, rest, save, fight on the tuned stack; the world track (2.W1–2.W4) starts beside it after 0.4 | "this is the game I want; it is worth building" | the verdict packet; O-4, O-9, O-11, O-16 |
| [2 The slice](phases/2-slice/README.md) | world track: the whole worldspace and the slice places; systems track: every system whole, people, dialogue and quests first, then combat's map, progression, the UI's second stage | "I played the slice in the studio; every system is real; the world is leg-work" | wave and world walks, a packet per few systems, the playthrough, O-8 |
| [3 The game shell](phases/3-shell/README.md) | main menu, settings, controls, character creation, the opening, install paths, first playable | "I started a new game and reached the open world; a stranger installed it" | the opening (hands-on), O-10, O-13, O-20 |
| [4 Build out sideways](phases/4-buildout/README.md) | before scale, region packets, narrative lines, interiors, systems depth, final look and release | "the whole province is populated, every quest completes, and it is released" | cities (hands-on), a walk per region, O-2, O-18 |

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
- **0.3's bridge and build, and 0.4's block.** If our plugin cannot load on the pin, or the block cannot be
  built and walked after the listed fallbacks, the owner gets a re-plan on Skyrim (decision 0001 §3).
- **1.7's verdict.** A "no" on combat or the host triggers decision 0001's re-plan, while switching is still cheap.

## 7. What is deliberately not in this plan

- **Native phone or browser builds** (Skyrim is PC-only; 0007). A future native path would be Mudcrab or
  OpenMW ESM4 maturing (S4), or a Steam Deck/Windows PC.
- **Voice acting** (unvoiced text dialogue, old 0139/0143; O-11).
- **Mounts, fire spreading, tide gating, the river-pirate system, drifting settlements, survival needs,
  bleedout** (cut in the old project, 0039/0042) and **boats chasing boats** (cut in 0026).
- **The old three.js renderer, streaming, LOD, light-field, kit-compression, Pages deploy and phone-frame
  work** (three.js-specific; see [inherited-rulings.md](inherited-rulings.md)). The old rule packages too:
  they are goal evidence only (decision 0026).
- **Multiplayer, monetisation, crowdfunding** (EULAs and the owner's "free" rule).
- **Any FromSoftware asset or moveset** (0004) and **any decompiled code** (0003).
- **Sea of Thieves, BotW, Wind Waker binaries**: studied only from talks and public docs (anti-cheat,
  console IP).

## 8. Lessons carried, and the gotchas of this host

From the old project:
- **Build the game, not the tools.** The old 2.10 spent most of its sessions on a filming rig. Here, journeys
  read state, keep a still per step as evidence, and a clip needs a written reason (0021).
- **Checks start from a known state in seconds.** A scene (a console batch file on the base save) instead of
  replaying the game; SkyLink and the console are the hands, not a harness of ours (0029).
- **Find everything, fix once.** One survey, one diagnosis, one batch, re-measure (loops.md rule 7).
- **The owner plays; the owner never does QA.**
- **Tools and process cost more than they look.** The old project's 18,000 lines of hooks, watchers, review gates
  and reader panels were most of its token bill; the 0.0 session built a whole streaming setup in two days with
  three scripts. A tool or hook is added after the incident it would have prevented (0011 §2, 0027 §7–9).

From Skyrim modding, each owned by a rule or a chunk:
- **Script lag and save bloat** come from Papyrus: logic lives in SKSE, Papyrus only for fragments (1.1).
- **Saves rot across builds:** the co-save is versioned with migrations from day one (1.1). Every scene starts
  from a fresh base save (0.3). The owner's long-lived save starts only in Part 3.
- **The mod stack is the fragile part:** one pinned runtime, pinned file hashes, a conflict list, re-test after
  each addition (0.2). A 60-minute soak closes Part 1 (1.7).
- **Never restart the game per check:** keep it running and apply scenes (measured in 0.3).
- **Steam's offline mode needs an online login every few weeks:** checked at every box start (0.0).
- **Stream latency is measured, not guessed,** and written beside every feel verdict. DS1 numbers are never
  retuned to suit the stream (0.2 §d).
- **Navmesh is the classic world-building sink:** survey every failure first, fix in one batch, keep the CK as a
  scripted fallback (2.W4).
- **Single-author dependencies** (PrismaUI, FreeClimb) are pinned and have a written fallback.
