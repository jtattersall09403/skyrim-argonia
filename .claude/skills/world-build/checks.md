# What each check proves

Every check reads the output its stage wrote (the heightmap, the shards, the written world file), never the plan
or the rule that made it. Each runs straight after its stage; a red one stops the run with its own lines. The
numbers behind each limit are in the research file named.

| Stage | Check | It proves | Mend it in | Numbers |
|---|---|---|---|---|
| the small world, before any full run | `tools/newworld/rebuild.sh small` | the stages from `land` to `readback` run green on one block of the real build, with each stage's own check below and the read-back's rows that judge a block; the block still holds one of everything a stage has a rule for; nothing under `out/newworld/` was written | the stage that owns the red check; the block (`tools/newworld/small`) when the world changed under it | |
| `tools` | the C# tools compile | the writer and the navmesh tool build before anything waits on them | the C# | |
| `terrain` | `python3 -m tools.newworld.terrain check` | the map's water lies under the water level and its land over it; every built place's beds are its held build's and its land that build's plus the ramped lift; each water kind's share of waterline triangles over 45 degrees (what the navmesh walks) is within Skyrim's for that kind; land and beds keep clear of the water plane at every LOD spacing; no road over its grade; every entrance dry and open; the build still answers everything it read (`inputs.json`) | `terrain_*.py`, `region_relief.json`, `terrain_held.json` | [relief](../../../docs/research/nw-02-walk5-relief.md) |
| `needs` | `python3 -m tools.newworld.terrain_needs` | every place has the ground its record asks for (island, rise, level pad behind the bank, shore access, seabed, entrance), but for the failures `terrain_needs_accepted.json` names, each for the reason and no worse than the value it was accepted at | the terrain's shaping, or the place's record | [relief](../../../docs/research/nw-02-walk5-relief.md) |
| `water` | `water_kinds` ends with its own two checks | each kind's bodies and area are within 2% of the accepted classification, on the same waterline and source picture; every owner edit still lies on its water with the owner's kind | `water_kinds.py`; `--accept` only on the owner's word | [water and the frame](../../../docs/research/nw-02-walk5-water-frame.md) |
| `relief` | `python3 -m tools.newworld.verify --only relief` | neighbouring regions read at least as far apart as Skyrim's; the land reaches past the picture on every side; built places keep their ground | `terrain_forms.py`, `region_relief.json` | [relief](../../../docs/research/nw-02-walk5-relief.md) |
| `landings` | `python3 -m tools.newworld.teleports landings` | every place has dry, gentle land within reach of its own cell, and every walk check its kind of water near its anchor, on this land and these water kinds | the water kinds, or the walk check's anchor in `teleports.py` | [far view](../../../docs/research/nw-02-walk5-L.md) |
| `place` | `python3 -m tools.newworld.place check` | nothing on a road (the placer itself keeps every collision at walking height clear of the road's walking width); no tree in flowing water, and in standing water only by its habitat's rule; every piece seated; no rock's open underside showing; cliffs face uphill and stand no taller than their hill; no two pieces within a metre; no cell over its budget; regions differ in what grows | `tools/newworld/place/`, the flora sets | `docs/research/nw-02-flora-rules.md` |
| `paint` | `python3 -m tools.newworld.world.texcheck` | on the engine's view (six textures a quadrant, blends per triangle): no quadrant over six; seams agree; no hard edge; roads ramp, join and keep their spine free of grass as Skyrim's do; no swathe of one ground or one grass runs further than Skyrim's holds; regions differ | `texture.py`, `roadpaint.py` | [ground](../../../docs/research/nw-02-walk5-ground.md) |
| `navmesh` | the build's own checks (`out/newworld/plugin/navmesh/check.json`), then `python3 -m tools.newworld.world.navobjects` | every land cell outside the margin has a mesh; no seam fault; no vertex off the ground; settlement pairs are joined by a path; the placed trees, rocks and cliffs cut the mesh: the objects fed are the refs in the shards that collide, by the navmesh tool's own count, and the mesh has a hole where the tall ones stand. Measured beside them, not judged: the road samples on the mesh, the cut-off pieces by size, and every place and road vertex that lies in one (`province.reach`: read it, and mend the terrain or the placement that closes them in) | `tools/navmesh/`; a road off the mesh in `tools/newworld/place/` | [navmesh](../../../docs/research/nw-02-walk5-navmesh.md) |
| `map` | `python3 -m tools.newworld.teleports check` | every teleport lands above the water, in the cell its name opens, clear of every placed object and of a built place's buildings; no name opens two cells | `teleports.py` | [far view](../../../docs/research/nw-02-walk5-L.md) |
| `esm` | `tools/newworld/world/world.sh map`, then `world.sh check` | the map box, markers, named cells and LOD flags are in the file; every cell has its land within the height error, seams match, no overflow; the water, the regions and the start marker are as planned; masters are Skyrim, Update and Black Marsh only | `tools/ArgoniaPlugin/` | |
| `readback` | `python3 -m tools.newworld.verify --skip lod,deploy,places,relief` | every requirement, with a number, on the written file and the staged stack: the plugin, land, textures, water, placed objects, mist, atmosphere, height fog, navmesh, map and start marker | the stage that owns the failing row | `out/newworld/verify/report.md` |

The navmesh has a fast test. The `navmesh` stage runs it before its province build, and it is run by hand before any
rebuild that reaches `place` or `navmesh` by a change to either:
`python3 -m tools.navmesh sample` builds five blocks of 64 cells (a dressed jungle road, an upland with cliff
pieces, a marsh with trees in water, a town's approach, a shore behind ridge pieces), each on the bare ground and
round what is placed, in about two minutes, into `out/newworld/navmesh-samples` (`--out` elsewhere in a worktree).
It is green when each block's checks are, every collidable reference is fed, and the road is on the mesh no less
than on the bare ground. A change to the placement is placed first (`python3 -m tools.newworld.place run`, three
minutes), so the test reads the refs the change makes.

On the small world the checks of `landings`, `relief` and `map` do not run, and the read-back's rows that count
the province are printed and not judged; the run names each with its reason.

The read-back's `lod`, `deploy` and `places` rows judge the other machines' work. They run in the whole read-back
(`python3 -m tools.newworld.verify`) once the LOD is built, the world file deployed and the built places rebuilt.
