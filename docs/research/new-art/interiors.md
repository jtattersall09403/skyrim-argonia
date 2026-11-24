# Interiors and new buildings: what is possible, what we hold, what it would take

Written 2026-11-24 for owner calls #93/#94 (the owner's interiors question). Research only; nothing generated,
bought or downloaded. Web claims carry a tag: [PAGE] I fetched and read it; [SNIPPET] only a search-result summary
(page not opened, or opening returned 403); [OWN] my inference. Local measurements are `file:line` or a command's output.

## 0. Live docs, and the one to edit

- Cover the topic already: `.claude/skills/place-rooms/SKILL.md` (rooms carried with their door pairs; a building's
  rooms from one other source via `room.copy_of`), `place-adapt/SKILL.md:48-50`, decision 0041,
  `docs/research/world/c-interiors-and-places.md` (2026-11-06 census: 71 interior cells in BM&V, option C4 "re-use
  vanilla interiors re-dressed"), owner-rulings.md:175 ("interiors may look Nordic where a borrowed interior is all
  there is", 2026-10-30), `docs/research/new-art/skyrim-asset-pipeline.md` section on architecture/huts (walkable MOPP
  collision, navmesh, LOD) and "doors ... interiors reuse existing cell doors" (line 132).
- Confirmed: the carried-room recipe works and is cheap; the old census (53 BM&V load doors reach 26 interiors) stands.
- Not covered anywhere: how Argonian huts are actually built inside (shell vs kit), the exterior/interior size
  relation in the held mods, and what a new building would take. This report is the first measurement.
- The one doc to edit: `docs/research/new-art/PROPOSAL.md`, section 6 "What I would not do at any level" (houses and hut
  kits, root-grown house) and section 10, using section 5 below. No new file.

## 1. How Skyrim interiors work (human guides)

Findings, each with its source:

1. **Interiors are separate cells reached through load doors.** Every exterior building is a static shell with a
   door that teleports (XTEL) into an interior cell; the two share no geometry. Our census: 575 whole-building shells in
   the three Black Marsh worlds, 26 of them with a load door (`c-interiors-and-places.md`, "Shells"). Enterable-exterior
   (walk-in, no load) is the Fallout/Oblivion-ruin exception and Skyrim does it only for ruins and tents, [OWN] because
   cell streaming and lighting are per cell.
2. **Skyrim's interiors are built from kits on a grid.** Bethesda's Nordic Ruin kit works on a **128-unit grid
   (about 2 m), snap angle 45 degrees** [SNIPPET: CK wiki "Bethesda Tutorial Layout Part 1", ck.uesp.net/wiki/Bethesda_Tutorial_Layout_Part_1,
   403 on fetch]. The 2013 GDC talk on Skyrim kits [PAGE: gamedeveloper.com/design/skyrim-s-modular-approach-to-level-design]: a character
   is about 128 units; a 512 room tiles with a 256 hall but a 384 room leaves gaps; the default snap is half the
   footprint; minimum corridor width two character widths; slopes 30-45 degrees read better than 60; pivots on the
   ground plane, centred; floors of a fixed predetermined thickness to avoid z-fighting; hallway kits tile on one axis,
   rooms on two; vertical tiling needs its own sub-kit; piece names carry kind plus variant (`...Mid..01L01`, `1Way`
   to `4way`). **Size of a kit: Cave kit used over 200 times with seven sub-kits, its small hallway sub-kit about 50 pieces;
   Ratway hall sub-kit 7 pieces; seven kits built well over 400 dungeon cells.** Two full-time kit artists served eight
   level designers; a kit took 1-3 weeks to prove, 1-4 weeks to graybox, then months to build out. Good lighting and
   ambient occlusion were the stated fix for ugly kit joins.
3. **Not every kit is tight.** A Nexus thread notes Skyrim's kits are "not as modular as Oblivion's" so snap values must
   be found per kit [SNIPPET: forums.nexusmods.com/topic/1081476]. Beyond Skyrim: Bruma's house tileset is only 2 pieces
   [SNIPPET: Nexus page search summary]; I found no published Beyond Skyrim or Project Tamriel interior guideline page
   (the search returned none), and no Darkfox127 kit tutorial. Tamriel Rebuilt has Morrowind interior style guides
   (tamriel-rebuilt.org/node/6845, node/6455) [SNIPPET, Morrowind not Skyrim] and an "int dev cheatsheet".
4. **Room bounds and portals** (optimisation): room markers are boxes that group objects for culling; portals sit at
   doors or openings and must connect two bounds; bounds must cover the whole visible area and extend below the floor;
   a stale bound copied from a vanilla cell makes objects pop in and out; console `MBC` toggles the system
   [SNIPPET: ck.uesp.net/wiki/Room_Bounds_and_Portal_Basics, Bethesda_Tutorial_Optimization; 403 on fetch]. The CK
   optimisation tutorial itself says manual optimisation is often unnecessary for small simple spaces. [OWN] A one-room hut
   needs none; our rooms copy the source's.
5. **Lighting**: four shadow-casting lights visible at once is the hard engine cap; extras flicker or switch off; keep
   non-shadow lights to about two on any mesh [SNIPPET: Nexus article 3552 and forum threads 6352511, 1015400]. Interior
   look also comes from a lighting template and image space (ours: `space.json` `lighting_template`; place-studio.md:129).
6. **Navmesh in interiors**: one navmesh per cell (or per room); unreliable to generate under Proton in our setup
   (skyrim-asset-pipeline.md:185). We carry the source's navmesh when it is one island, else the build meshes again
   (`place-rooms/SKILL.md:12-14`).
7. **Collision**: architecture needs walkable MOPP (bhkMoppBvTreeShape) collision; a mesh with a collision node can still
   drop the player through the floor [SNIPPET: Nexus thread 1036900]. NifSkope 2.0 Dev 7 cannot draw SE collision (same
   source). Our writer `niflod` writes no collision (pipeline report line 20); PyNifly can (lines 32-36).
8. **Interior bigger than exterior is the norm, and tolerated.** A modder reports vanilla interiors are scaled about 1.5x
   (so followers fit) and exterior models of vanilla houses are "about 50% smaller" than their cells; another found
   matching them harder than rebuilding the world; practical tips were build the interior first, then rescale the
   exterior and the door [SNIPPET: Nexus forum 6808362, 8651753; 403 on 8651753]. Both claims are forum assertions.
   **Measured in our own held Argonian mods (section 2) the interior shell is 80 to 120 percent of the exterior footprint,**
   so the Argonian modders matched far closer than Bethesda did.
9. **Shell vs kit.** Shell: one hand-modelled interior mesh per house, dressed with furniture. Kit: snapping wall/floor
   pieces. The huts we hold are all shells (section 2). Skyrim's own small houses are shells too (Whiterun `wrinteriors`,
   Solitude `interiors`: 357 pieces, Skyrim.esm catalogue), kits being for dungeons, halls and towers.
   [OWN, from the catalogue paths and the GDC talk saying kits were "primarily dungeon interiors"].

## 2. What we hold and do (measured)

**Interior pieces by mod** (`out/places/catalogue/bases.jsonl`, 40,968 bases; paths containing "interior"): KotM 388
(226 of them the Ayleid-ruin interior kit; `argonia/xanmeer/interior` 43, `architecture/xanmeer/interior` 40),
XanmeerResources 27, BM&V Black Marsh.esm 18, Valenwood 71, Baan Malur 564, Skyrim.esm 1,339. Cipactli: none under that name.

**Argonian hut interiors are one-piece shells paired to an exterior shell.** From the catalogue's model names and bounds:

| Pair (exterior / interior) | Exterior footprint (units, x y z) | Interior footprint | Mod |
|---|---|---|---|
| mudhut01 / mudhutint01 | 708 x 932 x 633 | 974 x 698 x 700 | KotM |
| smpodext01 / smpodint01 | 710 x 672 x 949 | 837 x 810 x 830 | KotM |
| roundhut01 / roundhut01int | 948 x 948 x 927 | 806 x 852 x 823 | KotM |
| house1 / house1in; house3 / house3in | 654 x 478 x 750; 684 x 729 x 752 | 598 x 368 x 280; 613 x 496 x 282 | KotM |
| hausneu01 / hausneu01innen | 1515 x 1148 x 1174 | 1100 x 963 x 806 | KotM |
| shiveringhouse_02 / _inside | 1379 x 823 x 1336 | 1115 x 617 x 985 | KotM |
| bamboohut01 / bamboohut01_int | 574 x 577 x 410 | 574 x 698 x 410 | Cipactli |

Counts of paired shells: about 21 interior shells (KotM mudhutint 1-3, smpodint 1-2, manorint, house1in..house4in
plus 2inb, hausneu01/02 innen, roundhut01int/varint/02int, shiveringhouse 01/02 inside; Cipactli bamboohut01/02_int;
ArgonianLakeHouse mudhut01intnew). Walls/partitions to subdivide: KotM `housepartion01-05` (+ wall, wide, window variants,
9 pieces), `plankwall01a..03a` (5), doorframes, `mudhutintfloor01`, `mudhutintstairs`. Xanmeer interior kit
(43 + 40 + 27, overlapping) is a ruin kit, not a house kit. BM&V has the `01ArgonianHouseinside` cell (1,557 refs,
973 statics; shell is Phitt stronghold plus BYOH pieces) and `HouseInt` (shell `architecture/small house/smallhouseint.nif`,
436 x 645 x 552); I did not open their meshes, so their look is unjudged.

**How rooms are carried today** (`place-rooms/SKILL.md:9-14`): `draft wholesale --rooms` copies each laid source door's
cell, pairs the doors, sets the arrival. Of our four drafted places there are **41 carried rooms from 24 distinct source cells:
22 BM&V, 15 KotM, 2 Baan Malur, 2 Skyrim** (measured from `newworld/places/*/spaces/*/space.json`, `copy_of`, clones `@` excluded).
**18 of the 41 are one cell** (Helstrom's `01ArgonianHouseinside`, copied 17 times, plus Ruusa-Wan's house), so the repeated
interior, not the kit, is the visible mismatch in Helstrom. Non-Argonian kits: the Council Strongroom (Baan Malur wine cellar,
Dunmer Dagon Fel kit), Gang-Master's Hut (Baan Malur hut), the Orc longhouse and cellar (Skyrim), four KotM Lilmoth rooms that
mix `argonia` pieces with Whiterun clutter (Merchant Manor: 53 Argonian pieces, 9 Whiterun). KotM's Seekhat huts mix their own shell
with vanilla `farmhouse` clutter (4-7 pieces each; srccells). So roughly 4 of 41 rooms are a foreign kit and about 8
carry vanilla farmhouse clutter; the dominant mismatch is sameness. The exterior-to-interior fit of Helstrom's houses is
BM&V's and was not measured (shell footprints vs room shells would need the placed exterior shell per door).

**Tools:** a room is a copy plus our changes; the room name, door pairing and `probe` checks exist (place-rooms; place-studio.md
sections on Room names and copy_space). Nothing in `tools/places` creates a room from geometry; no tool writes a shell NIF with
collision (niflod: visual only). `tools/navmesh` (ArgoniaNav) builds exterior and per-room meshes (`placed.py`, `solid.py`).

## 3. What image-to-3D and scene generators can do for rooms (evidence)

- **Tripo, Meshy, Rodin, Hunyuan3D, Trellis are object generators.** I found no vendor feature that makes a navigable room or
  building interior from an image [SNIPPET: searches, 2026-11-24, found only listicles and Scenario help pages]. Tripo's
  `generateParts` (V3.0/3.1; cannot combine with texture, PBR or quad output) and separate Segment v1/v2 split a mesh into
  parts [SNIPPET: fal.ai tripo segment llms.txt, Alibaba Model Studio docs, scenario.com blog]. Meshy "image to several
  semantic meshes" [SNIPPET, listing site]. Rodin takes up to 10 reference images [SNIPPET]. None is a scene tool.
- **Single-view room reconstruction is ambiguous**: the model must invent unseen parts [SNIPPET: arXiv 2512.17955 and the
  Total3DUnderstanding paper, which yields non-watertight meshes on complex shapes]. [OWN] An object generator given a hut
  photo returns a closed outside hull with the door painted on; the inside is solid or a thin skin facing outward.
- **World generators output splats or heavy meshes, not game rooms.** World Labs Marble: Gaussian-splat export; collider
  mesh GLB 3-4 MB (Standard plan); high-quality GLB about 600k triangles textured or about 1M with vertex colours, 100-200 MB,
  up to an hour, "floaters" and holes expected on thin structures; docs themselves recommend splat for clean quality; the free
  plan cannot export [PAGE: docs.worldlabs.ai/marble/export/mesh, no date on page]. HunyuanWorld 1.0 builds layered meshes from a
  360 panorama; community licence; some scenes fail to load on small hardware [SNIPPET: repo mirror, arXiv 2507.21809]. [OWN] Both
  are far over a Skyrim cell's triangle and texel budget, have no navmesh, and a panorama-derived interior is a one-viewpoint
  surface. I found nothing on SpAItial.
- **Layout-by-LLM research exists but places pre-made assets.** Holodeck (CVPR 2024): GPT-4 proposes spatial constraints, a solver
  places Objaverse assets, built on AI2-THOR; preferred over ProcTHOR in a 680-person study. LayoutGPT places objects directly and
  often ignores physical plausibility [SNIPPET: arXiv 2312.09067, Holodeck 2.0 2508.05899]. RoomPlanner (arXiv 2511.17048) adds
  door/window agents; World Craft (arXiv 2601.09150) carves rooms inward from a building envelope and places doors for circulation
  [SNIPPET]. No paper I found takes an existing exterior's door and window positions as input (searched once).
- **Procedural interiors**: Infinigen Indoors (Princeton, CVPR 2024): 100% procedural, Blender-based, constraint arrangement, exports to
  Omniverse and Unreal; runs as a Blender Python script [SNIPPET: arXiv 2406.11824, cgchannel 2025-06-30]. Photoreal Western rooms, not
  Skyrim and not low-poly. Sloyd: parametric building generators, "Low Poly" preset about 5,000 triangles, 512 px textures; its older
  API said not accepting new clients [SNIPPET: sloyd.gitbook.io, checked 2026-11-24; current API access UNVERIFIED].
- **AI-built modular kits**: I found no shipped example and no benchmark of generated wall/floor/corner pieces snapping [SNIPPET:
  search found only grid-snapping Blender add-ons such as ModularKit and a Summer Engine "blender kit" preset advising grid-first
  authoring]. [OWN, from texel and thin-part notes in the pipeline report] The expected failures: bounding boxes off the grid by
  a few percent (gaps), seams where baked textures do not tile, thin walls with no thickness, pivots at the centre not the base.
  UNVERIFIED by any trial.
- **Texel density at room scale** (pipeline report, line 45): one 2K texture is 683 px/m on 3 m, 256 on 8 m; a room shell of 8 to 12 m
  with unique texture is soft; shared tiling materials are the only way a room stays sharp.

## 4. Claude Code, MCP and agent write-ups

- **blender-mcp** (github.com/ahujasid/blender-mcp): Claude drives a live Blender; guides claim furniture placement and layouts, port 9876
  conflict with a second server [SNIPPET]. A hands-on review (MindStudio, 2026-05-06) [PAGE]: rooms, product shots and
  architectural concepts "play to the integration's strengths"; exact positioning needs several correction rounds; multi-object
  alignment "hit or miss"; Claude "doesn't reason about topology"; proportions need human review. Third-party extras: `blender-orchestrator`
  with a `create_room_bounds` tool and a reference of real-world dimensions for about 55 objects [SNIPPET]. All vendor or blog level.
- **Unity/Godot/Unreal MCP**: a Unity temple level built in 1,344 tool calls; "tools handle structure and wiring well; judging how the
  scene looks still needs a person looking at captures" (strayspark.studio, a seller of the tool) [SNIPPET]. No Unreal level-blockout
  post-mortem found.
- **Skyrim-specific agent tooling**: houseCARL (read-side Mutagen MCP over an MO2 profile), Skyrim Claude Code Modding Toolkit (XEditLib),
  Skyrim Forge (typed jobs for xEdit, CK, Wrye Bash), bgs-modding-superpowers (xEdit MCP, Papyrus), Spooky's AutoMod Toolkit
  [SNIPPET: mcpmarket.com, nexusmods.com/skyrimspecialedition/mods/181738, skillsmp.com]. None builds geometry or a room from an
  exterior; they edit records and scripts. Our own `tools/places` is further along for rooms than any of these.
- **LLM layout planners**: Holodeck/RoomPlanner/Co-Layout (integer programming over LLM-sampled constraints) [SNIPPET]; method
  that matches the owner's idea ("derive the floor plan from the exterior footprint, carry door and window positions"): World Craft's
  envelope-inward carving is the closest [SNIPPET]; nothing tested on a game with fixed shells.
- **No write-up of an agent building a Skyrim interior and passing a check** exists in my results. [OWN] The part an agent would do
  well is the part we already automate (records, door pairs, arrivals); the part it does badly is judging look, which is the owner's.

## 5. Feasibility for us, ranked from easiest

Fits the "simple things first" rule means: reuse a record or a held mod before geometry (CLAUDE.md "Reuse first").

**(a) No new geometry: Argonian interiors from held shells, paired to exteriors. EASIEST; in use.**
Needs: `room.copy_of` rows, door pairs, arrivals, names (place-rooms). Collision, navmesh, bounds, lights all come with the source
cell. Tools: complete. Gaps: only ~21 hut shells and 3 bamboo/mud kits, so the same 5 to 10 room looks repeat (the Helstrom
house is already 18 of 41). Risk: sameness. Cheap mitigation: pick a different held shell per house (KotM has 5 `house*in`,
3 `mudhutint`, 3 `roundhut*int`, 2 `smpodint`), re-dress furniture by place-adapt. Fits the rule.

**(b) Re-dress an existing shell with reed/mud materials. EASY, mostly records.**
Needs: a material-swap (BSLightingShaderProperty texture sets) on a copy of a vanilla or mod shell NIF saved under a new path, plus
the carried cell's refs pointed at the new path. Tools: niflod writes shaders and texture sets, nifdump reads (pipeline
report lines 18-21); a "re-texture an existing mesh" step is not yet proved, and the shared material library does not exist yet
(PROPOSAL.md section 5). Collision, navmesh, bounds unchanged because geometry is unchanged. Risk: licence of the donor shell
(KotM's AI clause, PROPOSAL.md section 8; vanilla Skyrim shells are fine for private build, never committed). Fits the rule.

**(c) A small new modular kit by script in Blender. MEDIUM; the first real new geometry.**
Needs (human-kit measure, section 1): a piece list (floor 1x1 and 2x2, wall straight, corner in/out, doorway, window wall, roof
panel, post, stair, partition), a grid (128 or 256 units), centred ground pivots, fixed floor thickness, per-piece MOPP
collision, a navmesh per placed room, lights, LOD only for the exterior side. [OWN] A minimal hut kit is about 12 to 20 pieces
(KotM's `housepartion`+`plankwall`+door/window set is 17 pieces; Skyrim's small hallway sub-kit is about 50). Generated geometry
is only for ornament (a carved post), per PROPOSAL.md. Tools missing: collision writer (niflod or PyNifly; the Blender exporter
is Windows-only per the pipeline report), a room-bounds/portal step (none needed for one-room huts), a snap/fit linter. Risks:
collision and navmesh joins at piece seams, texel density (use tiling materials), our own authoring time (the Skyrim kit cycle was
weeks per kit with dedicated artists). Violates "simple first" until (a) and (b) are exhausted.

**(d) One-piece interior shell derived from a generated exterior. HARD; the Argonian mods' own shell approach, automated badly.**
Needs: invert or offset the hull, cut door and window openings, thicken to a wall, add a floor, UV to tiling materials, write walkable
MOPP collision of the inner face, a navmesh, doors. The shipped huts (section 2) are authored pairs, not derived: interior size
80-120 percent of the exterior, never the same mesh. [OWN] A generated exterior hull has no thickness and dirty topology, so the derived
inside is unlikely to be walkable without hand repair; I would not try this before (c).

**(e) Fully generated rooms. NOT FEASIBLE for Skyrim today.** Splat or 600k-triangle outputs, no collision or navmesh, no tools in our
stack, and no source I found ships one. Marble's collider mesh is the only game-shaped output and is a simplified blob.

**Exterior side of any new building.** A new building exterior is a static shell: visual mesh, a walkable collision proxy if players
climb on it (MOPP), a door frame at a fixed size, a navmesh cut around its footprint in the exterior mesh, and LOD. Texel density at
6-12 m: 256 px/m at 8 m with one 2K texture, soft past 8 m; so tiling shared materials, split into parts, or accept a distant-only
view (pipeline report). Our exterior navmesh tool already accounts for placed shells (`tools/navmesh/ArgoniaNav/placed.py`); LOD we
write ourselves (docs/design/lod.md via niflod). **Yes: "new exterior as a static shell with a closed door, interior from an existing
kit behind a load door" is the cheap route**, and matches how the held Argonian mods already work (a separate interior shell behind a
load door, 80-120 percent of the exterior). It needs one new building block (a new shell NIF with collision) and nothing else new:
the door pair, room copy, arrival and names already exist. A closed shell with no interior (a facade) needs only the NIF
(BM&V's towns are mostly facades: about one enterable building per town, c-interiors-and-places.md).

## 6. Recommendation

1. **Do (a) now and improve it with (b)-level choices before any geometry:** vary which held shell each house uses, so rooms stop
   being 18 copies; take the KotM `house*in`/`roundhut*int`/`smpodint`/bamboo pairs (about 21 shells) as the Argonian interior stock.
   This is record work in place-rooms. **Well evidenced** (measured above).
2. **Treat new interiors as out of scope at every level of the new-art proposal for now** (keep PROPOSAL.md section 6's last list), and
   record the exception: a new *exterior* shell (stilt house, root-grown house) is allowed once the pilot proves collision writing,
   because the interior comes from (a). **Inference.**
3. If the owner wants a root-grown or stilt house with a matching interior, run **one trial of (c) at its smallest** (one room, about 12
   pieces, tiling materials) after the 5-model pilot, not before. **Inference.**

## 7. What only a trial would settle

Well evidenced (above): the Argonian mods use paired shells at 80-120 percent footprint; carried rooms cost records only; 4 shadow
casters is the cap; kits snap on 128 units; Marble/Hunyuan output is splat or hundreds of thousands of triangles; no source I found
ships AI-generated interiors for Skyrim.

Needs a trial (my inference, no source):
- Whether PyNifly or a niflod collision extension writes MOPP collision that a Skyrim player walks on from a script-built hull.
- Whether a retextured copy of a KotM or BM&V shell reads as Argonian to the owner (owner judges look).
- Whether a Tripo/Hunyuan exterior hull can be turned into a walkable shell at all (my guess: no) and what a hand-made inside costs.
- Whether a scripted 12-piece kit snaps without seams in game (piece fit at 128 units; MOPP seams; navmesh across joins).
- Whether the owner accepts an interior 80-120 percent of the exterior size (all held Argonian mods do) or wants exact match.
- Real Tripo `generateParts` output on a hut photo (UNVERIFIED; no write-up found).
- KotM's AI clause: whether new shells made by us may sit beside its huts (PROPOSAL.md section 8).

Covered: docs/research/new-art (PROPOSAL, places-and-pieces and asset-pipeline sections), .claude/skills/place-rooms, place-adapt, place-system, docs/decisions/0041, docs/research/world/c-interiors-and-places.md, docs/design/place-studio.md (grep), out/places/catalogue/bases.jsonl, out/places/srccells, newworld/places/*/spaces, newworld/out/world.sqlite (source_place), ~20 web searches · Skipped: tooling.md and visual-consistency.md beyond PROPOSAL's summary (already digested there); tools/navmesh source (named from file list only); nexus pages and CK wiki (403 on fetch, snippets only); no mesh opened, so shell look is unjudged.
