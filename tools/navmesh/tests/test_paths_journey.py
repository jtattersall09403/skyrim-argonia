"""The navmesh-paths journey generator: spread anchors, partners inside the loaded grid, one nav step per pair."""
import yaml

from tools.navmesh import paths_journey as pj


def test_spread_and_pairs_and_render():
    pts = [(x * 1000.0, y * 1000.0, 0.0, "s") for x in range(10) for y in range(10)]
    a = pj.spread(pts, 4)
    assert len(set(a)) == 4 and (0.0, 0.0, 0.0, "s") in a
    groups = pj.pairs(a, pts)
    for anc, ps in groups:
        assert len(ps) == pj.PER
        assert all(pj.NEAR_U <= ((p[0] - anc[0]) ** 2 + (p[1] - anc[1]) ** 2) ** 0.5 <= pj.FAR_U for p in ps)
    j = yaml.safe_load(pj.render(groups, (3, -12)))
    navs = [s for s in j["steps"] if "-nav-" in s["name"]]
    assert len(navs) == pj.PER * len(groups) and navs[0]["expect"][0]["read"][0] == "nav"
    assert j["steps"][-1]["name"] == "dense-frametime" and j["independent_steps"] is True


def test_arrival_order_teleport_settle_then_polled_worldspace():
    a = (100.0, 200.0, 5.0, "place x")
    j = yaml.safe_load(pj.render([(a, [(900.0, 200.0, 5.0, "s")] * pj.PER)], (3, -12)))
    s = j["steps"][0]
    assert s["name"] == "a00-arrive"
    assert [next(iter(d)) for d in s["do"]] == ["teleport", "settle"]
    assert s["do"][1]["settle"]["cap"] == 30 and s["do"][1]["settle"]["min"] >= 1
    ex = s["expect"]
    assert not any("console" in e for e in ex)
    assert ex[0]["read"] == ["player"] and ex[0]["path"] == "worldspace.editor_id" and ex[0]["eq"] == "ARG_Province"
    assert ex[0]["within"] >= 30
    px, py = ex[1], ex[2]
    assert (px["path"], py["path"]) == ("pos.x", "pos.y")
    assert px["ge"] == 100 - 210 and px["le"] == 100 + 210 and py["ge"] == 200 - 210 and py["le"] == 200 + 210
