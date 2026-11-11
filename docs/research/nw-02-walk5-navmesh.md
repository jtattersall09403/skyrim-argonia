# The navmesh and what is placed on the world (nw-02 walk 5)

## What Skyrim's own navmesh does

Measured on Skyrim.esm's Tamriel by `python -m tools.navmesh.vanilla --every 2` (half of the cells that hold
references; every exterior NAVM against every TREE, FLOR and STAT reference with navmesh within 384 units) and
`python -m tools.navmesh.vanilla islands` (every exterior NAVM joined by its neighbours and edge links). For each
reference the solid collision of its mesh is cut to the band a body fills (32 to 128 units above the ground, the
CK's climb and agent height) and a point of it is tested against the navmesh triangles.

| Kind | References | The navmesh is cut round it |
|---|---|---|
| Trees, collision in the band | 17,144 | 0.94 to 1.00 at every trunk radius: 0.947 of 1,065 at 8 to 12 units, 0.961 of 2,899 at 12 to 16, 0.98 at 20 to 28, 1.00 of 316 over 96 |
| Fallen logs and stumps | 1,847 | 0.81 to 1.00 at every radius; 0.86 to 0.95 once the top is over 16 units |
| Rocks, by the top's height above the ground | 15,960 | 0.37 at 0 to 16, 0.48 at 16 to 32, 0.56 at 32 to 48, 0.64 at 48 to 64, 0.73 at 64 to 96, 0.78 at 96 to 128, 0.87 over 128 |
| Plants and shrubs with collision, by the top | 2,276 | 0.18 at 0 to 16, 0.30 at 16 to 32, 0.74 at 64 to 96, 0.91 at 96 to 128 |
| Plants and shrubs with no collision at all | 29,243 | never: nothing to cut |

- There is no width below which Bethesda leaves a standing thing to the actors' own avoidance: the thinnest trunks
  (8 to 12 units) are cut round as often as the thickest. What decides is height: a thing that rises into the
  body's band is cut round, a thing that stays under stepping height is mostly left on the mesh.
- Bushes and shrubs: 93 % of Skyrim's plants on navmeshed ground have no collision, and those never cut. A plant
  that has collision and rises to body height is cut round like a tree (0.74 to 0.91). So a plant's collision is
  its body for the navmesh, however loosely the hull is drawn; there is no class of plant that is waved through.
- The gap from a point inside a trunk to the navmesh's edge is 17 to 52 units at its median for trunks of 8 to 40
  units' radius: a clearance of roughly 10 to 30 units beyond the bark.
- Cut-off pieces: Skyrim's navmesh (12.24 km2 in 12,817 records) is 2,705 pieces. 5.95 % of its area is off the
  largest piece. Pieces under 50 m2: 1,906 of them, 0.215 % of the area (0.18 % in forest cells, 0.28 % in rock
  cells); 940 are under 10 m2. Bethesda leaves small sealed pieces in the mesh.

## How ours applies it

- Every producer's shards (`plugin/refs/<producer>/cy*.jsonl`) are read; a reference is collidable when its base's
  mesh has solid collision.
- A placed thing is reduced, once, to the voxel columns it blocks (`tools/navmesh/solid.py`): a column of the
  navmesh's 16-unit grid is blocked when the thing's solid reaches into the band over the ground at the column's
  centre, above the 32-unit climb and under the 128-unit height. The solid is the collision's faces and what they
  enclose (a rock's collision has no underside, a trunk's hull is hollow), and the ground one thing closes in is
  inside it. What stays under the climb is stepped over; what hangs over an actor's head is walked under.
  ArgoniaNav is handed blocked columns, never triangles, and lays no mesh there. The clearance is its erosion of one
  voxel (16 units) beyond the blocked columns, inside Skyrim's 10 to 30.
- The reduction is done a cell row of references at a time and kept by row under the digest of what it is made
  from; ArgoniaNav keeps each cell under the digest of its own window. A second build on unchanged inputs reuses
  every row and every cell and writes the same bytes.
- The flora placer keeps the road's walking width clear by the same columns
  (`tools/newworld/place/place.py`, step 6): no blocked column within 48 units (the actor's radius and a voxel) of
  the wider of the road's surface and the 192-unit strip the navmesh marks as road. A natural reference that falls
  short is refused; road dressing is moved straight out by what it falls short.
- A built place's navmesh is cut round the same shards (`tools/places/build.py`, `exterior_navmesh`), less the world
  references the place clears, so the cells round the place come out byte for byte the world's own and the join is
  edge for edge. The place's clearance clears a world thing whose blocked columns come within 48 units of a street's
  surface or a door front, wherever it is rooted (`tools/places/draft/clear.py`, `across`).
- A row of references is kept under a digest that takes in `solid.py` and `placed.py` themselves: an edit to either
  builds every row again.
- Small sealed pieces are left in the mesh, as Skyrim leaves them. The check lists every place and road vertex that
  lies in a cut-off piece (`check.json`, `province.reach`).
- Two readings of the mesh files are corrected in `nif.py`: a node's rotation was applied transposed (every
  bone-mounted trunk capsule lay on its side), and a capsule was taken as its axis-aligned box. 32 of the 469 flora
  bases read differently for it. The flora placer seats by the base record's bounds, not by collision, so no
  reference is re-seated by the correction; none of the place tools' eight cached walk tops changes.

## The fast test

`python -m tools.navmesh sample` builds five blocks of 64 cells, each on the bare ground and again round what is
placed, in about two minutes (85 seconds when the rows are kept), and is green when every block's checks are, every
collidable reference is fed and the road is on the mesh no less than on the bare ground.

| Block | Cells | Road on the mesh, placed (bare) | Cut-off pieces, m2 | Tall things cut round |
|---|---|---|---|---|
| jungle-road: hist grove, cypress swamp, a dressed road | -16,-152 to -9,-145 | 1,597 of 1,597 (1,597) | 62, 759 | 1.00 |
| upland: scrub and outcrop, cliff pieces, a dressed road | -24,-176 to -17,-169 | 1,659 of 1,659 (1,650) | 27, 342 | 1.00 |
| marsh: drowned forest, trees in water | -40,-200 to -33,-193 | 861 of 861 (861) | 39, 1,633 | 0.995 |
| town-approach: the roads into Gul-Tej past mountain-trim pieces | -40,-160 to -33,-153 | 1,778 of 1,778 (1,778) | 18, 170 | 1.00 |
| coast-ridges: ridge pieces across a shore east of Lilmoth | 36,-223 to 43,-216 | 183 of 183 (183) | 17, 12,037 | 0.963 |

Before the road rule the same blocks held 0.70, 0.98, 0.86, 0.80 and 0.67 of their road samples.

## The province

Build 20261111T100156Z, 528,295 references in the navmesh's cells, 296,472 collidable, all fed, none unread.

| Measure | Bare ground | Round what is placed |
|---|---|---|
| Land cells without a mesh | 0 of 11,589 | 0 of 11,589 |
| Settlement paths | 20 of 20 | 20 of 20 |
| Seams mismatched, unmatched | 0, 0 | 0, 0 |
| Dry road samples on the mesh | 0.9986 | 0.9992 |
| Vertices off the ground by more than 32 units | 0 | 0 (the furthest 26.0) |
| Main piece | 40.01 km2, 0.9757 of the mesh | 33.92 km2, 0.9709 |
| Cut-off pieces on a main landmass | 134, 24,974 m2 | 3,089, 92,888 m2 (0.27 % of the mesh) |
| Cut-off pieces under 50 m2 | | 2,871, 28,961 m2 (0.082 %; Skyrim 0.215 %) |
| Tall placed things the mesh is cut round | | 0.9926 of 18,302 probed |

- 138 million columns are blocked: 15 % of the bare ground's mesh lies under placed collision. The mod trees'
  collision is wide (a hull round the whole buttress or crown, scaled with the tree).
- The largest cut-off piece is 10,304 m2 at (170213, -901051): a beach east of Lilmoth closed off from the land by
  mountain-trim pieces placed as boulders at scale 4 (each some 120 m across) and open only to deep water. The
  next four (3,596, 3,313, 1,999, 1,598 m2) are the bare ground's own, closed in by steep terrain.
- Reach: six road vertices at (216272, -810944) lie in a 3,313 m2 piece and the place `shipwreck-25-m95` in one of
  521 m2. Both pieces are cut off on the bare ground too: the terrain's to mend, not the placement's.
- Cost: the collision instanced is 58.6 million triangles, 21.4 million of them faces in some column's band;
  ArgoniaNav reads none (it read 70 million). A full build is 15 minutes (rows 206 s, cells 370 s, stitch 199 s,
  check 141 s; it was 19 with cells at 684 s).
