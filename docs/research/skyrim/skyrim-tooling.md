# Skyrim SE as host for Argonia: tooling, Linux, testing, distribution, porting

Research 2026-10-27. Sources: web (cited inline), universal-modder notes (read only), Argonia repo docs (read only).
Confidence marks: [V] fetched and read today; [K] prior knowledge, not re-verified today; [I] inference that a sample should prove.

## 0. What universal-modder already knows

Files read: `skills/mod-any-game/references/engines/bethesda.md`;
`knowledge/games/skyrim-special-edition/rebuilding-a-cut-gatekeeper-with-generated-plugin-records-di.md`;
`knowledge/games/fallout-4/fallout-4.md`; techniques `bethesda-plugin-record-format-esm-esp-esl.md`,
`bethesda-esl-light-masters-and-plugin-archive-pairing.md`, `running-xedit-and-windows-modding-tools-on-linux.md`,
`oracles-how-agents-know-a-mod-works.md`, `driving-a-game-from-a-mod-side-command-file-lab-profile-wake.md`,
`installers-load-order-and-loaded-code-checks.md`, `choosing-a-mashup-route.md` (Skyrim rows), and the
`game-automation` and `publish-mod` skills.

**The Skyrim field note (College of Winterhold gatekeeper, Claude Code Opus 5.5, 2026-10-18).** On Windows,
Skyrim SE 1.7.104 Steam, CK 1.7.99, MO2 2.5.2, no SKSE:
- About 600 lines of Python wrote an ESL-flagged ESP straight to bytes, with no CK and no Mutagen. It cloned vanilla
  records (QUST, DIAL, DLBR, INFO, PACK) and wrote GRUPs, VMAD script attachments, CTDA conditions and voice-file
  paths. The object IDs started at 0x800.
- The only CK pieces it used were PapyrusCompiler.exe (`-all -f=TESV_Papyrus_Flags.flg -i=...`) and LipGenerator.
  SSEEdit was used read-only.
- Its oracle was the real game with a new character per build, console reads (`getstage`, `getglobalvalue`,
  `prid`/`sv`), and a checklist that the human ticked. It took about 30 builds over two long sessions.
- Most of the time went on how the dialogue engine behaves:
  - DLBR flags: blocking 0x2, exclusive 0x4, 0x6 to take over an NPC.
  - Shared INFO needs the borrowed line's own conditions to pass.
  - Voice path rule: `<plugin>/<voicetype>/<quest>_<topic>_<formid low 12 bits>_<response n>.fuz`, with quest plus
    topic EDIDs at 25 characters or fewer.
  - Localized string IDs have to be delocalized when copied.
  - Force-greet packages only re-evaluate on `EvaluatePackage()`.
  - Begin fragments are reliable and end fragments on Goodbye lines are not.
- Lessons:
  - Generated plugins work.
  - Dialogue, AI package and quest behaviour can only be learned in game, so an in-game oracle is the bottleneck.
  - Bethesda `.fuz` files must not ship. Copy them at install time from the player's own BSA.
- The SKSE build on that install (2.2.3, built for 1.6.640) could not load on 1.7.104. Version drift is real.

**Other relevant notes.**
- The xEdit-on-Linux note has fixes for 64-bit Delphi xEdit under Wine: use a win64 prefix, patch riched20
  `tomCharFormat`, and add a win32u syscall stub (that one is Starfield's).
- The record-format note gives the byte layout: the 24-byte header, GRUP, FormID light-slot algebra, the
  `XXXX` escape, and the STRINGS files.
- The ESL note covers the archive-to-plugin base-name pairing, packing textures into a DX10 archive, and packing
  sound uncompressed.
- The oracle note:
  - Automate the whole launch-to-check loop.
  - Prove the screenshot oracle is live (hash two frames).
  - Circuit-break after 3 identical failures.
  - Never let the thing under test own the test.
- The command-file bridge pattern is a mod-side interpreter that reads a file, runs commands on the main thread
  and logs results. It is the cheapest in-game harness. On Wine, watch for the read/delete race.
- The `bethesda.md` playbook recommends:
  - an MO2 instance per project;
  - plugins written by xEdit scripts, `xelib`, `esplugin` or your own writer;
  - CommonLibSSE-NG plus Address Library for SKSE;
  - an SKSE bridge plugin that calls out over localhost, which is how SkyrimNet works.

## 1. Writing plugins without the Creation Kit

| Need | Tool | Linux status | Verdict |
|---|---|---|---|
| Read, write and create any record | **Mutagen** (C#/.NET, GPL-3.0; Skyrim LE/SE/VR, FO3/FO4, Oblivion, Starfield) https://github.com/Mutagen-Modding/Mutagen [V] | Runs on .NET 8 on Linux. The repo has `Mutagen.Records.Linux.sln` [V]. It is typed for every Skyrim record, including WRLD/CELL/LAND/LTEX/NAVM/QUST/DIAL/INFO/SCEN/PACK/NPC_/VMAD [K] | **Primary writer.** Better than the field note's hand-rolled Python: typed, with FormLinks and master handling |
| Plugin to text for git | **Spriggit** (Mutagen team), YAML or JSON with one file per record; CLI `serialize`/`deserialize`; the CLI is the Linux route, the UI is Windows only; `Spriggit.Linux.slnx` https://github.com/Mutagen-Modding/Spriggit [V]. SkyrimNet already ships its ESP as Spriggit source [V] | Linux CLI | **Use it.** The source of truth stays Argonia's JSON, Spriggit YAML is the reviewable intermediate, and the ESP is a build output. plugin2text (https://github.com/miere43/plugin2text) is lossy and Windows only [V] |
| Batch patchers | **Synthesis** (Mutagen patcher pipeline; NuGet `Synthesis.Bethesda.Execution` [V]) | The GUI is WPF and Windows only. Patchers are plain .NET console programs and run anywhere [K/I] | Not needed. Our generator is a patcher |
| xEdit scripts | SSEEdit 4.1.x (Delphi) under Wine | Works with a win64 prefix. Some UI paths need the riched20 patch (universal-modder note) | Use read-only for checks: conflicts, "check for errors", and the AutoTest preset generators. Do not write with it; Mutagen covers that |
| Worldspace terrain (LAND: VHGT heights, VNML, VCLR, BTXT/ATXT/VTXT texture layers; LTEX/TXST) | Mutagen writes LAND directly [K]. The maths: one cell is 4096 units (58.5 m) with 33x33 vertices at 128 units (1.83 m) | Pure data | **Clean fit.** Our 4033² heightfield at 1.828 m is 126x126 cells at 32 quads each, so it maps one sample to one Skyrim vertex with no resampling [I] (1.828 m is about 128 units × 0.01428 m). VHGT stores a float offset plus int8 deltas, and steep cliffs need re-basing per row [K] |
| Navmesh (NAVM: NVNM verts, triangles, edge links, covers, portals; NAVI master info) | No public standalone generator exists [V, search found only CK tutorials and the format pages https://en.uesp.net/wiki/Skyrim_Mod:Mod_File_Format/NVNM_Field]. Mutagen can write NAVM [K]. The CK generates it with Havok-based "Generate navmesh" [K] | The CK under Proton has a working render window, but navmesh generation is not reported (https://apocalyptech.com/games/skyrim-linux-ck/ [V]) | **The hardest gap.** Choices: (a) generate with Recast, which we already bake (`docs/world/72-navigation-ai.md:31`), convert polygons to triangles, write NVNM with Mutagen, and generate NAVI ourselves. Feasible, but undocumented cases (edge flags, cover, door and water triangles, cross-cell portals, NAVI rebuild) need in-game proof [I]. (b) The CK under Wine with an AutoHotkey-style GUI macro on Xvfb; fragile. (c) Hand-tune what is left in the CK on a Windows VM. Bad navmesh means NPCs stand still, which is a blocker |
| Distant LOD (terrain and object LOD, tree LOD) | xLODGen, TexGen and DynDOLOD 3 (sheson) under Proton | Reported working on Proton 9, but Texconv fails at random with "A call to an OS function failed" on staging/Proton Wine builds (about 1 in 4000 calls), plain Wine 9.22 is fine, and 32–64 GB RAM is advised (https://stepmodifications.org/forum/topic/19354-linuxproton-a-call-to-an-os-function-failed/page/4/ [V]) | **Feasible headless-ish.** These are GUI apps with command-line options [K]; run them under Xvfb with retries and the plain-Wine Texconv |
| Precombines and previs | The Skyrim engine has none (that is Fallout 4/Starfield) [K] | — | Not applicable |
| Dialogue, quests, scenes, packages | Mutagen records. The CK's Dialogue View and Scene editor may be broken under Proton [V apocalyptech] | — | Write as data. The field note proves this works, but behaviour needs in-game iteration |
| Papyrus compile | (1) The CK's `PapyrusCompiler.exe` (.NET Framework) under Wine [K: generally works, apocalyptech unsure]; (2) **Caprica** (Orvid, C++), v0.3.0 adds Skyrim, Starfield and FO76, MSVC-only build https://github.com/Orvid/Caprica/releases [V]; (3) **russo-2025/papyrus-compiler** in V, Skyrim SE/AE, MIT, Windows exe release, has a flake.nix https://github.com/russo-2025/papyrus-compiler [V]; (4) Pyro (fireundubh) is a build wrapper over (1) or (2) [K] | Use (1) under Wine as the reference. (3) may build natively on Linux through V/nix [I] | Feasible. The reference compiler under Wine is the safe default; check native builds against it |
| Lip files | CK `-GenerateLips:<plugin>` / `-GenerateSingleLip` command-line switches (https://ck.uesp.net/wiki/How_to_generate_voice_files_by_batch [V]); they need FonixData.cdf | Not tested under Wine | Only needed for voiced lines; Argonia's Morrowind-style text topics can stay unvoiced |
| Archives | BSArch (xEdit project) under Wine [V universal-modder]; there are also native libbsarch, bsa-rs and similar [K] | OK | Pack textures as BSA with Skyrim SE's LZ4 frame compression [K] |
| Meshes | NIF from the vault as they are; PyNifly is used already | — | Skyrim needs **no conversion** for Skyrim meshes. That removes the whole GLB pipeline for kit pieces |

**Does the CK run headless under Wine?** No public report of a truly headless CK exists. Under Proton it runs as a GUI
app (Proton 9 is better than 10; CK Platform Extended helps). The render window and placement work. The linking
dialog and new triggers crash, and Dialogue/Scenes are untested [V apocalyptech]. Its useful batch switches are
`-GenerateLips`/`-GenerateSingleLip` [V] (others exist for FO4, such as precombine generation [K]). There is
nothing for navmesh. Treat the CK as a last-resort GUI tool on Xvfb. The design must not depend on it.

## 2. SKSE plugin development from Linux

- **CommonLibSSE-NG** (CharmedBaryon/alandtse; one DLL covers SE 1.5.97, AE 1.6.x and VR through Address Library
  IDs) is the standard [V wiki]. CommonLibVR has been merged into NG [K].
- **Toolchain.** The NG wiki covers clang-cl on Windows only. It warns that you must link with MSVC `link.exe`,
  not `lld-link`, or SKSE cannot find the exports [V
  https://github.com/CharmedBaryon/CommonLibSSE-NG/wiki/Compiling-with-Clang]. Two Linux routes:
  - (a) **msvc-wine** (mstorsjo) runs real `cl.exe`/`link.exe` under Wine with CMake and Ninja; a common way to get
    MSVC builds on Linux [K].
  - (b) clang-cl plus `xwin` (MS CRT and SDK headers and libs) plus `lld-link`. This is native and fast. The
    export problem is probably solved by explicit `__declspec(dllexport)`/`.def` exports of `SKSEPlugin_Load` and
    `SKSEPlugin_Version` [I]; prove it on a sample.
  - vcpkg dependencies (spdlog, fmt, directxtk, rapidcsv) cross-build with a custom triplet [K/I]. No public
    write-up of a Linux-hosted NG build turned up today. **Prove route (a) first on a hello-world.**
- **Address Library** (meh321): per-runtime `version-*.bin`. There is an open names database (`.relib` offsets,
  `.rename` names) for AE 1.6.317 and later at https://github.com/meh321/AddressLibraryDatabase [V]. CommonLib
  headers plus that database are the community "Ghidra layer": thousands of classes (TESForm hierarchy, Actor,
  AI process, BSScript VM, Scaleform, BSGraphics, havok wrappers) with layouts and vtables [K]. Shared IDA or
  Ghidra databases for SkyrimSE.exe are not published openly. People make their own from the Address Library
  names plus RTTI dumps, such as skyretk's `dump_rtti` (GOG 1.6.659 only, https://github.com/noxsidereum/skyretk [V]).
- **Version pinning (from skse.silverlock.org [V]):**
  - AE Steam: SKSE 2.3.1 for game **1.7.104**.
  - GOG: 2.2.6 for 1.6.1179.
  - SE: 2.0.20 for **1.5.97**.
  - VR: 2.0.12 for 1.4.15.
  - The page's compatibility line says "latest Steam 1.9.32", which contradicts the rest of the page. Check the
    exe in the AMI before relying on it.
  - 1.6.1170 has been superseded by 1.7.x on Steam.
  - Pin by keeping the depot fixed: `steamcmd +download_depot` of an exact manifest [K], or the community
    downgrade patchers (UnofficialSkyrimDowngrade / "Best of Both Worlds") for 1.5.97 [K]. In a cloud AMI you
    install once and never update, so pinning is easy. Ship against whatever version players have: NG with
    Address Library covers 1.5.97, 1.6.x and 1.7.x with one DLL when the needed IDs exist [K].
- **Rust or other languages.** Telekinesis links Rust into an NG plugin [V BUILD.md]; Faith Runner statically links
  Rust into SKSE [V universal-modder]. Workable, but keep the C++ glue thin.

## 3. Running Skyrim and SKSE on a Linux GPU box, and automated testing

- **Running.**
  - Skyrim SE has a ProtonDB rating of Platinum or Gold [K].
  - `skse64_loader.exe` under Proton works when it replaces the launcher or runs as a non-Steam shortcut. MO2
    runs under Proton through community installers (spooknik guide
    https://github.com/spooknik/SkyrimSE-Linux-Modding, Jackify) [V links].
  - For a scripted rig, **skip MO2**. Write `plugins.txt` and `loadorder.txt` in the prefix and deploy files
    directly into `Data/` (or use a scripted overlayfs) [I]. MO2's USVFS under Wine is the most fragile part.
  - Launch `skse64_loader.exe` directly with `SteamAppId=489830` set. Skip the launcher by writing the ini files
    ahead of time [K].
- **Headless GPU.** The game needs a real Vulkan device (DXVK). Run a headless X server or Xvfb plus the NVIDIA
  driver, or gamescope headless, on the g4dn/g5/g6. Selkies already captures that display. No public reports cover
  this exact stack, but DXVK on NVIDIA headless X is routine [I].
- **DRM and offline.**
  - Skyrim SE uses Steamworks DRM [K]: the steam_api checks ownership through a running Steam client. Log Steam in
    once on the VM with the owner's account, then use offline mode. Steam needs a login refresh every couple of
    weeks [K].
  - steamcmd can download the depot but cannot provide ownership at runtime.
  - Do not use emulators such as Goldberg. They get around DRM, conflict with the "authorized copies" EULA terms,
    and are a bad look for a Nexus project.
- **Driving the game. Existing parts:**
  - **SkyrimNet** (MinLL): an SKSE DLL with a web dashboard on :8080 and **an MCP server on :8889 whose tools query
    quests, NPCs and items and run console commands on the game thread** [V https://github.com/MinLL/SkyrimNet-GamePlugin].
    It proves the pattern; we would build our own slimmer version.
  - **ConsoleUtil / ConsoleUtil Extended**: Papyrus `ExecuteCommand`, `PrintConsole`, `GetConsoleMessages`,
    `OnConsoleCommand` (https://nexusmods.com/skyrimspecialedition/mods/133569 [V]).
  - **AutoTest** (Muriel-Salvan, BSD-3): an in-game framework driven by JSON. It summons NPCs and takes
    screenshots, teleports to cells and pans the camera, and writes status JSON. It needs SKSE, PapyrusUtil,
    SkyUILib and ConsoleUtil (https://github.com/Muriel-Salvan/AutoTest [V]). There is also an xEdit preset
    generator for it (https://www.nexusmods.com/skyrimspecialedition/mods/166752 [V]). Limitation: a crash is
    never reported as a failure; the test just stays at "started".
  - Crash Logger SSE (alandtse) for crash stacks [V link]. Papyrus logs come from `bEnableLogging`.
  - Recommended harness: **our own SKSE "agent bridge"** with an HTTP or MCP port, or the command file from the
    universal-modder note. Commands:
    - `coc`/`setpos` teleport;
    - run a console line or call Papyrus;
    - read state (quest stage, actor position and AI package, dialogue topic list, nav path result);
    - screenshot (copy the D3D11 backbuffer in-process, which avoids the frozen-capture trap);
    - time scale and waits;
    - a scripted input queue.
    Build it on the main-thread task interface (`SKSE::GetTaskInterface()->AddTask`) [K]. Log a frame counter so a
    stale-oracle check is possible.
- **Performance at 1080p [K/I, no published cloud benchmarks found].** For scale, vanilla SE runs at 60+ fps on a
  GTX 1060.
  - T4 (about GTX 1070 class, power-limited to 70 W): vanilla or lightly modded 1080p at 60 is fine. ENB or
    Community Shaders plus a 4K texture list drops to 30–45.
  - A10G (about RTX 3070–3080 class with 24 GB): heavy lists at 60.
  - L4 (about 3070-class raster with 24 GB, plus NVENC AV1): heavy lists at 60, and the best price per frame for
    streaming.
  - The CPU (single-thread draw calls) bounds Skyrim more than the GPU, and AWS Xeon or EPYC clocks are modest.
    Expect a 45–60 fps cap in cities with many draw calls. **Prove with one benchmark run per instance type before
    committing.**

## 4. Distribution and the law

- **CK EULA (https://en.uesp.net/wiki/Tes5Mod:EULA [V]):**
  - Personal and non-commercial use only. No fees or crowdfunding without ZeniMax's written consent.
  - Mods are for use with the Product and go to owners of authorized copies.
  - You own the mod but grant ZeniMax a broad irrevocable licence.
  - You must include a not-made-by-ZeniMax notice.
  - Reverse-engineering clauses cover the **Editor**.
- So a free total conversion that needs an owned Skyrim SE is squarely tolerated. Precedents:
  - **Enderal** (SureAI) shipped as a Skyrim mod, then as a free standalone Steam app (Enderal: Forgotten Stories,
    https://store.steampowered.com/app/933480 [V]) that requires Skyrim ownership. This is the gold standard, and
    it came with an arrangement with Bethesda [K].
  - Others: Beyond Skyrim, Skyblivion, Nehrim.
  - SKSE and CommonLib have gone untouched for 10+ years [K].
- **Ownership check.** The plugin needs Skyrim.esm and BSAs from the user's Data folder, so ownership is implicit.
- **Packaging.**
  - A Nexus mod (ESM, BSAs, SKSE DLL, a FOMOD).
  - Optionally a **Wabbajack modlist** for a curated stack (SKSE, Address Library, PapyrusUtil, Engine Fixes,
    SkyUI, any animation frameworks). Wabbajack installs from users' own Nexus downloads and their game. Linux
    users use **Jackify**, which has a CLI (https://github.com/Omni-guides/Jackify/wiki/ [V]).
  - Never ship Bethesda files (voice `.fuz`, vanilla meshes). Kit meshes are referenced in place, which is
    automatic because they already live in the BSAs.
  - Mod assets taken from other Nexus mods need each author's permission to redistribute, or must be listed as
    Wabbajack dependencies. This fits the repo's sourcing-register rule.

## 5. Mapping Argonia's world onto Skyrim records (Mutagen)

| Argonia home (docs/world/98-data-model.md) | Skyrim record | Fit |
|---|---|---|
| Terrain heightfield 4033² at 1.828 m, land cover | WRLD (new worldspace; parent none; map data, water height) plus 126² exterior CELLs with LAND; LTEX/TXST per cover; region WTHR/CLMT/REGN | **Clean** (sample = vertex). Also needs: LOD by xLODGen; a world map texture; land texture blending limited to 6 layers per quadrant [K] |
| Water bodies, rivers (hydrology) | WATR records; the cell water height is **one plane per cell** [K]; river surfaces as placed water planes or meshes | **Partial.** Rivers that step down need placed water activators/meshes, as in Skyrim's own rivers [K] |
| Place layouts: kit poses of Skyrim meshes (`blueprints/<place>.layout.json`) | REFR per op in the right exterior cell (persistent if referenced), base STAT/MSTT/FURN/CONT/ACTI/LIGH/DOOR from the plugin record that owns the NIF | **Clean.** Poses convert metres to units (×70.03) with Euler ZYX in radians. Kit pieces taken from Skyrim plugins already have base records; mod assets need new STAT bases. Composites become several REFRs or an SCOL |
| Interiors bound to plugin load doors (0114, `exterior-interior-links.json`, interior cell deltas) | Interior CELL copied or overridden from the source plugin; a DOOR REFR with XTEL to the partner door; deltas become REFR adds, overrides or disables | **Very clean.** The repo already treats the plugin as the interior manifest; Skyrim is the plugin's native home |
| Sockets: containers, items, beds, seats, stations, shrines, plants | CONT REFR with LVLI or static inventory; FURN markers; IDLM idle markers; FLOR for plants; ACTI for shrines plus Papyrus | **Clean to moderate.** Frozen `lootTable` becomes the container inventory. Owner becomes XOWN (faction or NPC). Locks become XLOC (level, key). Traps become existing trap activators |
| Locks, keys, day-locked doors | XLOC on REFR plus a KEYM; a door locked by day needs a Papyrus OnUpdateGameTime script or AI-package lock flags [K] | Moderate |
| Living things (`npcs.json`: race, look, statblock, factions, home and bed, day blocks, role exceptions, services, loadout) | NPC_ (race, CLAS, FACT ranks, AI data, outfit OTFT, inventory, default package list, voice type, FaceGen), FACT, CLAS, OTFT, LVLN | **Clean for data.** FaceGen geometry and tint must be **generated**, which is the CK's "Export FaceGen" (Ctrl+F4) [K]. Without it, NPCs get dark faces. Options: reuse vanilla NPC templates (TPLT), or generate facegen NIFs ourselves (the repo already has FaceGen research). **A blocker to solve** |
| NPC schedules (home, bed, work spots with activities, day blocks) | PACK records (Sandbox, Sleep, Travel, Eat, UseIdleMarker) with schedule hour and duration, location by linked REFR or XMarker, listed in order on the NPC | **Clean.** Day blocks become packages with hour windows. Role exceptions become package variants under conditions. This is Skyrim's native model |
| Factions, ranks, standing, crime as Owing per region | FACT (ranks, crime gold, jail, vendor data); per-region Owing ledger means one crime faction per region | **Partial.** Skyrim crime is per crime faction (hold) with bounty gold. "Owing" as debt with custody hours needs Papyrus/SKSE |
| Quest stage graphs (`quests/<line>.json`: stages, objectives, onEnter actions, successors, fail-forward) | QUST (stages, log entries, objectives, aliases, stage fragments in VMAD), Papyrus fragment scripts | **Clean structurally.** Stages map one to one, onEnter actions become stage fragments (generated Papyrus), objectives map to objectives, conditions map to CTDA. Aliases (reference/location) carry the "who and where" |
| Condition vocabulary (`docs/quests/85-condition-vocabulary.md`) | CTDA (about 400 functions: GetStage, GetStageDone, GetQuestCompleted, GetGlobalValue, GetItemCount, GetFactionRank, GetRelationshipRank, GetInCell, GetInCurrentLoc, GetCurrentTime, GetIsID, GetActorValue, IsInFaction, GetDead, GetDistance, GetIsRace…) plus GLOB for flags and counters | **Mostly clean:** questStage, questState, stageEverReached, objectiveComplete, flag and counter (GLOB), hasItem, wearing (WornHasKeyword), skill and attribute, gold, faction rank, disposition (relationship rank or a GLOB), inCell/inRegion (GetInCurrentLocation/IsInLocation), timeOfDay, npcAlive (GetDead), detectedBy (GetDetected), weatherIs (GetIsCurrentWeather). **Needs a Papyrus/SKSE state store:** knowsTopic, topicHeardFrom, witnessed, evidenceState, custody, rumourActive, firstTime, daysSince, owingAtLeast, placeStanceIs, histStepAtLeast, speakerCulture. Each becomes a GLOB or quest variable (`GetVMQuestVariable`/`GetVMScriptVariable` conditions [K]) or an SKSE condition function |
| Morrowind-style topic dialogue (topics, pool lines with conditions, per-person overrides, greetings, barks, glossary hyperlinks, knowledge state) | DIAL (topics) + INFO (conditions, responses, fragments) + DLBR (branches) + a per-NPC GetIsID condition; greetings in the Hello topic; barks as Idle topics | **The weakest fit.** Skyrim has no topic list that grows as you learn words, and no hyperlinked words in answers. Player-side topics can be built as top-level branches gated by GLOB or a "knows topic" quest variable, and INFO end fragments can set them. Options: (a) imitate it in the vanilla menu (many top-level branches, a long list, a rough feel); (b) **an SKSE + Prisma UI/Ultralight HTML dialogue menu** that runs Argonia's own dialogue runtime (port the TS logic or keep it in a JS context) and drives NPC lip/idle animation. That is S3. Vanilla dialogue also limits player prompts to about 80 characters, and text-only lines need silent voice files of the right length [K] |
| Items, gear, books, spells, effects | WEAP/ARMO/ARMA/BOOK/MISC/KEYM/INGR/ALCH/SPEL/MGEF/ENCH/SCRL | **Clean.** Morrowind-style effects (Fortify/Drain attribute variants, Levitate, Water Walking) map to MGEF archetypes. Levitate needs SKSE |
| Boats, climbing, swimming and diving, Souls combat, phone quality bands | — | **Need SKSE** (boats can be a horse reskin as a prototype, which the repo already researched; climbing as SKSE plus a behaviour graph; Souls combat through existing frameworks such as SCAR, Precision, MCO/ADXP, OAR, with animation-mod dependencies). Phone bands do not apply, since Skyrim is PC only |

## 6. Tiers: Skyrim as host

| Tier | Agentic development | Automated testing | EULA and community tolerance | Maintenance risk |
|---|---|---|---|---|
| **S1. Classic data mod** (ESM + BSA + Papyrus + existing SKSE mods; no DLL of our own) | **High.** Mutagen + Spriggit + the reference Papyrus compiler under Wine all run on the build VM. The field note proves an agent can write working quests and dialogue without the CK. Gaps: navmesh generation, FaceGen export, LOD under Wine | Medium. Needs the GPU box with the real game; AutoTest plus ConsoleUtil already gives teleport, screenshot and status JSON | Fully standard (Enderal precedent) | **Low.** Plugins survive game updates; only third-party SKSE dependencies break |
| **S2. Our own SKSE plugins** (CommonLibSSE-NG, Address Library) | **Medium-high.** Code is C++; cross-building from Linux has to be proved (msvc-wine first). CommonLib headers make most game APIs ordinary calls. The agent bridge and test harness live here | **High once built.** Our own bridge (HTTP/MCP like SkyrimNet) gives full read and act control; this is what makes fully automated testing real | Tolerated for 10+ years (SKSE, thousands of DLL mods on Nexus) | **Medium.** Each Bethesda update breaks things until SKSE and Address Library catch up (days to weeks); 1.7.x shows Bethesda still patches in 2026. Mitigate by pinning the AMI and supporting NG multi-runtime |
| **S3. Deep engine hooking** (replacing subsystems: dialogue UI, climbing/swimming locomotion, boat physics, own HTML UI through Prisma UI/Ultralight; RE of SkyrimSE.exe beyond CommonLib in Ghidra/IDA) | **Low-medium.** An agent can do RE work. The Address Library names DB and RTTI dumps seed Ghidra, but there are no shared databases, and behaviour and Havok internals are poorly documented. Each hook needs an in-game oracle and a lot of iteration. Animation/behaviour (HKX) is the known hard part | Medium. The same bridge, but bugs are crashes and frame-level timing; Crash Logger helps | Tolerated (large SKSE frameworks exist: Precision, SkyrimSouls, Prisma UI https://backiee.wasmer.app/http_github_com/PrismaUI-SKSE/framework). Ultralight has its own licence terms | **High.** Raw offsets and patched code break every update and clash with other hook mods |
| **S4. Engines that read Skyrim data** | **Mudcrab** (Bevy/Rust, GPL-3.0, about 400 stars, 860 commits): ESM to SQLite and NIF to glTF converter, runtime under way, "real-asset sign-off pending", physics, scripting and dialogue not shown working (https://github.com/Mudcrab-Team/mudcrab [V]). **OpenMW ESM4**: reads BSAs and partial ESM4; Skyrim is far from playable (https://www.gamingonlinux.com/articles/13606/ [V]) | n/a today | GPL engines reading users' owned data are fine (OpenMW precedent) | Not ready. Watch Mudcrab as the long-term path. Argonia's own three.js engine already reads Skyrim data, so it is S4 in spirit |

## 7. Feasibility verdict

- **Fully agentic development: feasible for S1 and S2, with three named gaps.** All three need proof on a sample
  before committing:
  1. **Navmesh**: write NVNM from the Recast output, or fall back to the CK under Wine.
  2. **FaceGen** for new NPCs: CK export, our own generator, or vanilla templates.
  3. **SKSE cross-build** on Linux.
- Everything else (worldspace, LAND, references, interiors, NPCs, packages, quests, dialogue records, Papyrus, BSA,
  LOD) runs headless on the Linux VM with Mutagen, Spriggit, and Wine for Papyrus, xLODGen and BSArch.
- **Automated testing: feasible, but only with our own SKSE bridge (S2) on the GPU box.** Steam has to be logged in
  once and kept in offline mode. Run DXVK on headless X, with Selkies for the owner. The bridge handles teleport,
  console, state reads and in-process screenshots; AutoTest is the off-the-shelf starter.
- The universal-modder evidence is that dialogue, AI and quest behaviour only show up in the game. Budget many
  in-game iterations per system: about 30 builds for one gatekeeper scene.
- **Main design risks:**
  - Morrowind topic dialogue and the Souls/climb/swim/boat systems push toward S3, which is fragile across updates.
  - Skyrim is PC only, which ends the phone/browser target. Streaming through Selkies is the only browser path.
