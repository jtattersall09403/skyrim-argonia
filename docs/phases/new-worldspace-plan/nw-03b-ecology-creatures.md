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
* Find out if the lore supports random hostile NPC encounters, and how that should vary by regions (e.g. Naga bandits). If it does, implement these too. As with creatures, level and toughness and frequency should be linked to cell's danger band
* Ecology also covers harvestable plants. Has this been done already in the world build section or not? If not, include them now. For each region, base on lore for the region - what harvestable plants should that region have? And within regions/cells, plan placement rules around the hyperlocal geography (water of the various types, existing trees and groundcover and bushes etc). Mine skyrim to see if anything useful you can learn from how it's done there. Have the same density and variety of harvestable plants as Skyrim has. Source and use mods as asset sources if necessary to add Black Marsh plant types not available in Skyrim; use Tropical Skyrim if it has anything useful; you can repurpose vanilla/tropical skyrim assets and rename them/link them to new black marsh ingredients or whatever if necessary. Do not rebuild LOD.

Deploy the above onto the play machine.

DO NOT change the terrain or trees or scatter or groundcover. Do not do anything that would require rebuilding LOD. Do not rebuild the terrain or Helstrom or anything else that has already been built.

