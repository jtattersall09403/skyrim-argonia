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
