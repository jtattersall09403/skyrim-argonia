# Engine feasibility: OpenMW, Mudcrab, DS3 assets, and the OpenMW mod scene

Research date 2026-10-27, carried over from the planning conversation. This is the evidence for why the
project did **not** choose OpenMW (decision 0001) and what the fallback would involve. Two reports are merged
here: engine feasibility, and existing OpenMW mods.

## 1. OpenMW (0.51.0, 22 June 2026)

- 0.51 adds custom magic effects through Lua, runtime-created records, more bindings, a camera projection
  offset, gamepad work ([GamingOnLinux](https://gamingonlinux.com/2026/06/morrowind-game-engine-openmw-0-51-released-with-modding-and-gamepad-improvements)).
- Combat in Lua: `Combat.addOnHitHandler` can rewrite damage and hit type
  ([docs](https://openmw-vr.readthedocs.io/en/latest/reference/lua-scripting/interface_combat.html)). Stagger,
  knockdown, physical damage application and AI reactions are still C++
  ([issue 8642](https://gitlab.com/OpenMW/openmw/-/issues/8642)). Real poise is not scriptable without a fork.
- Animation: `AnimationController` plays blended groups with priorities and text-key hooks. New groups load
  from extra KF files ("use additional anim sources", off by default). Collada animated actors are supported;
  glTF/FBX are not ([custom models](https://ptmikheev-openmw.readthedocs.io/en/latest/reference/modding/custom-models/index.html)).
- **Water is one flat level per cell** (`worldimp.cpp` checks `z < cell->getWaterLevel()`); actors cannot swim
  in mesh water. Morrowind has one sea level for all exteriors; Oblivion added per-cell levels; no Bethesda
  engine does sloping rivers natively. Prior art: MWSE Water Volumes (original engine only, MIT,
  [repo](https://github.com/StormAtronach/MWSE-water-volumes)).
- **Skyrim support (ESM4)** is load-and-view only: about 40 record types kept at runtime, SSE `BSTriShape`
  renders with basic shading, **no SSE collision, no SSE skinning, no HKX/behaviour support**
  ([openmw.org](https://openmw.org/?p=6805), [MR 3465](https://gitlab.com/OpenMW/openmw/-/merge_requests/3465)).
- Android: no official build; community builds by cavebros (GitLab) and Sisah2 (GitHub) as CI artifacts;
  F-Droid stuck at 0.46. A maintained Android build would be ours to keep.
- Browser: openmw-web compiles to WebAssembly + WebGL2, desktop Chromium only
  ([repo](https://github.com/Virtastic/openmw-web)).
- Forks: sunspotdark/morrowind-modern-physics (0.52-dev base, Bullet, carry/throw items, ragdolls, arrows
  stick; 62 AI-written commits, Windows only, 1 star, unreviewed: read for its ragdoll code only). Jolt MR 3919
  is a draft. TES3MP and openmw-vr are on ~0.47.

## 2. Mudcrab

Rust/Bevy reimplementation of Skyrim SE, GPL-3.0-or-later, ships no assets
([repo](https://github.com/Mudcrab-Team/mudcrab)). Converter (ESM to SQLite, NIF to glTF, DDS to KTX2, Papyrus
to Luau), streaming world, first-person walking with Rapier. Its README: "Skyrim is not playable as a game
yet." No scripting/UI, combat, animation blending, saves or Android. A world viewer today; watch it as a
long-term S4 path (decision 0001).

## 3. ds3-open-re and Dark Souls assets

- ds3-open-re ([repo](https://github.com/garyttierney/ds3-open-re)) is netcode only (protobuf, cipher, server
  stub), abandoned 2021. Irrelevant to combat.
- Extraction tools: Smithbox (MIT), DSAnimStudio (GPL-3), Blender FLVER importer (experimental rigging).
  Converting DS animations to another skeleton is fragile.
- **Bandai Namco's EULA forbids reverse engineering and derivative works and limits content to personal use
  "exclusively in the Game"** ([EULA](https://www.bandainamcoent.com/legal/bnea-wweula-on)); they sent DMCA
  takedowns over Dark Souls mods before
  ([Techdirt](https://www.techdirt.com/2014/12/23/dark-souls-modder-gets-copyright-threat-game-developer-some-reason/)).
  So: DS assets and code never enter Argonia. Measuring mechanics (knowledge) and writing our own
  implementation is the line (decision 0004, docs/legal-and-sourcing.md).

## 4. Existing OpenMW mods (permissions matter)

Most valuable OpenMW combat mods carry restrictive Nexus terms (usable as player downloads, not modifiable).
Reusable: Kazedō dash (59825), Riposte (59828), Surefire no-dice (59646, fully open), Maxar's Timed Attacks,
Death Reflections, Sanctuary From Unarmored (MIT source), NCGDMW Lua (MIT), Lua NPC Schedule (58635),
Inventory Extender (MIT), Cell Bouncer, Your Own Gondola ("do whatever you want"), the GPL climbing compilation
(45694). Restrictive: N'Garde (58658, hand-made parry animations), Jim's Combat Camera (lock-on), Hit
Reactions Animated, Blue Water Sailing Ship (56471, player-steered with wind physics), Can't Touch This.
No OpenMW mod covers bonfire checkpoints, corpse runs, poise meters, directional attacks, mantling or ledge
grabs; mounts were hidden by moderators in Sep 2026.

Assets: Tamriel_Data (44537; free as a master, extracting assets needs authors' permission), OAAB_Data
(49042; remix with credit "for use in Morrowind"), Saxhleel Argonians (59180, conversion not allowed). Black
Marsh core (stilt villages, xanmeers, Hist, mangroves) is ~5–15% covered; Imperial/Dunmer/coast ~70–85%.
Swamp creatures in Tamriel_Data exist; wamasu, crocodiles, leviathans, kothringi exist only as Skyrim mods
(mainly MihailMods).

Graphics: MOMW lists (Graphics Overhaul 380 mods, Total Overhaul 631), MOMW Post Processing Pack (volumetric
clouds, godrays, SSAO, HDR). Result: roughly a modded Oblivion/early-Skyrim look.

Tools: tes3conv (MIT, ESP↔JSON), umo installer, OpenMW Lua integration-test framework.

## 5. Why this lost to Skyrim as host (summary)

OpenMW gives Morrowind's systems free but makes the "body" expensive: Black Marsh art and creatures would be
converted per mesh (with author permissions that forbid cross-game conversion), rivers need an engine fork,
climbing and souls combat are built from scratch with scarce animations. Skyrim gives the body free (the
Skyrim-format art the project already uses, flowing placed water, mature combat/climb mod APIs) and makes the
"soul" a code problem, which suits agents. Fallback trigger: see decision 0001.
