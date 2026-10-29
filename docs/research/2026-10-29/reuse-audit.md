# Build-versus-reuse audit (0.1 §j)

Dated 2026-10-29. Read-only research; nothing here is committed or shipped. Method: sources cloned shallowly and read
(GitHub), Nexus API v1 reads (the `permissions` fields do not exist in that API; see "Permissions" below), GitHub
API reads, web search. Everything not read from source or an API response is marked **UNVERIFIED**.
Source clones live in the session scratchpad only. Per CLAUDE.md "Never", this note carries no retail offsets,
Address Library ids or decompiled code: tes4skyrim's engine addresses are described by technique only.

Runtime pin: Skyrim 1.7.104 (our `SkyrimSE.exe` is 1.7.104.0, SKSE 2.3.1; see `docs/research/2026-10-28/stream-and-combat-stack.md` §2.1)
unless 0.2 G3 says otherwise.

## 0. Headlines

1. **tes4skyrim is not a drop-in for dialogue.** Its dialogue runtime is a real, tested port of OpenMW's filter, keyword
   search, disposition, persuasion and MWScript VM (about 27,700 lines of plugin C++ plus a vendored 204-file OpenMW
   subset). But its input is TES3-shaped text sidecars, its UI half (about 5,100 lines) is welded to a generated
   Morrowind-art SWF, it keeps its own co-save, and its only proof is on 1.6.x builds. Verdict: **fork the model half,
   replace the UI half with our view, port the interception method** (section 1).
2. **tes4skyrim's navmesh generator is not "from collision".** The live generator builds corridor ribbons *on the source
   game's pathgrid* (`if not nodes: return [], []`, `tes5_import/navmesh/build.py:66-67`); the collision-voxel
   generator the README still advertises was deleted. It is not usable on our LAND/REFR data alone. What *is* reusable
   is its NVNM/NAVI/edge-link/door-link binary knowledge and its collision-extraction method (section 1.4).
3. **Licence gaps.** The repo has no `LICENSE` file at its root (GitHub reports no licence); "MIT" is a README sentence
   (`README.md:399-401`). Treat it as source-available until the author adds a file. Per-DLL GPL-3 is documented
   (`tes_runtime/README.md:35-37`, `docs/commentary/morrowind_runtime.md:3814-3836`).
4. **PrismaUI's licence is custom and restrictive** (no public distribution of modified versions; Ultralight terms
   inherited). Depend on it unmodified; never fork it for release (section 3).
5. **Mutagen is GPL-3.0-only with no linking exception** (houseCARL `README.md:273`); our repo's 0015 choice of
   GPL-3.0-or-later is compatible only as "the combination is GPL-3.0". Note it in 0015's register.
6. **SCAR, CPR and Modern Stagger Lock have moved maintainers.** SkyHorizon3 forks are current (2026-10) and **GPL-3.0**;
   the max-su-2019 originals are MIT but stale (2023-2025). PLAN §4 says "SCAR (MIT)"; correct to name which one.
7. **universal-modder holds a Skyrim 1.7.104 field note that matches our route** (generated plugin records for
   dialogue, from Python) (section 5).

## 1. bryantmh/tes4skyrim (read in full: runtime, converter spine, navmesh, LOD, retargeting)

Repo facts. https://github.com/bryantmh/tes4skyrim, default branch `master`, last push 2026-10-13, latest release
tag 0.687 (2026-10-13, no assets; navmesh caches ship as separate prerelease zips), 145 stars, 33 open issues,
created 2026-04-07 (GitHub API). `VERSION` is an unexpanded git-archive placeholder. 213 files under `tes_runtime/`.
Clone read: commit `2abe3ce`. Prebuilt DLLs are committed in `tes_runtime/dist/` (`tes_runtime/README.md:53-57`);
we would build from source, never ship its binaries.
Maturity: pre-alpha; most MorrowindRuntime features are "confirmed in game" for the dialogue window and activation
(`docs/commentary/morrowind_runtime.md:259`, the SWF gate; `:553-606`, interception) but the character sheet, level-up,
chargen menus and attribute features are marked "unconfirmed in game" (`:3837`, `:4047-4516`).

### 1.1 Input shape: what MorrowindRuntime reads, and can our records be compiled into it

**It reads TES3-vocabulary text sidecars, not records.** At `kMessage_DataLoaded` the DLL walks
`Data\SKSE\Plugins\MorrowindRuntime\<plugin>\` and parses `DIAL.txt`, `INFO.txt`, `NPC__index.txt`, `GLOB.txt`,
`FACT.txt`, `GMST.txt`, `SKIL.txt`, `NPC_.txt`, `SCPT_*.txt` and three id-to-FormID maps
(`docs/commentary/morrowind_runtime.md:907-931`; loader `plugin/store.h:109-117`, `plugin/store.cpp`). The format is
KEY=VALUE blocks documented in `docs/reference/morrowind_dialogue_format.md` (topic: `EditorID`, `DialType`;
response: `Topic`, `Disposition`, `Rank`, `PCRank`, `Gender`, `Actor`, `Race`, `Class`, `Faction`, `Cell`, `PCFaction`,
`Response`, `ResultScript` (uncompiled MWScript), `QuestStatus`, `Condition[n].*`; `:42-78`). The in-memory model is
`Info` and `Topic` (`plugin/store.h:39-81`). So **yes, our own dialogue data can be compiled into it**, by a new
ArgoniaGen emitter that writes this text; nothing in the runtime needs TES3 files, only TES3-shaped strings.

**`ActorView` is not a dialogue-record input.** `plugin/actor.h:24-88` is the seam for *world state*: the speaker's id,
race, class, faction and rank, the player's skills, attributes, level, health, crime level, cell name, journal index,
globals and locals, disposition (owned by the DLL, `:46-48`). It has two implementations (the game reader
`plugin/game_actor.cpp` and test literals). It answers "what is true about this NPC and the player", so it is the place our
condition vocabulary's *predicates* would be answered, not where records enter.

What compiling our records would mean, row by row against our needs:

| Our need | Fit | Evidence and caveat |
|---|---|---|
| Topics, ordered first-match answers | Exact fit | Order is semantic (`Ordinal`/`Prev`); `OrderTopic` applies OpenMW's InfoOrder per plugin layer (`store.h:86-90`; `filter.h:35-40`) |
| Hyperlinked keywords, learned topics | Exact fit | OpenMW `KeywordSearch` is vendored, run over every visible dialogue after the result script (`session.h:59-63`; `morrowind_runtime.md:201-230`) |
| Disposition 0-100 | Exact fit | Owned by the DLL: `DialogueState::Disposition/SetDisposition/ModDisposition` (`dialogue_state.h:440-443`); INFO threshold in `Info.disposition` (`store.h:50`); base value saved in the co-save, temporary persuasion change folded in on goodbye (`morrowind_runtime.md:2853-2864`, `:2901-2921`) |
| Persuasion (admire, intimidate, taunt, bribe) | Exact fit | `persuasion.cpp:1-40`; OpenMW's formulas "ported line for line" with the dice roll injected for headless tests (`morrowind_runtime.md:2901-2910`). Uses GMSTs and Speechcraft/Personality/Luck, which our stats must answer through `ActorView::PlayerSkill/PlayerAttribute` |
| Barter, enchanting, travel services | Uses Skyrim menus, partially | Barter opens Skyrim's menu after a Service Refusal check (`:2922-2944`); the per-trade disposition change is not applied (`:2938-2939`); travel is OpenMW's TravelWindow (`:3006-3050`) |
| Conditions from our condition vocabulary | **Partial; the hard part** | The filter knows 74 TES3 numbered functions (`filter.h:58-80`) plus global (`'2'`), local (`'3'`/`'C'`), journal (`'4'`), item (`'5'`), dead (`'6'`) and the not-id/faction/class/race/cell forms (`filter.cpp:50-73, 216-260`). A condition with no TES3 equivalent must be expressed as a **global, local or journal index** that our code publishes; an unanswerable numbered function **rejects** the line (`filter.cpp:219-224`; the older table row at `morrowind_runtime.md:184` saying "passes" is stale). Missing global: filter passes; missing local: rejects (`:182-183`) |
| Evidence-gated topics (0024) | Feasible only via published state | Express each evidence predicate as a global the evaluator writes, or a journal index per clue; the DLL already mirrors globals and journal state into Skyrim GLOBs each tick for engine-evaluated barks (`morrowind_runtime.md:2011-2030`). Our evaluator (G10) would feed `GlobalVariable`/`JournalIndex` |
| Result actions | MWScript, not our actions | `Info.resultScript` is MWScript run by the vendored OpenMW compiler/VM against ~458 hand-ported opcode handlers (`morrowind_runtime.md:30-41`, `:1127`). We would either emit MWScript text from our records (a second language to keep right) or keep results out and let ArgoniaCore act on topic events |
| Our identifiers | Adapter needed | Everything is a case-insensitive TES3 string id (`actor.h:19`); routing is by FormID's load-order index bit plus an `NPC__index.txt` FormID=EditorID map written at import (`morrowind_runtime.md:484-551`, `plugin/activation.cpp:31-45`). Minted ids and per-plugin sidecar folders, with a folder skipped whole if its plugin is not loaded (`:529-542`) |
| State and co-save | **Conflicts with our rule** | It owns an SKSE co-save record (`MWRT`/`MWST`, `morrowind_runtime.md:2853-2859`). CLAUDE.md says new state lives in ArgoniaCore's versioned families; adopting the runtime splits state in two |

**Verdict, dialogue model: fork** (model half only: `store`, `filter`, `session`, `dialogue_state`, `persuasion`, `scope`,
about 6,500 lines, plus the vendored OpenMW closure; GPL-3, fits 0015). **Not a dependency**: it is pre-alpha, 1.6.x-proven,
its co-save and TES3-id model are not ours, and 0.1 §j's own sentence ("fork it or depend on it") is answered by "fork,
with the sidecar emitter as our adapter". The cheaper alternative, if G5 shows the sidecar emitter is the cost: keep
ArgoniaCore's own small store and take **only the method** (the filter's first-match, prefix-cell, choice-gating
semantics; OpenMW's disposition and persuasion formulas, which are in OpenMW's own source anyway).

### 1.2 Menu interception: how it works (a vtable swap, and why the dialogue menu is the wrong hook)

- It does **not** hook Skyrim's DialogueMenu. The first attempt sank the menu-open event; it cannot work because a
  converted Morrowind NPC has no Skyrim dialogue, so that menu never opens (`morrowind_runtime.md:553-561`).
- The real entry is **NPC activation**. The activation function cannot be detoured (its prologue is refused by the
  detour analyser), so the runtime **swaps one virtual slot** on each activatable base-form type's vtable, which
  fires on every activation of that type. A vtable swap steals no prologue bytes (`:568-602`; code
  `plugin/activation.cpp:486-514`, slot constants and the nine target types at `plugin/ids.h:196-239`). The install
  **refuses to swap a slot that does not hold the expected original function** (`:601`), a guard worth copying.
- Routing is one bit test on the FormID's load-order index byte, then a hash lookup of the base form's local id;
  returning true without calling the original suppresses Skyrim's own activation (`:484-506`).
- It opens its own window by **registering a new IMenu name with the menu manager** and posting an Open UIMessage
  with an interned `BSFixedString` name; the menu object must come from the Scaleform heap, must render itself
  (a Render slot call), and open/close arrive as messages, not constructor/destructor (`:604-905`; the generic
  class is `plugin/menu.h:44-125`). These notes are exactly what G5 and G11 would otherwise research; all are
  1.6.x-derived (UNVERIFIED on 1.7.104).
- **Reuse as method:** take the activation vtable swap and the custom-menu lifecycle notes. For our view we would not
  need a custom `IMenu` at all if PrismaUI hosts the window (G11): only the activation intercept, then a JSON message
  to the view.

### 1.3 Can the SWF menu be replaced by our own view

**Yes, with a cut, not a plug-in point.** Evidence:

- The model half has no Skyrim or UI types: `plugin/session.h:3-4` ("It holds no Skyrim types, so the whole of it is
  testable headless"). Its API is small and view-shaped: `OfferedTopics`, `Greet`, `Answer`, `MentionedTopics`,
  `ServiceRefusal` (`session.h:37-63`).
- The view half is not abstracted. The SWF carries **no ActionScript**; `conversation.cpp` (989 lines) resolves clicks
  against rects, field paths and font advances in a *generated* header `plugin/menu_layout.h` that comes from the
  Morrowind art (`conversation.h:1-9`; `menu_layout.h:1-4`; `morrowind_runtime.md:1021-1040`). Keyword hit-testing is the
  plugin's own word-wrap over the font's advances because Scaleform lacks `getCharIndexAtPoint` (`:1111-1125`). The
  UI-side files (menu, conversation*, widgets, chargen, level-up, stats sheet) total about 5,100 lines.
- The art is built on the player's machine from their Morrowind install and is never committed
  (`morrowind_runtime.md:374-395`); we would not ship it and do not need it.
- A replacement view therefore means: keep `BeginConversation`'s caller contract (`conversation.h:20`), drop
  `menu.cpp`/`conversation.cpp` and the SWF generator, and expose the session as messages: topics (id, isNew), history
  with keyword spans (from `MentionedTopics`), disposition, the persuasion list, a goodbye event; the view sends
  topic-click, persuade and goodbye. **Unknown:** whether the result-script runner's `MessageBox`/`Choice` calls and the
  Travel/Persuasion modals (`conversation_modal.cpp`, `conversation_travel.cpp`) can be re-fronted without rewriting
  (UNVERIFIED; they share one modal in `morrowind_runtime.md:3074`).
- The character sheet, level-up and class/birthsign menus are Morrowind-attribute features (`:3837-4646`, off unless
  enabled `README`); we need none of them (our stats are ArgoniaCore's, 1.3).

**Verdict, UI half: build** (our PrismaUI view, G11); **port the method** for the keyword hit-testing and the
disposition/persuasion layout rules (read from OpenMW's own `DialogueWindow`, as the code does).

### 1.4 Runtimes built for, and whether 1.7.104 is plausible

- **No CommonLibSSE-NG, no SKSE source tree, no CMake.** MSVC x64 via `build.bat`; the SKSE ABI is hand-declared
  (`tes_runtime/common/skse_abi.h:161-177`) and everything from the game resolves at run time through the Address
  Library (`tes_runtime/README.md:53-57`; `morrowind/build.bat:1-80`). The Windows-only MSVC build is the only build.
- The version struct declares Address-Library, signature and post-629-struct independence with an empty
  compatible-versions list (`morrowind/plugin/plugin.cpp:117-130`), i.e. it will be offered to any AE runtime.
- The loader reads Address Library formats for 1.5, 1.6 and **1.7.x (flat u32 format 5)**
  (`common/addresses.cpp:127-150, 113-120, 182-202`; `docs/reference/address_library_formats.md:15`), and
  the repo's identity check resolves its 62 Papyrus natives correctly on **1.7.104** (0 wrong), whereas the same ids
  are all wrong on 1.5.97 (`address_library_formats.md:185-199`). The repo has 1.7.104 unpacked exes and some
  1.7.104-specific data (`CLAUDE.md:208`; `plugin/ids.h:722`).
- Pre-AE (1.5.97, VR) runs **only** the character-sheet/skills features, not dialogue or activation
  (`morrowind_runtime.md:4452-4478`). The documented dev target is "1.6.1170, the build the user plays"
  (`CLAUDE.md:204-207`).
- **Plausible, not proven, on 1.7.104:** ids resolve; but struct offsets, the `IMenu` layout, Scaleform vtable indices
  and the activation slot were verified by disassembly on 1.6.659/1.6.1170 (`morrowind_runtime.md:645-683, 568-602`).
  Whether they are unchanged in 1.7.x is **UNVERIFIED**. The slot guard means a mismatch fails closed (no
  interception) rather than crashing. A 1.7.104 smoke test (open one conversation) is the 0.2 G5 gate.
- If our pin is 1.7.104, the work to keep a fork alive is re-deriving those offsets with the Ghidra scalpel (0010 §4),
  or avoiding the custom IMenu entirely (our PrismaUI view; only the activation hook remains).

### 1.5 Navmesh generation, standalone on our own LAND/REFR data

**No, not as it stands.** The README sells collision voxelisation with "the original pathgrid as a guide"
(`README.md:49`), but the live code path is the pathgrid corridor generator:

- `build_navmesh(refr_recs, base_model_by_fid, get_collision, nodes, edges, land_rec, ...)` returns nothing when
  `nodes` is empty (`tes5_import/navmesh/build.py:54-82`). Its default is "THE PATHGRID IS THE MESH": a fixed-width
  ribbon on every pathgrid edge, unioned per walkable surface (`corridor.py:1-45`). The voxel, region and spanmesh
  generators were **deleted from master** (Recast-era code lives on branch `test-navmesh-2`)
  (`docs/commentary/tes5_import_navmesh.md:2573-2590`, `:2623-2660`).
- An experimental "lattice" generator meshes "every floor within walking reach" of the pathgrid from collision columns
  (`lattice/build.py:1-6`); still seeded by the pathgrid.
- The result is deliberately sparse: "a corridor an actor can follow, not a room-filling floor" (`corridor.py:25-28`).
- Inputs it does need, and which we have an analogue for: REFR dicts (position, rotation, scale, XTEL door flag), a
  base-model-to-mesh map, a `get_collision` callable, decoded LAND heights (`world.py:75-160`), and door REFRs.
  **Collision comes from the converted Skyrim NIFs' `bhkCompressedMeshShape`**, decoded by `asset_convert/collision/cms.py`
  and split into walkable (|nz| >= cos 46 degrees) and blocking triangles (`asset_convert/collision/collision_extract.py:1-40`).
  Our placed pieces are Skyrim-format NIFs (Tropical Skyrim, BM&V after our conversion), so the extraction method applies.
- Packaging facts: Python 3.14, one prebuilt 64-bit `.pyd` kernel committed and imported unconditionally
  (`native/dist/README.md:20-25`, source `native/src/navgrow/grow.cpp`, 1,030 lines); input keys are the exporter's TES4
  KEY=VALUE dicts. Generation is the slow step (their cache cut Nehrim from 192 s to 3.8 s, `navmesh_cache/README.md`).
  It would not drop into our Mutagen-based, Linux-run tooling without a port.
- **What is genuinely reusable as method (read-only spec, verified against vanilla by the author):**
  NVNM packing (`from_pgrd.py:635-760`, "validated byte-exact against Skyrim.esm", `build.py:10-13`); NAVI/NVMI layout
  and the rule that a NAVM not indexed in NAVI is ignored (`navi.py:1-30`); the 10-byte edge-link record, reciprocity and
  portal/ledge types (`edge_links.py:1-25`); door-triangle reservation and XNDP (`tes5_import_navmesh.md:179-290,
  418-460`); the 64 KB XXXX size protocol (`:2163`). These answer 2.W4 §b's open question "does NAVI need every navmesh
  listed" (their answer: yes, mandatory, `navi.py:3-6`).
- The CK-generator analysis (`docs/commentary/ck_navmesh_generation.md`) reads CreationKit.exe strings and compiled-in
  defaults (three generators: Recast, Bethesda's own pass pipeline, legacy). Useful as a pointer to Recast parameters
  for our DotRecast config; its addresses are retail offsets and stay out of our repo.

**Verdict, navmesh: build** (DotRecast over our own collision, Mutagen writing NAVM/NAVI) **and port the method** of
NVNM/NAVI/edge-link/door-link from tes4skyrim as the binary spec. Its "round-trip through Mutagen first" step in 0026 §4
remains the right first test. Not a dependency; not a fork.

### 1.6 The rest of the converter, and what is reusable

| Part | What it is | Verdict | Evidence |
|---|---|---|---|
| `tes5_import/` record writer | Own Python ESM writer with a "derived FormID region" scheme (ids hashed from source records into the emptiest run per plugin) | port the method (we use Mutagen) | `tes5_import/base/writer.py:1-50` |
| LOD driving | Writes `LODSettings/<WRLD>.lod`, scans the ESM, calls xEdit's `LODGenx64.exe` (3.0.36.0; 2.2.0.0 let one bad model kill the process), cover-grid math for the settings | port the method (our xLODGen under Wine) | `asset_convert/lod/lod_gen.py:1-60`; README table (`README.md:405`) lists the xEdit binary as redistributed under MPL-2.0/GPL-2.0, which we do not do (0014) |
| `skyb_retarget/` | One-creature tool: fit Oblivion skeleton onto a Skyblivion mesh, retarget `.kf` clips via foot-path IK, rebuild ragdoll; hard-coded for one creature | port the method only; its README says "to be vendored off" | `skyb_retarget/README.md:1-27, 69-120`. Relevant to G9 only for FABRIK/joint-position retarget and ragdoll constraint re-seating. Input skeleton is Oblivion's `Bip01`; ours is Skyrim humanoid |
| `tes_runtime/tes/` | Jails (nearest prison), quest journal stage text and objectives, alchemy apparatus (GPL: ports OpenMW `applyTools`) | method only | `tes_runtime/README.md:17-21`; `morrowind_runtime.md:3814-3836`. Skyrim already has jails/crime factions (0026 §2) |
| `tes_runtime/creature/`, `havok_world_size/` | Creature animation compose; physics for huge worldspaces | `havok_world_size`: re-check when 2.W1 sizes the world (126x126 cells); `creature`: n/a | `tes_runtime/README.md:17-21` |
| Papyrus compiler route | Ships russo-2025 `papyrus-compiler` (MIT) | use as dependency candidate (MIT, redistributable) | `README.md:410`; the Linux Papyrus compile route is a 0.1/0.3 question UNVERIFIED |
| Co-save/idiom notes | "never classify by file name", route by load-order index byte, root path from the game exe not the DLL (MO2) | method | `morrowind_runtime.md:484-551, 994-1019` |

Licence summary: own code "MIT" by README (no LICENSE file); `external/` carries its own (OpenMW GPL-3.0; xEdit
binaries MPL/GPL; hkxcmd BSD-3 but statically links Havok; DovahNifWorkbench bridge has no licence and statically
links Havok; hkxconv no licence). Do not redistribute `external/` anything (`README.md:395-445`; 0003, 0014).

### 1.7 What in it is a dependency, a fork, or method only

- **Dependency:** none. (Nothing is packaged for reuse; DLLs are monolithic, TES3-tied, pre-alpha, 1.6.x-proven.)
- **Fork (GPL-3, our 0015 matches):** MorrowindRuntime's model half and the vendored OpenMW closure, if G5 shows the
  sidecar adapter is cheaper than our own store (plus a 1.7.104 smoke test).
- **Method only:** activation vtable-swap-with-guard; custom IMenu lifecycle notes; the filter's semantics (first match,
  prefix cell, choice gating, name-compared ids); NVNM/NAVI/edge-link/door-link binary spec; the collision-extraction
  split; the LOD settings and cover-grid recipe; the retarget fitting ideas.
- **Not reusable:** the SWF generator and Morrowind art path; character-sheet/chargen menus; MWScript object-script
  runtime (unless we adopt TES3-style scripted objects, which 0026 rules out); the Python 3.14 converter spine.

## 2. Authoring and data tools

| Component (PLAN row) | Candidate | Verdict | Licence | Runtime | Maturity | Evidence |
|---|---|---|---|---|---|---|
| Plugin writer, record models (terrain, places, NPCs, quests, NAVM; PLAN "Worldspace terrain", "Places", "NPCs", "Quests as data") | **Mutagen** (Mutagen-Modding/Mutagen) | use as dependency (ArgoniaGen links it) | **GPL-3.0-only, no linking exception** | writes SSE plugins; version-independent of the exe (file format) | v0.54.4 released 2026-08-08, pushed 2026-10-26, 180 stars | GitHub API; houseCARL `README.md:273` states "GPL-3.0-only, no linking exception"; record coverage: `docs/research/2026-10-28/prior-art-world-to-skyrim.md` row for Mutagen |
| Plugin to text for review (`plugin/` Spriggit YAML) | **Spriggit** (Mutagen-Modding/Spriggit) | use as dependency (CLI, review artifact) | GPL-3.0 | n/a | v0.41.0 2026-07-02, pushed 2026-07-10; has a Linux solution file (`Spriggit.Linux.slnx`) | clone read, `LICENSE`; GitHub API. Note: a StarkMP fork exists (UNVERIFIED relevance) |
| Navmesh from our collision (PLAN "Navmesh") | **DotRecast** (ikpil/DotRecast), C# port of Recast/Detour | use as dependency inside the navmesh job (or port method) | zlib | pure C#, no game runtime | release 2026.3.1 2026-08-02, pushed 2026-10-03, 960 stars | clone `LICENSE.txt`; GitHub API. It produces polygons, not NAVM; triangulation, adjacency, edge links, doors are ours (1.5 above gives the spec) |
| Agent bridge base, dev-only (PLAN "The studio, scenes, the two runners") | **SkyLink AI** (Nexus 175682; GitHub jarvann/SkryimMCM) | port the method (our ArgoniaBridge keeps its shape: named-pipe SKSE plugin + out-of-process MCP server); do not depend | README says MIT, **no LICENSE file in repo**; CommonLibSSE-NG | Page: SE/AE "1.5.97 / 1.6.x"; plugin declares Address-Library independence (`SkyrimMCPPlugin/src/Main.cpp:55`); **fails on 1.7.104** (0.2, 2026-10-29: its log says "failed to open address library file"; its CommonLib predates Address Library format 5, and the modal blocks start-up; dropped from the dev set, ArgoniaBridge takes its reads); built Mar 2026 on an older CommonLib-NG | v1.0, 2026-03-27, 502 downloads, 74 tools, ~4,400 lines C++ plugin + .NET 10 server | clone read: `SkyrimMCPPlugin/src/PipeServer.h`, `SkyrimMCP/Tools/*.cs`; Nexus API |
| Plugin and load-order inspection for agents | **houseCARL** (Nexus 181738; Avick3110/houseCARL) | use as dependency for agents (dev tool, not shipped); also a **reference** for Mutagen-based read tools | GPL-3.0 (own README says GPL-3.0-only because it bundles Mutagen) | reads files, no game runtime; Mutagen 0.54.4, .NET 10 | v2.1.1 released 2026-10-22, last commit today (2026-10-29), 50 stars, 31 tools, 7 skills | clone `README.md:271-273`; GitHub API; Nexus API. Overlap with our `world/` import and the sourcing register: use it for conflict/override queries during Part 0 |
| Generated dialogue/quest records from Python (PLAN "Writing quests", "Dialogue") | universal-modder field note "Rebuilding a cut gatekeeper with generated plugin records" | port the method | MIT (repo) | Skyrim 1.7.104, CK 1.7.99, no SKSE | 2026-10-24 | `knowledge/games/skyrim-special-edition/rebuilding-a-cut-gatekeeper-with-generated-plugin-records-di.md:1-40`; 261 lines of gotchas (e.g. exclusive branches and quest priority, gotcha 19) |

## 3. UI frameworks and skins

| Component | Candidate | Verdict | Licence / permissions | Runtime | Maturity | Evidence |
|---|---|---|---|---|---|---|
| Our UI and HUD, studio, dialogue view (PLAN "Our own UI", "The studio") | **PrismaUI** (Nexus 148718; PrismaUI-SKSE/framework) | use as dependency (pinned), never fork for release | **Custom "Prisma UI License"**: free use, non-commercial or commercial under US$100k revenue and US$100k funding, source viewable; **modified versions may not be publicly distributed without the author's written permission** (3.2); unmodified redistribution allowed with the licence file (2.4); inherits Ultralight's free licence (no reverse engineering, Pro licence above the limits) | CommonLibSSE-NG plugin; page says "NG: SE yes AE yes VR yes"; 1.7.104 **UNVERIFIED** (release 1.5.1 postdates the 1.7.99 build, but the notes do not say) | 1.5.1 released 2026-09-19 (GitHub), Nexus main file 2026-09-20; 239k downloads; API header file published | clone `LICENSE.md:1-45`, `CMakeLists.txt:44-45`; GitHub releases; Nexus API. 0015 ("forks need its author's permission") stands. Our GPL-3 code calls it only through its published API |
| Quest journal and book menu | **Dear Diary - Paper SkyUI Menus Replacer SE** (Nexus 23010, uranreactor) | method only (art and layout reference for a paper style); do not depend for our own view | **UNKNOWN**: the Nexus API has no permission fields and the description states none; it does say others may reskin it (links a manual, lists dozens of community skins) and credits SureAI's loadingmenu.swf "used with permission" | **Requires SkyUI 5.2SE**; 3.0.6 (2021-10-31) with patches for 1.6+ and 1.6.1130+; no 1.7 statement | 3.0.6 of 2021; 1.87M downloads | Nexus API description and file list (files "Paper Journal", "Paper MCM", favorites, inventory, "AIO" FOMOD choosing which menus). It is an **SWF replacer for SkyUI's menus** ("almost all SkyUI menus", plus the Book menu per the "No Magnifying Glass for book menu" add-on it lists); quest journal covered by the Journal files |
| Skin | **Wood and Paper - Dear Diary Skin** (44174) | method only | UNKNOWN permissions | needs SkyUI 5.2SE and Dear Diary 3.0+ | 1.0.2, 2021-06-20 | Nexus API |
| Loading menu | **Oblivion-like Loading Menu SE** (38708) | method only (a loading-screen paper style; ESL patches, "all plugins ESP-FE") | UNKNOWN permissions; reuses SureAI's SWF "with permission" | not stated; SWF plus ESPs | 1.0, 2020-07-27 | Nexus API |
| Menus, SkyUI (PLAN "Main menu...", "UI") | **SkyUI 6** (Nexus 12604) | use as dependency (MCM host, Papyrus UI; page lists 1.5.97/1.6.1170/1179, "verify the MCM opens" on 1.7.104) | Source on GitHub (schlangster/skyui) with **no licence file** (GitHub: none): source-visible, not open-licensed; UNVERIFIED permissions | SWF/Papyrus only, no DLL; works because no exe coupling | Nexus lists 6.9 (2026-05-05); our stack file is 6.11 | `docs/research/2026-10-28/stream-and-combat-stack.md:227-230`; Nexus API; `gh api repos/schlangster/skyui` |
| Menus | **Infinity UI** (SWF loader from a preset folder per its page) | do not depend; revisit only if a menu needs an SWF swap | UNVERIFIED | UNVERIFIED; comments report CTD risk on older setups | UNVERIFIED | web search summary only; Nexus mod id not resolved |

Permissions note: the API's `GET /mods/{id}.json` returns no permission or licence fields at all (fields seen: name,
summary, description, version, timestamps, author, endorsement). The page-level "permissions" box is only in the Nexus
HTML (403 for us). Every "UNKNOWN" above should be asked of the author or read by the owner in a browser before any reuse
beyond depending on the mod as a player-downloaded file.

## 4. Gameplay mods and frameworks

Licence column: what the source or page states; "source-visible" means readable but no licence grant.

| Component (PLAN row) | Candidate | Verdict | Licence | Runtime (1.7.104 unless noted) | Maturity | Evidence |
|---|---|---|---|---|---|---|
| Attributes, 27 skills (PLAN "Attributes, 27 skills, formulas") | **Custom Skills Framework** (Nexus 41780; Exit-9B/CustomSkills) | use as dependency | MIT (`LICENSE`, (c) 2023 Parapets) | 3.2.0 "Updated for SkyrimSE 1.7.99 and Address Library 12"; separate 3.2.0 file for 1.5.97; 1.7.104 **UNVERIFIED** (Nexus main file 2026-09-03) | 3.2.0 released 2026-09-02 (GitHub), Nexus updated 2026-10-02, 4.56M downloads, CommonLibSSE plugin, Papyrus API v4 | clone `LICENSE`; `gh release view v3.2.0`; Nexus files API. Skills are global-variable based, not actor values: matches 1.3's need for "unlimited" skills but not the AV-based formulas (G10 decides) |
| Skill use, the sitting (PLAN "Skill use...") | **Sleep to Gain Experience** (Nexus 17791, Zebrina) + CommonLib source (max-su-2019/SleepToGainExperience-Commonlib) | port the method (saved XP in the co-save, paid on sleep); do not depend | Original: UNKNOWN; port repo MIT (GitHub API; last push 2021-02-07) | 1.1.2 of 2023-06-09 "version independent" via Address Library; 1.7.104 **UNVERIFIED** | old, stable, 28.6k downloads | Nexus description: "Source Code ... SleepToGainExperience-Commonlib", "saved experience is stored in the SKSE co-save". Our ArgoniaCore co-save family replaces it (1.5) |
| Death pile, wake at last rest (PLAN "Death pile...") | **Respawn - Soulslike Edition** (Nexus 69267) | port the method (a pattern: respawn at a safe place, drop to a grave, reclaim) | UNKNOWN: "modification of Respawn - Death Overhaul by watang, uploaded with permission" | ESP + Papyrus, no DLL, so no exe coupling; last update 2022-07-16 (1.5) | 400k downloads, stale | Nexus description. Papyrus-only logic is against our "logic stays out of Papyrus" rule (CLAUDE.md), so method only |
| Journal, directions (PLAN "Journal, directions, no markers") | **Wayfinder** (Nexus 121765, csbx) | port the method (marker added only on arrival; directions into a notebook) | UNKNOWN | ESP + Papyrus; 2.0.15 of 2025-05-23; fomod patches for quest mods | 2.7k downloads; soft requirement EBQO | Nexus description. It edits vanilla quests, which 0012 quarantines |
| Same | **No Google Maps Skyrim** (Nexus 147105, SkyHorizon; SkyHorizon3/SSE-No-Google-Maps-Skyrim) | use as dependency (candidate), or fork | **GPL-3.0** (`LICENSE`) | page: SE 1.5.97, AE 1.6.640, 1.6.1130+, **1.7.99+**; 1.7.104 **UNVERIFIED** but claimed by "1.7.99+" | 0.4.0, 2026-10-12, pushed 2026-10-05, 7.3k downloads; CommonLib-NG | clone `LICENSE`, `README.md`; Nexus description. It removes the player marker and gates quest markers by distance, which is the "no markers" goal |
| World map (PLAN "World map, local map") | **Flat World Map Framework** (Nexus 29932, Caites and shad0wshayd3) + Flat Map Markers SSE (22122) | use as dependency | UNKNOWN permissions; the FOMOD bundles a GPLv3 add-on "with author's permission" | 1.9.990, 2026-08-23; page lists 1.5.97, 1.6.x, **1.7.99**; Flat Map Markers is a 2020 plugin (1.3.0) | maintained | Nexus description. Our own map image (the lod job) feeds it; the framework is "a texture map plus marker config" per its page |
| Magic (PLAN "Magic") | **Magic Expanded: Morrowind, Oblivion, Shout and New Spells** (Nexus 133435, Destructor36) | use as dependency (candidate) or port the method for Mark/Recall, Hoptoad, Slowfall effects | UNKNOWN | ESL-flagged ESP + SKSE; 5.1 of 2026-08-11. Requires SKSE; recommends SkyUI (MCM); optional SPID, PowerOfThree's Papyrus Extender and Tweaks, Address Library; so no DLL of its own | 1.5k downloads | Nexus description "Requirements" and "Flagged as ESL". Morrowind intervention/mark/recall already exist as a runtime effect set in MorrowindRuntime too (`morrowind_runtime.md:3311-3470`; GPL, method only) |
| Climbing (PLAN "Climbing, ladders") | **FreeClimb** (Nexus 193552, Epsilona11; GitHub Eelta/FreeClimb) | use as dependency; fork only if the rule tuning needs code (GPL-3.0-only, compatible with 0015) | **GPL-3.0-only** with CommonLibSSE-NG's linking exception; menu API LGPL-2.1; third-party animation and audio licences in `THIRD-PARTY-NOTICES.txt` (Mixamo and others: **check before any redistribution of its animations**) | README lists **1.7.99.0 and 1.7.104.0** explicitly, SKSE 2.3.1 (`README.md:19-24`); "multiruntime" DLL | 0.5.0, 2026-10-10, 21.6k downloads | clone `README.md:19-26, 145, 169`, `LICENSE`. Needs its 99-track HKX format; converter in repo (`README.md:112`). Whether the same author on Nexus and GitHub is **UNVERIFIED** (author names differ) |
| Swimming, diving, breath (PLAN "Swimming...") | **Underwater NG** | use as dependency (candidate) | UNVERIFIED (main page not retrievable; no GitHub repo located) | A Nexus compatibility article (articles/12345) says v1.0.1.4 was tested on **1.7.104.0**, SKSE 2.3.1, Address Library v13, and lists 1.5.97, 1.6.x, 1.7.99, 1.7.104 | 1.0.1.4 (date UNVERIFIED) | web search of the article only. Has a Diving skill UI needing SKSE Menu Framework; "leaves underwater combat to Skyrim". Oxygen Meter (Nexus 57452, powerofthree, 1.4.0 2026-08-28) is the fallback for a breath meter |
| Boats (PLAN "Boats") | **Sailable Ship(s)** (Nexus 72070, ziher "Sailable Ship VR and SE") | fork/modify with credit only after permission is read; otherwise build | UNKNOWN | ESP + Papyrus, "fairly script heavy"; 1.12 of 2023-12-06 | 72070 is the main SE one | Nexus API. Rowboats (CC BY-SA) and Sailboats were **not read** this session: UNVERIFIED |
| Thrown (PLAN "Ranged ... thrown") | **Throwable Weapons SKSE**; Throwable Items (THIT, 44627) | use as dependency; both are DLL or Papyrus | GitHub `tomnGithub/ThrowableWeaponsSKSE` GPL-3.0 (last push 2026-09-15; that this is the Nexus mod is **UNVERIFIED**); THIT UNKNOWN | the NPC add-on (Nexus 185102, 1.2, 2026-09-10) states it needs "Throwable Weapons SKSE" and mentions 1.7.104+ | active | GitHub API; Nexus description |

### 4.1 The combat stack already in use (one line each)

Versions and runtime status are from `docs/research/2026-10-28/stream-and-combat-stack.md:228-262`. Licences from GitHub
(`gh api`) unless marked.

- **SkySA** (Nexus 31390, v1.9.4, 2021): animation/behaviour only plus an ESP, no DLL, **no source or licence stated** (UNKNOWN); reads need AMR, DAR/OAR, Pandora.
- **Precision** (72347, 2.0.6, 2026-09-01): GPL-3.0 (`ersh1/Precision`), source available; "support runtime 1.7.99+". (Older MIT `max-su-2019/Precision` is a different fork.)
- **True Directional Movement** (51614, 2.3.1) and **TrueHUD** (62775, 1.1.10): GPL-3.0 (`ersh1/...`), source available, 1.7.x supported per the stack doc. Both carry the "modding exception" per 0010 §2.
- **TK Dodge RE** (56956) and its 1.7.99+ add-on **TK Dodge RE Addon** (125238, 3.3.0, 2026-09-04): original repo `max-su-2019/TK_Dodge_RE` is MIT (pushed 2023); the add-on's source and licence are **UNVERIFIED**. DMCO's DLL does not load on 1.7.x; **Dodge Framework NG** (195352, Apache-2.0 per the stack doc) replaces it.
- **Elden Parry** (D7ry; the doodlum fork is GPL-3.0, last push 2026-08-24; D7ry's original has no licence file, last push 2022): source available; runtime status on 1.7.104 **UNVERIFIED** here.
- **Rim Parry and Execution** (114366): source and licence **UNVERIFIED**; its page needs Behavior Data Injector plus Payload and is built on Elden Rim - Weapon Arts (search snippets). Pandora-order sensitive per comments.
- **One Click Power Attack NG** (jarari; `jarari/OneClickPowerAttack`, no licence file, last push 2023-03; the 1.7.104 build is an unofficial rebuild `DeadOnKeyboard1/OneClickPowerAttack_1.12.3_AE_1.7.104.0-Update`, Apache-2.0, 2026-09-14): **source available; provenance of the 1.7.104 build needs a note in the sourcing register** (0003 says nothing shipped that players do not own: we only depend on it as a player download).
- **Modern Stagger Lock**: `SkyHorizon3/ModernStaggerLock` MIT, pushed 2026-10-27 (original `max-su-2019/ModernStaggerLock` MIT, 2025-04); a third-party 1.7.104 rebuild exists (GPL-3.0, 2026-09-17).
- **MaxsuBlockOverhaul**: `max-su-2019/MaxuBlockOverhaul` is MIT but holds only behaviour/animation assets (no plugin source in the tree), last commit 2025-02-16; plugin source **UNVERIFIED**.
- **Open Animation Replacer** (92109), **AMR** (191697 1.7.104 update), **Payload Interpreter** (192679, DLL only): OAR is GPL-3.0 (`ersh1/OpenAnimationReplacer`, pushed 2026-08-31); Payload Interpreter source is MIT (`max-su-2019/PayloadInterpreter`, 2022; the 1.7.104 build's source UNVERIFIED).

### 4.2 BFCO, SCAR, CPR, Community Shaders

- **BFCO** (Nexus 117052, 3.100.11, 2026-09-20; 1.7.104 supported since 3.100.8 per the stack doc): `max-su-2019/BFCO` has **no licence file** (last push 2024-06); a combat-system/animation-framework with its own movesets; PLAN lists it as a combat-map option (1.4).
- **SCAR** (combo AI; Nexus 72014 SSE, 77285 AE): `max-su-2019/SCAR` MIT (2024-06) and the current fork `SkyHorizon3/SCAR` **GPL-3.0** (pushed 2026-10-17); clone read: CommonLibSSE-NG plugin with a Nemesis behaviour part and BehaviorDataInjector. PLAN says "(MIT)": correct to name which.
- **CPR** (Combat Pathing Revolution; Nexus 86950): `max-su-2019/CombatPathingRevolution` MIT (2023-09) and `SkyHorizon3/CombatPathingRevolution` **GPL-3.0** (pushed 2026-10-12).
- **Community Shaders** (`community-shaders/skyrim-community-shaders`): GPL-3.0, release v1.9.1 on 2026-09-24, pushed 2026-10-29, 1,139 stars; runtime status on 1.7.104 **UNVERIFIED** (release notes read did not state it). Feature modules are the way 2.W3 gets volumetrics and sun shafts.
- **Also found:** Tsptds `SkyParkour NG` (GitHub licence "NOASSERTION", 2026-08-25) and `SkyClimb-1170`: PLAN lists SkyParkour; its licence is unclear (UNVERIFIED), so treat as dependency-only.

## 5. universal-modder (rehan-remade/universal-modder)

MIT (`LICENSE`: (c) 2026 Rehan and universal-modder contributors); 9,181 stars; last commit 2026-10-27, pushed
2026-10-29; no releases. Clone read at the repo root.

**Skills (13)**, `skills/<name>/SKILL.md`: `asset-pipeline`, `blitz3d-decomp`, `fal-assets`, `game-automation`, `game-recon`,
`game-research-websearch`, `mashup-mods`, `mod-any-game`, `port-a-mod`, `publish-mod`, `reverse-engineering`,
`share-field-notes`, `showcase-video`. Agents: `agents/mod-game-worker.md`, `mod-offline-worker.md`, `mod-orchestrator.md`.
Also `knowledge/` (88 technique notes plus per-game notes) and the `um` CLI.

**The Bethesda playbook** is `skills/mod-any-game/references/engines/bethesda.md` (46 lines; mirrored under `.claude/` and
`.agents/` `skills/mod-any-game/references/engines/bethesda.md`). Relevant companions:
- `knowledge/techniques/bethesda-plugin-record-format-esm-esp-esl.md`, `bethesda-esl-light-masters-and-plugin-archive-pairing.md`,
  `havok-hkx-chunked-packfile-family.md`, `static-address-native-hooks-ini-dll.md`, `engine-recreation-measures-and-fidelity.md`;
- `knowledge/games/skyrim-special-edition/rebuilding-a-cut-gatekeeper-with-generated-plugin-records-di.md` (Skyrim SE **1.7.104**, CK 1.7.99,
  generated ESL-flagged plugin from a Python writer, dialogue branches, shared voice lines, force-greets, 261 lines, 2026-10-24);
- `knowledge/games/dark-souls-remastered/portal-gun-prototype-via-dinput8-proxy-dll-player-camera-and.md` (hook method, DSR);
- `knowledge/games/fallout-4/fallout-4.md`, `fallout-3`, `fallout-new-vegas`, `starfield` (sibling Bethesda notes).

**Used first (2-3):**
1. `game-recon`: before any Part 0 spike, the checklist for install, engine, version and how to read data (G3, 0.0).
2. `reverse-engineering` (with the playbook): the scalpel for named questions (0010 §4); its Ghidra route is what we already require.
3. `game-automation` (screenshots, windowed launch, driving): the oracle plumbing for L4 checks (0021, 0022); `share-field-notes` after a
   finding worth giving back. `publish-mod` as the pre-release lint reference for 3.4 (no game files, no leaked keys).
Not used: `blitz3d-decomp`, `showcase-video`, `mashup-mods` (we are not a passthrough), `asset-pipeline` (2D sprite fitting) unless 3.1 needs it.

## 6. Every PLAN §4 row: verdict

Verdicts: **dep** = use as dependency, **fork**, **method** = port the method, **build**. "Evidence" points to the sections above, to an existing research file, or says UNVERIFIED where this session did not read a candidate. Rows marked "no candidate searched" have no third-party tool in PLAN §4 beyond what appears in the "Deps / references" column; the earlier 2026-10-27/28 research files hold their evidence.

| PLAN §4 row | Verdict | Candidate and why | Evidence |
|---|---|---|---|
| Worldspace terrain (126x126) + apron | build (on **Mutagen**, dep) | Mutagen models LAND; no terrain importer found. tes4skyrim's LAND decode and LOD-cover notes are method | §2; `prior-art-world-to-skyrim.md`; tes4skyrim `world.py:75-160`, `tes5_import_navmesh.md:1731-1800` |
| Rivers, lakes, waterfalls, sea | build (records) | vanilla WATR kit; nothing to reuse found | not searched this session (0026 §5) |
| Navmesh | build + method | DotRecast (dep) + Mutagen; tes4skyrim only as binary spec; its generator needs a pathgrid | §1.5, §2 |
| LOD, distant terrain, the map image | method (tools = dep under Wine) | xLODGen/DynDOLOD driven as tools; tes4skyrim's `lod_gen.py` recipe is the template | §1.6 |
| Regions, weather, climate, sky | build (data) | not searched this session; tes4skyrim's `weather`/`region` record types exist as method (`tes5_import/record_types/weather.py`, `region.py`: not read) | UNVERIFIED |
| Roads, routes, the route graph | build | route graph can feed the navmesh job as the pathgrid substitute for tes4skyrim's corridor method if Recast proves poor: **a hedge, not a plan** | §1.5 |
| Places, interiors, doors | build | piece resolver is ours; door-triangle/XNDP knowledge from tes4skyrim is method | §1.5 |
| Vegetation | build | scatter converter; tes4skyrim's SpeedTree notes not read (UNVERIFIED) | -- |
| The studio, scenes, the two runners | method (SkyLink AI shape) + dep (PrismaUI for the studio) + dep (houseCARL for dev queries) | §2, §3 | -- |
| Game state, co-save, message schema, menu router | build | ArgoniaCore; MorrowindRuntime's co-save and menu-registration notes are method; its co-save is a conflict if adopted | §1.1, §1.2 |
| Where each rule lives (the native map, G10) | method | read this audit; OpenMW source for the Morrowind rules | -- |
| NPCs, templates, schedules, factions | build (data) | -- | -- |
| Fixed danger, roaming bands, respawn | build (data + Papyrus) | Respawn Soulslike is a pattern only | §4 |
| Attributes, 27 skills, formulas | **dep: Custom Skills Framework** + build | skills as global-variable skills; formulas in ArgoniaCore | §4 |
| Races, birthsigns, classes, effects, perks | build (records) | -- | -- |
| Skill use, vastei, levels at rest, sitting | method (Sleep to Gain XP) + build | §4 | -- |
| Death pile, wake at last rest | method (Respawn Soulslike) + build | §4 | -- |
| Dialogue: topics, hyperlinks, disposition, persuasion | **fork (model half of MorrowindRuntime) or build; UI = build (PrismaUI)** | §1.1 to §1.4; decision at G5 on the sidecar adapter's cost | -- |
| Quests as data, conditions | build (+ universal-modder field note as method) | §2, §5 | -- |
| Writing quests, dialogue, text | tool (our skills) | -- | -- |
| Investigation support, detectives | build | -- | -- |
| Journal, directions, no markers | **dep: No Google Maps** (GPL-3.0) + method (Wayfinder) + MorrowindRuntime journal-as-QUST notes (method) | §4, §1.6 | -- |
| World map, local map | **dep: Flat World Map Framework** | §4 | -- |
| Our own UI and HUD, Pelagiad, transitions | dep: **PrismaUI** (pinned; unmodified) + build views; Dear Diary as a paper-style reference (permissions unknown) | §3 | -- |
| Weapon classes, armour slots, condition | build (data) | -- | -- |
| Economy, barter, training, services, travel | build (data/hooks); MorrowindRuntime's barter and travel service flows are method | §1.1 | -- |
| Magic | dep: **Magic Expanded** (candidate) + build (rules) | §4 | -- |
| Crafting | build (data) | -- | -- |
| Stealth, crime, Owing, locks, pickpocket | build; crime-through-Skyrim's-system pattern from `tes_runtime/tes/crime.cpp` and `tes_runtime/morrowind` is method | §1.6 | -- |
| Combat (DS1's system) | dep (the 0.0 stack) + build per the combat map | §4.1 | -- |
| Wiring the mods to our stats | build | -- | -- |
| Movesets | dep (Elder Souls, etc.) + build (timing control) | `stream-and-combat-stack.md` | -- |
| Enemy AI, bosses | dep: SCAR and CPR (pick MIT originals or GPL-3 forks) | §4.2 | -- |
| Ranged, thrown | dep: Throwable Weapons SKSE; THIT | §4 | -- |
| Climbing, ladders | **dep: FreeClimb** (GPL-3.0-only; 1.7.104 stated) | §4 | -- |
| Swimming, diving, breath | dep: Underwater NG (page UNVERIFIED) | §4 | -- |
| Boats | method / fork after permission (Sailable Ship); build the rest | §4 | -- |
| Marsh specials | build | -- | -- |
| Ragdolls | dep (XP32 etc.), not searched | UNVERIFIED | -- |
| Graphics | dep: **Community Shaders** (GPL-3.0; 1.7.104 UNVERIFIED) | §4.2 | -- |
| Music, ambience, UI sound | build (data) | -- | -- |
| Vanilla quarantine | dep: Fuz Ro D-oh (not searched) | UNVERIFIED | -- |
| Immersion inventory and gate | build (tool) | -- | -- |
| Main menu, loading, settings, controls | build (PrismaUI or own SWF); Oblivion-like Loading Menu and Dear Diary as references | §3 | -- |
| Character creation, the opening | build (view); RaceMenu only if needed | -- | -- |
| Install, pin, distribute | dep: SKSE, Address Library, Pandora, PrismaUI (all player downloads); installer is ours | `stream-and-combat-stack.md:226-247` | -- |

## 7. What this changes in the briefs (method changes only)

1. **0.2 G5 (dialogue):** decide between "fork MorrowindRuntime's model half" and "our own small store" by one measured test: compile
   LH38's dialogue to the sidecar shape and open it on 1.7.104; the filter, keyword search, disposition and persuasion are already
   proven there, so G5's real risks are the 1.7.104 smoke test and the sidecar adapter, not the engine.
2. **0.2 G5 and G11:** the interception answer is the activation vtable swap with a "slot holds the expected function" guard; the
   dialogue menu is the wrong hook. Hook activation; let PrismaUI host the window; do not register a custom IMenu unless a screen needs it.
3. **0.2 G4 / 2.W4 §b (navmesh):** drop "tes4skyrim's navmesh method" as a generator; keep it as a binary spec (NVNM, NAVI, edge links,
   door triangles) and write the generator on DotRecast over Skyrim NIF collision. Make "NAVI lists every navmesh" an explicit test.
4. **0.2 G3:** add MorrowindRuntime and PrismaUI to the 1.7.104 smoke list as "load and log" checks, not only the combat stack.
5. **0.1 §j wording:** change "built for 1.6.1170, 1.6.659 and 1.5.97" to "built with no CommonLib; 1.7.x Address Library supported, offsets verified on 1.6.x";
   change "MIT core" to "MIT by README sentence, no LICENSE file; treat as source-available until the author adds one".
6. **G10 / ArgoniaCore:** state a rule that an adopted runtime's co-save is a second owner: either ArgoniaCore mirrors its records or the fork
   writes into our families (0015 note: register GPL-3.0-only for Mutagen, FreeClimb).
7. **UI briefs (1.2, 2.2, 3.1):** state PrismaUI's licence limits (unmodified redistribution only; modifications need written permission);
   our GPL code calls only its published API. Dear Diary and the paper family: permissions UNKNOWN, ask or read in a browser before reuse.
8. **Combat briefs (1.4, 2.7):** SCAR and CPR have GPL-3.0 forks maintained in 2026 (SkyHorizon3); the MIT originals stopped in 2023-24; pick one and
   record it. Record provenance for the unofficial 1.7.104 builds (OCPA NG, Modern Stagger Lock rebuild) in the sourcing register.
9. **Tooling (0.1 §a to §i):** vendor universal-modder's `game-recon`, `reverse-engineering`, `game-automation` and the Bethesda playbook first; copy the
   1.7.104 plugin-generation field note into `docs/research/` as prior art for the quest and dialogue emitters (2.5, 2.12).
10. **Every later brief's "Prior art" line:** cite the §6 row for its system, then re-check that row's candidate (last-push date, release, runtime) in 5 minutes,
    as §j already asks; this audit's UNVERIFIED items are the re-check list.
