"""Each room's name from what the place data holds (tools/places/draft/names.py)."""
import json

from tools.places.draft import names


def files(*rooms):
    return {"spaces": {"exterior": {"refs": [], "space": None},
                       **{sid: {"refs": [{"id": f"{sid}.r"}], "space": {"space_id": sid, "name": nm}} for sid, nm in rooms}},
            "people": [{"id": "p.inn", "work": {"space": "Ship"}, "services": [{"seq": 6}]},
                       {"id": "p.heal", "work": {"space": "Cave"}, "services": [{"seq": 5}]}]}


GIVES = [{"seq": 5, "give_kind_id": "trader-spells", "detail": "tree-minder's healer: tomes"},
         {"seq": 6, "give_kind_id": "trader-innkeeper", "detail": "the boatmen's lodge"},
         {"seq": 15, "give_kind_id": "arcane-enchanter", "detail": "the tree-minders' hall"}]
PLACE = {"stations": {"added": [{"station": "arcane-enchanter", "space": "Cave"}], "found": {}},
         "draft": {"room_names": {"Odd": {"name": "Market Cave", "why": "stalls inside"}}}}


def test_title_and_leftovers():
    assert names.title("the tree-minders' hall") == "Tree-Minders' Hall"
    assert names.title("boatmen's lodge") == "Boatmen's Lodge"
    assert names.leftover("Quick Test Cell") and names.leftover("01cellDUPLICATE002") and names.leftover("HallInt")
    assert not names.leftover("Boatmen's Lodge") and not names.leftover("House")


def test_rooms_named_by_promise_household_call_and_source(tmp_path):
    places = tmp_path / "newworld" / "places"
    (places.parent / "sources" / "people").mkdir(parents=True)
    (places.parent / "sources" / "people" / "x.json").write_text(json.dumps({
        "households": [{"id": "h1", "home_space": "Home"}, {"id": "h2", "home_space": "Ship"}],
        "people": [{"id": "a", "name": "Ixtul-Bei", "household": {"id": "h1", "role": "head"}},
                   {"id": "b", "name": "Sleeps-Last", "household": {"id": "h2", "role": "head"}}]}))
    f = files(("Home", "House"), ("Ship", "Ship"), ("Cave", "Quick Test Cell"), ("Odd", None), ("Spare", "Hut"))
    got = {k: v[0] for k, v in names.room_names("x", f, PLACE, GIVES, places).items()}
    assert got == {"Home": "Ixtul-Bei's House", "Ship": "Boatmen's Lodge", "Cave": "Tree-Minders' Hall",
                   "Odd": "Market Cave", "Spare": "Hut"}
    assert names.faults(f)                                   # as they stand: a leftover and a missing name
    for sid, nm in got.items():
        f["spaces"][sid]["space"]["name"] = nm
    assert names.faults(f, names.room_names("x", f, PLACE, GIVES, places)) == []
    f["spaces"]["Spare"]["space"]["name"] = "Ixtul-Bei's House"
    assert any("share the name" in x for x in names.faults(f))
