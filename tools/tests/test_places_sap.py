"""A place's Hist sap pools: one holding every living Hist, sized by its trunk at the ground (never its crown), off
the trunk toward open sky when decks hide it, its surface at the lowest ground of its rim in a hollow dug level all
round, and found missing when a Hist has none."""
import math

import pytest

from tools.places.draft import sap
from tools.places.seat import Ground, seat_all

BASES = {"P:hist": {"edid": "HistTree04", "kind": "static", "bounds": [[-254, -278, -24], [333, 296, 593]]},
         "P:big": {"edid": "HistTree03", "kind": "static", "bounds": [[-658, -731, -162], [734, 713, 1381]]},
         "P:dead": {"edid": "HistTree04Dead", "kind": "static", "bounds": [[-254, -278, -24], [333, 296, 593]]},
         "P:root": {"edid": "HistGland03Roots", "kind": "static", "bounds": [[-100, -100, 0], [100, 100, 50]]},
         sap.POOL: {"edid": "WaterPuddleHist", "kind": "activator", "model": "water/waterpuddle01.nif"}}


def slope():
    """One cell rising 0.08 units per unit eastward (some 5 degrees), no water."""
    return Ground({(0, 0): [0.08 * 128 * (i % 33) for i in range(33 * 33)]}, {})


def ext():
    return [{"id": "p.A", "base": "P:hist", "kind": "static", "pos": [2000.0, 2000.0, 0.0], "rot": [0, 0, 0], "scale": 1.0},
            {"id": "p.B", "base": "P:big", "kind": "static", "pos": [1500.0, 1500.0, 0.0], "rot": [0, 0, 0], "scale": 1.0},
            {"id": "p.C", "base": "P:dead", "kind": "static", "pos": [500.0, 500.0, 0.0], "rot": [0, 0, 0], "scale": 1.0},
            {"id": "p.D", "base": "P:root", "kind": "static", "pos": [900.0, 500.0, 0.0], "rot": [0, 0, 0], "scale": 1.0}]


def test_every_living_hist_has_its_pool_centred_and_sized():
    out = sap.plan("p", ext(), BASES)
    assert [r["id"] for r in out] == ["p.sap.A", "p.sap.B"]          # the dead Hist and the roots have none
    by = {r["id"]: r for r in out}
    for r, t in ((by["p.sap.A"], ext()[0]), (by["p.sap.B"], ext()[1])):
        assert math.dist(sap.centre(r), t["pos"][:2]) < 0.1
    assert by["p.sap.A"]["scale"] == sap.MIN_SCALE
    # sized by the trunk at the ground: the big Hist's crown (half-width 709) never sizes its pool
    assert by["p.sap.B"]["scale"] * sap.POOL_HALF == pytest.approx(sap.trunk_r(BASES["P:big"], 1.0) + sap.SAP_BAND, abs=2)
    assert sap.faults(ext() + out, BASES) == []


def test_a_hist_without_a_pool_and_a_pool_without_its_hist_are_faults():
    out = sap.plan("p", ext(), BASES)
    f = sap.faults(ext() + out[1:], BASES)
    assert f == ["p.A: a Hist without its sap pool"]
    f = sap.faults(ext()[1:] + out, BASES)
    assert f == ["p.A: a Hist without its sap pool", "p.sap.A: its Hist is gone"][1:]


def test_a_pool_placed_by_hand_on_the_trunk_is_kept():
    hand = dict(sap.pool_for("p", ext()[0], BASES["P:hist"]), id="p.add.X")
    out = sap.plan("p", ext() + [hand], BASES)
    assert [r["id"] for r in out] == ["p.sap.B"]


def test_on_a_slope_the_hollow_holds_the_pool_and_the_seat_stays():
    G = slope()
    e = ext()[:1]
    pools = sap.plan("p", e, BASES)
    seat_all(pools, G)
    hollow = sap.dish(G, e + pools, BASES, set())
    assert hollow and all(-sap.PATCH_MAX <= dz < 0 for r in hollow for _, _, dz in r["verts"])
    dug = Ground({k: list(v) for k, v in G.cells.items()}, {})
    dug.apply_patches(hollow)
    seat_all(pools, dug)
    z = pools[0]["pos"][2]
    cx, cy = sap.centre(pools[0])
    rad = sap.DISH * sap.POOL_HALF * pools[0]["scale"]
    inner = [dug.height(cx + rad * 0.6 * math.cos(a / 8 * math.pi), cy + rad * 0.6 * math.sin(a / 8 * math.pi)) for a in range(16)]
    assert max(inner + [dug.height(cx, cy)]) < z                     # the sap lies over its whole hollow
    assert sap.dish(G, e + pools, BASES, set()) == hollow             # the same dig again: the seat stays put
    assert sap.dish(G, e + pools, BASES, {(0, 0)}) == []              # a cell another row holds is left alone


def test_a_gland_within_a_trees_pool_is_part_of_that_tree_and_a_gland_apart_has_its_own():
    bases = dict(BASES, **{"P:gland": {"edid": "HistGland03", "kind": "static", "bounds": [[-80, -80, 0], [80, 80, 200]]}})
    near = {"id": "p.G", "base": "P:gland", "kind": "static", "pos": [1700.0, 1500.0, 0.0], "rot": [0, 0, 0], "scale": 1.0}
    far = {"id": "p.H", "base": "P:gland", "kind": "static", "pos": [5000.0, 5000.0, 0.0], "rot": [0, 0, 0], "scale": 1.0}
    rows = ext() + [near, far]
    out = sap.plan("p", rows, bases)
    assert [r["id"] for r in out] == ["p.sap.A", "p.sap.B", "p.sap.H"]
    assert sap.faults(rows + out, bases) == []


def test_a_named_trunk_sizes_the_pool_and_a_big_crown_does_not():
    bases = dict(BASES, **{"P:h1": {"edid": "HistTree01", "kind": "static", "bounds": [[-904, -902, -99], [844, 1003, 1612]]}})
    t = {"id": "p.T", "base": "P:h1", "kind": "static", "pos": [0.0, 0.0, 0.0], "rot": [0, 0, 0], "scale": 1.64}
    r = sap.plan("p", [t], bases)[0]
    assert r["scale"] * sap.POOL_HALF == pytest.approx(120 * 1.64 + sap.SAP_BAND, abs=2)   # some 400, not 2,800 across


def test_a_pool_under_a_deck_moves_toward_open_sky_with_the_trunk_kept_in_it():
    bases = dict(BASES, **{"P:deck": {"edid": "MurkmirePlatformBase03", "kind": "building", "bounds": [[-300, -300, 0], [300, 300, 400]]}})
    t = ext()[0]
    deck = {"id": "p.K", "base": "P:deck", "kind": "building", "pos": [2300.0, 2000.0, 300.0], "rot": [0, 0, 0], "scale": 1.0}
    r = sap.plan("p", [t, deck], bases)[0]
    cx, cy = sap.centre(r)
    assert cx < t["pos"][0] - 50 and sap.holds(r, t)                  # west, away from the deck east of the trunk
    assert sap.faults([t, deck, r], bases) == []
    alone = sap.plan("p", [t], bases)[0]
    assert math.dist(sap.centre(alone), t["pos"][:2]) < 0.1           # nothing over it: on the trunk
    fixed = sap.plan("p", [t, deck], bases, {"A": [0, 100]})[0]
    assert math.dist(sap.centre(fixed), (2000.0, 2100.0)) < 0.1       # the place's own offset


def test_the_surface_is_at_the_rims_lowest_ground_and_the_rim_is_dug_level():
    G = slope()
    e = ext()[:1]
    pools = sap.plan("p", e, BASES)
    seat_all(pools, G)
    z = pools[0]["pos"][2]
    cx, cy = sap.centre(pools[0])
    rad = sap.DISH * sap.POOL_HALF * pools[0]["scale"]
    rim = [G.height(cx + rad * math.cos(a / 8 * math.pi), cy + rad * math.sin(a / 8 * math.pi)) for a in range(16)]
    assert z <= min(rim) + sap.DZ + 0.5                               # never under a lip: at the rim's lowest
    banks = []
    hollow = sap.dish(G, e + pools, BASES, set(), banks)
    dug = Ground({k: list(v) for k, v in G.cells.items()}, {})
    dug.apply_patches(hollow)
    seat_all(pools, dug)
    from tools.places.seat import STEP
    for gx in range(int((cx - rad - STEP) // STEP), int((cx + rad + STEP) // STEP) + 2):
        for gy in range(int((cy - rad - STEP) // STEP), int((cy + rad + STEP) // STEP) + 2):
            d = math.dist((gx * STEP, gy * STEP), (cx, cy))
            if rad < d <= rad + STEP and not banks:
                assert dug.vertex(gx, gy) <= pools[0]["pos"][2] + sap.RIM_LIP + 0.2   # the rim level with the sap


def test_ground_falling_more_than_the_dig_limit_leaves_a_bank_and_says_so():
    steep = Ground({(0, 0): [0.6 * 128 * (i % 33) for i in range(33 * 33)]}, {})
    e = ext()[:1]
    pools = sap.plan("p", e, BASES)
    seat_all(pools, steep)
    banks = []
    hollow = sap.dish(steep, e + pools, BASES, set(), banks)
    assert banks and banks[0]["pool"] == "p.sap.A" and banks[0]["bank"] > 0
    assert all(dz >= -sap.PATCH_MAX for r in hollow for _, _, dz in r["verts"])


def test_a_pool_on_a_steep_side_goes_to_the_flat_side_of_its_trunk_so_no_bank_stands_over_the_sap():
    # flat east of x=2000, falling steeply west of it: the pool centred on the trunk would keep a bank
    h = [max(0.0, 2000.0 - 128 * (i % 33)) * 0.8 for i in range(33 * 33)]
    G = Ground({(0, 0): h}, {})
    e = ext()[:1]
    pool = sap.plan("p", e, BASES, None, G)[0]
    cx, cy = sap.centre(pool)
    assert cx > 2000.0                                           # moved toward the flat side
    assert sap.holds(pool, e[0])                                 # the trunk kept in its sap
    rad = sap.SEAT_REACH * sap.reach(BASES["P:hist"], 1.0)
    assert sap.relief(G, cx, cy, rad) <= sap.PATCH_MAX
    seat_all([pool], G)
    banks = []
    sap.dish(G, e + [pool], BASES, set(), banks)
    assert not banks
    assert sap.plan("p", e, BASES, {"A": [0, 0]}, G)[0]["pos"][:2] == sap.plan("p", e, BASES, [0, 0])[0]["pos"][:2]


def test_the_sap_never_stands_above_its_own_rim_where_a_bank_is_left():
    steep = Ground({(0, 0): [0.6 * 128 * (i % 33) for i in range(33 * 33)]}, {})
    e = ext()[:1]
    pools = sap.plan("p", e, BASES, None, steep)
    seat_all(pools, steep)
    banks, surfaces = [], {}
    steep.apply_patches(sap.dish(steep, e + pools, BASES, set(), banks, surfaces))
    sap.settle(pools, steep, surfaces)
    p = pools[0]
    cx, cy = sap.centre(p)
    rad = sap.DISH * sap.POOL_HALF * p["scale"]
    from tools.places.seat import STEP
    rim = [steep.vertex(gx, gy) for gx in range(-1, 34) for gy in range(-1, 34)
           if rad < math.dist((gx * STEP, gy * STEP), (cx, cy)) <= rad + STEP and steep.vertex(gx, gy) is not None]
    assert rim and p["pos"][2] <= min(rim) + 0.5                      # the surface no higher than the lowest rim


def test_a_steep_pool_shrinks_and_weighs_a_platform_over_it_as_a_bank():
    # rising eastward; a platform over the trunk's east side: the pool goes west, out from under it
    G = Ground({(0, 0): [0.25 * 128 * (i % 33) for i in range(33 * 33)]}, {})
    bases = dict(BASES, **{"P:deck": {"edid": "MurkmirePlatformBase03", "kind": "building", "bounds": [[-200, -400, 0], [200, 400, 400]]}})
    t = ext()[0]
    deck = {"id": "p.K", "base": "P:deck", "kind": "building", "pos": [2350.0, 2000.0, 900.0], "rot": [0, 0, 0], "scale": 1.0}
    bare = sap.plan("p", [t], bases, None, G)[0]
    under = sap.plan("p", [t, deck], bases, None, G)[0]
    assert sap.holds(under, t) and sap.centre(under)[0] < sap.centre(bare)[0] + 1e-6
    rad = sap.DISH * sap.POOL_HALF * under["scale"]
    assert sap.open_share(*sap.centre(under), rad, sap.covers([deck], bases)) > \
        sap.open_share(*sap.centre(bare), rad, sap.covers([deck], bases))
    full = sap.pool_for("p", t, bases["P:hist"])["scale"]
    assert bare["scale"] <= full                                      # shrunk where the slope leaves a bank


def test_the_dig_never_moves_another_row_seated_on_the_ground():
    G = slope()
    t = ext()[0]
    post = {"id": "p.post", "base": "P:root", "kind": "static", "pos": [2100.0, 2000.0, 0.0], "rot": [0, 0, 0],
            "scale": 1.0, "seat": {"mode": "above", "dz": 0.0}}
    pools = sap.plan("p", [t], BASES)
    seat_all(pools, G)
    from tools.places.seat import seat_z
    post["pos"][2] = seat_z(post, G)
    dug = Ground({k: list(v) for k, v in G.cells.items()}, {})
    dug.apply_patches(sap.dish(G, [t, post] + pools, BASES, set()))
    assert seat_z(post, dug) < post["pos"][2] - 1                     # the hollow reaches under it
    assert sap.hold_others([t, post] + pools, dug) == ["p.post"]
    assert seat_z(post, dug) == pytest.approx(post["pos"][2], abs=0.01)


def test_a_pool_placed_by_hand_off_the_trunk_keeps_its_place_and_size_and_is_dug_and_logged():
    bases = dict(BASES, **{"P:deck": {"edid": "MurkmirePlatformBase03", "kind": "building", "bounds": [[-300, -300, 0], [300, 300, 400]]}})
    t = ext()[0]
    deck = {"id": "p.K", "base": "P:deck", "kind": "building", "pos": [2900.0, 2000.0, 300.0], "rot": [0, 0, 0], "scale": 1.0}
    said: list = []
    r = sap.plan("p", [t, deck], bases, {"A": [900, 0]}, scales={"A": 2.3}, log=said.append)[0]
    assert math.dist(sap.centre(r), (2900.0, 2000.0)) < 0.1 and r["scale"] == 2.3   # under the deck: the hand holds
    assert not sap.holds(r, t) and sap.of_hist(r, t)                  # off the trunk, still the Hist's own pool
    assert sap.faults([t, deck, r], bases) == []
    assert said and "hand-placed" in said[0]
    G = slope()
    seat_all([r], G)
    dug = sap.dish(G, [t, r], bases, set())
    assert dug                                                         # its hollow is dug where the hand put it
    assert {tuple(d["cell"]) for d in dug} == {(0, 0)}
    # an offset alone (no scale) is still the stage's own size
    assert sap.plan("p", [t], bases, {"A": [0, 100]})[0]["scale"] == sap.MIN_SCALE


def test_a_hist_the_place_accepts_without_a_pool_gets_none_and_is_no_fault():
    none = {"A": "no open level ground at its foot"}
    out = sap.plan("p", ext(), BASES, none=none)
    assert [r["id"] for r in out] == ["p.sap.B"]
    assert sap.faults(ext() + out, BASES, none) == []
    assert sap.faults(ext() + out, BASES) == ["p.A: a Hist without its sap pool"]
