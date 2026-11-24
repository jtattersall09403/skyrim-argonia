# Interiors by kind, and the room shell: measured from the real cells

Read-only measurement, 2026-11-24. All numbers are mine, from the cells; scripts are session-local in
`/tmp/claude-1000/-home-ubuntu-skyrim-argonia/2a65b431-ff7b-4ba9-b9df-4fa9beab7dcb/scratchpad/w/` (extract2.py, classify.py, tags.py,
stage1.py, agg.py, agg2.py; not committed). Units: 70 game units = 1 m (tools/places/extract.py UNITS_PER_M); distances below are in units
(u) unless "m". Sample size sits beside every number as n=.

## 0. Live docs and the one to edit
- Covered today: `docs/research/new-art/interior-dressing.md` section B (112 houses/huts; floor things 78.5% within 30u of the walkable edge; 5.7 lights per
  vanilla house; 27% of small items unresolved) and `docs/research/new-art/interiors.md` (shells and kits at asset level; I read both heads, not every line).
- Confirmed: floor things stand against something. Here, with real shell collision walls instead of the walkable edge, 77% of loose floor items are <=40u
  from a wall (n=12,981 items, all 1,064 cells). Light refs per house: median 7 (n=219, vanilla+DLC+mods; the earlier 5.7 was vanilla only).
- Superseded: the earlier lane's "houses only" scope; a house is 219 of the 750 non-dungeon cells here. Its on-surface test used bounding boxes; mine uses collision
  triangle profiles of the supporting mesh (`tools/places/seat.solid_profile`), so its on-surface share (a lower bound) is not comparable to D below.
- Doc the writer should edit: `docs/research/new-art/interior-dressing.md` (add sections G-I and the per-kind tables); no new file. PT-derived checks go in its
  section C (skill design).

## 1. Method (what was read, how kinds were decided)
- Read every interior CELL and its REFRs (tools/argonia_world/esm.py): Skyrim, Update, Dawnguard, Dragonborn, HearthFires, Black Marsh.esm, Black Marsh North.esp,
  Valenwood.esp, King of the Murkmire, Journey to Baan Malur, Tropical Skyrim, ArgonianLakeHouse, Cathnoquey, Dawn of Skyrim, Grey Quarter Overhaul, Dunmer
  Settlements Solstheim, SolstheimExpand, CampNewZainab, Sailable Ship. 1,196 interior cells; 1,064 with >=12 refs analysed (22 of those had no furniture).
  "vanilla+DLC" = origin plugin Skyrim/Update/Dawnguard/Dragonborn/HearthFires; "BM&V" = Black Marsh.esm, Black Marsh North.esp, Valenwood.esp; "mods" = the rest.
  Cells counted by the plugin that FIRST defines them (form-id owner), overridden refs honoured, deleted/initially-disabled refs dropped.
- Kind by evidence in this order: junk/test names dropped; cell LOCATION keywords (LocTypeInn, Store, Temple, Jail, Barracks, Guild, Mine, Castle, Dwelling,
  House, dungeon-type keywords) via the cell's XLCN link; then cell edid + name patterns (smith, alchemist, clothier, bakery, temple, shrine, bunkhouse,
  cellar, longhouse, farm, mill, shipwreck...); then owner/furniture were read as MEASURES, not used to classify (so "alchemist has an alchemy bench" is a result).
  Known error: about 5-10% of cells sit in a neighbouring kind (spot-read of the lists: Falion's House as shop; Thalmor HQ as barracks; Hrodulf's House as camp;
  several BM&V `01xxx` cells are unnamed and fall to dungeon/other). Medians are robust to a few; kinds with n<12 are marked thin.
- Per-ref tags from base edid/signature (tags.py): bed, bedroll, seat, table, counter, cooking, fire, shelf, chest, wardrobe, dresser, cupboard, sidetable, barrel,
  crate, sack, urn, workbenches by FURN type (alchemy, enchanting, smith), shrine, weaponrack, bath, prison, wall decor, rugs, light refs (LIGH) and lit props
  (candle/lantern/chandelier statics), small things by class (tableware, food, drink, book, candle, ingredient, potion, tool, vessel, valuable, apparel...).
- Surfaces: a small thing rests on a table/shelf/counter/bed/etc. when its origin is inside that mesh's plan footprint (collision profile, 24x24 cells) and its
  lowest point is within 14u of the profile top ("top") or, for shelves and cupboards, between the profile base and the top ("in" = a shelf level). Shelf LEVELS
  are not separated (collision is a box); level is only the item's height. Floor things: lowest point within 12u of the nearest floor furniture's z.
- Walls: vertical collision triangles of the shell pieces (big non-clutter statics) projected to segments; "against a wall" = footprint boundary <=40u from a
  segment at that height; corner = two non-parallel walls <=70u. Cells with <=20 segments are excluded from C (the shell was not found: mostly mud-hut/whole-mesh shells
  and BM&V cells).
- Shell: shell pieces = statics that are big (>=120u) and not under clutter/furniture/effects; piece type from edid words; kit = first three folders of the model
  path; textures = the diffuse .dds paths found in each piece's NIF; materials by words in the file name; floor/ceiling from upward/downward collision faces.

## 2. Findings first (the numbers a planner can start from; detail in sections A-I below)
Presence (share of cells of the kind holding it; median count when present) is table B. The short list:
- house (n=219): bed 94% (2 slots, 1 per resident median; beds-per-resident 1.0 [p10 1.0-p90 2.0], n=113), table 96% (2), seats 92% (2), shelf 83% (2), cooking pot/spit 79%,
  hearth 65%, barrel 84% (5), cupboard 55%, sidetable 47%, chest 57%, dresser 42%, wardrobe 26%, counter 8%, shrine 4%, bath 8%, alchemy bench 8%, smith bench 5%.
- inn (n=59): counter/bar 59%, tables 5, seats 7, beds 4 slots (83% have one), hearth 71%, cooking 73%, barrels 7; bed against a wall 96%, head within 40u of a wall 74%.
- shop_general (n=53): shelf 89% (4), counter 43%, barrel 89%, crate 79%, bed 68% (living above/behind). smith (n=12): smith bench 67%. alchemist (n=15): alchemy
  bench 87% and counter 67%. temple (n=27): shrine 70%, bed 74%. jail (n=14): prison fittings 57%. fort/hall_keep: weapon racks 38%/29% (median 30/16 pieces).
- Placement, pooled house: bed against wall 77%, in a corner 44%; table 66% against wall; seats 48% (free-standing around tables); shelves 81% against wall (7u
  median); sidetable/dresser/cupboard 76-83%; fires 87% against wall and 73% in a corner; weapon racks 98%. Seats within 160u of a table or fire: 69% of seats (620 of 896 in houses), and of
  those 69% have their axis within 30deg of it (either way). Bed head within 40u of a wall: 48% house, 74% inn.
- On what (D): table 5 items median (p10 1 - p90 13; n=2,722 tables with items; mix tableware 33%, food 23%, drink 9%, valuables 6%); shelf 6 (n=3,696); counter 2
  (n=670); sidetable 2; cupboard 7; barrel 1; alchemy bench 66% ingredients/19% potions (n=32); cooking pot 49% food; beds almost never carry items (2/429 in houses).
  In houses 426 of 550 tables (77%) and 582 of 767 shelves (76%) hold something; 36% of counters hold anything.
- Walls (E): in houses 40% of sampled wall faces are covered by floor furniture, 3% by hung decor only, 57% bare (n=203 cells); hung decor per house median 2 (p90 12), centre
  height median 158u above floor (2.3 m; p10-p90 69-357u); halls 6 (p90 28), centre 221u; guild halls 16.
- Light (F): lit refs 7.7 per 100 m2 of occupied area in houses (n=219), 7.6 inns, 5.8 halls, 12 alchemists; nearest light to a seat 119u median (1.7 m), to a bed 145u,
  to a work spot 133u (houses). Kinds: candle 55%, hearth fire 14%, lantern 7%, window sun 7%. Lighting template set on 93-100% of cells of every kind.
- Wealth (G): house small items per cell 32 poor (n=19) / 43 mid (n=158) / 135 rich (n=18); rugs 3/3/8.5; hung decor 8/1/10; shelves 2/2/10.5; light refs 5/7/32; floor
  area (hull) 64/90/322 m2. Cell owner present on 85% of houses (104 faction, 83 NPC of 219), 90% inns, 92% shops.
- Room sets (H): of 1,064 interior cells only 309 have a teleport door to another interior cell in the set; buildings are mostly 2 cells (74 of 115 multi-cell
  buildings), 3 cells (27); the commonest orders from the exterior door are main > cellar, main > upper (inn/guild), hall > annex, jail > barracks.
- Shell (I): rooms are kits of floor/wall/corner/ceiling/beam/doorframe/stair pieces; houses median 7 shell pieces (p90 145) with 10% a whole-room mesh; inns 19,
  shops 15, halls 76, guilds 167, mines 118. Houses mix a median 9 distinct diffuse textures on the shell (poor 6.5, mid 9, rich 13); timber/plank in 98% poor
  vs 76% mid vs 91% rich; stone/brick 39% poor, 47% mid, 94% rich; plaster 48% rich. Ceiling height median 240-250u (3.4-3.6 m; houses n=80, inns n=24).

## 3. What we hold for Black Marsh and each culture (kit inventory, completeness, fit)
Source: out/places/catalogue/bases.jsonl (STAT, >=90u, non-clutter) grouped by model folder; looked at through `python -m tools.places search sheet` (contact
sheets read by eye; "COULD NOT LOOK black" notes on the sheets are the thumbnail renderer failing on shells, not a missing mesh). A piece count is not a kit.
Grid = modal width of wall/floor pieces (OBND, rounded to 16u).
- Argonian mud hut (KotM `argonia/mudhuts`, 44 pieces): WHOLE-ROOM shells, one dome per hut: MudHut01-06 `Ext` + `Int` pairs, extensions, chimney, stairs 01-03,
  2 floors, 3 walkways, doorway, awnings, a house01. Looked: domes; interiors are single meshes (renders black) = no wall/floor/corner/ceiling pieces at all.
  Used by 57 of our cells (house 12, inn 11, shop 9, smith 5, ...). ArgonianLakeHouse.esl `gv_meshes/argoniannest` (34): MudHut01Int shell, RoundFloor01,
  RoundThatch01, WallShell, tent, woven fences/table/bookshelf/wall shelf, bone chimes, platforms (looked: whole-hut kit, round plan, no ceiling/door pieces).
- Argonian reed / stilt plank (KotM `argonia/blackwood`, 183 pieces; used by 61 cells: house 11, shop 11, inn 11, barracks 7, smith 6): six whole-room
  `MurkmireHousePartionInt01-06` shells + wall panels IntWall01-03 (+window/door variants, window frame, door frame), PlankWall01-04 A/B, plank floors, platform bases,
  house shells 01/04/06 (Cypress/Beige). Grid 256. Looked: timber stilt houses, dark plank. Complete for floors, walls, door/window frames, stairs 5, loft 14; missing: ceilings
  other than the roofed shells, corners (only as fixed shells), hearth/chimney built-in, thatch interior. HTBM Curse of Cipactli `architecture/villages` (23): Hut1/Hut2 interior
  domes, KothGreatHouseInt, 3 docks, poles, plank, native table (whole-hut kit, not used by any cell we hold).
- Xanmeer stone (XanmeerResources.esp 27 interior pieces + KotM `argonia/xanmeer/interior` 43 + `architecture/xanmeer/interior` 40 + rubble 40): grid 256; floor 8-9, wall
  7-11, corner 3-4, ceiling 9-13, stair 3-6, loft 2-3, FreeFloor 1x1/2x2/3x3, RoomFloorBalcony/Lowered/Broken. Used mostly by the big Xanmeer dungeons (Xocei-Tluthek 996
  pieces, Lilmoth Roots 1,084); no house, shop or inn in the sets uses it. Missing: door frames beyond 3, beams, windows, hearths.
- Root-grown / Hist: `argonia/xanmeer/roots` (15: wall 6, floor 2, ceiling 2), Hist tree models (51, exterior), `evgSIRENROOT.esm` (76 pieces, creation-club dungeon
  set). KotM's "Roots" cells (KeebaRoots, LilmothRoots, SpirelandsHistTreeRoots) are cave/Xanmeer dungeon kits with roots as dressing; there is NO root-grown
  domestic shell (house/shop/inn) in anything we hold.
- Imperial colonial (`tesak1243/mwimperialarchitecture/architecture`, 357 pieces; Baan Malur 182, KotM 169; wall 80, corner 32, stair 26, doorframe 17, floor 8, ceiling 2;
  grid 256/512; plus `argonia/imperialruins`, `hlaaluarchitecture/*` in ArgoniaOwn: doorframe 17, corner 6, wall 5, stair 4): good walls and corners, thin floors/ceilings,
  used for exteriors and some interiors (apothecary 3 of 9 shell pieces).
- Dunmer (Baan Malur): `morrowind/sheogorad/dagon fel` (172; house 44 cells, inn 12, warehouse 6, farm 6, temple 6; wall 15, stair 12, door 11, hearth 9, shelf 5), `.../velothi`
  (243; pillar 30, wall 27, corner 24, stair 23, ceiling 19; grid 256), `tesak1243/mwnordhouse` (69; modular: corner 12, door 11, hearth 5, floor 4), `morrowind/rootspire`
  (49), `morrowind/pancake/platforms|ship` (lofts, beams, ship walls), `ashlandernewzainab` and `vvardenfell/ashlanderhut` (tents). Vanilla Solstheim `dlc02/architecture/ravenrock`
  (208) is the most-used house kit (57 houses, 18 inns, 17 shops). Fit: complete for houses, inns, shops; no barge/ship kit apart from `pancake/ship`.
- Ship/barge holds: Sailable Ship.esm `aaaship/interiors` (8 cells; per ship room: beam 51, floor 40, wall 30 pieces: a true modular hull), SOMR `morrowind/pancake/ship`,
  `bstamriel/dungeons/ships/cyrodiilicships/interiors` (ArgoniaOwn 45 + BMalur 12), vanilla `dungeons/ship/*`, KotM `argonia/stockades` + `tradeship` (The Lady Padomay 5 pieces,
  456 m2 of ship deck by collision). Whole-hull shell with piece-wise wood walls; no cargo-hold/bilge shell with ladders and hatches except Skyrim `dungeons/ship`.
- Bosmer (Valenwood.esp): `architecture/citebosmer/houses` (22; whole house shells 15, walls 3, doors 2, stair, loft), `passerelles` (14 walkways), `telvanni` (13), `rochester/house`
  (24), `seaview/mr_siika` (12), `manny_gf/alikr` (14: wall 3, ceiling 2, floor 1, pillar 1). 01treeint uses 75 citebosmer houses pieces, 01GrahtOaks 66 passerelle + 19 house.
- Black Marsh.esm / Black Marsh North.esp (BM&V) bring few own shells: `stroti/dragonstone/manor` (whole manor), `stroti/hobbit home`, `architecture/small house`, `phitt/aldredanyia|ashlands|stronghold`
  (7-14 each), `rochester/house` 8; its 24+ interiors otherwise reuse `riften/interior`, `shackkit`, caves and Dwemer kits.
- Which of our interior kinds have NO fitting shell: (1) root-grown/Hist-tree domestic rooms (house, inn, shop); (2) an Argonian MODULAR floor/wall/ceiling/corner set (every Argonian
  kit is whole-hut or whole-house; none has wall+corner+ceiling pieces you can tile into a variable plan); (3) temples/shrines other than Xanmeer stone (Baan Malur temple kits are Dunmer);
  (4) Argonian barracks/jail and counter-bearing shops use re-skinned mud-hut/blackwood shells (barracks 7+5 of 30 cells); (5) cargo-hold/ship-hold interiors; (6) mines/warehouses in
  Argonian style (warehouse 15 cells use `dagon fel` 6, blackwood 2, mudhuts 2).

## 4. Project Tamriel interior guide: what to adopt as planner checks (Skyrim equivalents measured here)
Only principles that hold in any engine. Dropped as Morrowind-specific: showcase and claim workflow, Construction Set, CSSE/snap, path-grid, TD asset ids and the named
Velothi 2x3 shell, NorthMarker, "must have 10 Tamriel_Data items", tableware per Morrowind culture, ID/key naming rules, Illegal-To-Sleep, cleaning with TESAME.
1. Judge clutter against comparable finished rooms, fitted to the owner's class. Skyrim equivalent: per-kind and per-wealth medians in B, D2, G (house items 32/43/135 poor/mid/rich;
   small items 213 hall rich vs 99 hall mid). Check: item count per room within p10-p90 of the same kind AND class.
2. Do not mix poor, middle and rich furniture sets without a reason. Equivalent: style prefixes (Farm/Wooden vs Common vs Noble/Upper): 7% of houses mix (14 of 209 with >=3 style pieces),
   95% are one class by >=60%. Check: >=60% of style-bearing furniture from one class unless the room is a cellar, servants' or guard room.
3. Placement is deliberate, not random ("spoon in an empty bowl", "axe head on floor, handle on wall"). Equivalent: every small thing has a support (D: top/shelf-level contact by
   collision profile) or, on the floor, a wall within 40u (77%) ; seats face their table/fire (69% within 30deg). Check: no loose thing floats; floor things <=40u from a wall or large furniture.
4. Things rest truly (no floaters, no bleeders). Equivalent: item lowest point within 14u of the support top (tables, counters, beds) or inside a shelf volume; floor items within 12u of the floor.
   Check by collision triangles, never bounding boxes.
5. Stairs without gaps; upper floors reached by stairs not trapdoors. Equivalent: navmesh connectivity from door to every bed/seat/work spot through the stair; shells show stairs in 26% of houses, 53%
   of inns, trapdoors in 6% / 10% (stairs 4-5x commoner than trapdoors in town interiors). Check: navmesh path door -> each functional spot, including up the stair.
6. Rooms read as lived in. Equivalent: bed present (houses 94%, inns 83%, barracks 87%, temples 74%), a table with a place setting set (77% of house tables hold items), owned beds (115 of 210 houses),
   residents per bed ~1. Check: the kind's presence table B.
7. Light set per room. Equivalent: the cell's lighting template (set on 93-100% of vanilla/mod cells), light refs per 100 m2 (houses 7.7, halls 5.8, inns 7.6), nearest light to seat 120u / bed 145u.
   Cell Owner field and the Public Area flag (17% houses, 90% inns, 85% temples, 92% forts) are Skyrim's reading of "illegal to sleep here": owned bed = sleeping is theft.
8. No cookie cutting: do not paste identical rooms. Equivalent: the earlier lane found Helstrom carries 17 copies of one house; Baan Malur's dockhouse cells are the same shell with a few moved
   things (e.g. BaanWDDockhouseLarge01..09 hold 82-111 refs). Check: base-set similarity between rooms of the same kit under a cap (not measured here: see Not measured).
9. Fit the exterior. Equivalent: a door's interior kit shell matches the exterior mesh folder (kit name) and the room's floor m2 is within the exterior footprint; floor-area data in I.
Not adopted: the numeric floor-space/clutter minimums (the page's own numbers were not in the supplied file).

## 5. (Superseded: every item below is now measured in section 5.1-5.9 at the end; only 5.10 is unreadable)
Original list kept for the record:
- Real ceiling height for 64% of rooms: no downward collision face at a recognisable level (whole-mesh shells, open ceilings). Where measured: houses n=80 med 250u, inns n=24 245u.
- Floor area from shell collision overstates (stacked upward faces within 30u): house shell floor med 172 m2 vs 95 m2 span of furniture and 67 m2 walkable in the earlier lane. Use floor m2 in I only
  as a ratio between kinds; the earlier walkable-mesh figure is the better absolute.
- Wall length covered: sampled points 30u off wall faces; both faces of thin walls are sampled, so "bare" includes door openings, windows, stairs. Figures are shares, not metres.
- Shelf levels and what is on which level (collision is a box); hooks/hangers (no hook record); facing of a seat (axis only, front unknown); counter-between-door-and-stock (not computed: no shop
  has a reliable "stock wall"); items by a bed on the floor (not computed; only on-bed and floor-wide numbers).
- Texture roles: floor/wall/ceiling textures only for shell pieces whose edid names the role; 35-55% of wall textures fall in "other" (non-material file names like dlc2rrbuildings01).
  Texture appearance (colour, wear) was not read, only names. Materials by file-name words.
- Trade/faith marks beyond furniture (banners, books, tools by owner class): owner faction lists in G; no mapping from faction to trade was done.
- Rooms in a building: door graph uses teleport doors found among our set; many interiors link to cells outside the set (exterior or dungeon) so sizes are lower bounds.
- Wealth: derived from furniture style prefixes (cells with >=3 style-bearing pieces: 209 of 219 houses); mod styles (mud hut, blackwood, Dunmer) fall under "mid/poor" by name only.
- Exemplar cells and kind labels were checked by eye on lists, not by looking in game.

## 6. Exemplar cells (read in the data: ref counts, set of functional things)
- house: Breezehome, Alvor and Sigrid's House, Hjerim (HearthFires/vanilla, wealthy end: Proudspire Manor); mods: BaanEDDockhouseLarge03 (Fredrik's House, 84 refs), SeekhatPlayerhome (169).
- inn: Sleeping Giant Inn, Bannered Mare, Silver-Blood Inn; mods: LilmothTaverna (Tsonashap-Uxith, 387), The Moist Tankard, Scrambling Scrib.
- shop: Belethor's General Goods, Arcadia's Cauldron (alchemist), The Scorched Hammer / Solitude Blacksmith (smith), Radiant Raiment (clothier); mods: Lilmoth Ironworks, Black-Tongue Brews, Baan Malur Brews, Drol Smithy.
- temple: Temple of Kynareth, Temple of Dibella, Hall of the Dead; mods: Temple of Reclamations, Shrine to Boet-hi-Ah. barracks/jail: Dawnstar Barracks, Falkreath Jail; mods: Cormaris Barracks, Fort Tulis Prison Block.
- hall: Jarl's Longhouse (Whiterun Dragonsreach/Bluepalace), Largashbur Longhouse, Mistveil Keep; mods: Lilmoth Dragonthorn Manor, Llynelis Manor. farm/mill: Chillfurrow Farm, Torolf's Mill; mod: Monger Mill.
- ship: Sailable Ship Captain's Cabin; KotM The Lady Padomay; Baan Malur Redoran Warship. mine: Kolskeggr/Left Hand Mine; Llerush Kwama Mine. cellar: Alva's Cellar; Wine Cellar (Baan Malur).

## Recommendations
1. Re-run this with 1 added pass (<= 30 min) for items-by-a-bed and shop counter orientation if the planner needs them (evidence: section 5, both skipped for lack of a reliable reference).
2. Make the measurement a committed tool (tools/places/dressing_measure.py as the earlier lane proposed) so numbers renew; the scratch scripts hold the whole method.
3. Treat the Argonian modular shell gap (section 3 point 2) as the planner's first hard constraint: every Argonian interior kind must pick a whole-hut/whole-house shell today.

# APPENDIX A: full tables (runs 2)
## A. Cells measured by kind (n; split vanilla+DLC / BM&V / mods)
- dungeon: 314  ({'mods': 35, 'BM&V': 20, 'vanilla+DLC': 259})  median refs 928
- house: 219  ({'mods': 117, 'BM&V': 7, 'vanilla+DLC': 95})  median refs 124
- hall_keep: 62  ({'BM&V': 2, 'mods': 19, 'vanilla+DLC': 41})  median refs 344
- inn: 59  ({'vanilla+DLC': 23, 'mods': 36})  median refs 221
- shop_general: 53  ({'mods': 31, 'vanilla+DLC': 22})  median refs 143
- other: 45  ({'vanilla+DLC': 15, 'mods': 22, 'BM&V': 8})  median refs 168
- mill_farm: 41  ({'vanilla+DLC': 25, 'mods': 16})  median refs 149
- bandit_camp: 32  ({'vanilla+DLC': 29, 'mods': 2, 'BM&V': 1})  median refs 712
- barracks: 30  ({'mods': 15, 'vanilla+DLC': 15})  median refs 139
- temple: 27  ({'mods': 12, 'vanilla+DLC': 15})  median refs 213
- guild: 25  ({'mods': 4, 'vanilla+DLC': 18, 'BM&V': 3})  median refs 714
- fort: 24  ({'vanilla+DLC': 24})  median refs 378
- mine: 21  ({'vanilla+DLC': 19, 'mods': 2})  median refs 365
- warehouse: 15  ({'mods': 11, 'vanilla+DLC': 4})  median refs 64
- alchemist: 15  ({'mods': 7, 'vanilla+DLC': 8})  median refs 157
- cellar: 14  ({'vanilla+DLC': 11, 'mods': 3})  median refs 226
- jail: 14  ({'vanilla+DLC': 10, 'BM&V': 1, 'mods': 3})  median refs 195
- ship: 12  ({'mods': 12})  median refs 141
- smith: 12  ({'mods': 9, 'vanilla+DLC': 3})  median refs 161
- clothier: 4  ({'mods': 2, 'vanilla+DLC': 2})  median refs 188
- camp_tent: 3  ({'mods': 3})  median refs 40
- fletcher: 1  ({'vanilla+DLC': 1})  median refs 500

## B. What it contains: share of cells holding each thing | median count when present
kind(n) bed bedroll seat throne table sidetable counter cooking fire shelf chest wardrobe dresser cupboard barrel crate sack basket urn wb_alchemy wb_smith wb_enchant shrine weaponrack bath prison dummy
dungeon(314) bed:27%/2 bedroll:21%/2 seat:56%/4 throne:0%/1 table:66%/4 sidetable:11%/2 counter:18%/5 cooking:23%/2 fire:38%/2 shelf:66%/6 chest:89%/3 wardrobe:3%/2 dresser:12%/1 cupboard:11%/2 barrel:53%/9 crate:33%/8 sack:32%/5 basket:1%/6 urn:40%/8 wb_alchemy:17%/1 wb_smith:7%/2 wb_enchant:14%/1 shrine:52%/5 weaponrack:5%/15 bath:1%/2 prison:54%/3 dummy:6%/2
house(219) bed:94%/1 bedroll:4%/3 seat:92%/2 throne:21%/2 table:96%/2 sidetable:47%/1 counter:8%/6 cooking:79%/2 fire:65%/1 shelf:83%/2 chest:57%/1 wardrobe:26%/1 dresser:42%/1 cupboard:55%/1 barrel:84%/5 crate:60%/5 sack:33%/6 basket:6%/3 urn:36%/4 wb_alchemy:8%/1 wb_smith:5%/1 wb_enchant:3%/1 shrine:4%/1 weaponrack:4%/16 bath:8%/1 prison:4%/3 dummy:4%/1
hall_keep(62) bed:68%/4 bedroll:10%/2 seat:89%/9 throne:24%/1 table:90%/5 sidetable:50%/5 counter:21%/7 cooking:65%/3 fire:65%/2 shelf:90%/8 chest:77%/2 wardrobe:44%/2 dresser:44%/3 cupboard:39%/3 barrel:82%/7 crate:66%/7 sack:58%/6 basket:5%/3 urn:19%/6 wb_alchemy:23%/1 wb_smith:11%/3 wb_enchant:26%/1 shrine:11%/2 weaponrack:29%/16 bath:21%/2 prison:15%/2 dummy:18%/2
inn(59) bed:83%/3 bedroll:7%/1 seat:93%/7 throne:14%/2 table:93%/5 sidetable:36%/2 counter:59%/6 cooking:73%/2 fire:71%/2 shelf:86%/3 chest:71%/2 wardrobe:34%/1 dresser:44%/1 cupboard:34%/2 barrel:86%/7 crate:63%/6 sack:36%/6 basket:19%/4 urn:47%/5 wb_alchemy:8%/1 wb_smith:5%/1 wb_enchant:5%/1 shrine:7%/4 weaponrack:5%/16 bath:10%/1 prison:0%/0 dummy:3%/2
shop_general(53) bed:68%/1 bedroll:6%/1 seat:79%/2 throne:4%/1 table:87%/2 sidetable:30%/1 counter:43%/5 cooking:42%/2 fire:49%/1 shelf:89%/4 chest:75%/2 wardrobe:23%/1 dresser:34%/1 cupboard:43%/1 barrel:89%/6 crate:79%/6 sack:47%/5 basket:15%/4 urn:47%/3 wb_alchemy:8%/1 wb_smith:21%/2 wb_enchant:4%/2 shrine:8%/1 weaponrack:9%/3 bath:8%/1 prison:2%/1 dummy:9%/1
other(45) bed:36%/2 bedroll:22%/2 seat:64%/4 throne:9%/1 table:71%/2 sidetable:29%/2 counter:13%/6 cooking:18%/2 fire:33%/2 shelf:47%/4 chest:44%/2 wardrobe:9%/4 dresser:24%/2 cupboard:22%/1 barrel:44%/10 crate:51%/3 sack:24%/2 basket:0%/0 urn:22%/4 wb_alchemy:13%/1 wb_smith:9%/3 wb_enchant:9%/1 shrine:24%/4 weaponrack:2%/14 bath:2%/1 prison:16%/3 dummy:4%/6
mill_farm(41) bed:95%/1 bedroll:5%/2 seat:98%/2 throne:7%/1 table:98%/2 sidetable:44%/1 counter:2%/7 cooking:80%/2 fire:68%/1 shelf:73%/2 chest:56%/1 wardrobe:27%/1 dresser:44%/1 cupboard:56%/1 barrel:83%/5 crate:44%/5 sack:44%/4 basket:7%/2 urn:29%/3 wb_alchemy:5%/1 wb_smith:5%/2 wb_enchant:0%/0 shrine:12%/1 weaponrack:0%/0 bath:2%/1 prison:0%/0 dummy:0%/0
bandit_camp(32) bed:53%/2 bedroll:62%/4 seat:84%/5 throne:0%/0 table:100%/5 sidetable:16%/1 counter:9%/6 cooking:47%/2 fire:69%/1 shelf:88%/4 chest:94%/2 wardrobe:9%/2 dresser:31%/2 cupboard:31%/2 barrel:94%/15 crate:78%/9 sack:78%/6 basket:0%/0 urn:12%/10 wb_alchemy:19%/1 wb_smith:34%/2 wb_enchant:9%/1 shrine:16%/4 weaponrack:19%/8 bath:0%/0 prison:53%/2 dummy:19%/2
barracks(30) bed:87%/3 bedroll:13%/4 seat:93%/4 throne:0%/0 table:97%/2 sidetable:33%/4 counter:13%/18 cooking:60%/2 fire:60%/1 shelf:93%/2 chest:70%/2 wardrobe:23%/1 dresser:33%/2 cupboard:37%/1 barrel:77%/6 crate:57%/6 sack:33%/5 basket:20%/3 urn:23%/3 wb_alchemy:3%/1 wb_smith:17%/2 wb_enchant:7%/1 shrine:17%/2 weaponrack:13%/8 bath:17%/1 prison:3%/2 dummy:10%/2
temple(27) bed:74%/2 bedroll:0%/0 seat:89%/4 throne:4%/1 table:78%/2 sidetable:37%/2 counter:7%/8 cooking:44%/1 fire:26%/2 shelf:70%/2 chest:41%/2 wardrobe:22%/2 dresser:26%/1 cupboard:19%/2 barrel:63%/3 crate:52%/8 sack:48%/5 basket:0%/0 urn:44%/5 wb_alchemy:4%/1 wb_smith:4%/1 wb_enchant:0%/0 shrine:70%/3 weaponrack:4%/16 bath:7%/2 prison:11%/4 dummy:0%/0
guild(25) bed:76%/3 bedroll:16%/1 seat:88%/14 throne:20%/2 table:96%/4 sidetable:60%/12 counter:16%/6 cooking:32%/2 fire:32%/8 shelf:88%/10 chest:80%/3 wardrobe:52%/3 dresser:56%/4 cupboard:60%/4 barrel:88%/10 crate:92%/11 sack:56%/6 basket:0%/0 urn:16%/10 wb_alchemy:28%/1 wb_smith:12%/3 wb_enchant:20%/1 shrine:12%/3 weaponrack:16%/20 bath:40%/1 prison:24%/4 dummy:16%/2
fort(24) bed:71%/6 bedroll:38%/3 seat:96%/7 throne:0%/0 table:96%/5 sidetable:46%/1 counter:29%/11 cooking:42%/3 fire:67%/2 shelf:83%/5 chest:96%/4 wardrobe:17%/2 dresser:50%/2 cupboard:46%/2 barrel:88%/9 crate:42%/4 sack:54%/10 basket:0%/0 urn:12%/2 wb_alchemy:17%/1 wb_smith:17%/1 wb_enchant:12%/1 shrine:12%/1 weaponrack:38%/30 bath:0%/0 prison:46%/5 dummy:21%/2
mine(21) bed:5%/1 bedroll:33%/1 seat:62%/3 throne:0%/0 table:81%/3 sidetable:0%/0 counter:5%/8 cooking:38%/2 fire:24%/1 shelf:52%/2 chest:43%/1 wardrobe:0%/0 dresser:0%/0 cupboard:0%/0 barrel:95%/6 crate:81%/7 sack:62%/5 basket:0%/0 urn:10%/10 wb_alchemy:0%/0 wb_smith:5%/1 wb_enchant:0%/0 shrine:10%/4 weaponrack:0%/0 bath:0%/0 prison:24%/1 dummy:5%/3
warehouse(15) bed:40%/2 bedroll:0%/0 seat:53%/4 throne:0%/0 table:47%/2 sidetable:13%/3 counter:7%/3 cooking:40%/2 fire:27%/1 shelf:93%/2 chest:27%/2 wardrobe:7%/1 dresser:13%/1 cupboard:27%/2 barrel:80%/10 crate:53%/5 sack:27%/4 basket:20%/2 urn:47%/4 wb_alchemy:0%/0 wb_smith:0%/0 wb_enchant:0%/0 shrine:0%/0 weaponrack:0%/0 bath:0%/0 prison:0%/0 dummy:0%/0
alchemist(15) bed:87%/1 bedroll:0%/0 seat:73%/3 throne:7%/1 table:100%/3 sidetable:40%/2 counter:67%/6 cooking:73%/3 fire:47%/1 shelf:93%/3 chest:87%/2 wardrobe:27%/2 dresser:60%/1 cupboard:40%/1 barrel:73%/6 crate:80%/5 sack:53%/4 basket:13%/4 urn:27%/2 wb_alchemy:87%/1 wb_smith:0%/0 wb_enchant:0%/0 shrine:7%/1 weaponrack:0%/0 bath:13%/1 prison:0%/0 dummy:7%/3
cellar(14) bed:29%/2 bedroll:0%/0 seat:71%/2 throne:0%/0 table:86%/2 sidetable:29%/2 counter:14%/4 cooking:14%/1 fire:0%/0 shelf:93%/4 chest:79%/2 wardrobe:14%/1 dresser:29%/1 cupboard:21%/3 barrel:93%/6 crate:64%/8 sack:50%/4 basket:0%/0 urn:21%/2 wb_alchemy:14%/1 wb_smith:21%/1 wb_enchant:0%/0 shrine:7%/1 weaponrack:29%/16 bath:0%/0 prison:7%/32 dummy:7%/3
jail(14) bed:43%/4 bedroll:64%/3 seat:93%/3 throne:0%/0 table:93%/3 sidetable:21%/3 counter:7%/14 cooking:0%/0 fire:29%/2 shelf:71%/4 chest:86%/2 wardrobe:21%/2 dresser:29%/2 cupboard:14%/2 barrel:86%/9 crate:64%/6 sack:64%/10 basket:0%/0 urn:14%/2 wb_alchemy:0%/0 wb_smith:7%/1 wb_enchant:0%/0 shrine:0%/0 weaponrack:7%/15 bath:7%/1 prison:57%/2 dummy:14%/2
ship(12) bed:92%/2 bedroll:42%/2 seat:67%/1 throne:0%/0 table:92%/3 sidetable:17%/10 counter:8%/36 cooking:42%/2 fire:25%/1 shelf:58%/3 chest:67%/2 wardrobe:17%/3 dresser:25%/3 cupboard:25%/3 barrel:83%/12 crate:83%/12 sack:42%/9 basket:0%/0 urn:17%/1 wb_alchemy:25%/1 wb_smith:25%/3 wb_enchant:25%/1 shrine:0%/0 weaponrack:25%/15 bath:8%/1 prison:8%/2 dummy:0%/0
smith(12) bed:67%/2 bedroll:0%/0 seat:75%/3 throne:8%/1 table:92%/3 sidetable:33%/1 counter:8%/1 cooking:50%/2 fire:75%/2 shelf:83%/5 chest:67%/1 wardrobe:17%/2 dresser:17%/2 cupboard:33%/1 barrel:75%/9 crate:75%/10 sack:50%/6 basket:25%/4 urn:33%/2 wb_alchemy:0%/0 wb_smith:67%/2 wb_enchant:0%/0 shrine:17%/2 weaponrack:0%/0 bath:8%/2 prison:0%/0 dummy:0%/0
clothier(4) bed:100%/2 bedroll:0%/0 seat:100%/4 throne:50%/1 table:100%/2 sidetable:75%/1 counter:25%/5 cooking:75%/3 fire:25%/1 shelf:100%/6 chest:100%/2 wardrobe:25%/4 dresser:50%/2 cupboard:75%/1 barrel:100%/6 crate:75%/3 sack:25%/6 basket:0%/0 urn:75%/4 wb_alchemy:0%/0 wb_smith:0%/0 wb_enchant:0%/0 shrine:0%/0 weaponrack:25%/6 bath:25%/1 prison:0%/0 dummy:0%/0
camp_tent(3) bed:0%/0 bedroll:0%/0 seat:67%/2 throne:0%/0 table:67%/1 sidetable:0%/0 counter:0%/0 cooking:0%/0 fire:0%/0 shelf:100%/2 chest:33%/2 wardrobe:0%/0 dresser:0%/0 cupboard:0%/0 barrel:100%/3 crate:100%/3 sack:0%/0 basket:0%/0 urn:0%/0 wb_alchemy:0%/0 wb_smith:0%/0 wb_enchant:0%/0 shrine:0%/0 weaponrack:0%/0 bath:0%/0 prison:0%/0 dummy:33%/1
fletcher(1) bed:100%/2 bedroll:0%/0 seat:100%/8 throne:0%/0 table:100%/5 sidetable:100%/7 counter:100%/5 cooking:100%/3 fire:100%/1 shelf:100%/15 chest:100%/2 wardrobe:100%/1 dresser:100%/4 cupboard:100%/2 barrel:100%/2 crate:100%/4 sack:100%/6 basket:0%/0 urn:0%/0 wb_alchemy:0%/0 wb_smith:0%/0 wb_enchant:0%/0 shrine:0%/0 weaponrack:0%/0 bath:0%/0 prison:0%/0 dummy:100%/1

### B2. beds per resident, seats per table, items
- dungeon: bed slots when any med 3.0 [p10 1.0, p90 9.0] n=126; residents(NPC refs) med 1.0 [p10 0.0, p90 10.0] n=314; beds-per-resident med 0.6 [p10 0.2, p90 2.0] n=110; seats within 170u of a table med 0.0 [p10 0.0, p90 1.0] n=1291; owned beds share 5/314
- house: bed slots when any med 2.0 [p10 1.0, p90 4.0] n=210; residents(NPC refs) med 1.0 [p10 0.0, p90 3.0] n=219; beds-per-resident med 1.0 [p10 1.0, p90 2.0] n=113; seats within 170u of a table med 1.0 [p10 0.0, p90 2.0] n=621; owned beds share 115/219
- hall_keep: bed slots when any med 4.0 [p10 2.0, p90 10.0] n=45; residents(NPC refs) med 2.0 [p10 0.0, p90 7.0] n=62; beds-per-resident med 1.3 [p10 0.7, p90 4.9] n=32; seats within 170u of a table med 1.0 [p10 0.0, p90 3.0] n=361; owned beds share 34/62
- inn: bed slots when any med 4.0 [p10 1.0, p90 5.1] n=50; residents(NPC refs) med 2.0 [p10 0.0, p90 6.0] n=59; beds-per-resident med 1.2 [p10 0.5, p90 3.0] n=42; seats within 170u of a table med 1.0 [p10 0.0, p90 2.0] n=369; owned beds share 40/59
- shop_general: bed slots when any med 2.0 [p10 1.0, p90 3.0] n=37; residents(NPC refs) med 1.0 [p10 0.0, p90 3.0] n=53; beds-per-resident med 1.0 [p10 0.8, p90 2.0] n=32; seats within 170u of a table med 1.0 [p10 0.0, p90 3.0] n=135; owned beds share 27/53
- other: bed slots when any med 3.0 [p10 1.0, p90 8.0] n=23; residents(NPC refs) med 1.0 [p10 0.0, p90 7.6] n=45; beds-per-resident med 1.0 [p10 0.7, p90 2.0] n=16; seats within 170u of a table med 1.0 [p10 0.0, p90 3.0] n=144; owned beds share 7/45
- mill_farm: bed slots when any med 2.0 [p10 1.0, p90 3.0] n=40; residents(NPC refs) med 2.0 [p10 0.0, p90 3.0] n=41; beds-per-resident med 1.0 [p10 1.0, p90 2.1] n=29; seats within 170u of a table med 1.0 [p10 0.0, p90 2.0] n=88; owned beds share 22/41
- bandit_camp: bed slots when any med 4.0 [p10 1.0, p90 8.0] n=27; residents(NPC refs) med 5.5 [p10 1.0, p90 18.0] n=32; beds-per-resident med 0.8 [p10 0.1, p90 2.3] n=27; seats within 170u of a table med 0.0 [p10 0.0, p90 2.0] n=235; owned beds share 1/32
- barracks: bed slots when any med 3.0 [p10 2.0, p90 8.6] n=28; residents(NPC refs) med 0.0 [p10 0.0, p90 3.0] n=30; beds-per-resident med 1.4 [p10 1.0, p90 4.0] n=12; seats within 170u of a table med 2.0 [p10 0.0, p90 3.0] n=117; owned beds share 19/30
- temple: bed slots when any med 2.0 [p10 1.0, p90 4.1] n=20; residents(NPC refs) med 1.0 [p10 0.0, p90 4.0] n=27; beds-per-resident med 1.0 [p10 0.6, p90 2.0] n=12; seats within 170u of a table med 1.0 [p10 0.0, p90 3.0] n=58; owned beds share 11/27
- guild: bed slots when any med 4.0 [p10 2.0, p90 16.4] n=20; residents(NPC refs) med 3.0 [p10 0.0, p90 9.6] n=25; beds-per-resident med 1.2 [p10 0.5, p90 2.2] n=17; seats within 170u of a table med 1.0 [p10 0.0, p90 2.0] n=185; owned beds share 19/25
- fort: bed slots when any med 6.0 [p10 3.0, p90 17.0] n=21; residents(NPC refs) med 0.0 [p10 0.0, p90 3.0] n=24; beds-per-resident med 3.0 [p10 1.5, p90 6.5] n=9; seats within 170u of a table med 1.0 [p10 0.0, p90 2.0] n=150; owned beds share 0/24
- mine: bed slots when any med 1.0 [p10 1.0, p90 1.9] n=8; residents(NPC refs) med 2.0 [p10 0.0, p90 5.0] n=21; beds-per-resident med 0.4 [p10 0.2, p90 1.0] n=8; seats within 170u of a table med 0.0 [p10 0.0, p90 1.6] n=45; owned beds share 5/21
- warehouse: bed slots when any med 2.0 [p10 2.0, p90 3.5] n=6; residents(NPC refs) med 0.0 [p10 0.0, p90 3.0] n=15; beds-per-resident med 1.0 [p10 0.8, p90 1.2] n=5; seats within 170u of a table med 1.0 [p10 0.0, p90 2.0] n=16; owned beds share 6/15
- alchemist: bed slots when any med 1.0 [p10 1.0, p90 2.8] n=13; residents(NPC refs) med 1.0 [p10 0.0, p90 2.0] n=15; beds-per-resident med 1.0 [p10 1.0, p90 1.5] n=11; seats within 170u of a table med 1.0 [p10 0.0, p90 2.0] n=39; owned beds share 10/15
- cellar: bed slots when any med 2.5 [p10 1.0, p90 4.0] n=4; residents(NPC refs) med 0.0 [p10 0.0, p90 5.1] n=14; beds-per-resident med 0.7 [p10 0.2, p90 3.3] n=3; seats within 170u of a table med 0.0 [p10 0.0, p90 2.0] n=34; owned beds share 2/14
- jail: bed slots when any med 3.5 [p10 1.1, p90 8.0] n=12; residents(NPC refs) med 0.5 [p10 0.0, p90 3.7] n=14; beds-per-resident med 2.0 [p10 0.3, p90 4.4] n=5; seats within 170u of a table med 1.0 [p10 0.0, p90 2.0] n=59; owned beds share 4/14
- ship: bed slots when any med 4.5 [p10 1.0, p90 9.0] n=12; residents(NPC refs) med 0.0 [p10 0.0, p90 0.0] n=12; beds-per-resident med 0.2 [p10 0.2, p90 0.2] n=1; seats within 170u of a table med 1.0 [p10 0.0, p90 2.0] n=58; owned beds share 5/12
- smith: bed slots when any med 2.0 [p10 1.0, p90 5.8] n=8; residents(NPC refs) med 1.0 [p10 0.0, p90 8.4] n=12; beds-per-resident med 1.0 [p10 1.0, p90 3.0] n=6; seats within 170u of a table med 1.0 [p10 0.0, p90 2.0] n=34; owned beds share 8/12
- clothier: bed slots when any med 1.5 [p10 1.0, p90 3.4] n=4; residents(NPC refs) med 1.0 [p10 1.0, p90 1.7] n=4; beds-per-resident med 1.5 [p10 1.0, p90 2.0] n=4; seats within 170u of a table med 1.5 [p10 0.0, p90 2.0] n=10; owned beds share 3/4
- camp_tent: bed slots when any n=0; residents(NPC refs) med 0.0 [p10 0.0, p90 0.0] n=3; beds-per-resident n=0; seats within 170u of a table med 2.0 [p10 1.2, p90 2.8] n=2; owned beds share 0/3
- fletcher: bed slots when any med 3.0 [p10 3.0, p90 3.0] n=1; residents(NPC refs) med 2.0 [p10 2.0, p90 2.0] n=1; beds-per-resident med 1.5 [p10 1.5, p90 1.5] n=1; seats within 170u of a table med 2.0 [p10 1.0, p90 3.0] n=5; owned beds share 1/1

## C. Where it stands (all furniture of the kind, pooled over cells of the group; edge-to-wall <=40u = against wall; corner = two non-parallel walls <=70u)
- dungeon/bed n=199: against wall 79%, corner 48%, wall dist med 8u; door dist med 3494.2 [p10 925.0, p90 6968.5] n=199; to fire med 1430.4 [p10 405.2, p90 3185.6] n=157; to light med 211.3 [p10 96.2, p90 453.8] n=199
- dungeon/table n=911: against wall 65%, corner 41%, wall dist med 15u; door dist med 2685.6 [p10 753.2, p90 6394.3] n=911; to fire med 1162.5 [p10 348.3, p90 3938.3] n=605; to light med 134.4 [p10 22.9, p90 446.3] n=905
- dungeon/seat n=1052: against wall 45%, corner 17%, wall dist med 53u; door dist med 2509.3 [p10 701.5, p90 6614.0] n=1052; to fire med 1031.2 [p10 285.1, p90 3710.9] n=676; to light med 184.0 [p10 62.4, p90 549.3] n=1052
- dungeon/counter n=298: against wall 63%, corner 33%, wall dist med 16u; door dist med 3065.0 [p10 796.9, p90 5444.3] n=298; to fire med 755.2 [p10 285.2, p90 2941.3] n=198; to light med 214.6 [p10 38.0, p90 489.0] n=298
- dungeon/shelf n=1540: against wall 81%, corner 54%, wall dist med 7u; door dist med 3074.2 [p10 751.4, p90 7578.8] n=1540; to fire med 1302.9 [p10 341.2, p90 4026.5] n=773; to light med 221.5 [p10 36.3, p90 625.0] n=1536
- dungeon/chest n=733: against wall 70%, corner 33%, wall dist med 20u; door dist med 3474.8 [p10 956.6, p90 8036.0] n=733; to fire med 1583.3 [p10 378.7, p90 6548.5] n=385; to light med 244.6 [p10 63.5, p90 746.5] n=730
- dungeon/cooking n=206: against wall 57%, corner 14%, wall dist med 26u; door dist med 3714.3 [p10 898.6, p90 7031.9] n=206; to fire med 0.0 [p10 0.0, p90 55.9] n=203; to light med 169.8 [p10 41.3, p90 577.7] n=206
- dungeon/fire n=411: against wall 67%, corner 45%, wall dist med 22u; door dist med 2876.4 [p10 784.6, p90 7360.8] n=411; to fire med 0.0 [p10 0.0, p90 0.0] n=411; to light med 97.7 [p10 8.6, p90 916.1] n=411
- dungeon/wb_alchemy n=51: against wall 73%, corner 31%, wall dist med 9u; door dist med 3721.3 [p10 578.3, p90 6962.2] n=51; to fire med 997.1 [p10 431.2, p90 4092.8] n=38; to light med 149.1 [p10 70.9, p90 386.5] n=51
- dungeon/wb_smith n=28: against wall 79%, corner 29%, wall dist med 11u; door dist med 2437.7 [p10 879.1, p90 5075.8] n=28; to fire med 807.2 [p10 343.5, p90 2433.5] n=28; to light med 208.5 [p10 128.8, p90 562.5] n=28
- dungeon/shrine n=951: against wall 76%, corner 50%, wall dist med 4u; door dist med 3578.5 [p10 1277.5, p90 8254.5] n=951; to fire med 1864.9 [p10 506.3, p90 6019.6] n=462; to light med 237.8 [p10 50.7, p90 661.7] n=951
- dungeon/weaponrack n=156: against wall 87%, corner 8%, wall dist med 10u; door dist med 2075.7 [p10 460.1, p90 4205.8] n=156; to fire med 1665.8 [p10 446.3, p90 3482.0] n=148; to light med 243.6 [p10 98.6, p90 483.1] n=156
- dungeon/barrel n=2256: against wall 57%, corner 26%, wall dist med 26u; door dist med 2430.3 [p10 444.7, p90 6336.6] n=2256; to fire med 1844.2 [p10 376.8, p90 4996.6] n=1723; to light med 278.0 [p10 75.8, p90 873.1] n=2256
- dungeon/sidetable n=72: against wall 75%, corner 25%, wall dist med 11u; door dist med 1841.1 [p10 415.6, p90 5354.8] n=72; to fire med 1093.7 [p10 345.3, p90 2645.6] n=59; to light med 91.6 [p10 11.6, p90 289.7] n=72
- dungeon/cupboard n=72: against wall 76%, corner 40%, wall dist med 7u; door dist med 1658.8 [p10 407.4, p90 4672.6] n=72; to fire med 898.5 [p10 220.2, p90 2564.4] n=65; to light med 178.6 [p10 31.0, p90 383.9] n=72
- dungeon/dresser n=66: against wall 80%, corner 42%, wall dist med 8u; door dist med 2626.2 [p10 565.0, p90 7228.2] n=66; to fire med 1428.6 [p10 540.2, p90 2675.1] n=52; to light med 160.1 [p10 36.9, p90 429.4] n=66
- dungeon/bed head end to wall: med 42.2 [p10 6.3, p90 150.7] n=194; head within 40u: 48%
- dungeon/seats within 160u of a table or fire: 494 of 1474; axis points at it (+-30deg either way) 72%; toward table 471 fire 23
- house/bed n=397: against wall 77%, corner 44%, wall dist med 9u; door dist med 689.0 [p10 286.5, p90 1594.3] n=394; to fire med 562.1 [p10 196.0, p90 1110.3] n=353; to light med 144.9 [p10 60.3, p90 319.5] n=396
- house/table n=587: against wall 66%, corner 37%, wall dist med 16u; door dist med 529.8 [p10 260.9, p90 1390.5] n=584; to fire med 398.4 [p10 130.3, p90 1019.0] n=519; to light med 55.0 [p10 7.3, p90 350.1] n=586
- house/seat n=817: against wall 48%, corner 18%, wall dist med 47u; door dist med 520.7 [p10 242.2, p90 1416.0] n=812; to fire med 424.8 [p10 160.0, p90 1002.6] n=749; to light med 116.3 [p10 55.2, p90 347.1] n=815
- house/counter n=135: against wall 56%, corner 39%, wall dist med 34u; door dist med 649.9 [p10 251.1, p90 2060.7] n=135; to fire med 754.5 [p10 261.1, p90 1751.3] n=123; to light med 136.8 [p10 21.1, p90 346.9] n=135
- house/shelf n=728: against wall 81%, corner 46%, wall dist med 7u; door dist med 683.4 [p10 263.9, p90 1800.5] n=723; to fire med 460.6 [p10 188.6, p90 1172.3] n=635; to light med 154.7 [p10 27.5, p90 389.7] n=727
- house/chest n=185: against wall 59%, corner 26%, wall dist med 21u; door dist med 529.1 [p10 273.3, p90 1316.3] n=185; to fire med 510.1 [p10 161.3, p90 1080.7] n=169; to light med 157.2 [p10 47.1, p90 373.7] n=185
- house/cooking n=595: against wall 54%, corner 24%, wall dist med 34u; door dist med 419.2 [p10 200.9, p90 960.0] n=584; to fire med 0.0 [p10 0.0, p90 67.4] n=595; to light med 105.1 [p10 36.4, p90 251.7] n=595
- house/fire n=231: against wall 87%, corner 73%, wall dist med 8u; door dist med 512.4 [p10 314.7, p90 2486.1] n=230; to fire med 0.0 [p10 0.0, p90 0.0] n=231; to light med 49.9 [p10 4.1, p90 129.4] n=230
- house/wb_alchemy n=16: against wall 88%, corner 62%, wall dist med 12u; door dist med 369.0 [p10 295.0, p90 1431.5] n=15; to fire med 330.2 [p10 74.3, p90 1291.0] n=15; to light med 122.6 [p10 20.6, p90 275.6] n=16
- house/wb_smith n=32: against wall 34%, corner 19%, wall dist med 1149u; door dist med 1744.9 [p10 388.9, p90 1824.3] n=32; to fire med 684.6 [p10 234.0, p90 1070.1] n=28; to light med 169.7 [p10 20.0, p90 322.5] n=32
- house/shrine n=13: against wall 62%, corner 23%, wall dist med 27u; door dist med 566.7 [p10 335.8, p90 3430.1] n=13; to fire med 763.7 [p10 157.5, p90 3585.1] n=12; to light med 39.3 [p10 24.1, p90 91.0] n=13
- house/weaponrack n=124: against wall 98%, corner 17%, wall dist med 8u; door dist med 961.6 [p10 329.6, p90 4971.4] n=124; to fire med 723.3 [p10 160.2, p90 1601.1] n=110; to light med 77.2 [p10 31.0, p90 197.5] n=124
- house/barrel n=897: against wall 79%, corner 30%, wall dist med 9u; door dist med 556.9 [p10 191.1, p90 1288.6] n=896; to fire med 574.9 [p10 224.2, p90 1097.3] n=778; to light med 194.9 [p10 60.3, p90 522.4] n=894
- house/sidetable n=210: against wall 83%, corner 38%, wall dist med 8u; door dist med 725.8 [p10 248.3, p90 1091.0] n=210; to fire med 581.8 [p10 188.5, p90 1077.0] n=202; to light med 92.9 [p10 11.1, p90 303.1] n=210
- house/cupboard n=182: against wall 79%, corner 52%, wall dist med 15u; door dist med 520.8 [p10 192.5, p90 1550.7] n=182; to fire med 423.7 [p10 203.5, p90 951.1] n=169; to light med 207.6 [p10 51.7, p90 453.1] n=182
- house/dresser n=182: against wall 76%, corner 40%, wall dist med 7u; door dist med 718.2 [p10 250.3, p90 1667.4] n=182; to fire med 620.0 [p10 335.8, p90 1199.1] n=172; to light med 62.2 [p10 6.3, p90 221.0] n=182
- house/bed head end to wall: med 43.1 [p10 4.5, p90 502.5] n=393; head within 40u: 48%
- house/seats within 160u of a table or fire: 620 of 896; axis points at it (+-30deg either way) 69%; toward table 580 fire 40
- hall_keep/bed n=161: against wall 85%, corner 49%, wall dist med 7u; door dist med 885.0 [p10 313.0, p90 2377.2] n=161; to fire med 693.5 [p10 209.0, p90 1737.7] n=131; to light med 140.5 [p10 50.6, p90 301.1] n=161
- hall_keep/table n=322: against wall 69%, corner 39%, wall dist med 17u; door dist med 819.0 [p10 326.5, p90 2315.8] n=322; to fire med 665.0 [p10 237.4, p90 1904.3] n=272; to light med 88.5 [p10 10.0, p90 301.2] n=320
- hall_keep/seat n=495: against wall 55%, corner 26%, wall dist med 31u; door dist med 770.3 [p10 340.8, p90 1858.1] n=495; to fire med 522.8 [p10 219.4, p90 1555.0] n=448; to light med 112.1 [p10 52.9, p90 272.4] n=495
- hall_keep/counter n=112: against wall 48%, corner 21%, wall dist med 44u; door dist med 802.0 [p10 350.3, p90 1663.6] n=112; to fire med 514.3 [p10 59.2, p90 3395.8] n=112; to light med 132.1 [p10 42.7, p90 323.7] n=112
- hall_keep/shelf n=620: against wall 76%, corner 44%, wall dist med 7u; door dist med 978.7 [p10 313.4, p90 1939.3] n=620; to fire med 617.4 [p10 204.9, p90 1914.5] n=562; to light med 160.5 [p10 44.6, p90 384.3] n=617
- hall_keep/chest n=162: against wall 61%, corner 30%, wall dist med 26u; door dist med 986.6 [p10 391.3, p90 1963.1] n=162; to fire med 815.0 [p10 349.3, p90 1619.2] n=151; to light med 151.3 [p10 37.1, p90 315.0] n=162
- hall_keep/cooking n=111: against wall 49%, corner 20%, wall dist med 41u; door dist med 637.8 [p10 272.6, p90 1163.8] n=111; to fire med 0.0 [p10 0.0, p90 47.2] n=109; to light med 59.2 [p10 12.4, p90 165.9] n=110
- hall_keep/fire n=100: against wall 71%, corner 50%, wall dist med 11u; door dist med 958.6 [p10 369.8, p90 2617.0] n=100; to fire med 0.0 [p10 0.0, p90 0.0] n=100; to light med 73.8 [p10 12.1, p90 335.0] n=100
- hall_keep/wb_alchemy n=13: against wall 100%, corner 54%, wall dist med 11u; door dist med 663.6 [p10 306.8, p90 2605.2] n=13; to fire med 835.5 [p10 201.8, p90 1606.5] n=10; to light med 69.9 [p10 26.0, p90 210.3] n=13
- hall_keep/wb_smith n=16: against wall 56%, corner 44%, wall dist med 23u; door dist med 727.2 [p10 168.2, p90 1422.5] n=16; to fire med 1046.5 [p10 407.2, p90 2036.4] n=16; to light med 129.0 [p10 102.5, p90 476.6] n=16
- hall_keep/shrine n=23: against wall 57%, corner 17%, wall dist med 37u; door dist med 858.1 [p10 216.7, p90 2102.8] n=23; to fire med 705.5 [p10 438.6, p90 2408.8] n=19; to light med 218.8 [p10 47.8, p90 737.1] n=23
- hall_keep/weaponrack n=406: against wall 57%, corner 7%, wall dist med 16u; door dist med 1142.2 [p10 580.9, p90 2424.9] n=406; to fire med 634.9 [p10 385.4, p90 1526.0] n=366; to light med 133.4 [p10 61.7, p90 270.4] n=406
- hall_keep/barrel n=482: against wall 84%, corner 37%, wall dist med 7u; door dist med 861.2 [p10 320.2, p90 1874.3] n=482; to fire med 700.5 [p10 297.9, p90 1952.5] n=376; to light med 157.2 [p10 48.7, p90 355.1] n=482
- hall_keep/sidetable n=151: against wall 83%, corner 44%, wall dist med 7u; door dist med 699.7 [p10 317.5, p90 2293.9] n=151; to fire med 555.3 [p10 201.1, p90 1076.9] n=137; to light med 91.7 [p10 4.3, p90 276.0] n=151
- hall_keep/cupboard n=97: against wall 78%, corner 44%, wall dist med 6u; door dist med 934.3 [p10 478.2, p90 1447.0] n=97; to fire med 662.1 [p10 248.5, p90 1354.8] n=89; to light med 147.7 [p10 47.5, p90 366.2] n=97
- hall_keep/dresser n=74: against wall 89%, corner 42%, wall dist med 4u; door dist med 934.6 [p10 415.0, p90 1648.9] n=74; to fire med 794.8 [p10 459.3, p90 1522.3] n=69; to light med 133.8 [p10 26.2, p90 325.7] n=74
- hall_keep/bed head end to wall: med 44.2 [p10 11.8, p90 194.1] n=161; head within 40u: 45%
- hall_keep/seats within 160u of a table or fire: 362 of 583; axis points at it (+-30deg either way) 60%; toward table 354 fire 8
- inn/bed n=155: against wall 96%, corner 75%, wall dist med 4u; door dist med 686.7 [p10 191.7, p90 1869.4] n=155; to fire med 604.3 [p10 210.6, p90 978.6] n=139; to light med 124.1 [p10 52.3, p90 260.4] n=155
- inn/table n=368: against wall 72%, corner 61%, wall dist med 8u; door dist med 754.7 [p10 235.4, p90 1447.2] n=368; to fire med 405.1 [p10 224.5, p90 981.8] n=327; to light med 47.4 [p10 13.0, p90 259.4] n=368
- inn/seat n=471: against wall 54%, corner 16%, wall dist med 34u; door dist med 566.7 [p10 191.8, p90 1450.4] n=471; to fire med 461.5 [p10 199.6, p90 1076.9] n=390; to light med 115.8 [p10 54.6, p90 357.3] n=471
- inn/counter n=256: against wall 33%, corner 12%, wall dist med 81u; door dist med 728.4 [p10 254.5, p90 1107.7] n=256; to fire med 565.2 [p10 226.0, p90 863.8] n=225; to light med 84.1 [p10 22.3, p90 283.6] n=256
- inn/shelf n=196: against wall 91%, corner 46%, wall dist med 5u; door dist med 501.1 [p10 226.2, p90 1607.0] n=196; to fire med 525.5 [p10 168.0, p90 1068.3] n=156; to light med 149.2 [p10 21.0, p90 326.1] n=196
- inn/chest n=94: against wall 45%, corner 10%, wall dist med 63u; door dist med 691.4 [p10 291.3, p90 1386.9] n=94; to fire med 718.2 [p10 270.5, p90 957.2] n=81; to light med 121.2 [p10 58.4, p90 363.7] n=94
- inn/cooking n=106: against wall 60%, corner 26%, wall dist med 28u; door dist med 487.7 [p10 251.7, p90 1360.2] n=106; to fire med 0.0 [p10 0.0, p90 73.9] n=106; to light med 74.7 [p10 12.1, p90 165.4] n=106
- inn/fire n=93: against wall 87%, corner 60%, wall dist med 6u; door dist med 491.4 [p10 275.3, p90 1376.1] n=93; to fire med 0.0 [p10 0.0, p90 0.0] n=93; to light med 48.8 [p10 4.1, p90 96.5] n=93
- inn/shrine n=25: against wall 20%, corner 12%, wall dist med 73u; door dist med 1403.2 [p10 523.6, p90 2229.0] n=25; to fire med 539.5 [p10 190.2, p90 1198.5] n=21; to light med 94.1 [p10 35.5, p90 282.9] n=25
- inn/weaponrack n=42: against wall 88%, corner 12%, wall dist med 7u; door dist med 398.3 [p10 210.9, p90 1016.2] n=42; to fire med 391.2 [p10 1.8, p90 815.4] n=42; to light med 78.0 [p10 3.0, p90 182.6] n=42
- inn/barrel n=684: against wall 83%, corner 41%, wall dist med 7u; door dist med 940.3 [p10 278.5, p90 2028.7] n=684; to fire med 732.3 [p10 314.2, p90 1219.5] n=607; to light med 207.0 [p10 56.0, p90 390.9] n=684
- inn/sidetable n=52: against wall 88%, corner 44%, wall dist med 6u; door dist med 1056.4 [p10 221.9, p90 1763.8] n=52; to fire med 591.2 [p10 218.8, p90 955.6] n=42; to light med 20.1 [p10 6.7, p90 229.9] n=52
- inn/cupboard n=42: against wall 95%, corner 62%, wall dist med 5u; door dist med 657.4 [p10 196.3, p90 1444.5] n=42; to fire med 641.1 [p10 209.3, p90 1205.9] n=36; to light med 206.6 [p10 47.9, p90 450.6] n=42
- inn/dresser n=48: against wall 94%, corner 58%, wall dist med 11u; door dist med 876.7 [p10 229.8, p90 1560.8] n=48; to fire med 779.1 [p10 338.9, p90 970.8] n=41; to light med 93.1 [p10 32.0, p90 218.3] n=48
- inn/bed head end to wall: med 16.5 [p10 2.3, p90 85.0] n=155; head within 40u: 74%
- inn/seats within 160u of a table or fire: 383 of 466; axis points at it (+-30deg either way) 68%; toward table 375 fire 8
- shop_general/bed n=54: against wall 83%, corner 54%, wall dist med 6u; door dist med 499.8 [p10 213.5, p90 1137.6] n=54; to fire med 375.5 [p10 152.0, p90 938.7] n=43; to light med 122.4 [p10 56.5, p90 284.8] n=54
- shop_general/table n=135: against wall 62%, corner 42%, wall dist med 14u; door dist med 576.1 [p10 259.5, p90 1400.8] n=135; to fire med 490.6 [p10 119.2, p90 1199.2] n=101; to light med 59.4 [p10 12.9, p90 243.4] n=135
- shop_general/seat n=189: against wall 46%, corner 14%, wall dist med 49u; door dist med 548.7 [p10 263.4, p90 1307.3] n=189; to fire med 591.8 [p10 171.1, p90 1341.4] n=135; to light med 93.3 [p10 57.5, p90 280.0] n=189
- shop_general/counter n=167: against wall 32%, corner 19%, wall dist med 97u; door dist med 499.2 [p10 273.2, p90 1221.2] n=167; to fire med 510.0 [p10 149.6, p90 1745.7] n=115; to light med 65.8 [p10 20.4, p90 168.5] n=167
- shop_general/shelf n=197: against wall 80%, corner 39%, wall dist med 8u; door dist med 544.6 [p10 186.7, p90 1226.2] n=197; to fire med 499.3 [p10 195.9, p90 1182.9] n=136; to light med 145.3 [p10 36.1, p90 298.2] n=197
- shop_general/chest n=105: against wall 40%, corner 15%, wall dist med 87u; door dist med 465.1 [p10 181.1, p90 1314.3] n=105; to fire med 525.2 [p10 228.5, p90 1272.3] n=77; to light med 130.0 [p10 43.8, p90 518.8] n=105
- shop_general/cooking n=58: against wall 57%, corner 28%, wall dist med 34u; door dist med 394.1 [p10 215.7, p90 1013.9] n=58; to fire med 0.0 [p10 0.0, p90 46.8] n=58; to light med 88.2 [p10 18.4, p90 205.2] n=58
- shop_general/fire n=33: against wall 85%, corner 73%, wall dist med 9u; door dist med 506.8 [p10 250.0, p90 1098.0] n=33; to fire med 0.0 [p10 0.0, p90 0.0] n=33; to light med 55.5 [p10 5.9, p90 217.0] n=33
- shop_general/wb_smith n=22: against wall 82%, corner 23%, wall dist med 8u; door dist med 616.8 [p10 318.2, p90 1926.3] n=22; to fire med 351.4 [p10 105.7, p90 1970.6] n=18; to light med 177.0 [p10 80.2, p90 322.8] n=22
- shop_general/weaponrack n=47: against wall 72%, corner 17%, wall dist med 5u; door dist med 388.1 [p10 171.6, p90 1985.4] n=47; to fire med 556.3 [p10 277.2, p90 2205.4] n=47; to light med 216.5 [p10 140.7, p90 321.6] n=47
- shop_general/barrel n=743: against wall 68%, corner 24%, wall dist med 12u; door dist med 679.8 [p10 297.8, p90 1347.3] n=743; to fire med 586.8 [p10 234.7, p90 2069.8] n=202; to light med 242.0 [p10 61.7, p90 487.3] n=737
- shop_general/sidetable n=31: against wall 77%, corner 29%, wall dist med 12u; door dist med 534.8 [p10 193.8, p90 1058.0] n=31; to fire med 621.3 [p10 135.5, p90 1284.8] n=22; to light med 104.6 [p10 9.3, p90 262.6] n=31
- shop_general/cupboard n=35: against wall 83%, corner 51%, wall dist med 8u; door dist med 542.0 [p10 320.2, p90 1277.0] n=35; to fire med 537.9 [p10 253.9, p90 1408.0] n=23; to light med 155.3 [p10 84.3, p90 357.2] n=34
- shop_general/dresser n=32: against wall 88%, corner 28%, wall dist med 13u; door dist med 487.5 [p10 215.9, p90 1431.8] n=32; to fire med 433.3 [p10 245.2, p90 1255.9] n=27; to light med 101.7 [p10 22.5, p90 232.1] n=32
- shop_general/bed head end to wall: med 26.9 [p10 3.8, p90 104.6] n=53; head within 40u: 70%
- shop_general/seats within 160u of a table or fire: 146 of 186; axis points at it (+-30deg either way) 66%; toward table 142 fire 4
- other/bed n=40: against wall 98%, corner 52%, wall dist med 6u; door dist med 918.9 [p10 350.3, p90 4139.1] n=40; to fire med 804.7 [p10 298.9, p90 3339.5] n=23; to light med 249.2 [p10 97.4, p90 407.2] n=40
- other/table n=136: against wall 63%, corner 28%, wall dist med 16u; door dist med 1165.2 [p10 315.9, p90 3747.6] n=136; to fire med 837.3 [p10 108.8, p90 3388.0] n=105; to light med 111.4 [p10 13.3, p90 569.6] n=136
- other/seat n=240: against wall 44%, corner 14%, wall dist med 46u; door dist med 1048.6 [p10 334.5, p90 4114.0] n=240; to fire med 898.3 [p10 228.4, p90 3304.7] n=174; to light med 143.5 [p10 65.6, p90 379.6] n=240
- other/counter n=30: against wall 30%, corner 10%, wall dist med 98u; door dist med 527.5 [p10 279.4, p90 2677.0] n=30; to fire med 657.0 [p10 413.9, p90 1241.3] n=19; to light med 52.7 [p10 22.1, p90 246.0] n=30
- other/shelf n=125: against wall 93%, corner 50%, wall dist med 4u; door dist med 1140.4 [p10 307.8, p90 3218.4] n=125; to fire med 1222.9 [p10 346.1, p90 8052.6] n=90; to light med 187.3 [p10 50.7, p90 545.3] n=125
- other/chest n=59: against wall 51%, corner 25%, wall dist med 38u; door dist med 1991.9 [p10 388.9, p90 8450.5] n=59; to fire med 623.5 [p10 231.7, p90 2824.0] n=33; to light med 308.7 [p10 76.1, p90 2048.2] n=54
- other/cooking n=19: against wall 63%, corner 16%, wall dist med 17u; door dist med 1601.2 [p10 342.2, p90 1996.9] n=19; to fire med 0.0 [p10 0.0, p90 317.2] n=19; to light med 134.6 [p10 70.2, p90 342.4] n=19
- other/fire n=38: against wall 61%, corner 45%, wall dist med 23u; door dist med 897.8 [p10 291.8, p90 2956.9] n=38; to fire med 0.0 [p10 0.0, p90 0.0] n=38; to light med 34.4 [p10 4.6, p90 166.1] n=38
- other/wb_smith n=10: against wall 90%, corner 30%, wall dist med 13u; door dist med 2063.6 [p10 1260.9, p90 2912.5] n=10; to fire med 1025.7 [p10 114.7, p90 1624.6] n=7; to light med 230.8 [p10 105.6, p90 399.8] n=10
- other/shrine n=598: against wall 92%, corner 90%, wall dist med 0u; door dist med 1476.5 [p10 648.3, p90 5919.0] n=37; to fire med 4989.4 [p10 478.6, p90 11629.5] n=23; to light med 470.7 [p10 117.6, p90 1129.0] n=598
- other/weaponrack n=14: against wall 100%, corner 21%, wall dist med 15u; door dist med 1651.5 [p10 989.6, p90 1704.0] n=14; to fire med 1294.3 [p10 944.0, p90 1350.3] n=14; to light med 419.5 [p10 150.6, p90 463.7] n=14
- other/barrel n=323: against wall 88%, corner 37%, wall dist med 10u; door dist med 1286.3 [p10 331.5, p90 3212.5] n=323; to fire med 1521.8 [p10 531.4, p90 3635.2] n=269; to light med 314.2 [p10 86.5, p90 990.8] n=323
- other/sidetable n=38: against wall 89%, corner 42%, wall dist med 5u; door dist med 571.3 [p10 347.7, p90 1564.0] n=38; to fire med 700.4 [p10 264.1, p90 2017.6] n=29; to light med 136.3 [p10 5.0, p90 2931.9] n=38
- other/cupboard n=13: against wall 92%, corner 62%, wall dist med 6u; door dist med 706.1 [p10 257.6, p90 1848.7] n=13; to fire med 804.1 [p10 354.6, p90 1813.4] n=6; to light med 208.0 [p10 30.8, p90 599.3] n=13
- other/dresser n=24: against wall 92%, corner 50%, wall dist med 8u; door dist med 895.0 [p10 262.5, p90 2080.6] n=24; to fire med 778.8 [p10 427.3, p90 2849.0] n=15; to light med 109.2 [p10 9.6, p90 1610.0] n=24
- other/bed head end to wall: med 21.7 [p10 2.3, p90 80.0] n=40; head within 40u: 68%
- other/seats within 160u of a table or fire: 142 of 249; axis points at it (+-30deg either way) 62%; toward table 137 fire 5
- mill_farm/bed n=62: against wall 81%, corner 47%, wall dist med 11u; door dist med 487.2 [p10 291.1, p90 856.6] n=62; to fire med 412.6 [p10 201.4, p90 968.1] n=51; to light med 143.1 [p10 46.4, p90 278.2] n=61
- mill_farm/table n=85: against wall 74%, corner 35%, wall dist med 9u; door dist med 463.5 [p10 237.0, p90 862.5] n=85; to fire med 357.6 [p10 129.9, p90 739.1] n=73; to light med 40.8 [p10 4.5, p90 271.0] n=84
- mill_farm/seat n=111: against wall 60%, corner 14%, wall dist med 33u; door dist med 438.6 [p10 207.6, p90 1000.9] n=111; to fire med 392.6 [p10 114.5, p90 775.0] n=99; to light med 122.5 [p10 54.9, p90 267.4] n=111
- mill_farm/shelf n=85: against wall 88%, corner 46%, wall dist med 5u; door dist med 486.3 [p10 229.9, p90 1032.7] n=85; to fire med 438.9 [p10 195.1, p90 805.6] n=76; to light med 168.8 [p10 34.8, p90 323.8] n=82
- mill_farm/chest n=28: against wall 54%, corner 7%, wall dist med 24u; door dist med 506.8 [p10 295.0, p90 806.7] n=28; to fire med 390.9 [p10 168.6, p90 761.0] n=24; to light med 103.6 [p10 35.2, p90 190.8] n=28
- mill_farm/cooking n=90: against wall 59%, corner 30%, wall dist med 34u; door dist med 411.8 [p10 257.8, p90 768.6] n=90; to fire med 0.0 [p10 0.0, p90 76.5] n=89; to light med 124.5 [p10 52.7, p90 310.0] n=90
- mill_farm/fire n=39: against wall 92%, corner 77%, wall dist med 8u; door dist med 512.2 [p10 255.2, p90 1204.4] n=39; to fire med 0.0 [p10 0.0, p90 0.0] n=39; to light med 20.3 [p10 4.0, p90 137.2] n=36
- mill_farm/barrel n=176: against wall 77%, corner 28%, wall dist med 10u; door dist med 518.3 [p10 195.2, p90 1115.8] n=176; to fire med 461.4 [p10 258.8, p90 769.4] n=152; to light med 158.1 [p10 54.0, p90 434.0] n=173
- mill_farm/sidetable n=24: against wall 92%, corner 21%, wall dist med 19u; door dist med 642.7 [p10 356.1, p90 906.9] n=24; to fire med 429.8 [p10 308.5, p90 968.9] n=24; to light med 59.3 [p10 11.5, p90 123.5] n=24
- mill_farm/cupboard n=31: against wall 81%, corner 39%, wall dist med 9u; door dist med 519.5 [p10 235.0, p90 915.8] n=31; to fire med 342.2 [p10 218.3, p90 786.0] n=29; to light med 174.9 [p10 39.0, p90 240.7] n=31
- mill_farm/dresser n=21: against wall 86%, corner 38%, wall dist med 7u; door dist med 398.1 [p10 216.2, p90 859.8] n=21; to fire med 408.6 [p10 215.7, p90 823.4] n=18; to light med 95.6 [p10 21.1, p90 219.6] n=21
- mill_farm/bed head end to wall: med 29.8 [p10 1.6, p90 182.0] n=62; head within 40u: 52%
- mill_farm/seats within 160u of a table or fire: 94 of 120; axis points at it (+-30deg either way) 67%; toward table 82 fire 12
- bandit_camp/bed n=49: against wall 98%, corner 61%, wall dist med 5u; door dist med 1450.3 [p10 440.3, p90 5276.2] n=49; to fire med 1023.3 [p10 602.3, p90 2739.6] n=42; to light med 213.0 [p10 120.0, p90 422.5] n=49
- bandit_camp/table n=213: against wall 69%, corner 41%, wall dist med 13u; door dist med 2472.4 [p10 635.3, p90 5942.9] n=213; to fire med 1435.6 [p10 340.0, p90 4429.0] n=184; to light med 151.0 [p10 25.1, p90 425.9] n=213
- bandit_camp/seat n=197: against wall 38%, corner 13%, wall dist med 61u; door dist med 2534.6 [p10 602.0, p90 4992.9] n=197; to fire med 1580.7 [p10 479.8, p90 6038.8] n=180; to light med 179.3 [p10 78.3, p90 409.8] n=197
- bandit_camp/counter n=28: against wall 46%, corner 11%, wall dist med 60u; door dist med 3570.2 [p10 501.7, p90 4638.4] n=28; to fire med 5702.6 [p10 515.5, p90 5893.0] n=28; to light med 186.5 [p10 72.3, p90 425.2] n=28
- bandit_camp/shelf n=155: against wall 84%, corner 50%, wall dist med 7u; door dist med 2009.3 [p10 423.0, p90 5031.4] n=155; to fire med 1504.4 [p10 293.2, p90 3769.1] n=126; to light med 203.8 [p10 42.9, p90 446.7] n=155
- bandit_camp/chest n=77: against wall 58%, corner 39%, wall dist med 24u; door dist med 2176.4 [p10 552.9, p90 4882.2] n=77; to fire med 1315.5 [p10 173.7, p90 3954.3] n=60; to light med 195.9 [p10 64.0, p90 349.3] n=77
- bandit_camp/cooking n=32: against wall 56%, corner 25%, wall dist med 35u; door dist med 2601.7 [p10 669.6, p90 4432.0] n=32; to fire med 0.0 [p10 0.0, p90 537.1] n=32; to light med 113.7 [p10 27.5, p90 461.4] n=32
- bandit_camp/fire n=67: against wall 81%, corner 58%, wall dist med 14u; door dist med 1809.5 [p10 579.5, p90 5029.9] n=67; to fire med 0.0 [p10 0.0, p90 0.0] n=67; to light med 93.6 [p10 10.0, p90 394.6] n=67
- bandit_camp/wb_smith n=21: against wall 71%, corner 48%, wall dist med 11u; door dist med 2582.5 [p10 822.7, p90 8392.4] n=21; to fire med 479.1 [p10 373.6, p90 4479.9] n=14; to light med 184.6 [p10 69.6, p90 287.8] n=21
- bandit_camp/shrine n=11: against wall 55%, corner 45%, wall dist med 33u; door dist med 1665.3 [p10 843.8, p90 5103.1] n=11; to fire med 1934.4 [p10 632.4, p90 2615.3] n=7; to light med 34.9 [p10 22.3, p90 573.5] n=11
- bandit_camp/weaponrack n=58: against wall 97%, corner 9%, wall dist med 16u; door dist med 2063.0 [p10 679.1, p90 4561.9] n=58; to fire med 1750.2 [p10 447.4, p90 4307.0] n=42; to light med 249.3 [p10 70.3, p90 335.9] n=58
- bandit_camp/barrel n=553: against wall 70%, corner 28%, wall dist med 17u; door dist med 2043.5 [p10 403.3, p90 4696.0] n=553; to fire med 1558.3 [p10 396.1, p90 3907.8] n=443; to light med 218.8 [p10 61.4, p90 422.1] n=553
- bandit_camp/cupboard n=22: against wall 95%, corner 32%, wall dist med 4u; door dist med 1345.6 [p10 406.5, p90 3506.2] n=22; to fire med 874.4 [p10 416.1, p90 2804.6] n=21; to light med 197.7 [p10 35.3, p90 312.5] n=22
- bandit_camp/dresser n=17: against wall 65%, corner 29%, wall dist med 5u; door dist med 2254.5 [p10 418.9, p90 5063.4] n=17; to fire med 1423.8 [p10 811.1, p90 2608.7] n=16; to light med 189.4 [p10 50.5, p90 718.9] n=17
- bandit_camp/bed head end to wall: med 31.2 [p10 5.4, p90 60.4] n=49; head within 40u: 65%
- bandit_camp/seats within 160u of a table or fire: 132 of 217; axis points at it (+-30deg either way) 80%; toward table 132 fire 0
- barracks/bed n=101: against wall 96%, corner 70%, wall dist med 6u; door dist med 424.0 [p10 193.9, p90 864.6] n=101; to fire med 477.0 [p10 162.2, p90 888.9] n=75; to light med 156.9 [p10 75.6, p90 298.3] n=101
- barracks/table n=89: against wall 75%, corner 42%, wall dist med 8u; door dist med 501.1 [p10 224.7, p90 1991.8] n=89; to fire med 385.3 [p10 190.3, p90 766.1] n=59; to light med 70.1 [p10 11.4, p90 291.7] n=89
- barracks/seat n=160: against wall 57%, corner 22%, wall dist med 29u; door dist med 502.3 [p10 218.9, p90 2723.4] n=160; to fire med 345.2 [p10 179.5, p90 833.5] n=83; to light med 121.6 [p10 59.8, p90 310.7] n=160
- barracks/counter n=45: against wall 69%, corner 53%, wall dist med 23u; door dist med 2068.4 [p10 268.0, p90 3020.4] n=45; to fire med 1978.9 [p10 430.8, p90 2244.2] n=15; to light med 232.7 [p10 15.6, p90 414.5] n=45
- barracks/shelf n=138: against wall 94%, corner 46%, wall dist med 4u; door dist med 787.6 [p10 268.7, p90 3233.5] n=138; to fire med 433.5 [p10 212.4, p90 2515.7] n=90; to light med 209.7 [p10 41.1, p90 351.1] n=138
- barracks/chest n=42: against wall 69%, corner 31%, wall dist med 15u; door dist med 422.5 [p10 206.2, p90 1277.0] n=42; to fire med 577.7 [p10 244.1, p90 1214.1] n=23; to light med 178.7 [p10 50.6, p90 295.8] n=42
- barracks/cooking n=41: against wall 63%, corner 41%, wall dist med 36u; door dist med 491.7 [p10 250.0, p90 710.1] n=41; to fire med 0.0 [p10 0.0, p90 47.2] n=40; to light med 98.1 [p10 19.6, p90 165.9] n=41
- barracks/fire n=25: against wall 88%, corner 56%, wall dist med 9u; door dist med 549.5 [p10 273.4, p90 691.0] n=25; to fire med 0.0 [p10 0.0, p90 0.0] n=25; to light med 15.5 [p10 1.6, p90 102.1] n=25
- barracks/wb_smith n=9: against wall 100%, corner 33%, wall dist med 5u; door dist med 359.4 [p10 212.1, p90 498.3] n=9; to fire med 438.3 [p10 193.9, p90 858.7] n=9; to light med 198.1 [p10 50.0, p90 264.1] n=9
- barracks/shrine n=9: against wall 67%, corner 11%, wall dist med 8u; door dist med 721.4 [p10 359.9, p90 3072.9] n=9; to fire med 445.1 [p10 390.1, p90 1891.2] n=7; to light med 78.9 [p10 10.2, p90 181.4] n=9
- barracks/weaponrack n=37: against wall 70%, corner 0%, wall dist med 14u; door dist med 308.7 [p10 201.3, p90 954.8] n=37; to fire med 1206.5 [p10 598.0, p90 1222.2] n=25; to light med 180.8 [p10 79.5, p90 235.9] n=37
- barracks/barrel n=147: against wall 83%, corner 42%, wall dist med 5u; door dist med 548.2 [p10 202.0, p90 2073.7] n=147; to fire med 436.1 [p10 131.1, p90 813.0] n=98; to light med 146.9 [p10 44.9, p90 289.0] n=147
- barracks/sidetable n=40: against wall 88%, corner 40%, wall dist med 5u; door dist med 641.0 [p10 195.5, p90 969.5] n=40; to fire med 476.2 [p10 295.4, p90 930.1] n=29; to light med 124.6 [p10 13.2, p90 284.1] n=40
- barracks/cupboard n=19: against wall 79%, corner 68%, wall dist med 6u; door dist med 620.4 [p10 339.0, p90 1228.7] n=19; to fire med 471.5 [p10 129.8, p90 908.2] n=11; to light med 150.8 [p10 24.2, p90 389.7] n=19
- barracks/dresser n=20: against wall 75%, corner 30%, wall dist med 10u; door dist med 784.5 [p10 261.3, p90 3066.7] n=20; to fire med 504.9 [p10 367.9, p90 999.0] n=10; to light med 154.7 [p10 86.7, p90 329.2] n=20
- barracks/bed head end to wall: med 18.6 [p10 2.6, p90 74.5] n=101; head within 40u: 75%
- barracks/seats within 160u of a table or fire: 149 of 212; axis points at it (+-30deg either way) 77%; toward table 143 fire 6
- temple/bed n=44: against wall 82%, corner 25%, wall dist med 13u; door dist med 1098.3 [p10 437.9, p90 3185.6] n=44; to fire med 466.2 [p10 378.8, p90 1347.0] n=34; to light med 221.7 [p10 66.0, p90 391.2] n=44
- temple/table n=58: against wall 66%, corner 36%, wall dist med 18u; door dist med 945.2 [p10 216.9, p90 2347.5] n=58; to fire med 656.1 [p10 258.7, p90 1589.1] n=42; to light med 96.2 [p10 9.9, p90 362.9] n=58
- temple/seat n=164: against wall 50%, corner 20%, wall dist med 41u; door dist med 895.7 [p10 235.0, p90 2166.7] n=164; to fire med 642.5 [p10 353.9, p90 1493.7] n=113; to light med 176.0 [p10 59.4, p90 443.1] n=164
- temple/counter n=15: against wall 80%, corner 87%, wall dist med 18u; door dist med 1046.8 [p10 490.0, p90 1481.1] n=15; to fire n=0; to light med 112.3 [p10 35.9, p90 279.0] n=15
- temple/shelf n=86: against wall 66%, corner 35%, wall dist med 11u; door dist med 822.3 [p10 329.2, p90 2097.7] n=86; to fire med 523.1 [p10 155.5, p90 1346.4] n=71; to light med 118.4 [p10 19.8, p90 333.6] n=86
- temple/chest n=27: against wall 37%, corner 19%, wall dist med 165u; door dist med 1495.6 [p10 581.1, p90 3513.9] n=27; to fire med 819.5 [p10 414.9, p90 1491.1] n=17; to light med 221.8 [p10 27.9, p90 572.2] n=27
- temple/cooking n=17: against wall 82%, corner 41%, wall dist med 6u; door dist med 775.2 [p10 634.2, p90 1490.2] n=17; to fire med 0.0 [p10 0.0, p90 47.2] n=16; to light med 64.1 [p10 60.6, p90 168.4] n=17
- temple/fire n=16: against wall 44%, corner 44%, wall dist med 266u; door dist med 1046.4 [p10 618.7, p90 2402.1] n=16; to fire med 0.0 [p10 0.0, p90 0.0] n=16; to light med 73.2 [p10 6.2, p90 168.3] n=16
- temple/shrine n=116: against wall 67%, corner 32%, wall dist med 9u; door dist med 1399.6 [p10 489.7, p90 1774.1] n=116; to fire med 1362.3 [p10 272.4, p90 1658.5] n=77; to light med 63.8 [p10 25.5, p90 272.8] n=116
- temple/weaponrack n=16: against wall 0%, corner 0%, wall dist med 1823u; door dist med 3693.2 [p10 3668.7, p90 3719.5] n=16; to fire med 4079.6 [p10 4043.0, p90 4117.7] n=16; to light med 178.9 [p10 104.2, p90 260.3] n=16
- temple/barrel n=114: against wall 79%, corner 39%, wall dist med 7u; door dist med 581.6 [p10 196.8, p90 1259.6] n=114; to fire med 1002.4 [p10 430.8, p90 1526.2] n=102; to light med 142.0 [p10 51.7, p90 344.5] n=114
- temple/sidetable n=29: against wall 72%, corner 28%, wall dist med 14u; door dist med 997.2 [p10 280.4, p90 2194.6] n=29; to fire med 803.1 [p10 406.4, p90 1517.1] n=21; to light med 64.5 [p10 1.5, p90 210.9] n=29
- temple/cupboard n=14: against wall 79%, corner 50%, wall dist med 7u; door dist med 708.0 [p10 430.8, p90 1556.9] n=14; to fire med 639.4 [p10 390.7, p90 1316.6] n=13; to light med 141.2 [p10 28.9, p90 356.2] n=14
- temple/dresser n=15: against wall 87%, corner 40%, wall dist med 11u; door dist med 1234.3 [p10 336.8, p90 2003.7] n=15; to fire med 1093.1 [p10 449.5, p90 1796.3] n=13; to light med 61.2 [p10 21.7, p90 157.8] n=15
- temple/bed head end to wall: med 52.9 [p10 9.7, p90 86.1] n=38; head within 40u: 26%
- temple/seats within 160u of a table or fire: 72 of 160; axis points at it (+-30deg either way) 75%; toward table 69 fire 3
- guild/bed n=100: against wall 73%, corner 38%, wall dist med 7u; door dist med 1205.1 [p10 594.4, p90 2395.3] n=100; to fire med 1006.3 [p10 490.1, p90 2035.2] n=49; to light med 172.1 [p10 23.4, p90 438.6] n=100
- guild/table n=167: against wall 68%, corner 40%, wall dist med 17u; door dist med 1020.6 [p10 318.5, p90 2324.9] n=167; to fire med 1125.4 [p10 312.0, p90 2303.4] n=93; to light med 95.1 [p10 18.8, p90 314.2] n=167
- guild/seat n=319: against wall 72%, corner 50%, wall dist med 13u; door dist med 896.2 [p10 376.7, p90 2047.7] n=319; to fire med 1003.7 [p10 299.0, p90 1749.5] n=123; to light med 134.0 [p10 66.4, p90 321.3] n=319
- guild/counter n=15: against wall 7%, corner 0%, wall dist med 174u; door dist med 1503.8 [p10 445.2, p90 2005.9] n=15; to fire med 2148.1 [p10 2089.8, p90 2518.7] n=6; to light med 55.2 [p10 12.1, p90 128.2] n=15
- guild/shelf n=299: against wall 84%, corner 45%, wall dist med 5u; door dist med 999.3 [p10 356.4, p90 2073.0] n=299; to fire med 1194.8 [p10 395.0, p90 2116.3] n=131; to light med 155.3 [p10 26.9, p90 362.9] n=299
- guild/chest n=74: against wall 57%, corner 41%, wall dist med 20u; door dist med 1008.5 [p10 445.5, p90 3985.2] n=74; to fire med 1268.6 [p10 547.5, p90 3697.7] n=32; to light med 177.8 [p10 69.4, p90 370.2] n=74
- guild/cooking n=11: against wall 45%, corner 0%, wall dist med 65u; door dist med 706.3 [p10 638.8, p90 4641.8] n=11; to fire med 0.0 [p10 0.0, p90 380.5] n=8; to light med 150.7 [p10 53.7, p90 488.8] n=11
- guild/fire n=58: against wall 67%, corner 43%, wall dist med 16u; door dist med 945.6 [p10 360.3, p90 7713.5] n=58; to fire med 0.0 [p10 0.0, p90 0.0] n=58; to light med 275.2 [p10 32.9, p90 5980.8] n=58
- guild/wb_alchemy n=8: against wall 62%, corner 12%, wall dist med 4u; door dist med 1078.8 [p10 627.3, p90 3521.9] n=8; to fire med 1369.7 [p10 720.1, p90 2067.7] n=4; to light med 119.0 [p10 22.0, p90 376.4] n=8
- guild/shrine n=16: against wall 62%, corner 19%, wall dist med 26u; door dist med 933.0 [p10 400.3, p90 1899.0] n=16; to fire med 1457.2 [p10 243.1, p90 2336.2] n=15; to light med 272.9 [p10 80.2, p90 825.8] n=16
- guild/weaponrack n=99: against wall 71%, corner 8%, wall dist med 8u; door dist med 1801.5 [p10 417.9, p90 2598.7] n=99; to fire med 1521.5 [p10 656.9, p90 2308.5] n=99; to light med 266.3 [p10 119.6, p90 493.3] n=99
- guild/barrel n=338: against wall 71%, corner 36%, wall dist med 13u; door dist med 915.6 [p10 329.5, p90 2456.5] n=338; to fire med 1190.7 [p10 613.3, p90 3193.0] n=151; to light med 160.0 [p10 70.3, p90 322.6] n=338
- guild/sidetable n=151: against wall 83%, corner 36%, wall dist med 9u; door dist med 909.5 [p10 465.0, p90 2150.9] n=151; to fire med 999.2 [p10 277.4, p90 1446.2] n=68; to light med 129.9 [p10 4.2, p90 287.3] n=151
- guild/cupboard n=76: against wall 63%, corner 36%, wall dist med 23u; door dist med 835.9 [p10 308.8, p90 2064.6] n=76; to fire med 1376.2 [p10 313.9, p90 1963.8] n=42; to light med 131.9 [p10 22.1, p90 284.0] n=76
- guild/dresser n=62: against wall 92%, corner 71%, wall dist med 3u; door dist med 1043.3 [p10 381.0, p90 2071.1] n=62; to fire med 765.9 [p10 318.6, p90 1553.0] n=19; to light med 149.4 [p10 17.0, p90 274.8] n=62
- guild/bed head end to wall: med 76.9 [p10 22.6, p90 674.2] n=100; head within 40u: 22%
- guild/seats within 160u of a table or fire: 160 of 339; axis points at it (+-30deg either way) 55%; toward table 152 fire 8
- fort/bed n=107: against wall 89%, corner 56%, wall dist med 6u; door dist med 828.1 [p10 410.5, p90 1502.6] n=107; to fire med 834.8 [p10 310.6, p90 1433.6] n=102; to light med 222.9 [p10 96.3, p90 441.4] n=107
- fort/table n=150: against wall 55%, corner 34%, wall dist med 21u; door dist med 831.6 [p10 358.6, p90 1499.0] n=150; to fire med 748.5 [p10 224.0, p90 1647.3] n=132; to light med 120.3 [p10 16.4, p90 381.8] n=150
- fort/seat n=228: against wall 39%, corner 10%, wall dist med 82u; door dist med 746.4 [p10 306.9, p90 1657.9] n=228; to fire med 676.7 [p10 224.5, p90 1630.0] n=209; to light med 132.8 [p10 49.2, p90 345.3] n=228
- fort/counter n=81: against wall 47%, corner 16%, wall dist med 49u; door dist med 600.2 [p10 200.4, p90 1697.5] n=81; to fire med 697.1 [p10 372.4, p90 1011.3] n=81; to light med 169.9 [p10 48.8, p90 347.0] n=81
- fort/shelf n=124: against wall 86%, corner 46%, wall dist med 4u; door dist med 866.8 [p10 350.3, p90 1639.0] n=124; to fire med 771.7 [p10 261.7, p90 1801.5] n=108; to light med 175.1 [p10 39.9, p90 431.7] n=124
- fort/chest n=94: against wall 68%, corner 27%, wall dist med 11u; door dist med 778.4 [p10 323.6, p90 1777.6] n=94; to fire med 925.2 [p10 242.3, p90 1814.3] n=80; to light med 194.9 [p10 67.5, p90 343.7] n=94
- fort/cooking n=36: against wall 42%, corner 22%, wall dist med 88u; door dist med 750.6 [p10 514.0, p90 1788.8] n=36; to fire med 0.0 [p10 0.0, p90 148.7] n=36; to light med 129.2 [p10 37.3, p90 332.9] n=36
- fort/fire n=37: against wall 68%, corner 46%, wall dist med 16u; door dist med 778.8 [p10 253.0, p90 1669.2] n=37; to fire med 0.0 [p10 0.0, p90 0.0] n=37; to light med 106.2 [p10 20.7, p90 231.7] n=37
- fort/weaponrack n=297: against wall 64%, corner 4%, wall dist med 9u; door dist med 903.0 [p10 381.1, p90 2008.8] n=297; to fire med 803.4 [p10 460.7, p90 1742.9] n=256; to light med 227.4 [p10 65.0, p90 492.9] n=297
- fort/barrel n=374: against wall 60%, corner 28%, wall dist med 21u; door dist med 802.4 [p10 264.2, p90 2527.3] n=374; to fire med 725.0 [p10 229.6, p90 1537.5] n=325; to light med 181.7 [p10 52.9, p90 358.4] n=374
- fort/sidetable n=17: against wall 88%, corner 24%, wall dist med 4u; door dist med 719.7 [p10 373.2, p90 1366.1] n=17; to fire med 794.3 [p10 495.1, p90 1373.5] n=14; to light med 100.0 [p10 18.9, p90 290.1] n=17
- fort/cupboard n=32: against wall 91%, corner 62%, wall dist med 3u; door dist med 792.0 [p10 469.6, p90 1732.6] n=32; to fire med 936.4 [p10 182.0, p90 1959.6] n=30; to light med 191.0 [p10 104.4, p90 381.8] n=32
- fort/dresser n=23: against wall 83%, corner 35%, wall dist med 5u; door dist med 732.9 [p10 359.3, p90 1468.2] n=23; to fire med 841.9 [p10 250.3, p90 1320.7] n=20; to light med 37.8 [p10 13.5, p90 278.4] n=23
- fort/bed head end to wall: med 45.1 [p10 7.5, p90 188.1] n=107; head within 40u: 40%
- fort/seats within 160u of a table or fire: 136 of 228; axis points at it (+-30deg either way) 70%; toward table 128 fire 8
- mine/table n=45: against wall 67%, corner 38%, wall dist med 12u; door dist med 2380.9 [p10 1261.5, p90 4165.3] n=45; to fire med 1026.1 [p10 291.6, p90 2036.8] n=16; to light med 130.6 [p10 27.5, p90 287.2] n=45
- mine/seat n=42: against wall 38%, corner 17%, wall dist med 61u; door dist med 2879.9 [p10 1625.4, p90 5577.0] n=42; to fire med 873.0 [p10 253.9, p90 1946.4] n=18; to light med 133.2 [p10 75.4, p90 415.5] n=42
- mine/counter n=8: against wall 100%, corner 75%, wall dist med 8u; door dist med 870.5 [p10 409.8, p90 1719.3] n=8; to fire med 743.3 [p10 296.6, p90 1250.7] n=8; to light med 103.4 [p10 76.7, p90 263.9] n=8
- mine/shelf n=20: against wall 90%, corner 75%, wall dist med 2u; door dist med 2820.0 [p10 1096.8, p90 5343.7] n=20; to fire med 1614.3 [p10 592.2, p90 2716.9] n=10; to light med 213.2 [p10 37.9, p90 406.6] n=20
- mine/chest n=13: against wall 85%, corner 54%, wall dist med 14u; door dist med 2025.5 [p10 1572.4, p90 5634.1] n=13; to fire med 658.4 [p10 401.2, p90 1885.0] n=7; to light med 165.6 [p10 67.2, p90 375.9] n=13
- mine/cooking n=15: against wall 80%, corner 20%, wall dist med 13u; door dist med 1622.5 [p10 849.3, p90 3181.6] n=15; to fire med 0.0 [p10 0.0, p90 91.1] n=13; to light med 170.2 [p10 79.2, p90 311.4] n=15
- mine/shrine n=8: against wall 62%, corner 25%, wall dist med 13u; door dist med 3319.8 [p10 1537.2, p90 4970.9] n=8; to fire med 552.3 [p10 369.7, p90 919.0] n=4; to light med 281.5 [p10 54.1, p90 537.0] n=8
- mine/barrel n=171: against wall 80%, corner 42%, wall dist med 7u; door dist med 2496.2 [p10 1285.7, p90 4662.4] n=171; to fire med 936.7 [p10 362.6, p90 2662.3] n=90; to light med 261.9 [p10 59.4, p90 499.0] n=171
- mine/seats within 160u of a table or fire: 22 of 42; axis points at it (+-30deg either way) 73%; toward table 21 fire 1
- warehouse/bed n=13: against wall 77%, corner 62%, wall dist med 12u; door dist med 766.6 [p10 358.8, p90 1588.4] n=13; to fire med 456.2 [p10 223.9, p90 892.8] n=13; to light med 118.6 [p10 74.3, p90 132.7] n=13
- warehouse/table n=16: against wall 31%, corner 31%, wall dist med 58u; door dist med 419.9 [p10 219.1, p90 1246.3] n=16; to fire med 316.8 [p10 132.7, p90 532.6] n=14; to light med 36.4 [p10 6.9, p90 274.8] n=14
- warehouse/seat n=26: against wall 54%, corner 12%, wall dist med 26u; door dist med 581.7 [p10 259.1, p90 1226.1] n=26; to fire med 310.9 [p10 129.0, p90 564.9] n=21; to light med 98.2 [p10 69.9, p90 277.1] n=22
- warehouse/shelf n=28: against wall 82%, corner 50%, wall dist med 13u; door dist med 460.0 [p10 215.7, p90 1040.1] n=28; to fire med 408.7 [p10 144.6, p90 624.3] n=15; to light med 149.2 [p10 41.6, p90 259.0] n=23
- warehouse/cooking n=16: against wall 56%, corner 12%, wall dist med 29u; door dist med 527.9 [p10 274.2, p90 1347.4] n=16; to fire med 0.0 [p10 0.0, p90 24.1] n=16; to light med 89.6 [p10 14.8, p90 263.1] n=16
- warehouse/barrel n=115: against wall 92%, corner 37%, wall dist med 5u; door dist med 434.5 [p10 212.4, p90 785.8] n=115; to fire med 387.4 [p10 117.6, p90 735.0] n=32; to light med 180.0 [p10 46.7, p90 294.8] n=84
- warehouse/bed head end to wall: med 22.5 [p10 8.0, p90 167.9] n=12; head within 40u: 67%
- warehouse/seats within 160u of a table or fire: 17 of 25; axis points at it (+-30deg either way) 65%; toward table 16 fire 1

## D. What is on what (items resting on support by class; contact from real collision profiles; "in" = inside shelf/cupboard volume)
- on table: 2722 supports with items; items per support med 5.0 [p10 1.0, p90 13.0] n=2722; mix tableware 33%, food 23%, drink 9%, valuable 6%, ingredient 5%, misc_other 4%, book 4%, weapon 3%
   co-occurrence lift (pair share of supports / chance), count>=12: plant+valuable x4.8 (n=73); book+craft_tool x3.7 (n=47); plant+weapon x3.0 (n=57); animal_part+tool x2.8 (n=19); ingredient+toy_music x2.7 (n=14); apparel+weapon x2.5 (n=56)
- on counter: 670 supports with items; items per support med 2.0 [p10 1.0, p90 5.0] n=670; mix tableware 27%, food 19%, drink 12%, ingredient 8%, valuable 6%, misc_other 6%, potion 4%, book 3%
   co-occurrence lift (pair share of supports / chance), count>=12: ingredient+potion x3.1 (n=13); misc_other+tableware x1.2 (n=23); food+ingredient x1.0 (n=18); food+tableware x0.9 (n=60); drink+tableware x0.9 (n=47); ingredient+tableware x0.8 (n=25)
- on shelf: 3696 supports with items; items per support med 6.0 [p10 2.0, p90 14.0] n=3696; mix tableware 20%, book 14%, food 11%, misc_other 10%, drink 10%, ingredient 8%, vessel 6%, potion 4%
   co-occurrence lift (pair share of supports / chance), count>=12: book+toy_music x2.5 (n=39); plant+valuable x2.4 (n=26); apparel+plant x2.3 (n=34); book+candle x2.3 (n=19); animal_part+valuable x2.3 (n=43); apparel+weapon x2.2 (n=67)
- on sidetable: 658 supports with items; items per support med 2.0 [p10 1.0, p90 4.0] n=658; mix tableware 32%, drink 13%, food 11%, book 10%, ingredient 7%, vessel 5%, valuable 4%, apparel 4%
   co-occurrence lift (pair share of supports / chance), count>=12: drink+tableware x1.4 (n=106); food+tableware x1.2 (n=57); plant+tableware x1.1 (n=12); tableware+vessel x0.9 (n=32); drink+food x0.8 (n=16); book+tableware x0.7 (n=42)
- on cupboard: 611 supports with items; items per support med 7.0 [p10 2.0, p90 12.0] n=611; mix tableware 40%, drink 11%, food 9%, tool 9%, book 5%, misc_other 5%, vessel 4%, ingredient 4%
   co-occurrence lift (pair share of supports / chance), count>=12: animal_part+valuable x6.4 (n=16); apparel+valuable x5.4 (n=23); animal_part+apparel x4.4 (n=19); misc_other+valuable x3.3 (n=21); animal_part+ingredient x3.3 (n=19); ingredient+valuable x3.1 (n=18)
- on dresser: 495 supports with items; items per support med 2.0 [p10 1.0, p90 6.0] n=495; mix tableware 23%, ingredient 10%, book 9%, drink 8%, food 7%, valuable 7%, vessel 7%, apparel 6%
   co-occurrence lift (pair share of supports / chance), count>=12: food+tableware x1.6 (n=40); tableware+vessel x1.2 (n=51); ingredient+tableware x1.2 (n=33); drink+weapon x1.1 (n=12); drink+tableware x1.1 (n=41); misc_other+tableware x1.1 (n=20)
- on chest: 25 supports with items; items per support med 1.0 [p10 1.0, p90 2.6] n=25; mix food 15%, vessel 10%, weapon 10%, potion 10%, drink 8%, tableware 8%, book 8%, ingredient 8%
   co-occurrence lift (pair share of supports / chance), count>=12: 
- on bed: 25 supports with items; items per support med 1.0 [p10 1.0, p90 3.0] n=25; mix book 28%, apparel 19%, vessel 11%, ingredient 11%, tableware 8%, vessel_static 6%, valuable 6%, animal_part 3%
   co-occurrence lift (pair share of supports / chance), count>=12: 
- on wb_alchemy: 32 supports with items; items per support med 2.0 [p10 1.0, p90 4.0] n=32; mix ingredient 66%, potion 19%, book 8%, food 6%
   co-occurrence lift (pair share of supports / chance), count>=12: 
- on wb_smith: 29 supports with items; items per support med 1.0 [p10 1.0, p90 2.2] n=29; mix apparel 18%, valuable 18%, weapon 16%, misc_other 16%, animal_part 9%, tool 7%, vessel 5%, book 5%
   co-occurrence lift (pair share of supports / chance), count>=12: 
- on barrel: 850 supports with items; items per support med 1.0 [p10 1.0, p90 3.0] n=850; mix vessel 21%, drink 14%, tableware 13%, food 13%, valuable 7%, ingredient 5%, potion 5%, misc_other 5%
   co-occurrence lift (pair share of supports / chance), count>=12: drink+tableware x1.1 (n=18)
- on shrine: 95 supports with items; items per support med 4.0 [p10 1.0, p90 10.0] n=95; mix misc_other 25%, valuable 22%, potion 9%, tool 8%, ingredient 8%, weapon 6%, book 5%, vessel_static 5%
   co-occurrence lift (pair share of supports / chance), count>=12: tool+valuable x1.7 (n=15); misc_other+tool x1.5 (n=24); misc_other+valuable x1.3 (n=17); misc_other+potion x1.1 (n=14)
- on cooking: 110 supports with items; items per support med 1.0 [p10 1.0, p90 4.0] n=110; mix food 49%, tool 12%, tableware 11%, ingredient 7%, drink 5%, valuable 5%, misc_other 4%, vessel 3%
   co-occurrence lift (pair share of supports / chance), count>=12: 

### D2. per kind: items on tables / shelves / counters per support, and items on the floor
- dungeon(n=314): table: 787/1273 supports hold items, 3.0 items per support; top tableware/misc_other/valuable | shelf: 1223/2144 supports hold items, 3.4 items per support; top misc_other/tableware/book | counter: 153/409 supports hold items, 0.8 items per support; top tableware/misc_other/drink | cupboard: 76/84 supports hold items, 6.5 items per support; top tableware/book/misc_other | sidetable: 61/104 supports hold items, 1.1 items per support; top tableware/book/apparel | bed: 6/269 supports hold items, 0.0 items per support; top ingredient/book/tableware | floor: vessel_static 5.9, plant 4.4, vessel 3.0, tableware 2.1, misc_other 1.9 per cell
- house(n=219): table: 426/550 supports hold items, 5.7 items per support; top food/tableware/drink | shelf: 582/767 supports hold items, 5.7 items per support; top tableware/food/book | counter: 72/171 supports hold items, 0.9 items per support; top food/tableware/drink | cupboard: 165/197 supports hold items, 6.6 items per support; top tableware/drink/tool | sidetable: 162/232 supports hold items, 1.6 items per support; top tableware/food/drink | bed: 2/429 supports hold items, 0.0 items per support; top book/apparel | floor: vessel 3.1, food 0.9, tableware 0.7, tool 0.6, vessel_static 0.4 per cell
- hall_keep(n=62): table: 234/338 supports hold items, 5.2 items per support; top tableware/food/drink | shelf: 403/678 supports hold items, 4.3 items per support; top tableware/book/food | counter: 66/202 supports hold items, 1.0 items per support; top food/tableware/ingredient | cupboard: 58/106 supports hold items, 3.1 items per support; top tableware/drink/food | sidetable: 117/173 supports hold items, 1.5 items per support; top tableware/ingredient/drink | bed: 2/181 supports hold items, 0.0 items per support; top apparel | floor: vessel 6.7, tableware 2.7, food 2.4, ingredient 1.4, tool 1.2 per cell
- inn(n=59): table: 221/323 supports hold items, 4.5 items per support; top tableware/food/drink | shelf: 177/196 supports hold items, 8.0 items per support; top drink/tableware/food | counter: 114/256 supports hold items, 1.1 items per support; top food/tableware/drink | cupboard: 37/42 supports hold items, 7.1 items per support; top tableware/drink/food | sidetable: 38/52 supports hold items, 1.6 items per support; top tableware/drink/book | bed: 1/155 supports hold items, 0.0 items per support; top vessel_static | floor: vessel 3.7, food 1.2, tableware 0.7, drink 0.7, tool 0.7 per cell
- shop_general(n=53): table: 87/118 supports hold items, 5.1 items per support; top tableware/food/drink | shelf: 181/197 supports hold items, 8.4 items per support; top tableware/book/food | counter: 68/167 supports hold items, 1.0 items per support; top tableware/food/valuable | cupboard: 32/35 supports hold items, 6.8 items per support; top tableware/food/vessel | sidetable: 18/31 supports hold items, 1.5 items per support; top tableware/food/valuable | bed: 0/54 supports hold items, 0.0 items per support; top  | floor: vessel 3.6, tool 0.7, drink 0.7, tableware 0.6, vessel_static 0.6 per cell
- other(n=45): table: 98/130 supports hold items, 4.0 items per support; top tableware/food/drink | shelf: 89/132 supports hold items, 5.2 items per support; top tableware/drink/book | counter: 13/40 supports hold items, 0.8 items per support; top ingredient/valuable/misc_other | cupboard: 15/18 supports hold items, 6.6 items per support; top tableware/book/food | sidetable: 12/39 supports hold items, 0.6 items per support; top tableware/drink/food | bed: 2/49 supports hold items, 0.0 items per support; top apparel/vessel | floor: vessel_static 2.4, vessel 2.0, food 1.1, misc_other 0.8, tableware 0.8 per cell
- mill_farm(n=41): table: 65/73 supports hold items, 9.4 items per support; top tableware/food/drink | shelf: 81/88 supports hold items, 8.6 items per support; top food/tableware/book | counter: 3/7 supports hold items, 0.9 items per support; top potion/drink | cupboard: 27/32 supports hold items, 9.2 items per support; top tableware/food/tool | sidetable: 23/26 supports hold items, 2.1 items per support; top drink/tableware/valuable | bed: 0/64 supports hold items, 0.0 items per support; top  | floor: vessel 3.3, food 0.8, ingredient 0.6, tableware 0.5, tool 0.3 per cell
- bandit_camp(n=32): table: 189/235 supports hold items, 4.7 items per support; top tableware/valuable/food | shelf: 141/169 supports hold items, 6.3 items per support; top tableware/drink/food | counter: 17/28 supports hold items, 2.0 items per support; top tableware/valuable/food | cupboard: 20/22 supports hold items, 6.5 items per support; top misc_other/tableware/food | sidetable: 6/6 supports hold items, 2.8 items per support; top tableware/food/apparel | bed: 3/49 supports hold items, 0.1 items per support; top vessel/apparel | floor: vessel 6.0, plant 4.7, tableware 2.5, valuable 1.6, food 1.5 per cell
- barracks(n=30): table: 94/114 supports hold items, 5.2 items per support; top tableware/food/drink | shelf: 84/172 supports hold items, 3.3 items per support; top tableware/book/food | counter: 4/73 supports hold items, 0.3 items per support; top misc_other/valuable/book | cupboard: 18/21 supports hold items, 5.9 items per support; top tableware/food/tool | sidetable: 30/43 supports hold items, 1.7 items per support; top tableware/drink/food | bed: 1/104 supports hold items, 0.0 items per support; top animal_part | floor: vessel 3.8, tableware 1.2, vessel_static 1.1, food 0.8, tool 0.8 per cell
- temple(n=27): table: 35/49 supports hold items, 4.8 items per support; top tableware/food/book | shelf: 60/86 supports hold items, 5.9 items per support; top tableware/book/food | counter: 6/15 supports hold items, 2.1 items per support; top food/tableware/ingredient | cupboard: 14/14 supports hold items, 5.9 items per support; top tableware/tool/drink | sidetable: 12/29 supports hold items, 0.7 items per support; top tableware/book/drink | bed: 0/44 supports hold items, 0.0 items per support; top  | floor: vessel 3.4, vessel_static 3.0, valuable 2.9, tableware 1.3, tool 0.9 per cell
- guild(n=25): table: 143/171 supports hold items, 6.6 items per support; top tableware/food/drink | shelf: 237/323 supports hold items, 5.1 items per support; top book/ingredient/tableware | counter: 21/46 supports hold items, 0.8 items per support; top tableware/food/book | cupboard: 71/81 supports hold items, 4.6 items per support; top tableware/food/drink | sidetable: 108/156 supports hold items, 1.4 items per support; top tableware/drink/book | bed: 0/108 supports hold items, 0.0 items per support; top  | floor: vessel 6.4, ingredient 2.4, tableware 2.0, plant 1.7, vessel_static 1.5 per cell
- fort(n=24): table: 136/150 supports hold items, 5.1 items per support; top tableware/food/book | shelf: 114/124 supports hold items, 9.4 items per support; top tableware/apparel/book | counter: 45/81 supports hold items, 1.2 items per support; top tableware/food/ingredient | cupboard: 31/32 supports hold items, 8.6 items per support; top tableware/book/misc_other | sidetable: 12/17 supports hold items, 1.5 items per support; top tableware/drink/food | bed: 8/107 supports hold items, 0.1 items per support; top book/tableware/apparel | floor: vessel 4.0, tableware 2.7, food 1.3, apparel 1.2, tool 1.1 per cell
- mine(n=21): table: 38/45 supports hold items, 4.8 items per support; top tableware/weapon/food | shelf: 14/20 supports hold items, 3.6 items per support; top apparel/tableware/potion | counter: 2/8 supports hold items, 0.5 items per support; top tableware/tool/valuable | floor: plant 6.0, tool 1.7, vessel 1.5, weapon 1.0, vessel_static 1.0 per cell
- warehouse(n=15): table: 10/15 supports hold items, 6.1 items per support; top food/tableware/vessel | shelf: 24/28 supports hold items, 6.0 items per support; top food/tableware/drink | cupboard: 6/6 supports hold items, 9.0 items per support; top tableware/food/tool | sidetable: 6/6 supports hold items, 3.8 items per support; top tableware/vessel/drink | bed: 0/13 supports hold items, 0.0 items per support; top  | floor: food 1.0, vessel 0.9, tool 0.5, tableware 0.3, apparel 0.2 per cell

### D3. loose floor items: distance to nearest wall
pooled all kinds med 18.2 [p10 2.0, p90 72.9] n=12981 share <=40u: 77%

## E. Walls: share of sampled interior wall faces (30u offset) occupied by floor furniture / hung decor only / bare; decor heights
- dungeon(cells 254): furniture-covered 27%, decor-only 1%, bare 72%; hung decor per cell med 1.0 [p10 0.0, p90 14.0] n=314; decor centre height above floor med 293.0 [p10 69.0, p90 707.6] n=1613; top decor {'banneranchor': 365, 'dwebanner': 217, 'hook': 115, 'genericbannerred': 114}; rugs per cell med 0
- house(cells 203): furniture-covered 40%, decor-only 3%, bare 57%; hung decor per cell med 2.0 [p10 0.0, p90 12.0] n=219; decor centre height above floor med 158.0 [p10 69.0, p90 357.0] n=1105; top decor {'hanginganimalsring': 99, 'pelthanging': 99, 'alpawallbasket': 85, 'wallbasket': 85}; rugs per cell med 3
- hall_keep(cells 59): furniture-covered 33%, decor-only 4%, bare 62%; hung decor per cell med 6.0 [p10 0.0, p90 27.9] n=62; decor centre height above floor med 221.0 [p10 67.0, p90 445.0] n=631; top decor {'wallbaskethex': 56, 'hanginganimalsring': 53, 'wallmountedslaughterfish': 32, 'pelthanging': 29}; rugs per cell med 5
- inn(cells 59): furniture-covered 38%, decor-only 6%, bare 56%; hung decor per cell med 2.0 [p10 0.0, p90 23.0] n=59; decor centre height above floor med 166.0 [p10 89.0, p90 344.0] n=452; top decor {'pelthanging': 111, 'snowberrywreath': 46, 'wallmountedelkfemale': 45, 'hanginganimalsring': 39}; rugs per cell med 5
- shop_general(cells 53): furniture-covered 41%, decor-only 3%, bare 56%; hung decor per cell med 3.0 [p10 0.0, p90 14.6] n=53; decor centre height above floor med 166.5 [p10 61.9, p90 366.7] n=294; top decor {'pelthanging': 37, 'alpawallbasket': 26, 'wallbaskethex': 25, 'hanginganimalsring': 24}; rugs per cell med 2
- other(cells 38): furniture-covered 27%, decor-only 1%, bare 72%; hung decor per cell med 0.0 [p10 0.0, p90 10.8] n=45; decor centre height above floor med 229.0 [p10 94.8, p90 489.0] n=193; top decor {'dlc': 30, 'pelthanging': 19, 'banneranchor': 17, 'winterholdbannerpost': 15}; rugs per cell med 0
- mill_farm(cells 38): furniture-covered 45%, decor-only 4%, bare 52%; hung decor per cell med 4.0 [p10 0.0, p90 11.0] n=41; decor centre height above floor med 154.0 [p10 98.0, p90 357.7] n=184; top decor {'pelthanging': 30, 'hanginganimalsring': 26, 'peltfarmwall': 21, 'wallmountedslaughterfish': 16}; rugs per cell med 2
- bandit_camp(cells 29): furniture-covered 21%, decor-only 1%, bare 78%; hung decor per cell med 3.5 [p10 0.0, p90 14.9] n=32; decor centre height above floor med 195.0 [p10 46.8, p90 425.6] n=199; top decor {'hook': 40, 'hanginganimalsring': 35, 'pelthanging': 27, 'wallmountedwolf': 15}; rugs per cell med 1
- barracks(cells 28): furniture-covered 48%, decor-only 3%, bare 48%; hung decor per cell med 4.0 [p10 0.0, p90 15.0] n=30; decor centre height above floor med 176.0 [p10 64.5, p90 497.6] n=238; top decor {'dwebanner': 26, 'wrintcastlewallstrwin': 26, 'alpawallbasket': 25, 'pelthanging': 25}; rugs per cell med 5
- temple(cells 27): furniture-covered 32%, decor-only 2%, bare 67%; hung decor per cell med 1.0 [p10 0.0, p90 13.0] n=27; decor centre height above floor med 240.0 [p10 120.3, p90 449.7] n=142; top decor {'dlc': 23, 'wrintcastlewallstrwin': 15, 'hanginganimalsring': 13, 'whstormcloaksfancybanner': 9}; rugs per cell med 3
- guild(cells 23): furniture-covered 31%, decor-only 3%, bare 66%; hung decor per cell med 16.0 [p10 3.4, p90 46.2] n=25; decor centre height above floor med 242.0 [p10 104.4, p90 548.0] n=519; top decor {'banneranchor': 38, 'wrjovaskrbanner': 34, 'winterholdbannerpost': 33, 'winterholdbanner': 33}; rugs per cell med 10
- fort(cells 24): furniture-covered 28%, decor-only 1%, bare 71%; hung decor per cell med 7.0 [p10 1.0, p90 45.6] n=24; decor centre height above floor med 283.0 [p10 69.0, p90 563.4] n=394; top decor {'civilwarbannerstorm': 84, 'civilwarbannerimp': 84, 'banneranchor': 56, 'hook': 39}; rugs per cell med 1
- mine(cells 20): furniture-covered 20%, decor-only 0%, bare 80%; hung decor per cell med 0.0 [p10 0.0, p90 2.0] n=21; decor centre height above floor med 254.0 [p10 18.0, p90 503.0] n=21; top decor {'genericbanneryellow': 7, 'hanginganimalsring': 5, 'hook': 5, 'genericbannerred': 2}; rugs per cell med 0
- warehouse(cells 15): furniture-covered 39%, decor-only 1%, bare 60%; hung decor per cell med 0.0 [p10 0.0, p90 5.6] n=15; decor centre height above floor med 162.5 [p10 34.0, p90 362.0] n=26; top decor {'wallbasket': 4, 'hanginganimalsring': 3, 'wallmountedmudcrab': 2, 'wallbasketlarge': 2}; rugs per cell med 0
- alchemist(cells 15): furniture-covered 37%, decor-only 3%, bare 60%; hung decor per cell med 3.0 [p10 0.0, p90 12.2] n=15; decor centre height above floor med 164.0 [p10 43.7, p90 400.6] n=68; top decor {'wallbasket': 12, 'pelthanging': 11, 'wallmountedslaughterfish': 8, 'wallbaskethex': 8}; rugs per cell med 3
- cellar(cells 14): furniture-covered 35%, decor-only 2%, bare 64%; hung decor per cell med 1.0 [p10 0.0, p90 6.8] n=14; decor centre height above floor med 176.0 [p10 32.5, p90 238.0] n=36; top decor {'hanginganimalsring': 11, 'citybannerwhiterun': 7, 'wallbasketlarge': 6, 'hook': 3}; rugs per cell med 0
- jail(cells 14): furniture-covered 29%, decor-only 1%, bare 70%; hung decor per cell med 0.0 [p10 0.0, p90 11.6] n=14; decor centre height above floor med 144.0 [p10 46.0, p90 472.0] n=51; top decor {'hook': 14, 'rtbanneranchor': 6, 'civilwarbannerimp': 5, 'citybannerriften': 5}; rugs per cell med 0
- ship(cells 5): furniture-covered 28%, decor-only 0%, bare 72%; hung decor per cell med 1.5 [p10 0.0, p90 19.3] n=12; decor centre height above floor med 157.0 [p10 61.9, p90 283.0] n=90; top decor {'banneranchor': 17, 'sbannerltall': 16, 'aaashipbanner': 15, 'hook': 9}; rugs per cell med 0
- smith(cells 12): furniture-covered 52%, decor-only 1%, bare 47%; hung decor per cell med 0.0 [p10 0.0, p90 5.6] n=12; decor centre height above floor med 151.0 [p10 84.2, p90 437.2] n=18; top decor {'hanginganimalsring': 3, 'alpawallbasket': 3, 'wallmountedslaughterfish': 3, 'pelthanging': 2}; rugs per cell med 2
- clothier(cells 4): furniture-covered 40%, decor-only 3%, bare 56%; hung decor per cell med 5.0 [p10 0.3, p90 9.7] n=4; decor centre height above floor med 165.0 [p10 58.8, p90 263.5] n=20; top decor {'pelthanging': 5, 'wallmountedwolf': 4, 'tgbanner': 2, 'morrcluttermirror': 1}; rugs per cell med 8

## F. Light: sources per 100 m2 of occupied hull; kinds; nearest light to seats/beds/workbenches
- dungeon(n=314): light refs/cell med 52.0 [p10 8.0, p90 174.1] n=314; per 100m2 med 1.6 [p10 0.4, p90 5.1] n=314; hull m2 med 4349.2 [p10 359.8, p90 17692.7] n=314; lit props (candles/lanterns) per cell med 24.0 [p10 0.0, p90 133.0] n=314; kinds candle 52%, other 14%, torch 13%, sconce 12%, window_sun 3%; nearest light: seat med 206.2 [p10 71.1, p90 616.9] n=1516, bed med 205.6 [p10 96.4, p90 447.2] n=270, work med 202.5 [p10 39.2, p90 575.5] n=564
- house(n=219): light refs/cell med 7.0 [p10 1.0, p90 31.2] n=219; per 100m2 med 7.7 [p10 0.7, p90 19.4] n=219; hull m2 med 95.1 [p10 30.3, p90 402.6] n=219; lit props (candles/lanterns) per cell med 3.0 [p10 0.0, p90 15.0] n=219; kinds candle 55%, fire 14%, other 11%, lantern 7%, window_sun 7%; nearest light: seat med 119.3 [p10 55.1, p90 371.5] n=896, bed med 144.9 [p10 61.5, p90 354.8] n=432, work med 132.5 [p10 20.8, p90 290.3] n=240
- hall_keep(n=62): light refs/cell med 27.5 [p10 5.2, p90 68.5] n=62; per 100m2 med 5.8 [p10 1.1, p90 14.0] n=62; hull m2 med 420.9 [p10 90.8, p90 1577.2] n=62; lit props (candles/lanterns) per cell med 19.0 [p10 2.1, p90 44.7] n=62; kinds candle 59%, other 14%, fire 7%, torch 7%, window_sun 6%; nearest light: seat med 112.9 [p10 54.2, p90 278.1] n=583, bed med 140.5 [p10 50.6, p90 324.2] n=181, work med 151.1 [p10 23.9, p90 388.4] n=251
- inn(n=59): light refs/cell med 14.0 [p10 3.0, p90 38.4] n=59; per 100m2 med 7.6 [p10 2.9, p90 14.5] n=59; hull m2 med 252.7 [p10 53.6, p90 557.7] n=59; lit props (candles/lanterns) per cell med 7.0 [p10 1.0, p90 30.0] n=59; kinds candle 57%, other 16%, lantern 13%, fire 10%, torch 2%; nearest light: seat med 115.8 [p10 54.6, p90 357.3] n=471, bed med 124.1 [p10 52.3, p90 260.4] n=155, work med 84.1 [p10 22.3, p90 296.1] n=270
- shop_general(n=53): light refs/cell med 10.0 [p10 4.0, p90 25.8] n=53; per 100m2 med 7.9 [p10 2.3, p90 22.3] n=53; hull m2 med 100.1 [p10 51.8, p90 591.8] n=53; lit props (candles/lanterns) per cell med 5.0 [p10 1.2, p90 14.0] n=53; kinds candle 47%, other 16%, lantern 16%, fire 10%, window_sun 7%; nearest light: seat med 93.3 [p10 57.5, p90 280.0] n=189, bed med 122.4 [p10 56.5, p90 284.8] n=54, work med 76.8 [p10 22.7, p90 218.4] n=196
- other(n=45): light refs/cell med 10.0 [p10 3.0, p90 63.2] n=45; per 100m2 med 4.1 [p10 0.1, p90 13.7] n=44; hull m2 med 422.3 [p10 23.9, p90 14719.8] n=45; lit props (candles/lanterns) per cell med 4.0 [p10 0.0, p90 33.0] n=45; kinds candle 43%, other 21%, torch 13%, lantern 7%, sconce 7%; nearest light: seat med 143.9 [p10 65.6, p90 373.4] n=249, bed med 242.3 [p10 104.0, p90 386.6] n=49, work med 90.9 [p10 23.5, p90 395.4] n=60
- mill_farm(n=41): light refs/cell med 12.0 [p10 1.0, p90 17.0] n=41; per 100m2 med 10.6 [p10 1.4, p90 19.0] n=41; hull m2 med 74.6 [p10 50.0, p90 188.4] n=41; lit props (candles/lanterns) per cell med 6.0 [p10 0.0, p90 9.0] n=41; kinds candle 51%, other 23%, fire 12%, window_sun 7%, lantern 6%; nearest light: seat med 125.0 [p10 57.5, p90 280.4] n=117, bed med 143.1 [p10 47.8, p90 304.6] n=63, work med 167.1 [p10 46.2, p90 385.8] n=13
- bandit_camp(n=32): light refs/cell med 40.5 [p10 15.2, p90 106.9] n=32; per 100m2 med 2.3 [p10 1.0, p90 5.1] n=32; hull m2 med 1824.1 [p10 344.8, p90 7217.3] n=32; lit props (candles/lanterns) per cell med 21.5 [p10 8.0, p90 72.5] n=32; kinds candle 66%, torch 16%, lantern 6%, other 4%, window_sun 4%; nearest light: seat med 188.4 [p10 78.6, p90 439.3] n=217, bed med 213.0 [p10 120.0, p90 422.5] n=49, work med 169.6 [p10 62.9, p90 425.2] n=59
- barracks(n=30): light refs/cell med 10.0 [p10 2.0, p90 42.2] n=30; per 100m2 med 7.4 [p10 2.5, p90 17.5] n=30; hull m2 med 111.9 [p10 53.4, p90 1188.8] n=30; lit props (candles/lanterns) per cell med 5.5 [p10 1.0, p90 26.4] n=30; kinds candle 39%, other 21%, fire 13%, sconce 10%, torch 7%; nearest light: seat med 124.4 [p10 57.7, p90 309.6] n=213, bed med 159.1 [p10 75.8, p90 310.3] n=104, work med 154.9 [p10 19.6, p90 382.1] n=85
- temple(n=27): light refs/cell med 27.0 [p10 3.0, p90 83.8] n=27; per 100m2 med 8.6 [p10 1.5, p90 21.7] n=27; hull m2 med 296.1 [p10 71.3, p90 1238.4] n=27; lit props (candles/lanterns) per cell med 16.0 [p10 1.0, p90 57.0] n=27; kinds candle 64%, other 10%, lantern 8%, fire 7%, torch 5%; nearest light: seat med 176.0 [p10 59.4, p90 443.1] n=164, bed med 221.7 [p10 66.0, p90 391.2] n=44, work med 123.3 [p10 42.5, p90 377.0] n=17
- guild(n=25): light refs/cell med 29.0 [p10 11.8, p90 113.4] n=25; per 100m2 med 4.6 [p10 0.8, p90 8.0] n=25; hull m2 med 677.3 [p10 363.6, p90 4732.1] n=25; lit props (candles/lanterns) per cell med 18.0 [p10 7.0, p90 71.4] n=25; kinds candle 67%, torch 8%, other 8%, window_sun 8%, lantern 4%; nearest light: seat med 132.9 [p10 62.6, p90 313.9] n=351, bed med 160.7 [p10 24.5, p90 401.7] n=108, work med 117.2 [p10 25.1, p90 272.2] n=68
- fort(n=24): light refs/cell med 24.5 [p10 15.0, p90 60.9] n=24; per 100m2 med 4.0 [p10 3.0, p90 8.7] n=24; hull m2 med 751.1 [p10 133.4, p90 1779.5] n=24; lit props (candles/lanterns) per cell med 14.0 [p10 5.6, p90 36.6] n=24; kinds candle 82%, torch 13%, lantern 3%, fill_glow 1%, window_sun 1%; nearest light: seat med 132.8 [p10 49.2, p90 345.3] n=228, bed med 222.9 [p10 96.3, p90 441.4] n=107, work med 137.2 [p10 48.8, p90 347.0] n=93
- mine(n=21): light refs/cell med 23.0 [p10 12.0, p90 54.0] n=21; per 100m2 med 4.0 [p10 2.3, p90 6.2] n=21; hull m2 med 604.1 [p10 275.0, p90 2640.4] n=21; lit props (candles/lanterns) per cell med 10.0 [p10 3.0, p90 19.0] n=21; kinds candle 56%, fire 18%, torch 11%, other 8%, lantern 3%; nearest light: seat med 133.2 [p10 75.4, p90 415.5] n=42, bed med 145.0 [p10 145.0, p90 145.0] n=1, work med 112.9 [p10 80.3, p90 262.7] n=9
- warehouse(n=15): light refs/cell med 4.0 [p10 0.0, p90 14.6] n=15; per 100m2 med 10.3 [p10 0.0, p90 15.1] n=15; hull m2 med 61.1 [p10 26.4, p90 130.0] n=15; lit props (candles/lanterns) per cell med 2.0 [p10 0.0, p90 7.4] n=15; kinds candle 50%, fire 20%, lantern 11%, other 9%, window_sun 9%; nearest light: seat med 98.2 [p10 69.9, p90 277.1] n=22, bed med 118.6 [p10 74.3, p90 132.7] n=13, work med 77.4 [p10 15.5, p90 153.0] n=3
- alchemist(n=15): light refs/cell med 10.0 [p10 2.6, p90 27.6] n=15; per 100m2 med 12.0 [p10 2.5, p90 22.3] n=15; hull m2 med 108.7 [p10 55.8, p90 278.6] n=15; lit props (candles/lanterns) per cell med 7.0 [p10 0.8, p90 16.6] n=15; kinds candle 63%, fire 10%, other 10%, window_sun 9%, lantern 4%; nearest light: seat med 104.5 [p10 41.0, p90 232.3] n=45, bed med 112.2 [p10 50.2, p90 334.0] n=16, work med 73.8 [p10 14.0, p90 241.0] n=80
- cellar(n=14): light refs/cell med 17.0 [p10 3.3, p90 53.4] n=14; per 100m2 med 9.0 [p10 2.1, p90 12.5] n=14; hull m2 med 208.3 [p10 44.3, p90 1171.2] n=14; lit props (candles/lanterns) per cell med 8.0 [p10 1.3, p90 28.7] n=14; kinds candle 71%, torch 14%, other 5%, window_sun 5%, lantern 3%; nearest light: seat med 165.0 [p10 60.8, p90 276.6] n=41, bed med 165.0 [p10 79.4, p90 408.0] n=9, work med 64.8 [p10 28.2, p90 226.9] n=14
- jail(n=14): light refs/cell med 16.0 [p10 7.5, p90 91.9] n=14; per 100m2 med 4.2 [p10 0.7, p90 7.2] n=14; hull m2 med 407.1 [p10 205.5, p90 3535.5] n=14; lit props (candles/lanterns) per cell med 9.5 [p10 2.9, p90 51.1] n=14; kinds candle 63%, other 18%, window_sun 5%, lantern 4%, torch 4%; nearest light: seat med 101.9 [p10 41.9, p90 223.8] n=102, bed med 169.0 [p10 94.8, p90 322.1] n=30, work med 223.3 [p10 215.2, p90 239.2] n=15
- ship(n=12): light refs/cell med 6.0 [p10 0.1, p90 41.6] n=12; per 100m2 med 9.9 [p10 3.4, p90 27.8] n=11; hull m2 med 64.4 [p10 27.8, p90 431.4] n=12; lit props (candles/lanterns) per cell med 3.0 [p10 0.0, p90 22.0] n=12; kinds candle 69%, lantern 13%, window_sun 10%, other 6%, fire 2%; nearest light: seat med 109.5 [p10 48.8, p90 266.4] n=80, bed med 148.6 [p10 92.5, p90 302.2] n=59, work med 106.8 [p10 31.7, p90 220.0] n=51
- smith(n=12): light refs/cell med 11.0 [p10 4.1, p90 19.8] n=12; per 100m2 med 5.3 [p10 2.2, p90 12.5] n=12; hull m2 med 179.5 [p10 82.7, p90 321.7] n=12; lit props (candles/lanterns) per cell med 5.0 [p10 1.1, p90 10.7] n=12; kinds candle 45%, fire 23%, other 15%, lantern 7%, window_sun 7%; nearest light: seat med 80.0 [p10 28.7, p90 158.3] n=31, bed med 157.4 [p10 37.9, p90 430.3] n=21, work med 151.5 [p10 61.1, p90 228.3] n=30
- clothier(n=4): light refs/cell med 11.0 [p10 7.5, p90 41.8] n=4; per 100m2 med 11.7 [p10 5.4, p90 14.2] n=4; hull m2 med 185.6 [p10 67.4, p90 365.3] n=4; lit props (candles/lanterns) per cell med 6.0 [p10 3.6, p90 28.7] n=4; kinds candle 60%, other 14%, window_sun 12%, lantern 10%, torch 4%; nearest light: seat med 87.7 [p10 26.3, p90 229.9] n=19, bed med 95.3 [p10 17.6, p90 141.8] n=7, work med 95.8 [p10 45.7, p90 102.7] n=5
- camp_tent(n=3): light refs/cell med 2.0 [p10 2.0, p90 5.2] n=3; per 100m2 med 9.1 [p10 9.1, p90 16.0] n=3; hull m2 med 22.0 [p10 22.0, p90 31.6] n=3; lit props (candles/lanterns) per cell med 1.0 [p10 1.0, p90 2.6] n=3; kinds other 50%, lantern 40%, candle 10%; nearest light: seat med 72.5 [p10 59.0, p90 108.5] n=4, bed n=0, work n=0
- fletcher(n=1): light refs/cell med 41.0 [p10 41.0, p90 41.0] n=1; per 100m2 med 16.5 [p10 16.5, p90 16.5] n=1; hull m2 med 247.9 [p10 247.9, p90 247.9] n=1; lit props (candles/lanterns) per cell med 26.0 [p10 26.0, p90 26.0] n=1; kinds candle 68%, window_sun 29%, fire 2%; nearest light: seat med 82.2 [p10 35.5, p90 106.8] n=8, bed med 115.8 [p10 42.6, p90 188.9] n=2, work med 77.4 [p10 13.5, p90 108.9] n=5
## G. Wealth and owner
- barracks/mid n=17: refs med 129.0 [p10 39.2, p90 373.2] n=17; hull m2 med 84.3 [p10 32.0, p90 347.2] n=17; small items per cell med 50.0 [p10 11.4, p90 97.8] n=17; beds med 3.0 [p10 1.6, p90 8.8] n=17; rugs med 3.0 [p10 0.0, p90 8.0] n=17; wall decor med 3.0 [p10 0.0, p90 14.4] n=17; shelves med 2.0 [p10 0.6, p90 5.2] n=17; light refs med 10.0 [p10 2.6, p90 26.6] n=17; tableware share cells 82% books 65%
- barracks/poor n=10: refs med 147.0 [p10 102.0, p90 1216.9] n=10; hull m2 med 142.7 [p10 66.8, p90 3264.9] n=10; small items per cell med 43.0 [p10 30.0, p90 256.4] n=10; beds med 4.0 [p10 0.0, p90 7.1] n=10; rugs med 7.0 [p10 0.0, p90 33.5] n=10; wall decor med 8.5 [p10 0.0, p90 14.4] n=10; shelves med 3.0 [p10 1.9, p90 29.5] n=10; light refs med 9.0 [p10 1.9, p90 81.8] n=10; tableware share cells 100% books 70%
- guild/mid n=9: refs med 419.0 [p10 117.6, p90 1006.0] n=9; hull m2 med 532.1 [p10 270.6, p90 3343.8] n=9; small items per cell med 42.0 [p10 24.6, p90 190.2] n=9; beds med 3.0 [p10 0.0, p90 8.0] n=9; rugs med 3.0 [p10 0.0, p90 9.0] n=9; wall decor med 4.0 [p10 2.0, p90 18.2] n=9; shelves med 2.0 [p10 0.8, p90 6.4] n=9; light refs med 20.0 [p10 10.6, p90 72.0] n=9; tableware share cells 67% books 78%
- guild/rich n=13: refs med 855.0 [p10 357.0, p90 1723.0] n=13; hull m2 med 677.3 [p10 456.9, p90 1019.1] n=13; small items per cell med 279.0 [p10 177.6, p90 507.0] n=13; beds med 3.0 [p10 0.4, p90 15.0] n=13; rugs med 19.0 [p10 8.4, p90 27.4] n=13; wall decor med 31.0 [p10 15.0, p90 46.6] n=13; shelves med 15.0 [p10 3.8, p90 39.0] n=13; light refs med 37.0 [p10 23.0, p90 85.6] n=13; tableware share cells 92% books 92%
- hall_keep/mid n=21: refs med 324.0 [p10 106.0, p90 900.0] n=21; hull m2 med 337.8 [p10 82.2, p90 2903.1] n=21; small items per cell med 99.0 [p10 24.0, p90 205.0] n=21; beds med 3.0 [p10 0.0, p90 6.0] n=21; rugs med 3.0 [p10 0.0, p90 10.0] n=21; wall decor med 4.0 [p10 0.0, p90 15.0] n=21; shelves med 7.0 [p10 2.0, p90 27.0] n=21; light refs med 25.0 [p10 4.0, p90 84.0] n=21; tableware share cells 95% books 71%
- hall_keep/rich n=28: refs med 545.0 [p10 280.0, p90 1318.0] n=28; hull m2 med 581.4 [p10 179.3, p90 1337.3] n=28; small items per cell med 213.0 [p10 33.1, p90 405.0] n=28; beds med 4.0 [p10 0.0, p90 9.3] n=28; rugs med 12.0 [p10 0.0, p90 27.3] n=28; wall decor med 9.5 [p10 1.4, p90 30.5] n=28; shelves med 10.0 [p10 2.7, p90 39.3] n=28; light refs med 37.5 [p10 13.5, p90 65.5] n=28; tableware share cells 96% books 89%
- house/mid n=158: refs med 120.0 [p10 45.7, p90 285.0] n=158; hull m2 med 90.3 [p10 41.1, p90 286.4] n=158; small items per cell med 43.0 [p10 13.7, p90 108.5] n=158; beds med 2.0 [p10 1.0, p90 3.0] n=158; rugs med 3.0 [p10 0.0, p90 4.3] n=158; wall decor med 1.0 [p10 0.0, p90 11.0] n=158; shelves med 2.0 [p10 0.0, p90 5.0] n=158; light refs med 7.0 [p10 1.0, p90 19.3] n=158; tableware share cells 96% books 44%
- house/mixed n=14: refs med 127.5 [p10 27.0, p90 643.1] n=14; hull m2 med 78.3 [p10 18.3, p90 1022.7] n=14; small items per cell med 21.5 [p10 12.3, p90 252.3] n=14; beds med 1.0 [p10 1.0, p90 6.4] n=14; rugs med 0.0 [p10 0.0, p90 16.8] n=14; wall decor med 0.0 [p10 0.0, p90 12.5] n=14; shelves med 1.0 [p10 1.0, p90 10.8] n=14; light refs med 8.0 [p10 2.0, p90 46.3] n=14; tableware share cells 93% books 57%
- house/poor n=19: refs med 110.0 [p10 56.4, p90 204.2] n=19; hull m2 med 63.6 [p10 16.8, p90 121.1] n=19; small items per cell med 32.0 [p10 14.2, p90 53.6] n=19; beds med 2.0 [p10 1.0, p90 4.0] n=19; rugs med 3.0 [p10 0.0, p90 5.2] n=19; wall decor med 8.0 [p10 1.6, p90 16.4] n=19; shelves med 2.0 [p10 0.8, p90 5.2] n=19; light refs med 5.0 [p10 1.0, p90 10.0] n=19; tableware share cells 100% books 79%
- house/rich n=18: refs med 696.5 [p10 225.6, p90 1054.9] n=18; hull m2 med 322.1 [p10 78.0, p90 754.0] n=18; small items per cell med 134.5 [p10 60.7, p90 330.4] n=18; beds med 3.0 [p10 1.0, p90 7.3] n=18; rugs med 8.5 [p10 1.7, p90 22.3] n=18; wall decor med 10.0 [p10 2.7, p90 25.6] n=18; shelves med 10.5 [p10 3.0, p90 15.9] n=18; light refs med 32.5 [p10 13.7, p90 74.0] n=18; tableware share cells 94% books 94%
- inn/mid n=27: refs med 208.0 [p10 54.2, p90 424.8] n=27; hull m2 med 240.7 [p10 42.2, p90 558.2] n=27; small items per cell med 71.0 [p10 6.4, p90 140.2] n=27; beds med 2.0 [p10 0.0, p90 4.0] n=27; rugs med 2.0 [p10 0.0, p90 8.2] n=27; wall decor med 0.0 [p10 0.0, p90 4.0] n=27; shelves med 3.0 [p10 0.0, p90 7.4] n=27; light refs med 11.0 [p10 2.6, p90 32.2] n=27; tableware share cells 81% books 41%
- inn/mixed n=11: refs med 341.0 [p10 97.0, p90 695.0] n=11; hull m2 med 474.9 [p10 157.8, p90 610.7] n=11; small items per cell med 154.0 [p10 36.0, p90 238.0] n=11; beds med 4.0 [p10 2.0, p90 5.0] n=11; rugs med 13.0 [p10 3.0, p90 17.0] n=11; wall decor med 20.0 [p10 2.0, p90 23.0] n=11; shelves med 3.0 [p10 2.0, p90 6.0] n=11; light refs med 37.0 [p10 7.0, p90 42.0] n=11; tableware share cells 100% books 82%
- inn/poor n=16: refs med 171.5 [p10 114.5, p90 355.5] n=16; hull m2 med 99.6 [p10 57.8, p90 474.3] n=16; small items per cell med 57.0 [p10 32.5, p90 144.5] n=16; beds med 4.5 [p10 1.5, p90 5.5] n=16; rugs med 7.0 [p10 4.0, p90 14.0] n=16; wall decor med 2.0 [p10 0.0, p90 23.0] n=16; shelves med 1.0 [p10 0.5, p90 3.0] n=16; light refs med 12.0 [p10 6.0, p90 37.0] n=16; tableware share cells 94% books 81%
- other/mid n=219: refs med 340.0 [p10 77.0, p90 1407.0] n=219; hull m2 med 512.0 [p10 59.9, p90 6877.6] n=219; small items per cell med 66.0 [p10 16.8, p90 214.4] n=219; beds med 2.0 [p10 0.0, p90 7.0] n=219; rugs med 2.0 [p10 0.0, p90 9.0] n=219; wall decor med 3.0 [p10 0.0, p90 15.0] n=219; shelves med 3.0 [p10 0.0, p90 9.0] n=219; light refs med 21.0 [p10 6.0, p90 102.0] n=219; tableware share cells 87% books 68%
- other/mixed n=31: refs med 373.0 [p10 144.0, p90 1709.0] n=31; hull m2 med 460.0 [p10 71.3, p90 7689.6] n=31; small items per cell med 50.0 [p10 20.0, p90 208.0] n=31; beds med 2.0 [p10 0.0, p90 7.0] n=31; rugs med 1.0 [p10 0.0, p90 8.0] n=31; wall decor med 1.0 [p10 0.0, p90 13.0] n=31; shelves med 3.0 [p10 2.0, p90 12.0] n=31; light refs med 27.0 [p10 3.0, p90 90.0] n=31; tableware share cells 90% books 74%
- other/poor n=159: refs med 1047.0 [p10 123.6, p90 2222.4] n=159; hull m2 med 5980.0 [p10 105.2, p90 19853.7] n=159; small items per cell med 74.0 [p10 8.0, p90 186.4] n=159; beds med 0.0 [p10 0.0, p90 5.2] n=159; rugs med 0.0 [p10 0.0, p90 2.0] n=159; wall decor med 2.0 [p10 0.0, p90 14.2] n=159; shelves med 5.0 [p10 0.0, p90 19.2] n=159; light refs med 66.0 [p10 6.8, p90 203.2] n=159; tableware share cells 68% books 59%
- other/rich n=25: refs med 683.0 [p10 314.6, p90 2761.0] n=25; hull m2 med 1001.6 [p10 249.3, p90 6718.0] n=25; small items per cell med 190.0 [p10 52.8, p90 492.8] n=25; beds med 3.0 [p10 0.0, p90 7.8] n=25; rugs med 5.0 [p10 0.0, p90 23.6] n=25; wall decor med 10.0 [p10 1.0, p90 47.6] n=25; shelves med 8.0 [p10 2.0, p90 23.2] n=25; light refs med 67.0 [p10 18.6, p90 169.8] n=25; tableware share cells 100% books 96%
- shop_general/mid n=33: refs med 229.0 [p10 107.2, p90 553.2] n=33; hull m2 med 141.2 [p10 64.1, p90 1043.4] n=33; small items per cell med 66.0 [p10 22.0, p90 141.6] n=33; beds med 2.0 [p10 0.0, p90 2.0] n=33; rugs med 3.0 [p10 0.0, p90 9.0] n=33; wall decor med 3.0 [p10 0.0, p90 14.4] n=33; shelves med 3.0 [p10 1.0, p90 6.8] n=33; light refs med 14.0 [p10 4.2, p90 25.8] n=33; tableware share cells 88% books 70%
- shop_general/poor n=9: refs med 115.0 [p10 96.0, p90 163.4] n=9; hull m2 med 78.0 [p10 45.4, p90 110.3] n=9; small items per cell med 39.0 [p10 29.0, p90 59.6] n=9; beds med 2.0 [p10 0.0, p90 3.0] n=9; rugs med 0.0 [p10 0.0, p90 3.2] n=9; wall decor med 3.0 [p10 0.0, p90 19.4] n=9; shelves med 3.0 [p10 1.8, p90 4.0] n=9; light refs med 8.0 [p10 4.8, p90 9.6] n=9; tableware share cells 100% books 56%

wealth marks by evidence: share of house cells classed (>=3 style-bearing pieces): 209 of 219

### owner type by kind (cell owner field: none / faction / NPC) and top owners
- dungeon(n=314): cell owner {'none': 300, 'FACT': 12, 'NPC_': 2}; cells with owned beds 5/126; top [('HouseofReclamationsFaction', 3), ('RootWhisperFaction', 2), ('Sathil', 1)]
- house(n=219): cell owner {'NPC_': 83, 'none': 32, 'FACT': 104}; cells with owned beds 115/210; top [('RootWhisperFaction', 4), ('KeebaHollowFaction', 4), ('PlayerFaction', 4)]
- hall_keep(n=62): cell owner {'none': 25, 'NPC_': 1, 'FACT': 36}; cells with owned beds 34/45; top [('WindhelmPalace', 3), ('DLC2RRMorvaynManorFaction', 2), ('PlayerFaction', 2)]
- inn(n=59): cell owner {'none': 6, 'FACT': 48, 'NPC_': 5}; cells with owned beds 40/50; top [('BaanWDCliffracersDemiseFaction', 2), ('BaanHSScramblingScribFaction', 2), ('WinterholdFrozenHearthFaction', 2)]
- shop_general(n=53): cell owner {'FACT': 47, 'none': 4, 'NPC_': 2}; cells with owned beds 27/37; top [('BaanMalurCrimeFaction', 3), ('CormarisCrimeFaction', 1), ('LilmothShipwrightFaction', 1)]
- other(n=45): cell owner {'none': 32, 'FACT': 13}; cells with owned beds 7/23; top [('BaanMalurGuardFaction', 3), ('BaanMalurCrimeFaction', 2), ('AshumallitFamily', 1)]
- mill_farm(n=41): cell owner {'none': 5, 'FACT': 28, 'NPC_': 8}; cells with owned beds 22/40; top [('CormarisLleftaFARMFaction', 2), ('CrossroadsCCFaction', 2), ('TownSalviusFarmFaction', 1)]
- bandit_camp(n=32): cell owner {'none': 32}; cells with owned beds 1/27; top []
- barracks(n=30): cell owner {'FACT': 27, 'none': 2, 'NPC_': 1}; cells with owned beds 19/28; top [('LilmothGuardFaction', 3), ('MarkarthWizardFaction', 3), ('SeekhatYolFaction', 2)]
- temple(n=27): cell owner {'FACT': 13, 'none': 5, 'NPC_': 9}; cells with owned beds 11/20; top [('HouseofReclamationsFaction', 3), ('WindhelmPriestsFaction', 1), ('FalkreathHouseofArkayFaction', 1)]
- guild(n=25): cell owner {'FACT': 10, 'none': 14, 'NPC_': 1}; cells with owned beds 19/20; top [('CompanionsFaction', 2), ('BaanIndorilFaction', 1), ('BaanSadrasFaction', 1)]
- fort(n=24): cell owner {'none': 24}; cells with owned beds 0/21; top []
- mine(n=21): cell owner {'FACT': 6, 'none': 14, 'NPC_': 1}; cells with owned beds 5/8; top [('TownMorKhazgurFaction', 2), ('MulushGroShugurz', 1), ('WhistlingMineFaction', 1)]
- warehouse(n=15): cell owner {'FACT': 13, 'none': 2}; cells with owned beds 6/6; top [('BaanMalurCrimeFaction', 2), ('CrossroadsCCFaction', 2), ('LilmothStablesFaction', 2)]
- alchemist(n=15): cell owner {'FACT': 13, 'none': 1, 'NPC_': 1}; cells with owned beds 10/13; top [('LilmothApothecaryFaction', 2), ('DLC2TelMithrynFaction', 1), ('BaanHSAlchemistFaction', 1)]
- cellar(n=14): cell owner {'FACT': 8, 'NPC_': 1, 'none': 5}; cells with owned beds 2/4; top [('MorthalAlvasHouseFaction', 1), ('MareinStablesFaction', 1), ('BaanMalurCrimeFaction', 1)]
- jail(n=14): cell owner {'none': 5, 'FACT': 9}; cells with owned beds 4/12; top [('MorthalGuardhouseFaction', 1), ('GuardFactionDawnstar', 1), ('BaanMalurGuardFaction', 1)]
- ship(n=12): cell owner {'none': 9, 'FACT': 3}; cells with owned beds 5/12; top [('MurkmireTravelShipFaction', 2), ('BaanMalurGuardFaction', 1)]
- smith(n=12): cell owner {'FACT': 10, 'none': 1, 'NPC_': 1}; cells with owned beds 8/8; top [('LilmothIronworksFaction', 2), ('LilmothOliisIronFoundryFaction', 2), ('BaanMalurGuardFaction', 1)]
- clothier(n=4): cell owner {'FACT': 4}; cells with owned beds 3/4; top [('BaanHSClothierFaction', 1), ('BaanEDWeaversFaction', 1), ('DLC2RRGloverMalloryFaction', 1)]
- camp_tent(n=3): cell owner {'NPC_': 1, 'FACT': 2}; cells with owned beds 0/0; top [('SOMRSaxhleelFaction', 2), ('SOMRSaxhleelKarJei', 1)]
- fletcher(n=1): cell owner {'FACT': 1}; cells with owned beds 1/1; top [('SolitudeFletcherFaction', 1)]

### what marks a trade or faith (share of cells of the kind with it; cells of other kinds with it)
- forge/anvil/grindstone/armor bench: smith 67%, bandit_camp 34%, ship 25%, cellar 21%, shop_general 21%, barracks 17%
- alchemy bench: alchemist 87%, guild 28%, ship 25%, hall_keep 23%, bandit_camp 19%, dungeon 17%
- enchanting: hall_keep 26%, ship 25%, guild 20%, dungeon 14%, fort 12%, bandit_camp 9%
- shrine/altar/statue: temple 70%, dungeon 52%, other 24%, barracks 17%, smith 17%, bandit_camp 16%
- weapon rack/armor stand: fort 38%, hall_keep 29%, cellar 29%, ship 25%, bandit_camp 19%, guild 16%
- counter/bar: alchemist 67%, inn 59%, shop_general 43%, fort 29%, hall_keep 21%, dungeon 18%
- prison fittings: jail 57%, dungeon 54%, bandit_camp 53%, fort 46%, guild 24%, mine 24%
- bath: guild 40%, hall_keep 21%, barracks 17%, alchemist 13%, inn 10%, ship 8%
- practice dummy: fort 21%, bandit_camp 19%, hall_keep 18%, guild 16%, jail 14%, barracks 10%

## H. Room sets (door graph from teleport doors)
interior cells in analysed set: 1064; with no teleport link to another interior cell in set: 755; multi-cell buildings found: 115
building size (interior cells joined by doors) -> count: {1: 11, 2: 74, 3: 27, 4: 8, 5: 2, 6: 2, 7: 1, 9: 1}
    2  house:main > cellar:cellar
    2  hall_keep:main > hall_keep:annex
    2  barracks:barracks > jail:barracks
    2  temple:main > dungeon:main
    2  jail:main > dungeon:main
    1  dungeon:main > other:main > guild:main > other:main > other:main > hall_keep:main
    1  inn:main > inn:upper
    1  dungeon:main > dungeon:main > dungeon:main > other:annex > temple:main
    1  barracks:upper > inn:main
    1  inn:main > inn:upper > alchemist:main > inn:upper > shop_general:main
    1  hall_keep:main > dungeon:main
    1  cellar:cellar > warehouse:main
    1  ship:main > dungeon:main > house:main
    1  clothier:main > shop_general:main > alchemist:main
    1  hall_keep:upper > hall_keep:main > jail:main
    1  guild:upper > guild:main > guild:upper
    1  jail:main > barracks:main
    1  jail:main > dungeon:main > guild:upper
    1  dungeon:main > dungeon:main > temple:main > dungeon:main
    1  mill_farm:main > cellar:cellar
    1  dungeon:main > guild:main > guild:upper
    1  jail:main > house:main
    1  jail:main > dungeon:main > hall_keep:main
    1  dungeon:main > jail:main
    1  inn:main > inn:cellar
rooms (interior cells) per building by entry kind: dungeon med 2 max 6 n=65; hall_keep med 2 max 3 n=7; jail med 2 max 4 n=7; guild med 3 max 7 n=5; temple med 2 max 9 n=5; other med 2 max 3 n=5; inn med 2 max 5 n=4; barracks med 2 max 4 n=4; house med 2 max 2 n=3; bandit_camp med 2 max 2 n=3; fort med 2 max 2 n=2; cellar med 2 max 2 n=1
exterior doors per cell: med 1.0 [p10 0.0, p90 2.0] n=1042

## I. Shell

### dungeon (n=314)
- shell pieces per room med 376.5 [p10 58.0, p90 1001.8] n=314; whole-room-mesh (<=4 shell pieces, one >=900u) 0%; no shell found 0%
- piece types per room (mean): other 241.6, wall 73.5, floor 51.2, corner 31.7, ceiling 22.4, pillar 16.2, loft 15.5, stair 12.0, doorframe 8.7
- kits used (cells): dungeons/caves/green 151; dungeons/nordic/rubble 130; dungeons/nordic/smrooms 100; dungeons/nordic/platforms 94; dungeons/nordic/bgrooms 90; dungeons/nordic/bridges 85
- floor m2 (main level, from shell collision) med 5770.3 [p10 969.5, p90 13341.6] n=309; floors with >=8 m2 med 3.0 [p10 1.0, p90 8.0] n=312; ceiling height u med 330.0 [p10 235.0, p90 580.0] n=16; rectangularity (floor/min bbox) med 20.3 [p10 1.4, p90 1004.5] n=309; aspect med 2.4 [p10 1.2, p90 12.8] n=309
- distinct diffuse textures on shell pieces per room med 22.5 [p10 10.0, p90 41.0] n=314
- share of rooms whose shell textures include: other 100%, stone/brick 95%, earth/mud/clay 75%, timber/plank 67%, metal 65%, hide/cloth 16%, plaster/stucco 3%
- floor pieces (260 rooms) textures per room med 4.0 [p10 1.0, p90 15.0] n=260; materials other 54%, stone/brick 31%, earth/mud/clay 11%, timber/plank 3%
- wall pieces (291 rooms) textures per room med 12.0 [p10 6.0, p90 26.0] n=291; materials other 52%, stone/brick 33%, metal 6%, timber/plank 5%
- ceiling pieces (210 rooms) textures per room med 4.0 [p10 1.0, p90 5.0] n=210; materials stone/brick 45%, other 39%, earth/mud/clay 12%, timber/plank 2%
- built-in features, share of rooms: stairs 70%, loft 46%, alcove 35%, trapdoor 18%, chimney 18%, ladder 6%, wallshelf 4%, window 3%
- light refs med 52.0 [p10 8.0, p90 174.1] n=314

### house (n=219)
- shell pieces per room med 7.0 [p10 1.0, p90 144.8] n=219; whole-room-mesh (<=4 shell pieces, one >=900u) 10%; no shell found 6%
- piece types per room (mean): other 19.7, wall 8.5, floor 8.4, ceiling 3.1, beam 2.8, corner 2.5, doorframe 1.8, pillar 0.9, stair 0.6
- kits used (cells): dlc02/architecture/ravenrock 57; morrowind/sheogorad/dagon fel 44; architecture/farmhouse/interior 35; architecture/whiterun/wrclutter 23; architecture/whiterun/wrinteriors 22; architecture/solitude/interiors 15
- floor m2 (main level, from shell collision) med 171.8 [p10 80.3, p90 871.8] n=201; floors with >=8 m2 med 2.0 [p10 1.0, p90 3.0] n=205; ceiling height u med 250.0 [p10 220.0, p90 412.0] n=80; rectangularity (floor/min bbox) med 1.9 [p10 0.7, p90 9.7] n=201; aspect med 1.5 [p10 1.0, p90 2.6] n=201
- distinct diffuse textures on shell pieces per room med 9.0 [p10 3.0, p90 18.0] n=219
- share of rooms whose shell textures include: other 93%, timber/plank 78%, stone/brick 45%, thatch/reed 44%, metal 23%, earth/mud/clay 19%, plaster/stucco 18%
- floor pieces (73 rooms) textures per room med 2.0 [p10 1.2, p90 5.0] n=73; materials timber/plank 43%, stone/brick 25%, other 21%, earth/mud/clay 11%
- wall pieces (86 rooms) textures per room med 6.0 [p10 3.0, p90 12.0] n=86; materials other 35%, timber/plank 32%, stone/brick 19%, plaster/stucco 6%
- ceiling pieces (39 rooms) textures per room med 6.0 [p10 1.8, p90 9.2] n=39; materials other 45%, timber/plank 41%, plaster/stucco 8%, stone/brick 4%
- built-in features, share of rooms: chimney 57%, window 26%, stairs 26%, wallshelf 25%, alcove 13%, trapdoor 6%, loft 6%, ladder 6%
- light refs med 7.0 [p10 1.0, p90 31.2] n=219

### hall_keep (n=62)
- shell pieces per room med 75.5 [p10 12.1, p90 361.3] n=62; whole-room-mesh (<=4 shell pieces, one >=900u) 2%; no shell found 0%
- piece types per room (mean): other 75.4, wall 21.4, corner 13.6, floor 13.3, doorframe 8.6, ceiling 5.7, pillar 4.4, stair 3.5, loft 2.9
- kits used (cells): architecture/whiterun/wrclutter 15; dlc02/architecture/ravenrock 9; architecture/solitude/interiors 8; dungeons/imperial/tower 6; architecture/farmhouse/interior 6; _byoh/architecture/byohhouse 6
- floor m2 (main level, from shell collision) med 823.4 [p10 173.4, p90 2407.0] n=62; floors with >=8 m2 med 2.0 [p10 1.0, p90 4.9] n=62; ceiling height u med 250.0 [p10 240.0, p90 620.0] n=21; rectangularity (floor/min bbox) med 2.0 [p10 0.8, p90 84.0] n=62; aspect med 1.7 [p10 1.1, p90 4.7] n=62
- distinct diffuse textures on shell pieces per room med 11.5 [p10 7.0, p90 23.0] n=62
- share of rooms whose shell textures include: other 100%, timber/plank 87%, stone/brick 85%, metal 31%, earth/mud/clay 29%, plaster/stucco 24%, thatch/reed 15%
- floor pieces (26 rooms) textures per room med 4.0 [p10 1.5, p90 6.5] n=26; materials stone/brick 34%, timber/plank 31%, other 27%, earth/mud/clay 8%
- wall pieces (48 rooms) textures per room med 5.5 [p10 3.0, p90 12.3] n=48; materials other 41%, stone/brick 24%, timber/plank 24%, earth/mud/clay 4%
- ceiling pieces (14 rooms) textures per room med 4.0 [p10 3.0, p90 5.7] n=14; materials other 37%, stone/brick 27%, timber/plank 27%, metal 3%
- built-in features, share of rooms: chimney 58%, stairs 55%, wallshelf 42%, window 21%, loft 13%, trapdoor 8%, ladder 5%, alcove 5%
- light refs med 27.5 [p10 5.2, p90 68.5] n=62

### inn (n=59)
- shell pieces per room med 19.0 [p10 7.0, p90 147.6] n=59; whole-room-mesh (<=4 shell pieces, one >=900u) 2%; no shell found 0%
- piece types per room (mean): other 17.6, wall 10.4, floor 6.9, corner 4.4, ceiling 1.9, doorframe 1.8, pillar 1.3, stair 1.2, beam 0.9
- kits used (cells): dlc02/architecture/ravenrock 18; architecture/farmhouse/interior 14; morrowind/sheogorad/dagon fel 12; argonia/blackwood 11; argonia/mudhuts 11; morrowind/pancake/platforms 6
- floor m2 (main level, from shell collision) med 417.5 [p10 110.8, p90 876.5] n=59; floors with >=8 m2 med 2.0 [p10 1.0, p90 4.0] n=59; ceiling height u med 245.0 [p10 230.0, p90 344.0] n=24; rectangularity (floor/min bbox) med 1.4 [p10 0.6, p90 7.1] n=59; aspect med 1.7 [p10 1.0, p90 2.8] n=59
- distinct diffuse textures on shell pieces per room med 9.0 [p10 5.8, p90 16.0] n=59
- share of rooms whose shell textures include: other 98%, timber/plank 85%, stone/brick 56%, thatch/reed 36%, metal 25%, plaster/stucco 14%, earth/mud/clay 5%
- floor pieces (16 rooms) textures per room med 2.0 [p10 2.0, p90 4.0] n=16; materials timber/plank 49%, other 28%, stone/brick 21%, earth/mud/clay 3%
- wall pieces (41 rooms) textures per room med 4.0 [p10 3.0, p90 8.0] n=41; materials other 42%, timber/plank 36%, stone/brick 14%, thatch/reed 5%
- built-in features, share of rooms: chimney 66%, stairs 53%, wallshelf 19%, window 14%, trapdoor 10%, ladder 5%, alcove 3%, loft 2%
- light refs med 14.0 [p10 3.0, p90 38.4] n=59

### shop_general (n=53)
- shell pieces per room med 15.0 [p10 3.0, p90 149.0] n=53; whole-room-mesh (<=4 shell pieces, one >=900u) 6%; no shell found 0%
- piece types per room (mean): other 16.7, wall 11.0, floor 7.1, ceiling 4.4, corner 3.6, beam 2.8, loft 2.0, doorframe 1.8, stair 0.9
- kits used (cells): dlc02/architecture/ravenrock 17; argonia/blackwood 11; argonia/mudhuts 9; architecture/whiterun/wrinteriors 9; architecture/riften/interior 6; morrowind/sheogorad/dagon fel 5
- floor m2 (main level, from shell collision) med 231.4 [p10 101.7, p90 708.0] n=53; floors with >=8 m2 med 2.0 [p10 1.0, p90 4.0] n=53; ceiling height u med 280.0 [p10 220.0, p90 676.0] n=23; rectangularity (floor/min bbox) med 1.8 [p10 0.9, p90 53.1] n=53; aspect med 1.7 [p10 1.0, p90 4.0] n=53
- distinct diffuse textures on shell pieces per room med 8.0 [p10 5.0, p90 20.0] n=53
- share of rooms whose shell textures include: other 100%, timber/plank 85%, stone/brick 53%, plaster/stucco 26%, thatch/reed 25%, metal 23%, earth/mud/clay 23%
- floor pieces (19 rooms) textures per room med 2.0 [p10 1.0, p90 6.4] n=19; materials timber/plank 40%, stone/brick 34%, other 13%, earth/mud/clay 11%
- wall pieces (29 rooms) textures per room med 5.0 [p10 1.8, p90 10.4] n=29; materials other 41%, timber/plank 40%, stone/brick 11%, plaster/stucco 5%
- ceiling pieces (11 rooms) textures per room med 8.0 [p10 3.0, p90 9.0] n=11; materials other 44%, timber/plank 41%, plaster/stucco 8%, stone/brick 7%
- built-in features, share of rooms: stairs 53%, chimney 51%, wallshelf 28%, window 26%, ladder 15%, alcove 11%, loft 11%, trapdoor 6%
- light refs med 10.0 [p10 4.0, p90 25.8] n=53

### other (n=45)
- shell pieces per room med 40.0 [p10 1.0, p90 435.6] n=45; whole-room-mesh (<=4 shell pieces, one >=900u) 7%; no shell found 0%
- piece types per room (mean): other 54.8, wall 44.9, floor 36.3, corner 11.0, ceiling 7.2, doorframe 4.9, pillar 3.8, beam 2.8, stair 2.8
- kits used (cells): dlc02/architecture/ravenrock 9; ashlandernewzainab 8; dungeons/caves/green 7; dungeons/mines/scaffolding 6; morrowind/pancake/platforms 5; dungeons/mines/cavepillars 4
- floor m2 (main level, from shell collision) med 569.1 [p10 77.4, p90 7257.8] n=44; floors with >=8 m2 med 3.0 [p10 1.0, p90 9.2] n=45; ceiling height u med 580.0 [p10 256.0, p90 808.0] n=7; rectangularity (floor/min bbox) med 2.3 [p10 0.7, p90 77.4] n=44; aspect med 3.1 [p10 1.2, p90 290.2] n=44
- distinct diffuse textures on shell pieces per room med 12.0 [p10 5.4, p90 25.6] n=45
- share of rooms whose shell textures include: other 96%, timber/plank 69%, stone/brick 58%, earth/mud/clay 38%, metal 38%, hide/cloth 20%, plaster/stucco 9%
- floor pieces (14 rooms) textures per room med 3.0 [p10 2.0, p90 6.0] n=14; materials other 40%, stone/brick 33%, timber/plank 17%, earth/mud/clay 10%
- wall pieces (22 rooms) textures per room med 9.0 [p10 4.0, p90 13.8] n=22; materials other 55%, stone/brick 21%, timber/plank 12%, earth/mud/clay 6%
- ceiling pieces (9 rooms) textures per room med 3.0 [p10 1.0, p90 5.6] n=9; materials other 58%, stone/brick 19%, timber/plank 16%, plaster/stucco 3%
- built-in features, share of rooms: stairs 38%, chimney 24%, trapdoor 11%, wallshelf 7%, alcove 7%, window 7%, loft 7%, ladder 4%
- light refs med 10.0 [p10 3.0, p90 63.2] n=45

### mill_farm (n=41)
- shell pieces per room med 8.0 [p10 2.0, p90 56.0] n=41; whole-room-mesh (<=4 shell pieces, one >=900u) 2%; no shell found 7%
- piece types per room (mean): other 8.8, wall 4.1, floor 3.2, corner 2.4, ceiling 1.0, pillar 0.6, stair 0.6, beam 0.6, doorframe 0.5
- kits used (cells): architecture/farmhouse/interior 13; morrowind/sheogorad/dagon fel 6; morrowind/thanedom/architecture 4; dlc02/architecture/ravenrock 4; architecture/riften/interior 4; architecture/whiterun/wrclutter 4
- floor m2 (main level, from shell collision) med 114.3 [p10 67.7, p90 304.8] n=38; floors with >=8 m2 med 1.0 [p10 1.0, p90 3.0] n=38; ceiling height u med 250.0 [p10 205.0, p90 280.0] n=16; rectangularity (floor/min bbox) med 1.1 [p10 0.7, p90 6.3] n=38; aspect med 1.6 [p10 1.1, p90 2.5] n=38
- distinct diffuse textures on shell pieces per room med 9.0 [p10 1.0, p90 12.0] n=41
- share of rooms whose shell textures include: other 88%, timber/plank 83%, stone/brick 61%, thatch/reed 51%, plaster/stucco 22%, metal 17%, earth/mud/clay 10%
- floor pieces (9 rooms) textures per room med 4.0 [p10 2.0, p90 5.0] n=9; materials timber/plank 49%, stone/brick 34%, other 9%, earth/mud/clay 9%
- wall pieces (23 rooms) textures per room med 6.0 [p10 3.0, p90 8.0] n=23; materials timber/plank 36%, other 34%, stone/brick 17%, thatch/reed 8%
- built-in features, share of rooms: chimney 71%, stairs 34%, wallshelf 32%, window 24%, alcove 7%, trapdoor 5%, ladder 2%
- light refs med 12.0 [p10 1.0, p90 17.0] n=41

### bandit_camp (n=32)
- shell pieces per room med 219.0 [p10 49.4, p90 510.3] n=32; whole-room-mesh (<=4 shell pieces, one >=900u) 0%; no shell found 0%
- piece types per room (mean): other 168.8, wall 38.7, corner 23.3, pillar 21.1, floor 20.2, doorframe 11.4, loft 10.5, ceiling 8.8, stair 6.9
- kits used (cells): dungeons/mines/scaffolding 18; dungeons/imperial/jail 14; dungeons/nordic/rubble 14; dungeons/caves/green 12; dungeons/imperial/smallroom 11; dungeons/imperial/smallhall 11
- floor m2 (main level, from shell collision) med 2919.6 [p10 634.0, p90 8703.3] n=32; floors with >=8 m2 med 3.0 [p10 1.0, p90 5.0] n=32; ceiling height u med 390.0 [p10 308.0, p90 475.0] n=8; rectangularity (floor/min bbox) med 7.3 [p10 1.2, p90 169.3] n=32; aspect med 1.7 [p10 1.0, p90 4.4] n=32
- distinct diffuse textures on shell pieces per room med 14.0 [p10 9.0, p90 30.0] n=32
- share of rooms whose shell textures include: timber/plank 100%, other 100%, stone/brick 97%, earth/mud/clay 91%, metal 59%, thatch/reed 3%, hide/cloth 3%
- floor pieces (26 rooms) textures per room med 3.0 [p10 1.0, p90 6.5] n=26; materials other 38%, earth/mud/clay 29%, stone/brick 22%, timber/plank 11%
- wall pieces (32 rooms) textures per room med 8.0 [p10 6.0, p90 15.0] n=32; materials other 53%, stone/brick 24%, earth/mud/clay 13%, timber/plank 7%
- ceiling pieces (14 rooms) textures per room med 2.0 [p10 1.0, p90 5.4] n=14; materials other 53%, stone/brick 29%, earth/mud/clay 9%, thatch/reed 6%
- built-in features, share of rooms: stairs 59%, trapdoor 25%, loft 25%, ladder 19%, chimney 16%, wallshelf 9%, alcove 9%, window 3%
- light refs med 40.5 [p10 15.2, p90 106.9] n=32

### barracks (n=30)
- shell pieces per room med 21.5 [p10 3.0, p90 335.8] n=30; whole-room-mesh (<=4 shell pieces, one >=900u) 17%; no shell found 3%
- piece types per room (mean): other 56.3, wall 24.5, floor 12.3, corner 7.4, ceiling 5.9, doorframe 4.0, stair 2.7, pillar 2.7, beam 1.3
- kits used (cells): argonia/blackwood 7; argonia/mudhuts 5; dungeons/dwemer/pipes 5; architecture/farmhouse/interior 4; morrowind/sheogorad/dagon fel 3; dungeons/imperial/jail 3
- floor m2 (main level, from shell collision) med 197.4 [p10 111.0, p90 2170.1] n=29; floors with >=8 m2 med 2.0 [p10 1.0, p90 4.0] n=29; ceiling height u med 250.0 [p10 224.0, p90 406.0] n=15; rectangularity (floor/min bbox) med 2.1 [p10 1.0, p90 28.9] n=29; aspect med 1.6 [p10 1.2, p90 3.5] n=29
- distinct diffuse textures on shell pieces per room med 10.5 [p10 5.0, p90 24.9] n=30
- share of rooms whose shell textures include: other 97%, timber/plank 87%, stone/brick 63%, thatch/reed 33%, metal 33%, plaster/stucco 23%, earth/mud/clay 7%
- floor pieces (9 rooms) textures per room med 4.0 [p10 1.0, p90 8.8] n=9; materials stone/brick 41%, other 41%, timber/plank 18%
- wall pieces (21 rooms) textures per room med 3.0 [p10 2.0, p90 19.0] n=21; materials other 45%, timber/plank 23%, stone/brick 23%, metal 4%
- ceiling pieces (7 rooms) textures per room med 4.0 [p10 1.6, p90 6.4] n=7; materials timber/plank 41%, stone/brick 30%, other 26%, earth/mud/clay 4%
- built-in features, share of rooms: chimney 60%, stairs 50%, window 27%, wallshelf 20%, trapdoor 13%, loft 10%, alcove 7%, ladder 3%
- light refs med 10.0 [p10 2.0, p90 42.2] n=30

### temple (n=27)
- shell pieces per room med 65.0 [p10 9.0, p90 145.6] n=27; whole-room-mesh (<=4 shell pieces, one >=900u) 4%; no shell found 0%
- piece types per room (mean): other 35.8, floor 13.9, wall 11.4, corner 6.9, doorframe 4.7, ceiling 4.1, pillar 3.5, stair 1.8, beam 1.1
- kits used (cells): dlc02/architecture/ravenrock 6; morrowind/tesak1243/mwnordhouse 6; morrowind/pancake/ship 6; morrowind/sheogorad/dagon fel 6; architecture/windhelm/interiorkits 3; dungeons/dwemer/platforms 3
- floor m2 (main level, from shell collision) med 522.2 [p10 147.3, p90 1476.8] n=27; floors with >=8 m2 med 2.0 [p10 1.0, p90 4.0] n=27; ceiling height u med 300.0 [p10 218.0, p90 300.0] n=10; rectangularity (floor/min bbox) med 3.4 [p10 0.9, p90 23.8] n=27; aspect med 1.4 [p10 1.2, p90 5.3] n=27
- distinct diffuse textures on shell pieces per room med 12.0 [p10 5.6, p90 19.4] n=27
- share of rooms whose shell textures include: other 100%, timber/plank 70%, stone/brick 59%, metal 52%, earth/mud/clay 22%, plaster/stucco 11%, thatch/reed 7%
- floor pieces (18 rooms) textures per room med 2.0 [p10 1.0, p90 4.0] n=18; materials other 42%, stone/brick 32%, timber/plank 25%
- wall pieces (20 rooms) textures per room med 4.5 [p10 1.0, p90 10.4] n=20; materials stone/brick 36%, other 30%, timber/plank 23%, metal 7%
- ceiling pieces (7 rooms) textures per room med 4.0 [p10 2.6, p90 6.6] n=7; materials timber/plank 57%, other 30%, stone/brick 10%, earth/mud/clay 3%
- built-in features, share of rooms: stairs 67%, wallshelf 37%, alcove 26%, window 19%, chimney 15%, loft 4%
- light refs med 27.0 [p10 3.0, p90 83.8] n=27

### guild (n=25)
- shell pieces per room med 167.0 [p10 12.4, p90 700.8] n=25; whole-room-mesh (<=4 shell pieces, one >=900u) 0%; no shell found 0%
- piece types per room (mean): other 176.5, wall 34.4, corner 20.7, floor 11.4, doorframe 9.5, ceiling 8.4, pillar 6.2, stair 4.0, beam 1.3
- kits used (cells): architecture/solitude/interiors 7; architecture/whiterun/wrclutter 7; architecture/winterhold 6; dlc02/architecture/ravenrock 4; dungeons/ship/questitems 3; dungeons/riften/ratwayhall 3
- floor m2 (main level, from shell collision) med 878.4 [p10 365.2, p90 5306.9] n=25; floors with >=8 m2 med 2.0 [p10 1.0, p90 5.0] n=25; ceiling height u med 350.0 [p10 255.0, p90 675.0] n=6; rectangularity (floor/min bbox) med 2.1 [p10 0.8, p90 185.0] n=25; aspect med 1.4 [p10 1.0, p90 4.9] n=25
- distinct diffuse textures on shell pieces per room med 14.0 [p10 4.8, p90 25.0] n=25
- share of rooms whose shell textures include: other 100%, timber/plank 64%, stone/brick 60%, earth/mud/clay 36%, metal 36%, plaster/stucco 28%
- floor pieces (9 rooms) textures per room med 2.0 [p10 1.0, p90 6.0] n=9; materials other 53%, stone/brick 20%, timber/plank 17%, earth/mud/clay 10%
- wall pieces (19 rooms) textures per room med 5.0 [p10 3.0, p90 14.4] n=19; materials other 65%, stone/brick 13%, timber/plank 10%, earth/mud/clay 6%
- ceiling pieces (8 rooms) textures per room med 4.0 [p10 1.7, p90 5.0] n=8; materials other 37%, stone/brick 26%, timber/plank 19%, earth/mud/clay 19%
- built-in features, share of rooms: wallshelf 56%, stairs 48%, chimney 32%, window 28%, trapdoor 20%, alcove 16%, loft 16%, ladder 8%
- light refs med 29.0 [p10 11.8, p90 113.4] n=25

### fort (n=24)
- shell pieces per room med 67.0 [p10 10.7, p90 115.7] n=24; whole-room-mesh (<=4 shell pieces, one >=900u) 0%; no shell found 0%
- piece types per room (mean): other 28.2, wall 14.7, doorframe 8.3, corner 8.1, pillar 3.8, floor 3.5, stair 2.6, ceiling 1.8, hearth 0.0
- kits used (cells): dungeons/imperial/smallhall 19; dungeons/imperial/exterior 15; dungeons/imperial/smallroom 15; dungeons/imperial/largeroom 14; dungeons/imperial/tower 13; dungeons/imperial/largehall 12
- floor m2 (main level, from shell collision) med 928.5 [p10 226.3, p90 2172.1] n=24; floors with >=8 m2 med 2.0 [p10 1.0, p90 3.0] n=24; ceiling height u med 485.0 [p10 384.0, p90 794.0] n=8; rectangularity (floor/min bbox) med 8.0 [p10 1.3, p90 354.1] n=24; aspect med 1.8 [p10 1.1, p90 7.2] n=24
- distinct diffuse textures on shell pieces per room med 11.0 [p10 8.0, p90 20.4] n=24
- share of rooms whose shell textures include: timber/plank 100%, other 100%, earth/mud/clay 96%, stone/brick 92%, metal 50%, thatch/reed 4%
- floor pieces (12 rooms) textures per room med 6.0 [p10 6.0, p90 7.0] n=12; materials other 39%, earth/mud/clay 31%, stone/brick 15%, timber/plank 15%
- wall pieces (21 rooms) textures per room med 8.0 [p10 5.0, p90 14.0] n=21; materials other 56%, earth/mud/clay 22%, timber/plank 10%, stone/brick 10%
- ceiling pieces (5 rooms) textures per room med 1.0 [p10 1.0, p90 1.6] n=5; materials other 100%
- built-in features, share of rooms: stairs 92%, chimney 54%, trapdoor 54%, ladder 54%, window 8%
- light refs med 24.5 [p10 15.0, p90 60.9] n=24

### mine (n=21)
- shell pieces per room med 118.0 [p10 52.0, p90 313.0] n=21; whole-room-mesh (<=4 shell pieces, one >=900u) 0%; no shell found 0%
- piece types per room (mean): other 127.9, wall 11.2, pillar 8.2, corner 7.1, doorframe 5.1, floor 4.7, stair 3.2, ceiling 2.2, loft 0.6
- kits used (cells): dungeons/mines/scaffolding 18; dungeons/mines/rocks 16; dungeons/mines/minelargehall 15; dungeons/mines/cavepillars 13; dungeons/mines/cavewall 11; dungeons/mines/cliffs 10
- floor m2 (main level, from shell collision) med 2092.4 [p10 457.1, p90 4042.4] n=21; floors with >=8 m2 med 3.0 [p10 1.0, p90 5.0] n=21; ceiling height u n=0; rectangularity (floor/min bbox) med 29.1 [p10 3.2, p90 370.5] n=21; aspect med 2.7 [p10 1.1, p90 9.4] n=21
- distinct diffuse textures on shell pieces per room med 12.0 [p10 9.0, p90 18.0] n=21
- share of rooms whose shell textures include: other 100%, timber/plank 95%, stone/brick 90%, earth/mud/clay 81%, metal 29%, thatch/reed 5%, hide/cloth 5%
- floor pieces (7 rooms) textures per room med 2.0 [p10 1.0, p90 3.8] n=7; materials other 40%, stone/brick 27%, earth/mud/clay 27%, timber/plank 7%
- wall pieces (19 rooms) textures per room med 6.0 [p10 3.6, p90 7.0] n=19; materials stone/brick 49%, other 36%, earth/mud/clay 12%, metal 2%
- ceiling pieces (4 rooms) textures per room med 1.5 [p10 1.0, p90 4.1] n=4; materials stone/brick 56%, other 33%, earth/mud/clay 11%
- built-in features, share of rooms: loft 24%, stairs 14%, alcove 10%, trapdoor 5%, ladder 5%
- light refs med 23.0 [p10 12.0, p90 54.0] n=21

### warehouse (n=15)
- shell pieces per room med 2.0 [p10 1.0, p90 70.2] n=15; whole-room-mesh (<=4 shell pieces, one >=900u) 13%; no shell found 0%
- piece types per room (mean): other 11.6, wall 3.7, ceiling 2.4, floor 2.3, corner 1.0, doorframe 0.4, stair 0.4, beam 0.4, hearth 0.2
- kits used (cells): morrowind/sheogorad/dagon fel 6; dlc02/architecture/ravenrock 3; argonia/blackwood 2; argonia/xanmeer/interior 2; argonia/mudhuts 2; architecture/whiterun/wrinteriors 2
- floor m2 (main level, from shell collision) med 159.2 [p10 45.9, p90 339.4] n=15; floors with >=8 m2 med 2.0 [p10 1.0, p90 4.0] n=15; ceiling height u med 410.0 [p10 230.0, p90 560.0] n=12; rectangularity (floor/min bbox) med 2.2 [p10 1.3, p90 2.7] n=15; aspect med 1.2 [p10 1.1, p90 2.4] n=15
- distinct diffuse textures on shell pieces per room med 7.0 [p10 6.0, p90 12.8] n=15
- share of rooms whose shell textures include: other 100%, timber/plank 93%, thatch/reed 53%, plaster/stucco 53%, stone/brick 47%, metal 13%, earth/mud/clay 7%
- wall pieces (6 rooms) textures per room med 5.0 [p10 2.5, p90 7.5] n=6; materials stone/brick 30%, other 30%, timber/plank 30%, plaster/stucco 7%
- built-in features, share of rooms: chimney 47%, window 27%, stairs 27%, wallshelf 13%, trapdoor 7%, alcove 7%
- light refs med 4.0 [p10 0.0, p90 14.6] n=15

### alchemist (n=15)
- shell pieces per room med 20.0 [p10 3.0, p90 140.8] n=15; whole-room-mesh (<=4 shell pieces, one >=900u) 7%; no shell found 0%
- piece types per room (mean): other 20.9, wall 8.2, floor 5.3, ceiling 3.3, corner 2.2, beam 1.4, doorframe 1.4, loft 1.3, stair 1.1
- kits used (cells): argonia/blackwood 3; dlc02/architecture/ravenrock 3; architecture/whiterun/wrclutter 3; morrowind/pancake/platforms 2; architecture/riften/interior 2; architecture/solitude/interiors 2
- floor m2 (main level, from shell collision) med 189.8 [p10 74.1, p90 627.3] n=15; floors with >=8 m2 med 2.0 [p10 1.0, p90 2.6] n=15; ceiling height u med 275.0 [p10 186.0, p90 679.0] n=4; rectangularity (floor/min bbox) med 1.7 [p10 0.8, p90 2.7] n=15; aspect med 1.4 [p10 1.1, p90 2.4] n=15
- distinct diffuse textures on shell pieces per room med 10.0 [p10 6.0, p90 18.0] n=15
- share of rooms whose shell textures include: other 100%, timber/plank 87%, stone/brick 67%, earth/mud/clay 27%, plaster/stucco 27%, metal 13%, thatch/reed 13%
- floor pieces (5 rooms) textures per room med 2.0 [p10 1.4, p90 4.6] n=5; materials stone/brick 43%, other 29%, timber/plank 21%, earth/mud/clay 7%
- wall pieces (11 rooms) textures per room med 3.0 [p10 2.0, p90 8.0] n=11; materials other 39%, stone/brick 25%, timber/plank 23%, earth/mud/clay 4%
- built-in features, share of rooms: chimney 53%, wallshelf 33%, stairs 33%, trapdoor 20%, window 20%, loft 13%, ladder 13%, alcove 7%
- light refs med 10.0 [p10 2.6, p90 27.6] n=15

### cellar (n=14)
- shell pieces per room med 63.5 [p10 10.9, p90 297.3] n=14; whole-room-mesh (<=4 shell pieces, one >=900u) 0%; no shell found 0%
- piece types per room (mean): other 59.6, floor 25.1, wall 14.1, ceiling 10.9, corner 10.6, doorframe 8.5, beam 3.4, stair 2.2, pillar 1.5
- kits used (cells): dungeons/caves/green 4; architecture/riften/interior 4; architecture/whiterun/wrinteriors 4; _byoh/architecture/byohhouse 3; morrowind/sheogorad/dagon fel 2; architecture/windhelm/interiorkits 2
- floor m2 (main level, from shell collision) med 290.4 [p10 119.9, p90 2000.3] n=14; floors with >=8 m2 med 2.0 [p10 1.0, p90 3.0] n=14; ceiling height u med 250.0 [p10 228.0, p90 586.0] n=9; rectangularity (floor/min bbox) med 1.4 [p10 1.0, p90 389.6] n=14; aspect med 1.8 [p10 1.2, p90 8.2] n=14
- distinct diffuse textures on shell pieces per room med 8.5 [p10 4.6, p90 25.9] n=14
- share of rooms whose shell textures include: other 93%, timber/plank 86%, stone/brick 71%, earth/mud/clay 36%, thatch/reed 21%, plaster/stucco 21%, metal 21%
- floor pieces (10 rooms) textures per room med 1.5 [p10 1.0, p90 11.0] n=10; materials other 40%, stone/brick 31%, timber/plank 14%, earth/mud/clay 14%
- wall pieces (12 rooms) textures per room med 6.0 [p10 3.1, p90 12.7] n=12; materials other 40%, timber/plank 29%, stone/brick 18%, earth/mud/clay 9%
- ceiling pieces (7 rooms) textures per room med 2.0 [p10 1.0, p90 7.2] n=7; materials other 39%, stone/brick 30%, timber/plank 17%, earth/mud/clay 13%
- built-in features, share of rooms: trapdoor 71%, wallshelf 36%, stairs 36%, ladder 21%
- light refs med 17.0 [p10 3.3, p90 53.4] n=14

### jail (n=14)
- shell pieces per room med 75.5 [p10 40.6, p90 374.3] n=14; whole-room-mesh (<=4 shell pieces, one >=900u) 0%; no shell found 0%
- piece types per room (mean): other 82.4, wall 18.4, corner 12.4, doorframe 12.1, floor 11.9, pillar 8.1, beam 6.8, ceiling 6.6, stair 1.8
- kits used (cells): architecture/markarth 6; dungeons/imperial/jail 6; dungeons/caves/green 4; architecture/farmhouse/interior 3; dungeons/mines/scaffolding 3; architecture/solitude/interiors 2
- floor m2 (main level, from shell collision) med 494.9 [p10 262.6, p90 2301.2] n=14; floors with >=8 m2 med 3.0 [p10 1.3, p90 5.7] n=14; ceiling height u med 255.0 [p10 230.0, p90 532.0] n=8; rectangularity (floor/min bbox) med 14.1 [p10 0.9, p90 559.9] n=14; aspect med 2.2 [p10 1.3, p90 6.7] n=14
- distinct diffuse textures on shell pieces per room med 18.5 [p10 7.3, p90 40.6] n=14
- share of rooms whose shell textures include: stone/brick 100%, other 100%, timber/plank 93%, metal 71%, earth/mud/clay 50%, plaster/stucco 21%
- floor pieces (7 rooms) textures per room med 2.0 [p10 1.6, p90 6.4] n=7; materials stone/brick 38%, other 35%, timber/plank 19%, earth/mud/clay 8%
- wall pieces (14 rooms) textures per room med 6.0 [p10 1.0, p90 11.0] n=14; materials other 47%, stone/brick 22%, timber/plank 16%, earth/mud/clay 8%
- ceiling pieces (4 rooms) textures per room med 3.5 [p10 2.3, p90 5.4] n=4; materials stone/brick 33%, timber/plank 27%, other 27%, earth/mud/clay 13%
- built-in features, share of rooms: stairs 36%, loft 21%, wallshelf 21%, trapdoor 14%, chimney 14%, alcove 7%, window 7%
- light refs med 16.0 [p10 7.5, p90 91.9] n=14

### ship (n=12)
- shell pieces per room med 23.0 [p10 3.2, p90 66.9] n=12; whole-room-mesh (<=4 shell pieces, one >=900u) 8%; no shell found 0%
- piece types per room (mean): beam 51.4, floor 40.0, wall 29.7, other 12.0, pillar 2.5, stair 0.7, doorframe 0.4, window 0.4, shelf 0.2
- kits used (cells): aaaship/interiors 4; aaaship/interiors/extlights 3; aaaship 3; dungeons/ship/katariah 2; argonia/stockades 2; argonia/tradeship 2
- floor m2 (main level, from shell collision) med 456.4 [p10 63.4, p90 1224.5] n=8; floors with >=8 m2 med 2.0 [p10 1.6, p90 4.0] n=9; ceiling height u med 290.0 [p10 273.0, p90 503.0] n=4; rectangularity (floor/min bbox) med 5.5 [p10 1.6, p90 23.0] n=8; aspect med 4.5 [p10 1.6, p90 54.5] n=8
- distinct diffuse textures on shell pieces per room med 6.0 [p10 0.0, p90 7.9] n=12
- share of rooms whose shell textures include: timber/plank 75%, other 67%, metal 33%
- floor pieces (6 rooms) textures per room med 2.0 [p10 1.0, p90 2.0] n=6; materials timber/plank 70%, other 30%
- built-in features, share of rooms: wallshelf 33%, trapdoor 33%, stairs 33%, window 25%, chimney 17%
- light refs med 6.0 [p10 0.1, p90 41.6] n=12

### smith (n=12)
- shell pieces per room med 36.5 [p10 7.5, p90 71.4] n=12; whole-room-mesh (<=4 shell pieces, one >=900u) 0%; no shell found 0%
- piece types per room (mean): other 14.8, wall 11.4, floor 5.2, corner 3.1, stair 1.2, doorframe 1.2, hearth 0.8, beam 0.8, trap 0.1
- kits used (cells): argonia/blackwood 6; argonia/mudhuts 5; dungeons/dwemer/pipes 3; morrowind/rootspire 2; dlc02/architecture/ravenrock 2; morrowind/ruins 2
- floor m2 (main level, from shell collision) med 376.7 [p10 180.2, p90 454.5] n=11; floors with >=8 m2 med 2.0 [p10 1.0, p90 3.9] n=12; ceiling height u med 280.0 [p10 250.0, p90 478.0] n=4; rectangularity (floor/min bbox) med 2.7 [p10 1.0, p90 454.5] n=11; aspect med 1.9 [p10 1.0, p90 2.7] n=11
- distinct diffuse textures on shell pieces per room med 10.0 [p10 6.1, p90 12.9] n=12
- share of rooms whose shell textures include: other 100%, timber/plank 92%, stone/brick 58%, metal 42%, thatch/reed 25%, plaster/stucco 25%, earth/mud/clay 8%
- floor pieces (4 rooms) textures per room med 2.0 [p10 1.3, p90 3.4] n=4; materials timber/plank 44%, stone/brick 33%, other 22%
- wall pieces (11 rooms) textures per room med 3.0 [p10 2.0, p90 7.0] n=11; materials other 52%, timber/plank 34%, stone/brick 7%, earth/mud/clay 2%
- built-in features, share of rooms: chimney 83%, stairs 58%, wallshelf 25%, window 17%, trapdoor 8%
- light refs med 11.0 [p10 4.1, p90 19.8] n=12

### clothier (n=4)
- shell pieces per room med 28.0 [p10 9.6, p90 129.0] n=4; whole-room-mesh (<=4 shell pieces, one >=900u) 25%; no shell found 0%
- piece types per room (mean): other 34.5, wall 7.0, floor 5.8, corner 4.8, doorframe 3.2, beam 1.5, stair 0.5, hearth 0.2
- kits used (cells): dlc02/architecture/ravenrock 3; morrowind/pancake/platforms 1; architecture/riften/interior 1; morrowind/tesak1243/mwnordhouse 1; morrowind/ruins 1; morrowind/sheogorad/dagon fel 1
- floor m2 (main level, from shell collision) med 401.3 [p10 203.9, p90 549.0] n=4; floors with >=8 m2 med 1.5 [p10 1.0, p90 3.4] n=4; ceiling height u med 285.0 [p10 226.0, p90 694.0] n=4; rectangularity (floor/min bbox) med 4.9 [p10 2.7, p90 111.8] n=4; aspect med 1.8 [p10 1.5, p90 34.3] n=4
- distinct diffuse textures on shell pieces per room med 11.5 [p10 8.2, p90 14.8] n=4
- share of rooms whose shell textures include: timber/plank 100%, other 100%, plaster/stucco 50%, stone/brick 50%, metal 25%, thatch/reed 25%
- built-in features, share of rooms: stairs 50%, trapdoor 25%, ladder 25%, chimney 25%, window 25%, wallshelf 25%
- light refs med 11.0 [p10 7.5, p90 41.8] n=4

### shell by wealth (house/inn/shop/hall pooled)
- poor n=46: floor m2 med 177.0 [p10 101.0, p90 626.2] n=46; ceil u med 240.0 [p10 190.0, p90 330.0] n=16; textures/room med 6.5 [p10 3.0, p90 11.0] n=46; materials timber/plank 98%, other 98%, stone/brick 39%, thatch/reed 37%, earth/mud/clay 15%, metal 11%
- mid n=239: floor m2 med 183.4 [p10 81.1, p90 829.0] n=223; ceil u med 240.0 [p10 220.0, p90 412.0] n=90; textures/room med 9.0 [p10 4.0, p90 17.2] n=239; materials other 94%, timber/plank 76%, stone/brick 47%, thatch/reed 40%, metal 28%, plaster/stucco 18%
- rich n=54: floor m2 med 851.0 [p10 244.1, p90 2034.7] n=54; ceil u med 260.0 [p10 240.0, p90 740.0] n=29; textures/room med 13.0 [p10 9.0, p90 23.0] n=54; materials other 100%, stone/brick 94%, timber/plank 91%, plaster/stucco 48%, earth/mud/clay 31%, metal 20%
- mixed n=27: floor m2 med 454.7 [p10 80.3, p90 1174.3] n=27; ceil u med 300.0 [p10 288.0, p90 446.0] n=5; textures/room med 11.0 [p10 4.0, p90 20.0] n=27; materials other 100%, timber/plank 85%, stone/brick 70%, thatch/reed 59%, metal 22%, earth/mud/clay 22%

### kit -> interior kinds that use it (cells)
- dungeons/caves/green: 202 cells; dungeon 151, bandit_camp 12, other 7, house 6, jail 4
- dungeons/nordic/rubble: 161 cells; dungeon 130, bandit_camp 14, other 3, mine 3, fort 3
- dlc02/architecture/ravenrock: 153 cells; house 57, inn 18, shop_general 17, dungeon 11, other 9
- dungeons/mines/scaffolding: 132 cells; dungeon 63, mine 18, bandit_camp 18, fort 7, other 6
- dungeons/nordic/smrooms: 110 cells; dungeon 100, bandit_camp 5, temple 1, hall_keep 1, mine 1
- dungeons/nordic/platforms: 100 cells; dungeon 94, bandit_camp 2, temple 1, mine 1, other 1
- morrowind/sheogorad/dagon fel: 99 cells; house 44, inn 12, warehouse 6, mill_farm 6, temple 6
- dungeons/nordic/bgrooms: 99 cells; dungeon 90, temple 3, bandit_camp 3, mine 1, other 1
- dungeons/nordic/bridges: 95 cells; dungeon 85, bandit_camp 4, temple 1, house 1, cellar 1
- dungeons/nordic/bghalls: 95 cells; dungeon 85, bandit_camp 5, jail 1, temple 1, mine 1
- dungeons/mines/rocks: 92 cells; dungeon 53, mine 16, bandit_camp 10, hall_keep 3, other 3
- architecture/farmhouse/interior: 89 cells; house 35, inn 14, mill_farm 13, hall_keep 6, shop_general 5
- dungeons/nordic: 88 cells; dungeon 82, bandit_camp 3, temple 1, mine 1, other 1
- dungeons/nordic/smhalls: 87 cells; dungeon 81, bandit_camp 3, mine 1, other 1, guild 1
- dungeons/dwemer: 86 cells; dungeon 64, house 5, temple 3, hall_keep 3, barracks 3
- dungeons/dwemer/pipes: 86 cells; dungeon 62, barracks 5, inn 4, smith 3, other 2
- dungeons/nordic/shafts: 86 cells; dungeon 74, bandit_camp 6, cellar 2, guild 2, jail 1
- architecture/whiterun/wrclutter: 81 cells; house 23, hall_keep 15, guild 7, dungeon 6, shop_general 5
- dungeons/imperial/jail: 80 cells; dungeon 28, bandit_camp 14, fort 11, jail 6, other 3
- dungeons/dwemer/rubble: 79 cells; dungeon 60, house 5, other 3, barracks 3, temple 2
- dungeons/dwemer/facades: 79 cells; dungeon 56, house 6, temple 3, hall_keep 3, barracks 3
- dungeons/nordic/pits: 76 cells; dungeon 71, bandit_camp 2, mine 1, other 1, guild 1
- dungeons/dwemer/platforms: 73 cells; dungeon 50, house 6, hall_keep 5, temple 3, barracks 3
- dungeons/imperial/exterior: 73 cells; dungeon 39, fort 15, bandit_camp 9, hall_keep 4, other 2
- dungeons/dwemer/smrooms: 72 cells; dungeon 48, house 6, temple 3, hall_keep 3, barracks 3
- dungeons/mines/cavepillars: 70 cells; dungeon 43, mine 13, bandit_camp 8, other 4, jail 2
- architecture/whiterun/wrinteriors: 66 cells; house 22, shop_general 9, dungeon 9, cellar 4, mill_farm 3
- dungeons/dwemer/partitions: 64 cells; dungeon 58, barracks 2, temple 1, house 1, other 1
- dungeons/dwemer/lgrooms: 64 cells; dungeon 50, barracks 3, other 2, temple 2, bandit_camp 1
- dungeons/imperial/smallhall: 64 cells; dungeon 28, fort 19, bandit_camp 11, hall_keep 3, jail 2
- dungeons/dwemer/walls: 64 cells; dungeon 45, house 6, barracks 3, temple 2, hall_keep 2
- dungeons/mines/cavewall: 62 cells; dungeon 39, mine 11, bandit_camp 8, jail 2, house 1
- argonia/blackwood: 61 cells; house 11, shop_general 11, inn 11, barracks 7, smith 6
- architecture/markarth: 59 cells; dungeon 28, fort 7, jail 6, hall_keep 5, mine 2
- dungeons/imperial/tower: 58 cells; dungeon 21, fort 13, bandit_camp 10, hall_keep 6, other 3
- dungeons/imperial/smallroom: 58 cells; dungeon 27, fort 15, bandit_camp 11, hall_keep 3, jail 1
- argonia/mudhuts: 57 cells; house 12, inn 11, shop_general 9, dungeon 6, smith 5
- dungeons/nordic/chambers: 57 cells; dungeon 54, bandit_camp 2, guild 1
- architecture/solitude/interiors: 55 cells; house 15, hall_keep 8, guild 7, dungeon 4, mill_farm 3
- dungeons/nordic/catacombs: 55 cells; dungeon 51, temple 1, bandit_camp 1, mine 1, other 1
- dungeons/imperial/largeroom: 52 cells; dungeon 23, fort 14, bandit_camp 9, house 2, hall_keep 2
- architecture/riften/interior: 51 cells; house 14, shop_general 6, hall_keep 5, mill_farm 4, cellar 4
- dungeons/caves/ice: 51 cells; dungeon 38, guild 3, other 2, mine 2, jail 1
- dungeons/mines/cavelargeroom: 49 cells; dungeon 30, mine 10, bandit_camp 6, house 1, jail 1
- dungeons/dwemer/lghalls: 48 cells; dungeon 39, barracks 3, temple 1, alchemist 1, house 1
# APPENDIX B: section 5 completed
# SECTION 5 COMPLETED: the former "not measured" items, now measured

Run: stage3 over 654 non-dungeon cells (0 errors); navmesh area for 1152 cells. u = game units, 70u = 1 m.

## 5.1 Ceiling height: ray cast up from the shell's real floor triangles to the first shell triangle
Method: visual triangles of every shell piece (nifdump), floor sample points = up-facing triangles within 30u of the main floor level (level = commonest floor-furniture z), up to 60 points area-weighted, first triangle above floor+90u. Sloped roofs/attics mean the cast gives the first surface, so the p10 (lowest) is the eave/wall-plate height and p90 the ridge.
- house: cells with a cast 194 of 220; median ceiling med 262 [p10 195, p90 408] n=194u; per-cell low point (p10 of points) med 197 [p10 138, p90 254] n=194u; high point (p90) med 396 [p10 227, p90 587] n=194u; share of floor points that hit anything 94%
- inn: cells with a cast 59 of 59; median ceiling med 261 [p10 192, p90 438] n=59u; per-cell low point (p10 of points) med 210 [p10 116, p90 251] n=59u; high point (p90) med 470 [p10 239, p90 770] n=59u; share of floor points that hit anything 95%
- hall_keep: cells with a cast 56 of 63; median ceiling med 327 [p10 252, p90 468] n=56u; per-cell low point (p10 of points) med 211 [p10 164, p90 320] n=56u; high point (p90) med 465 [p10 260, p90 740] n=56u; share of floor points that hit anything 92%
- shop_general: cells with a cast 52 of 53; median ceiling med 302 [p10 218, p90 549] n=52u; per-cell low point (p10 of points) med 218 [p10 149, p90 269] n=52u; high point (p90) med 407 [p10 232, p90 689] n=52u; share of floor points that hit anything 95%
- mill_farm: cells with a cast 38 of 41; median ceiling med 302 [p10 220, p90 381] n=38u; per-cell low point (p10 of points) med 212 [p10 126, p90 250] n=38u; high point (p90) med 391 [p10 236, p90 497] n=38u; share of floor points that hit anything 90%
- barracks: cells with a cast 27 of 30; median ceiling med 253 [p10 194, p90 399] n=27u; per-cell low point (p10 of points) med 184 [p10 111, p90 250] n=27u; high point (p90) med 412 [p10 249, p90 665] n=27u; share of floor points that hit anything 90%
- temple: cells with a cast 26 of 27; median ceiling med 286 [p10 228, p90 596] n=26u; per-cell low point (p10 of points) med 230 [p10 143, p90 277] n=26u; high point (p90) med 362 [p10 234, p90 1013] n=26u; share of floor points that hit anything 84%
- fort: cells with a cast 23 of 24; median ceiling med 388 [p10 308, p90 448] n=23u; per-cell low point (p10 of points) med 291 [p10 235, p90 346] n=23u; high point (p90) med 432 [p10 334, p90 688] n=23u; share of floor points that hit anything 98%
- mine: cells with a cast 19 of 21; median ceiling med 257 [p10 236, p90 501] n=19u; per-cell low point (p10 of points) med 164 [p10 129, p90 212] n=19u; high point (p90) med 456 [p10 252, p90 1141] n=19u; share of floor points that hit anything 93%
- guild: cells with a cast 16 of 25; median ceiling med 337 [p10 253, p90 704] n=16u; per-cell low point (p10 of points) med 226 [p10 179, p90 503] n=16u; high point (p90) med 568 [p10 341, p90 817] n=16u; share of floor points that hit anything 99%
- alchemist: cells with a cast 15 of 15; median ceiling med 278 [p10 225, p90 514] n=15u; per-cell low point (p10 of points) med 242 [p10 193, p90 262] n=15u; high point (p90) med 551 [p10 255, p90 881] n=15u; share of floor points that hit anything 89%
- warehouse: cells with a cast 14 of 15; median ceiling med 313 [p10 227, p90 385] n=14u; per-cell low point (p10 of points) med 117 [p10 113, p90 235] n=14u; high point (p90) med 460 [p10 309, p90 662] n=14u; share of floor points that hit anything 97%
- cellar: cells with a cast 12 of 14; median ceiling med 239 [p10 204, p90 252] n=12u; per-cell low point (p10 of points) med 213 [p10 129, p90 250] n=12u; high point (p90) med 251 [p10 209, p90 255] n=12u; share of floor points that hit anything 98%
- smith: cells with a cast 12 of 12; median ceiling med 260 [p10 198, p90 353] n=12u; per-cell low point (p10 of points) med 198 [p10 122, p90 283] n=12u; high point (p90) med 392 [p10 232, p90 623] n=12u; share of floor points that hit anything 87%
- jail: cells with a cast 12 of 14; median ceiling med 297 [p10 230, p90 454] n=12u; per-cell low point (p10 of points) med 222 [p10 196, p90 353] n=12u; high point (p90) med 344 [p10 230, p90 951] n=12u; share of floor points that hit anything 95%
- ship: cells with a cast 7 of 13; median ceiling med 225 [p10 194, p90 377] n=7u; per-cell low point (p10 of points) med 198 [p10 164, p90 367] n=7u; high point (p90) med 251 [p10 229, p90 413] n=7u; share of floor points that hit anything 88%
- clothier: cells with a cast 4 of 4; median ceiling med 251 [p10 228, p90 283] n=4u; per-cell low point (p10 of points) med 238 [p10 219, p90 246] n=4u; high point (p90) med 327 [p10 278, p90 788] n=4u; share of floor points that hit anything 100%
- camp_tent: cells with a cast 3 of 3; median ceiling med 204 [p10 204, p90 211] n=3u; per-cell low point (p10 of points) med 148 [p10 148, p90 178] n=3u; high point (p90) med 272 [p10 272, p90 294] n=3u; share of floor points that hit anything 47%

By wealth (house, inn, shop_general, hall_keep pooled):
- poor: median ceiling med 239 [p10 188, p90 388] n=45u; low point med 185 [p10 116, p90 215] n=45u
- mid: median ceiling med 299 [p10 223, p90 417] n=221u; low point med 212 [p10 143, p90 269] n=221u
- rich: median ceiling med 266 [p10 250, p90 500] n=44u; low point med 235 [p10 189, p90 271] n=44u
- mixed: median ceiling med 298 [p10 195, p90 456] n=26u; low point med 188 [p10 114, p90 249] n=26u

Cells whose shell gave no cast at all (no up-facing floor at furniture level, >400 pieces, or no visual mesh): 64 of 654

## 5.2 Shelf levels: levels from the shelf mesh's own up-facing surfaces (area >=35% of the largest); filled = a level holding any small thing
Shelf-like = shelf/bookcase, cupboard, dresser, wardrobe, sidetable. Level of an item = highest level whose surface is <= item base + 10u.
- shelf: n=2994 shelves; levels med 3 [p10 1, p90 4] n=2994; levels filled med 2 [p10 0, p90 3] n=2994; share of levels filled 58%; shelves with nothing 25%; contents tableware 21%, book 17%, food 15%, drink 11%, ingredient 8%, vessel 5%
- sidetable: n=839 shelves; levels med 1 [p10 1, p90 2] n=839; levels filled med 1 [p10 0, p90 1] n=839; share of levels filled 65%; shelves with nothing 31%; contents tableware 32%, drink 15%, book 11%, food 10%, ingredient 7%, vessel 5%
- cupboard: n=611 shelves; levels med 2 [p10 2, p90 3] n=611; levels filled med 1 [p10 0, p90 2] n=611; share of levels filled 47%; shelves with nothing 18%; contents tableware 41%, food 12%, drink 10%, tool 9%, vessel 5%, ingredient 4%
- dresser: n=561 shelves; levels med 1 [p10 1, p90 2] n=561; levels filled med 1 [p10 0, p90 1] n=561; share of levels filled 57%; shelves with nothing 30%; contents tableware 25%, ingredient 12%, book 9%, food 8%, drink 7%, valuable 7%
- wardrobe: n=354 shelves; levels med 2 [p10 2, p90 2] n=354; levels filled med 0 [p10 0, p90 1] n=354; share of levels filled 11%; shelves with nothing 78%; contents vessel 35%, tableware 14%, apparel 8%, ingredient 8%, food 6%, tool 6%

By kind (shelf + cupboard + bookcase pooled): share of levels filled | items per filled level | commonest content
- house (n=964 shelves): levels/shelf 2.8; levels filled 54%; items per filled level med 3 [p10 1, p90 7] n=1464; tableware 29%, food 17%, book 15%, drink 9%
- hall_keep (n=784 shelves): levels/shelf 2.6; levels filled 45%; items per filled level med 3 [p10 1, p90 7] n=901; tableware 23%, book 18%, food 14%, drink 13%
- inn (n=238 shelves): levels/shelf 2.9; levels filled 64%; items per filled level med 4 [p10 1, p90 8] n=442; drink 27%, tableware 23%, food 16%, vessel 9%
- shop_general (n=232 shelves): levels/shelf 2.8; levels filled 68%; items per filled level med 3 [p10 1, p90 9] n=441; tableware 24%, book 18%, food 17%, drink 9%
- mill_farm (n=120 shelves): levels/shelf 2.7; levels filled 68%; items per filled level med 4 [p10 1, p90 8] n=219; tableware 27%, food 25%, book 10%, drink 9%
- barracks (n=193 shelves): levels/shelf 2.2; levels filled 51%; items per filled level med 3 [p10 1, p90 6] n=217; tableware 22%, food 17%, book 15%, drink 13%
- temple (n=100 shelves): levels/shelf 2.5; levels filled 60%; items per filled level med 4 [p10 1, p90 7] n=152; tableware 27%, book 21%, food 10%, vessel 9%
- guild (n=404 shelves): levels/shelf 3.1; levels filled 52%; items per filled level med 3 [p10 1, p90 6] n=659; book 20%, tableware 15%, ingredient 14%, drink 10%
- fort (n=156 shelves): levels/shelf 3.5; levels filled 67%; items per filled level med 3 [p10 1, p90 7] n=367; tableware 32%, apparel 15%, book 13%, misc_other 12%
- mine (n=20 shelves): levels/shelf 3.4; levels filled 41%; items per filled level med 3 [p10 1, p90 5] n=28; apparel 15%, tableware 11%, potion 10%, drink 10%
- warehouse (n=34 shelves): levels/shelf 2.6; levels filled 64%; items per filled level med 3 [p10 2, p90 7] n=58; food 37%, tableware 27%, tool 8%, drink 8%
- alchemist (n=72 shelves): levels/shelf 3.0; levels filled 75%; items per filled level med 3 [p10 1, p90 8] n=162; ingredient 30%, tableware 16%, potion 15%, food 14%
- cellar (n=65 shelves): levels/shelf 2.8; levels filled 49%; items per filled level med 3 [p10 1, p90 7] n=88; drink 25%, food 20%, tableware 19%, misc_other 14%
- jail (n=49 shelves): levels/shelf 2.9; levels filled 63%; items per filled level med 3 [p10 1, p90 6] n=91; tableware 27%, book 14%, misc_other 13%, apparel 12%
- ship (n=45 shelves): levels/shelf 2.9; levels filled 61%; items per filled level med 4 [p10 1, p90 8] n=81; book 42%, tableware 20%, drink 7%, ingredient 6%
- smith (n=68 shelves): levels/shelf 2.6; levels filled 71%; items per filled level med 4 [p10 1, p90 8] n=123; valuable 25%, tool 18%, food 14%, misc_other 9%
- clothier (n=39 shelves): levels/shelf 2.3; levels filled 77%; items per filled level med 3 [p10 1, p90 7] n=69; apparel 26%, food 17%, tableware 17%, drink 9%
- fletcher (n=17 shelves): levels/shelf 2.1; levels filled 86%; items per filled level med 2 [p10 1, p90 6] n=31; food 29%, tableware 16%, weapon 15%, vessel 11%

By wealth (shelf+cupboard):
- poor (n=300): levels/shelf 2.7; filled 49%; food 20%, tableware 17%, ingredient 15%, misc_other 8%, drink 8%
- mid (n=1637): levels/shelf 2.9; filled 56%; tableware 28%, food 16%, drink 12%, book 11%, apparel 6%
- rich (n=1335): levels/shelf 2.7; filled 57%; book 23%, tableware 19%, food 11%, ingredient 11%, drink 10%
- mixed (n=228): levels/shelf 2.5; filled 65%; tableware 25%, drink 15%, food 13%, book 8%, misc_other 7%

## 5.3 Seat front: back found from the seat mesh (top part vs base centroid); front = the opposite way
seats read: 3608 (stools/benches with no back: 1385 = 38%; with a back 2223)
- what is in front of a backed seat within 150u (nearest in a +-50deg cone): table 57%, nothing within 150u in a 100-degree cone 26%, seat 5%, barrel 2%, cooking 2%, shelf 2%, bed 1%, chest 1%, crate 1%
- distance to it med 86 [p10 64, p90 123] n=1646u; angle off the seat axis med 12 [p10 1, p90 40] n=1646deg
- seats whose front meets a wall within 120u: 242 of 2223 = 11%
- house (n=624 seats): table 56%, nothing 28%, seat 4%, barrel 2%, crate 2%
- hall_keep (n=353 seats): table 57%, nothing 26%, seat 5%, chest 3%, barrel 2%
- inn (n=246 seats): table 61%, nothing 22%, seat 4%, shelf 2%, bed 2%
- shop_general (n=157 seats): table 57%, nothing 24%, seat 6%, cooking 3%, shelf 2%
- mill_farm (n=96 seats): table 47%, nothing 27%, cooking 8%, seat 5%, chest 3%
- barracks (n=135 seats): table 63%, nothing 19%, seat 8%, bed 2%, shelf 1%
- temple (n=66 seats): table 55%, nothing 32%, seat 5%, cooking 2%, chest 2%
- guild (n=156 seats): table 49%, nothing 32%, sidetable 4%, barrel 4%, seat 4%
- fort (n=125 seats): table 62%, nothing 22%, seat 6%, barrel 2%, bed 2%
- mine (n=30 seats): table 47%, nothing 43%, barrel 7%, cooking 3%

## 5.4 Counter between door and stock (shops): order along the line from the nearest teleport door to the stock centroid
tC = counter position as a fraction of door->stock distance (0 at door, 1 at stock); perp = counter distance off that line; stock behind = share of stock furniture (shelf/cupboard/dresser/wardrobe/barrel/crate) lying beyond the counter; keeper = nearest non-creature NPC ref to the counter and whether it stands on the stock side.
- smith: only 1 cells with the geometry (of 12); too few for a median
- alchemist: cells with a counter, a door and >=2 stock pieces 9 of 15; counter at med 0.59 [p10 0.36, p90 1.11] n=9 of the way door->stock; between door and stock (0<tC<1 and within 150u of the line) 33%; stock beyond the counter med 0.71 [p10 0.48, p90 0.95] n=9; door->counter med 362 [p10 261, p90 674] n=9u; keeper stands within med 150 [p10 90, p90 350] n=8u of the counter, on the stock side 88% (n=8)
- shop_general: cells with a counter, a door and >=2 stock pieces 22 of 53; counter at med 0.82 [p10 0.11, p90 1.28] n=22 of the way door->stock; between door and stock (0<tC<1 and within 150u of the line) 23%; stock beyond the counter med 0.57 [p10 0.34, p90 0.92] n=22; door->counter med 365 [p10 267, p90 943] n=22u; keeper stands within med 168 [p10 82, p90 461] n=20u of the counter, on the stock side 50% (n=20)
- clothier: only 1 cells with the geometry (of 4); too few for a median
- fletcher: only 1 cells with the geometry (of 1); too few for a median
- inn: cells with a counter, a door and >=2 stock pieces 31 of 59; counter at med 0.86 [p10 0.27, p90 1.15] n=31 of the way door->stock; between door and stock (0<tC<1 and within 150u of the line) 19%; stock beyond the counter med 0.67 [p10 0.42, p90 0.88] n=31; door->counter med 768 [p10 300, p90 1018] n=31u; keeper stands within med 132 [p10 91, p90 322] n=30u of the counter, on the stock side 70% (n=30)
- hall_keep: cells with a counter, a door and >=2 stock pieces 12 of 63; counter at med 0.86 [p10 0.11, p90 1.78] n=12 of the way door->stock; between door and stock (0<tC<1 and within 150u of the line) 25%; stock beyond the counter med 0.70 [p10 0.34, p90 0.85] n=12; door->counter med 753 [p10 422, p90 2269] n=12u; keeper stands within med 569 [p10 133, p90 1353] n=9u of the counter, on the stock side 67% (n=9)
- guild: cells with a counter, a door and >=2 stock pieces 4 of 25; counter at med 1.40 [p10 0.74, p90 1.62] n=4 of the way door->stock; between door and stock (0<tC<1 and within 150u of the line) 25%; stock beyond the counter med 0.39 [p10 0.14, p90 0.76] n=4; door->counter med 1778 [p10 1225, p90 4754] n=4u; keeper stands within med 310 [p10 221, p90 1340] n=4u of the counter, on the stock side 50% (n=4)

## 5.5 What stands within 120u (arm's reach plus a step) of a bed, by wealth; share of beds with at least one
- all beds (n=1409 beds): lightprop 41%, rug 36%, sidetable 29%, floorfill 27%, chest 21%, vessel 21%, seat 16%, bed 13%, dresser 13%, shelf 12%, barrel 12%, table 11%, apparel 10%, crate 10%
- wealth poor (n=194 beds): rug 48%, lightprop 32%, table 17%, seat 16%, urn 15%, wall 14%, floorfill 13%, cooking 13%, shelf 12%, vessel 10%, chest 10%, barrel 9%, crate 7%, basket 5%
- wealth mid (n=771 beds): lightprop 37%, rug 33%, floorfill 30%, sidetable 26%, chest 24%, vessel 20%, bed 16%, dresser 16%, barrel 12%, apparel 11%, table 11%, seat 11%, shelf 11%, crate 9%
- wealth rich (n=293 beds): sidetable 53%, lightprop 50%, rug 37%, vessel 32%, floorfill 24%, seat 22%, chest 19%, dresser 14%, shelf 14%, barrel 13%, crate 12%, apparel 11%, bed 10%, sack 8%
- wealth mixed (n=104 beds): lightprop 55%, rug 38%, seat 31%, sidetable 29%, chest 29%, vessel 20%, wall 20%, floorfill 19%, shelf 18%, sack 16%, crate 15%, table 15%, apparel 10%, barrel 8%
- kind house (n=433 beds): lightprop 43%, rug 33%, floorfill 29%, sidetable 26%, vessel 22%, dresser 19%, chest 16%, barrel 16%, crate 15%, shelf 14%, seat 13%, wall 9%, bed 9%, table 8%
- kind inn (n=155 beds): rug 53%, lightprop 52%, seat 29%, table 25%, chest 22%, sidetable 22%, vessel 20%, wall 17%, shelf 14%, urn 14%, floorfill 8%, crate 8%, dresser 6%, barrel 6%
- kind barracks (n=104 beds): rug 53%, sidetable 33%, chest 32%, lightprop 29%, vessel 21%, floorfill 21%, seat 14%, wall 14%, shelf 13%, bed 12%, apparel 8%, crate 8%, barrel 7%, table 5%
- kind hall_keep (n=181 beds): lightprop 46%, rug 38%, sidetable 35%, vessel 23%, chest 22%, floorfill 19%, apparel 17%, shelf 14%, barrel 12%, dresser 11%, bed 11%, seat 9%, sack 9%, crate 7%
- kind shop_general (n=54 beds): lightprop 54%, rug 39%, sidetable 31%, chest 31%, vessel 30%, floorfill 19%, table 17%, shelf 15%, barrel 15%, wall 13%, tableware 13%, drink 11%, apparel 9%, sack 9%
- kind ship (n=60 beds): floorfill 92%, lightprop 37%, bed 35%, seat 32%, barrel 28%, crate 22%, vessel 20%, table 18%, dresser 17%, sidetable 13%, rug 10%, wardrobe 10%, wall 7%, sack 7%
items by a bed: apparel (clothes/boots), tool, vessel, book, candle appear under their small-thing class names; basin = bath tag; lights = lightprop (candle/lantern statics).

## 5.6 Floor, wall and ceiling materials from the triangles: up-facing triangles within 30u of the floor = floor; down-facing triangles above floor+110u = ceiling; near-vertical triangles spanning floor+60..+100u = wall; each shape's diffuse texture takes the area
- house (n=220): floor: 1 textures (p90 2), 1 material groups (n=194); commonest timber/plank 42%, stone/brick/tile 15%, other:dlc2rrbulwarkfloor 15% / dlc2rrbulwarkfloor01.dds, dlc2rrplanks01.dds | wall: 2 textures (p90 3), 1 material groups (n=176); commonest timber/plank 44%, other:dlc2rrbuildings 23%, stone/brick/tile 9% / dlc2rrbuildings01.dds, woodwall01.dds | ceiling: 2 textures (p90 3), 1 material groups (n=196); commonest timber/plank 48%, thatch/reed/weave 12%, other:redoran 8% / woodpost02.dds, dlc2rrplanks01.dds | distinct textures across the three roles per room med 5 [p10 3, p90 7] n=200
- hall_keep (n=63): floor: 1 textures (p90 3), 1 material groups (n=56); commonest stone/brick/tile 38%, timber/plank 26%, earth/mud/clay 8% / riftencanalplanks01.dds, stonefloor01.dds | wall: 2 textures (p90 3), 2 material groups (n=56); commonest stone/brick/tile 33%, timber/plank 27%, other:redoran 6% / riftenlogdetails01.dds, ridgedstone06.dds | ceiling: 2 textures (p90 3), 2 material groups (n=56); commonest timber/plank 38%, stone/brick/tile 19%, plaster/stucco 6% / woodpost02.dds, wrwoodfloorint01.dds | distinct textures across the three roles per room med 6 [p10 4, p90 9] n=56
- inn (n=59): floor: 1 textures (p90 3), 1 material groups (n=59); commonest timber/plank 41%, stone/brick/tile 27%, other:redoranfloor 10% / stonefloor01.dds, dlc2rrplanks01.dds | wall: 2 textures (p90 3), 1 material groups (n=56); commonest timber/plank 41%, other:dlc2rrbuildings 16%, other:dryoakpost 14% / dryoakpost01.dds, woodwall01.dds | ceiling: 2 textures (p90 3), 1 material groups (n=59); commonest timber/plank 58%, other:dryoakpost 10%, other:redoran 10% / woodpost02.dds, dlc2rrplanks01.dds | distinct textures across the three roles per room med 5 [p10 4, p90 7] n=59
- shop_general (n=53): floor: 2 textures (p90 2), 1 material groups (n=53); commonest timber/plank 47%, stone/brick/tile 15%, other:redoranfloor 11% / rottingwood01.dds, redoranfloor01.dds | wall: 2 textures (p90 3), 2 material groups (n=48); commonest timber/plank 35%, other:dryoakpost 13%, other:dlc2rrbuildings 13% / dryoakpost01.dds, dlc2rrbuildings01.dds | ceiling: 2 textures (p90 3), 2 material groups (n=52); commonest timber/plank 51%, other:redoran 12%, other:dryoakpost 12% / dlc2rrplanks01.dds, dryoakpost01.dds | distinct textures across the three roles per room med 6 [p10 4, p90 8] n=53
- mill_farm (n=41): floor: 1 textures (p90 2), 1 material groups (n=38); commonest timber/plank 50%, stone/brick/tile 36%, earth/mud/clay 3% / stonefloor01.dds, dlc2rrplanks01.dds | wall: 2 textures (p90 2), 1 material groups (n=37); commonest timber/plank 52%, plaster/stucco 16%, other:dlc2rrbuildings 11% / woodwall01.dds, sstuccowallint01.dds | ceiling: 2 textures (p90 3), 1 material groups (n=38); commonest timber/plank 63%, other:dlc2rrbuildings 12%, other:dryoakpost 9% / woodpost02.dds, dlc2rrbuildings02.dds | distinct textures across the three roles per room med 5 [p10 3, p90 6] n=38
- barracks (n=30): floor: 1 textures (p90 3), 1 material groups (n=27); commonest timber/plank 50%, stone/brick/tile 19%, other:dryoakpost 9% / dlc2rrplanks01.dds, dryoakpost01.dds | wall: 2 textures (p90 3), 2 material groups (n=27); commonest timber/plank 42%, stone/brick/tile 12%, other:dlc2rrbuildings 11% / dryoakpost01.dds, rottingwood01.dds | ceiling: 2 textures (p90 3), 2 material groups (n=27); commonest timber/plank 52%, stone/brick/tile 11%, other:dryoakpost 10% / dryoakpost01.dds, whwoodboards02.dds | distinct textures across the three roles per room med 6 [p10 5, p90 8] n=27
- temple (n=27): floor: 2 textures (p90 3), 1 material groups (n=26); commonest timber/plank 33%, stone/brick/tile 33%, other:redoranfloor 13% / dlc2rrplanks01.dds, redoranfloor01.dds | wall: 2 textures (p90 4), 2 material groups (n=24); commonest timber/plank 42%, stone/brick/tile 31%, other:redoran 9% / dlc2rrplanks01.dds, redoran02.dds | ceiling: 2 textures (p90 3), 1 material groups (n=26); commonest timber/plank 49%, stone/brick/tile 31%, other:redoran 16% / dlc2rrplanks01.dds, redoran03.dds | distinct textures across the three roles per room med 5 [p10 4, p90 10] n=26
- guild (n=25): floor: 2 textures (p90 2), 2 material groups (n=16); commonest other:winterholdfloor 31%, timber/plank 20%, other:redoranfloor 17% / winterholdfloor01.dds, redoranfloor01.dds | wall: 2 textures (p90 4), 1 material groups (n=13); commonest stone/brick/tile 61%, timber/plank 27%, earth/mud/clay 5% / winterholdwall02.dds, winterholdwall01.dds | ceiling: 2 textures (p90 3), 1 material groups (n=16); commonest stone/brick/tile 38%, timber/plank 26%, other:redoran 22% / winterholdwall01.dds, redoran03.dds | distinct textures across the three roles per room med 6 [p10 4, p90 8] n=16
- fort (n=24): floor: 2 textures (p90 3), 1 material groups (n=23); commonest earth/mud/clay 77%, stone/brick/tile 19%, timber/plank 4% / impdirt01.dds, impfloormuddy01.dds | wall: 3 textures (p90 4), 2 material groups (n=24); commonest stone/brick/tile 45%, earth/mud/clay 39%, metal 9% / impdirt01.dds, impwall04.dds | ceiling: 3 textures (p90 3), 2 material groups (n=24); commonest stone/brick/tile 50%, earth/mud/clay 46%, timber/plank 5% / impdirt01.dds, impwall03.dds | distinct textures across the three roles per room med 8 [p10 6, p90 9] n=24
- mine (n=21): floor: 2 textures (p90 2), 2 material groups (n=19); commonest earth/mud/clay 67%, stone/brick/tile 22%, timber/plank 7% / minefloordirt01.dds, minerockwall02.dds | wall: 3 textures (p90 3), 2 material groups (n=19); commonest stone/brick/tile 38%, timber/plank 31%, earth/mud/clay 25% / minewood01.dds, dirtcliffsroots01.dds | ceiling: 3 textures (p90 3), 2 material groups (n=19); commonest stone/brick/tile 86%, timber/plank 12%, other:icefrozen 2% / minerockwall02.dds, minerockwall01.dds | distinct textures across the three roles per room med 7 [p10 6, p90 9] n=19
- warehouse (n=15): floor: 1 textures (p90 2), 1 material groups (n=15); commonest timber/plank 56%, stone/brick/tile 17%, other:dlc2rrbulwarkfloor 16% / dlc2rrplanks01.dds, dlc2rrbulwarkfloor01.dds | wall: 2 textures (p90 3), 2 material groups (n=14); commonest other:dlc2rrbuildings 46%, timber/plank 15%, stone/brick/tile 14% / dlc2rrbuildings01.dds, dlc2rrbulwark02.dds | ceiling: 2 textures (p90 3), 2 material groups (n=15); commonest timber/plank 47%, other:dlc2rrbuildings 27%, stone/brick/tile 8% / dlc2rrbuildings02.dds, dlc2rrplanks01.dds | distinct textures across the three roles per room med 6 [p10 5, p90 7] n=15
- alchemist (n=15): floor: 1 textures (p90 2), 1 material groups (n=15); commonest stone/brick/tile 31%, timber/plank 31%, earth/mud/clay 9% / whwoodboards02.dds, stonefloor01.dds | wall: 2 textures (p90 3), 1 material groups (n=15); commonest timber/plank 40%, stone/brick/tile 16%, other:dlc2rrbulwark 14% / dryoakpost01.dds, rottingwood01.dds | ceiling: 2 textures (p90 3), 1 material groups (n=15); commonest timber/plank 59%, stone/brick/tile 17%, other:dryoakpost 8% / dlc2rrplanks01.dds, whwoodboards02.dds | distinct textures across the three roles per room med 5 [p10 4, p90 7] n=15
- cellar (n=14): floor: 1 textures (p90 2), 1 material groups (n=12); commonest stone/brick/tile 48%, earth/mud/clay 24%, timber/plank 20% / riftenstonewall02.dds, cavebaseground01.dds | wall: 2 textures (p90 2), 1 material groups (n=13); commonest timber/plank 47%, stone/brick/tile 27%, other:dlc2rrbuildings 18% / riftenlogdetails01.dds, dlc2rrbuildings01.dds | ceiling: 2 textures (p90 2), 1 material groups (n=13); commonest timber/plank 44%, stone/brick/tile 41%, other:dlc2rrbuildings 11% / cavebasewall02.dds, riftenstonewall02.dds | distinct textures across the three roles per room med 4 [p10 4, p90 6] n=13
- jail (n=14): floor: 2 textures (p90 3), 1 material groups (n=12); commonest stone/brick/tile 40%, earth/mud/clay 32%, timber/plank 9% / stonefloor01.dds, impfloormuddy01.dds | wall: 3 textures (p90 4), 2 material groups (n=12); commonest stone/brick/tile 43%, timber/plank 22%, other:dlc2rrbulwark 18% / woodwall01.dds, icecavewall01.dds | ceiling: 2 textures (p90 4), 2 material groups (n=12); commonest timber/plank 39%, stone/brick/tile 29%, other:dlc2rrbulwark 12% / woodwalkway01.dds, dlc2rrbulwark01.dds | distinct textures across the three roles per room med 7 [p10 5, p90 10] n=12
- ship (n=13): floor: 1 textures (p90 2), 1 material groups (n=8); commonest timber/plank 100% / shipwoodfloor01.dds, dlc2rrplanks01.dds | wall: 2 textures (p90 2), 1 material groups (n=7); commonest timber/plank 85%, other:dlc2rrbulwark 15% / dlc2rrplanks01.dds, shipwood01.dds | ceiling: 2 textures (p90 2), 1 material groups (n=7); commonest timber/plank 86%, other:dlc2rrbulwark 14% / shipwoodfloor01.dds, dlc2rrplanks01.dds | distinct textures across the three roles per room med 5 [p10 2, p90 6] n=8
- smith (n=12): floor: 2 textures (p90 2), 2 material groups (n=12); commonest timber/plank 57%, other:dryoakpost 14%, other:dfloor 8% / rottingwood01.dds, whwoodboards02.dds | wall: 2 textures (p90 3), 2 material groups (n=12); commonest timber/plank 23%, other:dryoakpost 22%, other:dlc2rrbuildings 19% / dryoakpost01.dds, dlc2rrbuildings01.dds | ceiling: 2 textures (p90 4), 2 material groups (n=12); commonest timber/plank 52%, other:dryoakpost 18%, stone/brick/tile 10% / whwoodboards02.dds, dryoakpost01.dds | distinct textures across the three roles per room med 6 [p10 5, p90 9] n=12
- clothier (n=4): floor: 2 textures (p90 3), 2 material groups (n=4); commonest timber/plank 51%, other:redoranfloor 15%, other:dlc2rrbulwarkfloor 15% / swoodfloor01.dds, dlc2rrplanks01.dds | wall: 2 textures (p90 3), 1 material groups (n=4); commonest other:dlc2rrbuildings 50%, other:dlc2rrbulwark 25%, timber/plank 25% / dlc2rrbuildings01.dds, swoodcolumn01.dds | ceiling: 2 textures (p90 3), 2 material groups (n=4); commonest timber/plank 82%, thatch/reed/weave 9%, other:dlc2rrbuildings 6% / dlc2rrplanks01.dds, swoodbeam02.dds | distinct textures across the three roles per room med 6 [p10 5, p90 6] n=4

By wealth:
- wealth poor (house/inn/shop/hall) (n=46): floor: 1 textures (p90 2), 1 material groups (n=45); commonest timber/plank 82%, stone/brick/tile 12%, other:dryoakpost 5% / rottingwood01.dds, whwoodboards02.dds | wall: 2 textures (p90 2), 1 material groups (n=45); commonest other:dryoakpost 58%, timber/plank 31%, other:riftensiding 6% / dryoakpost01.dds, rottingwood01.dds | ceiling: 2 textures (p90 3), 2 material groups (n=45); commonest timber/plank 46%, other:dryoakpost 40%, thatch/reed/weave 8% / dryoakpost01.dds, whwoodboards02.dds | distinct textures across the three roles per room med 5 [p10 3, p90 6] n=45
- wealth mid (house/inn/shop/hall) (n=239): floor: 2 textures (p90 2), 1 material groups (n=221); commonest timber/plank 34%, stone/brick/tile 17%, other:dlc2rrbulwarkfloor 15% / dlc2rrbulwarkfloor01.dds, dlc2rrplanks01.dds | wall: 2 textures (p90 3), 1 material groups (n=196); commonest timber/plank 39%, other:dlc2rrbuildings 27%, stone/brick/tile 8% / dlc2rrbuildings01.dds, woodwall01.dds | ceiling: 2 textures (p90 3), 1 material groups (n=222); commonest timber/plank 50%, other:redoran 14%, thatch/reed/weave 8% / dlc2rrplanks01.dds, redoran03.dds | distinct textures across the three roles per room med 5 [p10 3, p90 7] n=226
- wealth rich (house/inn/shop/hall) (n=54): floor: 2 textures (p90 3), 2 material groups (n=45); commonest timber/plank 46%, stone/brick/tile 27%, other:sfloorhouse 13% / riftencanalplanks01.dds, sfloorhouse01.dds | wall: 2 textures (p90 3), 2 material groups (n=44); commonest timber/plank 49%, stone/brick/tile 19%, plaster/stucco 11% / riftenlogdetails01.dds, wrplasterint01.dds | ceiling: 2 textures (p90 4), 2 material groups (n=44); commonest timber/plank 59%, stone/brick/tile 10%, other:dryoakpost 6% / wrwoodfloorint01.dds, riftenlogdetails01.dds | distinct textures across the three roles per room med 6 [p10 4, p90 9] n=45
- wealth mixed (house/inn/shop/hall) (n=27): floor: 1 textures (p90 2), 1 material groups (n=26); commonest stone/brick/tile 42%, timber/plank 33%, other:dlc2rrbulwarkfloor 10% / stonefloor01.dds, dlc2rrplanks01.dds | wall: 2 textures (p90 4), 2 material groups (n=26); commonest timber/plank 62%, stone/brick/tile 22%, other:dlc2rrbuildings 8% / dlc2rrplanks01.dds, woodwall01.dds | ceiling: 2 textures (p90 2), 2 material groups (n=26); commonest timber/plank 42%, thatch/reed/weave 25%, stone/brick/tile 14% / woodpost02.dds, thatch03.dds | distinct textures across the three roles per room med 5 [p10 4, p90 8] n=26


## 5.7 Absolute floor area: navmesh (walkable triangles, plan area) per cell, all levels
- house: navmesh floor area med 85.5 [p10 21.0, p90 301.1] n=215 m2 (cells with navmesh 215 of 220)
- hall_keep: navmesh floor area med 379.1 [p10 91.3, p90 1093.7] n=60 m2 (cells with navmesh 60 of 63)
- inn: navmesh floor area med 177.6 [p10 55.9, p90 380.3] n=59 m2 (cells with navmesh 59 of 59)
- shop_general: navmesh floor area med 83.7 [p10 34.7, p90 324.3] n=53 m2 (cells with navmesh 53 of 53)
- mill_farm: navmesh floor area med 71.4 [p10 38.1, p90 129.6] n=41 m2 (cells with navmesh 41 of 41)
- barracks: navmesh floor area med 96.0 [p10 47.7, p90 826.8] n=30 m2 (cells with navmesh 30 of 30)
- temple: navmesh floor area med 208.6 [p10 47.9, p90 666.3] n=27 m2 (cells with navmesh 27 of 27)
- guild: navmesh floor area med 513.5 [p10 256.3, p90 1256.6] n=25 m2 (cells with navmesh 25 of 25)
- fort: navmesh floor area med 620.1 [p10 146.7, p90 1090.2] n=24 m2 (cells with navmesh 24 of 24)
- mine: navmesh floor area med 466.7 [p10 205.4, p90 993.0] n=21 m2 (cells with navmesh 21 of 21)
- warehouse: navmesh floor area med 65.0 [p10 56.6, p90 92.2] n=15 m2 (cells with navmesh 15 of 15)
- alchemist: navmesh floor area med 82.4 [p10 37.0, p90 216.7] n=15 m2 (cells with navmesh 15 of 15)
- cellar: navmesh floor area med 157.3 [p10 42.8, p90 737.3] n=14 m2 (cells with navmesh 14 of 14)
- jail: navmesh floor area med 388.7 [p10 170.7, p90 825.5] n=13 m2 (cells with navmesh 13 of 14)
- ship: navmesh floor area med 52.3 [p10 18.5, p90 516.8] n=11 m2 (cells with navmesh 11 of 13)
- smith: navmesh floor area med 103.7 [p10 39.3, p90 178.7] n=12 m2 (cells with navmesh 12 of 12)
- clothier: navmesh floor area med 93.8 [p10 58.3, p90 257.3] n=4 m2 (cells with navmesh 4 of 4)
- camp_tent: navmesh floor area med 15.1 [p10 11.9, p90 22.6] n=3 m2 (cells with navmesh 3 of 3)
By wealth (house): poor med 46.4 [p10 17.6, p90 114.4] n=19; mid med 86.5 [p10 31.0, p90 200.8] n=158; rich med 304.2 [p10 81.1, p90 743.7] n=17
cross-check house navmesh m2 vs earlier furniture-hull m2: ratio median 0.75 (n=214); earlier lane walkable-mesh median 67 m2.
cells with no navmesh in the files: 11 of 654 (mods that never built one); for those the up-facing floor triangles at furniture level give: med 79 [p10 11, p90 690] n=7 m2 (overstates, stacked faces)
## 5.8 Thin kinds: widened across every held plugin (1,196 interior cells; evidence = name, owning faction, NPC base names, clothing/bow item counts, looms/mannequins/targets, tent models in the cell)
How many truly exist (a cell counts only with a name, faction or NPC naming the trade; furniture or stock evidence alone is listed as "mentions"):
- Clothier / weaver / glover shops: 4. Radiant Raiment (Skyrim), Glover Mallory's House (Dragonborn), Fine Cladding and The Needle and Thread (Journey to Baan Malur; the latter a weaver). Stock-only evidence adds nothing: 79 other cells carry 8+ clothing refs or a mannequin/loom (forts, Dawnguard, Proudspire/BYOH houses, Arena Market) but none is a clothier by name, faction or NPC.
  Measured (n=4): bed 4/4, table 4/4, shelf 4/4, chest 4/4, barrel 4/4, counter 1/4, rug 4/4; small things per cell 48, 41, 107, 233; clothing refs 37, 2, 5, 37; navmesh 60, 58, 128, 313 m2; ceiling 236-291u; faction-owned in all 4; shell kits ravenrock 3, riften interior 1, pancake platforms 1.
- Fletcher / bowyer shops: 2. Fletcher (Solitude, Dawn of Skyrim) and Corkbulb Crock (Baan Malur archery; I had misfiled it as alchemist; faction BaanHSFletchersFaction). 60 other cells hold bows/arrows or archery targets (forts, caves, bandit dens) but are not shops.
  Measured (n=2): bed 2/2, table 2/2, shelf 2/2, chest 2/2, counter 1/2, sack 2/2, cupboard 2/2; small things 27 and 206; navmesh 57 and 220 m2; ceiling 619u (rafters) and 268u.
- Tent / yurt interiors: 11. Eight Ashlander yurts (Camp New Zainab, ~40 refs, navmesh 11-27 m2) + Kar-Jei's Tent, Storage Tent, Common Room (Baan Malur Saxhleel camp, 26-51 refs). No Argonian or Black Marsh tent interior exists in anything held (the ArgonianLakeHouse tent is a static, not a cell). Measured (n=11): seat 9/11, table 9/11, rug 9/11, crate 9/11, bedroll 5/11, bed 3/11, fire 5/11, chest 4/11, shelf 3/11, alchemy bench 1/11; small things 2-22 (median 8); light refs 2-11; navmesh median 15 m2 (p10-p90 11-25); owner faction on 4 of 11 (ashlander family/ Saxhleel). Where a ceiling cast hit (3 of 11) it reads 204-212u; the rest are tent meshes with no cast surface.
- Other thin kinds measured above with their true n: smith 12, alchemist 15, ship 12, warehouse 15, cellar 14, jail 14.

## 5.9 The Black Marsh shell gap, counted against need
Need counted from: (a) place records, newworld/story/data/db/place.jsonl (258 places; 144 with building interiors: outpost 41, village 29, hamlet 24, city 11, town 10, farm 9, fort 8, estate 3, logging camp 3, lighthouse 2, belvedere 1, homestead 1, prison 1, station 1; plus mine 10, cave 2, ruin 59, shipwreck 11, sunken ruin 7, camps 16 with no interior); (b) the six drafted places' interiors (41: Helstrom 27, Jal-Veesa 10, outpost m13 2, tribal camp m2 2); (c) the 15 distinct rooms named in newworld/story/quests/main/*.yaml; (d) people (165): guard 23, merchant 4, apothecary 2, innkeeper 1, smith 1, spell-trader 1, boatman 1, trainer 1; households 43. Derived (labelled): homes ~ population 1,901 in building places / 3.8 per household (165 people in 43 households) = about 500.
Held shells: KotM blackwood (6 whole-house Partion shells + wall/window/door panels, 183 pieces), mudhuts (6 Int/Ext whole domes, 44), ArgonianLakeHouse nest (whole hut + props, 34), BM 01ArgonianHouseinside (BYOH + "architecture and structures"), HTBM villages (reed domes, 23, no cell uses them), Xanmeer (interior 27+43+40; grid 256), Imperial colonial tesak (357) and Imperial jail/hall/room/tower, Dunmer dagon fel/velothi/mwnordhouse, Valenwood citebosmer houses, ship kits (Sailable Ship, pancake ship, stockades, tradeship), vanilla mines/farmhouse/ravenrock, CTQ wet caves (153), Ayleid/Dwemer ruins.
By culture of the 144 building places (fit judged from each culture's own description in culture.jsonl):
- Stilt/reed/hut cultures with a whole-hut/house shell held: forest-green 19, rose 15, rust 12 (clay-mound domes: mudhuts), jade 6, plum 6, olive 5, indigo 5, lime 4 = 72 places. Fit: yes, whole shells only (no modular set; no plan other than the 6+6+1+1 shells).
- Stone/Imperial/Dunmer cultures with a held stone kit: crimson-red 16 (Imperial forts), stone-grey 11 (Dunmer/Argonian stone farmsteads), umber 8, pale-green 8 (Imperial colonial; floors/ceilings thin: 8 floor / 2 ceiling pieces), steel-blue 7 (fortified towns), magenta 4 (stockade outposts: argonia/stockades 53) = 54 places. Fit: yes for walls/corners/stairs; thin floors and ceilings.
- Stone over Velothi/Ayleid foundations: sky-blue 5: velothi (243) and ayleid kits fit, domestic rooms from them: none used in any held house cell.
- NO fitting domestic shell: oxblood 7 (Kothringi-named towns), pearl 5 (Seafalls cliff-and-surf village), gold 1 (Archon harbour) = 13 places; and the root-hollow homes of forest-green (19 places; the culture "live on stilts and in root-hollows": stilts fit, root-hollows none).
By interior kind (need count, source -> held fit):
| kind | need | fit |
| Argonian stilt/reed/mud home | 25 drafted homes (Helstrom 17, Jal-Veesa 7, Ashgate 1); 2 quest houses; ~500 derived | FIT whole shells only (blackwood 6, mudhuts 6, BM house, nest) |
| root-hollow / Hist-grown home | 19 forest-green places | NONE |
| inn / lodge / bunkhouse | 2 drafted + quest Boatmen's Lodge + Pale Harvest; innkeeper 1 | FIT blackwood (11 of 59 inns), ship hull for the lodge |
| shops: general 5, smith 2, apothecary 2, books/spells 1 | people + 3 drafted shops | FIT blackwood (store 8 pieces, ironworks 33, distillery 9); by-trade shells none needed (trade is dressing) |
| Hist room / tree-minders' hall / "The Root" / Guardian's Hall | 4 (Helstrom hall, Jal-Veesa hut, quest Root, quest Root's chamber) | PARTIAL Xanmeer stone (complete shell, no living-root room); root pieces 15 fragments |
| barracks / levy post / wardens' quarters / watch | 3 drafted + South Watch Inner Room + guard 23 | FIT Imperial fort kits, blackwood barracks (7 cells) |
| jail / prison / cage | 1 drafted jail + quest Blackrose Prison + Sesk's Cage + 1 prison place | FIT Imperial jail kit (80 cell uses); cage is a prop |
| hall / council house / chief's hall / greathouse | council house 1 drafted; quest Raj-Kaal's Hall, Guardian's Hall, Kothringi Greathouse; tribal longhouse 1 | FIT blackwood manor (45 pieces) for the council house; NONE for Kothringi greathouse; longhouse is vanilla Nordic today |
| strongroom / vault | 1 drafted + quest Vault of the Household + Warden's Vault | FIT Imperial small rooms |
| ship / barge hold | quest Barge Hold + 1 drafted barge (01dock3to4) | FIT stockades/tradeship/aaaship, partial (no hatch/ladder hold) |
| cellar | 1 drafted (tribal) | NONE Argonian (vanilla farmhouse basement only) |
| mines | 10 places | FIT vanilla mines, kwama mine, CTQ wet caves |
| lighthouse 2, farm 9, estate 3, homestead 1, logging camp 3 | places | FIT partial: Baan Malur lighthouse, Cormaris farmhouse (Imperial), Lilmoth lumberworks (blackwood) |
| ruins: abandoned stilt village 8 | places | FIT blackwood ruin shells (MurkmireThatchHouseRuin01-02) |
| ruins: Ayleid 7, Velothi 12, Imperial 12, keep 3 | 34 places | FIT ayleid/velothi/imperial kits |
| ruins: Kothringi 8, Lilmothiit 9 | 17 places | NONE |
| shipwreck 11, sunken ruin 7 | 18 places | FIT vanilla ship interiors, underwater skyrim (not walked in 3D) |
| tent | tribal camps 14 (no interior in the records) | none needed |
Gap list, counted: no fitting domestic shell for 13 of 144 building places (oxblood, pearl, gold) + root-hollow homes of 19; no shell for the Hist-room kind (4 rooms), the Argonian cellar (1), the Kothringi greathouse (1) and Kothringi/Lilmothiit ruins (17 places); every other need is met by a whole-room shell but never by a modular one.

## 5.10 What truly cannot be read from the files
- Seat front of the 871 stools and benches (37% of seats): they have no back, so no front exists; their reach is measured as "nothing within 150u" only when they have a back.
- Smith counters door-to-stock: only 1 of 12 smith cells and 1 of 4 clothier cells hold a counter, a door and 2 stock pieces; there is no median for them (all other shop kinds have 9-31).
- Texture look (colour, wear, tint): the files hold paths; pixel content was not read.
- Hooks and hung-item attachments: no record exists; heights from item positions only.

## 5.11 Corrections to the earlier sections
- Ceiling height now measured for 85-95% of shells by cast (houses 259u median, p10 195 / p90 411, n=180; inns 243u n=28; shops 322u n=30; halls 327u n=47; barracks 251u n=24; ship 225u n=7); poor 222u, mid 301u, rich 282u (n=36/181/34). Replaces "250u, n=80".
- Floor area: use navmesh m2 in 5.7 (house median 80 m2, p10 20, p90 258, n=201; poor 46 n=18, mid 85 n=151, rich 297 n=15; inn 80, shop 73, hall 371, barracks 79, temple 202, guild 587, mine 472, jail 309, smith 111, alchemist 59). Replaces the collision-based 172 m2.
- Distinct materials: the earlier "distinct textures on the shell per room" (9 house) counted every piece texture; the per-role count in 5.6 is 2 floor / 2 wall / 2 ceiling textures in a typical house (5 across the three roles), at >=10% of the role's area.
- Corkbulb Crock is a fletcher, not an alchemist (thin-kind counts).
- Earlier alchemy/enchanting/smith benches were tagged as seats for the first run; the appendix tables B-F (second run) carry the corrected numbers.
