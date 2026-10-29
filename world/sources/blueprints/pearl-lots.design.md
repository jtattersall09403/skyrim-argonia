# The Counted Lots (pearl-lots) — design (16k walk 11 new places, type 7 works, aquaculture; part A of three)

The record is `place.saxhleel-coast.pearl-lots` in `world/sources/catalogue/places-saxhleel-coast.json`. The place is works, aquaculture, pearl-and-shell-bed, M1, argonian, D1. The promise ledger is `world/sources/placement/promises/place.saxhleel-coast.pearl-lots.json`. The ledger holds 25 rows. The site packet is `tooling/.reports/16k/place.saxhleel-coast.pearl-lots/site-packet.json`. The dossier is `world/sources/sites/dossiers/pearl-lots.{json,md}`.

## Site

### The choice
Choice row 7 (`tooling/.reports/16k/walk11/new-places/choice.md`): an underwater harvest on the
Saxhleel coast against Bog Iron's land extraction. The works lives in the water: the beds, the
tenders over them, the sorting on shore.

### The record, read
- `why`: an amphibious people with a port to sell into works a pearl bed, divided into numbered
  lots held by inheritance by diver families, each with a surface tender. The deep lots pay best
  and kill divers; both are entered in the tally book. Foreigners must never learn to dive here.
- `sitingPrefs.hardConstraints`: "clear water over a worked bed", "6-12 m depth"; preferences
  "worked from a shore settlement", "buoyed lot markers"; landform cove, islet, natural harbour.
- `vibe`: silhouette "marker buoys and a tender boat over water with no bed in sight"; palette
  "buoy ochre, green water, silver shell"; materials "buoys, grading baskets, weighted belts";
  signature "a diver's tally of lots worked, the deep lots entered in a second hand"; mood
  "businesslike about a dangerous trade"; approach "found by spotting the tender boat"; senses
  "rope creak above; the click of shell into a basket below".
- No services, no interior (`interior.kind none`, `entrance none`), `underwaterAccess deep-dive`,
  traversal dive / swim / boat. Occupants n1 crew "2-6 D1 divers", n2 "one surface tender".
  Sockets: `scene.pearl.deep-lot-dive`, `evidence.pearl.lot-tally`. Loot l1 unique-item, l2
  workshop-stock (materials). `relations.dependsOn` Archon, `reachedVia` Portdun-Mont.

### Record defect 1 (step 0 item 5): the site could not carry the record — RESEATED
The plot seated the dot at 5376.6, 3419.0 beside `body.2966-1867`, an inland swamp pool on the
hist-heartland border: 1.2 m deep over a flat silt bed (8 x 6 m depth grid on the workbench
window, max 1.55 m), 120-137 m from three hist-heartland places, 1.3 km from Portdun-Mont. The
16g remedy that pinned it asked only `minDepthM 1.0` (`plot-remedies.json` row, "a reef or bank
needs 1.0 m of dive water"), so the plot took a pond for a 6-12 m pearl bed.
Fix (builder's recommendation; owner call batched in the walk-12 packet § Owner calls): a
`reseat` row (`world/sources/sites/plot-remedies.json`, realised by `apply_sitings` for this
record alone; receipt in `reseat-receipts.json`; commit d2d7e4ee) moved the dot 923 m to
5440, 4340 over the ocean shelf east of Archon (`body.ocean`, level 0.0, 5.88 m at the dot).
Rule gap filed (Recommendations): the 16g pin translated the record's "6-12 m depth" hard
constraint into 1.0 m; a validator should read a depth in `hardConstraints` into `minDepthM`.

### The ground (`world/sources/sites/dossiers/pearl-lots.md`; workbench window pearl-lots-5410-4360-150)
- A low sand spit runs east from a headland: dry 5326-5404 x, 4286-4304 z, 0.2-0.5 m over the
  sea; the headland west of it rises to 1-2 m (5290-5340 x, 4300-4330 z).
- East of the spit tip the water deepens 0.3 m (5410) -> 1.0 m (5420) -> 1.5 m (5440); a
  drop-off on the line 5446,4296 - 5430,4318 falls to 3.5 m, then the bed lies at 6-7 m from
  x 5460 to 5560 (z 4320-4420) and 7-8 m at 5450-5500, 4400-4420 (the deep lots). A 3-6 m bar
  stands 100-150 m east (5540-5600, 4330-4400): the reef that shelters the bed. Bed slope under
  0.5 deg across the lots.
- Region class ocean; salinity p50 0.78; open sea 1.26 km; nearest route the boat route
  Archon -> Thorn, 21 m SE of the dot; the Long road (`route.road.archon-gideon`) 345 m SW.
  The province scatter already lays sponge, spiky coral, algae and pebbles on the bed
  (470 plants/ha).

### Quest provisions
`quest.provision.underwater-livelihood`; SX05 "Lot Four" (a diver dead on a lot she had no
right to work) and SX06 "The Unwritten Lot" (four families dive an heirless lot to claim it),
both settled in Archon (`world/sources/quests/local-saxhleel-coast.json`). Both need lots that
read as numbered and bounded on the bed, a deep lot and the tally.

### Lore read
- `world/sources/lore/archon.md:69-71`: Archon is where being amphibious is unremarkable, the
  harbour works in three dimensions; the place for underwater play in a safe, civic setting.
- `world/sources/lore/topics/material-culture.md:61`: mother-of-pearl is an attested working
  material.
- `world/sources/lore/regions/waters.md:26`: Archon's coast is the Padomaic Ocean.

### Nearby places (site packet, within 500 m)
contested-bank (fishing bank, 246 m NW), gap-reef (reef, 306 m NW), archon-lighthouse (372 m),
east-estuary-rootworm-station (380 m), archon-sacked-quarter, archon-harbour-hist,
coast-hist-less-refuge (477-495 m). None is built. Must not repeat: Gang Ground's barge and
pier, Claywater's dock-and-raft landing (both `dockstrent02` piers; this one is a short jetty
whose boats work away from it), Bog Iron's land machine.

## Intent

1. **Purpose.** The diver families' working ground, a short swim or paddle from Archon's
   harbour. In the morning the tenders row out over their lots; divers go down with weighted
   belts and baskets, fill them on the bed and are hauled up; the tender tips the shell into the
   grading baskets. In the afternoon the catch comes ashore to the spit, is opened, graded and
   entered lot by lot in the tally, then goes to Archon to sell.
2. **Mood: businesslike, about a dangerous trade.** Businesslike: everything is counted and
   placed: lot markers in a regular spacing, baskets in rows on the spit, the tally on its
   table. Dangerous: the deep lot is darker and further out with a skull among its clams;
   the tender over it rides alone.
3. **Three images.** Afar: two tender boats riding on green water with nothing under them but
   the buoys (rowboat and raft, marker buoys). Threshold: the spit's grading ground (baskets of
   shell by size, the drying rack, the fire, the tally on its table at the jetty foot). Heart and
   reward (under water): the lot bed: clam clusters in bounded lots, each corner a stone cairn
   under its buoy, a diver's basket and weight set down on the bed, kelp at the lot edges.
4. **Region, palette, climate.** Ocean and coastal class (`weather-states.json` coastal: clear
   humid 3, sea squall 2, monsoon downpour 2, ground mist 1, storm 1). Ground: pale sand spit,
   low dune grass on the headland. Water: open, green, always in view, the place is mostly
   water. Vegetation: none on the spit beyond grass; kelp and seaweed below. Material: wicker,
   plank, rope; the boats are swamp-built plank craft. Light: open sea glare by day, one fire
   at night. Air: salt haze, squalls.
5. **The ground you inherit.** Sand spit and shelf agree with the record; nothing to carry.
6. **Day, night, rain.** Night: the fire on the spit and a lantern on the drying rack at the
   jetty foot for the last tender home; the bed is dark. Rain: squalls drive the crew to the fire; no roof (the
   divers live in Archon). Sound: rope creak, water on hulls, shell into baskets.
7. **Age and wear.** Worked daily for generations: the cairns are old, the baskets new, the
   boats patched. Nothing failing; the deep lot is the cost.
8. **The promises as beats.** Approach: the tender boats (thing-boat), the buoys (vibe
   materials). Threshold: the jetty (thing-dock) and the grading baskets. Heart: the tally
   (evidence socket) and the crew (n1, n2 sockets). Reward: the dive (underwater access), the
   lots and the deep lot (scene socket), the diver's basket and anchor weight on the bed.
9. **Must not repeat.** No barge, no long pier, no building: the works is the water.

## Walk-through

| Stage | Seen | Mood | Pieces | Camera (eye X,Z -> look X,Z) |
|---|---|---|---|---|
| 1 Far (300-150 m) | from the headland path or a passing boat: two small boats on open water, buoys around them | businesslike | t-row, t-raft, buoys | 5300,4380 -> 5480,4370 |
| 2 Approach | along the headland onto the spit: the fire's smoke and the drying rack, baskets beyond | busy | s-fire, s-rack, s-baskets | 5320,4300 -> 5380,4295 |
| 3 Threshold | the grading ground at the jetty foot: graded shell in baskets, the tally table | businesslike | s-table, grading baskets and heaps, dk-1 | 5372,4298 -> 5400,4293 |
| 4 Heart | the jetty end: the canoe moored off the jetty end, the lots' buoys ahead, the drop-off | dangerous | dk-3, h-canoe, buoys | 5426,4293 -> 5480,4340 |
| 5 Reward (dive) | under the tender: the lot bed, cairns, clams, a diver's basket and weight; the deep lot further out with a skull | dangerous | lot clusters, cairns, skull | under water 5470,4330 (-3 m) -> 5470,4345 (-6 m) |
| 6 Exit | back to the spit and the headland path toward Archon; or swim out past the bar | — | path the-way | 5360,4296 -> 5300,4330 |

The approach follows openworld-approach §5, because the place is off the network. No way ends within 300 m. The Long road is 345 m SW. The nearest minor footpath is 378 m away. The place declares no network terminal. The walk starts at the headland edge, the first point of `route.pearl-lots.the-street`. Approaches run across country from the south-west and by water from the east.

## Brief

| Thing | Purpose | Kit piece | Rule / lore |
|---|---|---|---|
| jetty dk-1..4 | thing-dock (parcel `jetty` fills it); the way out to the lots; stage 3-4 | `vanilla:architecture/docks/dockstrsol01` x4 at the mined run pose (7.28 m), deck 0.30 m over the sea | landingRule: the land end 0.19 m over the spit (dockstrent02's 0.35 m deck stood 0.21-0.32 m over every reachable land end) |
| canoe h-canoe | a diver's own canoe at the jetty end; stage 4 | `canoe:actors/sfss/canoe/canoe1` from watercraft-v1 (water anchor, afloat: keel at the 0.15 m draught, upright), 1.3-1.5 m of water | an assembly member of the grading ground, not a berth parcel: it is not boarded from the deck |
| tender raft t-raft | the surface tender over lot one with a basket and net aboard; stage 1; thing-boat (marker socket `tender-boat`) | `ferries:yamadori/ferries/plank_ferry_swamp_01` | hull afloat; deck children `mount --inside` |
| tender rowboat t-row | the tender over the deep lot; stage 1 | `ferries:yamadori/ferries/rowboat_ferry_swamp_01` | hull afloat; moored offshore, reached by swimming, so no berth way (assembly member) |
| buoys b-a..b-d (4) | buoyed lot markers, one over each lot's first cairn, 1.6 m off it; silhouette | `vanilla:clutter/barrel01-keg-buoy` (watercraft-v1, kit lane `np-pearl-lots-kit`: the vanilla keg at its 0.68 m waterline; no buoy or float exists in the pool) | record vibe; sourcing log row |
| lot cairns c-a..c-d, c-a2..c-d2 | two opposite corners of each lot on the bed, so a diver reads the lot as bounded (round 10 reader: one cairn per lot read as a loose scatter); signature (the lots) | `vanilla:landscape/rocks/cairns/rockcairn01..04` (dug-in); the deep lot's second is the small rockcairn04 (rockcairn01 sank 1.47 m in the pit's slope) | R86 wet; rockSeatRule |
| clam beds (4 lots, 26 clams and 3 scallops) | the harvest; reward | `vanilla:plants/clam01`, `clamlarge01`, `clamthin01` (ground anchor after the kit lane's fix), `jokerine:_seaside/clam_large`, scallops | must seat on the bed, measured |
| diver's basket + weight on the bed | a diver's gear left on the lot, grading baskets below; stage 5 | `vanilla:clutter/basket01`, `canoe:weapons/sfss/anchor` | R86 wet |
| deep-lot skull | the deep lots kill divers; stage 5 | `vanilla:clutter/bones/humanskull` | record pressures |
| kelp / rocks | lot edges, the bar: two more plants at the edge of each lot (round 10: kelp nearly absent from the diver's view) | bed-rooted pieces only: `depths:landscape/grass/waterkelptall02/03`, `tbprockgrasswater03`, `tbpalgae01`, `shores:shoresofskyrim/shorerock0N` (part C: the BM&V and vanilla water-anchor kelps floated at the surface over the 6 m bed) | dressing.md § 5 |
| drying rack s-rack | shell meat and lines drying; the lantern's host at the jetty foot (round 10: at 5382 it stood 18 m from the jetty and read as the fire's); stage 2-3 | `vanilla:clutter/deadanimals/fishrack01` at 5395, 4297.2, turned 90 deg along the street (0.72 deg footprint; the cells at the jetty's land end run 2.6-3.3 deg) | `fishracksmall` is licensed indoors only (setting class: one interior reference) |
| fire s-fire | the crew's fire, the night light; stage 2 | `vanilla:clutter/woodfires/campfire01burning` | lights.density |
| grading baskets + heaps | grading by size; a row of four full baskets behind the table for the graded catch (§ Intent 2, "baskets in rows"; round 10: three baskets read as sparse); stage 3 | `htbm:…/argonian/wickerbasket01` x2, `kotm:argonia/clutter/basket01`, `mudmother:gv_meshes/argoniannest/basketfull` x4, `vanilla:clutter/bucket01`, `vanilla:clutter/barrel01`, six scallops/clams on the sand | vibe materials |
| tally table + book | the signature: the tally; evidence socket | `htbm:…/argonian/wickertable01` + `vanilla:clutter/books/book01/character assets/journalbasic` (works-v1) on its top, the socket on the book | evidence.pearl.lot-tally |
| rack lantern j-lamp | the light the last tender steers for at dusk | `mudmother:gv_meshes/argoniannest/argonianlanterns04` (the 1.0 m chain; the 2.7 m chain of `argonianlanterns02` put the cage 0.77 m into the sand) hung from the rack (`mount --hang`) | hanging-only row; a lantern cannot hang from a run member (the export binds a hung child to its host's parcel) |
| the street and the rack spur | spit path from the headland edge to the jetty foot; a 1.9 m spur to the rack's side | footpath 2.0 m, spur 1.2 m | R84; pathReachRule (the rack is a doorless parcel) |

The place has no interiors, no building and no door. Containers are the barrel and baskets on the spit, as container sockets with blanket fill. The diver's basket lies on the bed. The creative register has three points. First, the works has no building at all and the crew's ground is a bare spit. Second, the harvest lies under 6-8 m of water and the place is read from boats. Third, the lots are a grid of cairns, one a deep lot with a skull. Parcel `grading-ground` holds the shell s-rack. Every other piece, afloat or on the bed, is a member of that assembly. A doorless parcel under 6 m of water fails walkRule. A hull bound as a parcel is a berth. Parcel `jetty` holds the run. Socket npc n1 is the divers. The divers work at the grading baskets and cook at the fire at dusk. They go home at the jetty foot, where they leave for Archon. Socket npc n2 is the tender. The tender works fishing the lines at the jetty end and goes home at the jetty foot. The walk home to Archon belongs to the later schedule system, under the 0102 reason of a later-phase system. Marker `underwater-livelihood` sits over lot one and fills the quest provision and the deep-dive access. Marker `tender-boat` sits on the raft as thing-boat. Marker `scene-deep-lot-dive` sits over the deep lot. Marker `evidence-lot-tally` sits on the table. The place has no fauna, at D1. The seams are as follows. The place is off the network, with no way within 300 m. The street starts at the headland edge.

### Record defect 2 (step 0 item 5): trade-access with no trader
`lootTable.kinds` named `trade-access`, which only a trader or market parcel carries (type
sheet 07, Recipe); the catch is sold in Archon. Removed from the record (`trade-access` struck,
`materials` and `unique-item` kept), as Bog Iron did; the compile's macro obligation is met.

### Record coherence (step 5b, part C2)
One change set, from one reader's NO list (`tooling/.reports/16k/walk11/coherence/pearl-lots-c2-reader.md`):
- `vibe.palette` "buoy ochre" became "grey-brown keg buoys": no buoy or float exists in the pool
  (sourcing log G19, a completed search; 0102 reason: an asset that exists nowhere), so the keg's
  own colour is the buoy colour.
- `vibe.materials` "weighted belts" became "stone lot cairns": a weighted belt is a diver's worn
  gear, which the NPC equipment system dresses (0102 reason: a later-phase system); the anchor
  weight beside the diver's basket on the bed stays.
- `why.siteAdvantages` "six to twelve metres" became "six to nine": the bed is frozen ground and
  the lots stand 6 to 9 m down (0102 reason: an owner-level world call, the reseat). The hard
  constraint "6-12 m depth" is the siting range and stands.
- "inside the reef" became "inside an offshore bar" in the record and the three site rows: the
  shelter is the 3-6 m bar east of the bed, not a catalogued reef.
- `why.occupantsMotive` no longer says "a surface tender each": the record has one tender (n2)
  and two tender boats are built.
- `playerPurpose.secondary` lost `service-hub` and `assetPlan` lost `submerged-blocks`: neither is
  built. The place has no service; the catch is sold in Archon.
- SX05 is "Lot Four", not "Lot Nineteen": four lots are built. Lot four is the deep lot.
- `whySiteWon` and `plotFacts.landform` carry no "pending" text; the reseat (923 m) is an owner
  call in the walk packet (`plot-remedies.json` `ownerCall`).
- `vibe.senses` stands: sound is a later-phase system (0102); the tenders and the bed baskets are
  its sources.
Not changed, with reasons: `dangerBand 0` is the ground's band, the D1 danger is the work;
`minDepthM 1.0` is the plotter rule gap filed in part A; `reachedVia` Portdun-Mont is 640 m by the
spit; hostile neighbours (contested-bank, gap-reef) are their own places; "four families" in SX06
are claimants, not the divers present; lore: water-breathing does not remove the depth's dangers.

## Feel check

Shots are in `tooling/.reports/16k/place.saxhleel-coast.pearl-lots/round-10/` and `round-11/`. The `eye/` folders hold the walk-through cameras. The `shots/` folders hold the workbench views. The buoys and the tally book were not yet placed.

| Round | Shots | Businesslike | Dangerous | Images kept | Verdict |
|---|---|---|---|---|---|
| 10 | eye 1-6, 5a-5c under water, iso night | partly (eye-3 only) | absent | far boats weak; threshold partly; lot bed not found | fail |
| 11 | the same cameras, a green sea volume, four close-ups from above | partly (eye-c4, eye-3) | absent | far boats specks; threshold found; lot bed not found | fail |

After round 10 the rack and its lantern moved to the jetty foot. The fire moved beside the grading ground. A row of four baskets was placed behind the table. Each lot gained a second cairn. Each lot's edge gained two more plants. Each lot gained a seventh clam. After round 11 the changes were measured with `check` and a `wb.py bpy` script, with no render. The lantern changed to the short-chain argonianlanterns04. Its 2.7 m chain had stood the cage 0.77 m into the sand. The cage is now 0.93 m clear. The clams were drawn into tight patches, 55 % of their spread. The skull moved to the foot of the cairn of the deep lot. The basket row was staggered with a second basket mesh. Still open at the two-round cap: the tenders read as specks from 170 m. Danger shows above water only when the buoys and the lone tender over the deep lot are seen together.
