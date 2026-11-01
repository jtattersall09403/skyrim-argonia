"""The placement rules on synthetic ground (L2): medium masks, the strictest-entry rule, no-spawn, dens, seeds."""
import numpy as np

from tools.argonia_world.creatures import build, place as pl

FISH = ("water", pl.Medium(0.6, 60.0, 0.0, 90.0))
DRAKE = ("water", pl.Medium(3.0, 60.0, 0.0, 90.0))
CROC = ("shore", pl.Medium(-1.0, 1.2, 4.0, 30.0))
RAT = ("land", pl.Medium(-99.0, 0.0, 99.0, 35.0))


def rules(**kw):
    lists = {("x", "D2", "water"): ["fish", "drake"], ("x", "D2", "shore"): ["croc"], ("x", "D2", "land"): ["rat"]}
    r = pl.Rules(lists, {k: f"lvln.{'.'.join(k)}" for k in lists},
                 {"fish": FISH, "drake": DRAKE, "croc": CROC, "rat": RAT},
                 {"croc": "000001:A.esp", "rat": "000002:A.esp"}, {("x", "D2"): [("croc", 100.0)]}, {"D2": 3.0})
    for k, v in kw.items():
        setattr(r, k, v)
    return r


def ramp():
    """33 x 33: 5 m deep water in the west rising to 5 m of dry land in the east (level 0)."""
    return np.tile(np.linspace(-5.0, 5.0, 33), (33, 1))


def test_masks():
    h = ramp()
    d, s = -h, pl.slope_deg(h)
    assert FISH[1].mask(d, s, "water")[:, 0].all() and not FISH[1].mask(d, s, "water")[:, -1].any()
    assert RAT[1].mask(d, s, "land")[:, -1].all() and not RAT[1].mask(d, s, "land")[:, 0].any()
    sh = CROC[1].mask(d, s, "shore")
    assert sh[:, 16].all() and not sh[:, 0].any() and not sh[:, -1].any()


def test_list_takes_strictest_entry():
    m = rules().list_medium(("x", "D2", "water"))
    assert m.min_depth == 3.0  # the drake's: a list ref must suit every creature it can spawn


def test_refs_meet_their_rule_and_are_seeded():
    h = ramp()
    a = pl.plan_cell(3, 4, h, 0.0, "x", "D2", rules())
    b = pl.plan_cell(3, 4, h, 0.0, "x", "D2", rules())
    assert a == b and a
    r = rules()
    for ref in a:
        d = 0.0 - h[ref["i"], ref["j"]]
        if ref["kind"] == "spawn" and ref["medium"] == "water":
            assert d >= 3.0
        if ref["medium"] == "land":
            assert d < 0
        assert ref["zone"] == "eczn.wild.D2"
    assert any(x["kind"] == "den" for x in a)
    dens = [x for x in a if x["kind"] == "den"]
    preds = [x for x in a if x["kind"] == "predator"]
    assert len(dens) == len(preds) == 1 and preds[0]["base"] == r.first_form["croc"]
    assert np.hypot(dens[0]["i"] - preds[0]["i"], dens[0]["j"] - preds[0]["j"]) * pl.STEP_M <= pl.DEN_BESIDE_M + pl.STEP_M


def test_blocked_vertices_get_nothing():
    h = ramp()
    blocked = np.ones(h.shape, bool)
    assert pl.plan_cell(3, 4, h, 0.0, "x", "D2", rules(), blocked) == []


def test_no_list_no_spawn():
    assert [r for r in pl.plan_cell(3, 4, ramp(), 0.0, "y", "D2", rules()) if r["kind"] == "spawn"] == []


def test_wild_band_mode_and_cap():
    P = np.array([[0.0, 0.0], [10.0, 0], [20.0, 0], [30.0, 0], [40.0, 0], [1e6, 0]])
    assert build.wild_band(P, ["D5", "D2", "D2", "D3", "D5", "D1"], 0, 0) in ("D2", "D4")
    assert build.wild_band(P, ["D5"] * 6, 0, 0) == "D4"


def test_blocked_mask_radius():
    from tools.argonia_world import skyrim_units as su
    x, y = pl.vertex_xy(0, 0, np.array(16), np.array(16))
    m = build.blocked_mask(0, 0, np.array([[float(x), float(y)]]), np.array([10.0]))
    assert m[16, 16] and not m[0, 0]
    assert m.sum() < (2 * 10 / (su.VERTEX_SPACING_UNITS / su.UNITS_PER_METRE) + 1) ** 2 + 1
