# Skyrim SE asset pipeline for generated art (owner call #93, lane: asset pipeline)

> **Correction by the lead, 2026-11-24.** The game's Data folder IS on the build VM (`~/games/skyrimse/Data`,
> the vanilla archives included) and `tools/places/assets/resolve.py` reads any vanilla model from it. Read
> there: `weapons\steel\steelsword.nif` holds a BSTriShape, a blood-edge effect shape, BSXFlags, a
> NiStringExtraData `WeaponSword`, and a bhkRigidBody with a convex shape; `weapons\steel\steelwarhammer.nif`
> the same with `WeaponBack`; `armor\iron\shield.nif` a `SHIELD` string, BSInvMarker and a box rigid body;
> `furniture\bedroll\bedroll01.nif` a BSFurnitureMarkerNode and a MOPP collision inside the file. So the
> template-swap facts marked [K] for swords, warhammers, shields and bedrolls are confirmed on the real files,
> and donors need no play machine.


Runtime pinned: 1.7.104, SKSE 2.3.1 (docs/PLAN.md:12, decision 0002). The NIF format is the same SSE BSTriShape format
as on 1.6.x. Tags: [V] fetched or measured this session; [K] my modding knowledge, not re-fetched (verify by trial).

## Findings first

1. The repo already has a Linux NIF reader and writer built on ousnius/nifly: `tools/places/assets/nifdump` (reads every SSE
   shape to GLB, tools/places/assets/nifglb.py:3-8) and `tools/newworld/niflod/niflod.cpp:1-12` (writes BSFadeNode +
   BSTriShape + BSLightingShaderProperty + BSShaderTextureSet; no collision, no extra data, no skin). Binaries
   ~/.argonia/bin/nifdump and niflod (3.1 MB each) [V]. The static visual NIF is a proven block; collision, BSXFlags, markers,
   skinning and Blender are missing.
2. Installed here [V]: no blender, texconv, wine, nifskope, dotnet, cmake (gcc only). ~/.argonia/nwvenv has numpy 2.5, scipy,
   scikit-image, Pillow 13, networkx, imageio, numba. Build VM: 4 cores, 15 GB, no GPU. No game Data folder on it
   (tools/places/assets/resolve.py:18 default ~/games/skyrimse/Data is absent [V]); vanilla NIFs are on the play machine.
3. PyNifly (BadDogSkyrim, GPL) is the one maintained Blender<->NIF tool for SSE (supports Blender 4.0+, release notes to 5.2
   [V]). README says "Windows only" [V] because `io_scene_nifly/pyn/niflydll.py:52` does `cdll.LoadLibrary(...NiflyDLL.dll)`
   [V]. But `NiflyDLL/CMakeLists.txt` has a non-MSVC branch and builds on `external/nifly` [V], and nifly already builds here;
   the Python side (collision, `pyn/mopp_compiler.py`, `bhk_autopack.py`, furniture markers, trees) is pure Python [V].
   VERDICT PARTIAL: a Linux `libNiflyDLL.so` plus a loader patch is plausible and unproven. It is the biggest unknown.
   Fallback: Blender+PyNifly on the Windows play machine (on demand, costs money).
4. PyNifly collision export [V: wiki "Collisions", nif/collision.py]: bhkBoxShape (rectilinear), bhkCapsuleShape (from a UV
   sphere), bhkSphereShape (in code), bhkConvexVerticesShape (hull around a simple mesh), bhkListShape (+auto
   bhkConvexTransformShape), and MOPP collisions repacked as bhkMoppBvTreeShape + bhkCompressedMeshShape with auto-generated
   MOPP bytecode. Mass/damping/friction from Blender's Physics panel; bhkMaterial and layer (STATIC, CLUTTER, WEAPON, BIPED) are
   properties; flags `pynCollisionFlags`; radius is not unit-converted. Export also recognises objects named `BSXFlags*`,
   `BSFurnitureMarkerNode*` and an INV marker (nif/export_nif.py:932,963-970) [V].
5. DDS writing: Pillow 13 writes BC1/BC3/DXT5 but not BC7 and not BC5-from-RGBA [V tested: "cannot write pixel format BC7"],
   and the test files were single-mip. repo `tools/places/assets/dds.py` is read-only. Need DirectXTex texconv built on Linux
   (supported since 2021, `-nogpu` forces CPU BC7 [V: Walbourn blog, texconv wiki]) or Compressonator (Linux BC7 artefacts
   reported [V]). DynDOLOD's Texconv.exe runs on the play machine already (infra/gpu-box/lod-tools.json:40 [V]).
6. Stack: Community Shaders 1.9.1 is in (mods/dependencies.json id `community-shaders`, runs on 1.7.104 [V]); there is NO row
   for the True PBR plugin. No CBBE/UNP/HIMBO/RaceMenu/BodySlide row [V grep]: bodies are vanilla. xpmsse and pandora rows exist
   (skeleton and behaviour). Argonian armour/mask mods are rows (ancient-argonian-armor, argonian-funerary-masks...).
7. Texel maths: 2K over 1/3/8/20 m is 2048/683/256/102 px/m (4K: 4096/1365/512/205), less 20-40% packing loss. On a 1080p,
   90 degree view, a surface at 2 m shows ~480 screen px/m, at 4 m ~240. A 2K atlas is sharp to ~4 m of object, soft past 8 m.
8. Owner steer folded in: the template swap (new mesh into a copy of a vanilla NIF and record) removes most of the hard work
   for weapons, furniture, containers, clutter, shields and rigid headgear. See "Template swap" below; it is the recommended
   route, ranked there.

## Docs that cover this

- docs/research/skyrim/skyrim-tooling.md:75 says "PyNifly is used already; no GLB pipeline". CONTRADICTED: grep of tools/
  tooling/ infra/ finds nifly C++ only, no PyNifly [V]. This is the one doc to edit (add an "authored meshes" row).
- docs/research/mods/assets-creatures.md:108 "PyNifly Windows only, nifly better headless base": CONFIRMED, plus the CMake finding.
- docs/design/lod.md (cited by niflod.cpp:2) holds the LOD layout we already write.

## Template swap: new mesh into a copy of an existing asset (owner steer)

Idea: copy a vanilla (or mod) NIF, delete its visual shapes, put the new geometry in at the same origin/axes/scale, keep every
other node (collision, extra data, markers, attach points, controllers), save under a new path; copy the record and change only
the model path (and name/stats). Everything keyed to node names, extra data, keywords and the record's type is inherited:
animations, sounds, impact data, havok, activation. Tooling: Blender+PyNifly (import donor, replace shapes, export), or an
nifly C++ tool that swaps shapes inside a donor (extend niflod: it already links nifly). Donor NIFs are on the play machine.
Weapon facts below are [K] from Skyrim modding practice; Nexus 9678238/10492548 describe the same "swap into a vanilla weapon
NIF" workflow [V]; each must be confirmed by reading the donor with nifdump (a per-type measurement is the first trial).

### Weapons, by vanilla type
Common to all melee: root BSFadeNode; the visual BSTriShape(s) with BSLightingShaderProperty; a `bhkCollisionObject` ->
`bhkRigidBody` with a convex/box shape (dropped item; layer WEAPON/CLUTTER); `BSXFlags`; `BSInvMarker` (inventory rotation/zoom);
a `Prn` string extra data naming the bone it sits on when drawn (WeaponSword, WeaponAxe, WeaponMace, WeaponDagger, WeaponBack,
WeaponStaff, WeaponBow); optional blood/edge effect shape; a separate `_scb` scabbard NIF for swords/daggers. Grip is at the
NIF origin, the weapon extends along one fixed axis (the blade axis of vanilla; read it from the donor), scale 1 unit=1.43 cm.
Animations are bone-driven by the hand bone: the mesh just rides the hand, so ANY mesh at the donor's grip origin/axis swings
exactly like the donor. What can look wrong: length beyond the donor changes visual reach but not real reach (hit detection
uses the WEAP's reach and the actor, not the mesh), so long models clip into targets/ground and short ones whiff visually.
Safe length band: donor length +/-20%; beyond that, change the WEAP reach only through the WEAP record (reach field) and
accept visual mismatch. Width/thickness matter less; a big head on an axe changes the sheathed silhouette on the hip/back and
can clip the body or cape.
- Sword (1H): donor an iron/steel sword NIF plus its `_scb`. Sheath position is carried by the scabbard NIF's own attach node,
  so a new blade needs a new scabbard only if the blade is wider than the donor scabbard (else keep the donor scabbard, new
  blade hides inside). Record: copy the donor WEAP, change model, name, stats; keep animation type (OneHandSword), keywords
  (WeapTypeSword), impact data set, sounds (ITM sound refs). Plain swap: YES. Coverage: ~95% incl. first person (first-person
  uses the same model rig through the arms; some weapons carry a 1st-person STAT in WEAP WNAM, copy it as is) [K].
- Dagger: same as sword (reverse grip animation set; length band shorter, ~30-40 cm); sheath on the hip/back by the donor's
  Prn. Plain swap: YES.
- War axe / mace (1H): head-heavy; grip at the handle base; plain swap YES, keep the handle length of the donor so the
  swing arc and head position match the collision/impact. Sheath Prn WeaponAxe/WeaponMace.
- Warhammer / battleaxe / greatsword (2H): worn on the back (WeaponBack) with no scabbard; swap YES, with the larger length
  band (donor +/-15%) because two-handed grips need the second-hand position at a fixed place along the shaft: the visual
  hands are positioned by animation, not by the mesh, so if the shaft is shorter than the donor the off-hand floats off it.
- Staff (1H "staff" animation type): the staff is carried with idle and cast animation; vanilla staffs use the staff animation
  set and an enchantment effect; a swap works like a sword with the grip at the staff's centre, length ~ donor; no scabbard,
  worn on the back with its own Prn. Plain swap: YES-with-care (the head node often has effect shapes/NiPSys glow: keep or drop).
  Spell-casting staffs have no special collision.
- NOT plain swaps: Bows and crossbows: the limbs are skinned to bones, the string is a second skinned shape, the draw animation
  moves bones in the NIF via the behaviour graph (a bow is armed at a "WeaponBow" node and the 1st-person bow is a separate
  model, `WEAP.WNAM`), crossbows (Dawnguard) add bolt nodes; a new mesh must be re-skinned to the donor's bones with the same
  names; HARD. Spears/tridents: Skyrim has no spear class; mods use the 2H (or staff) animation set, which reads wrong
  (thrusting with a sweeping animation); the template swap works only visually (swap onto a greatsword or staff donor) and
  looks wrong in motion: avoid unless a mod already ships a spear animation set (e.g. our `animated-armoury`, `heavy-armory`
  rows exist [V in deps] - check whether they include spear animations before sourcing art). Blowguns: no vanilla analogue,
  would be a bow-type reskin: NOT WORTH IT.
- Can the record simply copy a vanilla WEAP and change only the model path? Yes for melee [K]: the WEAP holds the animation
  type, keywords, sounds, impact data, reach, speed and enchantment slot; change MODL (and optionally the name/stats). Add
  MODT only if the model changes the vertex format (omit and the engine rebuilds). Add a `Prn`/BSInvMarker copy in the NIF.
  Chance of mismatched feel: scale of the mesh changes only the visual.

### Other categories, rated by how completely a template swap covers them
Rank (most to least covered by pure swap; "inherits" = what comes free):
1. Rigid helmets/masks/circlets/shields/jewellery (slot 30/31/42/35/39): donor ARMA/ARMO + NIF; inherits biped slot, skinned
   single-bone or few-bone weights, first-person/ground model, armour rating, equip sound, enchantment slot. Swap geometry
   onto the same bones (copy donor weights by nearest vertex). Beast heads: pick a donor that already has an Argonian ARMA
   variant (our armour mods do) [K]. Shield: also inherits block animation fit and the SHIELD Prn.
2. Containers (chests, barrels, sacks, urns): donor CONT/ACTI NIF includes the open/close animated lid (a NiControllerManager
   with animation keys, "Open"/"Close" sequences) and sounds; swap only if the new mesh keeps the lid as a separate part with
   the donor's node name and pivot; else the animation breaks. Medium-high coverage for non-animated containers (sacks,
   urns whose lid is not animated) and none for chests with hinged lids.
3. Movable clutter (bowls, jugs, baskets, idols, skulls, mugs): donor MISC/STAT NIF with bhkRigidBody, mass, material, impact
   data, sounds, INV marker; swap geometry, keep rigid body, change collision hull to match only if the size differs >30%.
   Inherits drop physics, pickup, weight/value (record), impact sounds by material.
4. Furniture (beds, bedrolls, chairs, benches, hammocks, stools): donor FURN NIF keeps the BSFurnitureMarker (FRN) entries and
   collision; record keeps keywords/workbench flags; inherits all sit/lie/lean animations and entry points. Dimension limit: the
   marker height/offset must still match the new surface (mattress top within ~5 cm of the donor's marker height) or the actor
   floats or sinks (Nexus threads 6319666, 5140400 [V]). Hammock has no vanilla donor (hammock = bed animation on a low
   suspended mesh; use a bedroll marker raised): medium.
5. Harvestable flora (FLOR, ingredient plants, mushrooms, some trees): donor NIF has a pick-up activator, optional
   switch/harvested-state nodes and collision and "ripe"/"empty" model pair; record keeps PFIG/ingredient, SNAM sounds; swap shapes
   keeping node names; inherits the harvest animation/state if the structure is identical. Medium coverage; plants are small
   and are the closest to "reuse vanilla flora behaviour with new geometry".
6. Doors (loading doors and ordinary doors): swapping door geometry into a donor keeps the animated hinge (controller) and the
   teleport link; the frame and room-side must match donor size; medium coverage; interiors reuse existing cell doors.
7. Activators (levers, wells, braziers with sounds): donor ACTI carries animation/sound; low-medium: swap works only if the
   moving part keeps the donor's node name; otherwise static.
8. Lights (lanterns, torches, braziers, candles): donor LIGH+STAT NIF includes an attach point and fire/glow effect nodes; swap
   the geometry only, keep the light/flame nodes and the `AddOn`/effect shape: inherits light radius, flicker, emissive glow;
   small and easy; flame/ember nodes need to sit within ~10 cm of the new wick or the light looks wrong.
9. Armour body/cloth: little coverage (skin to body, partitions, sliders): template swap only helps if the generated outfit is
   fitted onto the vanilla body weights with a donor ARMA. HARD.
10. Trees (wind): swap trunk skin onto donor BSTreeNode bones, keep leaf cards (hybrid route) - partial coverage; see tree section.
Summary: swap covers weapons (melee) ~95%, rigid headwear/shields/jewellery ~90%, clutter ~85%, furniture ~80% (with marker
dimension limit), lights ~80%, harvestable flora ~60%, containers ~60% (static-lid only), doors/activators ~40%, bows ~10%,
full outfits ~10%.
Caveats: collision of the donor must fit the new shape (a hull from the donor may be larger/smaller: re-derive the hull from
the new mesh with PyNifly or niflod and keep the donor's material/layer/mass); donor NIFs from mods are permission-tied, so
prefer vanilla donors, and avoid donors from King of the Murkmire ("do not make use of AI") [V docs/research/mods/assets-creatures.md].

## Texel density table

px/m = texture_px / extent_m, UV use 100%.

| Object | 1 m | 3 m | 8 m | 20 m |
|---|---|---|---|---|
| 2048 | 2048 | 683 | 256 | 102 |
| 4096 | 4096 | 1365 | 512 | 205 |

Vanilla reference [K, unverified; needs a catalogue measurement]: Nordic architecture tiles 512-2048 px materials about every 2-4
m (~150-500 px/m); clutter ~500-1000 px/m. An 8 m hut at 256 px/m is vanilla-architecture level but one unique blurry
painting without detail; 20 m at ~100 px/m is below any vanilla building. Mitigations, best first: (a) split into parts, each its
own atlas (x4 density); (b) retexture with vanilla/Tropical Skyrim/BM&V tileable swamp wood, thatch, mud, re-unwrapped to tile
(generated geometry only for silhouette); (c) low-res generated colour + tiling detail (the SSE lighting shader has no true detail
map, partial only); (d) vertex-colour tint to break repetition; (e) accept softness for distant-only things.

## Per-category recipes (from-scratch route)

Front half common to all [K unless marked]:
 A. Generator GLB (Tripo: smart low-poly 500-20 000 faces, 10 000 max with quad, quad output FBX only, triangles GLB, texture
    size up to 8192 on the convert endpoint [V search; numbers differ per wrapper/version]). Ask for triangles, ~2-6k faces, 2K.
 B. Blender headless: import GLB, apply transforms, scale to metres then 70 units/m, Z up, set origin, merge by distance,
    recalc normals, delete loose, decimate, re-UV (Smart UV/xatlas) with padding, bake lighting out.
 C. Textures to DDS: diffuse BC1 (opaque) or BC3 (alpha), normal `_n` BC7 or BC5, mips; specular in normal alpha (non-PBR).
 D. NIF: BSFadeNode, BSTriShape + BSLightingShaderProperty + BSShaderTextureSet (niflod writes this), BSXFlags, bounds, collision.
 E. Records in Spriggit YAML (STAT/MISC/FURN/ACTI/ARMO+ARMA/WEAP/TREE/FLOR/GRAS), paths under meshes/argonia and textures/argonia.
 F. Validate off game (nifdump re-read, GLB render, xEdit check), then an owner check in game (CLAUDE.md "Never").

1. Static clutter/decor: A-D; collision convex or box, layer STATIC, BSXFlags havok bit; STAT; lantern light via LIGH ref.
   Failures: wrong scale (70/m), origin off centre, no collision (walk-through) or box too big (invisible wall), baked light
   double-lit, flipped normals, 8-30k triangle pot, alpha without alpha test flag, missing OBND. Headless: yes.
2. Movable clutter/misc: plus bhkRigidBody with mass, layer CLUTTER, material, convex only; MISC record; BSInvMarker for
   inventory centring [V PyNifly makes INV]. Failures: mass/shape mismatch (launching or sinking), concave dynamic collision,
   origin not at centre of mass, mass 0, zero collision radius falls through floors (PyNifly does not convert radius [V]).
3. Furniture: NIF needs shapes, collision and BSFurnitureMarker (FRN) [V Nexus article 52322, Beyond Skyrim "Nifskope Furniture
   tutorial"]; PyNifly exports `BSFurnitureMarkerNode*` objects [V]; FURN record. From scratch marker parameters must be copied
   from a vanilla bed: kitbash instead. Failures: markers lost in old NifSkope SE, offsets wrong, actors sink/float.
4. Architecture/huts: walkable MOPP + compressed mesh collision from a clean proxy; door/activator parts separate; navmesh
   needed (CK generation unreliable under Proton, skyrim-tooling.md:72 [V]); LOD via niflod. Failures: texel density,
   missing/too tight collision, steps not walkable, one-sided faces from inside, baked AO vs real shadows, navmesh blocked.
5. Trees/plants [V partial: Nexus 5427787, 10392218; DynDOLOD Tree LOD page]: TREE record with a BSTreeNode (bone list
   drives trunk sway) or BSLeafAnimNode root; the CK refuses others ("is not a BSTreeNode or a BSLeafAnimNode"); leaves are
   alpha-tested cards, vertex alpha is wind weight not transparency (nifglb.py:13-14, TREE_ANIM flag [V]). A plain STAT tree
   works but is still. Harvestable: FLOR with ingredient, harvest sound, harvested state; grass GRAS (cross cards, wind by
   vertex alpha; Community Shaders grass lighting in stack [V]). Tree LOD [V dyndolod.info]: one front-view billboard per tree
   in Textures\Terrain\LODGen (max 256 per atlas, no normals, upright only); ultra tree LOD (object LOD) takes 3D LOD NIFs or
   hybrid; our DynDOLOD runs on the play machine (infra/gpu-box/lod.ps1). A solid generated trunk/roots/knees/stump can do
   silhouette variety as statics, cannot sway, has no leaf cards or wind weights. Hybrid: keep donor BSTreeNode + leaf cards
   + bones, replace trunk skinned to the same bones (Nexus mod page does exactly this [V search]); never run SSE NIF Optimizer on
   trees [V]. Budget <5-8k tris per tree.
6. Boats/wrecks: large statics, walkable MOPP + deck navmesh, no buoyancy (vanilla boats are static); wrecks need only a hull
   convex or boxes. Failures: z-fighting with water, collision clipping, sails need double-sided alpha.
7. Weapons from scratch: see swap section; scratch only when no donor exists. First-person: same NIF, WEAP WNAM optional.
8. Armour/clothing: skinned BSTriShape to the XPMSSE skeleton, 4 weights per vertex, BSDismember partitions per biped slot
   (30 head, 32 body, 33 hands, 34 forearms, 35 amulet, 37 feet, 39 shield, 42 circlet...) [K], `_0`/`_1` weight files for NPC
   weight sliders, `_gnd` ground model, ARMA (race, slot, male/female/first-person models) + ARMO, beast-race variants for
   Argonian/Khajiit heads and the tail, vanilla body only (no CBBE in deps [V]), no HDT-SMP/CBPC rows so no cloth physics.
   Weights: Blender Data Transfer from the vanilla body then PyNifly export (4-weight cap enforced [V]); Outfit Studio is a
   Windows GUI. Rigid add-ons (mask, shoulder, necklace, headdress) are single-bone weight 1.0: realistic. Full outfits drape
   badly and need hand fit.
9. Shields, masks, jewellery, headdresses: CONFIRMED the easy end (single-bone, rigid), subject to beast-head fitting for
   Argonian masks and shield bone/grip alignment.

## Tool chain

| Step | Tool | Linux headless | State |
|---|---|---|---|
| Mesh clean/decimate/UV/bake | Blender `-b --python` [K] | yes (CPU) | not installed |
| NIF IO | PyNifly | needs libNiflyDLL.so + loader patch: PARTIAL | nifly already built |
| NIF IO alt | niflod/nifdump (nifly C++) | yes, proven | extend: bhkRigidBody/shape, BSXFlags, BSInvMarker, donor shape swap |
| Collision | PyNifly [V]; CK (GUI); ChunkMerge, NifUtilsSuite, 3ds Max Niftools (Windows); blender-niftools-addon (SE limited) | PyNifly only | |
| Skin weights | Blender Data Transfer; Outfit Studio (GUI) | Blender yes | |
| DDS write | DirectXTex texconv (Linux build), Compressonator, texconv-custom-dll; Pillow BC1/BC3 only [V] | build | none here |
| DDS read | Pillow (dds.py) [V] | yes | have |
| Normal map | Skyrim `_n` tangent-space, green = up (OpenGL), same as glTF; DirectX packs need G flipped; specular in alpha [K, confirm by a test render] | | |
| glTF PBR to Skyrim | base colour -> diffuse (de-light), normal -> `_n`, metal/rough -> spec in alpha approx [K]; True PBR needs CS plugin, no row [V] | | |
| De-light | ask for unlit albedo; else high-pass/numpy heuristics or re-bake onto clean UV; numpy/scipy/skimage present [V] | yes | |
| NIF optimise | Cathedral Assets Optimizer, SSE NIF Optimizer (Windows); not needed with clean writer; never on trees | Wine/Windows | |
| Validation | nifdump + GLB render [V], niflod --info [V], xEdit check (Wine/play machine), NifSkope manual only | partial | add a NIF linter |
| In game | owner check | play machine | |

Add once (building blocks): Blender + bpy pipeline script; Linux NiflyDLL or niflod extension; texconv Linux build with BC7;
NIF linter; record templates per category; donor-swap tool.

## Budgets [K] and AI-mesh failures
Triangles: small clutter 100-1500; large clutter/furniture 1500-6000; weapon 2000-8000; armour piece 5-20k body, 2-6k helmet; tree
3-12k plus cards; architecture kit piece 500-8000 per 4 m. Textures: clutter 512-1024; weapon/armour/furniture 1024-2048;
architecture tiled 1024-2048. Limits: 65 535 vertices per BSTriShape (u16 indices; niflod.cpp:15 [V]), 4 bone weights, power-
of-two DDS with mips. AI failures: 30-300k dense triangles, non-manifold/inside faces, tiny/unpadded UV islands bleeding in mips,
baked light/AO in albedo, lost PBR, asymmetry, thin unwalkable geometry, wrong scale. Fixes: decimate to budget, merge, recalc
normals, re-unwrap with 8+ px padding at 2K, bake high->low normal map from the dense mesh, de-light, separate collision proxy.

## Difficulty ladder (agent pipeline)

| Category | Rating | Reason | One-time block |
|---|---|---|---|
| Melee weapons by template swap | EASY | grip/axis match, inherited everything | donor-swap tool + per-type donor table (read by nifdump) |
| Rigid helmets/masks/shields/jewellery | EASY-MEDIUM | single-bone, donor ARMA; beast head fit | single-bone skinned export + donor weight copy |
| 1 Static clutter | EASY | niflod writes NIF now | Blender clean/bake -> NIF + convex collision -> texconv |
| 2 Movable clutter | MEDIUM (EASY by swap) | rigid body tuning | bhkRigidBody presets per size class |
| 3 Furniture | MEDIUM by swap, HARD from scratch | marker height match | donor-swap with bounds fit |
| Lights, containers (static lid) | EASY-MEDIUM by swap | keep effect/anim nodes | donor-swap |
| Harvestable flora | MEDIUM by swap | state nodes | donor-swap |
| 4 Architecture/huts | HARD above 3 m; MEDIUM small pieces | density, walkable collision, navmesh | part splitter + tiling retexture |
| 5 Trees | EASY rigid stumps/logs/roots; MEDIUM-HARD hybrid wind; NOT WORTH IT new harvest flora/LOD billboards | wind/LOD machinery | hybrid trunk swap |
| 6 Boats/wrecks | wrecks EASY-MEDIUM; small boats MEDIUM; walkable ships HARD | scale, deck | split-in-parts |
| Bows/crossbows, blowguns | HARD / NOT WORTH IT | skinned and animated | none |
| Spears/tridents | NOT WORTH IT unless a spear animation mod is already in the stack | wrong animation set | |
| 8 Full outfits | HARD | weights, slots, beast races | body weight transfer |
| Doors/activators | MEDIUM-HARD | animated parts | donor-swap |

## Open unknowns for a real trial
1. Does NiflyDLL build as a Linux .so and PyNifly run in Linux headless Blender?
2. Does an SSE NIF written by our tools render like vanilla: shader flags, normal green channel, specular in alpha, vertex colour?
3. Does a decimated Tripo mesh keep a usable, de-lit albedo through the DDS mip chain?
4. Real vanilla texel density (measure with nifdump plus DDS sizes; data is on the play machine only).
5. For each weapon type: the donor's blade axis, grip origin, length band, Prn name, whether a first-person model is required.
6. Skin-weight transfer quality for rigid headwear on Argonian/Khajiit heads.
7. Furniture marker tolerances; whether donors survive a PyNifly round trip.
8. Navmesh for authored buildings (CK unreliable under Proton).
9. Whether our animation mods (animated-armoury, heavy-armory) include spear/other animation sets.
10. Permissions: King of the Murkmire forbids AI use [V docs/research/mods/assets-creatures.md]; keep donors vanilla.

## Recommendations
1. First trial: one melee weapon by donor swap (steel sword) and one clutter piece by donor swap; evidence: all weapon behaviour
   is bone/record driven (this report) and niflod already links nifly.
2. Extend niflod (or build NiflyDLL .so) before installing anything large; Blender is needed either way for decimation and bake.
3. Edit docs/research/skyrim/skyrim-tooling.md:75 (false "PyNifly is used already").
4. Measure vanilla texel density once from the catalogue before the owner picks architecture work.

Sources: github.com/BadDogSkyrim/PyNifly (README, DEVELOPERS.md, RELEASE_NOTES.md, docs/mopp_format.md, NiflyDLL/CMakeLists.txt,
io_scene_nifly/pyn/niflydll.py, nif/export_nif.py, nif/collision.py); github-wiki-see.page/m/BadDogSkyrim/PyNifly/wiki/Collisions;
dyndolod.info/Help/Tree-LOD; wiki.beyondskyrim.org Nifskope_Furniture_tutorial.pdf; nexusmods.com/skyrim/articles/52322;
forums.nexusmods.com topics 5427787, 10392218, 9678238, 10492548, 6319666, 5140400, 8668583; cs.uesp.net/wiki/Blender/Custom_Sword;
github.com/microsoft/DirectXTex/wiki/texconv; walbourn.github.io (DirectXTex Linux); developers.tripo3d.com, docs.comfy.org TripoRetopologyNode.

Covered: repo tools/ tooling/ infra/ docs/research/{skyrim,mods}, nifdump/niflod/dds/nifglb, dependencies.json, PyNifly source, web pages above · Skipped: Beyond Skyrim asset guidelines, Outfit Studio and CAO manuals, CK wiki Furniture (403), NifSkope source, any Blender trial (not installed; no downloads allowed). Template-swap weapon/container/door node details are [K], not read from vanilla NIFs (game data absent on this VM).
