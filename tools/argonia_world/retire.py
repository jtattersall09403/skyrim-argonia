#!/usr/bin/env python3
"""Remove rows from the story database and everything that hangs on them, through db.py.

    python3 -m tools.argonia_world.retire quest.example.one faction.example [--like quest.fg.%] [--dry-run]

Each named id is deleted from every table whose primary key is a single `id` column holding it; `--like` adds the
ids matching a SQL LIKE pattern. Then, until no foreign key dangles: a row whose dangling column may be NULL has it
set to NULL, and any other row that points at a removed row is removed too. Nothing is written while db.py's checks
fail. The quest build's seed then drops the built records of what was removed (quest-build, "Seed the plugin").
"""
from __future__ import annotations

import argparse
import sys

from tools.argonia_world import db


def _id_tables(w: db.World) -> list[str]:
    return [n for n, t in w.tables.items() if t.pk == ["id"]]


def retire(w: db.World, ids: list[str], likes: list[str]) -> dict[str, int]:
    from tools.argonia_world import quest_record as qr
    w._begin()
    gone: dict[str, int] = {}
    ids = list(ids)
    for pat in likes:
        for t in _id_tables(w):
            ids += w.values(f'SELECT "id" FROM "{t}" WHERE "id" LIKE ?', pat)
    ids = sorted(set(ids))
    quests = [i for i in ids if w.get("quest", i) is not None]
    for qid in quests:      # a quest's record: its conditions, action lists, facts and quest_* rows
        conds, lists = qr._owned(w, qid)
        for node in reversed(list(qr._tables())[1:]):
            w.delete(node["table"], quest_id=qid)
        for cid in conds:
            w.delete("condition", cid)
        for aid in lists:
            w.delete("action_list", aid)
        w.delete("fact", quest_id=qid)
    # rows that name a removed id in a column called <kind>_id or <kind> without a declared key
    sweep = [(t.name, c.name) for t in w.tables.values() for c in t.columns
             if c.name in ("quest_id", "faction_id", "line_id", "faction", "line", "quest")]
    for t, c in sweep:
        if t in ("quest", "quest_line", "faction") and c == "id":
            continue
        for i in ids:
            n = w.con.execute(f'DELETE FROM "{t}" WHERE "{c}" = ?', (i,)).rowcount
            if n:
                w.dirty.add(t)
                gone[t] = gone.get(t, 0) + n
    likes = []
    for t in _id_tables(w):
        for i in ids:
            n = w.delete(t, i)
            if n:
                gone[t] = gone.get(t, 0) + n
        for pat in likes:
            n = w.con.execute(f'DELETE FROM "{t}" WHERE "id" LIKE ?', (pat,)).rowcount
            if n:
                w.dirty.add(t)
                gone[t] = gone.get(t, 0) + n
    for _ in range(50):
        bad = list(w.con.execute("PRAGMA foreign_key_check"))
        if not bad:
            break
        for table, fkid in sorted({(b[0], b[3]) for b in bad}):
            fk = [f for f in w.con.execute(f'PRAGMA foreign_key_list("{table}")') if f[0] == fkid]
            parent, cols, pcols = fk[0][2], [f[3] for f in fk], [f[4] for f in fk]
            q = lambda cs: ", ".join(f'"{c}"' for c in cs)  # noqa: E731
            dangling = (f'({q(cols)}) NOT IN (SELECT {q(pcols)} FROM "{parent}") AND '
                        + " AND ".join(f'"{c}" IS NOT NULL' for c in cols)) if len(cols) > 1 else \
                       (f'"{cols[0]}" IS NOT NULL AND "{cols[0]}" NOT IN (SELECT "{pcols[0]}" FROM "{parent}")')
            notnull = {c[1]: c[3] for c in w.con.execute(f'PRAGMA table_info("{table}")')}
            if all(not notnull[c] for c in cols) and not any(c in (w.tables[table].pk or []) for c in cols):
                w.con.execute(f'UPDATE "{table}" SET ' + ", ".join(f'"{c}" = NULL' for c in cols) + f" WHERE {dangling}")
            else:
                n = w.con.execute(f'DELETE FROM "{table}" WHERE {dangling}').rowcount
                gone[table] = gone.get(table, 0) + n
            w.dirty.add(table)
    w.con.execute("PRAGMA foreign_keys = ON")
    return gone


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--like", action="append", default=[])
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    w = db.load(strict=False)   # a table a cascade emptied in memory is written too, so a half-written retire heals
    gone = retire(w, a.ids, a.like)
    for t, n in sorted(gone.items()):
        print(f"{n:6d}  {t}")
    if a.dry_run:
        print("dry run: nothing written")
        return 0
    try:
        w._begin()
        on_disk = [t for t in w.tables if (w.root / db.DB_DIR / f"{t}.jsonl").exists()]
        names = w.save(tables=on_disk)   # ON DELETE CASCADE empties child tables db.py never marks dirty
    except db.LoadError as e:
        print("\n".join(map(str, e.args[0][:20])))
        return 1
    print(f"wrote {len(names)} tables")
    return 0


if __name__ == "__main__":
    sys.exit(main())
