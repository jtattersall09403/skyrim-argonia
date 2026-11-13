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
    from tools.newworld import idspace
    cs = (T.REPO / "tools/ArgoniaPlugin/NewWorldTravel.cs").read_text()
    psc = (T.REPO / "papyrus/ARG_QF_MQ101.psc").read_text()
    assert idspace.SPAN["travel-give"][0] == 0x090000 and "GiveId = 0x090000" in cs and "NWGiveId = 0x90000" in psc


def test_a_row_wider_than_the_screen_and_a_page_without_back_are_named():
    wide = [{"label": "x" * 24, "cell": "C"} for _ in range(5)]
    doc = {"root": "a", "pages": {"a": {"title": "A", "buttons": [{"label": "B", "page": "b"}]},
                                  "b": {"title": "B", "buttons": wide}}}
    bad = "\n".join(T.faults(doc))
    assert "characters wide" in bad and "b: no Back button" in bad and "share a label" in bad


def test_pager_fits_every_item_and_each_page_but_the_last_has_more():
    items = [{"label": f"Place number {i}", "cell": f"C{i}"} for i in range(30)]
    pages = T._chunks("p", "Places", items, "root")
    doc = {"root": "root", "pages": {"root": {"title": "R", "buttons": [{"label": "Places", "page": "p"}]}, **pages}}
    assert T.faults(doc) == []
    got = [b["cell"] for p in pages.values() for b in p["buttons"] if "cell" in b]
    assert sorted(got) == sorted(i["cell"] for i in items)
    assert all(any(b["label"] == T.MORE for b in p["buttons"]) for k, p in pages.items() if k != f"p-{len(pages)}")
