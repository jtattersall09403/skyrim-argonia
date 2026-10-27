# Skyrim SE as host for "Argonia": can it carry Morrowind's soul?

Research date 2026-10-27. Web sources: Nexus mod pages, GitHub, UESP / CK wiki, Wikipedia, press. Where a fact could not be fetched it is marked **(unverified)**.

## 0. Platform facts that frame everything

- **Runtime.** Skyrim SE/AE is now at 1.7.99 / 1.7.104 (Creations-menu updates; [Digital Citizen](https://www.digitalcitizen.life/skyrim-update-1-7-99-expands-mod-support-but-pc-players-may-want-to-protect-existing-modded-saves/)). Current SKSE plugins ship one DLL for 1.5.97 through 1.7.104 (for example [Throwable Weapons for NPCs](https://www.nexusmods.com/skyrimspecialedition/mods/185102), [dMenu NG](https://www.nexusmods.com/skyrimspecialedition/mods/166751), [No Google Maps Skyrim](https://www.nexusmods.com/skyrimspecialedition/mods/147105)). CommonLibSSE-NG plus Address Library is the standard way to do this. Any plugin we write should target CommonLibSSE-NG multi-runtime, and players should pin the game version. Bethesda patches still break the plugins tied to specific offsets.
- **Actor values are a fixed enum.** There are 164 (indices 0–163) ([UESP Actor Value Indices](https://en.uesp.net/wiki/Tes5Mod:Actor_Value_Indices)). `Variable01`–`Variable10` (68–77) are user-defined. About 40 are obsolete: skill-advance AVs 114–131, the condition AVs, Fame/Infamy, the bribe/flattery AVs, and others. No mod adds true new AV indices; that would be S3. Every new-skill mod instead keeps its values in globals or in borrowed AVs.
- **Biped slots.** Slots 30–61 (32 slots). Bethesda uses 17; 15 are free by convention, including 44, 45, 46 chest outer, 47, 49 pelvis outer, 52–60 and 57 shoulder ([CK bodyparts](https://ck.uesp.net/wiki/Skyrim_bodyparts_number)).
- **Tier key, as the coordinator defined it.**
  - **S1** is a classic data mod: ESP, Papyrus and existing mods, with no DLL of our own.
  - **S2** is our own SKSE C++ plugin that hooks the unmodified exe.
  - **S3** is deep hooking that replaces whole subsystems, such as an own UI renderer for dialogue and menus, or the actor value system.

---

## 1. Morrowind-style dialogue (topics, hyperlinks, learned topics, disposition, persuasion)

### (A) Existing work
- **Skywind** ([FAQ](https://tesrskywind.com/faq/)). It works inside Skyrim's dialogue menu. Morrowind's dialogue "is split into shorter segments and linked to keywords, with prompts for all topics", and every line is voiced. In other words, Morrowind topics become Skyrim player prompts gated by conditions. The FAQ does not mention a hyperlink text renderer. Not released; source not public.
- **Classic Dialogue Menu** ([UESP](https://en.uesp.net/wiki/Skyrim_Mod:Classic_Dialogue_Menu)). A dialoguemenu.swf replacer in the style of older Bethesda games. SE, v1.01, Sept 2024, SWF only. It changes the look but adds no topic-learning logic.
- **Dialogue History** by powerofthree ([Nexus 114238](https://nexusmods.com/skyrimspecialedition/mods/114238)). An SKSE plugin that logs every line, browsable per NPC with audio replay. This proves a plugin can capture the topic and response stream. Source not linked; licence not shown.
- **Dynamic Dialogue Replacer** by Scrab ([Nexus 135618](https://nexusmods.com/skyrimspecialedition/mods/135618)). An SKSE plugin that patches player and NPC lines at runtime from YAML, with Lua hooks. This proves the response text can be rewritten in flight, so keywords could be injected or highlighted.
- **EZ2C Dialogue Menu and Better Dialogue Controls** ([article](https://www.nexusmods.com/skyrimspecialedition/articles/2491)). SWF fixes for long option lists. Vanilla lists break with many options, which matters for a Morrowind-length topic list.
- **Enderal SE.** Its own `EnderalSE.dll` hooks DialogueMenu input and menu events ([commit 13635df](https://git.eddoursul.win/enderal/enderalse/commit/13635df9f80c60af99c6d9bda016735c80806815)). Source is on Eddoursul's public Gitea; no licence stated on the page.
- **Persuasion.** No Skyrim SE persuasion menu (admire, intimidate, taunt, bribe) was found. Vanilla has only speech checks as conditions on lines ([CK tutorial](https://ck.uesp.net/wiki/Tutorial:_Dialogue_Speech_Checks)) and the Bribe/Persuade/Intimidate prompts. Searches for "Morrowind persuasion" returned only Morrowind mods.
- **Conversations Raise Speechcraft** ([Nexus 93435](https://www.nexusmods.com/skyrimspecialedition/mods/93435)). Speech XP per topic. Small, but it shows a Papyrus function detecting topics already heard.

### (B) Closing the gap
- **Learned topics shared across NPCs.**
  - S1 compromise, the Skywind way: one "Topics" quest, with each topic a TESTopic whose lines carry a condition on a known-topic global or faction flag. A topic is learned by setting that flag from a fragment on the line that mentions it.
  - This works but does not scale well. It needs one global per topic, and the vanilla list UI shows every prompt the NPC has.
  - S2: a plugin keeps the learned-topic set in the SKSE co-save. It filters the DialogueMenu's topic list and evaluates `TESTopicInfo` conditions directly; CommonLib exposes the topic, info and condition structures.
- **Hyperlinked keywords in NPC text.** Vanilla shows the response as subtitles, not a clickable page. This needs a replacement dialogue UI that renders the response with clickable keywords and a scrolling topic sidebar, driven by the plugin.
  - The plugin reads the NPC's available topics, runs the condition evaluator, and plays the INFO with its voice and lip file.
  - Using PrismaUI (HTML) or a new SWF, this is **S3** under the coordinator's definition, because it replaces the dialogue menu.
- **Disposition.** Morrowind's 0–100 disposition does not exist; Skyrim has relationship rank −4..4.
  - S1 option: a per-NPC faction rank (0–100), or a borrowed `Variable0x` AV, used in conditions such as `GetActorValue Variable05 >= 50`.
  - Base disposition from race, faction and personality can be computed in a Papyrus or plugin function.
- **Persuasion menu.** A custom menu: S1 as message-box chains, S2/S3 for a real UI. The menu runs speechcraft versus disposition rolls and adjusts the disposition AV. Medium work once disposition exists.
- **Difficulty: large.** Most of the "soul" lives in the hyperlinked UI. The data (topics and conditions) fits Skyrim's records. A Skyrim-menu prompt list could be done at S1, Skywind-style, and is medium.

**Verdict: partly** (Skywind-style S1 prompts) / **gap** for true hyperlinks. A genuinely Morrowind-like dialogue **needs S2 + S3 UI**.

---

## 2. Attributes, 27 skills, classes, levelling at rest, vastei death pile

### (A) Existing work
- **Custom Skills Framework** by meh321 and Parapets ([Nexus 41780](https://www.nexusmods.com/skyrimspecialedition/mods/41780); source at GitHub Exit-9B/CustomSkills, MIT for v2+). An SKSE DLL for unlimited new skills with their own perk trees; values live in globals. v3.2.0 of 02 Oct 2026 supports 1.7.99. Mature and permissive. This is the route to 27 skills.
- **Skywind** ([FAQ](https://tesrskywind.com/faq/); [Wccftech May 2026](https://wccftech.com/skywind-2026-milestone-quests-written-no-release-date/amp/)).
  - Attributes return, and the 18-skill limit is bypassed with new skills that have perks.
  - It has a major/minor class system "like Oblivion", and the "full character class system" is implemented.
  - It requires SKSE. Not released; code not public.
- **E.S.L.A.** ([Nexus 60199](https://nexusmods.com/skyrimspecialedition/mods/60199)). Eight attributes, a level only after sleeping, 13 birthsigns, 21 classes, tied to perks. Requirements and permissions were not visible **(unverified)**.
- **Classic Classes and Birthsigns SSE (Reimagined)** ([Nexus 41298](https://www.nexusmods.com/skyrimspecialedition/mods/41298)). Papyrus and data. 21 classes plus custom classes, with a +20 ModAV on major skills. Last updated March 2023. Modification needs permission (the page contradicts itself).
- **Sleep to Gain Experience** by Zebrina ([Nexus 17791](https://www.nexusmods.com/skyrimspecialedition/mods/17791)). An SKSE plugin that banks skill XP and applies it only on sleep, stored in the co-save. CommonLib source by max-su-2019 and the original by Zebrina are on GitHub. 1.1.2, June 2023. This is almost exactly the "consolidate at rest" mechanic.
- **Sleep to Level Up** by essardi ([Nexus 32357](https://www.nexusmods.com/skyrimspecialedition/mods/32357)). Papyrus. You must sleep to level or spend perks. Very permissive. 2020.
- **Experience** by zax ([Nexus 17751](https://nexusmods.com/skyrimspecialedition/mods/17751)). An SKSE DLL with no ESP: XP comes from quests and exploration, and skill caps are tied to level. It shows the level-up pipeline can be replaced at S2.
- **Skyrim Skill Uncapper** by Kasplat ([Nexus 82558](https://www.nexusmods.com/skyrimspecialedition/mods/82558)). An SKSE DLL for XP rates, per-level gains and caps. Source on GitHub. 2.2.4, Sept 2026.
- **Gold Is XP** ([Nexus 20084](https://nexusmods.com/skyrimspecialedition/mods/20084)). Papyrus; skills stop rising by use and points are spent on level. A precedent for a currency-driven sitting.
- **Enderal** ([wiki](https://wiki.en.sureai.net/Enderal:Character_Progression)). Learning, crafting and memory points; skills rise only through books and points, not use. This shows Skyrim's levelling can be fully replaced.
- **Death and recoverable pile.**
  - **Respawn – Soulslike Edition** ([Nexus 69267](https://www.nexusmods.com/skyrimspecialedition/mods/69267)). Drop gold and gear in a single grave, respawn at the last bed, reset enemies. One grave at a time, so a second death loses the first. Needs SKSE + PapyrusUtil + po3 Papyrus Extender. 1.5, 2022. Redistribution and modification allowed with credit.
  - **Respawn – Death Overhaul** ([Nexus 27546](https://nexusmods.com/skyrimspecialedition/mods/27546)). Its Diablo mode leaves an ashpile.
  - The vastei pile maps directly onto this if vastei is a gold-like misc item or currency.

### (B) Closing the gap
- **Seven attributes.** No true AV slots. Options:
  - Repurpose `Variable01`–`07`, or obsolete AVs, read and written by Papyrus and the plugin (S1/S2).
  - Or keep them in CSF-style globals.
  - Effects such as Strength on carry weight and damage, Agility on dodge, and Speed on movement need hooks. SpeedMult is an AV; carry weight is an AV. The damage formulas need S2 hooks on hit or damage (Valhalla Combat and Precision show the hook points).
  - The stats menu cannot show them without a UI change: CSF draws its own skill-menu entries; otherwise a custom panel is needed.
- **27 skills.** 18 vanilla plus about 9 through CSF: Short Blade/Long Blade split, Spear, Axe vs Blunt, Medium Armor, Mysticism, Hand-to-Hand, Acrobatics, Athletics, Mercantile, and so on.
  - Use-based XP for CSF skills is Papyrus or plugin driven.
  - The vanilla `OneHanded` XP has to be redirected by weapon keyword with an S2 hook on `PlayerCharacter::AddSkillExperience`.
- **Major, minor and misc classes.** Data plus script (S1). Skywind and ESLA prove it.
- **Level at rest with vastei.**
  - Bank XP: the Sleep to Gain Experience pattern, MIT-adjacent, source available.
  - On sleep, open the "sitting" menu and spend vastei on attributes.
  - On death, drop vastei as a world pile (Respawn pattern).
  - All S1/S2. Note that Skyrim's death is a load-game by default; the Respawn mods intercept bleedout, which is a known pattern.
- **Perks.** Perk trees are AVIF data and can be emptied or repurposed (S1). CSF provides its own trees.
- **Difficulty: medium.** Attribute effects on combat formulas are the main S2 work. The attribute and sitting UI is medium.

**Verdict: partly covered.** The pieces exist (CSF, Sleep to Gain XP, Respawn, ESLA). Composition and the attribute formula hooks are ours. **Doable at S2, with no S3 needed**, if we accept globals or borrowed AVs instead of new AV indices.

---

## 3. Weapon classes and Morrowind armour slots

### (A) Existing work
- **Vanilla weapon types:** HandToHand, OneHandSword, OneHandDagger, OneHandAxe, OneHandMace, TwoHandSword, TwoHandAxe (also warhammers), Bow, Staff, Crossbow (Dawnguard). Crossbows are already present. Short blade maps to dagger plus shortsword with keywords.
- **Spears, halberds, quarterstaves, rapiers.**
  - Animated Armoury by NickaNak ([Oldrim 103155](https://www.nexusmods.com/skyrim/mods/103155); SE page 168523 could not be fetched, **unverified**). It adds new movesets for pikes, halberds, quarterstaves, rapiers, claws and whips through animation replacers keyed on weapon keywords, on top of existing anim types.
  - Patches such as [Requiem – Heavy Armory](https://www.nexusmods.com/skyrimspecialedition/mods/89009) integrate it.
  - [Armory Extended – Saints and Seducers](https://www.nexusmods.com/skyrimspecialedition/mods/164993) (Sept 2026) adds spears that rely on OCF-compatible animation mods. This is the pattern: new weapon class = keyword + OAR/DAR animation set.
- **Throwing.** Throwable Weapons SKSE plus [Throwable Weapons for NPCs SKSE](https://www.nexusmods.com/skyrimspecialedition/mods/185102) (GPL-3 DLL source, 1.5.97–1.7.104, Sept 2026). Also [Throwable Items](https://www.nexusmods.com/skyrimspecialedition/mods/44627) (May 2026).
- **Armour slots.** Morrowind's helm, cuirass, L/R pauldron, greaves, boots, L/R gauntlet and shield fit the free slots:
  - helm 30
  - cuirass 32
  - pauldrons 57 plus one of 46/47/59
  - greaves 49 or 53
  - boots 37
  - gauntlets 33 plus 58 or 59
  - shield 39

### (B) Closing the gap
- **Spears and other new classes.** Data plus existing animation mods (S1, as player dependencies). Separate skills go through CSF with a keyword-redirect hook (S2, see §2).
- **Separate armour slots.** Slot assignment is pure data (S1).
  - **Asset catch:** L/R split gauntlets and pauldrons need meshes cut per side. Under "we never make art" that means sourcing mods that already ship separate pieces, or accepting paired items.
  - Morrowind's per-slot weighted armour rating (cuirass 30%, and so on) differs from Skyrim's summed rating. Replicating it is an S2 hook on the damage-resist calculation. Ignoring it is S1.
  - Note the worn-armour body-mesh conflicts: the body (32) mesh must not include arms or legs if those slots are separate, which is again an asset question.
- **Difficulty: small to medium.** The data and existing animation mods carry most of it. The weighted armour formula and the skill split are S2.

**Verdict: mostly covered** (data and mods). The **assets for L/R splits are the real gap**; the armour formula is S2.

---

## 4. No quest markers, verbal directions, Morrowind journal, paper map

### (A) Existing work
- **Wayfinder** ([Nexus 121765](https://nexusmods.com/skyrimspecialedition/mods/121765)). Quest-givers give written directions into a "Wayfinder's Notebook", you can ask NPCs for directions, and map markers appear only after a visit. Data and Papyrus. A direct precedent for verbal directions.
- **No Google Maps Skyrim** by SkyHorizon3 ([Nexus 147105](https://www.nexusmods.com/skyrimspecialedition/mods/147105); GPL-3 on GitHub). An SKSE plugin that removes the player marker and map centring. The compass quest marker hides until within a set distance. 1.5.97–1.7.99+, 12 Oct 2026.
- **Compass Navigation Overhaul** by alexsylex ([Nexus 74484](https://www.nexusmods.com/skyrimspecialedition/mods/74484); details not fetched, **unverified**). A compass rework through Infinity UI.
- **Vanilla options.** The INI/game setting "quest markers off" (`bShowQuestMarkers`), compass toggle, and `bShowFloatingQuestMarkers`. Skywind says quest markers and fast travel can be switched off through its SkyUI MCM ([FAQ](https://tesrskywind.com/faq/)).
- **Flat World Map Framework (FWMF)** ([Skyrim Paper Map for FWMF](https://nexusmods.com/skyrimspecialedition/mods/62705)). It replaces the 3D map with a flat painted texture. Custom worldspaces are supported through a worldspace whitelist (FWMF FOMOD / FlatMapMarkers JSON), as the [Siege at Icemoth](https://www.nexusmods.com/skyrimspecialedition/mods/119974) and [Kirkmore](https://www.nexusmods.com/skyrimspecialedition/mods/107930) paper maps show (SE/AE/GOG to 1.6.1130).
- **A Quality World Map – Paper** ([5804](https://nexusmods.com/skyrimspecialedition/mods/5804)). Old (2016) but has a paper mode.
- **Atlas Map Markers** ([24104](https://nexusmods.com/skyrimspecialedition/mods/24104)). Markers can be set undiscovered per marker. Vanilla markers already stay hidden until discovered.
- **Journal.** Quest Journal Fix for SkyUI and journal SWF skins. No SE mod with a Morrowind topic index was found.

### (B) Closing the gap
- **No markers plus directions.** S1 (Wayfinder pattern, plus quest-target toggles) and the No Google Maps plugin. Small.
- **Paper world map.** FWMF with our own painted Black Marsh map. Since we make no art, that needs a sourced map image, such as UESP or ESO-derived (licence check), or a render of our own heightmap as UI (the UI exception).
  - The Morrowind *local* map, a paper-style per-cell map, is not covered. It needs an S2/S3 replacement of the local map or a custom UI. Medium.
- **Morrowind journal.** Dated entries plus a topics index (every learned topic and what each NPC said).
  - The data comes from the plugin's learned-topic store (§1) and Dialogue History-style logging.
  - The UI is a new journal page: SkyUI SWF tab or PrismaUI (S2/S3). Medium.
- **Difficulty: small** (markers) / **medium** (journal and local map).

**Verdict: markers and directions covered; paper world map covered; journal topic index and local map are gaps.**

---

## 5. Morrowind-style UI and HUD

### (A) Existing work
- **SkyUI 6** ([PCGH, March 2026](https://www.pcgameshardware.de/The-Elder-Scrolls-5-Skyrim-Spiel-37439/News/SkyUI-Mod-Comeback-nach-9-Jahren-1523510/)). The first big update since 2017. Supports 1.5–latest, source on GitHub (licence not stated in the article).
- **Infinity UI** by alexsylex ([Nexus 74483](https://nexusmods.com/skyrimspecialedition/mods/74483); [GitHub](https://github.com/alexsylex/InfinityUI)). An SKSE plugin that injects SWFs into any menu or the HUD.
- **TrueHUD** by Ershin ([Nexus 62775](https://nexusmods.com/skyrimspecialedition/mods/62775)). Boss bars, floating bars, a player widget, and an API for other plugins.
- **PrismaUI** by StarkMP ([Nexus 148718](https://www.nexusmods.com/skyrimspecialedition/mods/148718), page not fetchable; [GitHub](https://github.com/PrismaUI-SKSE/framework); [docs](https://www.prismaui.dev)).
  - An Ultralight-based HTML/CSS/JS (React or Vue) overlay on DX11, with C++↔JS JSON interop and a live JS debugger.
  - Vanilla SWFs stay untouched. Ported to Fallout 4 and Starfield as well.
  - In use: for example [Modern Floating Damage](https://www.nexusmods.com/skyrimspecialedition/mods/170076), Aug 2026.
  - **Licence:** the custom Prisma UI License allows non-commercial use and redistribution of the official files. Modified public forks need written permission, and the Ultralight SDK has its own free licence. Fine as a player-downloaded dependency.
- **dMenu NG** ([Nexus 166751](https://www.nexusmods.com/skyrimspecialedition/mods/166751); GPL-3, Sept 2026). An in-game ImGui-style settings menu with an external API.
- **Full skins** such as [Dear Diary Dark Mode](https://nexusmods.com/skyrimspecialedition/mods/60837) and [Outlander UI II](https://www.nexusmods.com/skyrimspecialedition/mods/118815). SWF reskins, which shows a whole Morrowind-parchment skin is feasible.
- **No "Morrowind UI" replacer** for Skyrim SE was found. Skywind's UI is "based on SE with custom changes" (FAQ).

### (B) Closing the gap
- **Scaleform route.** Skyrim's menus are Scaleform GFx with ActionScript 2 SWFs.
  - Authoring toolchain: SkyUI historically used Adobe Flash Pro CS-era plus AS2. [JPEXS FFDec](https://github.com/jindrapetrik/jpexs-decompiler) (Java, runs on Linux) can decompile and edit AS2 and recompile scripts.
  - Linux and agent-friendly authoring is weak: no maintained AS2 compiler or IDE, so you edit in FFDec and test only in-game on Windows with a GPU.
  - Hard for agents.
- **PrismaUI route.** HTML/JS is very agent-friendly: you can build and test it in a headless browser against mock JSON, then bind it in the plugin.
  - Caveats: input focus and menu-stack integration have to be handled in our plugin (pause, cursor, gamepad); an extra renderer costs some performance; and we depend on a single-author framework under a restrictive licence.
- **Plan.** Keep the vanilla inventory and barter menus reskinned (S1 SWF skins), and build new Morrowind-only screens in PrismaUI (S2/S3): dialogue, journal, sitting, persuasion, travel.
- **Difficulty: medium** (reskin) to **large** (a full Morrowind-parity menu set).

**Verdict: partly.** The frameworks exist; the Morrowind look and screens are ours.

---

## 6. Fixed regional danger, travel services, no auto fast travel, training limits, merchant gold

### (A) Existing work
- **Encounter zones (ECZN)** are data: owner, location, min/max level, flags such as "Never resets" and "Match PC below minimum", plus "Disable combat boundary".
  - Setting min = max fixes a zone's level. [Morrowloot Ultimate](https://www.nexusmods.com/skyrimspecialedition/articles/172) uses static encounter zones.
  - [Encounter Zones Unlocked](https://stepmodifications.org/wiki/SkyrimSE:Encounter%20Zones%20Unlocked%20SE) goes the other way.
  - Fixed actors instead of leveled lists are data too.
- **Travel.** Vanilla carriages are dialogue plus Papyrus `MoveTo` with time passing, and the Dragonborn boat to Solstheim is the same. A silt-strider or boat service is just dialogue topics per destination (S1).
- **Fast travel.** `Game.EnableFastTravel(false)` (Papyrus). [Horizon Zero Dawn Fast Travel](https://www.nexusmods.com/skyrimspecialedition/mods/35793) gates fast travel behind consumables (SKSE plus Papyrus).
- **Training.** Game setting `iTrainingNumAllowedPerLevel` limits sessions per level. The trainer's maximum is set by the trainer's class/data. Morrowind's rule that a trainer cannot teach above their own skill needs a condition or script. Gold cost is a game setting.
- **Merchant gold.** Vendor gold is a leveled list or container per vendor faction (data); there are many mods ([Nexus 29403](https://www.nexusmods.com/skyrimspecialedition/mods/29403) and others).

### (B) Closing the gap
- All of this is S1 data and Papyrus.
- Morrowind-exact barter that weighs disposition and mercantile is S2, as a hook on the price calculation. Vanilla uses the speech AV and the fBarter game settings, which you can tune at S1.
- **Difficulty: small.**

**Verdict: covered at S1.**

---

## 7. Precedents

| Project | Status (Oct 2026) | What it changed or built | Tools |
|---|---|---|---|
| **Skywind** | Unreleased, no date. May 2026 update: all quests written and being implemented, about 3,000 NPCs (92% recorded), 10/13 regions at 90–100%, class system and probes implemented ([Wccftech](https://wccftech.com/skywind-2026-milestone-quests-written-no-release-date/amp/)) | Attributes, major/minor classes, skills beyond 18, keyword-split dialogue, configurable markers and fast travel, own SkyUI variant, own launcher, requires SKSE ([FAQ](https://tesrskywind.com/faq/)) | Creation Kit, SKSE, custom SkyUI; volunteer team of about 300 VAs |
| **Skyblivion** | Not released. Slipped 2025 to 2026; "final marketing push" in Sept 2026, aiming for late 2026 ([Wikipedia](https://en.wikipedia.org/wiki/Skyblivion); [Wikipedia: Skyrim modding](https://en.wikipedia.org/wiki/Skyrim_modding)) | Mostly a content remake on Skyrim mechanics | CK; distributed through Nexus, Steam Workshop, Bethesda |
| **Enderal SE** | Released (2019 SE), maintained | Replaced levelling (learning, crafting and memory points, books), own systems, and an own SKSE DLL that hooks the dialogue menu, menus and video ([Eddoursul Gitea](https://git.eddoursul.win/enderal/enderalse/commit/13635df9f80c60af99c6d9bda016735c80806815); [wiki](https://wiki.en.sureai.net/Enderal:Character_Progression)) | CK, SKSE, CommonLib, SWF edits |
| **Beyond Skyrim** | Eight provinces TBA. Bruma (2017), Bonemold pack (2022) and Roscrea pre-release (2020) are out ([UESP](https://en.uesp.net/wiki/General:Beyond_Skyrim)) | Content on vanilla mechanics | CK, Arcane University training |
| **Beyond Skyrim: Argonia** ("The Roots of the World") | Wiki says "Releases: None"; most lore pages unwritten, no leads listed ([BS wiki](https://wiki.beyondskyrim.org/wiki/Black_Marsh)). Effectively dormant or early | n/a | n/a |
| **Vigilant** | Released (2017), last updated 16 Jul 2026 ([Nexus 11849](https://www.nexusmods.com/skyrimspecialedition/mods/11849/)) | A quest and content mod, not a total conversion: new creatures, weapon arts, JSON save flags | SKSE, PapyrusUtil, Fuz Ro D-oh |

**Lesson.** Skywind keeps Skyrim's dialogue menu and bolts Morrowind data onto it, and it still needs SKSE. Enderal shows a team can own a DLL. None of them ships a true hyperlinked Morrowind dialogue in Skyrim.

---

## Tier map (which items need S2/S3)

| Item | S1 alone | Needs S2 | Needs S3 |
|---|---|---|---|
| 1 Dialogue | Skywind-style topic prompts with flag conditions; disposition as faction rank or Variable AV | learned-topic store, list filtering, condition evaluation | **hyperlinked response text and topic sidebar UI (replacing DialogueMenu)** |
| 2 Attributes/skills/levelling | classes, perks, Papyrus sleep-level, Respawn-style pile; CSF is an existing DLL dependency | attribute effects on combat formulas, weapon-skill XP redirect, banked XP, sitting logic | only if true new AV indices are demanded (avoid) |
| 3 Weapons/armour | slots, keywords, existing animation and throwing mods | short/long-blade skill split, Morrowind weighted armour rating | none |
| 4 Markers/journal/map | Wayfinder directions, marker toggles, FWMF paper map | No-Google-Maps-style map behaviour (existing DLL), topic-index data | Morrowind local map and journal UI if built as a replacement menu |
| 5 UI/HUD | SWF reskins, TrueHUD, SkyUI | binding new screens | **new menu set in PrismaUI** |
| 6 Danger/travel/economy | all | Morrowind barter formula (optional) | none |

**Impossible without S2:** learned topics at scale, attribute-driven combat formulas, short/long blade split XP. **Impossible without S3:** a true Morrowind hyperlink dialogue window and a topics-index journal. Every other item is reachable at S1 plus existing community DLLs.

## Risks
- Single-author dependencies: PrismaUI (restrictive licence), CSF (MIT, safe), the Animated Armoury SE page (unverified).
- Runtime churn: 1.7.x updates break offsets, so CommonLibSSE-NG and Address Library are mandatory, and players should be told to pin the version.
- UI authoring: Scaleform AS2 tooling is poor on Linux. PrismaUI is the agent-friendly route.
- No local GPU: every in-game test needs Windows plus a GPU (RunPod Windows or the owner).
- Assets: L/R armour pieces and a paper map of Black Marsh must be sourced, not made.
