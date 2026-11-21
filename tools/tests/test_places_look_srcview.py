"""`look --source`: a source place seen by itself (tools/places/look/srcview.py). The look audit's golden scene serves
as its own source: its place rows are written into its source bundle's exterior."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pytest

from tools.places.look import draw, srcview

FX = Path(__file__).resolve().parent / "fixtures" / "look_truth"


def test_ring_points_close_and_keep_their_radius():
    ring = {"centre": [100.0, -50.0], "radius_m": 10}
    pts = draw.ring_points(ring, n=24)
    assert len(pts) == 25 and pts[0] == pytest.approx(pts[-1])
    assert all(math.dist(p, (100, -50)) == pytest.approx(700.0) for p in pts)


def test_ring_crossings_of_a_section():
    ring = {"centre": [0.0, 0.0], "radius_m": 10}   # 700 units
    assert draw.ring_crossings(ring, (-1000, 0), (1000, 0)) == pytest.approx([300.0, 1700.0])
    assert draw.ring_crossings(ring, (0, 0), (1000, 0)) == pytest.approx([700.0])
    assert draw.ring_crossings(ring, (-1000, 900), (1000, 900)) == []


def test_role_of_a_person():
    assert srcview.role_of({"class_edid": "EncClassAnimalPredator", "factions": [{"edid": "CreatureFaction"}]}) == "creature"
    assert srcview.role_of({"edid": "X", "services": {"guard": "k"}}) == "guard"
    assert srcview.role_of({"edid": "ArgonianMaleKid", "class_edid": "CombatWarrior1H"}) == "child"
    assert srcview.role_of({"edid": "Q", "class_edid": "Priest"}) == "priest"


@pytest.fixture(scope="module")
def fx(tmp_path_factory):
    root = tmp_path_factory.mktemp("srcview")
    sys.path.insert(0, str(FX))
    import make
    env = make.make(root)
    out = Path(env["PLACES_OUT"])
    rows = [json.loads(x) for x in (FX / "places" / make.PLACE / "spaces" / "exterior" / "refs.jsonl").read_text().splitlines() if x.strip()]
    src = [{"id": f"GsTruth.esm:{0xA00 + i:06X}", "base": r["base"], "kind": r.get("kind"), "pos": r["pos"],
            "rot": r.get("rot") or [0, 0, 0], "scale": r.get("scale", 1.0), "layer": "place", "flags": []}
           for i, r in enumerate(rows) if r.get("pos") and not r.get("removed")]
    p = out / "bundles" / f"src.{make.SOURCE}" / "spaces" / "exterior" / "refs.jsonl"
    p.write_text("".join(json.dumps(r) + "\n" for r in src))
    return {"root": root, "out": out, "src": src, "sid": make.SOURCE}


def test_prepare_writes_the_source_as_a_view_place(fx):
    base = fx["root"] / "view"
    pid = srcview.prepare(fx["sid"], 5, None, base=base, shared=fx["out"])
    assert pid == "source." + fx["sid"]
    place = json.loads((base / "places" / pid / "place.json").read_text())
    assert place["view_only"] and place["source_id"] == fx["sid"]
    assert place["look_ring"] == {"centre": [0.0, 0.0], "radius_m": 5.0}
    rows = [json.loads(x) for x in (base / "places" / pid / "spaces" / "exterior" / "refs.jsonl").read_text().splitlines()]
    assert len(rows) == len(fx["src"])
    by_src = {r["src"]: r for r in rows}
    for s in fx["src"]:   # unmoved, free, and outside the ring only past 5 m
        r = by_src[s["id"]]
        assert r["pos"] == s["pos"] and r["seat"]["mode"] == "free"
        assert (r["cluster"] == "outside") == (math.dist(s["pos"][:2], (0, 0)) > 350)
    g = base / "data" / "bundles" / f"ground.{pid}"
    assert (g / "spaces" / "exterior" / "terrain.f32").is_file() and not (g / "spaces" / "exterior" / "terrain.f32").is_symlink()
    assert (g / "spaces" / "exterior" / "refs.jsonl").read_text() == ""
    m1 = (base / "places" / pid / "place.json").stat().st_mtime_ns
    srcview.prepare(fx["sid"], 5, None, base=base, shared=fx["out"])   # unchanged: not rewritten (no page reload)
    assert (base / "places" / pid / "place.json").stat().st_mtime_ns == m1


def test_units_counts_inside_the_ring(fx):
    whole = srcview.units(fx["sid"], None, None, bundles=fx["out"] / "bundles")
    assert whole["pieces"] == whole["of"] == len(fx["src"])
    assert whole["by_class"].get("tree", 0) >= 1
    small = srcview.units(fx["sid"], 0.5, (99999.0, 99999.0), bundles=fx["out"] / "bundles")
    assert small["pieces"] == 0 and small["ring"]["radius_m"] == 0.5
    assert "inside the ring of 0.5 m" in srcview.units_text(small)


def test_the_hands_are_refused():
    with pytest.raises(SystemExit, match="read-only"):
        srcview.main(["fx_src", "move", "a", "1", "0", "0"])
