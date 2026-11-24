"""A house's footprint from its collision walls, cut from the walking mesh unless someone walks into it."""
import numpy as np

from tools.places import houses_cut as H


def box(r=200.0, h=300.0):
    q = []
    C = [(-r, -r), (r, -r), (r, r), (-r, r)]
    for (x0, y0), (x1, y1) in zip(C, C[1:] + C[:1]):
        q += [[[x0, y0, 0], [x1, y1, 0], [x1, y1, h]], [[x0, y0, 0], [x1, y1, h], [x0, y0, h]]]
    return np.array(q, float)


def test_a_house_no_one_walks_into_is_blocked_and_a_lived_in_one_is_not():
    rows = [{"id": "h", "base": "B", "kind": "building", "pos": [1000.0, 0.0, 50.0], "rot": [0, 0, 0.5], "scale": 1.0},
            {"id": "s", "base": "S", "kind": "building", "pos": [0.0, 0.0, 0.0], "rot": [0, 0, 0], "scale": 1.0}]
    bases = {"B": {"edid": "Hut01", "model": "hut.nif"}, "S": {"edid": "MudHutStairs03", "model": "stairs.nif"}}
    got = H.blocks(rows, bases, lambda m: box())
    assert [b["id"] for b in got] == ["h.house"] and all(p[2] == 50.0 for p in got[0]["outline"])
    assert H.blocks(rows, bases, lambda m: box(), keep=[[1000.0, 0.0]]) == []
    # a mesh with a triangle in the hut is named; one round it is not
    nav = {"spaces": {"exterior": {"verts": [990, -10, 60, 1010, -10, 60, 1000, 10, 60, 1500, 0, 50, 1600, 0, 50, 1550, 50, 50],
                                   "tris": [0, 1, 2, 3, 4, 5]}}}
    assert [c["id"] for c in H.cut("p", nav, rows, bases, lambda m: box())] == ["h"]
