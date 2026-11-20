"""The stocking split and the place-wealth read (tools/places/stock, tools/newworld/wealth.py)."""
from tools.newworld import wealth
from tools.places.stock import split


def item(sig, value=0, kws=(), **kw):
    return {"key": f"Test.esp:{abs(hash((sig, value, kws))) % 0xFFFFFF:06X}", "sig": sig, "value": value,
            "keywords": list(kws), "ench": None, **kw}


def test_split_items():
    r = split.rules()
    assert split.item_class({**item("MISC", 1), "key": "Skyrim.esm:00000F"}, r)[:2] == ("gold", True)
    assert split.item_class(item("WEAP", 10, ("WeapMaterialIron",)), r)[1]
    assert split.item_class(item("ARMO", 5, ("ArmorClothing",)), r)[:2] == ("clothing", False)
    assert split.item_class(item("ARMO", 120, ("ArmorClothing",)), r)[1]
    assert split.item_class(item("ARMO", 30, ("ArmorJewelry",)), r)[:2] == ("jewellery", True)
    assert split.item_class(item("ALCH", 3, food=True), r)[:2] == ("food", False)
    assert split.item_class(item("ALCH", 17, food=False), r)[:2] == ("potion", True)
    assert split.item_class(item("BOOK", 5, teaches={"skill": 3}), r)[:2] == ("skill-book", True)
    assert split.item_class(item("BOOK", 5), r)[:2] == ("book", False)
    assert split.item_class(item("MISC", 4, ("VendorItemClutter",)), r)[:2] == ("clutter", False)
    assert split.item_class(item("MISC", 100, ("VendorItemGem",)), r)[:2] == ("gem", True)
    assert split.item_class({**item("ARMO", 5, ("ArmorClothing",)), "ench": "Skyrim.esm:000001"}, r)[1]


def test_split_containers():
    r = split.rules()
    assert split.container_kind({"edid": "TreasBanditChestBoss"}, r) == ("boss-chest", True)
    assert split.container_kind({"edid": "BarrelFood01"}, r) == ("barrel", False)
    assert split.container_kind({"edid": "StrongBox01"}, r) == ("strongbox", True)
    assert split.container_kind({"edid": "UpperDresser01"}, r) == ("dresser", False)
    assert split.container_kind({"edid": "CommonChest"}, r) == ("chest", True)


def test_economy_read():
    rules = wealth.scale()["wealth"]
    pts, words = wealth.economy_read("It does not trade outward, but its market traders sell feathers.", rules)
    assert "-does not trade" in words and "+market" in words
    assert pts == 2 * rules["economy_plus_each"] - rules["economy_minus_each"]   # trade (traders), market; minus
    assert wealth.economy_read("", rules) == (0, [])


def test_an_owner_exception_on_a_container_row_is_read_by_space_and_ref(tmp_path):
    """A container the owner ruled out of the tier and value rules carries `owner_exception` {ruling, why} in its stock
    source row; verify reads it by (space, ref); a row with no ruling is not an exception."""
    import json
    from tools.places.stock import verify
    (tmp_path / "p.json").write_text(json.dumps({"containers": [
        {"ref": "a", "space": "hold", "owner_exception": {"ruling": "owner, 2026-11-19", "why": "his kit"}},
        {"ref": "b", "space": "hold", "owner_exception": {"why": "no ruling"}}, {"ref": "c", "space": "exterior"}]}))
    assert verify.owner_exceptions("p", tmp_path) == {("hold", "a"): {"ruling": "owner, 2026-11-19", "why": "his kit"}}
    assert verify.owner_exceptions("missing", tmp_path) == {}


def test_two_containers_of_one_ref_in_different_spaces_load_and_stay_apart():
    """Copied houses share a source ref id: a container is keyed (place, space, ref), its items and key with it."""
    import sqlite3
    from pathlib import Path
    from types import SimpleNamespace as NS
    from tools.places.stock import plan
    con = sqlite3.connect(":memory:")
    con.executescript((Path(__file__).parents[2] / "newworld/story/data/schema.sql").read_text())
    con.execute("PRAGMA foreign_keys=OFF")
    for sp, it in (("h.10", "A"), ("h.11", "B")):
        con.execute("INSERT INTO stock_container (place_id, ref_id, space_id, container_kind_id, security_level_id, "
                    "stock_tier_id, gold, why) VALUES ('p','R',?,'chest','s','T1',0,'w')", (sp,))
        con.execute("INSERT INTO stock_container_item VALUES ('p',?,'R',?,1,'w')", (sp, it))

    class W:
        def rows(self, table, **where):
            cur = con.execute(f"SELECT * FROM {table}")
            names = [d[0] for d in cur.description]
            return [NS(**dict(zip(names, r))) for r in cur]
    st = plan.Stock(W(), "p")
    assert set(st.containers) == {("h.10", "R"), ("h.11", "R")}
    assert [i.item_id for i in st.container_items[("h.10", "R")]] == ["A"]
    assert [i.item_id for i in st.container_items[("h.11", "R")]] == ["B"]
