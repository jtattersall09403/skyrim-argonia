#!/usr/bin/env python3
"""The scale measurement (decision 0030 §7): the world with every table duplicated N-fold, for timing the load and
the gate outside the default gate.

Every row is copied N-1 times with each key suffixed `~k`: every TEXT primary-key column and every TEXT column
that is a foreign key (to a table's key, so the copies reference each other's copies). Other columns are copied
as they are; an INTEGER column under a UNIQUE constraint (formid's form_id) is offset per copy. The result is a
world root a tool can be pointed at:

    python3 -m tools.argonia_world.scale --factor 10 --out out/scale
    ARGONIA_WORLD_ROOT=out/scale python3 -m tools.argonia_world.db check
    ARGONIA_WORLD_ROOT=out/scale make check
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from tools.argonia_world import db


def unique_int_columns(w, table: str) -> set[str]:
    out = set()
    for idx in w.con.execute(f'PRAGMA index_list("{table}")'):
        if idx[2] and idx[3] == "u":
            cols = [r[2] for r in w.con.execute(f'PRAGMA index_info("{idx[1]}")')]
            t = w.table(table)
            out |= {c.name for c in t.columns if c.name in cols and c.type == "INTEGER"}
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--factor", type=int, default=10)
    ap.add_argument("--out", default="out/scale")
    a = ap.parse_args(argv)
    w = db.load(db.REPO)
    root = Path(a.out).resolve()
    (root / db.DB_DIR).mkdir(parents=True, exist_ok=True)
    for f in (root / db.DB_DIR).glob("*.jsonl"):
        f.unlink()
    (root / db.SCHEMA).write_text((db.REPO / db.SCHEMA).read_text(encoding="utf-8"), encoding="utf-8")
    rows = 0
    for name, t in w.tables.items():
        keyed = {c.name for c in t.columns if c.type == "TEXT" and c.name in t.pk}
        keyed |= {col for col, _, _ in t.fks if next(c for c in t.columns if c.name == col).type in ("TEXT", "")}
        uniq = unique_int_columns(w, name) - set(t.pk)
        cols = t.names
        with (root / db.DB_DIR / f"{name}.jsonl").open("w", encoding="utf-8") as fh:
            for r in w.con.execute(f'SELECT {", ".join(chr(34) + c + chr(34) for c in cols)} FROM "{name}"'):
                base = dict(zip(cols, r))
                for k in range(a.factor):
                    row = {}
                    for c, v in base.items():
                        if v is None:
                            continue
                        if k and c in keyed and isinstance(v, str):
                            v = f"{v}~{k}"
                        elif k and c in uniq and isinstance(v, int):
                            v = v + k * 1_000_000
                        row[c] = v
                    col = {c.name: c for c in t.columns}
                    fh.write(json.dumps({c: db._to_json(col[c], v) for c, v in row.items()},
                                        ensure_ascii=False, separators=(",", ":")) + "\n")
                    rows += 1
    print(f"wrote {root}: {len(w.tables)} tables, {rows} rows ({a.factor}x)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
