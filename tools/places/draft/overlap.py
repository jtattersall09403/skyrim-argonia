"""Overlap: one placed thing standing inside another, by the build's own rule (tools/places/check.py
`check_overlap`): a solid's origin within OVERLAP_SHRINK of another solid's record box, unless the source had the pair
in that pose (both copied and in one exterior cluster, or one seated on the other). The draft resolves every overlap it
makes before writing, and `draft check` runs the build's test itself on the place files."""
from __future__ import annotations

import math
from collections import defaultdict

SOLID = {"building", "static", "furniture", "container", "door", "activator", "rock"}
SHRINK = 0.8       # the build's OVERLAP_SHRINK
CELL = 1024.0


def box(ref: dict, bases: dict) -> list | None:
    """The record bounds [[x0, y0, z0], [x1, y1, z1]] the build tests, scaled."""
    b = (bases.get(ref.get("base")) or {}).get("bounds")
    if not b:
        return None
    s = float(ref.get("scale") or 1.0)
    return [[v * s for v in b[0]], [v * s for v in b[1]]]


def inside(p, ref: dict, bases: dict, z: bool = True, pad: float = 0.0) -> bool:
    """Whether point p stands inside ref's record box (shrunk in plan as the build shrinks it; the full height when
    z is tested). `pad` widens the box in plan (a margin for the drafter's own placements)."""
    b = box(ref, bases)
    if not b:
        return False
    rz = (ref.get("rot") or [0, 0, 0])[2]
    dx, dy = p[0] - ref["pos"][0], p[1] - ref["pos"][1]
    c, s = math.cos(rz), math.sin(rz)
    u, v = dx * c - dy * s, dx * s + dy * c
    cu, cv = (b[0][0] + b[1][0]) / 2, (b[0][1] + b[1][1]) / 2
    hu, hv = (b[1][0] - b[0][0]) / 2 * SHRINK + pad, (b[1][1] - b[0][1]) / 2 * SHRINK + pad
    if abs(u - cu) > hu or abs(v - cv) > hv:
        return False
    if not z or len(p) < 3:
        return True
    return ref["pos"][2] + b[0][2] <= p[2] <= ref["pos"][2] + b[1][2] + 1.0


def _reach(ref: dict, bases: dict) -> float:
    b = box(ref, bases)
    if not b:
        return 0.0
    return math.hypot(max(abs(b[0][0]), abs(b[1][0])), max(abs(b[0][1]), abs(b[1][1])))


def source_had(a: dict, b: dict) -> bool:
    """The build's exemption: seated one on the other, or both copied in one exterior cluster (moved as one)."""
    if (a.get("seat") or {}).get("on") == b.get("id") or (b.get("seat") or {}).get("on") == a.get("id"):
        return True
    return bool(a.get("src") and b.get("src") and a.get("cluster") is not None and a.get("cluster") == b.get("cluster"))


def pairs(refs: list[dict], bases: dict, z: bool = True, exempt=source_had, pad: float = 0.0) -> list[tuple[dict, dict]]:
    """Every (a, b): a's origin inside b's box, not exempt. Bucketed by cell so a town's thousands stay quick."""
    solid = [r for r in refs if r.get("kind") in SOLID]
    grid: dict[tuple[int, int], list[dict]] = defaultdict(list)
    for b in solid:
        rad = _reach(b, bases) + pad
        if rad <= 0:
            continue
        x, y = b["pos"][0], b["pos"][1]
        for i in range(math.floor((x - rad) / CELL), math.floor((x + rad) / CELL) + 1):
            for j in range(math.floor((y - rad) / CELL), math.floor((y + rad) / CELL) + 1):
                grid[(i, j)].append(b)
    out = []
    for a in solid:
        for b in grid.get((math.floor(a["pos"][0] / CELL), math.floor(a["pos"][1] / CELL)), ()):
            if a is b or a.get("id") == b.get("id"):
                continue
            if inside(a["pos"], b, bases, z, pad) and not exempt(a, b):
                out.append((a, b))
    return out


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
    """Solids bucketed by cell for the origin-in-box test."""

    def __init__(self, refs: list[dict], bases: dict):
        self.bases = bases
        self.cells: dict[tuple[int, int], list[dict]] = defaultdict(list)
        for b in refs:
            self.add(b)

    def add(self, b: dict) -> None:
        rad = _reach(b, self.bases)
        if rad <= 0:
            return
        x, y = b["pos"][0], b["pos"][1]
        for i in range(math.floor((x - rad) / CELL), math.floor((x + rad) / CELL) + 1):
            for j in range(math.floor((y - rad) / CELL), math.floor((y + rad) / CELL) + 1):
                self.cells[(i, j)].append(b)

    def near(self, p) -> list[dict]:
        return self.cells.get((math.floor(p[0] / CELL), math.floor(p[1] / CELL)), [])

    def hits(self, rows: list[dict], z: bool = True) -> int:
        """How many of rows stand in a solid of the grid, or have one standing in them."""
        n = 0
        for a in rows:
            if any(inside(a["pos"], b, self.bases, z) for b in self.near(a["pos"])):
                n += 1
        others = {id(b): b for a in rows for b in self.near(a["pos"])}
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
            rot = list(r.get("rot") or [0, 0, 0])
            rot[2] = xf.yaw(rot[2])
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
        clash = pairs(allp, bases, z=False, exempt=lambda a, b: a["cluster"] == b["cluster"])
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
    for a, b in pairs(allp, bases, z=False, exempt=lambda a, b: a["cluster"] == b["cluster"]):
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
