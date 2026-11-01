"""The item records of Argonia.esm (1.3 §c; 2.3 §a rules), built from the imported `item` rows through db.py:
the straight-sword class (WEAP + its class KYWD), one armour set as ARMO + ARMA pairs in the Morrowind slots, one
container (CONT), one book (BOOK) and one potion (ALCH). Every field is a row's: the item, its set, its lock, its
document leaves, its effect rows; the class keyword to skill map and the slot numbers are the `weapon_class` and
`armour_slot` tables. The one combat number is a weapon's listed damage (76 §121.1, `combat_records.listed_damage`,
lane 1.6-wiring); armour rating stays 0 (mitigation is the carrier's) and condition is ArgoniaCore's.

An item's look is the row's asset data: a vanilla `meshes/` path as it stands (the base game's file, never shipped,
decision 0003), or, for a row whose model was the old project's `.glb` (no installer step makes those into meshes and
we make no art, decision 0006), the base-game record its `value_from` names: ArgoniaGen copies that record's meshes,
first-person model, armatures and sounds (`template`). An `Argonia\\...nif` path to a file nothing makes left the
1.12 sword and its inventory icon invisible (owner look 1).

The starting kit is start.json's `player.kit` (item rows); its weapons, ammunition and armour are written here and
the Player override carries them (`kit_entries`).
"""
from __future__ import annotations

import re

from tools.argonia_world import combat_records
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


def slug(s: str) -> str:
    return "".join(p.capitalize() for p in s.replace("-", ".").replace("_", ".").split("."))


def template(world, row, seen=()) -> str | None:
    """The base-game record (``Skyrim.esm:<EditorID>``) whose look the row wears: its ``value_from`` as
    ``<plugin>:<EditorID>``, an analogue's last ``~<set>:<EditorID>``, or a premium item's own row's."""
    v = row.value_from or ""
    if v.startswith("premium:"):
        base = world.get("item", v.rsplit(":", 1)[1])
        return template(world, base, seen + (row.id,)) if base is not None and base.id not in seen else None
    if v.startswith("analogue:"):
        return f"Skyrim.esm:{v.rsplit(':', 1)[1]}"
    if re.fullmatch(r"[\w ]+\.es[mpl]:\w+", v):
        return v
    return None


def model_path(row) -> str:
    """The record's vanilla mesh path from the row's asset data (``asset_availability_via``)."""
    via = row.asset_availability_via or ""
    if not via.startswith("meshes/"):
        raise ValueError(f"{row.id}: no mesh path in its asset data ({via!r})")
    return via[len("meshes/"):].replace("/", "\\")


def look(world, row) -> dict:
    """``{"model": path}`` for a row with a vanilla mesh, else ``{"template": record}`` (see the module's note)."""
    if (row.asset_availability_via or "").startswith("meshes/"):
        return {"model": model_path(row)}
    t = template(world, row)
    if t is None:
        raise ValueError(f"{row.id}: no mesh and no base-game record to take its look from ({row.value_from!r})")
    return {"template": t}


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
    if it.subkind == "arrow":
        raise ValueError(f"{item_id}: an arrow is ammunition (ammo_record)")
    if sub is None or not sub.animation:
        raise ValueError(f"{item_id}: subkind {it.subkind} has no weapon class or animation type yet")
    cls = world.get("weapon_class", sub.weapon_class_id)
    edid = f"ARG_Weap_{slug(it.id[5:])}"
    return {"type": "WEAP", "edid": edid, "formKey": alloc.form_key(edid, "WEAP", it.id), "name": it.name,
            **look(world, it), "weight": su.kg_to_weight(it.weight_kg), "value": it.value,
            "keywords": [alloc.form_key(cls.keyword_edid)], "animation": sub.animation,
            "equipSlot": su.weapon_equip_slot(sub.animation),
            "speed": su.WEAP_NEUTRAL_SPEED, "reach": su.WEAP_NEUTRAL_REACH,
            **_damage(world, item_id)}


def _damage(world, item_id: str) -> dict:
    """The listed damage (76 §121.1) where the weapon's class has its combat numbers; else none is written and
    ArgoniaGen keeps the template record's (the class's motion values are owed, 2.7 §b; nothing is guessed here)."""
    it = world.get("item", item_id)
    sub = world.get("weapon_class_subkind", it.subkind)
    if world.get("weapon_class_combat", sub.weapon_class_id) is None:
        return {}
    return {"damage": round(combat_records.listed_damage(world, item_id))}


def armour_set_records(alloc: Allocator, world, set_id: str = ARMOUR_SET, partial: frozenset = frozenset()) -> list[dict]:
    """ARMO + ARMA per slot of `armour_slot`. A slot whose piece the import lacks (`stand_in`) is written from the
    nearest piece's row (its weight, value and mesh) and named from the set; nothing is invented. ``partial``
    (a kit's item ids): only those pieces, no stand-ins."""
    st = world.get("item_set", set_id)
    atype = su.ARMOR_TYPE.get(st.armour_class or "")
    if atype is None and not partial:  # a kit's medium set (no engine type) keeps its base records' types
        raise ValueError(f"set {set_id}: armour class {st.armour_class!r} has no engine armour type")
    out: list[dict] = []
    for slot in world.rows("armour_slot"):
        pieces = [r for r in world.rows("item", set=set_id) if r.kind == "armour" and r.subkind == slot.subkind]
        if partial:
            pieces = [r for r in pieces if r.id in partial]
            if slot.stand_in or not pieces:
                continue
        if len(pieces) != 1:
            raise ValueError(f"set {set_id}: no {slot.subkind} row for slot {slot.id}")
        it = pieces[0]
        name = f"{st.name} {slot.label}" if slot.stand_in else it.name
        base = f"{slug(set_id)}_{slug(slot.id)}"
        mask = su.biped_mask(slot.biped_slot)
        arma_edid, armo_edid = f"ARG_Arma_{base}", f"ARG_Armo_{base}"
        key = f"{it.id}#{slot.id}"
        armo = {"type": "ARMO", "edid": armo_edid, "formKey": alloc.form_key(armo_edid, "ARMO", key), "name": name,
                "weight": su.kg_to_weight(it.weight_kg), "value": it.value, "biped": mask, "armorType": atype,
                "armatures": []}
        lk = look(world, it)
        if atype is None:
            if "template" not in lk:
                raise ValueError(f"set {set_id}: armour class {st.armour_class!r} has no engine armour type")
            del armo["armorType"]
        if slot.stand_in:
            pass  # no base-game piece fills a Morrowind-only slot: the piece is worn but shows nothing (never another slot's mesh)
        elif "template" in lk:
            armo["template"] = lk["template"]  # the base record's own armatures: every race it fits, first person too
        else:
            arma = alloc.form_key(arma_edid, "ARMA", key)
            out.append({"type": "ARMA", "edid": arma_edid, "formKey": arma, "biped": mask, "race": su.DEFAULT_RACE,
                        "maleModel": lk["model"]})
            armo["armatures"] = [arma]
        out.append(armo)
    return out


def ammo_record(alloc: Allocator, world, item_id: str) -> dict:
    """AMMO: an arrow row, its look, projectile and damage from its base-game record (``template``)."""
    it = _item(world, item_id)
    if it.subkind != "arrow":
        raise ValueError(f"{item_id}: not an arrow")
    edid = f"ARG_Ammo_{slug(it.id[5:])}"
    return {"type": "AMMO", "edid": edid, "formKey": alloc.form_key(edid, "AMMO", it.id), "name": it.name,
            **look(world, it), "weight": su.kg_to_weight(it.weight_kg), "value": it.value}


def kit_records(alloc: Allocator, world, kit) -> list[dict]:
    """The starting kit's weapon, ammunition and armour records (the steel sword and set are written already)."""
    out, sets = [], {}
    for k in kit:
        it = _item(world, k["item"])
        if it.kind == "weapon" and it.id != SWORD:
            out.append(ammo_record(alloc, world, it.id) if it.subkind == "arrow" else weapon_record(alloc, world, it.id))
        elif it.kind == "armour" and it.set != ARMOUR_SET:
            sets.setdefault(it.set, set()).add(it.id)
    for set_id, ids in sets.items():
        out += armour_set_records(alloc, world, set_id, partial=frozenset(ids))
    return out


def kit_edid(world, item_id: str) -> str:
    """The EditorID of a kit row's record (a weapon, an arrow or a set's armour piece)."""
    it = _item(world, item_id)
    if it.kind == "weapon":
        return f"ARG_{'Ammo' if it.subkind == 'arrow' else 'Weap'}_{slug(it.id[5:])}"
    if it.kind == "armour":
        slot = next(sl for sl in world.rows("armour_slot") if sl.subkind == it.subkind and not sl.stand_in)
        return f"ARG_Armo_{slug(it.set)}_{slug(slot.id)}"
    raise ValueError(f"start.json kit: {it.id} is a {it.kind}, not a weapon or armour")


def kit_entries(alloc: Allocator, world, kit) -> list[dict]:
    """The Player override's items: ``{"item": formKey, "count": n}`` per kit row, in kit order."""
    return [{"item": alloc.form_key(kit_edid(world, k["item"])), "count": int(k.get("count", 1))} for k in kit]


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
            "value": it.value, "inventoryArt": alloc.form_key(_art_edid(edid), "STAT", doc_id + "#inventory-art")}


def _art_edid(book_edid: str) -> str:
    return "ARG_BookArt_" + book_edid[len("ARG_Book_"):]


def book_records(alloc: Allocator, world, doc_id: str = BOOK_DOCUMENT) -> list[dict]:
    """The book and its inventory art: the STAT BookMenu draws as the open 3D book (a BOOK with no INAM crashes the
    menu, game-18: SkyrimSE+0EDC8C8). The art is the book's own mesh, as vanilla's inventory statics are."""
    b = book_record(alloc, world, doc_id)
    art = _art_edid(b["edid"])
    return [{"type": "STAT", "edid": art, "formKey": b["inventoryArt"], "model": b["model"]}, b]


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


def layer(alloc: Allocator, world, kit=()) -> Layer:
    recs = class_keywords(alloc, world) + [weapon_record(alloc, world)] + armour_set_records(alloc, world)
    recs += kit_records(alloc, world, kit)
    recs += [container_record(alloc, world), *book_records(alloc, world), potion_record(alloc, world)]
    return Layer("base:items", recs)
