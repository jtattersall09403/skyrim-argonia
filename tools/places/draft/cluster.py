"""Decompose a source place's exterior into clusters: each building with its yard, the landing, the streets.

A cluster moves as one piece in the fit. Membership comes from links first (linked refs, enable parents and door
pairs follow the ref they belong to), then from space: a thing belongs to the nearest building whose footprint it
stands within `YARD` of; things over the source's water join the landing; everything else forms street clusters by
single linkage. Plants and rocks never seed a cluster: inside a yard or a street they are the source's own planting
and come across; outside they are wild and our world's plants stand there instead.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from tools.places.draft import geom
from tools.places.seat import Ground, foot_area, foot_points

YARD = 512.0          # how far beyond its footprint a building's yard reaches
STREET_LINK = 640.0   # single-linkage distance of street things
LANDING_LINK = 768.0  # single-linkage distance of things over water
SHORE = 384.0         # land things this close to the landing join it
VEG = {"tree", "plant", "groundcover", "rock"}
SKIP = {"actor", "water"}
SEED_AREA = 600.0 * 600.0   # a building this big seeds a cluster of its own
DOOR_NEAR = 256.0          # ... and so does any building with a door this close
TOUCH = 96.0               # seeds this close are one building
MAX_SAMPLES = 64


@dataclass
class Cluster:
    id: str
    kind: str                      # building | landing | street
    members: list[str] = field(default_factory=list)
    head: str | None = None        # the building ref of a building cluster
    centre: tuple[float, float] = (0.0, 0.0)
    wet: list[tuple[float, float, bool]] = field(default_factory=list)   # source sample points and wetness
    feet: list[tuple[str, float, float, float, list]] = field(default_factory=list)  # (id, x, y, rz, foot)

    def as_dict(self) -> dict:
        return {"id": self.id, "kind": self.kind, "head": self.head, "members": len(self.members),
                "centre": [round(v, 1) for v in self.centre]}


def rect_dist(ref: dict, bases: dict, x: float, y: float) -> float:
    """Distance from a point to a ref's footprint rectangle (0 inside); point refs use their origin."""
    b = geom.bounds(ref, bases)
    px, py = ref["pos"][0], ref["pos"][1]
    if not b:
        return math.hypot(x - px, y - py)
    rz = ref.get("rot", [0, 0, 0])[2]
    c, s = math.cos(rz), math.sin(rz)
    dx, dy = x - px, y - py
    u, v = dx * c - dy * s, dx * s + dy * c
    ex = max(b[0][0] - u, 0.0, u - b[1][0])
    ey = max(b[0][1] - v, 0.0, v - b[1][1])
    return math.hypot(ex, ey)


def _components(ids: list[str], pos: dict, link: float) -> list[list[str]]:
    left, out = set(ids), []
    for i in ids:
        if i not in left:
            continue
        left.discard(i)
        comp, stack = [i], [i]
        while stack:
            a = stack.pop()
            near = [j for j in left if geom.dist(pos[a], pos[j]) <= link]
            for j in near:
                left.discard(j)
                comp.append(j)
                stack.append(j)
        out.append(sorted(comp))
    return out


def decompose(refs: list[dict], bases: dict, g: Ground) -> tuple[list[Cluster], dict[str, str], dict[str, str]]:
    """Returns (clusters, member -> cluster id, wild refs -> reason). Actors and water planes are left out."""
    by_id = {r["id"]: r for r in refs}
    pos = {r["id"]: (r["pos"][0], r["pos"][1]) for r in refs}
    def over_water(r):
        x, y = pos[r["id"]]
        w, h = g.water(x, y), g.height(x, y)
        return w is not None and h is not None and h < w - 8

    # seeds: buildings one enters, and big ones; a building standing in the water (a pier, a boathouse) belongs
    # to the landing, and small building pieces (posts, wall runs, road slabs) join a yard or a street
    doors = [r for r in refs if r.get("kind") == "door" and (r.get("door") or {}).get("to_space")]

    def seed(r):
        f = geom.foot(r, bases)
        if r.get("kind") != "building" or not f or over_water(r):
            return False
        if foot_area(f) >= SEED_AREA:
            return True
        return any(rect_dist(r, bases, d["pos"][0], d["pos"][1]) <= DOOR_NEAR for d in doors)

    seeds = sorted((r for r in refs if seed(r)), key=lambda r: r["id"])
    # seeds that touch are one building (a dwelling with its entrance and dome)
    group = {r["id"]: r["id"] for r in seeds}

    def root(i):
        while group[i] != i:
            group[i] = group[group[i]]
            i = group[i]
        return i
    for a_i, a in enumerate(seeds):
        ra = geom.radius(a, bases)
        for b in seeds[a_i + 1:]:
            if geom.dist(pos[a["id"]], pos[b["id"]]) <= ra + geom.radius(b, bases) + TOUCH:
                if rect_dist(a, bases, *pos[b["id"]]) <= geom.radius(b, bases) + TOUCH:
                    group[root(b["id"])] = root(a["id"])
    groups: dict[str, list[dict]] = {}
    for r in seeds:
        groups.setdefault(root(r["id"]), []).append(r)
    buildings = seeds
    of: dict[str, str] = {}
    clusters: dict[str, Cluster] = {}
    seed_ids = {r["id"] for r in seeds}
    for i, (_, members) in enumerate(sorted(groups.items())):
        cid = f"b{i + 1:02d}"
        head = max(members, key=lambda r: (geom.radius(r, bases), r["id"]))
        cx = sum(pos[m["id"]][0] for m in members) / len(members)
        cy = sum(pos[m["id"]][1] for m in members) / len(members)
        clusters[cid] = Cluster(cid, "building", [m["id"] for m in members], head["id"], (cx, cy))
        for m in members:
            of[m["id"]] = cid

    rest = [r for r in refs if r["id"] not in of and r.get("kind") not in SKIP]
    # 1. by links (two passes so chains settle)
    for _ in range(2):
        for r in rest:
            if r["id"] in of:
                continue
            for t in [lk.get("ref") for lk in r.get("linked") or []] + [(r.get("enable_parent") or {}).get("ref")]:
                if t in of and by_id.get(t, {}).get("kind") not in VEG:
                    of[r["id"]] = of[t]
                    break
    # 2. by yard
    for r in rest:
        if r["id"] in of:
            continue
        x, y = pos[r["id"]]
        best = min(((rect_dist(b, bases, x, y), b["id"]) for b in buildings), default=None)
        if best and best[0] <= YARD and not (over_water(r) and best[0] > 0):
            of[r["id"]] = of[best[1]]
    # 3. the landing: things over water, then land things on its shore
    wet_ids = sorted(r["id"] for r in rest if r["id"] not in of and r.get("kind") not in VEG and over_water(r))
    land_comps = _components(wet_ids, pos, LANDING_LINK)
    # the landing is the biggest group of things in the water, preferring one with a door; the rest stand in
    # shallows and fit like a yard that must stay wet
    def door_count(comp):
        return sum(1 for i in comp if by_id[i].get("kind") == "door")
    for k, comp in enumerate(sorted(land_comps, key=lambda c: (-door_count(c), -len(c), c[0]))):
        cid = "landing" if k == 0 else f"w{k:02d}"
        clusters[cid] = Cluster(cid, "landing" if k == 0 else "wet", [])
        for i in comp:
            of[i] = cid
    for r in rest:
        if r["id"] in of or r.get("kind") in VEG:
            continue
        near = [(geom.dist(pos[r["id"]], pos[j]), of[j]) for j in wet_ids]
        if near and min(near)[0] <= SHORE:
            of[r["id"]] = min(near)[1]
    # 4. streets
    street_ids = sorted(r["id"] for r in rest if r["id"] not in of and r.get("kind") not in VEG)
    for k, comp in enumerate(_components(street_ids, pos, STREET_LINK)):
        cid = f"s{k + 1:02d}"
        clusters[cid] = Cluster(cid, "street", [])
        for i in comp:
            of[i] = cid
    # 5. plants: the source's own planting inside a yard or a street; wild otherwise
    wild: dict[str, str] = {}
    placed_pts = [(pos[i], c) for i, c in of.items()]
    for r in rest:
        if r["id"] in of:
            continue
        x, y = pos[r["id"]]
        best = min(((rect_dist(b, bases, x, y), of[b["id"]]) for b in buildings), default=None)
        if best and best[0] <= YARD / 2:
            of[r["id"]] = best[1]
            continue
        near = min(((geom.dist((x, y), p), c) for p, c in placed_pts if clusters[c].kind == "street"), default=None)
        if near and near[0] <= STREET_LINK / 2:
            of[r["id"]] = near[1]
            continue
        wild[r["id"]] = "wild plant of the source's land; our world's own plants stand here"
    for i, cid in sorted(of.items()):
        if i not in clusters[cid].members:
            clusters[cid].members.append(i)
    for c in clusters.values():
        c.members.sort()
        pts = [pos[i] for i in c.members]
        if c.kind not in ("building",):
            c.centre = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
        for i in c.members:
            r = by_id[i]
            f = geom.foot(r, bases)
            rz = r.get("rot", [0, 0, 0])[2]
            if f and i in seed_ids:
                c.feet.append((i, pos[i][0], pos[i][1], rz, f))
            for px, py in foot_points(pos[i][0], pos[i][1], rz, f if r.get("kind") not in VEG else None):
                if g.has(px, py):
                    c.wet.append((px, py, g.wet(px, py)))
        if len(c.wet) > MAX_SAMPLES:
            step = len(c.wet) / MAX_SAMPLES
            c.wet = [c.wet[int(k * step)] for k in range(MAX_SAMPLES)]
    out = [c for c in clusters.values() if c.members]
    return sorted(out, key=lambda c: c.id), of, wild
