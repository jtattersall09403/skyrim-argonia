"""The item records of Argonia.esm (1.3 §c; 2.3 §a rules), built from the imported `item` rows through db.py:
the straight-sword class (WEAP + its class KYWD), one armour set as ARMO + ARMA pairs in the Morrowind slots, one
container (CONT), one book (BOOK) and one potion (ALCH). Every field is a row's: the item, its set, its lock, its
document leaves, its effect rows; the class keyword to skill map and the slot numbers are the `weapon_class` and
`armour_slot` tables. Nothing here is a combat number: damage, armour rating and condition are ArgoniaCore's.

A mesh path is the row's asset data: a vanilla `meshes/` path as it stands (the base game's file, never shipped,
decision 0003), or, for a sourced model built by the asset pipeline, `Argonia\\<path under files/>.nif` (the
installer makes the .nif on the player's machine, decision 0014).
"""
from __future__ import annotations

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.formids import Allocator
from tools.argonia_world.intermediate import Layer

SWORD = "item.steel-sword"  # straightSword, the steel set (canon status), the set the armour is taken from too
ARMOUR_SET = "steel"
CONTAINER_LOCK = "lock.opening-work-camp.guard-stores"  # its socket names the container class and the owner
BOOK_DOCUMENT = "document.the-three-mournings"  # authored lore text (its document rows), not a plugin's
POTION = "item.healing-draught"
EOL = "\r\n"  # Skyrim book text lines end CRLF (and the plugin YAML round trip keeps only that form)
PAGEBREAK = f"{EOL}[pagebreak]{EOL}"
MESH_ROOT = "Argonia"


def slug(s: str) -> str:
    return "".join(p.capitalize() for p in s.replace("-", ".").replace("_", ".").split("."))


def model_path(row) -> str:
    """The record's mesh path from the row's asset data (``asset_availability_via``)."""
    via = row.asset_availability_via
    if via.startswith("meshes/"):
        path = via[len("meshes/"):]
    elif "/files/" in via and via.endswith(".glb"):
        path = f"{MESH_ROOT}/{via.split('/files/', 1)[1][:-4]}.nif"
    else:
        raise ValueError(f"{row.id}: no mesh path in its asset data ({via!r})")
    return path.replace("/", "\\")


def _item(world, item_id: str):
    r = world.get("item", item_id)
    if r is None:
        raise ValueError(f"{item_id}: not in the item table")
    return r


def class_keywords(alloc: Allocator, world) -> list[dict]:
    return [{"type": "KYWD", "edid": c.keyword_edid, "formKey": alloc.form_key(c.keyword_edid, "KYWD", f"weapon_class.{c.id}")}
            for c in world.rows("weapon_class")]


def weapon_record(alloc: Allocator, world, item_id: str = SWORD) -> dict:
    it = _item(world, item_id)
    if it.kind != "weapon":
        raise ValueError(f"{item_id}: not a weapon")
    sub = world.get("weapon_class_subkind", it.subkind)
    if sub is None or not sub.animation:
        raise ValueError(f"{item_id}: subkind {it.subkind} has no weapon class or animation type yet")
    cls = world.get("weapon_class", sub.weapon_class_id)
    edid = f"ARG_Weap_{slug(it.id[5:])}"
    return {"type": "WEAP", "edid": edid, "formKey": alloc.form_key(edid, "WEAP", it.id), "name": it.name,
            "model": model_path(it), "weight": su.kg_to_weight(it.weight_kg), "value": it.value,
            "keywords": [alloc.form_key(cls.keyword_edid)], "animation": sub.animation,
            "speed": su.WEAP_NEUTRAL_SPEED, "reach": su.WEAP_NEUTRAL_REACH}


def armour_set_records(alloc: Allocator, world, set_id: str = ARMOUR_SET) -> list[dict]:
    """ARMO + ARMA per slot of `armour_slot`. A slot whose piece the import lacks (`stand_in`) is written from the
    nearest piece's row (its weight, value and mesh) and named from the set; nothing is invented."""
    st = world.get("item_set", set_id)
    atype = su.ARMOR_TYPE.get(st.armour_class or "")
    if atype is None:
        raise ValueError(f"set {set_id}: armour class {st.armour_class!r} has no engine armour type")
    out: list[dict] = []
    for slot in world.rows("armour_slot"):
        pieces = [r for r in world.rows("item", set=set_id) if r.kind == "armour" and r.subkind == slot.subkind]
        if len(pieces) != 1:
            raise ValueError(f"set {set_id}: no {slot.subkind} row for slot {slot.id}")
        it = pieces[0]
        name = f"{st.name} {slot.label}" if slot.stand_in else it.name
        base = f"{slug(set_id)}_{slug(slot.id)}"
        mask = su.biped_mask(slot.biped_slot)
        arma_edid, armo_edid = f"ARG_Arma_{base}", f"ARG_Armo_{base}"
        key = f"{it.id}#{slot.id}"
        arma = alloc.form_key(arma_edid, "ARMA", key)
        out.append({"type": "ARMA", "edid": arma_edid, "formKey": arma, "biped": mask, "race": su.DEFAULT_RACE,
                    "maleModel": model_path(it)})
        out.append({"type": "ARMO", "edid": armo_edid, "formKey": alloc.form_key(armo_edid, "ARMO", key), "name": name,
                    "weight": su.kg_to_weight(it.weight_kg), "value": it.value, "biped": mask, "armorType": atype,
                    "armatures": [arma]})
    return out


def container_placement(world, lock_id: str = CONTAINER_LOCK) -> dict:
    """The lock and owner a placed reference of the container takes (XLOC, XOWN are reference data in Skyrim, not
    base-record data: the place layer applies them where it places the container)."""
    lk = world.get("lock", lock_id)
    sock = next((s for s in world.query('SELECT * FROM socket WHERE "lock" = ?', lock_id)), None)
    if lk is None or sock is None:
        raise ValueError(f"{lock_id}: no lock row or no socket holding it")
    return {"lock": lk.id, "level": lk.level, "class": lk.class_, "key": lk.key, "trap": lk.trap,
            "ownerKind": lk.owner_kind, "ownerId": lk.owner_id, "socket": sock["id"],
            "containerClass": sock["container_class"]}


def container_record(alloc: Allocator, world, lock_id: str = CONTAINER_LOCK) -> dict:
    p = container_placement(world, lock_id)
    edid = f"ARG_Cont_{slug(lock_id[5:])}"
    return {"type": "CONT", "edid": edid, "formKey": alloc.form_key(edid, "CONT", lock_id),
            "name": p["containerClass"].replace("-", " ").title(), "weight": 0.0, "flags": []}


def book_record(alloc: Allocator, world, doc_id: str = BOOK_DOCUMENT) -> dict:
    doc = world.get("document", doc_id)
    it = _item(world, doc.item)
    pages = [r.value for r in world.rows("document_leaf", document_id=doc_id)]
    if not pages:
        raise ValueError(f"{doc_id}: no leaves")
    edid = f"ARG_Book_{slug(it.id[5:])}"
    return {"type": "BOOK", "edid": edid, "formKey": alloc.form_key(edid, "BOOK", doc_id), "name": doc.name,
            "text": PAGEBREAK.join(p.replace("\n", EOL) for p in pages), "model": model_path(it), "weight": su.kg_to_weight(it.weight_kg),
            "value": it.value}


def potion_record(alloc: Allocator, world, item_id: str = POTION) -> dict:
    it = _item(world, item_id)
    effects = []
    for e in world.rows("item_effect", item_id=item_id):
        m = world.get("effect_skyrim_mgef", e.value or e.effect_id)
        if m is None:
            raise ValueError(f"{item_id}: effect {e.value or e.effect_id!r} has no master record in effect_skyrim_mgef")
        effects.append({"effect": f"{m.form_id:06X}:{m.plugin}", "magnitude": e.magnitude, "area": 0,
                        "duration": int(round(e.duration_seconds or 0))})
    if not effects:
        raise ValueError(f"{item_id}: no effects")
    edid = f"ARG_Alch_{slug(it.id[5:])}"
    return {"type": "ALCH", "edid": edid, "formKey": alloc.form_key(edid, "ALCH", it.id), "name": it.name,
            "model": model_path(it), "weight": su.kg_to_weight(it.weight_kg), "value": it.value, "effects": effects}


def layer(alloc: Allocator, world) -> Layer:
    recs = class_keywords(alloc, world) + [weapon_record(alloc, world)] + armour_set_records(alloc, world)
    recs += [container_record(alloc, world), book_record(alloc, world), potion_record(alloc, world)]
    return Layer("base:items", recs)
