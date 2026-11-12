"""Hostile people of the ecology stage: each lore group's looks and its kit by band tier, from records we hold.

    python -m tools.newworld.ecology.people            # (re)bind the groups SPEC names in bindings.json
    python -m tools.newworld.ecology.people --list     # what each group would get, writing nothing

A group's looks are whole existing NPC_ records of the races its lore names (never Nord, never a Nord voice
type, never a record that takes its face from a template's levelled list, never a unique person), of the
bandit factions so they are hostile; its kit is a flat set of Skyrim's own armour and weapons per band tier
(low D2, mid D3, high D4 and D5), what that people would own, its value rising with the tier. The stage draws
looks and kit flat (place.py); the world writer wears the armour as an outfit and gives the weapons.

Only the groups SPEC names are written; every other row of bindings.json (the Naga, the tribal Argonians, the
undead, every kind) stays as it is.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
from pathlib import Path

BINDINGS = Path(__file__).resolve().parents[3] / "newworld/sources/ecology/bindings.json"
PLUGINS = ["Skyrim.esm", "Dawnguard.esm", "Dragonborn.esm"]
HOSTILE_FACTION = re.compile(r"^(BanditFaction|DLC2BanditDialogueFaction)$")
REJECT_VOICE = re.compile(r"Nord|Child|Unique|Ghost|Elder|Dremora|Vampire", re.I)
REJECT_EDID = re.compile(r"Child|Ghost|Corpse|Vampire|Draugr|Dead|Prisoner|Template|Demo|Companion|Dummy", re.I)
NORDIC = re.compile(r"Nord|Fur|Stormcloak|Carved|Ancient|Forsworn|Falmer|Draugr|Skaal|Bear|Wolf", re.I)
RACE = {"argonian": "ArgonianRace", "dunmer": "DarkElfRace", "imperial": "ImperialRace", "khajiit": "KhajiitRace",
        "redguard": "RedguardRace", "orc": "OrcRace", "breton": "BretonRace", "bosmer": "WoodElfRace"}

ARMOUR = {   # a set's armour pieces, by editor id, all of Skyrim.esm unless the id starts DLC2 (Dragonborn.esm)
    "hide": ["ArmorHideCuirass", "ArmorHideBoots", "ArmorHideGauntlets", "ArmorHideHelmet"],
    "leather": ["ArmorLeatherCuirass", "ArmorLeatherBoots", "ArmorLeatherGauntlets", "ArmorLeatherHelmet"],
    "iron": ["ArmorIronCuirass", "ArmorIronBoots", "ArmorIronGauntlets", "ArmorIronHelmet"],
    "banded": ["ArmorIronBandedCuirass", "ArmorIronBoots", "ArmorIronGauntlets", "ArmorIronHelmet"],
    "studded": ["ArmorImperialStuddedCuirass", "ArmorLeatherBoots", "ArmorLeatherGauntlets"],
    "steel": ["ArmorSteelCuirassA", "ArmorSteelBootsA", "ArmorSteelGauntletsA", "ArmorSteelHelmetA"],
    "scaled": ["ArmorScaledCuirass", "ArmorScaledBoots", "ArmorScaledGauntlets", "ArmorScaledHelmet"],
    "plate": ["ArmorSteelPlateCuirass", "ArmorSteelPlateBoots", "ArmorSteelPlateGauntlets", "ArmorSteelPlateHelmet"],
    "imperial-light": ["ArmorImperialLightCuirass", "ArmorImperialLightBoots", "ArmorImperialLightGauntlets",
                       "ArmorImperialLightHelmet"],
    "imperial": ["ArmorImperialCuirass", "ArmorImperialBoots", "ArmorImperialGauntlets", "ArmorImperialHelmet"],
    "imperial-officer": ["ArmorImperialCuirass", "ArmorSteelPlateBoots", "ArmorSteelPlateGauntlets",
                         "ArmorSteelPlateHelmet"],
    "elven-light": ["ArmorElvenLightCuirass", "ArmorElvenLightBoots", "ArmorElvenLightGauntlets", "ArmorElvenLightHelmet"],
    "elven": ["ArmorElvenCuirass", "ArmorElvenBoots", "ArmorElvenGauntlets", "ArmorElvenHelmet"],
    "orcish": ["ArmorOrcishCuirass", "ArmorOrcishBoots", "ArmorOrcishGauntlets", "ArmorOrcishHelmet"],
    "chitin-light": ["DLC2ArmorChitinLightCuirass", "DLC2ArmorChitinLightBoots", "DLC2ArmorChitinLightGauntlets",
                     "DLC2ArmorChitinLightHelmet"],
    "chitin-heavy": ["DLC2ArmorChitinHeavyCuirass", "DLC2ArmorChitinHeavyBoots", "DLC2ArmorChitinHeavyGauntlets",
                     "DLC2ArmorChitinHeavyHelmet"],
    "bonemold": ["DLC2ArmorBonemoldCuirassVariant01", "DLC2ArmorBonemoldBoots", "DLC2ArmorBonemoldGauntlets",
                 "DLC2ArmorBonemoldHelmet"],
    "bonemold-improved": ["DLC2ArmorBonemoldImprovedCuirass", "DLC2ArmorBonemoldImprovedBoots",
                          "DLC2ArmorBonemoldImprovedGauntlets", "DLC2ArmorBonemoldImprovedHelmet",
                          "DLC2ArmorBonemoldImprovedShield"],
}
SHIELD = {"iron": "ArmorIronShield", "banded": "ArmorIronBandedShield", "steel": "ArmorSteelShield",
          "imperial": "ArmorImperialShield", "imperial-light": "ArmorImperialLightShield", "orcish": "ArmorOrcishShield",
          "elven": "ArmorElvenShield", "hide": "ArmorHideShield", "chitin-heavy": "DLC2ArmorChitinShield",
          "bonemold": "DLC2ArmorBonemoldShield"}
# A kit: (armour, weapons, ammo or None, shield?)  Weapons are what is in the hand: the tier rises low to high.
S = lambda a, w, ammo=None, sh=False: {"armour": a, "weapons": w, "ammo": ammo, "shield": sh}   # noqa: E731
KITS = {
    "outlaw": {   # bandits, raiders, convicts, prospectors: what outlaws scavenge, worn then better
        "low": [S("hide", ["IronSword"]), S("leather", ["IronWarAxe"]), S("iron", ["IronMace"], sh=True),
                S("hide", ["HuntingBow"], "IronArrow")],
        "mid": [S("steel", ["SteelSword"], sh=True), S("banded", ["SteelWarAxe"], sh=True), S("scaled", ["SteelMace"]),
                S("leather", ["LongBow"], "SteelArrow")],
        "high": [S("plate", ["SteelGreatsword"]), S("scaled", ["SteelBattleaxe"]), S("plate", ["SteelWarhammer"]),
                 S("steel", ["ElvenBow"], "ElvenArrow")]},
    "imperial": {   # deserters: worn Imperial issue, the officers' plate last
        "low": [S("imperial-light", ["IronSword"]), S("studded", ["IronWarAxe"]), S("imperial-light", ["IronMace"], sh=True)],
        "mid": [S("imperial", ["SteelSword"], sh=True), S("imperial", ["SteelWarAxe"], sh=True),
                S("imperial-light", ["ImperialBow"], "SteelArrow")],
        "high": [S("imperial-officer", ["SteelGreatsword"]), S("imperial-officer", ["SteelBattleaxe"]),
                 S("imperial-officer", ["SteelSword"], sh=True)]},
    "pirate": {   # corsairs and wreckers: sea-worn leather and scale, a captain's elven blade
        "low": [S("leather", ["IronSword"]), S("hide", ["IronDagger"]), S("leather", ["IronWarAxe"])],
        "mid": [S("imperial-light", ["SteelSword"]), S("scaled", ["SteelWarAxe"]), S("elven-light", ["SteelSword"])],
        "high": [S("scaled", ["SteelBattleaxe"]), S("elven", ["ElvenSword"]), S("elven", ["ElvenWarAxe"], sh=True)]},
    "smuggler": {   # light, quick and carrying value: leather, studded, elven light
        "low": [S("leather", ["IronDagger"]), S("hide", ["IronSword"]), S("studded", ["IronWarAxe"])],
        "mid": [S("elven-light", ["SteelSword"]), S("studded", ["SteelWarAxe"]), S("imperial-light", ["SteelSword"], sh=True)],
        "high": [S("elven", ["ElvenSword"]), S("elven", ["ElvenBow"], "ElvenArrow"), S("scaled", ["ElvenWarAxe"])]},
    "slaver": {   # Dunmer slavers: the house armour, chitin, bonemold, hardened with the band
        "low": [S("leather", ["IronSword"]), S("hide", ["IronWarAxe"]), S("bonemold", ["IronMace"])],
        "mid": [S("chitin-light", ["SteelSword"]), S("bonemold", ["SteelWarAxe"], sh=True), S("chitin-light", ["SteelMace"])],
        "high": [S("chitin-heavy", ["SteelGreatsword"], sh=False), S("bonemold-improved", ["ElvenSword"]),
                 S("chitin-heavy", ["SteelBattleaxe"])]},
    "frontier": {   # Orc and frontier raiders: iron then orcish
        "low": [S("iron", ["IronGreatsword"]), S("hide", ["IronBattleaxe"]), S("leather", ["IronWarAxe"], sh=True)],
        "mid": [S("banded", ["OrcishSword"], sh=True), S("scaled", ["OrcishWarAxe"]), S("steel", ["SteelSword"], sh=True)],
        "high": [S("orcish", ["OrcishGreatsword"]), S("orcish", ["OrcishBattleaxe"]), S("orcish", ["OrcishWarhammer"])]},
}

# Each lore group: its races (looks per race), its kit style. The Naga, tribal Argonians and undead are E1's.
SPEC = {
    "althii-archipelago|bandits in the burnt forts": ("outlaw", {"imperial": 3, "redguard": 3, "breton": 2, "bosmer": 3, "argonian": 2}),
    "cape-percar|bandits in the burned mines and quarries": ("outlaw", {"orc": 3, "redguard": 3, "imperial": 2, "dunmer": 3, "breton": 2}),
    "tulmek-washes|bandits": ("outlaw", {"imperial": 3, "redguard": 3, "dunmer": 3, "argonian": 2, "breton": 2}),
    "tulmek-washes|Blackguards' heirs from Blackrose Prison": ("outlaw", {"imperial": 4, "redguard": 3, "breton": 3, "orc": 2}),
    "valley-of-storms|Morrowind border bandits": ("outlaw", {"dunmer": 6, "argonian": 2, "imperial": 3}),
    "lake-ulaish|toll-fort bandits on the shore roads": ("outlaw", {"imperial": 4, "redguard": 3, "breton": 3, "orc": 2}),
    "barsaebica|frontier raiders at Slough Point": ("frontier", {"orc": 4, "imperial": 3, "redguard": 3, "breton": 2, "argonian": 2}),
    "cape-percar|Imperial deserter bands from Soulrest": ("imperial", {"imperial": 6, "breton": 3, "redguard": 3}),
    "aphon-isle|smugglers working the cave": ("smuggler", {"khajiit": 3, "redguard": 3, "dunmer": 3, "imperial": 2, "bosmer": 2}),
    "hatandros-bight|smugglers at landings": ("smuggler", {"khajiit": 3, "bosmer": 3, "argonian": 2, "breton": 3, "redguard": 2}),
    "nushara-bayou|smugglers using the back-water routes": ("smuggler", {"argonian": 3, "dunmer": 3, "khajiit": 3, "bosmer": 3}),
    "okuwun-rahei|smuggler landings": ("smuggler", {"khajiit": 3, "redguard": 3, "bosmer": 3, "imperial": 2, "dunmer": 2}),
    "kotherra-mangroves|pirates of the eastern Topal Bay shore": ("pirate", {"redguard": 4, "breton": 3, "bosmer": 3, "khajiit": 2, "imperial": 2}),
    "topal-bay|pirates of the eastern shore": ("pirate", {"redguard": 4, "breton": 3, "bosmer": 3, "imperial": 2, "orc": 2}),
    "padomaic-ocean|Skeith Isle pirates": ("pirate", {"redguard": 4, "breton": 3, "khajiit": 3, "dunmer": 2, "imperial": 2}),
    "skeith-isle|Skeith Isle pirates and smugglers": ("pirate", {"redguard": 3, "breton": 3, "khajiit": 3, "bosmer": 3, "dunmer": 2}),
    "sea-of-mists|wreckers and pirates working the sandbars": ("pirate", {"redguard": 3, "breton": 3, "imperial": 3, "argonian": 2, "khajiit": 2}),
    "benthic-yobesh|Bell Station divers' rivals (salvagers)": ("pirate", {"breton": 3, "imperial": 3, "redguard": 3, "khajiit": 2, "argonian": 2}),
    "valley-of-storms|Stormhold crystal-seekers": ("outlaw", {"dunmer": 4, "imperial": 3, "breton": 3, "argonian": 2}),
    "arnesian-jungle|Dunmer slavers working the Morrowind border": ("slaver", {"dunmer": 12}),
    "padomaic-ocean|Dunmer slavers (the wreck of a slaver lies on the shelf)": ("slaver", {"dunmer": 12}),
}
LEFT_OUT = {"chixathe-mesa|Velothi undead": "no Dunmer undead actor; the Dunmer dead of the held plugins are unique ghosts"}


def digest(*parts: str) -> int:
    return int(hashlib.sha256("|".join(parts).encode()).hexdigest()[:12], 16)


def eligible(npc: dict, race: str, edids: dict) -> bool:
    """A look: a whole record of the race, hostile by faction, nobody unique, with a face of its own (a record whose
    traits come from a template list would draw anyone, Nords included)."""
    if edids.get(npc["race"]) != RACE[race] or npc["unique"] or (npc["tf"] & 1 and npc["tplt"]):
        return False
    if not any(HOSTILE_FACTION.match(edids.get(f, "")) for f in npc["fact"]):
        return False
    if npc["vtck"] and REJECT_VOICE.search(edids.get(npc["vtck"], "")):
        return False
    return bool(npc["edid"]) and not REJECT_EDID.search(npc["edid"])


def pick_looks(npcs: list, race: str, n: int, salt: str, edids: dict) -> list[dict]:
    """n looks of the race, both sexes alternating, each from a different editor-id family first; the order is a
    hash of the group, so two groups of one race wear different faces."""
    cand = sorted((x for x in npcs if eligible(x, race, edids)), key=lambda x: (digest(salt, x["edid"]), x["edid"]))
    fam = lambda x: re.sub(r"\d+|[MF]$", "", x["edid"])   # noqa: E731
    out, seen = [], set()
    for want_new in (True, False):
        for female in (False, True) * len(cand):
            for x in cand:
                if len(out) >= n:
                    return out
                if x in out or x["female"] != female or (want_new and fam(x) in seen):
                    continue
                out.append(x)
                seen.add(fam(x))
                break
        if len(out) >= n:
            break
    return out[:n]


def kit_set(spec: dict, vals: dict) -> dict | None:
    """The kit as the world writer reads it: armour and shield `items`, hand `weapons`, `ammo`, its value, and the
    editor ids for the audit. None when a piece is not held."""
    items = list(ARMOUR[spec["armour"]])
    if spec["shield"] and SHIELD.get(spec["armour"]) and SHIELD[spec["armour"]] not in items:
        items.append(SHIELD[spec["armour"]])
    parts = items + spec["weapons"]
    if any(p not in vals for p in parts + ([spec["ammo"]] if spec["ammo"] else [])):
        return None
    plug = lambda e: ("Dragonborn.esm:" if e.startswith("DLC2") else "Skyrim.esm:") + e   # noqa: E731
    out = {"set": f"{spec['armour']} + {'+'.join(spec['weapons'])}" + (f" + {spec['ammo']}" if spec["ammo"] else ""),
           "items": [plug(i) for i in items], "weapons": [plug(w) for w in spec["weapons"]],
           "value": sum(vals[p] for p in parts), "weapon_value": sum(vals[w] for w in spec["weapons"])}
    if spec["ammo"]:
        out["ammo"] = plug(spec["ammo"])
    return out


def group_binding(key: str, spec: tuple, npcs: list, edids: dict, vals: dict, plug_of: dict) -> dict:
    style, mix = spec
    looks, races = [], []
    for race, n in mix.items():
        got = pick_looks(npcs, race, n, key, edids)
        looks += got
        races += [race] * len(got)
    gear = {t: [k for k in (kit_set(s, vals) for s in sets) if k] for t, sets in KITS[style].items()}
    recs = [f"{plug_of[x['key']]}:{x['edid']}" for x in looks]
    return {"records": recs, "race": "/".join(dict.fromkeys(races)),
            "why": f"{style} people of the lore's races: whole bandit-faction records of the held plugins, never Nord",
            "levels": [x["lvl"] for x in looks], "looks": recs,
            "look_voices": {r: edids.get(x["vtck"], "") if x["vtck"] else "" for r, x in zip(recs, looks)},
            "gear": gear}


def scan() -> tuple[list, dict, dict, dict]:
    """NPC_ records (race, voice, template, factions), editor ids and the value of every ARMO, WEAP and AMMO of the
    plugins a group draws from. Reads the plugins with tools/argonia_world/esm.py."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from tools.argonia_world.esm import Plugin
    from tools.newworld.ecology.census import plugin_path
    npcs, edids, vals, plug_of = [], {}, {}, {}
    for name in PLUGINS:
        p = Plugin.read(plugin_path(name), {"NPC_", "RACE", "VTYP", "FACT", "ARMO", "WEAP", "AMMO"})
        for r in p.records():
            if r.edid:
                edids[r.key] = r.edid
        for r in p.records():
            if not r.own:
                continue
            if r.sig in ("ARMO", "WEAP", "AMMO") and r.sub("DATA") and r.edid:
                vals[r.edid] = struct.unpack_from("<i", r.sub("DATA"), 0)[0]
            elif r.sig == "NPC_":
                a = r.sub("ACBS")
                if not a or len(a) < 20:
                    continue
                fl = struct.unpack_from("<I", a)[0]
                npcs.append({"key": r.key, "edid": r.edid, "race": r.ref("RNAM"), "vtck": r.ref("VTCK"),
                             "tplt": r.ref("TPLT"), "female": bool(fl & 1), "unique": bool(fl & 0x20),
                             "lvl": struct.unpack_from("<H", a, 8)[0], "tf": struct.unpack_from("<H", a, 18)[0],
                             "fact": [p.form_key(struct.unpack_from("<I", s)[0]) for s in r.all("SNAM")]})
                plug_of[r.key] = name
    return npcs, edids, vals, plug_of


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args(argv)
    npcs, edids, vals, plug_of = scan()
    bind = json.loads(BINDINGS.read_text())
    groups = bind["npc_groups"]
    for key, spec in SPEC.items():
        gb = group_binding(key, spec, npcs, edids, vals, plug_of)
        mean = {t: round(sum(e["value"] for e in s) / len(s)) for t, s in gb["gear"].items() if s}
        print(f"{key}: {len(gb['looks'])} looks ({gb['race']}), kit means {mean}")
        if not a.list:
            groups[key] = gb
    for key, why in LEFT_OUT.items():
        if not a.list:
            groups[key] = {"dropped": why}
    if not a.list:
        BINDINGS.write_text(json.dumps(bind, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
