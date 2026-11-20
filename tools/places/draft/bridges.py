"""Walkway pieces laid over the water a street must cross: one rule for the whole draft and the streets stage."""
from __future__ import annotations

import math

from tools.places.check import WADE
from tools.places.draft import geom, io, overlap
from tools.places.draft import paths as paths_mod
from tools.places.seat import seat_z

DECK_OVER = 16.0         # a laid bridge's deck stands this far over the water under it
DECK_LIFT = 24.0         # the most a bridge deck is lifted over a drowned thing under it
STEP = 32.0              # units between the route's samples tested for water


def deep(G, x: float, y: float) -> bool:
    """Water one cannot wade (check.WADE, the one depth rule of the build and the draft check)."""
    return G.wet(x, y, WADE)


def over(place_id: str, route: list, k: int | str, walk_base: str, bases: dict, G, rows: list[dict]) -> list[dict]:
    """Walkway pieces of `walk_base` end to end over each stretch of `route` deeper than a wade, walked along it by
    length (one piece per piece length, never one per route step), standing on stilts; a piece that would stand in
    or round a solid already there (`rows`: a dock, a pier) is left out: that solid carries the street there.
    `k` is the street's index (its id's number less one), or the id's last part for a door's path (`path.add.<door>`)."""
    length, turn = paths_mod.deck_run(bases[walk_base])
    foot = geom.foot({"base": walk_base, "kind": "building"}, bases)
    deck = geom.walk(bases[walk_base]) or 0.0   # the deck under its posts, from the mesh
    cum = [0.0]
    for p, q in zip(route, route[1:]):
        cum.append(cum[-1] + geom.dist(p, q))

    def at(d):
        d = max(0.0, min(cum[-1], d))
        for i in range(1, len(cum)):
            if cum[i] >= d:
                t = (d - cum[i - 1]) / ((cum[i] - cum[i - 1]) or 1.0)
                p, q = route[i - 1], route[i]
                return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)
        return tuple(route[-1][:2])
    runs, start = [], None
    n_s = int(cum[-1] // STEP) + 1
    for i in range(n_s + 1):
        d = min(i * STEP, cum[-1])
        w = deep(G, *at(d))
        if w and start is None:
            start = d
        if (not w or i == n_s) and start is not None:
            runs.append((start, d))
            start = None
    joined: list[tuple[float, float]] = []
    for d0, d1 in runs:   # a dry blink shorter than half a piece is still the one crossing
        if joined and d0 - joined[-1][1] < length / 2:
            joined[-1] = (joined[-1][0], d1)
        else:
            joined.append((d0, d1))
    out: list[dict] = []
    for ri, (d0, d1) in enumerate(joined):
        n = max(1, math.ceil((d1 - d0) / length))
        for j in range(n):
            m0 = d0 + (d1 - d0) * (j + 0.5) / n
            row = None
            # slid along the route (never off it) until it stands clear of every solid there
            for slide in [0.0] + [sgn * kk * 32.0 for kk in range(1, int(length // 64) + 1) for sgn in (1, -1)]:
                m = m0 + slide
                p, q = at(m - length / 2), at(m + length / 2)
                x, y = at(m)
                yaw = (math.atan2(q[0] - p[0], q[1] - p[1]) + turn) % (2 * math.pi)
                cand = {"id": io.mint(place_id, "bridge", str(k), str(ri), str(j)), "base": walk_base,
                        "kind": "building", "pos": [round(x, 2), round(y, 2), 0.0],
                        "rot": [0.0, 0.0, round(yaw, 5)], "scale": 1.0, "layer": "place", "flags": [],
                        "src": None, "walk": deck,
                        "seat": {"mode": "stilts", "dz": round(DECK_OVER - deck, 1), "foot": foot},
                        "why": f"carries street {f'{k + 1:02d}' if isinstance(k, int) else k} over our water, which parts what the source's land "
                               f"joined"}
                near = [o for o in rows + out if o.get("kind") in overlap.SOLID and not o.get("removed")
                        and geom.dist(o["pos"], cand["pos"]) < length * 2 + 2048]
                cand["pos"][2] = seat_z(cand, G)    # by height too: a deck over a drowned mound is clear of it
                under = [o for o in near if overlap.inside(cand["pos"], o, bases)]
                lift = max((o["pos"][2] + overlap.box(o, bases)[1][2] + 2 - cand["pos"][2] for o in under),
                           default=0.0)
                if 0 < lift <= DECK_LIFT:   # a deck lifted a hand's breadth over a low thing just under it
                    cand["seat"]["dz"] = round(cand["seat"]["dz"] + lift, 1)
                    cand["pos"][2] = seat_z(cand, G)
                if not any(overlap.inside(cand["pos"], o, bases) or overlap.inside(o["pos"], cand, bases)
                           for o in near):
                    row = cand
                    break
            if row is not None:
                out.append(row)
    return out


def streets(place_id: str, paths: list[dict], rows: list[dict], bases: dict, G, walk_base: str | None,
            log=print) -> list[dict]:
    """The pieces the streets stage lays: over each street's stretch deeper than a wade that no walked-on piece
    (`paths.walked`) already carries, walkway pieces of the place's own `walk_base`. Pieces already laid for a street
    (by id) are not laid again. Returns the new rows."""
    if not walk_base:
        return []
    walk = [r for r in rows if not r.get("removed") and paths_mod.walked(bases.get(r["base"]))]
    have = {r["id"] for r in rows}
    new: list[dict] = []
    for p in paths:
        pts = p.get("points") or []
        bare = False
        for a, b in zip(pts, pts[1:]):
            n = max(1, int(math.dist(a[:2], b[:2]) // 64))
            for i in range(n + 1):
                x, y = a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n
                if deep(G, x, y) and not any(geom.contains_xy(r, bases, x, y, 96) for r in walk):
                    bare = True
                    break
            if bare:
                break
        if not bare:
            continue
        tail = str(p["id"]).rsplit(".", 1)[-1]
        k = int(tail) - 1 if tail.isdigit() else tail
        got = [r for r in over(place_id, pts, k, walk_base, bases, G, rows + new) if r["id"] not in have]
        got = [r for r in got if not any(geom.contains_xy(w, bases, r["pos"][0], r["pos"][1]) for w in walk)]
        if got:
            log(f"street {p['id']}: {len(got)} walkway pieces of {walk_base} over water deeper than a wade")
            new += got
            have |= {r["id"] for r in got}
    return new
