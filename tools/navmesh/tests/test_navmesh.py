"""L1: the navmesh codec, the record framing and the seam stitch on synthetic meshes (no game data; the vanilla
round trip is `python -m tools.navmesh vanilla`, the real-ground build `python -m tools.navmesh build`)."""
import struct

import numpy as np

from tools.argonia_world import skyrim_units as su
from tools.navmesh import esm, nvnm, stitch


def square_nvnm() -> nvnm.Nvnm:
    v = np.array([[0, 0, 1], [100, 0, 2], [100, 100, 3], [0, 100, 4]], np.float32)
    t = np.zeros(2, nvnm.TRI)
    t[0] = ((0, 1, 2), (-1, 0, 1), nvnm.FOUND | nvnm.EDGE_LINK[2], 0)
    t[1] = ((0, 2, 3), (0, -1, -1), nvnm.FOUND | nvnm.WATER, 0)
    n = nvnm.Nvnm(0x01000800, (3, -4), None, v, t)
    n.links = np.array([(nvnm.PORTAL, 0x01600001, 7), (nvnm.PORTAL, 0x01600002, 9)], nvnm.LINK)
    n.doors = np.array([(1, nvnm.PATHING_DOOR, 0x00012345)], nvnm.DOOR_TRI)
    n.cover = np.array([1], "<i2")
    nvnm.build_grid(n)
    return n


def test_codec_round_trip_and_record_sizes():
    n = square_nvnm()
    b = nvnm.encode(n)
    assert nvnm.TRI.itemsize == 16 and nvnm.LINK.itemsize == 10 and nvnm.DOOR_TRI.itemsize == 10
    m = nvnm.decode(b)
    assert nvnm.encode(m) == b
    assert m.grid_xy == (3, -4) and struct.unpack_from("<hh", b, 12) == (-4, 3)  # grid Y first
    assert m.divisor == 1 and len(m.grid) == 1


def test_interior_parent_is_a_cell():
    n = square_nvnm()
    n.world, n.grid_xy, n.cell = 0, None, 0x0001F00D
    assert nvnm.decode(nvnm.encode(n)).cell == 0x0001F00D


def test_lookup_grid_lists_every_triangle_where_it_lies():
    n = square_nvnm()
    nvnm.build_grid(n, divisor=2)
    listed = {int(t) for c in n.grid for t in c}
    assert listed == {0, 1}
    assert 0 in n.grid[1] and 1 in n.grid[2]  # row 0 col 1 is under triangle 0, row 1 col 0 under triangle 1


def test_divisor_rule_matches_vanilla_bands():
    for t, want in ((1, 1), (16, 1), (17, 2), (49, 2), (50, 3), (99, 3), (100, 4), (499, 11), (500, 12), (1296, 12)):
        assert nvnm.divisor_for(t) == want


def test_big_subrecord_uses_xxxx():
    payload = bytes(70000)
    b = esm.pack_subrecord(b"NVNM", payload)
    assert b[:4] == b"XXXX"
    assert list(esm.subrecords(b)) == [(b"NVNM", payload)]


def strip(cx: int, cy: int, ys: list[float]) -> stitch.Mesh:
    """A cell's mesh as a strip of triangles against its east seam, the seam cut at `ys` (cell-local units)."""
    x0, y0 = su.cell_origin(cx, cy)
    e = x0 + su.CELL_UNITS
    verts, tris = [], []
    for y in ys:
        verts.append([float(e - 1000), float(y0 + y), 10.0])
        verts.append([float(e), float(y0 + y), 10.0])
    for i in range(len(ys) - 1):
        a, b, c, d = 2 * i, 2 * i + 1, 2 * i + 2, 2 * i + 3
        tris += [[a, b, d], [a, d, c]]
    return stitch.Mesh(cx, cy, verts, tris, [63] * len(tris))


def mirrored(m: stitch.Mesh, cx: int) -> stitch.Mesh:
    """The same strip as the west side of the cell to the east, with its own seam cuts."""
    x0, _ = su.cell_origin(cx, m.y)
    verts = [[x0 + (x0 - v[0]), v[1], v[2] + 5.0] for v in m.verts]
    tris = [[t[0], t[2], t[1]] for t in m.tris]  # mirrored: keep counter-clockwise
    return stitch.Mesh(cx, m.y, verts, tris, list(m.area))


def test_seams_split_to_the_same_cuts_and_link_both_ways():
    a = strip(0, 0, [0, 1024, 4096])
    b = mirrored(strip(0, 0, [0, 2048, 3000, 4096]), 1)
    pa, pb = stitch.seam_points(a, "E"), stitch.seam_points(b, "W")
    assert stitch.split_seams(a, {"E": pb}) == 2 and stitch.split_seams(b, {"W": pa}) == 1
    assert {k for k in stitch.seam_edges(a, "E")} == {k for k in stitch.seam_edges(b, "W")}
    n = stitch.link_seam(a, b, "E")
    assert n == 4
    back = {(t, k): (c, u) for (t, k), (c, u) in a.links.items()}
    for (tb, kb), ((cx, cy), ta) in b.links.items():
        assert (cx, cy) == (0, 0)
        assert any(v == ((1, 0), tb) for (t, _), v in back.items() if t == ta)


def test_a_seam_step_higher_than_the_limit_is_not_linked():
    a = strip(0, 0, [0, 4096])
    b = mirrored(strip(0, 0, [0, 4096]), 1)
    for v in b.verts:
        v[2] += 500.0
    assert stitch.link_seam(a, b, "E") == 0


def test_finish_flags_links_water_and_road():
    a = strip(0, 0, [0, 2048, 4096])
    b = mirrored(strip(0, 0, [0, 2048, 4096]), 1)
    a.area[0], a.area[1] = stitch.WATER, stitch.ROAD
    stitch.link_seam(a, b, "E")
    g = stitch.Grid(-130, -130, 262)
    nv, mi, st = stitch.finish(a, g, 0x800)
    n = nvnm.decode(nv)
    assert n.tris["flags"][0] & nvnm.WATER and n.tris["flags"][1] & nvnm.PREFERRED
    linked = [(t, k) for t in range(len(n.tris)) for k in range(3) if n.tris["flags"][t] & nvnm.EDGE_LINK[k]]
    assert len(linked) == st["links"] == 2
    assert {int(x) & 0xFFFFFF for x in n.links["navm"]} == {g.local(1, 0)}
    assert struct.unpack_from("<I", mi)[0] == stitch.fid(g.local(0, 0))
