# Phase 4: the first story slice, built from the proven blocks

Status: [PROGRESS.md](../PROGRESS.md). The plan: [PLAN.md](../PLAN.md). Edit this file as the phase goes; it is the phase's whole brief.

- **Dialogue and text** for every speaker in the act, through `dialogue-write` and `text-review`, from Phase 2's
  records (now final).
- **Build the slice** (the opening act with the new-game flow and the opening scene, our Helgen, plus the chosen
  faction and questline subset) from Phase 3's blocks only: every stage, trigger, condition and effect is a copy of a proven
  block's shape; anything the act needs that is not a block goes back to Phase 2's method (a new block, proved first)
  or the quest is re-authored. The Phase 1 opening (the lightest form of the work detail) is replaced by the act's
  authored opening.
- **The world map, block W-wrld-map (built 2026-11-08; owner check owed).** The native 3D map of the real
  worldspace. As built: (1) `tools/ArgoniaPlugin/MapFix.cs` (called from Generate.cs; no new forms) overrides the four
  worlds' WRLD from the load order's winner (BlackMarsh extends the opening's override) and sets only MNAM's NW/SE
  cells. What differs from the plan: vanilla's convention, measured, is usable dimensions 0,0 (Tamriel, Solstheim) and
  an NW/SE box that is the camera's pan area well inside the land (Tamriel land x-57..61 y-43..50, box NW(-30,15)
  SE(40,-40)), so each box is the world's measured LAND extent (`plugin.sh mapprobe`) a quarter in from each side:
  BlackMarsh NW(-18,4) SE(18,-25), BlackMarsh2 NW(-17,16) SE(16,-15), BlackMarshNorth (Thorn) NW(-17,16) SE(16,-16),
  Valenwood NW(-16,19) SE(17,-16); camera kept; Valenwood.esp a master; the read-back (`plugin.sh check`) checks the
  box, that nothing else differs from the winner, and the marker names. (2) `infra/gpu-box/lodsettings.py`, run by
  `stack.py stage`, writes the derived mod `argonia-lodsettings` (LODSettings/BlackMarsh.lod -64,-64,128,4,32;
  BlackMarsh2.lod -32,-32,64,4,32; BlackMarshNorth.lod -32,-32,128,4,32) from BM&V's .btr names, the rule that
  reproduces BM&V's own Valenwood.lod; never committed. (3) Marker 0934A4 "Lolmoth" is "Lilmoth" and 083283
  "Southern Morowind Pass" is "Southern Morrowind Pass" (name-only); "Unkown Cave" (Valenwood.esp 18F86D) stands in
  Skyrim's Tamriel, not our worlds, and is left. No `sMapWorldDefaultWorldSpace`. (4) One owner check: M on Lilmoth's
  dock, in Thorn and in Valenwood. If the map is still Tamriel or blank, the next step is in Phase 5.
- **Rooms without load doors.** BM&V's towns stand many shell buildings you walk straight into (Lilmoth: 6
  exterior load doors, 52 shells). Done 2026-11-08: the `bmv_shell` table (`tools/argonia_world/bmv_shell.py`
  build/verify) holds 1,889 building refs in 86 settlements' exterior cells, classed by the winning navmesh inside
  each footprint: A 86 (joined to the street, >= 10 triangles), B 114, C 166, D 595, X 928 walkways and docks;
  counts per settlement in [census.md](../research/bmv/census.md#shells-rooms-without-load-doors). Quests and homes
  cite a shell by its `bmv_shell.id`, never "a house". Left: one owner walk into Lilmoth's 14 class-A shells, its
  verdict in `owner_verdict` (navmesh is a proxy, not proof; shells stand up to 12 m sunk).
- **Loop**: read the files that the game will consume and verify (to the extent that you can) that everything you intended to implement has been implemented correctly. If not, diagnose, fix, then repeat this loop until your read of the built game files (esm and plugin and whatever else) does meet this bar. But do not run the actual game yourself, just read/mine from the game files that you build. *Then* pass on to the owner.
- **Owner test:** play the slice from a new game: the new-game flow, the opening scene, the opening act and the
  chosen faction lines.
