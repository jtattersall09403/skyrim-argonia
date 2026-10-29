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
# The migrator writes only the tables it migrates (OWNED: every table it fills from world/sources). Every other
# world/db/*.jsonl (formid, the world track's tables, a table it does not know) is left untouched, and every other
# table's CREATE block in schema.sql is taken from the live file, re-read right before the write.
MARK = "-- == End of the 0030 migration's tables. A later chunk appends its own tables below this line. =="
BLOCK = re.compile(r'(?ms)^((?:--[^\n]*\n)*)CREATE TABLE "(\w+)" \(.*?^\);\n')


def owned(eng) -> set[str]:
    return {name for name, rows in F.all_rows(eng) if rows}


def merge_schema(sql: str, live: str, own: set[str]) -> str:
    """The rendered schema, with every table it does not own taken from the live file and the live file's tail
    (after MARK, or the tables the rendered schema does not have) kept at the end."""
    live_blocks = {m.group(2): m.group(0) for m in BLOCK.finditer(live.split(MARK, 1)[0])}
    rendered = {m.group(2) for m in BLOCK.finditer(sql)}

    def swap(m):
        name = m.group(2)
        return live_blocks[name] if name not in own and name in live_blocks else m.group(0)
    out = BLOCK.sub(swap, sql).rstrip("\n") + "\n\n" + MARK + "\n"
    if MARK in live:
        tail = live.split(MARK, 1)[1].lstrip("\n")
    else:
        tail = "\n".join(b for n, b in live_blocks.items() if n not in rendered)
    return out + "\n" + tail if tail.strip() else out


def seed(root: Path) -> None:
    """A scratch root starts as a copy of the live world, so the write path runs exactly as it would on world/."""
    (root / "world" / "db").mkdir(parents=True, exist_ok=True)
    if not (root / db.SCHEMA).exists():
        (root / db.SCHEMA).write_bytes((REPO / db.SCHEMA).read_bytes())
    for f in (REPO / db.DB_DIR).glob("*.jsonl"):
        dst = root / db.DB_DIR / f.name
        if not dst.exists():
            dst.write_bytes(f.read_bytes())


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
    ap.add_argument("--no-write", action="store_true", help="write to out/migrate (a copy of the live world)")
    ap.add_argument("--root", help="write to this root (seeded with a copy of the live world)")
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
    out_root = Path(a.root) if a.root else (REPO if not a.no_write else REPO / "out" / "migrate")
    if out_root.resolve() != REPO.resolve():
        seed(out_root)
    own = owned(eng)
    schema = out_root / db.SCHEMA
    live = schema.read_text(encoding="utf-8") if schema.exists() else ""   # re-read right before the write
    schema.write_text(merge_schema(sql, live, own), encoding="utf-8")
    dbdir = out_root / db.DB_DIR
    for name in own:
        f = dbdir / f"{name}.jsonl"
        if f.exists():
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
    w.save(tables=sorted(own))
    print(f"migrated: {len(w.tables)} tables, {sum(db.counts(w).values())} rows -> {dbdir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
