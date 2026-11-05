"""The stand measures' cache (lanes 1.15-r6-stand-cache, 1.15-r6-measures-local): clearance, grass hits, frame read,
frustum cover, water share and the eye-ray read are pure functions of the build near their arguments, so each result is
stored once per (local key, measure, rounded arguments) in out/journeys-cache/v<MEASURE_VERSION>.sqlite (WAL: several
refreshes append to one store and never evict each other). The local key is the content of exactly the cells a measure
reads (its `reach` box, a cell of padding each side): the vegetation, land and creature shard lines and cells.jsonl row
of each, plus the static tables (object_form, ltex_grass, canopy radii) and MEASURE_VERSION. A land change anywhere
moves only the stands within reach of it. Never this repo's code: an edit to gen.py moves nothing. Bump MEASURE_VERSION
when a measure's maths changes."""
from __future__ import annotations

import functools
import gzip
import hashlib

from tools.argonia_world import db, skyrim_units as su
import inspect
import json
import math
import re
import sqlite3
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = ROOT / "out" / "journeys-cache"
MEASURE_VERSION = 3   # 2: canopy radii widen the plant shapes; 3: frustum cover capped at 100 % per region
READS_DB = ("object_form", "ltex_grass")   # plant bounds (Build.shapes) and the landscape textures' grass (ltex_grass_heights)
ROUND = 4          # key arguments rounded to 0.1 mm (units are 1/70 m: finer than any search step)
KEEP_DAYS = 3

_state: dict = {"key": None, "db": None, "mem": None, "dir": None, "cells": None, "static": None, "gkey": None,
                "boxes": {}, "hit": 0, "miss": 0, "seen": None}
XY = re.compile(rb'"x":\s*(-?\d+),\s*"y":\s*(-?\d+)\s*\}\s*$')   # a shard line's cell, keys sorted: at the end


def static_key() -> str:
    """The tables and files every measure reads whatever the cell, by content: object_form (plant bounds), ltex_grass,
    the canopy radii, MEASURE_VERSION."""
    if _state["static"] is None:
        h = hashlib.sha1()
        for t in READS_DB:   # the jsonl bytes, the path named by db.py (0030 §3): other lanes' rebuilds of the rest move nothing
            h.update((db.WORLD_ROOT / db.DB_DIR / f"{t}.jsonl").read_bytes())
        if (ROOT / "data" / "canopy-radius.json").is_file():
            h.update((ROOT / "data" / "canopy-radius.json").read_bytes())
        h.update(f"v{MEASURE_VERSION}".encode())
        _state["static"] = h.hexdigest()[:16]
    return _state["static"]


def _shard_lines(path: Path):
    with gzip.open(path, "rb") as f:   # the gzip header's mtime is 0: only content counts
        for ln in f:
            m = XY.search(ln)
            c = (int(m.group(1)), int(m.group(2))) if m else (lambda d: (d["x"], d["y"]))(json.loads(ln))
            yield c, ln


def cell_hashes() -> dict:
    """(cx, cy) -> digest of that cell's vegetation, land and creature shard lines and cells.jsonl row; built once per
    process from the shards in one pass (a few seconds). A cell in no source is absent."""
    if _state["cells"] is None:
        o = ROOT / "out"
        hs: dict = {}
        for tag, files in (("v", sorted((o / "terrain" / "vegetation").glob("cy*.jsonl.gz"))),
                           ("l", sorted((o / "terrain" / "land").glob("cy*.jsonl.gz"))),
                           ("c", sorted((o / "terrain" / "creatures").glob("cy*.jsonl.gz")))):
            for p in files:
                for c, ln in _shard_lines(p):
                    hs.setdefault(c, hashlib.sha1()).update(tag.encode() + ln)
        wp = o / "water" / "cells.jsonl"
        if wp.is_file():
            with open(wp, "rb") as f:
                for ln in f:
                    m = re.search(rb'"x":\s*(-?\d+),\s*"y":\s*(-?\d+)', ln)
                    c = (int(m.group(1)), int(m.group(2))) if m else (lambda d: (d["x"], d["y"]))(json.loads(ln))
                    hs.setdefault(c, hashlib.sha1()).update(b"w" + ln)
        _state["cells"] = {c: h.digest() for c, h in hs.items()}
    return _state["cells"]


def local_key(x0: float, y0: float, x1: float, y1: float) -> str:
    """The key of the cells a box (units) reaches, a cell of padding each side (a plant belongs to the cell it stands
    in, the ground blends across the border): their content digests and the static key."""
    pad = su.CELL_UNITS
    cx0, cy0 = su.cell_of(min(x0, x1) - pad, min(y0, y1) - pad)
    cx1, cy1 = su.cell_of(max(x0, x1) + pad, max(y0, y1) + pad)
    box = _state["boxes"].get((cx0, cy0, cx1, cy1))
    if box is None:
        cells = cell_hashes()
        h = hashlib.sha1(static_key().encode())
        for cy in range(cy0, cy1 + 1):
            for cx in range(cx0, cx1 + 1):
                h.update(cells.get((cx, cy), b"-"))
        box = _state["boxes"][(cx0, cy0, cx1, cy1)] = h.hexdigest()[:16]
    return box


def build_key() -> str:
    """The whole build's key (every cell): what a measure without a `reach` is keyed by."""
    h = hashlib.sha1(static_key().encode())
    cells = cell_hashes()
    for c in sorted(cells):
        h.update(cells[c])
    return h.hexdigest()[:16]


def stats() -> str:
    return f"measures: {_state['hit']} hit, {_state['miss']} miss"


def _open() -> tuple[dict, sqlite3.Connection]:
    if _state["db"] is not None:
        return _state["mem"], _state["db"]
    d = Path(_state["dir"] or CACHE_DIR)
    d.mkdir(parents=True, exist_ok=True)
    stem = _state["key"] or f"v{MEASURE_VERSION}"
    p = d / f"{stem}.sqlite"
    db = sqlite3.connect(p, timeout=60, isolation_level=None)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    db.execute("CREATE TABLE IF NOT EXISTS m (k TEXT PRIMARY KEY, v TEXT, d INTEGER DEFAULT 0) WITHOUT ROWID")
    if "d" not in {r[1] for r in db.execute("PRAGMA table_info(m)")}:
        db.execute("ALTER TABLE m ADD COLUMN d INTEGER DEFAULT 0")
    today = int(time.time() // 86400)
    db.execute("DELETE FROM m WHERE d < ?", (today - KEEP_DAYS,))   # rows of cells long changed (a hit re-dates its row)
    rows = db.execute("SELECT k, v, d FROM m").fetchall()
    _state["db"], _state["dir"], _state["mem"] = db, str(d), {k: v for k, v, _ in rows}
    _state["seen"] = {k: dd for k, _, dd in rows}
    for old in d.glob("*.sqlite*"):   # stores of other versions or builds long gone
        if not old.name.startswith(stem) and time.time() - old.stat().st_mtime > KEEP_DAYS * 86400:
            old.unlink(missing_ok=True)
    return _state["mem"], db


def flush() -> None:
    """Every insert autocommits (a held write lock would stall the other refreshes); nothing to flush."""


def reset(directory=None) -> None:
    """Close the store (tests: a new directory or a new key)."""
    db = _state["db"]
    if db is not None:
        db.close()
    _state.update(key=None, db=None, mem=None, dir=str(directory) if directory else None, cells=None, static=None, gkey=None,
                  boxes={}, hit=0, miss=0, seen=None)


def _norm(v):
    if isinstance(v, float):
        return round(v, ROUND)
    if isinstance(v, (tuple, list)):
        return tuple(_norm(x) for x in v)
    return v


def around(x: float, y: float, r_m: float) -> tuple:
    """A reach box (units): the square r_m metres either side of a point."""
    r = r_m * su.UNITS_PER_METRE
    return x - r, y - r, x + r, y + r


def along(x: float, y: float, heading: float, length_m: float, r_m: float) -> tuple:
    """A reach box over the line from a point along `heading` (degrees, Skyrim bearing) for length_m, r_m either side."""
    a, L = math.radians(heading), length_m * su.UNITS_PER_METRE
    ex, ey = x + math.sin(a) * L, y + math.cos(a) * L
    r = r_m * su.UNITS_PER_METRE
    return min(x, ex) - r, min(y, ey) - r, max(x, ex) + r, max(y, ey) + r


def memo(name: str, skip: tuple = (), dec=None, enc=None, reach=None):
    """Cache a measure `f(b, *args)` on the real build only (a Build made from fixtures is never cached). `dec`/`enc`
    turn a result into JSON-able data and back where it is not plain (tuples, tuple-keyed dicts). `skip` names
    arguments the measure does not read. `reach(*args)` (the measure's arguments, defaults applied) gives the box in
    units the measure reads (`around`, `along`): its key is the content of those cells; without it, the whole build's.
    The whole store is read into memory on first use (a lookup is a dict hit)."""
    def deco(f):
        sig = inspect.signature(f)
        names = list(sig.parameters)[1:]
        skip_i = {names.index(k) for k in skip}
        defaults = tuple(p.default for p in list(sig.parameters.values())[1:])

        @functools.wraps(f)
        def wrapper(b, *args, **kw):
            if not getattr(b, "real", False):
                return f(b, *args, **kw)
            if reach is None:
                if _state["gkey"] is None:
                    _state["gkey"] = build_key()
                lk = _state["gkey"]
            else:
                if kw:
                    ba = sig.bind(b, *args, **kw)
                    ba.apply_defaults()
                    full = ba.args[1:]
                else:   # the common call: positional, the rest from the defaults
                    full = args + defaults[len(args):]
                lk = local_key(*reach(*full))
            k = lk + "|" + repr((name, _norm(tuple(a for i, a in enumerate(args) if i not in skip_i)),
                                 sorted((n, _norm(v)) for n, v in kw.items() if n not in skip)))
            mem, db = _open()
            hit = mem.get(k)
            today = int(time.time() // 86400)
            if hit is not None:
                _state["hit"] += 1
                if _state["seen"].get(k, today) < today:
                    _state["seen"][k] = today
                    db.execute("UPDATE m SET d = ? WHERE k = ?", (today, k))
                r = json.loads(hit)
                return dec(r) if dec else r
            _state["miss"] += 1
            res = f(b, *args, **kw)
            txt = json.dumps(enc(res) if enc else res)
            mem[k] = txt
            _state["seen"][k] = today
            db.execute("INSERT OR IGNORE INTO m VALUES (?, ?, ?)", (k, txt, today))
            return res
        wrapper.__wrapped_measure__ = f
        return wrapper
    return deco
