"""Check place records against their tier and the ground before they are written (decision 0040, place-research).

    python3 -m tools.newworld.record_check            # every place in the built database
    python3 -m tools.newworld.record_check jal-veesa  # one or more places

Three checks, each a fault line per place; exit 1 when any fault stands:
- population: an inhabited settlement's population sits inside its tier's range (a seat may be up to 25% over),
  and the tiers keep their order (no outpost above a village's smallest, and so on up to the metropolises);
- water: every water word of the summary, notes and gives names water the ground has within reach (the classified
  water raster, `out/newworld/water_classified.png`), and the siting agrees with the nearest water;
- Hist: every Hist pool is a pool of sap, never of water.
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict

from tools.newworld import frame as f

M_PER_PX = f.UNITS_PER_PX / f.UNITS_PER_METRE
TIER_ORDER = ("minor", "outpost", "village", "town", "small-city", "large-city", "metropolis")
GROUPS = {"sea": {"ocean", "bay", "shallow-coast", "estuary"}, "river": {"river", "stream", "estuary"},
          "lake": {"lake", "pond"}, "swamp": {"blackwater-swamp", "green-marsh"}}
# (name, words, water groups that make them true, reach in metres)
WATER_WORDS = (
    ("river", r"\b(rivers?|creeks?|streams?|weirs?|rapids|ford|riverbank)\b", ("river",), 700),
    ("harbour", r"\b(harbou?rs?|quays?|wharf|wharves|slipway)\b", ("sea", "river", "lake"), 500),
    ("docks", r"\b(docks?|jett(?:y|ies)|piers?|boathouses?)\b", ("any",), 300),
    ("boats", r"\b(boats?|canoes?|punts?|rafts?|barges?|ferr(?:y|ies))\b", ("any",), 500),
    ("fishing", r"\b(fishing|fish traps?)\b", ("any",), 500),
    ("over-water", r"\b(over (?:the )?water|above the water|on the water)\b", ("any",), 150),
    ("lake", r"\b(lakes?|lagoons?|meres?)\b", ("lake", "swamp"), 900),
    ("sea", r"\b(sea|ocean|tides?|tidal|surf|beach|shoreline)\b", ("sea",), 2500),
)
NAMED = re.compile(r"\b(sea of|Sea-?Folk|river-?folk|coast road|river[- ]road|rivers? forks?)\b|\b[A-Z][a-z]+ (River|Creek|Weir)\b")
NEGATED = re.compile(r"\b(no|not|without|never|dry|nor|far from|away from|lacks?|none)\b", re.I)
SITING = {"riverbank": ("river", 700), "coast": ("sea", 900), "lakeshore": ("lake", 700), "island": ("any", 400)}
HIST_POOL = re.compile(r"\bHist\b.*\b(pool|pond)s?\b|\b(pool|pond)s?\b.*\bHist\b", re.I)
# the aspects that describe the place as it stands (history and faith may name water elsewhere)
PLACE_ASPECTS = ("summary", "overview", "present", "look", "economy", "dangers", "gives")


def sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.;])\s+", text or "") if s]


def population_faults(places: list[dict], tier_of: dict[str, tuple[str, int, int, bool]]) -> list[tuple[str, str]]:
    """places: rows with id, symbol_id, status, population; tier_of: symbol id -> (tier, lo, hi, seat)."""
    out, by_tier = [], defaultdict(list)
    for p in places:
        if p["symbol_id"] not in tier_of or p["status"] != "inhabited":
            continue
        tier, lo, hi, seat = tier_of[p["symbol_id"]]
        pop = p["population"] or 0
        top = hi * 1.25 if seat else hi
        if not lo <= pop <= top:
            out.append((p["id"], f"population {pop} is outside its tier {tier} ({lo}-{hi:g})"))
        by_tier[tier].append((pop, p["id"]))
    for low, high in zip(TIER_ORDER, TIER_ORDER[1:]):
        if by_tier[low] and by_tier[high] and max(by_tier[low])[0] > min(by_tier[high])[0]:
            (a, aid), (b, bid) = max(by_tier[low]), min(by_tier[high])
            out.append((bid, f"{high} has {b} people, fewer than the {low} {aid} ({a})"))
    return out


def water_faults(texts: dict[str, str], siting: str | None, near: dict[str, float]) -> list[str]:
    """texts: aspect -> prose; near: water group (and 'any') -> metres to the nearest such water."""
    out = []
    for name, rx, groups, reach in WATER_WORDS:
        d = min(near[g] for g in groups)
        if d <= reach:
            continue
        for aspect, text in texts.items():
            if aspect not in PLACE_ASPECTS:
                continue
            for s in sentences(text):
                if NEGATED.search(s) or (name in ("river", "sea") and NAMED.search(s)):
                    continue
                m = re.search(rx, s, re.I)
                if m:
                    out.append(f"{aspect} says '{m.group(0)}' but the nearest {'/'.join(groups)} water is {d:.0f} m "
                               f"away (reach {reach} m): \"{s[:100]}\"")
    if siting in SITING:
        g, reach = SITING[siting]
        if near[g] > reach:
            out.append(f"siting '{siting}' but the nearest {g} water is {near[g]:.0f} m away (reach {reach} m)")
    return out


def hist_faults(texts: dict[str, str]) -> list[str]:
    return [f"{aspect}: a Hist pool not named as sap: \"{s[:100]}\"" for aspect, text in texts.items()
            for s in sentences(text) if HIST_POOL.search(s) and not re.search(r"\bsap\b", s, re.I)]


class Ground:
    """Metres from a map point to the nearest water of each group, from the classified water raster."""

    def __init__(self) -> None:
        import numpy as np
        from PIL import Image
        from scipy import ndimage

        lab = np.array(Image.open(f.OUT / "water_classified.png")).astype(np.int32)
        kinds = {w["raster_index"]: w["water_kind_id"]
                 for w in json.loads((f.OUT / "water_classified.json").read_text())}
        self.edt = {}
        for g, ks in GROUPS.items():
            mask = np.isin(lab, [i for i, k in kinds.items() if k in ks])
            self.edt[g] = ndimage.distance_transform_edt(~mask) * M_PER_PX
        self.edt["any"] = ndimage.distance_transform_edt(lab == 0) * M_PER_PX

    def near(self, px: float, py: float) -> dict[str, float]:
        x, y = int(px), int(py)
        return {g: float(a[y, x]) for g, a in self.edt.items()}


def main(argv: list[str]) -> int:
    from tools.argonia_world import db

    w = db.open("newworld")
    places = [dict(p.__dict__) if hasattr(p, "__dict__") else dict(p) for p in w.rows("place")]
    tiers = {t.id: t for t in w.rows("settlement_tier")}
    tier_of = {s.id: (s.settlement_tier_id, tiers[s.settlement_tier_id].population_lo,
                      tiers[s.settlement_tier_id].population_hi, s.id.endswith("-seat"))
               for s in w.rows("symbol") if s.settlement_tier_id}
    texts = defaultdict(dict)
    for n in w.rows("place_note"):
        if n.aspect_id != "source":
            texts[n.place_id][n.aspect_id] = n.text
    for g in w.rows("place_give"):
        texts[g.place_id]["gives"] = texts[g.place_id].get("gives", "") + " " + (g.detail or "") + "."
    want = set(argv) or {p["id"] for p in places}
    faults = [(pid, m) for pid, m in population_faults(places, tier_of) if pid in want]
    ground = Ground()
    for p in places:
        if p["id"] not in want:
            continue
        t = dict(texts[p["id"]], summary=p["summary"] or "")
        faults += [(p["id"], m) for m in water_faults(t, p["siting"], ground.near(p["px"], p["py"]))]
        faults += [(p["id"], m) for m in hist_faults(t)]
    for pid, m in faults:
        print(f"{pid}: {m}")
    print(f"{len(faults)} faults in {len(want)} places")
    return 1 if faults else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
