"""tools/places/build.join_seams: the two sides' border vertices are matched before the edges are paired, so a seam
split on one side only (Ashgate Landing's, at -98304,-527447) still closes edge for edge, both ways."""
import numpy as np

from tools.navmesh import nvnm
from tools.places import build as B
from tools.tests.test_places_join_seams import cell_mesh


def split_cell_mesh(x0, z, at, off=0.0):
    """A cell whose west seam has an extra vertex `at` along it (`off` units off the line, as a carried mesh leaves one)."""
    verts = np.array([[x0, 0, z], [x0 + 4096, 0, z], [x0 + 4096, 4096, z], [x0, 4096, z], [x0 + off, at, z]], np.float32)
    tris = np.zeros(3, nvnm.TRI)
    tris[0] = ((0, 1, 4), (-1, 1, -1), nvnm.FOUND, 0)
    tris[1] = ((4, 1, 2), (0, -1, 2), nvnm.FOUND, 0)
    tris[2] = ((4, 2, 3), (1, -1, -1), nvnm.FOUND, 0)
    return nvnm.Nvnm(1, (x0 // 4096, 0), None, verts, tris)


def all_answered(navs):
    by = {n["fid"]: n["nv"] for n in navs}
    for n in navs:
        nv = n["nv"]
        for i, t in enumerate(nv.tris):
            for k in range(3):
                if t["flags"] & nvnm.EDGE_LINK[k]:
                    L = nv.links[t["e"][k]]
                    o = by[int(L["navm"])]
                    T = o.tris[int(L["tri"])]
                    assert any(T["flags"] & nvnm.EDGE_LINK[q] and int(o.links[T["e"][q]]["tri"]) == i for q in range(3))


def open_on_seam(nv, x):
    got = 0
    for t in nv.tris:
        for k in range(3):
            a, b = nv.verts[t["v"][k]], nv.verts[t["v"][(k + 1) % 3]]
            if abs(a[0] - x) < 1 and abs(b[0] - x) < 1 and not t["flags"] & nvnm.EDGE_LINK[k]:
                got += 1
    return got


def test_a_seam_split_on_one_side_only_is_split_on_the_other_and_closes():
    for at, off in ((2000.0, 0.0), (2.2, 0.9)):   # mid-seam; Ashgate's: 2.2 from a corner and 0.9 off the line
        a = {"fid": 0x10, "space": "exterior", "cell": [0, 0], "nv": cell_mesh(0, 100)}
        b = {"fid": 0x11, "space": "exterior", "cell": [1, 0], "nv": split_cell_mesh(4096, 104, at, off)}
        assert B.join_seams([a, b]) == 2
        assert open_on_seam(a["nv"], 4096) == 0 and open_on_seam(b["nv"], 4096) == 0
        all_answered([a, b])
        nv = a["nv"]
        assert len(nv.tris) == 3
        # a's inner triangle (1) meets the piece that now holds its old neighbour edge, and that piece answers it
        def nbrs(i):
            return [int(nv.tris["e"][i][q]) for q in range(3) if not nv.tris["flags"][i] & nvnm.EDGE_LINK[q]]
        holder = [i for i in (0, 2) if 1 in nbrs(i)]
        assert len(holder) == 1 and holder[0] in nbrs(1)
        assert B.join_seams([a, b]) == 0   # idempotent


def test_border_vertices_within_the_snap_are_one_vertex():
    a = {"fid": 0x10, "space": "exterior", "cell": [0, 0], "nv": cell_mesh(0, 100)}
    b = {"fid": 0x11, "space": "exterior", "cell": [1, 0], "nv": cell_mesh(4096, 100)}
    b["nv"].verts[0][1] = 0.6   # under SEAM_SNAP from a's corner: no split
    assert B.join_seams([a, b]) == 1 and len(a["nv"].tris) == 2


def test_a_sliver_on_one_side_within_the_snap_gets_its_own_partner():
    """Ashgate Landing's river seam at -102400,-529077: one side keeps two border vertices 1.0 apart (a sliver edge on
    the seam), the other one vertex there; the other side is split at the sliver so it too closes edge for edge."""
    z = 100
    av = np.array([[0, 0, z], [4096, 0, z], [4096, 4096, z], [0, 4096, z], [4096, 2001, z]], np.float32)
    at = np.zeros(3, nvnm.TRI)   # a's east seam: one vertex, where b keeps the sliver's far end
    at[0] = ((0, 1, 4), (-1, -1, 1), nvnm.FOUND, 0)
    at[1] = ((0, 4, 2), (0, -1, 2), nvnm.FOUND, 0)
    at[2] = ((0, 2, 3), (1, -1, -1), nvnm.FOUND, 0)
    a = {"fid": 0x10, "space": "exterior", "cell": [0, 0], "nv": nvnm.Nvnm(1, (0, 0), None, av, at)}
    x0 = 4096
    bv = np.array([[x0, 0, z], [x0 + 4096, 0, z], [x0 + 4096, 4096, z], [x0, 4096, z],
                   [x0, 2000, z], [x0, 2001, z]], np.float32)
    bt = np.zeros(4, nvnm.TRI)   # b's west seam: a sliver 2000 to 2001
    bt[0] = ((0, 1, 4), (-1, 1, -1), nvnm.FOUND, 0)
    bt[1] = ((4, 1, 5), (0, 2, -1), nvnm.FOUND, 0)
    bt[2] = ((5, 1, 2), (1, -1, 3), nvnm.FOUND, 0)
    bt[3] = ((5, 2, 3), (2, -1, -1), nvnm.FOUND, 0)
    b = {"fid": 0x11, "space": "exterior", "cell": [1, 0], "nv": nvnm.Nvnm(1, (1, 0), None, bv, bt)}
    assert B.join_seams([a, b]) == 3
    assert open_on_seam(a["nv"], 4096) == 0 and open_on_seam(b["nv"], 4096) == 0
    all_answered([a, b])
    assert B.join_seams([a, b]) == 0
