"""A piece of a base no bundle holds yet is read from the catalogue, not reported as a missing base."""
from tools.places.look.scene import fill_from_catalogue


def test_fills_only_what_the_bundles_lack():
    bases = {"A:1": {"key": "A:1", "edid": "Old"}}
    cat = {"A:1": {"key": "A:1", "edid": "Catalogue"}, "B:2": {"key": "B:2", "edid": "Boat"}}
    got = fill_from_catalogue(bases, {"A:1", "B:2", "C:3"}, cat)
    assert got == ["B:2"]
    assert bases["A:1"]["edid"] == "Old"       # a bundle's row is never replaced
    assert bases["B:2"]["edid"] == "Boat"
    assert "C:3" not in bases                  # in no catalogue either: still missing


def test_nothing_wanted_reads_no_catalogue():
    assert fill_from_catalogue({"A:1": {}}, {"A:1"}, catalogue=None) == []
