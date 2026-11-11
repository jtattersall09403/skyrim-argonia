# The navmesh and what is placed on the world (nw-02 walk 5, lane N)

## What Skyrim's own navmesh does round trees, rocks and logs

Measured by `python -m tools.navmesh.vanilla --every 2` on Skyrim.esm's Tamriel (half of the cells that hold
references; every exterior NAVM against every TREE, FLOR and STAT reference with navmesh within 384 units). For each
reference the solid collision of its mesh is cut to the band a body fills (32 to 128 units above the ground, the
CK's climb and agent height) and a point of it is tested against the navmesh triangles.

| Kind | References | The navmesh is cut round it |
|---|---|---|
| Trees, collision in the band | 17,144 | 0.94 to 1.00 at every trunk radius: 0.947 of 1,065 at 8 to 12 units, 0.961 of 2,899 at 12 to 16, 0.98 at 20 to 28, 1.00 of 316 over 96 |
| Fallen logs and stumps | 1,847 | 0.81 to 1.00 at every radius; 0.86 to 0.95 once the top is over 16 units |
| Rocks, by the top's height above the ground | 15,960 | 0.37 at 0 to 16, 0.48 at 16 to 32, 0.56 at 32 to 48, 0.64 at 48 to 64, 0.73 at 64 to 96, 0.78 at 96 to 128, 0.87 over 128 |
| Plants and shrubs with collision, by the top | 2,276 | 0.18 at 0 to 16, 0.30 at 16 to 32, 0.74 at 64 to 96, 0.91 at 96 to 128 |

The rule: there is no width below which Bethesda leaves a standing thing to the actors' own avoidance. The thinnest
trunks measured (8 to 12 units) are cut round as often as the thickest. What decides is height: a thing that rises
into the body's band is cut round, a thing that stays under stepping height is mostly left on the mesh. The gap
from a point inside a trunk to the navmesh's edge is 17 to 52 units at its median for trunks of 8 to 40 units'
radius, a clearance of roughly 10 to 30 beyond the bark; ours is one 16-unit voxel of erosion beyond the voxels the
collision touches. Things with no collision (grass, ferns, reeds, mist) never cut.

## How ours applies it

- Every producer's shards (`plugin/refs/<producer>/cy*.jsonl`) are read; a reference is collidable when its base's
  mesh has solid collision. Of 526,543 references in the navmesh's cells, 295,816 are; none had an unreadable mesh.
- A placed thing is a solid obstacle: its faces are voxelised, each column is filled between the faces (a rock's
  collision has no underside, a trunk's hull is hollow), and each solid run meets the ground once: within the climb
  it is stepped over, above it the ground is cut. No mesh is laid on a placed thing.
- Two readings of the mesh files were wrong and are corrected in `nif.py`: a node's rotation was applied transposed
  (every bone-mounted trunk capsule lay on its side), and a capsule was taken as its axis-aligned box.

## What the full build shows and what it leaves open

- The mod trees' collision is wide: a hull round the whole buttress or crown, scaled with the tree (cypress 268
  units' radius at its usual scale; a jungle shrub model placed at scale 9 has a hull 1,600 wide). 16 % of the bare
  ground's mesh lies under placed collision (33.5 of 40.0 million m2 remain on the main landmass).
- Roads: 0.9198 of dry road samples are on the mesh (0.9986 on bare ground). In the sample cells the blockers were
  crown-wide hulls at scale 9 to 10, mountain-trim pieces at scale 4.5, hist glands, stumps and logs, and the
  road's own dressing at the verge. The placer keeps a road clear by an object's position; it has to keep it clear
  by the collision's width at the object's scale (`tools.navmesh.placed.footprint` measures it).
- 8,953 pockets (228,292 m2) are closed off by placed collision; the largest, 14,445 m2 at (166171, -896987), is
  not examined.
- Six vertices lie 32 to 45.6 units off the ground (the check's tolerance is 32).
- Cost: 70 million triangles for 295,816 references; a full build is 19 minutes (preparation 56 s, cells 684 s,
  stitch 205 s, check 215 s). The preparation is not cached by row and the collision is not reduced to the band.
