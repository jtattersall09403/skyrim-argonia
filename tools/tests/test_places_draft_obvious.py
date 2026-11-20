"""`draft check` refuses an obviously wrong piece (tools/places/draft/obvious.py): a stand-in box or a model that does
not resolve, a piece floating (by the look tool's rules, tools/places/look/geom.py) with nothing under it, a bridge without support at both ends."""
from tools.places.draft import obvious
from tools.places.seat import Ground

BASES = {
    "house": {"bounds": [[-200, -200, 0], [200, 200, 300]], "model": "x/house.nif"},
    "deck": {"bounds": [[-300, -100, -20], [300, 100, 0]], "model": "x/dockdeck.nif"},
    "bridge": {"bounds": [[-300, -100, -20], [300, 100, 20]], "model": "x/bridge01.nif"},
    "lamp": {"bounds": [[-12, -12, -24], [12, 12, 24]], "model": "x/lamp.nif"},
    "post": {"bounds": [[-50, -50, 0], [50, 50, 700]], "model": "x/post.nif"},
    "box": {"bounds": [[0, 0, 0], [0, 0, 0]], "model": None},
}


def ref(i, x, y, z, base, kind="building", **kw):
    return {"id": i, "base": base, "kind": kind, "pos": [x, y, z], "rot": [0, 0, 0], "scale": 1.0, "seat": {"mode": "ground"}, **kw}


def flat(h=0.0, water=None):
    return Ground({(c, d): [h] * 33 * 33 for c in range(-2, 2) for d in range(-2, 2)}, {}, water)


def test_a_bare_collision_box_or_an_unresolved_model_is_refused():
    box = ref("b", 0, 0, 0, "Skyrim.esm:000021", kind="marker", primitive={"type": "Box", "bounds": [500, 500, 500]})
    gone = ref("g", 900, 0, 0, "missing", kind="static")
    bad = obvious.faults([box, gone], BASES, flat())
    assert any(b.startswith("b ") and obvious.BOX in b for b in bad)
    assert any(b.startswith("g ") and obvious.UNRESOLVED in b for b in bad)
    # a box that travels with a kept piece (a wall on its balcony) is that piece's collision, not a stand-in
    house = ref("h", 0, 0, 0, "house")
    box["seat"] = {"mode": "on", "on": "h", "dz": 0}
    assert obvious.faults([house, box], BASES, flat()) == []


def test_a_floating_piece_is_refused_unless_something_carries_it():
    lamp = ref("l", 500, 500, 300, "lamp")
    assert any(obvious.FLOATS in b for b in obvious.faults([lamp], BASES, flat()))
    # hanging from a house's eave: the house's box holds it in plan and reaches its height
    house = ref("h", 400, 500, 0, "house")
    assert obvious.faults([lamp, house], BASES, flat()) == []
    # on the ground, or on water no deeper than the tolerance, it stands
    assert obvious.faults([ref("l", 500, 500, 30, "lamp")], BASES, flat()) == []
    # a parked (disabled) piece is never seen, so never judged
    assert obvious.faults([ref("l", 500, 500, 900, "lamp", flags=["initially_disabled"])], BASES, flat()) == []


def test_a_bridge_needs_support_at_both_ends():
    water = flat(-200.0, water=0.0)
    lone = ref("br", 0, 0, 500, "bridge")
    assert any("both ends" in b for b in obvious.faults([lone], BASES, water))
    # a deck carries a bridge's end only when the deck itself stands (on its post down to the bed)
    left, lpost = ref("dl", -500, 0, 480, "deck"), ref("pl", -500, 0, -200, "post")
    one = obvious.faults([lone, left, lpost], BASES, water)
    assert any("one end" in b for b in one if b.startswith("br "))
    right, rpost = ref("dr", 500, 0, 480, "deck"), ref("pr", 500, 0, -200, "post")
    got = [b for b in obvious.faults([lone, left, lpost, right, rpost], BASES, water) if b.startswith("br ")]
    assert got == []
    # a bridge whose ends rest on the banks stands
    assert obvious.faults([ref("br", 0, 0, 20, "bridge")], BASES, flat()) == []


def test_a_lantern_on_the_worlds_own_tree_is_held_as_probe_holds_it():
    bases = {**BASES, "lantern": {"bounds": [[-12, -12, -40], [12, 12, 0]], "model": "x/lantern.nif"},
             "tree": {"bounds": [[-60, -60, 0], [60, 60, 900]], "model": "x/tree.nif", "kind": "tree"}}
    lamp = ref("l", 0, 0, 400, "lantern")
    tree = ref("t", 0, 0, 0, "tree", kind="tree", layer="world")
    assert any(obvious.FLOATS in b for b in obvious.faults([lamp], bases, flat()))
    assert obvious.faults([lamp], bases, flat(), [tree]) == []
