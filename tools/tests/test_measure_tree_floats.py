"""measure flags a tree whose feet stand well over the ground with nothing under them (it grew on a rock since sunk)."""
from types import SimpleNamespace

from tools.places.look import measure


def _sc():
    return SimpleNamespace(everything=lambda: [], ground=None)


def test_feet_in_the_air_with_nothing_under_float(monkeypatch):
    monkeypatch.setattr(measure.geom, "aabb", lambda q: ([0, 0, 0], [1, 1, 1]))
    monkeypatch.setattr(measure.geom, "probe_piece", lambda *a, **k: {"lowest_over_ground": 700.0, "held_by": None})
    assert measure.tree_floats({"id": "t"}, _sc())


def test_feet_on_a_rock_or_near_the_ground_do_not(monkeypatch):
    monkeypatch.setattr(measure.geom, "probe_piece", lambda *a, **k: {"lowest_over_ground": 700.0, "held_by": ["rock"]})
    assert not measure.tree_floats({"id": "t"}, _sc())
    monkeypatch.setattr(measure.geom, "probe_piece", lambda *a, **k: {"lowest_over_ground": 40.0, "held_by": None})
    assert not measure.tree_floats({"id": "t"}, _sc())
