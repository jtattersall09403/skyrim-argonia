# Owner call #93, lane PLACES AND PIECES: where the asset pool is thin (research only)

Method of BRIEF-common.md, steps 1 to 4. Measured 2026-11-24 from `newworld/out/world.sqlite` (tables `place`, `place_source`,
`source_place`), `out/places/catalogue/bases.jsonl` (40,968 load-order bases with plugin, type, model, `nordic` flag),
the six drafted places' `newworld/places/*/spaces/*/refs.jsonl`, and the 54 mined source bundles
`out/places/bundles/src.*/spaces/*/refs.jsonl`. Scratch scripts were in the session scratchpad; nothing in the repo was changed.

## 0. Live docs, and the one to edit

- Cover this topic already: decision 0041 (carried-whole sources), owner-rulings.md lines 220-222 (2026-11-20 Nordic pieces fine,
  Tropical Skyrim version or easy swap, never laborious), 572-576 (2026-11-10 a piece a source place itself uses is accepted),
  646-656 (2026-11-12 Nordic layouts accepted, more sources for bad gaps), 164/175 (interiors may look Nordic),
  `story/lore/topics/material-culture.md` (three building kits, prop list, "grave-stakes have no mesh").
- Confirmed: the rulings make Nordic look non-blocking. The art case is therefore BREADTH and BLACK MARSH FEEL, not compliance.
- Superseded/contradicted: material-culture.md cites an "asset inventory gap 3" that exists in no file in the repo (grep found it only in
  that file). This report's section C/D is the first measured inventory.
- The one doc to edit if the owner proceeds: `docs/design/dressing.md` (kinds of small signature things, bases from the load order);
  not a new file. (Not verified that dressing.md is the right home beyond its name; `newworld/sources/dressing/kinds.json` is its data.)

## A. Places against their source places (258 places, 4 ranked candidates each)

Caveat that decides how to read it: `place_source` rank 0 is the matcher's best score (mean 0.73; 11 below 0.6), not the drafter's final
choice. Decision 0041 shows hand choice differs (Karsh-Naal's rank-0 orc stronghold was "about a fifth usable" and was swapped for KotM
Ree-An-Wo). The six drafted places' real sources (`place.json` `source_id`): Helstrom = BM&V Helstrom; Jal-Veesa = KotM Seekhat-Yol;
outpost-m6-m66 = KotM Hulux-Inoag village; outpost-m11-m63 and tribal-camp-m2-m68 = KotM Ree-An-Wo marker; outpost-m13-m65 = vanilla
Military Camp Hjaalmarch Imperial. (Mapping of the three outposts to Ashgate Landing / Reed-Sill Weir / Teel-Fen Weir is my inference from
PROGRESS.md:22 and the folder names; the places' names were not read from place.json.) So 4 of 6 drafts ended on Argonian-kit sources.

### A1. Where rank-0 sources come from (258 places)

| source mod | rank-0 places | kit |
|---|---|---|
| vanilla Skyrim locations (Tropical Skyrim winners) + Trading Posts | 105 + 5 = 110 (43%) | Nordic/Imperial/orc/giant, plus tropical trees |
| King of the Murkmire | 42 (32 distinct sources of 34) | Argonian (Saxhleel/Murkmire) |
| BM&V | 24 | mixed: mostly Nordic/Dunmer/Imperial tagged |
| Journey to Baan Malur | 20 | Dunmer/Morrowind |
| Wyrmstooth | 18 | Nordic |
| Nyhus | 13 | Nordic/mixed |
| Cipactli + HtBM | 7 + 4 | Argonian/Kothringi |
| 12 other mods (depths, solstheim x3, aho, caves, moonpath...) | 20 | various |

- Argonian-kit mods (KotM, BM&V, Cipactli, HtBM) supply 77 of 258 rank-0 sources (30%). By culture tag on the source (derived from model
  paths): `argonian` 73 (28%), `nordic` 164 (64%), `imperial` 124, `dunmer` 46, none 36. 100 places (39%) have an Argonian-kit mod or
  argonian tag at rank 0.
- The whole Argonian-kit source pool is 74 source places (KotM 34, BM&V 29, Cipactli 7, HtBM 4) for 258 places.
- Over all four ranks, 61 places have NO Argonian-kit-mod candidate at all and 35 have none even by tag.

### A2. By kind (rank 0). n; Argonian-kit mod; argonian tag or kit mod. Last column: distinct sources over all 4 ranks.

| kind | n | arg mod | arg any | distinct (4 ranks) | note |
|---|---|---|---|---|---|
| outpost | 41 | 6 | 7 | 50 | 29 rank-0 are vanilla military camps/towers/shacks |
| village | 29 | 11 | 9+ | 27 | |
| hamlet | 24 | 9 | 2+ | 29 | |
| tribal-camp | 14 | 1 | 4 | 16 | 11 vanilla (orc strongholds Mor Khazgur, Largashbur, Narzulbur; giant camps; redoubts) |
| imperial-ruin | 12 | 3 | 5 | 14 | fit is fine (Imperial kit is lore) |
| velothi-ruin | 12 | 0 | 1 | 13 | Dunmer mods (Baan Malur 7); fit fine, 12 of 12 have no Argonian candidate by design |
| city | 11 | 4 | 4 | 12 | Riften, Solitude, Markarth, Windhelm at rank 0 |
| shipwreck | 11 | 2 | 1 | 11 | Nordic ship kit; 8 of 11 have no Argonian candidate |
| town | 10 | 6 | 4 | 12 | |
| mine | 10 | 0 | 1 | 12 | all Nordic mines; 10 of 10 no Argonian candidate |
| farm | 9 | 0 | 2 | 10 | Nordic farmsteads; 9 of 9 no Argonian candidate; fewest distinct per place (1.1) |
| lilmothiit-ruin | 9 | 7 | 7 | 11 | good (KotM) |
| abandoned-village | 8 | 4 | 2 | 13 | |
| fort | 8 | 1 | 2 | 10 | 5 of 8 no Argonian candidate |
| kothringi-ruin | 8 | 3 | 2 | 12 | weak: Kothringi kit is only Cipactli's `kothringi/` folder (33 models) |
| ayleid-ruin | 7 | 6 | 5 | 7 | good, but 7 sources for 7 places = no variety |
| sunken-ruin | 7 | 7 | 7 | 9 | all KotM |
| estate 3, keep 3, peak 3, quarry 2, lighthouse 2, belvedere, prison, homestead | 15 | 0 | 0-1 | | all vanilla/Nordic, no Argonian candidate |

By people (165 places that have one of the 18 Argonian cultures; 93 are ruins/wrecks/camps with none): only 58 (35%) have an Argonian-kit
rank-0 source. Weakest: indigo Naka-Desh Riverbacks 0 of 5, magenta Hutan-Tzel 0 of 4, gold Archon Harbour 0 of 1, plum Three Waters 1 of 6,
steel-blue Mine-Burners 1 of 7, pearl Seafalls 1 of 5, lime Agaceph 1 of 4, stone-grey Shadowfen Border 3 of 11. Strongest: jade 3/3, olive 6/10,
sky-blue 3/5. By region weakest (rank-0 argonian-kit or tag): lake-ulaish 2 of 9, nha-enasa 2 of 11, nushara-bayou 2 of 11, banujha-basin 3 of 15,
valley-of-storms 3 of 14, okuwun-rahei 6 of 22, cape-percar 6 of 17, murkwood 5 of 13 (1 true kit mod). Strongest: benthic-yobesh 9/10, tulmek-washes 13/24.

Fewest distinct sources and weakest lore fit (my reading of the above): tribal camp, farm, mine, outpost, shipwreck, Kothringi ruin, and every
Argonian "people" village outside KotM's core. For the non-Argonian kinds (velothi, imperial) borrowing foreign kits is correct by lore.

### A3. What the lore calls for against what any held mod models (catalogue, plugin by plugin)

Held Argonian-style models (non-creature statics/furniture/containers): KotM 2,691 bases (`argonia/blackwood` 191 incl. docks, boats, cranes, round huts,
houses; `argonia/xanmeer` 210; `argonia/ayleidruins` 141; `argonia/clutter` 99; `argonia/furniture` 86; `argonia/stockades` 56; `argonia/mudhuts` 46 incl.
3 mud huts, shed, pods, doors, windows, docks; 5 egg meshes); Cipactli 508 (`architecture/ruins` 113 xanmeer; `architecture/villages` 34 incl. 2 bamboo
huts + interiors, wicker chair/sofa/table/basket, orc-style awnings, Kothringi stilt platform, swamp house, shiveringcamp, dock planks; 12+4 banner types; 3 totems +
4 skeleton totems); XanmeerResources 79 (bed_covered, benches, brazier, bookshelves, pots); ArgonianLakeHouse.esl 67 (`argoniannest`: 2 tents, totem, bone chimes,
4 lantern types, drum, platforms, wall hangings, pottery, fish rack, chitin chair, woven chair/table/fence, snake fence, sithis shrine, mud hut, thatch roofing);
BM&V own 431+283 (mostly trees; `01arghouse` is Phitt `architecture/phitt/stronghold/dwelling.nif`, mud mound is Telvanni `tel_ext_cap_03`, `01mosspost`
is a BYOH Nordic tower post, 2 hammocks); Valenwood.esp 788 (Bosmer/Ayleid). Mud Mother Grove (146557) is a dependency row but no plugin of that name is in the
catalogue, so what it contributes is not verified.

Lore building types against models:

| lore need (material-culture.md) | model held? | verdict |
|---|---|---|
| mud hut (Shadowfen) | KotM mudhut01-03, shed, pods; LakeHouse mudhut01 | present, only ~6 distinct bodies |
| reed-woven stilt house (Murkmire) | KotM thatchhouse01-03, roundhut, Cipactli bamboohut01/02, stilthouseplatform; BM&V stilthouseext | thin: no woven wall/roof panels, one thatch roof piece |
| grown-root house (`settlement-root-v1`, interior: Helstrom basin, Middle Argonia) | none. Only Hist roots/ramps (KotM `hist_root`, deadroot x6, Cipactli histroots x6) | GAP, and 19 of 165 culture places are the forest-green Root-Folk of Helstrom |
| xanmeer pyramid | KotM xanmeer exterior (4 `1mjyaztecbuilding`), Cipactli ruins 113, Xanmeer Resources | present |
| Hist shrine/sap pool | trees (Skyfall), roots, KotM shrine01/wayshrine01, argonian_statue01, snakestatue01 | present, small |
| egg/hatching | 5 egg meshes, nests, clutches | eggs yes; no hatching-pool structure |
| Teeba-Enoo ball court | none (catalogue search "ball"/"court" returns only ballista and a castle courtyard) | GAP (rare place) |
| grave-stakes (Naga-Kur deeps signature) | none; lore says so itself (material-culture.md:334) | GAP |
| fish weir / fish trap / net rack | none (search "weir" 0, "fishtrap" 0; only HearthFires `byohfishnet01/02`, CC fishing gear, vanilla fishrack01/02) | GAP, and Reed-Sill Weir and Teel-Fen Weir are Act I places |
| dugout canoe / twin-hull platform canoe / raft (lore boat kit) | none (canoe 0, pirogue 0, raft only workbenches); KotM boat01-03 and shiprowboat01, vanilla row/jolly boats | GAP |
| reed mat / hammock / bedroll | BM&V 2 hammocks; KotM bedsingle01, beddouble01, rusticbed(double), bedroll01/bedrollhay01 are the VANILLA bedroll model; Xanmeer bed_covered | no sleeping mat in any mod |
| totems (lore: "everywhere") | 4 skeleton totems + 3 totem + 1 argoniantotem01 | thin (about 8 models) |
| chimes (root kit signature), xeech'ki seed dolls, turtle platters, frog pipes | chimes: KotM tamwindchime01, LakeHouse 2 bone chimes; dolls: KotM doll_turtle, doll_spriggan etc.; the rest none | partial |

## B. The pieces: what is placed, and how Skyrim-looking

Counts: drafted = the six drafted places (3,538 placed refs; 2,843 excluding trees/plants/FX; 326 refs are not in the catalogue, mostly one Skyrim.esm base `0B735D` x222, unresolved).
src54 = 54 mined source bundles (181,470 refs): a sample of the 281 source places (449,712 refs total in `source_place.refs`; per-base counts exist only for the 54).
The catalogue `nordic` flag is name-based (words Nordic/Whiterun/snow/...), so it MISSES vanilla-looking furniture, bedrolls, barrels and lanterns: it flags 202 of 2,843 drafted refs (7%) and 21,277 of 181,470 src54 refs (12%).
Tropical Skyrim swaps nothing in this list: its plugin holds 87 bases, all trees, grass and 2 effects (`Tropical Skyrim.esp` in the catalogue), so no furniture, tent, clutter or sign is retextured by it.
No other held mod re-meshes these either (checked catalogue: no ArmoredReplacer-style plugin; asset replacers are loose files and not visible to the catalogue; unverified for loose files).

Drafted places, source of non-plant refs: Argonian-kit mod 670 (24%), vanilla/DLC/CC 648 (23%), BM&V/other 1,525 (54%, Helstrom).

Most-placed non-plant objects in the drafted places (refs): Skyrim `CandleLanternWithCandle01` 173; Skyrim `RuinsSconceRopeShort` 88; KotM Saxhleel woven fence 58+16; BM&V `01mosspost` (Nordic tower-post model) 47;
**BM&V `01loaddoorArg` = Nordic ruin carved door 41**; KotM dock end 40; Skyrim `Bedroll01F` 22+5; Skyrim Solitude `SHouseDoor02` 15; Skyrim dock `DockStrSol01` 24; Markarth dock bridge 14; KotM thatch/mud/shack doors 52.
Doors: 56 of 119 drafted doors (47%) are Nordic-ruin or Solitude doors (the Nordic ruin door alone is 35% and all in Helstrom). nordic_review.jsonl already marks both as `nordic`.

Families (drafted refs / src54 refs; examples; what is Skyrim-looking):

| family | drafted | src54 | what | read as |
|---|---|---|---|---|
| bedroll with furs | 27 (28% of 97 drafted furniture refs; outposts 3+6+12, camp 3, Jal-Veesa 2, Helstrom 1) | 139 (75 vanilla, 28 KotM copy, 11+8 hay) | `furniture/bedroll/bedroll01.nif` | Skyrim: fur-and-hide roll. Used by the prison/worker marker rules too (place-studio.md:1493) |
| beds | 3 KotM rusticbed | 539 (commonbed01 167, KotM bedsingle01 95, commonbeddouble01 43) | | common = Nordic; KotM bed = rustic wood, neutral |
| tents | 32 (KotM scaletent x10, BM&V velothi extentrance x9) | 312 (smallnordictent01 45 flagged Nordic, smallimperialtent 59, Raven Rock Redoran tent 36) | | hide/canvas tents are Skyrim; scale tents exist (KotM, LakeHouse): a swap, not new art |
| pelts/rugs | 10 (peltfloor01-03 only 3) | peltfloor02 196, rug03 194, Dunmer urns 853 (dlc2darkelfurn01 x853: Baan Malur 300 + Dragonborn 553) | | fur pelts Skyrim; Dunmer urns are not Argonian |
| barrels/crates/sacks | 42 (barrel01/02 13; crates 16; sacks 8) | barrels 5,201 (barrel02 1,959, barrel01 1,582, mead 297), crates 4,084, sacks 991, baskets 1,790, hay 1,576 | | generic medieval; the largest bulk family (about 14,000 refs, 8%) |
| hay bales/straw | 0 | 1,576 (hayscatter, haybale 204, haymound) | Nordic farm | flagged Nordic in part |
| lanterns/candles | 173 candle-lantern (5% of all refs) | 833 candle-lanterns, 583 imperial candles | Skyrim common lantern | Skyrim; LakeHouse argonianlanterns01-04 and KotM TorchbugLantern exist: swap |
| braziers/fire pits | 7 KotM xanmeer braziers, 17 fx fire | 566 braziers (KotM xanmeer 278, Imperial 86), 831 fire effects | | KotM braziers fine; Imperial braziers not |
| forge/grindstone/anvil | 9 | few hundred true (regex noise from "anvil palm") | | Skyrim |
| market stalls/awnings | 5 BM&V market stands | 160 (Baan Malur overhang 55, Skyrim 19 flagged) | | BM&V's stand fine |
| signs | 1 (Whiterun alchemy sign, in nordic_review as Nordic) | 207 (Baan Malur signpost 44, BM&V Aldredanyia 38, Nordic signs 56) | | |
| shrines of the Nine / Divine statues | 0 (a Mara statue was dropped, ledger) | 121 (Dibella statue 22, power-shrine circles 20 Nordic) | | Nine are foreign here; Hist shrine models exist |
| banners | 0 | 1,060 (Skuldafn 209, generic red 139, KotM xanmeer 86, Imperial) | | Xanmeer banners exist (KotM 86, Cipactli 8 variants) |
| mounted heads | 3 vurt-oak | 809 mixed (wall-mounted slaughterfish 84 and mudcrab 72 fit the marsh; elk/bear heads not isolated) | | |
| snow-bearing | 0 | 1,427 (0.8%) | all flagged Nordic | |
| horker/mammoth/antler | 1 | 456 (mostly human ribcage 161) | | little |
| dragon carvings | 1 cobraskull | 290 regex-noisy | | low |
| carts | 0 | 170 handcarts | | |
| fences/palisades | 164 (KotM woven/scaffold 116) | 2,525 (Skyrim stockade 558, KotM woven 126, Nordic woven 114) | | mostly KotM |
| wells | 0 | 9 Raven Rock Redoran | | |
| fish racks/nets | 28 (vanilla fishrack 10, CC fishing gear 13) | 248 | | vanilla rack generic |
| burial urns/coffins | 1 | 170 (commoncoffin01 34, noble coffin 34, ruins sarcophagus 14) | | Nordic tombs |
| weapon racks/mannequins | 0 | 425 | | Nordic/Imperial |
| dock/pier/boat | 103+27 (KotM docks 40+, boats 9, Skyrim DockStrSol 24, Markarth bridge 14) | boat: ship wood beams 1,220+ (Skyrim ship interiors) | | docks mixed |
| standing stones/totems | 1 | 23 | | |

nordic_review.jsonl (41 bases reviewed: 17 nordic, 24 neutral) is a review of what the drafts tripped over, not a census. Its 17 Nordic verdicts: High Hrothgar fire pit,
Nordic-ruin doors (2) and chair, Solitude doors/planters/temple walls (5), Whiterun sign, Nord hero greatsword, Windhelm fireplace, Sovngarde candlestick, Markarth throne.
It judges "BM&V gives it no texture set of its own" for the ruin door: BM&V reuses vanilla Nordic models raw in its own Argonian town.
Owner rulings on this (owner-rulings.md): 2026-11-20 Nordic pieces fine, Tropical version or easy swap; 2026-11-10 pieces from a source's own mods or Tropical Skyrim accepted; interiors may be Nordic.
Grep of owner-rulings.md for "bedroll", "hammock", "fur", "tent": only mechanical lines (place-studio selects a tent with its bedrolls as one unit); no ruling on look.

## C. Argonian/Black Marsh pieces we hold, by family (catalogue, statics/furniture/containers/activators)

| family | held | where |
|---|---|---|
| Hist trees, roots, ramps | 60+ roots/ramps, plus Skyfall tree set (23) | KotM, Cipactli, Skyfall |
| xanmeer ruins, pillars, braziers, banners, statues, murals | 500+ | KotM 210+141 ayleid, Cipactli 113, Xanmeer Resources 79 |
| mud huts/shed/pods/doors/windows | about 40 | KotM mudhuts 46, LakeHouse |
| thatch/stilt/bamboo houses | about 15 | KotM thatchhouse01-03, roundhut, Cipactli bamboohut, stilt platform, swamp house |
| docks/boats/cranes/stockades | about 150 | KotM blackwood 191, stockades 56, Cipactli Kothringi docks |
| furniture | about 80: rustic table/chair/bench/bed/chest/shelf/cupboard (KotM 34), wicker (Cipactli 4), woven (LakeHouse 3), xanmeer furniture 18 | |
| clutter | KotM 71 (tents x3, fences, tapestries x2, hanging feathers x3, bunting, spinning wheel, tokens, dolls, firewood piles, incense burner); Cipactli 85 (ingredients, banners, leopard pelts, clams); LakeHouse 57 | |
| eggs/nests | 5 + clutches | KotM |
| totems/chimes/drums/shrines | about 8 + 5 + 2 + 6 | |
| food/ingredients/weapons/armour | many (KotM, Cipactli, six weapon mods) | |
| pottery/baskets | KotM basketcontainer, saxhleelmetalpot, LakeHouse pottery 5, Cipactli wicker | about 20 |
| lanterns/lights | LakeHouse 4, KotM TorchbugLantern, hanging Hist lanterns (Dunmer lantern with rope) | about 8 |

The gap list is the difference between section A3's lore list and this table. Most striking: the Argonian set is rich in buildings of two kits and in Xanmeer ruin, thin in domestic and working
clutter and in anything that is neither wood nor stone: no mat, hammock, canoe, weir, net rack, stake, ball court, root-grown house.

## D. Step 2: Nexus (mods/dependencies.json rows excluded; the 193 held mods were checked for overlap)

The Nexus name-wildcard search is substring-noisy and found no Argonian or tropical-native building kit. Candidates by gap (id, author, endorsements, remarks):

| gap | candidate | permission/notes |
|---|---|---|
| hammock | Tcz Modders Resources 65061 (Tcz, file `tcz_uvremap_hammockstatic_darkelf`, 15 KB): a Telvanni/Phitt hammock static remapped to vanilla Dark Elf textures | a static: needs a furniture marker; Dunmer look; resource, credit |
| bedroll replacers (all Skyrim-fur type) | Bedroll Alternative 132480 sothasimp 7,629; Fluffy Beds and Bedrolls 93201 FrankBlack 2,097; Fur Bedroll 13354; Simple Bedroll 17283 | all swap the SAME vanilla bedroll with a nicer fur bedroll; do not make it Argonian. A replacer changes vanilla Skyrim too: fine for us |
| Dunmer bedrolls and tents | Ash Nomad 184382 sothasimp 618 (+ LessPoly 186127) | Dunmer ash-waste look: fits Dunmer outposts, not Argonian |
| tent overhaul | Kaidan Exterior Tent Overhaul 154480 Cizzy 5,765 | uses Oaristys/Lorsakyamuni/Tesak1243 resources; not Argonian |
| stilt house | Stroti's Stilt House Resource (Nexus LE 61824, Stroti/Tamira; SSE conversion not verified; its page allows use with credit) | one generic Oblivion stilt house, would need reed retexture |
| bamboo huts | Assorted Resources for Skyrim SE 4491 Tamira 172 (huts assembled from orc kit, straw/wicker roof, bamboo sides) | modder's resource; Cipactli already has bamboo huts |
| tree house | Stroti's Treehouse Resource 2378 (186); Stroti Resource Pack I/II 4559/4679 (BM&V already uses Stroti mushroom house) | credit; relevant to root-kit look only as a base |
| docks/boardwalks | Skyrim 3D Docks and Boardwalks 28781 mathy79 6,400 (+ weathered Riften textures) | replacer of vanilla docks: better planks, still Nordic shapes |
| Morrowind-style props | Phitt's Morrowind Resources Remapped SSE 107571 (pancake, 49); Phitt's Morrowind Style Lanterns 4736 (Phitt/Tamira); Phitt's Sheogorad Shack Texture Remapped 34458 | free with credit; Dunmer/Sheogorad. BM&V already draws on Phitt |
| Argonian homes (meshes only as player homes) | Xalfek 55595 DexMods 309; Darkwater Den 189608 Elianora 51; Roots of the Tree (Hist-themed home) 62422 Nateguy 42; Argonian Hut 59517 luposcainus (a 36 KB tree base, tiny); Tuktura houseboat 58753 (needs CC Fishing) | no resource licence; homes, not kits; Xalfek is 36 MB and could hold Argonian clutter meshes (unverified) |
| ESO Argonian/Murkmire furnishings | none ported; Elder Scrolls Online Imports 11729 (Sarthes Arai, 3,324) is a quest/ruin port (CC Ayleid resources derive from it) and its BOS add-on 141484 Lumendea | confirmed by search; ESO Argonian mat/reed furniture are only on UESP |
| Dunmer furniture | Rally's Dark Elf Furniture 112042; Weathered Dark Elf Furniture 84732; Dunmeri Furniture in Gray Quarter 60077 | fits Dunmer outposts only |
| orc furniture | Rally's Orc Furniture 111457; Malacath's Chosen 133717 sothasimp 7,427 | not Argonian |
| barrels/crates/baskets | HFs Barrels All-in-One 137509; Awesome HD Barrels 20698; Rally's Crates 80417; TB's HD Wicker Basket 133863 (5,589); Skyland Crates and Barrels 88573 | all HD replacers of the vanilla shape. A retexture/mesh replacer changes vanilla too; fine, but yields "better Nordic", not Argonian |
| clay/pottery | Ancient Pottery 24039 mathy79; HFs Glazed Pottery 152278; Halffaces Nordic Ruins Pottery 115926 | same: vanilla shapes |
| pelts | Better Pelts and Hides 87277, Peltapalooza 5442 (32,464), Fluffy Hanging and Floor Pelts 103120 | better fur, still fur; the Argonian answer is to remove pelts, not improve them |
| fish racks | Diverse Catches BOS 98989 FrankBlack 7,962 (12 variants); Fish Rack 54144 | BOS swap of vanilla fishrack01 |
| hay | Rudy HQ Hay 25125 (8,850); Real Hay Redux 41473; Mihail Haystacks 125021 | vanilla shape |
| shrines | JS Shrines of the Divines 33394 | Nine again: wrong |
| totems | Easthold Totemic Set 100401 (armour/clothes, not a static; unverified); Totemic Tombstones clutter remesh 157281 | no Argonian totem resource found |
| market stalls | Rally's Market Stalls Animated 81282; Improved Market Stall Canvas 37294 | vanilla look |
| lanterns | Lanterns of Skyrim 2429 (MannyGT, 53,208); Lanterns of Skyrim II 30817; Phitt lanterns 4736 | Skyrim/Morrowind lantern sets; Argonian ones are in LakeHouse only |
| jungle/tropical kits | none beyond Project Rainforest 20636 (land), TSOP 36153, Lagoon 37394 (island home) | no building kit |
| creators checked | Stroti/Tamira (resource packs listed above), Oaristys Witcher pack 137706, Mihail Shards of Immersion (Whale Bones on Coasts 91958, Beehive 79344, Haystacks 125021), Jokerine 801, Blary Booksets 159303 | Blary, Lolicept, Berticus, LorSakyamuni, Runspect, Elianora (homes only): nothing Argonian found by name search; Nexus search is name-only so mod text was not searched |

Result: no held or Nexus mod supplies a reed/woven sleeping mat, Argonian-themed barrel/crate set, canoe, weir, net rack, grave-stake, ball court or root-grown house. Replacers
that exist improve vanilla Nordic shapes only. Not verified: mod bodies were not read for loose clutter inside the player-home mods; Khmer, tiki, Polynesian, stilt, hammock name searches returned 0.

## E. Step 3: our own models, and the route for each (nothing here is made; sizes are estimates)

Route key: R1 = keep the vanilla record, furniture markers and collision, swap only geometry/texture (the markers sit in the NIF as the furniture-marker node, so Blender/Tripo geometry must
be merged under the vanilla file's marker node: engine-format knowledge, not verified here); R2 = plain retexture of an existing vanilla mesh (loose texture replacer, no geometry: cheapest);
R3 = new static base record with a collision shape; R4 = new record plus markers/animation (hardest).

| # | object | where seen, how often | size | solid/static | needs | route | difficulty |
|---|---|---|---|---|---|---|---|
| 1 | reed sleeping mat / hammock (replaces Bedroll01 look) | every camp, outpost, tent, prison cell; 27 of 97 drafted furniture refs, 139+ in src54 | 1 x 2 m | solid; flat | furniture marker node (rest), collision | R1 (vanilla FURN and markers kept) | easy: single flat object, texture is a woven pattern |
| 2 | clay pot / wicker basket / hollow-log barrel (replace barrel01/02, sacks, crates) | everywhere: 3,541 vanilla barrels, 4,084 crates, 1,790 baskets in src54 (about 10% of source refs) | 0.5-1 m | solid | container records keep; collision | R2 first (retexture barrel to dark wood and wet clay), R1 for a gourd/pot shape | easy |
| 3 | woven reed fence/screen panel and reed door mat | huts, fish camps | 2 m | solid | collision | R3 | easy (but KotM woven fences exist: check first) |
| 4 | Argonian door set (re-skin 41 Nordic ruin doors and Solitude doors in BM&V sources) | Helstrom: 56 of 119 doors | 1 x 2 m | the door record has an animation (open/close) | R1 keeps record and animation graph, new geometry on same rig; or just swap records to KotM mud/bamboo doors (no art) | | easy as swap; medium as new rigged door |
| 5 | totem, grave-stake, bone chime, seed doll (xeech'ki), turtle platter, frog-pipe | every village, every grave (lore: everywhere) | 0.3-3 m | solid | none | R3 | easy (skull totem exists: 8 models only) |
| 6 | fish weir, fish trap basket, net drying rack, fish smoking rack | Reed-Sill Weir, Teel-Fen Weir, every fishing camp and dock | 2-6 m | solid; weir sits in water | collision, water interaction only visual | R3 | easy to medium (weir needs water-line fit) |
| 7 | dugout canoe and platform canoe, moored | docks, creeks, stilt towns | 4-6 m | solid, no moving part | static only | R3 | easy as static; do not make rideable |
| 8 | reed/hide Argonian tent with scale or reed cover (outposts, war camps) | camps: 312 tents in src54; scale tents exist (KotM 3, LakeHouse 2) | hut size | solid | entrance collision | R3 | medium; first try swaps to KotM/LakeHouse tents |
| 9 | reed-thatch house wall/roof panels (stilt kit pieces) | Murkmire coast villages | house sized | solid | collision | R3 | medium to hard: big surfaces, one texture stretched thin |
| 10 | hist-root grown house (root-kit kit) | Helstrom basin, Middle Argonia: 19 forest-green places | house sized | | stairs, doors, collision | R3 | hard: a whole kit and walk-in interiors |
| 11 | Teeba-Enoo ball court | 1-3 places | 40 m | solid | | R3 | medium, rare: skip |
| 12 | Nine shrine/statue replacement (Hist shrine, snake statue) | any foreign source with shrines | 1-2 m | | | R3 or swap to KotM shrine01/wayshrine01 (held) | easy as swap |
| 13 | lantern (re-skin CandleLanternWithCandle01, 173 drafted refs; 833 src54) | every interior and street | 0.3 m | solid light | light record keep | R2 or swap to LakeHouse argonianlanterns (held) | easy |

## F. Step 4: rank by player impact per unit of difficulty

1. Swap, no art: lanterns (13), doors (4 as swap), banners, shrines (12), tents (8 as swap), fences. Held Argonian models already exist; the gain is by record swaps. 173 + 56 + ... refs in the six drafts, 833+ in the 54 sources. Highest impact per effort; not an art question.
2. Barrel/crate/sack/basket retexture (2, R2): the biggest single bulk family (about 14,000 refs, 8% of the source sample), seen close up in every dwelling; easy.
3. Sleeping mat / hammock (1, R1): the most-placed furniture in the drafts (27 of 97), the object the player uses to rest at; Skyrim-fur bedroll is the strongest Nordic tell at close range; easy.
4. Signature small props (5): totem, grave-stake, chime, seed doll: low count each, very high distinctiveness; the lore says "everywhere" and gives grave-stakes no mesh at all; easy.
5. Fish weir / net rack (6): two Act I places and every fishing camp; distinctive; easy-medium.
6. Canoe (7), woven reed screen (3): moderate breadth, easy statics.
7. Thatch/stilt wall and roof (9), tent (8 as new), then root house (10): large surfaces, hard; weigh only after 1 to 6 land.
8. Ball court (11): rare; skip.

## Recommendations (beyond the brief; evidence cited)

- Treat record swaps (lantern, door, banner, shrine, tent) as a first, art-free tranche: the held mods hold Argonian equivalents (catalogue lists above). Evidence: A3, B tables.
- Add a measured "Nordic tell" count that does not rely on the name regex: the catalogue flag misses bedrolls, barrels, lanterns (tool: `tools/places/assets/catalogue.py:46`).
- Keep section C's gap list in `story/lore/topics/material-culture.md` and remove the dangling "asset inventory gap 3" reference there (it leads nowhere).
- Before any generated sleeping mat, check whether KotM's `bedroll01` copy has a distinct model (28 refs in src54 point at a KotM record with the vanilla model path): a first, free test of R1.

Covered: newworld/world.sqlite, source_match, places/*, out/places/catalogue + bundles, mods/dependencies.json, owner-rulings, material-culture.md, Nexus API (about 120 term searches, 30 mod pages), 6 web searches · Skipped: 227 non-bundled sources' per-base counts (no ref files); loose-file replacers (invisible to the catalogue); mod bodies and archives (no downloads); hist-placement.md body (read headings only); decision 0006 text.
