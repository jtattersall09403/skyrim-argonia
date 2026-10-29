# Nine Bends (`place.pirate-freeholds.upriver-hist-village`) design

Nine Bends is a Type 2 Hist village, magnitude M3, in pirate-freeholds. The village is Argonian. Its type sheet is `.claude/skills/place-build/references/types/02-hist-village.md`. Part A covers steps 0-2 of a first-of-type-in-region build. The build is walk 11 new-places wave 1. The brief is `tooling/.reports/16k/walk11/new-places/briefs/nine-bends-a.md`.

## Distinguishing features (dressing.md § 7, walk 12)

1. The hatchery pool cut into the bank under the tree's roots (`hatchery`, `hist`, `hfl1`-`hfl4`).
2. The bend markers: a carved post at the west end of the houses lane and marker poles along it, one for each bend counted on the way to the tree (`ft-totem`, `ft-pole1`-`ft-pole3`).
3. The drying way: racks of fish and cane leaf along the lane between the two halves of the village (`ft-dryrack`, `gap-rack1`-`gap-rack3`).
4. The canoe beach: the village's canoes drawn up on the bank north of the landing stage (`ft-canoe1`, `ft-canoe2`, `dock1`, `dock2`).

## Site

The site packet is `tooling/.reports/16k/place.pirate-freeholds.upriver-hist-village/site-packet.json`. The dossier is `world/sources/sites/dossiers/upriver-hist-village.md`. The promise ledger is `world/sources/placement/promises/place.pirate-freeholds.upriver-hist-village.json`. The promise ledger has 34 rows.

- Record: `world/sources/catalogue/places-pirate-freeholds.json`, positionM (3462.8, 1433.9).
  why: a tribe keeps its Hist nine bends above Alten Corimont and hires its adults out to the
  gangs downriver. Fewer adults stay each year and the tree-minder has noticed. vibe: quiet, with too few people
  for the size of the village; cut reed, mud render, split cane walkways and a carved landing stage; wet
  green, sap-white trunk and dull red fired-clay hatchery lids. The signature is the hatchery pool cut into
  the bank so that the roots of the tree run down into it. The silhouette is a broad low tree with a ring of
  houses round its foot, with the river bending away on both sides. Approach: the chimes are heard a bend
  downstream.
- Services: lodging, shrine, trader. Occupants: D1 tribe, D1 tree-minder (named keeper n1),
  family band n2 (households whose adults are downriver) and pond guar kept for the warmth of the hatchery
  (c1). Notable slots: npc.opening.tree-minder, npc.opening.upriver-elder.
- Sockets: evidence.opening.harvest-cut; mark.opening.hatchery-pool; mark.opening.tree-foot;
  post.rest.nine-bends; scene.opening.tree-withdraws. Local states: speaking (chimes, lit
  hatchery, minders on the landing) / withdrawn (no chimes, pool covered, village indoors).
- Interior record: building / dwelling, S1, entranceCount 2, exteriorShell, verticalRelationship "behind".
- Quests: MQ01 (live; the Hist withdraws over a dead clutch, provision
  quest.provision.opening-hist-withdrawal; quests 25 :48, :153, :174), LP13 (village fish traps
  where the boats of the free port now load), LP14 (the same cut mark at the waterline on nine bends:
  the evidence socket) and LP19 (a clutch from No-Tree, 233 m away, named under this tree).
- Ground (dossier): centre 1.0 m, 0.97 m above the local water table, slope 10.2 deg facing 296;
  disc slope p50 5.4, p95 19.8; buildable 19.5 ha (39 %). Marsh-deep water (body.2442-1212,
  level 0.0) lies 11 m from the centre, with the shore 5 m away. Green: manfern, bamboo, bracken, fungal pod.
  Concealment is 0.96 (the record's "no road within sight" holds).
- Seams: the own track of the place `track.pirate-freeholds.upriver-hist-village` terminates here
  (0 m). The Gang Walk boardwalk to Gang Ground passes 159 m SE and the Border road passes 366 m E.
  Decision: the place stands off the road. The village is reached by its own track and by water (traversal boat,
  walk, swim).
- Built nearby: Gang Ground (`opening-work-camp`, 530 m; htbm-bamboo top), The Roll (barge,
  515 m) and No-Tree (233 m, unbuilt). The place must not repeat the bamboo-hut fabric of Gang Ground or the
  mud pods and ancient sleeping tree on a mound at Greenspring.
- Lore: `world/sources/lore/topics/hist-placement.md` (register row needed before the brief),
  `world/sources/lore/topics/hist-and-sap.md` (record source).

### Record defects and rule gaps (step 0 item 5), filed in
`tooling/.reports/16k/place.pirate-freeholds.upriver-hist-village/requests.jsonl`

1. entranceCount means two things in the tooling. The promise ledger reads it as "the principal
   interior, entered by N doors" (`blueprint_promises.py:702`). `record_coherence.relation_failures`
   (`record_coherence.py:499`) counts every claimed load door in the whole place (Greenspring 6,
   Claywater 4). Lead ruling (walk 11, brief `nine-bends-a2.md`): it is the total of load doors
   that the built shells carry, so no two-door house is needed. The built total is 5 and part C rewrites
   the record to it (std 12). The wording of the ledger stays a tooling sub-lane row.
2. Distance: "a day upriver" / "nine bends" against 530 m to Gang Ground. This is province scale. It is noted
   for 5b and no change is proposed.
3. vibe.materials named "split cane walkways", but every built way is an earth track (the-way,
   north-way and the house steps). Part C2 rewrote the line to match the build: bundled cane at the
   cane block and earth tracks between the houses (0102: the record follows the build).

## Palette

- The top shell family is `kotm-thatch-platform` (4 of 7 buildings: thatchhouse06 x2, thatchhouse05 x2,
  with-door composites), the Seekhat-Yol fabric of King of the Murkmire. It is top in no other published
  place. The second family is `htbm-bamboo` (3: bamboohut01 with door, orcawning01, orcawninghalf01), a
  home family of the region. It is kept below the thatch so that the bamboo fabric of Gang Ground is not repeated.
- The Hist is the `histtree01` of King of the Murkmire (24.9 x 27.1 x 24.4 m, broad and low,
  plugin-measured sink n 8). The sleeping tree of Greenspring and the Mud Mother tree (mesh-sill
  sink, R36) are not used. The setting class of the Hist is not in the published manifest (interior kit).
  The setting miner, run to /tmp/nb-setting.json, reads it as exterior village 2, ruin 6, wild 1
  (King of the Murkmire places it outdoors at Root-Whisper and Huluxinoag). This is filed as a request.
- Root `hist_root05`; chimes `tamwindchime01` (Seekhat-Yol hangs them outdoors, setting miner
  n 17); lanterns and candle stands from Mud Mother; totems `argoniantotem01`; fired-clay lids
  `potteryplate02` and painted urns `paintedurn01`; eggs `dragoneggs1/3`. The landing uses two vanilla
  `dockstrent02` lengths at the mined pose of the Claywater pair. The "carved" landing stage of the record
  is a 5b line for part C, because the pool searched here holds no carved Argonian dock piece.
- Lead ruling 2: the hatchery is the `pool` op at the toe of the bank, with no egg-tenders cell.

## Intent

1. Purpose. "The tree's island": a tribe keeps its Hist on a low island nine bends above Alten
   Corimont and hires its adults out to the gangs downriver. The residents are the tree-minder and the
   elder who houses strangers. The children and grandparents of households whose adults are
   on the rolls of the gangs live here too. They fish, cut cane, tend the clutches in the pool and wait for boats.
   Coin and news come up by boat to the landing.
2. Mood: sacred, quiet and too empty. The place is sacred because the tree stands on the highest ground, the shrine at its
   foot faces the arriving walker, chimes hang on its river side and the root runs down into the hatchery.
   It is quiet and too empty because seven buildings are spread round a common built for more, one house frame
   stands half taken down at the north edge, two houses share a cell plan and few lights burn.
3. Images. Far: a broad low crown over the reeds, with chimes before the bend (the Hist, chimes).
   Threshold: the trade house beside the way and the two totems at the foot of the trunk. Heart: the
   pool under the bank, with the clay lids in a row beside it and the root running into it.
4. Region, palette, climate. The setting is fringe marsh over firm lowland (`sitingPrefs.regionClasses`).
   Weather in marsh is ground mist 3, clear-humid 2, monsoon 2, storm 1
   (`weather-states.json`). Ground: firm mud and grass on a 1-3 m island. Water: the slow
   river on three sides, with the deep bend (body.2442-1212) east and south of the tree. Vegetation:
   manfern, bamboo, bracken, fungal pods (dossier). Building: thatch and plank on short stilts,
   with a single bamboo house. Light: candle stands at doors and two lanterns in the tree. Air: mist off the
   water in the morning.
5. The ground. The island lies at 0.5-3.5 m with a bump on its south-east, a steep east bank to the
   river and a gentle north-east shore. The tree takes the bump. The houses stand on padded
   ground west of it and the hatchery takes the flat toe of the bank.
6. Day, night, rain. Lit at night: a candle stand at each door, two at the shrine, one at the
   hatchery and two lanterns in the tree. Rain falls on thatch. The guar take shelter under their awning.
   Sound: chimes, water, insects and few voices.
7. Age and wear. The village has seen sixty years of use. The houses are mended and not new. One frame stands half taken
   down. The trade house is the newest and was built the downriver way.
8. Promises as beats, in walking order: the track (approach), the trade house (trader), the
   shrine and tree foot (shrine, tree-foot mark, the withdrawal scene), the elder's door (lodging,
   rest post, safe interior), the minder's house (tree-minder), the hatchery pool and its lids
   (hatchery mark, harvest cut on the trunk above the root), the landing (LP14 waterline mark) and
   the fishers' house and rack (LP13's fishers).
9. Not repeated: the bamboo fabric and muster yard of Gang Ground and the mud pods, rune
   circle and sleeping tree on a mound at Greenspring.

## Walk-through

1. Far (from the river, about 200 m east, eye 3474,1600 looking at 3447,1444): the broad crown
   over the reeds and the chimes; sacred. From the track the crown shows first (eye 3330,1470
   looking 3447,1444).
2. Approach: the way comes up out of the marsh at the west shore (terminal 3407.4,1456.4) and
   runs on along the line of the track past the trade house (3416,1446.5); quiet. Camera eye 3409,1447 looking 3440,1444.
3. Threshold: the two totems and candle stands at the west foot of the trunk (3440.4,1444); sacred.
   Camera eye 3430,1443 looking 3441,1444.
4. Heart: the common between the elder's, minder's and kin houses and the tree. The walk then goes round the
   north of the trunk to the bank top and the guar shelter; too empty. Camera eye 3436,1436
   looking 3447,1444.
5. Reward: the hatchery under the bank, with lids in a row and the root in the water; the minder's
   cell and the elder's bed. Camera eye 3467,1442 looking 3462,1449.
6. Exit: the landing runs out east into the bend (3468-3483,1440) and the way back runs west to the
   track. Every path ends at a door, the shrine, the hatchery or the landing and none dead-ends.

Approach questions follow world 97 §5. The crown is seen first, taller than the trees. The way is the sole cleared line through the reeds. The shrine faces the walker as the way reaches the tree. At night the door candles mark the ring.

## Brief

| Thing | Purpose | Kit piece (measured) | Rule or lore |
|---|---|---|---|
| The Hist (`hist`) | The reason for the village; heart, far image | `kotm:argonia/trees/hist trees/histtree01`, 24.9 x 27.1 x 24.4 m, sink p50 -1.02 plugin n 8, yaw 135 (burial 0.46 m, allowed 0.64) | hist-placement.md § 3 (Nine Bends row) |
| Root into the pool (`hist-root`) | Signature: the root runs down the bank into the hatchery | `hist_root05`, 6.7 x 12.6 x 9.8 m, plugin sink | record signatureFeature |
| Hatchery pool (`pool` op) | Signature; mark.opening.hatchery-pool | r 2.2, depth 0.6, rim 0.4 at (3464.5, 1446.8) | lead ruling 2 |
| Hatchery lids x4, eggs x2, urn, candle | The clutches under fired-clay lids; lit hatchery (speaking state) | `potteryplate02`, `dragoneggs1/3`, `paintedurn01` (pad 0.3), `argoniancandle01` (pad 0.3) | vibe.palette "dull red of fired clay hatchery lids" |
| Shrine (`hist-shrine` parcel) | Shrine service; tree-foot mark; withdrawal scene | 2 `argoniantotem01`, `paintedurn01` on a 2.6 m pad, 2 `urn01/02`, 2 candle stands | type 2 sheet; R94 facing west |
| Chimes x3 | vibe.approach: the chimes carry downstream | `tamwindchime01` hung on the Hist (`mount --hang`, bearings 120/150/175) | R53; reader approval r1 (part B) |
| Lanterns x2 | Lights in the tree over the shrine and the bank | `argonianlanterns02` hung (265, 105) | R53 |
| Minder's house | npc.opening.tree-minder; n1 | `composite:plank/thatchhouse06-with-door`, 12.5 x 8.7 m, pad apron 2.5 | doors-interiors-sockets §2 |
| Elder's house | Lodging (109 m2), rest post, safe interior | thatchhouse06 with door, pad apron 2.0 | promise_classes lodging >= 100 m2 |
| Trade house | Trader; the house built the downriver way | `composite:stilt/bamboohut01-with-door`, 8.2 x 8.2 m, pad apron 1.5, door south onto the way | promise_classes trader >= 16 m2 |
| Kin house | n2 households | thatchhouse05 with door, pad apron 2.5 | |
| Fishers' house, rack | LP13's fishers; work-at socket | thatchhouse05 with door; `fishracksmall` (pad 0.3) | |
| Empty frame | "too few people for the size of it" | `orcawninghalf01`, open, pad 1.5 | vibe.mood |
| Guar shelter | c1 pond guar, kept for the warmth of the hatchery | `orcawning01`, open, pad 1.5 | contents c1 |
| Landing | Boats from downriver; LP14 waterline mark | 2 `dockstrent02` at the mined pair pose, dy -0.12 | landingRule; vibe.materials (5b) |
| Door candles x5 | Lit entrances | `argoniancandle01` 1.1 m out of each door | lights.density |
| Yard sets | Household stores x5, cookpots x4, nets x2 | `hist-village-stores`, `-cookpot`, `-nets` (yard-sets/02-hist-village.json) | L33, L75 |
| Cane work in the common | "They fish, cut cane": where the kin cut cane between the elder's, minder's and kin houses; a common used by few | `woodchoppingblock` (pad 0.3), two `twigsbundle`, `basketfull`, `bucket01`, `bucket02a`, `basket03`, on the cane-block and elder pad flats | L75; R6 |
| Ways | The last stretch of the track, north path, door steps, hatchery path | footpaths 2.2 / 1.8 / 1.2 m | pathReachRule |

The bars come from the hamlet column of breadth-bars.json. The column counts the 5 `building` parcels. The two awnings and the landing are structures. Distinct shells number 5, against a bar of >= 4. The top shell share is 2/7 = 0.29, against a bar of <= 0.35. Dressing within 12 m per dwelling follows R6/R33. It counts the 4 `dwelling` parcels. The trade house is a shop and is not counted. Dressing counts are elder 21, minder 20, kin 20 and fishers 17. The p50 is 20, against a bar of 20. Dressing kinds number 28, against a bar of >= 10. Light kinds number 2: candle stand and lantern. Density is 17.8/ha, from 8 counted parcels over 0.45 ha. The hamlet band is 7-16, so density draws a warning. The buildings are not spread out, because the dry ground of the island is already the built hull. The band is filed as a rule gap in requests.jsonl nb-b-1. Greenspring misses the village band in the other direction.

### Interiors (5 load doors; built entranceCount 5)

| Door | Building | Shell | Tier and cell (claimed) | Why |
|---|---|---|---|---|
| .1 | minder's house | thatchhouse06 | A, SeekhatTreeminderHut | the minder's own hut (preferCell) |
| .2 | elder's house | thatchhouse06 | A, SeekhatEldersHut; safe interior D0 | the elder houses strangers |
| .3 | trade house | bamboohut01 | A, CIPHTBMHutInterior05 | Interior04 is held at Gang Ground and Greenspring |
| .4 | kin house | thatchhouse05 | A, SeekhatFishersHut | the sole linked cell of the shell |
| .5 | fishers' house | thatchhouse05 | A, SeekhatFishersHut | the same; linked set exhausted (R4) |

The open structures with no door are the empty frame, the guar shelter, the shrine and the landing. Thatchhouse07 is rejected by lead ruling 1. Thatchhouse08 is rejected because SeekhatCarpenterHut fails on the doll_turtle texture. The KotM roundhuts are rejected because their floors stand 8 m up on stilts with no stair composite. The house platforms are rejected because they have no shell family. The house platforms fail test_shell_breadth.

### Containers and items

Stores baskets, closed baskets and sacks from the yard sets yield their own container sockets. The painted urns at the shrine and the hatchery are containers. The urns hold offerings and clay for the lids.

### Creative register (three calls not in the register's rows)

1. A half-stripped house frame stands at the edge of the village. The family has gone downriver.
2. The clutches lie under a row of fired-clay plates on the mud beside the pool.
3. Chimes hang only on the river side of the tree, so they are heard from the water first.

### Sockets

| Socket | Kind | Host or spot | Data and why |
|---|---|---|---|
| npc-tree-minder | npc | minder's door | slot npc-opening-tree-minder (n1); work: idle-minder-tends at the shrine urn; home: idle-minder-home; fills n1, the notable slot, shrine |
| npc-upriver-elder | npc | elder's door | slot npc-opening-upriver-elder; work idle-elder-hosts (stores); home idle-elder-home; fills lodging |
| npc-trader | npc | trade door | slot n2; work idle-trader-work, idle-family-fish (rack); home idle-family-home (kin door); fills n2, trader |
| marker-elders-door | marker | elder's door | promise.entrance.door; post.rest.nine-bends |
| marker-harvest-cut | marker | trunk above the root | evidence.opening.harvest-cut |
| marker-hatchery-pool | marker | pool rim | mark.opening.hatchery-pool |
| marker-tree-foot | marker | shrine | mark.opening.tree-foot |
| marker-opening-hist-withdrawal | marker, scene | common before the shrine | scene.opening.tree-withdraws; the MQ01 provision |
| marker-waterline-cut | marker | landing | LP14 |
| fauna-pond-guar | fauna D1 | guar shelter | c1 |

The record's local states are speaking and withdrawn. They have no quest `STATE` key yet. No quest declares `STATE` for this place. Layout `stateKey` is refused without a declared `STATE`. This is filed as a request.

### Quests

MQ01 has the tree withdraw over the dead clutch at Gang Ground. The scene socket, the harvest cut and the hatchery marks are its provisions. LP13 uses the fishers' household and its rack. The traps themselves stand at the port and are not here. LP14 uses the waterline mark on the landing. LP19 is a naming under this tree, at the shrine. LP19 needs no new placement.

### Seams

The place is off the road. The village's own track is `track.pirate-freeholds.upriver-hist-village`. The track arrives at the west shore at terminal `terminal.upriver-hist-village.the-track`. The terminal stands at (3407.4, 1456.4), from rederive_terminals. The terminal kind is footpath. It is joined by `route.upriver-hist-village.the-way`. By water, the landing on the bend (body.2442-1212) serves the village. The place has no sign arms, because it has no fork.
