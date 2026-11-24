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
2. Nexus (both games, name and description; section 3) fills the plants and ships, not the signature forms.
   GKB Green Trees (skyrim:19268) is already our pool: 40 GKB meshes are in `flora_base`, among them all 5 mangroves.
   New finds: Harvestables (skyrim:15108: saltrice, marshmerrow, hackle-lo, sugarcane, stoneflower, trama root, bamboo),
   Ships and Boats of Tamriel (41653) plus Cyrodiil/Breton/Nord ship resources, Waterplants (6092), Cathnoquey (33446),
   Mad Modder's Assets (83445), Bones (skyrim:94817), Whale Bones (91958), a canoe in Sailboats/Script Free Sailing.
   No hit for: dugout, raft, houseboat, dhow, tree fern, banyan, cattail, rice, termite.
3. Own-model priority: (1) Argonian craft kit (dugout, reed raft, twin-hull canoe, houseboat), (2) reed/cattail/rice
   cards (Waterplants first), (3) driftwood/drowned set and mounds, (4) sick-Hist states and egg pod, (5) tree ferns,
   (6) mangrove roots only after auditing GKB's unused numbers, (7) wreck hulls. See sections 4 and 5.
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

## 3. Step 2: Nexus (re-run 2026-11-24 with the fixed `tooling/nexus_search.py`)

What was searched: Special Edition AND the 2011 game (`skyrim:<id>`), by mod name and by description text, for:
mangrove(s), cypress, "swamp tree", jungle, tropical, palm, bamboo, "tree fern", banyan, vines, moss, "lily pad", reeds,
cattail, mushroom, "giant mushroom", coral, kelp, rice, saltrice, "sugar cane", papyrus, "water hyacinth", canoe, dugout,
raft, houseboat, boat, ship, shipwreck, galleon, pier, driftwood, skeleton, bones, nest, termite, gkb, "Ga-Knomboe",
"dead trees", fern, and the resource-pack words "modders resource", "tree resource", "flora resource",
"plants resource", "boat resource", "ship resource"; then `--mod` on every strong candidate. Description hits are
noisy (mod guides, followers), so the lists below are read by summary. A `skyrim:` mod is usable once its meshes are
converted to Special Edition format (NifSkope/Cathedral-style conversion, textures kept); the permission line is
quoted where the description gives one; where it does not, I say so. Nexus pages themselves return 403, so I read the
API description only: file lists and model counts below are what the description or file list states, nothing more.

### 3.1 What we already hold from the big resources

- GKB Green Trees (skyrim:19268, Ga-Knomboe Boy, 910 endorsements, 204 MB): "hundreds of new green tree models based
  off re-textured vanilla models, and new models", "new trees with alternative textures and LODs", red/orange aspen
  colour variants. Permission: "use in whatever mod you want, just don't rename the trees and give credit in your
  read me files". LE mod, needs conversion. The description does not count mangroves.
- Our pool is already GKB's: `flora_base` holds 40 distinct GKB meshes (30+ `gkbjungletreenew*` variants numbered
  1 to 26, `gkbjunipertree`, `gkblillipad2`, `hodalder01gkb`, `hodsalixgkb09`, and the 4 `mangrovereachtree0gkb2/3/8/9`),
  carried by BM&V and Tropical Skyrim. Numbers 10, 18, 21, 22 and 25 of the jungle series and the mangrove numbers
  0/1/4-7 are not in our tables, so the pack probably holds siblings we do not use; whether they exist, and whether
  any mangrove has true prop roots, is NOT verified (no mesh access). So GKB Green Trees is first an audit target
  (list the unused numbers), not a new look. It is also the source of our temperate junipers and alders.

### 3.2 Trees, plants, rocks and misc: what Nexus now fills

| gap | candidate (id, author, endorsements) | what it holds | usable as | permission / note |
|---|---|---|---|---|
| Saltrice, marshmerrow, hackle-lo, sugarcane, stoneflower, trama root, ash yam, bamboo trees, apple trees, mandrake, alkanet | Harvestables (skyrim:15108, ChickenDownUnder, 354) | per its file list: Saltrice, Marshmerrow, Hackle lo, Sugarcane, Stoneflower, Trama Root, Ash Yam, Garlic, Carrot, Wheat, Blueberry, Bamboo Trees, Apple Trees, Mandrake, Alkanet | modder's resource, LE (convert); gives the Morrowind ingredient plants of `ingredients-alchemy.md:109-177` | permission line not in the description (UNVERIFIED). KotM's Saltrice/Marshmerrow/Hackle-Lo may well descend from these |
| tropical plant resources | Tropical Lands Assets - Cathnoquey (33446, CreatyChameleon, 43) | the Fractured Isles project's tropical assets, 440 MB; "let us know if you use anything, credit us"; s3d-prefixed files are not resources | SE modder's resource | contents list unread |
| plants/trees resource | New Plants (2750 SE and skyrim:22018, Tamira, 226/794) | plants as modder's resource (meshes derived from Yughues/Nobiax) | SE and LE | "use meshes and textures in your mods with credit; no paid mods; do not upload elsewhere" |
| plants, trees | Tashenis Skyberry Resource - Plants (skyrim:120004, 287 MB) | weeds, flowers, bushes, shrubs, trees; "more than 500 unique textures"; meshes are vanilla, Hoddminir, one GKB tree and two Tamira trees | LE | texture-heavy, meshes not new |
| tropical grass and plants | Tropical - Spring - Summer Grasses and Plants (skyrim:71674, unique1, 383); Tropical Skyrim Enhanced (skyrim:83982, Ewarre, 389) | Hoddminir-flower grass sets; TSE adds a new "fern" model and recolours | LE | credits go to original authors; TSE built on Tropical Skyrim (which we use in SE form) |
| warehouse of free assets | Mad Modder's Assets (83445, ManyMadModders, 160) | 1.1 GB, "thousands of meshes and textures from every resource I could get permissions to use" | SE | contents unread: worth a download-and-index in a later phase |
| lily pad | Unique Lily Pad Resource (skyrim:93338, mypillzes, 53) | one lily pad model converted from cadnav | LE | "free to use resource" |
| reeds, cattails, water grass | Waterplants (6092, Halifax0815, 11,855), Waterplants Improved (20288), Flora Additions - Waterplants (116324) | water plants, reeds, grass and kelp; 6092 allows use as a resource with credits | SE | model list unread; searches for reed(s), cattail and papyrus in both games returned no reed or cattail resource, so this is the only lead |
| water hyacinth, rice, paddy, sugar cane, termite | searched both games, name and description | nothing relevant except Harvestables' Sugarcane | | |
| giant mushrooms | Solstheim Mushroom Trees are vanilla Dragonborn records (high-poly fix 79111, Janissrim, 2,036); Blackreach mushrooms vanilla (40418, 29179) | tall mushroom trees | SE, no conversion | the record needs no mod |
| swamp trees, cypress | M.O.I.S.T. (99083, Alaxouche/BlubboDE, 756), Morthal Swamp Bald Cypress (189488), Flora Additions - Cypress (117459, 355), Cypresses improved (117560) | bigger cypress and swamp tree models | SE | replacers/additions on vanilla Reach and swamp trees; we hold 12 cypress |
| carnivorous-looking plants | Detailed Landscapes - Poison Blooms (93179), Screaming Maw (93195), Thorn Hook (93196), Mushroom Trees (93193), Root Weeds (93192), BecomingNplus1 | detailed vanilla Morthal swamp plants via BOS | SE | vanilla stand-ins |
| ferns | DrJacopo 3D Sword Ferns (82978, 8,044), TB's Better Ferns (72888, 4 models), Skyrim 3D Trees and Plants - Ferns only (87950) | sword fern replacers; none is a tree fern | SE | would add variety against ManFern only if loaded beside, not over |
| hanging moss, vines | Rally's (33225), Mari's (34772), ValArt (170945), Vines Improved (196209) | better meshes | SE | replacers; no new form |
| driftwood | TB's 3D Driftwood (80418, 2,209), HD Dead Trees and Driftwoods (35308) | driftwood and dead tree meshes | SE | replacers of Nordic tundra driftwood |
| rocks | Tropical Based Rock Retexture (skyrim:34317, MSFoxhound, 140); Skyrim 3D Rocks (17732), DrJacopo 3D Rocks (132608) | retexture/replacers of Skyrim rock | LE/SE | no swamp-specific rock set found |
| bones | Bones (skyrim:94817, RoboBirdie, 14 MB resource), Whale Bones on Coasts (91958, Mihail, 3,308), Swamp Skeletons (151282, 635) | bone sets, whale bones, swamp skeleton clutter | LE / SE | Mihail already a dependency author |
| nests | Kanjs Bird Nests and Eggs (64905), Haladoon nests (45853) | nest meshes | SE | cosmetic |
| tree resources that are not tropical | Paolos Tree Resource (skyrim:5929), Real Cherry Blossom (38980), Witcher 3 Flora (132962, "free modding use only"), Happy Little Trees, NOTWL, Ulvenwald, Cathedral Landscapes, Skyrim 3D Trees and Plants, Enhanced Vanilla Trees | temperate/Nordic tree sets | | replacers, not for Black Marsh (Paolos is "use as you like", unfinished) |

### 3.3 Boats, ships, wrecks: what Nexus now fills

| candidate | holds | usable as | permission |
|---|---|---|---|
| Ships and boats of Tamriel (41653, ThatShipGuy/DeviantKaled, 829) | "lore-friendly ships and boats with interiors and wrecks": v1.1 Skyrim, Iliac Bay (Breton) and Empire (EEC) ships; v1.2 ships, sloops, barges, ferries and more; no animation files; 206 MB | SE modder's resource | permission text not in the API description (UNVERIFIED); the same author's LE volumes say "use in your own mods ONLY with my permission; credit; not for profit" |
| DK's Lore-Friendly Ships and Boats Resources Vol. 1 Nords (skyrim:75965) and Vol. 2 Bretons (skyrim:77174) | original ship and boat models | LE, convert | the permission above (ask the author) |
| Cyrodiil Ship and boat resource (skyrim:59426, Markus Liberty, 475, Beyond Skyrim) | an Oblivion galleon remake and an Imperial rowboat | LE, convert | credit lines only in description |
| Sailboats - Script Free Sailing EXPANDED (40057, 191) and Script free ship sailing (skyrim:67727, ElstarTomas, 4.7 MB) | a rideable tilting canoe (canoe1.nif per the old audit) plus rowboats and sailboats that "use the collisions of the original canoe" | SE / LE | the old audit found 11 canoe registry paths in 86 (`dependency-audit.md:247`) |
| Dark Ship Retexture - unfolded sails (1054, Hannes821; skyrim:70287) | retextured longboat, large ship, rowboat and galley, added not replaced; "Free Ressource" | SE | free resource with credits |
| Redania Ship in Windhelm (skyrim:87973, mypilzzes, 182) | a Witcher 2 ship model | LE | "more of a modders resource" |
| Airship Resource (skyrim:68926), Moving Ships Resource (83140), Object Resource Moving Boat (109321, Vicn) | an airship; moving-ship meshes | | not Black Marsh |
| Wreck of the Crown Petone (17263, mnikjom/Jokerine, 456), More Shipwrecks (133810), Plankside Bandit Shipwreck (48790), Wreck of the Argent Raptor (140763), Haunted Shipwrecks (142986, sound only) | wreck places on Nord/Imperial hulls; Crown Petone is an Argonian settlement on a wreck | SE | source places |
| Skyrim Ferries / Carriage and Ferry (8379), Boats Operational (110882), Animated Ships (110260) | travel/animation | | not needed: our travel is data |

Searched and found nothing relevant: dugout, houseboat, junk, dhow, gondola, skiff, caravel, longship, raft (only the
canoe above). So Argonian and Kothringi craft (dugout, reed raft, twin-hull platform canoe, houseboat), Dunmer
coasters, Khajiit dhows and Topal Bay pirate hulls have no Nexus source; Imperial, Breton, Nord and EEC hulls do.

### 3.4 Verdict

Nexus fills: ingredient plants (Harvestables), water plants/reeds (Waterplants, unread), Imperial and Breton ships,
wrecks as places, bones, whale bones, rocks (retextures only), lily pads, more GKB tree numbers, tropical asset dumps
(33446, 83445). Nexus does not fill, by name or description in both games: a prop-root mangrove (beyond GKB's
`mangrovereachtree` family, whose prop roots are unverified), tree fern/cycad, banyan, cattail, rice, termite mound,
any Argonian/Dunmer/Khajiit craft, or sick-Hist variants.

## 4. Step 3: what we would model ourselves (after Nexus)

What an image-to-3D generator does well: solid, closed forms with a strong silhouette and bark/wood/rock texture; it
does badly with alpha-card foliage (leaves, fronds, reeds, grass, moss strands), because it makes one opaque mesh with
a baked texture and no cut-out cards, and thickens thin parts. So: generate the SOLID part, reuse or hand-make the CARDS.
- A. Solid only: stumps, logs, driftwood, prop-root masses, knees, mounds, boulders, giant mushrooms (stalk and cap),
  egg pods, coral heads, bone sets, hulls, rafts, canoes, hut-sized things.
- B. Hybrid (generated trunk/roots + leaf cards reused from a held tree): mangrove prop roots with GKB mangrove crown
  cards, tree fern/cycad (fibrous trunk + TS/KoTM frond cards), palm variants, banyan.
- C. Cards only (Fal alpha image, quads cut by hand, shader flags copied from KotM/BM&V foliage nodes): reeds, cattails,
  sedge, rice clumps, hanging moss, water hyacinth. A generator cannot make the alpha.

| # | object | size | solid / skin / collision | seen where, how often | recipe | difficulty |
|---|---|---|---|---|---|---|
| 1 | Argonian craft: dugout canoe, bundle-reed raft, twin-hull platform canoe, small houseboat (4 models) | 3-9 m | static solid, no skeleton (decoration and fixed travel props; our boats are fast travel), one box collision; hull rests in water | 31 boat stops (22 raft-master), ferries, camps, landings; close up at every boarding | A | E dugout and raft, M twin hull and houseboat (nearly a hut) |
| 2 | Reed / cattail / sedge / rice clump cards, 6 to 8 | 0.5-2 m | cards | 11 wet regions; 7.4 percent of refs on one mesh | C, unless Waterplants (6092) holds usable ones | M |
| 3 | Mangrove prop-root cluster, 3 to 4 variants | 6-12 m | solid roots + GKB crown cards | Kotherra 19 percent, Cape Percar, Nushara, Tulmek, Banujha, Althii, sea fringes | B | M; do only if a look at GKB's unused mangrove numbers (3.1) shows no real prop roots |
| 4 | Tree fern and cycad, 3 trunks | 3-8 m | hybrid | Arnesian, Chixathe cuts, Murkwood edges | B | M |
| 5 | Sick/dying/sealed Hist states (texture swaps of KotM Hist meshes), Hist seed pod (Mnemic egg), sap bulb | 1-20 m | texture edits; pod solid | story: endings show about 30 percent of trees dying (`owner-rulings.md:902-912`); every Hist place | texture; A | E |
| 6 | Drowned/driftwood set: hollow log, snag, half-sunk trunk, bleached driftwood pile (6) | 1-6 m | solid | every blackwater swamp and beach, from boats | A | E |
| 7 | Clay, mud and termite mounds (3) | 1-3 m | solid | Okuwun Rahei (clay mounds), Cape Percar, Chixathe; now Riften dirt mounds | A | E |
| 8 | Dunmer coaster hull and Argonian houseboat wreck, half sunk; low-poly | 15-30 m | solid, interior closed, in 3 to 4 sections | 11 wreck places, viewed from water at 10-60 m; 4 now on vanilla Nordic Icerunner | A (Imperial/Breton hulls from 41653 instead) | M-H: large surface for one texture |
| 9 | Hanging moss / liana curtains, water hyacinth mats | cards | cards | Murkwood, every water body | C | M |
| 10 | Giant fungus ledges and a few extra stalks (vanilla Solstheim mushroom trees cover the tall form) | 2-8 m | A | Arnesian, Murkwood, Barsaebica floors | A | E |
| 11 | Coral heads (3 to 5) and kelp variants | 0.5-3 m | A / C | the 4 sea regions | A / C | E coral, M kelp |
| 12 | Beast and leviathan rib set (Nexus bones/whale bones first) | 2-10 m | solid | coasts, Skeith, Chixathe | A | E |
| 13 | Banyan/strangler fig | 15-25 m | B | optional (no lore) | B | H: huge close trunk |

No longer on the own-model list because Nexus or our own files fill it: ingredient plants (Harvestables, plus KotM saltrice),
Imperial/Breton/Nord ships and rowboats, bone and whale-bone clutter, lily pads, bamboo trees, extra GKB jungle trees,
giant mushroom trees (vanilla). Not worth generating: grass, bushes, palm fronds, bamboo cards, generic rocks.
Cannot verify here: the in-engine look of any held mesh, the model lists of Waterplants, Mad Modder's Assets, Cathnoquey and
Ships and Boats of Tamriel, and the permission text of the SE pages.

## 5. Step 4: ranking (screen impact and closeness, per unit of difficulty)

1. Argonian craft kit (#1): the largest Black Marsh gap with no source anywhere; simple solids; seen at every landing. E-M.
2. Reed/cattail/rice cards (#2, #9): biggest breadth win (11 wet regions on one reed mesh); first try Waterplants, else cards. M.
3. Drowned/driftwood (#6) and mounds (#7): fast solids, many placements. E.
4. Sick Hist states and egg pod (#5): little art, large story value. E.
5. Tree fern/cycad (#4): breaks the fern monoculture in the jungle. M.
6. Mangrove prop roots (#3): conditional on auditing GKB's unused mangrove numbers first. M.
7. Wreck hulls (#8) after trying 41653's hulls for Imperial wrecks; giant fungus (#10), coral (#11), bones (#12): narrow regions. E-M.
8. Banyan (#13): last.

Do nothing / least / more / most: nothing = current pool; least = place saltrice, add vanilla mushroom trees, audit GKB's
unused numbers, adopt Harvestables, Waterplants and Ships and Boats of Tamriel/Cyrodiil boats as dependencies (no art);
more = least + #1, #6, #7, #5; most = more + #2 (if Waterplants fails), #4, #3, #8, #10, #11.

## Recommendations (beyond the brief, each with evidence)

- Audit GKB Green Trees (skyrim:19268) against the 40 GKB meshes in `flora_base` before any new tree work: unused
  numbers in the jungle series (10, 18, 21, 22, 25) and the mangrove series are free variety and the same author's licence
  ("credit, do not rename") is the easiest in this lane.
- Place KotM's Saltrice in Nushara Bayou, Althii and the Thorn side: `ArgoniaDomesticSaltrice01/ArgoniaWildSaltrice01`
  are in `harvest_bases.json` but in no flora table or pool; region notes name a "saltrice marsh".
- Add vanilla Dragonborn/Blackreach mushroom-tree records as a giant fungus family: no `giant_mushroom` base is tall
  (tinyshroom/smallmushroom/bigshrub in `flora_base`).
- Place the 5 unplaced KotM giant cypress knees and the 2 bamboo bases with 0 refs (`placed_refs`=0).
- Restore `docs/research/lore/marsh-watercraft-and-argonian-boats.md` or retarget `story/lore/topics/material-culture.md:267`
  (the file it cites does not exist).
- Re-add a boat/ship dependency row only if the owner wants vessels from a mod; none of the five in the old audit is
  among the current 193 rows. Ask ThatShipGuy/DeviantKaled for permission text before any use: the LE volumes require it.
- Rate the temperate set (`dwarfjunip*`, `poplar`, `oak-o`, `treeoak*`, `ESalixshrub03`, `braken`, gorse) at the next owner
  walk: they carry Aphon, Skeith, Aunike and Chixathe.

Covered: docs/design/{ecology,dressing}.md, newworld/sources/{ecology,dressing,flora,identity,travel}, world.sqlite (flora,
region, place, travel, place_source tables), nw-02-walk-5-handover, nw-03b-walk*, owner-rulings (grep), story/lore regions and
topics (grep), mods/dependencies.json, Nexus API (both games, name and description, about 50 terms and 20 `--mod` reads) and
6 web searches. Skipped: atmosphere.md and lod.md (not about models), game archives and meshes (not on this machine, so
every "look" claim is by name), Nexus pages (HTTP 403), mod downloads (forbidden by the brief).
