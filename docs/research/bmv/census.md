# The BM&V census (phase 1)

`Black Marsh.esm` (BM&V's only plugin; masters Skyrim, Update and the three DLC) read by
`tools/argonia_world/bmv_census.py build` into the `bmv_*` tables of `story/data/schema.sql`. Master forms that BM&V
points at (races, classes, factions, actor bases) take their names from the masters. `bmv_census.py verify` recounts
from the ESM and compares with the db. `db check` is green and every foreign key resolves.

## Counts

| table | rows | note |
|---|---|---|
| bmv_worldspace | 4 | BlackMarsh 23D689 (1,409 cells), BlackMarsh2 0D6960 (3,381 cells), plus Tamriel and Solstheim overrides |
| bmv_cell | 4,826 | 29 interiors; 855 cells have navmesh; 3 worldspace persistent cells |
| bmv_location | 7 | 6 LCTN overrides of vanilla Skyrim locations, plus 1 named by a cell: BM&V has no LCTN of its own |
| bmv_npc | 243 | 130 NPC_ records in the file, the rest master bases its ACHRs place; no LVLN |
| bmv_placement | 1,139 | 251 are people (race has ActorTypeNPC), the rest creatures; 6 start disabled |
| bmv_faction / bmv_npc_faction | 84 / 255 | 6 in the file (2 "Prisoners Faction", 3 merchant factions, 1 override) |
| bmv_race / bmv_class | 68 / 42 | |
| bmv_quest | 3 | 01Captain "Welcome to Black Marsh" (start-game-enabled, priority 30); 2 vanilla overrides |
| bmv_door | 79 | load doors; 78 pair inside the file |
| bmv_settlement / _cell | 24 / 1,403 | 0 sites: every interior that has an exit lands near a named cell |
| bmv_interior_exit | 40 | |
There are no map markers, no FULL names on exterior cells, and only 36 exterior cells have editor ids. The
settlements are grouped from those 36 names (editor ids, so `name` is a label such as `Grass` or `DWARVEN`, not a
display name). A settlement's squares are its named cells, the squares within 1 of them, and squares with content
nearest them within 8. Its interiors are found through the door graph.

## Settlements (cells / interiors / placed actors / people)

| settlement | world | cells | int | actors | people |
|---|---|---|---|---|---|
| blackrose (Blackrose, Blackrosemarket, Blackrosegate, mound) | BM | 72 | 2 | 135 | 67 |
| village | BM | 34 | 0 | 112 | 17 |
| swamplandsrose (+SPOT) | BM | 52 | 0 | 106 | 1 |
| longmont | BM | 42 | 1 | 100 | 5 |
| dwarven (+pyramid; Nzech ruins) | BM2 | 159 | 2 | 99 | 17 |
| lilmoth (Lilmoth, LilmothHist, Pussbottom, Dock1) | BM | 38 | 3 | 66 | 12 |
| temple | BM2 | 84 | 0 | 66 | 8 |
| murkwood (+dock4) | BM2 | 113 | 0 | 60 | 35 |
| hereguardplantation | BM | 20 | 0 | 45 | 10 |
| altenmeirhall | BM | 34 | 0 | 43 | 21 |
| banditcamp1, tribe, castle, outercave, dock2 (+BoattoBlackMarsh), grass, murkwoodext | | 13-68 | 0-2 | 21-39 | 0-12 |
| murkmire (+Murkmire1), temple2 (01BlackRoseJail), dock5 | BM2 | 63-134 | 0-1 | 1-11 | 0-9 |
| helstrom, dock3 (+BlackRoseold), mountainpass, therose | | 11-108 | 0-2 | 0 | 0 |
Helstrom has 9 house doors into one shared interior, `01ArgonianHouseinside`, but no actors at all.
Outside every settlement: 83 placements, 251 content squares and 6,612 refs (scattered wilderness). Twelve
interiors have no load door, in or out: 01Cavebig (723 refs, 10 actors), 01newcell1, 01Som_CaveDUPLICATE003,
01Som_Cave2, 01Dwarmerhome, 4 smaller ones, and 3 vanilla overrides. They are orphans, unreachable without a door
of ours.
## Main town cells

- Lilmoth: 00596F (3,-1). Dock1: 00591F. LilmothHist: 005A0D. Pussbottom: 005A0B.
- Blackrose: 0AFC34 (33,-14). Blackrosemarket: 0AFD1E. Blackrosegate: 0AFD20.
- Helstrom: 0D794B (BM2 -7,21).
- Longmont: 07548F. HereguardPlantation: 005919. AltenMeirhall: 039727. Murkwood: 0D73AF.
## How the worldspaces are entered
Only ships connect the worldspaces.

- **From Skyrim:** door 00AC5C stands in Tamriel at square (38,13), under the sea, on base `OrcDoorLoad01`, a Nordic
  element (decision 0006). It leads into ship interior `01ShipDUPLICATE001`, which exits at Lilmoth (BM 1,-3).
- **BlackMarsh to BlackMarsh2:** ship `01Ship` has exits at Lilmoth (7,-1), at Dock2 (10,-2) and at BM2 dock5
  (-10,12). Ship `01dock3to4` has exits at Blackrosegate (33,-18) and at BM2 Murkwood (18,1).

## Mapping coverage (place_bmv 18, npc_bmv 0, faction_bmv 0)
Mapped (8):
- High: Lilmoth, Blackrose, Helstrom, Hereguard Plantation.
- Medium: Longmont (BM&V places it north of Blackrose, the lore south-west), Alten Meerhleel (BM&V's AltenMeirhall
  is east of Lilmoth, the lore north-west), Murkwood Verge (to BM&V's Murkwood).
- Low: Blackrose Prison (to the interior 01BlackRoseJail, whose door is in BM2).
Waiting (10): Stormhold, Gideon, Thorn, Soulrest, Archon, Alten Corimont, White Rose Prison, Rockspring,
Greenspring, Rockgrove. Each row cites its lore file.
BM&V's actors are generic: creatures, and "Villager", "Merchant", "Prisoner". None of them is a designed person, and
none of its 6 factions is a designed faction, so `npc_bmv` and `faction_bmv` are empty.
## Unresolved

- Display names for the editor-id settlements are owed by the story side.
- Templated actors (10 BM&V NPCs, 67 master bases) may inherit race and name: `template_flags` records it, but
  the inheritance is not resolved.
- 19 master load-door bases are placed without XTEL. Nobody has checked what they are.
