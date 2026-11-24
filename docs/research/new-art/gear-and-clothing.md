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

## Step 2: Nexus candidates (not already rows in `mods/dependencies.json`; checked against its 193 rows)

Search note: `tooling/nexus_search.py` does name-wildcard only (asterisks return nothing); I used about 120 terms. Nothing found for:
loincloth Argonian, sarong, grass skirt, Aztec, Maya, Polynesian, Inca, tiki, atlatl, javelin, harpoon, stone axe, jade weapons,
turtle shell, reed, pearl armour. Most "tribal/rustic" clothing is Nordic/Reachman or CBBE glamour wear.

| Candidate | Nexus id | Author, endorsements | Fills | Worry |
|---|---|---|---|---|
| Shifts-Sand's Saxhleel Sundries (DEMO) | 191593 | YourFellowFern, 6 | ESO Argonian pieces: Nisswo robe, shell armour, Argonian Warrior armour, Tribalwear (m), Tribalwrap (f), Voskrona set, Argonian robe set, Deathmask, Shadowscale set: the single best match to the clothing/shell/robe gap | ESO rips ("I do not own any rights"); demo, weight-paint issues, dark armour; forge-recipe only; unverified Argonian-race support |
| Argonian (Saxhleel) Weapon pack | 67137 | MetalMonsterFNV, 340 | battleaxe, sword, dagger, greatsword, mace, waraxe, warhammer; ebony-level -> relabel T4/T5 | ebony recipe (ours replaces); no bow |
| Saxhleel War Club | 35555 | Muoviori, 187 | club, acts as warhammer/greatsword-speed | modder's resource? unverified |
| Simple Straw Hats | 89962 | GolinskiPRH, 516 | straw hats worn by man/woman/cat/lizard, circlet slot (head-safe); credit required; "modder's resource" | needs CC basket content |
| Argonian/Saxhleel clothing gap (mod 7260 Tail Binder, 85894 tail slot cloaks, 44986 Lizards Don't Wear Shoes) | 7260, 85894, 44986 | various | tail/footwear fixes only | utilities |
| I'noh-Ssu-Keh War Mask | 82282 | Mihail, 231 | rigid tribal war mask (helmet slot) | check Argonian ARMA |
| Giant Club Variety | 104029 | Mihail, 1,230 | crude club meshes (mace / warhammer, giant scale) | size; take meshes |
| Ultimate Voodoo and Witch Doctor Arsenal (port) | 181332 | SolidSnonk, 7 | modular witch-doctor armour, masks, mojos and charms | needs SKSE perk system; take items only |
| Ancient Bone Armor | 119440 | Aokili, 6,141 | bones and leather modular set (CBBE/3BA/UBE/BHUNP only): light bone plate that the stock lacks | female-body fit; "warmaiden" look |
| Tribal Clothes | 120203 | contentcat, 6,169 | tribal cloth set, 4 colours, CBBE/BHUNP + SMP | body fit; physics |
| Riverfolk Clothes | 135136 | Pulcharm, 6,563 | "Bjoulsae tribes" themed set | needs FSMP; body fit |
| Common Clothing Expansion | 134088 | Horn, 9,414 | 4 lore-friendly commoner outfits + hood, vanilla-like | Nordic-ish; body fit |
| Kreiste's Fisher Outfit | 59836 | Kreiste, 303 | a fisher outfit (our fisher kit has none) | body fit |
| Slave Rags | 68917 | (SE port), 305 | ragged slave/bonded-labour outfit | topless variants; body fit |
| Bosmer WoodElf LEAF Armor | 7869 | Jameza007, 634 | leaf camouflage armours (reed/leaf feel) | LE-era (2017) |
| Valenwood Ranger Armor Mashup | 126887 | W00DENKNIGHT, 7,644 | greenwood light armour (we already hold the Bosmer pack 5597) | overlaps |
| Racc's Headdress / Hunter's Headdress | 147060 / 50429 | raccoondance 255 / Caged_Disorder 41 | rigid headdress pieces (Forsworn-style) | Reach/Nordic look |
| Rustic Clothing / Rustic Amulets | 4703 / 35485 | Gamwich 79,228 / 12,135 | retextures of ALL vanilla clothes/amulets (lifts the vanilla pool, does not add models) | global retexture, would hit Skyrim clothes everywhere (acceptable?) |
| Immersive Jewelry / Amulets of Skyrim / Rustic amulets | 5336 / 487 / 35485 | various, 12-16k | many jewellery models (generic) | not Black Marsh |
| Easthold Totemic Set | 100401 | Pulcharm, 6,943 | totem/tribal armour (Nordic Easthold) | Nordic; rejected by 0006 |

Big authors checked: Mihail (clothes/weapons: Rustic Weapons Pack 27475 translation only; Giant Club Variety, Netch/Dres/Temple
already held), Billyro (generic swords), NordWarUA (Nordic/Imperial replacers), zzjay (glamour), 4thUnknown (Dark Brotherhood,
Mythic Dawn: DB already via 57539), Vicn (creatures), Stroti/Tamira (architecture), Elianora (houses). Oaristys, Blary, Lolicept,
LupusHegemonia: no usable hits by name. ESO ports other than Shifts-Sand: 11729 is a quest/lore mod, not gear.
Not verifiable: any permission text beyond the API's first lines; Argonian race support; real appearance (no screenshots read).

## Step 3: what remains for our own models

Owner steer applied: simplest first = a NEW MODEL that is held and swung exactly like an existing type, so every existing
animation, record template and perk reuse applies ("acts as ..."). Where Nexus adopts leave a gap in the lore's list:

### A. Plain swaps (rigid, static, no skinning: new nif + copy a vanilla record)

| Object | Acts as | Where seen | How often | Size | Difficulty |
|---|---|---|---|---|---|
| Jade / jadeflint sword | sword | priests, chiefs, shrine/ruin rewards (T2-T3) | rare, but a lore stand-out; unique rewards | 0.9 m | easy (single static blade, no moving parts; the game keeps every animation) |
| Jade dagger / ritual knife | dagger | Hist priests, Sisei-Xul, Sul-Xan | uncommon | 0.35 m | easy |
| Jade or flint war axe | waraxe | hunters, Naga | uncommon | 0.7 m | easy |
| Crocodile-tooth club / maul | mace (one-handed) and warhammer (two-handed) | tribal camps, Naga, fisher guard | common (tribal hide-and-flint issue) | 0.8 to 1.2 m | easy |
| Shark/fishbone-toothed sword (saw edge, "machete and saw" Xit-Xaht) | sword | Xit-Xaht, Spray-Folk, harbour | uncommon | 0.9 m | easy |
| Naga-Kur bone-and-frill sword and dagger ("weapons from their own dead") | sword, dagger | Naga-Kur camps and raiders | uncommon; lore lists them in "Still no model" | 0.9 / 0.35 m | easy |
| Skull-topped Hist staff (Xit-Xaht) | quarterstaff (AA type, swings as battleaxe) | Hist-branch priests, grave-singers | uncommon | 1.8 m | easy-medium: long thin mesh; Tripo struggles with thin staffs |
| Eel-gaff / fishing hook | dagger or sword (1H) | fishers, Eelskins | common | 0.8 m | easy |
| Reed-bundle or obsidian-edged heavy club | battleaxe / warhammer | tribal | common | 1 m | easy |
| Wamasu-tooth halberd head, harpoons | halberd / greatsword | boats | uncommon | 2 m | easy-medium: long, thin |
| Turtle-shell round shield, reed-wicker shield | shield (copy a vanilla shield record; rigid; must match the shield attach node and a convention for bash/block) | tribal, harbour, guard (T2) | common | 0.6 m | easy-medium: static, but the nif needs correct pivot/collision/node names (copy a vanilla shield nif's structure) |
| Boss-and-bone round shield | shield | guards | common | 0.6 m | easy-medium |
| Feather crest / head-fan | helmet-slot or circlet-slot, rigid attach to the head | elders, naheesh, priests: every settlement | very common close view | 0.3 m | medium: rigid, but must be fitted to the Argonian head and needs its own ARMA for ArgonianRace |
| Copper horn caps, silver frill clips | circlet/hair slot, rigid, left/right pair | the fashionable lukiul, Gideon youths | common | 0.1 m | medium (Argonian ARMA; symmetrical pairs) |
| Shell/jade/blue-jasper death mask or mask | helmet slot, rigid | Sul-Xan, Hist-priests (stock holds funerary 1 model, Moon Monk, Mihail 82282) | uncommon | 0.25 m | easy-medium (rigid, must clear snout) |
| Crocodile-tooth / jasper / pearl necklace | amulet slot (copy a vanilla amulet record, a skinned small mesh) | everyone with an adult trial (lore) | high: replaces 32 vanilla silver rings and amulets | 0.2 m | medium: the amulet nif is skinned to spine bones, so the model needs 1-2 bone weights; Blender job |
| Rings/bracelets of shell, bone, jade | ring (rigid, finger bone) | everyone | high | 0.03 m | easy |

### B. NOT plain swaps (state which)

- Bows (feathered reed bow, bone bow): rigged string/limb animation; vanilla bow skeleton nodes needed. Hard-ish; existing bows suffice (bamboo, chitin, ivory, Argonian, Arrowsong).
- Crossbows / blowgun: a crossbow uses Dawnguard's crossbow animations and loads a bolt; our blowgun (Ruddy88 12910) is the template (mesh swap only: acts as crossbow; easy mesh, but not a free record).
- Spears, tridents, harpoons, pikes: no spear animation set is loaded. Our approach: Heavy Armory (6308), HTBM (Cipactli), New Armory Argonian and Seagrave type them as greatsword (2H spear = greatsword swing) or sword (short spear = 1H sword): `items.md` table "Spear, trident, harpoon -> greatsword; Shortspear -> sword; Pike -> greatsword; Halberd -> battleaxe; Quarterstaff -> battleaxe". A new spear is therefore "acts as greatsword" and is easy; it just has no thrust animation. A real spear set would need a Nexus animation mod (Spear of Skyrim 89785, True Spear Combat 10483): not our plan.
- Thrown weapons, atlatl, nets, throwing knives: need new animation or script: outside "act as".
- Claw/whip/rapier: already via SkySA packs keyed on Animated Armoury keywords; a new model would copy those records (acts as dagger/mace/sword) and is easy as a mesh, but the six AA types have the animation only on AA's keywords, so a new model must reuse AA's record, not vanilla.

### C. Skinned outfits and wearables (harder; say so)

| Object | Kind | Difficulty | Reason |
|---|---|---|---|
| Loincloth / wrap / sash + tail band outfits | skinned torso+legs, tail | hard | weight paint, tail bone, body-fit; a poor texture wrapped round a skinned body is the hardest case; use Shifts-Sand or retexture |
| Commoner cloth tunics, robes in marsh dyes | skinned | hard to model; EASY to retexture vanilla meshes (UVs exist) | textures only is the cheapest way |
| Reed rain-cape / grass skirt | skinned or cloak-slot | hard | physics-free cape slot is easier than a skirt |
| Shell/scale pauldrons, bracers, leg wraps | skinned | medium-hard | small pieces, simple weights if copied from a vanilla pauldron nif |
| Tail bands with bells; tail stockings | skinned to tail bones | medium-hard | tail chain bones differ; mod 85894's slot handling needed |
| Bone/shell armour sets (light) | skinned | hard | whole-set; use 119440/191593 first |

## Step 4: ranking by player impact per unit of difficulty

1. NEXUS: Shifts-Sand's Saxhleel Sundries 191593 (tribal wear/wrap, shell, robes, deathmask): largest breadth for no modelling. Verify race support first.
2. NEXUS: Saxhleel Weapon pack 67137 + War Club 35555 + Simple Straw Hats 89962 (lizard-ready head item).
3. OWN, easy: crocodile-tooth/bone clubs (mace, warhammer), jade blades (sword, dagger, axe), Naga-Kur bone-and-frill blades, gaff: all "acts as" a vanilla type, rigid, T1-T3, the tribal camps' common issue.
4. OWN, easy-medium: turtle-shell shield and reed-wicker shield: they fill the ladder's one "no model anywhere" shield slot; seen on every guard.
5. OWN, medium: rigid head ornaments: feather crest, horn caps, frill clips, masks (replace vanilla leather helmets and hoods on tribal NPCs): highest Black Marsh feel per object; needs an ArgonianRace ARMA.
6. OWN, medium: crocodile-tooth/jasper necklaces and shell/bone/jade rings: one record family replaces the 32 vanilla silver rings worn in the six stocked places.
7. OWN, medium (textures only): marsh-dye retextures of vanilla farm/monk clothes (6 models) so the commoner pool is not Nordic-looking; Argonian tribal tinting by culture (18) is where "tint, not dress" differences could be fixed cheapest.
8. HARD: skinned loincloth/sash/tail outfits and bone/shell light armour: only if 1 does not deliver.

Do-nothing impact: Argonian towns look identical; villages identical; six tribes' signature weapons look like medieval pikes/rapiers.
Do-least: items 1 + 2 (no model). Do-more: + 3, 4. Do-most: + 5, 6, 7.

## Recommendations (each with its evidence)

- File arcane-mage-armor and dx-necromancer-robes items: the rows exist (`mods/dependencies.json`), reward-gear.md lists them, `item` has none.
- Fix the tribe table: gold, pearl, rust name light shell/bone-plate armour that does not exist (ladder table rows, `items.md`); either add the armour (#191593 shell armour) or change the overlay.
- The scale guard set's cuirass `BMArgBody` has no ground model and two of its three pieces are other sets' meshes (`bases`): decide whether that issue should be replaced.
- Replace the vanilla-relabelled T1 "bog iron" weapons if any Black Marsh iron/steel model arrives: they are the commonest weapons in the province.
- Cheap check before adopting any clothing mod: read its ARMA race list (my reader: `/tmp/claude-1000/-home-ubuntu-skyrim-argonia/044f6198-1702-4213-9f22-0f888669a49a/scratchpad/p.py`).

Covered: docs/design/items.md, newworld/sources/stock/{kits,materials,scale,regions}.json, story/design/quests/reward-gear.md, material-culture.md, province-vibe.md, world.sqlite (item, person_item, guard_issue), out/places/catalogue, mods/dependencies.json, ~120 Nexus queries and ~25 mod descriptions. Skipped: item_material.json/unique.json line by line (counts came from sqlite); story/design/quests/lines per-line outfits (reward-gear.md used); UESP pages (403); mesh/screenshots (not read); 21 Animated Armoury records' models (unresolved).
