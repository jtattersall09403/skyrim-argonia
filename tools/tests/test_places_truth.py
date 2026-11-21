"""The measuring tools against known answers: one golden place (fixtures/truth_place.json) whose every piece carries
its expected class, fault, lowest point and unit role, and whose land rows carry the expected ground heights. The
agreement tiers on the real drafts are `python -m tools.places truth` (tools/places/truth.py)."""
import json
import math
from pathlib import Path

import pytest

from tools.places import classify, truth, units, xform
from tools.places.look import geom
from tools.places.seat import Ground
from tools.places import shape

shape.REAL = False   # the golden place is measured by its own meshes and boxes, never a converted game model

FIX = json.loads((Path(__file__).parent / "fixtures" / "truth_place.json").read_text())
GROUND_TOL, LOW_TOL = 1.0, 1.0


def cells():
    k = FIX["ground"]["slope_x"]
    return {tuple(c): [k * ((c[0] * 32 + col) * 128.0) for row in range(33) for col in range(33)]
            for c in FIX["ground"]["cells"]}


def ground(rows=()):
    w = {tuple(int(v) for v in key.split(",")): h for key, h in FIX["ground"]["water"].items()}
    g = Ground({k: list(v) for k, v in cells().items()}, w, None)
    g.apply_patches(list(rows))
    return g


def pieces():
    out = []
    for r in FIX["refs"]:
        b = FIX["bases"][r["base"]]
        out.append({"id": r["id"], "base": r["base"], "kind": b["kind"], "edid": b["edid"], "model": b["model"],
                    "resolved": True, "m": xform.matrix(r["pos"], r.get("rot") or [0, 0, 0], r.get("scale", 1)),
                    "lo": b["bounds"][0], "hi": b["bounds"][1], "door": None,
                    "row": {"id": r["id"], "pos": r["pos"], "rot": r.get("rot") or [0, 0, 0], "scale": 1}})
    return out


EXPECT = {r["id"]: r["expect"] for r in FIX["refs"]}


# ---- ground ----
@pytest.mark.parametrize("pt", FIX["land_expect"], ids=lambda p: p["why"])
def test_the_ground_reader_and_the_reference_give_the_known_height(pt):
    g, ref = ground(FIX["land"]), truth.Reference(cells(), FIX["land"])
    assert abs(g.height(pt["x"], pt["y"]) - pt["h"]) <= GROUND_TOL
    assert abs(ref.height(pt["x"], pt["y"]) - pt["h"]) <= GROUND_TOL


def test_a_cells_rows_add_and_two_cells_copies_that_disagree_are_a_clash():
    g = ground(FIX["land"])
    assert g.clashes == []
    clash = FIX["land"] + [{"cell": [1, 0], "verts": [[20, 0, -8.0]]}]   # the edge vertex's other copy, another dz
    g2, ref = ground(clash), truth.Reference(cells(), clash)
    assert len(g2.clashes) == 1 and len(ref.clashes) == 1
    assert abs(g2.height(4096, 2560) - 393.6) <= GROUND_TOL   # the first cell's copy is kept, as the build keeps it


def test_an_edge_vertex_in_one_cell_reads_alike_from_both_and_is_named_one_sided():
    g, ref = ground(FIX["land"]), truth.Reference(cells(), FIX["land"])
    assert [v for v, _, _ in ref.one_sided] == [(32, 20)]
    for x in (4095.0, 4096.0, 4097.0):
        assert abs(g.height(x, 2560) - ref.height(x, 2560)) <= GROUND_TOL
    page = truth.PageGround(cells(), FIX["land"])
    assert abs(page.height(4096, 2560) - 409.6) <= GROUND_TOL   # the page's per-cell copy: why the row is flagged


def test_the_reference_and_the_reader_agree_over_a_grid():
    g, ref = ground(FIX["land"]), truth.Reference(cells(), FIX["land"])
    for x in range(10, 8180, 97):
        for y in range(10, 4090, 89):
            assert abs(g.height(x, y) - ref.height(x, y)) <= GROUND_TOL, (x, y)


# ---- classes ----
@pytest.mark.parametrize("rid", list(EXPECT))
def test_every_piece_has_its_known_class(rid):
    p = next(q for q in pieces() if q["id"] == rid)
    cls, fallback = classify.classify(p)
    assert cls == EXPECT[rid]["class"] and not fallback
    if "solid" in EXPECT[rid]:
        assert geom.solid(p) is EXPECT[rid]["solid"]


# ---- faults and lowest points ----
@pytest.fixture(scope="module")
def faults():
    out = {}
    for f in geom.faults(pieces(), ground(FIX["land"])):
        out.setdefault(f["id"], set()).add(f["fault"])
    return out


@pytest.mark.parametrize("rid", [r for r, e in EXPECT.items() if "fault" in e])
def test_every_piece_has_its_known_fault(rid, faults):
    want = EXPECT[rid]["fault"]
    got = faults.get(rid, set())
    assert (want in got) if want else not got, (rid, got)


@pytest.mark.parametrize("rid", [r for r, e in EXPECT.items() if "low_over" in e])
def test_the_probe_gives_the_known_lowest_point(rid):
    ps = pieces()
    p = next(q for q in ps if q["id"] == rid)
    got = geom.probe_piece(p, ground(FIX["land"]), ps)["lowest_over_ground"]
    assert abs(got - EXPECT[rid]["low_over"]) <= LOW_TOL, (rid, got)


def test_an_upside_down_piece_is_measured_by_its_turned_box():
    p = next(q for q in pieces() if q["id"] == "f.mound")
    lo, hi = geom.aabb(p)
    assert abs(lo[2] - 215) <= 1 and abs(hi[2] - 315) <= 1


# ---- units ----
@pytest.fixture(scope="module")
def roles():
    out = {}
    for u in units.derive(pieces(), ground(FIX["land"])):
        for r, ids in u["pieces"].items():
            for i in ids:
                out[i] = r
    return out


@pytest.mark.parametrize("rid", [r for r, e in EXPECT.items() if {"role", "not_role", "role_ground"} & set(e)])
def test_units_give_every_piece_its_known_role(rid, roles):
    e = EXPECT[rid]
    if "role" in e:
        assert roles.get(rid) == e["role"], (rid, roles.get(rid))
    for bad in e.get("not_role", []):
        assert roles.get(rid) != bad, rid
    if e.get("role_ground"):
        p = next(q for q in pieces() if q["id"] == rid)
        assert units.ground_piece(p)


def test_the_house_is_one_unit():
    us = [u for u in units.derive(pieces(), ground(FIX["land"])) if u["kind"] == "house"]
    assert len(us) == 1 and set(us[0]["pieces"]["posts"]) == {"f.post1", "f.post2"}
    assert math.isclose(len(us[0]["pieces"]["deck"]), 1)
