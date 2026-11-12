"""python -m tools.places sources-match

Matches every place of ours (newworld/story/data/db/place.jsonl) to the mined candidate source places
(out/newworld/sources/mined/*.jsonl, `python -m tools.places sources-mine`) and writes the committed match:

- newworld/sources/source_match/source_place.jsonl  every source place that is allocated or an alternate, its signals
- newworld/sources/source_match/place_source.jsonl  per place: rank 0 the allocated source (unique across places),
  ranks 1-3 the next most similar (may be shared), each with its score and the score's parts; rank 0 also carries
  the population the place now has and why (build_db overwrites place.population from it)
- newworld/places/sources_mined.jsonl                each of those sources as an extractor row, so
  `python -m tools.places extract <source_id>` (or `source <place_id>`) writes its bundle on demand
- out/newworld/sources/ranked.json                   the top ten per place and the run's numbers, for the page

Similarity is a weighted sum of explainable parts (WEIGHTS): kind (KIND_FIT), the text of the summary against the
candidate's description (bge-small, tools/places/search/embed.py), size, status, culture or tileset, water and
interior. The allocation is one linear assignment (scipy) whose cost is (1 - score) times the place's importance
weight, so a major place gets the most similar source. Fixed: FIXED (a drafted place keeps its source); excluded:
EXCLUDE (the owner did not like BM&V's Lilmoth).
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from tools.places.bundle import REPO
from tools.places.sources_mine import GROUPS, OUT as MINED

DB = REPO / "newworld" / "story" / "data" / "db"
MATCH = REPO / "newworld" / "sources" / "source_match"
ROWS = REPO / "newworld" / "places" / "sources_mined.jsonl"
RANKED = REPO / "out" / "newworld" / "sources" / "ranked.json"

WEIGHTS = {"kind": 0.38, "text": 0.14, "size": 0.14, "status": 0.10, "culture": 0.10, "water": 0.08, "interior": 0.06}
NAME_BONUS = 0.3            # the same place by name, over the weighted parts
NAME_GROUPS = {"bmv", "kotm"}   # the Black Marsh mods: a shared name there is the same place
IMPORTANCE_WEIGHT = {1: 1.0, 2: 1.5, 3: 2.5, 4: 4.0, 5: 6.0}
FIXED = {"helstrom": ("bmv.helstrom", re.compile(r"^blackmarsh\.cluster\.helstrom\."))}
EXCLUDE = [("bmv", re.compile(r"l[io]lmoth(?!iit)", re.I))]
LIVED = {"inhabited", "garrisoned", "occupied"}
WET_SITING = {"coast", "riverbank", "swamp", "lakeshore", "island", "seabed"}

# our kind -> the candidate kinds that fit it, best first (1 = the same kind of place)
RUINS = ("ruin-argonian", "ruin-ayleid", "ruin-dwemer", "ruin-imperial", "ruin-nordic", "ruin-dunmer", "ruin-falmer",
         "ruin-daedric", "ruin")
KIND_FIT: dict[str, dict[str, float]] = {
    "city": {"city": 1, "town": 0.75, "village": 0.4},
    "town": {"town": 1, "city": 0.75, "village": 0.65},
    "village": {"village": 1, "hamlet": 0.75, "town": 0.6, "camp-tribal": 0.45},
    "hamlet": {"hamlet": 1, "village": 0.8, "homestead": 0.6, "farm": 0.6, "camp-tribal": 0.5, "dock": 0.4},
    "abandoned-village": {"village": 0.9, "hamlet": 0.9, "ruin-argonian": 0.7, "ruin": 0.6, "homestead": 0.5},
    "tribal-camp": {"camp-tribal": 1, "camp-outlaw": 0.7, "hamlet": 0.55, "camp-military": 0.5},
    "outlaw-camp": {"camp-outlaw": 1, "camp-tribal": 0.7, "cave": 0.5, "fort": 0.45},
    "outpost": {"hamlet": 0.9, "tower": 0.85, "camp-military": 0.8, "camp-tribal": 0.75, "dock": 0.6,
                "homestead": 0.6, "fort": 0.5, "camp-outlaw": 0.45},
    "fort": {"fort": 1, "keep": 0.8, "camp-military": 0.65, "tower": 0.6, "ruin-imperial": 0.5},
    "keep": {"keep": 1, "fort": 0.9, "tower": 0.6},
    "prison": {"prison": 1, "fort": 0.8, "keep": 0.7},
    "station": {"dock": 0.85, "tower": 0.75, "camp-military": 0.6, "hamlet": 0.55},
    "ferry": {"dock": 1, "hamlet": 0.55, "homestead": 0.45},
    "mine": {"mine": 1, "quarry": 0.8, "cave": 0.5},
    "quarry": {"quarry": 1, "mine": 0.8},
    "cave": {"cave": 1, "mine": 0.5, "ruin": 0.4},
    "farm": {"farm": 1, "homestead": 0.8, "hamlet": 0.6},
    "homestead": {"homestead": 1, "farm": 0.8, "hamlet": 0.5},
    "estate": {"estate": 1, "keep": 0.6, "farm": 0.65, "homestead": 0.6},
    "logging-camp": {"mill": 1, "camp-outlaw": 0.45, "camp-tribal": 0.5, "farm": 0.4},
    "lighthouse": {"lighthouse": 1, "tower": 0.6, "dock": 0.4},
    "shipwreck": {"shipwreck": 1, "ship": 0.75, "dock": 0.3},
    "landmark": {"landmark": 1, "shrine": 0.8, "ruin": 0.5, "grove": 0.8},
    "peak": {"peak": 1, "landmark": 0.85, "shrine": 0.6},
    "belvedere": {"tower": 0.85, "estate": 0.75, "landmark": 0.6, "homestead": 0.55},
    "imperial-ruin": {"ruin-imperial": 1, "fort": 0.55, "ruin": 0.6, "ruin-nordic": 0.45, "ruin-ayleid": 0.45},
    "velothi-ruin": {"ruin-dunmer": 1, "ruin-daedric": 0.8, "ruin": 0.55, "ruin-dwemer": 0.3},
    "ayleid-ruin": {"ruin-ayleid": 1, "ruin": 0.55, "ruin-imperial": 0.45},
    # Kothringi: no tileset anywhere. By the lore (story/lore/topics/lost-peoples.md) they were human villagers
    # of the swamp, later Imperial-influenced (Gideon's garrison), who buried their dead in cairns: an abandoned
    # hamlet or village, an Imperial ruin, a native ruin; never a cave or a Dwemer city
    "kothringi-ruin": {"hamlet": 0.9, "village": 0.9, "ruin-imperial": 0.85, "ruin-argonian": 0.75, "ruin": 0.7,
                       "homestead": 0.6, "ruin-nordic": 0.4, "ruin-dwemer": 0.15, "ruin-falmer": 0.15},
    "lilmothiit-ruin": {"ruin-argonian": 1, "ruin": 0.6, "cave": 0.45, "ruin-ayleid": 0.4},
    "sunken-ruin": {"ruin-argonian": 0.95, "ruin": 0.6, "ruin-ayleid": 0.5, "ruin-imperial": 0.5, "shipwreck": 0.4},
}
FAMILY = {
    "city": "settlement", "town": "settlement", "village": "settlement", "hamlet": "settlement", "homestead": "settlement",
    "farm": "settlement", "estate": "settlement", "abandoned-village": "settlement", "outpost": "settlement",
    "ferry": "water", "station": "water", "dock": "water", "lighthouse": "water", "shipwreck": "water", "ship": "water",
    "tribal-camp": "camp", "outlaw-camp": "camp", "logging-camp": "camp", "camp-tribal": "camp", "camp-outlaw": "camp",
    "camp-military": "camp", "mill": "camp",
    "fort": "military", "keep": "military", "prison": "military", "tower": "military", "belvedere": "military",
    "mine": "underground", "quarry": "underground", "cave": "underground",
    "landmark": "landmark", "peak": "landmark", "shrine": "landmark", "grove": "landmark",
}
CULTURE_WANT = {
    "ayleid-ruin": ("ayleid",), "velothi-ruin": ("dunmer", "daedric"), "imperial-ruin": ("imperial",),
    "kothringi-ruin": ("imperial", "argonian"), "lilmothiit-ruin": ("argonian",), "sunken-ruin": ("argonian",),
    "fort": ("imperial", "argonian"), "keep": ("imperial", "argonian"), "prison": ("imperial", "argonian"),
    "belvedere": ("imperial", "argonian"), "estate": ("imperial", "argonian", "dunmer"),
}
CULTURES = ("ayleid", "dwemer", "imperial", "nordic", "dunmer", "argonian", "bosmer", "redguard", "khajiit", "falmer",
            "daedric", "orc")

KW_KIND = [  # Skyrim's location keywords -> a kind (decision 0034: Bethesda's own type of a place)
    ("LocTypeCity", "city"), ("LocTypeTown", "town"), ("LocTypeJail", "prison"), ("LocTypeMilitaryFort", "fort"),
    ("LocTypeCastle", "keep"), ("LocTypeMine", "mine"), ("LocTypeLumberMill", "mill"), ("LocTypeShipwreck", "shipwreck"),
    ("LocTypeShip", "ship"), ("LocTypeOrcStronghold", "camp-tribal"), ("LocTypeGiantCamp", "camp-tribal"),
    ("LocTypeForswornCamp", "camp-tribal"), ("LocTypeMilitaryCamp", "camp-military"), ("LocTypeBanditCamp", "camp-outlaw"),
    ("LocTypeHagravenNest", "camp-outlaw"), ("LocTypeDwarvenAutomatons", "ruin-dwemer"), ("LocTypeFalmerHive", "ruin-falmer"),
    ("LocTypeDraugrCrypt", "ruin-nordic"), ("LocTypeDragonPriestLair", "ruin-nordic"), ("LocTypeFarm", "farm"),
    ("LocTypeAnimalDen", "cave"), ("LocTypeDragonLair", "landmark"), ("LocTypeSettlement", "village"),
    ("LocTypeVampireLair", "cave"), ("LocTypeWarlockLair", "cave"), ("LocTypeSprigganGrove", "grove"),
]
MARKER_KIND = {
    "City": "city", "Town": "town", "Settlement": "village", "Cave": "cave", "Camp": "camp-outlaw", "Fort": "fort",
    "NordicRuin": "ruin-nordic", "DwemerRuin": "ruin-dwemer", "Shipwreck": "shipwreck", "Grove": "grove",
    "Landmark": "landmark", "DragonLair": "landmark", "Farm": "farm", "WoodMill": "mill", "Mine": "mine",
    "ImperialCamp": "camp-military", "StormcloakCamp": "camp-military", "Doomstone": "landmark", "WheatMill": "farm",
    "Smelter": "mine", "Stable": "farm", "ImperialTower": "tower", "Clearing": "landmark", "Pass": "landmark",
    "Altar": "shrine", "Rock": "landmark", "Lighthouse": "lighthouse", "OrcStronghold": "camp-tribal",
    "GiantCamp": "camp-tribal", "Shack": "homestead", "NordicTower": "tower", "NordicDwelling": "homestead",
    "Docks": "dock", "DaedricShrine": "shrine", "SkyrimCity": "city", "WindhelmCity": "city",
    "RavenRockCity": "town", "DLC02MiraakTemple": "ruin-daedric", "DLC02RavenRock": "town", "DLC02StandingStone": "shrine",
    "DLC02TelvanniTower": "tower", "DLC02ToSkyrim": "dock", "DLC02ToSolstheim": "dock", "DLC02CastleKarstaag": "ruin",
}
NAME_KIND = [  # tokens of a name or editor id, when no keyword or marker says
    (r"lighthouse", "lighthouse"), (r"wreck", "shipwreck"), (r"quarry", "quarry"), (r"mine(?!r)|smelter", "mine"),
    (r"prison|jail", "prison"), (r"fort\b|fort[A-Z_]|fortress|garrison", "fort"), (r"keep|castle|citadel", "keep"),
    (r"tower|watch|lookout|outpost", "tower"), (r"plantation|farm|homestead", "farm"), (r"mill|lumber", "mill"),
    (r"dock|port|harbou?r|pier|ferry", "dock"), (r"camp", "camp-outlaw"), (r"cave|grotto|cavern|den\b|hollow", "cave"),
    (r"temple|shrine|altar", "shrine"), (r"hist|grove", "grove"), (r"peak|summit|mount", "peak"),
    (r"ruin|xanmeer|ziggurat|crypt|tomb|barrow", "ruin"), (r"village|hamlet", "village"), (r"town", "town"),
    (r"city", "city"), (r"manor|estate|villa|plantation", "estate"), (r"ship\b", "ship"), (r"house|shack|hut", "homestead"),
]


def camel_words(s: str) -> str:
    s = re.sub(r"Location$|^marker\.|^cluster\.|Exterior\d*$", "", s or "")
    s = re.sub(r"^(DLC0?[12]|cc[A-Z]{3}SSE\d+)", "", s)
    return re.sub(r"(?<=[a-z])(?=[A-Z])|[_\-.]+", " ", s).strip()


def cand_name(c: dict) -> str:
    for n in (c.get("name"), (c.get("marker") or {}).get("name")):
        if n and not re.fullmatch(r".*\d+ -?\d+", n):
            return re.sub(r"\s*map ?marker( ?ref)?\s*", "", n, flags=re.I).strip() or n
    names = [n for n in c.get("interior_names") or [] if n.lower() not in ("ship", "house", "ruin", "ruins", "cavern")]
    if names:
        return names[0]
    edid = re.sub(r"(?i)map ?marker( ?ref)?", "", c.get("edid") or "")
    if edid and not edid.startswith("cluster"):
        return camel_words(edid)
    return f"{c.get('worldspace_edid') or 'world'} {c['cells'][0][0]},{c['cells'][0][1]}" if c.get("cells") else c["candidate_id"]


def ruin_culture(tags: dict) -> str:
    cult = {k: v for k, v in tags.items() if k in CULTURES}
    if not cult:
        return "ruin"
    top = max(cult, key=cult.get)
    return f"ruin-{'dunmer' if top == 'daedric' and cult.get('dunmer') else top}" if f"ruin-{top}" in RUINS else "ruin"


SETTLEMENTS = {"city", "town", "village", "hamlet"}
SETTLE_KW = {"LocTypeCity", "LocTypeTown", "LocTypeSettlement", "LocTypeDwelling", "LocTypeHabitation"}
SETTLE_MARKER = {"City", "Town", "Settlement", "SkyrimCity", "WindhelmCity", "RavenRockCity", "DLC02RavenRock"}
HOSTILE_KW = {"LocTypeDungeon", "LocTypeClearable", "LocTypeMilitaryFort", "LocTypeBanditCamp", "LocTypeVampireLair",
              "LocTypeWarlockLair", "LocTypeDraugrCrypt", "LocTypeFalmerHive", "LocTypeDwarvenAutomatons",
              "LocTypeForswornCamp", "LocTypeHagravenNest", "LocTypeAnimalDen", "LocTypeDragonPriestLair"}


def settled(c: dict) -> bool:
    """A settlement only on a settlement signal: Bethesda's keyword or map marker, or a built-up cluster of houses
    with people living in it (beds and furniture)."""
    kws = set(c.get("keywords") or [])
    if re.search(r"sanctuary|hideout|barrow|temple|cave|crypt|tomb|ruin|\bdun\b", f"{c.get('name')} {c.get('edid')}", re.I):
        return False  # a lair Bethesda files under a town keyword is still a lair
    if kws & SETTLE_KW or (c.get("marker") or {}).get("type") in SETTLE_MARKER:
        return True
    return bool("cluster" in kws or c.get("marker")) and c["counts"].get("building", 0) >= SMALL_CLUSTER \
        and (c["counts"].get("furniture", 0) > 0 or c.get("residents", 0) >= 3) and (c.get("residents", 0) > 0 or not c.get("enemies"))


SMALL_CLUSTER = 6   # buildings: a few huts with beds or furniture are a hamlet (a cluster with nobody in it, an empty one)


def cluster_kind(c: dict) -> tuple[str, str] | None:
    """A built-up cluster (or a bare map marker's cell) under a town's size (Mine.cs links a plugin's own buildings within 2048 units): ruin
    pieces of one tileset are a ruin of that culture, tents with people a camp (a tribe's when its tileset is a
    native people's), a few huts with beds or people a hamlet; None leaves it to the rules for big clusters."""
    t, b = c.get("tags") or {}, c["counts"].get("building", 0)
    res, en, furn = c.get("residents", 0), c.get("enemies", 0), c["counts"].get("furniture", 0)
    cult = culture_tags(c)
    top = max(cult, key=cult.get) if cult else None
    if t.get("ruin", 0) >= max(5, 0.3 * b) or (res == 0 and en > 0 and t.get("ruin", 0) >= 3):
        return ruin_culture(t), f"cluster of ruin pieces ({top or 'no'} tileset)"
    if t.get("camp", 0) >= 3 and b < 25 and (res or furn):
        return ("camp-tribal" if top in ("argonian", "dunmer", "bosmer", "khajiit") else "camp-outlaw"), "cluster of tents"
    if b < 40 and b >= SMALL_CLUSTER and (furn > 0 or res >= 3) and (res > 0 or not en):
        return "hamlet", f"cluster of {b} buildings, {res} people"
    return None


def hostile_people(c: dict) -> None:
    """In a place Bethesda types as a dungeon, a fort or a lair, everyone placed there is a foe (bandits, a
    garrison of the war): none of them is a resident."""
    if set(c.get("keywords") or []) & HOSTILE_KW and not set(c.get("keywords") or []) & SETTLE_KW:
        c["enemies"] = c.get("enemies", 0) + c.get("residents", 0)
        c["residents"] = 0


def classify(c: dict) -> tuple[str, str]:
    """(kind, why): a location keyword first, then the map marker's type, then the name, then the counts."""
    kws = set(c.get("keywords") or [])
    tags = c.get("tags") or {}
    res, en = c.get("residents", 0), c.get("enemies", 0)
    kind, why = None, ""
    own = f"{cand_name(c)} {c.get('edid') or ''}"
    if re.search(r"cave|grotto|cavern", own, re.I) and ("LocSetCave" in kws or (c.get("marker") or {}).get("type") == "Cave"):
        return "cave", "a cave by its name and keyword"
    if re.search(r"hrothgar|monastery", own, re.I):
        return "shrine", "a monastery by its name"
    for kw, k in KW_KIND:
        if kw in kws:
            kind, why = k, kw
            break
    if kind is None and c.get("marker") and MARKER_KIND.get(c["marker"]["type"]):
        kind, why = MARKER_KIND[c["marker"]["type"]], f"marker {c['marker']['type']}"
    if kind in (None, "landmark", "village"):
        inner = " ".join(c.get("interior_names") or [])
        hit = next(((rx, k) for rx, k in NAME_KIND if re.search(rx, own, re.I)), None) \
            or next(((rx, k) for rx, k in NAME_KIND if re.search(rx, inner, re.I)), None)
        for rx, k in [hit] if hit else []:
                if kind == "village" and k not in ("town", "city", "farm", "dock", "estate"):
                    break
                kind, why = k, f"name '{rx}'"
                break
    if kind == "fort" and re.search(r"temple|barrow|crypt|tomb|sanctuary|cave", own, re.I):
        kind, why = "ruin", f"a {why} named as a dungeon"
    if kind is None:
        if tags.get("ship", 0) >= 10:
            kind = "shipwreck"
        elif tags.get("ruin", 0) >= 5 or en > res:
            kind = "ruin"
        else:
            kind = "landmark"
        why = f"counts ({res} residents, {en} enemies)"
    blds = c["counts"].get("building", 0)
    if ("cluster" in kws and kind in (None, "landmark", "ruin", "homestead", "ship", "shipwreck")
            or not c.get("location") and kind in (None, "landmark")) and cluster_kind(c):
        kind, why = cluster_kind(c)
    if "cluster" in kws and tags.get("ruin", 0) < 0.3 * blds and (
            kind in ("ship", "landmark", "homestead", "shipwreck", None) and blds >= 40 or blds >= 150 and res >= 10):
        kind = "city" if blds >= 400 else "town" if blds >= 150 else "village"
        why = f"built-up cluster of {blds} buildings"
    if re.search(r"BYOHHouse", c.get("edid") or "") or (kind in ("town", "village") and res < 3 and blds < 25):
        kind, why = "homestead", why + "; a single house"
    if kind in SETTLEMENTS and not settled(c):
        kind = ruin_culture(tags) if en or tags.get("ruin", 0) >= 5 else "landmark"
        why += "; no settlement signal"
    if kind == "village" and res < 6:
        kind = "hamlet"
    if kind == "city" and res < 25:
        kind = "town"
    if kind in ("ruin", "ruin-nordic") and kind == "ruin":
        kind = ruin_culture(tags)
    if kind == "cave" and tags.get("mine", 0) >= 8 and tags.get("mine", 0) > tags.get("cave", 0):
        kind, why = "mine", why + "; mine tileset"
    if kind == "landmark" and (res + en) == 0 and c["counts"].get("refs", 0) < 30:
        kind = "landmark"
    return kind, why


def culture_tags(c: dict) -> dict:
    return {k: v for k, v in (c.get("tags") or {}).items() if k in CULTURES}


def description(c: dict) -> str:
    kind = c["kind"].replace("-", " ")
    ct = sorted(culture_tags(c).items(), key=lambda x: -x[1])[:2]
    other = sorted(((k, v) for k, v in (c.get("tags") or {}).items() if k not in CULTURES), key=lambda x: -x[1])[:3]
    wet = c.get("wet_cells", 0) / max(1, c.get("land_cells", 0))
    parts = [f"{c['name']}: a {kind}"]
    if ct:
        parts.append(f"built in {' and '.join(k for k, _ in ct)} style")
    if other:
        parts.append(f"with {', '.join(k for k, _ in other)} pieces")
    s = " ".join(parts) + "."
    s += f" {c.get('residents', 0)} people live there, {c.get('enemies', 0)} hostile."
    if c.get("interior_count"):
        names = ", ".join(c.get("interior_names")[:3]) if c.get("interior_names") else ""
        s += f" {c['interior_count']} interiors{(' (' + names + ')') if names else ''}."
    s += " By water." if wet > 0.4 else (" Near water." if wet > 0.1 else " Dry ground.")
    return s


def load_candidates() -> tuple[list[dict], dict]:
    status = json.loads((MINED / "status.json").read_text())
    out, dropped = [], Counter()
    for g, (_load, _mine, credit) in GROUPS.items():
        p = MINED / f"{g}.jsonl"
        if not p.exists() or not status.get(g, {}).get("mined"):
            continue
        seen = set()
        for line in p.open():
            c = json.loads(line)
            if not c.get("cells") or not c.get("worldspace"):
                dropped["no exterior"] += 1
                continue
            if {"LocTypeHold", "LocTypeHoldMajor", "LocTypeHoldCapital"} & set(c.get("keywords") or []) \
                    or re.search(r"Hold(Location)?$|Apocrypha|Worldspace|Region", c.get("edid") or ""):
                dropped["a hold or a whole worldspace"] += 1
                continue
            if c["counts"].get("refs", 0) < 15:
                dropped["under 15 refs"] += 1
                continue
            c["group"], c["credit"], c["name"] = g, credit, cand_name(c)
            if any(g == eg and (rx.search(c["name"]) or rx.search(c.get("edid") or "") or rx.search(c["candidate_id"]))
                   for eg, rx in EXCLUDE):
                dropped["owner excluded (Lilmoth)"] += 1
                continue
            sid = c["candidate_id"]
            n = 2
            while sid in seen:
                sid, n = f"{c['candidate_id']}.{n}", n + 1
            seen.add(sid)
            c["source_id"] = sid
            hostile_people(c)
            c["kind"], c["kind_why"] = classify(c)
            c["description"] = description(c)
            out.append(c)
    reps = physical_groups(out)
    dropped["aliases of one physical place"] = len(out) - len(reps)
    name_unnamed(reps)
    return reps, dict(dropped)


OVERHAULS = {"dawnofskyrim", "greyquarter", "dosgq"}   # mods that rebuild a vanilla town in its own cells
UNNAMED = re.compile(r"^\S+ -?\d+,-?\d+$")


QUARTER = 1024.0   # a quarter of a cell's side, the grain places are told apart at
CITY_WORLD = re.compile(r"^(Whiterun|Solitude|Markarth|Riften|Windhelm)World$")


def footprint(c: dict) -> set:
    """The quarter cells (QUARTER) that stand for a candidate when telling places apart: a bare map marker's own
    quarter, a cluster's bounds, else all its cells; an overhaul's cluster reaches a cell beyond it (it belongs to
    the town it extends); a walled city's own worldspace is one place whatever cells of it a candidate holds."""
    m = CITY_WORLD.match(c.get("worldspace_edid") or "") or re.match(
        r"^(Whiterun|Solitude|Markarth|Riften|Windhelm)Location$", c.get("edid") or "")
    if m:
        return {("city", m.group(1))}
    ws, q = c["worldspace"], QUARTER
    mk = c.get("marker") or {}
    if mk and not c.get("location") and "cluster" not in (c.get("keywords") or []):
        if mk.get("x") is not None:
            return {(ws, int(mk["x"] // q), int(mk["y"] // q))}
        cells = [mk["cell"]]
    elif c.get("box") and c.get("group") not in OVERHAULS:
        x0, y0, x1, y1 = c["box"]
        own = {(x, y) for x, y in c["cells"]}
        return {(ws, i, j) for i in range(int(x0 // q), int(x1 // q) + 1) for j in range(int(y0 // q), int(y1 // q) + 1)
                if (i // 4, j // 4) in own}
    elif c.get("group") in OVERHAULS:
        cells = {(x + dx, y + dy) for x, y in c["cells"] for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
    else:
        cells = c["cells"]
    return {(ws, 4 * x + i, 4 * y + j) for x, y in cells for i in range(4) for j in range(4)}


def physical_groups(cands: list[dict]) -> list[dict]:
    """One row per physical place: candidates whose cells overlap in one worldspace
    are one place (a location and its map marker, a mod's overhaul of a vanilla town). The richest (most refs)
    stands for the group; the rest are its aliases."""
    parent = list(range(len(cands)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    owner: dict = {}
    for i, c in enumerate(cands):
        for k in footprint(c):
            if k in owner:
                parent[find(i)] = find(owner[k])
            else:
                owner[k] = i
    groups = defaultdict(list)
    for i in range(len(cands)):
        groups[find(i)].append(cands[i])
    reps = []
    for members in groups.values():
        members.sort(key=lambda c: -c["counts"].get("refs", 0))
        rep = dict(members[0])
        rep["aliases"] = [m["source_id"] for m in members[1:]]
        town = next((m for m in members if m["group"] == "skyrim" and m.get("location")), None)
        if rep["group"] in OVERHAULS and town:  # an overhauled town keeps the town's name
            rep["name"] = f"{town['name']} ({rep['credit']})"
            rep["description"] = description(rep)
        if UNNAMED.match(rep["name"]):
            rep["name"] = next((m["name"] for m in members if not UNNAMED.match(m["name"])), rep["name"])
        reps.append(rep)
    return reps


def name_unnamed(reps: list[dict]) -> None:
    named = [(r["worldspace"], r["cells"][0], r["name"]) for r in reps if not UNNAMED.match(r["name"])]
    for r in reps:
        if not UNNAMED.match(r["name"]):
            continue
        x, y = r["cells"][0]
        near = min(((abs(cx - x) + abs(cy - y), n) for ws, (cx, cy), n in named if ws == r["worldspace"]), default=None)
        if near and near[0] <= 3:
            r["name"] = f"near {near[1]}"
            r["description"] = description(r)


def check_unique(srcs: list[dict]) -> None:
    """No two allocated sources stand on one cell of one worldspace."""
    seen: dict = {}
    for c in srcs:
        for k in footprint(c):
            if k in seen and seen[k] != c["source_id"]:
                raise AssertionError(f"allocated sources {seen[k]} and {c['source_id']} share cell {k}")
            seen[k] = c["source_id"]


def place_features() -> tuple[list[dict], dict]:
    """Our places, each with `population` set to the research's own estimate (newworld/sources/research/places),
    never the table's, which this match overwrites: a rerun on unchanged inputs writes the same numbers."""
    from tools.newworld.build_db import RESEARCH, load_json_dir
    est = {r["id"]: r.get("population") for r in load_json_dir(str(RESEARCH / "places" / "*.json"))}
    places = [json.loads(line) for line in (DB / "place.jsonl").open() if line.strip()]
    for p in places:
        p["population"] = est.get(p["id"])
    gives = defaultdict(list)
    for line in (DB / "place_give.jsonl").open():
        g = json.loads(line)
        gives[g["place_id"]].append(g)
    return places, gives


def scores(places, gives, cands, emb_p, emb_c) -> tuple[np.ndarray, dict]:
    P, C = len(places), len(cands)
    parts = {k: np.zeros((P, C), np.float32) for k in WEIGHTS}
    ckind = [c["kind"] for c in cands]
    res = np.array([c.get("residents", 0) for c in cands], float)
    en = np.array([c.get("enemies", 0) for c in cands], float)
    wet = np.array([c.get("wet_cells", 0) / max(1, c.get("land_cells", 0)) for c in cands])
    ints = np.array([c.get("interior_count", 0) for c in cands], float)
    size = np.array([max(max(c["footprint_m"]) if c.get("footprint_m") else 0, 40.0) if c.get("footprint_m")
                     else 58.0 * math.sqrt(len(c["cells"])) for c in cands])
    ctag = [culture_tags(c) for c in cands]
    text = np.clip((emb_p @ emb_c.T - 0.55) / 0.35, 0, 1)
    parts["text"][:] = text
    for i, p in enumerate(places):
        k = p["place_kind_id"]
        fit = KIND_FIT.get(k, {})
        parts["kind"][i] = [fit.get(ck, fit.get("ruin", 0.0) * 0.8 if ck.startswith("ruin") else 0.0) for ck in ckind]
        diam = 2 * (p.get("footprint_radius_m") or 60)
        s_size = np.exp(-np.abs(np.log(diam / size)) / 1.2)
        lived = p["status"] in LIVED
        pop = p.get("population") or 0
        if lived:
            s_pop = np.exp(-np.abs(np.log((pop + 1) / (res + 1))) / 1.5)
            parts["size"][i] = 0.5 * s_size + 0.5 * s_pop
            parts["status"][i] = np.where(res > 0, 1.0, 0.3)
        else:
            parts["size"][i] = s_size
            parts["status"][i] = np.where(res > 5, 0.3, 1.0)
        want_wet = bool(p.get("on_water")) or p.get("siting") in WET_SITING
        if p.get("siting") == "seabed" or k in ("sunken-ruin", "shipwreck"):
            parts["water"][i] = np.clip(wet * 1.5, 0, 1)
        elif want_wet:
            parts["water"][i] = np.clip(0.3 + wet, 0, 1)
        else:
            parts["water"][i] = 1 - 0.5 * wet
        want = CULTURE_WANT.get(k, ("argonian", "bosmer"))
        cs = []
        for t in ctag:
            tot = sum(t.values())
            if tot == 0:
                cs.append(0.5)
                continue
            good = sum(t.get(x, 0) for x in want) / tot
            nordic = t.get("nordic", 0) / tot
            cs.append(max(0.0, min(1.0, 0.35 + 0.65 * good - 0.5 * nordic)))
        parts["culture"][i] = cs
        gk = {g["give_kind_id"] for g in gives.get(p["id"], [])}
        want_int = bool(gk & {"combat-boss", "boss-chest", "inn-room"}) or k in ("mine", "cave", "prison", "keep")
        parts["interior"][i] = np.where((ints > 0) == want_int, 1.0, 0.4)
        _ = en
    # the same place by name (BM&V's Thorn for our Thorn): a bonus over the parts, kept as its own part
    parts["name"] = np.zeros((P, C), np.float32)
    cn = [norm(c["name"]) if c["group"] in NAME_GROUPS else "" for c in cands]
    for i, p in enumerate(places):
        pn = norm(p["name"])
        if len(pn) >= 4:
            parts["name"][i] = [1.0 if n == pn or (n.startswith(pn) and len(n) - len(pn) <= 4) else 0.0 for n in cn]
    total = sum(WEIGHTS[k] * parts[k] for k in WEIGHTS) + NAME_BONUS * parts["name"]
    return total, parts


def norm(s: str) -> str:
    return re.sub(r"[^a-z]", "", (s or "").lower())


POP_FLOOR = {"trader-general", "trader-innkeeper", "trader-blacksmith", "trader-apothecary", "trader-hunter",
             "trader-spells", "trader-jeweller", "trader-clothier", "trader-bookseller", "trader-fletcher", "trainer",
             "fence", "follower"}
def population(p: dict, gv: list, src: dict | None) -> tuple[int, str]:
    """The allocated source's residents, as the source layout was built for them (owner, 2026-11-12): no blend
    toward the record's estimate, no clamp to a kind's range. A place the record leaves empty stays 0; never fewer
    than the people its gives name; a source with no counted residents falls back to the record's estimate."""
    before = p.get("population") or 0
    if p["status"] not in LIVED and before == 0:
        return 0, f"{p['status']}: the record says nobody lives here"
    need = sum(g.get("count", 1) for g in gv if g["give_kind_id"] in POP_FLOOR)
    base = (src or {}).get("residents", 0)
    if base == 0:
        pop, why = max(before, need), f"fallback: the source counts no residents; the record's estimate of {before} kept"
    else:
        pop, why = base, f"the source's {base} resident{'' if base == 1 else 's'}"
    if pop < need:
        pop = need
        why += f"; raised to the {need} people its gives name"
    return int(pop), why


def repopulate() -> int:
    """Rewrite only the population of each allocated row from the committed match (no re-match, no model)."""
    places, gives = place_features()
    byid = {p["id"]: p for p in places}
    src = {json.loads(line)["id"]: json.loads(line) for line in (MATCH / "source_place.jsonl").open() if line.strip()}
    rows = [json.loads(line) for line in (MATCH / "place_source.jsonl").open() if line.strip()]
    for r in rows:
        if r["rank"] == 0 and r["place_id"] in byid:
            p = byid[r["place_id"]]
            pop, why = population(p, gives.get(p["id"], []), src.get(r["source_place_id"]))
            r.update(population_before=p.get("population"), population_after=pop, population_why=why)
    write_jsonl(MATCH / "place_source.jsonl", rows)
    a0 = [r for r in rows if r["rank"] == 0]
    print(f"{len(a0)} places; population {sum(r['population_before'] or 0 for r in a0)} estimated -> "
          f"{sum(r['population_after'] for r in a0)} from sources")
    return 0


def main(argv: list[str]) -> int:
    if argv[:1] == ["--population"]:
        return repopulate()
    from scipy.optimize import linear_sum_assignment
    from tools.places.search.embed import Embedder
    cands, dropped = load_candidates()
    places, gives = place_features()
    emb = Embedder()
    emb_p = emb([f"{p['place_kind_id'].replace('-', ' ')}: {p.get('summary') or p['name']}" for p in places])
    emb_c = emb([c["description"] for c in cands])
    total, parts = scores(places, gives, cands, emb_p, emb_c)
    pid = {p["id"]: i for i, p in enumerate(places)}
    # fixed allocations leave the pool first
    fixed = {}
    for place_id, (source_id, rx) in FIXED.items():
        js = [j for j, c in enumerate(cands) if rx.search(c["source_id"]) or any(rx.search(a) for a in c.get("aliases") or [])]
        fixed[place_id] = (source_id, js[0] if js else None, js)  # every piece of the fixed place leaves the pool
    cost = np.empty_like(total)
    for i, p in enumerate(places):
        cost[i] = (1 - total[i]) * IMPORTANCE_WEIGHT[p.get("importance") or 1]
    big = 1e6
    for place_id, (_sid, j, js) in fixed.items():
        for k in js:
            cost[:, k] = big
        if j is not None:
            cost[pid[place_id], :] = big
            cost[pid[place_id], j] = 0
    rows, cols = linear_sum_assignment(cost)
    alloc = dict(zip(rows.tolist(), cols.tolist()))
    check_unique([cands[j] for j in alloc.values()])
    MATCH.mkdir(parents=True, exist_ok=True)
    used: dict[str, dict] = {}
    match_rows, ranked = [], {}
    for i, p in enumerate(places):
        order = np.argsort(-total[i])
        j0 = alloc[i]
        alts = [int(j) for j in order if int(j) != j0][:3]
        ranked[p["id"]] = [int(j) for j in order[:10]]
        for rank, j in enumerate([j0] + alts):
            c = cands[j]
            sid = c["source_id"]
            if rank == 0 and p["id"] in fixed:
                sid = fixed[p["id"]][0]
            used.setdefault(sid, dict(c, source_id=sid))
            part = {k: round(float(parts[k][i, j]), 3) for k in (*WEIGHTS, "name")}
            why = (f"{c['kind']} ({c['kind_why']}) for a {p['place_kind_id']}; best parts: "
                   + ", ".join(f"{k} {v:.2f}" for k, v in sorted(part.items(), key=lambda x: -x[1] * WEIGHTS.get(x[0], NAME_BONUS))[:3]))
            row = {"place_id": p["id"], "rank": rank, "source_place_id": sid, "score": round(min(1.0, float(total[i, j])), 3),
                   **{f"score_{k}": v for k, v in part.items()}, "why": why}
            if rank == 0:
                pop, pwhy = population(p, gives.get(p["id"], []), c)
                row.update(population_before=p.get("population"), population_after=pop, population_why=pwhy)
                if p["id"] in fixed:
                    row["why"] = "fixed: the place is drafted from this source; " + why
            match_rows.append(row)
    src_rows, ext_rows = [], []
    for sid, c in sorted(used.items()):
        src_rows.append({
            "id": sid, "title": f"{c['name']} ({Path(c['plugin']).stem})", "name": c["name"], "plugin": c["plugin"],
            "mod_id": c["credit"], "mined_group": c["group"], "kind": c["kind"], "kind_why": c["kind_why"],
            "worldspace": c["worldspace"], "worldspace_edid": c.get("worldspace_edid"), "location": c.get("location"),
            "cells": len(c["cells"]), "interiors": c.get("interior_count", 0), "residents": c.get("residents", 0),
            "enemies": c.get("enemies", 0), "buildings": c["counts"].get("building", 0), "refs": c["counts"].get("refs", 0),
            "footprint_m": max(c["footprint_m"]) if c.get("footprint_m") else None,
            "wet_share": round(c.get("wet_cells", 0) / max(1, c.get("land_cells", 0)), 2),
            "aliases": ",".join(c.get("aliases") or []) or None,
            "culture_tags": ",".join(k for k, _ in sorted(culture_tags(c).items(), key=lambda x: -x[1])[:3]) or None,
            "description": c["description"],
        })
        if sid in FIXED.get("helstrom", ("",))[0:1]:
            continue
        load = GROUPS[c["group"]][0]
        ext_rows.append({"source_id": sid, "title": f"{c['name']} ({Path(c['plugin']).stem}, mined)", "plugins": load,
                         "worldspace": c["worldspace"], "cells": sorted(c["cells"], key=lambda x: (x[1], x[0])),
                         "follow_doors": True,
                         **({"extent_m": [c["footprint_m"][0], c["footprint_m"][1]]} if c.get("footprint_m") else {})})
    write_jsonl(MATCH / "source_place.jsonl", src_rows)
    write_jsonl(MATCH / "place_source.jsonl", match_rows)
    write_jsonl(ROWS, ext_rows)
    RANKED.parent.mkdir(parents=True, exist_ok=True)
    RANKED.write_text(json.dumps({
        "dropped": dropped, "candidates": len(cands),
        "by_group": Counter(c["group"] for c in cands), "kinds": Counter(c["kind"] for c in cands),
        "top10": {pid_: [{"source_id": cands[j]["source_id"], "name": cands[j]["name"], "kind": cands[j]["kind"],
                          "group": cands[j]["group"], "score": round(float(total[pid[pid_], j]), 3)} for j in js]
                  for pid_, js in ranked.items()},
    }))
    a0 = [r for r in match_rows if r["rank"] == 0]
    print(f"{len(cands)} candidates, {len(a0)} places allocated, {len(src_rows)} sources kept; mean score "
          f"{np.mean([r['score'] for r in a0]):.3f}; dropped {dropped}")
    return 0


def write_jsonl(path: Path, rows: list[dict]) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    tmp.replace(path)
