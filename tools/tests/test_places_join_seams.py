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


def test_an_opened_link_leaves_the_link_table():
    a = {"fid": 0x10, "space": "exterior", "cell": [0, 0], "nv": cell_mesh(0, 100)}
    b = {"fid": 0x11, "space": "exterior", "cell": [1, 0], "nv": cell_mesh(4096, 900)}  # a cliff: nothing joins again
    nv = a["nv"]
    nv.links = np.array([(nvnm.PORTAL, 0x11, 0), (nvnm.PORTAL, 0x99, 5)], nvnm.LINK)  # b does not answer; 0x99 is the world's
    nv.tris["e"][0][1], nv.tris["e"][1][2] = 0, 1
    nv.tris["flags"][0] |= nvnm.EDGE_LINK[1]
    nv.tris["flags"][1] |= nvnm.EDGE_LINK[2]
    assert B.unlink_one_way([a, b]) == 1 and B.join_seams([a, b]) == 0
    assert [int(x) for x in nv.links["navm"]] == [0x99]  # the NVMI's linked meshes are read from this table
    assert nv.tris["e"][1][2] == 0 and nv.tris["flags"][1] & nvnm.EDGE_LINK[2] and nv.tris["e"][0][1] == -1


def test_a_door_triangle_goes_to_the_mesh_under_the_arrival():
    """An interior with two navmeshes: the door's triangle is on the one its arrival stands on, whichever is listed first."""
    far, near = cell_mesh(8192, 0), cell_mesh(0, 0)
    navs = [{"fid": 0x02000010, "space": "house", "cell_raw": 0x02000001, "nv": far},
            {"fid": 0x02000011, "space": "house", "cell_raw": 0x02000001, "nv": near}]
    P = B.PLUGIN
    refs = [{"fk": f"{P}:000020", "id": "in", "space": "house", "teleport": {"to": f"{P}:000021", "pos": [0, 0, 0]}},
            {"fk": f"{P}:000021", "id": "out", "space": "exterior", "teleport": {"to": f"{P}:000020", "pos": [3000.0, 1000.0, 0.0]}}]
    rows, notes = B.finish_navmesh(navs, {"refs": refs}, 0x01000001)
    assert [r["doors"] for r in rows] == [0, 1] and notes == ["door out: no navmesh under its arrival point"]
    assert near.tris["flags"][0] & nvnm.DOOR and int(near.doors[0]["door"]) == 0x02000020


def test_a_source_cells_navmeshes_are_copied_whole_with_their_links_when_they_join(monkeypatch):
    def src(cell_x, link_to):
        nv = cell_mesh(cell_x, 0)
        nv.world, nv.grid_xy, nv.cell = 0, None, 0x01000001
        nv.links = np.array([(nvnm.PORTAL, link_to, 1 if cell_x == 0 else 0), (nvnm.PORTAL, 0x01000777, 0)], nvnm.LINK)
        t, k = (0, 1) if cell_x == 0 else (1, 2)  # the shared edge, x = 4096
        nv.tris["e"][t][k] = 0
        nv.tris["e"][t][0] = 1  # and a link out of the cell
        nv.tris["flags"][t] |= nvnm.EDGE_LINK[k] | nvnm.EDGE_LINK[0] | nvnm.DOOR
        nvnm.build_grid(nv)
        return nvnm.encode(nv)
    held = {"Src.esm:000A01": src(0, 0x01000A02), "Src.esm:000A02": src(4096, 0x01000A01)}
    monkeypatch.setattr(B, "source_names", lambda pl: ["Skyrim.esm", "Src.esm"])
    monkeypatch.setattr(B, "source_navms", lambda pl, want: held)

    class Ids:
        def local(self, key):
            return 0x900 + int(key[-1])
    I = {"space": "house", "fk": f"{B.PLUGIN}:000001", "copy": {"plugin": "Src.esm"}, "src_plugins": ["Src.esm"], "src_navmesh": list(held)}
    a, b = B.interior_navmesh(I, {}, Ids())
    assert I["src_islands"] == 1 and a["fid"] == 0x02000901 and a["nv"].cell == 0x02000001
    assert [(int(x["navm"]), int(x["tri"])) for x in a["nv"].links] == [(0x02000902, 1)]
    t = a["nv"].tris[0]
    assert t["flags"] & nvnm.EDGE_LINK[1] and not t["flags"] & (nvnm.EDGE_LINK[0] | nvnm.DOOR) and t["e"][0] == -1
    held.update({"Src.esm:000A01": src(0, 0x01000777), "Src.esm:000A02": src(4096, 0x01000777)})  # two pieces that do not join
    assert B.interior_navmesh(I, {}, Ids()) == [] and I["src_islands"] == 2
