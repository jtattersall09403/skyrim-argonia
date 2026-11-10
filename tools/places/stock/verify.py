"""The build check of a place's stock (docs/design/place-studio.md, Stock: "What the build check proves"), on the
built plugin read back: `check` runs `check_stock` and `check_promises` as two of its checks.

    ctx["stock"] = verify.load(place_id, plan, dump, esp)     # None: the place has no stock source
    verify.check_stock(ctx)      -> failures: nothing significant untraced, every row built, owners, locks, value,
                                    no respawn, the ledger, the never list, each person within their band
    verify.check_promises(ctx)   -> failures: a promise not delivered, or delivered by something the build lacks
    verify.summary(ctx["stock"]) -> the counts and the most valuable things, for the report

Every function past `load` reads only the dict `load` makes, so a test feeds it a small fixture. An item of ours that
the writer copied from a plugin that is not a master is read as its source (`<esp>.copies.json`).
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from tools.places.stock import split
from tools.places.stock.plan import load_stock, plugins_of
from tools.places.stock.records import GOLD, ITEM_SIGS, Records


def _stock_ref(r: dict) -> str:
    return r["src"] if r["space"] != "exterior" and r.get("src") else r["id"]


def load(place_id: str, plan: dict, dump: dict, esp: Path) -> dict | None:
    st = load_stock(place_id)
    if st is None:
        return None
    from tools.argonia_world import db
    from tools.newworld import frame
    w = db.open(frame.ROOT)
    sc = split.scale()
    copies_p = Path(str(esp) + ".copies.json")
    copies = json.loads(copies_p.read_text()) if copies_p.exists() else {}

    def src(k):
        return copies.get(k, k) if isinstance(k, str) else k

    built_refs = {r["fk"]: r for r in dump["refs"]}
    keys = set()
    for r in dump["refs"]:
        keys.add(src(r.get("base")))
        keys |= {src(c[0]) for c in r.get("contents") or []}
    for n in dump["npcs"]:
        keys |= {src(c[0]) for c in n.get("inventory") or []} | {src(k) for k in n.get("outfit_items") or []}
    keys |= {i.item_id for v in st.container_items.values() for i in v} | {r.item_id for r in st.loose.values()}
    keys |= {i.item_id for v in st.person_items.values() for i in v} | {i.item_id for v in st.trader_items.values() for i in v}
    rec = Records.load(plugins_of(keys))
    rules = sc["split"]
    never_m = set(sc["never"]["materials"])
    never_w = [x.lower() for x in sc["never"]["edid_words"]]

    def info(k: str) -> dict:
        it = rec.item(k)
        if it is None:
            return {"known": False, "significant": False, "value": 0, "tier": "T1", "kind": "?", "never": False, "edid": k}
        kind, sig, _ = split.item_class(it, rules)
        mat = next((m for m in it["keywords"] if "Material" in m), None)
        tier = split.item_tier(it, sc)[0]
        return {"known": True, "significant": sig, "value": it["value"], "tier": tier, "kind": kind, "edid": it["edid"],
                "sig": it["sig"],
                "name": it["name"], "never": bool(mat in never_m or any(x in (it["edid"] or "").lower() for x in never_w))}

    items = {k: info(k) for k in keys if k}
    pw = w.get("place_wealth", place_id)
    mine_fk = {r["fk"] for r in plan["refs"]}
    built = {"containers": {}, "loose": {}, "npcs": {}, "chests": {}}
    for r in plan["refs"]:
        d = built_refs.get(r["fk"])
        if d is None:
            continue
        key = (r["space"], _stock_ref(r))
        if d.get("contents") is not None:
            built["containers"][key] = {"fk": r["fk"], "contents": [(src(a), n) for a, n in d["contents"]],
                                        "respawns": d.get("respawns", False), "lock": d.get("lock"), "owner": d.get("owner")}
        elif rec.sig(src(d.get("base"))) in ITEM_SIGS:
            built["loose"][key] = {"fk": r["fk"], "item": src(d["base"]), "count": d.get("count") or 1, "owner": d.get("owner")}
    ppl = plan.get("people") or {}
    npc_fk = {n["id"]: n["fk"] for n in ppl.get("npcs", [])}
    dnpc = {n["fk"]: n for n in dump["npcs"]}
    for who, fk in npc_fk.items():
        n = dnpc.get(fk) or {}
        built["npcs"][who] = {"fk": fk, "inventory": [(src(a), c) for a, c in n.get("inventory") or []],
                              "outfit_items": [src(k) for k in n.get("outfit_items") or []],
                              "death_item": n.get("death_item") or "", "faction_keys": n.get("faction_keys") or []}
    chest_who = {c["fk"]: c.get("who") for c in ppl.get("containers", [])}
    for d in dump["refs"]:
        if d.get("base") in chest_who and d["fk"] in {m["fk"] for m in ppl.get("markers", [])}:
            built["chests"][chest_who[d["base"]]] = {"contents": [(src(a), n) for a, n in d.get("contents") or []],
                                                     "respawns": d.get("respawns", False)}
    fac_by_name = {f.get("name"): f["fk"] for f in ppl.get("factions", [])}
    owner_fk = {**{f"person:{p}": fk for p, fk in npc_fk.items()},
                **{f"household:{h}": fac_by_name.get(f"{h} household") for h in st.households},
                **{f"faction:{place_id}.{n.split(' ', 1)[1]}": fk for n, fk in fac_by_name.items()
                   if n and n.startswith(f"{place_id} ") and " " in n}}
    bands = {b["id"]: b for b in sc["person_wealth_bands"]}
    gives = {g.seq: g for g in w.rows("place_give", place_id=place_id)}
    return {
        "pid": place_id, "items": items, "mine": mine_fk,
        "tier_rank": {t["id"]: t["rank"] for t in sc["tiers"]}, "value_max": {t["id"]: t["value_max"] for t in sc["tiers"]},
        "open": pw.open_tier_id, "ceiling": pw.ceiling_tier_id, "locks": dict(st.locks),
        "sec_rank": {s_["id"]: i for i, s_ in enumerate(sc["security"])}, "share": sc["budget"]["owner_share"],
        "bands": bands, "issue_tier": split.guard_issue(getattr(w.get("place", place_id), "culture_id", None),
                                                        pw.ceiling_tier_id, split.source_plugins(place_id), sc)["tier"],
        "caps": sc["ledger"]["caps"],
        "containers": [{"ref": r.ref_id, "space": r.space_id, "owner_person": r.owner_person_id,
                        "owner_household": r.owner_household_id, "owner_faction": r.owner_faction, "lock": r.lock_level_id,
                        "security": r.security_level_id, "tier": r.stock_tier_id, "gold": r.gold,
                        "items": [(i.item_id, i.count) for i in st.container_items.get(r.ref_id, [])]}
                       for r in st.containers.values()],
        "loose": [{"id": r.id, "space": r.space_id, "item": r.item_id, "count": r.count, "owner_person": r.owner_person_id,
                   "owner_faction": r.owner_faction} for r in st.loose.values()],
        "persons": {p.id: {"band": p.person_wealth_band_id, "household": p.household_id, "role": p.person_role_id,
                           "name": p.name} for p in st.persons.values()},
        "person_items": {p: [(i.item_id, i.count, bool(i.worn)) for i in v] for p, v in st.person_items.items()},
        "traders": {p: {"gold": t.gold, "items": [(i.item_id, i.count) for i in st.trader_items.get(p, [])]}
                    for p, t in st.traders.items()},
        "deliveries": [{"give_seq": d.give_seq, "kind": gives[d.give_seq].give_kind_id if d.give_seq in gives else "?",
                        "detail": gives[d.give_seq].detail if d.give_seq in gives else "", "status": d.status, "by": d.by,
                        "person": d.person_id, "ref": d.ref_id, "why": d.why}
                       for d in w.rows("give_delivery", place_id=place_id)],
        "unique": [{"item": u.item_id, "place": u.place_id, "held_by": u.held_by} for u in w.rows("unique_item")],
        "built": built, "owner_fk": owner_fk, "world_markers": set((dump.get("world_markers") or {}).values()),
    }


def _sig(X: dict, k: str) -> bool:
    return k == GOLD or X["items"].get(k, {}).get("significant", False)


def _counts(pairs) -> Counter:
    c = Counter()
    for k, n in pairs:
        c[k] += n
    return c


def _diff(holder: str, want: Counter, got: Counter, X: dict) -> list[str]:
    """A holder's built things against its row: every significant thing exactly as the row has it, every set
    dressing thing of the row at least as many (the base's own set dressing may add to it)."""
    bad = []
    for k in sorted(set(want) | {k for k in got if _sig(X, k)}):
        ok = want[k] == got[k] if _sig(X, k) else got[k] >= want[k]
        if not ok:
            name = X["items"].get(k, {}).get("edid") or k
            bad.append(f"{holder}: {name} ({k}) x{got[k]} built, x{want[k]} in its row" if want[k] else
                       f"{holder}: {name} ({k}) x{got[k]} traces to no stock row")
    return bad


def _armour(X: dict, k: str) -> bool:
    """Only armour and clothing go in an outfit; a worn weapon is carried and the actor draws it."""
    return X["items"].get(k, {}).get("sig") == "ARMO"


def _owner_want(X: dict, person=None, household=None, faction=None) -> tuple[str | None, str]:
    if person:
        return X["owner_fk"].get(f"person:{person}"), f"person {person}"
    if household:
        return X["owner_fk"].get(f"household:{household}"), f"household {household}"
    if faction:
        if faction in X["owner_fk"].values() or ":" in faction and not faction.startswith(f"{X['pid']}."):
            return faction, f"faction {faction}"
        fk = X["owner_fk"].get(f"household:{faction}") or X["owner_fk"].get(f"faction:{faction}")
        return fk, f"faction {faction}"
    return None, "nobody"


def check_stock(ctx) -> list[str]:
    X = ctx.get("stock")
    if not X:
        return []
    bad: list[str] = []
    B, R = X["built"], X["tier_rank"]
    rows = {(c["space"], c["ref"]): c for c in X["containers"]}
    unique_items = {u["item"] for u in X["unique"] if u["place"] == X["pid"]}
    top = R[X["ceiling"]]

    def item_rules(holder: str, k: str, cap_tier: str | None = None):
        i = X["items"].get(k, {})
        if i.get("never"):
            bad.append(f"never: {holder}: {i.get('edid')} ({k}) is of a never material or a Skyrim-only kit")
        if (i.get("tier") == "T6" or k in unique_items) and k not in unique_items:
            bad.append(f"ledger: {holder}: {i.get('edid')} ({k}) is {i.get('tier')} with no unique_item row")
        if i.get("significant") and k not in unique_items and R.get(i.get("tier"), 0) > top:
            bad.append(f"value: {holder}: {i.get('edid')} ({k}) is {i.get('tier')}, above the place's ceiling {X['ceiling']}")
        if cap_tier and i.get("significant") and k != GOLD and k not in unique_items and R.get(i.get("tier"), 0) > R[cap_tier]:
            bad.append(f"value: {holder}: {i.get('edid')} ({k}) is {i.get('tier')}, above its holder's {cap_tier}")

    # containers: every one of the place traces to its row (a container with no row holds nothing significant)
    for key, b in sorted(B["containers"].items()):
        row = rows.get(key)
        holder = f"container {key[1]} in {key[0]}"
        got = _counts(b["contents"])
        want = _counts(row["items"] + ([(GOLD, row["gold"])] if row["gold"] else [])) if row else Counter()
        bad += [f"traces: {x}" for x in _diff(holder, want, got, X)]
        if row is None:
            continue
        if b["respawns"]:
            bad.append(f"respawn: {holder} respawns (only a trader's merchant chest restocks)")
        lock = X["locks"].get(row["lock"]) if row["lock"] else None
        if (b["lock"] or None) != lock:
            bad.append(f"locks: {holder}: built lock {b['lock']}, its row's {row['lock'] or 'none'} ({lock})")
        fk, who = _owner_want(X, row["owner_person"], row["owner_household"], row["owner_faction"])
        if (b["owner"] or None) != fk:
            bad.append(f"owner: {holder}: built owner {b['owner'] or 'none'}, its row's {who} ({fk})")
        if fk is None and row["security"] != "S0":
            bad.append(f"owner: {holder}: {row['security']} but nobody's (only S0 things and the wild are unowned)")
        reach = R[X["open"]] + X["sec_rank"][row["security"]]
        if R[row["tier"]] > reach:
            bad.append(f"locks: {holder}: tier {row['tier']} above what {row['security']} keeps (up to rank {reach})")
        share = X["share"]["none"]
        if row["owner_person"]:
            share = X["share"][X["persons"][row["owner_person"]]["band"]]
        elif row["owner_household"]:
            bands = [p["band"] for p in X["persons"].values() if p["household"] == row["owner_household"]]
            share = X["share"][max(bands)] if bands else X["share"]["none"]
        elif row["owner_faction"]:
            share = X["share"]["faction"]
        value = sum(X["items"].get(k, {}).get("value", 0) * n for k, n in row["items"] if k != GOLD)
        if value > X["value_max"][row["tier"]] * share:
            bad.append(f"value: {holder}: significant things worth {value}, over its budget "
                       f"{X['value_max'][row['tier']]} x {share}")
        for k, _n in row["items"]:
            item_rules(holder, k, row["tier"])
    for key in sorted(set(rows) - set(B["containers"])):
        bad.append(f"built: container row {key[1]} in {key[0]} is not in the build")

    # loose things: every significant one is a row; every row is built with its owner and count
    lrows = {(r["space"], r["id"]): r for r in X["loose"]}
    for key, b in sorted(B["loose"].items()):
        row = lrows.get(key)
        holder = f"loose {key[1]} in {key[0]}"
        if row is None:
            if _sig(X, b["item"]):
                bad.append(f"traces: {holder}: {X['items'].get(b['item'], {}).get('edid')} traces to no stock row")
            continue
        if b["item"] != row["item"] or b["count"] != row["count"]:
            bad.append(f"built: {holder}: {b['item']} x{b['count']} built, {row['item']} x{row['count']} in its row")
        fk, who = _owner_want(X, row["owner_person"], None, row["owner_faction"])
        if (b["owner"] or None) != fk:
            bad.append(f"owner: {holder}: built owner {b['owner'] or 'none'}, its row's {who} ({fk})")
        item_rules(holder, row["item"])
    for key in sorted(set(lrows) - set(B["loose"])):
        bad.append(f"built: loose row {key[1]} in {key[0]} is not in the build")

    # people: exactly their rows (carried and worn), within their band
    for who, b in sorted(B["npcs"].items()):
        p = X["persons"].get(who)
        rows_ = X["person_items"].get(who, [])
        holder = f"person {who} ({(p or {}).get('name')})"
        bad += [f"traces: {x}" for x in _diff(holder + " carries", _counts((k, n) for k, n, wn in rows_
                                                                         if not (wn and _armour(X, k))),
                                              _counts(b["inventory"]), X)]
        bad += [f"traces: {x}" for x in _diff(holder + " wears", _counts((k, 1) for k, _n, wn in rows_ if wn and _armour(X, k)),
                                              _counts((k, 1) for k in b["outfit_items"]), X)]
        if b["death_item"] and X["items"].get(b["death_item"], {}).get("significant"):
            bad.append(f"traces: {holder}: death item {b['death_item']} gives a significant thing")
        if p is None:
            continue
        band = X["bands"][p["band"]]
        cap = X["ceiling"] if band["top_tier"] == "ceiling" else band["top_tier"]
        if R[cap] > top:
            cap = X["ceiling"]
        if p["role"] == "guard" and R[X["issue_tier"]] > R[cap]:
            cap = X["issue_tier"]
        gold = sum(n for k, n, _w in rows_ if k == GOLD)
        if gold > band["carried"][1]:
            bad.append(f"value: {holder}: carries {gold} gold, over {p['band']}'s {band['carried'][1]}")
        jew = sum(n for k, n, _w in rows_ if X["items"].get(k, {}).get("kind") == "jewellery")
        if jew > band["jewellery"]:
            bad.append(f"value: {holder}: {jew} pieces of jewellery, over {p['band']}'s {band['jewellery']}")
        for k, _n, _w in rows_:
            item_rules(holder, k, cap)
    for who in sorted(set(X["person_items"]) - set(B["npcs"])):
        bad.append(f"built: possessions of {who}, who is not in the build")

    # traders: the merchant chest holds exactly the list and the gold, and restocks
    for who, t in sorted(X["traders"].items()):
        b = B["chests"].get(who)
        holder = f"trader {who}'s merchant chest"
        if b is None:
            bad.append(f"built: {holder} is not in the build")
            continue
        bad += [f"traces: {x}" for x in _diff(holder, _counts(t["items"] + ([(GOLD, t["gold"])] if t["gold"] else [])),
                                              _counts(b["contents"]), X)]
        if not b["respawns"]:
            bad.append(f"respawn: {holder} does not restock")
        for k, _n in t["items"]:
            item_rules(holder, k)
    for who in sorted(set(B["chests"]) - set(X["traders"])):
        bad.append(f"traces: trader {who}'s merchant chest has no trader row")

    # the ledger, game-wide
    if len(X["unique"]) > X["caps"]["unique"]:
        bad.append(f"ledger: {len(X['unique'])} unique_item rows, over the cap {X['caps']['unique']}")
    return bad


def check_promises(ctx) -> list[str]:
    X = ctx.get("stock")
    if not X:
        return []
    bad = []
    built_people = set(X["built"]["npcs"])
    plan_refs = (ctx.get("plan") or {}).get("refs", [])
    refs_built = {k[1] for k in X["built"]["containers"]} | {k[1] for k in X["built"]["loose"]} | \
        {r["id"] for r in plan_refs} | {r.get("src") for r in plan_refs}
    seen = defaultdict(list)
    for d in X["deliveries"]:
        seen[d["give_seq"]].append(d)
    for seq, ds in sorted(seen.items()):
        for d in ds:
            what = f"promise {seq} {d['kind']} ({d['detail']})"
            if d["status"] == "open":
                bad.append(f"open: {what}: {d['why']}")
            elif d["status"] == "delivered":
                if d["by"] == "person" and d["person"] not in built_people:
                    bad.append(f"{what}: delivered by {d['person']}, who is not in the build")
                if d["by"] in ("ref", "container", "loose") and d["ref"] not in refs_built:
                    bad.append(f"{what}: delivered by {d['ref']}, which is not in the build")
    return bad


def summary(X: dict, top: int = 10) -> dict:
    """The stocked place in numbers: what is authored, placed and taken out, its value against its budgets, and the
    most valuable things with who or what holds them."""
    B = X["built"]
    things = []
    for c in X["containers"]:
        for k, n in c["items"]:
            things.append((X["items"].get(k, {}).get("value", 0) * n, k, n, f"container {c['ref']} in {c['space']}"))
    for r in X["loose"]:
        things.append((X["items"].get(r["item"], {}).get("value", 0) * r["count"], r["item"], r["count"], f"loose {r['id']}"))
    for who, rows in X["person_items"].items():
        for k, n, w in rows:
            if k != GOLD:
                things.append((X["items"].get(k, {}).get("value", 0) * n, k, n,
                               f"{X['persons'].get(who, {}).get('name')} ({'worn' if w else 'carried'})"))
    sold = [(X["items"].get(k, {}).get("value", 0) * n, k, n, f"{X['persons'].get(who, {}).get('name')}'s merchant chest")
            for who, t in X["traders"].items() for k, n in t["items"]]
    budget = 0.0
    for c in X["containers"]:
        share = X["share"]["none"]
        if c["owner_person"]:
            share = X["share"][X["persons"][c["owner_person"]]["band"]]
        elif c["owner_household"]:
            bands = [p["band"] for p in X["persons"].values() if p["household"] == c["owner_household"]]
            share = X["share"][max(bands)] if bands else 1.0
        elif c["owner_faction"]:
            share = X["share"]["faction"]
        budget += X["value_max"][c["tier"]] * share
    cont_value = sum(X["items"].get(k, {}).get("value", 0) * n for c in X["containers"] for k, n in c["items"] if k != GOLD)
    gold = sum(c["gold"] for c in X["containers"]) + sum(n for rows in X["person_items"].values() for k, n, _w in rows if k == GOLD)
    best = sorted(things + sold, key=lambda t: (-t[0], t[1]))[:top]
    return {"containers_authored": len(X["containers"]), "containers_built": len(B["containers"]),
            "loose_rows": len(X["loose"]), "possession_items": sum(len(v) for v in X["person_items"].values()),
            "trader_items": sum(len(t["items"]) for t in X["traders"].values()),
            "items_placed": sum(n for _v, k, n, _h in things if k != GOLD),
            "container_value": cont_value, "container_budget": round(budget),
            "people_value": sum(v for v, k, _n, h in things if h.endswith(("(worn)", "(carried)"))),
            "loose_value": sum(v for v, _k, _n, h in things if h.startswith("loose")), "gold": gold,
            "trader_value": sum(v for v, _k, _n, _h in sold), "trader_items_placed": sum(n for _v, _k, n, _h in sold),
            "top": [{"value": v, "item": X["items"].get(k, {}).get("name") or X["items"].get(k, {}).get("edid") or k,
                     "count": n, "held_by": h} for v, k, n, h in best]}
