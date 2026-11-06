# C. Interiors and places: the true count, and the options

Written 2026-11-06 for the owner's question C. Read-only research; nothing built. Owner ruling the same day: the
default is BM&V as it is, minor edits only, for a first story slice.

## Method

An independent script (not bmv_census.py, not the story/data rows) read the four plugins at
`~/.argonia/stack/MO2/mods/bmv/` and Skyrim.esm, Update and the DLC (only to resolve vanilla targets): every interior
CELL (the DATA interior flag and the group type agree on every one); every exterior REFR with a live XTEL (a load
door), resolved to its target's cell; doors followed onward from those interiors; BMN's deletions applied.
Building shells: STAT references whose model is a whole building, from a curated model list (a floor, not exact).
Settlements: the census grouping (`bmv_settlement_cell`), else the nearest anchor.

## True counts

- **All four plugins: 71 interior cells** (54 new BM&V, 17 overrides of Skyrim and Dawnguard). Per plugin, new and
  overrides: Black Marsh.esm 24 and 5 (BMN deletes 3 of the 24), BMN 11 and 9, Valenwood.esp 22 and 7, BosmerArmor 0 and 4.
- **103 exterior load doors** (BlackMarsh 18, BlackMarsh2 23, BlackMarshNorth 12, Valenwood 50) reach **43
  interiors**; chains add 3 in Valenwood: **46 reachable**. Of the other 25, 12 are BM&V's doorless interiors (Gallows
  Rock, Darklight Tower and others; census.md), 13 are vanilla interiors BM&V only edits.
- **The three Black Marsh worlds: 53 doors lead to 26 distinct interiors**, and chains add none: 7 houses or halls,
  13 caves, ruins, dungeons or jail, 4 ships or dock links, 2 Skyrim interiors (Windpeak Inn, Cragslane). BM&V's own:
  24. **The census was right; adaptation.md line 112 ("34") was wrong** and should read 26 (24 BM&V's own).
- **Shells:** 575 whole-building shells stand in the three worlds; 26 (4.5%) have a load door within 1,000 units.
  355 door objects open nothing (no XTEL).

## Per town

| town | load doors | distinct interiors | enterable buildings | shells |
|---|---|---|---|---|
| Lilmoth | 6 | 6 | 2 (houses or taverns), plus a dungeon, 2 ships, the book portal | 23 |
| Blackrose | 3 | 2 | 1 (two shack doors share one interior), plus the ship | 66 |
| Helstrom with its landing | 12 | 4 | 2 (9 doors share one house interior; the hall), plus a ship, 01Exit2 | 105 |
| Murkmire | 1 | 1 | 0: the ship only | 17 |
| Thorn | 3 | 1 | 0: the ship only | 102 |
| Tear | 1 | 1 | 0: the ship only | 12 |
| Hereguard | 0 | 0 | 0 (9 door pieces on kit-built houses) | 0 |
| Alten Meirhall | 1 | 1 | 0: a Dwarven ruin | 21 |

Black Marsh's towns are mostly facades: about one enterable building per town. Script and full tables were kept off
the tree (they read game files); the method above reproduces them in about 30 seconds.

## Options

| | what | effort | risk | to the adaptation (§3, §4) | to the phases | to the owner's walk |
|---|---|---|---|---|---|---|
| **C1** BM&V exactly as is | shoehorn ~40 rooms into 24, plus exterior scenes | none | many quests forced outdoors or shared rooms; seats clash | allocation strains; more exterior scenes | none | towns feel empty |
| **C2** BM&V as is, a non-clashing subset first | the owner's ruling: a slice of lines that fit the 24 rooms and doorless 12 | small | low | §4 subset chosen; the rest waits | Phase 3 and 4 unchanged | a real test of the concept |
| **C2i** then add buildings only | a door on an existing shell, leading to a new or re-used interior | a door plus an interior each; one block | low: doors and interiors are proven kinds | every shell becomes a possible room: 549 available | one Phase 3 block, used in Phase 5 | towns gain doors where buildings already stand |
| **C2ii** then add land too | as C2i, plus question B's patches | B3's | B3's | B3's | a world track after Phase 4 | B3's |
| **C3** build many places first | new interiors and land before the quests | weeks to months | high: world before story, the old failure | redone around the new places | delays Phase 3 | many looks first |
| **C4** re-use vanilla interiors re-dressed (0012 point 6; ruling 2026-10-30) | copy Skyrim interiors behind BM&V shells, swap Nordic clutter | low per room | some Nordic look (allowed in interiors) | fills the 40-room need | fits C2i | more rooms soon |
| **C5** interior-only expansion | doors into the doorless 12 and new interiors under existing land | low | low | §3's "doorless next" rule, wider | as C2i | dungeons and halls |
| **C6** kits from other Black Marsh mods | import interiors or prefabs from another mod | per mod: permission, masters | licence and clash | depends | new dependency rows | varies |

## Recommendation

**C2 now, growing by C2i with C4 and C5 as its sources of rooms.** Start the story slice on BM&V as it is; when a
line needs a room, put a door on one of the 549 standing shells and furnish a re-dressed vanilla or new interior
behind it, or give a doorless interior its door. That is one new building block (a door on a shell to an interior),
proved once in Phase 3, then copied. C2ii follows only if B3 is approved; C3 no.
