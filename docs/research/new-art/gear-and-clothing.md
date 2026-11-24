# Gear, clothing and ornaments: where the pool is thin (call #93, lane WEAPONS / ARMOUR / NON-ARMOUR CLOTHING)

Research only. Method: the common brief's four steps. Evidence is a join of `newworld/out/world.sqlite` (`item`, `person_item`,
`guard_issue`) with model paths read from `out/places/catalogue/bases.jsonl` and from the ESPs unpacked in
`out/places/catalogue/plugins/` (my own throwaway reader; ARMO = the ground model `MOD2`, WEAP = `MODL`).

## Live docs that cover this

`docs/design/items.md` is the one doc (ladder, tribes, peoples, mods, "Still no model anywhere" at its end). I CONFIRM its counts
(ladder table, 6 Act I places) and its "no model anywhere" list. I SUPERSEDE its tribe table's claim "No model is made for any one
tribe: the difference is carried by which owned pieces each tribe takes first": measured below, 6 of 18 tribes' signature weapon
type has no Black Marsh model at all, and 3 tribe overlays (gold, pearl, rust) name a material that has no light-armour model. The doc to edit if
the owner relaxes the art rule: `docs/design/items.md` (section "Mods" and the closing list), plus `docs/design/consistency.md`
if place records change.

## FINDINGS (counts)

Caveat on the measure: "distinct models" = distinct ground-model nif paths of our 767 filed WEAP/ARMO records (344 weapons, 423
armour). 746 resolved; 21 Animated Armoury records (all the pikes, halberds, staves, rapiers, claws, whips) did not resolve
(`NewArmoury.esp` is not in the catalogue folder). Ground model is a proxy: a recolour that swaps only textures through an
alternate-texture set counts as one model (I counted 668 model+texture pairs against 638 models, so recolours are rare).
Records 767 -> 638 models -> 668 looks. Records from vanilla masters: Skyrim.esm 63, Dragonborn 10, Dawnguard 3, Creation Club
amber 13 = 89 (11.6%). Records from Black Marsh themed plugins (HTBM Cipactli, King of the Murkmire, BMN, Argonian Weapons,
Obsidian, Boneweave, Seagrave, Bamboo, Grummite, Naga-Kur, Stormhold, Ancient Argonian, clubs): 275 records, 240 models.

### 1. Ladder tier by slot: records / distinct models

| Tier | weapons | light armour | heavy armour | shields | other ARMO (clothes, jewellery, props) |
|---|---|---|---|---|---|
| T1 | 90 / 84 | 24 / 13 | 2 / 2 | 1 / 1 | 20 / 18 |
| T2 | 76 / 66 | 117 / 100 | 24 / 23 | 15 / 15 | 3 / 3 |
| T3 | 95 / 89 | 58 / 40 | 50 / 35 | 13 / 12 | 12 / 8 |
| T4 | 68 / 61 | 35 / 35 | 7 / 7 | 3 / 3 | 6 / 6 |
| T5 | 15 / 15 | 12 / 12 | 5 / 5 | 1 / 1 | 4 / 4 |
| T6 | 0 | 1 / 1 | 8 / 8 | 2 / 2 | 0 |

Breadth is large (most cells have a different model per record). The thinness is in WHICH models, not how many.

### 2. Where a tier/slot is one model, a relabel, or vanilla

- T1 weapons "bog iron" (11 records) are Skyrim.esm's own iron and steel models (`weapons/iron/longsword.nif`, `ironmace`,
  `steelsword`, `steeldagger`, `steelmace`, `steelwaraxe`, `steelbow`, `woodenbow`, a pickaxe): Nordic-looking Skyrim iron
  relabelled bog iron. T3 `scimitar.nif`, T4 elven/glass dagger and Nightingale blade/bow are vanilla too.
- Banujha "heavy bog iron of their own smelting" (kits.json tribe-steel-blue): the only heavy bog-iron piece is
  `AnWamasuIronCuirass` = vanilla `armor/iron/male/cuirasslightgnd.nif`. One piece, no helm/gauntlets/boots. Heavy bog iron: 1 record.
- Hide (T1, tribal camps' guard issue, five tribes): 2 light-cuirass models, both vanilla (`armor/hide/m`, King of the Murkmire's
  `armor/ominous` robes), boots `clothes/forswornarmor` (Forsworn: Nordic-adjacent), helmet one model. One hide shield (HTBM).
- Saxhleel (T2, "the marsh's own working issue", every village/outpost/farm of all 18 cultures): 19 cuirass records, 9 models, but
  one Argonian look: Stormhold Warrior's `son6of6tredis/armor/argonian` set (armor, pants, three pauldron variants) plus four
  vanilla reuses filed as Saxhleel (`armor/studded` x2, `clothes/farmclothes01`, `armor/thievesguild`). Weapons: 5 records, 5 models.
- Scale (T3, the town/city guard issue, `scale.json` guard_issue "argonian-scale", all 18 cultures): the three issued pieces
  (`Black Marsh North.esp:037DF0/F3/F7`) are boots = Shadowscale `shadowscale/feet_gnd`, gauntlets = Stormhold `argonian/gauntlent`,
  cuirass = `BMArgBody` with NO ground model. The "BM&V scale guard" is a reuse of two other sets; every town watch in the province
  looks the same. Light scale as a whole: 16 records, 5 cuirass models, three of them vanilla/other-culture (`bandit1go`,
  `spellsword`, `altscalearmor`).
- Shell: heavy only (4 records) + 2 shields. NO light shell armour exists. Bone plate: heavy only (4 Bone Cultist pieces) + weapons;
  NO light bone plate. Yet tribes gold/pearl ("light shell"), rust ("light bone-plate") and the Spray-Folk are specified as
  wearing those (kits.json tribe-gold, tribe-pearl, tribe-rust): pearl has no wearable at all, gold and rust fall to saxhleel/hide.
- Caravan steel (Khajiit; also tribe umber): 8 weapons/8 models but 25 light + 19 heavy + 2 shield records on only 8 + 4 + 1
  models (the Apex set recoloured: 19 heavy records, 4 models; heavy cuirass 7 records, 1 model).
- Greenwood (Bosmer): 21 records, 15 models, but light helmets are 5 hood/helm models of one pack; Bosmer elders' "T4" set is
  the same pack relabelled.
- Imperial: 73 records, about 68 models: the widest of any foreign kit, which is itself a finding (foreign gear has more variety than Argonian).
- Hist amber (T5): a Creation Club set, 13 records, vanilla-master. Xanmeer T6 heavy = HTBM "jaguar armor/nordiccarved..." (Nordic
  carved model labelled Xanmeer), plus `shieldofmagnus`; Masu plate T5 = `armor/nordplate` (Nordic plate) + two King of the
  Murkmire Argonian warrior pieces. The ladder's top end leans on Nordic meshes.
- Bronze (T4 "Ancient Argonian"): 3 heavy pieces (cuirass, gauntlets, tail piece), no helm or boots.

### 3. Weapon types with no Black Marsh model, by tier (distinct models from BM-themed plugins)

| type | T1 | T2 | T3 | T4 | T5 | T6 |
|---|---|---|---|---|---|---|
| sword | 14 | 13 | 6 | 4 | 0 | 0 |
| dagger | 7 | 7 | 3 | 5 | 0 | 0 |
| waraxe | 3 | 4 | 2 | 3 | 0 | 0 |
| mace | 10 | 6 | 3 | 4 | 0 | 0 |
| warhammer | 9 | 5 | 5 | 3 | 3 | 0 |
| greatsword | 9 | 4 | 8 | 4 | 1 | 0 |
| battleaxe | 2 | 2 | 3 | 2 | 1 | 0 |
| bow | 7 | 3 | 3 | 3 | 0 | 0 |
| halberd, pike, quarterstaff, rapier, whip, claw | 0 | 0 | 0 | 0 | 0 | 0 |
| crossbow | 0 | 1 (blowgun) | 0 | 0 | 0 | 0 |

- Zero BM-themed models for pike (5 records), halberd (4), quarterstaff (4), rapier (3), whip (2), claw (2): all Animated
  Armoury (generic medieval) and the six new types are the signature weapons of six tribes (crimson-red pike, forest-green
  quarterstaff, lime claw, plum whip, rose rapier, sky-blue halberd; `items.md` tribe table) = one third of the cultures.
- T5/T6 weapons: Argonian-themed models stop at T4 except Xanmeer great obsidian (5) and CC amber (8, vanilla master).
  T6 has no weapon at all (Xanmeer relics are armour only).
- Battleaxe: only 2 models per tier T1-T2. Bows: T5 0, T6 0; no Black Marsh crossbow (Argonian-made crossbow is a lore gap,
  `items.md` closing list).
- T3 heavy armour BM-themed: 0 (heavy T3 = chitin, bonemold, bone plate, caravan, greenwood, imperial: all foreign).
  T1 heavy BM-themed: 0. Heavy gauntlets/boots at T4 = 2 models each.

### 4. Cultures, tribes, factions: how distinct (kits.json overlays, scale.json guard_issue)

All 18 cultures are colour-named tribes (`kits.json` overlays `tribe-*`). Collisions:
- indigo (Naka-Desh) and sky-blue (Tsona-Kaleel): identical wear list (scale, hide) and both T1-T3 light; differ only by weapon.
- olive (Blackrose) and pale-green (Gideon) and crimson-red (Warden Marches, heavy): all wear the Imperial pool; pale-green and
  olive differ by corsair. Three tribes plus the marines, Company and Imperial households share it.
- plum (Three Waters) and rose (Lilmoth) wear saxhleel, as does the default village issue and forest-green; rose adds masu plate (3 distinct Argonian-warrior models).
- gold and pearl (shell light = no model), rust (bone-plate light = no model), forest-green and magenta (hide = vanilla/Forsworn).
- stone-grey = the Dunmer household's list (netch/chitin/bonemold); umber = the Khajiit household's (caravan steel).
- Tribes wearing vanilla-derived looks as the main body: forest-green, magenta, indigo, sky-blue, rust (hide + vanilla), plus
  every tribal camp/cave/outlaw camp issue (hide, `scale.json` "tribal-hide").
- Every Argonian town/city watch in the province: one look (the reused scale set); every Argonian village: one look (Stormhold).
  The 18 cultures differ in tint, not in dress.
- Factions: the nine lines' reward gear (reward-gear.md) is good where a pack exists (Shadowscale, pirates, Company, Ancient
  Argonian for the Unbound, Cipactli armour for Toh-Reel-Ka) but: Eelskins' "Linwe-style hooded armour" and "Thieves' leathers"
  are vanilla Skyrim; Lampbearers/Sisei-Xul/Cardruhn rewards are King of the Murkmire/vanilla Dunmer/robes; Chainbreakers share
  Toh-Reel-Ka's and BM&V's Argonian leathers (the same models as the Saxhleel/guard issue).
  `arcane-mage-armor` (50751) and `dx-necromancer-robes` (38201) are rows in dependencies.json but NO items of them are filed in
  `item` (no plugin among the ARMO counts): reward-gear lists them as given; the filing is owed.
- Fall back on vanilla/Nordic-looking: T1 bog-iron weapons; hide/leather T1-T2 light (studded, hide, Nightingale, thieves guild);
  Banujha heavy; Masu `nordplate`; Xanmeer T6 `nordiccarved`; jewellery; clothing (below).

### 5. Non-armour clothing: plans and pool

- `kits.json`: 23 trade kits. `wear` rows exist for only 11 of the 23 (and they are all armour slots: ArmorCuirass of leather/hide/
  scale/saxhleel/netch/chitin/bonemold/imperial/corsair/shadowscale/caravan). 12 kits have `wear: []`: gatherer, weaver, carver,
  builder, elder, trader, host, boatman, clerk, resident (and child, trainer, spell-trader through role "resident"). The
  people the province is made of (fishers wear hide/leather cuirass; priests saxhleel) have no cloth plan: none for commoners,
  children, elders, traders, innkeepers, bondsmen, slaves, bonded labour, priests' vestments (other than the Water-clan robes in
  items.md), tribes by wealth band. goods.json has 2 "clothing" kinds as wares only.
- What the stocked six places show (`person_item`, 165 persons): 39 persons have a worn armour/clothing row; 126 have none and keep
  BM&V's base outfit. Of the 39: 20 wear vanilla Skyrim.esm pieces (farm clothes 1-4 x10, monk robes x4, beggar robes, fine
  clothes, leather helmet x4), 14 BM&V's scale set, 9 King of the Murkmire, 5 HTBM. Jewellery: 32 plain vanilla silver rings and 4
  silver necklaces and 1 gold ring: all `armor/amuletsandrings/*go.nif`.
- Non-armour clothing models in the whole stock: vanilla Skyrim 6 (beggar, farm 1-4, fine, monk robes); Telvanni robes 10 (Dunmer,
  Tamriel-neutral); Moon Monk robes 12 records on 4 models; Bosmer headdress props 3 (deer skull, antlers, feather); Aves
  amulets 5 records on ONE model; Shadowscale body/arms 2; King of the Murkmire's Argonian robe/hood/hat/boots/gloves (An-Wamasu,
  Saxhleel Tribal) ~12 pieces; Funerary/Bog-blight mask 4 records, 1 model.
- Estimate of the province in vanilla farm clothes, furs and Nordic tunics: unmeasured for the 252 unstocked places (not yet
  drafted); in the six measured places the share of persons with an authored worn row in vanilla pieces is 20/165 = 12%,
  with an authored non-vanilla row 19/165 = 12%, with no row 126/165 = 76% (their outfit is the source NPC's: BM&V's, Tropical
  Skyrim's or the vanilla ones the build "set dressing" keeps). Trend: when the remaining places are stocked, the kits above put
  hide/leather cuirass and vanilla farm clothes on everyone who is not a guard or tribe fighter.
- Argonian-specific problems: (a) human body-fitted outfits (almost all clothing mods are CBBE/3BA/HIMBO/UBE) need an ARMA that
  lists ArgonianRace and a mesh that does not clip the Argonian body; I could NOT verify any candidate beyond its description
  (Nexus pages return 403 to the fetch tool; only Simple Straw Hats 89962 says "cat or lizard"). Cheap check owed: read each
  candidate plugin's ARMA race lists (my reader in the scratchpad does it in ~60 lines). (b) Tails: body armour hides the tail
  node unless the mesh has a tail slot (slot 43/46 conflicts, "Tail Binder" mod 7260, cloaks mod 85894 removes tail slot):
  loincloths and wraps are the only outfits that naturally leave the tail free. (c) Heads: Argonian head shape/horns/frills mean
  vanilla helmets/hoods clip; head items must be separate Argonian ARMAs or circlet-slot pieces (circlets use a rigid head bone
  attach, so they are the safest); hoods/hats of humanoid fit clip the snout. (d) Feet: digitigrade-ish Argonian feet: shoes clip;
  "Lizards Don't Wear Shoes" 44986 exists, sandals/wraps best.
- What the lore says they wear (`material-culture.md:53-56,78-81,165-171`): pre-Duskfall layered cloth, leather, bone, bronze,
  volcanic glass, adorned with feathers, dyed yarn, jewels, bronze emblems, gold; Naga-Kur armour from their own dead (scales,
  hide, bone, frills and spines); Xit-Xaht bone plate with exposed midriff, loincloths, sandals or bare feet, layered helms whose
  layer count shows status; tail bands of coloured leather with bells, tail stockings with hot-stone pockets, spines and plumes,
  copper horn caps, silver frill clips, betva-hen feathers on naheesh elders, crocodile-tooth necklaces, blue jasper jewellery
  ("masters of crafting jewellery"), jade death masks (Sul-Xan), red robes and skull masks (Kothringi Ideal Masters), weavers
  of grass/fibre, crocodile armour, turtle-shell shields, giant-snake hide, mother-of-pearl, silver. ESO's Murkmire/Elder
  Argonian style (UESP search result; pages not fetchable) uses hackwing plumage as its material. 
- Jewellery/masks/headdresses stock vs lore: stock has vanilla rings/amulets (18 models), Ave's necklaces (1 model), Funerary masks,
  Moon Monk masks, Bosmer skull/antler/feather props, Telvanni hoods. Missing: frill clips, copper horn caps, feather crests,
  tail bands/bells, crocodile-tooth/jasper necklaces, jade masks of our own, shell/bone/pearl ornaments. Shields: 35 records in
  the whole ladder; BM-themed shields exist only at T1 1, T2 12, T3 3, T4 1, T6 2; none turtle-shell or reed.

## Step 2: Nexus candidates (both games, names and descriptions)

What was searched: `tooling/nexus_search.py` (Special Edition and the 2011 game, name wildcard plus whole-word description match, 30
hits per term per game and field), 64 terms: Argonian, Saxhleel, Black Marsh, tribal, loincloth, sarong, wrap, sash, grass skirt, reed,
feather, headdress, crest, bone armour/armor, shell armour/armor, turtle shell, scale armor, jade, obsidian, flint, macuahuitl, club,
tooth, shark, crocodile, harpoon, gaff, blowgun, atlatl, straw hat, sandals, necklace, amulet, bracelet, mask, shield, Aztec, Mayan,
Polynesian, jungle, swamp, witch doctor, voodoo, fisher, slave rags, "armor resource", "clothing resource", "weapon resource",
"modders resource", "modder's resource", lizard, mesoamerican, tiki, totem, spear, javelin, pike, halberd, quarterstaff, rapier, whip,
claw (4,309 hits, 1,691 gear-category mods after de-duplication; names and summaries read for the top of each term; about 45
descriptions read in full with the API). Terms with no fitting gear-category hit by name or description: sarong, grass skirt, Polynesian, tiki, mesoamerican, gaff, atlatl returned no
gear-category mod by name or description that fits (the hits were body/skin mods and unrelated words). Nexus pages and UESP return
403 to the fetch tool, so descriptions, summaries and permission lines are from the API only; I looked at no screenshots and no
meshes of any candidate, so "Argonian fit" is only what a description states. A 2011-game mod (`skyrim:<id>`) is usable only after its
meshes are converted to Special Edition format (nif version, BSLightingShaderProperty, "44" in the community's phrase); the port
route for each is named.

### 2a. Special Edition (assets usable as player downloads)

| Candidate | Id | Author, endorsements | Holds | Argonian fit and permission |
|---|---|---|---|---|
| Shifts-Sand's Saxhleel Sundries (DEMO) | 191593 | YourFellowFern, 6 | ESO ports: Nisswo robe, shell armour, "Argonian Warrior" armour, Tribalwear (m), Tribalwrap (f), Voskrona set, Argonian robe set, Deathmask, Shadowscale set | Made for Argonians ("my Egg-Siblings"); weight-paint faults, some dark armour; author owns no rights (ESO rips); forge-recipe only. Strongest match to the clothing and shell gap |
| Argonian (Saxhleel) Weapon pack | 67137 | MetalMonsterFNV, 340 | battleaxe, sword, dagger, greatsword, mace, waraxe, warhammer (no bow) | ebony-level stats, we re-tier; no permission line found |
| Saxhleel War Club | 35555 | Muoviori, 187 | one two-handed club (warhammer reach, greatsword speed) | no permission line found |
| Simple Straw Hats | 89962 | GolinskiPRH, 516 | straw hats in the circlet slot, "man, woman, cat or lizard" | states lizard fit; credit required; "modder's resource" |
| Argonian Warrior Armour SSE Port | 96624 | gUISTASSI, 59 | the Reel-Ka warrior set (ESL, plus an integrated edition and a Heart Stone necklace and shield) | ported with the original author's open permission; our King of the Murkmire already holds this set as Masu plate (`argonianwarriorarmour/...` models), so only the shield and necklace are new |
| Equipable Beast Tails (HDT SMP) | 31745 | ansav042, 1,714 | an equippable Argonian/Khajiit tail item | tail node utility; physics framework |
| Feathery Argonian Tails (SSE) | 40560 | Nikikuriton, port by Byrdworker, 2 | fatter spiked, feathered tail, female | credit required; original author left Nexus |
| Argonian Fins / Kabu's Argonian Fins | 2504 / 65428 | Chilean Wolf 2,304; Kabunouveau 2,131 | head-fin and horn meshes | body-part replacers, not gear |
| I'noh-Ssu-Keh War Mask | 82282 | Mihail, 231 | rigid tribal war mask | check ArgonianRace in ARMA |
| Giant Club Variety | 104029 | Mihail, 1,230 | crude giant club meshes | giant scale; take as two-handed hammers |
| Ancient Bone Armor | 119440 | Aokili, 6,141 | bones-and-leather modular set | CBBE/3BA/UBE/BHUNP only |
| Tribal Clothes | 120203 | contentcat, 6,169 | tribal cloth outfit, 4 colours | CBBE/BHUNP, SMP physics |
| Riverfolk Clothes | 135136 | Pulcharm, 6,563 | "Bjoulsae tribes" outfit | needs FSMP |
| Common Clothing Expansion | 134088 | Horn, 9,414 | 4 lore-friendly commoner outfits and a hood | vanilla-like, Nordic-ish |
| Kreiste's Fisher Outfit | 59836 | Kreiste, 303 | fisher outfit | body fit |
| Slave Rags | 68917 | SE port, 305 | ragged slave outfit | body fit |
| Voodoo and Witch Doctor Arsenal (port) | 181332 | SolidSnonk, 7 | modular witch-doctor armour, masks, mojos, charms | SKSE perk system; take items |
| Red Eagle Reborn SSE | 43042 | Araanim, 471 | Reachman/Forsworn bone-and-feather trophies, ruin assets | Reach, Nordic-adjacent look |
| Aegyptus | 165651 | cc, 5,079 | headdress and loincloth outfit, SMP | Egyptian style, CBBE/BHUNP |
| Barbarian Loincloths | 9325 | Viltuska, 786 | six male loincloths | Nordic barbarian look, male |
| Katie's Beast Race Aesthetics Compendium | 45654 | katiexmongo, 397 | a curated list of Argonian mods with an "ESO Lore Preset" section (Naga-Kur, Saxhleel Sundries, Argonian weapons, Argonian Warrior Armour, Black Marsh Weapon Set, "Assorted Argonian Accoutrement"); a map of what exists, not gear | the list names the two LE finds below |
| Zim's Immersive Artifacts, Immersive Weapons, Expanded Skyrim Weaponry, Bob's Armory | 9138, 16788, 2300, skyrim:12060 | Zim, Hothtrooper, EngineersLogic, Mr Dave | generic medieval weapon variety (spear, halberd, club) | not Black Marsh; no use |

Not new but confirmed: Argonian Macuahuitl, Black Marsh weapons set, Ancient Argonian, Naga-Kur, Funerary Masks are already rows.

### 2b. 2011-game mods (need conversion to Special Edition meshes)

| Candidate | Id | Author, endorsements | Holds | Argonian fit and permission, port |
|---|---|---|---|---|
| AmA - Argonian Mercenary Armor with Armored Tail | skyrim:27676 | Spyke-Mayfly53, 3,353 | Argonian-based armour with an armoured tail piece; lizard scale armour | made for Argonians, tail slot included. Permission line: none found. Convert in the Creation Kit and optimise (Cathedral Assets Optimizer), the route Katie's list gives |
| Marsh Armor, Custom Ebony Argonian Heavy | skyrim:23920 | Spyke, 1,007 | heavy ebony armour made for Argonians | male only; no permission line; same conversion |
| HistBone and Bonewood Argonian Armors | skyrim:99144 | Sabbath6100, 48 | male and female bone and wood armour, heavy and light | "for all races", moss details; no permission line; conversion needed. Fills light bone plate |
| Argonian Warrior Armour (LE original) | skyrim:105061 | gUISTASSI, 107 | the Reel-Ka set | already ported (96624) |
| Edhildil's Argonian War Tails | skyrim:28502 | Edhildil, 281 | tail replacers: spiked ball, scorpion stinger, thorned, spiked, trident | "use at will, credit required": clearest permission line of the lot |
| Edhildil's Witch Doctor BBP | skyrim:44827 | Edhildil, 3,315 | witch doctor armour, one weapon, 7 items | female BBP only; credit required |
| Argonian Raptor Feet | skyrim:19283 | J Hamilton, 4,128 | Argonian-specific models for every vanilla boot and shoe | made for Argonians, conflicts with any boot mod; no permission line; solves the footwear clipping problem |
| Ghosu - Helmets, Bone Shield and Tribal Staff | skyrim:43293 | Ghosu, 3,010 | skull helmets, a bone shield, a tribal staff | "ALL MY ASSETS ARE FREE TO USE"; rigid pieces |
| Gemling Queen Resources | skyrim:54483 | Saerileth, 536 | jewellery meshes and textures | "blanket permission to use, modify, rehost or port to Special Edition, credit given": the clearest permission for necklaces and rings |
| Gemling Queen Jewelry | skyrim:52266 | Saerileth, 16,805 | jewellery set | same author; same permission statement |
| Static Armors and Clothing Resource | skyrim:69691 | Zylice, 122 | static (non-skinned) armour and clothing pieces | resource, credit required; suited to rigid head and shoulder pieces |
| Lizard Frog Hats | skyrim:88009 | 0Theara, 35 | two frog and lizard hats | "free to use assets" |
| Feathers for humanoid males and females | skyrim:25393 | zzjay, 1,856 | a craftable feather ornament (jewellery slot) | a feather ornament; no permission line |
| Poison Dart Launcher | skyrim:29514 | rcavanah, 115 | a crossbow that fires darts | an alternative blowgun; needs Dawnguard |
| Aztec Macahuitl | skyrim:20216 | Tzontlimixtli, 182 | macuahuitl and large macuahuitl weapons and armour | duplicates our Argonian Macuahuitl row |
| Jade Blade LE Port | skyrim:110218 | spaz490 and turtlegodking, 15 | a jade blade | credit given; the only jade weapon found; a katana-type |
| Obsidian Axe, Obsidian Sword | skyrim:14550, 36121 | Nicoroshi 160, LordStuff 70 | single obsidian pieces | the axe may be converted but model/texture "remain specific" |
| Barbarian Loincloths | skyrim:16167 | Viltuska, 953 | same as 9325 | SE version exists |
| Leather Sandals | skyrim:75905 | DenenC, 1,441 | sandals (heavy, light, cloth), female | human feet |
| Tribal Might Armor, Tribal Hunter Armor, Warchief Armor | skyrim:10235, 71705, 13366 | Hairon, Cursist, Hothtrooper | tribal-named armour (glass retexture; female hunter; orc/Nordic barbarian) | not Argonian; Warchief uses CD Projekt assets "with permission" |

LE note: the 2011-game port route needs the owner's decision on the conversion step (our "asset-only" rule: we copy records and the
player downloads the mod; a 2011-game mod downloaded by the player would need conversion by the player or by us, which is a
file change, not a record copy). I did not verify any permission line beyond the description text.

## Step 3: what remains for our own models

Owner rulings applied: (1) own weapons are new models that copy an existing record and swing exactly like it; (2) any weapon type in
Animated Armoury or another of our sources has animations taken as good: our own version copies that record and swaps the model;
(3) long thin shafts are a generator weakness: generate only the head or blade, build the shaft by script (a parametric cylinder
in Blender), then join and set the node. Head-and-shaft assembly is therefore part of every polearm and staff row.

### A. Weapon swaps (new model, copy this record)

| Object | Copies the record of | Swings as | Where seen | Size | Difficulty |
|---|---|---|---|---|---|
| Jade or jadeflint sword | an existing sword record (our `ladder` sword of the tier) | sword | priests, chiefs, shrine rewards | 0.9 m | easy |
| Jade dagger / ritual knife | a dagger record | dagger | Hist priests, Sisei-Xul, Sul-Xan | 0.35 m | easy |
| Jade or flint war axe | a waraxe record | waraxe | hunters, Naga | 0.7 m | easy |
| Crocodile-tooth club | a mace record | mace | tribal camps, Naga | 0.8 m | easy |
| Crocodile-tooth maul | a warhammer record | warhammer | tribal camps | 1.2 m | easy |
| Reed-bundle or obsidian-edged club | battleaxe record | battleaxe | tribal | 1 m | easy |
| Toothed or fishbone sword (saw edge) | a sword record (`SilvBone` shotel is the nearest) | sword | Xit-Xaht, Spray-Folk | 0.9 m | easy |
| Naga-Kur bone-and-frill sword, dagger | sword, dagger records | sword, dagger | Naga-Kur camps | 0.9 / 0.35 m | easy |
| Eel gaff / fishing hook | dagger record | dagger | fishers, Eelskins | 0.8 m | easy |
| Pike with a bone or obsidian head | the Animated Armoury pike record (`power_kind` pike, keyed on AA's keyword) | greatsword | Warden Marches (crimson-red) wardens | 2.4 m | easy-medium: generate the head, make the shaft by script |
| Spear / trident / harpoon with a fishbone or flint head | the Heavy Armory, HTBM or New Armory spear record (typed greatsword); Seagrave trident is the nearest | greatsword (shortspear: sword) | river hunters, harbour folk, fishers | 1.8 to 2.4 m | easy-medium: head only plus scripted shaft |
| Halberd / glaive with an obsidian blade | the Animated Armoury halberd record | battleaxe | Stone-Sleepers (sky-blue) | 2 m | easy-medium: blade only plus shaft |
| Skull-topped Hist staff, plain quarterstaff | the Animated Armoury quarterstaff record (Heavy Armory has one too) | battleaxe | Root-Folk (forest-green), priests | 1.8 m | easy-medium: skull or finial only plus shaft |
| Rapier with a shell or bone guard | the rapier record under the SkySA rapier pack (AA keyword) | sword | Lilmoth (rose) | 1 m | easy |
| Flail / whip with bone segments | the Animated Armoury whip record | mace | Three Waters (plum) | 1 m | easy-medium: a rigid chain in one nif |
| Claws with bone or chitin | the Animated Armoury claw record under SkySA claw | dagger | Agaceph (lime), Chainbreakers | 0.3 m | easy-medium: paired, two meshes |

### B. Shields, masks, headdresses, jewellery (rigid, copy an existing record)

| Object | Copies | Difficulty |
|---|---|---|
| Turtle-shell round shield, reed-wicker shield, boss-and-bone shield | a vanilla shield record (arm attach node) | easy-medium: static; copy a vanilla shield nif's node structure |
| Feather crest, head-fan, copper horn caps, silver frill clips | a circlet or helmet record with an ArgonianRace ARMA | medium: rigid but must fit the Argonian head |
| Jade or shell death mask, Hist mask | a helmet record (e.g. Mihail 82282 or Funerary Masks) | easy-medium |
| Crocodile-tooth, jasper, pearl necklace | an amulet record (the nif is skinned to 1 to 2 spine bones) | medium: Blender weight copy |
| Shell, bone, jade rings and bracelets | a ring record (rigid, finger bone) | easy |

### C. Still not plain swaps

- Bows and crossbows: bows need string rigging; crossbows use Dawnguard's animation (the blowgun and Poison Dart Launcher are templates).
- Thrown weapons, atlatl, nets: need new animation or script.
- Skinned outfits: loincloth, wrap, sash, tail band, reed cape, bone and shell light armour, tail stockings: hard (weight painting, tail and head fit). Cheaper: re-texture vanilla clothes or use Sundries/HistBone.

## Step 4: ranking by player impact per unit of difficulty

1. NEXUS (SE): Shifts-Sand's Saxhleel Sundries 191593; Saxhleel Weapon pack 67137 and War Club 35555; Simple Straw Hats 89962. No modelling, largest breadth. Verify ArgonianRace in each ARMA first.
2. NEXUS (SE, small): the Argonian Warrior Armour Heart Stone shield and necklace (96624); Mihail 82282 mask; Giant Club Variety.
3. OWN, easy weapon swaps: crocodile-tooth club and maul, jade blades, Naga-Kur bone blades, gaff (rows A, first nine): the tribal camps' common issue.
4. OWN, easy-medium polearm swaps with scripted shafts: pike, spear, halberd, staff, rapier, whip, claws (rows A, last eight): these six types are the signature weapons of six tribes and currently all look like generic medieval weapons; the animation and record work is done by Animated Armoury and SkySA.
5. OWN, easy-medium: turtle-shell and reed shields.
6. NEXUS (2011 game, needs conversion): AmA Argonian Mercenary Armor with tail 27676, HistBone and Bonewood 99144, Argonian Raptor Feet 19283, Edhildil War Tails 28502, Gemling Queen Resources 54483 (jewellery), Ghosu bone shield and tribal staff 43293. Cheap if conversion is acceptable; ranked here because the file conversion is a new step.
7. OWN, medium: rigid head ornaments and necklaces (crest, horn caps, frill clips, tooth and jasper necklaces, shell rings).
8. OWN, textures only: marsh-dye retexture of the 6 vanilla clothes.
9. HARD: skinned outfits, only if 1 and 6 do not deliver.

Options: do nothing (identical town watches); do least = 1 and 2; do more = 3 to 5; do most = 6 to 9.

## Recommendations (each with its evidence)

- File arcane-mage-armor and dx-necromancer-robes items: rows exist (`mods/dependencies.json`), reward-gear.md lists them, `item` has none.
- Fix the gold, pearl and rust overlays: they name light shell or light bone-plate armour that does not exist (ladder table, `items.md`).
- The scale guard set's cuirass `BMArgBody` has no ground model; two of its three pieces are other sets' meshes (`bases.jsonl`).
- Replace the vanilla-relabelled T1 "bog iron" weapons when a Black Marsh iron model arrives.
- Before adopting any clothing mod, read its ARMA race lists (my reader: `/tmp/claude-1000/-home-ubuntu-skyrim-argonia/044f6198-1702-4213-9f22-0f888669a49a/scratchpad/p.py`).
- Add the 2011-game search as a standing step in the Nexus method: it found the only Argonian armour with a tail slot, the Argonian-specific footwear and the clearest permission lines.

Covered: docs/design/items.md, newworld/sources/stock/{kits,materials,scale,regions}.json, story/design/quests/reward-gear.md, material-culture.md, province-vibe.md, world.sqlite (item, person_item, guard_issue), out/places/catalogue, mods/dependencies.json, 64 Nexus terms in both game domains, about 45 mod descriptions. Skipped: the per-line quest outfits (reward-gear.md used instead), UESP pages (403), meshes and screenshots, 21 unresolved Animated Armoury models, description hits beyond the top of each term (noisy).
