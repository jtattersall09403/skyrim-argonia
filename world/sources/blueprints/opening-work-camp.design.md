# Gang Ground: design (16k walk 9, type 9 early-game place, first slice, DRAFT for the owner)

The builder is the place-type-9 lane, walk 9, 2026-10-01. The layout file `opening-work-camp.layout.json` is the source (0105 R59). Round folders are `tooling/.reports/16k/place.pirate-freeholds.opening-work-camp/round-N/`. Type 9 is owner-guided (0062 § 9). This design is a draft for the owner to steer. It was applied with `--owner-guided`. The flag names the owner's walk-9 reply ('build one of each place type').

## Site

### The choice

The three type-9 candidates are the work barge (The Roll, M1), the camp of the gang (Gang Ground, M2) and the Corimont crosstrees (M1). MQ01 *No Name on the Work Roll* starts on the barge. MQ01 ends its first night at the camp. The crosstrees is an optional vantage inside Alten Corimont (type 8, unbuilt).

Gang Ground is built first.

- **The barge cannot be built from the pool as its record describes.** The
  record asks for "a flat barge with a plank shed amidships and a crane frame
  at the bow". Every boat folder of the vault was listed (vanilla ships and
  wrecks, Ships and Boats of Tamriel, DK Boats, Of Ships and Boats, Cyrodiil
  Ship and Boat Resource, Skyrim Ferries, Rowboats of Skyrim, Sailboats
  Expanded, King of the Murkmire). No flat barge exists. The nearest pieces are
  a full-rigged trade ship (King of the Murkmire `shipeectradeship01`, whose
  plugin links it to the `MurkmireTravelShip*` cells, a ready processing hold)
  and the Bretic `shipbreticgreyteship_hull01` (a hull with no rig). Either
  piece changes what the barge is. That is an owner call (packet decision 1).
- **The plot of the barge is also in question.** It lies 406 m from Alten
  Corimont against its own "inside 250 m" constraint, in a 25 m pond at sea
  level walled by 15 m bluffs.
- **The camp depends on nothing unbuilt** and holds most of the physical
  provisions of MQ01: the clutch (`opening-egg-clutch`), the camp states
  (`opening-camp`), the witness and the root route. Its record names the barge
  as `dependsOn`, but only through the gang that sleeps here.

### The record (`world/sources/catalogue/places-pirate-freeholds.json`)

- **why:** a dredging gang owes months on the barge. Its families live on the
  bank within walking distance of the roll and the clutch keeps them there.
- **vibe:** low sheds stand along a bank. A long shed set back from the water is
  banked with earth (the hatching shed). Plank walkways cross the wet ground and
  amber lamps burn at night.
- **interior:** dwelling S1, two entrances. **sockets:** scene camp-night,
  clutch-dies, choose-a-witness; evidence dead-clutch; post rest; marks
  hatching-shed, root-route. Promise ledger:
  `world/sources/placement/promises/place.pirate-freeholds.opening-work-camp.json`, 33 rows.

### The ground (`world/sources/sites/dossiers/opening-work-camp.{json,md}`, workbench maps and scans)

- The anchor (3991.5, 1395.6) stands 21 m up a slope of 16 degrees, 22 m
  above the marsh to the north (body.2442-1212, level 0). Below it lies a strip of
  bank 10-15 m deep at 0-0.8 m beside 0.1-1.2 m of water. Behind the strip the bank
  rises 15 m in about 10 m.
- The western side of the same slope (x 3925-3955, z 1380-1430) falls at
  8-12 degrees, 11-18 m up, between the Border road
  (`route.road.stormhold-thorn`, which loops round it to the south and east)
  and the marsh. Scans pass pads there for every shelter (round-1 scans 1-4).
- The gang's walk (`track.track.pirate-freeholds.gang-walk`) arrives from the
  barge at 3987, 1393, beside the road. The barge lies 183 m south-south-east of
  the middle of the camp, out of sight behind the ridge.

### Quest rows

MQ01 *No Name on the Work Roll* covers the raid, the fire, the clutch that dies that night and one witness saved. MQ32 *Names Written in Sap* has an epilogue that reads the camp back. Both quests are in `world/sources/quests/quests-main.json`.

### Lore read

- `world/sources/lore/topics/labour-and-bondage.md`:52-118: the Owing; a
  debtor's food added to the account; the washed-out look of those kept from
  their Hist.
- `world/sources/lore/extrapolation/argonia-4e201-state.md`:166: eggs, names
  and burial run through the Hist (the reason that a clutch cut off from it dies).

### Record defects found (for the step 5b change set)

- `plotFacts.dangerBand` is 3 against the hard constraint "danger band 2 or
  lower" (the sitingNote holds it at D1).
- `vibe.approach` says "the walkway from the water runs straight past the shed
  door" and "low sheds along a bank". The bank is a bluff here. The camp is
  terraced on the slope and entered from the Border road.
- `lootTable.kinds` `rest-shelter` needs a lodging parcel (built: the
  west sleeping shed carries `lodging`).
- The barge record: 406 m from Alten Corimont against "inside 250 m".

## Brief (draft, as applied in round 4)

| Thing | Purpose | Kit piece (measured) | Rule or lore |
|---|---|---|---|
| Hatching shed `b-hatch` | the clutch, kept dry on the top terrace | `composite:stilt/bamboohut01-with-door`, pad apron 1.5 m (n 2.5, w 2.0) with batter, worst edge 0.97 m (scan 4) | record signature; claim CIPHTBMHutInterior04 |
| Overseers' hut `b-over` | the brokers' two overseers | `composite:stilt/bamboohut02-with-door`, pad (e 3.0), worst edge 1.18 m | record occupants; claim CIPHTBMHutInterior01 (third and last use, R4) |
| Sleeping sheds `s-shed1`, `s-shed2` | the families sleep under open thatch on the lowest terraces | htbm `orcawninghalf01` (open-fronted and doorless, R18) | record silhouette |
| Family tents `t-tent1`, `t-tent2` | two households | mudmother `argoniantent02` | record materials |
| Cookfire `y-fire`, pot, urn, bench | the fire of the camp on its own levelled hearth | `campfire01burning` pad 1.5 m; KotM pot; mudmother urn; `farmbench01` | record senses |
| Stores, cookpot, nets | the stores of each shelter and the fishing gear of the families | yard sets `hist-village-stores` x3, `hist-village-cookpot`, `hist-village-nets` | type 2 sets |
| Hatching-shed threshold | amber lamps, totem, candle | two mudmother `argonianlanterns03` hung from the eave beside the door (`mount --hang`, unmined, approved on the round-1 close-up `11-front-h-lamp1.png`), `argoniantotem01`, `argoniancandle01` | record palette; lit entrance |
| Overseers' door | lit entrance | `argoniancandle01` `o-candle` 1.7 m from the threshold, south of the walk line | 0102 decision 7, R89 |
| The way down | the gang's one way from the camp to the landing and the barge, findable from the yard by the fire-bowl and poles at its head | `mound` ops `wd-head`, `wd-cut` (ramp), `wd-turn`; KotM `stairs02` mined pair `wd-a2`/`wd-a`; Kothringi `tamu_woodpole01` poles; Xanmeer `sconce2` | cliffWay.connected from the camp path start to the water; decision 0102 (the place's own ground) |
| Ways | road-way (from the Border road paint), yard-way and four spurs; the gang walk, a 2.5 m track way that starts on its terminal and continues the line of the boardwalk (27 deg off at first, 15 deg after the bend) | footpaths 1.5-2.0 m, track 2.5 m | R84, 97 C-stitch |
| Yards and door grades | the stilt shells stand on their posts with no pad (ruling 70); the store, net and clutch corners and both doors are graded instead | `mound` ops `yard-east-stores`, `yard-west-stores`, `yard-west-nets`, `yard-hatch-stores`, `yard-hatch-clutch`, `yard-hatch-door` (earth pad to the sill), `yard-over-door` (dug ramp); tent aprons narrowed to the 0.6 m edge bar; `h-oven` has its own 1 m pad | ruling 70; R170 earth pad |
| Sockets | 11 layout markers (2 entrance, 4 scene, evidence, 2 mark, post) with `fills`; sleep sockets hosted on their shelter parcels; the overseer sits on the bench by day and night | layout `socket` ops | 0103 decision 6, R95 |

## Creative register

- **The barge hull (walk 11, rulings R107).** Two hulls from the published watercraft kit were
  tried at the same berth pose (water 1.0-1.2 m deep, keel in the silt) and rendered from the same
  two cameras (`tooling/.reports/16k/walk11/places-a/renders/b-cmp-{bretic,trade}-{landing,camp}.png`).
  The reader preferred the Bretic hull without a rig (`sbot:.../shipbreticgreyteship_hull01`). With
  no masts, rigging or sails it reads as a stripped hulk. The trade ship (`shipeectradeship01`)
  reads as a ship that could sail. Its rig would also block the swing of the crane. The Bretic hull was kept. It lies
  east-west at (3965, 1345.3), bow to the landing.
- **What the deck really is.** The hull has no open 11 x 25 m deck. It has a raised bow castle
  (deck 4.9-6.3 m over the water, sloping up toward the bow), a sunken waist (2.2-2.5 m, cambered,
  with a hatch and its coaming at x 3963) and a stern castle (5.0-7.3 m). These figures were measured on a 1 m grid
  (`work/b-hull-grid.json`). The deck plan follows that shape. The open lean-to shed
  (`orcawninghalf01`, `g-shed`) fills the waist and is the processing station. Its back posts rest
  on the hatch coaming. The Hlaalu dock crane (`crane01`, `g-crane`) stands on the bow castle,
  pitched -8.5 deg to the slope of the castle, with its arm swung out over the shore side. Two stacks of sawn
  planks (`g-planks1`, `g-planks2`) are the hauled load on the stern castle. All are seated on the
  deck geometry (`wb.py mount --unmined --inside` on a hull, rulings R108).
- **The hull stays whole (gg-d2).** The reader of the d2 renders saw a clean ship. The barge is in
  daily use, so it keeps its sides. No mod makes broken planks or bare ribs that fit this hull.
  Loose boards leant on it would claim damage that the mesh does not show. The work shows in the crane,
  the shed, the stacked planks and the sacks on deck.
- **The way down is two legs cut into the bluff, with no stair (16x part 5).** The owner saw no way
  down. Readers saw any stair on the open face as a ladder up a cliff. A work crew would cut a
  switchback in the earth, so the way is now two cut legs. The camp path curves east past the cart
  to a level shelf on the lip. A lit fire-bowl stands there. Two poles mark the top of the cut
  (`wd-head`, `wd-sconce`, `wd-post-n`, `wd-post-s`). The upper leg is a path cut into earth banked
  against the face. It falls west at 27 degrees, under the 30-degree walk limit (`wd-cut`). It ends on a bench of banked earth in the corner of the west bluff, where the
  way turns (`wd-turn`, stake `wd-bank-stake2`). The lower leg turns back east along the foot of the
  cliff at 29 degrees (`wd-cut2`). It ends on the dry shelf at the head of the plank landing (`dk-0`).
  The head is at 10.25 m, the turn at 6.2 m and the shelf at 0 m. The shelf is too narrow for a
  third leg.
- **The way down reads as dug earth (16x part 7).** Readers at eye height saw the worn path paint
  as the colour of the ground, so the way did not read as built. The way is now painted
  `track_cut`: dark cliff dirt with a crisp edge. It is a clear step darker than the rock and scrub
  around the cut. It runs from the camp over the head, down both legs and onto the head of the plank
  landing (`dk-0`). The head shelf has no stake now. From the camp, any pole beside the gateway read as
  a third gateway pole. The remaining stake stands at the turn (`wd-bank-stake2`).
- **The join and the shoulder (16x part 8).** The way's cut earth now runs on from the foot of the
  lower leg onto the head of the plank landing as its own short way (`the-way-down-join`). The cliff
  way's route still ends at the head of the flight. The lower leg's mound (`wd-cut2`) blends out
  3.5 m instead of 2 m, so the leg sits on a wider bench. Laid logs were tried as shoring along both
  legs. They passed every check, but readers saw them as stray poles on the cliff, so they were taken
  out. Heavier shoring is a polish row (P1, backlog).
- **Material budget 130 (gg-d2).** This place holds two catalogue records: the camp and the barge
  (`place.pirate-freeholds.opening-work-barge`, tied to the camp by `boundTo`). The hull, the
  crane, the deck shed and the rowboat of the barge bring 32 materials that no other piece shares. The crane alone brings 15.
  The cap of 130 covers both records. The place uses 127 (`tooling/.reports/16k/walk11/gang-ground/d2/materials.txt`).

## Lessons this slice

- The skeleton schema costs a first slice most of its rounds: standard-2 ids, `parcel` against `parcelId` (a quest socket that a parcel's `playerPurpose` names carries both), `rosterSlotId` = the slot ids of the record. Recommendation: `wb.py skeleton`.
- A camp below a trunk road takes no road terminal (a footpath cannot continue a trunk and the join must also run within 20 degrees of its line). Its way in ends on the road paint. Its single network terminal is the track that serves it.
- Every yard-set member is bound to its parcel by uid. Otherwise the compile drops the member and every socket hosted on it.
- `argonianlanterns02` draws its flame at the eave (kit row `anchorClass` ground). Hang `argonianlanterns03` (lessons, buildings-doors-and-composites).
- A record roster that names a person twice needs two npc sockets. The duplicate `contents.npcs` row (n2) was dropped from the record.
- The provision fill subject and the multi-anchor quest premise were tooling gaps. They were fixed at source with a test each (`blueprint_promises.fill_subjects`, `record_coherence` anchor rule).

§ Interiors: door 1, the hatching shed, leads to CIPHTBMHutInterior04. CIPHTBMHutInterior04 is tier A and is a storage room. The clutch's room is the owner's call (packet decision 3). Door 2, the overseers' hut, leads to CIPHTBMHutInterior01 (tier A).
