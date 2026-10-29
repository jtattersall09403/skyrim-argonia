# Bog Iron Workings — design (16k walk 9, type 7 works; the type's first slice)

The builder was the place-type-7 lane, which worked on 2026-10-01. The layout file `bog-iron-workings.layout.json` is the source (0105 R59). The round folders are `tooling/.reports/16k/place.imperial-fringe.bog-iron-workings/round-N/`.

## Site

### The choice (type 7: works or landing)

The type 7 candidates were the 49 active `works` records. No `landing` type is active in the catalogue. The 20 landings carry ferry-stage or transit types. The candidates were ranked on the causal record and on the quest rows that anchor there. The third ranking was whether the vault holds the machinery of the works.

| Place | Zone | Quest rows | Machinery in the vault | Why not / why |
|---|---|---|---|---|
| **Bog Iron Workings** (`place.imperial-fringe.bog-iron-workings`) | imperial-fringe | LF67 (anchored) | the vanilla smelter (`furniture/smeltermarker`, Skyrim.esm `CraftingSmelterMarker1`, placed outdoors at Skyrim's mines; King of the Murkmire places it as `SmelterSTATIC`) and King of the Murkmire's forge set (`oaristys/forge`: coal pile, iron ore stack, ore bucket, iron ingots) | chosen: the kits can show the whole process of this works (ore, fuel, furnace, iron). LF67 needs a place feature (the deep end of the seep) that the frozen water already holds. The works depends on no unbuilt place and supplies the Cold Forge |
| Archon Bonded Row | saxhleel-coast | 5 | none (bonded warehouse: Imperial shells) | stands on Archon's quay, so it depends on a type-8 city that is not yet built |
| The White Pans | dunmer-north | LD57, LD91 | none: no salt-pan piece exists (saltpile only) | the pans themselves would have to be invented |
| Silyanorn Diggings | dunmer-north | 3 | Ayleid ruin, scaffold | depends on Stormhold (type 8). The diggings are a ruin entered sideways (type 5 ground) |

The contrast rule applies here. Claywater (type 1) stands 1.76 km west, a little south, in the same zone. Bog Iron Workings is a different type from Claywater. It is an Argonian works and is not a road station.

### The record (`world/sources/catalogue/places-imperial-fringe.json`)

- **why:** bog iron forms naturally here. Road crews that wear out nails and tools buy their iron here.
  Diggers from three villages work one season a year and think the work
  shameful. The seep is being worked out and the works would be abandoned without ceremony.
- **vibe** (edited at 5b, § Record changes): a squat clay furnace and its
  charcoal bed stand on a bench above the seep, with a plank hut beside them.
- **contents:** n1 the season's diggers (D2, few); c1 a creature in the deep end
  of the seep (D3; it was mis-filed as an npc slot, § Record changes).
- **sockets:** `scene.bog-iron-workings.the-mound`, `evidence...the-stained-boots`,
  `post...ore-digger`. **interior:** a single door, a dwelling, S1.
- **relations:** supplies the Cold Forge; reached via Cartwright's Cross and the Mile House.
- Promise ledger: `world/sources/placement/promises/place.imperial-fringe.bog-iron-workings.json`, 21 rows.

### The ground (`world/sources/sites/dossiers/bog-iron-workings.{json,md}`)

- The plotted anchor lies at 2004, 2599 at 15.5 m, with slope 6.6° and 0.23 m over the water table. It has no
  level cell for a hut pad.
- A level bench lies at x 1975-2000, z 2525-2545 (20.6 m, under 1.3° on the scan).
  East of the bench the ground falls 4-6° to x 2020 and then a steep bank leads down to the seep.
- The seep is `body.1117-1397` (marsh-deep, perennial, level 15.28 m). Its north lobe
  reaches z 2542 at x 2032-2044. Its deep end, 1.5 m of water, lies at 2040, 2556.
- A puddle at 1988-1992, 2520-2524 (level 20.5 m) lies 1.5 m from the hut pad.
- Ways: the Rim road (`route.road.gideon-stormhold`) runs east-west at z 2508.7.
  Three minor routes share a single line along the west shore of the seep at z 2607
  (`track.road.glenbridge-the-road-nisswo-house` and two more). None of them ends here.

### Quest provisions

- **LF67 Bog Iron, Deeper Pools** (skeleton, tier 3): the diggers stopped working
  the deep end of the seep without saying why. Needs: the deep end of the seep (frozen
  water, 1.5 m), the crew (n1, a `witness` purpose on their hut) and the creature in
  the pools (c1, fauna socket at the deep end).

### Lore read

- `world/sources/lore/topics/material-culture.md:53-57`: after Duskfall the
  Argonians almost never work metal. Bog iron is an attested Argonian material (UESP Lore:Black Marsh).
  The record's "they consider the work shameful" follows from this.
- `world/sources/lore/topics/fauna-hazards.md:109`: bog iron is listed among the minerals of the province.
- `material-culture.md` § Building: the crew's hut is a small King of the Murkmire plank house on posts. It is the only enterable shell that is legal here and whose linked cell passes the interior gate (walk 11; `culture-kits.json` imperial-fringe `visiting` row).

### Nearby places

Keeps-The-Lower-Water lodge lies 95 m north-west. Red Cart Yard lies 201 m north-west. Lower Onkobra Paddies lie 205 m west. None of the three is built. Claywater (1.76 km) is the sole built place in the zone. The claims register holds Claywater's signatures. The hut here takes a different dressing set and cell use.

## Brief

### The calls the ground forces

1. **The workings stand on the bench above the north end of the seep**, 60 m north of
   the plotted anchor (§ siting). The anchor has no level cell and stands on the
   water table.
2. **The way comes up from the seep track** and not from the Rim road, because the network-stitch
   rule refuses a footpath or track that continues a major road. The three
   minor routes along the west shore of the seep are the natural network of the place.
   The way runs 15 m along that line and then climbs north beside the water.
3. **The furnace floor is a pad** (apron 5 m, batter). The bench falls 4-6° there
   and every prop of the yard stands on the levelled floor.

### Rows

| Thing | Purpose | Kit piece (measured) | Rule or lore |
|---|---|---|---|
| Diggers' hut `b-hut` | the crew sleeps and keeps its stores; witness purpose for LF67 | `composite:plank/house1-with-door` (family `kotm-plank-house`), yaw 90, pad apron 3.0 m, seated by its reviewed designed sink 1.2 m; door faces east onto the way's end | record interior (dwelling, a single door); R83 linked cell |
| The furnace `bl-furnace` | the bloomery: it takes ore and charcoal and gives the bloom | see § Kit change; parcel piece on a 5 m pad | record vibe; R1 |
| Charcoal and fuel | the charcoal bed `bl-charcoal-bed` (`kotm:oaristys/forge/coalpile`, 3.5 × 4.1 × 0.44 m) is raked out before the furnace mouth on its west side; woodpile, chopping block | kit pieces, § Kit change | sitingPrefs "a drying rack for peat fuel": the racks had no exterior licence (R1), so fuel stands as stacks |
| Ore carry | hand cart, ore cakes heaped and in a bucket, full baskets by the furnace | `handcart02`, `kotm:oaristys/forge/orestack_iron` ×2, `orebucket_iron`, `basketfull`, `basket02`, `bucket01` | record why.siteAdvantages |
| Iron | the iron of the bloom stacked by the furnace foot | `kotm:oaristys/forge/ingotsiron01` | record lootTable materials |
| Crew stores | jars, sacks, crate, pail, small woodpile by the hut door | yard set `works-crew-stores` | 0098 clutter per dwelling |
| Cookfire | the crew's evening fire on the floor | `campfire01burning`, `saxhleelmetalpot01`, `paintedurn01` | R43 two light kinds |
| The way | track 2.5 m from the seep track to the hut door | path op | 97 C3; network stitch |
| Furnace path | footpath 1.2 m from the way to the furnace mouth | path op | pathReachRule; the front of the furnace faces it |
| Lights | candle by the hut door; the cookfire | `argoniancandle01`, `campfire01burning` | 97 C16 (lit entrance within 2 m) |

### Interiors

| Door | Shell | Cell | Why |
|---|---|---|---|
| `door.imperial-fringe.bog-iron-workings.1` | `composite:plank/house1-with-door` | `LilmothApothecaryHouse` (King of the Murkmire.esp, load door `088933E1`, tier A by `--claim`) | Of the linked set of the shell (AltenGeneralStore, LilmothIronworks, LilmothApothecaryHouse), this cell alone passes the interior acceptance gate. The crew sleeps in its double bed `088933BE`. |

In walk 11, `--claim` was run on a copy of the blueprint for each rejected shell. The round huts 02 and 03, the thatch houses 05, 06 and 08 and house3 were rejected. Their linked cells need meshes that the pool lacks. Those meshes are Creation Club fish, jungle trees and crafting benches. House2 (16.8 × 14.9 m) is too big for a single crew. The Imperial farmhouses were rejected because the record is Argonian. Earlier rounds rejected the mud pod, whose cells fail the bundle gate. Earlier rounds also rejected `kotm mudhut02`, whose load door is 6.7 m up. They rejected `mudmother mudhut01` as well, which has a Dragonborn Telvanni load door.

### Variety

The place has 1 shell. The shell is a single dwelling because the M1 works record holds one building. The signature is a plank hut and crew stores (`works-crew-stores`). The claimed pod sets look different from it.

### Approach (openworld-approach §5, short)

The place has a single approach, from the seep track. The water shows first through the reeds. The furnace at the top of the rise shows next. The hut shows last (`approaches[]`). The place has one way in and no raised level. The furnace is the sole landmark.

### Sockets and quests

Npc n1 works at the furnace. Npc n1 spends the evening at the cookfire. Npc n1 sleeps at night in the bed of the cell (`08095F78`). Fauna c1 lies at the deep end (2040, 2556, D3). The hut door is the entrance marker. Scene the-mound marks the furnace floor. Evidence the-stained-boots lies by the hut door. Post ore-digger stands at the bank head over the seep.

### Creative register

1. The furnace and its charcoal are the sole landmark of the place. It has no shrine and no sign.
2. The process reads in a line: ore up from the seep, cart, furnace, fuel, crew.
3. The hut of the crew turns its back on the road and its door faces the work.

## Kit change (works-v1)

The first layout stood the static `clutter/smelter/smelter01` and its `smelter01coal01` bed. Both are unplaced in Skyrim, with n 0, no setting licence and mesh-sill sinks. `setting.class` and `sink.fallback` were red because of that. Skyrim places its smelter as the furniture NIF `furniture/smeltermarker` (`CraftingSmelterMarker1`). `CraftingSmelterMarker1` has 25 references, in exterior town and wild. King of the Murkmire places the same mesh as `SmelterSTATIC`. The smelter was added to `works-v1`. It came with King of the Murkmire's `oaristys/forge` iron set, which holds an ore stack, an ore bucket, iron ingots and the coal pile. The first build shipped the hidden preview skeleton and body of the NIF. These showed as a mannequin and marker cards in the look sheet. `pipeline/blender/build_kit.py` now drops every shape that the NIF hides. A shape counts as hidden when the HIDDEN flag is on it or on a node above it. The script lists dropped shapes in `droppedShapes`. The smelter went from 27,083 to 1,174 triangles. Five other works pieces lost their trigger, ragdoll and anchor helpers. The drying racks (`wrherbdryingrack01`, interior only) are gone. The fuel is the woodpile.

## Diggings (walk 11, owner item 2)

The owner observed in walk 11 that the place had a forge. The place had no area showing the iron dug out of the bog. The dig is ground first and props second. The dig is at the south margin of the seep. The water there stands at 15.28 m and the ground at 15.3-15.4 m.

| Thing | Purpose | Piece | Rule |
|---|---|---|---|
| Three pits `seep-pit-1..3` | this season's pit, the water's-edge pit and last season's worked-out pit (why.pressures: the cakes lie further out each season) | `pool` ops, r 2.0-2.2 m, depth 0.5-0.6 m, rim 0.6 m | R73 (a basin is a pool op; no raster edit) |
| Spoil banks `spoil-bank-1..3` | the peat thrown out of each pit on its lip | `mound` ops, 0.5 m over the ground, blend 2 m | 0101 typed patch |
| Spoil heaps `sd-spoil`, `sd-spoil2` | the dug earth heaped south of the pits | `minecdirtmound02` x2 | dug-in rock seat |
| Duckboards `dw-plank1..14` | loose boards laid crosswise from the cart to the water's-edge pit | HTBM `tamu_woodplank02-04` (reviewed sink rows, walk 11) | R86: dry, on the margin |
| Cart `sd-cart` | carries the cakes up to the furnace | `handcart01` on a 0.5 m pad | scan `scan-w11.json` |
| Dig track | the spur of the way along the margin to the duckboards | footpath 2 m | R84 |
| Seep socket `seep-diggings` | fills the seep promise (a ground noun) | marker socket | promise class table |

Every prop stands outside the `radiusM + rimM` of each pool. The workbench seats props on the uncut ground. Renders of the pits come from `blender/examples/pool_look_shot.py`. No other render shows a pool.

## Record changes (5b)

- `lootTable.kinds`: `trade-access` was removed (the place has no trader or market and the hook
  says that visitors take the iron and do not buy it).
- `contents.npcs[n2]` ("D3 something in the deeper pools") moved to
  `contents.creatures[c1]` (apex-ambusher, D3, single). It is the LF67 creature.
- `assetPlan`: `stockade-scaffold`, `vanilla-farmhouse` (not an Argonian kit) and
  `landmark-civic` were replaced by what is built: `mud-mother-grove`, `works-props`,
  `argonian-props`, `argonian-lights`, `clutter`.
- `vibe`: silhouette, palette, materials, signatureFeature, condition and
  approach were rewritten to the built place (no orange water, no boot-boards and no
  stain, because the runtime draws none of them, R5).

## Lessons this slice

The report is `tooling/.reports/16k/walk9/place-type-7.md` § Lessons. The rows are filed as REQUEST rows. They are in `tooling/.reports/16k/place.imperial-fringe.bog-iron-workings/requests.jsonl`.
