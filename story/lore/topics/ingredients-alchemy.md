# Ingredients and alchemy

Status: `CANON_EXPLICIT` for the Morrowind table; `CANON_DERIVED` for the slice choices. Era policy: [0002](../../../../docs/decisions/0002-era-and-source-confidence.md); Morrowind (3E 427) supplies the effect vocabulary and the formula, Skyrim (4E 201) the records our ingredient rows come from.

Source: UESP [Morrowind:Ingredients](https://en.uesp.net/wiki/Morrowind:Ingredients), Tribunal:Ingredients and Bloodmoon:Ingredients, fetched 2026-10-20 through the API (`action=parse`, rendered tables; the wikitext holds only templates). Skyrim ingredient effects: UESP Skyrim:Ingredients.

## How the rows read it

- An ingredient row in `world/sources/registries/items.json` carries `effects`: four ids of `packages/magic/src/data/effects.json`. A Skyrim record keeps its own four effects mapped onto the Morrowind vocabulary (stamina → fatigue, one-handed → long blade, two-handed → axe or blunt, barter → mercantile, pickpocket → security, carry weight → feather, slow → drain speed, regenerate → restore, ravage/lingering → damage or poison). A marsh plant or creature part takes its nearest Morrowind kin, or the property the ecology dossier states.
- Luck is not an attribute here (the magic catalogue drops it), so a Luck effect is read as the nearest effect named in its line.
- `rareFortify: true` rides a row with a fortify on a crafting skill or input attribute (0144 item 7). At most three rows. Each has one placed node or looted container among its `sources`, and none is shelved: `worldgen.trade_tables` keeps rareFortify items off every shelf.
- Potion rows carry `effects` [{effectId, magnitude, durationSeconds}] at the world/76 §124 formula at the reference brew: journeyman apparatus (1.0), Alchemy 30, Intelligence 40. score = 30 + 40/10 = 34; magnitude = score × q / (3 × baseCost); duration = score × q / baseCost; one decimal, half up.

## The slice ingredients (68)

| Item | Effects | Why |
|---|---|---|
| `item.bee` | restore-fatigue, damage-fatigue, fortify-fatigue, weakness-to-shock | Skyrim.esm INGR record's own four effects (UESP Skyrim:Ingredients), mapped to Morrowind effect ids (stamina → fatigue). |
| `item.beehive-husk` | resist-poison, fortify-light-armor, fortify-sneak, fortify-destruction | Skyrim.esm INGR record's own four effects (UESP Skyrim:Ingredients), mapped to Morrowind effect ids. |
| `item.blue-dartwing` | resist-shock, fortify-security, restore-health, demoralize-humanoid | Skyrim.esm INGR record's own four effects (UESP Skyrim:Ingredients), mapped to Morrowind effect ids (pickpocket → security, fear → demoralize). |
| `item.bog-dog-dung` | drain-intelligence, detect-key, drain-personality, cure-common-disease | ecology-encounters-loot.md S1: dung is the other half of the good-luck concoction. Morrowind Muck, verbatim. |
| `item.canis-root` | damage-fatigue, fortify-long-blade, fortify-marksman, paralyze | Skyrim.esm INGR record's own four effects (UESP Skyrim:Ingredients), mapped to Morrowind effect ids (one-handed → long blade). |
| `item.crow-feather` | damage-magicka, fortify-conjuration, frenzy-humanoid, weakness-to-shock | ecology-encounters-loot.md S1 names feathers. Skyrim.esm INGR record 03ad66's own four effects (UESP Skyrim:Hagraven Feathers: Damage Magicka, Fortify Conjuration, Frenzy, Weakness to Shock), mapped, the nearest dark-feather record. |
| `item.daedra-heart` | restore-health, damage-fatigue, damage-magicka, demoralize-humanoid | Skyrim.esm INGR record DaedraHeart's own four effects (UESP Skyrim:Daedra Heart: Restore Health, Damage Stamina Regen, Damage Magicka, Fear), mapped to Morrowind effect ids (stamina regen → fatigue, fear → demoralize). Also the Daedric smithing input (0150 item 6; the Skyrim COBJ shape). |
| `item.death-hopper-bile` | cure-paralyzation, restore-health, lightning-shield, fortify-mercantile | ecology-encounters-loot.md S1: bile is half of the good-luck concoction. Morrowind Corkbulb Root (Cure Paralyzation, Restore Health, Lightning Shield, Fortify Luck), Fortify Luck read as Fortify Mercantile as the concoction does. |
| `item.deathbell` | damage-health, damage-fatigue, drain-speed, weakness-to-poison | Skyrim.esm INGR record's own four effects (UESP Skyrim:Ingredients), mapped to Morrowind effect ids (slow → drain speed). |
| `item.dragons-tongue` | resist-fire, fortify-mercantile, fortify-illusion, fortify-axe | fauna-hazards.md:97 grows it around the Ultherus; Skyrim.esm INGR record's own four effects (UESP Skyrim:Ingredients), mapped to Morrowind effect ids (barter → mercantile, two-handed → axe). |
| `item.dreugh-wax` | restore-strength, weakness-to-magicka, drain-personality, drain-willpower | Morrowind Dreugh Wax (Fortify Strength, Restore Strength, Drain Luck, Drain Willpower). Fortify Strength is a rareFortify effect, so the Skyrim Dreugh Wax record's first effect, Weakness to Magic, replaces it; Drain Luck read as Drain Personality. |
| `item.dried-flower-buds` | cure-common-disease, cure-poison, resist-common-disease, restore-fatigue | fauna-hazards.md:50 and material-culture.md:153: buds purify ground water, so the cures and resist-disease of Morrowind's Scrib Jelly / Willow Anther kin. |
| `item.ectoplasm` | fortify-agility, detect-animal, drain-strength, drain-health | Morrowind Ectoplasm, verbatim. |
| `item.eel-slime` | chameleon, cure-poison, cure-blight-disease, restore-willpower | ecology-encounters-loot.md:80: the eels pass a swimmer rubbed with it, so Chameleon, with the Cure Poison, Cure Blight Disease and Restore Willpower of the Morrowind slime kin (Scrib Jelly). |
| `item.feather-serpent-plume` | drain-willpower, levitate, slowfall, feather | ecology-encounters-loot.md S1: a legendary kill whose plumes keep its flight. Morrowind Racer Plumes (Drain Willpower, Levitate), with Slowfall and Feather for the stated lightness. |
| `item.fire-salts` | drain-health, fortify-agility, resist-frost, fire-shield | Morrowind Fire Salts, verbatim; Skyrim's FireSalts record gives the mesh, value 50 and weight 0.25; the incendiary of fire arrows ([fire-arrows-incendiary](fire-arrows-incendiary.md)). |
| `item.fleshfly-husks` | resist-poison, drain-fatigue, water-walking, water-breathing | ecology-encounters-loot.md S1: the dead of a fleshfly swarm. Morrowind Kwama Cuttle (insect remains), verbatim. |
| `item.fly-amanita` | resist-fire, fortify-axe, frenzy-humanoid, restore-fatigue | Skyrim.esm INGR record's own four effects (UESP Skyrim:Ingredients), mapped to Morrowind effect ids (two-handed → axe, regenerate stamina → restore fatigue). |
| `item.frost-salts` | drain-speed, restore-magicka, frost-shield, resist-fire | Morrowind Frost Salts, verbatim. |
| `item.giant-leech-blood` | drain-health, restore-fatigue, cure-common-disease, drain-speed | ecology-encounters-loot.md S1: a leech's blood is its healing use. Morrowind Chokeweed's Restore Fatigue and Cure Common Disease, with Drain Health and Drain Speed for the bite. |
| `item.giant-lichen` | weakness-to-shock, damage-health, weakness-to-poison, restore-magicka | Skyrim.esm INGR record's own four effects (UESP Skyrim:Ingredients), mapped to Morrowind effect ids (ravage health → damage health). |
| `item.glow-dust` | damage-magicka, drain-magicka, fortify-destruction, resist-shock | Skyrim.esm INGR record's own four effects (UESP Skyrim:Ingredients), mapped to Morrowind effect ids (magicka regen → drain magicka). |
| `item.grave-stake-essence` | drain-intelligence, cure-common-disease, drain-magicka, restore-endurance | ecology-encounters-loot.md S1: the life energy that clings to a grave-stake. Morrowind Gravedust, verbatim. |
| `item.hackwing-plume` | cure-common-disease, fortify-light-armor, fortify-long-blade, fortify-sneak | ecology-encounters-loot.md S1: the plumage is for armour that moves quickly. Skyrim.esm INGR record 0e7ed0's own four effects (UESP Skyrim:Hawk Feathers: Cure Disease, Fortify Light Armor, Fortify One-handed, Fortify Sneak), mapped (one-handed to long blade). |
| `item.hanging-moss` | damage-magicka, fortify-health, drain-magicka, fortify-long-blade | fauna-hazards.md:99 blue moss canopy; Skyrim.esm INGR record's own four effects (UESP Skyrim:Ingredients), mapped to Morrowind effect ids (Hanging Moss). |
| `item.hoarvor-blood-sac` | restore-fatigue, fortify-fatigue, reflect, detect-enchantment | ecology-encounters-loot.md S1: a carcass-feeder's sac. Morrowind Hound Meat (Restore Fatigue, Fortify Fatigue, Reflect, Detect Enchantment), verbatim. |
| `item.honeycomb` | restore-fatigue, fortify-block, fortify-light-armor, damage-fatigue | Skyrim.esm INGR record's own four effects (UESP Skyrim:Ingredients), mapped to Morrowind effect ids. |
| `item.imp-stool` | damage-health, poison, paralyze, restore-health | Skyrim.esm INGR record's own four effects (UESP Skyrim:Ingredients), mapped to Morrowind effect ids (lingering damage → poison). |
| `item.jassa-red-slug-mucus` | damage-health, disintegrate-armor, disintegrate-weapon, drain-fatigue | ecology-encounters-loot.md S1: acidic mucus that carves wood and stone. The stated property: Damage Health, Disintegrate Armor, Disintegrate Weapon, and Drain Fatigue from the Morrowind slime kin (Scrib Jelly). |
| `item.jazbay-grapes` | weakness-to-magicka, fortify-magicka, restore-magicka, damage-health | Skyrim.esm INGR record's own four effects (UESP Skyrim:Ingredients), mapped to Morrowind effect ids. |
| `item.jelly-feeler` | restore-personality, fortify-personality, drain-magicka, drain-speed | ecology-encounters-loot.md S1: the plum feeler is a luck charm. Morrowind Kresh Fiber (Restore Luck, Fortify Personality, Drain Magicka, Drain Speed), Restore Luck read as Restore Personality as marshweed does. |
| `item.kotu-gava-wings` | restore-fatigue, fortify-fatigue, feather, telekinesis | ecology-encounters-loot.md S1: the wings of a kotu gava swarm. Morrowind Scuttle (Restore Fatigue, Fortify Fatigue, Feather, Telekinesis), verbatim. |
| `item.lamia-scales` | drain-personality, water-walking, restore-endurance, swift-swim | ecology-encounters-loot.md S1 names scales. Morrowind Scales, verbatim. |
| `item.lavender` | resist-magicka, fortify-fatigue, damage-magicka, fortify-conjuration | Skyrim.esm INGR record's own four effects (UESP Skyrim:Ingredients), mapped to Morrowind effect ids. |
| `item.leviathan-spine` | spell-absorption, invisibility, poison, detect-enchantment | ecology-encounters-loot.md S1: spines. Morrowind Lloramor Spines (Tribunal), verbatim. |
| `item.leviathan-tusk` | drain-alteration, restore-intelligence, fortify-maximum-magicka, detect-animal | fauna-hazards.md and ecology-encounters-loot.md S1: tusks. Morrowind Horker Tusk (Bloodmoon), with the rareFortify Fortify Intelligence read as Restore Intelligence. |
| `item.marsh-giant-blood` | drain-speed, light, cure-common-disease, drain-magicka | ecology-encounters-loot.md S1: blood makes paints and inks. Morrowind's blood ingredient (Blood of an Innocent, Bloodmoon), verbatim. |
| `item.marsh-rat-meat` | drain-magicka, paralyze, cure-poison, resist-poison | ecology-encounters-loot.md S1: rat meat, eaten by the poor. Morrowind Rat Meat (Drain Magicka, Paralyze, Cure Poison, Resist Poison), verbatim. |
| `item.marshweed` | restore-fatigue, paralyze, water-breathing, restore-personality | fauna-hazards.md:99, smoked; nearest Morrowind kin is the chewed Hackle-Lo Leaf (restore luck → restore personality, Luck is dropped). |
| `item.medusa-scales` | drain-personality, water-walking, restore-endurance, paralyze | ecology-encounters-loot.md S1 names scales; the gaze stuns. Morrowind Scales with Paralyze in place of Swift Swim. |
| `item.moon-adder-venom` | weakness-to-poison, damage-health, damage-fatigue, poison | ecology-encounters-loot.md S1 and material-culture.md (Drugs and medicine): fatal to non-Argonians. Morrowind's Poison ingredient (Weakness to Poison, Damage Health, Damage Fatigue, Poison), verbatim. |
| `item.moon-sugar` | fortify-speed, dispel, drain-endurance, drain-willpower | Morrowind Moon Sugar, with Drain Luck (Luck is dropped) read as Drain Willpower, the craving. |
| `item.mudcrab-chitin` | restore-fatigue, cure-common-disease, resist-poison, resist-fire | Skyrim.esm INGR record's own four effects (UESP Skyrim:Ingredients), mapped to Morrowind effect ids; Morrowind Crab Meat agrees on restore fatigue. |
| `item.nirnroot` | damage-health, damage-fatigue, invisibility, resist-magicka | Skyrim.esm INGR record's own four effects (UESP Skyrim:Ingredients), mapped to Morrowind effect ids. |
| `item.orange-dartwing` | restore-fatigue, damage-magicka, fortify-security, damage-health | Skyrim.esm INGR record's own four effects (UESP Skyrim:Ingredients), mapped to Morrowind effect ids (lingering damage health → damage health). |
| `item.osheeja-gar-flesh` | restore-fatigue, resist-shock, lightning-shield, restore-personality | ecology-encounters-loot.md S1 names flesh. Morrowind Crab Meat (water-creature flesh), Restore Luck read as Restore Personality as marshweed does. |
| `item.river-betty` | damage-health, fortify-alteration, drain-speed, feather | Skyrim.esm INGR record's own four effects (UESP Skyrim:Ingredients), mapped to Morrowind effect ids (carry weight → feather). |
| `item.river-salt` | weakness-to-magicka, fortify-restoration, drain-speed, restore-magicka | Skyrim Salt Pile (Weakness to Magic, Fortify Restoration, Slow, Regenerate Magicka; not on the fetched table, from the Salt Pile page) mapped (regenerate → restore, slow → drain speed). |
| `item.rock-warbler-egg` | restore-health, fortify-long-blade, damage-fatigue, weakness-to-magicka | Skyrim.esm INGR record's own four effects (UESP Skyrim:Ingredients), mapped to Morrowind effect ids. |
| `item.rootland-mushroom` | drain-speed, drain-endurance, dispel, drain-strength | ecology-encounters-loot.md:36 tall rootland mushroom; nearest Morrowind kin is the tall Bungler's Bane, verbatim. |
| `item.rootworm-mucus` | drain-personality, fortify-agility, fire-shield, restore-agility | ecology-encounters-loot.md S1: the slick coat of a translucent worm. Morrowind Sload Soap (Drain Personality, Fortify Agility, Fire Shield, Restore Agility), verbatim. |
| `item.shine-mote` | fortify-agility, detect-animal, drain-strength, drain-health | ecology-encounters-loot.md S1: the mote a fading shine leaves. Morrowind Ectoplasm (Fortify Agility, Detect Animal, Drain Strength, Drain Health), verbatim. |
| `item.slaughterfish-egg` | resist-poison, fortify-security, damage-health, fortify-fatigue | Skyrim.esm INGR record's own four effects (UESP Skyrim:Ingredients), mapped to Morrowind effect ids (stamina → fatigue). |
| `item.slaughterfish-scales` | resist-frost, damage-health, fortify-heavy-armor, fortify-block | Skyrim.esm INGR record's own four effects (UESP Skyrim:Ingredients), mapped to Morrowind effect ids. |
| `item.small-pearl` | drain-agility, dispel, water-breathing, resist-common-disease | Morrowind Pearl, verbatim. |
| `item.snail-mucus` | fortify-willpower, cure-poison, cure-blight-disease, restore-willpower | giant snails of the marsh; nearest Morrowind kin is Scrib Jelly, a slime, verbatim. |
| `item.somnalius-frond` | drain-fatigue, calm-humanoid, restore-health, resist-paralysis | fauna-hazards.md:98 shade fern whose name means sleep; a soporific: drain fatigue, calm, a little healing, resist paralysis. |
| `item.spriggan-sap` | drain-magicka, fortify-enchant, fortify-smithing, fortify-alteration (rareFortify) | Skyrim.esm INGR record's own four effects (UESP Skyrim:Ingredients), mapped to Morrowind effect ids (enchanting and smithing are rareFortify). One looted source: the Claywater family hut container socket.KeebaHouseElder.0801AABE; never shelved. |
| `item.swamp-fungal-pod` | resist-shock, damage-magicka, paralyze, restore-health | ecology-encounters-loot.md:36; Skyrim.esm INGR record's own four effects (UESP Skyrim:Ingredients), mapped to Morrowind effect ids (lingering magicka → damage magicka). |
| `item.taproot` | weakness-to-magicka, fortify-illusion, restore-magicka, fortify-magicka | Skyrim.esm INGR record's own four effects (UESP Skyrim:Ingredients), mapped to Morrowind effect ids (regenerate magicka → fortify magicka). |
| `item.thistle-branch` | resist-frost, damage-fatigue, resist-poison, fortify-heavy-armor | Skyrim.esm INGR record's own four effects (UESP Skyrim:Ingredients), mapped to Morrowind effect ids. |
| `item.torchbug-thorax` | restore-fatigue, damage-magicka, weakness-to-magicka, fortify-fatigue | ecology-encounters-loot.md S1: thorax for alchemy. Skyrim.esm INGR record 04da73's own four effects (UESP Skyrim:Torchbug Thorax: Restore Stamina, Lingering Damage Magicka, Weakness to Magic, Fortify Stamina), mapped. |
| `item.troll-fat` | resist-poison, fortify-blunt-weapon, frenzy-humanoid, damage-health | Skyrim.esm INGR record's own four effects (UESP Skyrim:Ingredients), mapped to Morrowind effect ids (two-handed → blunt). |
| `item.void-salts` | restore-magicka, spell-absorption, paralyze, drain-endurance | Morrowind Void Salts, verbatim. |
| `item.wamasu-organ` | light, lightning-shield, shock-damage, resist-shock | ecology-encounters-loot.md S1: luminescent organs, and bones that are alchemically live. The stated property: Light, Lightning Shield, Shock Damage, Resist Shock. |
| `item.wasp-sting` | restore-fatigue, damage-fatigue, fortify-fatigue, weakness-to-shock | ecology-encounters-loot.md S1: sting and venom for alchemy. The Skyrim Bee record's four (UESP Skyrim:Ingredients), the giant wasp's nearest kin, mapped (stamina to fatigue). |
| `item.white-cap` | weakness-to-frost, fortify-heavy-armor, restore-magicka, damage-magicka | Skyrim.esm INGR record's own four effects (UESP Skyrim:Ingredients), mapped to Morrowind effect ids. |
| `item.wisp-wrappings` | restore-fatigue, fortify-destruction, feather, resist-magicka | Skyrim.esm INGR record's own four effects (UESP Skyrim:Ingredients), mapped to Morrowind effect ids (carry weight → feather). |

## The slice potions (10)

| Item | Effects (magnitude, seconds) | Why |
|---|---|---|
| `item.bog-luck-concoction` | fortify-mercantile 11.3 for 34.0 | ecology-encounters-loot.md:82, drunk before a trade: Fortify Mercantile. |
| `item.daril` | night-eye 56.7 for 170.0; detect-animal 15.1 for 45.3; fortify-willpower 1.4 for 4.3 | material-culture.md (Drugs and medicine): the prepared drug of moon adder venom, users see sounds and hear tastes (Night Eye, Detect Animal), the trance (Fortify Willpower, as Hist sap). Fatal to non-Argonians in the lore; that race rule is not modelled in the row. A bag item: recipes.json holds forge recipes only and potions brew free from ingredients. |
| `item.eel-slime-salve` | chameleon 11.3 for 34.0 | ecology-encounters-loot.md:80, the eels pass a swimmer rubbed with it: Chameleon. |
| `item.healing-draught` | restore-health 2.3 for 6.8 | material-culture.md:153: Restore Health. |
| `item.hist-sap` | fortify-health 11.3 for 34.0; fortify-willpower 11.3 for 34.0 | hist-and-sap.md, sacrament and drug: Fortify Health, Fortify Willpower. |
| `item.potion-of-minor-magicka` | restore-magicka 2.3 for 6.8 | Skyrim RestoreMagicka01: Restore Magicka. |
| `item.potion-of-regeneration` | restore-health 2.3 for 6.8 | Skyrim FortifyHealRate01, read as Restore Health over time. |
| `item.skooma` | restore-fatigue 11.3 for 34.0; drain-intelligence 11.3 for 34.0; drain-agility 11.3 for 34.0 | Morrowind Skooma without its Fortify Strength, a rareFortify effect no shelved bottle may carry: Restore Fatigue, Drain Intelligence, Drain Agility. |
| `item.weak-magicka-poison` | damage-magicka 1.4 for 4.3 | Skyrim DamageMagicka01: Damage Magicka. |
| `item.weak-paralysis-poison` | paralyze 0.3 for 0.9 | Skyrim Paralyze01: Paralyze. |

## Morrowind ingredients (UESP)

| Ingredient | Effect 1 | Effect 2 | Effect 3 | Effect 4 | Game |
|---|---|---|---|---|---|
| Alit Hide | Drain Intelligence | Resist Poison | Telekinesis | Detect Animal | base |
| Ampoule Pod | Water Walking | Paralyze | Detect Animal | Drain Willpower | base |
| Ash Salts | Drain Agility | Resist Magicka | Cure Blight Disease | Resist Magicka | base |
| Ash Yam | Fortify Intelligence | Fortify Strength | Resist Common Disease | Detect Key | base |
| Bittergreen Petals | Restore Intelligence | Invisibility | Drain Endurance | Drain Magicka | base |
| Black Anther | Drain Agility | Resist Fire | Drain Endurance | Light | base |
| Black Lichen | Drain Strength | Resist Frost | Drain Speed | Cure Poison | base |
| Bloat | Drain Magicka | Fortify Intelligence | Fortify Willpower | Detect Animal | base |
| Bonemeal | Restore Agility | Telekinesis | Drain Fatigue | Drain Personality | base |
| Bread | Restore Fatigue | - | - | - | base |
| Bungler's Bane | Drain Speed | Drain Endurance | Dispel | Drain Strength | base |
| Chokeweed | Drain Luck | Restore Fatigue | Cure Common Disease | Drain Willpower | base |
| Coda Flower | Drain Personality | Levitate | Drain Intelligence | Drain Health | base |
| Comberry | Drain Fatigue | Restore Magicka | Fire Shield | Reflect | base |
| Corkbulb Root | Cure Paralyzation | Restore Health | Lightning Shield | Fortify Luck | base |
| Corprus Weepings | Drain Fatigue | Fortify Luck | Drain Willpower | Restore Health | base |
| Crab Meat | Restore Fatigue | Resist Shock | Lightning Shield | Restore Luck | base |
| Daedra Skin | Fortify Strength | Cure Common Disease | Paralyze | Swift Swim | base |
| Daedra's Heart | Restore Magicka | Fortify Endurance | Drain Agility | Night Eye | base |
| Diamond | Drain Agility | Invisibility | Reflect | Detect Key | base |
| Dreugh Wax | Fortify Strength | Restore Strength | Drain Luck | Drain Willpower | base |
| Ectoplasm | Fortify Agility | Detect Animal | Drain Strength | Drain Health | base |
| Emerald | Fortify Magicka | Restore Health | Drain Agility | Drain Endurance | base |
| Fire Petal | Resist Fire | Drain Health | Spell Absorption | Paralyze | base |
| Fire Salts | Drain Health | Fortify Agility | Resist Frost | Fire Shield | base |
| Frost Salts | Drain Speed | Restore Magicka | Frost Shield | Resist Fire | base |
| Ghoul Heart | Paralyze | Cure Poison | Fortify Attack | - | base |
| Gold Kanet | Drain Health | Burden | Drain Luck | Restore Strength | base |
| Gravedust | Drain Intelligence | Cure Common Disease | Drain Magicka | Restore Endurance | base |
| Green Lichen | Fortify Personality | Cure Common Disease | Drain Strength | Drain Health | base |
| Guar Hide | Drain Fatigue | Fortify Endurance | Restore Personality | Fortify Luck | base |
| Hackle-Lo Leaf | Restore Fatigue | Paralyze | Water Breathing | Restore Luck | base |
| Heather | Restore Personality | Feather | Drain Speed | Drain Personality | base |
| Hound Meat | Restore Fatigue | Fortify Fatigue | Reflect | Detect Enchantment | base |
| Hypha Facia | Drain Luck | Drain Agility | Drain Fatigue | Detect Enchantment | base |
| Kagouti Hide | Drain Fatigue | Fortify Speed | Resist Common Disease | Night Eye | base |
| Kresh Fiber | Restore Luck | Fortify Personality | Drain Magicka | Drain Speed | base |
| Kwama Cuttle | Resist Poison | Drain Fatigue | Water Walking | Water Breathing | base |
| Large Kwama Egg | Restore Fatigue | Paralyze | Frost Shield | Fortify Health | base |
| Luminous Russula | Water Breathing | Drain Fatigue | Poison | - | base |
| Marshmerrow | Restore Health | Detect Enchantment | Drain Willpower | Drain Fatigue | base |
| Moon Sugar | Fortify Speed | Dispel | Drain Endurance | Drain Luck | base |
| Muck | Drain Intelligence | Detect Key | Drain Personality | Cure Common Disease | base |
| Netch Leather | Fortify Endurance | Fortify Intelligence | Drain Personality | Cure Paralyzation | base |
| Pearl | Drain Agility | Dispel | Water Breathing | Resist Common Disease | base |
| Racer Plumes | Drain Willpower | Levitate | - | - | base |
| Rat Meat | Drain Magicka | Paralyze | Cure Poison | Resist Poison | base |
| Raw Ebony | Drain Agility | Cure Poison | Frost Shield | Restore Speed | base |
| Raw Glass | Drain Intelligence | Drain Strength | Drain Speed | Fire Shield | base |
| Red Lichen | Drain Speed | Light | Cure Common Disease | Drain Magicka | base |
| Resin | Restore Health | Restore Speed | Burden | Resist Common Disease | base |
| Roobrush | Drain Willpower | Fortify Agility | Drain Health | Cure Poison | base |
| Ruby | Drain Health | Feather | Restore Intelligence | Drain Agility | base |
| Saltrice | Restore Fatigue | Fortify Magicka | Drain Strength | Restore Health | base |
| Scales | Drain Personality | Water Walking | Restore Endurance | Swift Swim | base |
| Scamp Skin | Drain Magicka | Cure Paralyzation | Restore Personality | Restore Strength | base |
| Scathecraw | Drain Strength | Cure Poison | Drain Health | Restore Willpower | base |
| Scrap Metal | Drain Health | Lightning Shield | Resist Shock | Restore Intelligence | base |
| Scrib Jelly | Fortify Willpower | Cure Poison | Cure Blight Disease | Restore Willpower | base |
| Scrib Jerky | Restore Fatigue | Fortify Fatigue | Burden | Swift Swim | base |
| Scuttle | Restore Fatigue | Fortify Fatigue | Feather | Telekinesis | base |
| Shalk Resin | Drain Fatigue | Fortify Health | Drain Personality | Fortify Speed | base |
| Sload Soap | Drain Personality | Fortify Agility | Fire Shield | Restore Agility | base |
| Small Kwama Egg | Restore Fatigue | - | - | - | base |
| Spore Pod | Drain Strength | Drain Fatigue | Detect Key | Paralyze | base |
| Stoneflower Petals | Restore Strength | Fortify Magicka | Drain Luck | Fortify Personality | base |
| Trama Root | Restore Willpower | Levitate | Drain Magicka | Drain Speed | base |
| Vampire Dust | Fortify Health | Fortify Strength | Spell Absorption | Vampirism | base |
| Violet Coprinus | Water Walking | Drain Fatigue | Poison | - | base |
| Void Salts | Restore Magicka | Spell Absorption | Paralyze | Drain Endurance | base |
| Wickwheat | Restore Health | Fortify Willpower | Paralyze | Damage Intelligence | base |
| Willow Anther | Drain Personality | Frost Shield | Cure Common Disease | Cure Paralyzation | base |
| Large Corprusmeat Hunk | - | - | - | - | base |
| Large Wrapped Corprusmeat | - | - | - | - | base |
| Medium Corprusmeat Hunk | - | - | - | - | base |
| Medium Wrapped Corprusmeat | - | - | - | - | base |
| Small Corprusmeat Hunk | - | - | - | - | base |
| Small Wrapped Corprusmeat | - | - | - | - | base |
| Wrapped Corprusmeat Hunk | - | - | - | - | base |
| Bread | Restore Fatigue | - | - | - | base |
| Daedra's Heart | Restore Magicka | Fortify Endurance | Drain Agility | Night Eye | base |
| Diamond | Drain Agility | Invisibility | Reflect | Detect Key | base |
| Emerald | Fortify Magicka | Restore Health | Drain Agility | Drain Endurance | base |
| Girth's Guar Hide | Drain Fatigue | Fortify Endurance | Restore Personality | Fortify Luck | base |
| Human Flesh | Fortify Health | Drain Intelligence | Drain Personality | - | base |
| Marsus's Guar Hide | Drain Fatigue | Fortify Endurance | Restore Personality | Fortify Luck | base |
| Meteor Slime | Fortify Willpower | Cure Poison | Cure Blight Disease | Restore Willpower | base |
| Muffin | Restore Fatigue | - | - | - | base |
| Pearl | Drain Agility | Dispel | Water Breathing | Resist Common Disease | base |
| Poison | Weakness to Poison | Damage Health | Damage Fatigue | Poison | base |
| Raw Ebony | Drain Agility | Cure Poison | Frost Shield | Restore Speed | base |
| Raw Glass | Drain Intelligence | Drain Strength | Drain Speed | Fire Shield | base |
| Roland's Tear | Drain Health | Burden | Drain Luck | Restore Strength | base |
| Ruby | Drain Health | Feather | Restore Intelligence | Drain Agility | base |
| Treated Bittergreen Petals | Restore Intelligence | Drain Magicka | Drain Endurance | Invisibility | base |
| Adamantium Ore | Burden | Restore Magicka | Poison | Reflect | Tribunal |
| Durzog Meat | Fortify Agility | Fortify Strength | Blind | Damage Magicka | Tribunal |
| Golden Sedge Flowers | Drain Magicka | Fortify Strength | Fortify Attack | Swift Swim | Tribunal |
| Horn Lily Bulb | Resist Paralysis | Drain Health | Restore Strength | Restore Endurance | Tribunal |
| Lloramor Spines | Spell Absorption | Invisibility | Poison | Detect Enchantment | Tribunal |
| Meadow Rye | Fortify Speed | Damage Health | Restore Speed | Drain Speed | Tribunal |
| Nirthfly Stalks | Damage Health | Fortify Speed | Restore Speed | Drain Speed | Tribunal |
| Noble Sedge Flowers | Damage Health | Restore Agility | Poison | Fortify Agility | Tribunal |
| Scrib Cabbage | Drain Intelligence | Damage Health | Restore Agility | Fortify Agility | Tribunal |
| Sweetpulp | Paralyze | Levitate | Resist Paralysis | Restore Health | Tribunal |
| Timsa-Come-By flowers | Dispel | Resist Paralysis | Drain Magicka | Restore Endurance | Tribunal |
| Bear Pelt | Drain Fatigue | Fortify Strength | Resist Common Disease | Night Eye | Bloodmoon |
| Bristleback Leather | Blind | Frost Damage | Resist Frost | Recall | Bloodmoon |
| Grahl Eyeball | Resist Frost | Night Eye | Drain Magicka | Fortify Strength | Bloodmoon |
| Gravetar | Resist Frost | Drain Health | Fortify Fatigue | Drain Luck | Bloodmoon |
| Heartwood | Restore Magicka | Fortify Agility | Drain Strength | Weakness to Fire | Bloodmoon |
| Holly Berries | Resist Frost | Frost Shield | Frost Damage | Weakness to Fire | Bloodmoon |
| Horker Tusk | Drain Alteration | Fortify Intelligence | Fortify Maximum Magicka | Detect Animal | Bloodmoon |
| Raw Stalhrim | Resist Frost | Frost Damage | Paralyze | Restore Health | Bloodmoon |
| Ripened Belladonna Berries | Resist Magicka | Restore Magicka | Fortify Magicka | Drain Magicka | Bloodmoon |
| Snow Bear Pelt | Drain Fatigue | Fortify Speed | Resist Common Disease | Night Eye | Bloodmoon |
| Snow Wolf Pelt | Drain Fatigue | Fortify Speed | Resist Common Disease | Night Eye | Bloodmoon |
| Unripened Belladonna Berries | Resist Magicka | Restore Magicka | Fortify Magicka | Drain Magicka | Bloodmoon |
| Wolf Pelt | Drain Fatigue | Fortify Speed | Resist Common Disease | Night Eye | Bloodmoon |
| Wolfsbane Petals | Restore Intelligence | Invisibility | Drain Endurance | Drain Magicka | Bloodmoon |
| Blood of an Innocent | Drain Speed | Light | Cure Common Disease | Drain Magicka | Bloodmoon |
| Flaming Eye of the Lightkeeper | Resist Frost | Night Eye | Drain Magicka | Fortify Strength | Bloodmoon |
| Heart of an Innocent | Restore Magicka | Fortify Endurance | Drain Agility | Night Eye | Bloodmoon |
| Heart of the Udyrfrykte | Restore Magicka | Fortify Endurance | Drain Agility | Night Eye | Bloodmoon |
| Heart of the Wolf | Restore Magicka | Fortify Endurance | Drain Agility | Night Eye | Bloodmoon |
| Pinetear | Fortify Magicka | Restore Health | Drain Agility | Drain Endurance | Bloodmoon |
