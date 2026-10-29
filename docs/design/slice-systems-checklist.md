<!-- imported unchanged from elder-souls-argonia docs/research/combat-and-systems/slice-systems-checklist.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Gameplay systems checklist for the final game (replan input, 2026-10-14)

Sources read: audit (`docs/research/combat-and-systems/game-buildout-systems-audit.md`, "audit"), cross-check ("xc"), decisions 0039 and 0042, buildout register (`docs/phases/buildout/README.md`, "reg", flagged stale by its own banner, 0074 §5), `docs/world/76-stats-progression.md` ("76" §116-129 + headings), `docs/world/72`, `75`, `00-core`, `docs/quests/README.md`, `quests/85`, `docs/PROGRESS.md`. UESP: WebFetch got 403, so I used the MediaWiki API link lists for Morrowind:Morrowind, :Services, :Stealth, :Magic, :Items and Skyrim:Skyrim, :Activities, :Services, :Items, :Stealth. The page lists match xc's ~125-page sweep; no new system turned up beyond the MISSING rows below.

## Reconciliation block
- Live docs on this topic: reg (docs/phases/buildout/README.md, deferred-systems table, which is the only per-system owner list), audit §2-3, xc §1-3, 0039 Rulings, 0042 §1-2. Rows under "Ruled" below cite these.
- Confirmed by this pass: the reg rows still cover almost every UESP system. Standing cuts hold: survival, bleedout, killmove, mounts, vampirism/lycanthropy, shouts, perks, level scaling, dice, pickpocket, crossbow/thrown, companions, VO, multiplayer.
- Stale or contradicted (verify before reusing):
  - reg says "eleven" standards; there are seventeen (reg banner).
  - reg and audit say renderer extraction is at Phase 14, but PROGRESS.md row 10b says "sandbox parity and renderer extraction" (0062 moved it to 10b).
  - Audit's training price conflict (76 §124 says 10x, economy.json 8x) is still "resolve at 10c".
  - 0039 S2 cut the survival layer, but 76 §117 still carries a `breath = 25 + 0.35*Athl` curve and the cross-check §4 torch rules; keep those as breath and light only.
- Single doc to edit: `docs/phases/buildout/README.md` (the reg). Rewrite it into the system-by-system slice map. Do not add a new file.
- Code reality, for slice sizing (PROGRESS.md and `ls packages/game-core/src`): built are interaction/arbiter, travel/travelServices, perception/detection+noise, hud/minimap, stats (character, checks, crafting, ladder), ai/enemyAi, interior doors/bundle, scheduling, CarriedLight, combat runtime in packages/character. Phases 9, 10b, 10c, 12, 13 are all `todo` or `in progress`.

Legend: Ruled = kept/cut by a named ruling. Planned = a reg row or phase owns it. MISSING = no doc owns it (grep of docs/world 70-76, 60, 57, quests 00/80, reg returned nothing). Slice: yes / nice / later.

## 1. Character and progression
| System | Final game needs | Status | Depends on | Slice |
|---|---|---|---|---|
| 7 attributes, 27 skills, derived stats, no-dice score/k-curve | Morrowind sheet, deterministic checks | Ruled, 76 §116-118; code `game-core/stats` exists; 10c ports data | stats data | yes |
| Use-based skill XP, worthiness, vastei currency, level sitting | Skills rise by use "in anger", vastei is the progress currency, levels at rest | Ruled, 76 §120; 10c ships math, no UI/runtime | save, rest | yes (cut-down: XP + level sitting) |
| Effect stack (StatEffect) | One object for racials, signs, disease, potions, spells, enchants, rites | Ruled, 76 §127; field enum open (audit §2E, reg "By 10c") | stats | yes |
| Races and powers[] | Morrowind-weight racials; once-per-day powers | Ruled 76 §127; powers semantics unstated (xc §4) | effect stack | nice (Argonian only) |
| Birthsigns | 13 signs, fixed at chargen | Slot ruled; contents deferred (76 §119.2, audit §2D); swappable stones cut (xc §2) | chargen | later |
| Class (5+5, specialization, favoured attrs) | Morrowind class | Ruled 76 §116 | chargen | yes (preset class) |
| Burden/encumbrance tiers (roll tier, overload) | 4 tiers by carried kg | Ruled 76 §122; 10c | inventory | yes |
| Training (trainers, price cap) | Gold for skill rank, cap at governing attr | Ruled 76 §124; price 10x vs 8x conflict open (audit §6) | economy, dialogue | nice |
| Skill books | One rank each, read in place | Ruled 76 §124, xc §4 | books UI | nice |
| Health/stamina/magicka pools, damage vs drain | Morrowind-derived pools | Ruled 76 §117, §127 | stats | yes |
| Difficulty knob | Two-sided damage multiplier | Ruled 76 §121.4, xc §4; 10c | settings | later |
| Hist communion powers | Once/day power at ~10 hero Hist | Ruled KEPT 0042 §1 | powers, Hist placement | later |
| Allegiance rites (corprus-style packages) | Faction reward stat trade-offs | Ruled 0028 / 76 §127 | factions, effect stack | later |
| Luck, perks, level scaling | none | CUT: 76 §118, 00-core criterion 2, audit §2J | n/a | n/a |

## 2. Combat
| System | Final game needs | Status | Depends on | Slice |
|---|---|---|---|---|
| Melee core (lock-on, roll, i-frames, parry/riposte, guard, backstab) | DS1-shaped 1v1 | BUILT in the sandbox (audit §2C); adoption in studio is 10b | PlayerMovementController | yes |
| Stamina, poise/stagger, equip-load tiers | DS1 spec | Ruled 76 §121.2-3 (0037); zero code until 10c | stats | yes (poise at least) |
| Moveset breadth per weapon class | Sourced clips for spear/blunt/axe/short blade/unarmed | Planned 10b (0042 §4); one family built | clip sourcing | nice (one more family) |
| Bows, arrows, recoverable projectiles | Ballistic bow, ammo slot, arrow recovery | BUILT (audit §2C); 75 §55 | inventory | yes |
| Combat verb completion (charged/running/plunging, shield bash, two-hand) | DS1 verbs | Planned, reg "Combat verb completion"; input reserved | movesets | later |
| Shield parry | ruling pending | polish backlog tag 10b (reg) | | later |
| Armour/damage formulas, condition/wear | AR shape, wear per hit | Ruled 76 §121.1, §121.6; no `condition` field in code | stats | nice |
| Weapon poisons and oils | Coat next hit | Ruled 76 §124, registered; owner 10c | alchemy, effect stack | later |
| Hand-to-hand fatigue knockout | Fatigue damage then collapse then finishable | Ruled YES 0039 S6; reg | stamina | later |
| Status buildup (bleed/poison meters) | DS1-style | Planned 10c effect stack + 13 content (audit §2C) | effect stack | later |
| Enemy AI: archetypes, groups, ranged, morale/flee, Fight/Flee/Alarm ints | Utility AI on baked nav | Planned: 10b port, 13 archetypes, reg "Enemy & boss AI depth"; 1 archetype today | nav, detection | yes (2-3 archetypes) |
| Boss encounter (Xal-Krona prototype) | Authored boss, plus non-combat stand-down | Planned, 0042 §5, reg | enemy AI | nice |
| Creature statblock class (3-skill) | Simplified creature schema | Ruled, xc §1, reg "By 10c" | actor schema | yes |
| Aquatic NPC combat/swim | NPCs swim and fight in water | Planned, 75 §57 | nav-swim | later |
| Respawn-on-rest classes | onRest / never / untilCleared | Ruled 0031, 76 §126 | save, rest | nice |
| Cut: killmove layer, projectile interception, bleedout, whips/crossbow/thrown | | CUT 0039 rulings, 76 §118 | | n/a |

## 3. Magic
| System | Final game needs | Status | Depends on | Slice |
|---|---|---|---|---|
| Casting verb (input, hold/fire-and-forget, cast time) | Real-time cast bound to a hand/slot | **Open**: audit §2E "casting verb unsettled"; reg pulls only the enum + interruption rule into 10c | input, magicka | yes |
| Cast interruption vs poise | Rule for hit during cast | Planned 10c deliverable (reg); Morrowind answer "attacking is hyperarmour" in xc §4 | poise | yes |
| Spell castability gate, tiers, damage bypass armour, Wil/4 resist | | Ruled 76 §123 | stats | yes |
| Spell-effect catalogue | Full Morrowind effect list | Planned (reg "Magic breadth"); data has 4 placeholder effects (audit §2E) | effect stack | yes (5-8 effects) |
| Elemental resist channels | fire/frost/shock separate? | **Open** (audit §2E) | effect stack | later |
| Traversal magic (levitate, water walk, Mark/Recall, telekinesis, Open, Detect, shrine Intervention) | All kept, race-neutral | Ruled KEEP ALL 0039 S1 | effect stack, locks, map | nice (levitate + water walk) |
| Spellmaking | 8 effects, fee formula | Ruled KEPT 76 §123 | spell merchants | later |
| Enchanting, soul gems, soul trap, recharge | Soul-size budgets; NPC souls untrappable | Ruled 76 §123, xc §1; **no item model for soul gems** (audit §2E) | items | later |
| Scrolls, spell acquisition (spell merchants, books) | Learn from vendors and tomes | Scrolls Ruled 76 §123; acquisition listed in reg "Magic breadth" | economy | nice |
| Summons | Stat blocks, cap, AI | **Open** (audit §2E; reg "summon AI") | AI | later |
| Bound weapons/armour (Morrowind Conjuration) | Conjured gear | **MISSING**: grep "bound item/conjure" empty in docs | summon, equipment | later |
| Atronach sign variant | No regen, absorption | Hook only (76 §123) | birthsigns | later |
| Cut: shouts, magicka fizzle dice | | CUT xc §2, 76 §123 | | n/a |

## 4. Stealth and crime
| System | Final game needs | Status | Depends on | Slice |
|---|---|---|---|---|
| Detection service (cones, light, noise, LoS) | One service for all NPC logic | RATIFIED 10b deliverable (reg); code exists `game-core/perception` | nav, light | yes |
| Sneak, sneak attack bands, sneak XP | Morrowind sneak | Ruled 76 §120.2, §121.5; 0151 | detection | yes |
| Search, alarm and return to post, hearing, per-observer state | Skyrim's rule | Ruled 0151 (2.10); distraction verbs beyond the arrow 4.5 | detection | yes |
| Lockpicking / Security / probes / trap disarm | Threshold open check, tool quality, wear | Ruled 76 §118; 2.10 wires the verb to the 2.2 lock screen; unpickable class with a spell key (0151) | doors, containers | yes |
| Locks, keys, Open magic | Keys always work | Ruled 76 §118; a key item record per lock (2.10) | containers | yes |
| Traps | Trap kinds as data, an effect from the 2.9 catalogue, probe threshold, resets | Ruled 0151 (2.10, whole system, one or two placed); step, tripwire and lever triggers and physical damage 0157 (2.9c) | locks, effect stack | yes |
| Hazard volumes, burning peat, shock into water | Stand in it and the effect lands; fire lights peat; shock spreads through water | Ruled 0157 (2.9c) | effect stack, magic, combat | yes (the Wamasu Shrine; slice places on peat ground) |
| Effect arrows | Crafted fire arrows; stacks enchanted by Morrowind's ammo rule | Ruled 0157 (2.9c) | crafting, enchanting, bow | yes |
| Hist hearing (touched, heard, sap-speaker), Hist sap and sap-poisoning | Rest bonus, bark reveals hidden places, risky sap | Ruled 0157 (2.11 records and the Greenspring Trial stand-in; 2.9c sap) | quests, discovery, effect stack | yes |
| Player scent, heart-mud | Masking lowers what scent-noticing creatures detect; mud slows | Ruled 0157 (2.9c) | detection, effect stack | yes |
| Crime as Owing ledger (per region), witnessed only; pay, serve or resist at a guard stop | Owing assessment, guards stop you | Ruled 76 §124, 0039, 0151 (2.10) | detection, factions | yes |
| Item ownership (optional owner, no stolen flag) and trespass zones with hours | | Ruled 0039, 0151 (2.10) | placement | yes |
| Reprisals / courier | Letters and hired enforcers | Ruled YES 0039; 4.5 | crime, time | later |
| Contraband, cursed offerings, attire signal, deed counters | Flags | Ruled adopted, xc §1; 4.5 | vocabulary | later |
| Pickpocketing | A visible chance and a seeded roll, the one gamble; weapons by weight class, worn armour never | Ruled 0151 (2.10) | detection | yes |
| Slavery (Morrowind) | | CUT: no slave market; slavery ended in 4E 201, and coerced labour is the Owing (debt-bound indentured work the Chainbreakers fight), [labour-and-bondage](../../world/sources/lore/topics/labour-and-bondage.md) | | n/a |

## 5. NPCs and dialogue
| System | Final game needs | Status | Depends on | Slice |
|---|---|---|---|---|
| Talk-to-service contract | Talk then menu (ferry, merchant, trainer) | Planned 16e (reg "Dialogue UI") | interaction | yes |
| Topic web, KnowledgeState, glossary, journal-feeding topics | Morrowind topic UI | Planned, reg "Dialogue/Quest engine" (Q0-Q2 gates) | vocabulary | yes (3-5 topics) |
| Disposition and persuasion (authored thresholds) | Morrowind persuasion without dice | Ruled 76 §125 | dialogue | nice |
| Speechcraft UI (persuade minigame replaced) | | Ruled threshold, UI not described (checks "publish what they want") | dialogue | later |
| Faction membership, ranks, reaction matrix, expulsion | | Ruled 76 §125, xc §1; reg "Factions runtime" | vocabulary | later |
| NPC daily routines (marks, patrols, 2-4 bands) | Morrowind-ceiling ambient life | Planned 72 §113, Phase 13; `game-core/scheduling` exists | nav | nice |
| Furniture/interaction markers, beds, stations used by NPCs | | Adopted xc §1 | placement | 2.4i: the player sleeps in a bed (an owned bed refuses) and sits on the seats people use |
| Staged scenes (2-6 speakers) | | Planned reg "Scene runtime" | marks | later |
| Followers/escorts | | CUT 0028; escort tiers D-conversions | | n/a |
| Marriage, adoption, pets | | CUT xc §2 | | n/a |
| Barks / ambient NPC chatter without VO | generic lines | Implied (xc audit "generic barks may use available audio"), no owner | audio, text | later |

## 6. Economy and items
| System | Final game needs | Status | Depends on | Slice |
|---|---|---|---|---|
| Inventory, equipment, weight UI | Morrowind-skinned inventory | BUILT (audit §2F); UI is "working draft" (reg HUD row) | | yes |
| Item generation (53/35/48) | Weapons/armour catalogue | BUILT; breadth is content, not a row | | yes |
| Barter (no haggle), finite purses, restock | Deterministic price, daily refresh | Ruled 76 §124; runtime reg "Economy runtime" | dialogue, time | yes |
| Loot placement (fixed, never levelled) | Provenance and absolute bands | Ruled 00-core criterion 9, 76 §128.2; 13 | placement | yes |
| Containers, respawn/safe-storage classes | Open, take, reset class | Adopted xc §1 (container respawn); container UI **not named in any row** | interaction | yes |
| Potions as healing, no estus | Instant, stackable | Ruled 76 §126 | alchemy | yes |
| Alchemy (apparatus, ingredients, visibility by skill) | Always succeeds | Ruled 76 §124; station reg row | stations | nice |
| Smithing, repair tools, tempering | Repair, temper, craft | Ruled 76 §124, xc §4 | stations | repair 2.4i3 (a station mends worn gear by hammer strokes: a repair hammer in the pack wears per stroke, 76 §124 `repairPerStroke` 6→22 by Smithing up to the item's max, 0.4 Smithing points a stroke; no hammer, a prompt; the paid service is 2.6's alternative); temper and craft 2.8 |
| Crafting stations and resource nodes | forge/grindstone/tan/cook/harvest | Adopted xc §1, reg | STATION sockets | 2.4i: forge, smelter, grindstone, workbench and tanning rack mend (with a hammer); a fish rack marks the trade; harvest 2.3 |
| Cooking / food | Skyrim cooking chain feeds food | Chain adopted xc §1; **food as consumable with effects: no row**; survival cut | | 2.4i: a cooking place turns raw food into its food record (items.json `cooksInto`); food effects later |
| Shops, services (repair, recharge, cure, guide, ferry, tolls, info) | Morrowind services | Ruled list 76 §124; reg | dialogue | nice |
| Shrine blessings, cure | one temp buff, priced by faith | Adopted xc §1 | effect stack | 2.4i placeholder: praying fills health and stamina; the spell 2.9 |
| Light sources (torch, lantern, magelight) | Finite, off-hand, quenched by water | Mechanics in xc §4; carried light BUILT (`CarriedLight.tsx`); design assigned to Phase 12 | dungeons | nice |
| Books / readable notes / lore books | read in place | Adopted xc §1,4; book UI not defined | text catalogue | nice |
| Keys, quest items, artifacts, donation sink | | Keys mentioned 76; quest items in vocabulary B3; donation adopted | | later |
| Disease and cure items | Staged regional disease | Adopted xc §1 | effect stack | later |
| Cut: survival gear, estus, haggle, fencing, Hearthfire | | CUT 0039 S2, 76 §126, xc §2 | | n/a |

## 7. Quests and journal
| System | Final game needs | Status | Depends on | Slice |
|---|---|---|---|---|
| Typed condition/action vocabulary | The only gate language | First cut AUTHORED: quests/85, standard 1 | | yes |
| Quest state machine, flag store, headless drivable | | Planned, reg "Quest engine" | vocabulary | yes |
| Journal UI | Morrowind journal entries | Planned (Q2 gate: exemplar quest + format) | quest engine | yes |
| No quest markers; diegetic pointers; grantable map markers | | Ruled 13 / reg "Map, markers" | map | nice |
| Evidence, custody, essential tier | | Planned reg | | later |
| Fail-forward, doom warning message, no invincibility | | Ruled 0030/0039 S6 | save | later |
| Ending availability (3 families) | | Planned | | later |
| Dream/vision harness | | Registered | | later |
| Radiant quests | | CUT xc §2 | | n/a |
| Narrative debugger, validators, headless sim | | Planned reg | | later |

## 8. World interaction
| System | Final game needs | Status | Depends on | Slice |
|---|---|---|---|---|
| Interaction arbiter (activate, pick up) | Prompt, priority | BUILT `game-core/interaction` | | yes |
| Load doors and swing doors, interior streaming | Typed doors, 0114 | Ruled 0114, reg; built `game-core/interior/doors`, swingDoors in 16k | | yes |
| Rest vs wait, beds, inns, rent, no camping in settlements | | Ruled 0039 S3, 76 §126 | save, time | yes |
| Death and wake at last rest, vastei pile | | Ruled 76 §126 | save | yes |
| Swim, dive, breath, Argonian water breathing | | Phase 9 (9a thin swim first), 76 §122 | | yes |
| Climbing | BotW-style; large surfaces climbable | Phase 9, 76 §122.1 | | yes |
| Boats (player craft only) | Sail/paddle | Phase 9 scope rule (0034); AI/cargo boats DEFERRED G3 (0042 §2) | water | nice |
| Fall damage, safe-fall | | Ruled 76 §118 | | nice |
| Fast travel: ferries, boat services, rootworm, urban water taxi; guides | Talk-pay-arrive on a service graph | Planned; `game-core/travel` exists; 16e/16g | dialogue, money | nice |
| Discoverable travel network / silt strider analogue | | 30 §fast-travel; rootworm ride only as talk-pay-arrive | | later |
| Harvest nodes (flora picking) | | Adopted xc §1 | | nice |
| Hist-tree interaction (drink sap) | | Ruled 0042 §1 | | later |
| Mounts, tide-gated doors, drifting settlements, fire spread | | CUT 0042 §2 | | n/a |
| Weather/time as gameplay (calendar, tides as flavour) | World clock, scale 30 | BUILT (phases 8) | | yes (exists) |
| Fishing | | Conditional on cheap clips (0039) | | later |
| Wait/sleep distinction and waiting UI | | Ruled 0039 S3 (verb split) | time | nice |
| Pause/menu time behaviour (game paused in inventory?) | Morrowind pauses in menus | **MISSING**: not stated anywhere in the docs read | UI | yes |

## 9. UI, HUD, menus
| System | Final game needs | Status | Depends on | Slice |
|---|---|---|---|---|
| HUD design system (tokens, components, one input model) | | Planned, 0042 §7, reg; owner says inventory is "OK for now" | | yes (first screens) |
| HUD core: bars, target, compass/minimap, prompts | | Partial (sandbox; `hud/minimap.ts`) | | yes |
| Character sheet, level-up, rest UI | | Planned 10c | stats | yes |
| Inventory/equipment, barter, container, dialogue, journal, map, spell menu, quick items | | Inventory built; rest Planned in separate rows; **spell menu/hotkeys and quick-item belt**: no row | | yes |
| Map (world + local, markers) | | Planned reg "Map" | | nice |
| Settings: input rebinding, audio, accessibility | | Planned reg "Menus, settings" | | later |
| Gamepad and touch | Phones are a budget target (CLAUDE.md); touch input exists in studio (audit §1) | Rebinding row only; **gamepad/touch UX in game not designed** | | nice |
| Subtitles/text for barks; localization | Out of scope, 'one explicit line owed' (audit §5) | undocumented | | later |
| Tooltips, tutorials, hints | | Tutorial-by-touch planned (vastei scene); no generic hint system | | later |
| Dev console / cheats / debug | Studio debug panels exist | Morrowind has console; not planned for the game | | later |

## 10. Persistence and shell
| System | Final game needs | Status | Depends on | Slice |
|---|---|---|---|---|
| Save/load (rest-save, hidden suspend-save, versioned, IndexedDB, slots) | | contract at 10c, system in reg "Save/load"; **audit's #2 load-bearing gap** | schemaVersion | yes |
| Manual/quick save | Browser game may want it | **MISSING**: only rest-save + suspend-save decided | save | later |
| Game shell: boot, loading screens, deploy | `apps/game` is a stub (audit §1, reg architecture debt) | Planned 14/G0; loading-screen design **MISSING** | renderer extraction | yes |
| Main menu, new game, continue | | Planned (reg menus) | save | yes |
| Chargen (diegetic class quiz, race, sign) + vastei tutorial | | Planned reg; template xc §1 | stats data | yes (can be a preset in the slice, one quiz stub nice) |
| Persistence of world state (flags, variants, ledgers, cleared dungeons) | | Reg "Save/load", "Local overlay" | stable IDs | yes |
| Streaming and interior transitions | | Phase 14 / `interior/doorTransition` built | | yes |
| Performance bands, quality settings | | Phase 14 / CLAUDE.md | | nice |

## 11. Audio and music
| System | Final game needs | Status | Depends on | Slice |
|---|---|---|---|---|
| Soundscape by region/clock/weather | | Planned 12b (57) | ecology | later |
| Combat/footstep/UI audio | combat audio is a stub (audit §2C) | Planned 12b; lane "Sound prep" open | | nice |
| Music/score | | Registered, nothing owned (reg "Music") | bus hooks | later |
| Voice | | CUT (text-led), barks maybe | | n/a |
| Tavern performers | | CUT 0039 | | n/a |

## 12. AI and ecology
| System | Final game needs | Status | Depends on | Slice |
|---|---|---|---|---|
| Baked nav (ground/swim/climb/boat) + validation | | Planned 10b/72 §114 | | yes |
| Creature territories, leashes, encounter templates | Fixed spawn points + classes | Planned 13; xc §1 | nav | nice |
| Fauna ecology, wild wamasu apex | | Ruled 0042 §2 | 13 | later |
| Disease-bearing variant creatures | | Adopted xc §1 | | later |
| AI state across interior portals | | audit §3 #16: implementation build-out | | nice |
| Hazards: rootworm, blight, fixed regional danger | Fixed danger field | Ruled 0004 / BUILT field | | yes |

## MISSING from the docs (no owner anywhere)
1. Pause/time behaviour while menus are open, and the wait UI.
2. Spell menu, quick-item belt and hotbar UX (the casting verb input itself is open: audit §2E).
3. Lockpick/probe/key *verbs and tools* (math and class exist only; no UI, no consumable tool rule, no key item class).
4. Container UI and the loot interaction flow (take all, take one).
5. Bound weapons and armour (Morrowind Conjuration).
6. Food as a consumable with effects (cooking chain adopted, survival cut, so food use is undefined).
7. Loading screens and boot flow design.
8. Manual save (rest-save only decided).
9. Gamepad/touch controls design for the game (rebinding only).
10. Slavery: no slave market; coerced labour is the Owing, by the lore ([labour-and-bondage](../../world/sources/lore/topics/labour-and-bondage.md)).
11. NPC barks without VO: noted, not owned.
12. Dev console/cheats: not ruled.

## Over-planned (plausibly unnecessary for a slice, or at all)
- Spellmaking, enchanting + soul gems + soul trap (the reg itself notes soul gems have no item model); a full effect catalogue; summons. Defer past the slice.
- Allegiance reward tracks, stronghold 3-layer compositor, artifact donation sink, deed counters, faction reaction matrix, shrine blessing priced by faith: large and all post-slice.
- Dream/vision harness, three-ending computation, narrative debugger plus LLM-critic: not slice material.
- Crime-as-Owing ledger with reprisals: bigger than Morrowind's bounty; a witnessed-theft-to-guard stub suffices for the slice.
- Weapon poisons and H2H finisher "pull-in" to 10c: adds scope to a phase already carrying poise, potions, profiles and archetype proving.
- Birthsign contents (13 sign packages), per-class crit table, tiered bed quality calibration.
- Festivals, pilgrimages, fishing: already deferred or conditional; keep deferred.

## Recommendations
- Treat the slice as one region touching one instance of each row marked "yes" above; for rows marked later, prove a contract only (e.g. Owing ledger with a single stub, enchant a placeholder).
- Decide the three open design calls the slice forces: casting verb and input, cast-vs-poise rule, pause behaviour in menus (evidence: audit §2E, reg "By 10c").
- Edit `docs/phases/buildout/README.md` to fold in the 12 MISSING rows and replace stale numbers (standards count 17, extraction at 10b per PROGRESS.md).
