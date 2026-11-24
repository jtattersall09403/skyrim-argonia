"""A way through a house or tent on the walking mesh, from the house's collision walls (tools/places/houses_cut.py)."""
import numpy as np

from tools.places import houses_cut as H


def box(r=200.0, h=300.0, sides=4):
    q = []
    C = [(-r, -r), (r, -r), (r, r), (-r, r)]
    for (x0, y0), (x1, y1) in list(zip(C, C[1:] + C[:1]))[:sides]:
        q += [[[x0, y0, 0], [x1, y1, 0], [x1, y1, h]], [[x0, y0, 0], [x1, y1, h], [x0, y0, h]]]
    return np.array(q, float)


def strip(xs, y0=-40, y1=40, z=0.0):
    """A strip of the walking mesh along x (a quad per step, two triangles), its neighbours joined."""
    V, T = [], []
    for i, x in enumerate(xs):
        V += [[x, y0, z], [x, y1, z]]
    for i in range(len(xs) - 1):
        a = 2 * i
        T += [[a, a + 2, a + 3], [a, a + 3, a + 1]]
    nb = []
    for k in range(len(T)):
        n = [-1, -1, -1]
        if k % 2 == 0:
            n[2] = k + 1
            if k + 3 < len(T):
                n[1] = k + 3
        else:
            n[0] = k - 1
            if k - 3 >= 0:
                n[2] = k - 3
        nb += n
    return {"verts": np.asarray(V).ravel().tolist(), "tris": np.asarray(T).ravel().tolist(), "nb": nb}


def test_only_what_encloses_is_a_house():
    rows = [{"id": "h", "base": "B", "kind": "building", "pos": [0.0, 0.0, 0.0], "rot": [0, 0, 0], "scale": 1.0},
            {"id": "w", "base": "W", "kind": "building", "pos": [0.0, 0.0, 0.0], "rot": [0, 0, 0], "scale": 1.0},
            {"id": "s", "base": "S", "kind": "building", "pos": [0.0, 0.0, 0.0], "rot": [0, 0, 0], "scale": 1.0}]
    bases = {"B": {"edid": "Hut01", "model": "hut"}, "W": {"edid": "Wall01", "model": "wall"}, "S": {"edid": "Stairs01", "model": "stair"}}
    tris = {"hut": box(), "wall": box(sides=1), "stair": box()}
    assert [h["id"] for h in H.houses(rows, bases, tris.get)] == ["h"]


def test_a_mesh_running_through_a_hut_is_a_way_through_and_one_into_it_is_not():
    h = H.hull(np.array([[-200, -200], [200, -200], [200, 200], [-200, 200]], float))
    through = H.through(strip(list(range(-600, 601, 100))), h, 0.0)
    assert through and through["openings"] == 2
    assert H.through(strip(list(range(-600, 1, 100))), h, 0.0) is None          # in at one side, a dead end
    assert H.through(strip(list(range(300, 900, 100))), h, 0.0) is None         # all outside
    rows = H.door_rows({"id": "h", "edid": "Hut01", "base": "B", **through})
    assert len(rows) == 1 and rows[0]["kind"] == "block"
