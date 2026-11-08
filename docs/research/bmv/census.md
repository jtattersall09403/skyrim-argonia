# The BM&V census (phase 1)

BM&V is four plugins, read in load order by `tools/argonia_world/bmv_census.py build` (masters Skyrim, Update and the
three DLC give their forms' names) into the `bmv_*` tables of `story/data/schema.sql`:

| plugin | size | masters (beyond Skyrim, Update) | what it is |
|---|---|---|---|
| BosmerArmorMATY743.esm | 75 KB | none | Bosmer armour and outfits, 14 NPC_ (6 its own), 8 vanilla cells edited (4 Skyrim inns and houses, 3 in Shadowgreen Cavern, 1 in Tamriel) |
| Black Marsh.esm | 20 MB | Dawnguard, HearthFires, Dragonborn | worldspaces BlackMarsh and BlackMarsh2 |
| Black Marsh North.esp | 27 MB | the DLC, Black Marsh.esm | worldspace BlackMarshNorth ("Thorn", up to Tear), the empty UnderDark; edits 765 of Black Marsh.esm's cells (3 deleted), deletes 13,925 of its refs, 94 actors, 5 NPC_ and 3 cells; adds the map markers and the Dawnstar book portal |
| Valenwood.esp | 20 MB | the DLC, BosmerArmorMATY743.esm | worldspace Valenwood; edits 13 vanilla Tamriel and Whiterun cells and 7 vanilla interiors |

Overrides are resolved as the engine does: a form's last version in load order wins, and a winner flagged deleted
removes the form. Every row keeps the form key of its defining master (`XXXXXX:Plugin`); `plugin` is the first BM&V
file that carries the record and `overridden_by` the later ones. `bmv_census.py verify` is the completeness proof below.
`db check` is green and every foreign key resolves.

## Completeness proof

Per plugin and type: records counted by a byte walk of the file (`bytes`, a second reader), as read (`read`), live
winners in the census (`census`), overridden by a later BM&V plugin (`later`), deleted by a later winner (`deleted`),
and fallen out (`dropped`: none). Every line holds `read = census + later + deleted` and `bytes = read`, and the other
way, every census row of a BM&V record is a live winner of its type. Doors are REFRs with XTEL; map markers REFRs of
the map-marker base with XMRK. Types a plugin lacks are 0 in every column (Bosmer: LAND, FACT, QUST, LCTN, doors).

| plugin | type | bytes | read | census | later | deleted |
|---|---|---|---|---|---|---|
| BosmerArmorMATY743.esm | WRLD / CELL / ACHR / NPC_ / BOOK | 2 / 8 / 2 / 14 / 1 | same | 1 / 8 / 2 / 13 / 1 | 1 / 0 / 0 / 1 / 0 | 0 |
| Black Marsh.esm | WRLD | 4 | 4 | 0 | 4 | 0 |
| | CELL | 4,826 | 4,826 | 4,058 | 768 | 0 |
| | LAND | 4,357 | 4,357 | 4,067 | 290 | 0 |
| | ACHR | 1,139 | 1,139 | 1,007 | 132 | 0 (BMN's deletions count under BMN) |
| | NPC_ / FACT / QUST / LCTN / BOOK | 130 / 6 / 3 / 6 / 4 | same | 107 / 6 / 3 / 5 / 4 | 23 / 0 / 0 / 1 / 0 | 0 |
| | load doors | (REFR) | 79 | 54 | 25 | 0 |
| Black Marsh North.esp | WRLD | 7 | 7 | 6 | 1 | 0 |
| | CELL | 3,581 | 3,581 | 3,577 | 1 | 3 |
| | LAND | 3,023 | 3,023 | 3,023 | 0 | 0 |
| | ACHR | 922 | 922 | 828 | 0 | 94 |
| | NPC_ / FACT / QUST / LCTN / BOOK | 91 / 2 / 0 / 3 / 4 | same | 86 / 2 / 0 / 2 / 4 | 0 / 0 / 0 / 1 / 0 | 5 / 0 / 0 / 0 / 0 |
| | load doors / map markers | (REFR) | 61 / 28 | 61 / 28 | 0 | 0 |
| Valenwood.esp | WRLD / CELL / LAND / ACHR | 3 / 3,918 / 3,440 / 1,032 | same | same | 0 | 0 |
| | NPC_ / FACT / QUST / LCTN / BOOK | 176 / 5 / 2 / 5 / 3 | same | same | 0 | 0 |
| | load doors / map markers | (REFR) | 126 / 12 | 126 / 12 | 0 | 0 |

Verdict: every WRLD, CELL, LAND, ACHR, NPC_, FACT, QUST, LCTN, BOOK, load door and map marker of the four files is
accounted for. The map's `verify` adds: every worldspace is on the switcher, every census cell, settlement, door,
exterior placement and map marker of each worldspace is on its page (interiors and their 421 placements have
no map position; they are in the census and the settlement panels), and every exterior cell with LAND (10,530) is drawn
(34 LAND records carry no heights, VHGT; they are drawn flat at the worldspace's default land height).

## Worldspaces

Size is the exterior cells with LAND, at 70 units a metre (a cell 58.5 m a side, 0.00342 km²). Skyrim.esm's Tamriel,
measured the same way, has 11,186 LAND cells: 38.3 km².

| worldspace | name | plugin | LAND cells | km² | of Skyrim | cells (with grid) | settlements | placements (people) | doors |
|---|---|---|---|---|---|---|---|---|---|
| BlackMarsh 23D689 | Black Marsh | Black Marsh.esm, edited by BMN | 1,127 | 3.9 | 10% | 1,408 | 13 | 623 (150) | 18 |
| BlackMarsh2 0D6960 | Black Marsh2 | Black Marsh.esm, edited by BMN | 3,230 | 11.1 | 29% | 3,380 | 14 | 450 (143) | 23 |
| BlackMarshNorth 005900 | Thorn | Black Marsh North.esp | 2,733 | 9.4 | 24% | 2,798 | 12 + 2 sites | 515 (59) | 12 |
| UnderDark 0B8BDD | a | Black Marsh North.esp (parent BlackMarshNorth) | 0 | 0 | | 0: an empty worldspace | | | |
| Valenwood 005900 | Valenwood | Valenwood.esp | 3,440 | 11.8 | 31% | 3,875 | 47 | 858 (253) | 50 |
| all four of BM&V's own | | | 10,530 | 36.1 | 94% | | 86 + 2 | 2,446 | |

Vanilla worldspaces BM&V edits, with no LAND of its own: Tamriel (15 cells: the Valenwood cave door at 43,16, a
map marker "Unkown Cave"), Solstheim (4), Shadowgreen Cavern (2), Whiterun (1), Update's `zz` (none). Interiors: 71
in all (`bmv_cell.interior`); 28 are in no settlement: 16 vanilla interiors whose editor id BM&V keeps
(Skyrim's places that BM&V edits, not BM&V places: the two inns get portals, books and an actor each, Cragslane
Cavern a rewired door and 89 refs, Thalmor Embassy rooms and others; Dawnguard's 018CE1 "Quick Test Cell" holds 27
BM refs and no door) and the 12 doorless
ones below.

## How each worldspace is entered

Books are not scripted: no BOOK of the four files has a script. The book portals are load doors whose base is a book
(`01doorbook` "Tome", openbook01.nif, Black Marsh North.esp; `01book` "Book", Valenwood.esp) or a magic conduit
(`01MagicPortal` "Magic Button", Valenwood.esp); their targets are XTEL.

- **Skyrim to Black Marsh (BMN):** Dawnstar's Windpeak Inn holds the two books of the ModDB description: the book
  portal 166BB5 (`01doorbook`), leading to door 166BB9 at Lilmoth (BlackMarsh 1,-3), and the book "Welcome to Black
  Marsh" (`01blackMarsh` 166BB6). BMN deletes Black Marsh.esm's undersea Tamriel door 00AC5C (`OrcDoorLoad01`), so
  the old Nordic-door entry is gone (BMN neutralises 13 of Black Marsh.esm's load doors: deletes 00AC5C, 156469,
  156473, 156482, 15646D, 15647C and strips XTEL from 156415, 156427, 156433, 15644B, 156463, 0F91ED, 23D458); its ship `01ShipDUPLICATE001` still links only to Lilmoth (005AB4, BlackMarsh 1,-3).
- **Skyrim to BlackMarsh2:** Black Marsh.esm rewires vanilla Cragslane Cavern's door 01544B:Skyrim.esm to BM2 15,-4.
- **Skyrim to Valenwood:** Riverwood's Sleeping Giant Inn holds two `01MagicPortal` doors, to Valenwood -30,-17
  (Woodhearth's Dock7) and -17,4 (Falinesti), and the book "Valenwood" (`01BookOfValenwood`); and a cave door at
  Tamriel 43,16 (map marker "Unkown Cave") leads through 01jail and 01Thalmor2 to Valenwood -29,-20 (01Dwemer1 a side loop).
- **Between BM&V's worlds (ships):** ship `01Ship` (extended by BMN) has exits at BlackMarsh 7,-1 and 10,-2,
  BlackMarsh2 -10,12, -10,7 and -23,20, and BlackMarshNorth 5,13, 6,13 (Thorn) and 25,19 (Tear); ship `01dock3to4`
  joins Blackrose's dock (door 1BEAD6 at BlackMarsh 33,-18, by cell DockDUPLICATE004 at 32,-17) and Murkwood (BlackMarsh2 18,1); house `01CabinInt2` has doors at
  BlackMarsh 12,-2 and BlackMarsh2 1,-10 and 12,0.
- **Book portals in the north:** BlackMarsh2 13,25 (abondedtemple) to BlackMarshNorth -12,1 through
  `01aundergroundcell`; BlackMarshNorth -9,15 into `01underdark` and -20,22 into `01Underdarkmiddle` (interiors; the
  UnderDark worldspace has no cells). Valenwood's `01book` doors: interior `01guild` to Valenwood -20,-7, and
  `01GrahtOaks` to `01SouthpointINT`.
- Valenwood has no door to any Black Marsh worldspace: it is entered only from Skyrim.
- Black Marsh.esm also edits Skyrim's AbandonedShackInterior (050F1E): its door 050F28 still leads to Skyrim's
  own door 050F1F, the only BM&V door besides Cragslane's to target a master door.
- The three vanilla interiors holding BM&V's ways in (Cragslane, the two inns) have no `bmv_interior_exit` rows:
  the settlements leave Skyrim's interiors out.

## Settlements

The settlements are grouped from the named exterior cells of BM&V's own worldspaces (editor ids, so `name` is a label
such as `Grass` or `test1`): a settlement's squares are its named cells, the squares within 1 of them, and squares with
content nearest them within 8; its interiors are found through the door graph. BlackMarsh and BlackMarsh2 keep their
ids (`bmv.<editor id>`); the new worlds' are `bmv.blackmarshnorth.<editor id>` and `bmv.valenwood.<editor id>`.
`marker_name` is the name of BM&V's own map marker (BMN's 28, Valenwood's 12) on its anchor or neighbour squares.

- **BlackMarsh (13):** lilmoth ("Lolmoth; Lilmoth Dock"), hereguardplantation, altenmeirhall ("Alten Merihall"),
  longmont, blackrose ("Black Rose"), village, swamplandsrose, dock2 ("Docks"), castle, grass, mountainpass, therose,
  gg (was dock3: BMN renames cell Dock3 to `gg`, and Blackrosemarket to `DockDUPLICATE004`); gg, therose and
  mountainpass, in the far west, have no actors and no doors: an unused old Black Rose (cell BlackRoseold).
- **BlackMarsh2 (14):** helstrom, dock5 ("Helstrom": BM&V's own map marker for Helstrom stands at the landing), dwarven
  ("Dwarven Ruins"), murkwood, murkwoodext ("Bandit Dock"), murkmire, temple, temple2 ("Road to Docks"), tribe,
  banditcamp1, outercave, and BMN's newly named abondedtemple, templepass ("Temple Pass") and groot.
- **BlackMarshNorth (12 + 2 sites):** thorn1 ("Thorn"), tear ("Tear") and tear1, manor ("Dres village"), marsh,
  lizardmen (+Shack), treehouse, waterfalls, ruin12, test1, dessert (the north strip to the Morrowind border markers),
  1; sites Swampy Cave (01Goblincave) and Sharpslope Cave (01templecave).
- **Valenwood (47):** eldenroot ("Elden Root"), capital ("Falinesti") and falinesti, bosmer ("Silvenar"), arenthi
  ("Arenthia"), woodhearth, greenheart, haven, moonmount, southpoint, bosmertree ("Canopy Pass"), and 36 more named
  cells (ruins, villages, wilds, and labels such as `fix` or `misttest`).
- Black Marsh North.esp populates Helstrom (13 placements: the boatman Namorine, soldiers, villagers) and its hall
  `01cellDUPLICATE002` (merchants One Who Has Fire Hands and a weapons dealer, a soldier), and Hereguard Plantation
  (two New Order Soldiers and the merchant Looks at books); it deletes Hereguard's two Breton merchants.

Doorless interiors (no load door in or out in the full load order, some because BMN stripped their doors;
reachable only by a script of ours): Gallows Rock 01grock1 (1,407 refs,
26 actors), Darklight Tower 01Tower (1,013, 7), 01Cavebig (723, 10), 01SoM_VulcanicDUPLICATE002, 01Dwarmerhome,
01cabinintDUPLICATE002, 01newcell1, 01Hobit1, 01Cell2, 01spidercave, 01cell1 and 01valenwoodEnt.

## Counts

| table | rows | note |
|---|---|---|
| bmv_worldspace | 10 | 5 of BM&V's own (UnderDark empty), 5 vanilla overrides |
| bmv_cell | 11,561 | 71 interiors; 2,863 with navmesh; 7 persistent cells |
| bmv_location | 26 | 12 LCTN overrides of vanilla locations, 14 more named by a cell; BM&V has no LCTN of its own |
| bmv_npc | 674 | 382 NPC_ in the files that win, the rest master bases ACHRs place |
| bmv_placement | 2,869 | 12 start disabled |
| bmv_faction / bmv_npc_faction | 160 / 853 | 13 in the files (prisoner and merchant factions, the Bosmer Guard Faction, 1 override) |
| bmv_race / bmv_class | 92 / 65 | |
| bmv_quest | 5 | 01Captain "Welcome to Black Marsh"; Valenwood's 0MainQuest1 "Valenwood" and AANEWQuestM "Welcome To Valenwood", both start-game-enabled; 2 vanilla overrides |
| bmv_door | 241 | 240 pair inside BM&V |
| bmv_map_marker | 40 | BMN 28 (on BM&V's worlds and the north), Valenwood 12 |
| bmv_book | 12 | each placed once |
| bmv_settlement / _cell | 88 / 5,096 | 86 settlements, 2 sites |
| bmv_interior_exit | 293 | |
| bmv_shell | 1,889 | building refs in settlements' exterior cells, by `bmv_shell.py` (below) |

## Shells: rooms without load doors

`python3 -m tools.argonia_world.bmv_shell build` reads every STAT or SCOL ref the load order places in a
settlement's exterior cells (83,773), keeps buildings by base model and editor id (houses, huts, towers, tents,
ships; walkways, docks and platforms as class X) at least 200 units a side and 100 high, and measures the winning
NAVM inside each footprint (the OBND box turned by the ref's rotation). `verify` proves every ref is a row or
excluded with a counted reason (nature 67,979, not a building 4,079, wall 1,357, clutter 1,344, small 846, ...).
Class A: navmesh inside joined to the street, >= 10 triangles; B: 1 to 9 joined; C: inside, not joined; D: none
inside (441 of the 595 stand where there is no navmesh at all, `navmesh_around` false: most of Valenwood); X:
walkway or platform. Built 2026-11-08 in 14 s.

| settlement | A | B | C | D | X |
|---|---|---|---|---|---|
| bmv.lilmoth | 14 | 12 | 19 | 7 | 15 |
| bmv.valenwood.eldenroot | 9 | 10 | 10 | 44 | 201 |
| bmv.blackrose | 5 | 9 | 26 | 29 | 61 |
| bmv.blackmarshnorth.manor (Dres village) | 5 | 7 | 0 | 2 | 2 |
| bmv.blackmarshnorth.thorn1 (Thorn) | 4 | 15 | 38 | 12 | 16 |
| bmv.longmont | 3 | 6 | 1 | 1 | 0 |
| bmv.dock5 (Helstrom dock) | 3 | 1 | 2 | 4 | 25 |
| bmv.murkwood | 2 | 1 | 1 | 40 | 115 |
| bmv.valenwood.bosmer (Silvenar) | 2 | 10 | 1 | 15 | 56 |
| bmv.helstrom | 1 | 3 | 10 | 7 | 0 |
| bmv.blackmarshnorth.marsh | 1 | 4 | 2 | 8 | 0 |
| bmv.blackmarshnorth.tear1 | 1 | 3 | 5 | 1 | 0 |
| bmv.altenmeirhall | 0 | 3 | 19 | 1 | 3 |
| bmv.murkmire | 0 | 4 | 1 | 34 | 5 |
| Woodhearth, gg, Haven, Falinesti (2), Arenthia, Southpoint, town2 (no navmesh) | 0 | 0 | 14 | 304 | 158 |
| 44 other settlements | 36 | 26 | 17 | 86 | 271 |
| all 86 | 86 | 114 | 166 | 595 | 928 |

A quest or home cites a shell by `bmv_shell.id` (the ref's form key, e.g. `0246BE:Black Marsh.esm`, Styrr's house
shell in Lilmoth) and reads its `settlement`, `x y z`, footprint and nearest `door`; prefer class A, and a shell
with an `owner_verdict` of the owner's walk. Navmesh is a proxy: `sunk_m` (ground above the origin; 65 A/B shells
are over 8 m sunk or 5 m above the ground) and the class need the owner's walk before a quest leans on one.

## Mapping coverage (place_bmv 19, npc_bmv 0, faction_bmv 0)

Mapped (10):
- High: Lilmoth, Blackrose, Helstrom, Hereguard Plantation, and now Thorn (BMN's worldspace is named Thorn; its
  map marker Thorn stands in `bmv.blackmarshnorth.thorn1`, with guards, soldiers, prisoners and slaves; the lore
  sets Thorn toward Tear, story/lore/thorn.md).
- Medium: Longmont, Alten Meerhleel (BM&V's AltenMeirhall), Murkwood Verge, Low-Reed Village (BM&V's unnamed Village east of Lilmoth, QA6; not the Hatching Pools).
- Low: Blackrose Prison (interior 01BlackRoseJail, door in BM2; BMN's map marker "Black Rose Jail" stands at
  BlackMarsh 31,-15 by Blackrose with no door there).
Waiting (9): Stormhold, Gideon, Soulrest, Archon, Alten Corimont, White Rose Prison, Rockspring, Greenspring,
Rockgrove: no editor id or name of any record in the four files names them (searched every record).
Valenwood: story/lore has no Valenwood place and our design none, so nothing maps there.
BM&V's actors are generic (creatures, "Villager", "Guard"); none is a designed person and none of its 13 factions a
designed faction, so `npc_bmv` and `faction_bmv` are empty.

## Changed citations (the full load order)

Black Marsh North.esp deletes placements that the Act I records cited: the Breton merchants 0AA64F, 0AA650 (MQ03,
Hereguard), the Daedroth pack 1453EF-1453F3 (MQ01), the Restless Dead 0AA65F and the crocodile 1453FD (MQ03), the
eight `SoM_00EncDraugrzombiez1` (084AF9 first) and 120E0A, 120E0B (MQ04). MQ05's "no actors at Helstrom" is no longer
true. The quest rows, quest_thing, quest_record_source, act1-on-bmv.md and blocks.md now say so.

## Unresolved

- MQ05's Hall of the Scalded Throne is "centuries empty", but BMN puts two merchants and a soldier in its interior
  `01cellDUPLICATE002`: a call for the quest writer.
- Valenwood's two start-game-enabled quests (0MainQuest1, AANEWQuestM) start on a new game: the shutdown and
  `mods/allowed-quests.json` were built on the trimmed BM&V and should be re-read against the full stack.
- Mappings for the story side to rule on: BM&V's Murkmire (BlackMarsh2 -22,20, marker 0821A2, 53 actors) against
  the designed Murkmire places (the lore puts the region south-east of Lilmoth); "Dres village" (marker 0821A8) against
  the Dres Rows and Old Pens; Tear (3 markers, a ship landing at 25,19 attached to no settlement, the book `01tear`)
  against Tearmouth; Valenwood's Capital (marker Falinesti) and falinesti, four squares apart, may be one city.
- 359 exterior cells with refs lie in no settlement (BMN 201, BM2 113, Valenwood 45), among them Argonian soldiers
  and Redoran guards at BMN 8..9,27..28 and the marker "Southern Morowind Pass" (BMN -8,27); BM2's far-west cells
  -35..-33,23..25 (1,340 refs, no LAND) are drawn as empty squares.
- BM&V's 6 regions (REGN) and its climates are not drawn or tabled; only three regions carry polygons.
- Display names for the editor-id settlements without a map marker are owed by the story side.
- Templated actors may inherit race and name: `template_flags` records it, but the inheritance is not resolved.

## Review rounds

- Round 1 (an independent `research` reviewer, briefed with the paths only): re-derived every table from the four
  files and found no wrong census row, and 13 findings in this write-up and in the judgement calls. Fixed in the
  write-up: the counts of exits, settlement cells, place_bmv rows and height-less LAND; Valenwood's edited interiors;
  the "kept as the masters made them" claim; BMN's 13 neutralised load doors; the Blackrose ship door and the
  Valenwood cave path; the unused old Black Rose; the map claim, now limited to exterior placements. Left for the
  story side (Unresolved): Murkmire, Dres village, Tear, Capital and falinesti; regions and climates not drawn.
- Round 2 (a fresh reviewer): recounted every winner, placement and door and found none wrong; six minor findings.
  Fixed: BMN's 765 edited cells; the map frame now holds every census cell (40 cells with refs but no LAND lay
  outside it) and `verify` checks it; the Blackrose door's square; the Abandoned Shack door; the vanilla interiors'
  missing exit rows explained. Recorded as unresolved: the 359 content cells outside any settlement.
