"""L1: the item records of Argonia.esm (1.3 §c) take every field from their imported rows; the seven armour slots,
the class keyword to skill map and the container's lock and owner are the db's. FormKeys come from a frozen copy of
the real allocator's table, so nothing here allocates."""
from __future__ import annotations

import pytest

from tools.argonia_world import db, items_records as ir
from tools.argonia_world import skyrim_units as su
from tools.argonia_world.formids import Allocator

SLOTS = {"helm": 30, "cuirass": 32, "pauldrons": 57, "greaves": 53, "boots": 37, "gauntlets": 33, "shield": 39}
CLASSES = {"shortBlade", "longBlade", "axe", "blunt", "spear", "marksman", "handToHand"}


@pytest.fixture(scope="module")
def world():
    return db.open()


@pytest.fixture(scope="module")
def alloc(world):
    return Allocator(world, frozen=True)


def by_type(recs):
    out = {}
    for r in recs:
        out.setdefault(r["type"], []).append(r)
    return out


@pytest.fixture(scope="module")
def recs(world, alloc):
    return by_type(ir.layer(alloc, world).records)


def test_keyword_maps_every_class_to_its_skill(world, alloc, recs):
    classes = world.rows("weapon_class")
    assert {c.id for c in classes} == CLASSES
    assert {c.skill for c in classes} == CLASSES  # Morrowind's class skills share the class id
    for c in classes:
        assert world.get("skill", c.skill) is not None
    kw = {k["edid"]: k["formKey"] for k in recs["KYWD"]}
    assert set(kw) == {c.keyword_edid for c in classes}
    assert len(set(kw.values())) == len(kw)


def test_every_mapped_subkind_names_a_real_class(world):
    for s in world.rows("weapon_class_subkind"):
        assert world.get("weapon_class", s.weapon_class_id) is not None
    kinds = {r.subkind for r in world.rows("item", kind="weapon")}
    assert world.get("weapon_class_subkind", "straightSword").weapon_class_id == "longBlade"
    assert kinds >= {"straightSword"}


def test_sword_comes_from_its_row_and_carries_the_long_blade_keyword(world, alloc, recs):
    [w] = recs["WEAP"]
    it = world.get("item", ir.SWORD)
    assert it.subkind == "straightSword"
    assert (w["name"], w["value"], w["weight"]) == (it.name, it.value, su.kg_to_weight(it.weight_kg))
    lb = world.get("weapon_class", "longBlade")
    assert w["keywords"] == [alloc.form_key(lb.keyword_edid)]
    assert world.get("skill", lb.skill).id == "longBlade"
    assert w["animation"] == "OneHandSword"
    assert w["equipSlot"] == su.EQUIP_EITHER_HAND  # none crashed the Container Menu (game-8)
    assert w["model"].endswith("steel-sword.nif") and "/" not in w["model"]


def test_armour_set_is_seven_pairs_in_the_morrowind_slots(world, recs):
    assert {s.id: s.biped_slot for s in world.rows("armour_slot")} == SLOTS
    armo, arma = recs["ARMO"], recs["ARMA"]
    assert len(armo) == len(arma) == 7
    assert sorted(a["biped"] for a in armo) == sorted(su.biped_mask(n) for n in SLOTS.values())
    addons = {a["formKey"]: a for a in arma}
    st = world.get("item_set", ir.ARMOUR_SET)
    for a in armo:
        [ad] = [addons[k] for k in a["armatures"]]
        assert ad["biped"] == a["biped"] and ad["race"] == su.DEFAULT_RACE
        assert a["armorType"] == su.ARMOR_TYPE[st.armour_class]
    real = {r.name: r for r in world.rows("item", set=ir.ARMOUR_SET, kind="armour")}
    for slot in world.rows("armour_slot"):
        m = [a for a in armo if a["biped"] == su.biped_mask(slot.biped_slot)]
        assert len(m) == 1
        if not slot.stand_in:
            assert m[0]["name"] in real
            row = real[m[0]["name"]]
            assert (m[0]["value"], m[0]["weight"]) == (row.value, su.kg_to_weight(row.weight_kg))
        else:
            assert m[0]["name"] == f"{st.name} {slot.label}"  # named from the set; stats from the nearest row


def test_container_takes_lock_and_owner_from_its_rows(world, recs):
    [c] = recs["CONT"]
    p = ir.container_placement(world)
    lk = world.get("lock", ir.CONTAINER_LOCK)
    assert (p["level"], p["class"], p["key"]) == (lk.level, lk.class_, lk.key)
    assert (p["ownerKind"], p["ownerId"]) == (lk.owner_kind, lk.owner_id)
    sock = world.query('SELECT * FROM socket WHERE "lock" = ?', lk.id)[0]
    assert p["socket"] == sock["id"] and p["containerClass"] == sock["container_class"]
    assert c["name"].lower() == sock["container_class"]


def test_book_text_is_its_documents_leaves(world, recs):
    [b] = recs["BOOK"]
    doc = world.get("document", ir.BOOK_DOCUMENT)
    pages = [r.value for r in world.rows("document_leaf", document_id=doc.id)]
    assert [p.replace(ir.EOL, "\n") for p in b["text"].split(ir.PAGEBREAK)] == pages
    assert b["name"] == doc.name and b["value"] == world.get("item", doc.item).value


def test_book_carries_its_inventory_art(recs):
    [b] = recs["BOOK"]
    art = {r["formKey"]: r for r in recs["STAT"]}[b["inventoryArt"]]
    assert b["model"] and art["model"] == b["model"]


def test_every_generated_book_has_inventory_art_and_model():
    """L1 over the committed plugin: every BOOK names a STAT of the plugin as InventoryArt and has a model."""
    from pathlib import Path
    root = Path(__file__).resolve().parents[3] / "plugin" / "Argonia"
    stats = {p.name.rsplit(" - ", 1)[1].removesuffix(".yaml").replace("_", ":", 1) for p in (root / "Statics").glob("*.yaml")}
    books = sorted((root / "Books").glob("*.yaml"))
    assert books
    for p in books:
        t = p.read_text()
        art = next((ln.split(":", 1)[1].strip() for ln in t.splitlines() if ln.startswith("InventoryArt:")), None)
        assert art in stats and "\nModel:\n  File: " in "\n" + t, p.name


def test_potion_effect_is_the_rows_effect(world, recs):
    [p] = recs["ALCH"]
    rows = world.rows("item_effect", item_id=ir.POTION)
    assert len(p["effects"]) == len(rows) == 1
    m = world.get("effect_skyrim_mgef", rows[0].effect_id)
    assert p["effects"][0] == {"effect": f"{m.form_id:06X}:{m.plugin}", "magnitude": rows[0].magnitude, "area": 0,
                               "duration": round(rows[0].duration_seconds)}


def test_biped_mask_rejects_out_of_range():
    assert su.biped_mask(30) == 1 and su.biped_mask(61) == 1 << 31
    with pytest.raises(ValueError):
        su.biped_mask(29)
