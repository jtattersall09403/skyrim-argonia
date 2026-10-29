#!/usr/bin/env python3
"""The quest record's authoring view (quest-write/quest-record.md): YAML in, rows out, and back (decision 0030 §5).

A quest record is rows: `quest` and its `quest_*` child tables, its facts in `fact` (`quest_id`), its conditions and
action lists in `condition*` and `action*`. A writer edits the YAML view; `import` turns it into rows through db.py
(every key, type, lookup and named check enforced; nothing written while one fails); `export` rebuilds the YAML
from the rows. `quest_view.json` maps each YAML path to its table and column; it was emitted once by the 0030
migrator from the same tree that moved the two records in, and is the view's definition from then on.

    python3 -m tools.argonia_world.quest_record export quest.local.lh38 [-o lh38.yaml]
    python3 -m tools.argonia_world.quest_record import lh38.yaml [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

import yaml

from tools.argonia_world import db, records

VIEW = json.loads((Path(__file__).with_name("quest_view.json")).read_text(encoding="utf-8"))
FACT_KEYS = {"id": "id", "claim": "claim", "from": "from_ref", "says": "says"}   # a record fact's keys -> fact


def _tables(node=VIEW):
    yield node
    for ch in node["children"]:
        yield from _tables(ch["node"])


# -- rows -> the YAML view -------------------------------------------------------------------------------------
def _setp(obj, rel, v):
    d = obj
    for k in rel[:-1]:
        d = d.setdefault(k, {})
    d[rel[-1]] = v


_num = records.num


def _cond(w, cid):
    return records.condition(w, cid, collapse=True)


def _acts(w, aid):
    return records.actions(w, aid, collapse=True)


def _ordered(obj, order):
    if not isinstance(obj, dict):
        return obj
    keys = [k for k in order if k in obj] + [k for k in obj if k not in order]
    return {k: obj[k] for k in keys}


def _rebuild(w, node, where: dict, path: str):
    t = w.table(node["table"])
    sql = f'SELECT * FROM "{t.name}" WHERE ' + " AND ".join(f'"{k}" = ?' for k in where)
    sql += " ORDER BY " + ", ".join(f'"{k}"' for k in t.pk)
    bools = {c.name for c in t.columns if c.type == "BOOLEAN"}
    out = []
    for r in w.query(sql, *where.values()):
        r = {k: (bool(r[k]) if k in bools and r[k] is not None else r[k]) for k in r.keys()}
        obj = {}
        for c, rel in node["fields"]:
            if r.get(c) is None:
                continue
            if rel == ["<value>"]:
                obj = _num(r[c])
            else:
                _setp(obj, rel, _num(r[c]))
        for c, rel in node["conds"]:
            if r.get(c) is not None:
                _setp(obj, rel, _cond(w, r[c]))
        for c, rel in node["acts"]:
            if r.get(c) is not None:
                _setp(obj, rel, _acts(w, r[c]))
        key = [r[k] for k in t.pk]
        for ch in node["children"]:
            sub = ch["node"]
            kids = _rebuild(w, sub, dict(zip(sub["parent_cols"], key)), path + "." + ".".join(ch["rel"]))
            if not kids:
                continue
            if ch["mode"] == "map":
                val = {kr[ch["key"]]: o for kr, o in kids}
            else:
                val = [o for kr, o in kids]
            if ch["rel"] == ["<list>"]:
                obj = val
            else:
                _setp(obj, ch["rel"], val)
        if isinstance(obj, dict):
            obj = _ordered(obj, node["order"])
            for k, v in list(obj.items()):
                sub_order = VIEW["inline_order"].get(f"{path}.{k}")
                if isinstance(v, dict) and sub_order:
                    obj[k] = _ordered(v, sub_order)
        out.append((r, obj))
    return out


def export(w: db.World, quest_id: str) -> dict:
    """The quest's record as its YAML view (a dict), or KeyError when there is no such quest."""
    got = _rebuild(w, VIEW, {"id": quest_id}, "")
    if not got:
        raise KeyError(f"no quest {quest_id!r}")
    q = got[0][1]
    facts = [{y: r[c] for y, c in FACT_KEYS.items() if r[c] is not None}
             for r in w.query("SELECT * FROM fact WHERE quest_id = ? ORDER BY ord, id", quest_id)]
    if facts:
        q["facts"] = facts
    return _ordered(q, VIEW["order"])


def dump(q: dict) -> str:
    head = (f"# {q.get('code', '')} {q.get('title', '')}: the quest record's YAML view, exported from the world database\n"
            f"# (python3 -m tools.argonia_world.quest_record export {q['id']}). Edit and import it; the rows are the source.\n")
    return head + yaml.safe_dump(q, sort_keys=False, allow_unicode=True, width=116, default_flow_style=None)


# -- the YAML view -> rows -------------------------------------------------------------------------------------
def legacy_repair(text: str) -> str:
    """Repairs of the two hand-written records' flow-mapping values the YAML parser split at their commas (each
    meant one string). An exported view quotes such values, so the repairs touch only the hand-written form."""
    text = re.sub(r"when: ((?:\d+|about sixty|the last three|a year|this|every|from)[^:{}\[\]]*?), (late evening|"
                  r"night|dawn), who:", r'when: "\1, \2", who:', text)
    return text.replace("setting: before witnesses (a council, a hearing, a household)",
                        'setting: "before witnesses (a council, a hearing, a household)"')


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(legacy_repair(Path(path).read_text(encoding="utf-8")))


def _getp(obj, rel):
    d = obj
    for k in rel:
        if not isinstance(d, dict) or k not in d:
            return None
        d = d[k]
    return d


def _covered(node):
    rels = [tuple(r) for _, r in node["fields"] + node["conds"] + node["acts"]]
    return set(rels) | {tuple(ch["rel"]) for ch in node["children"]}


def _unknown(obj, node, path, extra=()):
    """Every key of obj the view does not hold (it would be dropped silently)."""
    cov = _covered(node) | {(k,) for k in extra}
    out = []

    def walk(d, pre):
        for k, v in d.items():
            p = pre + (k,)
            if p in cov:
                continue
            if isinstance(v, dict) and any(c[:len(p)] == p for c in cov):
                walk(v, p)
            else:
                out.append(f"{path}.{'.'.join(p)}: not a field of the quest record (quest_view.json)")
    if isinstance(obj, dict):
        walk(obj, ())
    return out


class Rows:
    def __init__(self):
        self.rows: dict[str, list[dict]] = {}
        self.conds, self.cargs, self.lists, self.acts, self.aargs = [], [], [], [], []
        self.errors: list[str] = []

    def add(self, table, row):
        self.rows.setdefault(table, []).append(row)

    def cond(self, v, cid, parent=None, ord_=None):
        if isinstance(v, list):
            term, kids, args = "all", v, []
        elif isinstance(v, dict) and len(v) == 1:
            k, a = next(iter(v.items()))
            if k in ("all", "any"):
                term, kids, args = k, a, []
            elif k == "not":
                term, kids, args = "not", [a], []
            else:
                term, kids, args = k, [], (a if isinstance(a, list) else [a])
        elif isinstance(v, dict):
            term, kids, args = "all", [{k: a} for k, a in v.items()], []
        else:
            self.errors.append(f"condition {cid}: {v!r} is not a condition")
            return
        self.conds.append({"id": cid, "parent_id": parent, "ord": ord_, "term": term})
        for i, a in enumerate(args):
            self.cargs.append({"condition_id": cid, "ord": i,
                               "value": json.dumps(a, sort_keys=True) if isinstance(a, (dict, list)) else a})
        for i, kid in enumerate(kids):
            self.cond(kid, f"{cid}.{i}", cid, i)

    def actlist(self, v, aid):
        self.lists.append({"id": aid})
        for i, a in enumerate([v] if isinstance(v, dict) else v):
            if not isinstance(a, dict) or len(a) != 1:
                self.errors.append(f"action list {aid}: {a!r} is not one action")
                continue
            verb, args = next(iter(a.items()))
            self.acts.append({"list_id": aid, "ord": i, "term": verb})
            for j, x in enumerate(args if isinstance(args, list) else [args]):
                self.aargs.append({"list_id": aid, "ord": i, "arg_ord": j, "value": x})


def _flatten(out: Rows, node, obj, key: dict, path: str):
    t = node["table"]
    row = dict(key)
    pk_vals = "|".join(str(v) for v in key.values())
    if not isinstance(obj, dict):
        if isinstance(obj, list):     # a list element that is itself a list: its "<list>" child holds it
            ch = next(c for c in node["children"] if c["rel"] == ["<list>"])
            obj_children = [(ch, obj)]
            obj = {}
        else:
            row["value"] = obj
            out.add(t, row)
            return
    else:
        obj_children = []
        out.errors += _unknown(obj, node, path, extra=("facts",) if t == "quest" else ())
    poly = {tuple(ch["rel"]) for ch in node["children"]}   # a field that may also be a list (stage directions)
    for c, rel in node["fields"]:
        v = _getp(obj, rel)
        if isinstance(v, (dict, list)):
            if tuple(rel) not in poly:
                out.errors.append(f"{path}.{'.'.join(rel)}: one value is expected, not a {type(v).__name__}")
        elif v is not None:
            row[c] = v
    for c, rel in node["conds"]:
        v = _getp(obj, rel)
        if v not in (None, [], {}):
            row[c] = f"{t}:{pk_vals}:{c}"
            out.cond(v, row[c])
    for c, rel in node["acts"]:
        v = _getp(obj, rel)
        if v:
            row[c] = f"{t}:{pk_vals}:{c}"
            out.actlist(v, row[c])
    out.add(t, row)
    kv = list(key.values())
    for ch in node["children"]:
        v = obj_children[0][1] if obj_children and obj_children[0][0] is ch else _getp(obj, ch["rel"])
        if v is None or (ch["rel"] != ["<list>"] and not isinstance(v, (list, dict))):
            continue
        sub = ch["node"]
        ck = dict(zip(sub["parent_cols"], kv))
        if ch["mode"] == "map":
            if not isinstance(v, dict):
                out.errors.append(f"{path}.{'.'.join(ch['rel'])}: a map is expected")
                continue
            for k, e in v.items():
                _flatten(out, sub, e, {**ck, ch["key"]: k}, f"{path}.{'.'.join(ch['rel'])}.{k}")
        else:
            if not isinstance(v, list):
                continue      # a scalar at a poly path (stage `directions` as one string) is the field above
            for i, e in enumerate(v):
                _flatten(out, sub, e, {**ck, "ord": i}, f"{path}.{'.'.join(ch['rel'])}[{i}]")


def to_rows(q: dict) -> Rows:
    out = Rows()
    if not isinstance(q, dict) or not q.get("id"):
        out.errors.append("the record has no id")
        return out
    _flatten(out, VIEW, {k: v for k, v in q.items() if k != "facts"}, {"id": q["id"]}, q["id"])
    for i, f in enumerate(q.get("facts") or []):
        if not isinstance(f, dict):
            out.errors.append(f"facts[{i}]: {f!r} is not a fact")
            continue
        bad = set(f) - set(FACT_KEYS)
        if bad:
            out.errors.append(f"facts[{i}]: unknown key(s) {sorted(bad)}")
        out.add("fact", {**{FACT_KEYS[k]: v for k, v in f.items() if k in FACT_KEYS}, "quest_id": q["id"], "ord": i})
    return out


def _owned(w, qid):
    """The quest's current conditions and action lists: those named by its rows' condition and action columns."""
    conds, lists = set(), set()
    for node in _tables():
        t = node["table"]
        kc = "id" if t == "quest" else "quest_id"
        for c, _ in node["conds"]:
            conds |= set(w.values(f'SELECT "{c}" FROM "{t}" WHERE "{kc}" = ? AND "{c}" IS NOT NULL', qid))
        for c, _ in node["acts"]:
            lists |= set(w.values(f'SELECT "{c}" FROM "{t}" WHERE "{kc}" = ? AND "{c}" IS NOT NULL', qid))
    return conds, lists


def import_record(w: db.World, q: dict) -> list[str]:
    """Replace the quest's record rows with the YAML view's. Returns the errors (nothing changed when any); the
    caller saves. The quest row's registry columns (packet, registry status and note) are kept."""
    out = to_rows(q)
    if out.errors:
        return out.errors
    qid = q["id"]
    w._begin()
    w.con.execute("SAVEPOINT import_record")
    try:
        _replace(w, qid, out)
    except (ValueError, KeyError, sqlite3.IntegrityError) as e:
        # a value of the wrong type, a NOT NULL, CHECK or duplicate key: the quest's old rows come back
        w.con.execute("ROLLBACK TO import_record")
        w.con.execute("RELEASE import_record")
        return [f"{qid}: {e.args[0] if e.args else e}"]
    w.con.execute("RELEASE import_record")
    return []


def _replace(w: db.World, qid: str, out: Rows) -> None:
    existing = w.get("quest", qid)
    conds, lists = _owned(w, qid)
    for node in reversed(list(_tables())[1:]):
        w.delete(node["table"], quest_id=qid)
    for cid in conds:
        w.delete("condition", cid)
    for aid in lists:
        w.delete("action_list", aid)
    w.delete("fact", quest_id=qid)
    qrow = out.rows.pop("quest")[0]
    if existing is None:
        w.insert("quest", qrow)
    else:
        view_cols = {c for c, _ in VIEW["fields"] + VIEW["conds"] + VIEW["acts"]}
        w.update("quest", qid, **{c: qrow.get(c) for c in view_cols if c != "id"})
    w.insert_many("condition", sorted(out.conds, key=lambda r: r["id"].count(".")))
    w.insert_many("condition_arg", out.cargs)
    w.insert_many("action_list", out.lists)
    w.insert_many("action", out.acts)
    w.insert_many("action_arg", out.aargs)
    for t, rows in out.rows.items():
        w.insert_many(t, rows)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("export")
    e.add_argument("quest_id")
    e.add_argument("-o", "--out")
    i = sub.add_parser("import")
    i.add_argument("path")
    i.add_argument("--dry-run", action="store_true", help="check the record against the world; write nothing")
    a = ap.parse_args(argv)
    w = db.open()
    if a.cmd == "export":
        try:
            text = dump(export(w, a.quest_id))
        except KeyError as err:
            print(err.args[0])
            return 1
        if a.out:
            Path(a.out).write_text(text, encoding="utf-8")
            print(f"wrote {a.out}")
        else:
            sys.stdout.write(text)
        return 0
    q = load_yaml(Path(a.path))
    errs = import_record(w, q)
    if not errs:
        errs = w.errors()
    if errs:
        print(f"{a.path}: not imported, {len(errs)} error(s):\n  " + "\n  ".join(errs))
        return 1
    if a.dry_run:
        print(f"{q['id']}: imports cleanly (dry run, nothing written)")
        return 0
    written = w.save()
    print(f"{q['id']}: imported; wrote {len(written)} table(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
