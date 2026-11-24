# New art: trees, plants, boats, ships, wrecks and natural pieces (call #93, research only)

Lane: TREES, PLANTS, BOATS, SHIPS, SHIPWRECKS, MISC natural pieces. Method of BRIEF-common.md (thin areas, Nexus, own
models, ranking). All counts are from `newworld/out/world.sqlite` (tables `flora_base`, `region_flora`, `habitat`,
`place`, `travel_*`, `place_source`) read 2026-11-24, and the committed sources named below.

## 0. Headline

1. The tree pool is NOT thin in species count (193 distinct tree-family models in the 20 land regions, 510 distinct
   meshes in the whole flora table, from four mods) but it is thin in LOOK per screen area, in four ways:
   (a) a few meshes carry a quarter to half of everything seen: ManFern 11.0 percent of source refs, one reed mesh
   7.4 percent (and it is the ONLY reed model), bracken 6.5, the gkb lily pad 3.8 percent;
   (b) eleven wet-marsh regions share the same marsh kit (nearest-neighbour weighted cosine 0.76 to 0.89);
   (c) the signature Black Marsh forms are held by very few models: 5 mangroves, 4 moss-cypress variants, 12 Hist bases;
   (d) the whole boat/ship side is the thinnest of all: no Argonian craft model exists in our pool; the one ship
   placed is BM&V's Imperial `01Ship`; 10 of 11 wrecks come from vanilla Icerunner (4) and Journey to Baan Malur's
   Ink Lagoon (6) (not verified what the latter looks like), 1 from Wyrmstooth.
2. Nexus has almost nothing swamp/jungle-specific that we do not already hold (searches in section 4). The best
   unclaimed finds: Ships and Boats of Tamriel (41653, resource, ships + wrecks), Wreck of the Crown Petone
   (17263, an Argonian-settled wreck), Waterplants (6092, reeds/lilies/water grass), Cathnoquey tropical asset dump
   (33446, "Fractured Isles" tropical assets), DrJacopo/TB ferns (82978/72888), Whale Bones on Coasts (91958).
   Nothing found for: canoe, dugout, raft, junk, dhow, banyan, mangrove prop roots, tree fern, cattail, rice.
3. Own-model priority (impact per difficulty): (1) mangrove prop-root clusters, (2) native-craft kit (dugout canoe,
   reed/log raft, twin-hull canoe, houseboat), (3) a second and third reed/sedge/cattail card set, (4) tree
   ferns/cycads (trunk generated, fronds reused), (5) giant fungus/Hist state variants (sick, dying, egg pod),
   (6) drowned/driftwood/stump set, (7) sunken/wreck hulls re-skinned or modelled low-poly. See section 6.
4. Cheapest wins need no new art: place KotM's Saltrice (held, never placed, section 2.3); use unused vanilla
   Dragonborn/Blackreach giant mushrooms; recolour sick-Hist variants by texture swap.

## 1. Live docs and which one to edit

- `docs/design/ecology.md` (habitats, harvestables), `docs/design/dressing.md` (signature things),
  `docs/design/lod.md`, `docs/design/travel-network.md` (boat stops), `story/lore/topics/material-culture.md:84-128,
  264-267` (boat kit brief). The material-culture boat kit brief refers to
  `docs/research/lore/marsh-watercraft-and-argonian-boats.md`, which does NOT exist in the repo (checked
  `ls docs/research/lore` and grep): the lore's own boat research is missing.
- CONFIRMED: ecology.md: "never a Nordic name" for the harvestable kinds (`harvestables.json` kinds); the
  filler pools (`pools`) are Black Marsh kinds only. CONTRADICTED: nothing. SUPERSEDED: the old dependency audit
  (`docs/research/mods/dependency-audit.md:216-249`) lists Sailable Ship, Skyrim Ferries, Rowboats, Sailboats
  Expanded, Ships and Boats of Tamriel as rows; none of them is a row now: `grep -i "sailable|sailboats|rowboats|
  ships-and-boats|skyrim-ferries|boats-operational" mods/dependencies.json` finds only the ConsoleUtil line
  (`mods/dependencies.json:352`), so the 193-row file holds no boat mod at all.
- The one doc to edit if the owner opens this: `docs/design/ecology.md` for flora (add a "what we model ourselves"
  list) and `story/lore/topics/material-culture.md` for craft; vessels have no design doc (travel-network.md covers
  stops only), so add a short "Vessels" section to travel-network.md rather than a new file.

## 2. Step 1: where the pool is thinnest (measured)

### 2.1 Trees: models, mods, regions

`flora_base`: 534 bases, 510 distinct meshes. By mod: King of the Murkmire (KoTM) 332, BM&V 168, Depths 21,
Tropical Skyrim (TS) 13. Source refs (a proxy for visual weight, not world refs): BM&V 63,012, TS 38,504, KoTM 16,654,
Depths 1,277 (total 119,447). Tree-ish families (17 families, listed below) are 32.7 percent of refs (39,041).

| family | bases | main mods | notes |
|---|---|---|---|
| jungle_tree 24 / jungle_emergent 32 | 56 | BM&V gkbjungletree*, KoTM Greguire JungleTree01-06 (58-67 m emergents), TS | Greguire emergents are the one real "rainforest giant" |
| coast_palm 29 / small_palm 15 / date_palm 6 | 50 | KoTM CTQ/Palmoke palms, TS beach/fan palms, BM&V | 50 palm models; the best-served form |
| bald_cypress 12 / moss_cypress 4 / cypress knees 4 + 5 giant (0 refs) | 25 | KoTM cypress1-5, TreeBaldCypress, BM&V | knees held (4 sets, giant knees unplaced) |
| mangrove 5 | 5 | BM&V mangrovereachtree0gkb2/3/8/9, TS | only 5 meshes, 3,223 refs (2.7 percent); Kotherra 19 percent of its flora |
| swamp_giant 9, swamp_dead 13, swamp_log 34 | 56 | KoTM Greguire SwampTreeTall*, CypressDebris logs, BM&V leafless/vurt_deadtree | dead, broken, stumps, logs, branch piles all held |
| hist 12 + hist_root 23 | 35 | KoTM `argonia\trees\Hist trees\` (HistTree01-03, Gland01/03 + Dead, flowers, roots, vines) | 164 source refs only: rare by design |
| willow 13, dry_tree 20, seju 9, erut 8, bottle 3, bamboo 8 | 61 | KoTM, BM&V | dry_tree is ALL BM&V and partly temperate (below) |

Per-region sharing (tree families only, `region_flora` joined to `flora_base`, 20 land regions; the 4 sea regions
hold no tree except mangrove/palm fringes in Topal Bay and Sea of Mists):
- 193 distinct tree models across the land regions; only 9 appear in 10 or more of the 20 regions.
- Pairwise Jaccard of tree sets between any two regions tops out at 0.35 (Hatandros / Okuwun Rahei); none reaches
  0.5. So on SET membership the regions differ; on WEIGHTED whole flora (trees, reeds, ferns, undergrowth) they
  collapse into clusters (table below).
- Family mix gives the repeats: Aphon, Skeith, Aunike, Hatandros, Okuwun share {coast_palm, date_palm, dry_tree,
  small_palm, bottle_tree}; the cypress group (Blackwood, Nha Enasa, Murkwood, Ultherus, Tulmek) shares {bald_cypress,
  moss_cypress, swamp_dead, swamp_giant, willow, jungle_tree}.

Distinctness today, 0 to 3, my scoring from three measures (models used by that region alone, share of its weight on
meshes used in 12 or more regions, nearest-neighbour weighted cosine over all flora):

| region | models | exclusive | common share | nearest (cos) | score | what carries it |
|---|---|---|---|---|---|---|
| Murkwood | 119 | 15 | 10% | Tulmek 0.39 | 3 | Hist, hanging moss, moss cypress |
| Arnesian Jungle | 146 | 10 | 8% | Chixathe 0.26 | 3 | Greguire emergents, bamboo, ferns |
| Chixathe Mesa | 132 | 6 | 6% | Aphon 0.39 | 2 | dry scrub, cliff pieces, bamboo in the cuts |
| Skeith Isle | 84 | 0 | 3% | Chixathe 0.26 | 2 | boulders 33%, dry trees |
| Aphon Isle | 84 | 1 | 7% | Chixathe 0.39 | 2 | boulders 27%, dry trees 20% |
| Cape Percar | 131 | 2 | 10% | Althii 0.48 | 2 | mangrove, jungle, red-gum hills (no gum model) |
| Blackwood | 128 | 0 | 12% | Nha Enasa 0.67 | 2 | bald cypress, dead trees |
| Aunike Ridge | 109 | 0 | 11% | Valley of Storms 0.60 | 1 | boulders, dry trees (temperate junipers) |
| Hatandros Bight | 112 | 2 | 18% | Okuwun 0.69 | 1 | palms, dry trees; lore says "temperate grassland and salt marsh" |
| Kotherra Mangroves | 124 | 1 | 20% | Banujha 0.81 | 1 | 19% mangrove (5 meshes) is its only own thing |
| Tulmek Washes | 119 | 3 | 20% | Nha Enasa 0.85 | 1 | cypress + mangrove mix |
| Althii Archipelago | 115 | 2 | 21% | Nushara 0.80 | 1 | lore paddy and mangrove; no paddy model |
| Valley of Storms | 134 | 0 | 19% | Nha Enasa 0.76 | 1 | generic mix |
| Okuwun Rahei | 120 | 0 | 20% | Ultherus 0.83 | 0-1 | lore clay mounds: no mound model beyond dirt-mound dressing |
| Lake Ulaish | 118 | 2 | 25% | Ultherus 0.84 | 0-1 | reeds 20%, lily 15% |
| Nushara Bayou | 135 | 0 | 22% | Nha Enasa 0.86 | 0-1 | lore saltrice marsh: saltrice model held, unplaced |
| Banujha Basin | 109 | 0 | 23% | Ultherus 0.88 | 0 | reed 20%, lily 12% |
| Barsaebica | 132 | 1 | 20% | Nha Enasa 0.89 | 0 | lore fen and sedge: reed, lily |
| Nha Enasa | 117 | 0 | 28% | Barsaebica 0.89 | 0 | reed 23% |
| Ultherus Swamp | 98 | 0 | 28% | Nha Enasa 0.89 | 0 | reed 25%, lily 21% |

Sea regions (Benthic Yobesh 21 models, Padomaic Ocean 20, Sea of Mists 78, Topal Bay 63): seabed is Depths of Skyrim
(kelp, seaweed, coral 3 meshes 294 refs, shells 3), score 1: one look everywhere under water.

Reading: five regions (Banujha, Barsaebica, Nha Enasa, Ultherus, Lake Ulaish with Nushara/Okuwun) differ only by
which of three marsh kits they weight; the cheapest breadth gain is new MARSH-LAYER pieces (reeds, sedges, lilies,
herbs), not new tree species, because those layers are seen first and everywhere in 11 regions.

### 2.2 Lore forms with no model (or a stand-in)

Lore is thin on named vegetation: `story/lore/regions/*.md` mention mangroves (murkmire.md:23 "wall of mangroves";
waters.md:31 mangrove thickets screening Red Bramman's river), saltrice fields (thornmarsh-and-east.md:61,90),
Hist everywhere, "Path of the Lily" (murkmire.md:62), nut-throwing trees (thornmarsh-and-east.md:81), and region
notes (ecology/look) naming reed, cattail, rice/paddy, kelp, coral, red-gum, vine. No banyan, tree fern or
strangler fig in our lore (the only "stranglers" are creatures, `topics/loading-facts.md:767`).

| form | held model? | verdict (measured) |
|---|---|---|
| mangrove with prop roots | BM&V mangrovereachtree0gkb2/3/8/9 (the gkb "reachtree" file name is only a name, `flora_base.nordic_override` clears all 5) | 5 meshes; prop-root quality UNVERIFIED (no mesh access on this machine) |
| bald cypress, knees | yes, 12 trunks, 4 knees, 5 giant knees (0 refs) | good; giant knees unplaced |
| banyan / strangler fig | none | not in lore either; extrapolation only |
| giant ferns, tree ferns, cycads | TS ManFern, BM&V FernLarge03/braken (temperate), `fern` 16 bases = 26 percent of refs | no trunked tree fern; fern layer is the most-repeated plant |
| bamboo stands | 8 (KoTM, TS CITSfloraBamboo01, BM&V) | KoTM leaves recoloured (`recolour.json`: owner call L15); 2 KoTM bamboo bases 0 refs |
| palms | 50 models | best-served |
| dead drowned trees, stumps, logs | 13 + 34 | served |
| giant mushrooms | "giant_mushroom" family 7, but those are tinyshroom / smallmushroom / `bigshrub(colorful)`; 148 refs | the family name overstates: no true tall mushroom tree. Vanilla Blackreach and Dragonborn mushroom trees exist in games we own but no base uses them |
| Hist by age/state | HistTree01-03, HistGland01/03 + Dead, HistFlower01/02, HistRoot01-07, vines (KoTM, "Sleeping Hist Tree" mod 116792 is a row) | young/mature/dead covered; "sick, shrivelled, sealed" (owner rulings 2026-11, `docs/owner-rulings.md:902-912`, endings show trees dying) has no state variants |
| hanging moss / vines | 5 hanging_moss bases, 42 refs; HTBM Sithis' Beard x6 in harvest kinds | thin: the Murkwood signature is 42 source refs |
| lily pads | 11 (gkblillipad2 4,482 refs + KoTM) | one mesh = 93 percent |
| reeds | ONE: BM&V `vurt_reeds.nif`, 8,850 refs | monoculture across 11 wet regions |
| cattails | none (lore names cattail for Ultherus, region_note) | reed mesh stands in |
| giant flowers, carnivorous plants | KoTM Redwort, HTBM bloatspore/bog beacon/stinkhorn, Skyrim.esm swamp pod | harvest kinds only; ~2 per 100 cells |
| coral, kelp, salt-marsh | Depths coral 3, kelp 3+3, seaweed 3 | one underwater look province-wide |
| rice / paddy / saltrice | KoTM `ArgoniaDomesticSaltrice01` / `ArgoniaWildSaltrice01` (saltrice.nif) exist in `harvest_bases.json` | NOT in `flora_base`, `region_flora` or the harvest pools: Nushara "saltrice marsh" and Althii "paddy" show none |
| rotting stump, fallen log | 34 swamp_log (KoTM CypressDebris) | served |

Temperate/Nordic-looking pieces actually weighted in region flora (`flora_base`, model names): BM&V `dwarfjunip01/05/06`
(juniper, 675 refs, `dry_tree`; heavy in Aphon 20 percent, Aunike 18, Chixathe 15, Skeith 12), `poplar.nif`,
`oak-o.nif`, `treeoak03/08`, `ESalixshrub03` (392 refs, the top dry_tree), `braken.nif` (7,779, bracken),
`ztGorsebush*` (gorse), `ERaspberry`, `ESpMeadowsweet*`, `ver_herbgarden`, `Chickweed` (4,250), `StingingNettel`
(851), `Landscape\Mountains\MountainCliff*` rock walls (BM&V red cliff pieces, ~150 refs). Together roughly 20 to 25
percent of refs read temperate or Skyrim-ish (my count by name, not by sight: UNVERIFIED visually). The dressing kinds
`petal-drifts` (FXAmbPinkPetals at Aunike and Skeith) are cherry-blossom Skyrim effects.

### 2.3 Plants and harvestables

`harvestables.json`: 38 kinds; of the lore's 53 harvestables 18 are plants/fungi/eggs/shells and bound (ecology.md:221).
Binding of the 18: five or six have a Black Marsh model (somnalius frond HTBM, marshweed (new FLOR on HTBM swamp leaf),
dried flower buds (KoTM Redwort), rootland mushroom (HTBM stinkhorn), moon sugar cane (HTBM), hanging moss/Sithis'
Beard); the other 12 stand on vanilla Skyrim records: nirnroot, dragon's tongue, LAVENDER, THISTLE, giant lichen,
swamp fungal pod, fly amanita, white cap, imp stool (these three are KoTM mud copies of vanilla), slaughterfish egg,
rock warbler egg (vanilla BirdsNest), pearl oyster (Dragonborn).
- Stand-ins that read Nordic/alpine: thistle (open/mountain pool), lavender (open pool), giant lichen (rock/shore pool),
  dragon's tongue (hot-spring orange flower, neutral), spiky grass, canis root (Skyrim mountain root; in the shore and
  mountain pools), jazbay. The recorded Skyrim variety (`skyrim_bases_by_class_top`) is 84 to 86 percent Nordic/alpine
  by weight in forest, mountain and open (snowberry, juniper, tundra cotton, mountain flowers, thistle, lavender, aspen)
  but it is reference only: the filler draws from `pools` (Black Marsh kinds above), so snowberry/tundra cotton/juniper
  are NOT placed by the ecology stage (checked `harvest.py:210-244`). `NordicBarnacleCluster01` appears only in the
  reference list; the kraken barnacle (HTBM) stands in on the water pool.
- Lore alchemy plants with no native model: saltrice (model held, unplaced), kreshweed/wickwheat/stoneflower/scathecraw
  appear in `ingredients-alchemy.md:109-177` as the Morrowind base table (Morrowind kin, not Black Marsh placements);
  the lore file makes marshmerrow, hackle-lo, marshweed, flower buds, rootland mushroom, moon sugar, somnalius the
  Black Marsh plants, and all seven have a held or new model. So the plant bar is mostly met; the visual stand-ins
  (thistle, lavender, lichen) are small ground plants, 1 to 3 per 100 cells each.

### 2.4 Boats, ships, wrecks

Needs (sqlite):
- 31 boat stops: 22 served by raft-masters (poled raft or paddled canoe, `travel_operator` raft-master, open sea
  limit 500 m) and 9 by sea-coasters (Dunmer/Imperial small-draft coasters); by place kind: city 10, town 8, village 7,
  ferry 2, hamlet 2, belvedere 1, station 1. 90 routes. Water: 22 rivers, 27 lakes, 690 streams, 12 estuaries.
- 11 shipwreck places (6 Ink Lagoon, 4 Icerunner, 1 Wyrmstooth, `place_source` rank 1), 7 sunken ruins, 2 ferry
  places (Delta Ferry from Northshore Landing, vanilla Skyrim dock; Lujei Ferry from KoTM Alten Meerhleel),
  2 lighthouses (Mistfall Light from vanilla Solitude lighthouse, Seafalls from Wyrmstooth), 54 places on water.
- Vessel models actually seen in drafted places: BM&V `01Ship` (Imperial work barge at Ashgate Landing,
  `newworld/places/*/spaces/exterior/refs.jsonl`: "black marsh & valenwood's imperial ship"), `ship.barge`, planks
  (Helstrom's pier and ship per `nw-02-walk-5-handover.md:32`). Not found in any place: a canoe, dugout, raft model of ours. The surroundings
  detector (`tools/argonia_world/surroundings.py:39-44`) expects ship/longboat/rowboat/boat/canoe/raft names, i.e.
  Skyrim's kit: shiplongboat (Nordic), rowboat, "big ship" classes.
- `flora_base` has no boat or wreck mesh (query on model like boat/ship/wreck: empty).
- Lore: native craft are rafts, canoes, twin-hulled platform canoes, houseboats, Kothringi tidal canoe, shallow-draft
  sail-and-paddle boats from Korydon's boat-wrights (`material-culture.md:84-128`, `264-267`; places research
  `heartland.json:438`); Argonians do not build big ships, they crew Dunmer/Imperial ones; pirates of Topal Bay;
  lore flags any "living boat" as extrapolation (`material-culture.md:127`).
- Where a Nordic longboat stands in: Icerunner is a vanilla Nordic wreck (4 wrecks), Northshore Landing's dock
  (Delta Ferry). VERIFIED by `place_source`; what each source's hull looks like is NOT verified (no game files here).
- Held vessel kits per the old audit (now NOT dependencies): Skyrim Ferries (Claywater plank ferry), Sailboats Expanded
  (canoe1.nif, 11 canoe registry paths), Rowboats, Ships and Boats of Tamriel (Opening Work Camp), Sailable Ship
  (`dependency-audit.md:216-249`). Their absence from `mods/dependencies.json` means the pool today = vanilla boats +
  BM&V ship + whatever KotM/HTBM carry (a barge, planks, docks: KotM docks verified through Lujei source).

### 2.5 Rocks, bones, nests and other misc

- Rocks: `boulder` 34 bases and `cliff_piece` 21 (KoTM RockM/RockL, DirtCliffs, DesertRocksCliff), `rock_wall` 15
  (KoTM mountaincliff, BM&V MountainCliff = vanilla Skyrim mountain meshes in a red recolour), `seabed_rock` 15
  (Depths MountainTrim with moss). Boulders are 12 to 33 percent of the flora of Aphon, Skeith, Aunike, Chixathe,
  i.e. the island/upland regions look "Skyrim rock" (UNVERIFIED by sight; recoloured/mossy variants exist).
- Bones: dressing kinds `cairn-skulls` (Argonian skull statics: Blackwood, Chixathe), `xanmeer-bone-piles` (HTBM),
  `beast-skeletons` (Mihail giant snake skull + human spine: Chixathe, Skeith). No whale or leviathan bones.
- Nests/eggs: HTBM hackwing and bantam guar nests, KoTM Argonian eggs x5 colours (`gar-eggs`, `croc-nests`,
  `hist-spawn`, `hist-clutches`), 26 dressing kinds in all. Hives: only "honeycomb" is a creature drop, hive model
  not placed. Mounds: `crab-mounds` and `clay-mounds` use Riften dirt mounds (RiftenRWDirtMound01-04: a Nordic mound
  recoloured); no termite mound. Sap pools: one vanilla puddle mesh scaled (`docs/research/sap-water-bethesda.md:36-44`).
  Driftwood: not in the flora tables; dressing has `kelp-wrack` only.

## 3. Step 2: Nexus (run with `tooling/nexus_search.py`, 2026-11-24; the name wildcard misses many names)

Method note: searches for mangrove, banyan, canoe, dugout, galleon, dhow, fishing boat, skiff, longship, sugar cane,
rice, paddy returned nothing; "mangrove" by web search found only Nexus 19268 (a Skyrim LE tree resource with 4
mangrove trees, pages 403 here, so its permission, endorsement and SE port status are UNVERIFIED) and 2750 (New
Plants resource). Nexus pages cannot be fetched (HTTP 403), so permission lines come from the API description only.

### 3.1 Trees and plants

| candidate | id / author / endorsements | what | gap / note |
|---|---|---|---|
| Tropical Lands Assets - Cathnoquey asset dump | 33446 CreatyChameleon, 43 | the "Fractured Isles" project's tropical assets: dump of permitted assets, credit requested; 440 MB; s3d-prefixed files are NOT resources | most promising unseen tropical pool; contents list UNVERIFIED, must be downloaded to know (do not download now) |
| Flora Additions - Waterplants | 116324 Suinier, 1,425 | water plants | candidate for reeds/lily variety |
| Waterplants / Waterplants Improved | 6092 Halifax0815 11,855 / 20288 Pfuscher 4,021 | realistic reeds, water grass, kelp, lilies; description says it may be used as a resource with credit | candidate second reed/cattail set (contents UNVERIFIED) |
| Flora Additions - Cypress | 117459 Suinier, 355 | cypress variants | replacer-type; we already hold 12 |
| Morthal Swamp Bald Cypress / M.O.I.S.T. | 189488 cb3hinn 19 / 99083 Alaxouche-BlubboDE 756 | giant swamp tree overhaul (Morthal swamp trees, textures 2K/4K, models by BlubboDE) | replacer of vanilla Reach/swamp trees: usable as "big swamp tree" source, permission by BlubboDE stated in credits |
| Unique Marsh Trees | 54479 StephanoA 239 | ESL separating Reach trees in Morthal | plugin only |
| Thickets to Marsh Plants | 60569 Kiddgimmick/xcal68 842 | marsh plant mesh replacing thicket | replacer |
| Detailed Landscapes - Poison Blooms / Screaming Maw / Thorn Hook / Mushroom Trees / Root Weeds (BOS) | 93179, 93195, 93196, 93193, 93192 BecomingNplus1 (129 to 327) | higher-detail versions of vanilla Morthal swamp plants (carnivorous-looking pieces) | BOS replacers: possible stand-ins for "carnivorous plants" |
| High Poly Solstheim Mushroom Trees | 79111 Janissrim 2,036 | big mushroom trees (vanilla Dragonborn pieces) | giant mushroom form; the vanilla record is usable without the mod |
| Mushroom packs | Cathedral - Mushrooms 26103 (8,052), Rally's Blackreach 29179, Mari's Glowing 44464 | retextures | cosmetic |
| Hanging moss | Rally's 33225 (6,740), Mari's 34772 (3,091), Skyking 150002, ValArt 170945 | 3D hanging moss meshes | upgrades the 42-ref signature; replacers |
| Ferns | DrJacopo 3D Sword Ferns 82978 (8,044), TB's Better Ferns 72888, Mari's Reach Ferns 82527, ValArt 148127, Grumbledook 163949 | 3D sword/reach ferns | would break the ManFern monoculture only if used as additional meshes, not replacers |
| Skyrim 3D Trees and Plants | 12371 mathy79, 42,480 | replacer pack | general, not tropical |
| Enhanced Landscapes / Cathedral Landscapes / Happy Little Trees / NOTWL / Ulvenwald | various | temperate tree replacers | do not serve Black Marsh; note which are replacers vs resources: all of these are replacers |
| Witcher 3 Flora resource | 132962 Elrian 492 | rhododendron, rose, grapevine, sunflower, hedge meshes; "strictly free modding use" | Toussaint look, not swamp |
| Kemper's Tropical Fruits | 94050 Kemperer 94 | 9 fruits | clutter/harvest only |
| Project Rainforest SE / Lagoon / TSOP | 20636 sa547 858 / 37394 OldSaitoType02 986 / 36153 | rainforest climate/island mods | Project Rainforest is a climate/environment overhaul (assets UNVERIFIED) |
| Aquatic Jungle / Underwater plants | 43867 NeverLost 669 / 180035 renthal311 275 | underwater grass | seabed variety |
| Seashells | 4492 Jokerine 871 | shell clutter | beach scatter |
| TB's 3D Driftwood | 80418 Blender Animator 2,209; HD Dead Trees and Driftwoods 35308 | driftwood meshes | replacers of vanilla tundra driftwood (Nordic): usable as driftwood models |
| Rocks | Skyrim 3D Rocks 17732, DrJacopo 3D Rocks 132608, ERM 121336 | rock replacers | still Skyrim rock |
| Nests | Kanjs Bird Nests and Eggs 64905, Haladoon 45853, Diverse Bird's Nests BOS 100251 | nest meshes | cosmetic |
| Whale bones | Whale Bones on Coasts 91958 Mihail 3,308 (Xtudo port 91989) | coastal whale bone sets | fills "bones of big beasts" on coasts; Mihail is already a dependency author (kagouti, nix-hounds) |
| Swamp Skeletons | 151282 Chakra/Hexxagone 635 | swamp skeleton creature clutter | possible bone piles |

Verdict: no Nexus mod fills the Black Marsh signature forms (prop-root mangrove, tree fern, reed/cattail variety,
true giant fungus, Argonian craft). The held KoTM/HTBM/BM&V/TS pool already is the Nexus answer for trees. What Nexus
adds is detail and water-plant variety.

### 3.2 Boats, ships, wrecks

| candidate | id / author / endorsements | what | note |
|---|---|---|---|
| Ships and boats of Tamriel | 41653 ThatShipGuy/DeviantKaled, 829 | modder's resource: "lore-friendly ships and boats with interiors and wrecks", v1.1 Skyrim, Iliac Bay (Breton) and Empire (EEC) ships; v1.2 various ships, sloops, barges, ferries and more; no animation files; 206 MB | best single vessel source; the old audit had it as row 83 (b); Dunmer hulls not confirmed |
| Sailboats - Script Free Sailing EXPANDED | 40057 ElstarTomas/DeviantKhaled/Araanim 191 | rowboats, sailboats, canoe1.nif; uses DK's resource | was row 86/87; canoe mesh present |
| Skyrim Ferries / Carriage and Ferry Travel Overhaul | 8379 Kinaga 25,860 | ferries (travel) | already covered by our own travel network |
| Boats - Operational Animated Travel | 110882 Enneal 1,206 | animated boats | was row 88; animation = not needed for static craft |
| Animated Ships | 110260 Vicn 12,103 | vanilla ship animation | skeleton/animation, not new hulls |
| Rowboats of Skyrim (35341 PraedythXVI), Skyrim Rowboats (1019), Real Boats In Skyrim (123321), Of Ships and Boats (57673), Joy of Ships (28308), Boats and Ships 8k (45601), Beautiful Boats (7239) | various | retextures/meshes of vanilla boats | replacers, Nordic hulls |
| Wreck of the Crown Petone - Northern Argonian Settlement | 17263 mnikjom/Jokerine 456 | Argonian settlement built on a wreck, in the Sea of Ghosts | closest to an Argonian wreck dwelling; source-place candidate and mesh source |
| Haunted Shipwrecks | 142986 Clofas 1,372 | sound markers on vanilla wrecks | sound only |
| More Shipwrecks SE / Plankside Bandit Shipwreck / Wreck of the Argent Raptor | 133810 (57), 48790 (147), 140763 (232) | new wreck places | place sources, hull style UNVERIFIED |
| Moving Ships Resource / Model Ship Replacer | 83140 AndrealletiusVIII 230 / 51673 sync67 184 | moving ships; modder's resource | not needed |
| Skyrim 3D Docks and Boardwalks | 28781 mathy79 6,400; Better Docks 2384 | dock meshes | Nordic planks |

Nothing found for canoe, dugout, raft, junk, dhow, gondola, galleon, caravel, longship. Of the vessel lore, only
the Imperial/Breton/EEC ships (small sloops, barges, ferries) are covered; Argonian rafts/canoes/houseboats, Dunmer
coasters, Khajiit dhows and pirate (Topal Bay) ships are not.

## 4. Step 3: what we would model ourselves

What an image-to-3D generator does well: solid, closed forms with strong silhouette and bark/wood/rock texture; it
does badly with alpha-card foliage (thin leaves, fronds, reeds, grass, moss strands), because the output is a single
opaque mesh with a baked texture and no cut-out cards; it also fakes thin parts as thick blobs. So: generate the
SOLID part, hand-make or reuse the CARDS. Vegetation recipe family ("hybrid"):
- A. Solid only (generator alone): stumps, logs, driftwood, prop-root masses, cypress knees, root buttresses,
  termite/clay/mud mounds, boulders, giant mushrooms (stalk + cap, caps are solid), egg pods, gourds, coral heads,
  sap-bulb, bone sets, hulls, rafts, canoes, hut-sized things.
- B. Hybrid (generated trunk/roots + leaf cards reused from a held tree): mangrove (roots + BM&V mangrove crown cards),
  tree fern/cycad (fibrous trunk + TS/KoTM fern fronds), banyan/aerial-root fig (trunk mass + KoTM willow or jungle
  cards), palm variants (trunk + KoTM palm frond cards), sick Hist (existing Hist mesh, cards swapped by retexture).
- C. Cards only (no 3D generator; Fal image with alpha, hand-built quads): reeds, cattails, sedge, rice/saltrice
  clumps, lily pads, hanging moss/vines, grass. These need a person in Blender (or a script) to cut quads and set the
  shader flags to match the KotM/BM&V foliage nodes; a generator cannot do the alpha.

List, with player exposure and difficulty (E easy, M medium, H hard). "Where seen / how often" is from the measured region
weights above.

| # | object | size | solid? / skin / collision | where seen, how often | recipe | difficulty and reason |
|---|---|---|---|---|---|---|
| 1 | Mangrove prop-root cluster (3 to 4 variants, plus a seedling stand) | 6-12 m | static solid; roots need a collision proxy | Kotherra 19 percent, Cape Percar, Nushara, Tulmek, Banujha, Althii, Sea of Mists, Topal Bay; constantly, close up in boats | B (roots generated, crown cards from `mangrovereachtree0gkb*`) | M: bark texture stretches over a large mesh but roots are viewed from a boat at 3 to 20 m |
| 2 | Argonian dugout canoe, bundle-reed raft, twin-hull platform canoe, small houseboat (4 models) | 3-9 m, houseboat hut-sized | static solid; NO skeleton needed (boats on the map are decoration or fixed travel props; our travel is a fast-travel boat, not driven); collision one box; hull sits in water | 31 boat stops, 22 are raft-masters; every ferry/landing/camp; close up at every boarding | A | E for the dugout and raft (simple shapes), M for twin hull and houseboat (needs interior kept closed); houseboat is nearly a small hut (largest object here) |
| 3 | Reed/cattail/sedge/saltrice clump cards (6 to 8 clumps) | 0.5-2 m | cards, no collision | 11 wet regions, 7.4 percent of refs now on one mesh | C | M: modelling effort is the shader flags and LOD billboard; texture is a Fal alpha |
| 4 | Tree fern and cycad (3 trunks) | 3-8 m | hybrid | Arnesian Jungle, Chixathe cuts, Murkwood edges; 20 percent understory | B | M |
| 5 | Sick/dying Hist states (re-skins) and Hist seed pod (Mnemic egg), Hist sap bulb | 1-20 m | texture swap (re-skin of KotM HistTree) + pod solid | story: owner ruling says the endings show about 30 percent of trees dying; every Hist place | texture edits; pod A | E (texture) / E (pod) |
| 6 | Big drowned and driftwood set (hollow log, snag, stump, half-sunk trunk, bleached driftwood pile) 6 pieces | 1-6 m | static solid | blackwater and beaches; every swamp; from boats and shore | A | E |
| 7 | Hanging moss/liana curtains, lily-pad mat variants, water-hyacinth patch | cards | cards | Murkwood 11 percent, every water body | C | M |
| 8 | Black-Marsh shipwreck hulls: low-poly Dunmer/Imperial coaster hulls half sunk, one reed-and-timber houseboat wreck | 15-30 m | static solid, interior closed | 11 wreck places; 4 stand on vanilla Nordic Icerunner; seen from water at 10-60 m, boarded rarely | A with simple hull | M-H: big surface for one texture; viewed at distance, so M if broken into 3 to 4 sectional pieces |
| 9 | Giant fungus set (3 stalks, ledges/shelf fungus on trunks) | 2-8 m | stalk solid | Arnesian, Murkwood, Barsaebica floors | A | E-M (caps solid) |
| 10 | Clay/mud/termite mounds (3 variants) | 1-3 m | static solid | Okuwun Rahei (lore: clay mounds), Cape Percar, Chixathe; currently Riften dirt mound recolours | A | E |
| 11 | Whale/leviathan rib and beast skeleton set (4 pieces) | 2-10 m | static solid | coasts, Skeith, Chixathe | A | E; or Nexus whale bones 91958 first |
| 12 | Rice paddy / saltrice field plants (model exists for saltrice) | cards | cards | Althii, Nushara, Thorn | C or use KotM saltrice | E if held model is used |
| 13 | Coral heads and reef (3 to 5 shapes), kelp variants | 0.5-3 m | A solid for coral, C for kelp | the 4 sea regions | A | E coral, M kelp |
| 14 | Banyan/strangler fig | 15-25 m | B | optional (no lore) | B | H: huge trunk; skip unless the owner wants it |

Not worth generating: grass, bushes, palm fronds, bamboo leaf cards (held, 50 palm models), generic rocks (held).
Cannot verify here: the in-engine look of any held mesh, KotM/HTBM mesh lists beyond the plugin tables, the exact
contents of Nexus 33446/17263/41653.

## 5. Step 4: ranking (screen impact x closeness / difficulty)

1. Reed and marsh-layer cards (#3, #7, #12): the biggest breadth win; 11 regions, 7.4 percent of refs on one mesh;
   median difficulty, but no 3D generation (Fal alpha cards + hand-cut quads, or Waterplants 6092 first). Impact high,
   difficulty M.
2. Mangrove prop-root cluster (#1): defines the coast and boating views; B route; M.
3. Native craft kit (#2): the biggest "Black Marsh feel" gap (no Argonian vessel at all, boats in 31 stops); A route,
   simple shapes; E to M.
4. Driftwood/drowned set (#6) and mounds (#10): fast, solid, many placements; E.
5. Sick Hist states and egg pod (#5): small art, large story value; E.
6. Tree fern/cycad (#4): breaks the ManFern look in jungle; B; M.
7. Giant fungus (#9), coral (#13), bones (#11): E to M, narrow regions.
8. Wreck hulls (#8): 11 places, viewed from a distance, large surface: do after Ships and Boats of Tamriel is tried.
9. Banyan (#14): last.

"Do nothing / least / more / most" for the owner: nothing = current pool; least = place saltrice + unused vanilla
mushroom trees + try Ships and Boats of Tamriel/Waterplants as dependencies (no art); more = least + #2, #1, #6, #10, #5;
most = more + #3, #4, #8, #9, #13.

## Recommendations (beyond the brief, each with evidence)

- Place KotM's Saltrice in Nushara Bayou, Althii and Thorn-side regions: `ArgoniaDomesticSaltrice01/ArgoniaWildSaltrice01`
  are in `harvest_bases.json` (name "Saltrice") but in no flora table or pool (query on `flora_base` for "rice" empty);
  region notes name a "saltrice marsh" (Nushara, Arnesian ecology notes).
- Add vanilla Dragonborn/Blackreach giant mushroom records as a giant fungus family: no `giant_mushroom` base is tall
  (names tinyshroom/smallmushroom/bigshrub in `flora_base`).
- Place the 5 unplaced KotM giant cypress knees and the 2 unplaced bamboo bases (`placed_refs`=0, `cypress_knee_giant`).
- Restore `docs/research/lore/marsh-watercraft-and-argonian-boats.md` or retarget the reference at
  `story/lore/topics/material-culture.md:267`, which cites a file that does not exist.
- Re-add a boat/ship dependency row only if the owner wants vessels from a mod: none of the five boat mods in the
  old 98-row audit is in the current 193 rows.
- Rate the temperate set (`dwarfjunip*`, `poplar`, `oak-o`, `treeoak*`, `ESalixshrub03`, `braken`, gorse) at the next
  owner walk: these carry the upland regions (Aphon, Skeith, Aunike, Chixathe) and are the likeliest "Nordic" read.

Covered: docs/design/{ecology,dressing}.md, newworld/sources/{ecology,dressing,flora,identity,travel}, world.sqlite (all
flora, region, place, travel tables), nw-02-walk-5-handover, nw-03b-walk*, owner-rulings (grep), story/lore regions and topics
(grep), mods/dependencies.json, Nexus API searches (about 150 terms) and 6 web searches. Skipped: atmosphere.md and lod.md
(not about models), game archives and meshes (not on this machine, so every "look" claim is by name), Nexus pages
(HTTP 403), mod downloads (forbidden by brief).
