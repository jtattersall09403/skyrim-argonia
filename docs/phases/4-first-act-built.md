# Phase 4: the first story slice, built from the proven blocks

Status: [PROGRESS.md](../PROGRESS.md). The plan: [PLAN.md](../PLAN.md). Edit this file as the phase goes; it is the phase's whole brief.

- **Dialogue and text** for every speaker in the act, through `dialogue-write` and `text-review`, from Phase 2's
  records (now final).
- **Build the slice** (the opening act with the new-game flow and the opening scene, our Helgen, plus the chosen
  faction and questline subset) from Phase 3's blocks only: every stage, trigger, condition and effect is a copy of a proven
  block's shape; anything the act needs that is not a block goes back to Phase 2's method (a new block, proved first)
  or the quest is re-authored. The Phase 1 opening (the lightest form of the work detail) is replaced by the act's
  authored opening.
- **The world map, block W-wrld-map (planned 2026-11-08 at the owner's ask; not built yet).** The native 3D map of
  the real worldspace, the easiest and most reliable route (research of 2026-11-08 in
  [Phase 1](1-stack-in-bmv.md) "The map"): (1) WRLD overrides in our plugin for BlackMarsh, BlackMarsh2, Thorn and
  Valenwood setting MNAM's usable cells from their NAM0/NAM9 bounds (BlackMarsh NW (-36,20) SE (36,-39), BlackMarsh2
  NW (-35,32) SE (32,-31), Thorn NW (-32,41) SE (32,-32), Valenwood NW (-34,37) SE (36,-34)), camera kept,
  Valenwood.esp a master; the read-back checks MNAM in out/Argonia.esp; (2) the deploy writes
  `lodsettings/BlackMarsh.lod`, `BlackMarsh2.lod` and `BlackMarshNorth.lod` from the extents of BM&V's own .btr
  files (BlackMarsh: -64,-64, 128, 4, 32), generated on the machine, never committed; (3) Black Marsh North's map
  marker `0934A4` renamed "Lilmoth" (it reads "Lolmoth"), and its "Unkown Cave" and "Southern Morowind Pass" typos
  fixed, by name-only overrides; `sMapWorldDefaultWorldSpace=BlackMarsh` under `[MapMenu]` only if (1) alone does
  not take; (4) one owner check: press M on Lilmoth's dock, in Thorn and in Valenwood: BM&V's land, pan and zoom,
  markers. A few hours and one check. If the map is still Tamriel or blank, the next step is in Phase 5.
- **Rooms without load doors.** Lilmoth has 6 exterior load doors but about 60 shell buildings, most of them hollow
  and walkable from outside (vanilla Solitude, Markarth and farmhouse shells; measured by navmesh inside each
  footprint, 2026-11-08: [lilmoth-walkin-shells.tsv](../research/bmv/lilmoth-walkin-shells.tsv), class A = 14
  houses with navmesh joined to the street, B and C need a look). Quests and homes use them as rooms and cite the
  shell's ref key, not "a house". Before the first quest uses one, the census gains a `bmv_shell` table (ref, base,
  cell, footprint, class, navmesh joined, floors, nearest door) for every settlement, and the owner walks into the
  class-A list once (shells stand 100 to 800 units sunk, so navmesh is a proxy, not proof).
- **Loop**: read the files that the game will consume and verify (to the extent that you can) that everything you intended to implement has been implemented correctly. If not, diagnose, fix, then repeat this loop until your read of the built game files (esm and plugin and whatever else) does meet this bar. But do not run the actual game yourself, just read/mine from the game files that you build. *Then* pass on to the owner.
- **Owner test:** play the slice from a new game: the new-game flow, the opening scene, the opening act and the
  chosen faction lines.
