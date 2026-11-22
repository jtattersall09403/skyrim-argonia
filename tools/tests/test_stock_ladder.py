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


def test_power_tier_measures_an_item_off_the_ladder_against_skyrim_s_base_gear():
    table = {"sword": {"ceiling": {"T1": 8, "T2": 9, "T3": 11, "T4": 12, "T5": 13, "T6": 15}},
             "light-cuirass": {"ceiling": {"T1": 26, "T2": 26, "T3": 32, "T4": 35, "T5": 38, "T6": 41}}}
    sword = {"sig": "WEAP", "keywords": ["WeapTypeSword", "WeapMaterialGlass"], "damage": 12, "value": 165}
    assert split.power_tier(sword, table=table)[0] == "T4"
    leather = {"sig": "ARMO", "keywords": ["ArmorLight", "ArmorCuirass"], "rating": 38}
    assert split.power_tier(leather, table=table)[0] == "T5"
    assert split.power_tier({**sword, "damage": 17}, table=table)[0] == "T6"   # above every ceiling
    assert split.power_tier({"sig": "WEAP", "keywords": ["WeapTypeStaff"], "damage": 9}, table=table) == (None, "")


KOTM, HTBM, BMN = "King of the Murkmire.esp:", "Here There Be Monsters - Curse of Cipactli.esp:", "Black Marsh North.esp:"


def test_a_ladder_item_s_tier_is_its_material_s_whatever_the_mod_s_numbers():
    bone_sword = {"key": KOTM + "275050", "sig": "WEAP", "keywords": ["WeapTypeSword", "WeapMaterialGlass"], "damage": 12}
    leather = {"key": KOTM + "000D63", "sig": "ARMO", "keywords": ["ArmorLight", "ArmorCuirass"], "rating": 38}
    guard = {"key": BMN + "037DF0", "sig": "ARMO", "keywords": ["ArmorLight", "ArmorCuirass", "ArmorMaterialElven"], "rating": 35}
    assert split.item_tier(bone_sword)[0] == "T2" and split.item_tier(leather)[0] == "T2"     # Saxhleel work
    assert split.item_tier(guard)[0] == "T3"                                                  # Argonian scale
    great = {"key": HTBM + "1979CF", "sig": "WEAP", "keywords": ["WeapTypeBattleaxe"], "damage": 22}
    assert split.item_tier(great) == ("T5", split.item_tier(great)[1]) and "great obsidian" in split.item_tier(great)[1]
    # every ladder item takes its tier's Skyrim stats: the bone sword a steel sword's, the guard cuirass scaled's
    assert split.ladder_override(bone_sword)["power"] == 8.0
    assert split.ladder_override(guard)["power"] == 32.0


def test_mn01_s_gifts_already_stand_at_their_tier_and_are_left_as_they_are():
    gifts = {HTBM + "16F16F": ("WeapTypeWarhammer", 18), HTBM + "16F16D": ("WeapTypeSword", 7),
             HTBM + "1B0F7F": ("WeapTypeBow", 7), HTBM + "16F16A": ("WeapTypeDagger", 4)}
    for k, (typ, dmg) in gifts.items():
        it = {"key": k, "sig": "WEAP", "keywords": [typ], "damage": dmg}
        assert split.item_tier(it)[0] == "T1" and split.ladder_override(it) is None, k


def test_the_ladder_holds_one_tier_per_material_but_for_the_written_exceptions():
    tiers = {m: r["ladder_tier"] for m, r in split.materials()["materials"].items()}
    exc = {r["item"] for r in split.item_materials()["gear"].values() if r.get("tier")}
    items = {i["id"]: i for i in json.loads((STOCK / "items.json").read_text())["items"]}
    off = [(k, i["stock_tier_id"]) for k, i in items.items() if k in split.item_materials()["gear"] and k not in exc
           and i["stock_tier_id"] != tiers[i["material_id"]]]
    assert off == []
    assert all(r["why"] for r in split.item_materials()["gear"].values() if r.get("tier"))


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
    bad = reach.audit(w, "outpost-m13-m65", reach.load_source("outpost-m13-m65"))
    assert {b["material"] for b in bad} == {"imperial"} and len(bad) == 5


def test_a_denied_mention_in_the_record_is_no_reason(w):
    text = [("place_note.present", "Helstrom is the least Imperialised city."), ("place_note.history", "No imperial legion took it.")]
    assert reach.says(r"\b(imperial|legion)\b", text) is None


def test_the_region_and_the_place_class_flag_what_they_hold_none_of(w):
    doc = {"possessions": [{"person": "x", "items": [{"item": "Skyrim.esm:013ED9", "count": 1}]}]}   # Imperial cuirass
    bad = reach.audit(w, "helstrom", doc)
    assert bad and bad[0]["rule"] in ("material reach", "region")
    camp = reach.audit(w, "tribal-camp-m2-m68", reach.load_source("tribal-camp-m2-m68"))
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


def test_a_smith_sells_the_ingredients_its_place_and_region_make(w):
    from tools.places.stock.derive import smithing_wares
    rid = w.get("place", "helstrom").region_id
    got = {r["item"]: r for r in smithing_wares(w, "helstrom", rid, "trader-blacksmith")}
    assert got[HTBM + "81A1F3"]["count"] == 5 and "made here" in got[HTBM + "81A1F3"]["why"]   # bog iron: ironwork
    assert got["Skyrim.esm:0800E4"]["count"] == 6                                              # leather strips
    general = {r["item"] for r in smithing_wares(w, "helstrom", rid, "trader-general")}
    assert HTBM + "81A1F3" not in general and "Skyrim.esm:0800E4" in general
    assert smithing_wares(w, "helstrom", rid, "trader-apothecary") == []


def test_the_ladder_table_in_the_doc_is_the_data_s():
    from tools.newworld import stockdb
    s = stockdb.LADDER_DOC.read_text()
    block = s[s.index(stockdb.LADDER_MARK[0]) + len(stockdb.LADDER_MARK[0]) + 1: s.index(stockdb.LADDER_MARK[1])]
    assert block.strip() == stockdb.ladder_table().strip(), "run python3 -m tools.newworld.stockdb ladder"


def test_the_world_build_gets_every_ladder_item_its_overrides_and_its_recipes():
    from tools.newworld.world import smithing
    doc = smithing.records()
    assert len(doc["items"]) == len(split.item_materials()["gear"])
    assert all(o["power"] != o["was"]["power"] for o in doc["overrides"])
    assert HTBM + "16F16D" not in {o["item"] for o in doc["overrides"]}        # the iron-level macana stands
    assert all(r["bench"] in ("CraftingSmithingForge", "CraftingSmithingSharpeningWheel", "CraftingSmithingArmorTable")
               for r in doc["recipes"])
    assert [n["edid"] for n in doc["new_items"]] == ["ANW_Flint"]
