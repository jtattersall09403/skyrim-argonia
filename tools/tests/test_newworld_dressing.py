"""The dressing catalogue rules and its ids, on small tables."""
from tools.newworld.dressing import place as dp


def facts(**over):
    f = {"sig": "STAT", "lod": False, "half": 40, "mesh": "m.nif", "assets_ok": True}
    f.update(over)
    return f


ADJ = {"a": {"b"}, "b": {"a"}}


def test_catalogue_rules():
    ks = {"k1": {"regions": ["a"], "bases": ["P:x"]}, "k2": {"regions": ["a"], "bases": ["P:y"]},
          "k3": {"regions": ["b"], "bases": ["P:z"]}, "k4": {"regions": ["b"], "bases": ["P:w"]}}
    good = {b: facts() for b in ("P:x", "P:y", "P:z", "P:w")}
    assert dp.check_kinds(ks, good, ADJ, ["a", "b"]) == []
    bad = dict(good, **{"P:x": facts(lod=True), "P:y": facts(half=900), "P:z": facts(assets_ok=False)})
    f = dp.check_kinds(ks, bad, ADJ, ["a", "b"])
    assert any("distant LOD" in x for x in f) and any("half-extent" in x for x in f) and any("missing assets" in x for x in f)


def test_shared_with_neighbour_does_not_count():
    ks = {"k1": {"regions": ["a", "b"], "bases": ["P:x"]}, "k2": {"regions": ["a"], "bases": ["P:x"]}}
    f = dp.check_kinds(ks, {"P:x": facts()}, ADJ, ["a"])
    assert f == ["a: 1 signature kinds no neighbour has (want 2)"]


def test_ids_stable_and_in_range():
    g1, g2 = set(), set()
    a = [dp.fid_of(f"1,2/k/{i}", g1) for i in range(50)]
    b = [dp.fid_of(f"1,2/k/{i}", g2) for i in range(50)]
    assert a == b and len(set(a)) == 50 and all(dp.DRESS_FIRST <= x <= dp.DRESS_LAST for x in a)
