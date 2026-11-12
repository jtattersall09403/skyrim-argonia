"""The travel menu (tools/newworld/travel_menu.py): the committed pages hold the menu's rules, and a bad page is named."""
import json

from tools.newworld import travel_menu as T


def test_committed_menu_holds_its_rules():
    doc = json.loads(T.MENU.read_text())
    assert T.faults(doc) == []
    assert "spots" in doc["pages"]  # the reserved page for walk-check spots


def test_faults_are_named():
    doc = {"root": "a", "pages": {"a": {"title": "A", "buttons": [{"label": f"b{i}", "cell": "X"} for i in range(11)]},
                                  "b": {"title": "B", "buttons": [{"label": "x", "page": "nope"}]}}}
    bad = "\n".join(T.faults(doc))
    assert "11 buttons" in bad and "page nope does not exist" in bad and "b: not reachable" in bad
    assert T.faults({"root": "a", "pages": {"a": {"title": "A", "buttons": [{"label": "x", "cell": "C"}]}}}, {"D"})
