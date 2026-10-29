# Dependency audit: which of the 98 rows Parts 0-1 need

Dated 2026-10-29. Read-only research for the owner's question ("98 is a lot of mods as dependencies!"). Nothing is
committed or shipped. Method: `data/dependencies.json` read row by row; every archive in `~/.argonia/mods` listed
or unpacked in a scratch folder (loose `.pex`/`.dll`/`.hkx` searched for names; `Sailable Ship.bsa` decompressed with
a throwaway LZ4 reader to read its scripts); TES4 headers of the 56 synced plugins read for masters
(`~/games/skyrimse/Data`); `out/pieces-index.json`; the world DB queried through `tools.argonia_world.db query`.

## Live docs that cover this

- `data/dependencies.json` is the register (98 rows: 89 play, 7 pipeline, 2 dev). `docs/phases/0-foundation/0.2-the-stack.md` §b
  and its acceptance ("every row loaded") **contradict decision 0027 §7 "tools arrive at first use"** for the 18 rows
  that only the slice places, 2.7, 2.9 or 2.12 use. `docs/research/2026-10-29/lane-0.2-stack.md:28` repeats the 98.
- Confirmed: houseCARL 2.1.1 found no missing master (lane-0.2-stack.md:86). I re-read the headers: the only
  inter-mod masters are MCM Helper to SkyUI, EREP patch to Rim Parry, Sailboats.esp to Scriptfreeshipsailing.esp,
  Cipactli to HTBM. Everything else masters only Skyrim, DLC and the three Creation Club files KotM needs.
- Superseded: the row `chunk` field is stale (combat rows say 1.4, which is the one-quest chunk, not 1.6;
  traversal and boats say 2.8, not 2.13 and 2.15; map says 2.10, not 2.12; Depths says 2.W2, the brief never names it).
- **The one doc to edit: `data/dependencies.json`** (add a per-row `arrives` chunk, a `set` on the group-A support rows,
  delete rows 97, and mark the cuts). Then one line in 0.2 §b pointing at it. No new file.

## Findings, in order

1. **66 of 98 rows are needed now (class a); 18 can wait for a named chunk (b); 3 are redundant (c); 11 are not needed (d).**
   Dropping c and d and deferring b leaves 66 rows, of which 29 are combat group A with its support, 37 everything else.
2. **The Black Marsh mods are over-fetched for Parts 0-1.** Claywater, the only Part 1 place, reads 8 non-vanilla mods
   (BMV, KotM, HTBM and Cipactli, Mud Mother, Ferries, SFSS canoe, SNT ferry raft) and nothing else. Eleven more asset
   mods first matter at 2.W5 or never.
3. **BMV (9.6 GB, the biggest row) supplies mostly flora to the slice places**: 136 of its 152 layout refs are
   `bmv:landscape/*` shrubs, ferns, reeds and moss, the thing decision 0028 gives to Tropical Skyrim and the region
   generator. Only 16 refs (6 assets: road signs, signpost, advertising board, cleat, one mushroom) are buildings or props.
   Keep the row (creatures, signs, Claywater), but lay a path subset (see Recommendations).
4. **The "Papyrus helper" rows 5, 6, 7 have no consumer in the stack**, and row 8 duplicates the bridge. Four rows.
5. **Six pipeline-source rows are redundant or unused**: 90 and 94 are covered by laid rows (verified by path), 91, 92, 96 have zero refs.
6. **Group A needs seven core rows that group B does not** (AMR x2, Payload Interpreter x2, BDI, dtry key utils x2).

## Black Marsh asset mods: what the world DB actually references

Query: `select ... from layout_place` (1,321 refs, 277 distinct assets, 18 placed slice places = every row of `layout`;
these are Part 1 Claywater plus the 17 wave-1 and wave-2 places of Part 2), prefix mapped to a mod by the pool list in
`world/sources/placement/exterior-interior-links.json`. Interiors: mentions of the prefix in
`world/sources/placement/kit-interiors/*.json`. `asset`, `culture_kit` tables are empty (0 rows) and there is no
piece table, so the layout rows are the only place-to-mod join; `out/pieces-index.json` holds records per plugin
(supply capacity, not use) and its `meshes` list is vanilla-only, so it cannot resolve mod meshes.

| Prefix | Row | Layout refs | Distinct assets | Places (of 18) | Claywater refs | Interior mentions | Index records |
|---|---|---|---|---|---|---|---|
| vanilla | base game | 609 | 126 | 18 | 64 | 1,406 | 19,031+ |
| mudmother | 71 | 169 | 14 | 13 | 8 | 112 | 67 |
| bmv | 89 | 152 | 24 | 14 | 8 | 366 | 467 |
| htbm | 70 (69) | 117 | 18 | 12 | 2 | 138 | 698 (130) |
| kotm | 68 | 103 | 36 | 15 | 1 (+3 composite pods) | 695 | 3,206 |
| composite | built from kotm, vanilla, xanmeer | 42 | 14 | 12 | 4 | 34 | n/a |
| shores | 77 | 38 | 6 | 4 | 0 | 17 | n/a (no plugin) |
| histtree | 82 | 18 | 9 | 4 | 0 | 21 | 23 |
| depths | 84 | 16 | 3 | 1 | 0 | 22 | 115 |
| jokerine | 76 | 13 | 6 | 1 | 0 | 13 | n/a |
| ferries | 79 | 12 | 5 | 5 | 1 | 10 | 91 |
| canoe | 86 | 10 | 2 | 6 | 1 | 7 | 12 |
| mwkeep | 73 | 7 | 5 | 1 | 0 | 126 | 0 (KotM.esp holds 191 records on its meshes) |
| ferryraft | 95 | 6 | 2 | 3 | 1 | 6 | n/a |
| sailboats | 87 | 3 | 2 | 1 | 0 | 8 | 5 |
| tropical | 66 | 2 | 1 | 2 | 0 | 3 | 99 |
| sbot | 83 | 1 | 1 | 1 | 0 | 11 | n/a |
| rowboats | 80 | 1 | 1 | 1 | 0 | 5 | n/a |
| hlaalu | 74 | 1 | 1 | 1 | 0 | 72 | 0 |
| ayleidkit | 93 | 1 | 1 | 1 | 0 | 86 | n/a |
| ayleidcc | 81 | 0 | 0 | 0 | 0 | 68 | 74 |
| sirenroot | 85 | 0 | 0 | 0 | 0 | 6 | 207 |
| xanmeer | 67 | 0 | 0 | 0 | 0 | 0 | 79 |
| xalfek, darkwater, hoddminir, drjacopo, impships, boatsanim, marshrest | 72, 92, 91, 75, 96, 88, none | 0 | 0 | 0 | 0 | 0 | 9 (SSK) |

Claywater's plan slugs (`place_asset_plan`): vanilla-farmhouse, bmv-round-huts, signage-blank, landmark-civic, clutter.
Across the 18 places, `place_asset_plan` names `xanmeer-tileset` in 2 places and `xanmeer-ayleid-exterior` in 1, yet no
layout row uses the `xanmeer:` prefix (the Xanmeer look comes from KotM's `argonia/xanmeer/*` folder and one composite portico).
Across all 829 places the plan names 48 slugs; those not reachable in Parts 1-2 are 2.W5-and-later business.

## The lists

**Slim list for Part 0-1: 66 rows** (class a): rows 1-4, 9, 11-20, 22-29 (core 23), 30-51 (combat group A, 22), 53-56
(traversal 4), 57-61, 63, 65 (soul and UI 7), 66, 68-71, 79, 86, 89 (land 8), 95 (pipeline 1), 98 (dev 1). Full per-row
table at the end.

**Counts by group, keeping both combat groups switchable:**

| | Rows | Of which |
|---|---|---|
| Base, no combat-group rows | 37 | core minus A support, traversal, UI, land, pipeline, dev |
| Group A (0.0 stack, `souls-0.0`) | 22 combat + 7 support = 29 | 8 shared with B, 14 A only (TK Dodge x3, Dynamic Dodge, IFrame Gen, Elden Parry x3, BDI patch, Rim Parry x4, Modern Stagger Lock... listed in the table), 7 support rows in core |
| Group B (`dsc-b`, Dark Souls Combat 28567) | 8 shared + 1 = 9 | DSC is the only B-only row; B needs no support row (no animmotion/PIE/payload/dtry in its 35 files) |
| `dsc-b2` (A plus DSC, minus Modern Stagger Lock) | 22 | |
| A as laid today | 66; B profile: 37 + 9 = 46 | |

The 7 support rows (16, 17, 18, 19, 20, 22, 23) sit in group `core` today, so profile B would still lay them. Give
them `"set": ["souls-0.0","dsc-b2"]` so the switch removes them with A. Evidence: animmotion in 867 Rim Parry and 1,288
Dynamic Dodge clip files, PIE in 414 Rim Parry files, payload in TK Dodge RE (451), none in DSC. Counter-weight: plan §4 names
AMR, Payload Interpreter, XPMSSE for 2.7 §e movesets, so they return at 2.7 whatever B decides.

**Defer, by chunk (18 rows, 1.18 GB archives plus the DSC lane):**

| Arrives with | Rows | Reason |
|---|---|---|
| Group B lane after 0.2 | 52 DSC | owner brief 2026-10-29 |
| 2.5 | 10 Fuz Ro D'oh | silent-line timing; no Part 1 dialogue voice |
| 2.7 | 21 SPID | only the combat map's "SPID shim" |
| 2.9 | 64 Magic Expanded | optional; a scratch-lane check in 1.2 |
| 2.12 | 62 Flat World Map Framework | 1.2 says "if it carries this, else our own view" |
| 2.W5 wave 1 | 80 Rowboats, 82 Sleeping Hist Tree, 87 Sailboats Expanded, 93 Ayleid Building Kit (pipeline) | Riverwalk, Greenspring, Lighter Flotilla, Wamasu Shrine |
| 2.W5 wave 2 | 73 MW keep, 74 Hlaalu, 76 Seashells, 83 Ships and Boats of Tamriel, 84 Depths | Voriplasm Vault, Opening Work Camp, Pearl Lots |
| 2.W5 (either wave, interiors) | 67 Xanmeer Tileset, 77 Shores CC, 81 CC Ayleid, 85 SIRENROOT | |

**Drop (14 rows): c (3):** 8 (the bridge covers it), 90 (66 covers it), 94 (86 covers it). **d (11):** 5, 6, 7 (no
caller), 72 (zero refs), 75 (names never referenced), 78 (requirement of an unlaid plugin), 88, 91, 92, 96 (zero refs), 97
(already marked dropped; delete the row).

## Risk of each cut

| Cut | Risk | How to prove |
|---|---|---|
| 5 PapyrusUtil, 6 PO3 Tweaks, 7 PO3 PE | Low-medium. No loose script or DLL in 80 archives, nor the Sailable Ship scripts (decompressed), calls them. Not read: scripts packed in BSAs (KotM, Depths, Ferries, Dear Diary) and DLL imports by ordinal. UNVERIFIED for those | Boot the 0.2 smoke without them; read the Papyrus log for "unable to find function" and Crash Logger |
| 8 ConsoleUtil Extended | Low. Same DLL name as row 9 (NG wins), the bridge prints console output | A 0.3 scene whose check reads console output |
| 9 stays | Sailable Ship: 6 scripts call ConsoleUtil (aaashipinputscript, aaashipchangemaxta, aaashipreturntodeck, +3) | n/a |
| 72, 75, 88, 91, 92, 96 | None found: zero refs in layout_place and kit-interiors; no plugin of theirs is laid (72 and 76 had `*.esp` dropped) | Re-run the prefix query when layouts change |
| 78 Base Object Swapper | Low: the Shores plugin is not laid, so nothing asks for swaps | Check `po3_BaseObjectSwapper.dll` has no INI in `Data/` after 77 is laid |
| 90 TS LE | None: 869/869 registry-tropical paths are in the SSE archive | done |
| 94 SFSS LE | None: 11/11 canoe registry paths are in the SSE archive 86; the LE archive holds 1 nif | done |
| 97 SkyLink | None: row says it does not load on 1.7.104 | n/a |
| Deferred 73/74 | Medium-low: both are mesh-only; KotM.esp holds 191 records on keep meshes, so check KotM loads without the keep set before deferring (its dangling-ref count is already 336) | houseCARL sweep after removal |
| Deferred 67, 77, 81 | Low: no Claywater ref | pieces resolver L1 on the 0.4 block |
| 4 and 65 (kept) | CS refuses to hook without EngineFixes. Deferring CS to 2.W3 alone would also free row 4 and move the 0.2 perf bar | Owner call; I kept them because the 0.2 bar is "with the whole stack loaded" |

## Patches, addons and fixes that exist only for another row

Rows 15 (for 14), 17, 19, 23, 35, 43 (DLL rebuilds for 1.7.104), 28 (for 13 + 27), 44 (for 42 x Precision), 45, 47,
48, 49 (Rim Parry x4 and its patch), 60 (skin of 59), 78 (for an unlaid plugin), 86 (master of 87), 25 and 24 (FreeClimb and
TK Dodge addon), 26 (PrismaUI). None are optional on their own; each leaves with its parent. If 2.7's combat map drops Rim
Parry, rows 46-49, 45, 48 and 20 (BDI) go with it (6 rows).

## Uncertain

- Scripts in BSAs other than Sailable Ship were not read; rows 5-7 rest on that gap.
- Whether KotM.esp needs rows 73/74 meshes at load (it holds records on them; it did load in the 98-row sweep).
- Whether 1.2 picks PrismaUI (rows 26, 58 are provisional) and whether EVG (56) is needed by the 0.2 smoke (it names climb, swim, ladder, boat only).
- Claywater's ferry, raft and canoe are one ref each (rows 79, 86, 95). If the first place dropped them, three rows defer to 2.15.
- The "slice places" are the 18 `layout` rows; `place_asset_plan` covers 827 places and only 28 slugs reach the 18.

## Recommendations

1. Add `arrives` (chunk) to every row of `data/dependencies.json`, make `stack.py` lay only rows whose `arrives` has passed (evidence: 0.2 §b acceptance "every row loaded" versus 0027 §7), and correct the stale `chunk` fields.
2. Lay BMV by path subset, not whole (`pick` exists on rows; evidence: 136/152 refs are flora that 0028 gives to Tropical Skyrim, and BMV's 9.6 GB is larger than the other 97 rows together, 7.4 GB): `landscape/{trees,plants}`, signs, `architecture/phitt`, `sheogorad`, `trdata/mushrooms`, creatures when 2.14 arrives.
3. Put the 7 support rows under combat sets so profile B drops them (finding above).
4. Test rows 5-7 by removal in the next 0.2 smoke run; then delete them.
5. Settle in the 2.W5 brief whether layouts keep BMV flora (136 refs) or the region generator does it; today the layout contradicts 0028 §2.
6. Add the Claywater boat question (three rows, one ref each) to the 0.4 first-block acceptance.

Covered: data/dependencies.json (98 rows), CLAUDE.md, PLAN §4, decisions 0006 §8, 0027 §7, 0028, docs/phases 0.2/0.4/1.2-1.6/2.7/2.15/2.W2/2.W5, combat-mod-28567.md, lane-0.2-stack.md, world DB (place/layout/layout_place/place_asset_plan), out/pieces-index.json, ~/.argonia/mods archives, ~/games/skyrimse/Data plugin headers, world/sources/{placement,assets,catalogue} · Skipped: reuse-audit.md beyond its headline (it audits build-versus-reuse of tes4skyrim, not mods), counts.json read (immersion inventory is Skyrim record reach, 3,249 reachable of 189,936, no mod-level data), BMV archive contents (9.6 GB tar), mods' internal BSAs other than Sailable Ship.

## All 98 rows

| # | id | group | chunk in file | class | evidence / chunk | risk |
|---|---|---|---|---|---|---|
| 1 | skse | core | 0.2 | a | 0.2; every SKSE plugin |  |
| 2 | address-library | core | 0.2 | a | 0.2; every SKSE DLL |  |
| 3 | crash-logger | core | 0.3 | a | 0.3; read after every run |  |
| 4 | engine-fixes | core | 0.2 | a | 0.2; Community Shaders refuses to hook without EngineFixes.dll (row 4 why) | If CS is deferred, this becomes optional |
| 5 | papyrusutil | core | 0.2 | d | No consumer found: no .pex or .dll in the 80 scanned archives, nor in Sailable Ship.bsa (decompressed), calls StorageUtil/JsonUtil/MiscUtil/ActorUtil (only dropped SkyLink and the tool houseCARL do). Logic stays out of Papyrus (CLAUDE.md) | Low. Scripts inside other BSAs (KotM, Depths) not decompressed: UNVERIFIED. Boot without it and read the Papyrus log |
| 6 | po3-tweaks | core | 0.2 | d | Only consumer is row 7; no scanned mod calls PE | Low (drops with 7) |
| 7 | po3-papyrus-extender | core | 0.2 | d | No scanned mod calls PO3_SKSEFunctions/PO3_Events; SPID (21) does not need it; row 7 why ("UI and traversal mods call") is not borne out | Low; UNVERIFIED for BSA-packed scripts |
| 8 | consoleutil-extended | core | 0.3 | c | Redundant with ArgoniaBridge `console` (skse/ArgoniaBridge/src/ep_state.cpp:44, returns console output); its ConsoleUtilSSE.dll is overwritten by row 9 anyway (row 8 conflicts field) | Low; 0.3 scenes use the bridge |
| 9 | consoleutilsse-ng | core | 0.2 | a | Sailable Ship needs it: 6 of its scripts call ConsoleUtil (decompressed from Sailable Ship.bsa) | Keep while Sailable Ship (55) is in |
| 10 | fuz-ro-doh | core | 1.3 | b | 2.5 dialogue (2.5 "Re-check": Fuz Ro D'oh); 1.3 text does not use it | Low; row chunk says 1.3 |
| 11 | skyui | core | 0.2 | a | 0.2; MCM host, Dear Diary base |  |
| 12 | mcm-helper | core | 0.2 | a | 0.2; MCM pages of TDM, Precision, TrueHUD, OCPA (MCM_ConfigBase seen in their files) | Needed by both combat groups |
| 13 | pandora | core | 0.2 | a | 0.2; runs on the machine (0014); also the FNIS path group B needs |  |
| 14 | open-animation-replacer | core | 0.2 | a | 0.2; OAR Stamina Cost (51) and movesets |  |
| 15 | animation-queue-fix | core | 0.2 | a | 0.2; OAR requirement |  |
| 16 | amr | core | 0.2 | a | Group A support: Rim Parry (867 clip files) and Dynamic Dodge (1288) carry animmotion annotations; DSC has none. 2.7 §e movesets also use it | Cut from B profile only |
| 17 | amr-1.7.104 | core | 0.2 | a | DLL for 16 |  |
| 18 | payload-interpreter | core | 0.2 | a | Group A support: PIE/payload annotations in Rim Parry (414 files), TK Dodge RE, SkySA | Cut from B profile only |
| 19 | payload-interpreter-1.7.104 | core | 0.2 | a | DLL for 18 |  |
| 20 | behavior-data-injector | core | 0.2 | a | Group A support: BDI variables for Rim Parry and TK Dodge addon |  |
| 21 | spid | core | 0.2 | b | 2.7 combat map ("config patches and SPID shims"); no Part 0-1 chunk calls it (row says 0.2) | Low |
| 22 | dtry-key-utils | core | 0.2 | a | Group A support: Dynamic Dodge, Rim Parry reference dtry (seen in their files) |  |
| 23 | dtry-key-utils-1.7.104 | core | 0.2 | a | DLL for 22 |  |
| 24 | skse-menu-framework | core | 0.2 | a | FreeClimb and TK Dodge addon (SKSEMenuFramework seen in the addon) |  |
| 25 | imgui-icons | core | 0.2 | a | FreeClimb requirement (imgui in FreeClimb) |  |
| 26 | media-keys-fix | core | 1.2 | a | PrismaUI hard requirement; provisional on 1.2 §0 choosing PrismaUI | Moves to (b) if 1.2 picks Scaleform |
| 27 | xpmsse | core | 0.2 | a | 0.2; skeleton for the animation mods |  |
| 28 | pandora-xpmse-patch | core | 0.2 | a | 0.2; Pandora needs it with XPMSSE |  |
| 29 | ssedisplaytweaks | core | 0.2 | a | 0.2; frame cap for the perf bar |  |
| 30 | precision | combat | 1.4 | a | 1.6; shared by A and B |  |
| 31 | true-directional-movement | combat | 1.4 | a | 1.6; shared |  |
| 32 | truehud | combat | 1.4 | a | 1.6; shared |  |
| 33 | tk-dodge-se | combat | 1.4 | a | 1.6; A only |  |
| 34 | tk-dodge-re | combat | 1.4 | a | 1.6; A only |  |
| 35 | tk-dodge-re-addon | combat | 1.4 | a | 1.6; A only (TK Dodge RE DLL) |  |
| 36 | dynamic-dodge | combat | 1.4 | a | 1.6; A only |  |
| 37 | iframe-generator | combat | 1.4 | a | 1.6; A only |  |
| 38 | skysa | combat | 1.4 | a | 1.6; shared |  |
| 39 | elder-souls-sword | combat | 1.4 | a | 1.6; shared |  |
| 40 | one-click-power-attack | combat | 1.4 | a | 1.6; shared |  |
| 41 | oar-stamina-cost | combat | 1.4 | a | 1.6; shared |  |
| 42 | elden-parry | combat | 1.4 | a | 1.6; A only |  |
| 43 | elden-parry-1.7.99 | combat | 1.4 | a | 1.6; A only (DLL for 42) |  |
| 44 | elden-parry-precision-fix | combat | 1.4 | a | 1.6; A only (patch: Elden Parry x Precision) |  |
| 45 | bdi-payload-patch | combat | 1.4 | a | 1.6; A only (patch: Payload Interpreter without Nemesis) |  |
| 46 | rim-parry | combat | 1.4 | a | 1.6; A only |  |
| 47 | rim-parry-ctd-fix | combat | 1.4 | a | 1.6; A only (fix for 46) |  |
| 48 | rim-parry-elden-patch | combat | 1.4 | a | 1.6; A only (patch 46 x 42; EREP_patchSA.esp masters RimExecutionHitSA.esp) |  |
| 49 | rim-parry-one-parry | combat | 1.4 | a | 1.6; A only (patch for 46) |  |
| 50 | modern-stagger-lock | combat | 1.4 | a | 1.6; A only |  |
| 51 | maxsu-block-overhaul | combat | 1.4 | a | 1.6; shared |  |
| 52 | dark-souls-combat | combat | 2.7 | b | Group B lane after 0.2 (owner brief 2026-10-29); the only B-only row. Optional, switchable | Lay `bb_dsc*` sounds excluded (already in drop) |
| 53 | freeclimb | traversal | 2.8 | a | 0.2 smoke (climb a wall); owner: traversal from the start |  |
| 54 | swimming-extensions | traversal | 2.8 | a | 0.2 smoke (swim, dive) |  |
| 55 | sailable-ship | traversal | 2.8 | a | 0.2 smoke (board and sail); 767 MB |  |
| 56 | evg-animated-traversal | traversal | 2.8 | a | 0.2 owner list (vault, ledge); not named in the smoke scene | Weakest of the four; UNVERIFIED what the smoke needs from it |
| 57 | custom-skills-framework | soul-ui | 1.3 | a | 1.3 §c (27 skills) |  |
| 58 | prismaui | soul-ui | 1.2 | a | 1.2 (working assumption; 1.2 §0 probes it) |  |
| 59 | dear-diary | soul-ui | 1.2 | a | 1.2 paper theme |  |
| 60 | wood-and-paper | soul-ui | 1.2 | a | 1.2 skin of 59 |  |
| 61 | oblivion-loading-menu | soul-ui | 1.2 | a | 1.2 paper loading screen |  |
| 62 | flat-world-map | soul-ui | 2.10 | b | 2.12 (1.2 line 90: "if it carries this; else our own view"); 115 MB | Row chunk "2.10" is stale |
| 63 | no-google-maps | soul-ui | 2.10 | a | 1.4 (no markers) |  |
| 64 | magic-expanded | soul-ui | 2.9 | b | 2.9; the check happens in 1.2 in a scratch lane, optional row | Optional row; not in base |
| 65 | community-shaders | soul-ui | 2.W3 | a | 2.W3 volumetrics and the 0.2 perf bar (the bar is measured on the full stack) | Owner call: deferring it moves 4 and 65 together |
| 66 | tropical-skyrim-sse | land | 2.W1 | a | 0.4 first block, 2.W1 (decision 0028) |  |
| 67 | xanmeer-tileset | land | 0.4 | b | 2.W5 only: 0 layout refs, 0 kit-interior refs with the XanmeerResources prefix; used via plan slug in 2 of 18 slice places (not Claywater) | Low |
| 68 | king-of-the-murkmire | land | 0.4 | a | 0.4: Claywater (1 ref + 3 kotm-house-pod composites); 103 refs/36 assets across 15 of 18 places | Largest non-vanilla supplier after BMV |
| 69 | htbm | land | 0.4 | a | master of 70 (verified in the TES4 header) |  |
| 70 | htbm-cipactli | land | 0.4 | a | 0.4: Claywater 2 refs; 117 refs/18 assets, 12 places |  |
| 71 | mud-mother-grove | land | 0.4 | a | 0.4: Claywater 8 refs; 169 refs/14 assets, 13 places |  |
| 72 | xalfek | land | 0.4 | d | 0 refs anywhere (pool "xalfek" has no asset in layout_place or kit-interiors); plugin already dropped; overlaps 71 and 68 | None |
| 73 | mw-imperial-keep | land | 0.4 | b | 2.W5 wave 2 (Voriplasm Vault: 7 refs/5 assets; 126 interior mentions); meshes only, no records in pieces-index | If KotM.esp needs these meshes for its own records: UNVERIFIED |
| 74 | mw-hlaalu | land | 0.4 | b | 2.W5 wave 2 (Opening Work Camp: 1 ref; 72 interior mentions) |  |
| 75 | drjacopo-grass | land | 2.W1 | d | 0 refs; its meshes are *DrJ.nif names only referenced by the Cathedral plugins, which are not in the stack; Tropical Skyrim.esp points at vanilla grass names (strings) | Low; revisit only if 2.W4 swaps GRAS model paths |
| 76 | seashells | land | 0.4 | b | 2.W5 wave 2 (Pearl Lots: 13 refs/6 scallops and clam); vanilla clam01 already has 14 refs | Could drop to vanilla clams |
| 77 | shores-of-skyrim-cc | land | 0.4 | b | 2.W5 (38 refs/6 assets in Riverwalk, Wamasu Shrine, Chasepoint, Pearl Lots); no plugin laid |  |
| 78 | base-object-swapper | land | 0.4 | d | Requirement of the Shores of Skyrim plugin, which is not laid (row 77 lists no plugin); our REFRs need no swapper | Low |
| 79 | skyrim-ferries | land | 2.8 | a | 0.4: Claywater plank ferry (1 ref); 5 places |  |
| 80 | rowboats | land | 2.8 | b | 2.W5 wave 1 / 2.15 (Riverwalk, 1 ref) |  |
| 81 | cc-ayleid-resources | land | 0.4 | b | 2.W5 (interiors only: 68 mentions, 0 exterior refs) |  |
| 82 | sleeping-hist-tree | land | 0.4 | b | 2.W5 wave 1 (Greenspring; 18 refs/4 places) |  |
| 83 | ships-and-boats-of-tamriel | land | 2.8 | b | 2.W5 wave 2 (Opening Work Camp 1 ref; 11 interior mentions); 207 MB |  |
| 84 | depths-of-skyrim | land | 2.W2 | b | 2.W5 wave 2 (Pearl Lots 16 refs); 2.W2 brief does not name it |  |
| 85 | sirenroot | land | 0.4 | b | 2.W5 interiors (6 mentions); 346 MB; weakest case in this class | Candidate to drop if no interior survives |
| 86 | sailboats-expanded-update | land | 2.8 | a | 0.4: provides canoe1.nif (11/11 canoe registry paths verified in this archive); Claywater 1 ref, 6 places |  |
| 87 | sailboats-expanded | land | 2.8 | b | 2.W5 wave 1 / 2.15 (Lighter Flotilla 3 refs); 2.15 calls it "pattern only" for restrictive terms | Check 2.15 terms before laying |
| 88 | boats-operational | land | 2.8 | d | 0 refs (pool boatsanim); 2.15 does not list it |  |
| 89 | bmv | land | 0.4 | a | 0.4: Claywater 8 refs; 152 refs/24 assets, 14 places; 9.6 GB | See BMV note: 136 of 152 refs are flora |
| 90 | tropical-skyrim-le | pipeline | 0.4 | c | Covered by 66: 869 of 869 registry-tropical mesh paths exist in the SSE archive 78044; pipeline-only, never laid |  |
| 91 | hoddminir | pipeline | 0.4 | d | 0 refs (pool hoddminir); flora is Tropical Skyrim (0028); 352 MB |  |
| 92 | darkwater-den | pipeline | 0.4 | d | 0 refs (pool darkwater); props covered by 71; 76 MB |  |
| 93 | ayleid-building-kit | pipeline | 0.4 | b | 2.W5 wave 1/2 (Wamasu Shrine 1 ref; 86 interior mentions); only source of ArBlock01 |  |
| 94 | script-free-ship-sailing | pipeline | 2.8 | c | Covered by 86: the SSE Script Free Ship Sailing archive holds all 11 registry canoe paths; the LE archive holds 1 nif |  |
| 95 | solitude-ferry | pipeline | 2.8 | a | 0.4: Claywater 1 ref ferryraft01.nif (only source); 4 places |  |
| 96 | cyrodiil-ships | pipeline | 2.8 | d | 0 refs (pool impships); 83 (sbot) is the boat source |  |
| 97 | skylink-ai | dev | 0.3 | d | Already `dropped` in the row (does not load on 1.7.104); the bridge replaced it. Remove the row |  |
| 98 | housecarl | dev | 0.2 | a | 0.2 dev tool |  |