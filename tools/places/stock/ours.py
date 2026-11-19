"""Records of ours (plugin/Argonia, Spriggit YAML) that a stock row gives by editor id.

A stock source names an item of ours as "Argonia:<editor id>" (for example "Argonia:ANW_VoshLeerasRing"); the stock
database and the build carry it as the form key it has in Argonia.esp, "Argonia.esp:<6 hex>", read here from the
record's file name. `Records` serves these keys beside the game's, from the YAML.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import yaml

PLUGIN = "Argonia.esp"
ALIAS = "Argonia"
ROOT = Path(__file__).resolve().parents[3] / "plugin" / "Argonia"
FOLDERS = {"Armors": "ARMO", "Weapons": "WEAP", "MiscItems": "MISC", "Books": "BOOK", "Keys": "KEYM", "Ingestibles": "ALCH",
           "Ingredients": "INGR", "Ammunitions": "AMMO", "Lights": "LIGH", "SoulGems": "SLGM", "Scrolls": "SCRL"}
SLOTS = {"Head": 0x1, "Hair": 0x2, "Body": 0x4, "Hands": 0x8, "Forearms": 0x10, "Amulet": 0x20, "Ring": 0x40, "Feet": 0x80,
         "Calves": 0x100, "Shield": 0x200}
_FILE = re.compile(r"^(?P<edid>.+) - (?P<hex>[0-9A-F]{6})_Argonia\.esp\.yaml$")


@lru_cache(maxsize=None)
def index(root: Path = ROOT) -> dict[str, tuple[str, Path]]:
    """Editor id -> (key "Argonia.esp:<hex>", file) for every item record of ours."""
    out = {}
    for folder in FOLDERS:
        for p in sorted((root / folder).glob("*.yaml")) if (root / folder).is_dir() else []:
            m = _FILE.match(p.name)
            if m:
                out[m["edid"]] = (f"{PLUGIN}:{m['hex']}", p)
    return out


def resolve(key: str, root: Path = ROOT) -> str:
    """"Argonia:<editor id>" as its form key; any other key as it is. An editor id with no record of ours is an error."""
    if not key.startswith(ALIAS + ":"):
        return key
    edid = key.split(":", 1)[1]
    hit = index(root).get(edid)
    if hit is None:
        raise KeyError(f"{key}: no item record of ours has the editor id {edid} (plugin/Argonia)")
    return hit[0]


def items(kw_by_key: dict[str, str], root: Path = ROOT) -> dict[str, dict]:
    """Every item record of ours as the dict Records.item gives, by form key."""
    out = {}
    for edid, (key, p) in index(root).items():
        d = yaml.safe_load(p.read_text(encoding="utf-8"))
        kws = []
        for k in d.get("Keywords") or []:
            hexid, plugin = str(k).split(":", 1)
            pk = f"{plugin}:{hexid}"
            kws.append(kw_by_key.get(pk, pk))
        ench = d.get("ObjectEffect")
        if ench:
            hexid, plugin = str(ench).split(":", 1)
            ench = f"{plugin}:{hexid}"
        flags = (d.get("BodyTemplate") or {}).get("FirstPersonFlags") or []
        out[key] = {"key": key, "sig": FOLDERS[p.parent.name], "edid": edid, "name": (d.get("Name") or {}).get("Value"),
                    "keywords": kws, "ench": ench, "value": int(d.get("Value") or 0), "weight": float(d.get("Weight") or 0.0),
                    "rating": 0.0, "slots": sum(SLOTS.get(f, 0) for f in flags)}
    return out
