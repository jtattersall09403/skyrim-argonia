"""The step rule of the 1.15 water solve on synthetic reaches (L2)."""
from __future__ import annotations

import numpy as np
import pytest

from tools.argonia_world.water import solve as sv
from tools.argonia_world.water import steps as stp

CELL = sv.Q * sv.MPP  # metres per cell side
TOP = sv.NCELL * CELL  # south_m of the province's north edge is 0; the southern row is at TOP


def east_line(cells: float, south_m: float = TOP - 10.5 * CELL, e0: float = 0.5 * CELL):
    """A straight reach running east from the middle of cell (0, 10) for `cells` cells."""
    return [(e0, south_m), (e0 + cells * CELL, south_m)]


def test_flat_inside_a_cell_steps_only_at_edges():
    rs = sv.solve_reach(east_line(4), 10.0, 6.0)
    assert rs.dry is None
    cells = [v.cell for v in rs.visits]
    assert cells == [(0, 10), (1, 10), (2, 10), (3, 10), (4, 10)]
    assert rs.levels == sorted(rs.levels, reverse=True)  # monotone downstream
    assert len(set(rs.levels)) == len(rs.levels)  # one level per visit, one step per edge


def test_riffles_merge_and_carry_the_upper_level():
    rs = sv.solve_reach(east_line(4), 10.0, 9.2)  # 0.2 m per cell: under RIFFLE_M
    assert set(rs.levels) == {10.0} or len(set(rs.levels)) <= 2
    for a, b in zip(rs.levels, rs.levels[1:]):
        assert a == b or a - b >= sv.RIFFLE_M


def test_too_steep_inside_one_cell_is_a_dry_gully():
    rs = sv.solve_reach(east_line(2), 200.0, 100.0)  # 50 m per cell
    assert rs.dry and "inside cell" in rs.dry


def test_edge_drop_beyond_the_tallest_falls_is_dry():
    # a short reach that crosses one edge near its start: a 30 m drop inside a few metres of each cell
    p = [(CELL - 1.0, TOP - 10.5 * CELL), (CELL + 1.0, TOP - 10.5 * CELL)]
    rs = sv.solve_reach(p, 70.0, 10.0)
    assert rs.dry is not None


def test_corner_crossing_is_four_connected():
    p = [(0.5 * CELL, TOP - 10.5 * CELL), (1.5 * CELL, TOP - 11.5 * CELL)]  # diagonal south-east
    cells = [v.cell for v in sv.walk(p)[0]]
    for a, b in zip(cells, cells[1:]):
        assert abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1


def test_chain_choice_by_drop():
    assert stp.chain_for(0.5) == "rapids"
    assert stp.chain_for(1.5) == "cascade"
    assert stp.chain_for(8.0) == "falls"
    assert stp.MAX_DROP_M == pytest.approx(20.96, abs=0.01)


def test_section_is_the_vanilla_bed_and_bank():
    s = sv.section(10.0, 5.0)
    upm = sv.su.UNITS_PER_METRE
    assert s["bank_min_m"] >= 10.0
    assert 100 / upm - 1e-6 <= 10.0 - s["bed_edge_m"] <= 300 / upm + 1e-6
    assert s["bed_foot_m"] < 5.0
    assert 1 <= s["slope_vertices"] <= 28


def test_one_level_per_cell_bodies_before_rivers_lowest_river_wins():
    sea = (0, 0.0, "sea", None, None, 50.0)
    lake = (1, 12.0, "fresh", "body.l", None, 400.0)
    river_hi = (2, 15.0, "fresh", None, "reach.a", 30.0)
    river_lo = (2, 11.0, "fresh", None, "reach.b", 30.0)
    assert sv.resolve([sea, lake, river_hi])[0] == 12.0  # the lake's level, the step moves before it
    assert sv.resolve([river_hi, river_lo])[0] == 11.0  # the downstream level wins at a junction
    assert sv.resolve([sea, (1, 4.0, "fresh", "b", None, 50.0)])[0] == 0.0  # a tie goes to the lower level


def test_snap_rule():
    assert sv.body_level(0.3, "pond") == 0.0
    assert sv.body_level(2.4, "marsh-deep") == 0.0
    assert sv.body_level(3.0, "tarn-upland") == 3.0
    assert sv.body_type("marsh-deep", "lowland") == "blackwater"
    assert sv.body_type("swamp", "tidal") == "brackish"
    assert sv.body_type("marsh-fringe", "upland") == "fresh"


class FakeWorld:
    """Enough of db.World for solve(): three tables as tuples/dicts."""

    def __init__(self, bodies, reaches, points):
        self.t = {"body": bodies, "reach": reaches, "pts": points}

    def query(self, sql, *a):
        if "FROM hydrology_body" in sql:
            return self.t["body"]
        if "FROM hydrology_reach_point" in sql:
            return self.t["pts"]
        return self.t["reach"]


def test_province_two_levels_in_a_cell_rejected_and_steps_chained():
    n = sv.NCELL * sv.Q + 1
    lev = np.full((n, n), np.nan, dtype=np.float32)
    sea = np.zeros((n, n), dtype=bool)
    # a tarn at 12 m filling cell (3, 10) and part of (2, 10); a marsh at 2 m in (2, 10)
    r0 = n - 1 - 11 * sv.Q
    lev[r0 + 1:r0 + 31, 3 * sv.Q + 1:3 * sv.Q + 31] = 12.0
    lev[r0 + 1:r0 + 31, 2 * sv.Q + 28:2 * sv.Q + 31] = 12.0
    lev[r0 + 10:r0 + 13, 2 * sv.Q + 1:2 * sv.Q + 4] = 2.0
    sea[:, :sv.Q] = True  # cell column 0 is sea
    bodies = [
        {"id": "body.t", "kind": "tarn-upland", "level_m": 12.0, "altitude_band": "upland", "bbox_x0": 0,
         "bbox_y0": 0, "bbox_x1": n - 1, "bbox_y1": n - 1, "deepest_x": 0, "deepest_y": 0, "area_m2": 1.0},
        {"id": "body.m", "kind": "marsh-deep", "level_m": 2.0, "altitude_band": "lowland", "bbox_x0": 0,
         "bbox_y0": 0, "bbox_x1": n - 1, "bbox_y1": n - 1, "deepest_x": 0, "deepest_y": 0, "area_m2": 1.0},
    ]
    reaches = [{"id": "reach.r", "kind": "sloped-rapid", "level_from_m": 16.0, "level_to_m": 12.0,
                "water": "clearwater", "tidal": False, "width_m": 6.0}]
    points = [("reach.r", 5.5 * CELL, TOP - 10.5 * CELL), ("reach.r", 3.5 * CELL, TOP - 10.5 * CELL)]
    res = sv.solve(FakeWorld(bodies, reaches, points), raster=(lev, sea))
    c = {(cx - sv.CX0, cy - sv.CY0): v for (cx, cy), v in res.cells.items()}
    assert c[(3, 10)][0] == 12.0
    assert c[(2, 10)][0] == 12.0  # the marsh shares the tarn's cell: the basin's level (snap rule)
    assert res.body_outcome["body.m"].startswith("drop")
    assert res.reach_kind["reach.r"] == "water"
    keys = {(s.cx - sv.CX0, s.cy - sv.CY0, s.edge): s for s in res.steps}
    assert keys[(4, 10, "w")].chain in stp.CHAINS  # the reach's step into the tarn
    assert all(s.chain in stp.CHAINS or s.chain == "closed" for s in res.steps)
    assert all(s.upper_m > s.lower_m for s in res.steps)


def test_enclosed_cells_take_their_rings_level_as_vanilla_lakes_do():
    # a 3x3 lake at 4 m with a dry hole in the middle, a dry group on the grid edge, and a mixed ring
    lake = {(i, j): (4.0, "fresh", "body.l", None) for i in range(1, 4) for j in range(1, 4) if (i, j) != (2, 2)}
    add = sv.fill_enclosed(lake, n=6)
    assert add == {(2, 2): (4.0, "fresh", "body.l", None)}  # the hole, no edge group
    mixed = {(1, 2): (2.0, "fresh", "a", None), (3, 2): (2.0, "fresh", "a", None),
             (2, 1): (5.0, "fresh", "b", None), (2, 3): (2.0, "fresh", "a", None)}
    assert sv.fill_enclosed(mixed, n=6)[(2, 2)][0] == 2.0  # the level with most shared edges
    tie = {(1, 2): (2.0, "fresh", "a", None), (3, 2): (2.0, "fresh", "a", None),
           (2, 1): (5.0, "fresh", "b", None), (2, 3): (5.0, "fresh", "b", None)}
    assert sv.fill_enclosed(tie, n=6)[(2, 2)][0] == 2.0  # a tie to the lower level


def test_padding_ring_carries_the_level_one_cell_past_the_water():
    lake = {(2, 2): (4.0, "fresh", "body.l", None)}
    add = sv.pad_ring(lake, n=6)
    assert set(add) == {(i, j) for i in (1, 2, 3) for j in (1, 2, 3)} - {(2, 2)}
    assert all(v == (4.0, "fresh", "body.l", None) for v in add.values())
    two = {(1, 2): (2.0, "fresh", "a", None), (3, 2): (5.0, "fresh", "b", None)}
    assert sv.pad_ring(two, n=6)[(2, 2)][0] == 2.0  # the lowest neighbouring level


def test_yield_walls_moves_a_wall_taller_than_a_cell_into_dry_ground():
    from tools.argonia_world.water import solve as sv
    hi, lo = sv.WALL_STEP_M + 50, 0.5
    cells = {(0, 1): (hi, "fresh", "b.up", None), (1, 1): (hi, "fresh", "b.up", None),
             (0, 0): (lo, "fresh", "b.lo", None), (5, 5): (lo, "sea", None, None), (0, 2): (hi, "fresh", "b.up", None)}
    gone = sv.yield_walls(cells, keep={(1, 1)})
    assert gone == {(0, 1)}  # (1, 1) is a reach's; (0, 2) stands two cells off, within 2 x WALL_STEP_M
    assert (0, 0) in cells and (0, 2) in cells
    assert sv.yield_walls({(0, 1): (sv.WALL_STEP_M - 1, "fresh", None, None), (0, 0): (0.0, "sea", None, None)}) == set()


def test_a_snapped_body_never_drops_below_the_ground_its_samples_stand_on():
    assert sv.body_level(2.4, "marsh-deep", ground_min_m=-0.5) == 0.0  # its marsh reaches sea level: snapped
    assert sv.body_level(2.4, "marsh-deep", ground_min_m=0.8) == 2.4  # every sample's ground above 0: its own level
    assert sv.body_level(0.3, "pond", ground_min_m=0.1) == 0.0  # under SNAP_LO_M: the sea's


def test_padding_reaches_only_cells_whose_ground_comes_down_to_the_level():
    lake = {(2, 2): (4.0, "fresh", "body.l", None)}
    add = sv.pad_ring(lake, n=6, ground_min=lambda i, j: 40.0 if i == 1 else 4.1)
    assert set(add) == {(i, j) for i in (2, 3) for j in (1, 2, 3)} - {(2, 2)}  # the 40 m column stays dry
    two = {(1, 2): (0.0, "fresh", "a", None), (3, 2): (40.0, "fresh", "b", None)}
    assert sv.pad_ring(two, n=6, ground_min=lambda i, j: 39.9)[(2, 2)][0] == 40.0  # not 0 on a 40 m hillside
