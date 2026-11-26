# What our own plan already says about magic

Read-only audit of 2026-11-26 for the rewrite of [PROPOSAL.md](PROPOSAL.md). Paths are from the repo root. "L" = line.
Quest lines are in `story/design/quests/lines/` (shortened `lines/`). The new world's quests exist only as these pages
(no `newworld/story/data/quest_lines`; `story/data/quest_lines/*.json` is five old-world files with no magic).
Place records are `newworld/story/data/db/` (shortened `db/`).

## 0. Which docs cover the topic, and the one to edit

Live docs that already cover it: `story/design/quests/spell-groups.md` (the spells quests may use; owner's groups,
2026-11-16), the eight `lines/*.md` pages, `db/place_give.jsonl` + `db/person.jsonl` (planned sellers, trainers,
blessings, enchanters), `story/lore/topics/magic-practice.md` (the lore stance), `docs/decisions/0012` (shouts),
`docs/design/quest-form.md` and `blocks.md` (how a spell is taught).
Confirmed: the Sisei-Xul as "the province's one native order of magic" (lines/sisei-xul.md:34) and a spell in most
quests (7 of 13 teach a spell, 2 more rank tomes). Contradicted: "nobody sells a spell" (13 sellers exist), "the
schools stay five" (lore says six), "necromancy is foreign" (Neeja, an Argonian, teaches it). Superseded: "we put
nothing in the shouts' place" (0012 L23-25 reserved it for Hist communion powers).
The one doc to edit: `docs/research/magic/PROPOSAL.md` (rewrite whole); the lore stance lives in
`story/lore/topics/magic-practice.md` (the proposal already says to rewrite that, PROPOSAL L234-236).

## 1. What quests TEACH, GIVE, REQUIRE or STAGE

"Reuses" = the existing record named in the plan. "Name" = the name the plan gives (blank = it uses the game's own name).

### 1a. Spells taught (teach_spell, one step uses it)

| File:L | Quest | What | Who gives | Reuses | Used for |
|---|---|---|---|---|---|
| main-plot.md:172-175 | MQ1 No Name on the Work Roll | tome of Sparks (a choice among 4 loot picks) | Dralin | Skyrim novice tome | the opening's only spell |
| main-plot.md:180-182 | side: What the Herald Sent | scrolls of firebolt, fast healing; Ring of Minor Health | Vosh-Leera's parcel | Skyrim scrolls/ring | first heal and bolt |
| main-plot.md:198-199 | MQ2 The Dry Tree | the tree's blessing: breathe under water (Argonian: resist poison) | Weeltul, tree-minder of Jal-Veesa | Hist blessing record (db/place_give.jsonl:467) | the next dive; poison |
| main-plot.md:211-213 | MQ3 The First Dream | cup of sap; drinking it = black screen, vision as words | Vosh-Leera | Skyrim potion bottle, our name | shows Teel-Fen Weir |
| main-plot.md:227-231 | MQ3 | 3 potions Cure Poison (comfort branch) or Adept Alchemy training + sold fungus (truth branch) | Heem-Jasa | Skyrim potions | the choice is "real in play" |
| main-plot.md:338-339 | MQ9 | bottles of paralysis poison (grey paste) | Unbound's packs | Skyrim poison, our name | clue |
| main-plot.md:426-427 | MQ13 | Waterbreathing by blessing, spell, potion (steward sells) or enchantment | Meer-Tasi, Bell Station | Skyrim | the dive to Teku-Sul |
| main-plot.md:531 | side (Vosh-Leera) | amulet turning most of the guardian's venom | quest | custom enchantment (no record named) | hydra fight |
| main-plot.md:532 | side (Sesk) | scrolls of a paralysing spell, three uses | Sesk | "a paralysing spell"; none named | stop the hydra |
| main-plot.md:533 | side (Toklea elder) | a spell tome, "a spell of ours that burns the guardian far worse than anything else" | elder | NOT mapped; a custom spell | hydra fight |
| main-plot.md:535 | side (Bell Station steward) | scrolls of a storm striking every head; potions curing the venom fast | steward | storm spell not named; custom potion | hydra fight |
| main-plot.md:593-594 | MQ19 Take ending | amulet (fortify health/magicka, resist poison) + once-a-day power "the Eye's Gaze", paralyses every foe in sight | the Eye | Eye of Argonia, our record; power likely Mass Paralysis | endgame power |
| main-plot.md:603-606 | MQ19 Give-her ending | Cuts-the-Old-Knot as an ally called by one power, sent away by another; two spells she teaches, "Knot-Breaker's Storm" and "Root Ward", one a once-a-day power | Cuts-the-Old-Knot | custom; blocks.md:114 (two spells of ours move her) | endgame ally |
| main-plot.md:583,596-598,607 | MQ19 endings | Use: "stronger blessings from every Hist"; Take and Give: "No Hist gives the player its blessing again" | the Hist | Hist blessings | the ending's play cost |
| sisei-xul.md:139 | rank Leaf-Hand (q3) | tomes Cure Disease, Cure Poison; the Minder's Staff | Deegla-Tsei | Magic Expanded tomes; ME staff, our name | healing; staff |
| sisei-xul.md:199 | q4 Under the Oldest Foundation | Stoneflesh (Alteration 25), "the first of the Stone-Sleepers' stone spells" | Akeeta-Sul, Tsonac | Skyrim Stoneflesh | undead fight; she is also Alteration teacher (L90) |
| sisei-xul.md:216 | q5 Drag-Marks | Detect Dead | the egg-minder, Tazhul | Skyrim | see bog blights |
| sisei-xul.md:247 | q7 Slaver's Log | Waterbreathing ("an Argonian needs none") | the order | Skyrim | the wreck |
| sisei-xul.md:284 | q8 Empty Niche | tome of Conjure Familiar (Neeja gives, urn broken) | Neeja, an Argonian necromancer | Skyrim | reward |
| sisei-xul.md:307 | q10 Barred Cellar | Circle of Protection | the order | Skyrim | bound dead |
| sisei-xul.md:141 | rank Grave-Singer (q10) | tome of Guardian Circle; robe and hood (Arcane Mage Armor, our name) | Okan-Zeel | Skyrim | reward |
| sisei-xul.md:321 | q11 Egg Pools | Poison Spray "as old marsh fighters used it" | the order | Magic Expanded | native Destruction |
| sisei-xul.md:333 | q12 Thrall Ship | Paralyze (Alteration 75) | the order | Skyrim | guards, Ervyn |
| sisei-xul.md:349 | q13 Under the Well | Sun Fire | the order | Dawnguard | Morvayn |
| sisei-xul.md:140,293-300 | q6, q9 | Grave-Iron Claws (Turn Undead); a Turn-Undead blade broken at the arcane enchanter to learn Enchanting | order's enchanter | Skyrim Turn Undead | undead |
| sisei-xul.md:395-399 | ending (urn broken) | the First Singer's staff, custom enchantment "Sisei-Xul's Rest" (lays any undead it strikes, heals bearer by part of harm); Morvayn's tome of Command Undead | Okan-Zeel, Neeja | custom enchantment; ME tome | capstone |
| house-cardruhn.md:100-104 | join test | cast any conjuration before Ervyn; Conjuration 20 by casting Conjure Familiar; "Thorn's apothecary sells its tome" | Ervyn | Skyrim Conjure Familiar | gate |
| house-cardruhn.md:156 | q1 | Command Lesser Undead | Neeja | Magic Expanded | command the salt dead |
| house-cardruhn.md:168 | q2 | Conjure Flame Atronach | Neeja | Skyrim | fight |
| house-cardruhn.md:178 | q3 | Soul Trap (ghost's soul into a gem) | Neeja | Skyrim | the fire-stone |
| house-cardruhn.md:199 | q4 | Conjure Ghost (Conjuration 35) | Neeja | Magic Expanded | draw hunters |
| house-cardruhn.md:211-214 | q5 | Resist Frost as an enchantment (break a ring at the arcane enchanter, Conclave of the One, Thorn) | Ervyn | Skyrim | armour vs ghosts |
| house-cardruhn.md:231 | q6 | Paralysis Rune | Dalvela | Magic Expanded | hold diggers |
| house-cardruhn.md:244-245 | q7 | Command Undead (Conj 50); 2 potions of Waterbreathing | Dalvela | ME; Skyrim | the wreck |
| house-cardruhn.md:264 | q8 | Sun Fire | Dalvela | Dawnguard | the wraith |
| house-cardruhn.md:270 | q9 | Necromantic Healing | Neeja | Skyrim | heal thralls |
| house-cardruhn.md:318 | q11 | Command Greater Undead (Conj 75) | Dalvela | ME | |
| house-cardruhn.md:142-144 | ranks | tomes Raise Zombie, Conjure Ghost, Dead Thrall; Coffle-Whip, soul-trap dagger, 5+2 soul gems | Neeja/Dalvela | Skyrim; ME | |
| house-cardruhn.md:288-291 | q9 | Neeja's staff (ME staff, enchanted to raise a zombie); Keel-Vaxa's soul in a black gem (filled grand soul) | Neeja/Morvayn | ME staff; Skyrim | |
| house-cardruhn.md:369-370 | ending | Morvayn's staff, custom enchantment "Morvayn's Due" (a struck foe that dies rises as thrall for a long time) | Morvayn | DX Necromancer Robes staff | capstone |
| house-cardruhn.md:375 | Dalvela ending | a bound wraith "comes to the player's side with a power and goes with another" | Dalvela | called-ally block | |
| shadowscales.md:168 | q3 | poison recipe from deathbell+nightshade (Damage Health) | Hulee-Tah | Skyrim ingredients | the sergeant's bowl |
| shadowscales.md:192,208,217 | q5, q7, q9 | Muffle, Night-Eye, Invisibility | Hulee-Tah | Skyrim Muffle/Invisibility; ME Night-Eye | stealth |
| shadowscales.md:135-139 | contracts | Ghost-Step Boots (Muffle), Supper Ring (Fortify Alchemy 15), Sithis' Sting (paralysing bow), Drowned Man's Knife, Black Hood, Quick Hands | order | enchantments | a unique thing nearly every quest |
| shadowscales.md:299; thieves.md:299 | ending | Quiet Cloak (Fortify Sneak 25 + Muffle) | Eldest | enchantment | |
| thieves.md:139-141 | q3 Light Fingers | Enchanting taught: break a Fortify Pickpocket ring | Corso Delling | Skyrim | gloves |
| thieves.md:166-167 | q5 | "Muffle from the outpost's spell-seller" at the Blackrose outpost (NO such seller in db: see 5) | seller | Skyrim | sneak past smugglers |
| thieves.md:178 | q6 | Telekinesis, lift the pearl box across water | Swims-Without-Ripples (Argonian) | Skyrim | |
| thieves.md:231-232 | q10 | ring of Muffle off a bull crocodile, broken at the hall's enchanter | | | |
| thieves.md:286-287 | endings | the Still Water ring: constant Chameleon 50%, "no Chameleon spell exists" | Master Eel | custom enchantment (spell-groups.md:62) | |
| thieves.md:321 | q5 | Eel-slime potion: ripper eels (slaughterfish) ignore you for an hour | cache-master | slaughterfish egg, our name; effect not in game | the cistern |
| thieves.md:197 | q8 | "FreeClimb, or a scroll" over the wall | | | |
| lamps.md:214 | q3 | Calm (to calm a dog) | Marcella Dovi | Skyrim | |
| lamps.md:258 | q5 | Throw Noise | Marcella | ME | |
| lamps.md:295 | q7 | Clairvoyance | Marcella | Skyrim | follow the outlaw's trail |
| lamps.md:167,449 | ranks/ending | rapier paralysing 2 s; Lamp of Truth (Fortify Speech 25, Illusion spells cost 25% less) | | enchantments | |
| merchants.md:149,200,270 | q2, q5, q10 | potions of Waterbreathing (Gideon herbalist; pilot-elder at Seafalls sells them); scroll of Tinur's Hoptoad from the boatman | | Skyrim; ME scroll "of ours" (L396) | wrecks; climb a hull |
| merchants.md:355 | ending | Factor's Seal (Fortify Barter, Smithing, Block) | | custom enchantment | |
| pirates.md:51,167,169,467-468,480-482 | all | scrolls (no spells taught): Waterbreathing, Water Walking, Swift Swim, Tinur's Hoptoad (ME), Frenzy, Mayhem; Ma'jirra's crew sell Frenzy scrolls from rank Boarder, Selvo sells Mayhem from rank Mate, his quay stall sells all six after the ending | Ma'jirra's crew, Selvo Arenim | Skyrim scrolls; scroll records of ours of ME spells | boardings, wrecks, crews |
| pirates.md:170 | ending | Bramman's Coat enchantment (Fortify 1H, 2H, Waterbreathing) | | custom | |
| chainbreakers-newworld.md:389-390 | q8 | six rune scrolls (Fire Rune, Paralysis Rune) | watch-leader | Skyrim; ME | hold the mound |
| chainbreakers-newworld.md:490-494 | q14 | Aldyne (Destruction fighter, yields) drops an enchanted robe and staff, or her ring | | | |
| chainbreakers-newworld.md:559-560,572 | endings | Hasp of the Falls (cannot be held by Paralysis; intimidate +20); Firebrand claws (fire damage, struck flee) | | custom enchantments | |
| chainbreakers-newworld.md:538,542 | people freed | Ulasi sells potions at fair prices; Tsleeksa brings imp stools; Tumma-Ra 3 waterbreathing potions | | | |

### 1b. Planned in the place records (sellers, trainers, blessings, enchanters)

| File:L | Place | What |
|---|---|---|
| db/place_give.jsonl:44,58 | Archon | wandering hedge-mage: Restoration and Alteration tomes to Adept, Illusion to Apprentice, scrolls, soul gems, staves; arcane enchanter |
| :322 | Gideon | Temple of Dibella priestess: Restoration and Illusion tomes to Adept |
| :355,365 | Helstrom | tree-minder healer (Taleeka-Ma): Restoration and Alteration tomes to Adept; arcane enchanter in the tree-minders' hall |
| :370 | Hirecan | an Agaceph illusionist: Illusion tomes up to Expert, scrolls (trainer to Expert, :371) |
| :390 | Icalca | Illusion tomes to Apprentice, scrolls of calm and fear |
| :594 | Lilmoth | Breton dock mage: Conjuration and Illusion to Adept, Restoration to Apprentice, scrolls, soul gems |
| :1154,1165 | Soulrest | Imperial-descended mage: Alteration and Restoration to Adept; enchanter |
| :1183,1193 | Stormhold | Dunmer mage: Alteration and Illusion to Adept, scrolls, soul gems; enchanter |
| :1263-1264 | Thorn | Dunmer enchanter in the Conclave of the One: Illusion and Alteration to Adept, soul gems, scrolls (no Conjuration) |
| :1377 | Tsonac | tree-minder's pupil: Alteration tomes up to Expert, "the Stone-Sleepers' stone magic: Stoneflesh, Ironflesh, Ebonyflesh", Restoration to Adept |
| :1451,1462 | Xibcan, Yina | Illusion tomes to Novice, scrolls |
| :1476,1478 | Yulca (= Alten Corimont, main-plot.md:773) | hall's hedge-mage: Illusion to Adept, Alteration and Conjuration to Novice, scrolls, soul gems; enchanting table |
| :295, :1429 | Gandranen, a Velothi ruin | found tomes: Adept Alteration; Adept Illusion |
| :684 | Loriasel | enchanter's workbench |
| :63,84,146,369,467,475,545,607,796,949,1197,1360,1383,1401,1408 | 15 Hist blessings (timed, 8 h) | Archon waterbreathing + cure disease; Aroxhu Fortify Alchemy; Blackrose (drowned Hist, by diving) waterbreathing; Helstrom resist disease; Jal-Veesa waterbreathing (Argonian: resist poison); Jarecai waterbreathing; Korydon resist disease; Lilmoth waterbreathing; Noota-Nara resist fire; m16-m68 resist poison; Stormhold resist poison; Truowa fortify health; Tsonac Fortify Heavy Armor; Uluo stamina regeneration; Umpholo waterbreathing |
| :323,817,1148,1170,1271 | 5 foreign shrines | Dibella (Gideon, Olvani, Slough Point), the Nine (Soulrest, Stendarr), Saint Roris (Thorn) |
| db/give_kind.jsonl (standing-stone, altar-power, spell-tome kinds) | | the kinds exist; `shrine-blessing` and `spell-tome` are used, `standing-stone` and `altar-power` are used by no place |
| db/person.jsonl:95 / :41 / :157 / :115 | | Taleeka-Ma (role spell-trader, Helstrom); Wujeel (sap and herb seller, teaches Alchemy); Heem-Jasa (teaches Alchemy, Adept); Keeshu-Ra (Archery trainer): the only named persons so far |

Counts from the db: 13 trader-spells places (above), 2 found tomes, 7 arcane enchanters, 15 Hist blessings, 17 magic trainers
(Alchemy 7: place_give.jsonl:62,83,144,368,605,951,1016; Restoration 3: 325,367,606; Alteration 3: 1169,1195,1378;
Illusion 4: 371,391,990,1477), 15 alchemy labs, 1 tree-minder/teacher person with a role of spell-trader.

## 2. Who teaches, sells or trains magic (and Alchemy, Enchanting)

| Person or office | Place | Faction | What (file:L) |
|---|---|---|---|
| Deegla-Tsei, tree-minder | Arorha | Sisei-Xul | admits the player; sends them on (sisei-xul.md:88,193) |
| Okan-Zeel, First Grave-Singer | Helstrom hall | Sisei-Xul | Restoration teacher (:395), staff, ranks |
| Akeeta-Sul, Stone-Sleepers' minder | Tsonac | Sisei-Xul | "the order's teacher of Alteration" (:90); Stoneflesh (:199); trader pupil sells to Expert (db :1377) |
| Gam-Meesh, mason-smith | Tsonac | Sisei-Xul | Smithing; grave-iron (:91,228) |
| the order's alchemist by the Hist | Aroxhu | Sisei-Xul | poison draught (:165) |
| the order's enchanter | Helstrom | Sisei-Xul | Turn Undead blade, teaches Enchanting (:293) |
| the egg-minder | Tazhul | Root-Folk | Detect Dead (:216) |
| Neeja (Argonian necromancer) | Coldbrine, Helstrom | House Cardruhn | Command Lesser Undead, Conjure Flame Atronach, Soul Trap, Conjure Ghost, Necromantic Healing (house-cardruhn.md:87,156-270) |
| Dalvela Cardruhn, bone-mistress | Ovezza | House Cardruhn | Paralysis Rune, Command Undead, Sun Fire, Command Greater Undead (:231-318) |
| Ervyn Cardruhn, factor | Thorn | House Cardruhn | the conjuration test, Resist Frost enchanting (:100,211) |
| Hulee-Tah, handler | Archon | Shadowscales | Muffle, Night-Eye, Invisibility, a poison; Archery trainer (shadowscales.md:129,192-217) |
| Beem-Xal | Archon | Shadowscales | Master Sneak trainer (:130); alchemy table in his house (:159) |
| Black-Tongue Brews keeper | Lilmoth | Shadowscales | sells poisons, nightshade, eel-slime (:346) |
| Corso Delling | Blackrose | Eelskins | teaches Enchanting; Sneak to Master (thieves.md:68,139) |
| Swims-Without-Ripples | Lilmoth | Eelskins | Telekinesis (:178) |
| Sees-Nothing | | Eelskins | Pickpocket (:115) |
| Marcella Dovi, chief | Soulrest | Lampbearers | Calm, Throw Noise, Clairvoyance (lamps.md:214,258,295) |
| Teesh-Vaal, arbiter | Soulrest | Lampbearers | Master Illusion trainer (lamps.md:449) |
| Ma'jirra's crew, Selvo Arenim | Soulrest landing, Bramman's Watch | Brethren | sell scrolls (pirates.md:118,167,169) |
| the Company's smith | Gideon | Topal Bay Company | teaches Smithing recipes only (merchants.md:40) |
| Gideon's herbalist; Seafalls pilot-elder; Bell Station steward | | | sell potions of Waterbreathing (merchants.md:149,270; main-plot.md:730) |
| Weeltul, tree-minder and root-tender | Jal-Veesa | Sedge-Wardens | gives the blessing (main-plot.md:198) |
| Heem-Jasa, minder | Teel-Fen Weir | Sedge-Wardens | Adept Alchemy trainer, sells swamp fungus (:227-231; db person.jsonl:157) |
| Vosh-Leera, root-herald | Jal-Veesa | Toh-Reel-Ka | the cup of sap (:211) |
| Taleeka-Ma, tree-minder and healer | Helstrom | Root-Folk | tomes, healing teacher (db person.jsonl:95) |
| Wujeel | Helstrom | | sap and herb seller, teaches Alchemy (db person.jsonl:41) |
| Okeeh-Ja | Helstrom hall | | stands in the hall (db place_need, helstrom seq 4) |
| trainers by place | | | the 17 above |
| the Agaceph illusionists | Hirecan, Icalca | Agaceph | test strangers with illusion spells, "freeze an intruder" (db place_note hirecan dangers/people) |
| Nisswo, tree-minder, sap-speaker | | | "the mage archetype in Argonia is a neighbour with a knack, a Nisswo, a sap-speaker or a tree-minder, never a robed academic" (lore/topics/magic-practice.md:53-57) |

## 3. How magic works and is regarded (the proposal must respect these)

- **Who hears the Hist.** Marsh-born Argonians with a hand on the bark (main-plot.md:48; lore/topics/hist-and-sap.md:105-106). Argonians hatched outside (lukiul) cannot hear at all (:107-111). Hissmir's trials let even non-Argonians speak with a Hist (:112-114). The Spray-Folk live too far from any tree to hear (db/culture.jsonl pearl), a Hist that speaks through the wind is heard by hanging chimes (hist-and-sap.md:118-119; the Chime-Keepers' culture), Tsonac's Hist is asleep and read by a tree-minder (culture sky-blue). Sap on a non-Argonian is a bloodlust hallucinogen (hist-and-sap.md:37-38; smuggling it is a crime, :168-170).
- **Sap and visions in the main quest.** A hatchling licks its tree's sap on its naming day and it shapes the body for life (main-plot.md:43); drunk, sap brings visions of far places (:49); all the trees share a root and one knows what the others know (:49-50); "a tree can also give a blessing to someone its people trust" (:50-51); "the player sees and uses what they are told: a sick tree, a blessing from a tree and a cup of sap that shows them a real place" (:60-61). The vision is shown as words on a black screen (:211-213; blocks "vision"). Sap makes a fighter stronger (:86). The grey paste is a paralysis poison that numbs the scar shut (:71-73).
- **The Unbound drain sap** (main-plot.md:15,69-75): a cult of the tribeless that draws sap, then seals the tree; Cuts-the-Old-Knot brews a draught strong enough to kill the Root's beast (:86); she drank sap and the Eye's power runs through it (:502-503,585).
- **The Toh-Reel-Ka's dreamers**: people kept in the cellar of Fort Chalkmoth, fed sap, who see what any tree has seen (:96-102,540-543). Only the main quest knows them; no tree-minder knows (lines/consistency.md:19-20).
- **The Eye of Argonia and the Root.** The Eye is cut from Hist amber, "the knot that joins every root"; used where it sits it heals every tree, lifted it parts every tree (main-plot.md:79-84,474-475). Three endings: Use (healed trees; stronger blessings; Fort Chalkmoth as house), Take (three trees in ten die; no Hist blessing again; Eye's Gaze power), Give (Cuts-the-Old-Knot as called ally; Knot-Breaker's Storm and Root Ward) (:575-607).
- **Powers the player gains from the story:** Hist blessings (timed ability); Eye's Gaze once a day; the called ally and its two spells; rank rewards; custom enchantments (Sisei-Xul's Rest, Morvayn's Due, Still Water, Hasp of the Falls, Firebrand, Factor's Seal, Lamp of Truth, Quiet Cloak). Approved "ceiling" additions: called ally by a power, a spell cast before a person as a test, a potion the player made handed in, the vision fade (owner-bar.md:176-183).
- **In place of shouts.** decision 0012 L23-25: "The Shout key/menu is unbound or repurposed (Hist communion powers, old 0042, can use the power slot)"; owner-rulings.md:439: "LT shouts" in the soulslike layout. blocks.md:62,65 `teach_spell`/`add_perk` name the Nightingale, Black Book, standing-stone and shout perks as the model.
- **Birthsigns / standing stones.** 0012 L23 removes standing stones. `story/lore/topics/birthsigns.md` (13 Jel-named signs; powers Ancestor Guardian, Moonshadow, Lover's Kiss; spells Beggar's Nose, Blessed Word/Touch, Star-Curse) was written for the old engine (`packages/game-core`) and is not carried to the new world; the db has give kinds `standing-stone` and `altar-power` that no place uses.
- **Necromancy.** "Raising the dead breaks no Argonian law, but a soul kept from its Hist is the Toh-Reel-Ka's business" (sisei-xul.md:44); to Argonians "raising and binding the dead is their own enslavement over again: the order of magic and the necromancers are enemies for that reason" (owner-bar.md:124-125); Argonians bind souls too, in urns, as punishment (sisei-xul.md:75-77); grave-stakes hold life that can fuel necromancy, pulling one raises a bog blight (lore/topics/magic-practice.md:49-52,93-95); Neeja is an Argonian necromancer and teacher (house-cardruhn.md:87). Resurrection costs the caster nearly all health and is killing Morvayn (:70-71).
- **Soul trap, soul gems.** An Argonian's soul is Hist sap and returns to the tree; soul gems are a foreign technology keeping canon function (magic-practice.md:72-74). Mysticism (soul trap, detect, reflect, telekinesis, mark/recall-style transport) "is available in the interior and rare in foreign hands" (:90-92). The plan teaches Soul Trap through an Argonian (house-cardruhn.md:178). Hedge-mages sell soul gems (db place_give :44,594,1183,1263,1476).
- **Fire.** No plan line makes fire feared. Plan fire: Fire Rune scrolls (chainbreakers:389), Conjure Flame Atronach (house-cardruhn:168), a spell-lit fire (house-cardruhn:178-186), "no Destruction tomes sold" (no trader-spells row lists Destruction).
- **Daedra.** "Jel has no words for the Daedra" (lore/topics/loading-facts.md:182); Daedra as "intrusions into a Hist-and-Sithis world" (50-side-quests.md:105); a priestess of Mephala and a spider mark are the Cardruhns' (sisei-xul.md:309-310).
- **Magic as folk literacy.** "Black Marsh day-labourers are accomplished Illusionists"; no robed-mage guild; foreign mages "only where foreign institutions do (Gideon, Stormhold, Blackrose garrisons, Imperial docks)"; spells "bought, found, traded and taught informally; scroll magic is common and cheap" (magic-practice.md:39-57); the Agaceph are "accomplished illusionists, as most day labourers in Black Marsh are" (db/culture.jsonl lime).
- **Schools.** Six: Alteration, Conjuration, Destruction, Illusion, Mysticism, Restoration (magic-practice.md:27-32); the owner's skill list for quests names Mysticism (owner-bar.md:44; owner-rulings.md:450). No quest names Mysticism as a way through; spell-groups.md uses Skyrim's schools.
- **The Sisei-Xul's skills:** Alchemy, Smithing, Enchanting, Alteration, Restoration, Destruction's poisons (sisei-xul.md:38-39); House Cardruhn: all Conjuration, Enchanting for soul gems, Necromantic Healing (house-cardruhn.md:36-37); Shadowscales: Illusion Muffle, Invisibility, Night-Eye, Throw Noise; Chameleon only as an enchantment (shadowscales.md:29-30); Eelskins: Enchanting, Telekinesis, Muffle, Throw Noise, Detect Life (thieves.md:28-29); Lampbearers: Calm, Fury, Mayhem, Throw Noise, Clairvoyance (lamps.md:28-29); Brethren "do not teach spells" (pirates.md:51).
- **How a spell is taught.** "One copy per spell, and two forms naming it differently are refused" (docs/design/quest-form.md:234-236): a rename must be the same in every quest that teaches that spell. Every taught spell must be used in that quest as one step (owner-bar.md:84-85). A reward is an ordinary item unless the story needs a named one (owner-bar.md:59-60). Nothing is levelled (0035).
- **Markers and riddles.** Objectives are marked by area, never the exact thing (sisei-xul.md:131; main-plot.md:142); riddle side quests have no marker until found (main-plot.md:520-524; owner-bar.md).

## 4. Where the proposal contradicts, duplicates or overlooks the plan

Format: proposal line -> what it says -> the plan's line.

| # | Verdict | Proposal | Plan |
|---|---|---|---|
| 1 | FALSE | L43-45 "Nobody in our world sells a spell. All ten kinds of trader ... stock smith's or apothecary's goods, and our own one trader sells books but no tomes." | 13 places already sell tomes (section 1b, db/place_give.jsonl:44,322,355,370,390,594,1154,1183,1263,1377,1451,1462,1476) plus a named seller (db/person.jsonl:95); `trader-spells` is a give kind (db/give_kind.jsonl) and `spell-trader` a person role (db/person_role.jsonl). The sellers are also named in the quests: pirates.md:167,169,467 and thieves.md:167. |
| 2 | DUPLICATES | L120-123 option 1 "A tree-minder ... sells healing, cures and poison. An Agaceph raft-trader sells Illusion ... About 15 to 20 sellers" | Taleeka-Ma (Helstrom, db :355), Tsonac's tree-minder pupil (:1377), Hirecan's Agaceph illusionist to Expert (:370); Archon's hedge-mage covers Restoration, Alteration, Illusion. Already 13 sellers; the proposal's native/foreign split is already in the records, with Restoration and Alteration sold by Argonian tree-minders. "Harbour pilots at Archon sell water spells": the plan sells Waterbreathing as potions at Seafalls and Gideon and by Bell Station's steward (merchants.md:149,270; main-plot.md:730). |
| 3 | DUPLICATES | L145-148,154-155 "About ten Hist gifts ... given by a tree-minder when the player has earned trust"; Drowned Root from Blackrose; Sap-Mend from "any tree-minder" | 15 Hist blessings are already placed (section 1b), incl. Blackrose's drowned Hist: waterbreathing for 8 h (db/place_give.jsonl:146) and Jal-Veesa's trust-gated blessing (main-plot.md:198-199). Gifts and blessings must be one system; the endings change the blessings: Use "Stronger blessings from every Hist" (main-plot.md:583), Take and Give "No Hist gives the player its blessing again" (:596-597,607). The proposal never says what happens to gifts. |
| 4 | OVERLOOKS | L154 Drowned Root "breathe water" | An Argonian already breathes water; the plan gives the Argonian a different blessing (resist poison, main-plot.md:198-199; sisei-xul.md:247; house-cardruhn.md:245). A gift list must say what each does for an Argonian. |
| 5 | CONTRADICTS | L38-39 "We removed the shouts (decision 0012) and put nothing in their place." | 0012 L23-25 reserves the slot: "repurposed (Hist communion powers ... can use the power slot)"; owner-rulings.md:439 "LT shouts". The plan already says what goes there. |
| 6 | CONTRADICTS | L69,L98-99 "The schools stay Skyrim's five ... the lore supports that" | magic-practice.md:27-32 keeps Mysticism ("six schools are Morrowind's six"); owner-bar.md:44 and owner-rulings.md:450 list Mysticism among the quest skills. Needs a ruling: five (and fix both) or six. |
| 7 | CONTRADICTS | L80,L99,L236 necromancy, atronachs, soul trap "stay a foreign crime", "sold only by foreigners", "abominations" to Argonians | sisei-xul.md:44 "Raising the dead breaks no Argonian law"; Neeja, an Argonian, teaches Soul Trap, Conjure Ghost, Necromantic Healing, Command Lesser Undead and Conjure Flame Atronach, and gives her Conjure Familiar tome (house-cardruhn.md:87,156-270; sisei-xul.md:284); Argonians bind souls themselves (sisei-xul.md:75-77); the enmity is about slavery (owner-bar.md:124-125), not about conjuration as such. PROPOSAL L61 "a house of foreign necromancers" is also wrong: the Cardruhns are Dunmer, but Neeja is Argonian. |
| 8 | CONTRADICTS | L76,L80 Mark and Recall, telekinesis, soul trap are "foreign (learned)" | magic-practice.md:90-92 Mysticism content is "available in the interior and rare in foreign hands"; Swims-Without-Ripples, an Argonian thief, teaches Telekinesis (thieves.md:178); an egg-minder teaches Detect Dead (sisei-xul.md:216). |
| 9 | CONTRADICTS | L125 "Stoneflesh becomes Clay-Skin"; L157 Wamasu's Answer from the Stone-Sleepers; L160 Clay-Skin of the Mound from the Clay-Mound People | The Stone-Sleepers' signature is already stone-skin: "Stoneflesh, the first of the Stone-Sleepers' stone spells" (sisei-xul.md:38,199), "Stoneflesh, Ironflesh, Ebonyflesh" sold at Tsonac (db/place_give.jsonl:1377), a tome of Ironflesh (house-cardruhn.md:237). The Clay-Mound People's Aroxhu branch is alchemy (sisei-xul.md:37; blessing Fortify Alchemy, db :84). Two stone-skin gifts under two tribes clash; and a rename must change every form naming Stoneflesh (quest-form.md:234-236). |
| 10 | CONTRADICTS | L125-127 renames "Turn Undead -> a grave-song", Magic Expanded jumping spells get marsh names | The quests name spells plainly: Turn Undead (sisei-xul.md:140,294,299), Tinur's Hoptoad (pirates.md:51,481; merchants.md:200,396), Calm, Muffle, Night-Eye, Throw Noise, Detect Dead, Poison Spray, Sun Fire... A rename means editing those lines and the form `names` together. "Grave-song" is already the order's name for its tradition (sisei-xul.md:109): align the rename to that. |
| 11 | OVERLOOKS | L44-45 "the player has the two starting spells and a test kit due to be removed"; L128 | The opening teaches Sparks by tome and gives firebolt and fast healing scrolls (main-plot.md:172-182); Heem-Jasa gives Cure Poison potions (:229). Nothing is "test kit" there; it is planned content. |
| 12 | DUPLICATES | L159 Grave-Song gift, L125 | The Sisei-Xul already has Turn Undead on Grave-Iron Claws (sisei-xul.md:140), Circle of Protection (:307), Guardian Circle (:141), Sun Fire (:349) and its own staff Sisei-Xul's Rest (:395): lays any undead it strikes. A gift that makes the dead "flee or fall" repeats Sisei-Xul's Rest and Turn Undead. |
| 13 | DUPLICATES | L145-146,L176 once-a-day powers on the shout button | The plan already uses two once-a-day powers as top-tier ending rewards: the Eye's Gaze (main-plot.md:593-594) and a Knot-Breaker power (:605-606), and a called-ally power (blocks.md:114). Ten earlier gifts of the same shape dilute them; note also "Root Ward" (main-plot.md:605) against the proposal's "root-bind", "Root-Call" (L158,L165). |
| 14 | CONTRADICTS | L161 Sea-Memory "shows the way to what you seek" for "finding the next step in open marsh" | The plan gives area markers only and riddle side quests with no marker until found (main-plot.md:142,520-524; sisei-xul.md:131; owner-bar.md "riddle side quests"). Sea-Memory also contradicts the culture: the Spray-Folk "live too far from any tree" (db/culture.jsonl pearl) and so have no tree-minder to give a gift (L145 says gifts come from a tree-minder). The region note already names "the Spray-Folk's sea-memory" as faith (story/design/world/regions/okuwun-rahei.md:29). |
| 15 | PARTIAL | L95-96 "the player of any race can be given Hist gifts"; "the lore lets outsiders speak with a Hist at Hissmir" | main-plot.md:198-199 already blesses any race; but hist-and-sap.md:107-114 says outside-hatched Argonians cannot hear Hist, only Hissmir lets them, and sap is a bloodlust hallucinogen to non-Argonians (hist-and-sap.md:37-38). The plan sidesteps by calling the blessing "the tree's", and by having the player drink sap in MQ3 (main-plot.md:211). Say so. |
| 16 | OVERLOOKS | L79,L122 "fire is sold only by foreigners and is feared" | No seller in the records sells Destruction at all (none of the 13 `trader-spells` rows names it). Destruction comes by quest only: Sparks tome (main-plot.md:173), Poison Spray from the Sisei-Xul "as old marsh fighters used it" (sisei-xul.md:321, native), Paralysis Rune (house-cardruhn.md:231), Fire Rune scrolls (chainbreakers:389). "Feared" is not stated in the plan. |
| 17 | OVERLOOKS | L59-60 "The Sisei-Xul ... teaches a spell in most quests" | VERIFIED: 7 of 13 quests teach a spell (q4,5,7,10,11,12,13) and 2 rank tomes (q3, q10) plus Neeja's Conjure Familiar (q8). But the proposal does not mention the reward ladder (sisei-xul.md:136-142), the three custom enchantments, or that the order's Alteration teacher is Akeeta-Sul. |
| 18 | OVERLOOKS | L146-148 gift "through the quest form's existing step: no new script" | The step is `teach_spell`/`grantAbility` of "our copy of a load-order spell under our name; one copy per spell" (quest-form.md:68,234-236). The owner-bar rule: a taught spell is used in that quest as one step (owner-bar.md:84-85) and a small choice must have a real difference in play (owner-bar.md "small choice"). Each gift needs a use step and a quest it belongs to; the proposal says "one line in each giving quest", which is not enough. |
| 19 | NAME COLLISIONS | L190-191 option 3: "a wisp", "a spectral wamasu", "miregaunt" | 86-never-reuse-names.md:19 bans King of the Murkmire's own names: "Spectral Wamasu", "Wispmother", "Aspect of the Hist", "Swamp Leviathan", "Sap-Speaker X" (personal names). "A generic label or a canon creature ... resting on its own UESP page" is free; "Spectral Wamasu" is a KotM creature label and has no UESP page: do not carry it as a summon's name. No proposed name is in `story/design/retired-names.json` (checked: Spore Cloud, Sap-Mend, Drowned Root, Stillstare, Chime-Hush, Wamasu's Answer, Root-Call, Grave-Song, Clay-Skin, Sea-Memory, Histskin, Sap and Song). |
| 20 | NAME NEAR-USES | L152-161 | "Root Ward" (main-plot.md:605) vs Root-Call/root-bind; "Grave-song" already a topic (sisei-xul.md:109); "Sea-Memory" in the okuwun-rahei note; "Still Water" ring (thieves.md:286) vs Stillstare; "Spore Cloud" is the name of an old-world item (`story/data/db/item.jsonl:433`, retired old data) and of a Hist-magic fact (magic-practice.md:49). "Clay-Mound People", "Chime-Keepers", "Stone-Sleepers", "Agaceph" are culture names (db/culture.jsonl) and fine; "tree-minder", "root-herald" are generic offices. |
| 21 | OVERLOOKS | L57-58 "Robed college mages do not exist within 400 miles of Lilmoth" | The records place a Breton dock mage at Lilmoth (db :594), a Dunmer enchanter at Thorn's "Conclave of the One" (:1263; house-cardruhn.md:213), a Conclave of Baal at Stormhold (20-world-provisions.md:205), a Dibella priestess at Gideon (:322). The lore line is "no Mages Guild survives" (db :44), not "no mages". |
| 22 | OVERLOOKS | L47-48 repairs "Mark and Recall do not know our world" | Plan items: magic-practice.md:91 allows mark/recall-style transport "where quests permit"; the travel network (boat, rootworm, coach) is the intended fast travel (owner-bar.md fast travel, rootworm stops main-plot.md:264-268). Mark and Recall would bypass it; the plan does not place Mark/Recall anywhere (no seller lists it; Archon's hedge-mage sells Alteration to Adept only). |
| 23 | OVERLOOKS | L196-197 option 3 "Sap as fuel ... sold by sap-gatherers" | Sap is already a plot item: "a real, tradeable, dangerous substance" (magic-practice.md:83-84), smuggling it is "the most lore-appropriate crime" (hist-and-sap.md:168-170), the Unbound take it and the main quest turns on it; a seller of sap as a combat drug collides with the Toh-Reel-Ka and Unbound premise (main-plot.md:86). |
| 24 | OVERLOOKS | L84,L170 "a spell at each level" (Novice to Master) | The planned sellers stop at Adept except Hirecan (Expert Illusion) and Tsonac (Expert Alteration); no seller teaches Master. Master spells come only by quest (Paralyze 75, Command Greater Undead 75). |

## 5. Gaps in the other direction: what the stories need and no existing spell gives

spell-groups.md:60-67 lists three: Chameleon (only as an enchantment; Still Water ring), Charm, a crafting spell. More found:

| Need | Where | Why no existing record serves |
|---|---|---|
| a spell "of ours that burns the guardian far worse than anything else" | main-plot.md:533 | no such spell; custom damage keyed to the hydra |
| scrolls "of a storm that strikes every head in reach at once" and "of a paralysing spell, enough to stop the guardian three times" | main-plot.md:532,535 | Stormcell/Marsh Squall and Paralysis exist (spell-groups.md:13-14) but no scroll record of them is named |
| potions that cure the hydra's venom quickly; an amulet that turns most of its venom | main-plot.md:531,535 | Cure Poison/Resist Poison exist; the specific potions and amulet are custom records |
| the Eye's Gaze once-a-day power | main-plot.md:593-594 | Mass Paralysis is a spell (spell-groups.md:14); a power copy is needed |
| Knot-Breaker's Storm and Root Ward (one a power) | main-plot.md:605 | not mapped to any spell |
| the called ally: two spells that move a named person to the player and back | main-plot.md:603-604; house-cardruhn.md:375, 452; blocks.md:114 | "A named ally called by a power" has no stock spell; it is a new block |
| the eel-slime effect (ripper eels ignore the player) | thieves.md:321 | no stock effect; a faction or ability |
| a Chameleon ring and a Chameleon spell | thieves.md:286-287; shadowscales.md:29-30 | no Chameleon spell (spell-groups.md:62) |
| a Conjure Familiar tome sold at Thorn's apothecary | house-cardruhn.md:103-104 vs db/place_give.jsonl:1261,1263 | Thorn's apothecary sells ingredients and Thorn's enchanter sells only Illusion and Alteration: the join test's tome has no seller (Lilmoth's Breton mage sells Conjuration, :594) |
| a spell-seller at the Blackrose outpost (Muffle) | thieves.md:167 vs db: no `trader-spells` row for blackrose | the records name only trainers, the apothecary and the Hist blessing there |
| Detect Life for the Eelskins | thieves.md:29 | listed in the skills, taught in no quest |
| Fury, Mayhem for the Lampbearers | lamps.md:28 | listed, taught in no quest (Mayhem comes as a Brethren scroll) |
| "stronger blessings from every Hist" | main-plot.md:583 | the blessing records are one tier; a second tier must be made |
| "no Hist gives the player its blessing again" | main-plot.md:596-597 | needs a gate on every blessing record (or a removal) |
| a power that a rival's undead cannot be held by: Hasp of the Falls (cannot be held by Paralysis) | chainbreakers-newworld.md:559-560 | Resist Paralysis exists as a birthsign effect (birthsigns.md:60) but no stock enchantment is named |
| Mysticism spells as a school | magic-practice.md:27-32 | Skyrim has no Mysticism school |
| a native Conjuration summon for the Argonians | none in plan | Conjuration is all necromancy and atronachs in the plan (house-cardruhn.md:36); no marsh summon is promised anywhere |
| anything for the Chime-Keepers, Island of Blackrose, Spray-Folk, Three Waters, Naka-Desh, Hutan-Tzel, Mine-Burners, Warden Marches | db/culture.jsonl | no plan line gives these cultures any magic, seller or blessing beyond a shrine blessing |

Not in the plan at all: a Destruction seller; Master-level sellers; Mark/Recall; Levitate; potions of Alchemy beyond the named ones; any spellmaking service
(magic-practice.md:88-89 licenses "spell vendors, spellmaking and enchanting services"; only enchanters exist).

Counts: section 1a about 63 rows (spells, scrolls, powers, enchantments, blessings, potions), 15 Hist blessings, 13 spell sellers, 7 enchanters, 17 magic trainers, 4 named persons in db, 22 named persons or offices in section 2, 24 findings in section 4, 17 gaps in section 5.

Covered: story/design/quests/lines/*.md (all 12, by keyword then read the passages around every hit), spell-groups.md, reward-gear.md, 86-never-reuse-names.md, 20-world-provisions.md, 50-side-quests.md, 60-writing-and-lore.md (keyword), story/design/owner-bar.md (keyword), story/lore/topics/magic-practice.md, birthsigns.md, hist-and-sap.md, retired-names.json, docs/decisions/0012, docs/design/quest-form.md and blocks.md, docs/owner-rulings.md (magic entries), newworld/story/data/db (place_give, person, culture, give_kind, person_role, trade_kit, place_note) · Skipped: 20-world-provisions.md, 50-side-quests.md and 60-writing-and-lore.md read by keyword only (they are imported old-world plans, with no new-world spell content); the main plot's Act II quests 5-12 read for magic only; lore topics other than the four named; story/playtests.
