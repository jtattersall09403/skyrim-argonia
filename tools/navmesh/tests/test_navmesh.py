"""L1: the navmesh codec, the record framing and the seam stitch on synthetic meshes (no game data; the vanilla
round trip is `python -m tools.navmesh vanilla`, the real-ground build `python -m tools.navmesh build`)."""
import struct

import numpy as np

from tools.argonia_world import skyrim_units as su
from tools.navmesh import checks, esm, nvnm, stitch


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


def sliver_mesh() -> stitch.Mesh:
    """A sliver (corner 2 within 0.3 units of edge 0-1 in plan, the edge open) beside a fan that shares its corner."""
    verts = [[0.0, 0.0, 0.0], [200.0, 0.0, 0.0], [12.8, 0.3, 0.0], [100.0, 100.0, 0.0]]
    tris = [[0, 1, 2], [0, 2, 3], [2, 1, 3]]
    return stitch.Mesh(0, 0, verts, tris, [63] * 3)


def test_an_open_edge_is_never_split_at_its_own_corner():
    m = sliver_mesh()
    stitch.repair_t_junctions(m)  # without the sliver pass the corner lies on the open edge 0-1
    v, tv = np.array(m.verts), np.array(m.tris)
    assert not checks.degenerate_mask(v, tv).any()


def test_slivers_are_dropped_and_the_neighbours_close_over_the_corner():
    m = sliver_mesh()
    assert stitch.drop_slivers(m) == 1 and len(m.tris) == 2
    stitch.repair_t_junctions(m)
    v, tv = np.array(m.verts), np.array(m.tris)
    assert not checks.degenerate_mask(v, tv).any()


def test_the_degenerate_check_finds_repeated_and_collinear_corners():
    v = np.array([[0, 0, 0], [10, 0, 0], [20, 0, 5], [0, 10, 0]], float)
    tv = np.array([[0, 1, 3], [0, 1, 1], [0, 1, 2]])
    assert checks.degenerate_mask(v, tv).tolist() == [False, True, True]


def test_a_split_point_on_the_line_to_the_far_corner_is_left_out():
    # edge 0-1 open; vertex 3 lies on it (within EPS), one unit from corner 0, on the line from 0 to the far corner 2
    verts = [[0.0, 0.0, 0.0], [100.0, 0.4, 0.0], [-100.0, -0.4, 0.0], [1.0, 0.004, 0.0]]
    m = stitch.Mesh(0, 0, verts, [[0, 1, 2]], [63])
    # 2, 0 and 3 are on one line: (0, 3, 2) would have zero area
    assert stitch.fan_points(m, 0, 1, 2, [(0.01, 3)]) == []


def test_door_triangle_is_found_only_when_flagged_and_named():
    from tools.navmesh import doors
    n = square_nvnm()
    n.doors = np.zeros(0, nvnm.DOOR_TRI)
    m = doors.Navm("600001:ArgoniaWorld.esm", n, [])
    arrival = (70.0, 20.0, 2.0)  # inside triangle 0
    assert doors.door_triangle_near([m], "0008B7:Argonia.esm", arrival) is None  # no entry: red
    m.doors = [(0, "0008B7:Argonia.esm")]
    assert doors.door_triangle_near([m], "0008B7:Argonia.esm", arrival) is None  # an entry without the Door flag
    n.tris["flags"][0] |= nvnm.DOOR
    assert doors.door_triangle_near([m], "0008B7:Argonia.esm", arrival)[:2] == ("600001:ArgoniaWorld.esm", 0)
    assert doors.door_triangle_near([m], "0008B7:Argonia.esm", (70.0, 20.0, 400.0)) is None  # a floor above


def test_nvmi_door_links_are_replaced_in_place():
    from tools.navmesh import doors
    plain = nvnm.nvmi(0x01600001, (1, 2, 3), [0x01600002], [], 0x01000800, (3, -4), preferred=0.25)
    want = nvnm.nvmi(0x01600001, (1, 2, 3), [0x01600002], [0x02000892, 0x020008B7], 0x01000800, (3, -4), preferred=0.25)
    assert doors.nvmi_with_doors(plain, [0x020008B7, 0x02000892]) == want
    assert doors.form_id("0008B7:Argonia.esm", doors.MASTERS, doors.SELF_FILE) == 0x020008B7
