"""Clothing: every trade kit dresses its people, every piece filed for a race fits it (read from the plugin's ARMA race
lists), and the derive gives a non-guard person one worn outfit by their kit, race and wealth band."""
from __future__ import annotations

import json

import pytest

from tools.places.stock import split

STOCK = split.STOCK
CLOTHING = ("cloth", "fine-cloth")


def _clothing_rows():
    return {k: r for k, r in split.item_materials()["gear"].items() if r.get("races")}


def test_every_trade_kit_has_a_clothing_row_of_clothing_materials():
    kits = json.loads((STOCK / "kits.json").read_text())["kits"]
    for k in kits:
        rows = [w for w in k["wear"] if w.get("slot") == "clothing"]
        assert rows, k["id"]
        assert all(set(w["materials"]) <= set(CLOTHING) for w in rows), k["id"]


def test_clothing_rows_are_clothing_of_a_clothing_material_and_never_armour_typed():
    items = {i["id"]: i for i in json.loads((STOCK / "items.json").read_text())["items"]}
    rows = _clothing_rows()
    assert len(rows) >= 50
    for k, r in rows.items():
        assert r["material"] in CLOTHING and items[k]["power_kind"] is None, k     # an ArmorLight robe is armour
        assert items[k]["item_kind_id"] == "clothing" or items[k]["record"] == "ARMO", k


def test_every_piece_filed_for_argonians_fits_argonians_by_its_armature_races():
    from tools.places.stock import fit
    base = ["Skyrim.esm", "Update.esm", "Dawnguard.esm", "HearthFires.esm", "Dragonborn.esm"]
    rows = _clothing_rows()
    plugins = base + sorted({k.rsplit(":", 1)[0] for k in rows} - set(base))
    try:
        f = fit.Fit.load(plugins)
    except FileNotFoundError:
        pytest.skip("the clothing mods' plugins are not on this machine")
    for k, r in rows.items():
        ok, why = f.argonian(k)
        assert ok or "ArgonianRace" not in r["races"] and "*" not in r["races"], f"{k}: {why}"


def test_the_picker_dresses_by_race_and_band():
    from tools.places.stock.derive import Picker, ladder_records
    pick = Picker(None, split.scale(), None, ladder_records())
    poor = pick.clothing(["cloth"], "ArgonianRace", 1)
    rich = pick.clothing(["fine-cloth", "cloth"], "ArgonianRace", 5)
    assert poor and rich and poor["value"] <= rich["value"]
    gear = split.item_materials()["gear"]
    assert "ArgonianRace" in gear[poor["key"]]["races"] and "ArgonianRace" in gear[rich["key"]]["races"]
    dunmer = pick.clothing(["fine-cloth"], "DarkElfRace", 3)
    assert "DarkElfRace" in gear[dunmer["key"]]["races"]          # a Telvanni robe
    khajiit = pick.clothing(["fine-cloth", "cloth"], "KhajiitRace", 3)
    assert gear[khajiit["key"]]["races"] == ["*"]                 # Skyrim's own clothes, the fallback
