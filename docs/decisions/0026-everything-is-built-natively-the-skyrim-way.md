# 0026: Everything is built natively, the Skyrim way; the old project gives goals and content, never machinery

**Status:** decided 2026-10-28. The owner, after the Claywater Station deep dive:
- "getting our old one to work properly in threejs was a nightmare. Really don't want to reverse engineer that
  whole bad patchy buggy system. Want to just do it properly in whatever way skyrim modding is intended to be done,
  from day 1."
- On rebuilding Claywater natively or converting its layout: "rebuild natively, and that's what we'll do for all
  places going forward as well".
- Then, for every system: "magic, stealth, crime, enemy AI, etc etc - the previous repo is the guide for what
  goals we were *aiming for*, we hadn't actually achieved good enough against any of them, and our approaches
  were very hacky for trying to get them to work in threejs. what we want to do now is natively make use of
  skyrim's engine and existing tools as much as possible, and use them in better ways to achieve the goals we
  were previously aiming for".

## Context

The old project had to build in three.js everything Skyrim already has: a renderer, terrain, water, physics,
AI, detection, crime, magic, saves. Its rule packages (dialogue, narrative, stats, economy, crafting, crime,
perception, scheduling and the rest) were written to make up for an engine that had none of these. They never
reached a good enough standard against their goals. The earlier plan here asked whether to run that code inside
Skyrim (spike 1.1 §a, embedded JavaScript, against a C++ port). That would carry the old workarounds into an
engine that already has native systems for most of them.

## Decision

1. **The old project is a statement of goals and a source of content, never of machinery.**
   - **Goals:** what each system was aiming for, taken from its design docs, rulings and the intent of its tests.
     For example: Morrowind's magic schools and spellmaking, levitation included, the sitting, vastei, fixed regional
     danger, crime and bounties, schedules on the lamp clock.
   - **Content:** the heightfield and hydrology, places' designs and stories, people (records, homes,
     workplaces, routines, services, factions), items, quests, lore, numbers in the stats design.
   - **Not taken:** its code, harnesses, workarounds and three.js systems. Its tests are read for what they meant
     to assert, never run as acceptance.
2. **Each goal is met with Skyrim's own systems first, used better.** In route order (decision 0010):
   - Skyrim's records and settings: actor values, perks and entry points, magic effects, spells and
     enchantments, factions and crime factions, detection and stealth settings, AI packages and combat styles,
     encounter zones and levelled lists, quests and the journal, barter, game settings;
   - existing tools and mods, including tes4skyrim's runtimes (MorrowindRuntime for dialogue, scripts and
     services; TESRuntime for jails and journals), audited in 0.1 §j;
   - our own SKSE code only for what neither covers, kept small and unit-tested, and written for this engine.

   A goal Skyrim cannot meet at all goes to the owner as a call; it is never quietly dropped.
3. **Places are rebuilt natively, by an agent working the way a Skyrim modder works**, for Claywater Station and
   every place after it:
   - **Terrain** is LAND data from the heightmap, the same records the Creation Kit's heightmap import makes,
     with land textures painted by land-cover class.
   - **Ground under a building** is shaped by direct landscape edits in that place's cells, as a modder sculpts it
     in the CK. There is no overlay system. The edits belong to the place: old 0102 and 0140 still hold (a place
     carries its own ground and is edited in place by its own layer).
   - **Buildings and props** are ordinary placed references (REFRs) of the source plugins' base records, resolved
     by mesh path from plugin data. Load doors link to their interiors (old 0114).
   - **Trees, rocks and scatter** are placed by the CK's region generator from region records, never by hand
     outside a place; grass follows the painted land texture by itself; the land is Tropical Skyrim's
     ([0028](0028-the-land-is-tropical-skyrim-through-skyrims-own-systems.md)).
   - **Then navmesh (§4), then distant LOD.**
   - **The design is the specification; the old layout is a guide.** The agent rebuilds the place from its design
     note, using the old positions as a reference. It judges vantage stills against the design and fixes until
     they match.
   - Every old piece came from Skyrim or a Skyrim mod, so a native match always exists. The open cases are a mod
     we may not depend on, a mod that will not load on the pinned runtime, or a piece that looks different under
     Tropical Skyrim's textures (a look check).
4. **Navmesh from the world's own collision, by code; tes4skyrim as the binary spec.** The reuse audit
   (2026-10-29) found tes4skyrim's live generator walks Morrowind pathgrids and its collision-voxel generator was
   deleted, so it cannot run on our LAND and REFR data. The generator is ours, on DotRecast over the collision
   read from the placed meshes' `bhkCompressedMeshShape`, writing NVNM, NAVI, edge links and door triangles as
   tes4skyrim's writer documents them. The Creation Kit's generator, scripted on the Windows game machine, is the
   check and the fallback. The proving step comes first: round-trip one CK navmesh through Mutagen and confirm
   NPCs walk it, then generate.
5. **Water is Skyrim's own** (WATR records, cell water, placed planes, the vanilla rapids and falls pieces), tuned
   with Community Shaders. Nothing reproduces the old water's look.
6. **Mist and light are Skyrim's and Community Shaders':**
   - outdoors, volumetric lighting and fog, each weather's fog, and placed mist effects in hollows and over water;
   - indoors, sun shafts through windows that follow the sun are researched first (2.W3). If no current mod or
     Community Shaders feature gives them, **well-placed static light beams, set to the time of day, are
     accepted** (owner, 2026-10-28).
7. **People carry over as content.** Their records, homes, workplaces, routines and services are imported as data,
   and their dialogue is rewritten by the writing skills (0024). **Whole-body templates:** an NPC's appearance
   comes from one template NPC that supplies race, head parts, skin, weight and height together (TPLT with the
   traits flag), never a face alone. Each person gets a full-body still, and a reader checks it for neck seams
   and skin-tone mismatches.
8. **The UI's approach is chosen with the owner** (decision 0017, spike 1.2 §0). Adapting the old React UI in web
   views is one candidate among Skyrim's own menus, MorrowindRuntime's, OpenMW's layouts and hybrids.

## Consequences

- **Spike 1.1 §a changes question.** It no longer asks whether to run the old TypeScript or port it to C++. It
  maps every system's goals onto Skyrim's native mechanisms and existing tools, proves the hardest mappings in
  game, and sizes the SKSE code left over. QuickJS and the embedded rule bundle are dropped.
- **0.1 §f** imports the old rule packages read-only as goal evidence and writes **the goals list**,
  `docs/design/goals.md`: each system's goals, with sources. Every system brief reads its section.
- 0.4 builds the Claywater block natively; it is kept as Part 1's place. Its check is that every piece the
  design uses resolves to a base record (L1).
- 0.4's kit-id mapper becomes a **piece resolver**: a lookup the builder uses, not a converter.
- 2.W5 and 4.2 rebuild every place by the same recipe; the `world-builder` skill holds it.
- 0018 still holds: records are written by code, and the CK is a scripted tool. Its jobs run on the Windows game
  machine rather than under Wine.
- Unit tests (L2) prove our own SKSE code's pure core (decision 0029: no second runner). Behaviour that native
  Skyrim systems own is checked at L4.
- 0023's critique "wasted reuse" (not running the old rule code) is withdrawn by this ruling.
