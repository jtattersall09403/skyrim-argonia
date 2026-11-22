"""The items ladder (docs/design/items.md): our materials, the tier by power, the reach, region and trade-kit checks and
the expected mix, on the committed sources and the database built from them."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.argonia_world import db
from tools.newworld import frame
from tools.places.stock import reach, split

STOCK = Path(__file__).resolve().parents[2] / "newworld" / "sources" / "stock"
GOLD = "Skyrim.esm:00000F"
GREATSWORD = "King of the Murkmire.esp:098EC3"   # the Saxhleel greatsword: copper-edged steel (bog-iron)
FISHER = "outpost-m6-m66.1E488HDG6T5QBFE131SAZPE7BH"   # the eel-trapper at the weir


@pytest.fixture(scope="module")
def w():
    return db.open(frame.ROOT)


def test_every_material_row_is_whole_and_every_keyword_reads_as_one_material():
    doc = json.loads((STOCK / "materials.json").read_text())
    seen = {}
    for m in doc["materials"]:
        assert m["group"] in doc["groups"] and m["band"] in doc["bands"], m["id"]
        assert m["lore"] and m["reach"] or m["band"] == "never", m["id"]
        for k in m["keywords"]:
            assert k not in seen, f"{k} reads as {seen[k]} and {m['id']}"
            seen[k] = m["id"]
    assert set(doc["never"]["materials"]) <= {m["id"] for m in doc["materials"]}


def test_the_tables_hold_the_sources(w):
    assert {m.id for m in w.rows("material")} >= {"wood", "bone", "flint", "obsidian", "bog-iron", "imperial"}
    assert {r.material_id for r in w.rows("never_material")} == {"nordic", "falmer", "forsworn", "skyrim-orders"}
    assert len(w.rows("item_material")) == len(json.loads((STOCK / "item_material.json").read_text())["gear"])
    assert {r.region_id for r in w.rows("region_profile")} == {r.id for r in w.rows("region")}
    assert w.rows("trade_kit_never", kit_id="fisher")


def test_never_is_joined_on_our_material_not_the_keyword():
    zuuk = {"key": "Here There Be Monsters - Curse of Cipactli.esp:2AD6CD", "edid": "CIPHTBMKothringiCuirassZuuk",
            "keywords": ["DLC2ArmorMaterialNordicHeavy"]}
    assert split.material_of(zuuk)[0] == "kothringi-relic" and split.never_reason(zuuk) is None
    nord = {"key": "Dragonborn.esm:000000", "edid": "SomeSword", "keywords": ["DLC2WeaponMaterialNordic"]}
    assert "decision 0006" in split.never_reason(nord)


def test_the_tier_is_set_by_power_against_skyrim_s_base_gear():
    table = {"sword": {"ceiling": {"T1": 8, "T2": 9, "T3": 11, "T4": 12, "T5": 13, "T6": 15}},
             "light-cuirass": {"ceiling": {"T1": 26, "T2": 26, "T3": 32, "T4": 35, "T5": 38, "T6": 41}}}
    bone_sword = {"sig": "WEAP", "keywords": ["WeapTypeSword", "WeapMaterialGlass"], "damage": 12, "value": 165}
    assert split.power_tier(bone_sword, table=table)[0] == "T4"           # glass-grade damage, whatever its price
    leather = {"sig": "ARMO", "keywords": ["ArmorLight", "ArmorCuirass"], "rating": 38}
    assert split.power_tier(leather, table=table)[0] == "T5"
    assert split.power_tier({**leather, "rating": 26}, table=table)[0] == "T1"
    assert split.power_tier({**bone_sword, "damage": 17}, table=table)[0] == "T6"   # above every ceiling
    assert split.power_tier({"sig": "WEAP", "keywords": ["WeapTypeStaff"], "damage": 9}, table=table) == (None, "")


def test_an_item_material_row_s_tier_is_the_one_exception_to_power():
    priest = {"key": "Here There Be Monsters - Curse of Cipactli.esp:53EB2A", "sig": "ARMO", "edid": "CIPHTBMNagaPriestArmor",
              "keywords": ["ArmorLight", "ArmorHelmet", "ArmorMaterialScaled"], "rating": 25}
    assert split.item_tier(priest)[0] == "T1"


def test_every_itemised_piece_stands_on_the_ladder_at_its_measured_tier():
    sc = split.scale()
    lists = {(t["id"], s): set(t[s]) for t in sc["tiers"] for s in ("weapon", "heavy", "light", "shield")}
    bands = {m: r["band"] for m, r in split.materials()["materials"].items()}
    off = [(i["edid"], i["material_id"], i["stock_tier_id"]) for i in json.loads((STOCK / "items.json").read_text())["items"]
           if split.slot_of(i) and i["material_id"] and bands[i["material_id"]] != "never"
           and i["material_id"] not in lists[(i["stock_tier_id"], split.slot_of(i))]]
    assert off == []


def test_wares_name_real_goods_and_harvestables():
    goods = {g["id"] for g in json.loads((STOCK / "goods.json").read_text())["goods"]}
    h = json.loads((STOCK.parent / "ecology" / "harvestables.json").read_text())
    known = set(h["kinds"]) | set(h["lore"])
    for r in json.loads((STOCK / "item_material.json").read_text())["wares"]:
        assert r["good"] in goods, r
        assert r.get("harvestable") is None or r["harvestable"] in known, r


def test_reach_fails_imperial_gear_where_the_record_gives_no_reason_and_passes_it_where_it_does(w):
    r = reach.reaches(w, "outpost-m6-m66")
    assert not r["imperial"][0] and "gives no reason" in r["imperial"][1]
    assert not r["dwarven"][0] and not r["glass"][0] and r["flint"][0]
    assert reach.reaches(w, "outpost-m13-m65")["bonemold"][0]          # a stone-grey place: Dunmer make reaches it
    doc = {"possessions": [{"person": "x", "items": [{"item": "Skyrim.esm:013ED9", "count": 1}]}]}   # Imperial cuirass
    bad = reach.audit(w, "outpost-m13-m65", doc)
    assert {b["material"] for b in bad} == {"imperial"} and len(bad) == 1


def test_a_denied_mention_in_the_record_is_no_reason(w):
    text = [("place_note.present", "Helstrom is the least Imperialised city."), ("place_note.history", "No imperial legion took it.")]
    assert reach.says(r"\b(imperial|legion)\b", text) is None


def test_the_region_and_the_place_class_flag_what_they_hold_none_of(w):
    doc = {"possessions": [{"person": "x", "items": [{"item": "Skyrim.esm:013ED9", "count": 1}]}]}   # Imperial cuirass
    bad = reach.audit(w, "helstrom", doc)
    assert bad and bad[0]["rule"] in ("material reach", "region")
    iron = {"possessions": [{"person": "x", "items": [{"item": "Skyrim.esm:012EB7", "count": 1}]}]}   # iron sword
    camp = reach.audit(w, "tribal-camp-m2-m68", iron)
    assert camp and {b["rule"] for b in camp} == {"place class"}


def test_a_fisher_with_a_metal_greatsword_is_a_contradiction_unless_the_row_says_why(w):
    doc = {"possessions": [{"person": FISHER, "items": [{"item": GREATSWORD, "count": 1}]}]}
    bad = reach.contradictions(w, "outpost-m6-m66", doc)
    assert bad and bad[0]["kit"] == "fisher"
    doc["possessions"][0]["items"][0]["exception"] = "her late husband's sword, kept over the door"
    assert reach.contradictions(w, "outpost-m6-m66", doc) == []


def test_the_expected_mix_says_which_rule_gave_each_share(w):
    m = reach.expected_mix(w, "outpost-m13-m65")
    assert m["class"] == "village" and sum(t["pct"] for t in m["targets"]) in (99, 100, 101)
    assert any("stone-grey" in x for x in m["trace"])
    assert reach.expected_mix(w, "helstrom")["class"] == "city"


def test_every_piece_has_a_forge_and_a_tempering_recipe_of_obtainable_ingredients(w):
    from tools.places.stock import recipes
    doc = json.loads((STOCK / "recipes.json").read_text())
    made = {r.good_id for r in w.rows("region_good")} | {r.good_id for r in w.rows("place_good") if r.relation == "makes"}
    assert recipes.check(doc, split.item_materials()["wares"], made) == []
    forged = {r["item"]: r for r in doc["recipes"] if r["kind"] == "forge"}
    relic = forged["Here There Be Monsters - Curse of Cipactli.esp:5C2FDE"]      # Xanmeer heavy armour, T6
    assert relic["station"] is None and "never forged" in relic["why"]
    bone = forged["PrvtI_ArgonianWeapons.esp:00082D"]                          # the bone dagger: no horker tusk
    assert "Skyrim.esm:03AD68" not in {k for k, _ in bone["ingredients"]}
    assert len(w.rows("recipe")) == len(doc["recipes"])
