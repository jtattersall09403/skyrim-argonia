"""A place's Hist sap pools: one centred on every living Hist, sized to the tree, in a hollow dug to its seat on a
slope, and found missing when a Hist has none."""
import math

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
    assert by["p.sap.A"]["scale"] == sap.MIN_SCALE and by["p.sap.B"]["scale"] > 3.5
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
