"""A place's ground paint (`paint.jsonl`): the owner's and the agents' strokes of land texture, read into weights on
the land's own vertex lattice (one vertex every 128 units, 33 a cell edge), the resolution the engine paints at.

One row is one stroke, applied in id order (`paint.0001`, `paint.0002`, ...), each over what the strokes before it
left:

    {"id": "paint.0003", "texture": "<land texture key>", "brush": "soft" | "hard" | "scatter",
     "size": <radius, units>, "softness": 0..1, "strength": 0..1, "seed": <int, scatter only>,
     "points": [[x, y, pressure], ...]          # a stroke (one point: a dab, a circle of `size`)
     | "polygon": [[x, y], ...],                # or an area, its edge feathered over `size` * `softness`
     "erase": true,                             # an eraser: takes earlier paint away (no texture)
     "by": "owner" | "agent", "why": "..."}

A stroke's cover at a vertex: its brush's falloff at the distance from the stroke's line over the radius there
(`size` times PMIN + (1 - PMIN) pressure, the pressure interpolated along each segment), times `strength` and times
OP_MIN + (1 - OP_MIN) pressure; a hard brush is full to its radius, a soft one falls away over its outer `softness`
(a smoothstep); a scatter brush is a soft one broken by value noise (SCATTER_SCALE vertices, its `seed`). Painting a
texture at cover a: every weight under it times (1 - a), the texture's plus a, the paint's total p becomes
p (1 - a) + a. Erasing at a: every weight and the total times (1 - a), so the world's own paint (and a path's) shows
again where the paint is gone. Pure and deterministic; the studio's paint_rule.js is the same rule, tested against
numbers this module wrote (tools/places/studio/web/test/paint_rule.json).

The place build (build.py plan_paths) lays the painted weights over the world's composite and the paths' in every
quadrant they reach, under the engine's six textures a quadrant.
"""
from __future__ import annotations

import math

import numpy as np

CELL, VERTS, STEP = 4096, 33, 128
BRUSHES = ("soft", "hard", "scatter")
PMIN = 0.35            # a stroke's radius at no pressure, as a share of its size
OP_MIN = 0.5           # its opacity at no pressure, as a share of its strength
SCATTER_SCALE = 1.6    # the scatter brush's noise lattice, in vertices
SCATTER_CUT = (0.3, 0.75)  # noise values (0..1) mapped to nothing .. full cover
MAX_POINTS = 4000


class PaintError(ValueError):
    """A paint row that cannot be read."""


def _num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def check_row(row: dict) -> None:
    """Raise PaintError naming what is wrong with one paint row."""
    rid = row.get("id")
    if not isinstance(rid, str) or not rid:
        raise PaintError("a paint row needs an id")
    erase = bool(row.get("erase"))
    if not erase and not (isinstance(row.get("texture"), str) and ":" in row["texture"]):
        raise PaintError(f"{rid}: a paint row names its land texture by key (plugin:formid), or is an eraser")
    if row.get("brush", "soft") not in BRUSHES:
        raise PaintError(f"{rid}: brush must be one of {', '.join(BRUSHES)}")
    for k, lo, hi in (("size", 1, 65536), ("softness", 0, 1), ("strength", 0, 1)):
        if k in row and not (_num(row[k]) and lo <= row[k] <= hi):
            raise PaintError(f"{rid}: {k} must be a number from {lo} to {hi}")
    pts, poly = row.get("points"), row.get("polygon")
    if (pts is None) == (poly is None):
        raise PaintError(f"{rid}: a paint row has either points (a stroke) or a polygon (an area)")
    if pts is not None:
        if not (isinstance(pts, list) and 1 <= len(pts) <= MAX_POINTS and all(
                isinstance(p, list) and len(p) in (2, 3) and all(_num(v) for v in p) for p in pts)):
            raise PaintError(f"{rid}: points are 1 to {MAX_POINTS} [x, y, pressure] triples")
    else:
        if not (isinstance(poly, list) and 3 <= len(poly) <= MAX_POINTS and all(
                isinstance(p, list) and len(p) >= 2 and all(_num(v) for v in p[:2]) for p in poly)):
            raise PaintError(f"{rid}: a polygon is at least three [x, y] points")


def bounds(row: dict) -> tuple[float, float, float, float]:
    """The box a row can reach (x0, y0, x1, y1)."""
    pts = np.asarray([p[:2] for p in (row.get("points") or row.get("polygon"))], float)
    pad = float(row.get("size", 256))
    return float(pts[:, 0].min() - pad), float(pts[:, 1].min() - pad), float(pts[:, 0].max() + pad), float(pts[:, 1].max() + pad)


def cells_of(rows: list[dict]) -> set[tuple[int, int]]:
    """Every cell a row reaches."""
    out = set()
    for r in rows:
        x0, y0, x1, y1 = bounds(r)
        for cx in range(math.floor(x0 / CELL), math.floor(x1 / CELL) + 1):
            for cy in range(math.floor(y0 / CELL), math.floor(y1 / CELL) + 1):
                out.add((cx, cy))
    return out


def _smooth(s):
    s = np.clip(s, 0.0, 1.0)
    return s * s * (3 - 2 * s)


def falloff(t, softness: float):
    """A brush's cover at t (distance over radius): 1 inside 1 - softness, a smoothstep to 0 at 1."""
    t = np.asarray(t, float)
    if softness <= 1e-6:
        return (t <= 1.0).astype(float)
    return _smooth((1.0 - t) / softness)


def scatter(gx, gy, seed: int):
    """The scatter brush's mask (0..1) at world vertex (gx, gy): value noise cut to patches."""
    from tools.newworld.world.texture import vnoise
    n = np.clip(0.5 + 0.25 * vnoise(int(seed), np.asarray(gy, float), np.asarray(gx, float), SCATTER_SCALE), 0.0, 1.0)
    lo, hi = SCATTER_CUT
    return np.clip((n - lo) / (hi - lo), 0.0, 1.0)


def cover(row: dict, X: np.ndarray, Y: np.ndarray) -> np.ndarray:
    """One row's cover (0..1) at points X, Y (world units)."""
    size = float(row.get("size", 256))
    soft = float(row.get("softness", 0.0 if row.get("brush") == "hard" else 0.6))
    strength = float(row.get("strength", 1.0))
    if row.get("polygon") is not None:
        poly = np.asarray([p[:2] for p in row["polygon"]], float)
        inside = np.zeros(X.shape, bool)
        d = np.full(X.shape, np.inf)
        for a, b in zip(poly, np.roll(poly, -1, axis=0)):
            inside ^= ((a[1] > Y) != (b[1] > Y)) & (X < (b[0] - a[0]) * (Y - a[1]) / ((b[1] - a[1]) or 1e-12) + a[0])
            d = np.minimum(d, _seg(X, Y, a, b)[0])
        feather = size * soft
        v = inside.astype(float) if feather <= 1e-6 else np.where(inside, _smooth(d / feather), 0.0)
        p = np.ones(X.shape)
    else:
        pts = np.asarray([list(p[:2]) + [p[2] if len(p) > 2 else 1.0] for p in row["points"]], float)
        pts[:, 2] = np.clip(pts[:, 2], 0, 1)
        v, p = np.zeros(X.shape), np.zeros(X.shape)
        segs = list(zip(pts[:-1], pts[1:])) or [(pts[0], pts[0])]
        for a, b in segs:
            d, t = _seg(X, Y, a, b)
            pr = a[2] + (b[2] - a[2]) * t
            r = size * (PMIN + (1 - PMIN) * pr)
            f = falloff(d / np.maximum(r, 1e-6), soft)
            take = f > v
            v = np.where(take, f, v)
            p = np.where(take, pr, p)
    if row.get("brush") == "scatter":
        v = v * scatter(np.round(X / STEP), np.round(Y / STEP), int(row.get("seed", 0)))
    return np.clip(v * strength * (OP_MIN + (1 - OP_MIN) * p), 0.0, 1.0)


def _seg(X, Y, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = dx * dx + dy * dy
    t = np.clip(((X - a[0]) * dx + (Y - a[1]) * dy) / L, 0, 1) if L else np.zeros(X.shape)
    return np.hypot(X - (a[0] + t * dx), Y - (a[1] + t * dy)), t


def ordered(rows: list[dict]) -> list[dict]:
    return sorted(rows, key=lambda r: r["id"])


def cell_paint(rows: list[dict], cell: tuple[int, int]) -> tuple[np.ndarray, dict[str, np.ndarray]] | None:
    """The paint of one cell: (total [33, 33], {texture key: weight [33, 33]}), rows from the south; None when no
    row reaches it."""
    cx, cy = cell
    gx = cx * CELL + np.arange(VERTS) * STEP
    gy = cy * CELL + np.arange(VERTS) * STEP
    X, Y = np.meshgrid(gx.astype(float), gy.astype(float))
    P, W, any_ = np.zeros(X.shape), {}, False
    for r in ordered(rows):
        x0, y0, x1, y1 = bounds(r)
        if x1 < gx[0] or x0 > gx[-1] or y1 < gy[0] or y0 > gy[-1]:
            continue
        a = cover(r, X, Y)
        if not (a > 1e-4).any():
            continue
        any_ = True
        for k in W:
            W[k] = W[k] * (1 - a)
        if r.get("erase"):
            P = P * (1 - a)
        else:
            W[r["texture"]] = W.get(r["texture"], np.zeros(X.shape)) + a
            P = P * (1 - a) + a
    if not any_:
        return None
    return P, {k: v for k, v in W.items() if v.max() > 1e-4}


def plan(rows: list[dict]) -> dict[tuple[int, int], tuple[np.ndarray, dict[str, np.ndarray]]]:
    """Every painted cell -> its paint (cell_paint)."""
    out = {}
    for c in sorted(cells_of(rows)):
        got = cell_paint(rows, c)
        if got is not None and got[0].max() > 1e-4:
            out[c] = got
    return out


def next_id(rows: list[dict]) -> str:
    n = max((int(r["id"].split(".")[-1]) for r in rows if r.get("id", "").split(".")[-1].isdigit()), default=0)
    return f"paint.{n + 1:04d}"
