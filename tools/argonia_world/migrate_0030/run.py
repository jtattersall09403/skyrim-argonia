"""Run decision 0030's migration: families -> world/schema.sql + world/db/*.jsonl, then prove it lossless.

    python3 -m tools.argonia_world.migrate_0030.run [--families a,b] [--no-write]
"""
from __future__ import annotations

import argparse
import collections
import re
import sys
from pathlib import Path

from tools.argonia_world import db
from tools.argonia_world.migrate_0030 import engine as E
from tools.argonia_world.migrate_0030 import families as F

REPO = db.REPO


def suggest_fks(eng: E.Engine) -> list[str]:
    ids = {}
    for t in eng.tables.values():
        if t.pk == ["id"] or (len(t.pk) == 1 and t.parent is None):
            ids[t.name] = {r[t.pk[0]] for r in t.rows}
    out = []
    for t in eng.tables.values():
        for c in t.cols.values():
            if c.fk or c.lookup or c.path == "<key>":
                continue
            vals = {r.get(c.name) for r in t.rows} - {None}
            if not vals or not all(isinstance(v, str) for v in vals):
                continue
            for name, pool in ids.items():
                hit = len(vals & pool)
                if hit and hit >= 0.5 * len(vals):
                    miss = sorted(vals - pool)
                    out.append(f"FK? {t.name}.{c.name} ({c.path}) -> {name}: {hit}/{len(vals)}"
                               + (f" missing {miss[:4]}" if miss else ""))
    return out


def suggest_lookups(eng: E.Engine) -> list[str]:
    out = []
    for t in eng.tables.values():
        for c in t.cols.values():
            if c.fk or c.lookup or c.name in t.pk or c.name.endswith("_id"):
                continue
            vals = [r.get(c.name) for r in t.rows if r.get(c.name) is not None]
            if len(vals) >= 20 and all(isinstance(v, str) for v in vals):
                d = collections.Counter(vals)
                if len(d) <= 16 and all(len(v) < 40 and " " not in v.strip() for v in d):
                    out.append(f"LOOKUP? {t.name}.{c.name} ({c.path}): {sorted(d)}")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--families", default="")
    ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--suggest", action="store_true")
    a = ap.parse_args(argv)
    eng = E.Engine()
    specs = F.build(eng, only=[x for x in a.families.split(",") if x])
    for s in specs:
        eng.run(s)
    F.finish(eng)
    eng.finalise()
    sql = F.render(eng)
    print("\n".join(eng.report))
    if a.suggest:
        print("\n".join(suggest_fks(eng)))
        print("\n".join(suggest_lookups(eng)))
    out_root = REPO if not a.no_write else Path(REPO / "out" / "migrate")
    (out_root / "world").mkdir(parents=True, exist_ok=True)
    (out_root / "world" / "schema.sql").write_text(sql)
    dbdir = out_root / "world" / "db"
    dbdir.mkdir(parents=True, exist_ok=True)
    for f in dbdir.glob("*.jsonl"):
        f.unlink()
    w = db.load(out_root)          # empty world on the new schema
    for name, rows in F.all_rows(eng):
        t = w.table(name)
        cols = t.names
        by = {c.name: c for c in t.columns}
        w._begin()
        try:
            w.con.executemany(f'INSERT INTO "{name}" VALUES ({", ".join("?" * len(cols))})',
                              [[db._check_value(by[c], r.get(c)) for c in cols] for r in rows])
        except Exception as e:  # find the offending row
            for r in rows:
                try:
                    w.con.execute(f'INSERT INTO "{name}" VALUES ({", ".join("?" * len(cols))})',
                                  [db._check_value(by[c], r.get(c)) for c in cols])
                except Exception as e2:
                    print(f"{name}: {e2}: {dict((k, v) for k, v in r.items() if v is not None)}"[:600])
                    break
            raise SystemExit(f"{name}: {e}")
        w.dirty.add(name)
    errs = db.fk_errors(w)
    if errs:
        print(f"{len(errs)} FK errors:")
        groups = collections.Counter(re.sub(r" \(.*?\):", ":", e).split(" = ")[0] + " -> " + e.split("has no row in ")[1]
                                     for e in errs)
        for g, n in groups.most_common():
            print(f"  {n:5d} {g}")
        for e in errs[:20]:
            print("   ", e)
        return 1
    bad = []
    for s in specs:
        bad += E.prove(eng, w, s)
    if bad:
        print(f"{len(bad)} rebuild differences:")
        for b in bad[:30]:
            print("  ", b)
        return 1
    w.save(tables=[t for t in w.tables])
    print(f"migrated: {len(w.tables)} tables, {sum(db.counts(w).values())} rows -> {dbdir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
