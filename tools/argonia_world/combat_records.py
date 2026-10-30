"""The combat records of Argonia.esm (lane 1.6-wiring; docs/research/2026-10-30/combat-wiring.md), from the world
database's combat tables through db.py:

- (The GMSTs are `game_setting` rows with a `game_setting_combat` route; life_records.py writes every GMST.)
- PERK `ARG_Perk_Carriers`: one entry per wired `combat_carrier` row, Multiply 1 + Actor Value Mult on the
  carrier's actor value (native map P1). ArgoniaCore writes factor - 1 into each value and gives the player the
  perk; an unwritten carrier is 0, so the entry is neutral.
- Per `combat_archetype` row (native map P5, compiled from the band and position, never from player state): one
  PERK (light hit over listed damage on ModAttackDamage; 1 - mitigation of the reference blow on ModIncomingDamage),
  one ECZN with min = max = the band's level (soul contract C14), and the NPC_ (fixed level, health offset from the
  race's starting health, the weapon and shield, the face template's traits; decision 0014 §3).

Every number comes from a row; the formulas are the sheet's (76 §121.1, §121.4, §128). ArgoniaGen makes no choices.
"""
from __future__ import annotations

import json

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.formids import Allocator
from tools.argonia_world.intermediate import QUARANTINE, Layer

CARRIER_PERK = "ARG_Perk_Carriers"


def lerp(lo: float, hi: float, t: float) -> float:
    return lo + (hi - lo) * t


def mitigation(world, ar: float, blow: float) -> float:
    """76 §121.4: AR / (AR + constant + coefficient x blow), the constants the core's own table holds."""
    k = {r.id: r.value for r in world.rows("core_constant")}
    return ar / (ar + k["mitigation_constant"] + k["mitigation_damage_coefficient"] * blow)


def constant(world, cid: str) -> float:
    return world.get("combat_constant", cid).value


def listed_damage(world, item_id: str, heavy: bool = False) -> float:
    """76 §121.1: motion(class, attack) x the set's damage scale x the damage unit."""
    it = world.get("item", item_id)
    sub = world.get("weapon_class_subkind", it.subkind)
    cls = world.get("weapon_class_combat", sub.weapon_class_id)
    if cls is None:
        raise ValueError(f"{item_id}: weapon class {sub.weapon_class_id} has no weapon_class_combat row")
    scale = world.get("item_set", it.set).damage_scale if it.set else 1.0
    return (cls.motion_heavy if heavy else cls.motion_light) * scale * constant(world, "damage_unit")


def compiled(world, npc_id: str) -> dict:
    """The archetype's absolutes from its statblock band and position (76 §128)."""
    sb = world.get("npc_statblock", npc_id)
    band = world.get("danger_band_combat", sb.band)
    if band is None:
        raise ValueError(f"{npc_id}: band {sb.band} has no danger_band_combat row")
    arch = world.get("combat_archetype", npc_id)
    t = sb.position
    health = lerp(band.health_lo, band.health_hi, t)
    hit = lerp(band.light_hit_lo, band.light_hit_hi, t)
    ar = lerp(band.ar_lo, band.ar_hi, t)
    listed = listed_damage(world, arch.weapon)
    return {"band": sb.band, "position": t, "level": band.level, "health": health, "light_hit": hit, "ar": ar,
            "damage_mult": hit / listed, "incoming_mult": 1.0 - mitigation(world, ar, constant(world, "reference_blow")),
            "health_offset": round(health - constant(world, "race_start_health"))}


def _slug(s: str) -> str:
    return "".join(p.capitalize() for p in s.replace(".", "-").split("-"))


def carrier_perk(alloc: Allocator, world) -> dict:
    effects = []
    for c in world.rows("combat_carrier"):
        if not c.wired:
            continue
        e = {"entryPoint": c.entry_point, "function": "MultiplyOnePlusAVMult", "actorValue": c.actor_value,
             "value": 1.0, "rank": 0, "priority": 0, "tabCount": su.PERK_ENTRY_TABS[c.entry_point], "conditions": []}
        if c.condition_keyword:
            e["conditions"] = [{"tab": c.condition_tab, "function": "HasKeyword", "keyword": c.condition_keyword,
                                "op": "EqualTo", "value": 1}]
        effects.append(e)
    return {"type": "PERK", "edid": CARRIER_PERK, "formKey": alloc.form_key(CARRIER_PERK, "PERK", "combat.carriers"),
            "hidden": True, "playable": False, "trait": False, "level": 0, "ranks": 1, "name": "", "description": "",
            "effects": effects}


def _studio_class(alloc: Allocator) -> str:
    cls = json.loads((QUARANTINE / "start.json").read_text(encoding="utf-8"))["studio"]["class"]
    edid = f"ARG_Class_{cls.replace('-', '_')}"
    return alloc.form_key(edid, "CLAS", f"class.{cls}")


def archetype_records(alloc: Allocator, world, npc_id: str) -> list[dict]:
    from tools.argonia_world import items_records
    arch = world.get("combat_archetype", npc_id)
    npc = world.get("npc", npc_id)
    c = compiled(world, npc_id)
    base = _slug(npc_id.rsplit(".", 1)[1])
    perk_edid, ecz_edid, npc_edid = f"ARG_Perk_Arch_{base}", f"ARG_Ecz_{base}", f"ARG_Npc_{base}"
    perk = {"type": "PERK", "edid": perk_edid, "formKey": alloc.form_key(perk_edid, "PERK", f"{npc_id}#perk"),
            "hidden": True, "playable": False, "trait": False, "level": 0, "ranks": 1, "name": "", "description": "",
            "effects": [
                {"entryPoint": "ModAttackDamage", "function": "MultiplyValue", "value": round(c["damage_mult"], 6),
                 "rank": 0, "priority": 0, "tabCount": su.PERK_ENTRY_TABS["ModAttackDamage"], "conditions": []},
                {"entryPoint": "ModIncomingDamage", "function": "MultiplyValue", "value": round(c["incoming_mult"], 6),
                 "rank": 0, "priority": 0, "tabCount": su.PERK_ENTRY_TABS["ModIncomingDamage"], "conditions": []},
            ]}
    ecz = {"type": "ECZN", "edid": ecz_edid, "formKey": alloc.form_key(ecz_edid, "ECZN", f"{npc_id}#zone"),
           "minLevel": c["level"], "maxLevel": c["level"]}
    weapon = items_records.weapon_record(alloc, world, arch.weapon)["formKey"]
    items = [weapon]
    if arch.shield:
        it = world.get("item", arch.shield)
        slot = next(sl for sl in world.rows("armour_slot") if sl.subkind == it.subkind and not sl.stand_in)
        edid = f"ARG_Armo_{items_records.slug(it.set)}_{items_records.slug(slot.id)}"
        shield = next(r for r in items_records.armour_set_records(alloc, world, it.set) if r["edid"] == edid)
        items.append(shield["formKey"])
    ffa = world.get("npc_fight_flee_alarm", npc_id)
    rec = {"type": "NPC_", "edid": npc_edid, "formKey": alloc.form_key(npc_edid, "NPC_", npc_id), "name": npc.name,
           "race": arch.race_form, "template": arch.face_template, "templateFlags": ["Traits"],
           "class": _studio_class(alloc), "female": npc.sex == "female", "level": c["level"],
           "healthOffset": c["health_offset"], "aggression": "VeryAggressive" if ffa and ffa.fight >= 100 else "Aggressive",
           "confidence": "Foolhardy" if ffa and ffa.flee == 0 else "Average",
           "height": su.NPC_DEFAULT_HEIGHT, "weight": su.NPC_DEFAULT_WEIGHT, "perks": [perk["formKey"]], "items": [{"item": i, "count": 1} for i in items]}
    return [perk, ecz, rec]


def layer(alloc: Allocator, world) -> Layer:
    recs = [carrier_perk(alloc, world)]
    for a in world.rows("combat_archetype"):
        recs += archetype_records(alloc, world, a.npc_id)
    return Layer("base:combat", recs)
