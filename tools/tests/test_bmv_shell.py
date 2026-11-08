"""The shell census's geometry on tiny synthetic inputs: the footprint transform, inside-the-footprint and joined."""
import math

from tools.argonia_world import bmv_shell as s

FP = s.footprint((-100, -50, 0, 100, 50, 200), 2.0)    # 400 x 200 units, 400 high


def test_footprint_scales_bounds():
    assert FP == (-200, -100, 0, 200, 100, 400)


def test_local_round_trip_and_clockwise_turn():
    pos = (1000.0, 2000.0, 0.0)
    rz = math.radians(90)
    # Skyrim turns clockwise: the local +x axis points to world -y at 90 degrees
    wx, wy = s.to_world(pos, rz, 100, 0)
    assert (round(wx), round(wy)) == (1000, 1900)
    lx, ly = s.to_local(pos, rz, wx, wy)
    assert (round(lx), round(ly)) == (100, 0)


def test_reach_follows_rotation():
    pos, rz = (0.0, 0.0, 0.0), math.radians(90)
    # local (150, 0) is inside the 200-half-wide box; it lies at world (0, -150)
    assert s.reach(pos, rz, FP, 0, -150) < 1
    # world (150, 0) is local (0, 150): outside the 100-half-deep box
    assert s.reach(pos, rz, FP, 150, 0) > 1


def _grid(x0, y0, n, m, step, z=0.0, nav="N"):
    """A strip of n x m squares of two triangles each, sharing vertices."""
    out = []
    for i in range(n):
        for j in range(m):
            a, b = (x0 + i * step, y0 + j * step, z), (x0 + (i + 1) * step, y0 + j * step, z)
            c, d = (x0 + i * step, y0 + (j + 1) * step, z), (x0 + (i + 1) * step, y0 + (j + 1) * step, z)
            out += [(a, b, d, nav), (a, d, c, nav)]
    return out


def test_joined_floor_counts_inside_and_joined():
    # a 20-unit grid over x -300..300, y -40..40: crosses the footprint and runs into the ring on both ends
    tris = _grid(-300, -40, 30, 4, 20)
    m = s.measure((0.0, 0.0, 0.0), 0.0, FP, tris)
    assert m["inner_tris"] > 0
    assert m["joined_tris"] == m["inner_tris"]
    assert m["floor_levels"] == 1 and m["navmesh"] == "N" and m["ground_z"] == 0
    assert s.klass(m, False) == "A"


def test_island_inside_is_not_joined():
    inside = _grid(-60, -40, 6, 4, 20, nav="IN")          # wholly within the core
    outside = _grid(260, -40, 2, 4, 20, nav="OUT")         # in the ring, sharing no edge with it
    m = s.measure((0.0, 0.0, 0.0), 0.0, FP, inside + outside)
    assert m["inner_tris"] == 48 and m["joined_tris"] == 0
    assert s.klass(m, False) == "C"


def test_nothing_inside_is_d_and_walkway_is_x():
    m = s.measure((0.0, 0.0, 0.0), 0.0, FP, _grid(260, -40, 2, 4, 20))
    assert m["inner_tris"] == 0 and s.klass(m, False) == "D" and s.klass(m, True) == "X"


def test_kind_sorts_models():
    assert s.kind(r"Architecture\Solitude\SStyrrsHouse.nif", "SStyrrsHouse") == ("row", None)
    assert s.kind(r"Architecture\Docks\DockStrEnt01.nif", None) == ("row", "X")
    assert s.kind(r"Landscape\Trees\TreePineForest01.nif", None)[1] == "nature"
    assert s.kind(r"Architecture\Markarth\MrkDocksideBridge01.nif", None)[1] == "bridge"
    assert s.kind(r"_BYOH\Architecture\BYOHHouse\BYOHBYOHWRlonghsKBASE01.nif", None) == ("row", None)
