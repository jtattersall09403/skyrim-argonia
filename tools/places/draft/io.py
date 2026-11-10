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
NORDIC_REVIEW = ROOT / "newworld" / "places" / "nordic_review.jsonl"


def nordic_review(path: Path = NORDIC_REVIEW) -> dict[str, dict]:
    """The looked-at verdict on bases we may add from elsewhere whose model folder is Skyrim's Nordic kits (decision
    0006): {base key: {base, edid, model, verdict: nordic|neutral, why}}. A verdict outranks the folder rule. A piece
    the source place itself uses is never judged: it is accepted as it comes."""
    return {r["base"]: r for r in read_jsonl(path)} if path.exists() else {}


def is_nordic(key: str, base: dict, review: dict[str, dict]) -> bool:
    """For a base we add from elsewhere: Nordic by the review where it was looked at, else by the extractor's folder
    rule (the cautious default)."""
    v = review.get(key)
    return v["verdict"] == "nordic" if v else bool(base.get("nordic"))


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
    stations, lights and bridges the draft added (place.json). `nordic` is false on every base the source place
    itself uses (accepted as it comes) and the review's or the folder rule's verdict on what we add from elsewhere."""
    decisions = place.get("draft") or {}
    bases = dict(src.bases)
    for k, b in grd.bases.items():
        bases.setdefault(k, b)
    want = set()
    for v in (decisions.get("replace") or {}).values():
        want.add(v["base"] if isinstance(v, dict) else v)
    want |= {a["base"] for a in decisions.get("add") or []}
    want |= {a["base"] for a in (place.get("stations") or {}).get("added") or []}
    lit = place.get("lights") or {}
    want_lights = {a["base"] for a in lit.get("added") or []} | {t["base"] for t in lit.get("twins") or []}
    review = nordic_review()
    bases.update(catalogue_bases(want - set(bases)))
    if want_lights - set(bases):
        from tools.places.draft import lights
        bases.update({k: b for k, b in lights.light_bases().items() if k in want_lights and k not in bases})
    return {k: {**b, "nordic": False if k in src.bases else is_nordic(k, b, review)} for k, b in bases.items()}


WALKED = re.compile(r"dock|step|stair|bridge|walkway|plank|pier|ramp|boardwalk", re.I)
WALK_TOP_TOL = 32.0  # units: a walked piece's replacement keeps its walking top within this


def keeps_function(old: dict, new: dict) -> bool:
    """A replacement keeps what its original does: a piece people walk on (docks, steps, bridges, walkways, by editor
    id or model) is replaced only by one whose walking top stands where the original's did (steps stay steps)."""
    if not WALKED.search(f"{old.get('edid') or ''} {old.get('model') or ''}"):
        return True
    a, b = old.get("bounds"), new.get("bounds")
    return bool(a and b and abs(a[1][2] - b[1][2]) <= WALK_TOP_TOL and abs(a[0][2] - b[0][2]) <= 4 * WALK_TOP_TOL)


def replacements(dec: dict, bases: dict, refused: list | None = None) -> dict[str, dict]:
    """{source base: {base, turn_deg?}}: the place's own `draft.replace`, the agent's call on a piece that cannot
    stand in our place as it is (never its look as a Nordic piece: the source's own pieces are accepted as they
    come). A replacement is never applied when it is Nordic itself or does not keep the original's function
    (`keeps_function`); each refused one is listed in `refused`."""
    out = {k: (dict(v) if isinstance(v, dict) else {"base": v}) for k, v in (dec.get("replace") or {}).items()}
    for k in list(out):
        why = None
        if (bases.get(out[k]["base"]) or {}).get("nordic"):
            why = "the replacement is a Nordic piece (decision 0006)"
        elif k in bases and out[k]["base"] in bases and not keeps_function(bases[k], bases[out[k]["base"]]):
            why = "the replacement does not keep its walking top"
        if why:
            del out[k]
            if refused is not None:
                refused.append(f"replace {k} -> refused: {why}")
    return out


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
_STYLE_DEFAULT = list(STYLE_ORDER)


def style_order(order: list | None = None) -> None:
    """The plugins whose pieces a place's added things are taken from, first to last: the place's own
    (`draft.style_order`: a Dunmer place names its own mods first) or the marsh's. Skyrim.esm is always last."""
    global STYLE_ORDER, _stations
    want = ([p for p in order if p != "Skyrim.esm"] + ["Skyrim.esm"]) if order else list(_STYLE_DEFAULT)
    if want != STYLE_ORDER:
        STYLE_ORDER, _stations = want, None


# the keyword the game keys a crafting station on (the build's own map, tools/places/check.py CRAFT_KEYWORD)
STATION_KEYWORD = {"forge": "CraftingSmithingForge", "anvil": "CraftingSmithingForge",
                   "armour-workbench": "CraftingSmithingArmorTable", "grindstone": "CraftingSmithingSharpeningWheel",
                   "smelter": "CraftingSmelter", "tanning-rack": "CraftingTanningRack", "alchemy-lab": "WICraftingAlchemy",
                   "arcane-enchanter": "WICraftingEnchanting", "cooking-pot": "CraftingCookpot",
                   "oven": "BYOHCraftingOven", "staff-enchanter": "DLC2StaffEnchanter"}


def station_base(station: str, path: Path = CATALOGUE) -> dict | None:
    """The working crafting furniture for a station kind, from the catalogue: a base whose record carries the
    station's crafting keyword (what the game keys on; never chosen by name or look), non-Nordic, in the plugins whose
    style our places use first (STYLE_ORDER), never a hidden, test or dungeon variant. When no such base carries the
    keyword, the vanilla working base (Skyrim.esm), marked `fallback` with the reason: function wins, the look is the
    owner's call in the studio."""
    global _stations
    if _stations is None:
        _stations = {}
        if path.exists():
            with path.open() as f:
                for line in f:
                    if '"FURN"' in line:
                        r = json.loads(line)
                        if r.get("type") == "FURN" and r.get("model") and r.get("plugin") in STYLE_ORDER \
                                and not re.search(STATION_SKIP, r.get("edid") or ""):
                            for st, pat in STATION_EDID.items():
                                kw = STATION_KEYWORD.get(st)
                                if (re.search(pat, r.get("edid") or "", re.I) or (kw and kw in r.get("keywords", []))) \
                                        and (not kw or kw in (r.get("keywords") or [])):
                                    _stations.setdefault(st, []).append(r)
    cands = _stations.get(station) or []
    styled = [r for r in cands if not r.get("nordic")]
    if styled:
        return min(styled, key=lambda r: (STYLE_ORDER.index(r["plugin"]), r["key"]))
    vanilla = sorted((r for r in cands if r["plugin"] == "Skyrim.esm"), key=lambda r: r["key"])
    if not vanilla:
        return None
    return {**vanilla[0], "fallback": f"the vanilla working base: no non-Nordic base carries {STATION_KEYWORD[station]}"}
