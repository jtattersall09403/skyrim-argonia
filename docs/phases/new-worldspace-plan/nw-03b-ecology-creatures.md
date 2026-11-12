# Ecology and creatures between places

Goal: Author and deliver ecology and between-place creature spawning for our new Argonia world.

# What already exists
* Loads of Black Marsh relevant creatures from mods (and some from vanilla skyrim, like torch bugs), that we know already work
* Lots of good stuff on this was already done for the earlier version of this repo that tried to generate a mod world. Find this and adapt it/build on it. It wasn't perfect but probably some useful stuff
* Ecology research and lore dossiers. Check how complete they are for each of our regions and do additional research to fill any gaps (e.g. from UESP). We need to know what types of creatures each of our region should have. Whatever you can't get directly, extrapolate as logically as possible from the lore and ecology research.

# What we want
* Like with trees and groundcover and weather, we want per-region ecology. There can be *some* overlap in creature types between places (e.g. probably torch bugs in several marshy type areas), but minimal. Each region shoul feel distinctive, whilst being consistently part of the overall province.
* Full range of creature types across the province, from tiny torch bugs & other insects through things like frogs/toads, small animals, larger game, up to giant monsters. Our province should feel rich and alive.
* As wide a range as possible of creatures of each type, from the mods available, to meet our authored requirements for each region's ecology
* Mix of hostile and benign creatures
* No need to work on their behaviour - default behaviour from mods should be fine
* Creature types, toughness, and frequency of hostile encounters also influenced by danger band per cell. Lower danger band = mostly benign creatures, low level of creature toughness/strength; highest band = many, high level, difficult hostile encounters. Never levelled to the *player*; 'difficulty' is set by the band (early game players should find it very hard and lethal going into higher danger band areas; you 'earn the right' to go there through the game by getting stronger. High level players should find the highest danger bands much easier but still an interesting challenge, and the low danger bands trivial).
* Each creature type's spawn points within regions logically derived from local ecology - in water (different water types probably will have different creatures) vs on land; in the open vs under tree canopy vs in bushes; etc. There are lots of things that should influence spawn locations beyond what I've said here - you come up with them and implement them.
* Don't create 'dens' for creatures or add any other models to the world other than the creatures themselves (and harvestable plants if necessary; see below).
* Find out if the lore supports random hostile NPC encounters, and how that should vary by regions (e.g. Naga bandits). If it does, implement these too. As with creatures, level and toughness and frequency should be linked to cell's danger band. These NPCs should be widely varied (in a lore consistent way) in terms of appearance and gear. And quality and value of gear should be linked to danger band but also be lore/story consistent with who they are.
* Ecology also covers harvestable plants. Has this been done already in the world build section or not? If not, include them now. For each region, base on lore for the region - what harvestable plants should that region have? And within regions/cells, plan placement rules around the hyperlocal geography (water of the various types, existing trees and groundcover and bushes etc). Mine skyrim to see if anything useful you can learn from how it's done there. Have the same density and variety of harvestable plants as Skyrim has. Source and use mods as asset sources if necessary to add Black Marsh plant types not available in Skyrim; use Tropical Skyrim if it has anything useful; you can repurpose vanilla/tropical skyrim assets and rename them/link them to new black marsh ingredients or whatever if necessary. Do not rebuild LOD.

Deploy the above onto the play machine.

DO NOT change the terrain or trees or scatter or groundcover. Do not do anything that would require rebuilding LOD. Do not rebuild the terrain or Helstrom or anything else that has already been built.


# Delivered (round 1: sources and the pad route; the spawn stage is owed)

- Census of creature and harvestable sources: `tools/newworld/ecology/census.py` (out/newworld/ecology/census.json). HTBM, Curse of Cipactli, King of the Murkmire and Tropical Skyrim are asset-only on the New World card, so their creatures must be copied into our world file (as the flora stage copies bases) to spawn.
- Skyrim's measures: `tools/newworld/ecology/measure.py` -> `newworld/sources/ecology/skyrim_measures.json` (creatures 25.5 per 100 cells; shore 77, forest 60, mountain 14, open 12, water 8; 70% levelled lists, 38% hostile; groups mean 1.56; harvestables shore 460, forest 386, mountain 79, water 75, open 12.5 per 100 cells; 278 encounter zones, mostly via locations).
- Per-region ecology, all 24 regions: `newworld/sources/ecology/regions/*.json` (347 creature rows over five size classes, 100 signatures, no kind a signature in more than 2 regions, each row cited or a stated extrapolation; harvestables per region) and `npc_encounters.json` (23 of 24 regions have lore-backed hostile groups). The mod record behind each kind is not yet verified.
- Harvestables already in the world: 31 King of the Murkmire FLOR bases with ingredients, 35,343 refs, placed by the flora stage.
- Pad route: the New World card's new game starts at `ArgoniaNWStart` (Argonia.esp's MQ101 fragment finds the new world's marker and `ANW_TravelGive`: race menu, clothes, the power on the shout button; the Lilmoth opening is the other card's); a lesser power "Argonia Travel" (nested menus, data in `newworld/sources/travel/menu.json`, scripts in `papyrus/ANW_Travel*.psc`); built at the next world rebuild, compiled by deploy.

# Delivered (round 2: the ecology stage)

- Every creature kind bound to real records or dropped with its reason (`newworld/sources/ecology/bindings.json`: 68 of 96 kinds, 167 records); each lore-backed hostile group bound to varied looks and band gear tiers.
- The rebuild stage `ecology` (`tools/newworld/ecology/place.py`), its check and its readback rows; band actors at fixed levels written as ACHR by the world writer; green on the small world (91 actors). The recipe: [ecology](../../design/ecology.md).
- Harvestables measured per region against Skyrim and the region tables (ecology.md, Harvestables); none added.

Owed: the full rebuild and deploy, binding the regions' lore harvestables to FLOR and INGR records where a region lacks them (the sea first), and the owner's walk (nw-03b-walk.md).

Pad route walk spots (menu page "Walk-check spots", `SPOTS` in `tools/newworld/teleports.py`): D1 Cape Percar (-43,-197); D5 Murkwood (-6,-141); fresh water Banujha Basin (-26,-175); salt water Aphon Isle (-69,-186); canopy Arnesian Jungle (47,-120) against open (44,-114); night insects Nushara Bayou (37,-177); hostile people band Chixathe Mesa (17,-133, a band in the small world's draw); harvestables Ultherus Swamp (13,-183); dry Aunike Ridge (-20,-163); sea shore Hatandros Bight (61,-133).
