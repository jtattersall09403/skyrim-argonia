"""The ground-colour check on small tables: a shared flower grass, neighbours alike, the overlap bound."""
from types import SimpleNamespace

from tools.newworld.dressing import ground_colour as gc

KM = "King of the Murkmire.esp"


def tex(a_grass, b_grass):
    return SimpleNamespace(
        MATERIALS={"meadow": ("x", [f"{KM}:Base"], "d"), "river_mud": ("x", [f"{KM}:Kelp"], "d")},
        PROVINCES={"p": {"regions": ["a", "b"], "grass": {}}},
        REGIONS={"a": {"grass": {"meadow": a_grass}}, "b": {"grass": {"meadow": b_grass}}})


FAM = {"Lupin": "violet", "Cup": "yellow", "Fern": "green", "Reed": "green", "Base": "green", "Kelp": "orange"}
ADJ = {"a": {"b"}, "b": {"a"}}


def test_distinct_regions_pass():
    r = gc.check(tex([f"{KM}:Lupin", f"{KM}:Fern"], [f"{KM}:Cup", f"{KM}:Reed"]), FAM, ADJ, {"a": "violet", "b": "yellow"})
    assert r["faults"] == [] and r["shared_flowers"] == 0 and r["mean_overlap"] == 0


def test_shared_flower_and_overlap_fail():
    r = gc.check(tex([f"{KM}:Lupin", f"{KM}:Fern"], [f"{KM}:Lupin", f"{KM}:Fern"]), FAM, ADJ, {"a": "violet", "b": "violet"})
    assert r["shared_flowers"] == 1
    assert any("both show violet" in f for f in r["faults"]) and any("share 1.00" in f for f in r["faults"])


def test_colour_without_any_grass_is_unmet_not_fault():
    r = gc.check(tex([f"{KM}:Fern"], [f"{KM}:Cup"]), FAM, ADJ, {"a": "blue", "b": "yellow"})
    assert r["faults"] == [] and len(r["unmet"]) == 1


def test_missing_census_is_built(tmp_path, monkeypatch):
    from tools.newworld.dressing import grass_census

    def fake(argv):
        import json
        from pathlib import Path
        Path(argv[1]).write_text(json.dumps({"grasses": [{"edid": "Lupin", "family": "violet"}]}))
        return 0
    monkeypatch.setattr(grass_census, "main", fake)
    assert gc.census_families(tmp_path / "c.json") == {"Lupin": "violet"}
