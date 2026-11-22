"""The items ladder (docs/design/items.md): our materials, the tier by power, the reach, region and trade-kit checks and
the expected mix, on the committed sources and the database built from them."""
from __future__ import annotations

import json
import re
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
    doc = {"possessions": [{"person": "x", "items": [{"item": "Here There Be Monsters - Curse of Cipactli.esp:012438", "count": 1}]}]}   # Legion cuirass (Imperial)
    bad = reach.audit(w, "outpost-m13-m65", doc)
    assert {b["material"] for b in bad} == {"imperial"} and len(bad) == 1


def test_a_denied_mention_in_the_record_is_no_reason(w):
    text = [("place_note.present", "Helstrom is the least Imperialised city."), ("place_note.history", "No imperial legion took it.")]
    assert reach.says(r"\b(imperial|legion)\b", text) is None


def test_the_region_and_the_place_class_flag_what_they_hold_none_of(w):
    doc = {"possessions": [{"person": "x", "items": [{"item": "Here There Be Monsters - Curse of Cipactli.esp:012438", "count": 1}]}]}   # Legion cuirass (Imperial)
    bad = reach.audit(w, "helstrom", doc)
    assert bad and bad[0]["rule"] in ("material reach", "region")
    iron = {"possessions": [{"person": "x", "items": [{"item": "King of the Murkmire.esp:57AA3E", "count": 1}]}]}   # a bog-iron dagger
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


def test_a_smith_sells_the_ingredients_its_place_and_region_make(w):
    from tools.places.stock.derive import smithing_wares
    rid = w.get("place", "helstrom").region_id
    got = {r["item"]: r for r in smithing_wares(w, "helstrom", rid, "trader-blacksmith")}
    assert got[HTBM + "81A1F3"]["count"] == 5 and "made here" in got[HTBM + "81A1F3"]["why"]   # bog iron: ironwork
    assert got["Skyrim.esm:0800E4"]["count"] == 6                                              # leather strips
    general = {r["item"] for r in smithing_wares(w, "helstrom", rid, "trader-general")}
    assert HTBM + "81A1F3" not in general and "Skyrim.esm:0800E4" in general
    assert smithing_wares(w, "helstrom", rid, "trader-apothecary") == []


STAFF = KOTM + "735249"     # SaxhleelStaffSoulTrap: a magic staff its record types as a sword


def test_a_magic_staff_typed_as_a_sword_is_misfiled_and_flagged_and_never_issued(w):
    staff = {"key": STAFF, "edid": "SaxhleelStaffSoulTrap", "sig": "WEAP", "keywords": ["WeapTypeSword"]}
    assert "magic staff" in split.misfiled(staff)
    assert split.misfiled({"key": HTBM + "1B0F87", "edid": "CIPHTBMBambooStaff1", "sig": "WEAP",
                           "keywords": ["WeapTypeWarhammer"]}) is None          # a quarterstaff is a weapon
    items = json.loads((STOCK / "items.json").read_text())["items"]
    assert [i["edid"] for i in items if split.misfiled(i)] == []      # no catalogue item is misfiled now


def test_a_t2_guard_s_sidearm_is_a_real_t2_marsh_weapon_never_a_staff():
    from tools.places.stock.derive import Picker, ladder_records
    pick = Picker(None, split.scale(), None, ladder_records())
    got = pick.gear("T2", "weapon", "WeapTypeSword")
    assert got["key"] != STAFF and split.material_of(got)[0] in ("saxhleel", "bog-iron", "kothringi-relic", "imperial")
    assert split.item_tier(got)[0] == "T2" and not split.misfiled(got)


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


# ---- the guard issue is a table of ours, decided by the place and never by what its source gave ----------------------

def _facts(kind, culture="jade", held_by=""):
    return {"kind": kind, "culture": culture, "region": "barsaebica", "held_by": held_by}


def test_the_guard_table_is_decided_by_kind_culture_holder_and_ceiling():
    g = split.guard_issue
    assert g(_facts("city", "forest-green"), "T4")["row"]["id"] == "argonian-scale" and g(_facts("city", "forest-green"), "T4")["tier"] == "T3"
    assert g(_facts("town"), "T3")["row"]["id"] == "argonian-scale"
    assert g(_facts("town"), "T2")["row"]["id"] == "saxhleel-issue"          # the ceiling stops short of the scale set
    assert g(_facts("village"), "T2")["row"]["id"] == "saxhleel-issue" and g(_facts("outpost"), "T3")["row"]["id"] == "saxhleel-issue"
    assert g(_facts("tribal-camp", None), "T1")["row"]["id"] == "tribal-hide"
    assert g(_facts("outpost", "stone-grey", "A Dunmer gang-master and his reed-cutters"), "T2")["row"]["id"] == "dunmer-holdout"
    assert g(_facts("fort", "crimson-red", "An Imperial garrison"), "T2")["row"]["id"] == "imperial-post"
    assert g(_facts("outpost", "crimson-red", "Archwardens keeping the old Imperial fort"), "T2")["row"]["id"] == "saxhleel-issue"
    assert g(_facts("lighthouse", None), "T1")["set"] is None and g(_facts("lighthouse", None), "T1")["tier"] == "T2"   # the plain issue
    assert g(_facts("city", "forest-green"), "T4")["torch"] == "Skyrim.esm:01D4EC"


def test_every_row_of_the_guard_table_names_pieces_the_ladder_files_and_is_in_the_database(w):
    items = {i.id for i in w.rows("item")}
    mats = {m.id for m in w.rows("material")}
    table = split.scale()["guard_issue"]["table"]
    assert [r.id for r in sorted(w.rows("guard_issue"), key=lambda r: r.ord)] == [r["id"] for r in table]
    for r in table:
        assert set(r.get("items", [])) <= items, r["id"]
        assert set(r.get("materials", []) + r.get("fallback", []) + r.get("weapon_materials", [])) <= mats, r["id"]
        assert r["id"] == "plain" or r.get("kinds") or r.get("holder_pattern") or r.get("regions"), r["id"]


def test_a_materials_row_dresses_a_guard_slot_by_slot_from_the_ladder_whatever_the_source_used():
    from tools.places.stock.derive import ARMOUR_SLOTS, Picker, ladder_records
    pick = Picker(ladder_records(), split.scale(), None, None)
    row = next(r for r in split.scale()["guard_issue"]["table"] if r["id"] == "saxhleel-issue")
    got = [pick.issue_piece(row["materials"] + row["fallback"], s, "T2") for s in ARMOUR_SLOTS]
    assert all(got) and {split.material_of(g)[0] for g in got} <= {"saxhleel", "leather", "hide"}
    assert any(split.material_of(g)[0] == "saxhleel" for g in got)
    hide = next(r for r in split.scale()["guard_issue"]["table"] if r["id"] == "tribal-hide")
    assert pick.issue_piece(hide["materials"], "ArmorCuirass", "T1")["edid"] == "ArmorHideCuirass"


def test_a_stock_row_naming_an_item_of_a_plugin_the_source_never_used_passes_and_is_read(w):
    from tools.places.stock.plan import plugins_of
    pid = "outpost-m6-m66"
    src = json.loads((STOCK.parents[2] / "newworld" / "places" / pid / "place.json").read_text())["source_id"]
    used = set()
    for ln in (STOCK.parents[2] / "newworld" / "places" / "sources.jsonl").read_text().splitlines():
        row = json.loads(ln) if ln.strip() else {}
        if row.get("source_id") == src:
            used = set(row.get("plugins", [])) | set(row.get("extra_refs_plugins", []))
    guard = next(p for p in w.rows("person", place_id=pid) if p.person_role_id == "guard")
    foreign = [i for i in w.rows("item") if i.plugin not in used and i.item_kind_id == "weapon" and i.material_id in ("flint", "bone", "wood")
               and not reach.audit(w, pid, {"possessions": [{"person": guard.id, "items": [{"item": i.id, "count": 1}]}]})]
    assert foreign, "a ladder weapon of a plugin the source never used stands in the stock check"
    assert foreign[0].plugin in plugins_of([foreign[0].id])


def test_the_guard_issue_is_checked_against_the_table_and_a_written_exception_passes(w):
    pid = "jal-veesa"                                      # a town: the scale set, unless a row carries the exception
    guard = next(p for p in w.rows("person", place_id=pid) if p.person_role_id == "guard")
    cuirass = "Here There Be Monsters - Curse of Cipactli.esp:073E7D"
    row = {"item": cuirass, "count": 1}
    bad = reach.audit(w, pid, {"possessions": [{"person": guard.id, "items": [row]}]})
    assert [b["rule"] for b in bad] == ["guard issue"]
    row["exception"] = "guard issue: kept as stocked, owner 2026-11-22"
    assert reach.audit(w, pid, {"possessions": [{"person": guard.id, "items": [row]}]}) == []
    assert reach.audit(w, pid, reach.load_source(pid)) == []   # the stocked levy keeps its plain issue by that exception


def test_no_rule_of_the_stock_reads_the_plugins_of_a_place_s_source():
    import inspect
    from tools.places.stock import derive, verify
    assert not hasattr(split, "source_plugins")
    assert "plugins" not in inspect.signature(split.guard_issue).parameters
    for mod in (split, reach, derive, verify):
        src = inspect.getsource(mod)
        assert "source_plugins" not in src and "p.plugins()" not in src, mod.__name__
    text = json.dumps(split.scale()["guard_issue"])
    assert '"plugin"' not in text and "source plugin" not in text.replace("No plugin of the place's source is read", "")


SIX = Path(__file__).parent / "data" / "stock_six_places_pin.json"


def test_the_six_act_i_places_read_exactly_as_before_the_ladder_was_widened(w):
    """The wider ladder is for places from here on (owner, 2026-11-22): the six Act I places' reach flags and gear mix
    are pinned as they stood before it (tools/tests/data/stock_six_places_pin.json)."""
    pin = json.loads(SIX.read_text())
    for p, want in pin.items():
        doc = reach.load_source(p)
        m = reach.mix(w, p, doc)
        got = {"flagged": sorted([b["rule"], b["holder"], b["item"]] for b in reach.flagged(w, p, doc)),
               "mix": {"by_material": m["by_material"], "targets": [[t["groups"], t["target"], t["pct"]] for t in m["targets"]]}}
        assert json.dumps(got, sort_keys=True) == json.dumps(want, sort_keys=True), p


def test_the_new_weapon_types_take_animated_armoury_s_stats_per_tier():
    table = split.power_table()
    want = {"pike": (11, 13, 16, 17, 19, 20), "halberd": (14, 16, 19, 20, 21, 23), "quarterstaff": (10, 11, 14, 15, 17, 16),
            "rapier": (5, 6, 9, 10, 11, 12), "whip": (7, 8, 11, 12, 13, 14), "claw": (5, 6, 9, 10, 11, 12)}
    for kind, powers in want.items():
        assert tuple(int(table[kind]["stats"][f"T{i + 1}"]["power"]) for i in range(6)) == powers, kind
    pike = {"key": "NewArmoury.esp:153BA6", "sig": "WEAP", "keywords": ["WeapMaterialIron", "WeapTypePike", "WeapTypeGreatsword"],
            "damage": 11}
    assert split.power_kind(pike) == "pike" and split.slot_of(pike) == "weapon"
    assert split.item_tier(pike)[0] == "T2" and split.ladder_override(pike)["power"] == 13.0   # bog iron: a steel pike's


def test_every_renamed_piece_has_a_black_marsh_name_and_none_keeps_a_skyrim_people_s():
    gear = split.item_materials()["gear"]
    named = {k: r["name"] for k, r in gear.items() if r.get("name")}
    assert len(named) >= 50
    assert not [n for n in named.values() if re.search(r"Forsworn|Falmer|Riekling|Grummite|Steel|Iron\b", n)]
    assert gear["ccBGSSSE025-AdvDSGS.esm:000BE0"]["name"] == "Hist Amber Sword"


def test_the_widened_ladder_fills_the_named_gaps():
    items = {i["id"]: i for i in json.loads((STOCK / "items.json").read_text())["items"]}
    gear = split.item_materials()["gear"]
    on = [(items[k]["stock_tier_id"], split.slot_of(items[k]), items[k]["power_kind"], r["material"])
          for k, r in gear.items() if k in items]
    assert sum(m == "chitin" for *_, m in on) >= 9
    assert {"T1", "T3"} <= {t for t, s, *_ in on if s == "heavy"}
    assert {"sword", "dagger", "mace", "waraxe", "bow"} <= {k for t, s, k, _ in on if t == "T5"}
    assert not [m for t, s, k, m in on if t == "T6" and s == "weapon"]                    # T6 weapons stay relics only
    assert {m for t, s, k, m in on if t == "T2" and s == "light"} - {"saxhleel"}


def test_crossbows_are_on_the_ladder():
    """Dawnguard's crossbow and bolts are itemised as crossbow work, with crossbow stats; the order's armour is not."""
    gear = {r["item"]: r for r in json.loads((STOCK / "item_material.json").read_text())["gear"]}
    assert gear["Dawnguard.esm:000801"]["material"] == "crossbow"
    assert gear["Dawnguard.esm:000BB3"]["material"] == "crossbow"
    assert not [k for k in gear if k.startswith("Dawnguard.esm:") and "armor" in (gear[k].get("why") or "").lower()]
    assert json.loads((STOCK / "power.json").read_text())["kinds"]["crossbow"]["stats"]["T2"]["power"] == 19.0


def test_every_culture_has_its_own_leaning(w):
    """Each culture.jsonl row has a tribe overlay with a signature weapon and look, and its Argonians take it."""
    kits = json.loads((STOCK / "kits.json").read_text())["overlays"]
    by = {c: o for o in kits for c in o.get("cultures", [])}
    cultures = [json.loads(l)["id"] for l in (STOCK.parents[1] / "story/data/db/culture.jsonl").read_text().splitlines() if l.strip()]
    assert sorted(by) == sorted(cultures)
    assert all(o["carry"] and o["wear"] and o["tell"].startswith("you can tell") for o in by.values())
    sigs = {(o["carry"][0]["typ"], o["carry"][0]["materials"][0], o["wear"][0]["materials"][0]) for o in by.values()}
    assert len(sigs) == len(by)          # no two tribes lean the same way
    person = next(p for p in w.rows("person") if p.race_id == "ArgonianRace")
    culture = w.get("place", person.place_id).culture_id
    if culture:
        assert any(k.cultures and culture in k.cultures.split() for k in reach.kits_for(w, person))
