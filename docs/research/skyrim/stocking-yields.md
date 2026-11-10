# What vanilla towns yield, and what the soulslike collection changes (decision 0034)

Measured 2026-11-10 for the stocking scale (`newworld/sources/stock/scale.json`). The scale is ours: these numbers check
it and are not its source. Script: `python -m tools.places stock vanilla` (`tools/places/stock/vanilla.py`), reading
Skyrim.esm with Update.esm (and the DLC masters for item records) through `tools/argonia_world/esm.py`. The split is
the stocking split's own rule (`tools/places/stock/split.py`): gold, *significant* (weapons, armour, jewellery, gems,
soul gems, potions, poisons, scrolls, keys, skill and spell books, anything enchanted or worth 50 or more) and *set
dressing* (the rest).

**Method.** Vanilla levels its lists by the player's level, so a yield has to be read at a level. Each list is read at
the fixed reference levels 1, 10 and 30. The figure is the expected value: a list that picks one entry gives each entry
its share, a use-all list gives every entry, and chance-none is applied. Towns are the 209 interior cells whose editor
id starts with a hold town's name (Riverwood, Whiterun, Ivarstead, Solitude, Windhelm, Riften, Markarth, Falkreath,
Dawnstar, Morthal, Winterhold, Rorikstead, Dragon Bridge, Karthwasten, Shor's Stone). A building's kind is read from
its editor id. A person's role is their Job faction.

## 1. Per building (all containers and loose things in the cell; gold and significant value in gold, level 10)

| Kind | Cells | Containers | Gold, median / mean | Significant, median / mean |
|---|---|---|---|---|
| House | 115 | 17.7 | 19 / 125 | 499 / 1,443 |
| Inn | 16 | 24.7 | 157 / 555 | 370 / 2,238 |
| Shop | 15 | 18.2 | 869 / 829 | 5,291 / 5,266 |
| Keep or palace | 26 | 30.5 | 84 / 516 | 2,067 / 7,149 |
| Guild hall | 11 | 22.5 | 88 / 153 | 1,369 / 2,565 |
| Temple | 12 | 30.5 | 10 / 79 | 253 / 959 |
| Barracks | 6 | 8.7 | 16 / 19 | 222 / 549 |
| Jail | 8 | 24.9 | 0 / 7 | 78 / 260 |

A shop's figure is mostly its merchant chest, which the player cannot reach without stealing. A median house keeps
about 19 gold. The rich few (Breezehome's stock, the noble houses) pull the mean up to about 125. At level 30 a house's
significant value rises a fifth and its gold barely moves: vanilla levels the gear, not the coin.

## 2. Per container kind (per container; level 1 / 10 / 30)

| Kind | Count | Locked | Gold | Significant |
|---|---|---|---|---|
| Barrel | 1,177 | 0 | 0 | 0.3 |
| Sack | 1,143 | 0 | 0 | 0 |
| Chest | 577 | 35 (4 Novice, 17 Apprentice, 4 Adept, 4 Expert, 2 Master, 4 key) | 8 / 8 / 9 | 21 / 34 / 49 |
| End table | 310 | 0 | 3 | 2 / 3 / 6 |
| Wardrobe | 262 | 0 | 2 | 12 / 15 / 21 |
| Dresser | 180 | 0 | 0 | 0 |
| Urn | 167 | 0 | 0 | 0.4 |
| Cupboard | 152 | 0 | 0.5 | 0 |
| Merchant chest | 74 | 1 | 545 | 2,729 / 3,438 / 5,646 |
| Strongbox | 33 | 31 (all Apprentice) | 55 / 102 / 243 | 4 / 13 / 23 |
| Satchel | 32 | 0 | 1 | 73 / 220 / 333 |
| Safe | 10 | 4 (2 Adept, 2 Expert) | 53 / 103 / 303 | 266 / 471 / 945 |
| Boss chest (in town) | 3 | 2 Master | 39 / 66 / 145 | 288 / 432 / 958 |

What this tells the scale: town containers are almost all set dressing (barrels, sacks, dressers and cupboards hold
food and clutter). Value sits in few places and is locked in proportion: chests are mostly open and nearly empty,
every strongbox is locked, and safes hold the most behind the hardest locks.

## 3. Per role (what a person carries; 641 people placed in those cells; level 1 / 10 / 30)

| Role | People | Gold | Significant |
|---|---|---|---|
| Citizen | 412 | 10 / 12 / 18 | 98 / 160 / 262 |
| Merchant | 95 | 11 | 148 / 270 / 425 |
| Jarl | 19 | 32 | 320 / 583 / 906 |
| Smith | 18 | 12 | 176 / 311 / 479 |
| Trainer | 17 | 8 | 143 / 194 / 284 |
| Guard (in town interiors) | 16 | 1 | 82 / 105 / 138 |
| Housecarl | 14 | 9 | 237 / 354 / 497 |
| Bard | 14 | 17 | 200 / 369 / 572 |
| Steward | 12 | 28 | 274 / 522 / 819 |
| Farmer | 7 | 9 | 146 / 264 / 408 |
| Court wizard | 7 | 28 | 268 / 512 / 802 |
| Beggar | 6 | 9 | 81 / 143 / 224 |

Even a jarl carries only about 30 gold. A person's wealth shows in their home and their clothes, not their purse. The
significant value people carry is their weapon and armour, which vanilla levels with the player.

## 4. The level gates (the scale's tiers are checked against these)

The level at which vanilla's lists first hand out each material. The figure is the median over the 921
top-level lists that hold it; a few special lists give anything at level 1, so the minimum would mislead.

| Level | Weapons | Armour |
|---|---|---|
| 1 | iron, steel, silver | hide, iron, iron banded, studded |
| 4 to 8 | imperial (4), orcish (6) | steel, leather (6); imperial light, studded, heavy (7 to 8) |
| 12 | dwarven | dwarven, elven |
| 18 to 19 | elven | steel plate, scaled |
| 25 to 27 | glass | orcish (25), elven gilded (27) |
| 32 to 36 | ebony (36) | ebony (32), glass (36) |
| 40 to 48 | daedric (46) | dragonplate (40), dragonscale (46), daedric (48) |

Enchantment grades (the 01 to 06 of vanilla's enchanted weapons and armour): grade 1 at level 1, 2 at 4, 3 at 9, 4 at
17, 5 at 30, 6 at 43.

The danger bands' foe levels (D1 level 1, D2 10, D3 20, D4 35, D5 50) fall one per tier: T1 gates at 1 to 5, T2 at 6
to 11, T3 at 12 to 24, T4 at 25 to 35, T5 at 36 to 45, and T6 (ledger only) at 46 and over. That is
`scale.json` `danger_tier`.

## 5. Gold lists

Vanilla's gold lists, read at levels 1, 10 and 30:
- Loot gold: LootBanditGold 25 / 38 / 75. Boss chests: LootBanditGoldBoss and LootDraugrGoldBoss01 50 / 100 / 250;
  LootFalmerGoldBoss and LootDwarvenGoldBoss 50 / 75 / 150; LootDragonGold 100 / 150 / 300.
- Coin purses: 11, 20 and 35, not levelled.
- Vendor gold, not levelled: Misc 750, Blacksmith 1,000 (500 in a town, 400 for an Orc stronghold), Apothecary
  500, Spells 500, Inn 100, Street vendor 50; a fence starts at 1,000.

## 6. What the soulslike collection changes about gear strength

Read from each combat plugin of `mods/dependencies.json` (group `combat`, the Nexus collection xyf1u3 and the
owner's additions) as staged in `~/.argonia/stack/MO2/mods`.

Measured:
- **No vanilla weapon or armour record is changed.** No plugin of the collection overrides a vanilla WEAP's damage or
  value, or an ARMO's rating or value. The one exception is Animated Armoury, which overrides 7 WEAP: the Akaviri
  katanas, moved into its katana class.
- **Animated Armoury (`NewArmoury.esp`) adds 204 weapons of new classes** (rapier, pike, halberd, quarterstaff,
  claws, whip, katana) in every vanilla material. Their damage follows the vanilla ladder: iron rapier 5, iron
  sword 7; glass pike 17; ebony halberd 21. It also writes its weapons into 116 of vanilla's levelled lists (and adds
  101 of its own). Our stocking never uses a vanilla list as a list, so this reaches us only if we choose its bases.
  They are new bases for spears and pikes, which fit Black Marsh, but they need NewArmoury.esp as a master or a copy.
- **Stamina** (`Dark Souls Movement and Stamina Regen.esp`) overrides 20 races. Stamina regeneration goes from 5 to
  17 (Argonian) and 22.4 (Breton) per second, and the stamina regeneration delay after damage is 1.5 s (also set by
  NASC). NASC makes normal attacks cost stamina.
- **Poise** (Chocolate Poise, `SKSE/Plugins/ChocolatePoise.ini` and `.json`, read): an actor's poise is a base
  times 10 plus half the weight of their armour. A hit's poise damage is set per weapon class (dagger 2, sword 9,
  greatsword 16, war axe 11, battleaxe 20, mace 13, warhammer 24, bow 8, crossbow 14, pike 11, halberd 14, rapier 6)
  plus half the weapon's weight. Bashes count double. Gear weight therefore buys poise, so heavier materials also
  stagger more and are staggered less.
- **Execution and parry** (`RimExecutionHitSA.esp`, `EREP_patchSA.esp`) add perks and spells for parry, riposte and
  execution damage (RimExeDamage, ExeDamageWeak and the like). They change how often a hit lands hard, not a
  weapon's own numbers.

Not measured: the DLL side of Elden Parry, Elden Counter, Precision, TK Dodge and Stop On Slash (timings and hit
windows sit in compiled code and its settings); the perk entry points' actual multipliers in
`RimExecutionHitSA.esp` (read by name only); and anything in game.

What it means for the scale: the vanilla material ladder stands as the measure of strength, because the collection
leaves damage and armour values alone. Combat is gated by stamina and poise, so a fight turns on skill and weight more
than on a few points of damage. A one-tier step per danger band is therefore felt and is enough, and enchantment
grades stay at the tier's grade, never above. Heavier gear's poise is a reason the carried-in heavy materials (steel
plate, orcish, ebony) stay behind locks.

## 7. The danger bands read for loot (proposed record edits, not made)

The bands were set for foes. Under the stocking scale a settlement's things follow its wealth and a wild place's
follow its band (`scale.json` `danger_tier`; settlements open at T1 whatever their band). Read across all 258 places,
these read wrong for loot:

| Place | Now | Proposed | Why |
|---|---|---|---|
| tribal-camp-m7-m80 | D3 | D4 | It stands in a D5 cell. Reaching it crosses the worst ground in the province, and a D3 boss chest underpays that. |
| peak-m11-m84 | D2; treasure "D1 tier" | D3; treasure "D3 tier" | It stands in a D4 cell. The climb crosses D4 ground, so a D1 pack is no reward. |
| peak-m4-m90 | D2; treasure "D1 tier" | D3; treasure "D3 tier" | As above (D4 cell). |
| tribal-camp-9-m83 | D2; treasure "D1 tier" | D3; treasure "D3 tier" | It stands in a D4 cell. |
| tribal-camp-4-m91 | D2; treasure "D1 tier" | D2; treasure "D2 tier" | The record's band and its treasure disagree; the treasure follows the band. |

Also observed, with no edit proposed:
- No place carries D5, though 153 cells are D5. T5 is reached only by a rich city's vaults (P5) and T6 only by the
  ledger. Whether nw-05 puts places into the heartland is the owner's call.
- Nine inhabited outposts carry D3 with a boss chest for a lair beside them (outpost-1-m75, outpost-1-m81,
  outpost-2-m96, outpost-6-m77, outpost-m13-m79, outpost-m2-m79, outpost-m3-m83, outpost-m7-m77,
  outpost-m15-m112). Under the two channels the lair's chest is T3 and the residents' things follow their wealth
  (P1 or P2), so they read right.
- 19 ruins, caves and wrecks carry D3 or D4 while standing in D0 or D1 cells by a road or town. A ruin's inside is its own ground, so this is right.
