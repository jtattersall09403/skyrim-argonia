"""A place's Hist sap pools: one centred on every living Hist, sized to the tree, in a hollow dug to its seat on a
slope, and found missing when a Hist has none."""
import math

from tools.places.draft import sap
from tools.places.seat import Ground

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


def dig(G, e, pools):
    hollow = sap.dish(G, e + pools, BASES, set())
    dug = Ground({k: list(v) for k, v in G.cells.items()}, dict(G.water_by_cell))
    dug.apply_patches(hollow)
    return hollow, dug


def test_on_a_slope_the_pool_lies_in_a_bowl_level_at_the_rim_and_deep_in_the_middle():
    G = slope()
    e = ext()[:1]
    pools = sap.plan("p", e, BASES, G)
    assert pools[0]["seat"] == {"mode": "free"} and pools[0]["base"] == sap.POOL
    hollow, dug = dig(G, e, pools)
    assert hollow and all(-sap.PATCH_MAX <= dz < 0 for r in hollow for _, _, dz in r["verts"])
    z = pools[0]["pos"][2]
    cx, cy = sap.centre(pools[0])
    s, rz = pools[0]["scale"], pools[0]["rot"][2]
    rim = min(G.height(x, y) for x, y in sap.outline(cx, cy, s, rz))
    assert abs(z - (rim - sap.LIP)) < 0.2                            # the surface a few units under the rim
    assert all(dug.height(x, y) >= z for x, y in sap.outline(cx, cy, s, rz) if math.dist((x, y), (cx, cy)) > sap.DISH * sap.POOL_HALF * s)
    assert z - dug.height(cx, cy) > 40                               # deep in the middle: the water has depth to shade
    r = sap.DISH * sap.POOL_HALF * s                                 # deepest in the middle, shallowing to the rim
    assert dug.height(cx, cy) < dug.height(cx + r * 0.5, cy) < dug.height(cx + r * 0.9, cy) + 1
    steps = [abs(dug.vertex(gx + 1, gy) - dug.vertex(gx, gy)) for gx in range(int(cx // 128) - 6, int(cx // 128) + 6)
             for gy in (int(cy // 128),)]
    assert max(steps) < 70                                           # the bank slopes, no cliff
    again = sap.dish(G, e + [dict(p, pos=list(p["pos"])) for p in pools], BASES, set())
    assert again == hollow                                           # the same dig again changes nothing
    assert sap.dish(G, e + pools, BASES, {(0, 0)}) == []             # a cell another row holds is left alone


def test_a_hist_standing_in_water_has_its_pool_on_the_bank_and_none_when_there_is_no_bank():
    # water at 0; a dry shelf (60 high) from x = 2400 eastward; the Hist at x = 2000 stands in the water
    shelf = Ground({(0, 0): [(60.0 if 128 * (i % 33) >= 2400 else -40.0) for i in range(33 * 33)]}, {(0, 0): 0.0})
    e = ext()[:1]
    none = []
    pools = sap.plan("p", e, BASES, shelf, none)
    assert none == [] and len(pools) == 1
    cx, cy = sap.centre(pools[0])
    assert cx > 2400 and "bank" in pools[0]["why"]
    hollow, dug = dig(shelf, e, pools)
    assert pools[0]["pos"][2] > 0 + 8                                # the sap stands above our water, never on it
    assert all(dug.height(x, y) >= 0 + 8 - 0.01 for x, y in [(cx, cy)])   # the floor stays above the waterline
    sea = Ground({(0, 0): [-40.0] * (33 * 33)}, {(0, 0): 0.0})
    none = []
    assert sap.plan("p", e, BASES, sea, none) == []
    assert none == [{"on": "p.A", "why": "the tree stands in water with no dry bank at its foot"}]
    assert sap.faults(e, BASES, none) == [] and sap.faults(e, BASES) == ["p.A: a Hist without its sap pool"]


def test_a_gland_within_a_trees_pool_is_part_of_that_tree_and_a_gland_apart_has_its_own():
    bases = dict(BASES, **{"P:gland": {"edid": "HistGland03", "kind": "static", "bounds": [[-80, -80, 0], [80, 80, 200]]}})
    near = {"id": "p.G", "base": "P:gland", "kind": "static", "pos": [1700.0, 1500.0, 0.0], "rot": [0, 0, 0], "scale": 1.0}
    far = {"id": "p.H", "base": "P:gland", "kind": "static", "pos": [5000.0, 5000.0, 0.0], "rot": [0, 0, 0], "scale": 1.0}
    rows = ext() + [near, far]
    out = sap.plan("p", rows, bases)
    assert [r["id"] for r in out] == ["p.sap.A", "p.sap.B", "p.sap.H"]
    assert sap.faults(rows + out, bases) == []


def test_a_place_sets_a_pools_offset_and_scale_and_lists_a_hist_with_none():
    own = {"offset": {"A": [300.0, -100.0]}, "scale": {"p.A": 2.4}, "none": [{"on": "B", "why": "no level ground"}]}
    out = sap.plan("p", ext(), BASES, slope(), [], own)
    assert [r["id"] for r in out] == ["p.sap.A"]                      # B is listed in sap.none: no pool, no fault
    assert math.dist(sap.centre(out[0]), (2300.0, 1900.0)) < 0.1 and out[0]["scale"] == 2.4
    assert not [f for f in sap.faults(ext() + out, BASES, own["none"]) if "p.B" in f]
    assert sap.faults(ext() + out, BASES, {"B": "no level ground"}) == sap.faults(ext() + out, BASES, own["none"])
