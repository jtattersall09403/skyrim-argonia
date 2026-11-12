"""The creature roster test (tools/newworld/ecology/roster_check.py)."""
from tools.newworld.ecology import roster_check as R


def row(kind, cls, host="hostile", hab="bush"):
    return {"kind": kind, "size_class": cls, "hostility": host, "habitat": hab}


BIND = {"kinds": {}, "critter_kinds": {"fly": {"critter": "x"}}}


def full(prefix):
    rows = [row(f"{prefix}i1", "insect", "benign"), row("fly", "insect"),
            row(f"{prefix}s1", "small", "benign"), row(f"{prefix}s2", "small"), row(f"{prefix}s3", "small"),
            row(f"{prefix}g1", "game", "benign"), row(f"{prefix}g2", "game", "defensive"),
            row(f"{prefix}p1", "predator"), row(f"{prefix}p2", "predator"), row(f"{prefix}p3", "predator"),
            row(f"{prefix}x1", "giant", hab="water-fresh")]
    for r in rows:
        if r["kind"] != "fly":
            BIND["kinds"][r["kind"]] = {"records": ["a:b"], "why": "true"}
    return {"creatures": rows}


def test_a_full_region_passes_and_floors_fail():
    regions = {"a": full("a"), "b": full("b")}
    fails, stats = R.check(regions, set(), BIND, {"a": {"b"}, "b": {"a"}}, {"a": {"water-fresh"}})
    assert [f for f in fails if not f.startswith("province")] == []
    regions["a"]["creatures"] = [c for c in regions["a"]["creatures"] if c["kind"] != "ag1"]
    fails, _ = R.check(regions, set(), BIND, {}, {})
    assert "a: a game 1 < 2" in fails and "a: b game has no benign kind" in fails


def test_nearest_fit_dropped_and_water_fail():
    bind = {"kinds": {"n": {"records": ["a:b"], "why": "nearest: x"}, "d": {"dropped": "none"}}}
    assert R.true_model("n", bind) == "nearest fit"
    assert R.true_model("d", bind) == "dropped"
    assert R.true_model("u", bind) == "unbound"
    regions = {"a": full("a")}
    fails, _ = R.check(regions, set(), BIND, {}, {"a": {"water-salt"}})
    assert "a: d no swimmer of water-salt" in fails


def test_signatures_overlap_and_province():
    regions = {"a": full("a"), "b": full("a")}
    fails, stats = R.check(regions, set(), BIND, {"a": {"b"}, "b": {"a"}}, {})
    assert "a: c 0 kinds no neighbour has < 4" in fails
    assert "a/b: c overlap 1.00 > 0.5" in fails
    assert stats["actor_kinds"] == 10 and any(f.startswith("province: f") for f in fails)


def test_neighbours_and_water_kinds():
    cells = {"0,0": "a", "1,0": "a", "2,0": "b", "0,1": "a", "1,1": "b", "2,1": "b", "0,2": "a", "1,2": "b"}
    assert R.neighbours(cells, border_min=3) == {"a": {"b"}, "b": {"a"}}
    w = R.water_kinds([{"region_id": "a", "water_kind_id": "estuary", "area_m2": 30000.0},
                       {"region_id": "a", "water_kind_id": "pond", "area_m2": 100.0}])
    assert w == {"a": {"water-brackish"}}
