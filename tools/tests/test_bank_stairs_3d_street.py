"""A street laid on a deck at its own height (3-d points) is read in plan by bank_stairs: it once raised
"both points must have the same number of dimensions" and stopped `draft join`."""
from types import SimpleNamespace

from tools.places.draft import walk


class Flat:
    def height(self, x, y):
        return 0.0


def test_bank_stairs_reads_a_3d_street_over_a_deck(monkeypatch):
    deck = {"id": "d", "pos": [0.0, 0.0, 100.0], "rot": [0, 0, 0], "base": "b"}
    monkeypatch.setattr(walk, "decks", lambda rows, bases: [(deck, 100.0, (-500.0, -100.0, 500.0, 100.0))])
    Wd = SimpleNamespace(found=lambda p: (-1, 0.0, 0.0), main=[], line_ok=lambda S: [True] * len(S))
    paths = [{"id": "s", "points": [[-400.0, 0.0, 100.0], [400.0, 0.0, 100.0]]}]
    assert walk.bank_stairs("p", paths, Wd, [deck], {}, [], Flat()) == []
