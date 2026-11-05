# Phase 1 unknowns: AE-era DLLs on 1.7.104, the LAL addon pattern, BM&V's start facts

Researched 2026-11-05 for [phase 1](../../phases/1-stack-in-bmv.md). [V] = fetched or measured today, [K] = prior knowledge, unproven here.
Live docs: `mods/README.md` (Combat section) says Stop On Slash and Elden Counter are "AE-era DLLs: confirm each loads"; this note
answers that (verdicts below) and corrects `mods/dependencies.json` row `pace` (it says "PACE combat AI"; PACE is a movement-speed mod).
Doc to edit: `mods/README.md` Combat section, plus the `check` and `runtime` fields of the rows named below. No new file.

## 1. DLLs in collection xyf1u3 on runtime 1.7.104

Measured with `7z l` over the archives in `~/.argonia/mods` and a PE export parse (SKSEPlugin_Version data) of each DLL [V].
Only three of the eight mods hold a DLL: PACE, Elden Counter, Stop On Slash. NASC (`NASC.esl`), TUDM Reanimated (`Mod.esp`), Dark Souls
Movement (`Regen.esp`), SkySA (`SkySA.esp` + `Nemesis_Engine/mod/skysa`) and Arena Movement (`AMMCO.esp` + Nemesis folder) are data only.

| Mod | DLL | Verdict on 1.7.104 |
|---|---|---|
| NASC 32996, TUDM 33049, DS Movement 33135, SkySA 31390, Arena Movement 53528 | none | loads as is (Nemesis folders of SkySA and AMMCO need Pandora's Nemesis-mod reading [K]) |
| PACE 27268 v1.0.2 (2019) | `skse/plugins/PACE.dll`, exports only `SKSEPlugin_Query`/`Load` | **drop the DLL** |
| Stop On Slash 66155 v2.2 (2022-04-30) | `dTryHitStop.dll` (file 280468) | **needs file 794626** |
| Elden Counter 65579 v1.6 (2022-04-26) | `Counter/1.6/EldenCounter.dll` (file 279662) | **needs file 794613** |

- PACE: description "WARNING: unsupported for a long while", requires "Skyrim SE 1.5.97, SKSE64 2.0.17"
  (Nexus API `mods/27268.json`, 2026-11-05 [V]); Nexus files list no later build (last 2019-12-03, `files.json`) [V]. The DLL has only
  `SKSEPlugin_Query`, the pre-AE interface; SKSE on AE runtimes skips such plugins [K]. Without the DLL its MCM does nothing; the
  `.esl` is inert. Movement speeds that PACE set are covered by the collection's Dark Souls Movement `Regen.esp` and AMMCO [K]; the
  swing-speed and slow-time features are not part of the souls-like set. Drop the row (or keep the `.esl` only if another plugin masters it: check with houseCARL).
- Stop On Slash 2.2 DLL: exports `SKSEPlugin_Version`, uses Address Library (`versionlib-{}.bin` string), flags `addressLibrary` only,
  `compatibleVersions` = {0x01061610}, `structsPost629` not set [V]. The 1.7 runtime is not in that list and the DLL does not declare post-1.6.629
  structs, so SKSE 2.3.1 refusing it is likely [K, not proven]; the decisive check is SKSE's log at the main menu (`stack.py menu`).
  Do not rely on the original; use the community rebuild below.
- Elden Counter: collection ships `1.5/EldenCounter.dll` (`SKSEPlugin_Query` only, dead on AE) and `1.6/EldenCounter.dll` (same flags as Stop On Slash:
  addressLibrary only, compat {0x01061610}) [V]. The FOMOD choice must pick 1.6, then be overwritten as below.
- **The rebuild: "dTry Plugin Updates"**, https://www.nexusmods.com/skyrimspecialedition/mods/85740, v1.0.3 listing, updated 2026-08-24 [V, API].
  Files: 794613 "Elden Counter" 1.0.4 and 794626 "Stop On Slash" 2.2.1, both 2026-08-24, "CommonLibSSE-NG update with added support for Skyrim 1.7.99,
  previous versions are still compatible" (file descriptions) [V]. Earlier 1.7.99 files 793441/793457 (2026-08-22) are superseded (794626's older twin is ARCHIVED).
  Page text: "Compatible with all game versions, excluding VR"; "Requires the original mod if you select it"; Address Library for SKSE Plugins required;
  Stop On Slash "Don't use with Precision" [V]. Sources named: github doodlum/StopOnSlash, doodlum/EldenCounter (CommonLibSSE-NG fork).
  A 2026 note on the *Key Utils* page says its update is not done for 1.7.99+ (web search summary of nexus 69944 [V]); not needed here, Key Utils is not in the collection.
- Measured on the downloaded DLLs (794613: 620,032 B; 794626: 652,288 B, both dated 2026-08-22) [V]: `SKSEPlugin_Version` present, `addressLibrary`
  and `structsPost629` both set, `compatibleVersions` empty (version-independent), built with CommonLibSSE-NG v6.7.0 in a tree named `mods-1.7.99-ng`.
  They overwrite `SKSE/Plugins/EldenCounter.dll` and `SKSE/Plugins/dTryHitStop.dll` (same names as the originals); the rest of each original mod (esp, Nemesis/OAR
  files, ini, MCM) stays. Licence of the rebuilds: GPLv3 with a modding exception (`COPYING`, `EXCEPTIONS.md` in the zips) [V].
- Not proven: that the NG build resolves every Address Library ID on 1.7.104's `versionlib` (they name 1.7.99). The same pattern held for AMR and
  Payload Interpreter ("Skyrim 1.7.104 Update" rows) and for 13 other DLLs logged "loaded correctly" on 1.7.104.0 (`mods/dependencies.json:139-546`) [V].
  Action: add the two files as rows `elden-counter-1.7` and `stop-on-slash-1.7` after their originals (like `amr-1.7.104`), fetch with `--record`, run `stack.py menu`.
- Fallback if either fails the SKSE log: drop that row; Stop On Slash is feel only (hitstop), Elden Counter is the guard-counter move (the souls-like set still plays without it).
  Source is open (GitHub doodlum forks), so a 1.7.104 rebuild is possible under route 3 (open-mod fork) if the owner wants it [K].

## 2. Alternate Start - Live Another Life (Nexus 272, v4.2.6a, file 729409, 2026-03-08): the addon pattern

Read from the archive's own `Alternate Start - Live Another Life Extension Documentation.txt` (Arthmoor) and the example addon "ASLAL - City Guard Extension
Example" 1.0.4, Nexus file 523574 (2024-07-21), source `.psc` read today [V]. Nexus page: "Skyrim Special Edition 1.7.99 or greater. USSEP 4.3.9 or greater"; extension framework since LAL 2.5.0 [V].

The documented pattern (the .txt, 35 lines):
1. ESMify `Alternate Start - Live Another Life.esp` (TES5Edit or Wrye Bash), open it in the CK, **ESPify it afterwards**. Our plugin therefore masters LAL.
2. In quest `ARTHLALChargenQuest`, tab Player Dialogue, add a **Top Level** branch (not blocking), or put the dialogue in your own quest.
3. Each topic is conditioned on speaker `ARTHLALMaraStatueActivator` (the talking activator, statue of Mara in the prison), and **each response is flagged "Goodbye"**.
4. A TopicInfo fragment calls `ChargenQuest.SetAddonQuestStage(Int, Quest)`: `ChargenQuest` is a property of type `ARTH_LAL_StartQuest` (must be filled), `Int` a stage > 0
   of *your* quest, `Quest` your quest. LAL calls that stage after the player uses the bed in the prison cell (cell 00021594, "Abandoned Prison").
5. Your quest stage fragment outfits the player, adds factions, sets the objective and moves the player; its **last line must be**
   `ARTHLALRumorsOfWarQuest.RegisterForSingleUpdate(0.25)` (keeps the route to Helgen working; LAL is "NOT a means to kill the Main Quest").

The example confirms it (`ARTH_TIF_LALGuardsExtension_03000D66.psc`: `ChargenQuest.SetAddonQuestStage(1, ARTHLALExtensionExampleGuards)`;
`ARTH_QF_LALExtensionExample_03000D72.psc`: `Player.EquipItem(...)`, `Player.AddItem(...)`, `Player.MoveTo(ARTHLALGuardsMarkarthStart)`, `setObjectiveDisplayed(1)`,
then the RegisterForSingleUpdate line). The start marker is a plain XMarker reference in the addon's plugin (`ARTHLALGuardsMarkarthStart` etc.; LAL's own are `ARTHLAL*Start`,
e.g. `ARTHLALDawnstarDockStart`); `MoveTo` to a marker in another worldspace works the same, so a marker in a BM&V cell is the whole "place". The addon plugin masters
Skyrim, Update, DLCs, five CC files, USSEP and LAL (its TES4 master list) [V].
- **FALSE: "ARTH_LAL_StartLocationList".** No such form exists: the 12 FLSTs in LAL's esp are `ARTHLAL*HouseEnableList/DisableList`, `HelgenEnable/DisableList`,
  `HFHousePartsMasterList`, `VoicesExcluded`; the string is absent from the esp (strings scan) [V]. Starts are dialogue topics plus a quest, not a list.
- LAL's esp masters CC files `ccbgssse001-fish.esm`, `ccqdrsse001-survivalmode.esl`, `ccbgssse037-curios.esl`, `ccbgssse025-advdsgs.esm`, `_ResourcePack.esl` and USSEP [V]:
  the profile must hold the CC masters (decision 0002 line 23 already expects the CC files); houseCARL will flag a missing one.
- Known extensions: City Guard example, Legacy of the Dragonborn, New Beginnings (Nexus 4939) [V, LAL page]. **BM&V ships no LAL start and none is known**: BM&V's plugins master
  only Skyrim and DLC (section 3); no search hit pairs the two. Our plugin is the first.
- Shutdown interplay (phase 1): the addon's last line schedules `ARTHLALRumorsOfWarQuest`, which drives LAL's Helgen rumour/MQ force-start (Dragonsreach main hall failsafe, per the page);
  `mods/allowed-quests.json` and the MQ shutdown must treat that quest explicitly (LAL "force-starts MQ on entering the main hall" if the civil war route is taken).

## 3. BM&V facts for the start

Source: `~/.argonia/mods/vault-bmv.tar` `.../black-marsh-mod-source/plugins/`, ESM parsed in the scratchpad with a Python record walker (never copied into the repo) [V].
The profile loads only `Black Marsh.esm` (`mods/dependencies.json:772-782`, `drop`: Valenwood, Black Marsh North, BosmerArmor). Masters of `Black Marsh.esm`: Skyrim, Update, Dawnguard, HearthFires, Dragonborn; **no
USSEP, no LAL master**; the plugin header flag is 0 (not flagged ESM; the `.esm` extension still makes it a master [K]).

- Worldspaces defined: `BlackMarsh` ("Black Marsh", form 0x0523D689, plugin index 5 = itself), `BlackMarsh2` (0x050D6960, holds Helstrom, Murkwood, temple, pyramid, dwarven, tribe cells).
  It also overrides `Tamriel` (0x3C) and `DLC2SolstheimWorld` (0x800). (Black Marsh North.esp adds `BlackMarshNorth` "Thorn", `UnderDark`; Valenwood.esp adds `Valenwood`: both dropped.)
- LCTN records: only 6 and none for a town: `BlackreachLocation`, `BthardamzLocation`, `CragslaneCavernLocation`, `MzulftLocation`, `NchuandZelLocation`, `DaintySloadLocation`.
  Towns and places are **cell editor ids** with no FULL name (names appear only on interiors). Exterior cells in `BlackMarsh` (grid from XCLC): `Lilmoth` 0x0500596F (3,-1),
  `Dock1` 0x0500591F (1,-2), `Dock2` 0x0502F35A, `LilmothHist` 0x05005A0D, `Pussbottom` 0x05005A0B, `Blackrose` 0x050AFC34 (33,-14), `Blackrosemarket` 0x050AFD1E (32,-17),
  `Blackrosegate` 0x050AFD20, `BlackRoseold`, `TheRose`, `Dock3`, `AltenMeirhall`, `HereguardPlantation`, `Castle`, `Longmont`, `Village`, `mound`, `MountainPass`, `BoattoBlackMarsh` 0x050396AF (10,-2).
  In `BlackMarsh2`: `Helstrom` 0x050D794B (-7,21), `dock4`, `dock5`, `Murkwood`, `Murkmire`, `Temple`, `temple2`, `pyramid`, `DWARVEN`, `TRIBE`, `BANDITCAMP1`. Only 66 cells carry an EDID of 4,826 (the rest are bare grid cells).
  Interiors: `01Ship` (3 doors), `01ShipDUPLICATE001`, `01dock3to4`, `01BlackRoseJail`, `HouseInt`, `01ArgonianHouseinside` (9 doors), `01CabinInt2`, caves and ruins.
  Form ids above are file-local (index 05); at runtime they are the load-order index of `Black Marsh.esm`.
- **Registry**: `story/data/sources/assets/registry-bmv.jsonl` (12,016 rows) holds asset paths (`pool, path, category, confidence`) only, no worldspace or cell ids; it cannot answer this [V].
  `docs/research/bmv/*.md` hold texture and creature facts, nothing on entry or cells [V grep]. Use the ESM as the source for the census tables.
- **Entry from Skyrim**: the only exterior link in the ESM is a door pair (79 XTEL doors total, 2 cross the worldspace boundary):
  `REFR 0x0500AC5C` in Tamriel's persistent cell (0xD74; base Skyrim.esm 0x27FE8), at (157470, 53952, -13945) = Tamriel grid (38,13), **13,945 units below sea level**, teleports to
  `REFR 0x050F91ED` in interior `01ShipDUPLICATE001` ("Ship"); the ship's other door `REFR 0x050F9399` leads to `REFR 0x05005AB4` in `BlackMarsh`'s persistent cell at (5688, -9382, 178),
  one cell south of `Dock1` (grid (1,-3)). So the route is a boat-interior door, but the Tamriel end is not reachable by walking [V]. ModDB says the mod "starts at Lilmoth" and mentions a boat
  or book portal, and an older version had a portal via an inn in Dawnstar (web search 2026-11-05, https://www.moddb.com/mods/black-marsh [V snippet only; ModDB gives 403 to fetch]).
  **No door, boat or carriage from a Skyrim town is in the data.** A LAL marker at `Dock1`/`Lilmoth` (3,-1) therefore bypasses nothing BM&V needs. The first walk needs a return trip only if the owner wants one.
- **Conflicts** (record overrides vs the load order USSEP, Black Marsh.esm, LAL, measured by master+form id) [V]:
  Black Marsh.esm vs USSEP share 23 records (8 CELL, 3 LCTN, 3 ACHR, 2 NAVM, 2 WRLD, 1 each NAVI/REFR/CONT/INGR/RACE), including Tamriel (0x3C), Solstheim (0x800), CELL 0xD74, NAVI 0x12FB4.
  Black Marsh.esm vs LAL share 4: WRLD 0x3C, WRLD 0x800, CELL 0xD74, NAVI 0x12FB4 (Skyrim.esm). LAL loaded last wins all four.
  The one that matters is **NAVI**: it indexes navmeshes; a later plugin's NAVI that lacks BM's meshes makes BM's new navmeshes unreachable to the AI at runtime [K]. houseCARL's 2026-10-29 sweep reported none
  because it checks masters and DLLs, not this. Action: a merge patch (xEdit navmesh-info merge, or load BM last of the three) and a gate census of NAVI entries per plugin; also confirm that
  LAL's WRLD 0x3C override does not drop BM's map/parent edits.
- No BM&V requirement beyond the five Bethesda masters is stated in the ESM; the ModDB comment "needs the Valenwood mod" refers to the `Valenwood.esp` we drop [web search snippet, K].

## Recommendations
1. Add rows for dTry Plugin Updates files 794613 and 794626 (section 1) and run `stack.py menu`; set the PACE row to dropped and correct its `why`.
2. Write the LAL addon as: our plugin masters LAL + BM&V; quest + TopicInfo (`SetAddonQuestStage`) + marker at BM `Dock1` or `Lilmoth`; last line `RegisterForSingleUpdate(0.25)`; ESMify/ESPify step is CK-only, so for a plugin made without the CK confirm `ChargenQuest` property binding in xEdit.
3. Add a NAVI census to `make check` (BM, USSEP, LAL, ours) before the first walk.
4. Archive the two rebuild zips in `~/.argonia/mods` and the private cache with the other rows (not done here; this lane did not copy them out of its scratchpad).

Covered: `docs/phases/1-stack-in-bmv.md`, `mods/README.md`, `mods/dependencies.json` rows, the eight collection archives, LAL 4.2.6a archive, City Guard example, USSEP 4.3.9c esp, vault-bmv plugins, Nexus API for mods 66155 65579 27268 32996 33049 33135 31390 53528 272 85740 69944 · Skipped: Data1/Data2.rar (9.6 GB, no cell data), Nexus comment pages (403), in-game load test (no machine run), Pandora behaviour of Nemesis mod folders.
