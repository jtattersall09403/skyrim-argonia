"""People, economy and stock into the new world's database (docs/design/place-studio.md, "Stock").

Sources (all committed, the single truth for these world facts):
- `newworld/sources/stock/scale.json`: the scale (tiers, materials, locks, security, effort, kinds, the split);
- `newworld/sources/stock/place_wealth.json`: every place's wealth (tools/newworld/wealth.py);
- `newworld/sources/stock/materials.json`: Black Marsh's materials, who makes them and where they may be held;
- `newworld/sources/stock/item_material.json`: each item of gear's material and each ware's good (authored);
- `newworld/sources/stock/items.json`: the item catalogue (generated: `items`), `power.json` (generated: `power`),
  `goods.json`, `unique.json`;
- `newworld/sources/people/lookups.json` and `people/<place_id>.json`: households, people, their notes and ties;
- `newworld/sources/stock/places/<place_id>.json`: a place's goods, containers, loose things, possessions, traders
  and the deliveries stocking owns.
Placement stays in the place files (`newworld/places/<place_id>/`): people.jsonl's beds, routines and services and
place.json's stations are read here only to tie each promise (place_give) to what delivers it (give_delivery).

    python3 -m tools.newworld.stockdb load         # rewrite these tables alone (build_db does it with the rest)
    python3 -m tools.newworld.stockdb items        # regenerate items.json for every item the sources name
    python3 -m tools.newworld.stockdb power        # measure Skyrim's base gear per tier into power.json (before items)
    python3 -m tools.newworld.stockdb promises <place_id>   # each promise and what delivers it
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from tools.argonia_world import db
from tools.newworld import frame as f
from tools.newworld import wealth

SRC = f.ROOT / "sources"
STOCK = SRC / "stock"
PEOPLE = SRC / "people"
PLACES = f.ROOT / "places"
REPO = f.ROOT.parent

TABLES = ("lock_level", "stock_tier", "place_wealth_band", "person_wealth_band", "place_wealth", "material",
          "material_keyword", "material_maker", "material_reach", "tier_material", "never_material",
          "security_level", "effort_level", "container_kind", "item_kind", "item", "tier_item", "item_material",
          "good", "good_material", "good_kind", "item_good", "place_good", "region_profile", "region_people",
          "region_culture", "region_material", "region_good", "trade_kit", "trade_kit_item", "trade_kit_never",
          "recipe", "recipe_ingredient", "race", "person_role", "household_role", "relation_kind",
          "household", "person", "person_note", "person_note_source", "person_relation", "person_faction",
          "stock_container", "stock_container_item", "stock_container_key", "stock_loose", "person_item", "trader", "trader_item",
          "stock_container_source", "trader_source", "unique_item", "give_delivery")
ITEM_KINDS = {  # id: (always significant, about)
    "gold": (True, "Coin."), "weapon": (True, "A weapon."), "armour": (True, "Armour or a shield."),
    "jewellery": (True, "A ring, necklace or circlet."), "gem": (True, "A gem."), "soul-gem": (True, "A soul gem."),
    "potion": (True, "A potion."), "poison": (True, "A poison."), "scroll": (True, "A scroll."),
    "key": (True, "A key."), "ammunition": (True, "Arrows or bolts."), "spell-tome": (True, "A book that teaches a spell."),
    "skill-book": (True, "A book that raises a skill."), "clothing": (False, "Clothes; significant when worth 50 or more."),
    "book": (False, "A book; significant when worth 50 or more."), "food": (False, "Food and drink."),
    "ingredient": (False, "An alchemy ingredient; significant when worth 50 or more."),
    "ingot-or-ore": (False, "Ore or an ingot."), "hide": (False, "A hide or pelt."), "animal-part": (False, "An animal part."),
    "tool": (False, "A tool."), "clutter": (False, "Clutter: crockery, candlesticks, odds and ends."),
    "light": (False, "A carried light.")}
GIVE_STATION = {"shrine-blessing": "shrine"}     # a give delivered by a station of another name
STATION_GIVES = {"alchemy-lab", "anvil", "arcane-enchanter", "armour-workbench", "cooking-pot", "forge", "grindstone",
                 "smelter", "tanning-rack", "oven", "staff-enchanter", "shrine-blessing"}


def _json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def form_key(key: str) -> str:
    plugin, hexid = key.rsplit(":", 1)
    return f"{hexid}:{plugin}"


def _source(w, cite: str) -> str:
    """The source row a cite names: a repo path (a dossier) or a row of this database (reasoning)."""
    sid = "cite-" + re.sub(r"[^a-z0-9]+", "-", cite.lower()).strip("-")[:74]
    if w.get("source", sid) is None:
        kind = "reasoning" if re.match(r"^(place_note|place_give|culture|region|place):", cite) else "dossier"
        w.insert("source", id=sid, kind=kind, title=cite, locator=cite, url=None)
    return sid


def load(w) -> None:
    sc = _json(STOCK / "scale.json")
    w.insert_many("lock_level", [{"id": k, "level": v} for k, v in sc["lock_level"].items()])
    wealth.load(w)
    md = _json(STOCK / "materials.json")
    for m in md["materials"]:
        w.insert("material", id=m["id"], label=m["label"], group=m["group"], band=m["band"], lore=m["lore"],
                 statement_tier_id=m["tier"], power_weapon=m["power"]["weapon"], power_armour=m["power"]["armour"])
        w.insert_many("material_keyword", [{"keyword": k, "material_id": m["id"]} for k in m["keywords"]])
        w.insert_many("material_maker", [{"material_id": m["id"], **x} for x in m["makers"]])
        w.insert_many("material_reach", [{"material_id": m["id"], "seq": i, **x} for i, x in enumerate(m["reach"])])
    from tools.places.stock import split as _split    # the ladder, derived from each material's tier and the filed gear
    for (tier, slot), mats in sorted(_split.ladder().items()):
        w.insert_many("tier_material", [{"stock_tier_id": tier, "slot": slot, "material_id": k, "ord": i}
                                        for i, k in enumerate(mats)])
    w.insert_many("never_material", [{"material_id": k, "why": md["never"]["why"]} for k in md["never"]["materials"]])
    w.insert_many("security_level", [{"id": s["id"], "rank": i, "label": s["label"], "means": s["means"]}
                                     for i, s in enumerate(sc["security"])])
    w.insert_many("effort_level", [{"id": e["id"], "rank": i, "means": e["means"], "tier": e["tier"]}
                                   for i, e in enumerate(sc["effort"])])
    always = set(sc["split"]["always_significant_containers"])
    w.insert_many("container_kind", [{"id": k, "always_significant": k in always, "words": " | ".join(ws)}
                                     for k, ws in sc["split"]["container_kinds"]] +
                  [{"id": "other", "always_significant": False, "words": "(none of the above)"}])
    w.insert_many("item_kind", [{"id": k, "always_significant": a, "about": t} for k, (a, t) in ITEM_KINDS.items()])
    items = _json(STOCK / "items.json")["items"] if (STOCK / "items.json").exists() else []
    w.insert_many("item", items)
    by_edid = {i["edid"]: i["id"] for i in items if i.get("edid")}
    for t in sc["tiers"]:
        for use, names in (("soul-gem", [t["soul_gem"]]), ("gem", t["gem"]), ("jewellery", t["jewellery"])):
            for n in names:
                if n in by_edid:
                    w.insert("tier_item", stock_tier_id=t["id"], item_id=by_edid[n], use=use)

    goods = _json(STOCK / "goods.json")["goods"]
    w.insert_many("good", [{k: g[k] for k in ("id", "name", "kind", "about")} for g in goods])
    w.insert_many("good_material", [{"good_id": g["id"], "material_id": m} for g in goods for m in g["materials"]])
    w.insert_many("good_kind", [{"good_id": g["id"], "item_kind_id": k} for g in goods for k in g["item_kinds"]])
    im = _json(STOCK / "item_material.json")
    w.insert_many("item_material", [{"item_id": r["item"], "material_id": r["material"],
                                     "stock_tier_id": r.get("tier"), "why": r["why"]} for r in im["gear"]])
    w.insert_many("item_good", [{"item_id": r["item"], "good_id": r["good"], "harvestable": r.get("harvestable"),
                                 "why": r["why"]} for r in im["wares"]])
    _regions_and_kits(w)
    if (STOCK / "recipes.json").exists():
        for r in _json(STOCK / "recipes.json")["recipes"]:
            w.insert("recipe", item_id=r["item"], kind=r["kind"], station=r["station"], perk=" ".join(r["perk"]) or None,
                     source=r["source"], why=r["why"])
            w.insert_many("recipe_ingredient", [{"item_id": r["item"], "kind": r["kind"], "seq": i, "ingredient": k,
                                                 "count": n} for i, (k, n) in enumerate(r["ingredients"])])

    lk = _json(PEOPLE / "lookups.json")
    for t in ("race", "person_role", "household_role", "relation_kind"):
        w.insert_many(t, lk[t])
    for p in sorted(PEOPLE.glob("*.json")):
        if p.name == "lookups.json":
            continue
        doc = _json(p)
        for h in doc["households"]:
            w.insert("household", id=h["id"], place_id=doc["place_id"], home_space=h["home_space"], name=h.get("name"))
        for r in doc["people"]:
            hh = r.get("household") or {}
            w.insert("person", id=r["id"], name=r["name"], sex=r["sex"], race_id=r["race"],
                     culture_id=r.get("culture_id"), place_id=doc["place_id"], household_id=hh.get("id"),
                     household_role_id=hh.get("role"), person_role_id=r["role"], trade=r["trade"],
                     person_wealth_band_id=r["wealth"], level=r.get("level"), status=r.get("status", "alive"),
                     statement_tier_id=r.get("tier", "AGENT_INVENTED"))
            for n in r.get("notes", []):
                w.insert("person_note", person_id=r["id"], aspect_id=n["aspect"], text=n["text"],
                         statement_tier_id=n.get("tier", "AGENT_INVENTED"))
                for c in dict.fromkeys(n.get("cites", [])):
                    w.insert("person_note_source", person_id=r["id"], aspect_id=n["aspect"], source_id=_source(w, c),
                             locator=None)
        for r in doc["people"]:
            for rel in r.get("relations", []):
                w.insert("person_relation", person_id=r["id"], other_id=rel["to"], relation_kind_id=rel["kind"])
            for fa in r.get("factions", []):
                w.insert("person_faction", person_id=r["id"], faction=fa["faction"], rank=fa["rank"])

    for p in sorted((STOCK / "places").glob("*.json")):
        _load_place_stock(w, _json(p))
    for u in _json(STOCK / "unique.json")["items"]:
        w.insert("unique_item", **{k: u[k] for k in ("id", "item_id", "place_id", "held_by", "story", "why")})
    for pid in sorted({r[0] for r in w.query("SELECT DISTINCT place_id FROM place_give")}):
        _deliveries(w, pid)


def _regions_and_kits(w) -> None:
    """regions.json (each region's profile, peoples, materials and goods; region_culture counted from the places)
    and kits.json (the trade kits and the household overlays)."""
    rd = _json(STOCK / "regions.json")["regions"]
    for rid, r in sorted(rd.items()):
        w.insert("region_profile", region_id=rid, signature=r["signature"], missing=r["missing"])
        w.insert_many("region_people", [{"region_id": rid, **p} for p in r["peoples"]])
        w.insert_many("region_material", [{"region_id": rid, "material_id": m["material"], "band": m["band"],
                                           "why": m["why"]} for m in r["materials"]])
        w.insert_many("region_good", [{"region_id": rid, "good_id": g["good"], "why": g["why"]} for g in r["goods"]])
    counts: dict[tuple[str, str], int] = {}
    for p in w.rows("place"):
        if getattr(p, "culture_id", None):
            counts[(p.region_id, p.culture_id)] = counts.get((p.region_id, p.culture_id), 0) + 1
    w.insert_many("region_culture", [{"region_id": r, "culture_id": c, "places": n} for (r, c), n in sorted(counts.items())])
    kd = _json(STOCK / "kits.json")
    for i, k in enumerate(kd["kits"] + kd["overlays"]):
        w.insert("trade_kit", id=k["id"], label=k["label"], ord=i, match=k.get("match"),
                 roles=" ".join(k.get("roles", [])) or None, races=" ".join(k.get("races", [])) or None)
        seq = 0
        for use in ("carry", "wear", "home"):
            for x in k.get(use, []):
                w.insert("trade_kit_item", kit_id=k["id"], seq=seq, use=use, slot=x.get("slot"), typ=x.get("typ"),
                         materials=" ".join(x.get("materials", [])) or None, good_id=x.get("good"), why=x["why"])
                seq += 1
        for g in k.get("food", []):
            w.insert("trade_kit_item", kit_id=k["id"], seq=seq, use="food", slot=None, typ=None, materials=None,
                     good_id=g, why="food in the house")
            seq += 1
        for j, n in enumerate(k.get("never", [])):
            w.insert("trade_kit_never", kit_id=k["id"], seq=j, slot=n.get("slot"), types=" ".join(n.get("types", [])) or None,
                     materials=" ".join(n.get("materials", [])) or None, groups=" ".join(n.get("groups", [])) or None,
                     bands=" ".join(n.get("bands", [])) or None, why=n["why"])


def _load_place_stock(w, doc: dict) -> None:
    pid = doc["place_id"]
    for g in doc.get("goods", []):
        w.insert("place_good", place_id=pid, good_id=g["good"], relation=g["relation"], why=g["why"],
                 statement_tier_id=g.get("tier", "EXTRAPOLATED"))
    for c in doc.get("containers", []):
        w.insert("stock_container", place_id=pid, ref_id=c["ref"], space_id=c["space"],
                 container_kind_id=c["kind"], owner_person_id=c.get("owner_person"),
                 owner_household_id=c.get("owner_household"), owner_faction=c.get("owner_faction"),
                 lock_level_id=c.get("lock"), security_level_id=c["security"], effort_level_id=c.get("effort"),
                 stock_tier_id=c["tier"], gold=c.get("gold", 0), why=c["why"])
        for it in c.get("items", []):
            w.insert("stock_container_item", place_id=pid, space_id=c["space"], ref_id=c["ref"], item_id=it["item"], count=it["count"],
                     why=it["why"])
        if k := c.get("key"):
            pos = k.get("pos") or [None, None, None]
            w.insert("stock_container_key", place_id=pid, container_space_id=c["space"], ref_id=c["ref"], name=k["name"],
                     holder_person_id=k.get("person"), holder_ref_id=k.get("in"),
                     space_id=None if k.get("person") else k.get("space", c["space"]),
                     x=pos[0], y=pos[1], z=pos[2], why=k["why"])
        for cite in dict.fromkeys(c.get("cites", [])):
            w.insert("stock_container_source", place_id=pid, space_id=c["space"], ref_id=c["ref"], source_id=_source(w, cite), locator=None)
    for lo in doc.get("loose", []):
        pos = lo.get("pos") or [None, None, None]
        w.insert("stock_loose", place_id=pid, id=lo["id"], space_id=lo["space"], on_ref_id=lo.get("on"),
                 x=pos[0], y=pos[1], z=pos[2], item_id=lo["item"], count=lo["count"],
                 owner_person_id=lo.get("owner_person"), owner_faction=lo.get("owner_faction"),
                 effort_level_id=lo.get("effort"), why=lo["why"])
    for po in doc.get("possessions", []):
        for it in po["items"]:
            w.insert("person_item", person_id=po["person"], item_id=it["item"], count=it["count"],
                     worn=bool(it.get("worn")), why=it["why"])
    for t in doc.get("traders", []):
        w.insert("trader", person_id=t["person"], gold=t["gold"], why=t["why"])
        for it in t.get("items", []):
            w.insert("trader_item", person_id=t["person"], item_id=it["item"], count=it["count"], why=it["why"])
        for cite in dict.fromkeys(t.get("cites", [])):
            w.insert("trader_source", person_id=t["person"], source_id=_source(w, cite), locator=None)


def _deliveries(w, pid: str) -> None:
    """Each promise of the place and what delivers it: the stock source's own rows first (loot, record edits), then
    the place files' people (services) and stations; anything else is open."""
    gives = w.rows("place_give", place_id=pid)
    stock = STOCK / "places" / f"{pid}.json"
    own = {}
    if stock.exists():
        for d in _json(stock).get("deliveries", []):
            own.setdefault(d["give_seq"], []).append(d)
    folk = []
    pf = PLACES / pid / "people.jsonl"
    if pf.exists():
        folk = [json.loads(ln) for ln in pf.read_text(encoding="utf-8").splitlines() if ln.strip()]
    persons = {r.id for r in w.rows("person", place_id=pid)}
    stations = {}
    pj = PLACES / pid / "place.json"
    if pj.exists():
        stations = (_json(pj).get("stations") or {}).get("found") or {}
    for g in gives:
        rows = []
        for d in own.get(g.seq, []):
            rows.append({"by": d["by"], "person_id": d.get("person"), "ref_id": d.get("ref"), "status": d["status"],
                         "why": d["why"]})
        if not rows:
            for p in folk:
                if any(s.get("seq") == g.seq for s in p.get("services") or []) and p["id"] in persons:
                    rows.append({"by": "person", "person_id": p["id"], "ref_id": None, "status": "delivered",
                                 "why": f"{w.get('person', p['id']).name} ({p.get('role')}) gives it (people.jsonl services)"})
        if not rows and g.give_kind_id in STATION_GIVES:
            for ref in stations.get(GIVE_STATION.get(g.give_kind_id, g.give_kind_id), [])[:1]:
                rows.append({"by": "ref", "person_id": None, "ref_id": ref, "status": "delivered",
                             "why": f"the place's {GIVE_STATION.get(g.give_kind_id, g.give_kind_id)} (place.json stations)"})
        if not rows:
            rows.append({"by": "record", "person_id": None, "ref_id": None, "status": "open",
                         "why": f"nothing delivers it yet ({g.give_kind_id}: {g.detail})"})
        for i, r in enumerate(rows):
            w.insert("give_delivery", place_id=pid, give_seq=g.seq, seq=i, **r)


def clear(w) -> None:
    w._begin()
    for t in reversed(TABLES):
        w.con.execute(f'DELETE FROM "{t}"')
        w.dirty.add(t)
    w.con.execute("DELETE FROM source WHERE id LIKE 'cite-%'")
    w.dirty.add("source")


def reload() -> db.World:
    """Rewrite these tables alone, from their sources, without a whole build_db (which needs the map extraction)."""
    w = db.open(f.ROOT, cache=False)
    key = _json(SRC / "key.json")
    for a in key["note_aspect"]:
        if w.get("note_aspect", a["id"]) is None:
            w.insert("note_aspect", **a)
    clear(w)
    load(w)
    w.save()
    return w


def items() -> int:
    """items.json: every item the sources name (the scale's lists by editor id, the stock and ledger rows by key),
    read from the plugins with their kind, value, material, tier and the split's verdict."""
    from tools.places.stock import split
    from tools.places.stock.records import Records
    sc = _json(STOCK / "scale.json")
    keys: set[str] = set()
    for p in (STOCK / "places").glob("*.json"):
        doc = _json(p)
        for c in doc.get("containers", []):
            keys |= {i["item"] for i in c.get("items", [])}
        keys |= {lo["item"] for lo in doc.get("loose", [])}
        for h in doc.get("possessions", []) + doc.get("traders", []):
            keys |= {i["item"] for i in h.get("items", [])}
    keys |= {u["item_id"] for u in _json(STOCK / "unique.json")["items"]}
    im = _json(STOCK / "item_material.json")
    keys |= {r["item"] for r in im["gear"] + im["wares"]}
    order = ["Skyrim.esm", "Update.esm", "Dawnguard.esm", "HearthFires.esm", "Dragonborn.esm",
             "Black Marsh.esm", "Black Marsh North.esp"]
    # and every other plugin a source names an item of (a person built on King of the Murkmire's villagers carries its gear)
    order += sorted({k.rsplit(":", 1)[0] for k in keys if ":" in k} - set(order))
    rec = Records.load(order)
    edids = {t["soul_gem"] for t in sc["tiers"]} | {n for t in sc["tiers"] for n in t["gem"] + t["jewellery"]}
    keys |= {k for k, r in rec.raw.items() if r.edid in edids and r.sig in ("MISC", "ARMO", "SLGM")}
    out = []
    for k in sorted(keys):
        it = rec.item(k)
        if it is None:
            print(f"items: {k} is not an item record in the load order", file=sys.stderr)
            continue
        kind, sig, _ = split.item_class(it, sc["split"])
        mat = next((m for m in it["keywords"] if "Material" in m), None)
        tier = split.item_tier(it, sc)[0]
        lad = split.ladder_override(it, sc)    # a ladder item as the world build writes it: its tier's Skyrim stats
        out.append({"id": k, "form_key": form_key(k), "plugin": k.rsplit(":", 1)[0], "edid": it["edid"], "name": None,
                    "record": it["sig"], "item_kind_id": kind if kind in ITEM_KINDS else "clutter",
                    "value": lad["value"] if lad else it["value"], "material": mat, "material_id": split.material_of(it)[0],
                    "power_kind": split.power_kind(it),
                    "power": lad["power"] if lad else (split.power_of(it) if split.power_kind(it) else None),
                    "stock_tier_id": tier, "enchanted": bool(it["ench"]),
                    "significant": sig, "never": split.never_reason(it, sc) is not None})
    (STOCK / "items.json").write_text(json.dumps(
        {"about": "Generated by `python3 -m tools.newworld.stockdb items` from the plugins: every item a stock source, "
                  "the ledger or the scale names (ids and measured numbers only; names come from the game). Do not edit.",
         "items": out}, indent=1) + "\n", encoding="utf-8")
    print(f"items.json: {len(out)} items")
    return 0


def power() -> int:
    """power.json: each base of scale.json `power` measured from the plugins, and each tier's ceiling per kind (the
    strongest base at that tier or below; a tier with no base lies midway between its neighbours)."""
    from tools.places.stock.records import Records
    sc = _json(STOCK / "scale.json")
    rec = Records.load(["Skyrim.esm", "Update.esm", "Dawnguard.esm", "HearthFires.esm", "Dragonborn.esm"])
    by_edid = {r.edid: k for k, r in rec.raw.items() if r.sig in ("WEAP", "ARMO") and r.edid}
    tiers = [t["id"] for t in sc["tiers"]]
    kinds, missing = {}, []
    for kind, per in sc["power"]["bases"].items():
        bases = {}
        for t in tiers:
            got = {}
            for e in per.get(t, []):
                it = rec.item(by_edid[e]) if e in by_edid else None
                if it is None:
                    missing.append(e)
                    continue
                got[e] = float(it.get("damage") if it["sig"] == "WEAP" else it.get("rating") or 0)
            bases[t] = got
        top, ceil = 0.0, {}
        for t in tiers:
            if bases[t]:
                top = max([top] + list(bases[t].values()))
                ceil[t] = top
        known = [t for t in tiers if t in ceil]
        for i, t in enumerate(tiers):        # a tier with no base: midway between its neighbours
            if t not in ceil:
                lo = max((ceil[k] for k in known if tiers.index(k) < i), default=None)
                hi = min((ceil[k] for k in known if tiers.index(k) > i), default=None)
                if lo is not None and hi is not None:
                    ceil[t] = float(int((lo + hi) / 2))
        stats = {}
        for t, e in (sc["power"].get("stat_bases", {}).get(kind) or {}).items():
            it = rec.item(by_edid[e]) if e in by_edid else None
            if it is None:
                missing.append(str(e))
                continue
            stats[t] = {"edid": e, "power": float(it.get("damage") if it["sig"] == "WEAP" else it.get("rating") or 0),
                        "weight": it["weight"], "value": it["value"]}
        kinds[kind] = {"ceiling": {t: ceil[t] for t in tiers if t in ceil}, "bases": bases, "stats": stats}
    (STOCK / "power.json").write_text(json.dumps(
        {"about": "Generated by `python3 -m tools.newworld.stockdb power` from scale.json `power` and the plugins: Skyrim's "
                  "own base gear per kind and tier, and each tier's ceiling (the strongest base at that tier or below; a "
                  "tier with no base midway between its neighbours). split.item_tier reads it. Do not edit.",
         "kinds": kinds}, indent=1) + "\n", encoding="utf-8")
    print(f"power.json: {len(kinds)} kinds" + (f"; missing bases: {', '.join(missing)}" if missing else ""))
    return 1 if missing else 0


LADDER_DOC = REPO / "docs" / "design" / "items.md"
LADDER_MARK = ("<!-- ladder:start (generated by `python3 -m tools.newworld.stockdb ladder`; do not edit) -->",
               "<!-- ladder:end -->")


def ladder_table() -> str:
    """The ladder as a table, one line per material at its tier: how many filed items of each slot, the Skyrim base
    whose stats they take, and the items written at another tier with their reason."""
    from tools.places.stock import split
    mats = split.materials()["materials"]
    items = {i["id"]: i for i in _json(STOCK / "items.json")["items"]}
    gear = split.item_materials()["gear"]
    stats = split.power_table()
    rows = []
    for mid, m in mats.items():
        t = m.get("ladder_tier")
        mine = [items[k] for k, r in gear.items() if r["material"] == mid and k in items and not r.get("tier")]
        if not t or not mine and m["band"] in ("never", "unique"):
            continue
        n = {s: sum(split.slot_of(i) == s for i in mine) for s in ("weapon", "heavy", "light", "shield")}
        base = (stats.get("sword") or {}).get("stats", {}).get(t, {}).get("edid", "")
        rows.append((t, m["label"], n, base, m["band"]))
    out = ["| Tier | Material | Weapons | Heavy | Light | Shields | Band | Takes the stats of (a sword, e.g.) |",
           "|---|---|---|---|---|---|---|---|"]
    for t, label, n, base, band in sorted(rows, key=lambda r: (r[0], r[1])):
        out.append(f"| {t} | {label} | {n['weapon'] or ''} | {n['heavy'] or ''} | {n['light'] or ''} | {n['shield'] or ''} | {band} | {base} |")
    exc = [(r["tier"], k, r["why"].split("; tier ")[-1].split(": ", 1)[-1]) for k, r in gear.items() if r.get("tier")]
    if exc:
        out += ["", "Written at another tier than their material's, each with its reason:", ""]
        out += [f"- {t}: {items.get(k, {}).get('edid') or k}: {why}" for t, k, why in sorted(exc)]
    return "\n".join(out)


def ladder() -> int:
    """Write the ladder table into docs/design/items.md between its markers."""
    s = LADDER_DOC.read_text(encoding="utf-8")
    a, b = s.index(LADDER_MARK[0]), s.index(LADDER_MARK[1])
    LADDER_DOC.write_text(s[:a] + LADDER_MARK[0] + "\n" + ladder_table() + "\n" + s[b:], encoding="utf-8")
    print(f"{LADDER_DOC.relative_to(REPO)}: the ladder table written")
    return 0


def promises(pid: str) -> int:
    w = db.open(f.ROOT)
    open_ = 0
    for r in w.query("SELECT g.seq, g.give_kind_id, g.detail, d.by, d.person_id, d.ref_id, d.status, d.why "
                     "FROM place_give g LEFT JOIN give_delivery d ON d.place_id=g.place_id AND d.give_seq=g.seq "
                     "WHERE g.place_id=? ORDER BY g.seq, d.seq", pid):
        open_ += r["status"] != "delivered" and r["status"] != "dropped"
        print(f"{r['seq']:>3} {r['give_kind_id']:<18} {r['status'] or 'none':<9} {r['by'] or '':<7} "
              f"{r['person_id'] or r['ref_id'] or ''}  {r['why'] or ''}")
    print(f"{pid}: {open_} promise(s) not delivered")
    return 1 if open_ else 0


def main(argv: list[str]) -> int:
    if argv[:1] == ["load"]:
        w = reload()
        print({t: len(w.rows(t)) for t in TABLES if w.rows(t)})
        return 0
    if argv[:1] == ["items"]:
        return items()
    if argv[:1] == ["power"]:
        return power()
    if argv[:1] == ["ladder"]:
        return ladder()
    if argv[:1] == ["recipes"]:
        from tools.places.stock import recipes
        doc = recipes.generate()
        (STOCK / "recipes.json").write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
        print(f"recipes.json: {len(doc['recipes'])} recipes; {doc['audit']}")
        return 0
    if argv[:1] == ["promises"] and len(argv) == 2:
        return promises(argv[1])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
