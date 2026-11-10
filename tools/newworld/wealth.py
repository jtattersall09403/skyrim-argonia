"""Each place's wealth and its band on the stocking scale (lane S0; scale in newworld/sources/stock/scale.json,
contract docs/design/place-studio.md "Stock").

A place's wealth is derived from its facts, never from danger alone: its settlement tier or kind, importance,
population, trade position (roads at it, a major road, a boat stop, its traders) and a mechanical read of its
economy note. Its danger enters as its reward band (tools/newworld/place_danger.py): the band's tier is the best
the way in and the fight inside hold. Whose goods they are sets the ceiling (scale.json `ceiling_why`): a friendly
or wary place's ceiling is its wealth band's, as a city's is, whatever the land round it; a hostile lived place's is
the higher of its reward tier and its wealth's; an unpeopled place's is its reward tier. The figure, its band (P1..P5) and the reason are kept in `newworld/sources/stock/place_wealth.json`,
one row per place; a row's `owner` block overrules the derived band for that place and is never touched by a
rederive. build_db reads the file into the tables `place_wealth` (with the scale's lookups `stock_tier`,
`place_wealth_band`, `person_wealth_band`).

    python3 -m tools.newworld.wealth derive      # rewrite the derived part of every row from the database
    python3 -m tools.newworld.wealth show <place_id>
"""
from __future__ import annotations

import json
import math
import re
import sys
from collections import defaultdict

from tools.argonia_world import db
from tools.newworld import frame as f

STOCK = f.ROOT / "sources" / "stock"
SCALE = STOCK / "scale.json"
WEALTH = STOCK / "place_wealth.json"
LIVED = {"inhabited", "garrisoned", "occupied"}
OWN_GOODS = {"friendly", "wary"}       # dispositions whose goods are the people's own: the ceiling is the wealth's


def ceiling_of(disposition: str, danger_tier: str, wealth_tier: str, rank: dict) -> tuple[str, str]:
    """A lived place's ceiling and its reason (scale.json `ceiling_why`)."""
    if disposition in OWN_GOODS:
        return wealth_tier, f"{disposition}: its people's own goods, its wealth's {wealth_tier}"
    top = max(danger_tier, wealth_tier, key=lambda t: rank[t])
    return top, f"{disposition}: the higher of wealth {wealth_tier} and reward tier {danger_tier}"


def scale() -> dict:
    return json.loads(SCALE.read_text(encoding="utf-8"))


def _gives(w) -> dict[str, list]:
    out = defaultdict(list)
    for g in w.rows("place_give"):
        out[g.place_id].append(g)
    return out


def _roads(w) -> dict[str, dict]:
    node_place = {n.id: n.place_id for n in w.rows("road_node") if n.place_id}
    out = defaultdict(lambda: {"roads": 0, "major": False})
    for r in w.rows("road"):
        for nid in (r.from_node_id, r.to_node_id):
            pid = node_place.get(nid)
            if pid:
                out[pid]["roads"] += 1
                out[pid]["major"] |= r.road_class_id == "major"
    return out


def economy_read(text: str, rules: dict) -> tuple[int, list[str]]:
    """A mechanical read of the economy note: +each distinct trade or riches word, - each want word."""
    t = (text or "").lower()
    neg = [p for p in rules["economy_minus"] if re.search(p, t)]
    for p in neg:                                    # 'does not trade' is not trade
        t = re.sub(p, " ", t)
    pos = [p for p in rules["economy_plus"] if re.search(p, t)]
    pts = min(len(pos) * rules["economy_plus_each"], rules["economy_cap"]) - \
        min(len(neg) * rules["economy_minus_each"], rules["economy_cap"])
    word = lambda p: re.sub(r"[^a-z ]", "", p.replace("\\b", ""))      # noqa: E731
    return pts, [f"+{word(p)}" for p in pos] + [f"-{word(p)}" for p in neg]


def derive(w) -> list[dict]:
    sc = scale()
    rules, tiers = sc["wealth"], {t["id"]: t for t in sc["tiers"]}
    bands = sc["place_wealth_bands"]
    danger_tier = sc["danger_tier"]
    gives, roads = _gives(w), _roads(w)
    notes = {r["place_id"]: r["text"] for r in w.query("SELECT place_id, text FROM place_note WHERE aspect_id='economy'")}
    sym_tier = {s.id: s.settlement_tier_id for s in w.rows("symbol")}
    rows = []
    danger = {r.place_id: r for r in w.rows("place_danger")}
    rank = {t: v["rank"] for t, v in tiers.items()}
    for p in w.rows("place"):
        rb, disp = danger[p.id].reward_band_id, danger[p.id].disposition_id
        dt = danger_tier[rb]
        lived = (p.status in LIVED) and (p.population or 0) > 0
        row = {"id": p.id, "name": p.name, "disposition_id": disp, "reward_band_id": rb, "danger_tier": dt}
        if not lived:
            row.update(wealth_score=None, band=None, open_tier=tiers[dt]["below"], ceiling_tier=dt,
                       why=f"{p.status or 'unpeopled'}: no residents' wealth; the reward band {rb} "
                           f"sets it ({dt} at the hardest spot, {tiers[dt]['below']} along the way)")
            rows.append(row)
            continue
        parts = []
        st = sym_tier.get(p.symbol_id)
        base = rules["tier_points"].get(st) if st in rules["tier_points"] and p.place_kind_id in rules["settled_kinds"] \
            else rules["kind_points"].get(p.place_kind_id, 4)
        parts.append((base, f"{st if p.place_kind_id in rules['settled_kinds'] else p.place_kind_id} {base}"))
        imp = (p.importance or 1) * rules["importance_each"]
        parts.append((imp, f"importance {p.importance} {imp}"))
        pop = min(round(rules["population_log2"] * math.log2((p.population or 0) + 1)), rules["population_cap"])
        parts.append((pop, f"population {p.population} {pop}"))
        rd = roads.get(p.id, {"roads": 0, "major": False})
        tr = min(rd["roads"] * rules["road_each"], rules["road_cap"]) + (rules["major_road"] if rd["major"] else 0)
        ks = [g.give_kind_id for g in gives[p.id]]
        boat = rules["boat"] if "boat-stop" in ks else 0
        traders = min(sum(k.startswith("trader-") or k == "fence" for k in ks) * rules["trader_each"], rules["trader_cap"])
        parts.append((tr + boat + traders, f"trade {tr + boat + traders} ({rd['roads']} roads"
                      f"{', major' if rd['major'] else ''}{', boat stop' if boat else ''}, {traders // max(rules['trader_each'], 1)} traders)"))
        ep, words = economy_read(notes.get(p.id, ""), rules)
        parts.append((ep, f"economy {ep:+d} ({' '.join(words) or 'no telling words'})"))
        score = max(0, sum(x for x, _ in parts))
        band = next(b for b in reversed(bands) if score >= b["min_score"])
        top, cwhy = ceiling_of(disp, dt, band["ceiling_tier"], rank)
        row.update(wealth_score=score, band=band["id"], open_tier="T1", ceiling_tier=top,
                   why=f"score {score} = " + " + ".join(s for _, s in parts) + f" -> {band['id']} {band['label']}; "
                       f"ceiling {top} ({cwhy}; reward band {rb} {dt})")
        rows.append(row)
    return rows


def write(rows: list[dict]) -> None:
    old = {r["id"]: r for r in json.loads(WEALTH.read_text())["places"]} if WEALTH.exists() else {}
    out = []
    for r in rows:
        r = dict(r)
        r["owner"] = (old.get(r["id"]) or {}).get("owner")
        out.append(r)
    doc = {"about": "Each place's derived wealth and its band on the stocking scale (tools/newworld/wealth.py "
                    "derive). `owner` overrules: {band, ceiling_tier?, why}; a rederive keeps it.",
           "places": sorted(out, key=lambda r: r["id"])}
    WEALTH.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def load(w) -> None:
    """build_db: the scale's lookups and every place's row into the database."""
    sc = scale()
    for t in sc["tiers"]:
        w.insert("stock_tier", id=t["id"], rank=t["rank"], label=t["label"], ref_level=t["ref_level"],
                 enchant_grade=t["enchant_grade"], lock_level_id=t["lock"], gold_lo=t["gold"][0], gold_hi=t["gold"][1],
                 value_max=t["value_max"], about=t["about"])
    for b in sc["place_wealth_bands"]:
        w.insert("place_wealth_band", id=b["id"], rank=b["rank"], label=b["label"], min_score=b["min_score"],
                 ceiling_tier_id=b["ceiling_tier"], trader_gold_mult=b["trader_gold_mult"],
                 people=b["people"], about=b["about"])
    for b in sc["person_wealth_bands"]:
        w.insert("person_wealth_band", id=b["id"], rank=b["rank"], label=b["label"], carried_lo=b["carried"][0],
                 carried_hi=b["carried"][1], home_lo=b["home"][0], home_hi=b["home"][1], top_tier=b["top_tier"],
                 about=b["about"])
    rows = {r["id"]: r for r in json.loads(WEALTH.read_text())["places"]}
    missing = [p.id for p in w.rows("place") if p.id not in rows]
    if missing:
        raise ValueError(f"place_wealth.json lacks {len(missing)} places (run tools.newworld.wealth derive): {missing[:5]}")
    rank = {t["id"]: t["rank"] for t in sc["tiers"]}
    band_ceiling = {b["id"]: b["ceiling_tier"] for b in sc["place_wealth_bands"]}
    for pid, r in sorted(rows.items()):
        o = r.get("owner") or {}
        band = o.get("band", r["band"])
        if o.get("ceiling_tier"):
            ceiling = o["ceiling_tier"]
        elif "band" in o:                    # an overruled band moves the ceiling with it, by the same rule
            ceiling = ceiling_of(r["disposition_id"], r["danger_tier"], band_ceiling.get(band, "T1"), rank)[0]
        else:
            ceiling = r["ceiling_tier"]
        w.insert("place_wealth", place_id=pid, wealth_score=r["wealth_score"], place_wealth_band_id=band,
                 open_tier_id=r["open_tier"], ceiling_tier_id=ceiling,
                 why=(f"owner: {o['why']} (derived: {r['why']})" if o else r["why"]), by="owner" if o else "derived")


def main(argv: list[str]) -> int:
    if argv[:1] == ["derive"]:
        rows = derive(db.open(f.ROOT))
        write(rows)
        from collections import Counter
        print(f"{len(rows)} places -> {WEALTH}")
        print(dict(sorted(Counter(r["band"] or "none" for r in rows).items())))
        return 0
    if argv[:1] == ["show"] and len(argv) > 1:
        rows = {r["id"]: r for r in json.loads(WEALTH.read_text())["places"]}
        print(json.dumps(rows[argv[1]], indent=1, ensure_ascii=False))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
