"""L1/L2 on small fixtures: the route geometry helpers and the road paint."""
import numpy as np

from tools.argonia_world.routes import build as B
from tools.argonia_world.routes import paint as P


def test_simplify_keeps_corners_drops_collinear():
    pts = [(0, 0), (1, 0.01), (2, 0), (2, 2)]
    assert B.simplify(pts, 0.1) == [(0, 0), (2, 0), (2, 2)]


def test_sub_polyline_cuts_at_chainages():
    pts = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0)]
    assert B.sub_polyline(pts, 5.0, 15.0) == [(5.0, 0.0), (10.0, 0.0), (10.0, 5.0)]
    assert B.length_2d(B.sub_polyline(pts, 0.0, 20.0)) == 20.0


def test_components_largest_first():
    edges = [{"from_node_id": "a", "to_node_id": "b"}, {"from_node_id": "c", "to_node_id": "d"},
             {"from_node_id": "d", "to_node_id": "e"}]
    assert B.components(["a", "b", "c", "d", "e", "f"], edges) == [{"c", "d", "e"}, {"a", "b"}, {"f"}]


class _Ground:
    def length_3d(self, pts):
        return B.length_2d(pts)


def test_join_splits_the_leg_and_adds_a_spur():
    nodes = {k: {"id": k, "x_m": x, "y_m": y} for k, x, y in (("place.a", 0, 0), ("place.b", 100, 0), ("place.c", 50, 20))}
    edges = [{"id": "edge.r", "route_id": "route.road.r", "from_node_id": "place.a", "to_node_id": "place.b", "mode": "road",
              "from_chain_m": 0.0, "to_chain_m": 100.0, "length_m": 100.0, "_pts": [(0.0, 0.0), (100.0, 0.0)]}]
    done = B.join(nodes, edges, _Ground())
    assert len(done) == 1 and len(B.components(nodes, edges)) == 1
    j = next(n for n in nodes if n.startswith("junction."))
    assert (nodes[j]["x_m"], nodes[j]["y_m"]) == (50.0, 0.0)
    assert sorted(e["length_m"] for e in edges) == [20.0, 50.0, 50.0]


def test_paint_lays_the_road_within_half_its_width_and_spares_water():
    # one road along grid row 10 from col 2 to col 12, 2 samples half-width; a road beats a track
    seg = np.array([[[10.0, 2.0], [10.0, 12.0]]])
    segs = [(P.TRACK, 4.0, seg), (P.ROAD, 2.0, seg)]
    cls = np.zeros((20, 20), dtype=np.int16)
    cls[10, 5] = 35  # sea floor
    P.override_classes(cls, 0, 0, frozenset({35}), segs=segs)
    assert cls[10, 7] == P.ROAD and cls[13, 7] == P.TRACK and cls[16, 7] == 0
    assert cls[10, 5] == 35 and cls[10, 17] == 0
    # a window offset into the grid sees the same paint
    win = np.zeros((6, 6), dtype=np.int16)
    P.override_classes(win, 8, 4, segs=segs)
    assert win[2, 0] == P.ROAD
