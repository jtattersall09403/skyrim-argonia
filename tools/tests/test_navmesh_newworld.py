"""The new world's navmesh build end to end on synthetic ground (no game data; needs the .NET SDK, else skipped):
skipped (margin) cells get no NAVM, deep water none, shallow water is flagged water on the bed, a placed obstacle cuts
a hole, seams link with no mismatch, settlement paths run, and the per-cell checkpoint reuses every cell on a rerun
and rebuilds only a changed cell's ring."""
import gzip
import json

import numpy as np
import pytest

from tools.navmesh import __main__ as nav
from tools.navmesh import nvnm, province, stitch, world
from tools.newworld.world import units as nwu

CX0, CY_TOP, N = 10, -14, 7  # a 7 x 7 cell grid; the build box is the inner 5 x 5


def land(tmp_path):
    w = h = N * 32 + 1
    g = nwu.Grid("test", w, h, CX0 * 4096.0, (CY_TOP + 1) * 4096.0, 0.0)
    return world.Land(g, "test", "k", tmp_path)


def ground():
    n = N * 32 + 1
    r, c = np.mgrid[0:n, 0:n].astype(np.float32)
    h = 200 + 3 * np.sin(c / 9) * 40 + 2 * np.cos(r / 7) * 40  # gentle hills
    h = np.minimum(h, -300 + (c - 66) * 20)  # a shore shelving gently into a shallow sea on the west (wading depth)
    h[:, :66] = -3000  # deep water beyond it (the whole of cell column 11): no navmesh
    return h.astype(np.float32)


def box_tris(x0, y0, x1, y1, z0, z1):
    p = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    t = []
    for i in range(4):
        (ax, ay), (bx, by) = p[i], p[(i + 1) % 4]
        t += [[(ax, ay, z0), (bx, by, z0), (bx, by, z1)], [(ax, ay, z0), (bx, by, z1), (ax, ay, z1)]]
    t += [[(x0, y0, z1), (x1, y0, z1), (x1, y1, z1)], [(x0, y0, z1), (x1, y1, z1), (x0, y1, z1)]]
    return np.array(t, np.float64)


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("nav")
    try:
        nav.build_tool()
    except Exception as e:  # no SDK here
        pytest.skip(f"no .NET SDK: {e}")
    ld = land(tmp)
    box = (CX0 + 1, CY_TOP - N + 2, CX0 + N - 2, CY_TOP - 1)
    cells = {(x, y) for x in range(box[0], box[2] + 1) for y in range(box[1], box[3] + 1)} - {(box[2], box[3])}  # one margin cell
    # a tall obstacle (a rock) in the middle of cell (13, -16): 600 x 600 units, 800 high
    ox, oy = 13 * 4096 + 1700, -16 * 4096 + 1700
    obj = box_tris(ox, oy, ox + 600, oy + 600, -100, 1200)
    road = [[(11 * 4096 + 2000, -18 * 4096 + 100, False), (15 * 4096 + 2000, -15 * 4096 + 100, False)]]
    places = [{"id": "a", "name": "A", "kind": "town", "x": 12 * 4096 + 500, "y": -17 * 4096 + 500},
              {"id": "b", "name": "B", "kind": "town", "x": 15 * 4096 + 3000, "y": -16 * 4096 + 3000}]
    out = tmp / "out"
    old = world.settlements
    world.settlements = lambda: places
    try:
        first = nav.build(out, box, run_check=True, objects=obj, cells=cells, land=ld, heights=ground(), polylines=road)
        again = nav.build(out, box, run_check=False, objects=obj, cells=cells, land=ld, heights=ground(), polylines=road)
    finally:
        world.settlements = old
    return out, box, cells, first, again, (ld, obj, road)


def navms(out):
    return {(x, y): n for x, y, fk, n in stitch.read_navm(out)}


def test_cells_margin_and_deep_water(built):
    out, box, cells, first, *_ = built
    got = navms(out)
    assert (box[2], box[3]) not in got  # the margin cell
    assert all((CX0 + 1, y) not in got for y in range(box[1], box[3] + 1))  # the deep-water column
    assert first["check"]["province"]["coverage"]["land_cells_without_navm"] == 0


def test_shallow_water_is_flagged_on_the_bed(built):
    out, *_ = built
    wet = [(n, t) for n in navms(out).values() for t in range(len(n.tris)) if n.tris["flags"][t] & nvnm.WATER]
    assert wet
    z = np.array([n.verts[n.tris["v"][t].astype(int)][:, 2].mean() for n, t in wet])
    assert z.max() < 0 and z.min() < -200  # on the bed below the surface (0), as vanilla's water triangles


def test_obstacle_cuts_a_hole(built):
    out, *_ = built
    n = navms(out)[(13, -16)]
    p = np.array([[13 * 4096 + 2000.0, -16 * 4096 + 2000.0]])
    from tools.navmesh import checks
    v, tv = n.verts.astype(np.float64), n.tris["v"].astype(int)
    inside = checks.covered(p, v, tv)[0]
    on_top = (v[tv][:, :, 2].mean(axis=1) > 1000).any()
    assert not inside or on_top  # either cut out or only its walkable top is meshed


def test_checks_green_seams_and_paths(built):
    out, box, cells, first, *_ = built
    ck = first["check"]
    assert ck["green"], {k: ck[k] for k in ("heights", "degenerate", "links", "navi")}
    p = ck["province"]
    assert p["seams"]["mismatched"] == 0 and p["seams"]["unmatched_segments"] == 0 and p["seams"]["linked_pairs"] > 0
    assert p["paths"]["pairs"] == 1 and p["paths"]["ok"] == 1
    assert ck["road"]["share"] > 0.95


def test_rerun_reuses_every_cell_and_a_change_rebuilds_its_ring(built, tmp_path):
    out, box, cells, first, again, (ld, obj, road) = built
    assert again["totals"]["built"] == 0 and again["sha256"] == first["sha256"]
    h = ground()
    c = (13 - CX0) * 32 + 16
    r = (CY_TOP - (-17)) * 32 + 16
    h[r - 2:r + 3, c - 2:c + 3] += 400
    before = {k: ln for k, ln in lines(out).items()}
    edited = nav.build(out, box, run_check=False, objects=obj, cells=cells, land=ld, heights=h, polylines=road)
    ring = {(13 + dx, -17 + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)} & set(before)
    assert edited["totals"]["built"] == len(ring)
    after = lines(out)
    assert {k for k in after if after[k] != before.get(k)} <= ring


def lines(out):
    d = {}
    for p in (out / "navm").glob("cy*.jsonl.gz"):
        for ln in gzip.open(p, "rt"):
            j = json.loads(ln)
            d[(j["x"], j["y"])] = ln
    return d


def test_pairs_take_nearest_unused():
    ps = [{"id": i, "kind": "city", "x": x, "y": 0} for i, x in (("a", 0), ("b", 10), ("c", 100), ("d", 105))]
    assert [(p["id"], q["id"]) for p, q in province.pairs(ps)] == [("a", "b"), ("c", "d")]
