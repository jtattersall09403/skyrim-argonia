# What Skyrim's places give the player

Every new-world place lists what it gives the player as hard gameplay (owner ruling 2026-11-09). The kinds and the
combat-to-reward rule below are measured from how Bethesda did it (decision 0034). The counts are the load order's
winners in Skyrim.esm, Update, Dawnguard, HearthFires and Dragonborn, read by
`dotnet out/tools/ArgoniaPlugin/ArgoniaPlugin.dll gives <the five .esm paths>` (tools/ArgoniaPlugin/GiveStudy.cs).
That tool prints counts only. No game text is read or stored (decision 0003).

The kinds live in `newworld/sources/research/give_kinds.json`: 47 kinds in 9 groups. A place record points at them by
id (see newworld/sources/research/FORMAT.md, "Gives").

## The measured counts

| What | Count in Skyrim + DLC |
|---|---|
| Map markers | 471: Cave 81, NordicRuins 40, Fort 33, Shack 20, Landmark 19, DwemerRuin 16, Imperial/Stormcloak camps 26, Mine 12, Shipwreck 12, Settlement 12, GiantCamp 12, Doomstone 11, DragonLair 11, Town 11, Stable 5, Shrine 5, BeastStone 5, OrcStronghold 4 |
| Vendor factions with members, by buy list | general (all but Key, VendorNoSale) 29; innkeeper or food 29; blacksmith (AnimalHide, Armor, Arrow, OreIngot, Tool, Weapon) 24; apothecary (AnimalPart, Food, FoodRaw, Ingredient, Poison, Potion, Recipe) 22; spells (Book, Clothing, DaedricArtifact, Jewelry, Scroll, SoulGem, SpellTome, Staff) 17; jeweller (Gem, Jewelry, OreIngot, Tool) 3; fletcher (Armor, Arrow, Tool, Weapon) 2; clothier 1; bookseller (Book, SpellTome) 1; stolen-only fence 1; roaming hunters (AnimalHide, AnimalPart, FoodRaw) 24 NPCs |
| Spell tomes by school | Conjuration 29, Destruction 27, Restoration 22, Alteration 17, Illusion 16 (111 in all, Novice to Master) |
| Crafting furniture placed, by keyword | cooking pot 260 (197 small pots, 63 spits), tempering in all 211, alchemy lab 167, tanning rack 133, grindstone 120, enchanter 101, forge 100, armour workbench 91, smelter 41, oven 3, staff enchanter 1 |
| Trainers (JobTrainer faction members) | 54: Master 21, Expert 22, Journeyman 11. Every one of the 18 skills has an Expert and a Master. The class sets the cap: Journeyman 50, Expert 75, Master 90 |
| Shrine blessings (TempleBlessingScript) | Talos 20, Arkay 15, Dibella 11, Kynareth 10, Mara 10, Akatosh 9, Zenithar 9, Julianos 8, Stendarr 8, Auriel 4, Nocturnal 1 |
| Standing stones | 13 Doomstones (powerShrineScript) and 5 Skaal stones |
| Word walls | 60 placed (47 Skyrim, 4 Dawnguard, 9 Dragonborn); 117 shouts, 107 words |
| Ore veins (MineOreScript) | iron 694, corundum 249, silver 119, gold 97, orichalcum 93, clay 85, quicksilver 73, moonstone 58, stone 57, ebony 47, malachite 35, heart stone 28, stalhrim 22, gem geodes 52 |
| Harvestables | 70 ingredient kinds. Commonest: mountain flowers 6152, hanging moss 1895, snowberry 1837. Rarest worth naming: giant lichen 143, swamp fungal pod 143, pearls 157, glow plants 66. Coin purses 806 |
| Containers | boss chests 255 (bandit 80, draugr 67, dwarven 24, warlock 22, falmer 18, vampire 14, hagraven 13, apocrypha 10); other treasure 3645 |
| Beds | 1082 beds, 796 bedrolls; 20 inns (LocTypeInn) |
| Homes and followers | 8 player houses (LocTypePlayerHouse); 67 potential followers |
| Encounter zones | 355: 349 set only a minimum level (6 at 138 zones, 8 at 38, 2 at 36, 10 at 31, 18 at 20 ...); 6 capped; 0 fixed (min = max); 90 never reset |

## How Bethesda pairs combat with reward

- **Every clearable place ends in one boss chest beside its boss.** There are 244 clearable locations and 255 boss
  chests. A boss chest holds gold, gems, jewellery, potions, scrolls, soul gems, lockpicks and a 25% chance of a
  magic item. The 3645 lesser containers along the way hold small amounts.
- **Places by type:** boss chests stand in bandit camps 36, draugr crypts 36, Dwemer ruins 25, warlock lairs 23, forts
  18, falmer hives 16, forsworn camps 11, dragon lairs 10, hagraven nests 10, vampire lairs 10 and dragon priest
  lairs 8. Dragon priests also guard a fixed mask.
- **The difficulty comes from the encounter zone's minimum level.** Foes are never below it: 6 for most places, up to
  40 for the deepest.
- **The loot ladder is player-levelled, so we do not copy it.** Almost every boss-chest list carries
  CalculateFromAllLevelsLessThanOrEqualPlayer, so the loot follows the player and not the place. The levels it climbs
  are still the scale we use:
  - Swords: steel 1, Orcish 6, Dwarven 12, Elven 19, glass 27, ebony 36, Daedric 46.
  - Heavy cuirasses: iron 1, steel 6, Dwarven 12, steel plate 18, Orcish 25, ebony 32, dragonplate 40, Daedric 48.
  - Light cuirasses: leather or studded 1 to 6, Elven 12, scaled 19, gilded Elven 27, glass 36, dragonscale 46.
  - Boss gold, draugr: 50, 100, 150, 200, 250 at levels 1, 6, 11, 16 and 21.
- **No vanilla zone is fixed.** Bethesda's non-levelling answer is to give a zone a high minimum level and never
  reset it. Ours goes further and fixes both sides (decision 0035):
  - Each place's foes stand at its band's `foe_level`.
  - Its reward is cut at the same level on the ladder above: fixed items, or levelled lists whose entries all sit at
    level 1, so the player's level never changes them.

## The reward rule by danger band

A combat give must name its reward: a loot give (boss-chest, treasure, gold-hoard or unique-item) at the same place.
The reward's tier is the place's danger band. The player's level never counts.

| Band | Foes (level) | Combat allowed | Reward at that tier (Bethesda's ladder at the band's level) |
|---|---|---|---|
| D0 Safe | 0 | none | none |
| D1 Settled | 1 | combat-foes, combat-creature | treasure: up to 50 gold, iron and steel, leather, common potions |
| D2 Wild | 10 | + combat-boss | boss-chest: about 150 gold, Orcish and Dwarven arms, Elven light armour, a minor enchanted item |
| D3 Dangerous | 20 | as D2 | boss-chest: about 250 gold, Elven and steel-plate arms, scaled armour, a lesser magic item |
| D4 Deadly | 35 | as D2 | boss-chest + gold-hoard: glass and ebony arms, Orcish heavy armour, a greater magic item |
| D5 Lethal | 50 | as D2 | boss-chest + unique-item: Daedric, dragonplate and dragonscale, one named fixed item |

- The gold above level 21 is not on Bethesda's list. D4 and D5 add a gold-hoard or a unique item rather than more
  coin.
- Skill rewards (trainer, word-wall, standing-stone) never pay for combat. In Skyrim they sit behind the fight, as
  word walls do in 60 crypts, and are listed as gives of their own.
