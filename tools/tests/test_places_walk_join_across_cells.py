"""An owner's walk-zone join whose bridge spans a cell edge is honoured: walknav clips the bridge to each cell and
join_seams links the two halves edge for edge, both ways, with no open seam edge left."""
import numpy as np

from tools.navmesh import nvnm
from tools.places import build as B
from tools.places import walknav
from tools.tests.test_places_seam_split import all_answered, open_on_seam


def island(cx, x0, x1, y0, y1, z):
    verts = np.array([[x0, y0, z], [x1, y0, z], [x1, y1, z], [x0, y1, z]], np.float32)
    tris = np.zeros(2, nvnm.TRI)
    tris[0] = ((0, 1, 2), (-1, -1, 1), nvnm.FOUND, 0)
    tris[1] = ((0, 2, 3), (0, -1, -1), nvnm.FOUND, 0)
    return nvnm.Nvnm(1, (cx, 0), None, verts, tris)


def test_a_join_across_a_cell_edge_closes_its_seam():
    a = {"fid": 0x10, "space": "exterior", "cell": [0, 0], "nv": island(0, 3700, 3950, 2000, 2300, 100), "nvmi": None}
    b = {"fid": 0x11, "space": "exterior", "cell": [1, 0], "nv": island(1, 4250, 4500, 2000, 2300, 100), "nvmi": None}
    st = walknav.apply_exterior([a, b], [{"id": "j1", "kind": "join", "points": [[3950, 2150, 100], [4250, 2150, 100]], "gap": 400}])
    assert st["joined"] == 1 and not st["refused"]
    assert open_on_seam(a["nv"], 4096) > 0       # the bridge reaches the line on both sides
    assert B.join_seams([a, b]) >= 1
    assert open_on_seam(a["nv"], 4096) == 0 and open_on_seam(b["nv"], 4096) == 0
    all_answered([a, b])
