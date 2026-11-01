<!-- imported unchanged from elder-souls-argonia docs/research/lore-facts-audit/group3.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Fact audit group 3: creatures + flora (32 facts)

Entry points read: docs/world/74-ecology.md (species rows :99-139), world/sources/registries/creatures.json (42 species; keys incl. `harvest`, `reaction`, `sourcing`, no attack-effect field), registries/creature-harvest.json (42 rows, `items` lists), registries/resource-nodes.json (8 nodes), docs/phases/2-slice/2.9b-crafting.md, 2.9b-loops/plants.md, 2.7-loops/fighting-species.md, docs/phases/4-buildout/4.5-systems-depth.md (:creature specials, disease/toxin/insect counterplay, cooking, seasons), docs/quests/20-world-provisions.md:196-232, docs/world/30-lore-systems.md:206-229, lore topics fauna-hazards.md/ingredients-alchemy.md, items.json.
Asset note: creature rigs per creatures.json `sourcing.via`; plant meshes per 2.9b-loops/plants.md. No new art assumed.

## Table

| id | derivation | exists/planned (file:line) | status | value | effort | timing |
|---|---|---|---|---|---|---|
| wamasu | Shock the water (swim hazard), hide/bone/organ drops; luminescent organs -> lanterns, charged bones -> weapon/enchant material; juvenile/adult male cannibalism flavour | Row 74-ecology.md:125 (electrifies water; hide, organs, bones). Statblock D3 in fighting-species.md:25. Drops: creature-harvest `item.wamasu-bone`+`item.hide` only; organs have no item. 4.5 "wamasu shock the water" = PLANNED (4.5-systems-depth.md creature specials; quests/20:212). Shrine den built (2.9b-crafting.md:137) | EXISTS (creature, bone, hide, shrine) / PLANNED (water shock, 4.5) / GAP (organ lantern item) | H | M | seam-now: creature attack/area effect field (see Seams) |
| bog-dogs | Pack hunter, pelt, dung -> luck concoction; plants in fur | 74-ecology.md:129; fighting-species.md:20 (pack rally, breaks at 2); harvest `item.pelt`; `item.bog-luck-concoction` ingredients-alchemy.md:63 (dung ingredient item absent) | EXISTS | L | S | later (dung item) |
| rormasu | Crocodile ambush at banks; hide/teeth/tongue; teeth as maturation-trial necklaces | 74-ecology.md:99; harvest `item.crocodile-tooth`,`item.hide`; tongue = food unmapped; cooking is 4.5 | EXISTS / PLANNED (cooking 4.5) | M | S | later |
| tree-viper-lookalike | Red hooped tree-viper vs harmless wasso hedge snake: a look-alike trap (identify before touching/gathering), snake-lore book/dialogue, Hunter-guide topic | No creature row for either (creatures.json 42 ids, none); fauna-hazards has no line; zero grep hits in docs/world | GAP | M | M | later; flavour/dialogue now. Seam: species row needs only a `lookalike` ref, cheap to add anytime |
| moon-adders | Snake, venom -> daril (fermented with swamp-jelly gas bladder), Argonian venom resistance | Row 74-ecology.md:137; harvest "venom (daril)" but creature-harvest `items: []` ("2.3 items gap"); no daril item/recipe (items.json has only weak poisons :13542-13583); Argonian venom resistance: racial resist unchecked (2.8 birthsigns only) | PARTIAL: creature+harvest text, no item | H | S | seam-now: items `item.moon-adder-venom`, `item.daril` + harvest items |
| bear-lizards | Beast of burden / "useful lizards": mount or pack-animal, hide | No row; fauna-hazards.md:80 lists Bear-Lizards in a bred-animal line; `creature.lizard-steed` exists (creatures.json) | PARTIAL (steed row only) | M | M | later (4.x steeds); dialogue now |
| ancestor-lizards | Tree-dwelling forebears: lore books, Hist-shrine carving, rare canopy creature, dialogue | No row | GAP: flavour/dialogue/book only | L | S | later |
| hackwings | Saw beak, wound-withdraw-return flock attack; leather -> light armour/furniture, plumage | Row :107; fighting-species.md:25; harvest `item.hide` only (plumage unmapped); armour from leather via 2.9b recipes | EXISTS (creature, hide) / GAP (plumage item, leather recipe flavour) | M | S | later |
| swamp-jellies | Floating, flavour-named breeds by hue; plum = luck charm, gas bladder -> daril, Deepmire breed stings | Row :130 (stings D3; netch-less witchlight build :154); ecology-encounters-loot.md:81,130; harvest items empty; no breed names data | PARTIAL | M | S | slice-now cheap: breed tint variants already in sourcing; items later |
| fleshflies | Damage cloud follows warm body; face deformation; emollient repellent; protective clothing | Row :103 (particle cloud + damage volume; "vile emollient repels"); 4.5 "fleshfly swarms as damage volumes" + "disease, toxin and insect counterplay" PLANNED; 30-lore-systems.md:220 | PLANNED (4.5) | H | M | seam-now: hazard-volume record + repellent effect (see Seams) |
| underground-express | Rootworm transit stations; swallowed-and-carried travel | Row :121 (not an actor, no asset by owner rule); routes/rootworm-stations.json 4 stations (quests/20:224-229); service kind rootworm (60-water-traversal.md:422); Gideon seasonal stop (4.5 seasons; quests/20:214) | PLANNED (graph built; travel service 2.6/3) | H | M | later; seam already present |
| slugs | Slugshaping art: acid mucus carves wood/stone; cooking | Jassa red slug row :111, harvest "acidic mucus" with no item; slugshaping as craft = none; cooking 4.5 | PARTIAL | M | M | later (4.5 cooking / slugshaping recipe); item seam-now |
| voriplasms | Strips body to bone: bone-pile corpse dressing, D4 guardian in flooded halls; bones/undissolved loot harvest | Row :124; fighting-species.md:24 (D4, squash staging :99); harvest empty (item gap) | EXISTS / GAP (drop item; "stripped corpse" dressing) | M | S | later |
| will-o-wisps | Lure over deep water, glow dust harvest | Row :126; wisp attack RED needs a 2.9 spell effect (fighting-species.md:77); harvest `item.glow-dust` (ingredient effects drain/fortify destruction) | EXISTS; PARTIAL (attack effect) | M | S | slice-now only if wisp strike fix wanted |
| miregaunts | Rises again after death, guards set ground, cavity holds relic | Row :118; "return when killed, loot with provenance" quests/20:213 + 4.5 creature specials PLANNED; harvest item gap | PLANNED (4.5) | H | M | seam-now: respawn class `untilReturn` / provenance loot (statblock.respawn today onRest/never/untilCleared, 98-data-model.md:92) |
| marsh-giants | Spirit that fells dead trees; hinders loggers/miners; blood paints; killing is an offence | Row :116 (reaction: fights if loggers cut nearby); harvest item missing; offence = crime rule (2.10 deeds); logging-camp interaction unplanned | PARTIAL | M | M | later (works-place hazard); quest hook |
| singing-frogs | Frogs tuned for vossa-satl: instrument item, ambient sound, music | fauna-hazards.md:86; material-culture.md:176 (vossa-satl); registry-kotm.jsonl vossa asset; no creature row; 2.14 sound owns frogs? (not confirmed) | PARTIAL (lore + instrument asset) | L | S | later; 2.14 ambience flavour |
| death-hoppers | Pack spit-lunge; vocal sacs -> Sul-Xan armour, bile -> luck concoction | Row :100; fighting-species.md:23,90-100 (lunge staging); harvest items empty | EXISTS / GAP (items) | M | S | later |
| ripper-eels | Trained canal hunters; eel-slime counter (chameleon salve) | Row :131; `item.eel-slime-salve` EXISTS (ingredients-alchemy.md:64); harvest items `[]` though salve exists; "ignores anyone rubbed" reaction in row | EXISTS (salve) / GAP (harvest-to-salve link, rule "ignores rubbed") | H | S | slice-now if Lilmoth canal enters slice; else later; seam: detection-by-item flag |
| extinct-wraxu | Giant extinct bird: skeleton set-piece, Soulrest wraxu frieze/stacks | quests LM51/LM52 mercantile-coast.wraxu-frieze (local-mercantile-coast.md:59-60), PP15 proposed.md:23; no creature | PLANNED (quest sites only) | L | S | later |
| dragons-tongue | Deadly-to-touch herb; fire-red fronds + golden flower; ingredient/poison | node.dragons-tongue + item (effects resist-fire etc) in resource-nodes.json; 2.9b-crafting.md:164 known gap: no 3-LOD mesh, "touch hurts" rule absent; harvest sockets none (plants.md) | PARTIAL | M | M | later (touch-damage on harvest = hazard rule, 4.5 toxin) |
| somnalius-fern | Delicate, inhaling fatigues: ingredient + inhale hazard | node.somnalius-fern, `item.somnalius-frond` drain-fatigue (plants.md:18); many sockets placed | EXISTS (ingredient/node); inhale hazard = GAP | M | M | later |
| scaldroot | Foul tea cleans teeth | No hits; mouth-plover row (:119) is the teeth theme; potential tea consumable (cooking 4.5) | GAP: flavour/dialogue; cooking item later | L | S | later |
| dragonthorn | Chewed for healthy eggs: fertility, egg-clutch/hatching quest, consumable | No item; Dragonthorn only a place name (86-never-reuse-names.md:16); hatching-season birthsigns built (2.9b-crafting.md:130s); hatchery rules Part 4 | GAP: could be ingredient (restore-endurance/fortify) + hatchery quest hook | M | S | later; item seam-now trivial |
| flint-vine | Rope/ladder plant | `item.flint-vine` misc exists (items.json); stock-tables.json:4923 (sold); ladders built in 2.12 (:92-103) but placed ladders do not take it | PARTIAL (item exists, unused) | M | M | slice-now optional: craft/placed "rope ladder" climb link; else later |
| mangrove-spider-folktale | Spiders turned to trees: folk story book/dialogue, shrine site | World mangrove scatter 20-province-design; fauna-hazards.md:94; no book | GAP: dialogue/flavour only (book) | L | S | later |
| lilmoth-plants | Sleeping palm, bamboo, glowing lucan mold | fauna-hazards.md:94-100; lucan mold in climatology research; no node; lucan glow = light-source dressing | GAP: lucan mold node/ingredient (glow light), palms scatter | M | S | later (Lilmoth packet) |
| regrowing-weeds | Stink weed/swamp grass regrow after cutting | Regrow built: `regrowDays` on plants (2.3-items-and-containers.md:142), save `plant-regrow` (98-data-model.md:41), node `respawnHours` (:61) | EXISTS (mechanism); no stinkweed/grass species | L | S | none |
| nightbloom-vine | Secluded-bog vine precious to Naga-Kur: rare ingredient, Naga-Kur quest item | Name only (Nightbloom Manor place, 86-never-reuse-names.md:16); fauna-hazards.md:99; not in resource-nodes.json | GAP | M | S | later |
| lizardfruit | Plum near White Rose: food item, vendor/forage, plum jelly relation | No item | GAP (food) | L | S | later (cooking 4.5) |
| wasso-nut | Leaves cook + padding; fruit delicacy: armour padding/material, food | No item, no armour link | GAP | L | S | later (cooking/armour materials) |
| starblossom | Burned inhalant entering dream-wallow (Naga-Kur rite): ritual item with magic effect | type-recipes.json:11660-11666 props; dream-wallow in 76-stats-progression.md:1137; main-quest 30-main-quest.md; no item; 4.5 "Hist communion powers", "dream and vision harness" PLANNED | PLANNED (4.5/2.11 vision harness) | H | M | seam-now: ritual item `item.starblossom` + use-effect `dreamState` hook |

## Common threads

1. Creature drops without items (moon-adder, jelly, hopper, eel, slug, voriplasm, giant, miregaunt, wamasu organs): creature-harvest.json `items:[]` rows with note "2.3 items gap" feed ingredients -> daril, luck concoction, emollient, salve. One items pass closes ~8 facts.
2. Creature special attack / area effect (wamasu water shock, jelly sting, wisp strike, hopper spit, voriplasm strip, fleshfly cloud, dragon's-tongue touch): data shape for a creature effect + hazard volumes; 4.5 plans specials but the species row has no field now.
3. Counterplay items (eel-slime, fleshfly emollient, venom resistance, pahnjee rack): "ignored if item/effect" detection rule; reaction notes already carry the text.
4. Cooking/food (slug, tongue, plum, wasso, scaldroot tea): all 4.5 cooking.
5. Rare/ritual plants (starblossom, nightbloom, dragonthorn, lucan): node+ingredient+quest, reuse node.* pattern (resource-nodes.json).
6. Look-alike/folk lore and species lacking rows (tree-viper, wasso snake, bear-lizard, ancestor lizard, singing frog, wraxu): dialogue, books, encyclopedia.
7. Return-after-death guardians (miregaunt): respawn class.
8. Rope/ladder crafting (flint-vine) joins 2.12 ladders.

## Seam-now candidates (exact record/field)

- registries/creature-harvest.json `items[]` + items.json: add rows for `item.moon-adder-venom`, `item.daril`, `item.jelly-bladder`, `item.jelly-feeler-plum`, `item.eel-slime`, `item.wamasu-organ`, `item.acid-mucus`, `item.vocal-sac`, `item.bile` (names illustrative); tie ingredient effects in ingredients-alchemy.md. Cheap now, each hand-crafting link otherwise needs per-species rewrite.
- registries/creatures.json: new optional `attackEffect` / `areaEffect` field (effect id from packages/magic catalogue + radius), so wamasu shock, jelly sting, wisp strike (fighting-species.md:77 needs a "2.9 spell effect") and fleshfly damage volumes share castSpell. Also `counterItem` (eel-slime, emollient) feeding detection.
- statblock.respawn (98-data-model.md:92): add class for miregaunt return (e.g. `returns`).
- node record `hazardOnHarvest` (dragon's-tongue touch, somnalius inhale): resource-nodes.json today has yields only.
- items.json `flint-vine` -> ladder/rope placed-piece link (2.12) and `starblossom` ritual item with a use-effect hook for the 2.11 dream/vision harness.

## Slice-now candidates

- ripper-eel / eel-slime rule (salve exists; reaction is text only) if a canal enters the slice.
- wisp strike spell effect (fighting-species.md:77 RED).
- Jelly breed tint variants (cheap).

## Most valuable gaps

1. Moon-adder venom / daril and the empty harvest items (creature-harvest.json).
2. Wamasu water shock + organ lantern (4.5 planned, field not).
3. Fleshfly damage volume + emollient counter (4.5 planned).
4. Miregaunt return + provenance loot (4.5).
5. Starblossom dream-wallow ritual item.
6. Ripper-eel counter wired as detection.
