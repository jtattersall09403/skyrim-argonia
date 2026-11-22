"""The material ladder on one place's stock (docs/design/items.md; skill `place-stock`): does the place reach every
material it holds, and how does its gear sit against its class's target mix?

    python -m tools.places stock reach <place_id> [--source PATH] [--md PATH]   # exit 1 while any row fails
    python -m tools.places stock mix <place_id> [--source PATH]

`reach` fails each stock row (a container's, a loose thing's, a person's, a trader's) whose item is of a material of
ours the place does not reach: a material reaches a place when any one of its `material_reach` rows holds (anywhere;
the place's kind or family; its culture; a pattern over its record text: name, map label, summary, held_by, aliases
and notes; a ledger row for a unique), and never when it is a never material or has no row. The reason names the
record text that matched, or says that the record gives none. `mix` counts the place's gear (weapons, armour and
shields; ammunition apart) by material, group and band, against the target of its class (scale.json `mix`).

Both read the stock source (newworld/sources/stock/places/<place>.json, or --source for a scratch copy) and the
database (items, materials, the place's record), never the built plugin, so they run on any machine. `place-check`
and `python -m tools.places handover` require `reach` to pass.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from tools.places.stock import split

STOCK = split.STOCK


NOT_WORLD = {"source"}      # a note on the source place a draft is carried from, not a fact of the world
NEG = re.compile(r"\b(no|not|never|without|nor|none|least|refused)\b", re.I)


def record_text(w, pid: str) -> list[tuple[str, str]]:
    """(where, sentence) of everything the place record says of the world in words: its name, map label, summary,
    holder, aliases and notes (the source note aside), one sentence at a time."""
    p = w.get("place", pid)
    out = [(f"place.{c}", getattr(p, c)) for c in ("name", "map_label", "summary", "held_by") if getattr(p, c, None)]
    out += [("place_alias", a.alias) for a in w.rows("place_alias", place_id=pid)]
    out += [(f"place_note.{n.aspect_id}", n.text) for n in w.rows("place_note", place_id=pid)
            if n.aspect_id not in NOT_WORLD]
    return [(where, s.strip()) for where, t in out for s in re.split(r"(?<=[.;!?])\s+", t) if s.strip()]


def says(pattern: str, text: list[tuple[str, str]]) -> tuple[str, str] | None:
    """(where, the words) of the first sentence that says the pattern and does not deny it."""
    for where, s in text:
        m = re.search(pattern, s, re.I)
        if m and not NEG.search(s[:m.start()]):
            return where, m.group(0)
    return None


def reaches(w, pid: str, unique_items: set[str] | None = None) -> dict[str, tuple[bool, str]]:
    """{material id: (reached, why)} for every material, by its material_reach rows (any one is enough)."""
    p = w.get("place", pid)
    kind = w.get("place_kind", p.place_kind_id)
    family = getattr(kind, "family", None)
    text = record_text(w, pid)
    never = {r.material_id for r in w.rows("never_material")}
    rows = defaultdict(list)
    for r in w.rows("material_reach"):
        rows[r.material_id].append(r)
    out = {}
    for m in w.rows("material"):
        if m.id in never:
            out[m.id] = (False, f"{m.label} is a never material (decision 0006)")
            continue
        got = None
        for r in sorted(rows[m.id], key=lambda r: r.seq):
            if r.kind == "anywhere":
                got = f"{m.band}: {r.why}"
            elif r.kind == "place-kind" and p.place_kind_id == r.value:
                got = f"the place is a {r.value}: {r.why}"
            elif r.kind == "place-family" and family == r.value:
                got = f"the place is of the {r.value} family ({p.place_kind_id}): {r.why}"
            elif r.kind == "culture" and getattr(p, "culture_id", None) == r.value:
                got = f"the place's culture is {r.value}: {r.why}"
            elif r.kind == "record":
                hit = says(r.value, text)
                if hit:
                    got = f"the record says \"{hit[1]}\" ({hit[0]}): {r.why}"
            elif r.kind == "unique":
                got = "unique" if unique_items is not None else None
            if got:
                break
        if got:
            out[m.id] = (True, got)
        elif not rows[m.id]:
            out[m.id] = (False, f"{m.label} is {m.band}: no road into Black Marsh")
        else:
            conds = "; ".join(f"{r.kind} {r.value}" if r.value else r.kind for r in rows[m.id])
            out[m.id] = (False, f"{m.label} is {m.band}, and the record gives no reason for it here (it needs: {conds}; "
                                f"the place is a {p.place_kind_id}, culture {getattr(p, 'culture_id', None) or 'none'}, "
                                f"and no words of its record match)")
    return out


def stock_rows(doc: dict):
    """Every item row of a stock source: {holder, item, count, exception, person, household}; `person` is the person
    whose kit judges the row (a possession's owner, a container's owning person), `household` a container's owning
    household (judged by its head's kit)."""
    for c in doc.get("containers", []):
        for it in c.get("items", []):
            yield {"holder": f"container {c['ref']} in {c['space']}", "item": it["item"], "count": it["count"],
                   "exception": it.get("exception"), "person": c.get("owner_person"),
                   "household": c.get("owner_household")}
    for lo in doc.get("loose", []):
        yield {"holder": f"loose {lo['id']} in {lo['space']}", "item": lo["item"], "count": lo["count"],
               "exception": lo.get("exception"), "person": lo.get("owner_person"), "household": None}
    for po in doc.get("possessions", []):
        for it in po.get("items", []):
            yield {"holder": f"person {po['person']}", "item": it["item"], "count": it["count"],
                   "exception": it.get("exception"), "person": po["person"], "household": None}
    for t in doc.get("traders", []):
        for it in t.get("items", []):
            yield {"holder": f"trader {t['person']}", "item": it["item"], "count": it["count"],
                   "exception": it.get("exception"), "person": None, "household": None}


def load_source(pid: str, source: Path | None = None) -> dict:
    p = source or STOCK / "places" / f"{pid}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def region_bands(w, pid: str) -> dict[str, tuple[str, str]]:
    """{material: (band, why)} of the place's region (region_material)."""
    rid = w.get("place", pid).region_id
    return {r.material_id: (r.band, r.why) for r in w.rows("region_material", region_id=rid)}


def audit(w, pid: str, doc: dict) -> list[dict]:
    """Every stock row whose item's material the place does not reach, or that its region marks absent, unless the
    row carries an `exception`: {holder, item, edid, count, material, rule, why}."""
    uniq = {u.item_id for u in w.rows("unique_item") if u.place_id == pid}
    reach = reaches(w, pid, uniq)
    region = region_bands(w, pid)
    rid = w.get("place", pid).region_id
    items = {r.id: r for r in w.rows("item")}
    mats = {m.id: m for m in w.rows("material")}
    exp = expected_mix(w, pid)
    none_of = {g for t in exp["targets"] if t["pct"] == 0 for g in t["groups"]}
    bad = []
    guards = {p.id for p in w.rows("person", place_id=pid) if p.person_role_id == "guard"}
    for row in stock_rows(doc):
        it = items.get(row["item"])
        if it is not None and not row["exception"]:
            wrong = split.misfiled({"edid": it.edid, "record": it.record, "power_kind": it.power_kind,
                                    "enchanted": it.enchanted, "id": it.id})
            if not wrong and row["person"] in guards and it.enchanted and it.item_kind_id in ("weapon", "armour"):
                wrong = f"{it.edid} is enchanted: never a guard's routine issue"
            if wrong:
                bad.append({"holder": row["holder"], "item": row["item"], "edid": it.edid, "count": row["count"],
                            "material": it.material_id, "rule": "misfiled", "why": wrong})
                continue
        mid = getattr(it, "material_id", None) if it else None
        if mid is None or row["exception"]:
            continue
        ok, why = reach.get(mid, (False, f"{mid} is no material of ours"))
        rule = "material reach"
        if ok and mats[mid].band == "unique" and row["item"] not in uniq:
            ok, why = False, f"{mats[mid].label} enters only by story: it needs a unique_item row naming this place"
        if ok and region.get(mid, ("",))[0] == "absent":
            ok, why, rule = False, f"the region ({rid}) has none: {region[mid][1]}", "region"
        if ok and it.item_kind_id in ("weapon", "armour", "ammunition") and mats[mid].group in none_of:
            ok, rule = False, "place class"
            why = (f"a {exp['class']} place holds no {mats[mid].group} gear (scale.json mix: its expected share is "
                   f"0%): {mats[mid].label} has no place here")
        if not ok:
            bad.append({"holder": row["holder"], "item": row["item"], "edid": it.edid, "count": row["count"],
                        "material": mid, "rule": rule, "why": why})
    return bad


TYPE_OF = {v: k for k, v in split.WEAP_KINDS.items()}


def kits_for(w, person) -> list:
    """The trade kit a person takes (the first whose pattern fits their trade or whose roles hold their role) and the
    overlays their race takes."""
    kits = sorted(w.rows("trade_kit"), key=lambda k: k.ord)
    base = next((k for k in kits if not k.races and ((k.roles and person.person_role_id in k.roles.split())
                                                     or (k.match and re.search(k.match, person.trade or "", re.I)))), None)
    over = [k for k in kits if k.races and person.race_id in k.races.split()]
    return ([base] if base else []) + over


def contradictions(w, pid: str, doc: dict) -> list[dict]:
    """Every possession of a person, and every thing in a store their household or they own, that a `never` row of
    their kit names, unless the row carries an `exception`: {holder, item, edid, count, kit, rule, why}."""
    persons = {p.id: p for p in w.rows("person", place_id=pid)}
    heads = {p.household_id: p for p in persons.values() if p.household_role_id == "head"}
    items = {r.id: r for r in w.rows("item")}
    mats = {m.id: m for m in w.rows("material")}
    nevers = {}
    for n in w.rows("trade_kit_never"):
        nevers.setdefault(n.kit_id, []).append(n)
    bad = []
    for row in stock_rows(doc):
        who = persons.get(row["person"]) or heads.get(row["household"])
        it = items.get(row["item"])
        if who is None or it is None or row["exception"] or it.material_id is None:
            continue
        m = mats[it.material_id]
        slot = split.slot_of({"power_kind": it.power_kind}) if it.power_kind else None
        typ = TYPE_OF.get(it.power_kind)
        for k in kits_for(w, who):
            for n in nevers.get(k.id, []):
                conds = [(n.slot, slot), (n.types, typ), (n.materials, m.id), (n.groups, m.group), (n.bands, m.band)]
                if all(want is None or (have is not None and have in want.split()) for want, have in conds):
                    bad.append({"holder": row["holder"], "item": row["item"], "edid": it.edid, "count": row["count"],
                                "kit": k.id, "rule": f"kit {k.id}",
                                "why": f"{who.name} ({who.trade}) takes the kit '{k.label}': {n.why}"})
                    break
            else:
                continue
            break
    return bad


def place_class(w, pid: str, sc: dict | None = None) -> str:
    sc = sc or split.scale()
    kind = w.get("place", pid).place_kind_id
    return next((c for c, v in sc["mix"]["classes"].items() if kind in v["place_kinds"]), sc["mix"]["default"])


def expected_mix(w, pid: str) -> dict:
    """The place's expected share of gear by group, and why: the target of its class (province), bent by its region's
    peoples and materials, its culture and its trade (scale.json `mix.bends`), the whole brought back to 100."""
    sc = split.scale()
    p = w.get("place", pid)
    cls = place_class(w, pid, sc)
    targets = [{"groups": t["groups"], "pct": float(t["pct"])} for t in sc["mix"]["classes"][cls]["targets"]]
    trace = [f"{cls} target (province): " + ", ".join(f"{'+'.join(t['groups'])} {t['pct']:g}%" for t in targets)]
    people = {(r.people, r.share) for r in w.rows("region_people", region_id=p.region_id)}
    rmat = {(r.material_id, r.band) for r in w.rows("region_material", region_id=p.region_id)}
    makes = {g.good_id for g in w.rows("place_good", place_id=pid) if g.relation == "makes"}
    for b in sc["mix"]["bends"]:
        hit = (b["when"] == "region-people" and (b["value"], b["share"]) in people) or \
              (b["when"] == "culture" and getattr(p, "culture_id", None) == b["value"]) or \
              (b["when"] == "place-good" and b["value"] in makes) or \
              (b["when"] == "region-material" and (b["value"], b["band"]) in rmat)
        tgt = next((t for t in targets if b["group"] in t["groups"]), None)
        if hit and tgt is not None and (tgt["pct"] > 0 or cls != "tribal"):
            tgt["pct"] = max(0.0, tgt["pct"] + b["delta"])
            trace.append(f"{b['delta']:+d} {b['group']}: {b['why']} ({b['when']} {b['value']})")
    total = sum(t["pct"] for t in targets) or 1.0
    for t in targets:
        t["pct"] = round(100 * t["pct"] / total)
    return {"class": cls, "targets": targets, "trace": trace}


def mix(w, pid: str, doc: dict) -> dict:
    """The place's gear by material, group and band, against its expected mix (expected_mix) within the tolerance."""
    sc = split.scale()
    items = {r.id: r for r in w.rows("item")}
    mats = {m.id: m for m in w.rows("material")}
    by_mat, ammo, unfiled = Counter(), Counter(), Counter()
    for row in stock_rows(doc):
        it, n = items.get(row["item"]), row["count"]
        if it is None or it.item_kind_id not in ("weapon", "armour", "ammunition"):
            continue
        mid = it.material_id
        if it.item_kind_id == "ammunition":
            ammo[mid or "unfiled"] += n
        elif mid is None:
            unfiled[it.edid] += n
        else:
            by_mat[mid] += n
    total = sum(by_mat.values())
    groups, bands = Counter(), Counter()
    for mid, n in by_mat.items():
        groups[mats[mid].group] += n
        bands[mats[mid].band] += n
    exp = expected_mix(w, pid)
    tol = sc["mix"]["tolerance"]
    targets = []
    for t in exp["targets"]:
        have = sum(groups[g] for g in t["groups"])
        pct = round(100 * have / total) if total else 0
        targets.append({"groups": t["groups"], "target": t["pct"], "have": have, "pct": pct,
                        "ok": not total or abs(pct - t["pct"]) <= tol})
    return {"place": pid, "class": exp["class"], "total": total, "by_material": dict(by_mat.most_common()),
            "groups": dict(groups), "bands": dict(bands), "targets": targets, "trace": exp["trace"],
            "ammunition": dict(ammo), "unfiled": dict(unfiled)}


def worklist_md(pid: str, bad: list[dict], m: dict | None = None) -> str:
    """A place's worklist: the rows the reach and region checks fail and the kit contradictions, each with its rule,
    then its gear against its expected mix and why."""
    lines = [f"# {pid}: stock rows the material checks flag", "",
             "Generated by `python -m tools.places stock reach " + pid + " --md <this file>` (docs/design/items.md). "
             "Each row is flagged by a rule: `material reach` (the place does not reach the item's material; the "
             "reason is read from the place's record), `region` (the region marks the material absent) or `kit <id>` "
             "(the holder's trade kit would never own it). Restock each by the skill `place-stock` (section 4): "
             "replace it with what the place, the region and the holder's kit expect at the same tier and slot, "
             "drop it, or keep it with an `exception` giving the reason in words.", ""]
    if not bad:
        lines += ["No row is flagged.", ""]
    else:
        lines += ["| Holder | Item | Count | Rule | Why |", "|---|---|---|---|---|"]
        for b in bad:
            lines.append(f"| {b['holder']} | {b['edid']} ({b['item']}) | {b['count']} | {b['rule']} | {b['why']} |")
        by = Counter(b["rule"] for b in bad)
        lines += ["", f"{len(bad)} row(s) flagged: " + ", ".join(f"{k} {n}" for k, n in by.most_common()) + ".", ""]
    if m:
        lines += [f"## Gear against the expected mix (`stock mix {pid}`; within {split.scale()['mix']['tolerance']} "
                  f"points is as expected)", "", "| Material | Pieces |", "|---|---|"]
        lines += [f"| {k} | {n} |" for k, n in m["by_material"].items()]
        lines += ["", "| Groups | Now | Expected | |", "|---|---|---|---|"]
        lines += [f"| {'+'.join(t['groups'])} | {t['pct']}% | {t['target']}% | {'as expected' if t['ok'] else 'off'} |"
                  for t in m["targets"]]
        lines += ["", "Why the expected mix is what it is:", ""] + [f"- {x}" for x in m["trace"]]
        if m["ammunition"]:
            lines += ["", "Ammunition: " + ", ".join(f"{k} {v}" for k, v in m["ammunition"].items()) + "."]
        if m["unfiled"]:
            lines += ["", "Gear of no material yet (file it in item_material.json): "
                      + ", ".join(f"{k} {v}" for k, v in m["unfiled"].items()) + "."]
        lines.append("")
    return "\n".join(lines)


def flagged(w, pid: str, doc: dict) -> list[dict]:
    """Every row the reach and region checks fail, then every kit contradiction not already flagged."""
    bad = audit(w, pid, doc)
    seen = {(b["holder"], b["item"]) for b in bad}
    return bad + [c for c in contradictions(w, pid, doc) if (c["holder"], c["item"]) not in seen]


def main_reach(argv: list[str]) -> int:
    from tools.argonia_world import db
    from tools.newworld import frame
    ap = argparse.ArgumentParser(prog="stock reach")
    ap.add_argument("place")
    ap.add_argument("--source", help="a stock source to read instead of the place's own (a scratch copy)")
    ap.add_argument("--md", help="also write the flagged rows and the mix here as a worklist")
    a = ap.parse_args(argv)
    w = db.open(frame.ROOT)
    doc = load_source(a.place, Path(a.source) if a.source else None)
    bad = flagged(w, a.place, doc)
    for b in bad:
        print(f"{b['rule']}: {b['holder']}: {b['edid']} ({b['item']}) x{b['count']}: {b['why']}")
    print(f"{a.place}: {len(bad)} stock row(s) flagged")
    if a.md:
        Path(a.md).parent.mkdir(parents=True, exist_ok=True)
        Path(a.md).write_text(worklist_md(a.place, bad, mix(w, a.place, doc)), encoding="utf-8")
    return 1 if bad else 0


def main_mix(argv: list[str]) -> int:
    from tools.argonia_world import db
    from tools.newworld import frame
    ap = argparse.ArgumentParser(prog="stock mix")
    ap.add_argument("place")
    ap.add_argument("--source", help="a stock source to read instead of the place's own (a scratch copy)")
    ap.add_argument("--json", help="also write the numbers here")
    a = ap.parse_args(argv)
    w = db.open(frame.ROOT)
    m = mix(w, a.place, load_source(a.place, Path(a.source) if a.source else None))
    mats = {x.id: x for x in w.rows("material")}
    print(f"{a.place} ({m['class']}): {m['total']} pieces of gear")
    for mid, n in m["by_material"].items():
        print(f"  {mid:<16} {n:>4}  {mats[mid].group:<8} {mats[mid].band}")
    for t in m["targets"]:
        print(f"  {'+'.join(t['groups']):<16} {t['pct']:>3}% (expected {t['target']}%){'' if t['ok'] else '  OFF'}")
    for x in m["trace"]:
        print(f"    why: {x}")
    if m["ammunition"]:
        print("  ammunition: " + ", ".join(f"{k} {v}" for k, v in m["ammunition"].items()))
    if m["unfiled"]:
        print("  of no material yet: " + ", ".join(f"{k} {v}" for k, v in m["unfiled"].items()))
    if a.json:
        Path(a.json).write_text(json.dumps(m, indent=1) + "\n")
    return 0
