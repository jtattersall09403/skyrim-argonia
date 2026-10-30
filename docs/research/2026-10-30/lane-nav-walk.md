# Lane nav-walk: real collision for the block navmesh, door triangles (2026-10-30; handed off at the context mark)

## Route taken: real collision (no fallback)
- **The meshes are already on the build VM.** The laid MO2 stack is at `~/.argonia/stack/MO2` (KotM's BSA, htbm,
  bmv, mud-mother-grove, Ferries), and the vanilla BSAs are in `~/games/skyrimse/Data`. No sync from the game machine
  was needed, so infra/gpu-box gained no helper.
- `tools/navmesh/bsa.py` reads SSE BSAs (v105 LZ4 frames, pure Python, with no new dependency) by byte range.
- `meshes.py` resolves a MODL the way MO2 does: loose files in modlist order, then the mods' BSAs, then the game's.
- `nif.py` reads collision from NIF 20.2.0.7 (layout from niftools nif.xml):
  - shape types: CMS chunks and big tris, packed strips, convex hulls, boxes, transform shapes, lists, rigid body T;
  - layers kept: the solid ones only (Havok scale 69.99125).
- **Checked against OBND** for every Claywater base: the collision bboxes match the bounds (dock, barrel, house1,
  pods). 78 refs have collision, 8 have none (plants and markers, as in game), 0 fall back to a box, 9,115 triangles.
- `placed.triangles` replaces `placed.boxes`. ArgoniaNav rasterises the triangles (walkable up to 45 deg) and:
  - **makes the ground solid**: spans below the ground span merge into it, or buried hut bases became floor and the
    ground beside them read as a ledge;
  - snaps each vertex to the nearest surface, ground or object, within snapMax;
  - **erodes cells that hold placed collision by 16, not 32** (params.OBJECT_AGENT_RADIUS). At 32 the doorframe slab
    in front of the station-house door (125 deep, 45 above the ground) eroded away. Measured: radius 16 alone
    connects it; cs 8, a 60-deg object slope and climb 48 were tried and are not needed. Ground-only cells are
    unchanged, and the gate's navmesh sample hash is unchanged.
- `checks.py` heights read the object surfaces. `paths.py` runs A* over our NVNM triangles and Portal links.

## Measured (block claywater, `python -m tools.navmesh build --block claywater`, 13 s, peak 236 MB)
- L1 green: 0 degenerate, 0 heights over (vertex max 31.2), 1,908 links all symmetric, NAVI 64/64; main component 152,764 m2.
- Paths from Livia's day spot (-231193, 47690, 2568) to each door's arrival point (the linked door's XTEL):

  | Door | Before | Now |
  |---|---|---|
  | **station house (000892)** | not on navmesh | **on navmesh, a 12-triangle path** |
  | polers 0008B7, family 0008BC, store 0008C3 | not on navmesh | on navmesh, no path |

- **Why the pods have no path:** each arrival point lies under the KotM mud pod's (smpodext01) dome. At the dome's
  mouth the shell is about 100 units above our ground (y 52450 at the polers hut), under the 128 agent height. This
  is a placement/ground question, not a navmesh bug, and it is open.

## Door triangles: the rule is measured, the code is not written
- **Vanilla rule** (Skyrim.esm, 426 door triangles in 300 NAVMs, 185 exterior and 241 interior; 426/426 match): the
  door triangle is the triangle that holds the **arrival point**, the linked door's XTEL position, and it carries flag
  0x400.
- **Blocker (design):** our doors are Argonia.esm REFRs, while the NAVMs are in ArgoniaWorld.esm. That plugin cannot
  master Argonia.esm (the masters would be circular), so the door data must be a NAVM override in Argonia.esm.
  - Argonia.esm is committed as Spriggit YAML. The overlay must therefore be generated inside `ArgoniaGen generate`
    (PlaceCells.cs), which is outside this lane's paths.
  - The NAVI need not be copied: Update, Dawnguard, KotM and Black Marsh each override the NAVI with only their own
    NVMIs (313 to 4,379 entries against Skyrim's 15,462). So the engine merges the NAVI, and Argonia.esm's NAVI
    override can carry just the door cells' NVMI (with door links).
- **Interiors:** the 4 houses are KotM interiors; their doors keep KotM's refs (8933E1 and others), so KotM's own
  door triangles should still point at them. This is not yet checked.

## Left, in order
1. A `doors.py` pass, from the intermediate: per exterior load door, the arrival triangle gets flag 0x400 and an
   NVNM door entry, then the L1 check "door triangle within 1 m on both sides" (failed once on purpose).
2. The overlay in Argonia.esm: NAVM overrides plus the partial NAVI, with masters [Skyrim.esm, ArgoniaWorld.esm] and
   self Argonia.esm, through NavmeshRecords.Parse. This needs PlaceCells.cs/Generate.cs (ask the planner for the path).
3. Check the KotM interior NAVMs: their door triangles and the bed reachable from the interior arrival point
   (8622, -5157, 5712).
4. `make navmesh` (the province with real collision, about 26 min), then `make plugin` twice with the same hash, plugin-check and `make check`.
5. Tell game-8 (ace72a7eb30f15ba8) to re-run claywater-walk's night step.
6. The pods' mouth clearance (backlog).

Not done: steps 1 to 5, `make check` (only `pytest tools/navmesh` and the navmesh sample hash were run), and game-8
has not been told. In game the porch exists only after step 4, and the door link only after step 2.
