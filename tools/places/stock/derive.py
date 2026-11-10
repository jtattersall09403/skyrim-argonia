"""The measurable part of stocking a place: a first stock source, every row with its reason, for the place-stock
skill to read, correct and complete by hand.

    python -m tools.places stock derive <place_id> [--out DIR] [--to PATH]

Writes the shape of `newworld/sources/stock/places/<place_id>.json` (contract: docs/design/place-studio.md, Stock)
to --to (default out/places/stock/<place_id>.derived.json; never the source file itself). From:
- the split (classify): which containers are significant, and what the source held that is taken out;
- the place's facts in the database: its wealth band and ceiling (place_wealth), danger, culture, goods (place_good)
  and promises (place_give); each person's role, household and wealth band (person);
- the scale (scale.json): tier materials, gold, locks, security, budgets, traders, provenance;
- the road tables, for provenance: the road distance to the nearest place that makes a thing, or to an import gate.
A row of the stock source that holds the owner's own words (a reason or note at the statement tier OWNER_STATED,
which the studio's edits write) is never overwritten: it stands in the draft as it is, and the difference is reported.
Variety comes from facts, never from dice: a household's size sets where in its band's gold range its savings fall,
a person's trade picks their tool, and every choice of a base is the first by value and key among those that fit.
"""
from __future__ import annotations

import argparse
import heapq
import re
import json
from collections import defaultdict
from pathlib import Path

from tools.argonia_world import db
from tools.places.stock import split
from tools.places.stock.classify import classify
from tools.places.stock.place import Place

ARMOUR_SLOTS = ("ArmorCuirass", "ArmorBoots", "ArmorGauntlets", "ArmorHelmet")
ROLE_WEAPON = {"guard": "WeapTypeSword", "smith": "WeapTypeWarhammer", "boatman": "WeapTypeDagger",
               "carter": "WeapTypeDagger",
               "resident": "WeapTypeDagger", "merchant": "WeapTypeDagger", "apothecary": "WeapTypeDagger",
               "spell-trader": "WeapTypeDagger", "innkeeper": "WeapTypeDagger"}
TRADER_LISTS = {  # what a trader kind sells: (slot or kind, types) at each tier from T1 to the place's best
    "trader-blacksmith": [("weapon", ("WeapTypeSword", "WeapTypeDagger", "WeapTypeWarAxe", "WeapTypeMace")),
                          ("armour", ("ArmorCuirass", "ArmorBoots", "ArmorGauntlets", "ArmorHelmet", "ArmorShield"))],
    "trader-general": [("weapon", ("WeapTypeDagger", "WeapTypeBow")), ("soul-gem", ()), ("potion", ("RestoreHealth",))],
    "trader-apothecary": [("potion", ("RestoreHealth", "RestoreMagicka", "RestoreStamina"))],
}


class Picker:
    """The first base by value and key that has every keyword asked for: unenchanted, named, never a never-material."""

    def __init__(self, rec, scale):
        self.rec, self.scale = rec, scale
        self.never = set(scale["never"]["materials"])
        self.words = [w.lower() for w in scale["never"]["edid_words"]]
        self.scale_mats = {m for t in scale["tiers"] for s in ("weapon", "armour") for m in t[s]}
        self.by_edid = {}
        self.items = []
        for k, r in rec.raw.items():
            if r.sig in ("WEAP", "ARMO", "MISC", "SLGM", "ALCH"):
                it = rec.item(k)
                if it and it["name"]:
                    self.items.append(it)
                    self.by_edid.setdefault(it["edid"], it)

    def ok(self, it) -> bool:
        """Unenchanted, of no never material, of no material off the scale's tiers (a vampire's or a creature's), and
        no creature's or quest's own piece."""
        e = (it["edid"] or "").lower()
        mats = {k for k in it["keywords"] if "Material" in k}
        return not it["ench"] and not (set(it["keywords"]) & self.never) and not any(w in e for w in self.words) \
            and mats <= self.scale_mats and not re.match(r"^(dlc\d)?cr[a-z]", e) \
            and "nonplayable" not in e and not e.startswith(("dun", "mq", "ms", "da", "tg", "db", "cw", "mg", "c0"))

    def by_keywords(self, *kws) -> dict | None:
        fit = [i for i in self.items if self.ok(i) and all(k in i["keywords"] for k in kws)]
        return min(fit, key=lambda i: (i["value"], i["key"])) if fit else None

    def edid(self, e: str) -> dict | None:
        return self.by_edid.get(e)

    def potion(self, effect: str, grade: int) -> dict | None:
        for g in range(grade, 0, -1):
            it = self.by_edid.get(f"{effect}{g:02d}")
            if it:
                return it
        return None


def road_km(w, pid: str) -> dict[str, float]:
    """Shortest road distance in km from the place to every place on the road graph."""
    node_place = {n.id: n.place_id for n in w.rows("road_node")}
    adj = defaultdict(list)
    for r in w.rows("road"):
        adj[r.from_node_id].append((r.to_node_id, r.length_m / 1000))
        adj[r.to_node_id].append((r.from_node_id, r.length_m / 1000))
    start = [n for n, p in node_place.items() if p == pid]
    dist = {n: 0.0 for n in start}
    q = [(0.0, n) for n in start]
    while q:
        d, n = heapq.heappop(q)
        if d > dist.get(n, 1e9):
            continue
        for m, l in adj[n]:
            if d + l < dist.get(m, 1e9):
                dist[m] = d + l
                heapq.heappush(q, (d + l, m))
    out: dict[str, float] = {}
    for n, d in dist.items():
        p = node_place.get(n)
        if p and d < out.get(p, 1e9):
            out[p] = d
    return out


def derive(p: Place) -> dict:
    sc = split.scale()
    w = db.open("newworld")
    pid = p.place_id
    tiers = {t["id"]: t for t in sc["tiers"]}
    rank = {t["id"]: t["rank"] for t in sc["tiers"]}
    tier_of = {t["rank"]: t["id"] for t in sc["tiers"]}
    pw = w.get("place_wealth", pid)
    place = w.get("place", pid)
    ceiling, open_tier = pw.ceiling_tier_id, pw.open_tier_id
    band = next((b for b in sc["place_wealth_bands"] if b["id"] == pw.place_wealth_band_id), None)
    wb = {b["id"]: b for b in sc["person_wealth_bands"]}
    persons = {r.id: r for r in w.rows("person", place_id=pid)}
    households = {h.id: h for h in w.rows("household", place_id=pid)}
    members = defaultdict(list)
    for r in persons.values():
        members[r.household_id].append(r)
    pick = Picker(p.rec, sc)
    cite_wealth = f"place_wealth:{pid}"

    # provenance: the nearest maker of each material keyword or item kind, on the roads
    km = road_km(w, pid)
    makers = defaultdict(set)
    for g in w.query("SELECT pg.place_id, gm.keyword FROM place_good pg JOIN good_material gm ON gm.good_id = pg.good_id "
                     "WHERE pg.relation = 'makes'"):
        makers[g["keyword"]].add(g["place_id"])
    gates = {r["place_id"] for r in w.query("SELECT g.place_id FROM place_give g JOIN place p ON p.id = g.place_id "
                                            "WHERE g.give_kind_id = 'boat-stop' AND p.siting IN ('coast', 'island')")}
    steps = sc["provenance"]["steps"]

    def provenance(it: dict, kind: str) -> tuple[dict, str]:
        keys = [k for k in it["keywords"] if "Material" in k] + [kind]
        if any(pid in makers[k] for k in keys):
            return steps[0], "made here"
        near = min([km.get(m, 1e9) for k in keys for m in makers[k]] + [km.get(g, 1e9) for g in gates] + [1e9])
        step = next(s for s in steps if s["max_km"] is None or near <= s["max_km"])
        src = "an import gate or maker" if near < 1e9 else "no maker or gate on the roads"
        return step, f"{step['label']} ({src}, {near:.0f} km by road)" if near < 1e9 else f"{step['label']} ({src})"

    def tier_cap(t: str) -> str:
        return t if rank[t] <= rank[ceiling] else ceiling

    def person_tier(band_id: str) -> str:
        top = wb[band_id]["top_tier"]
        return ceiling if top == "ceiling" else tier_cap(top)

    def gold_in(lo: int, hi: int, frac: float) -> int:
        return int(round(lo + (hi - lo) * max(0.0, min(1.0, frac))))

    out = {"place_id": pid, "about": f"Derived by `python -m tools.places stock derive {pid}`: a first draft for the "
                                     f"place-stock skill, not yet the source.",
           "facts": {"wealth": pw.place_wealth_band_id, "ceiling": ceiling, "open": open_tier,
                     "danger": place.danger_band_id, "why": pw.why},
           "goods": [], "containers": [], "loose": [], "possessions": [], "traders": [], "deliveries": [],
           "taken_out": [], "open": []}

    # containers: every significant one gets a row; its source contents are taken out
    rows = classify(p)
    conts = {}
    for r in rows:
        if r["holder"] == "container" and r["container_significant"]:
            conts.setdefault(r["ref"], r)
        if r.get("significant") and r.get("item"):
            out["taken_out"].append({"holder": r["holder"], "where": r.get("ref") or r.get("person"),
                                     "item": r["item"], "edid": r["edid"], "chance": r["chance"]})
    home_of = {h.home_space: h for h in households.values()}
    store_rank = ["safe", "strongbox", "chest", "wardrobe", "dresser", "end-table", "satchel", "cupboard"]
    store = {}          # each household's one store: its best-kept container
    for ref, r in sorted(conts.items()):
        hh = home_of.get(r["space"])
        k = store_rank.index(r["container_kind"]) if r["container_kind"] in store_rank else len(store_rank)
        if hh and r["container_kind"] != "corpse" and (hh.id not in store or k < store[hh.id][0]):
            store[hh.id] = (k, ref)
    for ref, r in sorted(conts.items()):
        kind, space = r["container_kind"], r["space"]
        hh = home_of.get(space)
        if hh and kind != "corpse" and store[hh.id][1] != ref:
            out["containers"].append({
                "ref": ref, "space": space, "kind": kind, "owner_household": hh.id, "security": "S1",
                "tier": "T1", "gold": 0, "items": [],
                "why": f"the household's other {kind}: its source's significant things are taken out and its store "
                       f"is {store[hh.id][1]}; set dressing stays", "cites": [cite_wealth]})
            continue
        if kind == "corpse":
            t = tiers[open_tier]["id"] if place.danger_band_id in ("D0", "D1") else tiers[ceiling]["below"]
            it = pick.by_keywords(tiers[t]["weapon"][0], "WeapTypeDagger")
            out["containers"].append({
                "ref": ref, "space": space, "kind": kind, "security": "S0", "effort": "E1", "tier": t,
                "gold": gold_in(*tiers[t]["gold"], 0.0),
                "items": [{"item": it["key"], "count": 1, "why": "the dead one's own knife"}] if it else [],
                "why": f"a body on the place's ground: nobody's, so free to take; the open tier {t} of a "
                       f"{place.danger_band_id} place, the least gold of that tier", "cites": [cite_wealth]})
            continue
        if hh:
            head = next((m for m in members[hh.id] if m.household_role_id == "head"), None) or \
                max(members[hh.id], key=lambda m: m.person_wealth_band_id)
            b = wb[head.person_wealth_band_id]
            t = person_tier(b["id"])
            frac = len(members[hh.id]) / 6
            gold = gold_in(*b["home"], frac)
            lock = None if b["rank"] <= 2 else ("Novice" if b["rank"] == 3 else tiers[t]["lock"])
            sec = {None: "S1", "Novice": "S2", "Apprentice": "S2", "Adept": "S3", "Expert": "S4", "Master": "S5"}[lock]
            items = []
            if b["rank"] >= 3 and tiers[t]["jewellery"]:
                j = pick.edid(tiers[t]["jewellery"][0])
                if j:
                    items.append({"item": j["key"], "count": 1, "why": f"{b['label'].lower()} savings in a ring"})
            if b["rank"] >= 4 and tiers[t]["gem"]:
                g = pick.edid(tiers[t]["gem"][0])
                if g:
                    items.append({"item": g["key"], "count": 1, "why": "a gem put by"})
            out["containers"].append({
                "ref": ref, "space": space, "kind": kind, "owner_household": hh.id, "lock": lock, "security": sec,
                "tier": t, "gold": gold, "items": items,
                "why": f"the household store of {head.name} ({b['id']} {b['label']}, head of {len(members[hh.id])}): "
                       f"gold {gold} of {b['home'][0]}-{b['home'][1]} by household size; best tier {t}; "
                       f"{'unlocked' if not lock else lock} ({b['home_store']})",
                "cites": [cite_wealth, f"person:{head.id}"]})
        else:
            t = open_tier
            out["containers"].append({
                "ref": ref, "space": space, "kind": kind, "owner_faction": f"{pid}.town", "security": "S1",
                "tier": t, "gold": gold_in(*tiers[t]["gold"], 0.0), "items": [],
                "why": f"a {kind} in a shared space of {place.name}: the town's, ordinary ({t}), the least gold",
                "cites": [cite_wealth]})

    # possessions: by role and wealth band, the tier the band reaches in this place; a guard's gear is the issue
    issue = split.guard_issue(place.culture_id, ceiling, p.plugins() or split.source_plugins(pid), sc)
    issue_plain = next(o for o in sc["owner"] if o["id"] == "faction")["issue_tier"]
    for r in sorted(persons.values(), key=lambda x: x.id):
        b = wb[r.person_wealth_band_id]
        guard = r.person_role_id == "guard"
        t = person_tier(b["id"]) if not guard else tier_cap(tier_of[max(1, min(b["rank"], 3))])
        items = []
        wt = ROLE_WEAPON.get(r.person_role_id, "WeapTypeDagger")
        tw = t if wt != "WeapTypeDagger" else "T1"
        if guard:  # the guard's issue (scale `guard_issue`): the weapon of its set, else the plain issue's sword
            tw = issue_plain
        weap = None if guard and issue["set"] and issue["set"].get("weapon") else \
            next((pick.by_keywords(m, wt) for m in tiers[tw]["weapon"] if pick.by_keywords(m, wt)), None)
        if guard and issue["set"] and issue["set"].get("weapon"):
            items.append({"item": issue["set"]["weapon"], "count": 1, "worn": True,
                          "why": f"the levy's issue: the weapon of {issue['why']}"})
        if weap:
            step, prov = provenance(weap, "weapon")
            items.append({"item": weap["key"], "count": 1, "worn": True,
                          "why": f"{r.trade}: a {wt[8:].lower()} of {tw} ({prov})"})
        if guard and issue["set"]:
            for k in issue["set"]["items"]:
                items.append({"item": k, "count": 1, "worn": True,
                              "why": f"the levy's issue: {place.name}'s guards wear {issue['why']}"})
        elif guard:
            ti = issue_plain
            mats = [m for m in tiers[ti]["armour"] if pick.by_keywords(m, "ArmorLight", "ArmorCuirass")] or tiers[ti]["armour"]
            for slot in ARMOUR_SLOTS:
                a = next((pick.by_keywords(m, slot) for m in mats if pick.by_keywords(m, slot)), None)
                if a:
                    step, prov = provenance(a, "armour")
                    items.append({"item": a["key"], "count": 1, "worn": True,
                                  "why": f"the levy's {slot[5:].lower()} at {ti}, light for the marsh ({prov})"})
        if guard:
            items.append({"item": issue["torch"], "count": 1, "worn": False,
                          "why": "the levy's torch: " + sc["guard_issue"]["torch_why"]})
        if b["rank"] >= 3 and tiers[t]["jewellery"]:
            j = pick.edid(tiers[min(t, "T2", key=rank.get)]["jewellery"][0]) if b["rank"] == 3 else \
                pick.edid(tiers[t]["jewellery"][-1 if b["rank"] == 5 else 0])
            if j:
                items.append({"item": j["key"], "count": 1, "worn": True, "why": f"{b['label'].lower()}: worn jewellery"})
        frac = (len(r.trade) % 7) / 6           # a fact of the person, not a die: the length of their trade's words
        gold = gold_in(*b["carried"], frac)
        gk = sc["split"]["gold"][0]
        if gold:
            items.append({"item": gk, "count": gold, "worn": False,
                          "why": f"carried gold, {b['carried'][0]}-{b['carried'][1]} for {b['id']} {b['label']}"})
        out["possessions"].append({"person": r.id, "items": items,
                                   "why": f"{r.name}: {r.person_role_id}, {r.trade}, {b['id']}; best tier {t}"})

    # traders: gold and a fixed list from T1 to the place's best
    folk = {x["id"]: x for x in p.people}
    for g in w.rows("place_give", place_id=pid):
        if not g.give_kind_id.startswith("trader-"):
            continue
        who = next((x for x in folk.values() if any(s.get("seq") == g.seq for s in x.get("services") or [])), None)
        if who is None:
            out["open"].append(f"give {g.seq} {g.give_kind_id}: no person gives it")
            continue
        gold = int(sc["traders"]["gold"].get(g.give_kind_id, 500) * (band["trader_gold_mult"] if band else 1))
        items, budget = [], sc["traders"]["list_value"].get(pw.place_wealth_band_id or "P1", 400)
        spec = TRADER_LISTS.get(g.give_kind_id)
        if spec is None:
            out["open"].append(f"give {g.seq} {g.give_kind_id} ({g.detail}): its list is written by hand (the derive "
                               f"cannot tell a spell's school or a dish from the records it reads)")
        for rk in range(1, rank[ceiling] + 1):
            t = tier_of[rk]
            n = rank[ceiling] - rk + 1
            for kind, types in spec or []:
                if kind in ("weapon", "armour"):
                    for typ in types:
                        it = next((pick.by_keywords(m, typ) for m in tiers[t][kind] if pick.by_keywords(m, typ)), None)
                        if it:
                            step, prov = provenance(it, kind)
                            cnt = max(1, int(n * step["count"]))
                            if it["value"] * cnt * step["cost"] > budget:
                                continue
                            budget -= it["value"] * cnt * step["cost"]
                            items.append({"item": it["key"], "count": cnt, "why": f"{t} {typ[8 if kind == 'weapon' else 5:].lower()} ({prov})"})
                elif kind == "soul-gem":
                    it = pick.edid(tiers[t]["soul_gem"])
                    if it and it["value"] * n <= budget:
                        budget -= it["value"] * n
                        items.append({"item": it["key"], "count": n, "why": f"{t} soul gem"})
                elif kind == "potion":
                    for eff in types:
                        it = pick.potion(eff, tiers[t]["potion_grade"])
                        if it and it["value"] * n <= budget:
                            budget -= it["value"] * n
                            items.append({"item": it["key"], "count": n, "why": f"{t} {eff} (grade {tiers[t]['potion_grade']})"})
        out["traders"].append({"person": who["id"], "give_seq": g.seq, "gold": gold, "items": items,
                               "why": f"{g.detail}: vanilla's {g.give_kind_id} gold times {pw.place_wealth_band_id}'s "
                                      f"{band['trader_gold_mult'] if band else 1}; tiers T1 to {ceiling}, fewer of each "
                                      f"tier upward, within a list value of {sc['traders']['list_value'].get(pw.place_wealth_band_id or 'P1')}",
                               "cites": [cite_wealth, f"place_give:{pid}/{g.seq}"]})

    # promises stocking owns: loot gives with no container in the place files are open
    for d in w.query("SELECT g.seq, g.give_kind_id, g.detail FROM give_delivery d JOIN place_give g ON "
                     "g.place_id = d.place_id AND g.seq = d.give_seq WHERE d.place_id = ? AND d.status = 'open'", pid):
        out["open"].append(f"give {d['seq']} {d['give_kind_id']} ({d['detail']}): nothing in the place files can "
                           f"deliver it; the place needs the spot built (place-build) or the record edited with the reason")
    return out


HOLDERS = {"containers": ("space", "ref"), "loose": ("id",), "possessions": ("person",), "traders": ("person",),
           "deliveries": ("give_seq",), "goods": ("good", "relation")}


def _owner_words(x) -> bool:
    """True when a row holds the owner's own words (a reason or note at the owner's statement tier)."""
    from tools.places.edits import OWNER_TIER
    if isinstance(x, dict):
        return x.get("why_tier") == OWNER_TIER or x.get("tier") == OWNER_TIER or any(_owner_words(v) for v in x.values())
    return isinstance(x, list) and any(_owner_words(v) for v in x)


def keep_owner_rows(doc: dict, source: dict | None) -> dict:
    """An agent's derive never overwrites the owner's words: every row of the stock source that holds a reason or note
    at the owner's tier stands in the derived draft as the source has it, and where the derive would say otherwise
    the difference is reported in `owner_kept` ({list, key, derived}: what the derive would have written)."""
    doc.setdefault("owner_kept", [])
    for table, keys in HOLDERS.items():
        mine = {tuple(r.get(k) for k in keys): r for r in (source or {}).get(table, []) if _owner_words(r)}
        if not mine:
            continue
        rows = doc.setdefault(table, [])
        for i, r in enumerate(rows):
            k = tuple(r.get(x) for x in keys)
            if k in mine:
                if r != mine[k]:
                    doc["owner_kept"].append({"list": table, "key": list(k), "derived": r})
                rows[i] = mine.pop(k)
        for k, r in mine.items():   # an owner's row the derive does not make at all
            rows.append(r)
            doc["owner_kept"].append({"list": table, "key": list(k), "derived": None})
    return doc


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="stock derive")
    ap.add_argument("place")
    ap.add_argument("--out", help="the places output folder holding bundles/ (default out/places)")
    ap.add_argument("--to", help="where to write the derived stock (default out/places/stock/<place>.derived.json)")
    a = ap.parse_args(argv)
    p = Place.load(a.place, Path(a.out) if a.out else None)
    doc = derive(p)
    from tools.places.stock.plan import stock_source
    src = stock_source(a.place)
    keep_owner_rows(doc, json.loads(src.read_text(encoding="utf-8")) if src.exists() else None)
    to = Path(a.to) if a.to else p.out / "stock" / f"{a.place}.derived.json"
    to.parent.mkdir(parents=True, exist_ok=True)
    to.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    n = {k: len(doc[k]) for k in ("containers", "possessions", "traders", "taken_out", "open")}
    print(f"wrote {to}: {n}")
    for o in doc["open"]:
        print("  open:", o)
    for o in doc["owner_kept"]:
        print(f"  the owner's row kept: {o['list']} {'/'.join(map(str, o['key']))}"
              + (" (the derive would write it otherwise)" if o["derived"] else " (the derive makes no such row)"))
    return 0
