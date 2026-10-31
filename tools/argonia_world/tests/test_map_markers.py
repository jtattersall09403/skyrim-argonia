"""1.12: the map markers (map_markers.py): one hidden marker per placed place, its type by kind, no orphan."""
from tools.argonia_world import db, map_markers as m, quest_gen
from tools.argonia_world import skyrim_units as su


class _Alloc:
    def form_key(self, edid, rtype=None, key=None):
        return f"{abs(hash(edid)) % 0xFFFFFF:06X}:Argonia.esm"


def _refs():
    return m.refs(_Alloc(), db.open(), lambda x, y: 0.0)


def test_one_hidden_marker_per_placed_place():
    w = db.open()
    rs = _refs()
    placed = m.placed(w)
    assert len(rs) == len(placed) >= 1
    assert len({r["edid"] for r in rs}) == len(rs)
    by_name = {p.name for p in placed}
    for r in rs:
        assert r["base"] == su.MAP_MARKER and r["persistent"]
        assert r["mapMarker"]["flags"] == [] and r["mapMarker"]["name"] in by_name  # no orphan
    assert quest_gen.check_records([{"type": "WRLD", "persistentRefs": rs}]) == []


def test_claywater_is_a_hidden_settlement():
    cw = [r for r in _refs() if r["edid"] == "ARG_MapMarker_ClaywaterStation"]
    assert cw and cw[0]["mapMarker"] == {"name": "Claywater Station", "type": "Settlement", "flags": []}


def test_the_rule_catches_a_shown_marker():
    r = dict(_refs()[0], mapMarker={"name": "x", "type": "Camp", "flags": ["Visible"]})
    assert quest_gen.check_records([{"type": "WRLD", "persistentRefs": [r]}])


def test_type_mapping():
    assert m.marker_type("settlement", "major-city") == "City"
    assert m.marker_type("settlement", "tribal-village") == "Settlement"
    assert m.marker_type("sacred", "hist") == "Grove"
    assert m.marker_type("lair", "beast-lair") == "Cave"
    assert m.marker_type(None, None) == m.DEFAULT_TYPE
    assert m.marker_type("nothing", "x") == m.DEFAULT_TYPE


def test_edid_shared_name_carries_region():
    assert m.marker_edid("place.hist-heartland.marsh-giant-ground-basin", True) == \
        "ARG_MapMarker_HistHeartland_MarshGiantGroundBasin"


def test_committed_worldspace_yaml_shows_no_marker(tmp_path):
    assert quest_gen.check_yaml(quest_gen.REPO / "plugin" / "Argonia" / "Worldspaces") == []
    (tmp_path / "w.yaml").write_text("    MapMarker:\n      Name: x\n      Flags:\n      - Visible\n    Placement: 1\n")
    (tmp_path / "ok.yaml").write_text("    MapMarker:\n      Type: Camp\n    Flags:\n    - Visible\n")
    assert len(quest_gen.check_yaml(tmp_path)) == 1
