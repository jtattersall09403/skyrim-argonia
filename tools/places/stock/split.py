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


def source_plugins(place_id: str) -> list[str]:
    """The place's mods: the plugins of its source (newworld/places/<id>/place.json `source_id`, sources.jsonl)."""
    pj = REPO / "newworld" / "places" / place_id / "place.json"
    sid = json.loads(pj.read_text()).get("source_id") if pj.exists() else None
    for ln in (REPO / "newworld" / "places" / "sources.jsonl").read_text().splitlines():
        row = json.loads(ln) if ln.strip() else {}
        if sid and row.get("source_id") == sid:
            return list(row.get("plugins", [])) + list(row.get("extra_refs_plugins", []))
    return []


def guard_issue(culture_id: str | None, ceiling: str, plugins: list[str], sc: dict | None = None) -> dict:
    """What a place's guards are issued (scale.json `guard_issue`): {tier, set, torch, why}. Their own culture's guard
    set where the place's mods provide one and the place's ceiling reaches its tier (`set` the scale's row), else the
    plain issue at the faction's issue tier (`set` None)."""
    sc = sc or scale()
    gi = sc["guard_issue"]
    rank = {t["id"]: t["rank"] for t in sc["tiers"]}
    plain = next(o for o in sc["owner"] if o["id"] == "faction")["issue_tier"]
    have = {p.lower() for p in plugins}
    for s in gi["sets"]:
        if culture_id in s["cultures"] and s["plugin"].lower() in have and rank[s["tier"]] <= rank[ceiling]:
            return {"tier": s["tier"] if rank[s["tier"]] > rank[plain] else plain, "set": s, "torch": gi["torch"],
                    "why": f"its own culture's guard set, {s['label']} ({s['tier']}): the place's mods provide it and "
                           f"its ceiling ({ceiling}) reaches it"}
    return {"tier": plain, "set": None, "torch": gi["torch"], "why": f"the plain issue ({plain})"}


def item_tier(it: dict, sc: dict | None = None) -> tuple[str | None, str]:
    """(tier, how) of one item on the scale, wherever a tier is computed (the item catalogue, the check, the studio):
    1. the scale's explicit lists win: a tier that names the item itself (its soul gem, gems, jewellery) — a soul
       gem's power outruns its price, so its value never sets its tier;
    2. else its material: the lowest tier whose weapon or armour list names it;
    3. an enchanted thing reaches the tier of its enchantment's grade (the tier whose `enchant_grade` it is) when that
       is higher: an iron sword of arcing is not common, though its record's value is an iron sword's;
    4. a thing of no listed material takes the tier its value reaches;
    5. no value known (an item not measured yet) and none of the above: None.
    `it` needs edid and keywords; value, ench and ench_grade when known (records.Records.item, the catalogue)."""
    sc = sc or scale()
    tiers = sc["tiers"]
    rank = {t["id"]: t["rank"] for t in tiers}
    edid = it.get("edid") or ""
    for t in tiers:
        if edid and (edid == t.get("soul_gem") or edid in t.get("gem", []) or edid in t.get("jewellery", [])):
            return t["id"], "the scale's list for that tier"
    kws = set(it.get("keywords") or [])
    mat = next(((t["id"], f"its material ({k})") for t in tiers for k in t.get("weapon", []) + t.get("armour", [])
                if k in kws), None)
    value = it.get("value")
    if mat is None and value is not None:
        mat = (next((t["id"] for t in tiers if value <= t["value_max"]), tiers[-1]["id"]), f"its value ({value})")
    grade = it.get("ench_grade")
    by_ench = next((t["id"] for t in tiers if grade and t.get("enchant_grade") == min(grade, 6)), None)
    if by_ench and (mat is None or rank[by_ench] > rank[mat[0]]):
        return by_ench, f"its enchantment's grade ({grade})"
    return mat or (None, "")


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
