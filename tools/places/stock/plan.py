"""What the build makes of a place's stock (docs/design/place-studio.md, Stock: "What the build makes of it").

    from tools.places.stock import plan as stockplan
    stock = stockplan.plan(P, S, people, ids, problem, notes)   # None for a place with no stock source
    stockplan.key(place_id)                                     # what the shard's key must change with

Reads the stock tables of the new world's database (loaded from `newworld/sources/stock/places/<place>.json` and
`newworld/sources/people/<place>.json` by `tools.newworld.stockdb load`) and the item records of the plugins the
place's bases come from. It changes the planned refs and people in place and returns the records the writer
(tools/ArgoniaPlaces/Build Stock.cs and People.cs) adds:
  - a `stock_container` row: the ref's base becomes a container of ours holding the base's own set dressing (at
    level 1) plus exactly the row's items and gold, never respawning; the ref gets the row's lock (its level, no
    key) and owner (a person's actor base, a household faction of ours whose members are the household's people at
    rank 0, or the named faction);
  - a container the split calls significant with no row: a copy of ours holding its set dressing alone;
  - a container whose placed ref carries a `name` (a thing the place names, place-studio.md, Place files): a copy of
    ours with that name, holding its row's items and gold alone (a new thing keeps none of its base's contents);
  - `person_item` rows: the person's actor base carries exactly the non-worn rows plus the base's own set dressing,
    and wears an outfit of ours of the worn rows plus the base outfit's set dressing in the slots they leave free; a
    death item that would give a significant thing is cleared;
  - a `trader` row: the vendor's merchant chest holds exactly the row's items and gold (it restocks to them);
  - a `stock_loose` row: whose id is a ref of the place, that ref kept with the row's owner and count; any other
    id, a new placed ref of the item at `pos` (or on the named container's top); every other significant loose ref
    of the place is not built.
Nothing levelled is left by it: every list is read at level 1 the way the writer flattens one (records.fixed).
"""
from __future__ import annotations

import hashlib
from collections import defaultdict
from pathlib import Path

from tools.places.stock import split
from tools.places.stock.records import GOLD, ITEM_SIGS, Records

REPO = Path(__file__).resolve().parents[3]
STOCK_SRC = REPO / "newworld" / "sources" / "stock"
PEOPLE_SRC = REPO / "newworld" / "sources" / "people"
DB_DIR = REPO / "newworld" / "story" / "data" / "db"
TABLES = ("stock_container", "stock_container_item", "stock_loose", "person_item", "trader", "trader_item",
          "unique_item", "household", "person", "lock_level")
MASTER_ORDER = ("Skyrim.esm", "Update.esm", "Dawnguard.esm", "HearthFires.esm", "Dragonborn.esm", "Black Marsh.esm")
OUR_PLUGIN = "ArgoniaNWPlaces.esp"


def stock_source(place_id: str) -> Path:
    return STOCK_SRC / "places" / f"{place_id}.json"


def key(place_id: str) -> str:
    """The stock's part of a shard's key: the stock tables, the people and stock sources and this code."""
    h = hashlib.sha256(place_id.encode())
    here = Path(__file__).parent
    for p in [stock_source(place_id), PEOPLE_SRC / f"{place_id}.json", STOCK_SRC / "scale.json"] + \
             [DB_DIR / f"{t}.jsonl" for t in TABLES] + [here / n for n in ("plan.py", "split.py", "records.py")]:
        if p.exists():
            h.update(p.name.encode() + p.read_bytes())
    return h.hexdigest()[:16]


def plugins_of(keys) -> list[str]:
    """The plugins a set of form keys come from, masters first in their load order."""
    names = {k.rsplit(":", 1)[0] for k in keys if isinstance(k, str) and ":" in k} - {OUR_PLUGIN, "ArgoniaNewWorld.esm"}
    return [m for m in MASTER_ORDER] + sorted(names - set(MASTER_ORDER))


class Stock:
    """The place's stock rows from the database, by holder."""

    def __init__(self, w, pid: str):
        self.pid = pid
        self.containers = {(r.space_id, r.ref_id): r for r in w.rows("stock_container", place_id=pid)}
        self.container_items = defaultdict(list)
        for r in w.rows("stock_container_item", place_id=pid):
            self.container_items[r.ref_id].append(r)
        self.loose = {r.id: r for r in w.rows("stock_loose", place_id=pid)}
        self.persons = {r.id: r for r in w.rows("person", place_id=pid)}
        self.households = {r.id: r for r in w.rows("household", place_id=pid)}
        self.person_items = defaultdict(list)
        for r in w.rows("person_item"):
            if r.person_id in self.persons:
                self.person_items[r.person_id].append(r)
        self.traders = {r.person_id: r for r in w.rows("trader") if r.person_id in self.persons}
        self.trader_items = defaultdict(list)
        for r in w.rows("trader_item"):
            if r.person_id in self.persons:
                self.trader_items[r.person_id].append(r)
        self.locks = {r.id: r.level for r in w.rows("lock_level")}


def load_stock(pid: str):
    """The place's stock from the database, or None when the place has no stock source (not stocked yet)."""
    if not stock_source(pid).exists():
        return None
    from tools.argonia_world import db
    from tools.newworld import frame
    return Stock(db.open(frame.ROOT), pid)


def plan(P: dict, S: dict, people: dict, ids, problem, notes: list[str], st: "Stock | None" = None,
         rec: Records | None = None) -> dict | None:
    pid = P["place"]["place_id"]
    st = st or load_stock(pid)
    if st is None:
        return None
    rules = split.rules()
    if rec is None:
        keys = [r.get("base") for r in S["refs"]] + [n.get("from") for n in (people or {}).get("npcs", [])]
        rec = Records.load(plugins_of(keys))
    out = {"containers": [], "outfits": [], "taken_out": [], "kept_loose": [], "placed_loose": []}

    def significant(k: str) -> bool:
        it = rec.item(k)
        return bool(it) and split.item_class(it, rules)[1]

    def dressing(pairs) -> list[dict]:
        """The set dressing of (key, count) pairs, each list read at level 1 as the writer flattens it."""
        got: dict[str, int] = {}
        for k, n in pairs:
            for x, c in rec.fixed(k):
                if rec.item(x) is not None and not significant(x):
                    got[x] = got.get(x, 0) + c * n
        return [{"item": x, "count": c} for x, c in got.items()]

    def sig_of(pairs) -> list[str]:
        return [x for k, n in pairs for x, _ in rec.fixed(k) if significant(x)]

    # owners: a person's actor base, a household faction of ours, a faction of the place, or a form key
    npc_of = {n["id"]: n for n in (people or {}).get("npcs", [])}
    fac_by_fk = {f["fk"]: f for f in (people or {}).get("factions", [])}
    households_used: set[str] = set()

    def owner(person=None, household=None, faction=None, where="") -> str | None:
        if person:
            if person not in npc_of:
                problem(f"stock: {where}: owner {person} is no person of {pid}")
                return None
            return npc_of[person]["fk"]
        if household or (faction and faction in st.households):
            hid = household or faction
            if hid not in st.households:
                problem(f"stock: {where}: owner household {hid} is no household of {pid}")
                return None
            households_used.add(hid)
            return ids(f"fact:household:{hid}")
        if faction:
            if ":" in faction and not faction.startswith(f"{pid}."):
                return faction
            name = faction.split(".", 1)[1] if faction.startswith(f"{pid}.") else faction
            fk = ids("fact:town" if name == "town" else f"fact:{name}")
            if fk not in fac_by_fk:
                problem(f"stock: {where}: owner faction {faction} is not a faction of {pid}'s people")
                return None
            return fk
        return None

    # containers and loose refs, by the stock source's way of naming a ref: our id outside, the source key in a room
    def stock_ref(r: dict) -> str:
        return r["src"] if r["space"] != "exterior" and r.get("src") else r["id"]

    gone: set[str] = set()
    n_cont = 0
    seen_rows: set = set()
    for r in S["refs"]:
        base = r.get("base") or ""
        sig = rec.sig(base)
        sref = stock_ref(r)
        if sig == "CONT":
            c = rec.cont(base)
            row = st.containers.get((r["space"], sref))
            source_sig = sig_of(c["items"])
            named = r.get("name")
            if row is None and not source_sig and not named and not split.container_kind(c, rules)[1]:
                continue                                # set dressing: built as the source has it
            seen_rows.add((r["space"], sref))
            n_cont += 1
            items = [] if named else dressing(c["items"])
            if row is not None:
                items += [{"item": i.item_id, "count": i.count} for i in st.container_items.get(sref, [])]
                if row.gold:
                    items.append({"item": GOLD, "count": row.gold})
                where = f"container {sref} in {r['space']}"
                r["lock"] = st.locks[row.lock_level_id] if row.lock_level_id else None
                r["owner"] = owner(row.owner_person_id, row.owner_household_id, row.owner_faction, where)
            fk = ids(f"cont:stock:{r['space']}:{sref}")
            out["containers"].append({"fk": fk, "edid": f"ANP_{pid}_Stock{n_cont:03d}", "from": base, "items": items,
                                      "ref": r["fk"], "row": row is not None, **({"name": named} if named else {})})
            out["taken_out"] += [{"holder": sref, "item": x} for x in source_sig]
            r["base"] = fk
            r["stock_base_from"] = base
        elif r.get("name"):
            problem(f"stock: {sref} in {r['space']}: named {r['name']!r}, but only a container carries a name of ours "
                    f"(its base {base} is a {sig})")
        elif (sig in ITEM_SIGS or sig == "LVLI") and r.get("kind") != "container":
            row = st.loose.get(sref)
            if row is None:
                if any(significant(x) for x, _ in rec.fixed(base)):
                    gone.add(r["id"])
                    out["taken_out"] += [{"holder": sref, "item": x} for x, _ in rec.fixed(base)]
                continue
            r["owner"] = owner(row.owner_person_id, None, row.owner_faction, f"loose {sref}")
            r["count"] = row.count
            out["kept_loose"].append(sref)
    for (space, sref), row in st.containers.items():
        if (space, sref) not in seen_rows:
            problem(f"stock: container row {sref} in {space} names no container of the place")
    if gone:
        S["refs"][:] = [r for r in S["refs"] if r["id"] not in gone]
        for i in gone:
            S["by_id"].pop(i, None)

    # new loose things
    have = {stock_ref(r) for r in S["refs"]} | set(out["kept_loose"])
    by_stock = {(r["space"], stock_ref(r)): r for r in S["refs"]}
    from tools.places.build import cell_of
    for lid, row in sorted(st.loose.items()):
        if lid in have:
            continue
        pos = [row.x, row.y, row.z] if row.x is not None else None
        if pos is None and row.on_ref_id:
            on = by_stock.get((row.space_id, row.on_ref_id))
            c = rec.raw.get((on or {}).get("stock_base_from") or (on or {}).get("base") or "")
            top = _obnd_top(c) if c is not None else None
            if on is None or top is None:
                problem(f"stock: loose {lid}: lies on {row.on_ref_id}, which is no container of {row.space_id}: give it a pos")
                continue
            pos = [on["pos"][0], on["pos"][1], on["pos"][2] + top * float(on.get("scale") or 1.0)]
        if pos is None:
            problem(f"stock: loose {lid}: neither a ref of the place nor a pos")
            continue
        new = {"id": lid, "fk": ids(f"ref:{lid}"), "base": row.item_id, "kind": "clutter", "space": row.space_id,
               "pos": pos, "rot": [0.0, 0.0, 0.0], "scale": 1.0, "count": row.count, "disabled": False,
               "persistent": False, "owner": owner(row.owner_person_id, None, row.owner_faction, f"loose {lid}"),
               "seat": {"mode": "free"}}
        if row.space_id == "exterior":
            new["cell"] = list(cell_of(*pos[:2]))
        S["refs"].append(new)
        S["by_id"][lid] = new
        out["placed_loose"].append(lid)

    # people: inventory, outfit, death item
    for n in (people or {}).get("npcs", []):
        who = n["id"]
        npc = rec.npc(n["from"]) or {}
        rows = st.person_items.get(who, [])
        # only armour and clothing make an outfit; a worn weapon is carried, and the actor draws its best one
        carried = [{"item": i.item_id, "count": i.count} for i in rows if not (i.worn and rec.sig(i.item_id) == "ARMO")]
        worn = [i.item_id for i in rows if i.worn and rec.sig(i.item_id) == "ARMO"]
        n["inventory"] = dressing(npc.get("items") or []) + carried
        taken = sum((rec.item(k) or {}).get("slots", 0) for k in worn)
        base_worn = [x for k in rec.outfit(npc.get("outfit") or "") for x, _ in rec.fixed(k)]
        keep = []
        for x in base_worn:
            it = rec.item(x)
            if it is None or significant(x):
                continue
            if it.get("slots", 0) & taken:
                continue                                # the worn row takes this slot
            taken |= it.get("slots", 0)
            keep.append(x)
        ofk = ids(f"otft:stock:{who}")
        out["outfits"].append({"fk": ofk, "edid": f"{n['edid']}_StockOutfit", "items": keep + worn})
        n["outfit"] = ofk
        if npc.get("death_item") and sig_of([(npc["death_item"], 1)]):
            n["clear_death_item"] = True
        out["taken_out"] += [{"holder": who, "item": x} for x in sig_of(npc.get("items") or [])] + \
                            [{"holder": who, "item": x} for x in base_worn if significant(x)]
    for who in st.person_items:
        if who not in npc_of:
            problem(f"stock: possessions of {who}, who is no person of {pid}'s build")

    # traders: the merchant chest holds exactly the row's list and gold
    for c in (people or {}).get("containers", []):
        who = c.get("who")
        row = st.traders.get(who)
        if row is None:
            if who:
                notes.append(f"stock: {who} trades with no trader row: the merchant chest keeps vanilla's list at level 1")
            continue
        c["items"] = [{"item": i.item_id, "count": i.count} for i in st.trader_items.get(who, [])] + \
                     ([{"item": GOLD, "count": row.gold}] if row.gold else [])
    for who in st.traders:
        if not any(c.get("who") == who for c in (people or {}).get("containers", [])):
            problem(f"stock: trader row of {who}, who has no merchant chest (no trader-* service in people.jsonl)")

    # household factions: one of ours per owning household, every member at rank 0
    for hid in sorted(households_used):
        fk = ids(f"fact:household:{hid}")
        people["factions"].append({"fk": fk, "edid": f"ANP_{pid}_Household_{_edid(hid)}", "name": f"{hid} household"})
        for p in st.persons.values():
            if p.household_id == hid and p.id in npc_of:
                npc_of[p.id]["factions"].append({"faction": fk, "rank": 0})
    out["counts"] = {"containers": len(out["containers"]), "rows": sum(c["row"] for c in out["containers"]),
                     "outfits": len(out["outfits"]), "kept_loose": len(out["kept_loose"]),
                     "placed_loose": len(out["placed_loose"]), "taken_out": len(out["taken_out"])}
    return out


def _obnd_top(rec) -> float | None:
    d = rec.sub("OBND")
    if not d or len(d) < 12:
        return None
    import struct
    return float(struct.unpack_from("<6h", d)[5])


def _edid(s: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in s.split(".", 1)[-1])
