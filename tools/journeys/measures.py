"""The stand measures' cache (lane 1.15-r6-stand-cache): clearance, grass hits, frame read, frustum cover, water share
and the eye-ray read are pure functions of the build and their arguments, so each result is stored once per (build key,
MEASURE_VERSION, measure, rounded arguments) in out/journeys-cache/<build key>.sqlite (WAL: several refreshes append to
one store and never evict each other). The build key is the content of what the measures read, never this repo's code:
an edit to gen.py moves nothing. Bump MEASURE_VERSION when a measure's maths changes."""
from __future__ import annotations

import functools
import hashlib

from tools.argonia_world import db
import inspect
import json
import sqlite3
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = ROOT / "out" / "journeys-cache"
MEASURE_VERSION = 1
READS_DB = ("object_form", "ltex_grass")   # plant bounds (Build.shapes) and the landscape textures' grass (ltex_grass_heights)
ROUND = 4          # key arguments rounded to 0.1 mm (units are 1/70 m: finer than any search step)
KEEP_DAYS = 3

_state: dict = {"key": None, "db": None, "mem": None, "dir": None}


def build_key() -> str:
    """What the measures read, by content not mtime: the plant-bounds and grass tables, the water cells, the vegetation and
    land shard bytes (sha256 of each; a boot re-checkout touches every mtime) and MEASURE_VERSION."""
    h = hashlib.sha1()
    for t in READS_DB:   # the tables the measures read, by content: other lanes' rebuilds of the rest move nothing
        h.update((db.WORLD_ROOT / db.DB_DIR / f"{t}.jsonl").read_bytes())   # the jsonl bytes, the path named by db.py (0030 §3)
    o = ROOT / "out"
    h.update((o / "water" / "cells.jsonl").read_bytes())
    for p in [*sorted((o / "terrain" / "vegetation").glob("cy*.jsonl.gz")), *sorted((o / "terrain" / "land").glob("cy*.jsonl.gz"))]:
        if p.is_file():
            h.update(p.name.encode() + b":" + hashlib.sha256(p.read_bytes()).digest())   # the gzip header's mtime is 0: equal content, equal bytes
    h.update(f"v{MEASURE_VERSION}".encode())
    return h.hexdigest()[:16]


def _open() -> tuple[dict, sqlite3.Connection]:
    if _state["db"] is not None:
        return _state["mem"], _state["db"]
    d = Path(_state["dir"] or CACHE_DIR)
    d.mkdir(parents=True, exist_ok=True)
    if _state["key"] is None:
        _state["key"] = build_key()
    p = d / f"{_state['key']}.sqlite"
    db = sqlite3.connect(p, timeout=60, isolation_level=None)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    db.execute("CREATE TABLE IF NOT EXISTS m (k TEXT PRIMARY KEY, v TEXT) WITHOUT ROWID")
    _state["db"], _state["dir"], _state["mem"] = db, str(d), dict(db.execute("SELECT k, v FROM m"))
    for old in d.glob("*.sqlite*"):   # stores of builds long gone
        if not old.name.startswith(_state["key"]) and time.time() - old.stat().st_mtime > KEEP_DAYS * 86400:
            old.unlink(missing_ok=True)
    return _state["mem"], db


def flush() -> None:
    """Every insert autocommits (a held write lock would stall the other refreshes); nothing to flush."""


def reset(directory=None) -> None:
    """Close the store (tests: a new directory or a new key)."""
    db = _state["db"]
    if db is not None:
        db.close()
    _state.update(key=None, db=None, mem=None, dir=str(directory) if directory else None)


def _norm(v):
    if isinstance(v, float):
        return round(v, ROUND)
    if isinstance(v, (tuple, list)):
        return tuple(_norm(x) for x in v)
    return v


def memo(name: str, skip: tuple = (), dec=None, enc=None):
    """Cache a measure `f(b, *args)` on the real build only (a Build made from fixtures is never cached). `dec`/`enc`
    turn a result into JSON-able data and back where it is not plain (tuples, tuple-keyed dicts). `skip` names
    arguments the measure does not read. The whole store is read into memory on first use (a lookup is a dict hit)."""
    def deco(f):
        names = list(inspect.signature(f).parameters)[1:]
        skip_i = {names.index(k) for k in skip}

        @functools.wraps(f)
        def wrapper(b, *args, **kw):
            if not getattr(b, "real", False):
                return f(b, *args, **kw)
            k = repr((name, _norm(tuple(a for i, a in enumerate(args) if i not in skip_i)),
                      sorted((n, _norm(v)) for n, v in kw.items() if n not in skip)))
            mem, db = _open()
            hit = mem.get(k)
            if hit is not None:
                r = json.loads(hit)
                return dec(r) if dec else r
            res = f(b, *args, **kw)
            txt = json.dumps(enc(res) if enc else res)
            mem[k] = txt
            db.execute("INSERT OR IGNORE INTO m VALUES (?, ?)", (k, txt))
            return res
        wrapper.__wrapped_measure__ = f
        return wrapper
    return deco
