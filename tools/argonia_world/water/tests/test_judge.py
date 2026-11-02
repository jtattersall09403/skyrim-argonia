"""L2: the water check's three placement rules (judge.py) on synthetic cells: a step laid by `steps.place` on the
ground the terrain grades passes; round 3's placement (the skirt at the upper water facing down, the foot pieces on
the edge, no rapids line over a falls) fails; a sheet ending over low ground fails; a river cell copying the still
water fails."""
import numpy as np
import pytest

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.water import judge, layer
from tools.argonia_world.water import steps as stp
from tools.argonia_world.water.solve import Step

UPM = su.UNITS_PER_METRE
UP, LO = 10.0, 5.0  # metres: a falls step from (-62,-61) south into (-62,-62)
STEP = Step(-62, -61, "s", UP, LO, 10, 20, "falls")
LEVELS = {(-62, -61): UP, (-62, -62): LO}


def ground():
    g = np.full((su.PROVINCE_SAMPLES, 70), 30.0, np.float32)  # banks well above both waters
    n = g.shape[0] - 1
    edge_r = n - Q * 1  # the s edge of cell row 1 from the south
    k = stp.foot_vertices(UP - LO)
    for c in range(STEP.cross_lo, STEP.cross_hi + 1):
        for kk in range(k + 1):  # generate.py's graded band: edge bed down to the foot bed
            g[edge_r + kk, c] = (UP - stp.STEP_BED_M) + ((LO - stp.FOOT_BED_M) - (UP - stp.STEP_BED_M)) * kk / k
        g[edge_r - Q + 1:edge_r, c] = UP - 1.0  # the upper cell's channel
        g[edge_r + k + 1:, c] = LO - 1.0  # the lower cell's channel
    return g


Q = su.QUADS_PER_CELL


def refs_of(pl):
    return [(p["kind"], p["pos"], p["yaw"]) for p in pl]


def test_place_passes_on_the_graded_ground():
    assert judge.pieces([STEP], LEVELS, refs_of(stp.place(STEP, 10.0)), ground()) == []


def test_round_3_placement_fails():
    # round 3: tall body and skirt at the upper water on the edge, yawed down; mist on the edge at the lower water
    x, y = stp.edge_point(STEP)
    down = stp.YAW["s"]
    r3 = [(None, (x, y, UP * UPM), down), ("skirt", (x, y, UP * UPM), down), ("mist", (x, y, LO * UPM), down)]
    bad = judge.pieces([STEP], LEVELS, r3, ground())
    assert any("does not take" in b for b in bad)
    assert any("skirt" in b and "faces" in b for b in bad)
    assert any("skirt" in b and "off its water" in b for b in bad)
    assert any("mist" in b and "off its place" in b for b in bad)
    assert any("no rapids line" in b for b in bad)


def test_uphill_facing_fails():
    pl = stp.place(STEP, 10.0)
    for p in pl:
        if p["kind"] == "rapids":
            p["yaw"] = (p["yaw"] + 180) % 360
    assert any("rapids" in b and "faces" in b for b in judge.pieces([STEP], LEVELS, refs_of(pl), ground()))


def test_step_needs_two_levels():
    flat = {(-62, -61): UP, (-62, -62): UP}
    assert any("levels differ" in b for b in judge.pieces([STEP], flat, refs_of(stp.place(STEP, 10.0)), ground()))


def test_hovering_sheet_at_a_bank():
    g = ground()
    inside = lambda x, y: x >= -62 and y >= -62  # noqa: E731
    assert judge.hovering(LEVELS, [STEP], g, inside) == []
    n = g.shape[0] - 1
    g[n - 2 * Q, 25] = UP - 2.0  # the upper cell's north edge (a dry neighbour) dips 2 m under its level
    assert any("(-62,-61) n" in b for b in judge.hovering(LEVELS, [STEP], g, inside))


def test_still_and_flow():
    still, flow = layer.type_key("fresh"), layer.type_key("fresh" + layer.FLOW)
    t = {r["formKey"]: r["template"] for r in layer.records()}
    assert judge.still_flow([(0, 0, "body.1", None, still), (0, 1, None, "reach.1", flow)], t) == []
    assert judge.still_flow([(0, 0, None, "reach.1", still)], t)
    assert judge.still_flow([(0, 0, "body.1", "reach.1", flow)], t)
    assert layer.cell_type("fresh", None, "reach.1") == "fresh-flow"
    assert layer.cell_type("sea", None, "reach.1") == "sea"


@pytest.mark.parametrize("drop", [0.5, 2.0, 8.0, 20.0])
def test_foot_matches_the_generator(drop):
    from tools.argonia_world.terrain.generate import LIP
    import math
    assert stp.foot_vertices(drop) == int(min(Q - 1, max(1, math.ceil(drop / (0.8 * LIP)))))
