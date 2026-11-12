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
    "abandoned-village": {"village": 0.85, "hamlet": 0.85, "ruin-argonian": 0.7, "ruin": 0.6, "homestead": 0.5},
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
    "velothi-ruin": {"ruin-dunmer": 1, "ruin-daedric": 0.7, "ruin": 0.55, "ruin-dwemer": 0.5},
    "ayleid-ruin": {"ruin-ayleid": 1, "ruin": 0.55, "ruin-imperial": 0.45},
    "kothringi-ruin": {"ruin-argonian": 1, "ruin": 0.6, "cave": 0.45, "ruin-ayleid": 0.4},
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
    "kothringi-ruin": ("argonian",), "lilmothiit-ruin": ("argonian",), "sunken-ruin": ("argonian",),
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


def classify(c: dict) -> tuple[str, str]:
    """(kind, why): a location keyword first, then the map marker's type, then the name, then the counts."""
    kws = set(c.get("keywords") or [])
    tags = c.get("tags") or {}
    res, en = c.get("residents", 0), c.get("enemies", 0)
    kind, why = None, ""
    for kw, k in KW_KIND:
        if kw in kws:
            kind, why = k, kw
            break
    if kind is None and c.get("marker") and MARKER_KIND.get(c["marker"]["type"]):
        kind, why = MARKER_KIND[c["marker"]["type"]], f"marker {c['marker']['type']}"
    text = f"{cand_name(c)} {c.get('edid') or ''} {' '.join(c.get('interior_names') or [])}"
    if kind in (None, "landmark", "village"):
        for rx, k in NAME_KIND:
            if re.search(rx, text, re.I):
                if kind == "village" and k not in ("town", "city", "farm", "dock", "estate"):
                    break
                kind, why = k, f"name '{rx}'"
                break
    if kind is None:
        if res >= 30:
            kind = "town"
        elif res >= 10:
            kind = "village"
        elif res >= 3:
            kind = "hamlet"
        elif tags.get("ship", 0) >= 10:
            kind = "shipwreck"
        elif tags.get("ruin", 0) >= 5 or en > res:
            kind = "ruin"
        else:
            kind = "landmark"
        why = f"counts ({res} residents, {en} enemies)"
    blds = c["counts"].get("building", 0)
    if "cluster" in kws and tags.get("ruin", 0) < 0.3 * blds and (
            kind in ("ship", "landmark", "homestead", "shipwreck", None) and blds >= 40 or blds >= 150 and res >= 10):
        kind = "city" if blds >= 400 else "town" if blds >= 150 else "village"
        why = f"built-up cluster of {blds} buildings"
    if re.search(r"BYOHHouse", c.get("edid") or "") or (kind in ("town", "village") and res < 3 and blds < 25):
        kind, why = "homestead", why + "; a single house"
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
            c["kind"], c["kind_why"] = classify(c)
            c["description"] = description(c)
            out.append(c)
    return out, dict(dropped)


def place_features() -> tuple[list[dict], dict]:
    places = [json.loads(line) for line in (DB / "place.jsonl").open() if line.strip()]
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
TIER_RANGE = {"city": (40, 400), "town": (18, 80), "village": (8, 30), "hamlet": (4, 14), "outpost": (2, 10),
              "tribal-camp": (5, 20), "outlaw-camp": (6, 24), "fort": (6, 30), "keep": (4, 24), "prison": (6, 30),
              "farm": (2, 8), "homestead": (1, 5), "estate": (4, 14), "logging-camp": (3, 10), "mine": (2, 12),
              "lighthouse": (1, 5), "ferry": (2, 6), "station": (3, 12), "belvedere": (2, 8), "cave": (0, 8),
              "quarry": (0, 8), "peak": (0, 2), "landmark": (0, 2)}


def population(p: dict, gv: list, src: dict | None) -> tuple[int, str]:
    """Baseline the allocated source's residents, then move toward what the record promises: halfway (in log) to
    the record's own estimate, bounded by the kind's range, never under the people its gives name."""
    before = p.get("population") or 0
    if p["status"] not in LIVED and before == 0:
        return 0, f"{p['status']}: the record says nobody lives here"
    need = sum(g.get("count", 1) for g in gv if g["give_kind_id"] in POP_FLOOR)
    base = (src or {}).get("residents", 0)
    lo, hi = TIER_RANGE.get(p["place_kind_id"], (0, 400))
    if base == 0:
        pop, why = max(before, need), f"source has no residents; record's {before} kept"
    else:
        f = math.sqrt(max(before, 1) / base)
        f = min(2.0, max(0.5, f))
        pop = round(base * f)
        why = f"source {base} residents x{f:.2f} toward the record's {before}"
    if pop < lo or pop > hi:
        pop = min(max(pop, lo), hi)
        why += f"; held to a {p['place_kind_id']}'s {lo}-{hi}"
    if pop < need:
        pop = need
        why += f"; raised to the {need} people its gives name"
    return int(pop), why


def main(argv: list[str]) -> int:
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
        j = next((j for j, c in enumerate(cands) if rx.search(c["source_id"])), None)
        fixed[place_id] = (source_id, j)
    cost = np.empty_like(total)
    for i, p in enumerate(places):
        cost[i] = (1 - total[i]) * IMPORTANCE_WEIGHT[p.get("importance") or 1]
    big = 1e6
    for place_id, (_sid, j) in fixed.items():
        if j is not None:
            cost[:, j] = big
            cost[pid[place_id], :] = big
            cost[pid[place_id], j] = 0
    rows, cols = linear_sum_assignment(cost)
    alloc = dict(zip(rows.tolist(), cols.tolist()))
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
