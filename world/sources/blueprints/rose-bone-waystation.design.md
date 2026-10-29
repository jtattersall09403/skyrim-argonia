# The Tag House — design (16k walk 9, type 6 shrine, first slice)

The builder was the place-type-6 lane in walk 9, on 2026-10-01. The layout file `rose-bone-waystation.layout.json` is the source (0105 R59). Round folders are under `tooling/.reports/16k/place.imperial-penal-south.rose-bone-waystation/round-N/`.

## Site

### The choice

This is the first type-6 place, a shrine or sacred site. There are 45 active `sacred` records. The Tag House is `place.imperial-penal-south.rose-bone-waystation`, family `the-dead`, a bone-repatriation waystation of magnitude M1. The Tag House has the strongest causal record and the most quest weight of the 45. BC05 *Bones to the Dirt* (Chainbreakers) is the live faction quest of the province. BC05 names the Tag House as its promoted provision, `quest.provision.whiterose-prison-ruin`, in `docs/quests/25-quest-place-map.md`:95. Three local quests anchor on the Tag House: LR03, LR24 and LR39. Argonians who die away from the Hist, "even in stone prisons such as White Rose", return to the Hist if their bones are brought to the dirt. The lore is in UESP Lore:Argonian and `world/sources/lore/topics/prisons.md`:86-91. The place belongs to the `the-dead` family. Neither the Greenspring Hist shrine nor the Riverwalk Sithis totems represent the `the-dead` family. Teeth of Sithis (NI05) was rejected. Teeth of Sithis is a hist-sanctum dungeon of size S3 under xanmeer stone. Teeth of Sithis would make a dungeon slice and not a shrine. Bundle Racks and Carries-Them-Home were also rejected. Both belong to the same family but have a weaker quest load and no provision.

### The record (`world/sources/catalogue/places-imperial-penal-south.json`)

- **why:** the Chainbreakers built a station on the Blackrose road to receive
  the dead of the Rose. The families of the Rose release a body for a "carriage
  charge". This is the most resented transaction in the south.
- **vibe:** "a handover shed on a causeway with a bone-tag rack on the prison
  side and a wrapping bench on the village side and a painted line on the
  floor between them". The colours are tag-bone white, cloth grey and causeway mud. The mood is formal and
  unhappy.
- **interior:** dwelling S1, a single door: the tag-keeper's hut, linked to
  its own plugin interior (walk 11 record edit below). **sockets:** evidence
  `evidence.tag-house.carriage-charges`. **lootTable:** services,
  faction-access, lore-fragment. **contents.loot:** l1 ledger, l2 grave goods.
- Promise ledger: `world/sources/placement/promises/place.imperial-penal-south.rose-bone-waystation.json`, 17 rows.

### The ground (`world/sources/sites/dossiers/rose-bone-waystation.{json,md}`, workbench scans)

- The site is a low dry rise at 8-11 m, 3.2 m over the water table, with slope 3-6 degrees,
  falling north-east. The ground is firm lowland, danger band 2. No marsh or water lies within
  100 m and the nearest water is 113 m off. No causeway exists here.
- The footpath of the place (`track.imperial-penal-south.rose-bone-waystation`,
  `routes-minor.json`) starts at 2577.6, 6564.4 and runs east then north-east
  toward the villages. The Prison road (`route.road.blackrose-lilmoth`) passes
  189 m to the north-west.
- Neighbours within 500 m: the ferry stage (94 m), Murkwood Verge (111 m),
  the bonded stores (180 m), Blackrose (275 m, north-west) and Blackrose Prison
  (521 m, west-south-west). None is built.

### Quest rows

BC05 *Bones to the Dirt* is the procession from White Rose Prison. BC05 is live and is in `world/sources/quests/quests-factions.json`. LR03 *The Tag Not Returned*, LR24 *Out on Another Name* and LR39 *Tags for the Living* are skeleton quests. They are in `world/sources/quests/local-imperial-penal-south.json`. They concern bone-tags and the paperwork of the dead.

### Lore read

- `world/sources/lore/topics/prisons.md`:86-91, 125-127: bones in stone
  prisons must come home. This is the plainest quest premise in the sources.
- `world/sources/lore/topics/material-culture.md`:300-301: bone-and-tin
  chimes hang at every threshold and eave; :232 the grave-singer.
- `world/sources/lore/extrapolation/argonia-4e201-state.md`:165-167: burial
  runs through the Hist.

### Record defects found (fixed in the step 5b change set)

`lootTable.kinds` listed `faction-access`, which needs a guild hall, council or court. A roadside shed has no guild hall, council or court. `playerPurpose.primary` was `dungeon-delve` for a place with no dungeon. `deferredWhy` and `deferredFromStatus` survived on an active record. The "causeway" and "painted line" of the vibe did not match the ground or the kits. The "on the Blackrose road" of the founding did not match the ground. The ground is a dry rise 189 m off the road. No paint decal exists in the kits.

In Walk 11, `interior.family` read `civic-hall`, a hall of 100 m2 or more. The signature feature, the occupants and magnitude M1 all describe a handover shelter with the keeper's hut beside it. A tag-keeper is the sole occupant. No quest that uses the place needs a hall. BC05, LR03, LR24 and LR39 need the hut wall, the keeper and the ledger. The family is now `dwelling`. The dwelling is the keeper's hut, HTBM bamboohut02, of 67 m2. The plugin of HTBM places bamboohut02 in the village world of HTBM. The mined exterior has class wild and n 9. The build is unchanged.

## Brief

### The calls the ground and the kits force

1. **The shed is an open half pavilion.** HTBM `orcawninghalf01` (a thatched
   canopy on log posts, open at its straight front, 8.2 x 5.0 x 5.8 m) is the
   sole open-sided Argonian roof in the pools that shelters two parties at once.
   Its sink had no measured row (mesh-sill fallback, R36). It takes a reviewed
   `assetPlacement` row (-0.10 m, from its siblings bamboohut01/02 on the same
   stake legs, n 16) and settlement-stilt-v1 was refreshed.
2. **No painted floor line exists.** A row of three Argonian candle stands
   runs from the threshold across the floor between the two halves to mark the line.
3. **The keeper's hut is HTBM bamboohut02** (plugin-linked). Every one of its
   nine linked cells is a storage room and CIPHTBMHutInterior01 alone is fully
   sourced. The ledger is therefore kept outside at the keeper's table and the hut is
   the carriers' store.

### Rows (as built)

| Thing | Purpose | Kit piece (measured) | Rule or lore |
|---|---|---|---|
| Handover shelter `s-shelter` | where the dead change hands; front north onto both ways | `htbm:.../orcawninghalf01` (settlement-stilt-v1), pad apron 1.5 m with batter, worst edge 0.70 m | prisons.md:86-91; R36 policy row |
| Arrival half (yard set `handover-arrival-side`) | the Rose side: closed baskets that carry the remains, an urn | `basketclosed01` x3, `paintedurn01` | record vibe |
| Tag chimes `s-chime1`, `s-chime2` | the tags: chimes hung under the arrival eave, one tag on each | Sleeping Tree `windchimehavok` (exterior licensed), `mount --hang` on the canopy (unmined, reader-approved r2) | material-culture.md:300 |
| Released bones `s-bones-skull1..3`, `s-bones-spine`, `s-bones-rib1`, `s-bones-rib2`, `s-bones-arm` | the dead as the Rose hands them over: skulls and a spine at the arrival front; two ribcages, a skull and an arm bone laid on the arrival-half floor among the tag baskets, awaiting their tags (audit10 c5, P5) | kotm `issgard_boneargonianskullfull`, vanilla `humanspine`, `humanribcage`, `humanarmleft` (settlement-root-v1), settled on the ground | why.founding (`thing-bones`) |
| Candle row `s-line1..3` | the line between the two halves, lit | mudmother `argoniancandle01` | record vibe (line) |
| Departure half (yard set `handover-departure-side`) | the villages' side: wicker bench, wrapped bundles, urns, cloth basket | HTBM `wickertable01`, `miscsacklargeflat01` x2, `paintedurn01` x2, `basketfull` | record vibe (wrapping bench) |
| Waiting bench and brazier `p-bench`, `p-brazier` | the families of the Rose wait outside the west corner | `farmbench01`, `impbrazier01` | record pressures |
| Keeper's hut `b-keeper` | the keeper of the Chainbreakers; the carriers' stores | `composite:stilt/bamboohut02-with-door`, pad apron 2 m (s 6, w 3) with batter | R83 linked cell |
| Keeper's yard (yard set `keepers-yard`) | the fee counted and written down at the door | `wickertable01`, `wickerchair01` x2, `basketsmall01`, `miscsacklarge`, `wickerbasket01`, `paintedurn01`, `firewoodpilemedium01` | record occupantsMotive |
| Door light, totem, eave chimes `k-candle`, `k-totem`, `k-chimes` | the threshold of the hut; the chimes hang from its eave (LR39's "Tag House wall") | `argoniancandle01`, `argoniantotem01`, `windchimehavok` hung (`mount --hang`, unmined, reader-approved r2) | material-culture.md:300 |
| The villages' way | the end of the track, past the hut to the east corner of the shelter | footpath 2.0 m | seams |
| The keeper's path | spur to the door | footpath 1.5 m | R84 |
| The Rose's way | from the west corner of the shelter down toward the Prison road | footpath 2.0 m, leaves the place | seams |

`breadth-bars.json` has no bar for type 6, so type 6 falls back to the M1 hamlet column. The place counts one building and one structure. The place is built below every column of the bars. The breadth gates report this and R33 does not bind. The place has 2 light kinds: candle and brazier. The place has 14 dressing kinds.

### § Interiors

| Door | Shell | Linked cells | Claim | Why |
|---|---|---|---|---|
| `door.imperial-penal-south.rose-bone-waystation.1` | bamboohut02 | CIPHTBMHutInterior01, 03, 07, 08, 11, 13, 15, 16, 17 (all storage) | CIPHTBMHutInterior01, tier A | this is the only fully sourced cell (the other eight miss five Dragonborn clutter forms and a furniture form). It is the third use in the province and the first in the region (R4) |

The shelter has no door. It is an open structure that is entered on foot (R18).

### § Containers and items

- Container: `s-hv-urn1` (urn, authored loot, grave goods: record l2).
- The ledger (record l1) is the evidence socket at the keeper's table.

### § Creative register (calls unlike Claywater, Greenspring, Riverwalk)

1. The use of the place splits it in two: an arrival half and a departure half
   stand under one roof, each dressed for its side.
2. Light marks a boundary: the candle row is the line the dead cross.
3. The side of the Rose is Imperial (a farm bench and an iron brazier). The
   side of the villages is Argonian (wicker and mud-ware).

### § Sockets

| Socket | Kind | Host | Why |
|---|---|---|---|
| `idle-keeper-tags` | idle tend | `s-hp-basket1` | the tag-keeper opens each basket and hangs its tag on the chimes |
| `idle-keeper-home` | idle sleep | under the shelter's thatch | the tag-keeper sleeps beside the dead who await their journey (the hut's cell has no bed) |
| `npc-tag-keeper` | npc, roster slot `tag-keeper` | the shelter front | morning at the tags, afternoon at the keeper's table, night under the thatch |
| `evidence-carriage-charges`, `scene-procession`, `marker-keeper-door` | marker | keeper's table; shelter front; keeper's door | the record's evidence socket, BC05's stop, the door |
| `idle-wrapper` | idle tend | `s-hv-flat1` | the carrier ties off the wrapped bundles |
| `idle-family-waits` | idle sit | `p-bench` | a family waits for the fee |
| `idle-keeper-counts` | idle work-at | `k-ty-table` | the keeper counts and writes |
| `container-grave-goods` | container urn | `s-hv-urn1` | the grave goods |
| `q-evidence-carriage-charges` | quest evidence | the keeper's table | the record's evidence socket |
| `whiterose-prison-ruin-procession` | quest scene | the shelter front | BC05's procession stops here |

The record gains a notable slot, the tag-keeper, in the step 5b change set. The tag-keeper receives the fee and writes the fee in the ledger. The `services` reward needs an npc socket.

### § Seams

The place is off the road. The villages' way continues the minor track of the place from its terminal `terminal.rose-bone-waystation.villages-track`. The Rose's way leaves the place toward the Prison road. The Rose's way is unpainted beyond the place. The place has no ferry, berth or sign.

### § Approach (openworld-approach §5)

Approach check 1 passes with two approaches: the track from the east and the grass from the Prison road. Approach check 2 passes. Approach check 3 passes: the hut and the thatch stand on the rise over grass. Approach check 4 passes: the hut drops behind the slope. Approach check 5 fails: the villages' way is straight for 20 m. That straight length is a short end of a 300 m track that bends twice before it. Approach check 6 passes. Approach check 7 is n/a because the place has no gate. Approach check 8 passes: the villages' way is the spine. Approach check 9 passes: the shelter is the beacon. Approach check 10 passes. Approach check 11 passes: both ways end at the shelter. Approach check 12 is n/a. Approach check 13 passes: the batter edges of the two pads. Approach check 14 passes: 1-3 people and two buildings. Approach check 15 passes. Approach check 16 is n/a.

## Lessons this slice

The lessons are filed as REQUEST rows. The rows are in `tooling/.reports/16k/place.imperial-penal-south.rose-bone-waystation/requests.jsonl`. The integrator applies the rows.

1. Yard sets laid by `group place --parcel` are not bound. Every member
   needs its own `bind` op (tooling row: the tool binds them).
2. Read the post clusters of an open structure (`blender/examples/post_clusters.py`)
   before dressing it. Leave a free walk cell by every yard-set table.
3. Yard sets beside a padded building stand on the flat of the pad and not on its
   batter (`apronBySide`).
4. HTBM bamboohut cells are storage rooms with no bed, so the keeper sleeps
   under a roof elsewhere.
5. Read the setting licence of every outdoor piece before the layout.
   `argonianbonechime01` and `wrherbdryingrack01` are interior-only and
   turned `setting.class` red after the first publish. A hanging chime
   (`windchimehavok`) stood on the ground passes `check` (tooling row).
