# Walk 2, lane seat: how placed things sit on the ground (L6, L11, L12)

## (a) The lines

| L# | cause (measured) | change | proof |
|---|---|---|---|
| L6 | The 85 `seat` rows of 2026-11-12 lowered each lying log and stump until its lowest vertex touched the ground, and that vertex is a root tip. The audit of the main tree's placed refs (508,237) finds 4,967 logs whose bulk (the median underside of the log's body) hovers more than 0.25 m, 676 logs whose lowest point is still over 0.5 m up, and 2,928 stumps whose trunk foot hovers. The worst is KoTM's uprooted cypress log, its bulk 16.7 m above the ground. The old seater also turned the mesh the wrong way: its rotation was the transpose of Skyrim's, so for any thing turned about z it judged the ground under the wrong points. | A new seating rule, `tools/newworld/place/audit.py`, is step 7 of the placement and applies to every placed thing. A lying log is seated so the median underside of its bulk is at the ground. Bulk means the columns at least 40% as thick as the thick ones, so not a root tip or a twig. It is laid either at its own tilt or flat on the ground's plane, at whichever of 16 yaws is first to leave no part of its bulk spanning a hollow (p90 no more than 0.5 m up). If no such pose exists, the log is not placed there. An upright log (a stump) is seated by its trunk's foot ring, 0.25 m into the ground. The rotation is now Skyrim's own (`tools.navmesh.placed.rotation`). The `seat` edit rows now use the same rule. | Skyrim.esm, Tamriel's logs and stumps standing on the land alone (no rock within 6 m), 30 a mesh at most: the bulk median sits at +0.13 m (p25 -0.29, n 351) and the stump foot ring at -0.25 m (p25 -0.95, n 441). The rule seats the bulk at 0.0 and the stump at -0.25. On the small world after the change: bulk_hovers 0, floats 0. 76 logs and 92 stumps were reseated, and 48 logs were refused. Of the block's 124 lying logs, 48 had no pose that kept their bulk off a hollow. Tests: `tools/tests/test_newworld_place_audit.py` (a log with a root tip). |
| L11 | Trees were seated by a pivot sink taken from their source worlds. On a slope that leaves the downhill side of the trunk in the air, and the seat rows then only lowered a root tip onto the ground. In the main tree's refs, 76,250 things standing on a trunk have the highest point of their trunk's foot ring more than 0.1 m above the ground: understorey 34,639, canopy_tree 26,982, mushroom 7,964, palm 3,737 (and 2,928 stumps, under L6). Some stand half over a bank, for example a cypress at (203670, -807545) with half its foot over an 8 m drop into a lake. | Each mesh's trunk is found: the closed column round its axis 0.3 to 1.2 m up, followed down while its cylinder stays closed. Its foot ring is posed with the ref's rotation and scale. z is set so the ring's highest point is 0.1 m under the ground, so the trunk's base is at or below the ground at every point round it, slope included. If the ground under the ring spreads more than the 35-degree tree slope window allows across its width (plus 0.3 m), as with a trunk half over a bank, the tree is not placed there. | Skyrim.esm's trees on the land alone: the foot ring's highest point sits at -0.06 m (p25 -0.52, n 2,920), and the rule seats it at -0.1. On the small world after the change: trunk_hovers 0, and 3,519 trees and plants were reseated. Tests: a tree on a slope; a tree half over a bank is refused. |
| L12 | Rocks and cliffs were checked only by a box shrunk from their bounds, and turned by a measured open side that only some shells have (a boulder whose open side was never measured was given any yaw). In the main tree's refs, 9,282 shells show their hollow rim (the edge of the mesh's open side, the 95th percentile of the rim more than 0.1 m above the ground): boulder 7,614, road rock piles 1,049, seabed_rock 506, cliff 112, road boulder 1. The worst is KoTM's ArgoniaRockL01, its rim 40 m up. The sandy rocky piece in tmp/image copy 17.png is one of these: an open-bottomed mesh hanging on a root tip with its hollow underside at head height. | Each mesh's open rim is found (the edges of one face only, after coincident vertices are welded) and posed. A rock, cliff, seabed rock or road dressing rock that is open by 0.2 or more is posed at its own tilt or laid on the ground's plane (at most 45 degrees), at whichever of 16 yaws needs the least burial to put its rim under the ground. It is then sunk until the rim is 0.05 m below. If that burial passes 0.35 of its height, it is not placed there. x, y and form ids are kept; only z, the tilt and the yaw change. | Skyrim.esm's own rocks on the land alone show their rim at +0.16 m (median, n 1,356): Skyrim hides the rest by stacking rocks, which our placement does not do. So the rule is stricter than Skyrim, by the owner's ruling (the open side never visible). On the small world after the change: hollow_shows 0, 330 rocks reseated or turned, and 19 refused. Tests: a bottomless rock is buried or refused; a shell is turned so its open back faces into the hill. |

### The audit (the placement's check)

`python -m tools.newworld.place.audit refs [DIR]` reads every placed ref and its base's mesh, judges each against the
ground under its footprint, and lists each fault class by kind. The placement's check (`python -m tools.newworld.place
check`) runs it and needs zero in every class: `seat_trunk_hovers`, `seat_bulk_hovers`, `seat_hollow_shows` and
`seat_floats`.

| class | main tree now (508,237 refs) | small world after |
|---|---|---|
| trunk_hovers (foot ring > 0.1 m up) | 76,250: understorey 34,639, canopy_tree 26,982, mushroom 7,964, palm 3,737, log (stumps) 2,928 | 0 |
| bulk_hovers (log bulk median > 0.25 m up) | 4,967: log | 0 |
| hollow_shows (open rim p95 > 0.1 m up) | 9,282: boulder 7,614, road_rock_pile 1,049, seabed_rock 506, cliff 112, road_boulder 1 | 0 |
| floats (lowest point > 0.5 m up) | 1,287: log 676, understorey 395, water_plant 85, canopy_tree 56, herb 53, palm 12, mushroom 5, fern 4, seabed_plant 1 | 0 |

Every placed kind is judged. Herbs, ferns, reeds and water and seabed plants have no trunk, bulk or rim to read, so
they are judged only by whether they float. Ecology and the dressing lane place no static refs into the flora shards,
so they have no rows here.

## (b) Walk checks

- Lying trees and logs: go to "D5, the highest danger: Murkwood cypress swamp" and look at the fallen cypress trunks
  and logs on the ground. Each should lie on the ground along its length, or be partly sunk into it. None should rest
  on a root tip with its body in the air. Reply ok, or fault with what you saw.
- Standing trees on slopes: at "A dry region: Aunike Ridge scrub", walk round a few trees that stand on sloping ground
  and look at the downhill side of the trunk. The base of the trunk should go into the ground all the way round, with
  no gap under it and no trunk held up on its roots. Reply ok, or fault.
- Hollow rocks: go to "D1, the lowest danger: Cape Percar open coast", where the sandy rocky piece in your picture
  was. Walk round the rocks and cliff pieces nearby and look under and behind them. You should never be able to see
  into a hollow side or underside. Reply ok, or fault with where you were.
- Cliffs on hillsides: at "Fresh black water creatures: Banujha Basin", look at the cliff pieces on the slopes from
  below and from the side. Any open back should face into the hill and be buried in it. Reply ok, or fault.

## (c) For the lead

- The changes.md row is "Placement rules" (`tools/newworld/place/place.py`, `audit.py`). It makes `place` stale, and
  after it `edits`, `paint`, `mist`, `navmesh`, `map`, `ecology`, `dressing`, `esm` and `readback`. Then the deploy,
  and the LOD's tree and object step, since trees moved in z and some rocks turned. All of these fall within the
  lead's one rebuild: `tools/newworld/rebuild.sh run`, then the read-backs, the deploy and the one LOD build.
- `checks.py` changed ("The placement's check" row), so `place`'s check is rerun as part of the same rebuild.
- One small change outside this lane: `tools/newworld/rebuild.py`, where the `place` stage now reads
  `tools/newworld/place/audit.py` (the test that each stage reads its code requires it).
- The 85 `seat` rows in `newworld/sources/placed_edits.jsonl` stay. They now mean "seat by the mesh rule", which the
  placement already does, so they move nothing unless the ground changes.
- After the rebuild, run `python -m tools.newworld.place.audit refs out/newworld/plugin/refs/flora`. It should show 0
  in every class, and the rebuild's place check proves the same.
- Decide: `rebuild.sh small` is green in every stage except `map`, where the row "the block's LOD plan holds
  lodmodel: 0 bases (at least 1)" fails. The block had one base with its own LOD model: one cliff piece
  (`_resourcepack\landscape\rocks\desertrockscliff02.nif`, at 81599, -488163). It is a slab open underneath, standing
  on a slope. No tilt or yaw buries its open rim within 0.35 of its height, so the rule now refuses it: it was showing
  its hollow underside, the L12 fault. So the row has nothing to count. In the main tree's small world it passed
  with that one base. Either the row's floor moves to a base that is still placed in the block (the small-world tool,
  `tools/newworld/small`), or the row accepts 0 when the placement refuses the block's only LOD-model base. I
  changed neither, because both are outside this lane. The block's read-back is 68 rows judged, 0 FAIL.
- For eco (dressing): `tools/newworld/dressing/hang_points.py` poses hang points with `place.seat.rot_matrix`. That
  is the transpose of Skyrim's reference rotation (`tools.navmesh.placed.rotation`), so on a tree turned about z, a
  moss hang point lands on the mirrored side. Its test, `test_hang_world_posed_by_tree`, asserts the transposed
  convention (rz = pi/2 takes +x to +y, where Skyrim's clockwise yaw takes it to -y). I kept `seat.rot_matrix` as it
  was, for that reader alone, so the eco lane can make the change with its own test.
