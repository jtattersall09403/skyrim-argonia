# nw-02 region flora: the plant, tree and rock set of each region

Built by `tools/newworld/flora.py` (`pull` from the flora study's catalogue, `build` into the db, `report` writes this file) from `newworld/sources/flora/` (families, habitats, guilds, regions). Tables: flora_class, flora_family, flora_base, habitat, habitat_family, flora_guild(_member), region_habitat, region_family, region_flora (schema.sql, Flora). Rules and evidence: [nw-02-flora-rules](nw-02-flora-rules.md).

Bases: 534 (BM&V 168, Depths 21, KoTM 332, TS 13), in 40 families, 19 habitats, 8 companion guilds; 5465 region_flora rows.

Nordic: catalogue rows with nordic_flag are dropped, plus Valenwood temperate trees (redwood, birch, maple, cedar) and props (wrecks, book towers, bones, coast-wave FX). One exception, kept with its reason in flora_base.nordic_override: the gkb mangrove meshes, flagged only for 'reachtree' in their file name.

## Similarity (weighted Jaccard of the regions' base weights, sum of minima over sum of maxima)

- Land pairs: max 0.292, mean 0.132 (test threshold 0.35).
- Pairs with a sea region: max 0.453, mean 0.046 (threshold 0.5: Depths ships only 3 corals, 3 seaweeds, 3 kelps and 3 clams, so the seabeds must share most of them).
- Most alike: padomaic-ocean / sea-of-mists 0.453; benthic-yobesh / padomaic-ocean 0.425; kotherra-mangroves / tulmek-washes 0.292; barsaebica / nha-enasa 0.290; banujha-basin / ultherus-swamp 0.290.

Within a region, a family's bases are a region-seeded subset (45 %, 2 to 8 bases), so regions sharing a family still show different meshes.

## Standing water

Bases stand in water only in a region's standing-water habitats (mangrove fringe, cypress swamp, drowned forest, reed marsh, open still water), to the lesser of the habitat's and the family's depth (mangrove, cypress, dead swamp trees 3.0 m; drowned forest cap 3.5 m; knees, reeds, logs 1.5 m; lilies 2.0 m; dry trees and palms 0.5 m). No habitat is flowing water; rivers carry riverine forest on their banks only.

## Regions

### Althii Archipelago (land; Coastal marsh and rice paddy)

- 116 bases in 23 families; 58 may stand in still water.
- Habitats: dry hammock 22%, mangrove fringe 22%, reed marsh 22%, coastal grassland 14%, beach and shore 12%, rocky outcrop 8%.
- Families: reed 13%, boulder 12%, marsh_herb 10%, undergrowth 10%, coast_palm 8%, mangrove 8%, flowers 6%, dry_tree 5%.
- Top bases: 001reed (BM&V) 13.1%, 01MANGROVE (BM&V) 2.5%, 01MANGROVE3 (BM&V) 2.5%, 01MANGROVE4 (BM&V) 2.5%, 01MountainTrim01FieldGrass01 (BM&V) 1.4%, RockPileL02WetBEACH (BM&V) 1.4%.

### Aphon Isle (land; coastal island scrub)

- 84 bases in 14 families; 0 may stand in still water.
- Habitats: upland scrub 35%, rocky outcrop 25%, beach and shore 15%, coastal grassland 15%, cliff face 10%.
- Families: boulder 27%, dry_tree 20%, undergrowth 16%, flowers 8%, cliff_piece 6%, small_palm 5%, marsh_herb 5%, coast_palm 3%.
- Top bases: RockL05MossTEMP1 (BM&V) 3.4%, ArgoniaMountainTrim03MarshGrass (KoTM) 3.4%, ArgoniaRockL01 (KoTM) 3.4%, ArgoniaRockM01 (KoTM) 3.4%, ArgoniaRockPileL01Rainforest (KoTM) 3.4%, ArgoniaRockPileM03MarshGrass (KoTM) 3.4%.

### Arnesian Jungle (land; Humid lowland jungle and riverine forest, with grassland at the Thorn end)

- 146 bases in 23 families; 0 may stand in still water.
- Habitats: rainforest floor 45%, riverine forest 20%, coastal grassland 10%, swamp hummock 10%, rocky outcrop 8%, cliff face 7%.
- Families: undergrowth 17%, jungle_tree 12%, boulder 10%, fern 10%, jungle_emergent 7%, hanging_moss 6%, marsh_herb 4%, cliff_piece 4%.
- Top bases: 001yellowbush (BM&V) 2.1%, 01BUSH1 (BM&V) 2.1%, ArgoniaTreeShrub02 (KoTM) 2.1%, ArgoniaTreeShrub04 (KoTM) 2.1%, ArgoniaTreeUndergrowth01Jungle (KoTM) 2.1%, ArgoniaTreeUndergrowth04Jungle (KoTM) 2.1%.

### Aunike Ridge (land; Upland marsh ridge of rock outcrop, scrub, reed and a few stunted trees)

- 109 bases in 19 families; 41 may stand in still water.
- Habitats: upland scrub 38%, rocky outcrop 22%, reed marsh 18%, cliff face 12%, coastal grassland 10%.
- Families: boulder 21%, dry_tree 18%, undergrowth 12%, flowers 10%, reed 8%, marsh_herb 7%, cliff_piece 7%, rock_wall 3%.
- Top bases: 001reed (BM&V) 8.0%, 01mudrockstack (BM&V) 2.7%, ArgoniaRockL02 (KoTM) 2.7%, ArgoniaRockL04 (KoTM) 2.7%, ArgoniaRockM03 (KoTM) 2.7%, ArgoniaRockPileL01Rainforest (KoTM) 2.7%.

### Banujha Basin (land; flooded basin swamp)

- 109 bases in 21 families; 66 may stand in still water.
- Habitats: reed marsh 30%, mangrove fringe 25%, drowned forest 20%, swamp hummock 15%, open still water 10%.
- Families: reed 20%, lily 12%, marsh_herb 9%, mangrove 8%, swamp_log 8%, swamp_dead 8%, fern 6%, bald_cypress 5%.
- Top bases: 001reed (BM&V) 20.0%, 01MANGROVE (BM&V) 2.8%, 01MANGROVE2 (BM&V) 2.8%, 01MANGROVE4 (BM&V) 2.8%, ArgoniaLilypad01A (KoTM) 2.4%, ArgoniaLilypad01B (KoTM) 2.4%.

### Barsaebica (land; fen and sedge)

- 134 bases in 24 families; 41 may stand in still water.
- Habitats: reed marsh 38%, swamp hummock 22%, dry hammock 15%, open still water 10%, rocky outcrop 10%, cliff face 5%.
- Families: reed 17%, marsh_herb 15%, lily 11%, boulder 9%, undergrowth 8%, fern 6%, swamp_shrub 5%, flowers 3%.
- Top bases: 001reed (BM&V) 17.4%, 01gkblillipad (BM&V) 2.2%, ArgoniaLilypad01B (KoTM) 2.2%, ArgoniaLilypad02A (KoTM) 2.2%, ArgoniaLilypad02B (KoTM) 2.2%, ArgoniaLilypad03 (KoTM) 2.2%.

### Benthic Yobesh (sea; Open sea floor, coral and kelp)

- 23 bases in 6 families; 0 may stand in still water.
- Habitats: seabed, deep (20 to 80 m) 50%, seabed, mid (5 to 20 m) 30%, seabed, shallow (0 to 5 m) 20%.
- Families: seabed_rock 36%, seaweed 27%, kelp 14%, shell 12%, coral 11%, boulder 1%.
- Top bases: TBP_seaweed02 (Depths) 13.4%, TBPSeaweed06Cluster (Depths) 13.4%, 01kelpshort (BM&V) 6.9%, 01waterkelp (BM&V) 6.9%, ArgoniaRiverClam01 (KoTM) 6.2%, ArgoniaRiverClamLarge01 (KoTM) 6.2%.

### Blackwood (land; bog and low forest)

- 129 bases in 23 families; 65 may stand in still water.
- Habitats: drowned forest 25%, cypress swamp 20%, reed marsh 15%, rocky outcrop 15%, swamp hummock 15%, cliff face 10%.
- Families: boulder 14%, bald_cypress 11%, reed 8%, swamp_dead 8%, fern 6%, marsh_herb 6%, swamp_log 5%, cliff_piece 5%.
- Top bases: 001reed (BM&V) 8.3%, ArgoniaTreeCypressKnee01 (KoTM) 2.5%, ArgoniaTreeCypressKnee04 (KoTM) 2.5%, 01cypress2 (BM&V) 1.9%, 01cypress3 (BM&V) 1.9%, 01cypressDUPLICATE001 (BM&V) 1.9%.

### Cape Percar (land; Coastal swamp forest and mangrove, with drier red-gum hills)

- 133 bases in 25 families; 42 may stand in still water.
- Habitats: dry hammock 28%, mangrove fringe 22%, swamp hummock 15%, coastal grassland 13%, beach and shore 12%, rocky outcrop 10%.
- Families: undergrowth 14%, boulder 13%, marsh_herb 8%, mangrove 7%, coast_palm 6%, erut 6%, dry_tree 5%, flowers 5%.
- Top bases: 001reed (BM&V) 3.2%, 01MANGROVE (BM&V) 2.5%, 01MANGROVE2 (BM&V) 2.5%, 01MANGROVE3 (BM&V) 2.5%, 01tROPICAL2 (BM&V) 1.7%, 01tropicalshrubDUPLICATE001 (BM&V) 1.7%.

### Chixathe Mesa (land; Dry upland scrub and stunted forest on the mesa tops, riverine jungle in the cuts)

- 132 bases in 22 families; 0 may stand in still water.
- Habitats: upland scrub 35%, cliff face 20%, riverine forest 20%, rocky outcrop 15%, rainforest floor 10%.
- Families: boulder 18%, dry_tree 15%, undergrowth 13%, cliff_piece 10%, rock_wall 7%, jungle_tree 5%, flowers 4%, fern 4%.
- Top bases: 01morrowindrock2 (BM&V) 2.3%, 01redrock2 (BM&V) 2.3%, ArgoniaRockL01 (KoTM) 2.3%, ArgoniaRockM01 (KoTM) 2.3%, ArgoniaRockPileS01Mud (KoTM) 2.3%, ArgoniaRockPileS04Rainforest (KoTM) 2.3%.

### Hatandros Bight (land; temperate coastal grassland and salt marsh)

- 113 bases in 20 families; 41 may stand in still water.
- Habitats: coastal grassland 35%, reed marsh 22%, beach and shore 15%, dry hammock 13%, rocky outcrop 10%, cliff face 5%.
- Families: boulder 16%, undergrowth 14%, flowers 12%, dry_tree 10%, marsh_herb 10%, reed 10%, small_palm 7%, swamp_log 4%.
- Top bases: 001reed (BM&V) 9.8%, 01blueflowers (BM&V) 3.0%, 01meadowClusterPlant (BM&V) 3.0%, 01meadowClusterPlant2 (BM&V) 3.0%, 01rasberrybush (BM&V) 3.0%, ArgoniaRockL01 (KoTM) 2.0%.

### Kotherra Mangroves (land; mangrove swamp and estuary)

- 124 bases in 23 families; 74 may stand in still water.
- Habitats: mangrove fringe 45%, reed marsh 18%, swamp hummock 15%, drowned forest 10%, open still water 7%, beach and shore 5%.
- Families: mangrove 19%, reed 16%, fern 10%, marsh_herb 8%, lily 8%, swamp_log 6%, swamp_dead 4%, bald_cypress 4%.
- Top bases: 001reed (BM&V) 15.6%, 01MANGROVE2 (BM&V) 6.2%, 01MANGROVE3 (BM&V) 6.2%, 01MANGROVE4 (BM&V) 6.2%, 01gkblillipad (BM&V) 1.6%, ArgoniaLilypad01B (KoTM) 1.6%.

### Lake Ulaish (land; Shallow freshwater lake, reed beds, silt islets and delta marsh)

- 119 bases in 22 families; 41 may stand in still water.
- Habitats: reed marsh 35%, lake and river-mouth bed 25%, dry hammock 15%, swamp hummock 13%, open still water 12%.
- Families: reed 20%, lily 15%, kelp 14%, marsh_herb 8%, boulder 6%, undergrowth 5%, shell 5%, fern 4%.
- Top bases: 001reed (BM&V) 20.5%, 01kelp (BM&V) 6.8%, 01waterkelp (BM&V) 6.8%, 01gkblillipad (BM&V) 3.1%, ArgoniaLilypad01A (KoTM) 3.1%, ArgoniaLilypad05A (KoTM) 3.1%.

### Murkwood (land; Dense Hist swamp forest of great roots and hanging moss, black Heart-Mud flats and slow rivers)

- 120 bases in 22 families; 59 may stand in still water.
- Habitats: hist grove 30%, cypress swamp 25%, swamp hummock 20%, drowned forest 15%, open still water 10%.
- Families: hanging_moss 11%, bald_cypress 10%, fern 10%, lily 9%, hist_root 8%, swamp_log 5%, cypress_knee 5%, marsh_herb 5%.
- Top bases: 01mossbush (BM&V) 3.8%, 01mossDUPLICATE001 (BM&V) 3.8%, AltElvenVine (BM&V) 3.8%, 001reed (BM&V) 3.0%, ArgoniaTreeCypressKnee02 (KoTM) 2.4%, ArgoniaTreeCypressKnee03 (KoTM) 2.4%.

### Nha Enasa (land; river swamp with reed banks)

- 117 bases in 22 families; 57 may stand in still water.
- Habitats: reed marsh 40%, riverine forest 20%, swamp hummock 18%, open still water 10%, rocky outcrop 7%, cypress swamp 5%.
- Families: reed 23%, fern 12%, lily 11%, marsh_herb 10%, undergrowth 7%, boulder 6%, jungle_tree 5%, swamp_shrub 5%.
- Top bases: 001reed (BM&V) 22.5%, ArgoniaLilypad01A (KoTM) 2.2%, ArgoniaLilypad01B (KoTM) 2.2%, ArgoniaLilypad02B (KoTM) 2.2%, ArgoniaLilypad03 (KoTM) 2.2%, ArgoniaLilypad05B (KoTM) 2.2%.

### Nushara Bayou (land; Tidal bayou and saltrice marsh)

- 136 bases in 25 families; 58 may stand in still water.
- Habitats: reed marsh 30%, mangrove fringe 22%, swamp hummock 18%, open still water 15%, dry hammock 10%, beach and shore 5%.
- Families: reed 18%, marsh_herb 14%, lily 14%, mangrove 7%, fern 6%, undergrowth 6%, swamp_log 4%, swamp_shrub 4%.
- Top bases: 001reed (BM&V) 18.4%, ArgoniaLilypad01B (KoTM) 2.8%, ArgoniaLilypad03 (KoTM) 2.8%, ArgoniaLilypad04 (KoTM) 2.8%, ArgoniaLilypadGiant01 (KoTM) 2.8%, ArgoniaWaterWeed01 (KoTM) 2.8%.

### Okuwun Rahei (land; clay mounds, lakes and marsh with tidal creeks)

- 122 bases in 23 families; 41 may stand in still water.
- Habitats: reed marsh 28%, dry hammock 25%, coastal grassland 12%, open still water 10%, rocky outcrop 10%, lake and river-mouth bed 8%, cliff face 7%.
- Families: reed 14%, boulder 12%, lily 12%, flowers 9%, marsh_herb 9%, undergrowth 8%, kelp 5%, dry_tree 5%.
- Top bases: 001reed (BM&V) 14.4%, 01kelpshort (BM&V) 2.5%, 01waterkelp (BM&V) 2.5%, 01gkblillipad (BM&V) 2.3%, ArgoniaLilypad02A (KoTM) 2.3%, ArgoniaLilypad04 (KoTM) 2.3%.

### Padomaic Ocean (sea; open sea, kelp and sandbank)

- 23 bases in 6 families; 0 may stand in still water.
- Habitats: seabed, deep (20 to 80 m) 40%, seabed, mid (5 to 20 m) 35%, seabed, shallow (0 to 5 m) 25%.
- Families: kelp 31%, seaweed 24%, seabed_rock 22%, shell 19%, coral 3%, boulder 1%.
- Top bases: 01kelpshort (BM&V) 15.7%, 01waterkelp (BM&V) 15.7%, TBP_seaweed02 (Depths) 12.0%, TBPSeaweed06Cluster (Depths) 12.0%, ArgoniaRiverClamLarge01 (KoTM) 9.3%, ArgoniaRiverClamThin01 (KoTM) 9.3%.

### Sea of Mists (sea; Shallow sea with mangrove fringes)

- 80 bases in 15 families; 42 may stand in still water.
- Habitats: seabed, mid (5 to 20 m) 35%, seabed, shallow (0 to 5 m) 35%, mangrove fringe 15%, seabed, deep (20 to 80 m) 10%, beach and shore 5%.
- Families: kelp 23%, seabed_rock 17%, coral 14%, seaweed 14%, shell 12%, mangrove 6%, boulder 4%, coast_palm 2%.
- Top bases: 01kelpshort (BM&V) 11.4%, 01waterkelp (BM&V) 11.4%, TBPCoralMedium01 (Depths) 7.0%, TBPCoralSmall01 (Depths) 7.0%, TBP_seaweed02 (Depths) 6.9%, TBPSeaweed06Cluster (Depths) 6.9%.

### Skeith Isle (land; rock, sea-grass and scrub)

- 84 bases in 14 families; 0 may stand in still water.
- Habitats: rocky outcrop 35%, cliff face 20%, upland scrub 20%, beach and shore 15%, coastal grassland 10%.
- Families: boulder 33%, undergrowth 15%, dry_tree 12%, cliff_piece 10%, flowers 7%, rock_wall 7%, small_palm 4%, marsh_herb 3%.
- Top bases: 01MountainTrim02Rocks01 (BM&V) 4.1%, ArgoniaRockL04 (KoTM) 4.1%, ArgoniaRockM01 (KoTM) 4.1%, ArgoniaRockM02 (KoTM) 4.1%, ArgoniaRockPileL04Rainforest (KoTM) 4.1%, ArgoniaRockPileM02Mud (KoTM) 4.1%.

### Topal Bay (sea; coastal sea)

- 65 bases in 13 families; 42 may stand in still water.
- Habitats: seabed, shallow (0 to 5 m) 50%, mangrove fringe 25%, seabed, mid (5 to 20 m) 25%.
- Families: kelp 23%, coral 21%, shell 17%, seabed_rock 12%, mangrove 8%, reed 4%, seaweed 3%, boulder 3%.
- Top bases: 01kelp (BM&V) 11.5%, 01waterkelp (BM&V) 11.5%, TBPCoralBig01 (Depths) 10.3%, TBPCoralSmall01 (Depths) 10.3%, ArgoniaRiverClam01 (KoTM) 8.6%, ArgoniaRiverClamLarge01 (KoTM) 8.6%.

### Tulmek Washes (land; Swamp, lake and mangrove)

- 119 bases in 23 families; 76 may stand in still water.
- Habitats: reed marsh 25%, cypress swamp 22%, drowned forest 18%, mangrove fringe 15%, open still water 10%, swamp hummock 10%.
- Families: reed 17%, lily 12%, bald_cypress 9%, marsh_herb 8%, fern 7%, cypress_knee 7%, swamp_dead 6%, swamp_log 6%.
- Top bases: 001reed (BM&V) 16.6%, ArgoniaTreeCypressKnee02 (KoTM) 3.4%, ArgoniaTreeCypressKnee03 (KoTM) 3.4%, ArgoniaLilypad01B (KoTM) 2.5%, ArgoniaLilypad02A (KoTM) 2.5%, ArgoniaLilypad02B (KoTM) 2.5%.

### Ultherus Swamp (land; Cattail and reed swamp with dragon's-tongue beds, hummocks and braided channels)

- 100 bases in 19 families; 57 may stand in still water.
- Habitats: reed marsh 42%, swamp hummock 20%, open still water 18%, cypress swamp 12%, lake and river-mouth bed 8%.
- Families: reed 25%, lily 21%, marsh_herb 11%, fern 6%, swamp_shrub 5%, kelp 5%, bald_cypress 4%, undergrowth 4%.
- Top bases: 001reed (BM&V) 25.1%, 01gkblillipad (BM&V) 4.3%, ArgoniaLilypad01A (KoTM) 4.3%, ArgoniaLilypad01B (KoTM) 4.3%, ArgoniaLilypad02A (KoTM) 4.3%, ArgoniaLilypadGiant01 (KoTM) 4.3%.

### Valley of Storms (land; fresh marsh and sedge plain)

- 135 bases in 24 families; 41 may stand in still water.
- Habitats: reed marsh 25%, coastal grassland 20%, dry hammock 15%, riverine forest 15%, rocky outcrop 13%, cliff face 12%.
- Families: boulder 14%, undergrowth 11%, reed 11%, marsh_herb 10%, dry_tree 8%, flowers 7%, cliff_piece 7%, willow 4%.
- Top bases: 001reed (BM&V) 11.0%, RockL05MossTEMP1 (BM&V) 1.8%, ArgoniaRockM02 (KoTM) 1.8%, ArgoniaRockPileM01Mud (KoTM) 1.8%, ArgoniaRockPileM02Mud (KoTM) 1.8%, ArgoniaRockPileM03MarshGrass (KoTM) 1.8%.
