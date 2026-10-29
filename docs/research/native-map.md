# The native map: where each goal lives in Skyrim (1.1 §a)

Dated 2026-10-29. Paper lane `1.1-sa-native-map`. For every goal in [the goals list](../design/goals.md), the
Skyrim mechanism that carries it, in the route order of [0010](../decisions/0010-reuse-first-and-the-running-game-is-the-oracle.md)
and in the spirit of [0026](../decisions/0026-everything-is-built-natively-the-skyrim-way.md): records and settings
first, then the tools and mods of the [reuse audit](2026-10-29/reuse-audit.md) (whose §1 is the 0.1 §j
MorrowindRuntime audit), then our own SKSE code for what is left. Read with
[1.1](../phases/1-core-loop/1.1-game-state-seam.md), [0005](../decisions/0005-the-morrowind-soul-contract.md),
[0012](../decisions/0012-vanilla-skyrim-is-quarantined.md) and
[0019](../decisions/0019-combat-maps-each-ds1-behaviour-to-a-tuned-mod-or-our-own-ds1-build.md).
Nothing here ports the old project's machinery or quotes decompiled code; it names engine mechanisms by their
public names (CommonLibSSE-NG headers, the CK wiki, UESP) and carries no offsets or Address Library ids.

## 0. How to read it

**Goal ids.** `Gss.n` = the n-th bullet under the ss-th `###` heading of `goals.md`, counted in file order
(`G14.1` is the first bullet under "Attributes, 27 skills, formulas"). The count script in the lane report
re-derives the ids from `goals.md` and checks this map has exactly one row per goal.

**Routes** (0010): 1 data (records, game settings), 2 existing mod as a dependency, 3 fork of an open mod,
4 our Papyrus, 5 our SKSE code (`skse/core` rules behind ArgoniaCore), 6 our deep hook or our own screen,
T our own build-time tool (Python or ArgoniaGen; not a runtime route, listed because some goals are only tools).
A row lists every route it uses, cheapest first.

**Fit.** *fully*; *loss* (with the stated loss); *none* (Skyrim, mods and our code cannot meet it: an owner call).

**Evidence tags.** `[CL file:line]` = read in CommonLibSSE-NG at commit `dec1be18` (release 15.2.0, 2026-10-29),
`https://github.com/alandtse/CommonLibSSE-NG/blob/dec1be18b1880c1f643afedc0d01db0118d648f9/include/RE/<file>`.
`[W:name]` = a web source listed in §7 (UESP and the CK wiki answer 403 to fetches from this host, so these were
read through search-result excerpts, which is weaker than a page read). `[A §n]` = the reuse audit's section.
**UNVERIFIED** = not read in any source; each one names the L4 stub (§5) or the chunk that settles it.

**Part 1 rows** (first rung in 1.1–1.6) name an L4 stub id `S..`; §5 states each stub as a check that can fail.
The other rows are mapped on paper and proved by the chunk named.

## 1. Owner calls ("none" rows) and losses the planner should raise

**No goal is "none" on present evidence.** Every goal has a mechanism that meets it fully or with a stated loss.
None of the losses below is hard to reverse, so none blocks a chunk; each is raised with its chunk's check-in, and
any that its L4 stub turns into "none" becomes an owner call at once.

| Goal | The loss | Raised in | Would become "none" if |
|---|---|---|---|
| G02.3 floods | flood stages are stepped (enable-parented water planes), not a continuous rise | 2.W2 | placed water planes cannot be toggled with working swim and submersion |
| G05.2 28-night moons | the climate's moon phase length is a whole number of days `[CL T/TESClimate.h:67]`; if a cycle is eight phases, 28 nights is not reachable (24 or 32 are) without our override | 2.W3 | an SKSE override of the phase cannot be found (UNVERIFIED) |
| G25.2 item condition | Skyrim has no item condition; ours is per inventory instance, and identical stacked items may share one value | 1.3 §c | instances cannot be told apart at all (S25b) |
| G27.3 spellmaking | spells made at run time are new forms that must be rebuilt from our co-save on every load | 2.9 | runtime-created spell forms cannot be equipped or cast |
| G29.1 detection | Skyrim's per-observer detection is tuned to approximate the Elusiveness formula, not to equal it | 2.11 | — (a hook is the fallback, route 6) |
| G36.1 underwater layer | diving and underwater play come from Swimming Extensions / Underwater NG; Skyrim's own swimming is surface-only | 0.2 → 2.13 | neither mod gives free diving on the pinned runtime |
| G37.1 Wind Waker sailing | no vehicle physics: the boat is a moved reference; wave and wake response is faked | 0.2 → 2.15 | — |

## 2. The patterns the rows reuse

- **P1 Carrier actor value.** Where Morrowind's arithmetic (a score over two values, a curve `k`) cannot be written
  as Skyrim conditions, ArgoniaCore computes the number in `skse/core` and writes it into a reserved actor value;
  a perk entry point applies it with *Multiply Actor Value Mult* or *Multiply 1 + Actor Value Mult*
  `[CL B/BGSEntryPointFunction.h:26-27]`. Reserved values come from `Variable01`–`Variable10`
  `[CL A/ActorValues.h:76-85]` and the obsolete ones the 1.3 §a audit clears (`Fame`, `Infamy`, `DEPRECATED05` and
  others, `[CL A/ActorValues.h:68, 170]`); the free count is **UNVERIFIED** (the audit settles it). Only the player
  needs live carriers (one per hand, not one per skill); NPC numbers are compiled (P5). Fallback when the budget
  runs out: generated stepped perk rows conditioned on `GetActorValue` bands (a quantisation loss).
- **P2 Condition mirror.** Predicates Skyrim has are Skyrim condition functions (`GetStage`, `GetStageDone`,
  `GetItemCount`, `GetFactionRank`, `GetIsRace`, `GetActorValue`: `[CL T/TESCondition.h:49, 86, 98-99, 109, 113]`).
  The rest are evaluated in `skse/core/conditions` and **mirrored** into one generated global per predicate
  instance a record references, read by `GetGlobalValue` `[CL T/TESCondition.h:114]` (or a quest-script
  property through `GetVMQuestVariable` `[CL T/TESCondition.h:763]`). Mirrors are player-scoped and update on the
  change event, so they can be a frame late. Adding new condition functions from SKSE is **UNVERIFIED** and not
  needed.
- **P3 Activation takeover.** A perk on the player with an *Activate* entry `[CL B/BGSEntryPoint.h:29]` whose
  choice carries *Run Immediately* and *Replace Default* `[CL B/BGSEntryPointFunctionDataActivateChoice.h:15-19]`
  replaces the vanilla activation of whatever its conditions select (Argonia speakers, camp spots and beds,
  locked doors and lids); its Papyrus fragment is one line calling one ArgoniaCore native. Route 1 + 4 (glue
  only). This is cheaper than the audit's guarded activate-slot swap `[A §1.2]`, which stays the fallback
  (route 6) if the fragment's latency shows (measured at S18a; **UNVERIFIED**).
- **P4 Vanilla progression off by data.** Each vanilla skill's AVSK `useMult`/`offsetMult` `[CL A/ActorValueInfo.h:115-124]`
  set to 0 stops vanilla skill gain; `fXPPerSkillRank` = 0 stops character XP, so the level-up menu never fires
  (`character XP = skill level × fXPPerSkillRank`, defaults `fXPLevelUpBase` 75 / `fXPLevelUpMult` 25 [W:leveling]).
  ArgoniaCore then owns every gain. Whether every vanilla gain path honours `useMult` = 0 is **UNVERIFIED**
  (S16a reads the vanilla skill XP `[CL P/PlayerCharacter.h:532-586]` after each use class).
- **P5 Compile with the core's own formulas.** NPCs, enemies, merchants, loot and traps get fixed numbers at build
  time. The ladder compiler links `skse/core` built natively on Linux (a small CLI), so the game's player rules and
  the compiled actors share one implementation and one table (G11.2). NPC values Skyrim stores natively go into the
  NPC record; the rest (carrier values, our attributes) go into one generated ability per actor.
- **P6 The menu router** (1.1 §d) owns every vanilla surface we suppress or replace: `StatsMenu`, `LevelUpMenu`,
  `JournalMenu`, `SleepWaitMenu`, `DialogueMenu` `[CL S/StatsMenu.h:27, L/LevelUpMenu.h:13, J/JournalMenu.h:19,
  S/SleepWaitMenu.h:13, D/DialogueMenu.h:16]`, seen through `MenuOpenCloseEvent`; menus carry an
  `kAllowSaving` flag `[CL I/IMenu.h:30]`.
- **P7 Canonical state in the co-save.** Our values live in ArgoniaCore's families; the actor values, globals and
  records above are mirrors written from them, never read back as truth.

## 3. The map

Columns: goal · mechanism, cheapest route first · routes · fit and why · proved by · Part 1 stub.

### 3.1 World and land

| Goal | Mechanism | Routes | Fit, why | Proved by | Stub |
|---|---|---|---|---|---|
| G01.1 | WRLD + LAND (heights, normals, LTEX paint) written by ArgoniaGen from the heightfield, the records the CK's heightmap import makes (0026 §3) | 1, T | fully; the 126×126-cell physics size is **UNVERIFIED** (tes4skyrim's `havok_world_size` is the re-check, [A §1.6]) | 0.4 → 2.W1 | — |
| G01.2 | the apron as LAND at 1:1 plus worldspace default water as the sea; far land through LOD | 1, T | fully | 2.W1, 2.W4 | — |
| G01.3 | terrain and water planned together by our build tools; Skyrim only receives the result | T | fully: a build-time goal | 2.W1, 2.W2 | — |
| G02.1 | WATR records, cell water height, placed water planes; body semantics stay rows in the world DB | 1 | loss: one water height per exterior cell, so stepped rivers need placed planes (2.W2's first step proves them) | 2.W2 | — |
| G02.2 | placed refs of the vanilla falls and rapids kit (Tropical Skyrim's textures) | 1 | fully: it is the goal's own wording | 2.W2 | — |
| G02.3 | flood stages as enable-parented water planes and dressing, switched by the season from ArgoniaCore's calendar rule | 1, 5 | loss: stepped stages, not a continuous rise; runtime change of a cell's water height is **UNVERIFIED** | 2.W2 | — |
| G03.1 | NAVM from our collision (DotRecast job, tes4skyrim as the binary spec [A §1.5]), each person's walk proved by a journey | 1, T | fully | 0.4 → 2.W4 | — |
| G03.2 | NAVM + Skyrim's AI packages (PACK); rich AI is not built | 1 | fully | 2.4, 2.W4 | — |
| G03.3 | Skyrim's own actor processing: unloaded actors advance their packages without pathing, loaded ones walk | 1 | fully; the exact low-process behaviour is **UNVERIFIED** (a still pair before and after a cell load in 2.4) | 2.4 | — |
| G04.1 | xLODGen, DynDOLOD, FaceGen and the map render run by the installer on the player's machine (0014) | 2, T | fully | 2.W4 → 3.4 | — |
| G04.2 | WTHR fog distances and colours from the climate fields, Community Shaders volumetrics | 1, 2 | fully | 2.W3 | — |
| G04.3 | object and terrain LOD of the apron | 1, T | fully | 2.W4 | — |
| G05.1 | WTHR and CLMT generated from the climate fields (sun, sky colours, fog, moons) | 1, T | loss: the star field is the sky's texture, not a catalogue; new star art is outside 0006 | 2.W3 | — |
| G05.2 | Skyrim's calendar (12 months, `GameYear`/`GameMonth`/`GameDay` globals `[CL C/Calendar.h:43-91]`) set to 4E 201; moons from CLMT phase length `[CL T/TESClimate.h:67]` | 1 (+5) | loss: see §1, 28 nights may need our override (**UNVERIFIED**) | 2.W3 | — |
| G05.3 | REGN weather lists per region, the province timeline forcing the current weather from a small ArgoniaCore rule | 1, 5 | fully if forcing holds; Skyrim's weather choice is otherwise a per-region chance; the forcing call is **UNVERIFIED** | 2.W3 | — |
| G05.4 | REGN records from the region table | 1 | fully | 2.W3 | — |
| G06.1 | the route generator over hydrology at build time | T | fully | 2.W3 | — |
| G06.2 | the approach rule checked by the route generator and the place builder | T | fully | 2.W3, 2.W5 | — |
| G07.1 | a place row's reason in the world DB, checked at L1 | T | fully | 0.4 → 2.W5 | — |
| G07.2 | the `world-builder` recipe placing REFRs of source plugins' base records (0026 §3) | 1, T | fully | 2.W5 | — |
| G07.3 | load doors (XTEL) on the plugin's own door refs | 1 | fully: native | 0.4 | — |
| G07.4 | interior CELLs built with their place by the same recipe | 1, T | fully | 2.W5 → 4.4 | — |
| G08.1 | Skyrim's four tiers: grass (GRAS on LTEX), placed TREE/STAT refs, object LOD, tree LOD | 1, 2 | fully | 2.W3 → 2.W4 | — |
| G08.2 | the CK's region generator once from REGN object lists (0028); wind is the engine's | 1, T | fully; whether the CK generator is repeatable for a seed is **UNVERIFIED** (the generator job records its output; 2.W4) | 2.W4 | — |
| G08.3 | Tropical Skyrim SSE and the Black Marsh mods as dependencies, the piece resolver choosing them first | 2, T | fully | 0.4 | — |

### 3.2 Tools and state

| Goal | Mechanism | Routes | Fit, why | Proved by | Stub |
|---|---|---|---|---|---|
| G09.1 | SkyLink AI and the console as the hands; ArgoniaBridge only for what SkyLink lacks (dev only) | 2, 5 | fully | 0.3 | — |
| G09.2 | scenes = a base save plus console batch files; `tools/run_journey.py` | 1, T | fully | 0.3 | — |
| G09.3 | the ladder L1–L6 (0021) | T | fully: method | 0.3 onward | — |
| G10.1 | ArgoniaCore: one plugin owns the families, calls `skse/core`, installs the hooks once, talks to the views by the message schema | 5 | fully | 1.1 | S10a |
| G10.2 | SKSE co-save families (id, version, save, load, migrate, reset) through the SKSE serialization interface | 5 | fully | 1.1 §b | S10b |
| G10.3 | world DB home tables; stable FormIDs from the allocator; records derived | 1, T | fully | 0.4 §0, 1.1 §e | S10c |
| G11.1 | this map; every rule's home named above; `skse/core` only for §6's list | 1–6 | fully | 1.1 §a | S11a |
| G11.2 | one table per number under `world/` or `data/`; GMSTs, perk rows, mod settings and `skse/core` constants all generated from it (P5) | 1, 5, T | fully | 1.1 → every chunk | S11b |

### 3.3 People and the living world

| Goal | Mechanism | Routes | Fit, why | Proved by | Stub |
|---|---|---|---|---|---|
| G12.1 | NPC_ records with one whole-body template (TPLT, traits flag, 0026 §7); FaceGen made on the player's machine; homes and work from the place record | 1, T | fully | 0.4 → 2.4 | — |
| G12.2 | AI packages with time conditions (sleep, eat, work, sandbox) on the lamp clock; lamps switched by enable parents on a time rule | 1 (+5) | fully; the lamp switch needs a tiny time rule (Papyrus is not used for it) | 2.4 | — |
| G12.3 | race shares applied by the build tools when people are made | T | fully | 2.4 | — |
| G12.4 | FACT records with ranks; advancement conditions by P2 and quest stages | 1, 5 | fully | 2.4 | — |

### 3.4 Fixed danger, bands, respawn

| Goal | Mechanism | Routes | Fit, why | Proved by | Stub |
|---|---|---|---|---|---|
| G13.1 | ECZN with min = max level and *Never Resets* where wanted `[CL B/BGSEncounterZone.h:14-16]`; NPCs at static levels, never *PC Level Mult* `[CL T/TESActorBaseData.h:29]`; no levelled lists for hostiles or loot (an L1 rule) | 1 | fully | 1.6 (one zone) → 2.7 §j | S13a |
| G13.2 | the ladder compiled to fixed NPC record numbers and per-actor abilities (P5) | 1, 5, T | fully | 1.6 (one D2 archetype) → 2.7 | S13b |
| G13.3 | enemy factions and aggression in records; roaming bands as placed actors on patrol packages; answered violence through Skyrim's assist and crime responses | 1 | fully | 1.6 (attack on sight) → 2.7 §j | S13c |
| G13.4 | capability gates authored as data (lock levels, climb heights, water depth, conditions by P2) | 1, T | fully | 2.W5, 2.12 | — |

Respawn on rest (G17.1's death and 1.5) is mapped here: Skyrim respawns a cell on a timer and only on re-entry
(`iHoursToRespawnCell` 240 h, `iHoursToRespawnCellCleared` 720 h [W:respawn]; cells reset only when re-entered
[W:cellreset]). Ours: those timers set out of reach; on each rest (and wake from death) ArgoniaCore resurrects and
returns the `onRest` actors the roster compiled (`Actor::Resurrect` `[CL A/Actor.h:399]`, then move to their
editor location); `untilCleared` reads the location's cleared state `[CL B/BGSLocation.h:114]`; `never` is the
default. Whether `Reset` can override *Never Resets* does not matter here (a forum report says it cannot,
[W:respawn]); resurrecting refs in unloaded cells is **UNVERIFIED** (S17a kills the archetype, walks away, rests).

### 3.5 Character

| Goal | Mechanism | Routes | Fit, why | Proved by | Stub |
|---|---|---|---|---|---|
| G14.1 | Seven attributes canonical in the `stats` family, mirrored into seven reserved actor values (1.3 §a audit); derived values written as base AVs by `SetBaseActorValue` `[CL A/ActorValueOwner.h:19]`: Health, Stamina, Magicka, CarryWeight, SpeedMult, StaminaRate, MagickaRate, JumpingBonus `[CL A/ActorValues.h:36-40, 70]`; Strength's damage term and every score-and-curve job by P1 on `ModAttackDamage` and kin `[CL B/BGSEntryPoint.h:50]` | 1, 5 | loss: a score over two values cannot be a condition, so it is a carrier (P1) and depends on the AV budget; carry weight is in Skyrim units through the units module | 1.3 §a | S14a |
| G14.2 | 14 vanilla skill AVs plus 13 Custom Skills Framework skills (the 1.3 table; CSF skills are globals [A §4]); growth by P4 + `progression`; One-handed, Two-handed, Pickpocket hidden by the views | 1, 2, 5 | loss: CSF skills are globals, so conditions and perk rows read them only as globals and only for the player; NPC values are compiled | 1.3 §a | S14b |
| G14.3 | one schema: the compiler runs the core formulas for every actor (P5) and writes NPC_ skills and offsets plus one ability | 1, 5, T | fully | 1.6 (archetype) → 2.4, 2.7 | S14c |
| G15.1 | our stats view over the `stats` family; vanilla `StatsMenu` and the perk constellation suppressed (P6) | 5, 6 | fully | 1.3 → 2.2 | S15a |
| G15.2 | races (RACE) and birthsigns as permanent ability spells whose effects Skyrim has (resist poison, water breathing `[CL A/ActorValues.h:65]`); fields Skyrim lacks (our attributes, poise, block stability) as `StatEffect` entries in `effects`; one stack in the view; no standing stones (0012) | 1, 5 | fully | 1.3 (gear, a potion) → 2.1 | S15b |
| G15.3 | our creation view; face sliders from the vanilla race menu or RaceMenu if 3.2 needs it, the menu itself hidden (P6) | 2, 6 | fully | 3.2 | — |
| G16.1 | P4 stops vanilla gain; ArgoniaCore turns engine events (hit, damage taken, block, cast, unlock, brew, trade; `TESHitEvent` and kin, `AddSkillExperience` `[CL P/PlayerCharacter.h:731]` as the hook if an event is missing) into use events for `progression`, which applies Morrowind's rank cost, worthiness and vastei and writes skills back (AV or CSF API) | 1, 2, 5 | fully; that `useMult` = 0 covers every vanilla path is **UNVERIFIED** (S16a) | 1.5 | S16a |
| G16.2 | `progression`'s ranks-per-level curve (1…8, then 8) and the 1 : 3 misc credit, from the curves table | 5 | fully | 1.5 | S16b |
| G16.3 | rest (P3 on camp spots and beds) → the router opens our sitting view; `sitting` prices and applies; vanilla `LevelUpMenu` never fires (P4); Skyrim's own level is a mirror only (how it is written is **UNVERIFIED**; nothing reads it once zones are fixed) | 1, 4, 5, 6 | fully | 1.5 | S16c |
| G17.1 | Potions are ALCH (native). Death: the player's bleedout is caught (`TESEnterBleedoutEvent` `[CL T/TESEnterBleedoutEvent.h:9]`; the Respawn – Soulslike pattern [A §4]); `death` drops one pile ref, ArgoniaCore fades, moves the player to the last rest and restores, then resets `onRest` actors. Rest is the only save: `Game.SetInChargen(abDisableSaving)` [W:setinchargen] blocks player saves, ArgoniaCore writes the rest save with `BGSSaveLoadManager::Save` `[CL B/BGSSaveLoadManager.h:122]`, the router hides save entries | 1, 4, 5, 6 | loss: a frame of the bleedout kneel may show before the fade (fallback: catch lethal damage in `HandleHealthDamage` `[CL A/Actor.h:488]`, route 6); whether `SetInChargen` also blocks our own `Save` call is **UNVERIFIED** (S17a) | 1.5 → 2.8 | S17a |
| G17.2 | all of 76 §120 and §126 in `progression`, `sitting`, `rest`, `death`, `respawn` from the first rung (no placeholder rules) | 5 | fully | 1.5 → 2.8 | S17b |

### 3.6 Story and text

| Goal | Mechanism | Routes | Fit, why | Proved by | Stub |
|---|---|---|---|---|---|
| G18.1 | Skyrim's DIAL/INFO menu cannot grow a topic list or hyperlink keywords, so Argonia speakers do not use it. **Intercept** by P3 (activate choice, *Replace Default*), fallback the audit's guarded slot swap [A §1.2]; **engine**: our `topics` store and `conditions` (route 5), or a fork of MorrowindRuntime's model half (route 3, about 6,500 lines, GPL-3, [A §1.1]); 1.3 §b picks on its prototype; **view**: PrismaUI (route 2 + 6) | 1, 3 or 5, 4, 6 | fully | 1.3 §b → 2.5 | S18a |
| G18.2 | per-speaker answer variants in the topic records (written by the skills), first-match order picks the speaker's own | 1, 5 | fully | 1.3 → 2.5 | S18b |
| G18.3 | disposition 0–100 in the `dispositions` family (Skyrim's `GetRelationshipRank` `[CL T/TESCondition.h:514]` is a −4…4 ladder, too coarse, not used); bands < 30, 30–69, ≥ 70 pick variants; *essential* topics carry a data flag and an L1 rule that no condition on them reads disposition | 1, 5 | fully | 1.3 → 2.5 | S18c |
| G19.1 | quest rows → ArgoniaGen QUST (stages, log entries, objectives with no target, aliases) + generated Papyrus stage fragments (glue only); the universal-modder 1.7.104 field note as method [A §2] | 1, 4, T | fully | 1.4 → 2.12 | S19a |
| G19.2 | the vocabulary's native terms as Skyrim conditions and actions (`SetStage`, items, faction rank), the rest evaluated in `conditions` and mirrored (P2); our actions called from fragments through ArgoniaCore natives | 1, 4, 5 | loss: mirrors are player-scoped and may be a frame late; per-NPC predicates (`topicHeardFrom`) need one generated global per referenced instance | 1.4 → 2.12 | S19b |
| G19.3 | location packets as world DB rows, checked by the tools | T | fully | 2.12, 4.2 | — |
| G20.1 | world DB → writing skills → records; no line typed into a plugin | T | fully | 1.3, 1.4 | S20 |
| G20.2 | the `quest-write`, `dialogue-write`, `text-review` skills | T | fully | 2.5, 2.12 | — |
| G20.3 | lore extrapolation docs read by the skills | T | fully | 2.5 → 4.3 | — |
| G21.1 | FACT record, its quests and line record (0025) | 1, T | fully | 2.4 → 4.1 | — |
| G21.2 | evidence items as records with keywords (one base record per tamper state); `knowledge` family for witnessed, heard-from, custody; mirrored by P2 | 1, 5 | fully | 2.12 | — |
| G21.3 | QUST records and lines from the main-quest record | 1, 4, T | fully | 4.3 | — |
| G22.1 | No Google Maps Skyrim (GPL-3, gates quest markers, removes the player marker [A §4]); objectives with no target; the compass hidden by 1.2; Skyrim's own map markers appear on discovery | 1, 2 | fully | 1.4 → 2.12 | S22a |
| G22.2 | the directions generator over the route graph at build time; text goes into journal rows | T | fully | 2.12 | — |
| G22.3 | journal text through `text-review`; our journal view over the `journal` family; vanilla `JournalMenu` replaced (P6) | 5, 6, T | fully | 1.4 → 2.12 | S22b |
| G23.1 | Flat World Map Framework with our map image [A §4], markers by discovery, no player marker | 2, 6 | fully | 2.12 | — |
| G23.2 | the map render made by the installer on the player's machine | T | fully | 2.12 → 3.4 | — |
| G24.1 | the approach 1.2 §0 chose with the owner: PrismaUI views (pinned, unmodified [A §3]) over a Dear Diary paper theme, the Pelagiad font | 2, 6 | fully | 1.2 → 2.2 → 3.1 | S24 |

### 3.7 Items and systems

| Goal | Mechanism | Routes | Fit, why | Proved by | Stub |
|---|---|---|---|---|---|
| G25.1 | class keywords on WEAP records; P4 keeps One-handed and Two-handed at zero and `progression` credits the class skill from the hit's weapon keyword; crossbows from vanilla, thrown from Throwable Weapons SKSE [A §4] | 1, 2, 5 | fully | 1.3 §c → 2.3 | S25a |
| G25.2 | Blocking is Skyrim's (Block AV, `ModPercentBlocked` `[CL B/BGSEntryPoint.h:54]`) with the stack's guard mods. Condition 0–100 per item instance in an `items` family; unusable at 0 by refusing the attack in ArgoniaCore; armour effectiveness by P1 on `ModArmorRating` `[CL B/BGSEntryPoint.h:100]`. Skill never touches i-frames or windows: nothing here reads skill for them | 1, 2, 5 | loss: Skyrim keeps no condition and its per-instance data is the tempering value; how to tell instances apart (unique-id extra data) is **UNVERIFIED** (S25b) | 1.3 §c → 2.3 | S25b |
| G26.1 | coin by the barter menu; goods and favours by our service view, the favour paid by `completeQuest` | 1, 5, 6 | fully | 2.6 | — |
| G26.2 | prices by P1 on `ModBuyPrices`/`ModSellPrices` `[CL B/BGSEntryPoint.h:23, 75]` with `fBarterMin`/`fBarterMax` neutralised [W:speech]; purses are Skyrim's vendor gold lists; restock every 48 h by the vendor-respawn setting (its name and default **UNVERIFIED**); training by our service view (Skyrim's trainer cap is the trainer's own, not the governing attribute); travel as ferry activators; crime: Skyrim's witnesses, crime factions and guard stop, with the bounty mirrored into the `owing` ledger and custody handled by ArgoniaCore | 1, 4, 5, 6 | fully (the purse timer and bounty mirror are **UNVERIFIED**) | 2.6, 2.11 | — |
| G27.1 | Skyrim hands, dual cast and MGEF archetypes as the effect families; Magic Expanded for Morrowind effects (Mark, Recall, levitation [A §4]); castability `2×skill + Wil/5 ≥ cost` by a `CheckCast` hook `[CL P/PlayerCharacter.h:735]`; magnitude and cost by P1 on `ModSpellMagnitude`/`ModSpellCost` `[CL B/BGSEntryPoint.h:44, 53]`; folk sellers as data | 1, 2, 5 | fully; levitation's quality in Magic Expanded is **UNVERIFIED** | 2.9 | — |
| G27.2 | seller stock picked at build time with the core's castability (P5) | 1, T | fully | 2.9 | — |
| G27.3 | the rest of 76 §123: the 75 % cost-reduction cap in `magic`; enchanting budget by P1 on `ModEnchantmentPower` `[CL B/BGSEntryPoint.h:92]`; spellmaking in our view, making runtime spell forms | 1, 5, 6 | loss: see §1, runtime forms rebuilt from the co-save on load (**UNVERIFIED**); cast time has no entry point (**UNVERIFIED**) | 2.9 | — |
| G28.1 | Skyrim crafting: COBJ recipes, stations, alchemy and enchanting menus | 1 | fully | 2.10 | — |
| G28.2 | COBJ, INGR, ENCH records; soul tiers by conditions on `ModSoulGemEnchanting` `[CL B/BGSEntryPoint.h:94]` | 1 | fully | 2.10 | — |
| G28.3 | alchemy potency by P1 on `ModAlchemyEffectiveness` `[CL B/BGSEntryPoint.h:81]`, effects visible at 15/30/45/60 by stepped `ModInitialIngredientEffectsLearned` rows; tempering by `ModTemperingHealth` `[CL B/BGSEntryPoint.h:91]`; material tier by COBJ conditions on a carrier; repair (Skyrim has none) in `smithing` behind our view | 1, 5, 6 | fully | 2.10 | — |
| G29.1 | per-observer detection is Skyrim's (`RequestDetectionLevel` `[CL A/Actor.h:692]`), tuned by sneak settings and `ModDetectionSneakSkill`/`Light`/`Movement` `[CL B/BGSEntryPoint.h:62-63, 72]`; pickpocket chance is Skyrim's visible percentage via `ModPickpocketChance` `[CL B/BGSEntryPoint.h:71]`; locks by P3 on locked refs, `locks` deciding open or refuse and pick wear | 1, 4, 5 | loss: see §1 (the Elusiveness formula approximated); Skyrim's roll is not seeded | 2.11 | — |
| G29.2 | Skyrim's detection levels and combat states (unaware, searching, in combat) mapped to the three; the HUD's eye shows them | 1, 6 | fully; the mapping is **UNVERIFIED** (2.11) | 2.11 | — |

### 3.8 Combat and traversal

The owner added a candidate on 2026-10-29: **Nexus mod 28567**, a DS-style combat overhaul with poise, roll bands,
bash-parry, riposte, backstab and backstep, trialled as an alternative combat route; the planner's research lane is
evaluating it. Its licence, runtime support on 1.7.104 and source are **UNVERIFIED** here (not read by this lane).
It enters the combat map (2.7 §0) as a candidate on the rows it claims; it changes no route below until that lane
reports.

| Goal | Mechanism | Routes | Fit, why | Proved by | Stub |
|---|---|---|---|---|---|
| G30.1 | the combat map (2.7 §0) per DS1 behaviour: the 0.0 stack tuned (route 2), tweaked (route 3 or a shim), or built in ArgoniaCombat (route 5); candidates BFCO, SCAR, CPR and **Nexus 28567** (owner addition, under evaluation) | 1, 2, 3, 5 | fully: the map is the mechanism and records its own losses | 1.6 (tuned stack) → 2.7 | S30a |
| G30.2 | damage by P1 on `ModAttackDamage` (damage position and the Strength term per hand); stamina costs by mod settings and `ModPowerAttackStamina` `[CL B/BGSEntryPoint.h:42]`; poise by Modern Stagger Lock, the stack, **Nexus 28567** (candidate) or ArgoniaCombat, with `ModIncomingStagger`/`ModTargetStagger` `[CL B/BGSEntryPoint.h:48-49]`; defence: `AR/(AR + 135.6 + 0.6 × damage)` depends on the blow, which Skyrim's armour settings cannot express | 1, 2, 5 | loss in Part 1: mitigation approximated by armour settings (1.6 records the error); fully from 2.7 if the map moves it into a damage hook (`HandleHealthDamage` `[CL A/Actor.h:488]`) | 1.6 → 2.7 §a | S30b |
| G31.1 | the wiring spec (2.7 §a): every number reaches a mod by settings or perk rows generated from the sheet's tables (P1, P5) | 1, 5, T | fully | 1.6 draft → 2.7 §a | S31 |
| G32.1 | permitted Skyrim movesets through OAR and AMR (route 2), timing corrected at run time (0014 §2) when a window needs it; **Nexus 28567**'s own clips, if it has any, are checked against 0019 §6 by the research lane | 2, 5 | fully | 2.7 §e | — |
| G32.2 | hostile places and roaming bands placed as data (G13.3) | 1, T | fully | 2.7 §j, 4.2 | — |
| G33.1 | compiled ladder numbers (P5); AI by SCAR, CPR and the rest of the stack | 1, 2 | fully | 2.7 | — |
| G33.2 | encounter sockets placed from ecology and motive rows by the place builder | T | fully | 2.W5, 4.2 | — |
| G34.1 | recovery by `ModRecoverArrowChance` `[CL B/BGSEntryPoint.h:36]` rows per arrow keyword; impact response by material through Skyrim's impact data sets | 1 | fully | 2.7 §i | — |
| G34.2 | Skyrim archery and TDM aim; delivered-damage position by P1 for bows, no Strength carrier applied to bows (a weapon-type condition) | 1, 2 | fully | 2.7 §i | — |
| G35.1 | FreeClimb (GPL-3.0-only; README lists 1.7.104 [A §4]); our Acrobatics bands written into its settings, fork (route 3) only if a rule needs code | 2 (3) | fully if its settings reach speed and stamina drain (**UNVERIFIED**) | 0.2 → 2.13 | — |
| G35.2 | surface semantics as climbable flags or keywords on our pieces' collision as FreeClimb reads them (**UNVERIFIED** what it reads) | 1, 2 | fully if FreeClimb's test is data-driven, else a fork | 2.13 | — |
| G36.1 | Swimming Extensions (189821) and, if needed, Underwater NG for diving; breath `25 + 0.35×Athletics + 0.25×End` by the breath setting plus Argonian water breathing; swim speed by P1 | 1, 2 | loss: see §1, the underwater layer is the mods' | 0.2 → 2.13 | — |
| G36.2 | swimming creatures by race flags; underwater pursuit by the diving mods' AI support (**UNVERIFIED**) | 1, 2 | loss: Skyrim actors swim at the surface unless a mod adds diving AI | 2.13 | — |
| G37.1 | Sailable Ship (modified with credit after permission, route 3) plus ArgoniaBoats' helm and wind model (route 5) | 3, 5 | loss: see §1, a moved reference, no vehicle physics | 0.2 → 2.15 | — |
| G37.2 | ownership, moorings and recovery in an ArgoniaBoats family; routes and ferries as data | 1, 5 | fully | 2.15 | — |
| G38.1 | hazards (HAZD), spells, effect shaders and triggers authored from the marsh rows | 1 | fully | 2.14 | — |
| G38.2 | one hazard table → placed hazard refs or trigger volumes applying a magic effect; volume entry seen by ArgoniaCore rather than a Papyrus `OnTriggerEnter` | 1, 5 | fully | 2.14 | — |
| G38.3 | creature attack spells and projectiles as records (the wamasu's shock spit) | 1 | fully | 2.14 | — |
| G39.1 | XP32 ragdolls, Precision impulses | 2 | fully (nice to have) | 2.7 §i | — |

### 3.9 Look, sound and release

| Goal | Mechanism | Routes | Fit, why | Proved by | Stub |
|---|---|---|---|---|---|
| G40.1 | Community Shaders features and our weathers and lighting templates | 1, 2 | fully | 0.2 → 2.W3 → 4.6 | — |
| G41.1 | SOUN, SNDR, MUSC and acoustic spaces per region and cell | 1 | fully | 2.16 | — |
| G42.1 | our start quest, start-enabled flags off in overrides, story-manager branches gated (0012); strings ours; silent lines (Fuz Ro D-oh pattern) if any line goes through the vanilla path; the running-quest allow-list read through the bridge | 1, 2 | fully | 0.4 §b → 2.17 → 3.3 | — |
| G42.2 | Tropical Skyrim SSE first in the piece resolver and the land (0028) | 2, T | fully | 0.4 | — |
| G43.1 | the immersion inventory and its gate | T | fully | 0.4 §c → 2.17 → 4.1 | — |
| G44.1 | our shell views; the main menu and loading screens as Scaleform restyles if PrismaUI is not up before the main menu (**UNVERIFIED**) | 2, 6 | fully | 3.1 | — |
| G45.1 | our creation view (G15.3) | 2, 6 | fully | 3.2 | — |
| G45.2 | the opening quest's content | 1, 4, T | fully | 3.3 | — |
| G46.1 | the installer and modlist; the no-assets guard | T | fully | 0.2 → 3.4 → 4.6 | — |

## 4. What this map changes

- **The dialogue intercept has a route-1 option the audit did not list:** P3's activate choice with *Replace
  Default*. 1.3 §b's prototype tries it before the slot swap. If it holds, no 1.7.104 offsets are needed for the
  intercept.
- **Vanilla progression is switched off by data (P4), not by hooks.** The 1.1 router's "level-up and XP
  suppression" becomes a check that `LevelUpMenu` never opens, plus a hook only if S16a finds a gain path that
  ignores `useMult`.
- **One carrier per hand, not one per skill (P1).** This keeps the actor-value budget small enough for the 1.3 §a
  audit to fit.
- **The ladder compiler links `skse/core` (P5).** The formulas are not written twice, in Python and C++.

## 5. The Part 1 L4 stubs

Each stub starts from a scene on the base save (0022), reads state through SkyLink and the bridge, keeps a still
per step (0021), and fails if any read differs. "Core value" means the `skse/core` function run at L2 on the same
inputs. Scene names are proposals for the 1.1 build lane.

| Stub | Goal | Scene | Steps and the read that fails |
|---|---|---|---|
| S10a | G10.1 | `bat claywater-block` | List ArgoniaCore's registered families and hooks: every Part 1 family named in §6 is there. Register one hook id twice: the second is refused and logged |
| S10b | G10.2 | `bat claywater-block` | Write a marker value into each family, rest (the rest save), quit, load: every value reads back equal. Load a save made with family version 1 into version 2: the migration ran (version reads 2, value converted) |
| S10c | G10.3 | `bat claywater-block` | For the three Claywater people and the archetype, the form at the allocator's FormID has the editor id of its world DB row |
| S11a | G11.1 | any | ArgoniaCore's load log of installed hooks and event sinks equals §6's hook list; one not in the list fails |
| S11b | G11.2 | any | `fXPPerSkillRank`, ten perk-row multipliers and the reference character's base Health read in game equal the data table's values |
| S13a | G13.1 | `bat claywater-ambush` | Read the archetype's level and max health with the player at level 1, then at level 20 (set through ArgoniaCore): equal both times |
| S13b | G13.2 | `bat claywater-ambush` | The archetype's health, light-hit damage and armour rating equal the compiler's D2 output for its position |
| S13c | G13.3 | `bat claywater-ambush` | Teleport the player 15 m from the archetype in its view: within 5 s it is in combat targeting the player; a Claywater person in the same view is not |
| S14a | G14.1 | `bat sheet-1` … `bat sheet-5` | For five characters set through ArgoniaCore, read base Health, Stamina, Magicka, CarryWeight, SpeedMult, StaminaRate, MagickaRate, JumpingBonus: each equals the core value. At level 10 raise Endurance 50 → 70: Health 100 → 130 with no reload. Two identical blows on a training target with Strength 0 and 100: damage ratio 0.5 : 1.5 (P1 applied) |
| S14b | G14.2 | `bat sheet-1` | All 27 skills read (14 AVs, 13 CSF globals) equal the co-save; the stats view lists 27 and a reader finds no One-handed, Two-handed or Pickpocket on any player screen |
| S14c | G14.3 | `bat claywater-block` | The archetype's and one Claywater person's skills, health, stamina and carrier values equal the compile CLI's output for their rows |
| S15a | G15.1 | any | The stats key opens our sheet view (still); `MenuOpenCloseEvent` never reports `StatsMenu` open |
| S15b | G15.2 | `bat sheet-1` | Equip the cuirass, drink a Fortify Long Blade 10 potion: the stack lists both entries with sources; effective Long Blade = base + 10, back to base after 60 s game time |
| S16a | G16.1 | `bat duel-ring` | Long Blade 15 (major, specialised): ten connecting blows of ≥ 15 % target health on a hostile → Long Blade 16; vastei equals the core value; vanilla One-handed XP (PlayerSkills) unchanged. Repeat one use of each Part 1 class (block, hit taken, cast, unlock): vanilla XP unchanged each time. A blow on a `trainingDummy` target adds 0 |
| S16b | G16.2 | `bat sheet-1` | At level 1, one counted rank → one pending level; three misc ranks → one counted rank |
| S16c | G16.3 | `bat camp` | With one pending level: activate the camp spot → our sitting view opens and `LevelUpMenu` never does; buy one Endurance point: vastei drops by `cost(End, 1, level)`, level +1, Health recomputed. Activate a bed spot inside the settlement bounds: refused, wait only |
| S17a | G17.1 | `bat camp` then `bat claywater-ambush` | Rest at the camp, kill the archetype, carry 120 vastei, take lethal damage: the player wakes within 2 m of the camp marker, no save is loaded (a container moved before death stays moved), one pile ref at the death spot holds 120, carried is 0, the archetype is alive again. Teleport 1.5 m from the pile, activate: carried 120. Die twice: one pile, the second amount. The quicksave key and the journal's save entry write no file (save-folder count unchanged); one rest writes exactly one |
| S17b | G17.2 | 1.5's journey | Fight to a pending level, die, wake, retrieve, rest, spend, load the rest save: every step's read passes |
| S18a | G18.1 | `bat claywater-block` | Activate a Claywater person: our dialogue view opens and `DialogueMenu` never reports open; the view's greeting equals the record; clicking a hyperlinked keyword adds that topic to the `topics` family. The time from activation to the view's first frame is measured and recorded (no budget) |
| S18b | G18.2 | `bat claywater-block` | Learn a topic from person A, ask person B: B answers, and B's text is B's record line, not A's |
| S18c | G18.3 | `bat claywater-block` | Set B's disposition to 20, then 80: the topic's variant text differs and each equals its band's record; at 0, an essential topic still answers |
| S19a | G19.1 | `bat quest-board` | Start the quest in dialogue: `GetStage` reads the start stage, its fragment's native call is logged, the journal family holds the entry |
| S19b | G19.2 | `bat quest-board` | With `knowsTopic(T)` false the gated line is absent; grant T through ArgoniaCore: the generated global reads 1 on the next frame and the line appears. The negated condition does the reverse |
| S20 | G20.1 | `bat claywater-block` | The greeting and two answers as the view received them (message log) equal the world DB rows byte for byte |
| S22a | G22.1 | `bat quest-board` | Stills at three steps of the quest show no compass and no quest marker; the target's map marker is undiscovered before arrival and discovered after |
| S22b | G22.3 | `bat quest-board` | The journal view's entry text equals the record and carries the game date |
| S24 | G24.1 | `bat claywater-block` | Open the dialogue window, journal, HUD and chart: each is a PrismaUI view (still; a reader confirms Pelagiad and the theme); `DialogueMenu` and `JournalMenu` never report open |
| S25a | G25.1 | `bat duel-ring` | A straight-sword hit adds Long Blade progress and no One-handed XP; a dagger hit adds Short Blade |
| S25b | G25.2 | `bat duel-ring` | 30 blocks lower the shield's condition by the core value; two identical shields in one stack keep separate conditions (or the loss is recorded); a weapon at 0 refuses the attack with "Your weapon is broken" and spends no stamina; damage at condition 1 equals damage at 100 |
| S30a | G30.1 | `bat duel-ring` | Draw, lock on, roll through a swing, guard, parry, riposte: each action's event or graph variable from the stack reads in order |
| S30b | G30.2 | `bat duel-ring` | A blow of known listed damage on the reference armour removes the health the wiring draft predicts, within the Part 1 approximation it records; a light attack's stamina cost equals the spec × the burden multiplier at each tier |
| S31 | G31.1 | any | Every game setting and mod setting in the wiring draft reads back in game equal to the table |
