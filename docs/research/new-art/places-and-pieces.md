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
| reed mat / hammock / bedroll | 4 hammock statics (BM&V `01hammock`, `01hammockDUPLICATE001`; Baan Malur `SOMRHammock`, `SOMRHammockLegs`), no furniture record; KotM bedsingle01, beddouble01, rusticbed(double), bedroll01/bedrollhay01 are the VANILLA bedroll model; Xanmeer bed_covered | no reed sleeping mat in any held mod |
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

## D. Nexus, searched in both Nexus games, by name and by description

What was searched (python3 tooling/nexus_search.py after the 2026-11-24 fix: Special Edition and the 2011 game, mod names and description text, most endorsed first): hammock, sleeping mat, bedroll,
reed, bamboo, thatch, stilt, hut, tiki, jungle, tropical, swamp, tribal, Polynesian, Aztec, Mayan, Khmer, wicker, basket, pottery, clay, gourd, fish trap, weir, net, canoe, dugout, drying rack,
totem, grave, stake, lantern, tent, market stall, Argonian, Saxhleel, Black Marsh, primitive, village kit, hut kit, native huts, boardwalk, dock resource, fishing resource, "modders resource",
"clutter resource", "furniture resource", "architecture resource", and the authors Phitt, Kelretu, Elinen, Ztree, Vurt, Berticus, Lolicept, Runspect, Lorsakyamuni, Sheogorad, Telvanni, Morrowind resource.
Hits were read in the "Modders Resources" category (all terms) and unfiltered for Polynesian, Khmer, Mayan, weir, canoe, dugout, drying rack, fish trap, totem, market stall; then candidate descriptions were read
with --mod or the API description. Description hits are noisy (guides and player homes), so a zero below means zero relevant summaries among the hits read, not that nothing exists.
A mod marked "2011" (`skyrim:` id) is usable only if its meshes are converted to Special Edition format (NifSkope/optimiser pass); marked "SE" it is already in that format.
All are used here as asset-only player dependencies, so a resource licence is not needed, but the permission line is noted.

### D1. Gaps Nexus now fills (or partly fills)

| gap | candidate (id, author, endorsements) | what it holds (from its description) | format | permission line |
|---|---|---|---|---|
| hammock (static) | already held: BM&V North `01hammock` (`architecture/phitt/dagonfel/hammock.nif`), BM&V `01hammockDUPLICATE001`, Journey to Baan Malur `SOMRHammock` and `SOMRHammockLegs` (Tcz remap) | catalogue, four hammock statics; no FURN record for them, so it still needs a furniture marker | in load order | n/a |
| hammocks, baskets, fishing net with herrings, tapestries, rug, 5 shacks, dock kit, 2 awnings, 5 overhangs | skyrim:60125 Phitt's Sheogorad Resource Part Two (Phitt and Tamira, 435) | the same Phitt/Sheogorad set Baan Malur already carries under `morrowind/sheogorad/` | 2011, convert | "may not be used in paid mods"; credit; read the included Sheogorad Terms of Use |
| yurt-type Ashlander huts with interiors, paper lanterns, plants, rocks, mushrooms | skyrim:59632 Phitt's Sheogorad Resource Part One (466) | BM&V already holds `vvardenfell/ashlanderhut/*` (incl. `001Swamptent`) | 2011, convert | same |
| wicker furniture | skyrim:66282 Wicker Set (Garnet, 398) | wicker chair, sofa, table, animated chest, Morrowind-style basket | 2011, convert | free to use the resources, credit appreciated, do not redistribute changed |
| bamboo huts and interiors and doors, animated wind chimes | 4491 (SE) / skyrim:57394 Assorted Resources (Tamira, 172 / 468) | huts assembled from the orc hut kit with straw/wicker roof and bamboo sides; moving wind chimes with sound; made "for tropical/desert/caribbean surroundings" | SE | "none of these resources may be used in paid mods" |
| bamboo trunk | skyrim:14812 Bamboo modders resource (Scot, 131) | one trunk; trees already held (KotM `bamboo01/02`, Cipactli) | 2011 | do not put on Steam Workshop |
| tiki torch | skyrim:24711 Tiki Torch Modders Resource Pack (Teirdalin, 65) | tiki torches and a "Tiki Dog" torch, merged from vanilla parts (no new textures) | 2011, convert | free, credit |
| stilt house | skyrim:61824 Stroti's Stilt House Resource (Stroti and Tamira, 270) | stilt house with animated folding-shutter door, grill, hut and platform split | 2011, convert | "not in paid mods" |
| rustic furniture | skyrim:24450 Strotis Rustic Furniture Resource (383) | rustic furniture set (list not read) | 2011, convert | same family terms |
| tents | skyrim:12104 Meos Tents for All (Meo, 204); skyrim:82985 Kelretu's Modders Resources (433, Nordic tent variations, ropes, small chests, farmhouse line, ovens) | recoloured Imperial-type tents | 2011, convert | credit; do not port to other games; Kelretu "as open as possible" |
| docks | skyrim:63982 tamu75 Wood Dock Resources (94) | 3 docks, 7 planks, pole | 2011 | credit; already in KotM (`tamu_wooddock*`), so held |
| docks and farmhouse kits | skyrim:58262 Building kits and other items (Elianora, 596) | 383 meshes: farmhouse kit 235 parts, modular dock kit, upgraded upper-class bed with mattress | 2011, convert | credit with a link on the mod page, or removal |
| ships and boats | 41653 Ships and boats of Tamriel (SE, ThatShipGuy, 829); skyrim:75965 DK's Lore-Friendly Ships Vol.1 Nords | resource sets with interiors, rowboats and barges (Imperial, Bretic, Nord) | SE / 2011 | credit; none is a dugout or platform canoe |
| canoe | 40057 Sailboats Script Free Sailing EXPANDED (SE, Araanim and others, 191); skyrim:67727 Script free ship sailing (ElstarTomas, 941) | the 2011 mod advertises a canoe model; the SE expanded mod adds rowboats and sailboats (canoe in SE not confirmed) | SE / 2011 | mod page terms not read |
| tropical assets | 33446 Tropical Lands Assets, Cathnoquey (SE, CreatyChameleon, 43) | 440 MB asset dump of a Padomaic tropical-isles project made by over 150 volunteers; page does not list its contents | SE | free to use any asset, textures and sounds, credit requested; files starting `s3d` removed (not resources). Strongest unknown: needs one look inside the archive |
| big warehouses | 83445 Mad Modder's Assets (SE, ManyMadModders, 160) | thousands of meshes: wall mounts, trophies, furniture, outdoor decor, tents, market stalls, containers (categories only) | SE | per-asset credits; contents not itemised |
| pots, jars, baskets, food containers | skyrim:16525 Oaristys and Tony67 Modder's Resource Pack (2,637, ~500 meshes: pottery, ingredient jars, food baskets, platters); skyrim:53022 Jokerine's Misc Resources (602); skyrim:14133 Blary FoodContainer (982: 6 vegetable baskets, 5 food crates, hanging meat); skyrim:53192 Elianora's Extra Resources (1,275: retextured furniture, coloured baskets) | statics for pottery, baskets, crates in vanilla styles | 2011, convert | free to use with credit |
| lanterns | skyrim:59977 / 4736 Phitt's Morrowind Style Lanterns (275 / 104); skyrim:59632 paper lanterns | Morrowind-style movable and static lanterns | 2011 / SE | not in paid mods |
| flora and trees (not a gap) | skyrim:19268 GKB Green Trees (910); skyrim:22018 Tamira New Plants; skyrim:38651 Hoddminir | jungle, cypress and cedar trees; palms; tropical shrubs | 2011 | Tropical Skyrim already carries GKB trees |

### D2. Searched, no relevant candidate in the hits read

Polynesian (3 hits: a bird mod, an NPC mod), Khmer (2 hits, none relevant), Mayan (11, only King of the Murkmire, Cipactli and a Markarth retexture), Aztec (23; one unrelated resource pack),
weir (20, no relevant), dugout (2; campsite mods only), drying rack (14, none relevant), fish trap (60, none relevant), grave (160 hits read by category only: none relevant), stake (69, none), net (166, none relevant),
totem (106; only werewolf-totem retextures, a Nord religion mod, Nord totemic armour), gourd (87; plant and food retextures), market stall (106; stall retextures and a vendor mod, all vanilla shapes),
Argonian (163) and Saxhleel (57) and Black Marsh (88): races, skins, weapons, armour, player homes (Xalfek 55595, Darkwater Den 189608, Roots of the Tree 62422), no building or clutter kit.
Replacers of vanilla shapes (Nexus names above in the first draft: HFs Barrels 137509, Rally's Crates 80417, Better Pelts and Hides 87277, Bedroll Alternative 132480, Diverse Catches 98989) change vanilla Skyrim province-wide, which is fine for us,
but they make the Nordic shape nicer, not Argonian. Not verified: Cathnoquey's contents, Mad Modder's Assets' contents, Lolicept Resources (description gives no list), Kelretu's full list, Stroti Rustic Furniture's list;
the SE bodies of no 2011 mod were checked for existing SE conversions beyond those listed.

### D3. Net effect on the gap list of A3

- Hammock: not a gap in assets (4 statics held); the gap is a usable furniture record (static plus marker) and an Argonian cover.
- Bamboo/thatch hut, wicker furniture, wind chimes, tiki torch, tents, docks, baskets and pots: obtainable by conversion, mostly duplicating what BM&V, Cipactli and Baan Malur already hold.
- Still unfilled by any search above: reed sleeping mat as an Argonian object, grown-root house, fish weir/trap/net rack, grave-stake, ball court, dugout or platform canoe (only a possible canoe in 67727), Hist-themed totems beyond the 8 held, woven reed wall/roof panels.
- One unopened lead could change this: Cathnoquey Tropical Assets (33446).

## E. What remains for our own models (after D), and the route for each

Route key: R1 = keep the vanilla record, furniture markers and collision, swap only geometry/texture (markers live inside the NIF as a furniture-marker node, so new geometry must be merged under the vanilla
file's marker node: format knowledge, not verified here); R2 = plain retexture of an existing vanilla mesh (a loose texture replacer, cheapest); R3 = new static base record with a collision shape; R4 = record plus markers/animation.
"First try" lists the held or Nexus item to use before making anything.

| # | object | where seen, how often | size | static | needs | first try | route | difficulty |
|---|---|---|---|---|---|---|---|---|
| 1 | reed sleeping mat (Argonian cover over the hammock/bedroll) | camps, outposts, tents, prison cells: 27 of 97 drafted furniture refs, 139 bedrolls and 539 beds in src54 | 1 x 2 m | solid, flat | furniture marker node, collision | the four held hammock statics plus a vanilla bedroll marker | R1 | easy |
| 2 | clay pot / wicker basket / hollow-log barrel look (replace barrel01/02, crates, sacks) | 3,541 vanilla barrels, 4,084 crates, 1,790 baskets in src54 | 0.5-1 m | solid | container records kept | Wicker Set, Oaristys/Blary/Jokerine statics (convert) for the wicker and clay forms; a barrel retexture is R2 | R2 first, R1 for new shapes | easy |
| 3 | grave-stake, totem, bone chime, seed doll (xeech'ki), turtle platter | every village and grave; lore says "everywhere", grave-stakes have no mesh (material-culture.md:334) | 0.3-3 m | solid | none | held skull totems, bone chimes, doll_turtle; Tamira wind chimes | R3 | easy |
| 4 | fish weir, fish trap basket, net drying rack, smoking rack | Reed-Sill Weir, Teel-Fen Weir, every fishing camp and dock | 2-6 m | solid; weir at the water line | collision | Phitt's net with herrings (Part Two) for a rack; nothing for a weir | R3 | easy to medium |
| 5 | dugout and platform canoe (moored statics) | docks, creeks, stilt towns | 4-6 m | solid | static only | 67727's canoe (verify), KotM boat01-03 | R3 | easy as static |
| 6 | woven reed screen / mat panel and reed door curtain | huts, fish camps | 2 m | solid | collision | KotM woven fences, Cipactli bamboo hut walls | R3 | easy |
| 7 | woven reed-thatch wall and roof panels (stilt kit pieces) | Murkmire coast villages | house size | solid | collision | Cipactli bamboo huts, Tamira/Stroti stilt house, KotM thatch houses | R3 | medium to hard: large surface, stretched texture |
| 8 | scale/reed Argonian tent | outposts and war camps: 312 tents in src54 | hut size | solid | entrance collision | held KotM scaletent01-03, LakeHouse argoniantent01-02 | R3 | medium (usually a record swap) |
| 9 | grown-root house (settlement-root-v1) | Helstrom basin, Middle Argonia: 19 forest-green places | house size | solid | stairs, doors, collision | none | R3 | hard |
| 10 | Teeba-Enoo ball court | 1-3 places | 40 m | solid | none | none | R3 | medium, rare: skip |
| 11 | Argonian door (replace 41 Nordic-ruin and 15 Solitude doors in Helstrom) | 56 of 119 drafted doors | 1 x 2 m | animated open/close | door record and rig | KotM mud/shack doors and Cipactli bamboo hut door (held, no art) | R1 only if a new look is wanted | easy as swap |

## F. Ranking by player impact per unit of difficulty

1. Record swaps to held models (lanterns 173 refs in the drafts and 833 in src54, doors, banners, shrines, tents, fences): no art, large and immediate. Not an art question.
2. Conversions of 2011 resources that duplicate held kit: low value, since BM&V, Cipactli and Baan Malur already hold the same bamboo huts, hammocks, Phitt props and wicker; take only a missing piece (tiki torch, wicker chest).
3. Barrel/crate/basket retexture or swap (#2): the largest bulk family (about 14,000 source refs, 8%), seen close up in every dwelling; easy.
4. Sleeping mat (#1): most-placed furniture in the drafts, the thing the player rests on; a held hammock static plus marker gets most of the way; easy.
5. Signature small props (#3): totem, grave-stake, chime, seed doll; few per place, high distinctiveness; easy.
6. Fish weir / net rack (#4): two Act I places and every fishing camp; easy to medium.
7. Canoe (#5) and woven screen (#6): moderate breadth; easy static.
8. Open Cathnoquey Tropical Assets (33446) once before starting items 9 and 10, since it may supply tropical huts and props.
9. Reed-thatch panels (#7), tents as new models (#8), then the grown-root house (#9): large surfaces, hard.
10. Ball court (#10): rare; skip.

## Recommendations (beyond the brief; evidence cited)

- Treat record swaps (lantern, door, banner, shrine, tent) as a first, art-free tranche: the held mods hold Argonian equivalents (catalogue lists above). Evidence: A3, B tables.
- Add a measured "Nordic tell" count that does not rely on the name regex: the catalogue flag misses bedrolls, barrels, lanterns (tool: `tools/places/assets/catalogue.py:46`).
- Keep section C's gap list in `story/lore/topics/material-culture.md` and remove the dangling "asset inventory gap 3" reference there (it leads nowhere).
- Before any generated sleeping mat, check whether KotM's `bedroll01` copy has a distinct model (28 refs in src54 point at a KotM record with the vanilla model path): a first, free test of R1.

Covered: newworld/world.sqlite, source_match, places/*, out/places/catalogue + bundles, mods/dependencies.json, owner-rulings, material-culture.md, Nexus API in both games (about 190 term searches, 45 mod descriptions), 6 web searches · Skipped: 227 non-bundled sources' per-base counts (no ref files); loose-file replacers (invisible to the catalogue); mod bodies and archives (no downloads); hist-placement.md body (read headings only); decision 0006 text.
