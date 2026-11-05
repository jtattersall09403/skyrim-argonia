<!-- imported unchanged from elder-souls-argonia docs/research/lore-facts-audit/group1.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Fact audit group 1: geography + cities (37 facts)

## Reconciliation block
Live docs covering this: docs/world/30-lore-systems.md §17-19, §24-27 (failed roads, rootworm, pirates, disease/insects, jellies); docs/world/55-light-sky-time.md:62-84 (season scalar s(t), "resolve from season(), not ad-hoc flags"); docs/world/74-ecology.md:28-33,99-100; docs/quests/20-world-provisions.md:196-232 (named provisions: Bramman's river :206, wintertide Gideon :214, wamasu/grave-stakes); docs/phases/4-buildout/4.5-systems-depth.md:11-25 (cooking :16, seasons :23, creature specials :24, fast travel :20, disease :21); 2.15-boats.md; 2.9b-crafting.md:109 (cooking deferred to 4.5).
Confirmed: seasons are a deferred consumer of an existing scalar (4.5:23); cooking/stations beyond slice are 4.5 (4.5:16); boats/ferries are 2.15/2.6; death hopper, wisp, shine, croc, jelly, hackwing exist as creature rows (registries/creatures.json:244,3172,4492,119).
Contradicted/superseded: none. Gaps the docs do not mention: item spoilage/freshness, pottery/kiln, washtongue, death-hopper harvest items, Stormhold crystal enchant function, skull-bait trap.
Single doc to edit: docs/phases/4-buildout/4.5-systems-depth.md (add rows below); the two slice-now data fixes go in the 2.9b/2.3 item rows (world/sources/registries/items.json, creature-harvest.json). Do not create a new file.

## Table
Cols: id | derivation | exists/planned (file:line) | status | value | effort | timing

| fact | derivation | exists/planned | status | V | E | timing |
|---|---|---|---|---|---|---|
| mer-name-argonia | Dialogue/book: Mer/Imperial characters say "Argonia", Argonians say otherwise; foreigner-vs-native name register in dialogue + a book | outsider names appear in lore dossiers only (black-marsh-province.md) | GAP (flavour only) | L | S | later |
| no-word-for-homeland | Dialogue topic "homeland"; Argonian NPCs never say "Black Marsh" as a nation; style-guide term rule | style guide/2.5 voice register not checked for this term | GAP (flavour only) | L | S | later |
| everything-egg | Gee-Rusleel NPC line; already a book text | world/sources/registries/documents.json mentions kronka only via lore (argonia-4e201-state.md, gap-register.md); loading-facts is its only row | PARTIAL (lore only) | L | S | later |
| regions-of-the-marsh | Region name on place-discovery banner/map region label; Owing regions already name 8 regions | 2.2-ui-system.md:140-145 (place banner); owing.json regionName (2.10 brief :41-42); no player-facing region banner | PARTIAL | M | S | later (add region line to banner when 3.x map polish) |
| borders | Dialogue (road to Cyrodiil, border posts), Claywater import point; border-guard rumours | import-points.json (claywater-station, Blackwood Road); gideon-blackwood-road ferry | EXISTS (as placement) | L | - | - |
| travel-by-boat | Boats as horses; ferries; water taxis | 2.15-boats.md:1-25 (boats), 2.6 ferry 3 (2.6:20), travel-services.json (3 services), 4.5:20 water taxis | PLANNED | H | L | slice (2.15) |
| panther-river | Named river reach: dialogue/map label; Panther frogs' chirp makes voice-actor; fork at Greenspring/Helstrom | waters.md:28; hydrology names (names.json not read for these) | PARTIAL (dossier only) | L | S | later (name on reach in Part 4 packet) |
| onkobra-river | Fast white water near Gideon (a boat-hazard class), red clay delta, muddy road | waters.md:27; 2.15 `navigableReach` falls/rapids typed (2.15:36-37) | PARTIAL | M | S | later |
| blackwood-red-clay | Resource node `node.red-onkobra-clay` (gather at Onkobra banks/Gideon NE), yields clay for pottery; clay jug item | item.clay-jug exists (items.json:1661, whyHere "Red Onkobra clay"); no clay node (resource-nodes.json has plants only); rootworm stop marked by red clay (quests/20:214) | PARTIAL | M | S | later (4.5 cooking/works) |
| washtongue-powder | Misc ingredient `item.washtongue-powder` + pottery firing recipe at a kiln station; sold by potters | nothing in repo outside loading-facts (grep) | GAP | L | M | later (4.5 stations); no Skyrim mesh needed (reuse powder/ingredient clutter) |
| solstice-island | Offshore destination for a boat quest; Solstice book exists | item.book-argonians-of-western-solstice (documents.json:413); offshore feasibility research says islands marginal (docs/research/world-terrain/offshore-islands-feasibility.md) | PARTIAL (book only) | L | L | later (Part 4, if ever) |
| rotting-caravans | Food spoils on long hauls: goods carry freshness; roadside/city vendors sell rotten goods cheap; rot -> disease risk; a boat/ferry courier quest "get it there fresh"; Argonian preservation (smoke, salt) | NO freshness/perishable field on food (items.json:10334 saltrice-loaf has none); trade-classes.json no spoilage; 4.5:16 cooking is not preservation | GAP | M | M | seam-now (see below) |
| seasonal-floods | Season scalar drives crossing state (ford -> ferry), bridges under water "four days" (fauna-hazards.md:55), flood-wrack | world/55:62-84 scalar; world/50:144-145 says NO wet/dry toggle for water level, only draw-down; 4.5:23 "seasons in play" | PLANNED (4.5) | M | M | later; seam: crossing rows already generated (water-crossings.json), add season gate later |
| shadowfen-location | Region identity for Owing/regions; dialogue | owing.json regionName; shadowfen.md | EXISTS | L | - | - |
| murkmire-coast | Oliis Bay access; Keel-Sakka river; mercantile-coast places | places-mercantile-coast.json (lilmoth, oliis-boardwalk); waters.md | EXISTS | L | - | - |
| heart-mud | Hazard surface: black mud "holds a standing man's feet fast" (fauna-hazards.md:51-53) = movement-slow/stuck surface volume at Helstrom; Heart-Mud ingredient/quest sample | no mud/slow surface in 2.12 (wade only 2.12:18,111); Helstrom paused to 4.1b; 4.5:24 damage volumes only | GAP | M | M | seam-now: surface type (see below); content later (4.1b) |
| mangrove-wall | Climbable/divable root wall; hidden cuts and air pockets; smugglers' channel | places: mangrove-wall-village, mangrove-air-pocket, mangrove-cut-village, mangrove-reef, oliis-boardwalk (catalogue saxhleel-coast/mercantile-coast); 2.12 climbs roots (2.12:5,117); quests/20:206 hidden channel | EXISTS/PLANNED (2.12) | H | - | slice (2.12) |
| helstrom-capital | Safe heart city inside a lethal basin; convoy MQ05 | world/30:~82-90 convoy; place.hist-heartland.helstrom active but Helstrom paused to 4.1b (2-slice/README.md:9) | PLANNED (4.1b) | H | L | later |
| helstrom-skull-traps | Trap kind `trap.skull-bait` (Dead-Water: giant croc skull lures/triggers); also bait items | traps.json has only 7 Morrowind spell traps (traps.json); 4.5:11 "trap kinds beyond the slice's (data rows by 2.10's recipe)" | PLANNED (4.5 trap rows, not named) | M | S | later |
| gideon-twyllbek | Flooded Ayleid ruin under Gideon: dungeon + quest | place.imperial-fringe.twyllbek-ruins, twyllbek-crown (catalogue), deeds.json | EXISTS | H | - | - |
| gideon-blackwood-way | Only dry road through a flooded city = causeway district; flood-damaged legs | place gideon, route.road.gideon-blackwood-road, drowning-gate ferry (travel-services.json) | EXISTS | M | - | - |
| gideon-death-hoppers | Poison-spitting pack creature; harvest sacs/bile; Castle Giovesse haunt | creature.death-hopper (creatures.json:244, ecology 74:100, detection loop 2.10), castle-giovesse place (ruined); harvest.death-hopper `items: []` (creature-harvest.json:44-50) "no item record" | PARTIAL: harvest items missing | M | S | slice-now |
| archon-coast | Eastern Padomaic port; shipyard/lighthouse | saxhleel-coast archon places incl. estuary light, shipyard (cut) | EXISTS | L | - | - |
| thorn-jewel | Deadly beautiful city; Dres | place thorn, thorn-paddy-terraces | EXISTS | L | - | - |
| thorn-saltrice | Saltrice crop, food items, Dres profit/slavery, trade good | saltrice-loaf/flatbread/noodles (items.json:10334), stock-tables "Dunmer traders: saltrice" (:635), thorn-paddy-terraces | EXISTS | M | - | - |
| blackrose-prison-apart | Separate dungeon a day's march south | place.imperial-penal-south.blackrose-prison separate from blackrose | EXISTS | M | - | - |
| lilmoth-jewel | Merchant city, sunken villas; era: 4E 201 is the smaller rebuilt stilt town (lilmoth.md:104) | place.mercantile-coast.lilmoth + Under-Yard; dossier era notes | EXISTS | M | - | - |
| lilmoth-shallows | Ships anchor out; lighters carry goods; import point = lighters (import-points.json lighter-flotilla); cargo shuttle/water taxi | import-point.lighter-flotilla; 2.15 boat service; 4.5:20 water taxis | PARTIAL (import yes, taxi 4.5) | M | M | later |
| lilmoth-stilts | Stilt platforms over water; imperial homes sink | argonian-stilt kit/district rule (backlog.md:90) | EXISTS | M | - | - |
| lilmoth-pusbottom | Criminal underground district; fence/thieves | pusbottom-barge place; Owing/fence in 2.10 | EXISTS | M | - | - |
| lilmoth-shines | Harmless wisp cousins: ambient fauna/light, no attack; glow dust | creature.shine (creatures.json:4492) exists; no harvest row, not in creature-harvest.json; wisp harvest.wisp -> item.glow-dust exists | PARTIAL | L | S | later (ambient fauna by Lilmoth packet) |
| stormhold-silyanorn | Ayleid ruin "Library": lore book source, dungeon with a lost book of crystal wisdom | silyanorn-diggings, the-silyanorn-crown, outer-silyanorn places (dunmer-north) ; lost-book hook stormhold.md:47 | EXISTS (places) | M | - | - |
| stormhold-tree-pond | Hist tree in pond ringed by pillars: Hist communion/sap site | place.dunmer-north.stormhold, mazzatun-hist etc.; 4.5:15 Hist communion powers pulled by Hist sites | PLANNED (4.5) | M | M | later |
| stormhold-crystals | Filled crystal = charge source for enchanting/teleport; hollow stores corruption (soul-gem-like). Item exists but NOT usable | item.stormhold-crystal (items.json:12721, value 90, stocked) has no `soulGem` field (petty-soul-gem row does); 2.5x4 notes "fill and hollow like soul gems" but no implementation; 2.9b:32,63 soul gems only | PARTIAL: item without function | H | S | slice-now (see below) |
| soulrest-capital | Quiet Topal Bay port, 3E capital, Governors' Ground graves | places soulrest*, long table tradehouse, import-point.chasepoint | EXISTS | L | - | - |
| eight-major-cities | All 8 cities connected "never absent" acceptance rule | travel-services.json:120 deadEnd rule; places exist (Helstrom paused) | EXISTS (gate) | M | - | - |
| mazzatun-puzzle-city | Puzzle city: lever/gate puzzles, mad Hist Tsono-Xuhil, Xit-Xaht wamasu | places mazzatun, mazzatun-hist; lever gates exist (world/98 "Lever gate"); no puzzle design doc (grep "puzzle" in 2-slice/70/90: none) | PARTIAL | M | M | later (Part 4 dungeon packet; lever-gate record is the seam, exists) |

## Common threads
1. Crystal/soul gem system: stormhold-crystals (fill/hollow), storm-crystal quest item, hollow stores corruption (curse/disease sink). One `soulGem` field gives enchanting, soul-trap-like corruption, Stormhold dungeon loot, and Silyanorn lost-book quest.
2. Food and logistics: rotting-caravans, saltrice (Thorn), lighter shuttle (Lilmoth), seasonal floods, boats. Needs a freshness/shelf-life field on food, price-by-distance later, and 4.5 cooking/preservation (smoke, salt).
3. Pottery/clay: red clay node, clay jug, washtongue powder, kiln station; share one 4.5 chunk with cooking (stations beyond the slice).
4. Season/flood/tide: seasonal-floods, bridges under water, wintertide Gideon stop, rivers: all one consumer of world/55 season(), already 4.5:23.
5. Surface hazards: heart-mud (stuck feet), mangrove roots (climb/dive), deep mud: one "surface type" in movement (2.12 wade) with a slow/stuck rule.
6. Creature harvest: death hopper sacs/bile, shine glow, hopper packs: item rows for creature-harvest.json.
7. Traps/lure: Dead-Water skull traps (trap row), arrow lure (2.10).
8. Naming/flavour dialogue only: mer-name-argonia, no-word-for-homeland, everything-egg, regions list.

## Seam-now candidates
(No gap here is architecturally hard; these are the cheap-now ones.)
1. `item.stormhold-crystal` (items.json:12721): add `soulGem {size, capacity, filled}` like item.petty-soul-gem, plus a filled variant row and a hollow variant (hollow carries `stores: "corruption"`). Slice-now: crystal is already stocked at Dunmer traders (stock-tables.json:635-638); otherwise a bought item that does nothing.
2. `world/sources/registries/creature-harvest.json` harvest.death-hopper (:44): `items: []` -> add `item.hopper-vocal-sac` and `item.hopper-bile` ingredient rows (bile = luck concoction per harvest text). Slice-now (hoppers are in the 2.10 detection loop and 2.7 roster). Reuse existing clutter ingredient meshes (no art).
3. Food perishability: optional `shelfLifeHours` (null = never) on `consumable food` rows in items.json plus matching schema in `packages/world-schema/schemas/` and the inventory stack row; and `freshness` hook in trade-classes.json. Costly to retrofit after inventory/save stacks and shops are scaled; a null default costs nothing now.
4. Movement surface: add a surface `bog-mud` (slow factor, stuck-feet) to the physical-materials/surface vocabulary (physical-materials.json) before 2.12 wade lands; Heart-Mud content later.
5. Station vocabulary: reserve `station.kiln` kind in packages/crafting/src/data/stations.json and `node.red-onkobra-clay` row shape in resource-nodes.json (`kind: mineral`); rows only, built in 4.5.
6. Region field on place discovery banner (2.2:140-145): include `regionName` (owing.json already holds eight names) so region discovery is not a retrofit.

## Slice-now
- stormhold-crystals `soulGem` field (S, H)
- death-hopper harvest items (S, M)

## Most valuable gaps (non-slice)
1. rotting-caravans -> food freshness + preservation + courier quest (M value, M effort, seam now).
2. stormhold-crystals as full enchant/corruption system with Storm Crystal dungeon (H value).
3. heart-mud / bog-mud surface (M/M).
4. clay/washtongue/kiln pottery under 4.5 cooking chunk (M value, L effort).
5. skull-bait trap row (M, S).
6. Mazzatun puzzle-city lever sequences (M, M).

## Recommendations
- Add to 4.5-systems-depth.md the rows: "food freshness and preservation (smoke, salt), pottery and kilns (clay node, washtongue)", "Stormhold crystals as charge/corruption stores", "Dead-Water skull-bait trap", "bog-mud surface". Evidence: gaps above.
- Era check before using lilmoth-jewel as present tense: lilmoth.md:104 (4E 201 is a rebuilt smaller stilt town); loading-facts already use past tense.
