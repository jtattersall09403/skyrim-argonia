"""Routine reachability, off game: every person's stops each reachable from the one before, and each on walkable
ground or a piece of furniture.

Outside, one walks our ground (dry, or over a walkway or a deck piece; never through a building) and our streets
(one network, `draft check` 5). Inside, one walks the room the builder keeps: the island reached from the room's own
way out (`tools.places.build.room_partition`, read through `interiors.kept`). Between them, the door pair: a room is
reached from the streets by its door from outside (or its parent room's). So a stop outside is reached when a walk
over walkable ground joins it to a street; a stop inside when its thing is in the room's island (or is one we set on
the walked-in floor) and the room's door chain leads out to a door the streets reach."""
from __future__ import annotations

import math
from collections import deque

from tools.places.draft import geom, interiors, overlap
from tools.places.draft import paths as paths_mod

GRID = 64.0
SEARCH = 4096.0        # how far a stop may lie from the street it is walked to (across a camp)
FURNITURE = {"furniture", "container", "activator"}


class Outside:
    """Walkable cells of the exterior and the cells our streets cover."""

    def __init__(self, refs: list[dict], bases: dict, paths: list[dict], G):
        self.refs, self.bases, self.G = refs, bases, G
        self.walk = [r for r in refs if paths_mod.WALKWAY.search(str((bases.get(r["base"]) or {}).get("model", "")))
                     or "street" in str(r.get("why", ""))]
        walk_ids = {id(r) for r in self.walk}
        self.solid = [r for r in refs if r.get("kind") == "building" and id(r) not in walk_ids and geom.foot(r, bases)
                      and not geom.underfoot(r, bases, G)]
        self.street: set[tuple[int, int]] = set()
        for p in paths:
            pts, half = p["points"], p.get("width", paths_mod.STREET_WIDTH) / 2
            for a, b in zip(pts, pts[1:]):
                n = max(1, int(math.dist(a, b) // (GRID / 2)))
                for k in range(n + 1):
                    x, y = a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n
                    r = int(half // GRID)
                    for i in range(-r, r + 1):
                        for j in range(-r, r + 1):
                            self.street.add((round(x / GRID) + i, round(y / GRID) + j))
        self._ok: dict[tuple[int, int], bool] = {}

    def _near(self, x, y, rs, pad):
        return [r for r in rs if abs(r["pos"][0] - x) < geom.reach(r, self.bases) + pad
                and abs(r["pos"][1] - y) < geom.reach(r, self.bases) + pad]

    def walkable(self, x: float, y: float, skip: frozenset = frozenset()) -> bool:
        k = (round(x / GRID), round(y / GRID))
        if skip:
            return self.G.has(x, y) and not any(geom.contains_xy(r, self.bases, x, y, -16)
                                                for r in self._near(x, y, self.solid, 0) if r["id"] not in skip) \
                and self.walkable_ground(x, y)
        if k in self._ok:
            return self._ok[k]
        ok = True
        if not self.G.has(x, y):
            ok = False
        elif self.G.wet(x, y, 8) and not any(geom.contains_xy(r, self.bases, x, y, 48)
                                             for r in self._near(x, y, self.walk, 64)):
            ok = False
        elif any(geom.contains_xy(r, self.bases, x, y, -16) for r in self._near(x, y, self.solid, 0)):
            ok = False
        self._ok[k] = ok
        return ok

    def walkable_ground(self, x: float, y: float) -> bool:
        return not (self.G.wet(x, y, 8) and not any(geom.contains_xy(r, self.bases, x, y, 48)
                                                    for r in self._near(x, y, self.walk, 64)))

    def to_street(self, x: float, y: float, skip: frozenset = frozenset()) -> bool:
        """A walk over walkable cells from (x, y) to a street (8-way, within SEARCH)."""
        s = (round(x / GRID), round(y / GRID))
        if s in self.street:
            return True
        lim = int(SEARCH // GRID)
        seen, q = {s}, deque([s])
        while q:
            c = q.popleft()
            for di in (-1, 0, 1):
                for dj in (-1, 0, 1):
                    n = (c[0] + di, c[1] + dj)
                    if n in seen or abs(n[0] - s[0]) > lim or abs(n[1] - s[1]) > lim:
                        continue
                    seen.add(n)
                    if n in self.street:
                        return True
                    if self.walkable(n[0] * GRID, n[1] * GRID, skip):
                        q.append(n)
        return False


def stops(person: dict) -> list[dict]:
    return [s["at"] for s in person.get("routine") or [] if s.get("at")]


def check(folk: list[dict], refs: list[dict], spaces: dict[str, dict], bases: dict, paths: list[dict], G,
          door_reached) -> list[str]:
    """Faults: a stop no walk reaches from the one before (named by person, stop and why)."""
    out = Outside(refs, bases, paths, G)
    by_id = {r["id"]: r for r in refs}
    bad: list[str] = []
    memo: dict = {}

    def where(st: dict) -> tuple[str, str | None]:
        """(the island a stop stands in, a fault or None). Islands: 'out' (the streets' network), else a room."""
        key = (st.get("space"), st.get("ref"), tuple(st.get("pos") or []))
        if key in memo:
            return memo[key]
        memo[key] = res = _where(st)
        return res

    def _where(st: dict) -> tuple[str, str | None]:
        sp = st.get("space", "exterior")
        if sp == "exterior":
            r = by_id.get(st.get("ref")) if st.get("ref") else None
            p = r["pos"] if r else st.get("pos")
            if p is None:
                return "out", None   # the town at large
            on_street = (round(p[0] / GRID), round(p[1] / GRID)) in out.street
            if r is None or r.get("kind") not in FURNITURE:
                if not on_street and not out.walkable(p[0], p[1]):
                    return "out", f"at {p[0]:.0f},{p[1]:.0f} is not walkable ground (water or inside a building)"
            skip = frozenset()
            if r is not None and r.get("kind") in FURNITURE:
                held = [o for o in out.solid if o is not r and geom.contains_xy(o, bases, p[0], p[1], 0)]
                if any(not overlap.source_had(r, o) for o in held):
                    return "out", f"{r['id']} stands inside a building the source did not have it in"
                skip = frozenset(o["id"] for o in held)   # a bed in its tent: one walks in at the tent's mouth
            if not out.to_street(p[0], p[1], skip):
                return "out", f"at {p[0]:.0f},{p[1]:.0f} no walk over our ground reaches a street"
            return "out", None
        s = spaces.get(sp)
        if s is None:
            return sp, f"space {sp} is not drafted"
        ref = st.get("ref")
        if ref:
            keep = interiors.kept(s.get("copy_of"), s.get("room"))
            ours = {o["id"] for o in s.get("overrides") or []}
            if keep is not None and ref not in keep and ref not in ours:
                return sp, f"{ref} is outside the room {sp} keeps (the builder's island from its way out)"
        # the door chain out to the streets
        seen = set()
        while s is not None and sp not in seen:
            seen.add(sp)
            d = s.get("door_from")
            if not d:
                return sp, f"room {sp} has no door in"
            if s.get("parent", "exterior") == "exterior":
                if not door_reached(d):
                    return sp, f"the door into {sp} is reached by no street"
                return sp, None
            sp = s["parent"]
            s = spaces.get(sp)
        return sp, f"room {sp} has no way out"

    for p in folk:
        st = stops(p)
        for i, a in enumerate(st):
            _, why = where(a)
            if why:
                prev = st[i - 1] if st else a
                bad.append(f"{p['id']} ({p.get('role')}): stop {i + 1} ({a.get('space', 'exterior')}) unreachable "
                           f"from stop {(i - 1) % len(st) + 1} ({prev.get('space', 'exterior')}): {why}")
    return bad


def _tops(r: dict, bases: dict) -> float | None:
    b = geom.bounds(r, bases)
    return r["pos"][2] + b[1][2] if b else None


def arrival_faults(refs: list[dict], spaces: dict[str, dict], bases: dict, paths: list[dict], G,
                   out: "Outside | None" = None) -> list[str]:
    """Every room the draft copies is entered through a door pair in our place on both sides (the outside door
    naming the room's door and back), and the outside arrival stands on walkable ground the streets reach: on the
    ground (or a low piece over it), or on a deck that joins the ground through decks each a step from the next."""
    out = out or Outside(refs, bases, paths, G)
    by_id = {r["id"]: r for r in refs}
    bad = []
    for sid, s in sorted(spaces.items()):
        if s.get("parent", "exterior") != "exterior":
            continue
        d = by_id.get(s.get("door_from"))
        inner = {o["id"]: o for o in s.get("doors") or []}
        dd = (d or {}).get("door") or {}
        back = inner.get(dd.get("to_ref"), {}).get("door") or {}
        if d is None or dd.get("to_space") != sid or back.get("to_ref") != d["id"]:
            bad.append(f"room {sid} has no door pair into the place (outside door {s.get('door_from')} and the "
                       f"room's door must each name the other)")
            continue
        a = dd.get("arrival") or back.get("to_pos")
        if not a:
            bad.append(f"door {d['id']} into {sid} has no arrival point")
            continue
        g = G.height(a[0], a[1])
        if g is None:
            bad.append(f"door {d['id']} into {sid}: its arrival is off our ground")
            continue
        sh = geom.stand_height(a[0], a[1], g, refs, bases)
        if abs(a[2] - sh) <= geom.STEP:
            if not out.to_street(a[0], a[1], frozenset(o["id"] for o in out.solid
                                                         if geom.contains_xy(o, bases, a[0], a[1], 0))):
                bad.append(f"door {d['id']} into {sid}: its arrival {a[0]:.0f},{a[1]:.0f} is walled in, no walk "
                           f"reaches a street")
            continue
        # above the ground: it must stand on a walkway (a pier, a deck, a road piece) a step from its top, and that
        # walkway must reach a street; a ship's or a tower's body is no floor one is known to walk on
        on = [r for r in out.walk if geom.contains_xy(r, bases, a[0], a[1], 32)
              and abs(geom.top(r, bases) - a[2]) <= geom.STEP]
        if not on:
            tops = sorted(round(geom.top(r, bases) - a[2]) for r in out.walk if geom.contains_xy(r, bases, a[0], a[1], 32))
            bad.append(f"door {d['id']} into {sid}: its arrival stands {a[2] - sh:.0f} above the ground on no walkway "
                       f"(walkways under it, top minus arrival: {tops or 'none'})")
        elif not out.to_street(a[0], a[1], frozenset(o["id"] for o in out.solid
                                                       if geom.contains_xy(o, bases, a[0], a[1], 0))):
            bad.append(f"door {d['id']} into {sid}: its walkway reaches no street")
    return bad
