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
    still, flow = layer.type_key("lake"), layer.type_key("river-ne")
    f = {layer.type_key(t): layer.is_flow(t) for t in layer.EMIT_TYPES}
    assert judge.still_flow([(0, 0, "body.1", None, still), (0, 1, None, "reach.1", flow)], f) == []
    assert judge.still_flow([(0, 0, None, "reach.1", still)], f)
    assert judge.still_flow([(0, 0, "body.1", "reach.1", flow)], f)
    assert judge.still_flow([(0, 0, "body.1", None, "FFFFFF:X.esm")], f)


def test_cell_type_keys_on_the_database():
    ct = layer.cell_type
    assert ct("sea", None, None, None, None, None) == "sea" and ct("sea", "lagoon", "tidal", None, None, None) == "sea"
    assert ct("brackish", "marsh-deep", "lowland", None, None, None) == "brackish"
    assert ct("blackwater", "mudflat", "tidal", None, None, None) == "brackish"
    assert ct("fresh", None, None, "reach.1", 1, "sw") == "creek-sw"
    assert ct("blackwater", None, None, "reach.1", 3, "nw") == "river-nw"
    assert ct("blackwater", None, None, "reach.1", None, "se") == "river-se"  # a tidal channel, no river
    assert ct("blackwater", "marsh-deep", "lowland", None, None, None) == "marsh"
    assert ct("fresh", "backswamp", "upland", "reach.1", 2, "ne") == "marsh"  # a body's cell is still
    assert ct("blackwater", "swamp", "lowland", None, None, None) == "black"
    assert ct("blackwater", "marsh-fringe", "lowland", None, None, None) == "black"
    assert ct("fresh", "pond", "montane", None, None, None) == "cold"
    assert ct("fresh", "tarn-upland", "upland", None, None, None) == "cold"
    assert ct("fresh", "pond", "lowland", None, None, None) == "lake"
    assert ct("fresh", "lake-lowland", "lowland", None, None, None) == "lake"
    assert ct("blackwater", None, None, None, None, None) == "black" and ct("fresh", None, None, None, None, None) == "lake"
    with pytest.raises(ValueError):
        ct("fresh", "geyser", "lowland", None, None, None)
    assert layer.quadrant(1, 1) == "ne" and layer.quadrant(-1, 1) == "nw" and layer.quadrant(1, -1) == "se"
    assert layer.quadrant(-1, -1) == "sw"
    assert all(t.split("-")[0] in ("river", "creek") for t in layer.EMIT_TYPES if layer.is_flow(t))
    assert {f"{k}-{q}" for k in ("river", "creek") for q in layer.QUADS} <= set(layer.EMIT_TYPES)


def test_types_counts_and_winners():
    recs = [{"formKey": "A", "edid": "ARG_a", "template": "Tropical Skyrim.esp:DefaultWater"},
            {"formKey": "B", "edid": "ARG_b", "template": "Skyrim.esm:DefaultMarshWater"}]
    win = {"DefaultWater": ("Tropical Skyrim.esp", None), "DefaultMarshWater": ("Tropical Skyrim.esp", None)}
    counts, bad = judge.types([(0, 0, None, None, "A"), (0, 1, None, None, "A"), (0, 2, None, None, "C")], recs, win)
    assert counts == {"ARG_a": 2, "ARG_b": 0}
    assert any("(0,2)" in b for b in bad) and any("ARG_b copies Skyrim.esm" in b for b in bad) and len(bad) == 2
    assert judge.types([(0, 0, None, None, "A")], recs[:1], None) == ({"ARG_a": 1}, [])


@pytest.mark.parametrize("drop", [0.5, 2.0, 8.0, 20.0])
def test_foot_matches_the_generator(drop):
    from tools.argonia_world.terrain.generate import LIP
    import math
    assert stp.foot_vertices(drop) == int(min(Q - 1, max(1, math.ceil(drop / (0.8 * LIP)))))


def test_seat_holds_every_piece_between_its_waters_and_reseats_a_hanging_line():
    """r6 water-steps (finding 19): the line on a 5 m step at a 2 m channel's width hangs (its OBND's foot -560 u x
    scale over the lower water); place re-seats it to the drop, and the seat rule reds the unseated one, a piece over
    the upper water, one under the lower and one facing uphill."""
    pl = stp.place(STEP, 2.0)
    seat = [(p["kind"], p["pos"], p["yaw"], p["scale"]) for p in pl]
    n, bad = judge.seat([STEP], seat)
    assert bad == [] and n["pieces"] == 4 and [p["kind"] for p in pl if p["reseated"]] == ["rapids"]
    k, pos, yaw, _ = seat[0]
    unseated = su.metres_to_units(2.0) / stp.PIECES["rapids"][1]
    x, y, z = pos
    wrong = [(k, pos, yaw, unseated), (k, (x, y, z + 200), yaw, 10.0), ("ring", (x, y, LO * UPM - 200), yaw, 1.0),
             (k, pos, (yaw + 180) % 360, 10.0)]
    n, bad = judge.seat([STEP], wrong)
    assert {r: n[r] for r in ("hanging", "above upper", "below lower", "uphill")} == dict.fromkeys(
        ("hanging", "above upper", "below lower", "uphill"), 1), bad
