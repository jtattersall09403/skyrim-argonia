"""tools/places/build.join_seams: two cells' open seam edges are joined edge for edge, both ways."""
import numpy as np

from tools.navmesh import nvnm
from tools.places import build as B


def cell_mesh(x0, z):
    verts = np.array([[x0, 0, z], [x0 + 4096, 0, z], [x0 + 4096, 4096, z], [x0, 4096, z]], np.float32)
    tris = np.zeros(2, nvnm.TRI)
    tris[0] = ((0, 1, 2), (-1, -1, 1), nvnm.FOUND, 0)
    tris[1] = ((0, 2, 3), (0, -1, -1), nvnm.FOUND, 0)
    return nvnm.Nvnm(1, (x0 // 4096, 0), None, verts, tris)


def test_open_seam_edges_join_both_ways():
    a = {"fid": 0x10, "space": "exterior", "cell": [0, 0], "nv": cell_mesh(0, 100)}
    b = {"fid": 0x11, "space": "exterior", "cell": [1, 0], "nv": cell_mesh(4096, 110)}
    assert B.join_seams([a, b]) == 1
    ta, tb = a["nv"].tris[0], b["nv"].tris[1]
    assert ta["flags"] & nvnm.EDGE_LINK[1] and a["nv"].links[ta["e"][1]]["navm"] == 0x11
    assert a["nv"].links[ta["e"][1]]["tri"] == 1
    assert tb["flags"] & nvnm.EDGE_LINK[2] and b["nv"].links[tb["e"][2]]["tri"] == 0
    assert B.join_seams([a, b]) == 0  # idempotent: nothing left open


def test_edges_at_different_heights_stay_open():
    a = {"fid": 0x10, "space": "exterior", "cell": [0, 0], "nv": cell_mesh(0, 100)}
    b = {"fid": 0x11, "space": "exterior", "cell": [1, 0], "nv": cell_mesh(4096, 400)}
    assert B.join_seams([a, b]) == 0


def test_a_one_way_link_is_opened_then_joined_both_ways():
    a = {"fid": 0x10, "space": "exterior", "cell": [0, 0], "nv": cell_mesh(0, 100)}
    b = {"fid": 0x11, "space": "exterior", "cell": [1, 0], "nv": cell_mesh(4096, 100)}
    nv = a["nv"]
    nv.links = np.array([(nvnm.PORTAL, 0x11, 0)], nvnm.LINK)  # points at b's tri 0, which does not answer
    nv.tris["e"][0][1] = 0
    nv.tris["flags"][0] |= nvnm.EDGE_LINK[1]
    assert B.unlink_one_way([a, b]) == 1
    assert B.join_seams([a, b]) == 1
    assert a["nv"].links[a["nv"].tris[0]["e"][1]]["tri"] == 1


def test_a_door_triangle_is_the_ground_beside_not_the_roof_over_the_arrival():
    verts = np.array([[0, 0, 100], [80, 0, 100], [0, 80, 100], [100, 100, 500], [300, 100, 500], [100, 300, 500]], np.float32)
    tris = np.zeros(2, nvnm.TRI)
    tris[0] = ((0, 1, 2), (-1, -1, -1), nvnm.FOUND, 0)  # ground, the arrival a step beside it
    tris[1] = ((3, 4, 5), (-1, -1, -1), nvnm.FOUND, 0)  # an overhang's top, over the arrival in plan
    n = nvnm.Nvnm(1, (0, 0), None, verts, tris)
    assert B.tri_under(n, (120, 120, 104)) == 0
