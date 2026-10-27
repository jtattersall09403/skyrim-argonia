# The plan: Elder Souls: Argonia on Skyrim SE

Written 2026-10-27 for the Claude Code planner that will build this, from a long founding conversation with
the owner and twelve research reports. Read this file in full at the start of every planning session, then
[PROGRESS.md](PROGRESS.md), then the current phase file.

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

## 2. The three rules of this plan

1. **Reuse first, in route order** ([0010](decisions/0010-reuse-first-and-the-running-game-is-the-oracle.md)):
   data → existing mod (player-downloaded) → fork of an open mod → Papyrus → our SKSE code → our deep hook or
   HTML screen → ask the owner. We never make art beyond UI and minor Fal-made 2D elements, never ship others'
   files, never copy decompiled code.
2. **The running game is the oracle.** Nothing is done until it passes in game on the GPU box with a check
   that can fail, and the owner has seen it in a check-in where the phase says so.
3. **Every system joins what later phases own.** Build each piece to the final interface even when the slice
   only needs a corner of it (the old project's "systems whole, content thin" rule, old 0134/0144).

## 3. Architecture

```
world/ (imported JSON: places, NPCs, quests, dialogue, hydrology, routes, stats tables, lore)  ── P0 import
   │  tools/argonia_world  (Python: validate, plan, convert units, flatten dialogue, plan water, plan placement,
   │                        generate directions, emit intermediate JSON)
   ▼
build/intermediate/*.json ──► tools/ArgoniaGen (C# .NET 8 + Mutagen: write records) ──► plugin/ (Spriggit YAML,
   committed)  ──► out/Argonia.esm + ArgoniaUI/Argonia - Main.bsa (our own files only)
skse/  (CMake, CommonLibSSE-NG, built from Linux)
   core/      pure C++ logic, no Skyrim types, unit-tested natively on Linux
   ArgoniaCore    stats, skills, vastei, sitting, death pile, topic store, condition evaluator, disposition,
                  persuasion, Owing ledger, schedules glue, directions, journal log, PrismaUI bindings
   ArgoniaCombat  DS1 timing windows, i-frames, parry/riposte, backstab, poise, hit zones, stamina table,
                  boss phases; consumes Precision/TDM/OAR/TK Dodge APIs
   ArgoniaBoats   helm sailing (Wind Waker model), boat ownership/moorings/recovery
   ArgoniaBridge  DEV ONLY: localhost HTTP/MCP for agents (teleport, console, state, screenshots, input queue)
papyrus/   our scripts (quest fragments generated + hand-written systems glue)
ui/        our own original UI as PrismaUI views (React/TypeScript), ported from the old repo's design system
           (decision 0017): HUD and every major screen; a mock harness runs them in headless Chrome
data/      golden combat table, dependency manifest (pinned mods), immersion inventory, sourcing register,
           FormID allocator, parity tables
installer/ modlist manifest + install/verify scripts; later a Wabbajack/Jackify list
infra/     build VM and GPU box scripts, Selkies, idle-stop, budgets, Steam/Proton setup
tests/     in-game scenarios (YAML) the bridge runs on the GPU box; Python/C++ unit tests
tooling/   guards (no_assets, shell, job), brief template, session tokens, owner inbox
spikes/    Phase 1 spike code (throwaway unless a spike adopts it)
private/   gitignored: decompiles, dumps, Morrowind/DS reference text, drafts ($ARGONIA_PRIVATE)
```

Top-level directories: `world/ tools/ plugin/ skse/ papyrus/ ui/ data/ installer/ infra/ tests/ tooling/ spikes/
docs/` plus gitignored `out/ build/ private/`.

**Derived files** (FaceGen, LOD, behaviours, animation timing, menu patches) are made at runtime or by the
installer on the player's machine, never shipped ([0014](decisions/0014-derived-files-are-made-on-the-players-machine.md)).

**The Creation Kit** is installed and used only as a scripted tool (Papyrus compiler, load checks, navmesh,
FaceGen, flowmaps); records are written by code ([0018](decisions/0018-the-creation-kit-is-a-tool-not-the-workflow.md)).

**Machines.** The build VM (`argonia-build`, x86, no GPU) runs Claude Code, generators, compilers (Wine for
the Windows-only ones) and levels L1–L3 tests. The GPU box (`argonia-play`, started on demand) runs Skyrim
under Proton with the pinned stack, ArgoniaBridge, Selkies for the owner, and levels L4–L6 tests.

**Testing levels** (cheapest sufficient level wins; compose once; detail in
[ways-of-working.md](ways-of-working.md)): L1 data and records; L2 unit (Python, native C++ core); L3 UI
harness (PrismaUI views in headless Chrome against mock JSON); L4 in-game scripted through the bridge; L5
recorded clip for a feel judgement, only with a stated reason; L6 the owner plays a packet via the stream.

## 4. Every system, where it lives, and which phase builds it

Route numbers follow 0010 (1 data, 2 existing mod, 3 open-mod fork, 4 Papyrus, 5 our SKSE, 6 deep
hook/HTML screen). "Deps" are player-downloaded mods (pinned in P2). Source designs are in the old repo
(`76` = `docs/world/76-stats-progression.md`; numbers like `0152` are old decision records).

| System | Design source | Route | Deps / references | Our component | Phase |
|---|---|---|---|---|---|
| Worldspace terrain (126×126 cells) + apron | old heightfield, 0067 apron | 1 | — | tools + ArgoniaGen | P3 |
| Rivers, lakes, waterfalls, sea | hydrology graph, 0064 waterfalls vanilla kit | 1 (+5 if needed) | vanilla water records/meshes | water planner | P3 |
| Navmesh | old Recast bakes | 1 (+CK fallback) | — | navmesh writer | P1 spike, P3 |
| LOD, distant terrain | — | 1 | xLODGen, DynDOLOD (tools, Wine) | lod job | P3 |
| Regions, weather, climate, sky | climate/weather-states, star catalogue | 1 | — | ArgoniaGen | P3 |
| Roads, routes, travel services | routes/*.json, 23 services | 1 + 4 | — | travel dialogue + Papyrus | P3, P4 |
| Places, interiors, doors | blueprints, 0114 interior manifest | 1 | BM&V, Xanmeer, KotM, others; **Tropical Skyrim SSE** for any base-Skyrim asset | placement converter | P3, P9 |
| Vegetation | flora rules, groundcover rules | 1 | BM&V, **Tropical Skyrim SSE (78044)** (base-asset layer, 0006 §8) | scatter converter | P3 |
| NPCs, faces, schedules | npcs.json, 0138 lamp clock | 1 (+FaceGen solution) | — | ArgoniaGen, AI packages | P1 spike, P3, P9 |
| Fixed danger D0–D5, roaming bands, respawn on rest | 0004, 0142, 76 §128 | 1 + 4 | — | encounter zones, spawner | P4 |
| Attributes, 27 skills, classes, races, birthsigns | 76 §116–119 | 2 + 5 | Custom Skills Framework | ArgoniaCore stats | P4 |
| Skill use, vastei, levels at rest, sitting (PrismaUI view) | 76 §120, 0147 | 3 + 5 + 6 | Sleep to Gain XP (pattern), Skill Uncapper | ArgoniaCore + sitting view | P4 |
| Death pile, wake at last rest, rest = only save | 76 §126, 0031, 0144 | 3 + 5 | Respawn – Soulslike (pattern, permissive) | ArgoniaCore | P4 |
| Perks | owner C4 | 1 | — | perk audit + records | P4 |
| Dialogue: topics, hyperlinks, disposition, persuasion | 0139, 0143, 0145, dialogue data | 5 + 6 | PrismaUI | ArgoniaCore topic store + dialogue view | P1 spike, P4 |
| Quests as data, conditions | 0153, condition vocabulary | 1 + 4 + 5 | — | quest generator + condition evaluator | P4, P9 |
| Journal, directions, no markers | 0137 | 2 + 5 + 6 | Wayfinder (pattern), No Google Maps | directions generator + journal view | P4 |
| World map, local map | old map styles | 2 + 6 | Flat World Map Framework | map art (UI) + local map view | P4 |
| Our own UI and HUD (every major screen, chargen, inventory with paperdoll), Pelagiad; UI map and transition loops; OpenMW window study | old `packages/ui` (React), 2.2 UI, palette | 6 (port) | PrismaUI; TrueHUD/Infinity UI only to save engineering | ported views (0017), our font library (0014 §7) | P2, P4, P8 |
| Weapon classes (incl. crossbows/thrown, 0016), armour slots, armour rating, condition | 76 §118, 0040 | 1 + 2 + 5 | spear/throwing mods, animation sets | keywords, slot data, rating hook | P4 |
| Economy, barter, training, services | 0141, 76 §124 | 1 + 4 (+5) | — | data, price hook | P4 |
| Magic (never fails, spellmaking, hands, dual cast) | 0146, 0148, 76 §123 | 1 + 4 + 5 | Skyrim magic | ArgoniaCore magic rules | P4 |
| Crafting (alchemy, smithing tiers, enchanting) | 0150, 76 §124 | 1 + 4 | Skyrim crafting | recipes, stations | P4 |
| Stealth, crime, Owing, locks, pickpocket | 0151, 0092 | 1 + 4 + 5 | Skyrim detection | Owing ledger, lock threshold | P4 |
| Factions, reputation, allegiance | 0028, 76 §125 | 1 + 4 | — | data + Papyrus | P4 |
| **Combat: DS1's whole system** (state machine, buffering and cancels, roll/backstep i-frames by burden, stamina, guard, parry/riposte, backstab, poise and stagger, hyper-armour, per-hitbox rates, lock-on) | **DSR measured** (0004, 0019); nothing from the old combat | 5 | Precision (hits), BFCO (attacks), TK Dodge (roll input), TDM (lock-on), OAR (clip choice) as I/O only | ArgoniaCombat: our core state machine + adapter | P5 |
| Wiring DS1 to our stats | 76 sheet + DSR | 5 | — | the wiring specification (P5-WP5.0) | P5 |
| Movesets | chosen for DS1 fidelity (0019 §4) | 2 (+5) | permitted Skyrim movesets, AMR, Payload Interpreter, XPMSSE | runtime timing control (0014 §2) | P1-G9, P5 |
| Enemy AI, bosses | DSR AI shape, 0142 | 2 + 5 | SCAR (MIT), CPR, UND, Wait Your Turn | AI config from DSR summaries; boss phases | P5 |
| Ranged (shoulder aim, recoverable arrows) | 76 §121.1 | 1 + 2 | Skyrim archery, TDM aim | tuning | P5 |
| Climbing | 0152 BotW | 2 (+3) | FreeClimb (GPL), SkyParkour | stamina/rule tuning | P6 |
| Ladders | 0152 | 2 | EVG Animated Traversal | marker placement | P6 |
| Swimming, diving, breath | 76 §122 | 1 + 2 | Underwater NG | breath formula | P6 |
| Boats: sail, own, moor, recover | 0158, 0159 | 3 + 5 | Sailable Ship (modify w/ credit), Sailboats (pattern), Rowboats (CC BY-SA) | ArgoniaBoats | P6 |
| Ragdolls (nice to have) | — | 2 | XP32 True Ragdoll, Precision impulses | — | P5 |
| Graphics: lighting, fog, volumetrics | owner | 2 | Community Shaders (+ its volumetric/fog features), weather mods restyled | presets | P2, P8 |
| Music, ambience, UI sound | owner | 1 + Fal/CC | — | music records | P8 |
| Vanilla quarantine | 0012 | 1 + 4 | Fuz Ro D-oh (silent lines) | start quest, overrides | P2, P8 |
| World registries: hazards, grave stakes, harvest, deeds, rumours, markers, physical materials | old registries | 1 + 4 + 5 | — | data + ArgoniaCore | P4-WP4.21, P5-WP5.9 |
| Immersion inventory and audit | 0006 | tool | — | inventory generator | P2 → P8 |
| Install, pin, distribute | 0002, 0003 | — | SKSE, Address Library, Pandora, PrismaUI | installer, modlist | P2, P10 |

## 5. Phases

Estimates are calendar weeks on the 5x plan with the owner answering check-ins within a day or two. They are
guesses: universal-modder's evidence is 4 days to 2 weeks per mechanic with a human checking builds, so they are
likely optimistic. **At P1's close the planner re-estimates every phase** from G8's measured cycle time × the
number of L4 checks each phase plans, and re-plans at every phase close after that.

| Phase | Goal | Depends on | Owner involvement | Est. |
|---|---|---|---|---|
| [P0](phases/P0-bootstrap.md) | Repo, ways of working, build VM toolchain, content import | — | infra steps, O-1, O-2 | 1–2 wk |
| [P1](phases/P1-spikes.md) | Nine go/no-go spikes (G1–G9) that decide whether the architecture holds | P0 | Steam login (O-7), stream test, O-3, O-6 | 2–4 wk |
| [P2](phases/P2-foundation.md) | Pinned dependency stack, installer, full bridge and test harness, generator pipeline, immersion inventory, permission requests | P1 | O-5 | 2–3 wk |
| [P3](phases/P3-world.md) | The Argonia worldspace: terrain, apron, water, navmesh, LOD, regions/weather, roads, vegetation, the already-built places | P2 | 1 walk packet | 3–5 wk |
| [P4](phases/P4-soul.md) | Morrowind's soul: stats, levelling, death, dialogue, quests, journal, map, UI/HUD, chargen, items, economy, magic, crafting, stealth, factions, danger | P2 (P3 for in-world checks) | 2–3 packets, O-4, O-9, O-11 | 6–9 wk |
| [P5](phases/P5-combat.md) | DS1 combat: measurement, golden table, ArgoniaCombat, AI, bosses | P2, P4-WP4.1 stats | 2 feel packets | 4–6 wk |
| [P6](phases/P6-traversal.md) | Climbing, ladders, swimming/diving, boats | P2, P3 water | 2 packets | 3–5 wk |
| [P7](phases/P7-slice.md) | Vertical slice: the opening region played end to end | P3–P6 | full playthrough, O-10 | 2–4 wk |
| [P8](phases/P8-immersion.md) | Immersion to 100%: inventory closed, music, quarantine, graphics presets | P7 (track runs from P2) | packets, O-8 | 3–5 wk |
| [P9](phases/P9-content.md) | Content buildout in region packets until the province is complete | P7, P8 | one walk per packet | months |
| [P10](phases/P10-release.md) | Installer, docs, Nexus release, owner's permanent setup | P9 (an early access release may follow P8) | O-13 | 2–3 wk |

P3, P4, P5 and P6 overlap after P2: the planner runs at most two build lanes at once on 5x (the GPU box runs
one game at a time) and orders work by the dependency column.

**Cross-cutting tracks**, run by the planner in every phase:
- **T-IMM** immersion: every new element enters the inventory with a verdict (0006).
- **T-COST** cost: month-to-date AWS spend and Claude usage in every owner check-in; stop machines; the
  stop-and-ask rule and per-phase budgets in decision 0008.
- **T-LEGAL** sourcing: every dependency and asset has a sourcing-register row before it is used.
- **T-OWN** owner check-ins: one packet per milestone, plain English, one check per bullet, how to reply.
- **T-DOCS** docs stay current: the repo holds the current state, git the history.

## 6. Phase gates

A phase closes only when its exit gate passes (listed in each phase file), its PROGRESS rows are green, its
risks are re-assessed, and the next phase's starting state is written. A gate failure is never waved through:
the planner diagnoses, tries the phase's listed fallbacks, and only then brings the owner a re-plan.

The architecture's single biggest uncertainties are front-loaded into P1: SKSE from Linux, Skyrim headless on
the GPU box, streaming latency, world generation without the Creation Kit (navmesh, faces), the HTML dialogue
window, DSR measurement, Pandora on Linux, and meeting DS1 timings without shipping edited animations (G9). If G1 or G4 fails, decision 0001's fallback applies.

## 7. What is deliberately not in this plan

- **Native phone or browser builds** (Skyrim is PC-only; 0007). A future native path would be Mudcrab or
  OpenMW ESM4 maturing (S4), or a Steam Deck/Windows PC.
- **Voice acting** (unvoiced text dialogue, old 0139/0143; O-11).
- **Mounts, fire spreading, tide gating, the river-pirate system, drifting settlements, survival needs,
  bleedout** (cut in the old project, 0039/0042) and **boats chasing boats** (cut in 0026).
- **The old three.js renderer, streaming, LOD, light-field, kit-compression, Pages deploy and phone-frame
  work** (three.js-specific; see [inherited-rulings.md](inherited-rulings.md)).
- **Multiplayer, monetisation, crowdfunding** (EULAs and the owner's "free" rule).
- **Any FromSoftware asset or moveset** (0004) and **any decompiled code** (0003).
- **Sea of Thieves, BotW, Wind Waker binaries**: studied only from talks and public docs (anti-cheat,
  console IP).
