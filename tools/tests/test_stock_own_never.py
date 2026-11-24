"""A gear row's own `never` bars that item from stock, with its reason; the Xanmeer obsidian make stays stockable
while the glass recolours it covers are barred (owner, #94, 2026-11-24)."""
from tools.places.stock import split


def _item(key, edid):
    return {"key": key, "edid": edid, "keywords": [], "ench": False}


def test_own_never_reason_bars_the_covered_recolour():
    why = split.never_reason(_item("Obsidian Weapons Update 4.esp:000D6A", "ObsidianSword_holz"))
    assert why and "Xanmeer" in why


def test_xanmeer_make_is_not_barred():
    row = split.item_materials()["gear"]
    xan = [k for k, r in row.items() if r.get("material") == "obsidian" and "Cipactli" in k]
    assert xan and all(not row[k].get("never") for k in xan)


def test_recolour_fills_the_two_handed_gap():
    row = split.item_materials()["gear"]
    kept = [k for k, r in row.items() if k.startswith("Obsidian Weapons Update 4.esp") and not r.get("never")]
    assert len(kept) == 6      # battleaxe, greatsword and warhammer at T4, black and clear: the Xanmeer make has them only at T5
