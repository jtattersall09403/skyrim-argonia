"""The clearance by body: a world thing whose solid collision at walking height lies across a street's walking width
or a door front is cleared wherever it is rooted; one whose body stops short, or that stays under stepping height,
stands (tools/places/draft/clear.py `across`, bodies.py). Synthetic ground and meshes."""
import numpy as np

from tools.navmesh import nif
from tools.places.draft import bodies, clear
from tools.tests.test_navmesh_newworld import CX0, CY_TOP, box_tris, ground

FRAME = (CX0 * 4096.0, (CY_TOP + 1) * 4096.0, 128.0)
MESHES = {"root.nif": box_tris(-60, -60, 1500, 60, -100, 400),   # a great root: 1500 units out from where it is rooted
          "slab.nif": box_tris(-60, -60, 1500, 60, -100, 16),    # as long, under the climb height
          "fern.nif": np.zeros((0, 3, 3))}
BASES = {"W:root": {"model": "root.nif"}, "W:slab": {"model": "slab.nif"}, "W:fern": {"model": "fern.nif"}, "W:none": {}}


class Resolver:
    def collision(self, modl):
        t = MESHES.get(modl)
        return None if t is None else nif.Collision(t, np.ones(len(t), np.uint8), {})


def at(dx, dy):
    x, y = 13 * 4096 + dx, -16 * 4096 + dy
    return [x, y, float(ground()[int((FRAME[1] - y) // 128), int((x - FRAME[0]) // 128)])]


def thing(i, base, pos, rz=0.0):
    return {"id": f"w{i}", "base": base, "kind": "tree", "pos": pos, "rot": [0, 0, rz], "scale": 1.0, "layer": "world"}


def test_a_body_is_the_columns_its_collision_blocks_at_walking_height():
    b = bodies.Bodies(BASES, ground(), FRAME, Resolver())
    root = thing(0, "W:root", at(1000, 1000))
    cols = b.columns(root)
    assert b.reach(root) > 1500 and len(cols) > 500
    assert cols[:, 0].min() < root["pos"][0] - 30 and cols[:, 0].max() > root["pos"][0] + 1450   # the whole run of it
    assert abs(cols[:, 1] - root["pos"][1]).max() < 100
    assert len(b.columns(thing(1, "W:slab", at(1000, 1000)))) == 0     # stepped over
    assert b.reach(thing(2, "W:fern", at(1000, 1000))) == 0 == b.reach(thing(3, "W:none", at(1000, 1000)))


def test_a_body_across_a_street_or_a_door_front_is_cleared_wherever_it_is_rooted():
    b = bodies.Bodies(BASES, ground(), FRAME, Resolver())
    x0, y0, _ = at(1000, 1000)
    street = [{"id": "p", "points": [[x0 + 1200, y0 - 800], [x0 + 1200, y0 + 800]], "width": 160.0}]
    across = thing(0, "W:root", at(1000, 1000))                 # rooted 1200 units off, lying across the street
    short = thing(1, "W:root", at(1000 - 500, 1000 + 300))      # ends 200 units short of it
    away = thing(2, "W:root", at(1000, 1000 + 400), rz=np.pi)   # turned the other way
    low = thing(3, "W:slab", at(1000, 1000 - 300))
    world = [across, short, away, low, {**across, "id": "w9", "kind": "marker"}]
    rows = clear.across(world, set(), street, [], b)
    assert [(r["ref"], r["why"]) for r in rows] == [("w0", "its body lies across a street")]
    assert rows[0]["base"] == "W:root" and rows[0]["by"] == "draft" and rows[0]["pos"] == [round(v, 1) for v in across["pos"]]
    assert clear.across(world, {"w0"}, street, [], b) == []     # already cleared
    door = (x0 - 500 + 1500 + 40, y0 + 300)                     # a door front 40 units past the short one's end
    assert [(r["ref"], r["why"]) for r in clear.across(world, set(), [], [door], b)] == [("w1", "its body stands in a doorway")]
    assert clear.across(world, set(), [], [], b) == []
