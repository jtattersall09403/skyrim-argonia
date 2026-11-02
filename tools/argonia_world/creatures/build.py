"""Run the planner over a set of province cells and write out/creatures/spawns.jsonl (+ summary.json).

Inputs: Sources.load()'s ground (terrain/grid.py), water/solve.py's cell water, cell_region_run, the places'
positions, classes and danger tiers. Output lines are place.plan_cell's refs (ArgoniaGen's reader turns them into
ACHR under the cell, base the list's NPC_ template or the den creature's form, XEZN the zone).
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.creatures import place as pl


def cell_classes(w) -> dict[tuple[int, int], str]:
    out = {}
    for r in w.query("SELECT * FROM cell_region_run"):
        cls = r["land_region_id"].split(".")[-1]
        for cx in range(r["cx0"], r["cx1"] + 1):
            out[(cx, r["cy"])] = cls
    return out


def places(w) -> list[tuple[float, float, str, str]]:
    """(x units, y units, no-spawn radius m, band) of every positioned place."""
    rad = {r["place_class"]: r["radius_m"] for r in w.query("SELECT * FROM place_no_spawn")}
    out = []
    for r in w.query("SELECT position_m_x, position_m_y, classification_class, danger_tier FROM place "
                     "WHERE position_m_x IS NOT NULL"):
        x, y = su.province_to_skyrim(r["position_m_x"], r["position_m_y"])
        band = r["danger_tier"] if r["danger_tier"] and r["danger_tier"] != "D0" else "D1"
        out.append((x, y, rad.get(r["classification_class"], 40.0), band))
    return out


NEAREST = 5  # places whose most common danger tier is a wild cell's band
WILD_TOP = "D4"  # D5 rows are hand-authored set pieces, never ambient (74-ecology rule 2)


def wild_band(P: np.ndarray, B: list[str], cx: int, cy: int) -> str:
    """A wild cell's band: the most common tier of its NEAREST places (ties to the lower), at most WILD_TOP. A
    single dungeon does not make its whole surround D5; the stretch takes its neighbourhood's band (74-ecology
    rule 1: a route takes its region band)."""
    d = np.hypot(P[:, 0] - (cx + .5) * su.CELL_UNITS, P[:, 1] - (cy + .5) * su.CELL_UNITS)
    near = [B[i] for i in np.argsort(d)[:NEAREST]]
    best = sorted(set(near), key=lambda b: (-near.count(b), b))[0]
    return min(best, WILD_TOP)


def blocked_mask(cx: int, cy: int, P: np.ndarray, R: np.ndarray) -> np.ndarray:
    ii, jj = np.mgrid[0:su.QUADS_PER_CELL + 1, 0:su.QUADS_PER_CELL + 1]
    x, y = pl.vertex_xy(cx, cy, ii, jj)
    m = np.zeros(ii.shape, bool)
    cxu, cyu = (cx + .5) * su.CELL_UNITS, (cy + .5) * su.CELL_UNITS
    near = np.hypot(P[:, 0] - cxu, P[:, 1] - cyu) < R * su.UNITS_PER_METRE + su.CELL_UNITS
    for (px, py), r in zip(P[near], R[near]):
        m |= np.hypot(x - px, y - py) < r * su.UNITS_PER_METRE
    return m


def stems(veg: Path | None) -> dict[tuple[int, int], np.ndarray] | None:
    """The vegetation's stems per cell (x, y units) from its shards (vegetation/build.py), or None."""
    if veg is None or not any(veg.glob("cy*.jsonl.gz")):
        return None
    from tools.argonia_world.vegetation import build as vb
    return {(c["x"], c["y"]): np.array([[r[2], r[3]] for r in c["refs"]], np.float32).reshape(-1, 2)
            for c in vb.read_cells(veg)}


def run(w, src, cw, cells: list[tuple[int, int]], out: Path | None = None, log=print, veg: Path | None = None,
        cache: Path | None = None) -> dict:
    """`cache`: the directory whose _rows/ keeps each row's plans by content key (row_key); None plans every row."""
    t0 = time.time()
    st = stems(veg)
    rules = pl.load_rules(w)
    cls = cell_classes(w)
    pp = places(w)
    P = np.array([(p[0], p[1]) for p in pp])
    R = np.array([p[2] for p in pp])
    B = [p[3] for p in pp]
    refs, skipped, reused = [], 0, 0
    rows: dict[int, list[tuple[int, int]]] = {}
    for cx, cy in cells:
        rows.setdefault(cy, []).append((cx, cy))
    code = _code_stamp() + repr(rules)
    for cy, row in rows.items():  # one cached row of plans per content key (1.15 build speed)
        args = []
        for cx, _ in row:
            c = cls.get((cx, cy))
            if c is None or c == "border" or not src.in_province(cx, cy):
                skipped += 1
                continue
            band = wild_band(P, B, cx, cy)
            r0, r1 = src.cell_rows(cy)
            c0, c1 = src.cell_cols(cx)
            h = src.heights(r0, r1 + 1, c0, c1 + 1)
            lv = cw.level(cx, cy)
            level = lv if lv is not None else cw.nearest_level(cx, cy)
            cov = None if st is None else pl.cover_counts(cx, cy, st.get((cx, cy), np.zeros((0, 2), np.float32)))
            args.append((cx, cy, h, level, c, band, blocked_mask(cx, cy, P, R), cov))
        key = row_key(code, args)
        got = load_row(cache, cy, key) if cache else None
        if got is None:
            got = [r for cx, cy_, h, level, c, band, m, cov in args
                   for r in pl.plan_cell(cx, cy_, h, level, c, band, rules, m, cov)]
            if cache:
                save_row(cache, cy, key, got)
        else:
            reused += 1
        refs += got
    log(f"creatures: {reused} of {len(rows)} rows reused by key")
    summ = {"cells": len(cells), "skipped": skipped, "refs": len(refs),
            "by_kind": _count(refs, "kind"), "by_medium": _count(refs, "medium"), "by_band": _count(refs, "band"),
            "by_class": _count(refs, "class"), "by_cover": _count([r for r in refs if "cover" in r], "cover"),
            "seconds": round(time.time() - t0, 1)}
    if out:
        out.mkdir(parents=True, exist_ok=True)
        with (out / "spawns.jsonl").open("w") as f:
            for r in refs:
                f.write(json.dumps(r, sort_keys=True) + "\n")
        (out / "summary.json").write_text(json.dumps(summ, indent=1, sort_keys=True) + "\n")
    log(json.dumps(summ))
    return {"refs": refs, "summary": summ, "rules": rules, "places": (P, R)}


def _code_stamp() -> str:
    import hashlib
    h = hashlib.sha256()
    for f in sorted(Path(__file__).parent.glob("*.py")):
        h.update(f.name.encode() + f.read_bytes())
    return h.hexdigest()


def row_key(code: str, args) -> str:
    """A row's content stamp: the creature code and rules, and every cell's planner inputs (heights, level, class,
    band, blocked mask, cover counts)."""
    import hashlib
    h = hashlib.sha256(code.encode())
    for a in args:
        for v in a:
            if isinstance(v, np.ndarray):
                v = np.ascontiguousarray(v)
                h.update(f"a{v.shape}{v.dtype}".encode() + v.tobytes())
            else:
                h.update(f"v{v!r};".encode())
    return h.hexdigest()


def _row_path(out: Path, cy: int) -> Path:
    return out / "_rows" / f"{cy:+04d}.pkl"


def load_row(out: Path, cy: int, key: str):
    import pickle
    try:
        k, got = pickle.loads(_row_path(out, cy).read_bytes())
    except (OSError, EOFError, ValueError, pickle.UnpicklingError):
        return None
    return got if k == key else None


def save_row(out: Path, cy: int, key: str, got) -> None:
    import pickle
    p = _row_path(out, cy)
    p.parent.mkdir(parents=True, exist_ok=True)
    t = p.with_suffix(".part")
    t.write_bytes(pickle.dumps((key, got), protocol=pickle.HIGHEST_PROTOCOL))
    t.replace(p)


def _count(refs, k):
    d = {}
    for r in refs:
        d[r[k]] = d.get(r[k], 0) + 1
    return dict(sorted(d.items()))


def sample_cells(boxes) -> list[tuple[int, int]]:
    return [(x, y) for x0, y0, x1, y1 in boxes for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)]
