# The North Cut Camp (`place.naga-kur-deeps.naga-highway-camp-active-north`), design

The North Cut Camp is a Type 4 camp of type `naga-highway-camp`. Its family is hostile-camp, with magnitude M1 and danger D4. Its culture is argonian (tribeless Naga). Its region is naga-kur-deeps, region class rootland deep marsh. It is the first naga-kur-deeps place. It is contrast row 4 of `tooling/.reports/16k/walk11/new-places/choice.md`. The contrast is a hostile Naga camp against the Broke Column's Imperial deserters. The agent `np-naga-camp-a` built it in walk 11 part A, steps 0-2. The site is about x 2306, z 4560, at the bone-road track terminal.

## § Site

- Record (`world/sources/catalogue/places-naga-kur-deeps.json`): why = a tribeless Naga camp
  working the northern poling route from a blind bend where craft must slow; they take cargo
  and rarely kill; the settled hold pays the camp to leave its stretch alone (LN07). Vibe: a
  smoke plume above a cut bank with a chain across the channel; hide stretched grey on
  frames; cane, wet hide thongs, smoked hide; grave cairns stepped up the bank, one course a
  death; businesslike banditry; signature: a scratched tally-stick receipt for what they take.
  Occupants: n1 lieutenant (named, writes the receipts), n2 band. Loot l1 hidden cache, tier 2,
  "cargo held against claims, some of them years old". Hostility: hostile, flips to guarded at
  200 gold, neutral at faction rank 1; respawn faction-refills. Interior none; services none;
  lootTable loot-cache and services.
- Promise ledger `world/sources/placement/promises/place.naga-kur-deeps.naga-highway-camp-active-north.json`:
  21 rows (2 occupants, 14 prose, 1 quest, thing-boat, thing-dock, thing-sign).
- Dossier `world/sources/sites/dossiers/naga-highway-camp-active-north.md`: plotted anchor at
  8.1 m on the flat south of a 3 m bank, 0.66 m over the water table; nearest route the
  Gideon-Soulrest road 368 m west; channels 164 m SW (headwater) and 324 m E; canopy 0.62,
  cypress 19 %. Measured here (wb ground, 2.5 m grid): a bench of firm ground at 11-11.6 m
  (x 2280-2330, z 4570-4608) falls 3 m south to the anchor's flat at z 4610-4635; north of
  the bench both arms of `track.road.bone-road-waystation-the-counted-dead` bend round a pond
  (level 10.69 m, at most 0.85 m deep, x 2290-2320, z 4540-4550) and meet at the track's
  terminal (2305.8, 4559.5).
- Seams (step 0.3b): on the road. The bone-road track's terminal is this place's
  `networkTerminals[0]`; the camp path continues the west arm's line east for 14 m (C-stitch
  within 20 deg), then turns up the bench to the fire. No crossings, berths or stations within
  500 m. 12 neighbours within 500 m (none published): The Black Eye 198 m, Deepmire 226 m,
  The Egg Camp (poacher camp) 285 m, The Reed Gate Camp (the rival Naga camp) 464 m.
- Lore: `world/sources/lore/tribes.md` § Naga (Lore:Naga: Naga acted as highway robbers in
  the plantation years and went back into the inner swamps; Naga-Kur, the Dead-Water tribe,
  hold the inner swamps); `world/sources/lore/regions/murkmire.md`.
- Built nearby: nothing published within 2 km. Must not repeat: Gang Ground's two
  `argoniantent02` family tents plus totem plus campfire as its whole camp grammar; the
  Broke Column's tent line, banners and levy barricade.

### Record defects (step 0 item 5), filed in the report

1. **The site breaks two of the record's hard constraints.** `sitingPrefs.hardConstraints`
   asks for "on a blind bend of a poling route" and "on the bank of the northern poling
   channel, water within 15 m"; the plot (`whySiteWon`: "no free 'any-channel-bank' site was
   left in the zone, so plain ground") is 164 m from the nearest channel. The poling line
   `route.boat.deeps-inner-poling-line` is unsolved (no geometry). The plotter placed a homeless
   record on a site that fails its own hard constraints without flagging it (rule gap for the
   tooling sub-lane: the plot stage must refuse, or mark `siteBreaksHardConstraints`).
   Owner call in the packet: move the camp to a channel bank once the poling line is compiled,
   or keep this site and rewrite the record as a track camp (builder's recommendation: keep;
   the type is a highway camp with variant `road-active` and discovery `road`; the track it
   sits on carries walkers every day).
2. Eight prose rows name the channel, boats or polers (listed in § Record change set); they
   stay unconfirmed until the change set lands at step 5b (part C) or the owner moves the place.
3. `thing-boat`, `thing-dock` (from the channel premise and `assetPlan` docks-piers): unfilled,
   reason `owner-world-call`; the pond is under 1 m deep, so no hull passes `hullWater`.
4. Packet gap: `site_packet` finds no type sheet for `naga-highway-camp` (sheet 04-camp names
   no Naga type), so the type-4 lessons rows were not in the packet.

## § Intent

1. **Purpose.** A toll stop run like a business by Naga who belong to no tribe. A lieutenant
   and four to seven of his band watch the one bend where both arms of the bone-road track
   meet, stop walkers at a cane gate, take part of what they carry and cut them a tally stick
   for it. The held cargo waits behind the lieutenant's tent until its owner comes back with
   the matching tally and pays (the `trader` service: buying back held cargo, open when the
   camp is guarded). Food is pond fish and roots; water is carried up from the pond; hides
   come off the walkers' loads and are smoked over the fire.
2. **Mood: wary, businesslike, a little grim.** Wary: the watch scaffold on the bench corner
   sees both arms of the track before a walker sees the camp; the way in is one narrow path
   through the gate. Businesslike: the tally board, the cargo stacked and sorted, the hide racks
   in use. Grim: four grave cairns stepped down the bank behind the camp, two Argonian candles
   burning at them at night.
3. **Three images.** Far: the smoke column over the bench and the scaffold's platform against
   the cypress (fire smoke `fx:smoke-column`, `stockade-scaffold-2stage`). Threshold: the
   totem and the two cane fences narrowing the path where it leaves the track, the band
   member standing by the totem. Heart and reward: the fire between two brown hide tents with a
   hide rack either side. Behind the lieutenant's tent stand the stacked crates, sacks, barrel
   and handcart of held cargo.
4. **Region, palette, climate.** Rootland deep marsh in the deep interior: firm low rises in
   cypress swamp, ground mist most mornings, humid clear spells, monsoon downpours (weather
   mix `marsh (fringe/interior/rootland/lakes)`: ground-mist 3, clear-humid 2,
   monsoon-downpour 2, storm 1). Ground: dark peat and fern under cypress (dossier: cypress
   19 %, bracken 14 %, manfern 8 %); water: one still pond in view at the bend, no moving
   water; building material: cane and hide (Mud Mother tents), cut timber only in the stolen
   scaffold; light: one fire and two candles; air: smoke over mist.
5. **The ground.** The bench is the region's read already (firm rise in deep marsh); placed
   assets add the hide, cane and smoke. The record's "no green anywhere" palette cannot hold in
   a cypress swamp whose ground cover survives (R73); it is in the change set.
6. **Day, night, rain.** At night the fire and the two cairn candles are the only lights; the
   fire is seen from the bend, the candles from the flat south of the bank. Rain beats on the
   hide; the band sits under the tents' open fronts. Sound: the pond, insects, the drum at the
   watch when a walker is sighted (an audio cue for later; no drum mesh is kitted).
7. **Age and wear.** Tents are mended hide, pitched for one or two seasons; the scaffold is
   older timber taken from somewhere else; the cache holds cargo years old under fresh loads;
   the cairns are oldest at the bottom of the bank.
8. **Promises as beats.** Walker sees smoke and the watch (vibe silhouette, condition);
   stopped at the gate by the band (n2, encounter-the-bend, D4); the lieutenant at the tally
   board under the watch (n1, thing-sign, signature); the fire, racks and tents (materials,
   mood); the cache behind the lieutenant's tent (l1, lootTable loot-cache, trader); the
   cairns down the bank (materials: one course a death).
9. **Not repeated.** No banner, no barricade across the track, no tent line (Broke Column);
   not the Gang Ground set of two family tents beside a totem. Here the tents face each other
   over the fire with the totem at the gate; the landmark is the watch and tally board.

### § Palette

1. Shared grammar with the region (home family `mudmother-grove` in `culture-kits.json`
   `regionalStyles.naga-kur-deeps`): Mud Mother hide tent `argoniantent02` x2 (top family
   mudmother-grove, top in no other place yet: `worldgen.shell_breadth`), Mud Mother totem and
   cane fences, Argonian candles.
2. Distinct: the stolen watch scaffold (`composite:works/stockade-scaffold-2stage`, first use
   in a place), the hanging tally board (`kotm:argonia/blackwood/sign`, first use), tanning
   racks with hides (`vanilla:furniture/tanningrackmarker`, first use), the Sleeping Tree
   grave cairns (`histtree:.../rockcairn01-04`, first use in a place).
3. Further from the same type elsewhere: the Broke Column is canvas Legion tents in a line,
   banners and stakes; this is hide and cane round a fire with a timber watch; Gang Ground is
   bamboo huts on terraces with a barge.
4. First in the game here: the scaffold, the tally board, the tanning racks, the
   rockcairn01-04 set, the woven chairs outdoors.
5. Not a subset of any sibling's palette (no published sibling of `naga-highway-camp`;
   sibling_palette prints none).
6. Not used and why: `argoniantent01` (the big Mud Mother tent, the first choice for the
   lieutenant): its interiors sidecar promotes its 3.1 m open front to a closed shell with a
   tileset interior (`closedShellPromotedBy: own-geometry-door`), so `archwayRule` asks for a
   Telvanni door in it; filed as a tooling task (report). `archwaysticks` (a gate of sticks
   over the path): its mesh starts 4 m above its pivot, so `hangingRule` reads it as a hanging
   part; filed. `canoe1` as a taken boat: a water-class hull cannot stand on land or in the
   0.85 m pond.

### Internal variety

The landmark is the watch scaffold with the tally board under it. The fabric is two Mud Mother tents at different yaws, which face each other over the fire. The north corner holds the gate, with the totem and fences. The middle holds the fire set: fire, wood, chopping block, chairs and racks. The south-west holds the cache. The east holds the band's water and food. The bank holds the cairns. The tents are new and the scaffold is old. The oldest cairns lie low on the bank.

## § Walk-through

The main approach runs from the west arm of the track, the Gideon side. The Gideon-Soulrest road lies 368 m west of the camp.

| Stage | What is seen | Mood | Pieces | Feel-check camera (eye X,Z -> look X,Z) |
|---|---|---|---|---|
| 1 Far | smoke column over the bench, the watch platform against cypress | wary | y-fire smoke, w-watch | 2262,4518 -> 2300,4575 |
| 2 Approach | the track bends round the pond; the gate's totem and fences show at the bend | wary | g-totem, g-fence1-4 | 2293,4559 -> 2312,4565 |
| 3 Threshold | the path leaves the track east along its line, then turns up through a cane funnel that closes on the two totems | wary, grim | camp-path, g-totem, g-totem2, g-fence1-4, idle-n2-gate | 2310,4559 -> 2315,4572 |
| 4 Heart | the fire between two hide tents, hide racks either side | businesslike | y-fire, b-lieut, b-band, h-rack1/2 | 2313,4576 -> 2303,4588 |
| 5 Reward | the cache behind the lieutenant's tent; the tally board under the watch | businesslike | c-crate1-4, c-sack1-3, c-barrel, c-barrel2, c-cart, c-cart2, g-tally | 2302,4597 -> 2295.5,4589.5 (from the cairn way, at the cache centroid) |
| 6 Exit | south over the bank past the cairns and candles to the flat (the fallback way out) | grim | k-cairn1-4, k-candle1/2 | 2300,4606 -> 2306,4626 |

The Approach section follows 97 §5. The first object that a walker sees is the smoke, then the scaffold. The way in is the only path. The gate faces the walker on the track. Nothing dead-ends. The bank is the camp's retreat and is walkable at 8-10 deg.

## § Brief

| Thing | Purpose | Kit piece (measured) | Rule or lore pointer |
|---|---|---|---|
| b-lieut, lieutenant's tent | n1 home; faces the fire and the gate (stage 4) | `mudmother:.../argoniantent02` 6.14 x 5.31 x 4.26 m, pad apron 1.0 (s 3.0, w 2.5 for the cache), yaw 60 at 2298.5,4587.5; its open side is local north (ring rays, `round-1/lieut-ring.json`: open from 85 to 185 deg at yaw 135), so yaw = the bearing to the fire | home family R101; camp sheet tents |
| b-band, band tent | n2 home (stage 4) | `argoniantent02`, pad apron 1.0, yaw 300 at 2312.5,4588 | as above |
| w-watch, watch tower | sees both arms of the track (stages 1-2); the top deck is the lookout, reached from stage 1 inside the frame | `composite:works/stockade-watch-2stage` 3.70 x 3.88 x 6.20 m, pad 0.5, yaw 225 | assetPlan stockade-scaffold; setting camp |
| w-stair, tower stair | the way up from the yard to stage 1 | `vanilla:clutter/stockade/stockadescaffoldstairs01`, pad 0.5, yaw 225, posed by plugin pairing t1654 (no template pairs a stair from stage 1 to the deck) | setting camp |
| y-fire + y-wood, y-chop, y-chair1/2 | heart, smoke plume, cook socket (stage 4) | `campfire01burning` pad 1.0; firewoodpilesmall01; choppingblock01; `wovenchair01` x2 (small dressing) | camp sheet fire set; R94 seats |
| h-rack1/2, hide racks | smoked hide black and stiff (materials) | `vanilla:furniture/tanningrackmarker` 1.61 x 0.90 x 1.72 m | vibe materials, palette |
| g-totem, g-totem2, g-fence1-4, the gate | the threshold where walkers stop (stage 3): two totems as gate posts where the path turns off the track, a cane funnel closing on them | `argoniantotem01` x2; `argonianfence01` (1.58 m) flaring 20 deg outward from each totem toward the walker (g-fence1 yaw 107.8, g-fence3 yaw 147.8), `argonianfence02` (0.89 m) lining the climb inward from each totem (g-fence2, g-fence4, yaw 307.8); each piece's pivot end 0.5 m off its totem's centre (round 4) | assetPlan totems-ritual, fences-wattle |
| g-tally, tally board | thing-sign; signature (stage 5) | `kotm:argonia/blackwood/sign` 0.25 x 1.40 x 1.39 m: a round blackwood sign-shield hung by two straps from a log (six-view look, `round-2/look-sign/`); its face looks along local X, so yaw 0 turns it east to the gate and the path (yaw 90 showed its edge, round 2); hung under the watch platform (`mount --hang`, `reader-approved r3`: attached at its top, no gap; `measure` shows only its top patch touching the beam, 0.021 m; its bottom hangs 1.15 m over the ground) | assetPlan signage-blank; signature |
| cache: c-crate1-4, c-sack1-3, c-barrel, c-barrel2, c-cart, c-cart2 | l1 hidden cache, trader stock (stage 5) | cratesmall01 x2, cratesmalllong01 x2, miscsacklarge x2, miscsacklargeflat01, barrel01 x2, handcart02, handcartcrate (a cart loaded with crates: crate-on-crate stacking has no mined pair and the crates are over the 0.6 m unmined cap), on the tent's south and west pad aprons (round 4) | contents.loot l1 |
| s-basket, s-barrel | band's food and water | basketfull, barrel01 | camp sheet: one store per tent |
| k-cairn1-4, k-candle1/2 | grave cairns, one course a death; night lights (stage 6) | `histtree:.../rockcairn01-04` with 0.3 m pads stepped down the bank; `argoniancandle01` x2 | vibe materials |
| b-lieut-candle, b-band-candle | a lit flame at each lived-in tent's mouth at night (reader row 24b, round 2) | `argoniancandle01` on a 0.3 m pad beside each mouth, on the fire side | camp sheet lights; R94 |
| camp-path (track, 2.5 m) + 4 footpaths | terminal to fire; the watch step; the camp yard (4.0 m, band tent mouth past the fire's south side to the lieutenant's mouth: the worn mud under the camp, round 4); the cache floor (3.0 m, worn mud under the held cargo, both ends on the lieutenant's pad); the cairn way from the yard between the tents, down the bank past the cairns to the flat (stage 6, reader row 4, round 2) | `path` ops | R84; C-stitch |

The planned bars are 3 counted buildings. The 3 buildings sit below every breadth-bars column, so tier bars are not judged. The plan has 38 placements. The plan has 2 light kinds: campfire and candle. The plan has 18 dressing asset kinds.

### § Interiors

The camp has no interiors. Both tents are open hide shelters that visitors enter (R18). The scaffold is open. The camp has no doors.

### § Containers and items

The cache crates are authored containers of moderate value. The crates hold cargo with split tallies. The sacks are authored containers. The tar barrel is an authored container. The band water barrel is a blanket household container. The band food basket is an authored container. The tally sticks themselves are Phase 13 inventory items. No `item` class names a stick. The tally board shows the stick signature now.

### § Creative register

The camp makes three calls that differ from the register's camp row. The Broke Column's camp row has a tent line, colours, a levy barricade and a brazier. Call (1): a tally board hangs under a stolen watch scaffold, where the camp issues its receipts. Call (2): the camp keeps the held cargo as a sorted cache and sells it back to its owners, as a trader service. Call (3): grave cairns step down the bank with Argonian candles, one course a death.

### § Sockets

| Socket | Kind | Host / at | Data | Why |
|---|---|---|---|---|
| npc-n1 | npc | 2301.0,4586.1 | n1 lieutenant; morning idle-n1-tally, night idle-n1-home | runs the camp |
| idle-n1-tally | idle stand | 2292.2,4571.4 | at the tally board | issues the tallies |
| idle-n1-home | idle sleep | 2300.4,4586.4 | tent mouth | sleeps facing the gate |
| npc-n2 | npc | 2310.0,4586.6 | n2 band; morning gate, sunset cook, dusk sit, night home | the band |
| idle-n2-gate | idle stand | 2319.6,4562.4 | between the totems | stops walkers |
| idle-n2-cook | idle cook | y-fire | | smokes hides, cooks |
| idle-n2-sit | idle sit | y-chair1 | | evenings |
| idle-n2-home | idle sleep | 2310.6,4586.9 | tent mouth | sleeps in turns |
| encounter-the-bend | encounter | 2305.8,4561.0 | D4, approach | the band holds the bend |
| encounter-the-fire | encounter | 2305.5,4578.5 | D4, camp | the camp fights at its fire |
| container-cache-crate, -small, -sack, -sack-flat, -tar, -water, -basket | container | c-crate2, c-crate1, c-sack1, c-sack2, c-barrel, s-barrel, s-basket | fill rules above | held cargo, stores |

### § Quests

The skeleton quest is LN07 "Ledgered as Hire". The hold's accounts show a boat hire every season for craft that it does not own. The money is paid for quiet from this camp. The quest needs nothing here beyond the camp, the lieutenant and the cache. The lieutenant can be asked. The ledger confirms the provision.

### § Seams

The camp has the terminal `terminal.naga-highway-camp-active-north.bone-road-track`. It is a footpath-kind terminal on the bone-road track. The camp path kind is track, 2.5 m wide. The camp has no signpost. A camp never carries a signpost, per the camp sheet.

### § Record change set (applied in part B)

The lead ruled in the part B brief to keep the site and rewrite the record as a track camp. Part B added `traversalModes` and dropped boat. Part B added `traversalFallback` walk. Part B added `landformClasses` any-firm-ground. `vibe.palette` names the hides on the racks, not grey tents. The Mud Mother tents render brown in round 2. One text-reader pass is at `tooling/.reports/16k/<place>/text-reader-b.md`. `thing-boat` and `thing-dock` are gone. `thing-fire` is filled by y-fire. Part C's step 5b runs the full record-coherence protocol over the result. § Site above quotes the record as plotted. Eight rows are confirmed as rewritten fields. `why.founding` now says the camp works the bone-road track's bend, not the poling route. `why.siteAdvantages` now names a blind bend where walkers meet below the bench. `why.occupantsMotive` changes "poler" to "walker". `vibe.silhouette` now has smoke above the bank and no chain across a channel. `vibe.approach` and `playerPurpose.hook` now say a walker stops at a cane gate under a watch, not at a rope across a channel. `vibe.senses` now has no gunwale chain and a drum that carries over the pond. `vibe.palette` drops "no green anywhere". `assetPlan` drops docks-piers. `sitingPrefs.hardConstraints` now makes the track bend replace the channel lines. `relations.patrols` now names the bone-road track, not the poling line. Rerunning `blueprint_promises --write` drops `thing-boat` and `thing-dock`. The pond lies at 10.69 m and is under 0.85 m deep. The firm bench lies at 11-11.6 m and falls 3 m to a flat to the south, where the cairns go. The nearest channel lies 164 m south-west of the camp. A second channel lies 324 m east.

## § Feel check

Round 3 was part B, under the lead's two-round cap. The shots are six eye-height `paint-look` stages over a scratch bundle. They are saved in `tooling/.reports/16k/<place>/round-3/feel/`. Cameras 1 and 2 moved in to 35 m so that they stand on the render's ground patch. The check is recorded in `camera-check.json`. The night workbench shots are `round-5/04`, `05` and `08`. Two readers wrote `feel-reader-a.md` and `feel-reader-b.md`.

| Item | Reader A | Reader B | Verdict and lever |
|---|---|---|---|
| Blind read names a camp | yes (lean-tents, scaffold, totems, cairns) | yes | pass |
| wary | partly (scaffold, spiked totems) | partly | open: no smoke in the render; lever: the watch's sightline is real, so recheck it on the published place with fx |
| businesslike | partly (fire set; cargo too small to read) | partly | MISS: the held cargo does not read. Lever: cache density (more stacked crates and sacks on the lieutenant's apron) and the stage 5 camera aimed at the cache centroid |
| grim | absent (bright day, flowered ground) | partly (racks, totems) | MISS: the ground under the camp renders as flowered grass, not peat; lever: the place's own ground paint (a worn mud patch under the fire, tents and cache) |
| far image (smoke + scaffold) | scaffold yes, smoke no | same | open: the smoke column is a runtime fx the eye render does not draw |
| threshold image (totems + cane fences) | partly: no fences read | partly | MISS: the fences do not narrow the path in the stage 3 view. Lever: fence poses closing on the totems, or the camera turned up the climb |
| heart image | partly (fire unlit by day) | yes | pass for layout; the flame is runtime fx |
| reward image | not found | not found | MISS, as businesslike above |
| stand-ins | water as flat slabs (render), repeated tents, racks and cairns | same | tents: the region's one hide tent, turned and dressed apart (R101); racks: one asset, a lever for part C (a second hide-rack asset if the pool has one) |

The exit rule was not met. The lead capped part B at two render rounds. The misses go to part C as its first fix rows. Part C works the misses in the layout before step 5. Part C then reruns the feel check on the published place.

Round 4 was part C1 and made one layout change. The cache grew to 12 pieces with a loaded cart. The stage 5 camera moved out onto the cairn way and aims at the cache. Four cane fences funnel onto the two totems. The camp yard and cache floor are painted as worn mud. The shots are the six eye-height stages over the publish bundle, in `round-4/feel/`. The workbench night iso and gate and cache joints are in `output/renders/naga-camp/round-7/`. Two readers wrote `round-4/feel-reader-a.md` and `-b.md`.

| Item | Reader A | Reader B | Verdict |
|---|---|---|---|
| businesslike | EVIDENCED (crates, barrels, cart in rows, stage 5) | EVIDENCED | pass |
| reward image | found (stage 5) | found | pass |
| threshold image | found, but reads as a spiked-stake jumble, not a funnel | partly: no narrowing read | open after rounds 2-4: owner look check (the gate at 2313,4570). Measured: no fence touches a totem (gaps 0.11 to 0.22 m) |
| grim, ground | ABSENT: meadow speckle under the camp, bright sky | weak, same | open after rounds 2-4: owner look check. The worn-mud yard and cache floor are painted (paint-check 0 failures); the eye renders draw no mist or smoke |
| stand-ins | slab water, unlit fire, repeated cairns | same | renderer limits (no water shader, no fx in `paint-look`): judged in the studio walk |

## § Lessons this slice

Part C3 wrote the lessons at slice close. `lessons/record-and-grounding.md` records that hard constraints are read for every plotted place. It also records that rivals are named back and that unplaceable words are checked at step 5b. `lessons/tooling-gaps-still-open.md` records that way paint is cut under an assembly pad. It also records that `argoniantent01` and `archwaysticks` were refused. `types/04-camp.md` holds the Argonian camp pieces. `types/04-camp.md` also holds the 3 m gate funnel and the canoe as cargo. Part C3's record change set makes the record's rivals name Cut-Rope and Long-Water Hold back. `why.pressures` names both rivals. `why.wouldChangeIf` drops "toll rates". No placed piece can carry a toll. The camp robs and levies no toll.
