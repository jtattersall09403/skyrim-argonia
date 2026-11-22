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
STOCK = REPO / "newworld" / "sources" / "stock"
SCALE = STOCK / "scale.json"


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


WEAP_KINDS = {"WeapTypeDagger": "dagger", "WeapTypeSword": "sword", "WeapTypeWarAxe": "waraxe", "WeapTypeMace": "mace",
              "WeapTypeGreatsword": "greatsword", "WeapTypeBattleaxe": "battleaxe", "WeapTypeWarhammer": "warhammer",
              "WeapTypeBow": "bow"}
ARMOUR_SLOTS = {"ArmorCuirass": "cuirass", "ArmorHelmet": "helmet", "ArmorGauntlets": "gauntlets", "ArmorBoots": "boots"}


@lru_cache(maxsize=1)
def materials() -> dict:
    """materials.json as lookups: {"materials": {id: row}, "keyword": {Skyrim keyword: id}, "never": {ids}, ...}."""
    doc = json.loads((STOCK / "materials.json").read_text(encoding="utf-8"))
    return {"materials": {m["id"]: m for m in doc["materials"]},
            "keyword": {k: m["id"] for m in doc["materials"] for k in m["keywords"]},
            "never": set(doc["never"]["materials"]), "never_why": doc["never"]["why"], "groups": doc["groups"],
            "bands": doc["bands"]}


@lru_cache(maxsize=1)
def item_materials() -> dict:
    """item_material.json as lookups: {"gear": {item key: row}, "wares": {item key: row}}."""
    p = STOCK / "item_material.json"
    doc = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    return {"gear": {r["item"]: r for r in doc.get("gear", [])}, "wares": {r["item"]: r for r in doc.get("wares", [])}}


@lru_cache(maxsize=1)
def power_table() -> dict:
    """power.json (generated by `stockdb power`): {kind: {"ceiling": {tier: power}, "bases": {tier: {edid: power}}}};
    {} before it is made."""
    p = STOCK / "power.json"
    return json.loads(p.read_text(encoding="utf-8")).get("kinds", {}) if p.exists() else {}


def _key(it: dict) -> str:
    return it.get("key") or it.get("id") or ""


def material_of(it: dict) -> tuple[str | None, str]:
    """(our material id, how): the item's item_material row, else the material its Skyrim keyword reads as
    (materials.json `keywords`), else None: an item of no material (clothing, a ware, a modded piece not yet filed)."""
    row = item_materials()["gear"].get(_key(it))
    if row:
        return row["material"], "its item_material row"
    km = materials()["keyword"]
    kw = next((k for k in it.get("keywords") or [] if k in km), None)
    if kw:
        return km[kw], f"its keyword {kw}"
    if it.get("material_id"):           # an items.json row already carries it
        return it["material_id"], "its item row"
    if it.get("material") in km:
        return km[it["material"]], f"its keyword {it['material']}"
    return None, ""


def power_kind(it: dict) -> str | None:
    """What an item's power is measured against: a weapon type (sword), an armour class and slot (light-cuirass),
    a shield; None for anything else (a staff, clothing, a ware)."""
    if it.get("power_kind"):
        return it["power_kind"]
    kws = set(it.get("keywords") or [])
    sig = it.get("sig") or it.get("record")
    if sig == "WEAP":
        return next((v for k, v in WEAP_KINDS.items() if k in kws), None)
    if sig == "ARMO":
        if "ArmorShield" in kws:
            return "shield"
        slot = next((v for k, v in ARMOUR_SLOTS.items() if k in kws), None)
        cls = "heavy" if "ArmorHeavy" in kws else "light" if "ArmorLight" in kws else None
        return f"{cls}-{slot}" if slot and cls else None
    return None


def slot_of(it: dict) -> str | None:
    """weapon, heavy, light or shield: where an item of gear stands on the ladder (tier_material's slot)."""
    kind = power_kind(it)
    if kind is None:
        return None
    if kind in WEAP_KINDS.values():
        return "weapon"
    return "shield" if kind == "shield" else kind.split("-", 1)[0]


def power_of(it: dict) -> float | None:
    """Its damage (a weapon) or armour rating (armour), as measured."""
    if it.get("power") is not None:
        return float(it["power"])
    v = it.get("damage") if (it.get("sig") or it.get("record")) == "WEAP" else it.get("rating")
    return float(v) if v else None


def power_tier(it: dict, sc: dict | None = None, table: dict | None = None) -> tuple[str | None, str]:
    """(tier, how) by power: the lowest tier whose ceiling for the item's kind reaches its damage or rating (above
    T6's ceiling, T6). A tier's ceiling is the strongest of Skyrim's own base gear at that tier or below (scale.json
    `power`, measured into power.json). (None, "") when the item has no kind or power, or its kind no ceilings."""
    sc = sc or scale()
    table = power_table() if table is None else table
    kind, pw = power_kind(it), power_of(it)
    ceil = (table.get(kind) or {}).get("ceiling") if kind else None
    if not ceil or not pw:
        return None, ""
    for t in sc["tiers"]:
        if t["id"] in ceil and pw <= ceil[t["id"]]:
            return t["id"], f"its power ({kind} {pw:g}; Skyrim's {t['id']} reaches {ceil[t['id']]:g})"
    return sc["tiers"][-1]["id"], f"its power ({kind} {pw:g}, above every tier's ceiling)"


def item_tier(it: dict, sc: dict | None = None) -> tuple[str | None, str]:
    """(tier, how) of one item on the scale, wherever a tier is computed (the item catalogue, the check, the studio):
    1. the scale's explicit lists win: a tier that names the item itself (its soul gem, gems, jewellery) — a soul
       gem's power outruns its price, so its value never sets its tier;
    2. an item_material row's own `tier`, set only where a record's numbers are a mod's error (its reason given);
    3. its power: a weapon's damage or an armour piece's rating against Skyrim's base gear of each tier, by weapon
       type or armour class and slot (power_tier): what a player feels in a fight, whatever its keyword or price;
    4. else its Skyrim material keyword: the lowest tier whose power keywords (power_weapon, power_armour) name it;
    5. an enchanted thing reaches the tier of its enchantment's grade (the tier whose `enchant_grade` it is) when that
       is higher: an iron sword of arcing is not common, though its record's value is an iron sword's;
    6. a thing of none of the above takes the tier its value reaches;
    7. no value known (an item not measured yet) and none of the above: None.
    `it` needs edid and keywords; value, damage or rating, ench and ench_grade when known (records.Records.item, the
    catalogue, an items.json row)."""
    sc = sc or scale()
    tiers = sc["tiers"]
    rank = {t["id"]: t["rank"] for t in tiers}
    edid = it.get("edid") or ""
    for t in tiers:
        if edid and (edid == t.get("soul_gem") or edid in t.get("gem", []) or edid in t.get("jewellery", [])):
            return t["id"], "the scale's list for that tier"
    row = item_materials()["gear"].get(_key(it))
    if row and row.get("tier"):
        return row["tier"], f"its item_material row ({row['why']})"
    mat = power_tier(it, sc)
    if mat[0] is None:
        kws = set(it.get("keywords") or []) | {it.get("material")}
        mat = next(((t["id"], f"its material ({k})") for t in tiers
                    for k in t.get("power_weapon", []) + t.get("power_armour", []) if k in kws), (None, ""))
    value = it.get("value")
    if mat[0] is None and value is not None:
        mat = (next((t["id"] for t in tiers if value <= t["value_max"]), tiers[-1]["id"]), f"its value ({value})")
    grade = it.get("ench_grade")
    by_ench = next((t["id"] for t in tiers if grade and t.get("enchant_grade") == min(grade, 6)), None)
    if by_ench and (mat[0] is None or rank[by_ench] > rank[mat[0]]):
        return by_ench, f"its enchantment's grade ({grade})"
    return mat


def never_reason(it: dict, sc: dict | None = None) -> str | None:
    """Why an item may never be stocked (decision 0006), or None: its material of ours is a never material — a Black
    Marsh piece filed under its true material passes, whatever keyword its record carries — or, unfiled, its editor
    id names a Skyrim-only kit."""
    sc = sc or scale()
    mid, how = material_of(it)
    if mid in materials()["never"]:
        return (f"{materials()['materials'][mid]['label']} ({how}) is Skyrim's own gear, which has no road into Black "
                f"Marsh (decision 0006)")
    edid = (it.get("edid") or "").lower()
    word = next((w for w in sc["never"]["edid_words"] if w.lower() in edid), None)
    if word and _key(it) not in item_materials()["gear"]:
        return f"it is {word} gear, Skyrim's own, which has no road into Black Marsh (decision 0006)"
    return None


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
