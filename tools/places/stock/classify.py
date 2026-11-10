"""The split, run over a place: every container, loose item and person's inventory item, sorted into set dressing
or significant from record data alone (scale.json `split`), and the list of what it catches printed before anything
is taken out.

    python -m tools.places stock classify <place_id> [--out DIR] [--json PATH] [--all]

Reads the draft bundle `out/places/bundles/draft.<place_id>` (the place files resolved: the exterior and every copied
room), the place's people.jsonl, and the item records of the source's plugins. A container's contents and a person's
inventory and outfit are read at level 1, as the build flattens them (decision 0035). A container is significant when
its kind always is (chest, strongbox, safe, corpse, boss or merchant chest), when it is locked, or when it holds a
significant thing; a person's significant things are listed under them.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from tools.places.stock import split
from tools.places.stock.place import Place
from tools.places.stock.records import ITEM_SIGS


def classify(p: Place) -> list[dict]:
    """One row per thing: {holder: container|loose|person, space, ref?, person?, container_kind?, locked?, item,
    edid, name, kind, count, chance, value, significant, reason}."""
    rules = split.rules()
    rec = p.rec
    rows: list[dict] = []

    def items_of(base: str, n: float = 1) -> list[dict]:
        out = []
        for key, cnt, ch in rec.expand(base, 1):
            it = rec.item(key)
            if it is None:
                continue
            kind, sig, why = split.item_class(it, rules)
            out.append({"item": key, "edid": it["edid"], "name": it["name"], "kind": kind, "count": round(cnt * n, 2),
                        "chance": round(ch, 3), "value": it["value"], "significant": sig, "reason": why})
        return out

    for space, r in p.refs:
        base = r.get("base")
        sig = rec.sig(base) if base else None
        if sig == "CONT":
            c = rec.cont(base)
            ckind, always = split.container_kind(c, rules)
            inside = [i for k, n in c["items"] for i in items_of(k, n)]
            locked = bool(r.get("lock"))
            significant = always or locked or any(i["significant"] for i in inside)
            why = ("always significant" if always else "locked" if locked else
                   "holds a significant thing" if significant else "set dressing")
            head = {"holder": "container", "space": space, "ref": r["id"], "base": base, "container_kind": ckind,
                    "locked": locked, "lock": r.get("lock"), "owner": r.get("owner"), "respawns": c["respawns"],
                    "container_significant": significant, "container_reason": why}
            if not inside:
                rows.append({**head, "item": None, "significant": significant, "reason": why})
            rows += [{**head, **i} for i in inside]
        elif sig in ITEM_SIGS or sig == "LVLI":
            if sig == "LIGH" and not (rec.item(base) or {}).get("carried"):
                continue
            n = r.get("count") or 1
            for i in items_of(base, n):
                rows.append({"holder": "loose", "space": space, "ref": r["id"], "owner": r.get("owner"), **i})
    for person in p.people:
        npc = rec.npc(person.get("base_from") or "")
        if npc is None:
            continue
        tpl = rec.npc(npc["template"]) if npc["template"] else None
        carried = npc["items"] or (tpl["items"] if tpl else [])
        worn = rec.outfit(npc["outfit"] or (tpl or {}).get("outfit") or "")
        name = (p.identities.get(person["id"]) or {}).get("name") or person.get("name")
        for k, n in carried:
            rows += [{"holder": "person", "person": person["id"], "person_name": name, "role": person.get("role"),
                      "worn": False, **i} for i in items_of(k, n)]
        for k in worn:
            rows += [{"holder": "person", "person": person["id"], "person_name": name, "role": person.get("role"),
                      "worn": True, **i} for i in items_of(k)]
    return rows


def report(rows: list[dict], top: int = 10) -> str:
    sig = [r for r in rows if r.get("significant") and r.get("item")]
    conts = {r["ref"]: r for r in rows if r["holder"] == "container"}
    lines = [f"containers: {len(conts)}; significant {sum(r['container_significant'] for r in conts.values())} "
             f"({dict(Counter(r['container_kind'] for r in conts.values() if r['container_significant']))}); "
             f"set dressing {sum(not r['container_significant'] for r in conts.values())}"]
    for holder in ("container", "loose", "person"):
        hs = [r for r in rows if r["holder"] == holder and r.get("item")]
        s = [r for r in hs if r["significant"]]
        lines.append(f"{holder} items: {len(hs)} possible (each pick of a levelled list a line), significant {len(s)} "
                     f"by kind "
                     f"{dict(Counter(r['kind'] for r in s).most_common())}; set dressing {len(hs) - len(s)}")
    lines.append(f"top {top} significant by value (unit value x count):")
    best = sorted(sig, key=lambda r: -(r["value"] * max(r["count"], 1)))[:top]
    for r in best:
        where = (f"{r['container_kind']} {r['ref']} in {r['space']}" if r["holder"] == "container" else
                 f"loose {r['ref']} in {r['space']}" if r["holder"] == "loose" else
                 f"{r['person_name']} ({r['role']}{', worn' if r.get('worn') else ''})")
        chance = "" if r["chance"] >= 1 else f" (chance {r['chance']:.2f})"
        lines.append(f"  {r['value'] * max(r['count'], 1):>6.0f}  {r['name'] or r['edid']} x{r['count']:g}{chance}"
                     f"  [{r['kind']}]  {where}")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="stock classify")
    ap.add_argument("place")
    ap.add_argument("--out", help="the places output folder holding bundles/ (default out/places)")
    ap.add_argument("--json", help="write every row here")
    ap.add_argument("--all", action="store_true", help="also print every significant row")
    a = ap.parse_args(argv)
    p = Place.load(a.place, Path(a.out) if a.out else None)
    rows = classify(p)
    print(report(rows))
    if a.all:
        for r in rows:
            if r.get("significant") and r.get("item"):
                print(json.dumps(r, ensure_ascii=False))
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    return 0
