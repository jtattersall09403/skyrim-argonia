# New art, lane: every region, culture and faction against the lore (owner call #93, research only)

> **Correction by the lead, 2026-11-24.** This report read `place_source` rank 1, which is each place's SECOND
> choice of source (ranks run 0 to 3; rank 0 is the first choice). At rank 0 the 258 places draw on 246 distinct
> source places and the most-used one serves 3 places, so the "62 sources / Ree-An-Wo 62 places / five sources
> carry half" finding, the "same place in assets" rows that rest on it (Hutan-Tzel, Agaceph, Naka-Desh,
> Root-Folk, the six regions at 73 to 82%) and the "re-match the 62 places" recommendation do not hold. What
> does hold at rank 0 is in places-and-pieces.md: 110 places take a vanilla Skyrim source and 77 an Argonian-kit
> source. The signature-object list, the Nexus search and the own-model list do not depend on the rank.


Method: BRIEF-common.md steps 1 to 4. Counts are from `newworld/out/world.sqlite` (queried 2026-11-24), mesh lists from
`/home/ubuntu/games/skyrimse/Data/argonia-mesh-lists/*.txt` and `story/data/sources/assets/registry-{kotm,bmv,vanilla}.jsonl`,
Nexus from `tooling/nexus_search.py`, UESP through its MediaWiki API (WebFetch is 403 on uesp.net; the API answers).

## 0. Live docs that already cover this

- `docs/design/identity.md` (+ `newworld/sources/identity/regions.json`): each region's light, sight, weather, sound, ground colour, water,
  one small signature and one creature. CONFIRMED and measured by `identity.py`: neighbours differ on 3 of 6 *atmosphere* axes.
  SUPERSEDED for our question: it never measures what buildings, props, banners or dress a region shows. It is atmosphere identity only.
- `docs/design/dressing.md` + `newworld/sources/dressing/kinds.json`: the small signature things are fungi, bone piles, skulls, fireflies,
  dragonflies, flesh flies, moths, lanterns. No tribe object, no totem, no grave-stake, no banner, no shrine.
- `story/lore/topics/material-culture.md` (build/craft/dress/music/play), `hist-and-sap.md`, `hist-placement.md`, `sithis-nisswo-shadowscales.md`,
  `tribes.md`, `lost-peoples.md`, `story/design/province-vibe.md` §4: the lore is rich in objects (totems, grave-stakes, chimes, xeech'kis, vossa-satl,
  sap, uxith). CONFIRMED against UESP below; the lore wants far more visible objects than the dressing rules place.
- The one doc to edit if the owner relaxes the art rule and the plan proceeds: `docs/design/dressing.md` (add a "tribe and faction marks" kind table);
  `identity.md` should gain an "assets" row per region only after that.

## 1. Findings first

1. **The asset pool is thinnest in sharing, not in kinds of prop.** Of 258 places, the matcher's first-choice source place is one of only 62
   distinct ones (`place_source` rank 1). Five source places carry 50% of all places (129 of 258): KotM "Ree-An-Wo" 62, KotM "Seekhat Yol"
   (Bright-Throat village) 26, KotM "Teeth of Sithis" 14, KotM "near Loreisian" camp cluster 14, vanilla "Nightcaller Temple" 13. Ree-An-Wo alone is 24%.
   Caveat (measured): drafts deviate from rank 1 in 4 of the 6 drafted outposts/camps (`newworld/places/*/place.json` source_id vs rank 1), so this is the
   matcher's plan, not the final look; but only 13 of 258 places are drafted, so it is the best available measure.
2. **The tribes the lore calls different are, in assets, one place.** Rank-1 source = Ree-An-Wo for: Hutan-Tzel (magenta, 4/4 places, 1 source),
   Agaceph (lime, 4/4, 1 source), Naka-Desh (indigo, 5/5, 1 source), Three Waters (plum, 5 of 6), Sedge-Wardens (jade, 4 of 6), Root-Folk (forest-green,
   17 of 19), Mine-Burners (5 of 7), Chime-Keepers (5 of 9). Seekhat Yol is the single look for 26 villages of 5 cultures
   (olive 7, rust 5, rose 5, umber 3, pale-green 3). Nothing but a tint and a name tells Hutan-Tzel from Agaceph from Naka-Desh.
3. **The pool already holds more signature props than the plan uses**, mostly in King of the Murkmire (KotM), HTBM Curse of Cipactli and
   Mud Mother Grove (mesh lists): Xanmeer totem01-03 and skeletontotem01-04, `argoniantotem01`, `argonianbonechime01/02`, `drum01`, `sithisshrine`,
   `paintedurn01`, 8 `xanmeerbanner*` plus 4 `xanlongbanner*`, `saxhleeltapestry01/02`, `wallhanging01-03`, `hangingfeathers01-03`, `scaletent01-03`,
   `scalefence01-05`, `snakefence01-03`, `vossasatl01-03`, `doll_turtle`, `nisswocoin`, `fishtoken`, `ghosttoken`, `serpentstatue_feathered`, `argonianhead01-03`,
   `skullstack01`, `runicstone`, `roadsign1-5`, windchimes. BMV holds Dunmer house banners (`bannerdres`, `bannerhlaalu`, `bannerindoril`, `bannerredoran`,
   `bannertelvanni`) and lcr_totem1-6. Vanilla holds 74 banner meshes, Hagraven poles and fences (the nearest thing to a grave-stake).
   So the gap is *variety per tribe, emblems on the banners, and the lore objects with no mesh at all* (section 4), not "no props".
4. **Objects with no mesh anywhere in the pool** (searched all mesh lists and the 12 016 + 2 100 + 15 050-row registries): grave-stake (xul-vaat), uxith
   with Argonian eggs (Argonian "eggs" are vanilla dragon eggs: `argonianeggs/dragoneggs1-5`), sap tap or sap jar, Hist-cultivation stele, Vos-Toh
   tablets, Argonian ritual drum beyond `drum01`, Teeba-Enoo court/ball, fetishes (Veeskhleel sinew), Argonian boundary posts, Company standard,
   pirate flag, any faction hideout sign. Nexus has none of them either (section 3).
5. **Three lore tribes of ours have no place at all**: Naga-Kur, Dead-Water, Black-Tongue, Root-Whisper, Miredancer, Tum-Taleel, Veeskhleel, Bright-Throat,
   Teeba-playing Hapsleet appear in 0 place notes; Murkmire canon is folded into the Rose/Lilmoth coast. Paatru (13 notes) and Sarpa (14) are mentioned only
   as "inland tribes". The Naga-Kur are shown by gear (held `naga-kur-armor`, HTBM Naga armour dirs), not by any place or prop.
6. **Foreign enclaves have flags we hold but unlabelled**: Dunmer (34 place notes), Imperial/Legion/Warden (69), pirates (35), Topal Bay Company (9),
   Khajiit (22), Bosmer (6). Dunmer banners (BMV) and Imperial banners (HTBM `imperialbanner01-04`) exist; Company, pirate and Brethren marks do not.
7. **Nordic leakage is still real**: `newworld/places/nordic_review.jsonl` flags 17 of 41 reviewed BMV bases as Nordic (High Hrothgar fire pit, Nordic ruin
   doors); `skyrim.nightcallertemplelocation` (Nightcaller Temple, Nordic stone) is the rank-1 source of 13 places (11 imperial-ruin, 2 kothringi-ruin). Cited, not re-measured here.

## 2. Region table (24 regions)

Columns: places / distinct rank-1 sources / share on the top-5 sources. D = distinctiveness from neighbours *in assets*, C = lore/vibe consistency (0-3).
"Lore looks like" quotes the region's `look` note (all EXTRAPOLATED except Topal Bay) plus `region_profile.signature`.

| Region | n / src / top5 | Lore looks like | We hold to show it | D | C | Missing signature things |
|---|---|---|---|---|---|---|
| Althii Archipelago | 22 / 13 / 45% | paddies, stilt villages, brick ruins in vines; saltrice dishes | KotM + Tropical Skyrim winners; 5 Lilmothiit ruins; rose culture 11 | 2 | 2 | rice-paddy dike/sluice props, estate gate, tenant vs garrison signage |
| Aphon Isle | 4 / 4 / 25% | grey hills, white-washed lookout, smugglers' cave, contraband | vanilla Tropical winners, Wyrmstooth | 2 | 2 | Brethren sign, moon-sugar crates (pirates.md:238) |
| Arnesian Jungle | 10 / 7 / 40% | terraced stone towns, hardwoods, Velothi ruins under vines | KotM, Baan Malur, Xanmeer tileset, glowing fungi | 2 | 2 | Stone-Sleeper carved terrace posts; Tsonac "asleep Hist" shrine |
| Aunike Ridge | 4 / 3 / 50% | rock outcrops, stone-footed huts, windchimes, watchfires | KotM + Nyhus; tin chimes in sheet only | 1 | 2 | tin chimes (held `tamwindchime01` is one generic) , penned-lizard pens |
| Banujha Basin | 15 / 8 / 73% | flooded channels, scorched timber, tiered stilt halls | KotM stockades (45 pieces) + bmv; burn-scar bones | 2 | 2 | scorched/burnt retexture of stockade set; Mine-Burner trophies; Soulrest-bound mine signs |
| Barsaebica | 14 / 8 / 43% | white Ayleid stone in reed beds, stilt huts, weirs | cc-ayleid-resources, Ayleid ruins, reed weirs, bone piles | 3 | 3 | reed-warden charm (Ayleid oddment), weir fish-traps (check KotM `fishracksmall`) |
| Benthic Yobesh | 10 / 6 / 50% | blue-green water, coral, spires, black trench | Depths of Skyrim, Sirenroot, underwater rivers | 3 | 3 | none new; coral-crusted relic is a retexture |
| Blackwood | 7 / 6 / 43% | flooded hills, cairn-fields | KotM blackwood set (111 pieces), cairn skulls | 2 | 2 | cairn/stake hybrid markers; Sul-Xan jade mask idols (4 notes) |
| Cape Percar | 17 / 11 / 35% | red-gum hills, burn-scars, grey Imperial ruins, stilt coast | Tropical winners + KotM | 2 | 2 | Khajiit coaster stalls, Imperial-descended crockery |
| Chixathe Mesa | 16 / 8 / 44% | pale cliffs, chalk, stone cuts, dry stores | Baan Malur, mine kits, cairn skulls | 2 | 2 | chalk-white retexture of stone cuts, Agaceph book shelves |
| Hatandros Bight | 10 / 6 / 50% | grey mudflats, black Velothi headlands, sea fog | Baan Malur Velothi, Caves of Morrowind | 2 | 2 | salt-pan frames, smuggler landing marks |
| Kotherra Mangroves | 9 / 6 / 78% | black water, red mud, Imperial grey stone road | KotM + Tropical; red-clay pottery | 1 | 2 | Cyrodiilic road markers; Imperial household set (held vanilla only) |
| Lake Ulaish | 9 / 5 / 78% | pale lake, lantern posts, eel traps, stone-footed farms | KotM lanterns (`saxhleellantern01/02`) | 1 | 2 | eel traps, silt-islet lantern posts, Warden toll post at Gysilla |
| Murkwood | 13 / 5 / 77% | dark wood of huge roots, hanging moss, Hist grove | Sleeping Hist Tree, KotM Hist roots (hist_root01-11, glands), hanging lanterns | 3 | 3 | tapping and sap jars, tree-minder platform, grave-stakes |
| Nha-Enasa | 11 / 7 / 82% | reed banks, stilt platforms, grey ruin stones | KotM, Kothringi ruins | 1 | 2 | gar spears racks, salt bag stacks, caravan stalls |
| Nushara Bayou | 11 / 7 / 55% | brown sheets of water, raft-houses, herons | KotM, glowing fungi; rafts none | 2 | 2 | **raft-houses** (no raft/pontoon mesh, only `argonianplatform`), shell/rice racks |
| Okuwun Rahei | 22 / 13 / 36% | red-brown clay mounds, bright reed thatch, kilns, Seafalls | KotM, Velothi ruins; mud huts | 2 | 2 | **kiln, painted clay ware, mound terrace walls** (KotM has `bigpot`, `paintedurn01` only) |
| Padomaic Ocean | 3 / 2 / 0% | grey-green swell, drowned timbers | Baan Malur wrecks, Sailable Ship | 2 | 3 | wreck goods of three eras |
| Sea of Mists | 2 / 2 / 0% | mist banks, islets | same | 1 | 3 | none |
| Skeith Isle | 5 / 5 / 0% | grey crags, keep, Grey Tooth spire | Wyrmstooth, Caves of Morrowind, Ashlander camp | 3 | 3 | pirate hoard dressing, Brethren flag |
| Topal Bay | 2 / 2 / 0% | grey-green bay, sailors' gear | vanilla Tropical, Baan Malur | 1 | 3 | Company standard |
| Tulmek Washes | 24 / 13 / 46% | brown water, stilt towns, boardwalks, drowned domes | KotM Lilmoth, boardwalk kits, Lilmothiit ruins | 2 | 3 | Blackrose prison look (**one prison, drafted from a Skyrim keep?**), toll tokens |
| Ultherus Swamp | 4 / 3 / 75% | cattail maze, stilt towns hung with metal chimes | KotM | 1 | 2 | metal chimes; dragon's-tongue drying racks |
| Valley of Storms | 14 / 10 / 57% | stone-footed farms, causeways, grey Imperial forts | KotM + Skyrim farms, Nyhus forts | 2 | 2 | Dunmer minority marks, causeway markers |

Honest sameness (by shared sources and no prop of its own): **Nha-Enasa, Lake Ulaish, Kotherra Mangroves, Ultherus Swamp, Murkwood and Banujha Basin
are, in rank-1 source, largely the same Ree-An-Wo / Seekhat Yol camp** (top-5 share 73 to 82%); they differ only by terrain, atmosphere and ground
colour (`identity.md`). Region D scores of 1 are exactly these. Open water regions (Padomaic, Sea of Mists, Topal) are tiny (7 places) and differ by wrecks.

## 3. Culture table (18 cultures; `culture` rows in the sqlite, `tribes.md`, `material-culture.md`)

| Culture (tint) | places / src | Lore looks like | We hold | D | C | Missing |
|---|---|---|---|---|---|---|
| Warden Marches (crimson-red) | 21 / 12 | stone forts, keeps, posts held by Argonians; Warden militia | vanilla Imperial forts, Nyhus, HTBM legion banners and armour, ancient-imperial-armor | 2 | 1 | **Argonian over-Imperial mark** (Warden standard over Legion-style fort); Nordic residue in fort stone (nightcaller 13) |
| Root-Folk of Helstrom (forest-green) | 19 / 3 | stilts, root hollows, nothing new in stone, Hist grove | Sleeping Hist Tree, hist_root set, KotM huts | 2 | 3 | sap jars, tree-minder tools, grave-stakes |
| Archon Harbour Folk (gold) | 1 / 1 | amphibious port, underwater games, guar that breathe underwater | Lilmoth KotM, Ferries | 1 | 2 | jump-stick, jaw-beetle game props (material-culture: Archon games) |
| Naka-Desh (indigo) | 5 / 1 | wide-faced river people, osheeja gars, chimes in memory of Kothringi | Ree-An-Wo only | 0 | 2 | bridled-gar fishing rafts, chimes |
| Sedge-Wardens (jade) | 6 / 3 | reed weirs and mats, Hist pool market | KotM Alten Meerhleel look | 1 | 3 | reed mats, weir traps |
| Agaceph (lime) | 4 / 1 | rainbow-scaled, razor-thin tail rafts, looted books | Ree-An-Wo only | 0 | 2 | **tail-driven one-person raft**, book shelves, rainbow dye |
| Hutan-Tzel (magenta) | 4 / 1 | totems carved with runes only they read | Ree-An-Wo only; HTBM totem01-03 exist but unplaced by culture | 1 | 2 | **rune-carved totem set (the tribe's one canon object)**, naheesh feather staff |
| Island of Blackrose (olive) | 10 / 4 | island city, prison ruin, stilt villages | KotM Seekhat Yol, vanilla keep | 1 | 2 | prison gate, ledger room dressing |
| Chime-Keepers (oxblood) | 9 / 4 | Kothringi-named towns: tin and copper chimes at every eave, metal-woven rope, stone footings, tidal canoe | `argonianbonechime`, windchimehavok (HTBM), `tamwindchime01` | 1 | 3 | **tin/copper chime strings in quantity and metal rope**, Kothringi tidal canoe (UESP Online:Kothringi Tidal Canoe; only boats ours: `shiprowboat`) |
| Gideon Frontier (pale-green) | 8 / 5 | most Cyrodiilic; courthouse, records, red-clay pottery | KotM, vanilla Imperial, Skyrim farms | 2 | 3 | courthouse notice boards, Company/Imperial merchants' signs |
| Spray-Folk of Seafalls (pearl) | 5 / 4 | cliff-and-surf village, no Hist reach | Keeba Hollow, Wyrmstooth lighthouse | 2 | 2 | surf-shell dress, falls-side racks |
| Three Waters (plum) | 6 / 2 | reed houses on rafts and stilts that move | KotM huts, `argonianplatform` | 1 | 2 | **raft-houses, pontoons** (none held) |
| Lilmoth and Murkmire Coast (rose) | 16 / 10 | rebuilt stilt town over the mass grave, merchant council, drowned Imperial quarter | KotM Lilmoth (9 uses), Baan Malur | 2 | 3 | grave-stake field (the lore's "carved grave-stakes and memorials", province-vibe §2); drowned-quarter silt dressing |
| Clay-Mound People (rust) | 12 / 6 | red clay mounds, kilns, pottery, dye | KotM, `paintedurn01` | 1 | 2 | **kiln, clay mound slopes, painted ware** |
| Stone-Sleepers (sky-blue) | 5 / 3 | jungle upland people who still build in stone over Velothi/Ayleid | Xanmeer tileset, Velothi kits | 2 | 3 | dream-reader tree-minder seat |
| Mine-Burners (steel-blue) | 7 / 3 | fortified towns, watch posts, scorched trophies, salvaged iron | KotM stockade (45), mine kits | 2 | 2 | scorched trophies, burnt stockade variants |
| Shadowfen Border / Stormhold (stone-grey) | 11 / 4 | stone causeways, raised farms, Vicecanons, oldest Dunmer minority | KotM, Skyrim farms, Dunmer packs (solstheim-dunmer-additions) | 2 | 2 | Vicecanon office signage, Dunmer-Argonian mixed marks |
| Soulrest/Topal Coast (umber) | 16 / 11 | ex-capital, mixed people, Khajiit coasters, Bosmer seafarers | Tropical winners, Khajiit packs, Bosmer packs | 2 | 3 | Soulrest merchant council seal |

Also in the lore but with no culture row or place: Naga-Kur, Dead-Water, Black-Tongue, Root-Whisper, Miredancer, Tum-Taleel, Veeskhleel, Sul-Xan, Xit-Xaht,
Kothringi (8 ruins only), Lilmothiit (9 ruins), Barsaebic Ayleids (7 ruins). Their ruin looks come from Nightcaller Temple (Nordic stone) and Teeth of Sithis (KotM).

## 4. Faction and story line table (9 `story_line` rows; sign cited from the line file)

| Line | Lore sign / look | Places | We hold | D | C | Missing |
|---|---|---|---|---|---|---|
| Main quest / Xeech-Leel and Toh-Reel-Ka | forts with sap jars marked "Jal-Veesa's knot" (main-plot.md:408); sap cellars | Fort Chalkmoth + forts (8 fort, 3 keep) | Stormhold Warrior armour, Sign of Cipactli | 1 | 2 | knot mark on jar, sap-cellar dressing |
| Chainbreakers | Twin Lamps iron lantern sign in door/window (chainbreakers-newworld.md:37, loading-facts:724) | safe houses (Marque Landing noted) | vanilla iron lantern | 0 | 3 | **sign** is a hanging lantern pair, a texture or a recoloured vanilla lantern |
| House Cardruhn | spider-in-circle carved on cellar door (sisei-xul.md:304, house-cardruhn.md:436) | Thorn, Ovezza | dx-necromancer robes, Telvanni robes | 0 | 3 | carved door texture, silver token (Skyrim amulet mesh) |
| Lampbearers | detectives; a hook and eye cut as owner's sign (lamps.md:70) | Pusbottom, Tarak Shan | KotM coat | 0 | 2 | chalk mark decal |
| Sisei-Xul | spider-circle token | Ovezza | arcane-mage-armor | 0 | 2 | same spider sign |
| Brethren (pirates) | Brethren sign at the stair foot (merchants.md:238/311, pirates.md) | Aphon Signal Tower, Bramman's Watch, Kelp-Mouth Cave, Marque Landing, Rainbreaker Keep, Skeith (6 notes) | pirate cutlasses, Pirate Armor | 1 | 2 | **flag, black sail, lookout banner** (Nexus Flags Resource 56152 has Jolly Rogers) |
| Topal Bay Company | East Empire armour | Archon, Arorha, Gideon, Bramman's Watch, Coldbrine Mine (11 notes) | east-empire-company-armor, imperial-guard-centurion | 1 | 2 | **Company standard/sign** |
| Eelskins (thieves) | hook and eye; sewer hall under Pusbottom | Lilmoth sewers | KotM Lilmoth sewer hideout | 1 | 3 | none beyond sign |
| Shadowscales | Shadowscales' sign on ruin (lamps.md:521) | Archon, Lilmoth (2 notes) | dark brotherhood, serpent dagger | 1 | 3 | sign on xanmeer wall (carved texture) |

Honest reading: all nine factions are separated by *gear and dialogue*, none by place dressing; no faction sign exists as a mesh or texture yet.

## 5. Signature objects: the cross-cutting list the owner asked for

Counts are place counts from the sqlite: "Argonian living" = village 29 + hamlet 24 + outpost 41 + tribal-camp 14 + town 10 + city 11 + abandoned-village 8 = **137**
(`place` by place_kind); "mentions" = place notes (people/present/faith/look/overview/economy) matching the word, an upper bound.

| Object | Marks | Uses (places) | Lore | Held? |
|---|---|---|---|---|
| Grave-stake (xul-vaat) carved biography posts; ESO has Large Fearsome/Glyphed/Serpent/Skull/Twinned and Small Glyphed | all Argonian communities; Rose most | 137 living + Rose (16) as a field; 17 notes name stakes | sithis-nisswo-shadowscales.md:123-129,182 "single best environmental storytelling canon gives us"; state:749 | NO (Hagraven poles are the proxy) |
| Tribe totems: wood, mud, plumage, crocodile skulls; Hutan-Tzel runes | tribes, camps | 14 tribal camps + 4 Hutan-Tzel + 14 notes mention | material-culture.md "Totems"; tribes.md:106; UESP Murkmire Totem Post, Beacon, Stone Head, Wolf-Lizard; Argonian Totem of Skulls/Snake/Frilled Skull/Painted Skull | partial: HTBM totem01-03, skeletontotem01-04, `argoniantotem01`; one look each |
| Clan standards/banners (ESO: Banner Bright-Throat, Dead-Water, Root-Whisper; Half Hands, Frilled, Hanging) | 18 cultures | 137 | UESP Online:Murkmire/Argonian Furnishings | meshes held (`xanmeerbanner01-04`, `xanlongbanner`); 2D emblems absent |
| Hist-rite furniture: stele (Hist Cultivation, Hist Guardians), Vos-Toh tablets of Dance/Death/Song, offering bowls, censer | Hist trees | 123 mention the Hist | hist-and-sap.md; UESP list | NO (only `histbark`, `sithisshrine`) |
| Sithis idols/hearth shrines (Coiled, Figure, Looming, Rearing, Relief) | every settlement, Nisswo | 20 shrine-blessing gives, 110 faith notes | sithis-nisswo-shadowscales.md:112-130 | partial: `sithisshrine`, `serpentstatue*`, `snakestatue01` |
| Egg nests (uxith), clutch | villages with Hist | 50 mention eggs or uxith | hist-and-sap.md:74 | weak: vanilla dragon eggs retitled `argonianeggs` |
| Sap vessels and tapping gear | Hist-tending places, Jal-Veesa, Haj Uxith | 23 sap mentions | hist-and-sap.md:49 (rubber, jars); docs/design/dressing.md "Hist sap" | water only; `urn01/02`, `paintedurn01`; no taps/jars |
| Frog-instruments | Panther River, Stormhold | 2 mentions | material-culture.md Music | YES `vossasatl01-03` |
| Bone chimes and metal chimes | Chime-Keepers, Kothringi towns, Bright-Throat | 29 mentions, 9 oxblood places | lost-peoples.md:22,139; UESP Bonding Chimes | YES, few meshes |
| Fetishes (sinew) | Veeskhleel only | 0 places | Ghost People (UESP) | NO |
| Boundary markers: rune totems, cairns, skull posts | Hutan-Tzel, Blackwood cairn-fields | 14 tribal camps, 7 Blackwood | hist-placement.md:159 | cairn skulls (dressing kind) |
| Dunmer/Imperial/Company/pirate signage for enclaves | Stormhold, forts, Archon, Aphon | 34 + 69 + 9 + 35 mentions | foreign-powers.md | Dunmer banners (BMV) yes; Imperial yes; Company/pirate NO |
| Faction hideout dressing | 9 lines | ~10 hideout spots | story lines | none |

## 6. Step 2: Nexus (searched 100+ terms; 2026-11-24, `tooling/nexus_search.py`, rows already in `mods/dependencies.json` excluded)

**Result: Nexus has no Argonian totem, idol, grave-stake, banner-emblem or tribal-shrine pack beyond what we hold.** Searches totem, idol, tribal, fetish, effigy, tiki, voodoo,
Aztec, Mayan, witch, Sithis, Hist, grave marker, bone chime, drum, frog, Xanmeer, Murkmire, Saxhleel, Kothringi returned nothing usable (Easthold Totemic Set 100401
and Rally's Werewolf Totems 28882 are armour/Nordic; HFs Totem 164197 is an Odin totem).

Candidates worth carrying (asset-only):
- Flags Resource, Incaendo, 56152 (pirate Jolly Roger and national flags; textures for a flag mesh; texture-only route; permission "modder's resource").
- Murkmire Official Housing Pack, pancake0723, 194072 (24 endorsements, 141 KB): a KotM add-on; check for new props before relying.
- Shifts-Sand's Saxhleel Sundries, YourFellowFern, 191593 (DEMO, 6 end.): ESO Argonian clothing ports; dress for the tribes.
- Statue of Sithis, Mandragorasprouts, 73735 (3574 end., "do not upload elsewhere"): a Sithis statue; asset-only OK, size larger than a hut-prop.
- Totemic Tombstones re-mesh, Nyym, 157281 (329): a mesh for Tombstone01-03; Nordic totem look; weak.
- Sepolcri, WiZkiD, 34105 (4872): burial overhaul with tombstone meshes; Nordic look, not grave-stakes.
- WiZkiD Hagraven Clutter and Bones 49277 (3993) and Unique Skulls HD 52073 (5826): retextures of the nearest "skull-on-pole" props.
- East Empire Company Building FYX, Yuril, 86526 (2757): fixes only.
- Dunmer: Morrowind Mystique Decor 97500 (retex, permission "feel free, ask and credit"); Morrowind Hlaalu Architecture, Angelio, 157997 (modder's resource); House Telvanni Banners Restored 57443 (3 KB).
- Banner retextures (Rally's Banners 116289, Ennead 10564, Sigils of Skyrim 74875, Hold Border Banners 1737): all overwrite the vanilla banner textures
  globally. Useful only as a texture style reference; our clan emblems need our own texture paths on copied meshes.
- Not usable: totem searches returned only armour/Nordic; menhir/standing stones (Menhir 59927) are Nordic stones.

**Texture-only route is enough for: clan standards and long banners (mesh: `xanmeerbanner*`, `xanlongbanner*`, `imperialbanner*`, `bannerdres/hlaalu/redoran/telvanni`),
the Company standard, the pirate/Brethren flag, door-carving signs (spider-in-circle, hook-and-eye as decals), jar marks, painted/rune retextures of totem01-03 per tribe,
burnt stockade and chalk-white retextures, red-clay ware retextures.** A banner is 2D art on a held mesh; only the nif's texture path needs editing.

## 7. Step 3: what we would model ourselves (still thin after Nexus)

| # | Object | What / where seen / how often | Size | Static? | Difficulty |
|---|---|---|---|---|---|
| 1 | Grave-stake family (4 skull/glyph/serpent/twinned + small) | slim carved post staked in mud; in every settlement and as a field at Lilmoth; seen daily, close, but thin | 1.5-2.5 m x 0.2 | solid, no collision beyond a column | easy to medium: one narrow shape, texture carries the carving; thin shape stretches Tripo texture least |
| 2 | Tribe totems (rune, frilled skull, snake, painted skull) | per tribe, 14 camps + 4 Hutan-Tzel | 2-3 m | solid | medium: carved volume; retexture of held totem01-03 first |
| 3 | Sithis hearth shrines/idols (2-3 poses beyond `sithisshrine`) | home hearth, village centre | 0.6-1.5 m | solid | medium |
| 4 | Sap jar, tap and gourd | beside every Hist; at Jal-Veesa, forts | 0.2-0.5 m | solid, optional activator | easy |
| 5 | Uxith egg clutch in shell cup | nursery huts, 50 places | 0.3-0.6 m | solid | easy, replaces dragon eggs |
| 6 | Hist stele and Vos-Toh tablets | Hist pools | 1-2 m slab | solid | easy to medium: flat relief, texture-led |
| 7 | Raft-house pontoon and one-person tail raft | Nushara/Three Waters, Agaceph | 3-4 m | needs collision and water float; no movement | medium to hard: stability on water, collision |
| 8 | Kiln and clay mound wall | Okuwun Rahei, Aroxhu (12 rust places) | 2-3 m | solid | medium: larger surface |
| 9 | Tin and copper chime tree | Chime-Keepers (9) | 2 m | solid; chime sound handled by the engine light | easy |
| 10 | Teeba-Enoo court markers, ball | tribe sites | small | solid | easy |
| 11 | Veeskhleel sinew fetish | 1-2 spots | 0.3 m | solid | easy |
| 12 | Company standard and Brethren flag (texture) | enclaves, 6 Brethren places | banner | static | easy (2D) |

## 8. Step 4: ranking by player impact per unit of difficulty

1. **Clan/faction standards (texture on held banner meshes)**: easy, 137 + 9 lines; instantly separates 18 cultures. Do first.
2. **Rune/colourway retextures of held totems (per tribe)**: easy, 14 camps + Hutan-Tzel, the lore's one named object.
3. **Grave-stake family (own model)**: easy to medium, 137 places, the lore's single best repeatable system; a stake field marks the Rose (16 places) and the 4E 48 memory.
4. **Sap jar/tap and uxith clutch (own models)**: easy; Hist places are 123 mentions, separate Hist-forest (Murkwood, Root-Folk) from everyone.
5. **Company standard, pirate/Brethren flag, door-sign decals**: easy; 35 + 11 + faction hideouts; no faction is marked now.
6. **Sithis shrines (2-3 poses)**: medium; 20 give places, 110 notes; the faith is the province's centre of gravity.
7. **Hist stele, Vos-Toh tablets, chime tree**: easy to medium; fewer places.
8. **Kiln/clay mound pieces, raft-house, tail raft**: medium to hard; they would give Okuwun Rahei and Nushara (22 + 11 places) their own silhouette, but are larger.
9. **Everything bigger (huts, houses)**: do not model; no evidence that the huts are the gap (KotM has 46 mud hut, 45 stockade, 111 Blackwood pieces).

## 9. Not verified

- Final draft sources for the 245 undrafted places (rank 1 is the matcher's pick; 4 of 6 checked drafts differ).
- How the held meshes actually look (no screenshots); whether `argoniantotem01`, `xanmeerbanner*` and `sithisshrine` read as distinct per tribe; whether each already ships a separate texture.
- UESP pages for Dead-Water, Black-Tongue, Root-Whisper and Miredancer were not returned under those titles by the API; the Bright-Throat, Tum-Taleel, Ghost People, Paatru, Sarpa, Hapsleet, Xanmeer pages and the Argonian/Murkmire furnishing categories were. UESP's own wording is cited via the repo's lore files for the rest.
- Nexus permission lines were read from API summaries only.

## Recommendations

- Add one "tribe and faction marks" table to `docs/design/dressing.md`: 18 culture standards, 9 faction signs, the totem colourways, then wire them to the existing place cultures (evidence: kinds.json has no tribal object; culture 18 rows exist).
- Fix the Ree-An-Wo concentration before adding art: re-match the 62 places so Hutan-Tzel, Agaceph and Naka-Desh draw different sources, or accept that the new marks are the distinction (evidence: section 1.2).
- Start the art pilot with the grave-stake set (it has the strongest lore citation, sithis-nisswo-shadowscales.md:182).

Covered: story/lore (tribes, topics, extrapolation excerpts), story/design (province-vibe, quest lines), docs/design/{identity,dressing}, newworld sources (dressing kinds, cultures, regions), world.sqlite (region, culture, place, place_source, place_note, story_line), mesh lists and asset registries, UESP via API (Murkmire/Argonian furnishings categories, tribe pages), Nexus (about 120 terms, ~35 --mod checks) · Skipped: story/design/world/regions/*.md and story/lore/regions/* (110 KB each; the sqlite carries their look notes), docs/phases nw-01/nw-05c (no assets content), 245 undrafted place plans, Nexus file pages beyond API summaries (no mod downloads by brief).
