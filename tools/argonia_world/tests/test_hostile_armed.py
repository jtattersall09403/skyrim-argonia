"""L1: every hostile NPC_ in the built plugin spawns armed (diag6 6: the deserter carried his sword and shield in Items,
unequipped, with no outfit or combat style). A hostile record that does not inherit its inventory from a template has a
default outfit holding one of our weapons, and a combat style."""
from pathlib import Path

import yaml

PLUGIN = Path(__file__).resolve().parents[3] / "plugin" / "Argonia"
HOSTILE = {"Aggressive", "VeryAggressive", "Frenzied"}


def _records(kind: str) -> dict[str, dict]:
    out = {}
    for f in sorted((PLUGIN / kind).glob("*.yaml")) if (PLUGIN / kind).is_dir() else []:
        r = yaml.safe_load(f.read_text(encoding="utf-8"))
        out[r["FormKey"]] = r
    return out


def hostile_unarmed(npcs: dict, outfits: dict, weapons: set) -> list[str]:
    bad = []
    for fk, n in npcs.items():
        if (n.get("AIData") or {}).get("Aggression") not in HOSTILE:
            continue
        if "Inventory" in ((n.get("Configuration") or {}).get("TemplateFlags") or []):
            continue  # a creature's kit is its template's
        o = outfits.get(n.get("DefaultOutfit"))
        if not o or not any(i in weapons for i in o.get("Items") or []):  # `weapons`: weapon lists, or weapons
            bad.append(f"{n.get('EditorID')} ({fk}): no default outfit with a weapon")
        if not n.get("CombatStyle"):
            bad.append(f"{n.get('EditorID')} ({fk}): no combat style")
    return bad


def test_every_hostile_npc_spawns_armed():
    npcs = _records("Npcs")
    assert npcs, "plugin/Argonia/Npcs is empty"
    weapons = set(_records("Weapons"))
    lists = {fk for fk, r in _records("LeveledItems").items()  # an OTFT carries its weapon in a levelled list
             if any(e["Data"]["Reference"] in weapons for e in r.get("Entries") or [])}
    assert hostile_unarmed(npcs, _records("Outfits"), weapons | lists) == []


def test_the_check_refuses_the_deserter_as_it_was():
    npc = {"EditorID": "ARG_Npc_AmbushDeserter", "AIData": {"Aggression": "VeryAggressive"},
           "Configuration": {"TemplateFlags": ["Traits"]}, "Items": [{"Item": {"Item": "000840:Argonia.esm"}}]}
    assert len(hostile_unarmed({"000858:Argonia.esm": npc}, {}, {"000840:Argonia.esm"})) == 2
