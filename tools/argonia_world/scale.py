#!/usr/bin/env python3
"""The scale measurement (decision 0030 §7): the world with every table duplicated N-fold, for timing the load and
the gate outside the default gate.

Every row (but the vocabularies': lookups and condition_term, copied once) is copied N-1 times with each key suffixed `~k`: every TEXT primary-key column and every TEXT column
that is a foreign key (to a table's key, so the copies reference each other's copies). Other columns are copied
as they are; an INTEGER column under a UNIQUE constraint (formid's form_id), is offset per copy; a
table keyed by integers only (a raster's cells, a root list) is copied once. The result is a
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


def unique_columns(w, table: str) -> set[str]:
    out = set()
    for idx in w.con.execute(f'PRAGMA index_list("{table}")'):
        if idx[2] and idx[3] == "u":
            cols = [r[2] for r in w.con.execute(f'PRAGMA index_info("{idx[1]}")')]
            t = w.table(table)
            out |= {c.name for c in t.columns if c.name in cols and c.type in ("INTEGER", "TEXT")}
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
    # Vocabularies do not grow with the world: the lookups (id, about) and the condition vocabulary are copied once
    # and every copy references them unchanged.
    vocab = {n for n, t in w.tables.items() if t.names == ["id", "about"]} | {"condition_term"}
    for name, t in w.tables.items():
        if name in vocab:
            keyed, factor = set(), 1
        else:
            to_vocab = {col for col, parent, _ in t.fks if parent in vocab}
            keyed = {c.name for c in t.columns if c.type == "TEXT" and c.name in t.pk} - to_vocab
            factor = a.factor
            keyed |= {col for col, parent, _ in t.fks if parent not in vocab
                      and next(c for c in t.columns if c.name == col).type in ("TEXT", "")}
        uq = unique_columns(w, name) - set(t.pk)
        if factor > 1:
            keyed |= {c.name for c in t.columns if c.name in uq and c.type == "TEXT"} - to_vocab
        uniq = {c.name for c in t.columns if c.name in uq and c.type == "INTEGER"}
        if t.pk and not keyed & set(t.pk):   # a key of integers only (a raster's cells, a root list): copied once
            factor = 1
        cols = t.names
        with (root / db.DB_DIR / f"{name}.jsonl").open("w", encoding="utf-8") as fh:
            for r in w.con.execute(f'SELECT {", ".join(chr(34) + c + chr(34) for c in cols)} FROM "{name}"'):
                base = dict(zip(cols, r))
                for k in range(factor):
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
