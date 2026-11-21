"""The owner's walking-mesh zones on tiny synthetic meshes (tools/places/walknav.py): a block zone cuts cleanly, a walk
zone meshes the gap it covers and joins what is round it, a join bridges two edges or says why not."""
import math

import numpy as np
import pytest

from tools.places import carrynav as cn
from tools.places import walknav as wn


def grid(x0, y0, x1, y1, z=0.0, n=4, f=0):
    """A flat rectangle of 2 n^2 triangles: [(tri, flags)]."""
    xs, ys = np.linspace(x0, x1, n + 1), np.linspace(y0, y1, n + 1)
    out = []
    for i in range(n):
        for j in range(n):
            a, b = (xs[i], ys[j], z), (xs[i + 1], ys[j], z)
            c, d = (xs[i + 1], ys[j + 1], z), (xs[i], ys[j + 1], z)
            out += [([a, b, c], f), ([a, c, d], f)]
    return [([list(map(float, p)) for p in t], fl) for t, fl in out]


def islands(cells: dict) -> list[int]:
    """Island sizes over finished cells: shared edges within a cell, shared border vertices across cells."""
    nodes = [(k, i) for k, c in cells.items() if c for i in range(len(c["tris"]))]
    idx = {n: i for i, n in enumerate(nodes)}
    par = list(range(len(nodes)))

    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a
    by_edge = {}
    for k, c in cells.items():
        if not c:
            continue
        for i, e in enumerate(c["edges"]):
            for j in e:
                if j >= 0:
                    par[find(idx[(k, i)])] = find(idx[(k, j)])
        for i, t in enumerate(c["tris"]):
            for q in range(3):
                p1, p2 = c["verts"][t[q]], c["verts"][t[(q + 1) % 3]]
                key = tuple(sorted([tuple(np.round(p1, 1)), tuple(np.round(p2, 1))]))
                if key in by_edge:
                    par[find(idx[(k, i)])] = find(by_edge[key])
                else:
                    by_edge[key] = idx[(k, i)]
    sizes = {}
    for n in range(len(nodes)):
        sizes[find(n)] = sizes.get(find(n), 0) + 1
    return sorted(sizes.values(), reverse=True)


def area(cell) -> float:
    V = cell["verts"]
    return sum(abs(0.5 * ((V[b][0] - V[a][0]) * (V[c][1] - V[a][1]) - (V[c][0] - V[a][0]) * (V[b][1] - V[a][1]))) for a, b, c in cell["tris"])


def centroids(cell):
    V = cell["verts"]
    return [tuple(np.mean([V[i] for i in t], axis=0)) for t in cell["tris"]]


def test_block_zone_cuts_cleanly():
    meshes = {(0, 0): grid(0, 0, 2000, 2000)}
    block = {"id": "w1", "kind": "block", "outline": [[700, 700, 0], [1300, 650, 0], [1350, 1300, 0], [650, 1250, 0]]}
    done, st = wn.apply(meshes, [block], cell_of=True)
    cell = done[(0, 0)]
    poly = [(p[0], p[1]) for p in wn.clean_outline(block["outline"])]
    hole = abs(cn.area2(poly)) / 2
    assert math.isclose(area(cell), 2000 * 2000 - hole, rel_tol=1e-4)
    hs = cn.planes(poly)
    assert not any(all(cn._side(h, c) > 1 for h in hs) for c in centroids(cell))   # nothing walkable inside
    assert cell["stats"]["slivers"] == 0 and cell["stats"]["nonmanifold_edges"] == 0
    assert cn.t_junctions(cell) == 0
    assert st["block"] == 1 and not st["refused"]


def test_concave_block_zone():
    meshes = {(0, 0): grid(0, 0, 2000, 2000)}
    L = [[400, 400, 0], [1600, 400, 0], [1600, 800, 0], [800, 800, 0], [800, 1600, 0], [400, 1600, 0]]
    done, _ = wn.apply(meshes, [{"id": "w1", "kind": "block", "outline": L}], cell_of=True)
    hole = 1200 * 400 + 400 * 800
    assert math.isclose(area(done[(0, 0)]), 2000 * 2000 - hole, rel_tol=1e-4)
    assert len(wn.convex_parts(wn.clean_outline(L))) == 2


def test_walk_zone_joins_a_gap_on_the_surface_under_it():
    # two decks with a 200 gap; the gap's ground is 30 higher on the right (the pen read it)
    meshes = {(0, 0): grid(0, 0, 1000, 1000, 100) + grid(1200, 0, 2200, 1000, 130)}
    done0, _ = wn.apply(meshes, [{"id": "x", "kind": "block", "outline": [[3000, 3000, 0], [3100, 3000, 0], [3100, 3100, 0]]}], cell_of=True)
    assert islands(done0) == [32, 32]
    walk = {"id": "w2", "kind": "walk", "outline": [[900, 400, 100], [1300, 400, 130], [1300, 600, 130], [900, 600, 100]]}
    done, st = wn.apply(meshes, [walk], cell_of=True)
    cell = done[(0, 0)]
    assert len(islands(done)) == 1
    assert cell["stats"]["nonmanifold_edges"] == 0 and cn.t_junctions(cell) == 0
    # the zone over each deck stands on the deck (the mesh that was there), in the gap at the pen's height
    zs = {tuple(np.round(v[:2])): v[2] for v in cell["verts"]}
    assert zs[(900.0, 400.0)] == pytest.approx(100) and zs[(1300.0, 600.0)] == pytest.approx(130)
    assert st["walk"] == 1 and st["added"] >= 1


def test_join_bridges_two_edges():
    meshes = {(0, 0): grid(0, 0, 1000, 1000, 0) + grid(1150, 0, 2150, 1000, 40)}
    join = {"id": "w3", "kind": "join", "points": [[1000, 500, 0], [1150, 520, 40]], "gap": 256}
    done, st = wn.apply(meshes, [join], cell_of=True)
    assert st["joined"] == 1 and not st["refused"]
    assert len(islands(done)) == 1
    assert done[(0, 0)]["stats"]["nonmanifold_edges"] == 0 and cn.t_junctions(done[(0, 0)]) == 0


@pytest.mark.parametrize("dz,gap,why", [(200, 256, "in height"), (40, 100, "apart, more than")])
def test_join_refused_says_why(dz, gap, why):
    meshes = {(0, 0): grid(0, 0, 1000, 1000, 0) + grid(1150, 0, 2150, 1000, dz)}
    join = {"id": "w4", "kind": "join", "points": [[1000, 500, 0], [1150, 500, dz]], "gap": gap}
    done, st = wn.apply(meshes, [join], cell_of=True)
    assert st["joined"] == 0 and why in st["refused"][0] and st["refused"][0].startswith("join w4:")
    assert len(islands(done)) == 2


def test_join_far_from_any_mesh():
    _, st = wn.apply({(0, 0): grid(0, 0, 1000, 1000)}, [{"id": "w5", "kind": "join", "points": [[3000, 3000, 0], [3100, 3000, 0]]}], cell_of=True)
    assert "no open edge" in st["refused"][0] or "no walking mesh" in st["refused"][0]


def test_zone_across_a_cell_line_keeps_the_seam():
    meshes = {(0, 0): grid(3096, 0, 4096, 1000), (1, 0): grid(4096, 0, 5096, 1000)}
    block = {"id": "w6", "kind": "block", "outline": [[3900, 300, 0], [4300, 300, 0], [4300, 700, 0], [3900, 700, 0]]}
    done, _ = wn.apply(meshes, [block], cell_of=True)
    # short edges a cut leaves are merged (carrynav.collapse_short): the cut edge holds within SNAP of the outline
    assert abs(area(done[(0, 0)]) + area(done[(1, 0)]) - (2 * 1000 * 1000 - 400 * 400)) <= cn.SNAP * 1600
    for c in done.values():   # nothing past its own cell line
        assert c["verts"][:, 0].min() >= 3096 - 0.5 and c["verts"][:, 0].max() <= 5096 + 0.5
    on = lambda c: sorted(round(float(v[1]), 1) for v in c["verts"] if abs(v[0] - 4096) < 0.5)   # noqa: E731
    assert on(done[(0, 0)]) == on(done[(1, 0)])
    assert len(islands(done)) == 1


def test_interior_zones_merge_the_room():
    from tools.navmesh import nvnm
    tris = grid(0, 0, 1000, 1000)
    V = np.asarray([p for t, _ in tris for p in t], np.float32)
    T = np.zeros(len(tris), nvnm.TRI)
    T["v"] = np.arange(len(V)).reshape(-1, 3)
    navs = [{"fid": 1, "space": "Room", "cell_raw": 5, "nv": nvnm.Nvnm(0, None, 5, V, T)}]
    st = wn.apply_interior(navs, [{"id": "w7", "kind": "block", "space": "Room", "outline": [[0, 0, 0], [500, 0, 0], [500, 1000, 0], [0, 1000, 0]]}])
    assert st["block"] == 1 and len(navs) == 1
    v = navs[0]["nv"].verts
    assert v[:, 0].min() >= 500 - 0.5 and navs[0]["nv"].cell == 5


def test_a_zone_holds_its_own_level():
    # a deck 300 over the ground: a block drawn on the deck cuts the deck, never the ground under it
    meshes = {(0, 0): grid(0, 0, 1000, 1000, 0) + grid(200, 200, 800, 800, 300, n=2)}
    block = {"id": "w8", "kind": "block", "outline": [[300, 300, 300], [700, 300, 300], [700, 700, 300], [300, 700, 300]]}
    done, _ = wn.apply(meshes, [block], cell_of=True)
    c = done[(0, 0)]
    V = c["verts"]

    def a(ts):
        return sum(abs(0.5 * ((V[q][0] - V[p][0]) * (V[r][1] - V[p][1]) - (V[r][0] - V[p][0]) * (V[q][1] - V[p][1]))) for p, q, r in ts)
    ground = [t for t in c["tris"] if max(V[i][2] for i in t) < 1]
    deck = [t for t in c["tris"] if min(V[i][2] for i in t) > 299]
    assert math.isclose(a(ground), 1000 * 1000, rel_tol=1e-4)
    assert math.isclose(a(deck), 600 * 600 - 400 * 400, rel_tol=1e-3)
