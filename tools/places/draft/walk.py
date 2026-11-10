"""The walkable network of a drafted place, by the build's own navmesh, and the joins the draft lays across it.

`network` builds the place (`build <place_id>` into out/places/draft_check, cached by the place files' key, so an
unchanged draft is not rebuilt) and loads it exactly as `check` does; `islands` lists each door's exterior navmesh
that is not on the place's main walkable network; `join` lays walkway pieces from each such island to the nearest
point of the network at a walkable height and reseats, until no door is on an island (or no join is possible).
`draft check` and `check` read the same network, so what `join` makes walkable the build's check finds walkable.
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
from collections import Counter
from pathlib import Path

import numpy as np

from tools.places.draft import io, overlap
from tools.places.draft import paths as paths_mod

CHECK_OUT = io.ROOT / "out" / "places" / "draft_check"
LEVEL = 48.0         # units of height a join may leave between its two ends (a step the navmesh climbs)
JOIN_ROUNDS = 6
TRIES = 200        # joins tried per island, shortest first, for one no house or ship stands across


def build(place_id: str, places: Path = io.PLACES, out: Path = CHECK_OUT) -> list[str]:
    """`build <place_id> --keep-going` into `out`: the build's problems, or the failure."""
    p = subprocess.run([sys.executable, "-m", "tools.places", "build", place_id, "--keep-going", "--places-dir", str(places),
                        "--out", str(out)], cwd=io.ROOT, capture_output=True, text=True)
    lines = [x.strip() for x in (p.stdout + p.stderr).splitlines() if x.strip()]
    bad = [f"build: {x}" for x in lines if x.startswith(f"{place_id}: ")]
    if p.returncode != 0:
        bad += [f"build failed ({p.returncode}): {x}" for x in lines[-10:]]
    return bad


def network(place_id: str, places: Path = io.PLACES, out: Path = CHECK_OUT) -> tuple[dict | None, list[str]]:
    """The built place as `check` loads it (its context dict), and the build's problems."""
    bad = build(place_id, places, out)
    if any(b.startswith("build failed") for b in bad):
        return None, bad
    from tools.places import check as C
    ctx = C.load(place_id, out)
    ctx["place_dir"] = places / place_id
    return ctx, bad


def islands(ctx: dict, W: "Walkable") -> dict:
    """{door id: (its island, the island's triangle centres)} for each door of ours whose exterior navmesh is off the
    main network."""
    from tools.places import check as C
    m = C.mine(ctx)
    out: dict = {}
    for n in W.navs:
        if getattr(n, "world", False):
            continue
        for ti, d in n.doors:
            c = W.comp[W.off[n.fk] + ti]
            row = m["rows"].get(d)
            if not W.main[W.off[n.fk] + ti] and row is not None and row["id"] not in out:
                out[row["id"]] = (int(c), W.cent[W.comp == c])
    return out


ON_TOL = 48.0          # plan units: a point within this of a triangle stands on it
Z_BELOW, Z_ABOVE = 128.0, 512.0   # a triangle this far under or over the point's height is another level (a roof, a cellar)
BUCKET = 512.0
STEP = 64.0            # units between the samples of a street tested against the network (paths.smooth's spacing)
SNAP = 384.0           # an end off the network (a doorway) is taken to the nearest network point this near
ROUTE_CAP = 200_000    # triangles a re-lay's search may open


class Walkable:
    """The built exterior navmesh (ours and the world's round the place) as one index: each triangle's walkable
    component and whether it is the town's main network (the largest component over doors, as `check` finds it);
    triangles bucketed in plan for point lookup, and their neighbours for routing on the mesh. `zref(x, y)` gives a
    plan point's height (our ground, as the build stands a marker given in plan; over water the mesh's own water
    triangles lie on the bed, and the decks above it are within Z_ABOVE); a 3-d point carries its own."""

    def __init__(self, ctx: dict, zref=None, comp: dict | None = None):
        from tools.places import check as C
        comp = comp if comp is not None else C.components(ctx["navs"], C.door_pairs(ctx))
        main = Counter(comp.values()).most_common(1)[0][0]
        self.zref = zref
        self.navs = [n for n in ctx["navs"].values() if n.space == "exterior" and len(n.tri)]
        self.off, tri, ids, o = {}, [], {}, 0
        cid = []
        for n in self.navs:
            self.off[n.fk] = o
            o += len(n.tri)
            tri.append(n.verts[n.tri])
            cid += [ids.setdefault(comp[(n.fk, i)], len(ids)) for i in range(len(n.tri))]
        self.T = np.concatenate(tri) if tri else np.zeros((0, 3, 3))
        self.comp = np.asarray(cid, int)
        self.main = self.comp == ids.get(main, -1)
        self.cent = self.T.mean(axis=1)
        lo = np.floor((self.T[:, :, :2].min(axis=1) - ON_TOL) / BUCKET).astype(int)
        hi = np.floor((self.T[:, :, :2].max(axis=1) + ON_TOL) / BUCKET).astype(int)
        span = hi - lo
        keys, idx = [], []
        for di in range(int(span[:, 0].max(initial=0)) + 1):
            for dj in range(int(span[:, 1].max(initial=0)) + 1):
                m = (span[:, 0] >= di) & (span[:, 1] >= dj)
                keys.append(((lo[m, 0] + di).astype(np.int64) << 32) + (lo[m, 1] + dj).astype(np.int64))
                idx.append(np.nonzero(m)[0])
        keys = np.concatenate(keys) if keys else np.zeros(0, np.int64)
        idx = np.concatenate(idx) if idx else np.zeros(0, int)
        order = np.argsort(keys, kind="stable")
        keys, idx = keys[order], idx[order]
        u, start = np.unique(keys, return_index=True)
        ends = np.append(start[1:], len(keys))
        self.bucket = {int(k): idx[s:e] for k, s, e in zip(u, start, ends)}
        self._nbr = None

    def _height(self, p) -> float | None:
        if len(p) > 2:
            return float(p[2])
        return self.zref(float(p[0]), float(p[1])) if self.zref else None

    def near(self, p, tol: float = ON_TOL) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """(triangle indices, plan distance, height at p) of the triangles within `tol` of p in plan and at its
        level."""
        i, j = math.floor(p[0] / BUCKET), math.floor(p[1] / BUCKET)
        c = self.bucket.get((i << 32) + j)
        if c is None:
            return np.zeros(0, int), np.zeros(0), np.zeros(0)
        t = self.T[c]
        a, b, cc = t[:, 0, :2], t[:, 1, :2], t[:, 2, :2]
        q = np.asarray(p[:2], float)

        def cross(u, v):
            return (q[0] - v[:, 0]) * (u[:, 1] - v[:, 1]) - (u[:, 0] - v[:, 0]) * (q[1] - v[:, 1])
        d1, d2, d3 = cross(a, b), cross(b, cc), cross(cc, a)
        inside = ~(((d1 < 0) | (d2 < 0) | (d3 < 0)) & ((d1 > 0) | (d2 > 0) | (d3 > 0)))

        def seg(u, v):
            w = v - u
            L = np.maximum((w * w).sum(axis=1), 1e-9)
            s = np.clip(((q - u) * w).sum(axis=1) / L, 0.0, 1.0)
            return np.linalg.norm(q - (u + w * s[:, None]), axis=1)
        dp = np.where(inside, 0.0, np.minimum(np.minimum(seg(a, b), seg(b, cc)), seg(cc, a)))
        # the triangle's plane at p (its centre's height for one seen edge on)
        e1, e2 = t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]
        nrm = np.cross(e1, e2)
        flat = np.abs(nrm[:, 2]) > 1e-6
        z = np.where(flat, t[:, 0, 2] - (nrm[:, 0] * (q[0] - t[:, 0, 0]) + nrm[:, 1] * (q[1] - t[:, 0, 1]))
                     / np.where(flat, nrm[:, 2], 1.0), self.cent[c, 2])
        z = np.clip(z, t[:, :, 2].min(axis=1), t[:, :, 2].max(axis=1))
        keep = dp <= tol
        h = self._height(p)
        if h is not None:
            keep &= (z >= h - Z_BELOW) & (z <= h + Z_ABOVE)
        return c[keep], dp[keep], z[keep]

    def on(self, p, tol: float = ON_TOL) -> bool:
        """Whether p stands on the town's main network."""
        c, _, _ = self.near(p, tol)
        return bool(self.main[c].any())

    def snap(self, p, reach: float = SNAP):
        """The nearest point of the main network to p within `reach` in plan (p itself when it is on it), else None."""
        if self.on(p):
            return tuple(p[:2])
        for r in np.arange(STEP / 2, reach + 1, STEP / 2):
            for k in range(16):
                q = (p[0] + r * math.cos(k * math.pi / 8), p[1] + r * math.sin(k * math.pi / 8))
                if self.on(q, tol=8.0):
                    return q
        return None

    def tri(self, p) -> int:
        """The main-network triangle under p nearest its height, else -1."""
        c, dp, z = self.near(p)
        m = self.main[c]
        if not m.any():
            return -1
        h = self._height(p)
        score = dp[m] + (np.abs(z[m] - h) * 0.01 if h is not None else 0.0)
        return int(c[m][np.argmin(score)])

    def neighbours(self) -> list[list[int]]:
        """Each triangle's neighbours over shared edges and edge links between meshes."""
        if self._nbr is None:
            nb = [[] for _ in range(len(self.T))]
            for n in self.navs:
                o = self.off[n.fk]
                for i in range(len(n.tri)):
                    for k in range(3):
                        e = int(n.edge[i][k])
                        if n.flags[i] & (1 << k):
                            if 0 <= e < len(n.links):
                                _, tgt, tt = n.links[e]
                                if tgt in self.off:
                                    nb[o + i].append(self.off[tgt] + tt)
                                    nb[self.off[tgt] + tt].append(o + i)
                        elif e >= 0:
                            nb[o + i].append(o + e)
            self._nbr = nb
        return self._nbr

    def clear(self, a, b) -> bool:
        """Whether the straight line a -> b stands on the main network all along."""
        n = max(1, math.ceil(math.dist(a[:2], b[:2]) / (STEP / 2)))
        return all(self.on((a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n)) for k in range(n + 1))

    def route(self, a, b) -> list | None:
        """The way the mesh walks from a to b (each on the main network): a search over the triangles, pulled
        straight where the line stays on the network, then eased with paths.smooth without leaving it."""
        import heapq
        s, g = self.tri(a), self.tri(b)
        if s < 0 or g < 0:
            return None
        nb, C = self.neighbours(), self.cent
        dist, prev, heap, opened = {s: 0.0}, {}, [(0.0, s)], 0
        while heap:
            _, u = heapq.heappop(heap)
            if u == g:
                break
            opened += 1
            if opened > ROUTE_CAP:
                return None
            for v in nb[u]:
                if not self.main[v]:
                    continue
                d = dist[u] + float(np.linalg.norm(C[u] - C[v]))
                if d < dist.get(v, float("inf")):
                    dist[v], prev[v] = d, u
                    heapq.heappush(heap, (d + float(np.linalg.norm(C[v, :2] - C[g, :2])), v))
        if g not in dist:
            return None
        chain, u = [], g
        while u != s:
            chain.append(u)
            u = prev[u]
        pts = [tuple(a[:2])] + [tuple(C[t, :2]) for t in reversed(chain[1:])] + [tuple(b[:2])]
        pulled, i = [pts[0]], 0
        while i < len(pts) - 1:
            j = len(pts) - 1
            while j > i + 1 and not self.clear(pts[i], pts[j]):
                j -= 1
            pulled.append(pts[j])
            i = j
        return paths_mod.smooth(pulled, lambda x, y: not self.on((x, y)))


def standing(G):
    """A plan point's height on our ground (patched land included), as the build stands a marker given in plan."""
    return G.height


def samples(pts: list, step: float = STEP) -> list[tuple[int, tuple]]:
    """A street's points every `step` units along it: [(the segment it lies on, (x, y))], its own points included."""
    out = []
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        n = max(1, math.ceil(math.dist(a[:2], b[:2]) / step))
        out += [(i, (a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n)) for k in range(n)]
    if pts:
        out.append((max(0, len(pts) - 2), tuple(pts[-1][:2])))
    return out


def off_network(paths: list[dict], folk: list[dict], W: Walkable) -> tuple[list[tuple], list[tuple]]:
    """([(street id, point)], [(person id, patrol point)]) of the street samples and patrol points off the main
    network."""
    st = [(p["id"], q) for p in paths for _, q in samples(p["points"]) if not W.on(q)]
    pa = [(p["id"], q) for p in folk for q in (p.get("patrol") or {}).get("points") or [] if not W.on(q)]
    return st, pa


def mend(path: dict, W: Walkable, passes: int = 3) -> int | None:
    """Re-lay each stretch of a street off the main network along the way the mesh walks between the stretch's last
    and next points on it (an end off it, at a doorway, is first taken to the nearest network point), again over the
    new line until it holds (a gap finer than the sampling shows only on the new line). The stretches re-laid, or
    None when one has no way on the mesh (the street is then left as it was)."""
    before, total = list(path["points"]), 0
    for _ in range(passes):
        n = _mend(path, W)
        if n is None:
            path["points"] = before
            return None
        if n == 0:
            return total
        total += n
    return total


def _mend(path: dict, W: Walkable) -> int | None:
    pts = [tuple(q[:2]) for q in path["points"]]
    if len(pts) < 2:
        return 0
    S = samples(pts)
    ok = [W.on(q) for _, q in S]
    if all(ok):
        return 0
    for e in (0, len(S) - 1):
        if not ok[e]:
            q = W.snap(S[e][1])
            if q is None:
                return None
            S[e], ok[e] = (S[e][0], q), True
            pts[0 if e == 0 else -1] = q
    out, cursor, k, n = [], 0, 0, 0
    while k < len(S):
        if ok[k]:
            k += 1
            continue
        a = k - 1
        b = next(j for j in range(k, len(S)) if ok[j])
        way = W.route(S[a][1], S[b][1])
        if way is None:
            return None
        out += pts[cursor:S[a][0] + 1] + [S[a][1]] + list(way[1:-1]) + [S[b][1]]
        cursor, k, n = S[b][0] + 1, b + 1, n + 1
    out += pts[cursor:]
    clean = [out[0]]
    for q in out[1:]:
        if math.dist(q, clean[-1]) > 1.0:
            clean.append(q)
    path["points"] = [[round(float(q[0]), 1), round(float(q[1]), 1)] for q in clean]
    return n


def dry(pts: np.ndarray, G) -> np.ndarray:
    """The triangle centres one walks on out of the water (a seabed under our water is no street)."""
    keep = []
    for p in pts:
        w = G.water(float(p[0]), float(p[1]))
        keep.append(w is None or p[2] >= w - 8)
    return pts[np.asarray(keep, bool)] if len(pts) else pts


def pairs(isl: np.ndarray, net: np.ndarray) -> list[tuple[float, np.ndarray, np.ndarray]]:
    """Level joins from an island to the network (ends within LEVEL of each other), shortest first: [(plan length, from, to)], one per
    island point (its nearest such network point)."""
    out = []
    for p in isl:
        d = np.linalg.norm(net[:, :2] - p[:2], axis=1)
        ok = np.abs(net[:, 2] - p[2]) <= LEVEL  # flat pieces: a join never climbs more than a step
        if ok.any():
            j = int(np.argmin(np.where(ok, d, np.inf)))
            out.append((float(d[j]), p, net[j]))
    return sorted(out, key=lambda t: t[0])


def walk_base(rows: list[dict], bases: dict) -> str | None:
    """The walkway piece the place's own joins and bridges use: the commonest the draft already laid, else the
    commonest walkway piece of the place."""
    laid = Counter(r["base"] for r in rows if not r.get("src") and r.get("kind") == "building" and r.get("why"))
    if laid:
        return sorted(laid, key=lambda b: (-laid[b], b))[0]
    ways = Counter(r["base"] for r in rows if r.get("kind") == "building"
                   and paths_mod.WALKWAY.search(str((bases.get(r["base"]) or {}).get("model", ""))))
    return sorted(ways, key=lambda b: (-ways[b], b))[0] if ways else None


def piece_length(bases: dict, base: str) -> float:
    bb = bases[base]["bounds"]
    return max(64.0, bb[1][1] - bb[0][1] - 16)


def lay(place_id: str, door_id: str, a, b, base: str, rows: list[dict], bases: dict, G) -> list[dict]:
    """Walkway pieces end to end from a to b ([x, y, z] each), their decks (the top surface of the mesh, geom.walk) on
    the line between the two heights."""
    from tools.places.draft import geom
    top = geom.walk(bases[base]) or 0.0
    length = piece_length(bases, base)
    near = [r for r in rows if r.get("kind") in overlap.SOLID and math.dist(r["pos"][:2], a[:2]) < math.dist(a[:2], b[:2]) + 4096]
    run = math.dist(a[:2], b[:2])
    n = max(1, math.ceil(run / length))
    yaw = math.atan2(b[0] - a[0], b[1] - a[1]) % (2 * math.pi)
    out = []
    for j in range(n):
        t = (j + 0.5) / n if run > length else 0.5
        x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        deck = float(a[2] + (b[2] - a[2]) * t)
        cand = {"id": io.mint(place_id, "join", door_id, str(j)), "base": base, "kind": "building",
                "pos": [round(x, 2), round(y, 2), round(deck - top, 2)], "rot": [0.0, 0.0, round(yaw, 5)], "scale": 1.0,
                "layer": "place", "flags": [], "src": None, "walk": top,
                "seat": {"mode": "free"},
                "why": f"joins door {door_id}'s walkable island to the town's network"}
        hit = [o for o in near if overlap.inside(o["pos"], cand, bases) or overlap.inside(cand["pos"], o, bases)]
        ways = [o for o in hit if paths_mod.WALKWAY.search(str((bases.get(o["base"]) or {}).get("model", "")))]
        if len(hit) > 1 or (hit and not ways):
            continue  # a door, a house or two pieces stand there: the join leaves that piece out
        if ways:
            cand["seat"]["on"] = ways[0]["id"]  # it rests on the walkway it continues
        out.append(cand)
    return out


def cut(place_id: str, door_ids: list[str], rows: list[dict], pdir: Path, log=print) -> int:
    """A door left on an island no level join reaches (a ship's hatch with no way aboard in the source) leads
    nowhere one can walk to: its room is left out with it, with the reason in the ledger, unless someone lives or
    works in that room (then it stays, and `draft check` lists the island). Returns the rooms left out."""
    import shutil
    used = set()
    for p in io.read_jsonl(pdir / "people.jsonl") if (pdir / "people.jsonl").exists() else []:
        used.add(p.get("home"))
        for k in ("bed", "work"):
            used.add((p.get(k) or {}).get("space"))
        used.update(s.get("space") for s in p.get("stops") or [] if isinstance(s, dict))
    by_id = {r["id"]: r for r in rows}
    gone, ledger = set(), []
    for did in door_ids:
        sid = ((by_id.get(did) or {}).get("door") or {}).get("to_space")
        sdir = pdir / "spaces" / str(sid)
        if not sid or sid == "exterior" or sid in used or not sdir.is_dir():
            continue
        sp = json.loads((sdir / "space.json").read_text())
        if sp.get("door_from") != did:
            continue   # a room with another way in stays
        why = (f"its only door {did} stands on a walkable island with no way to the town (the source gives no "
               f"way aboard) and nobody lives or works in it")
        gone.add(did)
        ledger.append({"src": by_id[did].get("src") or did, "space": "exterior", "status": "dropped", "why": why})
        ledger.append({"src": "*", "space": sid, "status": "dropped", "why": why})
        shutil.rmtree(sdir)
        log(f"join {place_id}: left out room {sid} and its door {did}: no way to it")
    if gone:
        dropped = {r["space"] for r in ledger if r["src"] == "*"}
        srcs = {r["src"] for r in ledger if r["src"] != "*"}
        # the links that led to a door left out go with it, and the walkway pieces laid to carry them
        pj, carried = pdir / "paths.jsonl", ()
        if pj.exists():
            paths = io.read_jsonl(pj)
            dead = [p for p in paths if p.get("from") in srcs or p.get("to") in srcs]
            if dead:
                carried = tuple(f"carries street {p['id'].rsplit('.', 1)[-1]} " for p in dead)
                io.write_jsonl(pj, [p for p in paths if p not in dead])
        io.write_jsonl(pdir / "spaces" / "exterior" / "refs.jsonl",
                       [r for r in rows if r["id"] not in gone and not str(r.get("why", "")).startswith(carried or ("\0",))])
        old = [r for r in io.read_jsonl(pdir / "ledger.jsonl") if r.get("space") not in dropped
               and not (r.get("space") == "exterior" and r.get("src") in srcs)]
        io.write_jsonl(pdir / "ledger.jsonl", old + ledger)
    return len(gone)


def rehome(place_id: str, W: "Walkable", bases: dict, src, pdir: Path, log=print) -> int:
    """A person whose bed outdoors (a camp bed) stands where the town's walkable network does not reach (a tent shut
    in by blocks) sleeps instead in a free bed of a home: the first room, by name, with a bed nobody has (never the
    inn's, whose beds are let); with none free, the last resident (residents only fill the beds left over) gives up
    theirs. Returns the people moved."""
    from tools.places import check as C
    from tools.places.draft import interiors
    rows = {r["id"]: r for r in io.read_jsonl(pdir / "spaces" / "exterior" / "refs.jsonl")}

    def reached(pos) -> bool:   # within the build's own reach of a stop (a bed cuts the mesh round itself)
        return W.on(pos, tol=C.STOP_PLAN_TOL)
    ppl = io.read_jsonl(pdir / "people.jsonl")
    inns = {(p.get("work") or {}).get("space") for p in ppl
            if any((g.get("give_kind_id") or g.get("kind")) == "inn-room" for g in p.get("services") or [])}
    taken = Counter(((p.get("bed") or {}).get("space"), (p.get("bed") or {}).get("ref")) for p in ppl)
    free = []
    for sdir in sorted((pdir / "spaces").iterdir()):
        sp = json.loads((sdir / "space.json").read_text()) if (sdir / "space.json").exists() else None
        if not sp or sp["space_id"] == "exterior" or sp.get("parent") != "exterior" or sp["space_id"] in inns:
            continue
        src_space = str(sp.get("copy_of") or "").split("/")[-1]
        if src_space not in src.spaces:
            continue
        for b in interiors.beds_in(src.spaces[src_space].refs, bases, sp.get("room"), sp.get("copy_of")):
            free += [(sp["space_id"], b["ref"])] * max(0, b["sleeps"] - taken[(sp["space_id"], b["ref"])])
    moved = 0
    for p in ppl:
        bed = p.get("bed") or {}
        r = rows.get(bed.get("ref")) if bed.get("space") == "exterior" else None
        if r is None or reached(r["pos"]):
            continue
        if not free:   # residents only fill the beds left over: the last of them gives up a bed
            res = sorted((q for q in ppl if q.get("role") == "resident" and not q.get("_gone")
                          and (q.get("bed") or {}).get("space") not in (None, "exterior", *inns)), key=lambda q: q["id"])
            if not res:
                continue
            res[-1]["_gone"] = True
            free.append((res[-1]["bed"]["space"], res[-1]["bed"]["ref"]))
            log(f"join {place_id}: resident {res[-1]['id']} left out: a guard needs the bed")
        sid, ref = free.pop(0)
        log(f"join {place_id}: {p['id']} sleeps in {sid}: the camp bed {r['id']} is off the town's walkable network")
        p["bed"] = {**bed, "space": sid, "ref": ref}
        p["home"] = sid
        for st in p.get("routine") or []:
            if st.get("at") == bed:
                st["at"] = p["bed"]
        moved += 1
    if moved:
        io.write_jsonl(pdir / "people.jsonl", [q for q in ppl if not q.get("_gone")])
    return moved


ARRIVAL_LEVEL = 64.0    # units: a door's arrival stands on mesh within this of its own height (the deck it lands on)
ARRIVAL_REACH = 288.0   # how far from where it was an arrival is moved to stand on the mesh


def arrivals(place_id: str, pdir: Path, W: Walkable, bases: dict, log=print) -> int:
    """Every door's arrival outside stands on the town's main walkable network of the built mesh, at its own level
    (on the deck or the ground it lands one on): one that does not is moved to the nearest point that does, on the
    same side of its door, outside every placed thing's body, at the mesh's height there. The partner door's `to_pos`
    and the door's `arrival` move together. Returns the arrivals moved."""
    from tools.places.draft import geom

    def level(q, z):   # the mesh's height at q on the main network at level z, else None
        c, dp, zz = W.near((q[0], q[1], z), tol=ON_TOL)
        m = W.main[c] & (np.abs(zz - z) <= ARRIVAL_LEVEL)
        return float(zz[m][np.argmin(dp[m])]) if m.any() else None
    ext = pdir / "spaces" / "exterior" / "refs.jsonl"
    rows = io.read_jsonl(ext)
    by_id = {r["id"]: r for r in rows}
    moved, inner_dirty = 0, {}
    for d in rows:
        a = (d.get("door") or {}).get("arrival")
        sid = (d.get("door") or {}).get("to_space")
        if d.get("kind") != "door" or not a or not sid or len(a) < 3:
            continue
        if level(a, a[2]) is not None:
            continue
        sup = by_id.get((d.get("seat") or {}).get("on"))
        near = [r for r in rows if r.get("kind") in geom.SOLID_KINDS and r is not d and r is not sup
                and math.dist(r["pos"][:2], a[:2]) < 2048]
        side = (a[0] - d["pos"][0], a[1] - d["pos"][1])
        got = None
        for r_ in np.arange(8.0, ARRIVAL_REACH + 1, 8.0):
            for k in range(32):
                q = (a[0] + r_ * math.cos(k * math.pi / 16), a[1] + r_ * math.sin(k * math.pi / 16))
                if (q[0] - d["pos"][0]) * side[0] + (q[1] - d["pos"][1]) * side[1] <= 0:
                    continue   # never behind its door
                z = level(q, a[2])
                if z is not None and not any(geom.stands_in(o, bases, (q[0], q[1], z)) for o in near):
                    got = [round(float(q[0]), 2), round(float(q[1]), 2), round(z, 2)]
                    break
            if got:
                break
        if got is None:
            log(f"join {place_id}: door {d['id']}: its arrival {[round(v) for v in a]} is off the walkable mesh, "
                f"with no point of it within {ARRIVAL_REACH:.0f} units")
            continue
        sp = pdir / "spaces" / sid / "refs.jsonl"
        inner = inner_dirty.get(sid) or (io.read_jsonl(sp) if sp.exists() else [])
        back = next((o for o in inner if (o.get("door") or {}).get("to_ref") == d["id"]), None)
        if back is None:
            continue
        yaw = math.atan2(got[0] - d["pos"][0], got[1] - d["pos"][1]) % (2 * math.pi)
        back["door"] = {**back["door"], "to_pos": got, "to_rot": [0.0, 0.0, round(yaw, 5)]}
        d["door"] = {**d["door"], "arrival": got}
        inner_dirty[sid] = inner
        moved += 1
        log(f"join {place_id}: door {d['id']}: arrival moved {math.dist(a[:2], got[:2]):.0f} units onto the walkable "
            f"mesh, z {a[2]:.0f} -> {got[2]:.0f}")
    if moved:
        io.write_jsonl(ext, rows)
        for sid, inner in inner_dirty.items():
            io.write_jsonl(pdir / "spaces" / sid / "refs.jsonl", inner)
    return moved


def streets(place_id: str, pdir: Path, W: Walkable, log=print) -> int:
    """Every street lies on the town's main walkable network of the built mesh: a stretch off it is re-laid along the
    way the mesh walks (`mend`), said in the street's `laid`; then each guard's patrol is taken again from the
    streets, every point on the network. Returns the changes (stretches re-laid and patrols changed)."""
    from tools.places.draft import people
    pj, fj = pdir / "paths.jsonl", pdir / "people.jsonl"
    paths = io.read_jsonl(pj) if pj.exists() else []
    n = 0
    for p in paths:
        got = mend(p, W)
        if got is None:
            log(f"join {place_id}: street {p['id']} has a stretch off the walkable network with no way round on it")
        elif got:
            n += got
            p["laid"] = f"{str(p.get('laid') or 'routed').split('; ')[0]}; re-laid on the built walkable network"
            log(f"join {place_id}: street {p['id']}: {got} stretch(es) re-laid on the built walkable network")
    if n:
        io.write_jsonl(pj, paths)
    folk = io.read_jsonl(fj) if fj.exists() else []
    guards = {io.mint(place_id, "person", "guard", str(k)): k for k in range(len(folk))}
    beats, changed = people.beats(paths), 0
    for g in folk:
        if g.get("role") != "guard" or g["id"] not in guards or not isinstance(g.get("patrol"), dict):
            continue
        pts = people.patrol(beats, guards[g["id"]], W.on)
        if not pts or pts == g["patrol"].get("points"):
            continue
        old = g.get("work")
        g["patrol"]["points"] = pts
        g["work"] = {**(old or {}), "space": "exterior", "pos": pts[0]}
        for st in g.get("routine") or []:
            if st.get("at") == old:
                st["at"] = g["work"]
        changed += 1
    if changed:
        io.write_jsonl(fj, folk)
        log(f"join {place_id}: {changed} guards' patrols taken again from the streets, on the walkable network")
    return n + changed


def join(place_id: str, places: Path = io.PLACES, out: Path = CHECK_OUT, log=print) -> int:
    """Build the place and read its walkable network; in each build round move the sleepers it does not reach
    (`rehome`), join every door's island to it by level walkway pieces, and once no island is left (or none can be
    joined) lay every street and patrol on it (`streets`); a round that changed what the mesh is built from (pieces,
    streets) builds again. Returns the changes made."""
    from tools.places import check as C
    pdir = places / place_id
    place = json.loads((pdir / "place.json").read_text())
    src = io.load(f"src.{place['source_id']}")
    grd = io.load(f"ground.{place_id}")
    bases = io.place_bases(src, grd, place)
    from tools.places.seat import Ground
    G = Ground.load(grd.path)
    G.apply_patches(io.read_jsonl(pdir / "land.jsonl") if (pdir / "land.jsonl").exists() else [])
    done = 0

    def settle():
        """The place files as they ship: reseated and in canonical order, so the build each round makes is the one
        `draft check` and the real build find unchanged."""
        from tools.places import edits
        from tools.places.seat import reseat_place
        reseat_place(place_id, places=places)
        edits.write_place(pdir, edits.load_place(pdir))
    settle()
    for _ in range(JOIN_ROUNDS):
        ctx, bad = network(place_id, places, out)
        if ctx is None:
            log(f"join {place_id}: the build failed: {bad[-1:]}")
            return done
        W = Walkable(ctx, standing(G), C.components(ctx["navs"], C.door_pairs(ctx)))
        # people moved to a reached bed change nothing the mesh is built from: no build round of their own
        moved = rehome(place_id, W, bases, src, pdir, log)
        isl = islands(ctx, W)
        if isl:
            rows = io.read_jsonl(pdir / "spaces" / "exterior" / "refs.jsonl")
            base = walk_base(rows, bases)
            if base is None:
                log(f"join {place_id}: no walkway piece to join islands with")
                return done
            have = {r["id"] for r in rows}
            net = dry(W.cent[W.main], G)
            new, joined = [], set()
            # every island in one round, each by its shortest clear level join to the network
            for door_id, (c, pts) in sorted(isl.items()):
                if c in joined:
                    continue
                for d, a, b in pairs(dry(pts, G), net)[:TRIES]:
                    n = max(1, math.ceil(math.dist(a[:2], b[:2]) / piece_length(bases, base)))
                    got = [r for r in lay(place_id, door_id, list(a), list(b), base, rows + new, bases, G)
                           if r["id"] not in have]
                    if len(got) == n:
                        new += got
                        have |= {r["id"] for r in got}
                        joined.add(c)
                        log(f"join {place_id}: door {door_id}: {n} pieces over {d:.0f} units, z {a[2]:.0f} -> {b[2]:.0f}")
                        break
            if new:
                done += len(new) + moved
                io.write_jsonl(pdir / "spaces" / "exterior" / "refs.jsonl", rows + new)
                settle()
                continue   # the joined islands are the network once built
            log(f"join {place_id}: no island ({', '.join(sorted(isl))}) has a clear walkable way to the network")
            moved += cut(place_id, sorted(isl), rows, pdir, log)
        got = arrivals(place_id, pdir, W, bases, log) + streets(place_id, pdir, W, log)
        done += got + moved
        if got or moved:
            settle()
        if not got:
            break
        # the streets mark the mesh's road triangles: the next round proves the new lines on the mesh built with them
    return done
