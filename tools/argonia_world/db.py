"""The world database (decision 0030): the only reader and the only writer of `world/db/*.jsonl`.

`world/schema.sql` is the single description of the world's data; `world/db/<table>.jsonl` holds one row per line,
columns in schema order, rows sorted by primary key. This module loads every table into SQLite with the DDL and
foreign keys enforced, hands out typed rows and queries, and writes changed tables back sorted. A tool that opens a
`world/` file itself is a defect (the gate's `world-reads` check).

    from tools.argonia_world import db
    w = db.open()                          # load (or reuse a fresh out/world.sqlite), FKs on
    w.get("npc", "npc.x")                  # one typed row (a dataclass), or None
    w.rows("npc_faction", npc_id="npc.x")  # typed rows, ordered by primary key
    w.query("SELECT ... WHERE id = ?", x)  # sqlite3.Row list for anything else
    w.insert("topic", id=..., ...); w.update("topic", "topic.x", label="..."); w.delete("topic", "topic.x")
    w.save()                               # FK check + named checks, then the changed tables written back sorted

    python3 -m tools.argonia_world.db build [--out out/world.sqlite]   # `make db`
    python3 -m tools.argonia_world.db check                            # the gate: load + constraints + named checks
    python3 -m tools.argonia_world.db query "SELECT count(*) FROM npc"
    python3 -m tools.argonia_world.db show npc npc.claywater.x
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import os
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any, Callable, Iterable

REPO = Path(__file__).resolve().parents[2]
SCHEMA = "world/schema.sql"
DB_DIR = "world/db"
OUT = "out/world.sqlite"

PYTYPE = {"TEXT": str, "INTEGER": int, "REAL": float, "BOOLEAN": bool, "": object}


class LoadError(Exception):
    """The world does not load: a row breaks a type, key or constraint. `errors` lists every one found."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__(f"{len(errors)} error(s):\n  " + "\n  ".join(errors[:50]))


@dataclasses.dataclass(frozen=True)
class Column:
    name: str
    type: str          # TEXT, INTEGER, REAL, BOOLEAN or '' (any scalar)
    notnull: bool
    pk: int            # position in the primary key, 0 if not part of it


@dataclasses.dataclass
class Table:
    name: str
    columns: list[Column]
    pk: list[str]
    fks: list[tuple[str, str, str]]      # (column, parent table, parent column)
    row_type: type = None

    @property
    def names(self) -> list[str]:
        return [c.name for c in self.columns]


def _schema_tables(con: sqlite3.Connection) -> dict[str, Table]:
    out = {}
    names = [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    for name in names:
        cols = [Column(r[1], (r[2] or "").upper(), bool(r[3]), r[5])
                for r in con.execute(f'PRAGMA table_info("{name}")')]
        pk = [c.name for c in sorted((c for c in cols if c.pk), key=lambda c: c.pk)]
        fks = [(r[3], r[2], r[4]) for r in con.execute(f'PRAGMA foreign_key_list("{name}")')]
        t = Table(name, cols, pk, fks)
        t.row_type = dataclasses.make_dataclass(
            "".join(p.title() for p in name.split("_")),
            [(c.name, PYTYPE.get(c.type, object) | None) for c in cols], frozen=True)
        out[name] = t
    return out


def _check_value(col: Column, v: Any) -> Any:
    """The JSON value as SQLite stores it, or ValueError when it is not of the column's type."""
    if v is None:
        return None
    t = col.type
    if t == "TEXT":
        if isinstance(v, str):
            return v
    elif t == "BOOLEAN":
        if isinstance(v, bool):
            return int(v)
    elif t == "INTEGER":
        if isinstance(v, int) and not isinstance(v, bool):
            return v
    elif t == "REAL":
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return float(v)
    elif t == "":
        if isinstance(v, (str, int, float, bool)):
            return v
    raise ValueError(f"{col.name}: {v!r} is not {t or 'a scalar'}")


def _to_json(col: Column, v: Any) -> Any:
    if v is None:
        return None
    if col.type == "BOOLEAN":
        return bool(v)
    return v


class World:
    """One loaded world: a SQLite connection with foreign keys on, the schema's tables, and the write path."""

    def __init__(self, con: sqlite3.Connection, root: Path):
        self.con = con
        self.root = root
        self.tables = _schema_tables(con)
        self.dirty: set[str] = set()

    # -- reading ---------------------------------------------------------------------------------------------
    def table(self, name: str) -> Table:
        try:
            return self.tables[name]
        except KeyError:
            raise KeyError(f"no table {name!r} in {SCHEMA}") from None

    def _typed(self, t: Table, r: sqlite3.Row | tuple):
        vals = []
        for c, v in zip(t.columns, r):
            vals.append(bool(v) if c.type == "BOOLEAN" and v is not None else v)
        return t.row_type(*vals)

    def rows(self, table: str, order: str | None = None, **where) -> list:
        """Typed rows of one table where every keyword equals its column, ordered by primary key (or `order`)."""
        t = self.table(table)
        bad = set(where) - set(t.names)
        if bad:
            raise KeyError(f"{table} has no column(s) {sorted(bad)}")
        sql = f'SELECT {", ".join(chr(34) + n + chr(34) for n in t.names)} FROM "{table}"'
        if where:
            sql += " WHERE " + " AND ".join(f'"{k}" IS ?' for k in where)
        sql += " ORDER BY " + (order or ", ".join(f'"{k}"' for k in (t.pk or ["rowid"])))
        return [self._typed(t, r) for r in self.con.execute(sql, list(where.values()))]

    def get(self, table: str, *key):
        """The row with this primary key (one value per key column), or None."""
        t = self.table(table)
        if len(key) != len(t.pk):
            raise KeyError(f"{table}'s key is {t.pk}, got {key!r}")
        got = self.rows(table, **dict(zip(t.pk, key)))
        return got[0] if got else None

    def query(self, sql: str, *params) -> list[sqlite3.Row]:
        """Any read-only SQL; rows support r["col"] and r[0]."""
        if not re.match(r"\s*(SELECT|WITH|PRAGMA)\b", sql, re.I):
            raise ValueError("query() reads; write through insert/update/delete")
        return self.con.execute(sql, params).fetchall()

    def values(self, sql: str, *params) -> list:
        """The first column of every row of a query."""
        return [r[0] for r in self.query(sql, *params)]

    # -- the write path --------------------------------------------------------------------------------------
    def _prepare(self, t: Table, row: dict) -> dict:
        bad = set(row) - set(t.names)
        if bad:
            raise KeyError(f"{t.name} has no column(s) {sorted(bad)}")
        by = {c.name: c for c in t.columns}
        return {k: _check_value(by[k], v) for k, v in row.items()}

    def _begin(self) -> None:
        """Writes run in one transaction with foreign keys deferred to save(), so rows may arrive in any order."""
        if not self.con.in_transaction:
            self.con.execute("BEGIN")
            self.con.execute("PRAGMA defer_foreign_keys = ON")

    def insert(self, table: str, row: dict | None = None, **cols) -> None:
        self._begin()
        t = self.table(table)
        r = self._prepare(t, {**(row or {}), **cols})
        names = list(r)
        self.con.execute(f'INSERT INTO "{table}" ({", ".join(chr(34) + n + chr(34) for n in names)}) '
                         f'VALUES ({", ".join("?" * len(names))})', [r[n] for n in names])
        self.dirty.add(table)

    def insert_many(self, table: str, rows: Iterable[dict]) -> int:
        t = self.table(table)
        n = 0
        for row in rows:
            self.insert(t.name, row)
            n += 1
        return n

    def upsert(self, table: str, row: dict | None = None, **cols) -> None:
        t = self.table(table)
        r = {**(row or {}), **cols}
        key = [r.get(k) for k in t.pk]
        if self.get(table, *key) is None:
            self.insert(table, r)
        else:
            self.update(table, *key, **{k: v for k, v in r.items() if k not in t.pk})

    def update(self, table: str, *key, **cols) -> None:
        t = self.table(table)
        if len(key) != len(t.pk):
            raise KeyError(f"{table}'s key is {t.pk}, got {key!r}")
        r = self._prepare(t, cols)
        if not r:
            return
        self._begin()
        cur = self.con.execute(
            f'UPDATE "{table}" SET {", ".join(f"{chr(34)}{k}{chr(34)} = ?" for k in r)} '
            f'WHERE {" AND ".join(f"{chr(34)}{k}{chr(34)} = ?" for k in t.pk)}', [*r.values(), *key])
        if cur.rowcount != 1:
            raise KeyError(f"{table} has no row {key!r}")
        self.dirty.add(table)

    def delete(self, table: str, *key, **where) -> int:
        """Delete by primary key, or every row matching `where` (columns equal)."""
        t = self.table(table)
        cond = dict(zip(t.pk, key)) if key else where
        if not cond:
            raise ValueError("delete needs a key or a where")
        self._begin()
        cur = self.con.execute(f'DELETE FROM "{table}" WHERE ' + " AND ".join(f'"{k}" IS ?' for k in cond),
                               list(cond.values()))
        self.dirty.add(table)
        return cur.rowcount

    def errors(self) -> list[str]:
        """Every dangling foreign key and every failing named check."""
        out = fk_errors(self)
        from . import checks
        out += checks.run(self)
        return out

    def save(self, tables: Iterable[str] | None = None) -> list[str]:
        """Write the changed tables (or `tables`) back to world/db, sorted by key, after the FK and named checks.
        Nothing is written while any check fails; the errors are raised."""
        errs = self.errors()
        if errs:
            raise LoadError(errs)
        self.con.commit()
        names = sorted(set(tables) if tables is not None else self.dirty)
        d = self.root / DB_DIR
        d.mkdir(parents=True, exist_ok=True)
        for name in names:
            write_table(self, name, d / f"{name}.jsonl")
        self.dirty.clear()
        return names

    def dump(self, out: Path) -> Path:
        """The loaded world as one SQLite file (for DuckDB, pandas or the sqlite3 shell)."""
        out = Path(out)
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_suffix(".tmp")
        if tmp.exists():
            tmp.unlink()
        self.con.commit()
        dst = sqlite3.connect(tmp)
        self.con.backup(dst)
        dst.close()
        os.replace(tmp, out)
        return out


def write_table(w: World, name: str, path: Path) -> None:
    t = w.table(name)
    cols = t.columns
    order = ", ".join(f'"{k}"' for k in (t.pk or t.names))
    lines = []
    for r in w.con.execute(f'SELECT {", ".join(chr(34) + n + chr(34) for n in t.names)} FROM "{name}" ORDER BY {order}'):
        obj = {c.name: _to_json(c, v) for c, v in zip(cols, r) if v is not None}
        lines.append(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))
    tmp = path.with_suffix(".jsonl.tmp")
    tmp.write_text("".join(x + "\n" for x in lines), encoding="utf-8")
    os.replace(tmp, path)


def fk_errors(w: World) -> list[str]:
    out = []
    for table, rowid, parent, fkid in w.con.execute("PRAGMA foreign_key_check"):
        t = w.tables[table]
        fk = [f for f in w.con.execute(f'PRAGMA foreign_key_list("{table}")') if f[0] == fkid]
        cols = [f[3] for f in fk]
        key = w.con.execute(f'SELECT {", ".join(chr(34) + k + chr(34) for k in (t.pk or ["rowid"]))}, '
                            f'{", ".join(chr(34) + c + chr(34) for c in cols)} FROM "{table}" WHERE rowid = ?',
                            (rowid,)).fetchone()
        n = len(t.pk or ["rowid"])
        out.append(f"{table} {tuple(key[:n])}: {', '.join(cols)} = {tuple(key[n:])} has no row in {parent}")
    return out


def _connect(path: str = ":memory:") -> sqlite3.Connection:
    con = sqlite3.connect(path)
    con.execute("PRAGMA foreign_keys = ON")
    return con


def load(root: Path | str | None = None, db_dir: Path | str | None = None, strict: bool = True) -> World:
    """Build the world in memory from schema.sql and world/db/*.jsonl. Every type, NOT NULL, CHECK, UNIQUE and
    foreign-key violation is collected and raised as one LoadError (strict) or left in w.load_errors."""
    root = Path(root or REPO)
    con = _connect()
    con.executescript((root / SCHEMA).read_text(encoding="utf-8"))
    w = World(con, root)
    d = Path(db_dir) if db_dir else root / DB_DIR
    errs: list[str] = []
    known = set(w.tables)
    for f in sorted(d.glob("*.jsonl")) if d.exists() else []:
        if f.stem not in known:
            errs.append(f"{f.name}: no table {f.stem} in {SCHEMA}")
    con.execute("PRAGMA defer_foreign_keys = ON")
    con.execute("BEGIN")
    for name, t in w.tables.items():
        f = d / f"{name}.jsonl"
        if not f.exists():
            continue
        by = {c.name: c for c in t.columns}
        names = t.names
        sql = f'INSERT INTO "{name}" VALUES ({", ".join("?" * len(names))})'
        batch = []
        with f.open(encoding="utf-8") as fh:
            for i, line in enumerate(fh, 1):
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                    bad = set(obj) - set(names)
                    if bad:
                        raise ValueError(f"unknown column(s) {sorted(bad)}")
                    batch.append([_check_value(by[n], obj.get(n)) for n in names])
                except ValueError as e:
                    errs.append(f"{name}.jsonl:{i}: {e}")
        try:
            con.executemany(sql, batch)
        except sqlite3.IntegrityError:
            for row in batch:  # find each offending row
                try:
                    con.execute(sql, row)
                except sqlite3.IntegrityError as e:
                    key = {k: row[names.index(k)] for k in t.pk}
                    errs.append(f"{name} {key}: {e}")
    errs += fk_errors(w)
    w.load_errors = errs
    if errs and strict:
        con.rollback()
        raise LoadError(errs)
    con.execute("PRAGMA defer_foreign_keys = OFF")
    con.commit()
    w.dirty.clear()
    return w


def _fresh(root: Path, out: Path) -> bool:
    if not out.exists():
        return False
    t = out.stat().st_mtime
    srcs = [root / SCHEMA, *(root / DB_DIR).glob("*.jsonl")]
    return all(p.stat().st_mtime <= t for p in srcs if p.exists()) and \
        len(list((root / DB_DIR).glob("*.jsonl"))) == int(_meta(out).get("tables", -1))


def _meta(out: Path) -> dict:
    try:
        con = sqlite3.connect(f"file:{out}?mode=ro", uri=True)
        r = con.execute("SELECT value FROM _built WHERE key = 'tables'").fetchone()
        con.close()
        return {"tables": r[0]} if r else {}
    except sqlite3.Error:
        return {}


def open(root: Path | str | None = None, cache: bool = True) -> World:  # noqa: A001 - the module's verb
    """The world for a tool: a fresh out/world.sqlite copied into memory when it is newer than every table file
    and the schema, else a full load (which also refreshes the cache)."""
    root = Path(root or REPO)
    out = root / OUT
    if cache and _fresh(root, out):
        src = sqlite3.connect(f"file:{out}?mode=ro", uri=True)
        con = _connect()
        src.backup(con)
        src.close()
        con.execute("DROP TABLE IF EXISTS _built")
        con.execute("PRAGMA foreign_keys = ON")
        return World(con, root)
    w = load(root)
    if cache:
        build(w, out)
    return w


def build(w: World, out: Path) -> Path:
    n = len(list((w.root / DB_DIR).glob("*.jsonl")))
    w.dump(out)
    con = sqlite3.connect(out)
    con.execute("CREATE TABLE IF NOT EXISTS _built (key TEXT PRIMARY KEY, value)")
    con.execute("INSERT OR REPLACE INTO _built VALUES ('tables', ?)", (n,))
    con.commit()
    con.close()
    return out


def counts(w: World) -> dict[str, int]:
    return {t: w.con.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0] for t in w.tables}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="db", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="load and write out/world.sqlite")
    b.add_argument("--out", default=OUT)
    sub.add_parser("check", help="load with every constraint, then the named checks")
    q = sub.add_parser("query")
    q.add_argument("sql")
    s = sub.add_parser("show")
    s.add_argument("table")
    s.add_argument("key", nargs="+")
    sub.add_parser("counts")
    a = ap.parse_args(argv)
    try:
        w = load() if a.cmd in ("build", "check") else open()
    except LoadError as e:
        print(f"world does not load: {e}")
        return 1
    if a.cmd == "build":
        out = build(w, REPO / a.out)
        print(f"wrote {out.relative_to(REPO)}: {len(w.tables)} tables, {sum(counts(w).values())} rows")
    elif a.cmd == "check":
        errs = w.errors()
        if errs:
            print(f"world: {len(errs)} error(s)\n  " + "\n  ".join(errs))
            return 1
        print(f"world: {len(w.tables)} tables, {sum(counts(w).values())} rows, FKs and named checks green")
    elif a.cmd == "query":
        for r in w.query(a.sql):
            print("\t".join("" if v is None else str(v) for v in r))
    elif a.cmd == "show":
        r = w.get(a.table, *a.key)
        print(json.dumps(dataclasses.asdict(r), indent=1, ensure_ascii=False) if r else "no such row")
        return 0 if r else 1
    elif a.cmd == "counts":
        for t, n in sorted(counts(w).items()):
            print(f"{n:8d}  {t}")
    return 0


Check = Callable[[World], list[str]]

if __name__ == "__main__":
    sys.exit(main())
