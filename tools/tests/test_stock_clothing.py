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


def _who(race="ArgonianRace", culture="jade", role="resident", trade="fisher", place="outpost-m11-m63", pid="x"):
    from types import SimpleNamespace
    return SimpleNamespace(id=pid, race_id=race, culture_id=culture, person_role_id=role, trade=trade, place_id=place)


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
    poor = pick.clothing(["cloth"], _who(), 1)
    rich = pick.clothing(["fine-cloth", "cloth"], _who(), 5)
    assert poor and rich and poor["value"] <= rich["value"]
    gear = split.item_materials()["gear"]
    assert "ArgonianRace" in gear[poor["key"]]["races"] and "ArgonianRace" in gear[rich["key"]]["races"]
    dunmer = pick.clothing(["fine-cloth"], _who("DarkElfRace", trade="mage"), 3)
    assert "DarkElfRace" in gear[dunmer["key"]]["races"]          # a Telvanni robe
    khajiit = pick.clothing(["fine-cloth", "cloth"], _who("KhajiitRace"), 3)
    assert gear[khajiit["key"]]["races"] == ["*"]                 # Skyrim's own clothes, the fallback


def _worn_by(person, materials=("fine-cloth", "cloth")):
    from tools.places.stock.derive import Picker, ladder_records
    pick = Picker(None, split.scale(), None, ladder_records())
    gear = split.item_materials()["gear"]
    got = []
    for band in range(1, 6):
        c = pick.clothing(list(materials), person, band)
        got.append(gear[c["key"]] if c else None)
    return got


def test_a_garment_of_the_gone_or_of_an_enemy_people_or_an_office_is_never_given_to_another():
    for person in (_who(), _who(culture="forest-green", place="helstrom"), _who("DarkElfRace", "stone-grey", trade="gang-master"),
                   _who(culture="stone-grey", trade="fire-tender")):
        for mats in (("cloth",), ("fine-cloth",), ("fine-cloth", "cloth")):
            for row in _worn_by(person, mats):
                assert row is None or not (row.get("people") or row.get("office")), (person, row)
    mage = _worn_by(_who("DarkElfRace", "stone-grey", trade="a Telvanni hedge-mage"), ("fine-cloth",))
    assert all(r.get("office") == "mage" for r in mage)


def test_the_naga_camp_is_dressed_in_naga_dress_and_the_chime_keepers_in_kothringi_dress():
    naga = _who(culture="stone-grey", place="tribal-camp-m2-m68", pid="tribal-camp-m2-m68.7PPTW3WSTPDPAZ05VNAD6T0165")
    for mats in (("cloth",), ("fine-cloth",)):
        assert all(r.get("people") == "naga" for r in _worn_by(naga, mats)), mats
    keeper = _worn_by(_who(culture="oxblood", place="x"), ("fine-cloth",))
    assert any(r.get("people") == "kothringi" for r in keeper)


def test_every_garment_whose_why_names_a_people_or_an_office_is_tagged_with_it():
    dress = json.loads((STOCK / "item_material.json").read_text())["dress"]
    for k, r in _clothing_rows().items():
        w = r["why"].lower()
        for people in dress["peoples"]:
            if people in w:
                assert r.get("people") == people, f"{k}: {r['why']}"
        if "telvanni" in w or "mage" in w or "robe" in w and "monk" not in w and "sacrificial" not in w:
            assert r.get("office") == "mage" or r.get("people"), f"{k}: {r['why']}"
        assert r.get("people", "") in ("", *dress["peoples"]) and r.get("office", "") in ("", *dress["offices"]), k
    for d in (*dress["peoples"].values(), *dress["offices"].values()):
        assert d["lore"].startswith("story/lore/") and "wearers" in d
