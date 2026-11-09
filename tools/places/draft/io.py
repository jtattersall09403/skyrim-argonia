"""Reading bundles and place files for the draft (the contract's shapes, docs/design/place-studio.md)."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from tools.places.seat import BUNDLES, PLACES, ROOT, Ground, read_jsonl, write_jsonl

__all__ = ["Bundle", "Space", "load", "read_jsonl", "write_jsonl", "mint", "ROOT", "BUNDLES", "PLACES", "Ground"]


@dataclass
class Space:
    space_id: str
    meta: dict
    refs: list[dict]
    navmesh: list[dict]
    path: Path

    @property
    def interior(self) -> bool:
        return self.meta.get("type") == "interior" or self.space_id != "exterior"


@dataclass
class Bundle:
    path: Path
    meta: dict
    bases: dict[str, dict]
    npcs: dict[str, dict]
    spaces: dict[str, Space] = field(default_factory=dict)
    _ground: Ground | None = None

    @property
    def exterior(self) -> Space | None:
        return self.spaces.get("exterior")

    @property
    def ground(self) -> Ground:
        if self._ground is None:
            self._ground = Ground.load(self.path)
        return self._ground

    def stamp(self) -> str:
        """A short key of the bundle's own stamp (its inputs), or of its files when it has none."""
        st = self.meta.get("stamp")
        blob = json.dumps(st, sort_keys=True) if st else json.dumps(sorted(p.name for p in self.path.rglob("*")))
        return hashlib.sha256(blob.encode()).hexdigest()[:16]


def load(bundle_id: str, root: Path = BUNDLES) -> Bundle:
    bdir = root / bundle_id
    if not (bdir / "bundle.json").exists():
        raise FileNotFoundError(f"bundle {bundle_id} not found under {root}")
    meta = json.loads((bdir / "bundle.json").read_text())
    bases = {b["key"]: b for b in read_jsonl(bdir / "bases.jsonl")}
    npcs = {b["key"]: b for b in read_jsonl(bdir / "npcs.jsonl")}
    b = Bundle(bdir, meta, bases, npcs)
    sroot = bdir / "spaces"
    for sdir in sorted(p for p in sroot.iterdir() if p.is_dir()) if sroot.exists() else []:
        sj = sdir / "space.json"
        smeta = json.loads(sj.read_text()) if sj.exists() else {"space_id": sdir.name}
        b.spaces[sdir.name] = Space(sdir.name, smeta, read_jsonl(sdir / "refs.jsonl"), read_jsonl(sdir / "navmesh.jsonl"),
                                    sdir)
    return b


_B32 = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def mint(place_id: str, *parts: str) -> str:
    """A stable id `<place_id>.<26 chars>` from what the thing is (reruns of the draft keep every id)."""
    h = int.from_bytes(hashlib.sha256("|".join((place_id,) + parts).encode()).digest()[:17], "big")
    s = "".join(_B32[(h >> (5 * i)) & 31] for i in range(26))
    return f"{place_id}.{s}"


CATALOGUE = ROOT / "out" / "places" / "catalogue" / "bases.jsonl"


def catalogue_bases(keys: set[str], path: Path = CATALOGUE) -> dict[str, dict]:
    """Base rows of the asset catalogue (every source we hold) for keys a bundle lacks (replacements, additions)."""
    if not keys or not path.exists():
        return {}
    out = {}
    with path.open() as f:
        for line in f:
            if any(k in line for k in keys):
                r = json.loads(line)
                if r.get("key") in keys:
                    out[r["key"]] = r
    return out


def place_bases(src: "Bundle", grd: "Bundle", place: dict) -> dict[str, dict]:
    """Every base a draft may place: the source's, the ground's, and the catalogue's for the agent's choices and the
    stations and bridges the draft added (place.json)."""
    decisions = place.get("draft") or {}
    bases = dict(src.bases)
    for k, b in grd.bases.items():
        bases.setdefault(k, b)
    want = set()
    for v in (decisions.get("replace") or {}).values():
        want.add(v["base"] if isinstance(v, dict) else v)
    want |= {a["base"] for a in decisions.get("add") or []}
    want |= {a["base"] for a in (place.get("stations") or {}).get("added") or []}
    bases.update(catalogue_bases(want - set(bases)))
    return bases


STATION_EDID = {
    "forge": r"^CraftingBlacksmithForge", "anvil": r"Anvil", "grindstone": r"SharpeningWheel|Grindstone",
    "smelter": r"Smelter", "tanning-rack": r"TanningRack", "alchemy-lab": r"AlchemyWorkbench|AlchemyLab",
    "arcane-enchanter": r"EnchantingWorkbench|ArcaneEnchanter", "cooking-pot": r"CookingPot|Cookpot",
    "armour-workbench": r"ArmorWorkbench|ArmorTable", "oven": r"Oven", "staff-enchanter": r"StaffEnchant",
}
STATION_SKIP = r"Invisible|Inv$|test|Drink|NPC|Skyforge|Tabletop|Poison|DB|WR$|Dwe|DwaSp"
STYLE_ORDER = ["Black Marsh.esm", "Black Marsh North.esp", "King of the Murkmire.esp", "XanmeerResources.esp",
               "Here There Be Monsters - Curse of Cipactli.esp", "Here There Be Monsters.esp", "Dragonborn.esm",
               "Skyrim.esm"]
_stations: dict | None = None


def station_base(station: str, path: Path = CATALOGUE) -> dict | None:
    """The working crafting furniture for a station kind, from the catalogue: non-Nordic, in the plugins whose style
    our places use first (STYLE_ORDER), never a hidden, test or dungeon variant."""
    global _stations
    if _stations is None:
        _stations = {}
        if path.exists():
            with path.open() as f:
                for line in f:
                    if '"FURN"' in line:
                        r = json.loads(line)
                        if r.get("type") == "FURN" and not r.get("nordic") and r.get("model") \
                                and r.get("plugin") in STYLE_ORDER and not re.search(STATION_SKIP, r.get("edid") or ""):
                            for st, pat in STATION_EDID.items():
                                if re.search(pat, r.get("edid") or "", re.I):
                                    _stations.setdefault(st, []).append(r)
    cands = _stations.get(station) or []
    return min(cands, key=lambda r: (STYLE_ORDER.index(r["plugin"]), r["key"])) if cands else None
