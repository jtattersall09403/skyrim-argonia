# New buildings by hand: generated exteriors, matching shells, snap-together kits, agents at a 3D bench

Written 2026-11-24 for owner calls #93/#94, after the owner rejected PROPOSAL section 6 as timid. Research only; nothing
generated, bought or downloaded. Tags: [M] measured here (command or file:line given); [PAGE] a page I fetched;
[SNIP] a search-result summary only; [K] my modding or Blender knowledge, not re-fetched; [INF] my inference; TRIAL = only
a trial settles it. Method: hand work is the default; every "not feasible" below names the obstacle and the way through.

## 0. Live docs, and the one to edit

- Cover it already: `docs/research/new-art/PROPOSAL.md` section 6 (the timid plan: routes 1 to 6), `interiors.md` (held shells,
  GDC kit facts, route ranking), `skyrim-asset-pipeline.md` (PyNifly, collision, texel table), `docs/design/agent-view.md`,
  `place-look` skill (the eyes and hands), `place-rooms` skill, `docs/design/lod.md`.
- Confirmed: interiors are separate cells behind load doors; the held Argonian huts are one-piece shells at 80 to 120 % of the
  exterior footprint; 41 carried rooms come from 24 source cells and 18 are one cell; texel maths; 45 degree walk slope.
- Contradicted or superseded: (1) interiors.md section 5(d) "hard, hand repair, would not try before (c)" and section 6
  "new interiors out of scope": superseded; the repair IS the plan here. (2) interiors.md section 3 "no vendor guide for interiors":
  Tripo has one, but it covers furnishings only (section G). (3) PROPOSAL "boxes for flat kit pieces": see B.5, vanilla does not do it.
  (4) interiors.md "navmesh for a new shell unproven": the build already meshes an interior from collision (B.7).
- The one doc to edit: PROPOSAL.md section 6 and the "do not" list in section 7, rewritten whole from sections F and G below.
  interiors.md gets a one-line pointer. No new file beyond this report.

## Findings first

0. **Corrections folded in (owner, 2026-11-24).** House exteriors are closed shells (0 of 288 rays); doors and windows are textures on separate shapes, a door
   recess, a separate pane shape and a separate `WindowGlow` effect shape (A.2); the door is a DOOR record; the interior is a separate cell, so matching is
   correspondence (B.1), and walk-through structures are the exception (A.2c, C.3). Stairs have their own section H: vanilla interior stairs use real tread collision in
   most pieces [M], and Bethesda's stairwell opening is a floor piece with a hole.

1. **The agent's eyes already exist and need one addition.** `look` has named subjects, section, orbit, probe with a void probe in
   rooms, `place` / `move` / `turn` / `sink` / `duplicate`, capture validation (agent-view.md). What it lacks for new geometry:
   (a) a way to load a NIF/GLB that is not yet a catalogued base; (b) a grid-snap verb; (c) a Blender-side bench with the same verbs.
2. **Interior from collision exists.** `tools/places/build.py:1363-1420` (`recast_refs`, `_recast_refs`) meshes an interior cell's
   navmesh from the collision of its placed pieces with the same Recast parameters as the world (slope 45, climb 32, agent height 128,
   radius 32: `tools/navmesh/params.py:7-10`). A space with no `copy_of` is already a legal row (`build.py:920`: `plugin=None`).
   So a hand-built shell NIF with collision, placed in an authored cell, gets a navmesh from our own tool. [M] Gaps: the shell NIF
   with collision, the cell's lighting rows for a space with no source, and the studio loading the new model.
3. **Vanilla architecture is MOPP + compressed-mesh collision, not boxes.** I read the collision blocks of vanilla NIFs with our reader
   [M, command at section B.5]: Whiterun interiors 151 of 200 MOPP+bhkCompressedMeshShape (6 box/convex, 34 none); Nordic
   architecture 165 of 200 plus 28 convex-only; Whiterun building shells 81 of 124 (41 none); the 9 King of the Murkmire shells
   I could resolve 9 of 9. Even a flat 1024 floor tile is MOPP+compressed. So boxes-only shells are legal Havok but unprecedented in
   Bethesda's content; the safe path is the same blocks Bethesda wrote.
4. **PyNifly's MOPP compiler runs outside Blender and Windows.** `pyn/mopp_compiler.py` imports only `math` and `typing`;
   `compile_mopp(verts, triangles, radius=0.005, output_ids=None) -> (bytes, origin, scale)`; no OS call; no licence header
   [PAGE: raw.githubusercontent.com/BadDogSkyrim/PyNifly/main/io_scene_nifly/pyn/mopp_compiler.py]. VERIFIED for the compiler.
   It is bytecode only: the compressed-mesh chunk packing is `bhk_autopack.py` (pure Python per the pipeline report) and the blocks
   must still be written (niflod, nifly C++). Whether the game walks on its output is TRIAL 1. PyNifly is GPL; we never ship tools.
5. **Slope and size numbers we can hand an agent** [M unless tagged]: walk slope 45 deg, climb 32, agent 128 high and radius 32
   (params.py); Whiterun interior kit floors 256 and 1024 square, wall pieces 512 long by 512 high and 36 to 48 thick, doorway pieces
   256 wide by 512 high (bases.jsonl); KotM huts: door frames 155 to 190 wide by 210 to 299 high, partitions 280 to 307 high, interior
   shells 280 (house1in) to 980 high, plank walls 262 high, 494/743 long; vanilla door leaf 132 wide by 178 high (WRDoor02);
   128 units = 6 ft, about 70 per metre (UESP "Unit" [SNIP]).
6. **Ambition is justified by the data.** 144 of 258 places have buildings. The 19 Root-Folk places have 3 interior cells across all
   their source places (`source_place.interiors` summed, rank-1 source) and 22 households; the Sedge-Wardens have 3 for 13
   households. 126 places lean on vanilla-built sources, 154 on King of the Murkmire. Reusing the 21 held shells cannot serve that.
7. **The honest hard parts, in order:** (1) collision authoring (TRIAL 1); (2) the studio showing a new model (small code); (3) texel
   density by tiling materials (solved by method, A.3); (4) LOD for new exteriors (derived models exist: `lodmodels.py`, lod.md);
   (5) door pairing (records only); (6) agents judging 3D from renders (D); (7) the KotM no-AI clause beside its huts (F).

## A. Generated exteriors, made game-ready by hand

### A.1 What the generators give (evidence)
- Hunyuan 3D v3.1 Pro on fal takes up to 8 views (front, back, left, right, top, bottom, two 45 degree diagonals); $0.375 a
  generation plus $0.15 with multi-view; a Part Splitter endpoint exists, input details not read [SNIP: fal.ai Hunyuan pages].
  Tripo H3.1 multiview takes 2 to 4 views, order front/left/back/right, front required [SNIP: fal.ai tripo h3.1 multiview].
  The proposal's "Hunyuan up to 8 views" is right; Tripo is not.
- Tripo generate-parts and Segment split a mesh into parts; they cannot combine with texture/PBR/quad output [SNIP, interiors.md section 3].
  Rodin up to 10 reference images [SNIP]. Face limits and prices are in PROPOSAL section 3; I did not re-check them.
- Single-view generators return a closed outer hull, door painted on, inside solid [INF, consistent with interiors.md].

### A.2 What the agent does in Blender (all of it exists in Blender; the failure is in judging, section D)
Blender is not installed here (pipeline report line 23) and the build VM has no GPU. It is free GPL; `blender -b -P script.py`
runs headless on Linux [K]. Steps, each followed by a fixed-camera render (D.3):
1. Import GLB; apply transforms; scale to 70 units per metre; set origin at the base centre; Z up.
2. Clean: Merge by Distance, delete loose, Recalculate Normals (outside), Fill Holes; check with 3D-Print "Non-manifold" select. [K]
3. **Straighten and flatten.** Cut the base at a plane (Bisect, fill) at grade z=0; snap vertices of walls that should be straight to
   planes by scripted vertex alignment (scale-to-zero on an axis for a selected wall loop). Cheaper and more reliable: do not repair
   the hull, re-model over it (A.5).
4. **Door recess and painted windows, never holes (corrected by the owner's ray test).** Skyrim house exteriors are closed shells:
   0 of 288 rays got through riften\rtfarmhouse01, whiterun\wrbuildings\wrhouse02, farmhouse\farmhouse01 and KotM mudhuts\mudhut01 [owner's
   measurement, 2026-11-24]. I read the shapes of two of them with `nifglb.dump` [M]: **rtfarmhouse01** has a 4-triangle shape textured
   `RiftenDoor01` (the door painted into a recessed panel), a 16-triangle shape textured `RiftenWindows02` (the panes: one shape, flag
   set `16809985` unlike the walls' `32801`, no vertex colours), a separate `WindowGlow` shape (96 triangles, `BSEffectShaderProperty`
   with `RiftenWindows02_g.dds`, alpha-blended, translated to the window row: the night glow, switched by the game's day/night
   handling [K]) and separate log, plank, shingle, stone shapes; **wrhouse02** has a 66-triangle `WRWindows01` shape and a lattice shape.
   So the agent models: a door RECESS or frame (a notch 20 to 40 deep, 155 to 190 wide, 210 to 299 high, the KotM frame sizes) with
   a floor step; the working door is a separate DOOR record placed in it with the teleport link (our huts: `ThatchHutDoor01`,
   `argonia/blackwood/shackdoor.nif`, 1.6 m wide, 2.1 m tall [owner]); windows are a separate pane shape (own material, so
   it can take a glass/lattice/shutter texture), an optional frame and shutter mesh, and for night glow a separate effect-shader plane
   0 to 2 units in front of the pane with a `_g` greyscale glow texture (vanilla's own method; the pane shape and glow shape are
   separate so they are lit differently). No Boolean on the exterior is needed, which removes the need for a manifold hull
   (the hull need only be closed, not clean). Boolean remains for modelling recesses and for walk-through structures (A.2c).
5. **Separate parts**: Separate by loose parts or by material after assigning faces by normal and height (roof = faces above the eave
   line facing up; walls = near-vertical; posts = Tripo segment if it works). Each part gets its own material slot, so each can
   be tiled differently and each can be its own NIF shape.
6. **Re-UV for tiling (the texel-density answer).** Blender's `uv.cube_project` (Cube Projection, with `cube_size` set in metres)
   and the UV Project modifier give a world-scale, constant-density map on any size of part, because the UV is world metres divided by
   tile size, not 0-1 across the object [K, Blender manual UV > Cube Projection, UV Project modifier; not re-fetched]. With the
   tile 1.5 to 3 m, a 2K tile gives 680 to 1,360 px per metre at any building size (same maths as the proposal's table).
   - **Seams:** cube projection splits per face by dominant axis; a seam is invisible on a tileable texture, visible on a
     directional one only where the direction flips. Break at hard edges (corners, eaves) so seams sit where a real joint is.
   - **Faces at 45 degrees stretch.** Fix by bevelling the corner or splitting the island and projecting each from its own normal;
     the agent checks stretch with a checker texture render (Workbench shows it) before leaving the stage.
   - **Directional materials (planks, thatch courses, reed weave):** project each wall from its own axis and rotate the island 90
     degrees for vertical boards; roof thatch is projected along the slope (Project from View, aligned to the roof plane, or
     per-roof-face-group Cube). Planks that run along a post must be a separate part. Mixed-direction hull parts are separate shapes.
   - **Trim sheet:** one atlas with bands (eave, base mud course, door frame, lintel), the standard environment-art method
     (Polycount wiki trim-sheet pages [K, not fetched]); a hand-modelled frame piece takes UVs from the band, not a unique map.
7. **Grime, moss, wear without unique textures.** (a) Vertex colour: Skyrim's lighting shader multiplies diffuse by vertex colour when
   the shader's vertex-colour flag is set [K]; it only darkens or tints, which suits grime, damp at the base, moss tint on a neutral
   tile; the agent paints it by script from rules (height above grade: damp ramp; upward normals: moss; cavities by Blender's
   Ambient-Occlusion bake to vertex colour). (b) A second UV set: SSE BSTriShape carries one UV set [K, UNVERIFIED]; do not plan on it.
   (c) Decal overlays: thin separate shapes with alpha-tested grime/stain textures hovering 1 to 2 units off the wall, the way vanilla
   does moss and cobwebs [K]. (d) Unique generated texture only on ornament (carved lintel, mask, banner).
8. Triangle budget: 2,000 to 8,000 for a hut shell; Decimate (collapse) or the clean re-model keeps it.

### A.2b Entrances that are not a door in a wall [owner, folded in]
Skyrim reaches interiors by a load door or other activator entrance; the exterior never shows the inside. Other entrance types for a new
building are therefore the same mechanism, a placed activator/door with a teleport link, in a different dress: a hatch or trapdoor
(a flat door model in a deck), a window you climb through (a small shuttered door model; the player activates it), a cave mouth (a
recess in rock with the door model hidden inside), a boat's cabin hatch (a door on the hull), a ladder (a door record in a ladder-shaped
frame: Skyrim has no climbable ladders; a ladder is a load door or decoration, see H). The exterior model supplies the recess, hatch frame and
`_g`-style glow; the DOOR record supplies the link. Door pairing is records (place-rooms).

### A.2c True exceptions: open-sided and walk-through structures (enterable exteriors)
Stilt platforms, market halls, ruins, tents and boathouses are walked into with no load; they need walkable collision on floors and stairs and a roof above
the 128 agent height (see C.3). The owner's ray test let 37 of 288 rays through King of the Murkmire's thatch house: PARTIAL evidence it is open-sided or has a
small gap; I did not re-test it (VERIFY: one ray test and a collision read of that NIF before copying its method).

### A.3 Which buildings suit which route [INF, from what generators do badly: PROPOSAL section 3]
| Route | Building types |
|---|---|
| Generate, then clean (A.2) | mud domes and mounds, root-grown houses, hide and reed tents, rock-cut and cave mouths, ruins, wrecks, shrines, Hist-adjacent shells |
| Re-model over a generated concept (A.5) | anything organic that needs a straight door recess and frame, e.g. a clay-mound house with a plank porch |
| Hand or kit (C) | stilt houses, plank decks, Imperial-colonial masonry, Dunmer buildings, docks, walkways: straight carpentry that generators round off |

### A.4 AI-generated buildings taken into a game: what exists
I found no independent write-up of a shipped AI-generated building taken into a game with collision and an interior; vendor
posts only (Tripo's interior pages, section G, are furnishings). Tag: TRIAL; nobody has published the join.

### A.5 "Generated model as 3D concept, agent re-models cleanly over" (recommended default for organic)
Blender supports this directly [K]: show the generated mesh as a reference object (wire or 40 % transparent); build a clean low
mesh from a few primitives (cylinder, sphere, box) and extrusions with vertex/face snapping to the reference; or use a Shrinkwrap
modifier (Nearest Surface Point or Project) to pull a clean grid onto the hull, then apply. Result: manifold by construction,
correct normals, flat base, UV from the start, door recess and window shapes modelled as it is built, a separate collision proxy. The generated mesh
costs about a dollar and gives the silhouette and a reference photo for every angle; the agent supplies cleanliness. This replaces
repair of dirty topology (the step interiors.md called probably impossible) with construction (the step agents do best, D.2).
Texture then comes from shared tiles and vertex colour; the generated texture is reference only.

## B. Matching interior shells

### B.1 Make the interior from the CLEAN exterior, not from the generated hull
Derive from the clean re-model (A.5) or the cleaned hull. Methods and what goes wrong [K unless marked]:
| Method | Use | Failure |
|---|---|---|
| Solidify modifier, thickness negative, offset -1 | simple convex plans (domes, round huts) | self-intersection at concave corners and at the door/window cut; normals point to the shell, not the room |
| Displace along normals by -wall thickness (apply to a duplicate) | organic shapes | pinches where curvature is tighter than the offset; fixed by smoothing (Smooth modifier) and fewer subdivisions |
| Voxel Remesh the hull, shrink, Shrinkwrap a clean mesh onto it | irregular roots/rocks | blobby walls; resolution must be under half the wall thickness (about 10 units) |
| Re-model the shell at plan scale (Archimesh-style room) | plank and carpentry houses | none; it is construction, with exact numbers |
After the offset: flip normals to face the room; delete the outer skin; cap the base with a flat floor at z=0. **The interior is a separate model in
a separate cell (owner, measured): it is never seen with the exterior, so "matching" means correspondence, not continuity.** What players notice [INF]:
the footprint's proportion and rough size (a long hut inside a long hut), the door on the same side as the outside door, the number and side of windows,
the material and motif (reed inside a reed house, carved posts both sides), the roofline (a hipped roof outside, rafters inside), levels (a loft
inside a two-storey outside). What they do not notice: exact wall positions, metre-level size, a window's exact height. What this frees: larger inside than
outside (up to 1.3x footprint is routine, and bigger in height), multi-room layouts behind a single-door exterior, a different roof structure inside, a loft in a
low hut, corridors and alcoves the exterior could never hold; and it removes the constraint that the shell be derived by offset at all, so B.1's methods are
conveniences for a first-draft plan, and the usual route is a plan drawn from the exterior's footprint then built from the kit (C). Window panes inside: a plane
with a glow texture in a recess or wall slot, not a hole onto the void (B.6). A door opening in the interior shell is a real opening (the interior door is a
doorframe the load-door model fills, as the held KotM shells do).

### B.2 Scale
- Held pairs: interior footprint 80 to 120 % of exterior (7 pairs measured, interiors.md section 2). The forum claim that vanilla
  interiors are about 1.5x exterior is an unmeasured assertion [SNIP]. The reason for larger interiors is third-person camera and
  follower room [INF]. Use 1.0 to 1.3 x the exterior footprint, 1.0 for a hut the player squeezes into for effect, 1.3 for a trader's
  house; cut the exterior's roof overhang from the count (interior = wall-to-wall).
- Ceiling: KotM house shells are 280 to 307 high inside; Bethesda's castle wall piece is 512; agent height is 128. Use 280 minimum
  (huts), 300 to 350 typical, taller under a dome or a gable's peak [M]. Corridor/passage: Bethesda says at least two character widths
  [PAGE GDC]; our measured door frames are 155 to 190; use 128 minimum, 160 to 192 for a path the player walks daily. Slopes: 45 deg is
  walkable; GDC says 30 to 45 reads better than 60 [PAGE]; stairs at 30 to 35 deg, riser at most 32 to stay on the navmesh.

### B.3 Multi-room: partitions, lofts, stairs, posts, alcoves
Partition walls are 12 to 16-unit-thick boxes with 155 to 190 openings; lofts are floor slabs at 128 + 20 over the main floor leaving
the 128 agent height under them (so 150 clearance minimum; 200 better), reached by a stair or ladder-like ramp; stairs: see H (measured: vanilla stair collision is stepped treads in most interior pieces and a ramp in the castle and Nordic hall pieces, not uniformly a ramp);
posts and beams are visuals with
a thin box collision or none. Numbers come from the kit table in C.2 so the pieces agree.

### B.4 Checking by eye (all with tools we have)
- `look <place> in <room> overview`, `at --eye` (camera on the floor), `probe --all` (void openings listed with side and floor points),
  `playwalk --rooms` (every room look tested for the void), `section` through a stair or loft for heights (agent-view.md).
- Add by hand to the Blender bench (D.4): eye-height camera at each door and at each room's centre; a "look out of every opening" render
  with a magenta world; orthographic floor-plan and section through every door.
- Navmesh: `probe --mesh` is for places; for a new room `recast_refs` meshes the collision and the check says islands (build.py:1323).

### B.5 Collision without a MOPP, or with one
What Bethesda ships [M, ~/.argonia/nwvenv/bin/python reading NIF block types with tools/navmesh/meshes.py over 37,914 NIF paths]:
| Set (first 200 or all found) | MOPP + CompressedMesh | Convex only | Box or List | No collision |
|---|---|---|---|---|
| Whiterun interiors (200) | 151 | 6 (+6 list+convex) | 3 box | 34 |
| Nordic architecture (200) | 165 (+7 combined) | 28 | 2 list | 0 |
| Whiterun building shells (124) | 81 (+2) | 0 | 0 | 41 |
| King of the Murkmire huts and shells (9) | 9 | 0 | 0 | 0 |
- **Boxes in a bhkListShape for floors and walls:** legal Havok; PyNifly writes bhkBoxShape/bhkListShape and wraps children in
  bhkConvexTransformShape [PAGE: PyNifly wiki Collisions]; the page gives no limit on children and no performance advice. No modder source
  found on a shell made of boxes [SNIP search]. A Nexus thread says anything beyond primitives/convex needs MOPP first and one modder saw
  FPS collapse after stripping MOPP data [SNIP, forums.nexusmods.com, a mesh case]. Verdict: PARTIAL; legal, unproven for a shell; fine for a
  floor slab and straight walls (a few dozen boxes), a poor fit for a curved dome (a ring of rotated boxes is a hand decomposition, 16 to 24 pieces).
- **Convex decomposition (V-HACD, CoACD) for organic shells:** I found no Skyrim modder source using either [SNIP search]; Skyrim has
  bhkConvexVerticesShape and NifSkope can make one per shape. Convex pieces suit solid props, not a room (convex hulls cannot be hollow:
  each piece is a wall segment, a floor, a roof, never the room). So decomposition applies to a shell cut into wall slabs, not to the shell.
- **MOPP + compressed mesh:** the vanilla route. Our options: (a) PyNifly's pure-Python `compile_mopp` + `bhk_autopack.py` driving a
  nifly-based writer (niflod extended) on Linux; (b) PyNifly with a Linux libNiflyDLL.so (CMake non-MSVC branch exists, pipeline report
  line 29); (c) Blender+PyNifly on the Windows play machine (costs money). Recommended order: **boxes first for the grey-box kit (they
  are easy and the floor rule is a flat top), MOPP via (a) for the first organic hut**, both under the same TRIAL: write, place in the
  studio, walk it in the game by the owner (we do not test in game ourselves: CLAUDE.md).
- **Where the player's own walking happens:** the character controller collides with the static's collision, so the floor must be solid
  top faces at grade; walls need collision on the room side. Single-sided tris in a compressed mesh are collidable from both sides
  [K]; the agent's check is a section render with the collision drawn (D.4) and a ray test script in Blender over the proxy.

### B.6 Light and window fakes
Interior windows: a plane with an additive-glow material (vanilla "window glow" / light-shaft statics [K]) in the opening; a point light
without shadow near it; a four-shadow-caster cap [interiors.md section 1]. A sealed, windowless cell reads as a cave: the owner's call on
what looks right; the Blender probe catches voids.

### B.7 Navmesh and cell for an authored (not carried) room
- Navmesh: yes, from collision. `build.py:1323 interior_navmesh` takes `room_mesh`, else a copied source's navmesh, else `recast_refs`
  (collision of the cell's placed pieces; `ground=True` adds a plane under the lowest collision, cut away outside the walls) with
  ArgoniaNav and the world's Recast parameters; `mesh_navm` limits 32,767 triangles and 65,535 vertices a record. [M] Exterior
  heightfield side: `solid.py:1-9` says a thing blocks a column when its solid reaches the band between climb and agent height; a hut
  with a floor at grade, walls and a roof above 128 is walked into if its door is open (see C.4).
- Cell record: a no-source interior space needs a lighting row set and image space (place-studio.md:129 lists `lighting_template` for
  a space with a source; for none we would choose a template by hand, as vanilla small houses do). I did not find where our build writes the XCLL
  of a source-less space: UNVERIFIED, a small code gap to read before the first trial.
- Door pair, room marker, name: as place-rooms. Room bounds: only if a cell is large; a hut needs none (CK optimisation tutorial [SNIP]).

## C. Hand-designed snap-together kits

### C.1 What Bethesda did (GDC 2013, Burgess and Purkeypile) [PAGE: gamedeveloper.com]
Abstract units; character about 128; footprint = full bounds including walls; a 512 room tiles with a 256 hall, a 384 room does not; sub-kit
footprints multiples of each other; snap = half the footprint, as large as possible; pivots on the ground plane, centred (edge pivot only
for hinged pieces); floor thickness predetermined (stacked co-planar faces z-fight); hall kits tile on one axis, rooms on two, vertical
stacking has its own sub-kit; one door-frame size across all kits; naming = kit, sub-kit, type, inside/outside, tiling role, variant
(`Mid`, `01L01`, `1Way` to `4way`), with the lesson that over-abbreviated names kept a kit unused; glue kits (platforms, tunnels, ledges)
join kits; kit-bashing mixes kits to kill art fatigue. Scale: cave kit used 200+ times, seven sub-kits, hall sub-kit about 50 pieces; Ratway
hall sub-kit 7 pieces; seven kits built 400+ cells with two full-time kit artists. **Proving a kit:** proof stage (1 to 3 weeks; almost no
detail, no textures; proportions and naming), graybox (1 to 4 weeks; the primary sub-kit first, stress-tested by designers), build-out one
finished piece before variants. Stress tests: loop the kit back on itself; stack it vertically; build pillared rooms from hall pieces; avoid
patch-up pieces; playtest because editor-only work hides tiny holes. Project Tamriel/Beyond Skyrim kit standards: I found no published page
[SNIP, interiors.md section 1]; general references (Polycount modular wiki, Klafke, Epic talks) not fetched [K].
Measured vanilla kit sizes [M, bases.jsonl]: Whiterun interior floors 256 and 1024 square, wall 512 long x 512 high, doorway pieces
256 x 512; stairs: dungeon stair 256 wide x 803 long x 320 rise (22 deg), castle plat stairs 192 wide, 320 rise. KotM house partitions 598 x 368 x 280 to 307
(a whole room cell piece), plank walls 494 and 743 long, door frames 155 to 190.

### C.2 A small kit per culture on the game's grid (my design [INF]; every number from C.1 or the measured table)
Grid: 128-unit module (the character height; the sub-grid 64; floor thickness 16; wall thickness 16 for reed/plank walls, 32 for mud).
Pivot: ground plane, centred; pieces model from the origin outward in whole modules; vertical module 128 (storey 256 or 384).
**Kit A, Argonian reed-and-stilt carpentry (exterior AND interior, double-sided)** about 24 pieces, names in the GDC style
(`ArgStilt_Wall_Plank_1x2_01`):
- Floor/deck: Deck_1x1 (128), Deck_2x2 (256), Deck_1x2, Deck_Edge, Deck_Corner_In/Out, Deck_Hatch (trap hole), Deck_Stair_Gap (opening for stairs).
- Walls (double-sided, 16 thick, 256 high): Wall_Plank_1 (128 long), Wall_Plank_2, Wall_Plank_4; Wall_Reed_2 (reed weave); Corner_Out/In (post);
  Door_2 (155 wide recess or opening, 210 high, with lintel; an opening only on walk-through and interior walls, a recess with a door record on a house's exterior); Window_2 (shutter opening 64 x 64 at 96 high); Wall_End_Cap; Wall_Half (low wall, 96 high).
- Roof (thatch, gable and lean-to): Roof_Slope_2x2 (30 deg), Roof_Slope_2x1, Roof_Ridge_2, Roof_Hip_Corner, Roof_Gable_End (triangle fill), Eave_Trim.
- Structure: Post_Stilt_256 and Post_Stilt_384 (pivot at the top for height variants: sink verb already exists), Beam_2, Beam_4, Brace.
- Stairs and glue: Stair pieces per H.4 (flights of 128 or 256 rise), Ramp_Boardwalk_4, Ladder_Loft, Platform_Landing, Joint_Rope (cosmetic).
**Kit B, interior-only** about 14 pieces: Floor_Plank_2x2 and Floor_Mud_2x2, Wall_Interior_Plank_2 (single-sided, 12 thick), Wall_Interior_Mud_2, Partition_2 and
Partition_Door_2 (155), Alcove_Niche_1 (recessed, 64 deep), Post_Interior_256, Beam_Ceiling_4, Ceiling_Plank_2x2, Loft_Floor_2x2 (at 150 clear), Loft_Stair, Hearth_Pit
(visual; light separate), Window_Glow_1, Doorframe_Interior.
**Kit skin, one geometry for many peoples:** a piece's geometry is made once; a skin is (a) a material set (diffuse/normal per material slot), (b) a trim/ornament
band texture, (c) swapped ornament pieces (lintel, finial, door leaf) with the same pivots and bounds, (d) vertex-colour defaults. Imperial-colonial = the same Wall_2/Door_2
geometry with plaster and timber-frame skin and a tiled roof skin; Dunmer-in-the-marsh = the same with Velothi stone-and-lacquer skin and curved roof ornament. In
Skyrim terms a skin is a different NIF per culture with the same shape nodes and collision (copy the NIF, repoint the texture sets; niflod already writes texture sets), or
one NIF and per-reference alternate textures (`alt_tex` in the catalogue, place-studio.md:1341 [M]). Geometry once, skin per culture, ornament per household.

### C.3 When an enterable-exterior building is sensible
Skyrim does walk-in structures for ruins, tents and open halls; it does not for houses [interiors.md section 1, OWN]. Our own pipeline makes it feasible: the exterior navmesh
rule blocks columns only between climb and agent height (solid.py:1-9), so a hut with a grade floor and a roof above 128 is walkable if the door is a gap [INF from M].
Costs [INF/K]: no cell-bound lighting (interior needs placed lights and a lighting for the exterior cell's ambient; the sun shadows through the roof; weather precipitation
falls through unless an occlusion piece is added); no load-door door pair needed (saves one cell and a load), but every such building sits in the exterior cell's
object count and occlusion is weaker than a sealed cell. Use it for: open-sided stilt shelters, drying huts, boat houses, fish racks, shrines, ruins, a loft over a deck; keep
sealed interior cells for homes with owners and beds, where a closed door, sleeping and ownership matter. TRIAL: one open stilt hut walked in game.

### C.4 How an agent models kit pieces by hand and proves the kit
Blender: set Unit Scale so 1 BU = 1 unit (or 70 per metre: pick one), grid 128/64/32 increments, snap to Increment with absolute grid snap; vertex snap for joins; every
piece is made by script from named parameters (`make_wall(length_modules=2, height=256, thick=16, opening=None)`), then viewed in orthographic front/side/top
and perspective renders, bounding-box asserted to whole modules (script fails on a half-unit). Check by an automatic "kit linter": bounds on the grid, pivot at origin,
open edges at piece boundaries only, tris count, UV scale (cube projection at the tile size), normals out, material slots named.
Prove the kit before art, GDC style: **build three different buildings from the pieces in the place studio and look** (`place` pieces at module coordinates; `probe --all`,
`orbit`, `section`, `at --eye`, `in <room>` for the inside). Add stress cases from the talk: a loop (a square of walls joined at four corners), a stack (storey over storey),
a pillared room. Collision for flat pieces: boxes are PARTIAL (B.5): a 2x2 floor is a flat top box and a wall a thin box; or the same MOPP path as vanilla. The grey-box stage uses
flat-coloured cubes the studio already draws for missing models; the proof stage needs the studio to load a new model.
**What the studio needs** [read: place-studio.md:887, hands.py, agent-view.md "Hands"]: today `place <base>` takes a catalogued base; `move` nudges by 1, 10 or 50 units; a
"snap flush against what is beside it" exists within 24 units along the axis moved. Needed: (1) `place` accepting a model path for an uncatalogued kit piece (a
`pieces/` base list read from a kit manifest, with bounds from the NIF); (2) `place --grid 128` and `move --snap 128` (round to the module; the pieces' pivot is on the grid); (3) `kit <name>`
palette verb listing pieces with their footprints; (4) `build <recipe>` run as a loop of `place` calls for a building plan (a wall run, a corner) so an agent may say "wall from a to b" instead of 12 calls;
(5) a `snapcheck` probe: every piece's open face adjacent within 1 unit to another's or flagged. All five are small additions on existing ops (`ref.add`, `ref.move`). [INF]

## D. Agents modelling by hand with eyes: the state of the art and its limits

### D.1 Evidence
- **blender-mcp** (ahujasid): Claude drives live Blender; reviews call rooms and architectural concepts its strength; exact positioning needs correction rounds; multi-object alignment "hit
  or miss"; Claude "doesn't reason about topology" [PAGE: MindStudio review 2026-05-06, interiors.md section 4].
- **BlenderGym** (CVPR 2025, 245 start/goal scene pairs, five tasks: object placement, lighting, procedural material, blend shape, procedural geometry): even the best VLM system struggles
  with tasks easy for human Blender users; a verifier that is itself scaled with inference compute helps; a later agent (VIGA) reports gains over one-shot baselines [SNIP: arXiv 2504.01786 abstract; scores not read].
- **LL3M** (arXiv 2508.08228): a team of agents plans, retrieves, writes, debugs and refines Blender scripts from text; its author server was discontinued as the Claude 3.7 backend retired
  [SNIP: github threedle/ll3m]. Related: a planner-actor-critic framework notes syntax and logic errors in Blender scripts [SNIP: arXiv 2601.05016]; L3GO: LLM-made meshes lag diffusion text-to-3D in quality [SNIP]; 3D-GPT: limited curve
  control [SNIP]; SceneCraft: scene graph then script then VLM self-critique [SNIP]. I found no Claude-specific architecture write-up beyond the blender-mcp reviews.
- Newer room agents (2025-26) place assets rather than make shells: SceneWeaver (agent over generation tools, Blender/IsaacSim output), SceneSmith (210 prompts), INTERIORAGENT (3DV 2026), SceneFoundry, RoomPilot (text/CAD floor plan
  to a domain-specific language) [SNIP: arXiv 2509.20414, 2512.11234, 2601.05810].
### D.2 What makes them succeed and what breaks them (from the sources and our own experience in `look`)
Succeed: parametric construction with exact numbers; small verified steps; fixed named cameras; orthographic plus perspective; measurement; reference beside the result; checklists. Fail: spatial misjudgement
from one render; drift over a long session; accepting a bad render. Our place-look contract answers each already: **named subjects and `at` (fixed cameras); `section` (orthographic truth); `probe` (numbers
for truth, pictures for judgement); capture validation (a failed capture is struck, not judged); `compare` (before/after); `snapshot`/`restore`/`undo`; every call logged.** The owner's own report is that this gets much better results than the
pictures-only workflow. So the bench copies the contract and does not invent a new one.
### D.3 The model workshop: verbs it needs (same names as `look`)
Subject naming: parts by name (`roof`, `wall.N`, `door`) and a piece `at <part> --from n..nw --eye|--high|--top`; `orbit`, `section <part> --axis` (orthographic cut with a scale), `probe` (manifold, normals out, open edges, bounds on grid, tri count, UV stretch, texel density in px/m,
openings sizes, ceiling height, slope of every walkable face, step heights), `measure <a> <b>` (distance, bounds), `pick <png> <px> <py>` (what mesh/face is under a pixel, via a face-id buffer), `compare-to-reference` (reference image beside a matched-angle render), `walk` (eye-height path through doors),
`void` (every opening looked through, magenta world), `snapshot/restore/undo`. Act verbs: `extrude`, `inset`, `bevel`, `loop-cut`, `boolean-cut <box>`, `solidify`, `shrinkwrap`, `snap <vertex> <to>`, `align <loop> <axis> <value>`, `project-uv cube <m>`, `assign-material`, `paint-vertex <rule>`, `set-origin`, `export <glb|nif>`; each verb is a small script run in `blender -b`
and answers with before/after numbers, as `move`/`sink` answer today.
### D.4 Rendering without a GPU [K, TRIAL for times]
Workbench engine renders on CPU and needs no GPU; it gives flat/studio shading, wireframe overlay, matcap, cavity, and an id-like object colour mode: suitable for shape judging (a 1920x1440 frame in seconds on 4 cores is my expectation, TRIAL).
Eevee Next needs OpenGL 4.3 and software GL (Mesa llvmpipe) is possible but slow (TRIAL); Cycles CPU is minutes a frame, only for a hero check. The cheaper, proven loop: **export GLB and view it in our own studio's headless
Chromium scene** (software GL, "seconds a view on a warm daemon", agent-view.md "Not guaranteed"), which gives the same view verbs, id buffers, capture validation, the NIF-faithful materials and the real place beside it. Plan: Workbench
for the modelling loop (orthographic sheets, X-ray collision, stretch checker), the studio for in-context judgement. The id buffer gives `pick` in both.
### D.5 Where it goes wrong, specifically
Counting loops and openings; mirror errors (left/right); a render hiding a hole (single-sided face, camera from outside); proportional drift when one dimension is edited and not the dependents (fixed by parametric script with all numbers in one dict, rerun end to end);
accepting a "looks fine" capture (answer: the failed-capture banner and `subject_seen` numbers already in `look`); long-session drift (answer: each stage ends with a snapshot and a probe table, and a fresh context reads the table, not the history).

## E. Hand-dressing a new shell
Our place agents already place and judge clutter by hand. A new empty shell adds only: (1) lights, at most four shadow casters, extras non-shadow [interiors.md]; (2) a lighting template and image space from the cell record (see B.7 gap); (3) furniture markers and beds: beds, benches, hammocks come from vanilla donor NIFs with
their furniture markers (template swap, PROPOSAL section 4), placed so the marker's approach point is on the room's navmesh; (4) idle and patrol markers are placed from vanilla markers; (5) containers owned by household (place-stock); (6) room bounds only if large. Probes already exist for floating, buried and door-ground faults. Variety across a province: several shells per culture (4 to 6 organic shells and a kit with 3 or 4 plan templates), each in 2 to 3 layouts, dressed by household from place-people and place-stock, with ornament skin per household; the 18-of-41 repetition problem disappears when each household gets its own plan and clutter.

## F. The ambitious staged plan
| Stage | What is proved | What it needs built | Gain |
|---|---|---|---|
| 0 (days) | the join: a one-box hut visible and walkable | read `build.py` for a source-less space's lighting; studio loads a NIF by path; niflod writes BSXFlags + box rigid body (or PyNifly MOPP via compile_mopp); Blender installed on the build VM; Workbench bench with `at`/`section`/`probe` | one test cube cell the owner can walk |
| 1 | one organic generated hut with a matching shell, hand-dressed | one Hunyuan multi-view generation (about $0.50 to $2.70 with retries) of a root-grown house; re-model over (A.5); shell by offset (B.1); cube-projected tiling materials; vertex colour; MOPP collision (TRIAL 1); a LOD model via `lodmodels.py`; door pair via place-rooms with a source-less space | the first Root-Folk root-grown house; reusable recipe; one new shell |
| 2 | one carpentry kit grey-boxed (Kit A, 24 pieces), three buildings assembled in the studio | studio verbs C.4 (1 to 5); kit linter; three plan recipes; the same pieces as interior (double-sided) | the stilt house the Argonians lack; 3 plans times skins |
| 3 | culture skins and shell variety | skin manifests (Imperial-colonial, Dunmer); alternates on 2 to 3 households; open-sided enterable buildings trial | variety across the province |
| 4 | at scale | agent-by-agent per place, as place-drafter owns a place | remaining places |
**What the province gains** [M, world.sqlite]: 258 places, 144 of them with buildings. Households: Root-Folk 22, Sedge-Wardens 13, Shadowfen Border 7, 43 in all. Interior cells held by the rank-1 source places per culture: Root-Folk 3 (19 places), Sedge-Wardens 3 (6), Hutan-Tzel 0 (4), Agaceph 0 (4), Naka-Desh 0 (5), Three Waters 3 (6), Mine-Burners 4 (7), against 100 or more for Clay-Mound (12 places, 109), Blackrose (10, 105) and Lilmoth (16, 102). The Root-Folk's 19 places have no root-grown house; interiors.md names 21 held shells for all Argonian places and the repeated cell is 18 of 41 rooms. 126 places draw on vanilla-built sources and 154 on King of the Murkmire. (`source_place.buildings` is a reference count, not a house count, and is not used.)
**Honest obstacles:** collision authoring (TRIAL 1); studio loading new models (small); LOD (derived models already automated; kit pieces under 512 units get none, as lod.md says); door pairing (records); texel density (solved by tiling, A.2); **KotM**: its page says add-ons should not use AI and our record says the owner's permission, held since 24 September, covers our use (PROPOSAL section 9); the exposure is new generated buildings standing beside its huts, so Stage 1 uses generation for a concept only (A.5, re-modelled by hand) and the first placement is in a Root-Folk place that has no KotM huts; a decision for the owner if he wants generated hulls shipped as geometry.
**Well evidenced:** sections B.5 table, C.1, B.2 measured numbers, the compiler fact, the interior-navmesh route, the province counts. **Inference:** the double-sided kit, skins, enterable buildings, Workbench times, offset methods, V-HACD uselessness for rooms. **Only trials settle:** (1) the game walks on our collision (box-list and MOPP both); (2) a hand-made shell's source-less cell lights; (3) Hunyuan multi-view quality on a building and Part Splitter on it; (4) the Workbench/studio per-view times; (5) the agent's loop count per hut (the cost); (6) KotM's reading of "no AI" for concept use; (7) an open-sided building's weather and lighting.

## G. Tripo's interior-design guides, and scene set-up tools

### G.1 What the Tripo pages say (snippets only; tripo3d.ai returns 403 to automated fetches and I did not try to get round that)
[SNIP, via search results of 2026-11-24, English and other-language versions, vendor marketing]:
- The guide "AI 3D Models for Interior Design: Generate, Stage, and Visualize Any Room" lays out generate, preview, stage, export, refine in render tools; it positions Tripo for furniture, decor and object assets and says AI models complement, not replace, professional modelling.
  Export GLB, OBJ or FBX into Blender, SketchUp or Unreal; inputs are text, photos, sketches and product images. **This corrects interiors.md section 3: the guide exists; it is a furnishing-and-prop path, and the staging is done in another tool.**
- The "custom furniture libraries" and "automate room layout planning" pages say generated furniture must be scaled to real-world dimensions in the target room planner's own measure tools after import ("AI models may not always export at precise real-world dimensions");
  recommend GLB for web planners; claim the layout algorithm avoids overlaps and respects walking clearances (no independent evidence; the "200 billion parameter" figure is asserted); credit tiers: free 300 a month, professional 3,000 with commercial licence (to check against current pricing).
- The "3D inside house" guide says the room shell is made by tracing a floor plan and extruding walls to height in a separate modelling programme: a manual route, as ours. A use-case page speaks of turning plans, sketches and ideas into 3D layouts without detail. I could not confirm that Tripo Studio has a shell or wall-extraction feature.
- Not Tripo: a Hugging Face project InteriorGen3D reconstructs one room from one photo with furniture as objects [SNIP; not assessed].
Consequence for us: furnishing generation (bowls, mats, hammocks, stools) is Tripo's strength and already in PROPOSAL; the shell, scale, placement and staging are ours to do, and the place studio is the staging tool.

### G.2 Scene set-up tools an agent could drive
| Tool | What it does | Cost / licence | Headless Linux | Helps us? |
|---|---|---|---|---|
| Blender (bpy), Archimesh (bundled) | rooms, doors, windows from parameters | GPL, free [SNIP: Blender manual] | yes (`blender -b`) | Yes: the bench itself; Archimesh a starting script source |
| Archipack | walls, doors, windows, slabs, stairs, roofs, fences, trusses; free tier plus paid; Python | free + paid [SNIP: OSArch wiki]; licence of paid not found | Blender add-on, so yes | Maybe: stairs and roofs parametric; our own scripts are small and exact, so low priority |
| Building Tools (ranjian0), HomeBuilder | floor plan, walls, openings, stairs add-ons | open source (GPL) [K, not fetched] | add-on | Optional |
| Buildify (Pavel Oliva) | geometry-nodes building generator from modular parts, free [SNIP] | free | Blender 3.2+ nodes | A reference for kit assembly by nodes; not Skyrim-sized |
| PBG 2, BRiCKiTECT and similar | paid geometry-nodes building generators | paid; PBG2 cannot make curved walls and was broken on Blender 5.2.0 [SNIP] | with Blender | No: Western masonry |
| Sverchok | node-based parametric geometry | GPL [K] | add-on | Not needed: scripts do the same |
| Bonsai/BlenderBIM + IfcOpenShell | IFC walls, doors, windows, stairs; `ifcopenshell.api` runs standalone and in Blender; MCP wrappers exist [SNIP] | LGPL/GPL, free | yes | Interesting for exact walls with openings, but heavy; our kit scripts achieve the same |
| FloorplanToBlender3d | floor-plan image to Blender mesh [K, not found in my search] | open source | yes | Only if we draw floor plans; skip |
| blender-mcp | Claude drives live Blender; port 9876 [SNIP] | MIT [K] | needs a running Blender (headless with a display-less runner is TRIAL) | Yes if we want live interaction; our scripted verbs give more control |
| Tripo Studio / Meshy / Sloyd | object generation; Sloyd parametric low-poly buildings, API access unverified [SNIP] | credits / unknown | web | Sloyd worth one look for its low-poly parametric buildings |
| Holodeck, LayoutGPT, SceneWeaver, SceneSmith, INTERIORAGENT, RoomPlanner, RoomPilot | LLM layout planners that output placements (asset, position, rotation) | research code, licences mixed [SNIP] | Python | As a method: their placement-JSON could feed `place`; our place agents already do this by eye and are better placed because they see the real navmesh |
| Unreal/Unity MCP builders | scene building by tool calls (a Unity temple in 1,344 calls) | vendor [SNIP] | no | Method reference only |
| Our place studio (`tools/places`) | places pieces, writes records, probes, sections, walks, commits drafts | ours | yes | THE assembly and dressing tool; needs the five additions in C.4 |
| Creation Kit | the Skyrim editor; GUI only; only for the Papyrus compiler and FaceGen under decision 0018 | free with the game | no | No for assembly |
| Reference rigs for image-to-3D | fixed camera, turntable, orthographic sheets | an ordinary Blender script, or Hunyuan 8-view conventions | yes | Yes: a script renders a standard 8-view sheet from any clean model so each generation gets the same references |
| Asset-browser libraries | Blender's asset library for a furniture/kit palette | built in | yes | Yes for kit pieces once they exist (a catalogue of marked assets) |

### G.3 The smallest set, and what is worth paying for or enabling
1. **Blender headless on the build VM** (free): the bench. Needed for every stage.
2. **Our place studio with five additions** (C.4): assembly, dressing, proof. Our own code; no cost.
3. **A scripted "kit linter" and "building probe"** (our code): the checks of D.3.
4. **blender-mcp as an optional enable** (free): worth enabling only for exploratory sessions on the play machine or a desktop; the batch workflow uses scripts.
5. **Hunyuan multi-view on fal** (about $0.5 to $2.70 per hut with retries): worth paying for as the concept source (A.5); no extra account.
Not worth paying for now: Archipack paid, PBG2, Sloyd (until its API is verified), Tripo's own scene features (none found). Reference rig, asset library, and a floor-plan sketch tool are ordinary scripts.


## H. Stairs and levels

### H.1 How vanilla and held mods do interior stairs (measured: bounds from `bases.jsonl`, collision read with `tools/navmesh` over the game's NIFs)
Method: for each piece the bounds give width, run and rise; collision triangles give tread count (distinct upward-facing levels) and whether a
slope (normal z 0.5 to 0.99) is present. "Tread levels" counts triangle centroids, so a ramp reads as many 2-unit levels.
| Piece (family) | Width x run x rise | Collision [M] | Reads as |
|---|---|---|---|
| WRDunIntStairsDown01 (Whiterun dungeon interior) | 256 x 803 x 320 | 22 tread levels, 14.5 rise each; 4 ramp tris | stepped treads, 22 deg, floor-to-floor 320 |
| WRIntFloorDirtStrStairsDown01 (Whiterun interior) | 587 x 255 x 257 | 5 levels (18 rise), ramp tris at 36 deg | short steep flight, 257 |
| WHIntStairs01 (Windhelm interior) | 244 x 875 x 378 | 16 levels, 24 rise, no ramp | stepped treads, 23 deg |
| WHIntWoodStairs01 (Windhelm wood) | 255 x 349 x 258 | 17 levels (18), some ramp at 37 deg | stepped, 36 deg, 258 |
| WHIntCastleHallStair01 | 270 x 905 x 621 | 1,164 tris, ramp 28 deg | grand stair, ramp-like, 621 |
| RifRmSmSecondFloorStair01 (Riften small room) | 242 x 82 x 264 | 13 levels (20), ramp tris at 31 deg | narrow steep loft stair, slope by bounds 47 deg, 264 |
| RifRmSmBaseFloorStairs01 / BaseCeilingStairs01 | 256 x 256 x 130 / 138 | 9 levels (16) / ramp 64 tris | the floor piece and ceiling piece around a stair to the basement |
| FarmIntLHLoft01 (farmhouse loft with stair) | 657 x 768 x 353 | 9 levels, ramp tris 48 deg | loft piece with built-in stair |
| SLGCStaSpiral01 / BulwarkIntSpiralStair (Solitude) | 614 x 1026 x 361 | 19 levels (18), ramp 43 deg | spiral, 361 |
| WHIntWoodLadder01 | 82 x 287 x 325 | 15 levels (20), ramp 48 deg | a "ladder": a steep stair-collision shape you walk up, not a climb animation [INF: no ladder animation exists in Skyrim] |
| NorCatHallBg1wayRamp256Ice (Nordic hall ramp) | 717 x 1024 x 876 | ramp 22 deg, 431 tris | ramp piece, 256 grid |
| NorTmpExtPlatStairCap, ImpExtIceStairs01 | 332 x 758 x 513; 255 x 598 x 366 | stepped + ramp (39 deg; 12.5 deg) | dungeon stairs |
Verdicts: the "usual Bethesda practice" of a smooth ramp over the visible steps is PARTIAL: 6 of the 13 above use tread collision with no
ramp (Whiterun, Windhelm, Riften base), 4 mix, 3 are ramps. All sampled stair pieces carry only collision layer 1 (static); I did not see a
stair-helper layer on any. Rise per step is 14.5 to 24 everywhere (never above 24), which is inside the navmesh's 32 climb. Floor-to-floor heights
implied: 257, 258, 264 (two 128 modules plus 0 to 8), 320, 361, 378. So 256 is the standard small-house storey and 320 to 380 the large one.
**KotM and the Dunmer mods reuse the vanilla pieces:** KotM `MudHutStairs01` and `MurkmirePlatformStairs02` have bounds 242 x 82 x 264, identical to the Riften
loft stair; so do `SOMRStonehouseIntStairs`, `SOMRShipIntStairs` (Solstheim/Dunmer). KotM also has `MudHutStairs02` (629 x 272 x 251), `MudHutStairs03`
and `MurkmirePlatformStairs01` (172 x 153 x 156), cypress stockade stairs (251 x 242 x 242; 91 x 274 x 198) and the Ayleid halls (`AYLDIntSmHallStairComplex` 1281 x
1054 x 771). Cipactli: 4 stair pieces (dock 181 x 290 x 261; temple 706 x 1096 x 415). Baan Malur's Velothi/Dagon Fel kits: `VLTINTTunStairs` 256 x 100 x 302,
`VLTINTTunStairsSmall` 128 x 100 x 238, `SOMRTownhouseINTStairsBricks03b` 263 x 266 x 493, `VLTINTSmCornerCurveRamp` 752 x 752 x 374. Those mod meshes are not
resolved by `meshes.Resolver` on this machine (not found by path), so their collision is not read: bounds only.
**Counts held** (catalogue STAT rows whose model or edid says stair/steps/ladder/ramp/spiral/loft; interior = path or edid says interior): Skyrim 470 other
+ 68 interior; Journey to Baan Malur 103 + 63; King of the Murkmire 57 + 32; BM&V 36 + 4; Cipactli 4 + 0; Wyrmstooth 22 + 5; Project AHO 19 + 0; Nyhus 12 + 5;
Solstheim Dunmer 3 + 3; Xanmeer 1 + 3; CC Ayleid 0 + 5. The count is rows, not placed instances, and includes exterior stairs, ramps and dungeon pieces. The Argonian
house stair stock is therefore the Riften loft stair (and its KotM copies) plus MudHutStairs02; there is no wide straight, half-turn, quarter-turn or plank-ramp
stair in an Argonian dress.

### H.2 Rules an agent needs to place a flight reliably
Numbers: [M] unless tagged.
1. **Floor-to-floor is a whole number of flights and of risers.** Use 256 (small house, matches the Riften/Whiterun/Rift stair rises 257 to 264) or 384 (hall); a flight
   of rise R has n = R / rise risers with rise 16 to 20 (vanilla 14.5 to 24; never over 24), so 256 = 16 risers of 16, or 13 of 19.7; a half-flight is half the rise with a landing.
2. **Slope.** Navmesh walkable angle 45 deg (`params.MAX_SLOPE_DEG`); stairs for NPCs at 30 to 35 deg (vanilla stepped pieces are 22 to 37 deg); a steep loft stair up to
   47 deg exists in vanilla (Riften, 82 wide) but sits at or over the navmesh cut, so NPCs should not be asked to use it [INF]. Step height for NPC pathfinding: 32 climb; rise per step 24 max.
   The player's step height in the character controller is not documented in anything I read [UNVERIFIED]; stay at or under vanilla's 24.
3. **Headroom.** Agent height 128. Vanilla gives the head of a flight an opening in the upper floor; the dungeon stair above is the next storey's ceiling or open. Rule: clear
   height over every tread nosing at least 192 for the player in third person, 256 preferred (the camera sits behind and above the head: [INF], measure by trial); the stairwell opening
   at least run + 128 long and 128 to 192 wide (Whiterun's 256 x 256 floor and ceiling pieces around a stair are the vanilla numbers: RifRmSmBaseFloorStairs01 is a floor piece with a
   hole for the stair, RifRmSmBaseCeilingStairs01 is its ceiling counterpart).
4. **Landings.** Clear 128 x 128 at the foot (the agent diameter is 64; the door swing and a person need 128) and at the head (at least 128 deep past the last riser); a quarter-turn landing is
   a 128 to 192 square; no door arc or furniture within 96 of either end.
5. **Opening and railing.** Cut the upper floor: omit floor pieces over the stairwell (kit rule), or use a floor piece with the hole (vanilla pattern); railing along the open edges is a 96 to 112 high
   visual with a thin box collision; bare edges are a gap the probe flags.
6. **Doors and furniture stay off the flight** and off the foot and head landings.
7. **No climbable ladders.** Skyrim has no ladder climb animation [K]; a ladder is a load door (a trapdoor or a hatch with a visual ladder) or decoration; the Windhelm "ladder" is a steep stair shape [M]. A loft is reached by (a) a steep stair (the Riften piece), (b) a short ramp, or (c) a loft as its own cell behind a hatch door.
8. **Spiral and curved:** the Solitude spiral (614 x 1026 x 361) shows spiral collision as stepped treads with a few ramp tris; use a held spiral rather than model one.

### H.3 Navmesh over stairs
- Our generator: `tools/navmesh/params.py:7-10` climb 32, slope 45, radius 32 (object cells 16); `solid.py` blocks a column when solid reaches above the climb and below the agent height, so a tread
  of rise 24 or less is walkable and a flight forms a connected mesh over its treads; a ramp slab under 45 deg is walkable as a slope [INF from the rules; TRIAL on one stair].
  For an interior, `recast_refs` (build.py:1363) meshes the placed collision with those parameters; a stair in the shell is therefore included if its collision is a solid layer (layers 1, 2, 4... SOLID_LAYERS, nif.py:25).
- Carried rooms keep the source's navmesh when it is one island (place-rooms; build.py:1323); stairs in a carried cell are the source's own.
- Where a ramp piece is steeper than 45 deg (Windhelm ladder 48 deg, farm loft 48 deg) Recast would leave a hole; the check says islands.

### H.4 What the place studio needs (read: `tools/places/look/hands.py:158-230` `steps_bases`, `lay_steps`; `tools/places/units.py:1362-1400` `joint_rows`)
- Exists: `steps <from deck, structure or door> <to point or thing>`: lays one flight from a deck edge DOWN to the ground using the place's own steps pieces, picks the piece whose foot
  meets the ground, hangs it square to the edge. `probe --mesh <a> <b>` says whether a walk joins two things on the built mesh and where it breaks. `units --joints` lists every steps/span/bridge/dock end
  with the gap along and in height to what it meets, using the ground as the lower deck.
- Missing for interiors: (1) `stairs <room> <from z> <to z> <start x,y> <direction> --family <kit> [--shape straight|half|quarter|loft]` that chooses the flights of a family to make the rise (H.2 rule 1), lays
  landings, snaps the start to the 128 grid and the foot to the floor, and cuts or reports the stairwell; the exterior `steps` verb goes DOWN from a deck, the interior verb must go UP from a floor to a named upper floor, so
  `lay_steps` needs an "up" mode, a floor-to-floor argument and landing pieces; (2) a flight probe: foot and head within 4 units of their floors (the `joints` gap), clear height along the flight line (a section along it measuring every piece above the nosing line), walk-test foot to head on the room's mesh (`probe --mesh`), and the stairwell opening length; (3) fixed views: `at <flight> --from foot|head|side` (eye at the foot looking up, eye at the head looking down, orthographic side section along the run).
- Does `units --joints` extend to interiors? Its inputs are `pl.sc.pieces` and `pl.sc.ground`; agent-view.md says a room draws its pieces and its floor "stands in for the ground" in `in <room>` verbs, so
  `in <room> units --joints` is plausible but I did not find it documented or tested [INF]; the classifier (`classify.kind_of` "steps") must recognise interior stair edids (stair/steps/ladder/ramp), which
  my catalogue pattern did in 928 rows, so it probably does.

### H.5 A stair set of our own, per culture (hand-modelled on the 128 grid, shared materials, tread collision as vanilla does)
| Piece | Size (w x run x rise) | Where | Notes |
|---|---|---|---|
| Straight flight 128 | 128 x 192 x 128 | all | 8 risers of 16; slope 34 deg; combine two for 256 |
| Straight flight 256 | 128 x 384 x 256 | all | 16 risers of 16; the standard storey |
| Half-flight + landing | 128 x 192 x 128 twice + 128 x 128 landing | small houses, stilt houses | turns 180 deg in a 128 x 512 footprint |
| Quarter-turn | two flights at 90 deg + 128 square landing | Imperial and Dunmer houses | the landing is the pivot, on the grid |
| Steep loft stair | 64 to 82 x 128 to 192 x 128 to 256 | huts, lofts | rise 24; up to 45 deg (vanilla Riften piece is 242 x 82 x 264; reuse it) |
| Notched-log / plank ramp | 96 x 384 x 192 | Argonian stilt houses, boardwalks | single ramp slab (box collision rotated, PARTIAL: boxes are unproven for architecture, B.5) or cleats as tread collision; 26 deg |
| Stone flight | 128 to 192 x 384 x 256 | Imperial, Dunmer | stepped tread collision as Whiterun/Windhelm pieces |
| Stairwell floor piece | 128 x 256 with a hole | all | the vanilla pattern; plus railing set |
Collision: real tread boxes (each tread a box in a bhkListShape) or MOPP over the visible stair mesh (the vanilla route, B.5). Avoiding boxes-only guesses, the flight collision should
follow the treads, because that is what 6 of 13 sampled vanilla pieces do [M]. **Which held pieces make our own unnecessary:** the Riften/KotM 242 x 82 x 264 steep stair (loft), `MudHutStairs02` (629 x 272 x 251, a wide
hut stair), Whiterun/Windhelm stair pieces for a stone flight (but they are Nordic-dressed; retexture under the same shape is the cheap skin, C.2), `VLTINT*Stairs` for Dunmer. We would
model only: the half-flight, the quarter-turn landing, the plank ramp and the Argonian-dress straight flight. Stage 2's kit includes those four; Stage 1's hut uses a steep loft stair from the held stock, so the first trial needs no new stair.

## Recommendations (each with its evidence)
1. Rewrite PROPOSAL section 6 whole around stages 0 to 3 (F); drop "route 5 no" and "new interiors out of scope" (interiors.md:218).
2. Run the Stage 0 cube first: it settles collision, studio loading and the source-less cell in one day and costs nothing (findings 2 to 4).
3. Read where the build writes a source-less interior's XCLL (B.7 gap) before the trial; one grep and a short read in `tools/places/build.py` and the plugin writer.
4. Add the sentence "boxes are the unproven way; MOPP+compressed is the vanilla way" to the asset-pipeline report so nobody assumes boxes work (B.5 table).
5. Measure vanilla door-in-wall proportions on a small house (the 1.5x door claim is a forum assertion) with one catalogue query before fixing the kit's Door_2 (B.2).
6. Add the interior `stairs` verb and flight probe (H.4) to the studio before Stage 2; read once whether `in <room> units --joints` runs (H.4).
7. Install Blender and time Workbench against the studio's headless view on one hut (D.4).

Covered: docs/research/new-art (PROPOSAL 94-300, interiors.md whole, asset-pipeline findings and texel), docs/design/agent-view.md whole, place-look skill (via agent-view), place-rooms skill, tools/navmesh (params, solid, placed docstrings), tools/places/build.py (interior_navmesh, recast_refs, space rows), place-studio.md (snaps, lighting lines), docs/design/lod.md head, bases.jsonl measurements, NIF block scan of 37,914 paths, newworld/out/world.sqlite; web: GDC article, PyNifly mopp_compiler.py and Collisions wiki, Hunyuan/Tripo fal pages, BlenderGym, LL3M, Tripo interior pages (snippets), Archipack/Buildify/Bonsai search · Skipped: tools/places/hands.py in full (read only its header; the verbs are taken from agent-view.md), Blender manual pages (not fetched, tagged K), Polycount/Klafke/Epic kit talks (not fetched), Sverchok/FloorplanToBlender3d/Building Tools (search found nothing, tagged K), tripo3d.ai pages (403, snippets only), the CK wiki (403 earlier).
