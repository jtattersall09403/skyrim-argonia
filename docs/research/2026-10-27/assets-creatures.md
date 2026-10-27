# Argonia on OpenMW 0.51: assets, creatures, Skyrim content, performance

Researched 2026-10-27 by web search and fetch. Some Nexus/ModDB/OpenMW-forum pages refused fetch (client errors, Anubis), so those items are marked unverified. Repo cross-checks: docs/world/90-asset-strategy.md, docs/research/lore/creature-asset-availability.md, docs/research/placement-settlements/settlement-kit-sourcing-log.md, building-asset-breadth.md.

---

## 1. Morrowind/OpenMW asset mods for a Black Marsh setting

### 1.1 The big shared libraries

**Tamriel_Data** (Nexus morrowind 44537, v26.08, Aug 2026): https://www.nexusmods.com/morrowind/mods/44537
- It is the shared asset base for Tamriel Rebuilt (TR) and Project Tamriel (PT), with assets for "all of the Tamrielic provinces and common races". Since v10 it ships loose files (UESP: https://content1.uesp.net/wiki/Tamriel_Data).
- **Permissions:** you need no permission if you list Tamriel_Data.esm as a dependency. To unpack or reuse assets in your own work, "contact before unpacking"; you credit the creators and never re-upload, pointing users to the official mirrors instead. Some assets carry third-party licences (Sketchfab, freesound).
- **Fit for Black Marsh (verified from TR art reports):**
  - Argonian content: wooden Argonian clutter, Argonian ceramic tableware (in progress), an Argonian skeleton (hostile and as bone clutter), and Argonian-fitted gear. https://tamriel-rebuilt.org/node/10824 and https://tamriel-rebuilt.org/node/10536
  - Region concepts only: Arnesian Jungle/Swamp, the Benthic Yobesh region of Argonia, an Argonian cliff racer, and an Arnesian swamp bullfrog whose model "does not exist yet". https://tamriel-rebuilt.org/node/8624 and https://tamriel-rebuilt.org/node/8650
  - Dres architecture set, "nearly complete" in 2022 (https://tamriel-rebuilt.org/node/7467). This is the Dunmer slaver-plantation style that borders Black Marsh.
  - Waterfronts: Hlaalu waterfront and dock extensions, an Indoril dock set, a Dunmer cargo barge for the Thirr, and ship sets (Gaurong ships, a TR cutter used by a sailing mod).
  - Imperial (Cyrodiil, from PT), Ayleid ruins (the TR Ayleid dungeon in Grasping Fortune plus Ayleid creatures), Nordic, Colovian and Hammerfell sets.
- **No Black Marsh kit exists in Tamriel_Data:** no Argonian stilt or hut architecture, no xanmeer, no Hist trees and no mangroves. Black Marsh itself belongs to the dormant "Eye of Argonia", which TR describes as "not in active development". Only a heightmap ESP exists, and only once mainland Morrowind is finished. https://tamriel-rebuilt.org/node/1602 and https://en.m.uesp.net/wiki/Project_Tamriel

**TR releases nearest Black Marsh.** Grasping Fortune (May 2025) added Narsis, Shipal-Shin, the Coronati Basin/Thirr River and Othreleth Woods (https://content2.m.uesp.net/wiki/UESPWiki:News/Tamriel_Rebuilt_Releases_Grasping_Fortune). The Arnesian Jungle ("the shifting, deceptive northern reaches of Black Marsh", Fort Arnesia, the Argonian village Taj'Xa'thaxi) is still unreleased and partly in TR_Preview (https://content1.uesp.net/wiki/Tamriel_Rebuilt:Arnesian_Jungle). Expect the first real TR swamp/jungle assets with that region, years out.

**OAAB_Data** (Nexus 49042): https://www.nexusmods.com/morrowind/mods/49042
- Contents: architecture, caverns and dungeons, foliage, water, creatures, clutter, armour and clothing. Vvardenfell-focused, but it includes shipwreck and Bitter Coast flavour.
- **Permissions:** adapt, remix and transform freely *for use in Morrowind*, with attribution; non-commercial only. "For use in Morrowind" matters for a forked, standalone OpenMW game: a dependency is safe, extracting assets is grey.

**Project Tamriel: Cyrodiil.** Released: Stirk only. Next: "Abecean Shores" (Gold Coast and Anvil). https://app.uesp.net/wiki/Project_Tamriel:Cyrodiil. These are Imperial-colonial coastal assets and suit Gideon, Soulrest and Stormhold's Imperial layers.

### 1.2 Trees, swamp flora, groundcover

| Mod | Use | Permissions (as stated) |
|---|---|---|
| Forested Morrowind 48975 https://nexusmods.com/morrowind/mods/48975 | Makes the Bitter Coast "much more swampy and overgrown". Bundles trees by Vurt, Remiros, Melchior and others; optional Graht Morrowind Swamp Trees | Page text gave no terms; per-author |
| Classic Morrowind Forested 48756 https://www.nexusmods.com/morrowind/mods/48756 | Leafy and forest replacers | Permissive: asset use, conversion and modification with credit; not in paid mods |
| Graht Morrowind Swamp Trees (58447, page refused) | Big swamp trees, the closest thing to cypress or mangrove in MW. Reused by "TR Border" 56462 (https://www.nexusmods.com/morrowind/mods/56462) | Unverified |
| SM Bitter Coast Tree Replacer 49883 https://modding-openmw.com/mods/sm-bitter-coast-tree-replacer/ | 8 Bitter Coast trees; OpenMW "fully working" | Not stated |
| Vurt's Bitter Coast Trees II, Vurt's Groundcover for OpenMW https://modding-openmw.com/mods/vurts-groundcover-for-openmw/ | The standard swampy trees and grass | Vurt historically open; check per file |
| Bitter Coast Redux I 45708 https://www.nexusmods.com/morrowind/mods/45708 | Muddy, dark Bitter Coast landscape textures | **Restrictive:** no upload, no modification or reuse without permission, conversion forbidden |
| Lush Synthesis 52931 https://modding-openmw.com/lists/total-overhaul/287 | Groundcover remix that includes water plants | Not stated |
| Palm resource 40934 https://www.nexusmods.com/morrowind/mods/40934 | 35 palm NIFs (coast, pirate freeholds) | Free in MW mods; **no editing**; contact the author first; non-commercial |
| West Gash Pines and Parasols 57564 | Parasol trees (savanna or upland) | Asset use with credit; conversion not allowed |
| OAAB Saplings / OAAB Pomegranates 50726 | Small flora | OAAB licence (non-commercial, credit, "for Morrowind") |

**Mangroves:** I found no true mangrove tree pack for Morrowind (searches of Nexus, TR art reports and modding-openmw). The nearest stand-ins are Bitter Coast trees with exposed roots (vanilla, Vurt, Graht). **Hist trees:** I found no Morrowind Hist mesh. "The Unhatched" 57826 has Argonian temple ruins and Hist Dream sequences (https://www.nexusmods.com/morrowind/mods/57826). It depends on TR, TD and OAAB, its assets are "free... contact us first", and it is tagged AI-Generated (Midjourney murals). Avoid the murals.

### 1.3 Argonian people, clothing, kits, boats
- **Argonian Full Helms 53011** (https://www.nexusmods.com/morrowind/mods/53011): 25 Argonian-fitted helms; open with credit.
- **Saxhleel Argonians 59180** (https://www.nexusmods.com/morrowind/mods/59180): an Argonian race replacer built on LizTail Beast Bodies and Westly. Asset use with credit; upstream permissions needed; conversion not allowed. Westly's and LizTail's beast-body resources are the de facto Argonian head and body base in Morrowind.
- **Stilt house, boardwalk, xanmeer kits for Morrowind:** none found. Docks and boardwalks come from Hlaalu, Indoril and vanilla Seyda Neen/Ebonheart docks and OAAB; there is no Argonian dock style.
- **Boats:** there is a wind-driven OpenMW sailing mod using the TR cutter (56471; permissions blank), https://www.nexusmods.com/morrowind/mods/56471. "Your Own Gondola" 53611 (https://www.nexusmods.com/morrowind/mods/53611) has OpenMW collision and the terms "Do whatever you want". These are useful as code and approach references, not art.
- **Imperial forts and towns:** vanilla MW Imperial forts plus TD/PT Cyrodiil, and Imperium Castle Ebonheart 51120 (open with credit). **Dunmer strongholds:** vanilla MW strongholds plus TR Dres and Hlaalu sets.

### 1.4 A note on vanilla Morrowind and the standalone question
Vanilla Morrowind meshes (Bitter Coast, Imperial forts, Dunmer strongholds, creatures) are dependencies only if the player owns Morrowind. Every TD/OAAB consumer is built on MW.esm plus Tribunal and Bloodmoon. A fork that ships on the OpenMW Game Template (public domain; https://assumeru-openmw.readthedocs.io/en/latest/reference/modding/openmw-game-template.html) without MW.esm needs written permission from TD/OAAB to unpack their assets, or else it must require MW ownership. That decides the whole asset plan.

### 1.5 Candid estimate: how much of Black Marsh the Morrowind ecosystem can dress
- **Imperial colonial towns (Gideon), Imperial forts, Dunmer frontier forts (Stormhold's Dres and Hlaalu layers), pirate freeholds, coast, docks, ships, shipwrecks, Ayleid ruins:** about 70–85%, from vanilla MW, TD, OAAB and PT Cyrodiil. Quality is MW-era to TR modern (low poly, coherent).
- **Generic swamp and flooded forest (big gnarled trees, roots, swamp grass, mud textures, fungi):** about 40–60%. It reads as "Bitter Coast", not Murkmire or a tropical jungle.
- **What makes it Argonia (stilt villages, xanmeer step pyramids, Hist trees, mangroves, jungle canopy, Saxhleel architecture, Kothringi remains):** about 5–15% (clutter, one race, a skeleton, temple ruins from one quest mod).
- **Overall:** about 30–40% of a Black Marsh world, and the culturally defining 60% is missing. The Argonian identity has to come from the Skyrim-side pool (BM&V, Xanmeer tileset, KotM, Tropical Skyrim) through local conversion. Otherwise the world reads as "Bitter Coast with Imperial forts".

---

## 2. Creatures for OpenMW

TD creatures ship as working Morrowind actors (NIF plus KF, with text keys), so each has animations. Lists come from UESP's Tamriel Data creature pages:
https://content2.uesp.net/wiki/Tamriel_Data:Beasts, https://app.uesp.net/wiki/Tamriel_Data:Waterdwellers, https://content1.uesp.net/wiki/Tamriel_Data:Insects, https://content1.uesp.net/wiki/Tamriel_Data:Undead, https://app.uesp.net/wiki/Tamriel_Data:Animals, https://app.uesp.net/wiki/Tamriel_Data:Fliers, https://app.uesp.net/wiki/Tamriel_Data:Dungeon_Creatures

**Swamp, coast and Black Marsh-usable creatures in Tamriel_Data:**
- **Swamp Troll and Diseased Swamp Troll.** TR fixed their animations (node/8650).
- Mud Golem, Land Dreugh, Diseased Dreugh, Spriggan (plus Elder and Nymph), and troll variants.
- Sea Crab, Mooncrab and Molecrab.
- Slaughterfish (blind, orange, small and diseased variants), Spearmouth, Sturgeon, Tully and other fish.
- Cephalopods, Bullfrog, Iron Toad, River Newt and Lamia.
- Sload: in TD "but not yet in any project release". Its animation state is uncertain.
- Muck Leech, Swampfly, Muskfly, Parastylus and Ornada (Thirr River).
- Spiders (small, large and matron) and the Riverstrider.
- Danswyrm Viper (snake), Kagouti and Armun Kagouti, Nix-Mount, Guar, Netch and Velk.
- Birds (seagull and others), the Argonian Skeleton, ghosts and wraiths, a Skeleton Pirate.
- Ayleid creatures: Welkynd Spirit, Redeemed Keeper/Sentinel and Sorcerer-King. Also goblins, kobolds and gremlins.

**Vanilla MW/Bloodmoon (needs MW ownership):** mudcrab, slaughterfish, dreugh, alit, kagouti, nix-hound, cliff racer (stand-in for the hackwing, as this repo already does), kwama, netch, plus Bloodmoon spriggan, bear, boar and wolf.

**Not found in the Morrowind ecosystem:** wamasu, hackwing (native model), crocodile or alligator, swamp leviathan, kothringi (use the generic Ghost re-textured), Hist creatures, giant frog or "death hopper" (the TR bullfrog is small, and the Arnesian bullfrog has no model).

**OAAB_Data** tags include creatures. I could not get a verified list (the docs tab refused fetch). Expect Vvardenfell additions rather than swamp megafauna.

**Skyrim-side creatures the previous build relied on** (repo: docs/research/lore/creature-asset-availability.md): the BM&V pool holds the Mihail crocodile, a treant (miregaunt), a slug (voriplasm), river naga, sharks, cliff racer, gant, daedroth and others. KotM credits MihailMods for crocodiles, voriplasms, guars, wamasu, naga and river trolls. All of these are HKX-animated Skyrim actors: see §3c.

**Permissions:** using TD creatures through the dependency is fine. Mihail's pages typically say "not allowed to convert this file to work on other games", with an author note that he "usually authorizes" when asked (https://www.nexusmods.com/skyrimspecialedition/mods/35975). Nexus describes his creatures as "fully open source" (https://www.nexusmods.com/news/13766). Ask him explicitly. CDPR-derived creatures and audio are a separate licence.

---

## 3. Skyrim content in OpenMW

### 3a. Can OpenMW 0.51 render Skyrim SE NIFs referenced from a TES3/omwaddon plugin?
- The 0.49 announcement (https://openmw.org/2025/openmw-0-49-0-released/) says:
  - It has "complete parsing of all official NIF files from Oblivion, Skyrim, and Fallout 3/NV/4/76", gated behind `load unsupported nif files` (experimental; docs warn of "memory corruption, freezes or even crashes", https://openmw-zack.readthedocs.io/en/latest/reference/modding/settings/models.html).
  - "Collision geometry is based on the rendered geometry for games up to 2011 Skyrim" but "isn't generated for Skyrim SE and Fallout 4/76".
  - "Missing skinned geometry for Skyrim SE, particles, any animation".
  - "OpenMW-CS does not currently support newer NIF formats".
- MR 3465 (https://gitlab.com/OpenMW/openmw/-/merge_requests/3465): BSTriShape rendering is "placeholder-ish", there is no SSE skinning ("so no trees"), and there is no collision.
- The 0.50 and 0.51 notes add nothing on ESM4 or newer NIFs (https://openmw.org/?p=6979). 0.51 adds graceful rejection of malformed NIFs, BC6H/BC7 DDS (with the OSG fork), Lua runtime-created statics and creatures, and an object-paging LOD-centre fix.
- **Answer:** NIF loading is independent of the content-file format, so a TES3 or omwaddon Static pointing at a Skyrim NIF does go through the same loader. With the flag on, LE-format (2011) static meshes can show with render-mesh collision. SSE BSTriShape meshes render roughly, with no collision, no skinning and no trees. Skyrim shader properties (BSLightingShaderProperty: normal, specular, env, glow, parallax, vertex-alpha foliage) have no documented complete support. ESM4 (Skyrim's own .esm) loading is a prototype "walking simulator" (https://shazoo.ru/2025/07/05/169931/...). **Do not ship on raw Skyrim NIFs. Convert to Morrowind-format NIF (or OSG/COLLADA) at install time.**

### 3b. Conversion paths for statics
1. **PyNifly** (https://github.com/BadDogSkyrim/PyNifly): Blender import of SSE, LE and FO4 NIFs; GPL-3; **Windows only** (nifly DLL). The underlying **nifly** C++ library (ousnius) is cross-platform and is the better base for a headless install-time converter.
2. **Morrowind Blender plugin io_scene_mw** (Greatness7; https://blender-morrowind.readthedocs.io/en/latest/basics/exporting.html): exports MW NIF plus KF ("Extract Keyframe Data"), with collision through a "collision" node convention.
3. **OpenMW native alternatives** (https://ptmikheev-openmw.readthedocs.io/en/latest/reference/modding/custom-models/index.html): COLLADA (.dae) handles static and animated meshes but "doesn't yet work in all parts of the engine". OSG native handles statics only. Neither licence restricts you. glTF is not supported.
4. **Per-mesh conversion work:**
   - Retarget materials from BSLightingShaderProperty to NiTexturingProperty (base, normal through the OpenMW normal-map convention `_n`, specular `_spec`, glow).
   - Convert SSE BC7 to BC1/BC3 or keep BC7 (0.51 plus the OSG fork).
   - Move vertex-colour alpha on foliage into alpha test.
   - Split meshes over 65k vertices.
   - Decimate, and build a collision mesh (from the bhk shape or a simplified render mesh).
   - Check the scale. Both games use Gamebryo units of roughly 70 per metre, so expect about 1:1, but prove it on a sample before batching.
5. **Community precedent:** effectively no public Skyrim-to-Morrowind ports. A Nexus forum answer says "no known mod does it" and that Skyblivion and Skywind rebuild everything (https://forums.nexusmods.com/topic/13031412-converting-skyrim-assets-to-morrowind-assistance). Nexus moderators say "Using assets from other Bethesda games is not allowed unless you have permission", and that Bethesda "rarely gives permission" (https://forums.nexusmods.com/topic/9720278-questions-about-content-usage-from-other-bethesda-games). Bethesda required Skyblivion to "fully replace 100% of all assets" and to need both games owned (https://en.wikipedia.org/wiki/Skyblivion). **Morroblivion** is the install-time precedent: it was pulled in 2008 over distributing Morrowind assets, then moved to an installer that "deploys converted material from the user's own games" (https://morroblivion.com/morroblivion-faq). Our plan (convert locally, never redistribute) is exactly that model. It is tolerated, not licensed. Bethesda's EULA and CK terms still bind vanilla Skyrim assets to Skyrim, so keep the converter separate and ship no converted output.

### 3c. Skinned creatures, NPCs and HKX animations into OpenMW
- **Meshes:** extract the skinned mesh and skeleton through PyNifly or nifly, then export as an MW skinned NIF on a Bip01-style skeleton. Skyrim skeletons are NPC-rooted and differ per creature, but OpenMW tolerates arbitrary bone names for creatures (the skeleton lives in the NIF).
- **Animations:** Skyrim clips are Havok packfiles (SSE 64-bit).
  - Tools: hkxcmd and hkxpack (LE 32-bit). blender-hkx (https://github.com/jgernandt/blender-hkx; MIT; Blender 3.2; needs a converter built against the Havok SDK 2010, which is not redistributable). PyNifly HKX import/export (Blender 4.4+).
  - Route: HKX to Blender action, then io_scene_mw exports a KF with **hand-authored text keys** (Idle, WalkForward, Attack1 start/hit/stop, Death and so on). Skyrim's behaviour graphs (.hkx behavior and annotations) carry no MW text keys.
- **Feasibility:** proven pieces exist but there is no end-to-end tool and no public precedent. Budget about 1–3 days per creature to set up, then batch it. A plain install-time batch is hard because the HKX unpack needs Havok-SDK tooling. Better: decide the text keys and clip map once per creature as data (yours to ship), and have the installer run only the mechanical extract and resample.
- **Humanoid NPCs:** Skyrim's NPC body, head and FaceGen, plus the behaviour-driven animation set, do not map onto MW's beast-race body and NPC animation set. Use TD/Westly Argonians and MW animations (or OpenMW's animation-blending replacers). Do not port Skyrim NPC animation.

### 3d. Tropical Skyrim and Black Marsh & Valenwood terms
- **Tropical Skyrim** (Soolie, https://www.nexusmods.com/skyrim/mods/33017/): "you MUST contact me and obtain permission before uploading this mod to other sites or using its contents in your own mod." It bundles GKB Green Trees, Muppetpuppet's Moonpath foliage and creatures, Tamira's New Plants, Birds of Skyrim and lookout21 textures, each with its own terms. The repo records owner-held permission from every author in the pool (sourcing log, 2026-09-24). Re-confirm that this covers *conversion to another engine*, not just use in a Skyrim-asset three.js build.
- **Black Marsh & Valenwood** (dalecallen1987, https://www.moddb.com/mods/black-marsh-valenwood): the ModDB page states **no permissions and no credits**. It bundles credited third-party resources (Mihail creatures and others; one `swamp house.nif` is reportedly from Sniper: Ghost Warrior 2, owner-ruled usable per decision 0098 §3). Treat it as "ask the author", with upstream terms inherited per asset.
- **King of the Murkmire** (pancake0723, SSE 190459, https://www.nexusmods.com/skyrimspecialedition/mods/190459): "free for use in your mods if they are released for free and do not make use of AI". Do not redistribute the plugins; seek permission from the relevant authors. Voice: no use. The Xanmeer resource is credited to NorthwindBlue and DarthVitrial; crocodiles and wamasu to MihailMods.
- **Personal local conversion** of files the player downloaded is generally outside what Nexus permission flags govern, since they govern redistribution and derivative releases. But "convert to other games: not allowed" flags (Mihail, Hlaalu 157997, Saxhleel 59180) read against shipping a converter that targets those files by name. Get written OKs from BM&V, Mihail, Soolie and the Xanmeer authors.
- "Sign of Cipactli" was not found by search. Confirm its URL.

---

## 4. Performance: Skyrim-detail meshes in OpenMW on Android (Adreno 830)
- **Android OpenMW status:**
  - No official Play or F-Droid build is current (F-Droid stuck at 0.46, OMW Nightly at 0.48 and discontinued: https://f-droid.org/packages/com.libopenmw.openmw/, https://apt.izzysoft.de/fdroid/index/apk/is.xyz.omw_nightly?repo=archive).
  - Community builds (Sisah2, cavebros, tazok81 https://github.com/tazok81/openmw-android) are compiled per release. Historically they render through gl4es (a GL-to-GLES translation layer) rather than native GLES or Vulkan, which costs CPU per draw call.
  - 0.51 removed the fixed-function pipeline, so shader paths are mandatory.
  - A fork will own its Android build.
- **Cost model:**
  - OpenMW is draw-call and CPU-bound well before it is triangle-bound. Skyrim statics run about 2–20k triangles and trees about 10–60k with several sub-shapes, against MW's 0.3–3k.
  - On a tile-based Adreno, the killer is **alpha-tested foliage overdraw** (dense Skyrim tropical trees, ferns and grass cards) plus shadows, more than raw polygons.
  - Adreno 830-class GPUs can push millions of triangles, but gl4es draw-call overhead and alpha-test-heavy overdraw will cap it.
- **Object paging** (https://openmw-zack.readthedocs.io/en/latest/reference/modding/settings/terrain.html):
  - It batches non-terrain objects outside (and optionally inside) the active grid by merge cost against draw calls saved (`min size`, `merge factor`, `min size cost multiplier`).
  - High-poly meshes have a high merge cost, so they page less and use more RAM. Paging "active grid" helps when CPU-limited but hits light limits.
  - 0.51 keeps NiLODNode centre data, so LOD switch nodes in converted NIFs are a usable lever.
  - modding-openmw tips: raise `object paging min size` (0.023+), view distance at most 7 cells on weak GPUs, halve the shadow map distance, cheaper water (https://modding-openmw.com/tips/performance/).
- **Recommendations for the converter:**
  - Bake a phone quality band. Decimate to about 25–40% of the triangles, cap textures at 1K or 512 (BC1/BC3; check BCn versus ETC2/ASTC support on the chosen GL path), and merge sub-shapes per material.
  - Emit NiLODNode LOD1 and LOD2 and a simplified collision mesh.
  - Convert foliage to OpenMW groundcover (instanced, `[Groundcover]` density and distance) and keep tree cards few.
  - Disable or limit shadows on foliage. Use a 3–5 cell view distance on phones with aggressive paging.
  - Measure on the device before scaling. This repo has no GPU or device lane for Android, so plan one.
