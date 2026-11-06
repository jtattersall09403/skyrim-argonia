# B. Extending BM&V's land to fill out the province

Written 2026-11-06 for the owner's question B. Read-only research; nothing built. Owner ruling the same day: the
default is BM&V as it is for the first story slice.

## What the lore wants that BM&V lacks

The allocation (story/design/quests/adaptation.md §4) already homes Stormhold on BMN's Marsh, Gideon on the Castle,
Soulrest on the Docks; Archon, Rockspring and Hissmir are "named in talk only". The lore's west (Shadowfen, Blackwood
and Gloommire; story/lore/regions/) and the real city scale (story/lore/city-scale-comparison.md) are not in BM&V.

## How BM&V's author built the land (measured)

- **LAND:** 10,530 cells in four worlds (census.md). Each world is an island ringed by flat sea floor at -2,048
  units, water at 0 everywhere, no per-cell water heights: simple, hand-sculpted CK land.
- **Textures:** 31 LTEX, all new; LAND uses 73 textures (28 BM&V's, 45 vanilla), at most 6 layers a quadrant, the
  vanilla cap. New land can paint with the same set.
- **Objects:** buildings are mostly static shells: of 575 building shells in the three worlds, 26 (4.5%) have a load
  door (c-interiors-and-places.md). Trees and rocks are vanilla and BM&V statics placed by hand.
- **Navmesh:** 23,329 NAVM, covering only 27% of LAND cells: the author navmeshed towns and paths, not the wilds.
- **LOD:** loose files, generated once (btr/bto/btt per world); only Valenwood ships a `.lod` settings file.
- **A free site:** BlackMarsh2 cells -35..-33, 23..25 hold 1,340 references with no LAND.

So the land is extendable by its own method: CK sculpt and paint, place kit statics, navmesh by hand or the CK's
auto-generate, then regenerate LOD with xLODGen or DynDOLOD on the play machine (GUI only, hours a world).

## What the old project's failure teaches (git before d269dbf5; 0028, 0031, 0033; rounds 1 to 6)

1. **Off-game checks do not prove land looks right.** Generated terrain passed every check and showed swathes of one
   texture, hard edges, 10% of land over 45 degrees and 674 cells overflowing VHGT; 20,165 placed water planes
   hovered or went black. Only the owner's eye judged it.
2. **LOD is a GUI job** with no headless mode (xLODGen, TexGen, DynDOLOD; the CK's LOD crashes on big worlds). A BSA
   of 21k loose files killed every launch (5a31e186). Each land change means a LOD rerun on the play machine.
3. **Navmesh** generated off game was never proven in the engine; a NAVM absent from NAVI is ignored.
4. **The process cost more than the tools:** eight days, three designs, six rounds, 340 commits in the world tools,
   34 owner findings in one playtest, then the pivot (0038).

The difference now: hand CK work on a small patch beside BM&V's own land, in BM&V's own textures and kit, is not a
generator. But it is still "making a world", which PLAN §6 excludes, and the look is judged only by the owner.

## Effort, by size

| size | what | agent effort | owner time | risk |
|---|---|---|---|---|
| a site | one new place on BM&V's existing land: a ruin, a camp, a town quarter of kit shells | 1 to 3 days | one look | low: no new land, no LOD rerun beyond objects |
| a patch | 10 to 50 new cells off an existing coast (e.g. Archon on a new headland) | 2 to 4 weeks with CK on the play machine | 3 to 5 looks | medium to high: edge seams, textures, LOD rerun |
| a region | the west, Stormhold's real country: hundreds to thousands of cells | months | many rounds | very high: the old project's scale and failure mode |

## Options

| | what | for quests and factions | for the plan |
|---|---|---|---|
| **B1** no new land | BM&V as it is; Archon and others stay talk-only | allocation unchanged | none |
| **B2** sites only, on existing land | new built places on BM&V's land (ties to C) | adds homes for talk-only places, re-seats a line if wanted | a Phase 3 block ("a built place"), reused in Phase 5 |
| **B3** one patch, as a world track after Phase 4 | one new coastal patch for the most-wanted missing city | the allocation gains a home; the ledger, census and map are rerun | a world track beside Phase 5, owner looks gated, needs CK on the play machine |
| **B4** a region before Phase 3 | fill out the province first | the whole allocation is redone | delays every story phase by months; repeats 0038's failure |

Cross-system costs of any new land: the census and the map rerun (tools exist); LOD rerun per touched world;
navmesh for every walkable new cell; performance unknown until played; BM&V updates may move cells we abut.

## Recommendation

**B1 now (the owner's ruling), B2 as the way to grow, B3 only after Phase 4 and only if a missing place is worth it.**
B4 no. Sites on existing land give most of what the story needs without new terrain, LOD or seams.
