"""Overlap: one placed thing standing inside another, by the build's own rule and geometry (tools/places/check.py
`overlap_pairs` and `obb_contains`: a solid's origin within OVERLAP_SHRINK of another solid's record box under its
full three-axis rotation, unless the source had the pair in that pose). This module only feeds the drafter's rows
(bounds from its bundle) to those functions and moves clusters apart; it has no geometry of its own for the test."""
from __future__ import annotations

import math
from collections import defaultdict

from tools.places import check as C

SOLID = C.SOLID
SHRINK = C.OVERLAP_SHRINK
CELL = 1024.0


def box(ref: dict, bases: dict) -> list | None:
    """The record bounds [[x0, y0, z0], [x1, y1, z1]] the build tests, scaled."""
    b = (bases.get(ref.get("base")) or {}).get("bounds")
    if not b:
        return None
    s = float(ref.get("scale") or 1.0)
    return [[v * s for v in b[0]], [v * s for v in b[1]]]


def thing(ref: dict, bases: dict) -> dict:
    """A row as the build's check sees it: its base's record bounds beside its pose."""
    b = (bases.get(ref.get("base")) or {}).get("bounds")
    return {**ref, "space": ref.get("space", "exterior"), "rot": ref.get("rot") or [0, 0, 0],
            "bounds": list(b[0]) + list(b[1]) if b else None}


def inside(p, ref: dict, bases: dict, z: bool = True, pad: float = 0.0) -> bool:
    """Whether point p stands inside ref's record box, by the build's `obb_contains`. `pad` widens it in plan."""
    return C.obb_contains(thing(ref, bases), p, SHRINK, pad, z)


def _reach(ref: dict, bases: dict) -> float:
    b = box(ref, bases)
    if not b:
        return 0.0
    return math.sqrt(sum(max(abs(b[0][i]), abs(b[1][i])) ** 2 for i in range(3)))


source_had = C._source_had


def hits(row: dict, near: list[dict], bases: dict) -> list[dict]:
    """The solids of `near` that `row` stands inside or that stand inside it, by the build's own rule (`check`'s
    overlap test and its exemptions: what rests on its carrier, what the source had so)."""
    a = thing(row, bases)
    reach = _reach(row, bases)
    out = []
    for o in near:
        if o is row or o["id"] == row["id"] or math.dist(o["pos"][:2], row["pos"][:2]) > reach + _reach(o, bases):
            continue
        b = thing(o, bases)
        if (C.obb_contains(b, a["pos"], SHRINK) or C.obb_contains(a, b["pos"], SHRINK)) and not C._source_had(a, b):
            out.append(o)
    return out


def pairs(refs: list[dict], bases: dict, z: bool = True, pad: float = 0.0) -> list[tuple[dict, dict]]:
    """Every (a, b) the build's check would report: a's origin inside b's box, the source not having them so."""
    things = [thing(r, bases) for r in refs]
    back = {id(t): r for t, r in zip(things, refs)}
    return [(back[id(a)], back[id(b)]) for a, b in C.overlap_pairs(things, pad, z)]


def foot_hits(a: dict, b: dict, bases: dict, pad: float = 0.0) -> bool:
    """Whether two things' plan boxes (record bounds, unshrunk, widened by pad) intersect: a separating-axis test."""
    ba, bb = box(a, bases), box(b, bases)
    if not ba or not bb:
        return False

    def corners(r, bx):
        rz = (r.get("rot") or [0, 0, 0])[2]
        c, s = math.cos(rz), math.sin(rz)
        pts = []
        for u in (bx[0][0] - pad, bx[1][0] + pad):
            for v in (bx[0][1] - pad, bx[1][1] + pad):
                pts.append((r["pos"][0] + u * c + v * s, r["pos"][1] - u * s + v * c))
        return pts, [(c, -s), (s, c)]
    pa, axa = corners(a, ba)
    pb, axb = corners(b, bb)
    for ax in axa + axb:
        la = [p[0] * ax[0] + p[1] * ax[1] for p in pa]
        lb = [p[0] * ax[0] + p[1] * ax[1] for p in pb]
        if max(la) < min(lb) or max(lb) < min(la):
            return False
    return True


class Grid:
    """Solids bucketed by cell for the origin-in-box test. A solid that moves is taken out and put back (`move`)."""

    def __init__(self, refs: list[dict], bases: dict):
        self.bases = bases
        self.cells: dict[tuple[int, int], list[dict]] = defaultdict(list)
        self.keys: dict[int, list[tuple[int, int]]] = {}
        for b in refs:
            self.add(b)

    def add(self, b: dict) -> None:
        rad = _reach(b, self.bases)
        if rad <= 0:
            return
        x, y = b["pos"][0], b["pos"][1]
        keys = [(i, j) for i in range(math.floor((x - rad) / CELL), math.floor((x + rad) / CELL) + 1)
                for j in range(math.floor((y - rad) / CELL), math.floor((y + rad) / CELL) + 1)]
        for k in keys:
            self.cells[k].append(b)
        self.keys[id(b)] = keys

    def remove(self, b: dict) -> None:
        for k in self.keys.pop(id(b), ()):
            self.cells[k] = [o for o in self.cells[k] if o is not b]

    def move(self, b: dict) -> None:
        """Re-bucket b after its position changed."""
        if id(b) in self.keys:
            self.remove(b)
            self.add(b)

    def near(self, p) -> list[dict]:
        return self.cells.get((math.floor(p[0] / CELL), math.floor(p[1] / CELL)), [])

    def hits(self, rows: list[dict], z: bool = True, skip=()) -> int:
        """How many of rows stand in a solid of the grid, or have one standing in them; the solids in `skip` (the
        rows' own originals) left out."""
        out = {id(b) for b in skip}
        n = 0
        for a in rows:
            if any(inside(a["pos"], b, self.bases, z) for b in self.near(a["pos"]) if id(b) not in out):
                n += 1
        others = {id(b): b for a in rows for b in self.near(a["pos"]) if id(b) not in out}
        for b in others.values():
            if any(inside(b["pos"], a, self.bases, z) for a in rows):
                n += 1
        return n


SHIFTS = [(r * math.sin(j * math.pi / 8), r * math.cos(j * math.pi / 8))
          for r in (32.0, 64.0, 96.0, 128.0, 192.0, 256.0, 384.0, 512.0, 768.0, 1024.0, 1280.0) for j in range(16)]


def separate(sc, fit, clusters, by_src: dict, bases: dict, base_of, rounds: int = 64) -> list[dict]:
    """The fit's last pass: no piece of one cluster may stand in a piece of another (the build's rule, by record box).
    Each clash is resolved by moving the smaller cluster the least distance that clears it without landing it on
    water or in a third cluster; returns the moves made (and any clash left, which `draft check` then lists)."""
    cl = {c.id: c for c in clusters}

    def placed(c, xf) -> list[dict]:
        out = []
        for rid in c.members:
            r = by_src.get(rid)
            if not r or r.get("kind") not in SOLID:
                continue
            x, y = xf.pt(r["pos"][0], r["pos"][1])
            rot = xf.rot3(r.get("rot"))
            out.append({"id": rid, "base": base_of(r), "kind": r["kind"], "pos": [x, y, r["pos"][2]], "rot": rot,
                        "scale": r.get("scale") or 1.0, "cluster": c.id, "src": rid})
        return out

    def size(c) -> float:
        return sum((b[1][0] - b[0][0]) * (b[1][1] - b[0][1]) for r in placed(c, fit.per[c.id])
                   if (b := box(r, bases)))
    moves: list[dict] = []
    tried: set = set()
    for _ in range(rounds):
        allp = [p for c in clusters for p in placed(c, fit.per[c.id])]
        clash = pairs(allp, bases, z=False)
        if not clash:
            break
        progress = False
        for a, b in clash:
            ca, cb = cl[a["cluster"]], cl[b["cluster"]]
            if (ca.id, cb.id) in tried:
                continue
            tried.add((ca.id, cb.id))
            for m in sorted((ca, cb), key=lambda c: (c.kind == "landing", size(c))):
                grid = Grid([p for p in allp if p["cluster"] != m.id], bases)
                cur = fit.per[m.id]
                if grid.hits(placed(m, cur), z=False) == 0:
                    break
                misses = sc.misses(m, cur)
                about = cur.pt(*m.centre)
                best = None
                for dx, dy in SHIFTS:
                    cand = cur.then(dx, dy, 0.0, about)
                    if grid.hits(placed(m, cand), z=False) or sc.misses(m, cand) > misses:
                        continue
                    k = math.hypot(dx, dy)
                    if best is None or k < best[0] - 1e-6:
                        best = (k, cand, dx, dy)
                    elif k > best[0] + 1e-6:
                        break
                if best:
                    fit.per[m.id] = best[1]
                    moves.append({"cluster": m.id, "dx": round(best[2], 1), "dy": round(best[3], 1),
                                  "clear_of": (cb if m is ca else ca).id})
                    progress = True
                    tried.clear()
                    break
            if progress:
                break
        if not progress:
            break
    # a clash no cluster step clears: the smaller piece of the pair gives way (left out, with the reason)
    allp = [p for c in clusters for p in placed(c, fit.per[c.id])]
    gone: set = set()
    for a, b in pairs(allp, bases, z=False):
        if a["id"] in gone or b["id"] in gone:
            continue
        area = {r["id"]: ((bx[1][0] - bx[0][0]) * (bx[1][1] - bx[0][1]) if (bx := box(r, bases)) else 0.0)
                for r in (a, b)}
        small, big = (a, b) if area[a["id"]] <= area[b["id"]] else (b, a)
        if by_src.get(small["id"], {}).get("kind") not in ("static", "rock", "activator", "furniture", "container"):
            small, big = big, small
        gone.add(small["id"])
        moves.append({"drop": small["id"], "why": f"stood in {big['id']} once the clusters were fitted, with no step "
                                                  f"of either cluster clear"})
    return moves
