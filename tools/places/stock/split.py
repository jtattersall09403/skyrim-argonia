"""The split: is a thing set dressing or significant? Decided from record data alone (type, keywords, value,
enchantment, container kind), by the rules in `newworld/sources/stock/scale.json` `split`; never by eye.

    from tools.places.stock import split
    rules = split.rules()
    split.item_class(item, rules)        -> (kind, significant: bool, reason)
    split.container_kind(cont, rules)    -> (kind, always_significant: bool)
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SCALE = REPO / "newworld" / "sources" / "stock" / "scale.json"


@lru_cache(maxsize=1)
def scale() -> dict:
    return json.loads(SCALE.read_text(encoding="utf-8"))


def rules() -> dict:
    return scale()["split"]


def item_class(it: dict, r: dict | None = None) -> tuple[str, bool, str]:
    """(kind, significant, reason) of one item record (records.Records.item)."""
    r = r or rules()
    kws = set(it.get("keywords") or [])
    sig, value = it["sig"], it.get("value") or 0
    vmin = r["value_min"]
    if it["key"] in r["gold"]:
        return "gold", True, "gold"
    if it.get("ench"):
        return _kind(it, kws, r), True, "enchanted"
    if kws & set(r["jewellery_keywords"]):
        return "jewellery", True, "jewellery"
    if kws & set(r["gem_keywords"]):
        return "gem", True, "a gem"
    if sig in r["always_significant_sigs"]:
        kind = {"WEAP": "weapon", "AMMO": "ammunition", "SLGM": "soul-gem", "SCRL": "scroll", "KEYM": "key"}[sig]
        return kind, True, f"every {kind} is significant"
    if sig == "ARMO":
        if kws & set(r["clothing_keywords"]) and not kws & set(r["armour_keywords"]):
            return ("clothing", True, f"clothing worth {value} (>= {vmin})") if value >= vmin else \
                ("clothing", False, f"plain clothing worth {value}")
        return "armour", True, "armour"
    if sig == "BOOK":
        t = it.get("teaches") or {}
        if t.get("spell"):
            return "spell-tome", True, "teaches a spell"
        if t.get("skill") is not None and t.get("skill", -1) >= 0:
            return "skill-book", True, "raises a skill"
        return ("book", True, f"a book worth {value}") if value >= vmin else ("book", False, f"a book worth {value}")
    if sig == "ALCH":
        if it.get("poison"):
            return "poison", True, "a poison"
        if not it.get("food"):
            return "potion", True, "a potion"
        return ("food", True, f"food worth {value}") if value >= vmin else ("food", False, "food")
    if sig == "LIGH":
        return "light", False, "a carried light"
    kind = _kind(it, kws, r)
    if value >= vmin:
        return kind, True, f"worth {value} (>= {vmin})"
    return kind, False, f"{kind} worth {value}"


def _kind(it: dict, kws: set, r: dict) -> str:
    s = it["sig"]
    if s == "WEAP":
        return "weapon"
    if s == "ARMO":
        return "clothing" if kws & set(r["clothing_keywords"]) and not kws & set(r["armour_keywords"]) else "armour"
    if s == "INGR":
        return "ingredient"
    if s == "MISC":
        for kw, k in r["misc_kinds"].items():
            if kw in kws:
                return k
        return "clutter"
    return {"BOOK": "book", "ALCH": "potion", "AMMO": "ammunition", "SLGM": "soul-gem", "SCRL": "scroll",
            "KEYM": "key", "LIGH": "light"}.get(s, s.lower())


def container_kind(cont: dict | None, r: dict | None = None, extra: str = "") -> tuple[str, bool]:
    """(kind, always significant) from the container base's editor id, name and model words."""
    r = r or rules()
    text = " ".join(str(x or "") for x in ((cont or {}).get("edid"), (cont or {}).get("name"),
                                          (cont or {}).get("model"), extra)).lower()
    for kind, words in r["container_kinds"]:
        if any(re.search(w, text) for w in words):
            return kind, kind in r["always_significant_containers"]
    return "other", False
