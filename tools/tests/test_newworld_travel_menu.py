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


def test_every_walk_spot_is_a_menu_button_and_the_start_ids_agree():
    from tools.newworld import teleports as tp
    doc = json.loads(T.MENU.read_text())
    cells = {b["cell"] for p in doc["pages"].values() for b in p["buttons"] if "cell" in b}
    assert {s["name"] for s in tp.SPOTS} <= cells
    reg = json.loads((T.REPO / "newworld/sources/world_formids.json").read_text())["ids"]["base"]
    cs = (T.REPO / "tools/ArgoniaPlugin/NewWorldTravel.cs").read_text()
    psc = (T.REPO / "papyrus/ARG_QF_MQ101.psc").read_text()
    assert reg["travel:give"] == "0x00F000" and "GiveId = 0x00F000" in cs and "NWGiveId = 0xF000" in psc
