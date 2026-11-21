from types import SimpleNamespace

from tools.places.look import hands


def test_a_walkway_with_a_level_deck_is_a_deck_steps_can_leave(monkeypatch):
    fake = SimpleNamespace(decks=lambda rows, bases: [], deck_rect=lambda b: (50.0, (-100.0, -20.0, 100.0, 20.0)))
    monkeypatch.setattr(hands, "_walk", lambda: fake)
    monkeypatch.setattr(hands, "platform_top", lambda b: None)
    row = {"id": "w", "base": "k", "kind": "building", "pos": [0.0, 0.0, 500.0], "scale": 1.0}
    sc = SimpleNamespace(bases={"k": {"model": "x/murkmirewalkwaylong01.nif"}})
    got = hands.decks(sc, [row])
    assert got and got[0][1] == 550.0
