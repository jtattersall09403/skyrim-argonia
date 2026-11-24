# New art, lane: every region, culture and faction against the lore (owner call #93, research only)



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

1. **The pool is thin in what the places can show, not in how many source places they draw on.** At `place_source` rank 0 (the first choice; ranks run 0 to 3) the 258 places draw on 246 distinct source places; the most-used (KotM Ree-An-Wo, Seekhat Yol) serve 3 each. By source family (mod of the rank-0 source): 126 places take a vanilla-derived source (Skyrim itself plus Nyhus, trading posts, Explore Skyrim, Northwatch), 77 an Argonian-kit source (King of the Murkmire, HTBM, BMV), 55 another mod (Baan Malur 20, Wyrmstooth 18, Depths and underwater 6, Dunmer/Ashlander packs 8, others). Only 30% of places start from an Argonian kit.
2. **The places the lore calls most Black Marsh lean on vanilla.** Murkwood (Hist forest, "most traditional Argonian gear") draws 10 of its 13 places from vanilla sources and 1 from an Argonian kit; Root-Folk (forest-green) 13 of 19 vanilla, 4 Argonian-kit; Banujha Basin 11 of 15 vanilla; Cape Percar 12 of 17; Nha-Enasa 7 of 11; Rose (Lilmoth coast) 9 of 16 vanilla. The Argonian-kit places concentrate in Tulmek Washes (12 of 24), Benthic Yobesh (9 of 10), Althii (9 of 22), Barsaebica (7 of 14). Tribes: Hutan-Tzel 3 of 4 vanilla, Naka-Desh 3 of 5 vanilla and 0 Argonian-kit, Three Waters 3 of 6 vanilla, Mine-Burners 6 of 7 vanilla, Stormhold 7 of 11 vanilla. These are the matcher's plan, not the final look: of the 6 drafted outposts/camps checked the draft differs from rank 1 in 4 (rank 0 not rechecked), and only 13 of 258 places are drafted. The fix is therefore what the drafts then dress them with, which is where marks and signature objects act.
3. **No place or culture is told apart by an object of its own.** `kinds.json` dressing has fungi, bones, insects and lanterns only; no tribe mark, totem, banner emblem, grave-stake or shrine. Hutan-Tzel (whose one canon object is the rune-carved totem), Agaceph, Naka-Desh and the Root-Folk differ in assets by tint and name only. This is the finding that the art would change, and it does not depend on the source ranks.
4. **The pool already holds more signature props than the plan uses**, mostly in King of the Murkmire (KotM), HTBM Curse of Cipactli and Mud Mother Grove (mesh lists): Xanmeer totem01-03 and skeletontotem01-04, `argoniantotem01`, `argonianbonechime01/02`, `drum01`, `sithisshrine`, `paintedurn01`, 8 `xanmeerbanner*` plus 4 `xanlongbanner*`, `saxhleeltapestry01/02`, `wallhanging01-03`, `hangingfeathers01-03`, `scaletent01-03`, `scalefence01-05`, `snakefence01-03`, `vossasatl01-03`, `doll_turtle`, `nisswocoin`, `fishtoken`, `ghosttoken`, `serpentstatue_feathered`, `argonianhead01-03`, `skullstack01`, `runicstone`, `roadsign1-5`, windchimes. BMV holds Dunmer house banners (`bannerdres`, `bannerhlaalu`, `bannerindoril`, `bannerredoran`, `bannertelvanni`) and lcr_totem1-6. Vanilla holds 74 banner meshes, Hagraven poles and fences (the nearest thing to a grave-stake).
5. **Objects with no mesh in the pool** (all mesh lists and the 12 016 + 2 100 + 15 050-row registries searched): grave-stake (xul-vaat), uxith with Argonian eggs (the "Argonian eggs" are vanilla dragon eggs, `argonianeggs/dragoneggs1-5`), sap tap or jar, Hist-cultivation stele, Vos-Toh tablets, Teeba-Enoo court, Veeskhleel fetishes, boundary posts, Company standard, pirate flag, any faction sign. Section 6 lists what Nexus (both games, name and description) offers for each.
6. **Nine story lines are separated by gear and dialogue only**; no sign (Twin Lamps lantern, spider-in-circle, hook-and-eye, Brethren sign) exists as a mesh or texture.
7. **Lore tribes with 0 place mentions**: Naga-Kur, Dead-Water, Black-Tongue, Root-Whisper, Miredancer, Tum-Taleel, Veeskhleel, Bright-Throat, Hapsleet. Paatru (13 notes) and Sarpa (14) appear only as inland tribes. Foreign enclaves: Dunmer 34 place notes, Imperial/Legion/Warden 69, pirates 35, Company 9, Khajiit 22, Bosmer 6; Dunmer and Imperial banners are held, Company and pirate marks are not.
8. **Nordic leakage**: `newworld/places/nordic_review.jsonl` flags 17 of 41 reviewed BMV bases as Nordic; `skyrim.nightcallertemplelocation` (Nordic stone) serves imperial and Kothringi ruins. Cited, not re-measured.

## 2. Region table (24 regions)

Columns: places / rank-0 first-choice source family (Argonian kit: KotM, HTBM, BMV; vanilla-derived; other mod). D = distinctiveness from neighbours *in assets*, C = lore/vibe consistency (0-3).
"Lore looks like" quotes the region's `look` note (all EXTRAPOLATED except Topal Bay) plus `region_profile.signature`.

| Region | n / rank-0 sources (Arg-kit / vanilla / other) | Lore looks like | We hold to show it | D | C | Missing signature things |
|---|---|---|---|---|---|---|
| Althii Archipelago | 22 / 9 / 11 / 2 | paddies, stilt villages, brick ruins in vines; saltrice dishes | KotM + Tropical Skyrim winners; 5 Lilmothiit ruins; rose culture 11 | 2 | 2 | rice-paddy dike/sluice props, estate gate, tenant vs garrison signage |
| Aphon Isle | 4 / 1 / 1 / 2 | grey hills, white-washed lookout, smugglers' cave, contraband | vanilla Tropical winners, Wyrmstooth | 2 | 2 | Brethren sign, moon-sugar crates (pirates.md:238) |
| Arnesian Jungle | 10 / 4 / 2 / 4 | terraced stone towns, hardwoods, Velothi ruins under vines | KotM, Baan Malur, Xanmeer tileset, glowing fungi | 2 | 2 | Stone-Sleeper carved terrace posts; Tsonac "asleep Hist" shrine |
| Aunike Ridge | 4 / 1 / 2 / 1 | rock outcrops, stone-footed huts, windchimes, watchfires | KotM + Nyhus; tin chimes in sheet only | 1 | 2 | tin chimes (held `tamwindchime01` is one generic) , penned-lizard pens |
| Banujha Basin | 15 / 3 / 11 / 1 | flooded channels, scorched timber, tiered stilt halls | KotM stockades (45 pieces) + bmv; burn-scar bones | 2 | 1 | scorched/burnt retexture of stockade set; Mine-Burner trophies; Soulrest-bound mine signs |
| Barsaebica | 14 / 7 / 7 / 0 | white Ayleid stone in reed beds, stilt huts, weirs | cc-ayleid-resources, Ayleid ruins, reed weirs, bone piles | 3 | 3 | reed-warden charm (Ayleid oddment), weir fish-traps (check KotM `fishracksmall`) |
| Benthic Yobesh | 10 / 9 / 1 / 0 | blue-green water, coral, spires, black trench | Depths of Skyrim, Sirenroot, underwater rivers | 3 | 3 | none new; coral-crusted relic is a retexture |
| Blackwood | 7 / 2 / 4 / 1 | flooded hills, cairn-fields | KotM blackwood set (111 pieces), cairn skulls | 2 | 2 | cairn/stake hybrid markers; Sul-Xan jade mask idols (4 notes) |
| Cape Percar | 17 / 3 / 12 / 2 | red-gum hills, burn-scars, grey Imperial ruins, stilt coast | Tropical winners + KotM | 2 | 2 | Khajiit coaster stalls, Imperial-descended crockery |
| Chixathe Mesa | 16 / 3 / 7 / 6 | pale cliffs, chalk, stone cuts, dry stores | Baan Malur, mine kits, cairn skulls | 2 | 2 | chalk-white retexture of stone cuts, Agaceph book shelves |
| Hatandros Bight | 10 / 3 / 6 / 1 | grey mudflats, black Velothi headlands, sea fog | Baan Malur Velothi, Caves of Morrowind | 2 | 2 | salt-pan frames, smuggler landing marks |
| Kotherra Mangroves | 9 / 3 / 5 / 1 | black water, red mud, Imperial grey stone road | KotM + Tropical; red-clay pottery | 2 | 2 | Cyrodiilic road markers; Imperial household set (held vanilla only) |
| Lake Ulaish | 9 / 1 / 4 / 4 | pale lake, lantern posts, eel traps, stone-footed farms | KotM lanterns (`saxhleellantern01/02`) | 2 | 2 | eel traps, silt-islet lantern posts, Warden toll post at Gysilla |
| Murkwood | 13 / 1 / 10 / 2 | dark wood of huge roots, hanging moss, Hist grove | Sleeping Hist Tree, KotM Hist roots (hist_root01-11, glands), hanging lanterns | 3 | 2 | tapping and sap jars, tree-minder platform, grave-stakes |
| Nha-Enasa | 11 / 2 / 7 / 2 | reed banks, stilt platforms, grey ruin stones | KotM, Kothringi ruins | 2 | 2 | gar spears racks, salt bag stacks, caravan stalls |
| Nushara Bayou | 11 / 2 / 4 / 5 | brown sheets of water, raft-houses, herons | KotM, glowing fungi; rafts none | 2 | 2 | **raft-houses** (no raft/pontoon mesh, only `argonianplatform`), shell/rice racks |
| Okuwun Rahei | 22 / 5 / 8 / 9 | red-brown clay mounds, bright reed thatch, kilns, Seafalls | KotM, Velothi ruins; mud huts | 2 | 2 | **kiln, painted clay ware, mound terrace walls** (KotM has `bigpot`, `paintedurn01` only) |
| Padomaic Ocean | 3 / 0 / 2 / 1 | grey-green swell, drowned timbers | Baan Malur wrecks, Sailable Ship | 2 | 3 | wreck goods of three eras |
| Sea of Mists | 2 / 0 / 1 / 1 | mist banks, islets | same | 1 | 3 | none |
| Skeith Isle | 5 / 1 / 2 / 2 | grey crags, keep, Grey Tooth spire | Wyrmstooth, Caves of Morrowind, Ashlander camp | 3 | 3 | pirate hoard dressing, Brethren flag |
| Topal Bay | 2 / 0 / 1 / 1 | grey-green bay, sailors' gear | vanilla Tropical, Baan Malur | 1 | 3 | Company standard |
| Tulmek Washes | 24 / 12 / 9 / 3 | brown water, stilt towns, boardwalks, drowned domes | KotM Lilmoth, boardwalk kits, Lilmothiit ruins | 2 | 3 | Blackrose prison look (**one prison, drafted from a Skyrim keep?**), toll tokens |
| Ultherus Swamp | 4 / 2 / 1 / 1 | cattail maze, stilt towns hung with metal chimes | KotM | 2 | 2 | metal chimes; dragon's-tongue drying racks |
| Valley of Storms | 14 / 3 / 8 / 3 | stone-footed farms, causeways, grey Imperial forts | KotM + Skyrim farms, Nyhus forts | 2 | 2 | Dunmer minority marks, causeway markers |

Honest reading at rank 0: sources are not shared (246 distinct for 258 places); the thinness is **Argonian feel**. Regions whose people the lore makes most Argonian but whose places mostly start from a vanilla source: **Murkwood (10 of 13), Banujha Basin (11 of 15), Cape Percar (12 of 17), Nha-Enasa (7 of 11), Kotherra (5 of 9)**; Murkwood and Banujha scores for consistency are lowered accordingly (C 2 and 1 respectively). Each of the 24 regions' distinctness among neighbours still rests on atmosphere (`identity.md`); no region has an object that only it shows. Open-water regions are tiny (7 places).

## 3. Culture table (18 cultures; `culture` rows in the sqlite, `tribes.md`, `material-culture.md`)

| Culture (tint) | places / rank-0 (Arg-kit / vanilla / other) | Lore looks like | We hold | D | C | Missing |
|---|---|---|---|---|---|---|
| Warden Marches (crimson-red) | 21 / 5 / 9 / 7 | stone forts, keeps, posts held by Argonians; Warden militia | vanilla Imperial forts, Nyhus, HTBM legion banners and armour, ancient-imperial-armor | 2 | 1 | **Argonian over-Imperial mark** (Warden standard over Legion-style fort); Nordic residue in fort stone (nightcaller 13) |
| Root-Folk of Helstrom (forest-green) | 19 / 4 / 13 / 2 | stilts, root hollows, nothing new in stone, Hist grove | Sleeping Hist Tree, hist_root set, KotM huts | 2 | 3 | sap jars, tree-minder tools, grave-stakes |
| Archon Harbour Folk (gold) | 1 / 0 / 0 / 1 | amphibious port, underwater games, guar that breathe underwater | Lilmoth KotM, Ferries | 1 | 2 | jump-stick, jaw-beetle game props (material-culture: Archon games) |
| Naka-Desh (indigo) | 5 / 0 / 3 / 2 | wide-faced river people, osheeja gars, chimes in memory of Kothringi | other-mod and vanilla sources; no tribe object | 1 | 2 | bridled-gar fishing rafts, chimes |
| Sedge-Wardens (jade) | 6 / 3 / 2 / 1 | reed weirs and mats, Hist pool market | KotM Alten Meerhleel look | 1 | 3 | reed mats, weir traps |
| Agaceph (lime) | 4 / 1 / 0 / 3 | rainbow-scaled, razor-thin tail rafts, looted books | other-mod and vanilla sources; no tribe object | 1 | 2 | **tail-driven one-person raft**, book shelves, rainbow dye |
| Hutan-Tzel (magenta) | 4 / 0 / 3 / 1 | totems carved with runes only they read | vanilla sources; HTBM totem01-03 exist but none tied to the tribe | 1 | 2 | **rune-carved totem set (the tribe's one canon object)**, naheesh feather staff |
| Island of Blackrose (olive) | 10 / 5 / 5 / 0 | island city, prison ruin, stilt villages | KotM Seekhat Yol, vanilla keep | 1 | 2 | prison gate, ledger room dressing |
| Chime-Keepers (oxblood) | 9 / 4 / 4 / 1 | Kothringi-named towns: tin and copper chimes at every eave, metal-woven rope, stone footings, tidal canoe | `argonianbonechime`, windchimehavok (HTBM), `tamwindchime01` | 1 | 3 | **tin/copper chime strings in quantity and metal rope**, Kothringi tidal canoe (UESP Online:Kothringi Tidal Canoe; only boats ours: `shiprowboat`) |
| Gideon Frontier (pale-green) | 8 / 3 / 5 / 0 | most Cyrodiilic; courthouse, records, red-clay pottery | KotM, vanilla Imperial, Skyrim farms | 2 | 3 | courthouse notice boards, Company/Imperial merchants' signs |
| Spray-Folk of Seafalls (pearl) | 5 / 1 / 3 / 1 | cliff-and-surf village, no Hist reach | Keeba Hollow, Wyrmstooth lighthouse | 2 | 2 | surf-shell dress, falls-side racks |
| Three Waters (plum) | 6 / 1 / 3 / 2 | reed houses on rafts and stilts that move | KotM huts, `argonianplatform` | 1 | 2 | **raft-houses, pontoons** (none held) |
| Lilmoth and Murkmire Coast (rose) | 16 / 3 / 9 / 4 | rebuilt stilt town over the mass grave, merchant council, drowned Imperial quarter | KotM Lilmoth (9 uses), Baan Malur | 2 | 3 | grave-stake field (the lore's "carved grave-stakes and memorials", province-vibe §2); drowned-quarter silt dressing |
| Clay-Mound People (rust) | 12 / 4 / 6 / 2 | red clay mounds, kilns, pottery, dye | KotM, `paintedurn01` | 1 | 2 | **kiln, clay mound slopes, painted ware** |
| Stone-Sleepers (sky-blue) | 5 / 3 / 1 / 1 | jungle upland people who still build in stone over Velothi/Ayleid | Xanmeer tileset, Velothi kits | 2 | 3 | dream-reader tree-minder seat |
| Mine-Burners (steel-blue) | 7 / 1 / 6 / 0 | fortified towns, watch posts, scorched trophies, salvaged iron | KotM stockade (45), mine kits | 2 | 2 | scorched trophies, burnt stockade variants |
| Shadowfen Border / Stormhold (stone-grey) | 11 / 1 / 7 / 3 | stone causeways, raised farms, Vicecanons, oldest Dunmer minority | KotM, Skyrim farms, Dunmer packs (solstheim-dunmer-additions) | 2 | 2 | Vicecanon office signage, Dunmer-Argonian mixed marks |
| Soulrest/Topal Coast (umber) | 16 / 4 / 10 / 2 | ex-capital, mixed people, Khajiit coasters, Bosmer seafarers | Tropical winners, Khajiit packs, Bosmer packs | 2 | 3 | Soulrest merchant council seal |

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

## 6. Step 2: Nexus, both games, name and description (re-run 2026-11-24)

Searched with `tooling/nexus_search.py` (Special Edition and the 2011 game, name and description text): totem, idol, tribal, shrine, banner, flag, standard,
fetish, skull, effigy, statue, grave, stake, tombstone, marker, Argonian, Saxhleel, Sithis, Hist, Aztec, Mayan, tiki, voodoo, swamp, "witch doctor", egg,
nest, jar, amphora, urn, chime, drum, stele, tablet, pirate, "East Empire", "modders resource", "statue resource", "clutter resource"; then Hawaiian, Polynesian,
Maori, Inca, Mesoamerican, "tribal mask", "skull pole", "bone totem", shaman, Incaendo, Tamira, "tribal village", "stilt house", raft, "war paint", "carved totem",
"wooden idol". Hits were read by category (Modders Resources, Models and Textures, Miscellaneous, Items and Objects) and summary; description hits are noisy, so
candidates below were read with `--mod`. **Not found by any term: a pack of Argonian grave-stakes, carved tribal totems, sap vessels or egg nests.** The
nearest, listed per row. "SE" = Special Edition listing, usable as is; "2011" = the 2011 game, usable only if its meshes are converted to Special Edition format
(NIF to SSE, e.g. Cathedral Assets Optimizer or NifSkope; textures unaffected). Permission lines are the author's own text from the mod page API.

| Candidate (Nexus id) | Author, endorsements | What it holds (from the description) | Fills | Format | Permission line |
|---|---|---|---|---|---|
| Incaendo's Banner Resource SSE (SE 17604) | Incaendo, 122 | 59 new banners with their own textures | clan standards, Company, pirate flag | SE | modder's resource; credit |
| Incaendo's Banner Resource 2 (SE 94919) | Incaendo, 31 | 141 designs, 163 banners with colour variants, most standard movable-static banners, some thin Solitude-style static; made with image editing, AI image generators and public-domain images | clan standards by culture | SE | modder's resource; "please check out my other resources" |
| Incaendo's Asset Library (SE 141898) | Incaendo, 4 | esp master bundling the banner packs, paintings and Skaven banners | same | SE | modder's resource |
| Incaendo's Banner Resource (2011 skyrim:91591) | Incaendo, 86 | the same 59 banners | same | 2011 (SE port above exists) | modder's resource |
| Incaendo's Miscellaneous Resources (SE 85915) | Incaendo, 23 | 26 objects, mainly vanilla retextures (contents not itemised on the page) | possible props | SE | modder's resource; read the pack before relying |
| Flags Resource (SE 56152) | Incaendo, 2.0 | national, historical, political and misc flags (Jolly Roger named) | pirate flag, enclave flags | SE | modder's resource |
| Hawaiian Deity Statue (SE 20247; 2011 skyrim:93880) | Incaendo, 15 / 14 | one Hawaiian deity statue mesh; textures not included (they come from the credited 2011 mod 83645). HTBM already carries a `dwg_hawdeity_01-03` family | idol (a Sithis or Hist idol) | SE and 2011 | modder's resource; texture credit to the original |
| Stroti's Stilt House Resource (2011 skyrim:61824) | Stroti and Tamira, 270 | open stilt house, animated shutter door, grill; optional separate hut and platform | stilt houses and platforms for Nushara/Three Waters | 2011 (Oblivion conversion); convert | use meshes and textures in your own mods with credit, no charge; "none may be used in paid mods" |
| Tiki Torch Pack (2011 skyrim:24711) | Teirdalin, 65 | tiki torches (and a dog torch) merged from vanilla models | brazier/boundary torch | 2011; convert | "feel free to use in your own mods, credit me" |
| BadGremlins Witches Festival Resources (2011 skyrim:57800) | badgremlin, 132 | glass skulls, festival ropes with skulls, bone pile, offering bowls, mounted skulls, witchboard, retextured tent, skull-handle door, witches throne, sign on a pole | skull ropes, offering bowls | 2011; convert | modder's resource (full line not read) |
| Unique TombStone Models (2011 skyrim:93116) | mypilzzes, 76 | HD tombstone models | grave markers (Nordic-leaning, retextured) | 2011; convert (128 MB) | "for everyone" |
| Liam's Clutter Resource (2011 skyrim:94175) / Liam's Dragon Bone Furniture and Clutter (skyrim:93686) | Liam, 150 / 57 | clutter meshes; furniture and clutter built from dragon bones | bone furniture, clutter | 2011; convert | modder's resource (lines not read) |
| Spriggan Statue (2011 skyrim:60696), Ogre Statue (skyrim:65268), Stendarr and Tiber statues, Female Statue Resources (skyrim:98157) | GendunDrup, Edhildil, Maduck89 | single statue meshes | none fit Argonian lore; Spriggan statue only as a swamp-spirit idol | 2011; convert | free use with credit |
| Building kits and other items (2011 skyrim:58262) | jet4571 / Elianora, 595 | 383 farmhouse/dock/porch kit meshes at 64-unit snap | docks, porches | 2011 | credit with link; cannot be ported to another game without permission; not for other resource packs |
| Mad Modder's Assets (SE 83445) | ManyMadModders | thousands of meshes and textures from many authors | unknown contents | SE | author states he made 5% of it; per-asset permissions vary; do not rely |
| Murkmire Official Housing Pack (SE 194072), Shifts-Sand's Saxhleel Sundries (SE 191593) | pancake0723, 24; YourFellowFern, 6 | KotM housing add-on; ESO Argonian clothing ports (DEMO) | housing; tribal dress | SE | read the mod page before use |
| Statue of Sithis (SE 73735) | Mandragorasprouts, 3574 | one Sithis statue | Sithis idol (size larger than a hut prop) | SE | "do not upload this mod on other sites" |
| Rally's Werewolf Totems (SE 28882; 2011 skyrim:99300), Totemic Tombstones (SE 157281), HFs Totem (SE 164197), Easthold Totemic (armour) | various | retextures of the Nordic werewolf totem props, an Odin totem, tombstone remesh | nothing Argonian; vanilla retexture bases only | SE | author's lines |
| Sepolcri (SE 34105), Graveyards of the Marshlands (SE 132767, PBR 189308) | WiZkiD 4872; Retrophyx 410 | burial-site overhaul; Morthal-swamp graveyard decor | marsh graveyard decor; Nordic stones | SE | credits only |
| East Empire Company Armor (already a row), FYX Eastern Empire Company Building (SE 86526) | Yuril, 2757 | building fixes only | none | SE | n/a |
| Banner retexts: Rally's Banners 116289, Ennead Banners 10564, Sigils of Skyrim 74875, Hold Border Banners 1737, House Telvanni Banners Restored 57443 | various | overwrite vanilla banner textures; not new designs | style reference | SE | author's lines |

Standing gaps after this search: nothing found for Argonian grave-stakes, carved totems, sap jars, egg nests, Hist stelae or Vos-Toh tablets. Statues of a deity (Hawaiian)
and tiki torches are the closest tribal shapes found and are non-Argonian; any use is a judgement call for the owner (lore consistency, `owner-bar` and decision 0006).

**Texture-only route is enough for**: clan standards, the Company standard, the pirate/Brethren flag, door-carving signs (spider-in-circle, hook-and-eye as decals), jar marks,
per-tribe colourway or rune retextures of totem01-03, burnt and chalk-white retextures of stockade pieces, red-clay ware retextures. For banners the pool is now large: Incaendo's two
SE packs hold 220+ finished designs (some AI-generated, public-domain images), so only our own emblem textures need making, and Fal art could draw them onto the same movable-static banner mesh.

## 7. Step 3: what we would still model ourselves

After section 6 these still have no mesh (Argonian grave-stake, sap jar and tap, uxith clutch, Hist stele, totems in Argonian form, Sithis shrine poses beyond `sithisshrine`, kiln, raft-house).
Stilt houses and platforms exist in the 2011 resource (row 8) but need conversion; the raft, tail raft and kiln do not exist anywhere searched.

| # | Object | What / where seen / how often | Size | Static? | Difficulty |
|---|---|---|---|---|---|
| 1 | Grave-stake family (4 skull/glyph/serpent/twinned + small) | slim carved post staked in mud; every settlement, a field at Lilmoth; daily, close, but thin | 1.5-2.5 m x 0.2 | solid, no collision beyond a column | easy to medium: one narrow shape, texture carries the carving |
| 2 | Tribe totems (rune, frilled skull, snake, painted skull) | per tribe, 14 camps + 4 Hutan-Tzel | 2-3 m | solid | medium; retexture of held totem01-03 first |
| 3 | Sithis hearth shrines (2-3 poses beyond `sithisshrine`) | home hearth, village centre | 0.6-1.5 m | solid | medium; Hawaiian deity statue (converted) is a possible base |
| 4 | Sap jar, tap and gourd | beside every Hist; Jal-Veesa, forts | 0.2-0.5 m | solid, optional activator | easy |
| 5 | Uxith egg clutch in shell cup | nursery huts, 50 places | 0.3-0.6 m | solid | easy; replaces dragon eggs |
| 6 | Hist stele and Vos-Toh tablets | Hist pools | 1-2 m slab | solid | easy to medium: flat relief, texture-led |
| 7 | Raft-house pontoon and one-person tail raft | Nushara/Three Waters, Agaceph | 3-4 m | collision and float, no movement | medium to hard |
| 8 | Kiln and clay mound wall | Okuwun Rahei, Aroxhu (12 rust places) | 2-3 m | solid | medium |
| 9 | Tin and copper chime tree | Chime-Keepers (9) | 2 m | solid | easy |
| 10 | Teeba-Enoo court markers, ball | tribe sites | small | solid | easy |
| 11 | Veeskhleel sinew fetish | 1-2 spots | 0.3 m | solid | easy |
| 12 | Our own clan emblem textures | 18 cultures, 9 lines | banner | static | easy (2D, on Incaendo or HTBM banner meshes) |

## 8. Step 4: ranking by player impact per unit of difficulty

1. **Clan/faction standards (our emblems on the held HTBM banners or Incaendo's SE banner meshes)**: easy, 137 living places plus 9 lines; separates 18 cultures. Do first.
2. **Rune/colourway retextures of held totems (per tribe)**: easy, 14 camps + Hutan-Tzel, the lore's one named object.
3. **Grave-stake family (own model)**: easy to medium, 137 places, the lore's single best repeatable system; a stake field marks the Rose (16 places) and the 4E 48 memory.
4. **Sap jar/tap and uxith clutch (own models)**: easy; 123 notes mention the Hist; separates the Hist forest from everyone.
5. **Company standard, pirate/Brethren flag (Flags Resource 56152 and our textures), door-sign decals**: easy; 35 + 11 + faction hideouts; no faction is marked now.
6. **Sithis shrines (2-3 poses)**: medium; 20 give places, 110 notes.
7. **Hist stele, Vos-Toh tablets, chime tree**: easy to medium; fewer places.
8. **Stilt house/platform conversion (Stroti, 2011)**: medium (conversion, then check against KotM stilt kit); gives Nushara/Three Waters silhouette only if KotM's platforms fail.
9. **Kiln/clay mound, raft-house, tail raft**: medium to hard; larger surfaces.
10. **Huts and houses**: do not model; KotM holds 46 mud hut, 45 stockade and 111 Blackwood pieces.

## 9. Not verified

- Final draft sources for the 245 undrafted places (rank 0 is the matcher's first choice; 4 of 6 checked drafts differed from the rank-1 pick, rank 0 not rechecked).
- How the held meshes actually look (no screenshots); whether `argoniantotem01`, `xanmeerbanner*` and `sithisshrine` read as distinct per tribe; whether each already ships a separate texture.
- UESP pages for Dead-Water, Black-Tongue, Root-Whisper and Miredancer were not returned under those titles by the API; the Bright-Throat, Tum-Taleel, Ghost People, Paatru, Sarpa, Hapsleet, Xanmeer pages and the Argonian/Murkmire furnishing categories were. UESP's own wording is cited via the repo's lore files for the rest.
- Nexus permission lines were read from API summaries only.

## Recommendations

- Add one "tribe and faction marks" table to `docs/design/dressing.md`: 18 culture standards, 9 faction signs, the totem colourways, wired to the existing place cultures (evidence: kinds.json has no tribal object; 18 culture rows exist).
- When drafting, give the places that start from a vanilla source (Murkwood 10 of 13, Banujha 11 of 15, Cape Percar 12 of 17) the Argonian kit's props and the tribe marks, since the source choice leaves them thin on Argonian feel (section 1.2).
- Start the art pilot with the grave-stake set (strongest lore citation, sithis-nisswo-shadowscales.md:182) and the clan emblem textures on a held banner mesh.

Covered: story/lore (tribes, topics, extrapolation excerpts), story/design (province-vibe, quest lines), docs/design/{identity,dressing}, newworld sources (dressing kinds, cultures, regions), world.sqlite (region, culture, place, place_source, place_note, story_line), mesh lists and asset registries, UESP via API (Murkmire/Argonian furnishings categories, tribe pages), Nexus (both games, name and description, about 90 terms, 30 --mod checks) · Skipped: story/design/world/regions/*.md and story/lore/regions/* (110 KB each; the sqlite carries their look notes), docs/phases nw-01/nw-05c (no assets content), 245 undrafted place plans, Nexus file pages beyond API summaries (no mod downloads by brief).
