"""One-off normaliser for decision 0030's migration: nested JSON families -> 3NF tables -> schema.sql + JSONL.

Kept in git history only (deleted after the migration). Each family is a Spec; the engine decides per path how a
nested value becomes relational (column, inline prefix, 1:1 sub-table, map table, list table, tuple columns,
condition tree, action list), infers types, NOT NULL, foreign keys and lookups from the spec, emits the DDL, and can
rebuild every source object from the loaded tables to prove the migration lossless.
"""
from __future__ import annotations

import collections
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

SCALARS = (str, int, float, bool)
MAP = "{*}"


def snake(s: str) -> str:
    s = re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", s)
    s = re.sub(r"[^0-9a-zA-Z]+", "_", s).lower().strip("_")
    return s or "x"


def tname(t):
    return type(t).__name__


@dataclass
class Spec:
    family: str                      # the entity table's name
    comment: str
    items: list                      # [(context dict, entity dict)] built by the family loader
    pk: list = field(default_factory=lambda: ["id"])
    maps: dict = field(default_factory=dict)       # path -> key column name
    subs: set = field(default_factory=set)         # dict paths forced to a 1:1 table
    inline: set = field(default_factory=set)       # dict paths forced inline
    lists: set = field(default_factory=set)        # numeric list paths forced to a list table (not a tuple)
    drop: dict = field(default_factory=dict)       # path -> why
    rename: dict = field(default_factory=dict)     # path -> column name
    tables: dict = field(default_factory=dict)     # path -> child table name
    entity: dict = field(default_factory=dict)     # list path -> key field of each element (its own PK)
    fk: dict = field(default_factory=dict)         # path -> table (or "table.col")
    lookup: dict = field(default_factory=dict)     # path -> lookup table
    check: dict = field(default_factory=dict)      # path -> SQL with {c}
    cond: set = field(default_factory=set)         # condition paths
    actions: set = field(default_factory=set)      # action-list paths
    comments: dict = field(default_factory=dict)   # child table name -> comment
    merge: dict = field(default_factory=dict)      # list path -> (table, kind value)
    split: dict = field(default_factory=dict)      # list path -> (discriminator field, {value: table}, default table)
    notnull_off: set = field(default_factory=set)
    unique: list = field(default_factory=list)     # extra UNIQUE column groups on the entity table


@dataclass
class Col:
    name: str
    path: str
    types: collections.Counter = field(default_factory=collections.Counter)
    nulls: int = 0
    fk: str | None = None
    lookup: str | None = None
    check: str | None = None
    notnull: bool | None = None
    declared: str | None = None


@dataclass
class TDef:
    name: str
    comment: str
    pk: list
    cols: dict = field(default_factory=dict)       # name -> Col (key columns first)
    rows: list = field(default_factory=list)
    parent: "TDef | None" = None
    parent_cols: list = field(default_factory=list)   # this table's columns that key the parent
    fields: list = field(default_factory=list)     # (col, relpath tuple) scalar fields
    tuples: list = field(default_factory=list)     # ([cols], relpath)
    children: list = field(default_factory=list)   # (TDef, relpath, mode, extra)
    conds: list = field(default_factory=list)      # (col, relpath)
    acts: list = field(default_factory=list)       # (col, relpath)
    short: str = ""
    entity: str = ""
    unique: list = field(default_factory=list)
    family: str = ""
    discriminator: tuple | None = None             # (col, value) for merged tables

    def col(self, name, path=""):
        if name not in self.cols:
            self.cols[name] = Col(name, path)
        return self.cols[name]


class Engine:
    def __init__(self):
        self.tables: dict[str, TDef] = {}
        self.lookups: dict[str, dict] = collections.OrderedDict()   # name -> {value: about}
        self.lookup_comments: dict[str, str] = {}
        self.report: list[str] = []
        self.cond_rows: list[dict] = []
        self.cond_args: list[dict] = []
        self.act_lists: list[dict] = []
        self.act_rows: list[dict] = []
        self.act_args: list[dict] = []
        self.terms_used: collections.Counter = collections.Counter()
        self.specs: list[Spec] = []

    # -- stats ---------------------------------------------------------------------------------------------
    def stats(self, spec: Spec):
        st = collections.defaultdict(lambda: {"types": collections.Counter(), "keys": collections.Counter(),
                                              "lens": collections.Counter(), "elems": collections.Counter(),
                                              "n": 0})

        def walk(x, p):
            s = st[p]
            s["n"] += 1
            s["types"][tname(x)] += 1
            if p in spec.cond or p in spec.actions or p in spec.drop:
                return
            if isinstance(x, dict):
                m = p in spec.maps
                for k, v in x.items():
                    s["keys"][k] += 1
                    walk(v, f"{p}{MAP}" if m else (f"{p}.{k}" if p else k))
            elif isinstance(x, list):
                s["lens"][len(x)] += 1
                for v in x:
                    s["elems"][tname(v)] += 1
                    walk(v, p + "[]")
        for _, obj in spec.items:
            walk(obj, "")
        return st

    def mode(self, spec, st, p):
        s = st[p]
        types = {t for t in s["types"] if t != "NoneType"}
        if p in spec.cond:
            return "cond"
        if p in spec.actions:
            return "actions"
        if p in spec.split:
            return "split"
        if p in spec.merge:
            return "merge"
        if not types:
            return "null"
        if types <= {"str", "int", "float", "bool"}:
            return "scalar"
        if types == {"dict"}:
            if p in spec.maps:
                return "map"
            if p in spec.subs:
                return "sub"
            if p in spec.inline:
                return "inline"
            keys = s["keys"]
            nd = s["types"]["dict"]
            if len(keys) > 12 and sum(1 for c in keys.values() if c >= 0.5 * nd) < 0.3 * len(keys):
                self.note(f"{spec.family}: {p} looks like a map ({len(keys)} keys); add to maps")
            parent = p.rsplit(".", 1)[0] if "." in p else ""
            pn = st[parent]["types"]["dict"] if parent in st else nd
            if nd < 0.5 * max(pn, 1) and len(keys) >= 3:
                return "sub"
            return "inline"
        if types == {"list"}:
            el = set(s["elems"])
            if p not in spec.lists and el and el <= {"int", "float"} and len(s["lens"]) == 1 \
                    and next(iter(s["lens"])) in (2, 3):
                return "tuple"
            return "list"
        if types <= {"str", "int", "float", "bool", "dict"}:
            return "poly"
        if types == {"dict", "list"} or types <= {"str", "int", "float", "bool", "list"}:
            self.note(f"{spec.family}: {p} is a {'/'.join(sorted(types))}: lists go to a table, the rest "
                               f"to columns")
            return "dictlist"
        raise ValueError(f"{spec.family}: {p} has types {sorted(types)}; add a rule")

    # -- emission ------------------------------------------------------------------------------------------
    def table(self, name, comment, pk, parent=None, parent_cols=(), family=""):
        if name in self.tables:
            return self.tables[name]
        t = TDef(name, comment, list(pk), parent=parent, parent_cols=list(parent_cols), family=family)
        for k in pk:
            t.col(k, "<key>")
        self.tables[name] = t
        return t

    @staticmethod
    def child_key(t: TDef, key: dict) -> dict:
        out = {}
        for k, v in key.items():
            if k == "id":
                out[f"{t.entity or t.name}_id"] = v
            elif k == "ord" or k == "key":
                out[f"{t.short}_{k}"] = v
            else:
                out[k] = v
        return out

    def run(self, spec: Spec):
        self.specs.append(spec)
        st = self.stats(spec)
        self._st, self._spec = st, spec
        t = self.table(spec.family, spec.comment, spec.pk, family=spec.family)
        t.short, t.entity, t.unique = spec.family, spec.family, spec.unique
        for ctx, obj in spec.items:
            row = dict(ctx)
            for k in spec.pk:
                if k not in row:
                    row[k] = obj.get(k)
            self.flat(t, row, obj, "", "", {k: row[k] for k in spec.pk}, (), skip=set(spec.pk) - set(ctx))
            t.rows.append(row)
            for k, v in ctx.items():
                if k not in spec.pk:
                    t.col(k, "<context>")

    def flat(self, t, row, obj, path, cp, key, rel, skip=()):
        spec, st = self._spec, self._st
        for k, v in obj.items():
            if not path and k in skip:
                if not any(f[0] == k for f in t.fields):
                    t.fields.append((k, rel + (k,)))
                continue
            p = f"{path}.{k}" if path else k
            if path.endswith(MAP) or path.endswith("[]"):
                p = f"{path}.{k}"
            if p in spec.drop:
                continue
            m = self.mode(spec, st, p)
            c = spec.rename.get(p) or (cp + snake(k))
            r2 = rel + (k,)
            if m == "null":
                self.note_drop(spec, p, "always null")
                continue
            if m == "scalar":
                self.put(t, row, c, v, p, r2)
            elif m == "inline":
                self.reg(t.fields, None)
                if not any(x[1] == r2 and x[2] == "inline" for x in t.children):
                    pass
                if v is not None:
                    self.flat(t, row, v, p, c + "_", key, r2)
            elif m == "poly":
                if isinstance(v, dict):
                    self.flat(t, row, v, p, c + "_", key, r2)
                else:
                    self.put(t, row, c, v, p, r2)
            elif m == "dictlist":
                if isinstance(v, list):
                    ch = self.child(t, p, cp + snake(k), key, "list", r2)
                    ck = self.child_key(t, key)
                    for i, e in enumerate(v):
                        k2 = {**ck, "ord": i}
                        self.elem(ch, dict(k2), e, p + "[]", k2)
                elif isinstance(v, dict):
                    self.flat(t, row, v, p, c + "_", key, r2)
                elif v is not None:
                    self.put(t, row, c, v, p, r2)
            elif m == "tuple":
                cols = [f"{c}_{a}" for a in "xyz"[: next(iter(st[p]["lens"]))]]
                if not any(x[1] == r2 for x in t.tuples):
                    t.tuples.append((cols, r2))
                for i, cc in enumerate(cols):
                    col = t.col(cc, p)
                    val = v[i] if v is not None else None
                    col.types[tname(val)] += 1
                    if val is None:
                        col.nulls += 1
                    row[cc] = val
            elif m == "sub":
                ch = self.child(t, p, cp + snake(k), key, "sub", r2)
                if v is not None:
                    ck = self.child_key(t, key)
                    self.elem(ch, dict(ck), v, p, ck)
            elif m == "map":
                kc = spec.maps[p]
                ch = self.child(t, p, cp + snake(k), key, "map", r2, extra=kc)
                if p + "{key}" in spec.fk:
                    ch.col(kc).fk = spec.fk[p + "{key}"]
                if p + "{key}" in spec.lookup:
                    ch.col(kc).lookup = spec.lookup[p + "{key}"]
                ck = self.child_key(t, key)
                for kk, vv in (v or {}).items():
                    k2 = {**ck, kc: kk}
                    self.elem(ch, dict(k2), vv, p + MAP, k2)
            elif m == "list":
                if p in spec.entity:
                    idf = spec.entity[p]
                    ch = self.child(t, p, cp + snake(k), key, "entity", r2, extra=idf)
                    ck = self.child_key(t, key)
                    for i, e in enumerate(v or []):
                        k2 = {idf: e[idf]}
                        r = {**k2, **ck, "ord": i}
                        self.elem(ch, r, {kk: vv for kk, vv in e.items() if kk != idf}, p + "[]", k2)
                else:
                    ch = self.child(t, p, cp + snake(k), key, "list", r2)
                    ck = self.child_key(t, key)
                    for i, e in enumerate(v or []):
                        k2 = {**ck, "ord": i}
                        self.elem(ch, dict(k2), e, p + "[]", k2)
            elif m == "merge":
                tbl, kind = spec.merge[p]
                ch = self.child(t, p, cp + snake(k), key, "merge", r2, extra=kind, name=tbl)
                ck = self.child_key(t, key)
                for i, e in enumerate(v or []):
                    k2 = {**ck, "kind": kind, "ord": i}
                    self.elem(ch, dict(k2), e, p + "[]", k2)
            elif m == "split":
                fld, by, default = spec.split[p]
                ck = self.child_key(t, key)
                for i, e in enumerate(v or []):
                    tbl = by.get(e.get(fld), default)
                    ch = self.child(t, p, cp + snake(k), key, "split", r2, extra=(fld, e.get(fld) if tbl != default else None),
                                    name=tbl)
                    k2 = {**ck, "ord": i}
                    self.elem(ch, dict(k2), e, p + "[]", k2)
            elif m == "cond":
                cid = None
                if v is not None and v != [] and v != {}:
                    cid = f"{t.name}:{'|'.join(str(x) for x in key.values())}:{c}"
                    self.cond(v, cid, None, 0)
                self.put(t, row, c, cid, p, r2, kind="cond")
                t.col(c).fk = "condition"
            elif m == "actions":
                aid = None
                if v:
                    aid = f"{t.name}:{'|'.join(str(x) for x in key.values())}:{c}"
                    self.actlist(v, aid)
                self.put(t, row, c, aid, p, r2, kind="actions")
                t.col(c).fk = "action_list"

    def note(self, msg):
        if msg not in self.report:
            self.report.append(msg)

    def reg(self, *a):
        pass

    def note_drop(self, spec, p, why):
        msg = f"{spec.family}: dropped {p} ({why})"
        if msg not in self.report:
            self.report.append(msg)

    def put(self, t, row, c, v, p, rel, kind="field"):
        if c in t.cols and t.cols[c].path == "<key>" and p != "<key>":
            c2 = f"{c}_ref"
            msg = f"{t.name}: {p} renamed {c2} (its name is a key column); add a rename"
            if msg not in self.report:
                self.report.append(msg)
            c = c2
        if c in row and row[c] is not None and v is not None and t.cols.get(c) and t.cols[c].path != p:
            raise ValueError(f"{t.name}: column {c} from {p} collides with {t.cols[c].path}")
        col = t.col(c, p)
        if col.path in ("", None):
            col.path = p
        spec = self._spec
        if p in spec.fk:
            col.fk = spec.fk[p]
        if p in spec.lookup:
            col.lookup = spec.lookup[p]
        if p in spec.check:
            col.check = spec.check[p]
        if p in spec.notnull_off:
            col.notnull = False
        col.types[tname(v)] += 1
        if v is None:
            col.nulls += 1
        row[c] = v
        lst = {"field": t.fields, "cond": t.conds, "actions": t.acts}[kind]
        if not any(x[0] == c for x in lst):
            lst.append((c, rel))

    def child(self, t, p, k, key, mode, rel, extra=None, name=None):
        spec = self._spec
        name = name or spec.tables.get(p) or f"{t.name}_{snake(k)}"
        ck = list(self.child_key(t, key))
        if mode == "sub":
            pk = ck
        elif mode == "map":
            pk = ck + [extra]
        elif mode == "entity":
            pk = [extra]
        elif mode == "merge":
            pk = ck + ["kind", "ord"]
        else:
            pk = ck + ["ord"]
        com = spec.comments.get(name) or self.auto_comment(t, p, mode)
        ch = self.table(name, com, pk, parent=t, parent_cols=ck, family=spec.family)
        if mode == "entity":
            for c in ck + ["ord"]:
                ch.col(c, "<key>")
        ch.short = spec.rename.get(p) or snake(k)
        ch.entity = ch.entity or (name if mode == "entity" else "")
        ex = extra if mode not in ("split",) else extra
        if not any(x[0] is ch and x[1] == rel and (mode != "split" or x[3] == ex) for x in t.children):
            t.children.append((ch, rel, mode, ex))
        if mode == "merge":
            ch.discriminator = ("kind", None)
        return ch

    @staticmethod
    def auto_comment(t, p, mode):
        what = {"sub": "the optional block", "map": "one row per key of", "list": "one row per element of",
                "entity": "one row per element of", "merge": "one row per element of", "split": "the elements of"}[mode]
        return f"Home of {what} `{p}` of each {t.name} row (ordered by `ord` where it has one)."

    def elem(self, ch, row, e, path, key):
        if isinstance(e, dict):
            self.flat(ch, row, e, path, "", key, ())
        elif isinstance(e, list):
            if e and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in e) and len(e) in (2, 3):
                cols = [f"{a}" for a in "xyz"[: len(e)]]
                if not any(x[1] == () for x in ch.tuples):
                    ch.tuples.append((["x", "y", "z"][: len(e)], ()))
                for i, cc in enumerate(cols):
                    col = ch.col(cc, path)
                    col.types[tname(e[i])] += 1
                    row[cc] = e[i]
            else:
                sub = self.child(ch, path, "items", key, "list", ("<list>",))
                ck = self.child_key(ch, key)
                for i, x in enumerate(e):
                    k2 = {**ck, "ord": i}
                    self.elem(sub, dict(k2), x, path + "[]", k2)
        else:
            self.put(ch, row, "value", e, path, ("<value>",))
        ch.rows.append(row)

    # -- conditions and actions ----------------------------------------------------------------------------
    def cond(self, v, cid, parent, ord_):
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
            raise ValueError(f"condition {cid}: {v!r}")
        self.terms_used[term] += 1
        self.cond_rows.append({"id": cid, "parent_id": parent, "ord": ord_ if parent else None, "term": term})
        for i, a in enumerate(args):
            if isinstance(a, (dict, list)):
                a = json.dumps(a, sort_keys=True)
                self.report.append(f"condition {cid}: structured argument stored as JSON text")
            self.cond_args.append({"condition_id": cid, "ord": i, "value": a})
        for i, kid in enumerate(kids):
            self.cond(kid, f"{cid}.{i}", cid, i)

    def actlist(self, v, aid):
        self.act_lists.append({"id": aid})
        if isinstance(v, dict):
            v = [v]
        for i, a in enumerate(v):
            if not isinstance(a, dict) or len(a) != 1:
                raise ValueError(f"action list {aid}: {a!r}")
            verb, args = next(iter(a.items()))
            self.terms_used[verb] += 1
            self.act_rows.append({"list_id": aid, "ord": i, "term": verb})
            for j, x in enumerate(args if isinstance(args, list) else [args]):
                self.act_args.append({"list_id": aid, "ord": i, "arg_ord": j, "value": x})

    # -- types, DDL ----------------------------------------------------------------------------------------
    @staticmethod
    def sqltype(col: Col):
        if col.declared:
            return col.declared
        ts = {t for t in col.types if t != "NoneType"}
        if col.path == "<key>" and not ts:
            return "TEXT"
        if not ts:
            return "TEXT"
        if ts == {"bool"}:
            return "BOOLEAN"
        if ts == {"int"}:
            return "INTEGER"
        if ts <= {"int", "float"}:
            return "REAL"
        if ts == {"str"}:
            return "TEXT"
        return ""

    def finalise(self):
        for t in self.tables.values():
            for k in t.pk:
                col = t.cols[k]
                for r in t.rows:
                    col.types[tname(r.get(k))] += 1
                if k.endswith("ord"):
                    col.declared = "INTEGER"
            n = len(t.rows)
            for c in t.cols.values():
                present = sum(1 for r in t.rows if r.get(c.name) is not None)
                if c.notnull is None:
                    c.notnull = (present == n and n > 0)
                if c.name in t.pk:
                    c.notnull = True
        for t in self.tables.values():
            for c in t.cols.values():
                if c.lookup:
                    lk = self.lookups.setdefault(c.lookup, {})
                    for r in t.rows:
                        if r.get(c.name) is not None:
                            lk.setdefault(r[c.name], None)

    def ddl(self, t: TDef, known=None) -> str:
        lines = []
        for c in t.cols.values():
            typ = self.sqltype(c)
            s = f'  "{c.name}"' + (f" {typ}" if typ else "")
            if c.notnull:
                s += " NOT NULL"
            if typ == "BOOLEAN":
                s += f' CHECK ("{c.name}" IN (0, 1))'
            if c.check:
                s += f" CHECK ({c.check.format(c=chr(34) + c.name + chr(34))})"
            ref = c.lookup or c.fk
            if ref and known is not None and ref.partition(".")[0] not in known:
                msg = f"FK pending: {t.name}.{c.name} -> {ref} (table not migrated)"
                if msg not in self.report:
                    self.report.append(msg)
                ref = None
            if ref:
                tbl, _, rc = ref.partition(".")
                s += f' REFERENCES "{tbl}"("{rc or "id"}")'
            lines.append(s)
        lines.append(f'  PRIMARY KEY ({", ".join(chr(34) + k + chr(34) for k in t.pk)})')
        if t.parent is not None:
            pk = t.parent.pk
            lines.append(f'  FOREIGN KEY ({", ".join(chr(34) + k + chr(34) for k in t.parent_cols)}) '
                         f'REFERENCES "{t.parent.name}" ({", ".join(chr(34) + k + chr(34) for k in pk)}) '
                         f'ON DELETE CASCADE')
        for u in t.unique:
            lines.append(f'  UNIQUE ({", ".join(chr(34) + k + chr(34) for k in u)})')
        com = "\n".join("-- " + x for x in wrap(t.comment))
        return f'{com}\nCREATE TABLE "{t.name}" (\n' + ",\n".join(lines) + "\n);\n"


def wrap(text, width=116):
    out, line = [], ""
    for w in text.split():
        if len(line) + len(w) + 1 > width:
            out.append(line)
            line = w
        else:
            line = f"{line} {w}".strip()
    if line:
        out.append(line)
    return out


# -- rebuilding the source from the loaded world (the lossless proof) ----------------------------------------------
def setp(obj, rel, v):
    d = obj
    for k in rel[:-1]:
        d = d.setdefault(k, {})
    d[rel[-1]] = v


def rebuild(eng: Engine, w, t: TDef, where: dict | None = None):
    """Rows of t (optionally filtered by parent key) back to nested objects, keyed by t's pk tuple."""
    out = collections.OrderedDict()
    cols = list(t.cols)
    sql = f'SELECT {", ".join(chr(34) + c + chr(34) for c in cols)} FROM "{t.name}"'
    rows = [dict(zip(cols, r)) for r in w.con.execute(sql)]
    tm = {c: eng.sqltype(t.cols[c]) for c in cols}
    for r in rows:
        for c in cols:
            if tm[c] == "BOOLEAN" and r[c] is not None:
                r[c] = bool(r[c])
    kids = {}
    for ch, rel, mode, extra in t.children:
        if ch.name not in kids:
            kids[ch.name] = rebuild_grouped(eng, w, ch)
    res = []
    for r in rows:
        obj = {}
        for c, rel in t.fields:
            if rel and rel[0] == "<value>":
                if r.get(c) is not None:
                    obj = r[c]
                continue
            if r.get(c) is not None:
                setp(obj, rel, r[c])
        for cols_, rel in t.tuples:
            vals = [r.get(c) for c in cols_]
            if any(v is not None for v in vals):
                if rel == ():
                    obj = vals
                else:
                    setp(obj, rel, vals)
        for c, rel in t.conds:
            if r.get(c) is not None:
                setp(obj, rel, cond_tree(w, r[c]))
        for c, rel in t.acts:
            if r.get(c) is not None:
                setp(obj, rel, act_list(w, r[c]))
        pkey = tuple(r[k] for k in t.pk)
        splits = {}
        for ch, rel, mode, extra in t.children:
            grp = kids[ch.name].get(tuple(r[k] for k in t.pk), [])
            if mode == "sub":
                if grp:
                    setp(obj, rel, grp[0][1])
            elif mode == "map":
                if grp:
                    setp(obj, rel, {cr[extra]: o for cr, o in grp})
            elif mode == "merge":
                vals = [o for cr, o in sorted(grp, key=lambda x: x[0]["ord"]) if cr["kind"] == extra]
                if vals:
                    setp(obj, rel, vals)
            elif mode == "split":
                acc = splits.setdefault(rel, {})
                for cr, o in grp:
                    acc[cr["ord"]] = o
            elif mode == "entity":
                vals = []
                for cr, o in sorted(grp, key=lambda x: x[0]["ord"]):
                    o = {extra: cr[extra], **(o if isinstance(o, dict) else {})}
                    vals.append(o)
                if vals:
                    setp(obj, rel, vals)
            else:
                vals = [o for cr, o in sorted(grp, key=lambda x: x[0]["ord"])]
                if vals:
                    if rel == ("<list>",):
                        obj = vals
                    else:
                        setp(obj, rel, vals)
        for rel, acc in splits.items():
            if acc:
                setp(obj, rel, [acc[i] for i in sorted(acc)])
        if obj == {} and any(rel == ("<value>",) for c, rel in t.fields):
            obj = None
        res.append((r, pkey, obj))
    return res


def getp(obj, rel):
    d = obj
    for k in rel:
        if not isinstance(d, dict) or k not in d:
            return None
        d = d[k]
    return d


def prev_items(prev):
    return list(enumerate(prev)) if isinstance(prev, list) else []


def rebuild_grouped(eng, w, ch: TDef):
    g = collections.defaultdict(list)
    for r, pkey, obj in rebuild(eng, w, ch):
        g[tuple(r[c] for c in ch.parent_cols)].append((r, obj))
    return g


def cond_tree(w, cid):
    term = w.con.execute("SELECT term FROM condition WHERE id = ?", (cid,)).fetchone()[0]
    kids = [r[0] for r in w.con.execute("SELECT id FROM condition WHERE parent_id = ? ORDER BY ord", (cid,))]
    args = [r[0] for r in w.con.execute("SELECT value FROM condition_arg WHERE condition_id = ? ORDER BY ord",
                                        (cid,))]
    if term in ("all", "any"):
        return {term: [cond_tree(w, k) for k in kids]}
    if term == "not":
        return {"not": cond_tree(w, kids[0])}
    return {term: args}


def act_list(w, aid):
    out = []
    for ord_, term in w.con.execute("SELECT ord, term FROM action WHERE list_id = ? ORDER BY ord", (aid,)):
        args = [r[0] for r in w.con.execute(
            "SELECT value FROM action_arg WHERE list_id = ? AND ord = ? ORDER BY arg_ord", (aid, ord_))]
        out.append({term: args})
    return out


def canon_cond(v):
    if isinstance(v, list):
        return {"all": [canon_cond(x) for x in v]}
    if isinstance(v, dict):
        if len(v) != 1:
            return {"all": [canon_cond({k: a}) for k, a in v.items()]}
        k, a = next(iter(v.items()))
        if k in ("all", "any"):
            return {k: [canon_cond(x) for x in a]}
        if k == "not":
            return {"not": canon_cond(a)}
        return {k: [json.dumps(x, sort_keys=True) if isinstance(x, (dict, list)) else x
                    for x in (a if isinstance(a, list) else [a])]}
    return v


def canon_acts(v):
    if isinstance(v, dict):
        v = [v]
    return [{k: (a if isinstance(a, list) else [a]) for k, a in x.items()} for x in v]


def norm(x):
    """Comparison form: no None, no empty containers."""
    if isinstance(x, dict):
        out = {k: norm(v) for k, v in x.items()}
        return {k: v for k, v in out.items() if v not in (None, {}, [])}
    if isinstance(x, list):
        return [norm(v) for v in x]
    if isinstance(x, float) and x.is_integer():
        return int(x)
    return x


def prepare_source(spec: Spec, obj):
    """The source object as the rebuild will produce it: dropped paths removed, conditions and actions canonical."""
    def walk(x, p):
        if isinstance(x, dict):
            out = {}
            m = p in spec.maps
            for k, v in x.items():
                q = f"{p}{MAP}" if m else (f"{p}.{k}" if p else k)
                if q in spec.drop:
                    continue
                if q in spec.cond:
                    out[k] = canon_cond(v) if v not in (None, [], {}) else None
                elif q in spec.actions:
                    out[k] = canon_acts(v) if v else None
                else:
                    out[k] = walk(v, q)
            return out
        if isinstance(x, list):
            return [walk(v, p + "[]") for v in x]
        return x
    return norm(walk(obj, ""))


def prove(eng: Engine, w, spec: Spec) -> list[str]:
    t = eng.tables[spec.family]
    got = {pkey: obj for r, pkey, obj in rebuild(eng, w, t)}
    bad = []
    for ctx, obj in spec.items:
        k = tuple({**obj, **ctx}[c] for c in spec.pk)
        src = prepare_source(spec, obj)
        reb = norm(got.get(k, {}))
        for c in ctx:
            reb.pop(c, None) if c not in obj else None
        if src != reb:
            bad.append(f"{spec.family} {k}: {first_diff(src, reb)}")
    return bad


def first_diff(a, b, p=""):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if a.get(k) != b.get(k):
                return first_diff(a.get(k), b.get(k), f"{p}.{k}")
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            if x != y:
                return first_diff(x, y, f"{p}[{i}]")
    return f"{p}: source {json.dumps(a)[:160]} != rebuilt {json.dumps(b)[:160]}"


def jload(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))
