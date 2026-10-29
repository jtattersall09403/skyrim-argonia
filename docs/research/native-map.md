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
