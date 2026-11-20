"""Seeing past trees: which pieces are canopy (a tree's crown, a Hist, hanging moss and vines; never roots), the
height over the subject's ground the canopy is cut at, and how much of a subject the canopy hides from a camera
(rays through the subject's points, first hit by pick's own box test). Pure numbers; the page cuts the canopy
(agent.js canopyCut) by the same names."""
from __future__ import annotations

import re

import numpy as np

from tools.places.look import geom

CANOPY = re.compile(r"tree|hist|canopy|moss|vine|willow|mangrove|palm|fern|hanging|leaves|branch", re.I)
ROOTS = re.compile(r"root|stump|log", re.I)
HEAD = 250.0        # cut this far over the subject's ground: over a person's head, under every crown


def is_canopy(p: dict) -> bool:
    """A piece whose crown the canopy cut takes away (the same names the page cuts)."""
    name = f"{p.get('edid') or ''} {p.get('model') or ''}"
    return (p.get("kind") == "tree" or bool(CANOPY.search(name))) and not ROOTS.search(str(p.get("edid") or ""))


def cut_height(ground_z: float) -> float:
    return float(ground_z) + HEAD


def subject_points(pieces: list[dict], n: int = 48) -> np.ndarray:
    """Points on the subject to look for: each piece's top middle and its box's upper corners, at most n."""
    pts = []
    for p in pieces:
        lo, hi = geom.aabb(p)
        pts.append([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, hi[2] - 4])
        for x in (lo[0] + 8, hi[0] - 8):
            for y in (lo[1] + 8, hi[1] - 8):
                pts.append([x, y, hi[2] - 4])
    P = np.asarray(pts, float).reshape(-1, 3)
    if len(P) > n:
        P = P[np.linspace(0, len(P) - 1, n).astype(int)]
    return P


def hidden(cam: dict, subject: list[dict], everything: list[dict]) -> dict:
    """How much of the subject the canopy hides from cam: of the subject's points in frame, the share whose ray from
    the camera first meets a canopy piece that is not the subject's own. Returns {seen, hidden, frac, by}."""
    own = {p["id"] for p in subject}
    canopy = [p for p in everything if p["id"] not in own and is_canopy(p) and p.get("model")]
    if not subject or not canopy:
        return {"seen": 0, "hidden": 0, "frac": 0.0, "by": []}
    P = subject_points(subject)
    pp = geom.project(cam, P)
    o = np.asarray(cam["pos"], float)
    n = h = 0
    by: dict[str, int] = {}
    for q, xy in zip(P, pp):
        if xy[2] <= 0 or not (0 <= xy[0] <= cam["w"] and 0 <= xy[1] <= cam["h"]):
            continue
        n += 1
        d = q - o
        dist = float(np.linalg.norm(d))
        d = d / max(dist, 1e-9)
        best = None
        for c in canopy:
            t = geom.ray_box(o, d, c)
            if t is not None and 0 < t < dist - 16 and (best is None or t < best[0]):
                best = (t, c)
        if best:
            h += 1
            by[best[1].get("edid") or best[1]["id"]] = by.get(best[1].get("edid") or best[1]["id"], 0) + 1
    return {"seen": n, "hidden": h, "frac": round(h / n, 2) if n else 0.0,
            "by": sorted(by, key=lambda k: -by[k])[:5]}
