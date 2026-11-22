"""The carried walking mesh's rules on tiny synthetic meshes (tools/places/carrynav.py): cut on our cell lines with
shared border vertices, joined to the generated mesh round it with shared vertices, no sliver, no T-junction."""
from collections import defaultdict

import numpy as np

from tools.places import carrynav as cn


def grid(x0, y0, x1, y1, s, z=0.0):
    out = []
    for i in np.arange(x0, x1, s):
        for j in np.arange(y0, y1, s):
            a, b, c, d = (i, j, z), (i + s, j, z), (i + s, j + s, z), (i, j + s, z)
            out += [[a, b, c], [a, c, d]]
    return out


def gen_cells(cells, s=256.0, z=3.0):
    return {c: [(t, 0) for t in grid(c[0] * 4096, c[1] * 4096, c[0] * 4096 + 4096, c[1] * 4096 + 4096, s, z)] for c in cells}


def components(cell):
    par = list(range(len(cell["tris"])))

    def root(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x
    for i, e in enumerate(cell["edges"]):
        for j in e:
            if j >= 0:
                par[root(i)] = root(j)
    return len({root(i) for i in range(len(par))})


def sound(cell):
    st = cell["stats"]
    assert st["nonmanifold_edges"] == 0, st
    assert cn.t_junctions(cell) == 0
    assert st["min_area"] >= cn.MIN_AREA


def test_carried_disk_is_joined_to_the_generated_ring_with_shared_vertices():
    car = [(t, cn.PREFERRED | cn.DOOR, 0) for t in grid(100, 100, 1500, 1500, 97.3, 0.0)]
    out = cn.build_cells(car, gen_cells([(0, 0)]), cn.Region(cn.disk((800, 800), 500, 16)))
    cell = out[(0, 0)]
    sound(cell)
    assert components(cell) == 1                        # one mesh: the carried disk and the generated ring are joined
    assert cell["stats"]["open_edges"] == 64            # only the cell's own border (16 generated edges a side)
    tags = set(cell["tags"])
    assert tags == {0, -1}
    car_flags = {f for f, g in zip(cell["flags"], cell["tags"]) if g == 0}
    assert car_flags == {cn.PREFERRED}                  # the source's preferred kept, its door bit cleared


def test_a_real_footprint_polygon_has_no_sliver_or_overlap():
    car = [(t, 0, 0) for t in grid(-2000, -2000, 2000, 2000, 131.7, 0.0)]
    region = cn.Region(cn.disk((0, 0), 1800, 24), [cn.grow([(100, 100), (420, 100), (420, 380), (100, 380)])])
    out = cn.build_cells(car, gen_cells([(-1, -1), (-1, 0), (0, -1), (0, 0)]), region)
    for c, cell in out.items():
        # edges of a real footprint's length (470) over a skew grid: a rare near-collinear spot may keep one fault
        st = cell["stats"]
        assert st["nonmanifold_edges"] + cn.t_junctions(cell) <= max(2, st["tris"] // 500), (c, st)
        assert st["slivers"] <= st["tris"] // 100, (c, st)
        assert components(cell) == 1, c


def test_cells_cut_on_our_lines_share_border_vertices():
    """A carried mesh crossing a cell line (after the transform the source's cell grid no longer lines up with ours)
    is cut along OUR line; both sides hold the same border vertices, so the seam pairs edge for edge."""
    car = [(t, 0, 0) for t in grid(-700, -500, 700, 500, 113.0, 10.0)]
    out = cn.build_cells(car, gen_cells([(-1, -1), (-1, 0), (0, -1), (0, 0)]), cn.Region(cn.disk((0, 0), 450, 24)))
    def border(c, ax, v):
        cell = out[c]
        V = cell["verts"]
        return sorted(round(float(p[1 - ax]), 2) for p in V if abs(p[ax] - v) < 0.01 and -1000 < p[1 - ax] < 1000)
    assert border((0, 0), 0, 0.0) == border((-1, 0), 0, 0.0)
    assert border((0, 0), 1, 0.0) == border((0, -1), 1, 0.0)
    for cell in out.values():
        sound(cell)


def test_zone_is_generated_and_joined():
    car = [(t, 0, 0) for t in grid(0, 0, 2000, 2000, 100.0, 0.0)]
    zone = cn.grow([(800, 800), (1100, 800), (1100, 1000), (800, 1000)])
    out = cn.build_cells(car, gen_cells([(0, 0)]), cn.Region(cn.disk((1000, 1000), 900, 32), [zone]))
    cell = out[(0, 0)]
    sound(cell)
    assert components(cell) == 1
    V = np.asarray(cell["verts"])
    mid = [V[t].mean(axis=0) for t in cell["tris"]]
    inside = [g for m, g in zip(mid, cell["tags"]) if 850 < m[0] < 1050 and 850 < m[1] < 950]
    assert inside and set(inside) == {-1}               # inside the zone only the generator's triangles


def test_water_follows_our_water_and_steep_is_reported():
    t = [(0, 0, -10.0), (100, 0, -10.0), (0, 100, -10.0)]
    assert cn.water_flag(cn.WATER, t, lambda x, y: None) == 0
    assert cn.water_flag(0, t, lambda x, y: 0.0) == cn.WATER
    assert cn.slope_deg([(0, 0, 0), (100, 0, 0), (0, 100, 0)]) == 0.0
    assert cn.slope_deg([(0, 0, 0), (100, 0, 150), (0, 100, 0)]) > cn.MAX_SLOPE_DEG


def test_near_miss_cut_snaps_instead_of_making_a_sliver():
    # a vertex 3 units outside the footprint's edge: snapped onto it, not cut into a 3-unit sliver
    car = [([(0, 0, 0), (1000, 0, 0), (500, 1003, 0)], 0, 0), ([(0, 0, 0), (500, 1003, 0), (-500, 1000, 0)], 0, 0)]
    square = [(-600, -100), (1100, -100), (1100, 1000), (-600, 1000)]
    out = cn.build_cells(car, gen_cells([(0, 0), (-1, 0)]), cn.Region(square))
    for cell in out.values():
        sound(cell)
        assert cell["stats"]["slivers"] == 0 or cell["stats"]["min_area"] >= cn.MIN_AREA


def test_t_junction_is_split():
    m = cn.Mesh()
    m.add_poly([(0, 0, 0), (100, 0, 0), (100, 100, 0)], 0)
    m.add_poly([(0, 0, 0), (50, 0, 0), (50, -50, 0)], 0)
    m.add_poly([(50, 0, 0), (100, 0, 0), (50, -50, 0)], 0)
    assert cn.fix_t_junctions(m) == 1
    cell = cn.finish_cell(m)
    assert cn.t_junctions(cell) == 0 and cell["stats"]["open_edges"] == 4
    nb = defaultdict(int)
    for e in cell["edges"]:
        nb[sum(1 for x in e if x >= 0)] += 1
    assert sum(k * v for k, v in nb.items()) == 2 * 4   # four inner edges, each seen from both sides


def test_sides_a_climb_apart_in_height_still_join():
    """Recast and the source read a bank or a stair up to a climb and a detail error apart: the boundary still joins."""
    car = [(t, 0, 0) for t in grid(100, 100, 1500, 1500, 97.3, 0.0)]
    out = cn.build_cells(car, gen_cells([(0, 0)], z=40.0), cn.Region(cn.disk((800, 800), 500, 16)))
    cell = out[(0, 0)]
    sound(cell)
    assert components(cell) == 1


def test_a_hole_in_the_source_mesh_is_filled_by_the_generator_and_joined():
    """Inside the footprint, where the source left no triangle (water there, a bank on our ground), the generated mesh
    stands; a strip thinner than HOLE_THICK along the carried edge is not a hole."""
    car = [(t, 0, 0) for t in grid(0, 0, 2000, 2000, 100.0, 0.0)
           if not all(700 <= p[0] <= 1300 and 700 <= p[1] <= 1300 for p in t)]      # a 600-unit hole
    out = cn.build_cells(car, gen_cells([(0, 0)]), cn.Region(cn.disk((1000, 1000), 900, 32)))
    cell = out[(0, 0)]
    sound(cell)
    assert components(cell) == 1
    V = np.asarray(cell["verts"])
    mids = [(V[t].mean(axis=0), g) for t, g in zip(cell["tris"], cell["tags"])]
    assert {g for m, g in mids if 750 < m[0] < 1250 and 750 < m[1] < 1250} == {-1}
    assert not any(g == -1 and np.hypot(m[0] - 1000, m[1] - 1000) < 850 and not (700 < m[0] < 1300 and 700 < m[1] < 1300)
                   for m, g in mids)                   # no generated scrap over the carried mesh round the hole
    assert cn.thick([(0, 0), (100, 0), (100, 100), (0, 100)]) and not cn.thick([(0, 0), (400, 0), (400, 10), (0, 10)])


def test_ground_under_a_carried_deck_is_generated_where_the_source_had_none():
    """A walkway the source laid over its water, now over our dry ground: the deck is carried, the ground under it
    generated (a deck far over the ground covers nothing at the ground's level)."""
    ground = [(t, 0, 0) for t in grid(0, 0, 2000, 2000, 100.0, 0.0)
              if not all(700 <= p[0] <= 1300 and 700 <= p[1] <= 1300 for p in t)]
    deck = [(t, 0, 0) for t in grid(800, 800, 1200, 1200, 100.0, 300.0)]
    out = cn.build_cells(ground + deck, gen_cells([(0, 0)], z=0.0), cn.Region(cn.disk((1000, 1000), 900, 32)))
    cell = out[(0, 0)]
    V = np.asarray(cell["verts"])
    under = [g for t, g in zip(cell["tris"], cell["tags"]) if 850 < V[t].mean(axis=0)[0] < 1150
             and 850 < V[t].mean(axis=0)[1] < 1150 and V[t].mean(axis=0)[2] < 50]
    top = [g for t, g in zip(cell["tris"], cell["tags"]) if V[t].mean(axis=0)[2] > 250]
    assert under and set(under) == {-1} and top and set(top) == {0}


def test_border_with_a_cell_not_rebuilt_keeps_that_cells_vertices_only():
    """A cut through a big generated triangle leaves points on its edge; on a border with a cell that is not rebuilt
    (whose triangles the world's links name) ours are taken back, so the two sides match edge for edge."""
    car = [(t, 0, 0) for t in grid(600, 600, 3400, 3400, 120.0, 0.0)]
    gen = gen_cells([(0, 0)], s=4096.0, z=0.0)
    out = cn.build_cells(car, gen, cn.Region(cn.disk((2000, 2000), 1300, 24)),
                         neighbours={(1, 0): [(4096.0, 0.0, 0.0), (4096.0, 4096.0, 0.0)]})
    cell = out[(0, 0)]
    border = sorted(round(float(p[1])) for p in cell["verts"] if abs(p[0] - 4096) < 0.5)
    assert border == [0, 4096]
    assert cell["stats"]["nonmanifold_edges"] == 0 and components(cell) == 1


def test_a_border_stretch_covered_twice_keeps_one_triangle():
    """Two triangles sharing an edge on the cell's border, both on the cell's side (a generated sliver under a
    carried piece, or the same triangle twice), leave that border edge used twice inside the cell, so the neighbour's
    edge cannot be joined to it: the smaller goes and the border edge is open for the seam to join."""
    m = cn.Mesh()
    big = [(0.0, 100.0, 0.0), (0.0, 300.0, 0.0), (200.0, 200.0, 0.0)]
    sliver = [(0.0, 100.0, 0.0), (0.0, 300.0, 0.0), (20.0, 200.0, 0.0)]
    m.add_poly(big, 0, 0)
    m.add_poly(sliver, 0, -1)
    m.add_poly(big, 0, -1)
    assert cn.drop_folds(m, (0, 0)) == 2 and len(m.T) == 1
    cell = cn.finish_cell(m)
    assert cell["stats"]["open_edges"] == 3 and cell["stats"]["nonmanifold_edges"] == 0
