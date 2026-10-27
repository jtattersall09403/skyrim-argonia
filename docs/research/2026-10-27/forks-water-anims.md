# OpenMW forks, Skyrim support, water and animations (research, 2026-10-27)

Method: web fetch of project pages, plus a blobless read-only clone of
sunspotdark/morrowind-modern-physics (branch `physics`) at
`/tmp/claude-0/-home-claude/4eae515a-2cd9-5a49-b7da-638a25d58e2a/scratchpad/ext2/mmp`.
That fork's base commit `628b6c2b7` is OpenMW master of 2026-10-03, so all
"upstream code" claims below are read from that commit (file:line), not from
memory. Nothing was built or executed.

## 1. sunspotdark/morrowind-modern-physics

- What: an unofficial OpenMW fork (not a GitHub network fork; full upstream
  history imported, 38,977 commits, 62 by sunspotdark). README: "Fork version
  1.1 ... Based on OpenMW 0.52.0 (development version, upstream commit
  628b6c2b72, 2026-10-03)". https://github.com/sunspotdark/morrowind-modern-physics
- Engine: stays on **Bullet** (no Jolt). First commit "Simulate bottles as
  Bullet rigid bodies" (10a15e0c0, 2026-10-03).
- Features: small items become rigid bodies with auto convex hulls; furniture
  gets detailed collision; carry/rotate/throw on Activate/Attack; buoyancy by
  density; arrows stick (soft materials) or bounce, recoverable; material
  impact sounds (YAML-tuned, vanilla sounds only); **ragdolls** for NPCs and
  creatures fitted to skinned meshes, draggable by limb, saved in the save,
  float in water, fallback to death pose. **No vehicles, no boats, no
  climbing, no water changes beyond buoyancy/splashes.**
- Size: 73 files, +6,764/-55 vs base. New: `apps/openmw/mwphysics/ragdoll.cpp`
  (690 lines), `mwworld/impactsounds.cpp` (565), `mwworld/materials.cpp`
  (166); large edits in `physicssystem.hpp` (+143), `worldimp.cpp` (+379),
  `mwrender/animation.cpp` (+359), `esm3/creaturestats.cpp` (save format).
- Maturity: 17 days of work (2026-10-03 to 2026-10-17, v1.1). One star, no
  forks. Author: "I am not a programmer ... vibecoded ... with Claude Opus
  5.5", "everything around Seyda Neen seems to be working", not reviewed by
  any OpenMW developer. Saves with ragdolls will not load in stock OpenMW.
- Licence: GPLv3 (same as OpenMW).
- Platforms: "Windows only for now (other platforms may build from source but
  are untested)". No Android build.
- Upstreaming: unlikely as is. It adds a new save field and settings, is not
  split into reviewable merge requests, and upstream has a competing Jolt
  rewrite in draft (MR !3919, below) plus a VSG port in progress. Worth
  treating as a **reference for ragdoll, carry and buoyancy logic**, not as a
  base. Rebasing it onto 0.51 would also mean back-porting about 4 months of
  master.

## 2. OpenMW "supports Skyrim": exact status (code at 2026-10-03)

- Release notes: 0.50 and 0.51 posts say nothing new about ESM4 or Skyrim
  (https://openmw.org/?p=6887, https://openmw.org/2026/openmw-0-51-0-released/).
  0.50 only says that "running Oblivion and later Bethesda open-world engine
  games is in the engine's eventual scope". Wikipedia's claim that 0.49 brought
  "support" means **loading and viewing**, not play.
- Records: `components/esm4/` has readers for about 90 record types
  (ACHR ACTI ALCH ... WATR is absent, see below ... WEAP WRLD). Only about 40
  are actually stored at runtime (`apps/openmw/mwworld/esmstore.hpp:148-156`):
  Activator, actors, Ammo, Armor, ArmorAddon, Book, Cell, Clothing, Container,
  Creature, Door, Furniture, Flora, Hair, HeadPart, Ingredient, ItemMod, Land,
  LandTexture, levelled lists, Light, MiscItem, MovableStatic, Npc, Outfit,
  Potion, Race, Reference, Sound, SoundReference, Static, StaticCollection,
  Terminal, TextureSet, Tree, Weapon, World. No quests, dialogue, scripts,
  AI packages, magic or water types are used. ESM4 cells render with object
  paging and terrain (2025-07 "esm4paging", "ESM4 landscape textures"); ESM4
  doors play an opening sound; NPCs render with a TODO "Body and head parts
  are placed incorrectly" (`apps/openmw/mwrender/esm4npcanimation.cpp:75`).
- NIF: header parser covers Bethesda versions through FO4. `BSTriShape`,
  `BSDynamicTriShape`, `BSSegmentedTriShape`, `BSMeshLODTriShape`,
  `BSSubIndexTriShape` are read and drawn (`components/nifosg/nifloader.cpp:179`).
  `BSLightingShaderProperty` types are mapped but most log "Unhandled
  BSLightingShaderType" (`nifloader.cpp:2451-2481`), so SSE shading is basic.
- **Skinned SSE meshes: not supported.** `nifloader.cpp:1852` says
  "This is the skinning data Fallout 4 provides // TODO: support Skyrim SE
  skinning data". Skyrim LE (NiTriShape + NiSkinInstance) skinning goes
  through the older path and works. MR !3465 (Alexei Kotov, opened 2023-09,
  still open) says "SSE skinning is still unsupported".
  https://gitlab.com/OpenMW/openmw/-/merge_requests/3465
- **Collision for SSE statics: none generated.** Gamebryo collision ignores
  Havok data ("FIXME: hack, using rendered geometry instead of Bethesda Havok
  data", `components/nifbullet/bulletnifloader.cpp:134`) and builds a shape
  only from `Nif::NiGeometry` (`bulletnifloader.cpp:241`). `BSTriShape`
  derives from `NiAVObject`, not `NiGeometry` (`components/nif/node.hpp:390`),
  so SSE BSTriShape meshes get no collision. !3465 also notes "Collision for
  BSTriShape is also not auto-generated yet". bhk* records are parsed
  (`components/nif/physics.hpp`) but unused for physics.
- Animation: no `.hkx` or Havok Behavior support at all (no file in the tree).
  Skyrim actors cannot animate in OpenMW.
- Can a TES3 game reference SSE NIF statics directly? Rendering: yes, with
  basic shading. Walkable or blocking: no. Skinned or animated SSE: no.
  Practical routes: convert SSE meshes to LE/NiTriShape form (e.g. Cathedral
  Assets Optimizer / NifSkope tooling) or to NIF 4.0/Collada, and add explicit
  collision (a RootCollisionNode or a "collision" child in .dae). This is an
  inference from the code above; I have not test-loaded files.
- Rendering backend: master is mid-way through a VulkanSceneGraph port
  (`vsg/*` merges through 2026-10-02 per git log, e.g. "vsg/250-workqueue-drop-osg").
  Expect churn in renderer code over the next releases.

## 3. Other forks and derivatives

- **Jolt in upstream**: Draft MR !3919 "Jolt physics implementation" by
  cykoder, opened 2024-03-02, last edited 2026-03-15, 77 commits, 140 files;
  water collision, scaled-mesh navmesh, tests done; still a draft, not merged.
  https://gitlab.com/OpenMW/openmw/-/merge_requests/3919
- **TES3MP**: multiplayer fork, last major 0.8.x line based on old OpenMW
  (0.47 era); separate codebase, not tracking 0.51. Mirror:
  https://git.cijber.net/mirror/openmw-tes3mp
- **openmw-vr** (Mads Buvik, OpenXR): docs at https://openmw-vr.readthedocs.io/;
  it was merged into TES3MP's VR builds; it is not in upstream master.
- **Browser (WASM)**: a Reddit user, "Dumpster Buddy", compiled OpenMW to
  WebAssembly with WebGL2 (shadows, water and lighting reworked,
  supersampling instead of MSAA); covered by PC Gamer on 2026-07-28. I found
  no repo URL or version. https://pcgamer.com/games/the-elder-scrolls/you-can-now-play-morrowind-entirely-in-your-browser-honestly-just-wanted-to-see-if-it-could-be-done
- **Android**: upstream keeps Android CI scripts (`CI/before_script.android.sh`)
  and merged "androidproof" (2025-12-07), but publishes **no official APK**.
  The old ports are dead: F-Droid `com.libopenmw.openmw` 0.46 (2020, "No
  Source Since"), and xyzz/openmw-android nightly 0.48 (2021, "no longer under
  development"). Community repos exist (github.com/tazok81/openmw-android,
  github.com/SCARaw/Android-OpenMW); I did not verify how current they are.
  Android is therefore a self-maintained build of whatever fork you pick, with
  GLES via gl4es or ANGLE. Morrowind-scale content on a phone is feasible;
  Skyrim-density assets will not be.
- **Standalone games**: the OpenMW Example Suite (https://gitlab.com/OpenMW/example-suite)
  is the official template (2018, 172 commits). The Land Racer creature
  tutorial uses Collada. No full commercial or standalone game on OpenMW is
  known: community threads (e.g. https://lemmy.imagisphe.re/post/1606264/4392462)
  find none fully free of Morrowind data. The lesson is that the engine works
  for a total conversion, but you ship your own data and must replace every
  Morrowind-hardcoded assumption (GMSTs, base animations, `xbase_anim`,
  default sounds, UI textures).

## 4. Water

- **Engine fact: one flat water height per cell.** `World::isUnderwater`
  returns `pos.z() < cell->getWaterLevel()` if the cell has water
  (`apps/openmw/mwworld/worldimp.cpp:2142-2151`); swimming is
  `isUnderwater(object, mSwimHeightScale)` (`worldimp.cpp:2118-2120`).
  Physics uses the same single level (`mwphysics/physicssystem.cpp:666`).
  Lua exposes `cell.waterLevel` read-only (`mwlua/cellbindings.cpp:132`).
  Exteriors share one sea level. **Actors cannot swim in mesh water in
  OpenMW**; any mesh "river" above sea level is visual only.
- There is no WATR or ESM4 water support in the runtime store. I found no open
  OpenMW issue or MR for multiple water levels, water volumes or flow (search
  hits such as #7841 are about the editor saving WHGT). Treat it as unplanned
  upstream.
- **MWSE Water Volumes** (StormAtronach), the best prior art. It is for the
  original engine, not OpenMW: a 32-bit MWSE DLL patches 83 sites in
  Morrowind.exe. Meshes with a shape named `WaterVolume...` (`depth`, `noswim`,
  ...) become swimmable water at any height or tilt, with breath and an
  underwater camera, for player and NPCs. It has a 37-mesh kit (river pieces,
  swamp, mud and blood variants). "The water has no current." Repo MIT, built
  DLL GPLv2. https://github.com/StormAtronach/MWSE-water-volumes
  It is the design to port into an OpenMW fork: replace
  `getWaterLevel(cell)` with a query "water surface at (x,y,z)" over a set of
  volume shapes, then feed swim, physics buoyancy, the camera underwater
  state and rendering.
- OpenMW visual mods (shaders only, no new water heights): Complete Water
  Shaders and PBR for 0.51 (MrZer0x0, no modification without permission;
  https://www.nexusmods.com/morrowind/mods/59485), OpenMW Water Shader
  Enhanced (https://www.nexusmods.com/morrowind/mods/56186), Vanilla Inspired
  Water (https://www.nexusmods.com/morrowind/mods/49391), More Dynamic Water
  Meshes (distortion on TR/OAAB river and waterfall meshes, needs soft
  particles; https://modding-openmw.com/mods/openmw-more-dynamic-water-meshes/).
  Wonders of Water (NullCascade, MIT) is MGE XE/MWSE only.
  MorrowSwim (Lua aquatics skill, swim dash, NPC breath and diving;
  https://www.nexusmods.com/morrowind/mods/57804) shows how far Lua can go
  inside the single-level limit.
- Tamriel Rebuilt: rivers above sea level are non-swimmable water and
  waterfall meshes. The UESP bodies-of-water page lists rivers but no
  technique (https://en.uesp.net/wiki/Tamriel_Rebuilt:Bodies_of_Water).
- Skyrim's approach: a cell or worldspace water plane plus placeable water
  planes (WATR-typed, swimmable, at any height). Sloped streams are
  MovableStatic river meshes, or tilted water planes chained with seams hidden
  by rocks
  (https://forums.nexusmods.com/topic/9104428-how-to-make-a-small-river-that-flows-down-a-slope).
  Flow is a per-WaterType flowmap painted in the CK, one flow worldspace per
  plugin (https://wiki.beyondskyrim.org/wiki/Arcane_University:Water_Flow_Editing).

## 5. Animations

- Lua API (upstream, `apps/openmw/mwlua/animationbindings.cpp:127-232`):
  `hasGroup/hasBone/isPlaying/getCurrentTime/getCompletion/setSpeed/cancel/
  playQueued/playBlended(group,{priority,blendMask,autoDisable,speed,startKey,
  stopKey,startPoint,loops,forceLoop})/addVfx`. Mods should go through
  `I.AnimationController.playBlendedAnimation`, `addTextKeyHandler` and
  `addPlayBlendedAnimationHandler`
  (`files/data/scripts/omw/mechanics/animationcontroller.lua:20-100`). 0.51
  added an "Animation end" handler. New groups ship as extra KF files loaded
  with "use additional anim sources" (`settings-default.cfg:304`, default
  false), which is why every combat mod tells you to enable it. Root motion
  and procedural moves are done in Lua with the controls or physics, not by
  the animation.
- Formats: NIF/KF native. Collada (.dae) animated actors are supported via
  OSG, with documented pipelines
  (`docs/source/reference/modding/custom-models/pipeline-blender-collada-animated-creature.rst`;
  exporter https://github.com/openmw/collada-exporter). collada_dom is now
  linked only for static OSG builds (2026-06 commits). **No glTF or FBX
  loader.**
- The combat mods:
  - Kazedō (devilymoon, 59825) is Lua plus a blur shader, with no animation
    files stated. The most permissive: modify, convert and use assets with
    credit; not in paid works.
  - N'Garde (MrArrean, 58658) does ship new animations: shield, 2H, goblin,
    Almalexia and miss-dodges by **Dubiousnpc**, shield-raise by Xerxse, H2H
    block by SaintJ, VFX bone NIF by Greatness7. Hand-made by modders, with
    no Mixamo mentioned. Permissions: no upload, modify only with permission,
    no conversion, assets only with permission.
  - Can't Touch This (59155) ships 11 miss-dodge animations (8 by
    DubiousNPC). Same restrictive terms.
  - Hit Reactions Animated v2 (Max Yari, 56594, updated 2026-10-18) has
    stagger, death and twitch animations; needs Max Yari's Script Services;
    asset use only with permission.
  - Dash (58262) is Lua with an Athletics-scaled dash; no animations stated.
  - Riposte (59828): the page would not fetch; not verified.
- New animation types elsewhere:
  - ReAnimation v2 (Max Yari, 52596; GitHub MaxYari/OpenMWReAnimation) is a
    1st-person set: 1H and bow locomotion, dagger set, sneak sets, alternating
    attacks. "Absolute most animations are remade from scratch". No licence
    file seen.
  - One-handed animations and idle fixes (Max Yari, 55059) is based on
    Graybark's Animation Compilation and Dirnae; modify with credit, assets
    by permission.
  - Animation Compilation (Graybark, 43982) has Dirnae run, walk and beast
    sets, Djok sneak and female walk, and Almalexia casting; "Please contact
    the original authors".
  - Weapon Sheathing (Greatness7) is meshes, not new animation groups.
  - Thu'um (devilymoon, 59871) has a shout animation by DetailDevil; ask
    DetailDevil.
  - Source Movement (gugetastic, 59496) is pure-Lua bhop, surf and slope
    movement; it has an optional DLL injector, so the Lua physics API has
    limits.
- **No climbing, ledge-grab or roll animation set for OpenMW was found**,
  and no Mixamo-sourced pack. Licences across the scene are mostly "ask the
  author", so a total conversion cannot ship them without written
  permission. Note also that these KF files target Morrowind's
  `base_anim` skeleton, not Skyrim's.

## Bottom line for Argonia

OpenMW 0.51 cannot use Skyrim assets as-is. Statics render with no collision.
Actors (SSE skinning, HKX animations) do not work at all. Water is one plane
per cell. Climbing, boats, sloped or swimmable rivers and souls-like
locomotion each need engine work in a fork: water volumes in the MWSE design,
kinematic boat platforms, climb states. The modern-physics fork gives
prototype ragdoll and carry code but is not a base: 17 days old, unreviewed,
Windows-only. Android has no maintained official path. Mod animations are
Morrowind-skeleton and mostly permission-locked.
