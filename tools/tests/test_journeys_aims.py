"""Aim overrides (tools/journeys/aims.py): write, apply, drop; the panel's vantages and sky-ab honour them."""
import json

from tools.argonia_world import panel, skyrim_units as su
from tools.journeys import aims

U = su.UNITS_PER_METRE
TEXT = """steps:
  - name: a
    do: [{console: "player.setpos x 1000"}, {console: "player.setpos y 2000"}, {console: "player.setangle z 10"}, {console: "player.setangle x -3"}]
  - name: b
    do: [{console: "player.moveto ARG_Ref_M"}, {console: "player.setangle z 20"}, {console: "player.setangle x 0"}]
"""


def test_record_writes_and_replaces_one_row_per_step(tmp_path):
    p = tmp_path / "aims.yaml"
    aims.record("j", "a", 154, None, 1000, 2000, p)
    aims.record("j", "a", 200, -5, 1000, 2000, p)
    assert aims.load(p) == [{"journey": "j", "step": "a", "heading": 200.0, "x": 1000, "y": 2000, "pitch": -5.0}]


def test_apply_sets_heading_and_pitch_keeping_the_stand(monkeypatch, capsys):
    rows = [{"journey": "j", "step": "a", "heading": 154.0, "x": 1000, "y": 2000},
            {"journey": "j", "step": "b", "heading": 90.0, "pitch": 5.0, "x": 50, "y": 60}]
    out = aims.apply_text("j", TEXT, {"ARG_Ref_M": (52, 61)}.get, rows)
    assert "player.setangle z 154" in out and "player.setangle x -3" in out and "player.setpos x 1000" in out
    assert "player.setangle z 90" in out and "player.setangle x 5" in out and "player.setangle z 20" not in out
    assert "aim override: j a 154" in capsys.readouterr().out
    assert aims.apply_text("other", TEXT, rows=rows) == TEXT


def test_an_override_is_dropped_when_the_stand_moved_over_5_m(tmp_path, monkeypatch):
    p = tmp_path / "aims.yaml"
    monkeypatch.setattr(aims, "PATH", p)
    aims.DROPPED.clear()   # other tests run the generators against the real aims.yaml
    aims.record("j", "a", 154, None, 1000 + 6 * U, 2000)
    aims.record("j", "b", 90, None, 50, 60)
    out = aims.apply_text("j", TEXT, {"ARG_Ref_M": (50 + 4 * U, 60)}.get)
    assert "player.setangle z 10" in out and "player.setangle z 90" in out   # a dropped, b (4 m) kept
    assert [r["step"] for r in aims.prune()] == ["a"]
    assert [r["step"] for r in aims.load()] == ["b"]


def test_the_panels_vantages_honour_an_override(monkeypatch):
    v = {"id": "x-shore", "x_m": 1, "y_m": 2, "ground_m": 3, "yaw_deg": 94, "pos": [500, 600, 700], "noon": None, "dawn": None}
    monkeypatch.setattr(panel, "marker_edid", lambda v: "ARG_Ref_PanelX")
    monkeypatch.setattr(panel.db, "open", lambda: type("W", (), {"rows": lambda s, t: []})())
    monkeypatch.setattr(aims, "load", lambda path=None: [{"journey": "world-panel", "step": "x-shore-noon", "heading": 154.0, "x": 500, "y": 600}])
    j = json.loads("".join(ln for ln in panel.journey_text([v]).splitlines(True) if not ln.startswith("#")))
    ang = {s["name"]: [c["console"] for c in s["do"] if "setangle z" in str(c.get("console"))] for s in j["steps"][1:]}
    assert ang == {"x-shore-noon": ["player.setangle z 154"], "x-shore-dawn": ["player.setangle z 94"]}
