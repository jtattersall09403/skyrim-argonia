# Population and creature parity: named NPCs and creature types in Skyrim and Morrowind

Purpose: totals and per-city numbers for sizing the province roster and the creature table. Game-content counts, not era-bound lore (decision 0002); counted on 2026-10-17 from the UESP MediaWiki API (`action=parse` for wikitext, `expandtemplates` for the transcluded People pages). Tier: CANON_DERIVED (counts by script over UESP lists; a few percent parsing error, see Method). Supersedes the Vivec, Ald'ruhn and Sadrith Mora rows of [city-scale-comparison.md](../city-scale-comparison.md), which left out manor interiors and sub-pages.

## Method

- Named NPC = a bold linked name (`'''[[Name]]'''`) or an `{{NPC Data|Name}}` row on a UESP People page. Plural guard/soldier group rows are dropped. "Unique" = distinct link targets; a person listed at two places counts once.
- The People pages list every individually named person, including bandits, witches and smugglers in caves; generic spawns (guards, Skyrim farmers) are not counted. Skyrim and Morrowind are therefore comparable with each other, and our named slots, but not with our unnamed `resident` rows.
- Creature type = one entry of UESP's creature list (a type such as Wolf or Alit, not its variants: diseased, blighted, snow, plague, levelled forms).

## 1. Named NPCs

| Measure | Count | Source page (https://en.uesp.net/wiki/...) |
|---|---:|---|
| Skyrim, unique names, all add-ons | 1,022 | Skyrim:People (34 settlement templates + literal tables) |
| Skyrim, base game only (minus Dawnguard, Dragonborn, Hearthfire, Creation Club marks and DLC places) | about 860 | Skyrim:People, minus Skyrim:Raven Rock / Tel Mithryn / Skaal Village / Thirsk Mead Hall / Fort Dawnguard / Volkihar Keep / Dayspring Canyon / Forgotten Vale People |
| Skyrim settlement pages (34 templates), sum / mean | 837 / 24.6 | the 34 `Skyrim:<Place> People` pages |
| Morrowind base, unique names (16 location pages) | 2,478 | Morrowind:City / Town / Legion Fort / Ashlander Camp / Daedric Ruins / Dunmer Stronghold / Dwemer Ruins / Vampire Stronghold / Cave / Mine / Stronghold / Tower / Tomb / Farm / Other / Wilderness People |
| Morrowind cities (7), sum / mean | 821 / 117 | Morrowind:City People |
| Morrowind towns (16), sum / mean | 395 / 24.7 | Morrowind:Town People |
| Morrowind cities and towns (23), mean | 52.9 | the two above |
| Tribunal adds | about 100 | Tribunal:Great Bazaar / Godsreach / Royal Palace / Temple Courtyard People |
| Bloodmoon adds | about 109 | Bloodmoon:People (+ Bloodmoon:Fort Frostmoth / Raven Rock / Skaal Village / Thirsk / Other People) |
| Morrowind with both expansions | about 2,690 | sum of the three rows |

Per-settlement means: Skyrim 24.6 named per settlement page (the five big cities average 84; the other 29 settlements average 11). Morrowind 52.9 per city or town (towns 24.7).

### The big cities (unique named NPCs, counted 2026-10-17)

| City | Count | Source page |
|---|---:|---|
| Riften | 100 | Skyrim:Riften People |
| Markarth | 87 | Skyrim:Markarth People |
| Solitude | 86 | Skyrim:Solitude People |
| Whiterun | 79 | Skyrim:Whiterun People |
| Windhelm | 69 | Skyrim:Windhelm People |
| Vivec (nine sub-pages) | 326 | Morrowind:Vivec People |
| Ald'ruhn | 127 | Morrowind:Ald'ruhn People |
| Balmora | 93 | Morrowind:Balmora People |
| Sadrith Mora | 90 | Morrowind:Sadrith Mora People |
| Ebonheart | 74 | Morrowind:Ebonheart People |
| Gnisis | 63 | Morrowind:Gnisis People |
| Molag Mar | 48 | Morrowind:Molag Mar People |

Largest Skyrim city 100 (Riften); largest Morrowind city 326 (Vivec), next Ald'ruhn 127. The 2026-10-06 counts in city-scale-comparison.md differ by up to 4 percent for the Skyrim cities (Whiterun 78, Solitude 87, Windhelm 71, Riften 98, Markarth 88) and fall short for Ald'ruhn (89), Sadrith Mora (67) and Vivec (311), which skipped manor and sub-page tables.

## 2. Creature types

| Measure | Count | Source page |
|---|---:|---|
| Skyrim, active creature types, all add-ons and Creation Club | 70 | Skyrim:Creatures (LinkList entries) |
| Skyrim, active creature types, base game (minus 23 marked Dawnguard / Dragonborn / CC) | 47 | Skyrim:Creatures |
| Skyrim, passive "creatures" (fish, food, insects, other; scenery-like, no attacks) | 60 | Skyrim:Passive Creatures |
| Skyrim, new in Dawnguard | 46 records, 4 new types (Ancestor Moth, Frost Giant, Gargoyle, Shellbug) plus named creatures | Skyrim:Dawnguard Creatures |
| Morrowind base, regular types | 42 | Morrowind:Beasts (11), Ash Creatures (7), Daedra (11 with the three atronachs), Dwemer Centurions (3), Kwama (5), Undead (5) |
| Morrowind base, unique special creatures | 4 (Dagoth Ur, Heart of Lorkhan, Vivec, Yagrum Bagarn) | Morrowind:Special Creatures |
| Tribunal adds | about 10 types (Durzog x2, Fabricant x2, Goblin x3, Lich, Centurion Archer, Advanced Steam Centurion) plus 3 unique | Tribunal:Creatures and its sub-pages |
| Bloodmoon adds | about 13 types (bears x3, wolves x3, Grahl, Horker, Riekling, Spriggan, Tusked Bristleback, Bonewolf, Draugr) plus 4 unique | Bloodmoon:Creatures, Bloodmoon:Undead |
| Morrowind with both expansions | about 65 regular, about 76 with unique ones | sum |

Reading: base Skyrim (47) and base Morrowind (46 with the unique four) are the same size. With every add-on the games sit at 70 and about 76.
