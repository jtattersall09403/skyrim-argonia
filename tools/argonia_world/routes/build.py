"""The road network and the route graph (2.W3 §b), written to the world database.

Geometry: the old chain solved every road and track and painted it into the land-cover raster (BC_ROAD 30 for the
major roads, TRACK 29 and PATH 27 for the minor network); the solved polylines themselves are not in the vault
(searched 2026-10-29: only the per-road length report and the structure windows are). So each land route is traced
back off its own paint: a least-cost path between its two ends over a 4-sample grid (7.3 m) whose cost is lowest on
its own surface, higher on the other surfaces, high on bare ground and highest on water (a bridge or ford), then
simplified (Douglas-Peucker, one grid step) so the staircase does not lengthen it. The old chain's own length per
major road (`major-routes-report.json`, fetched by regions/vault.py) is the independent check: the 3D length over the
2.W1 heights must match it within 5 %.

The route graph: a node per place, station and exit a route touches; an edge per route leg (land legs carry the
traced 3D length, water legs the straight length between their ends); landmarks are the places within 120 m of a land
leg. Signposts stand at every node where two or more land legs meet; each arm points at a leg's far end.

    python3 -m tools.argonia_world.routes.build build    trace, then write road, road_point, route_node, route_edge...
    python3 -m tools.argonia_world.routes.build check    L1: the graph connected; distances within 5 %
"""
from __future__ import annotations

import argparse
import heapq
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

from tools.argonia_world import db
from tools.argonia_world import skyrim_units as su
from tools.argonia_world.regions.cells import data_root

STRIDE = 4  # samples per search step
STEP_M = STRIDE * su.PROVINCE_SAMPLE_M
MARGIN_M = 1500.0  # the painted road may swing well wide of the line between its ends
COST = {"own": 1.0, "other": 2.5, "ground": 14.0, "water": 40.0}
ROAD_COVER, TRACK_COVER, PATH_COVER = 30, 29, 27
WIDTH = {"trunk": (6.0, 2.0), "road": (5.0, 2.0)}  # flat width, shoulder (m): old grade params flatWidthM 5, 2
TRACK_WIDTH_M = 2.5
LANDMARK_M = 120.0
TOLERANCE = 0.05


# --- geometry helpers ------------------------------------------------------------------------------------------------
def simplify(pts: list[tuple[float, float]], tol: float) -> list[tuple[float, float]]:
    """Douglas-Peucker."""
    if len(pts) < 3:
        return list(pts)
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        (x1, y1), (x2, y2) = pts[a], pts[b]
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy) or 1e-9
        best, k = -1.0, -1
        for i in range(a + 1, b):
            d = abs(dy * (pts[i][0] - x1) - dx * (pts[i][1] - y1)) / L
            if d > best:
                best, k = d, i
        if best > tol:
            keep[k] = True
            stack += [(a, k), (k, b)]
    return [p for p, f in zip(pts, keep) if f]


def length_2d(pts) -> float:
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def resample(pts, step: float) -> list[tuple[float, float]]:
    out = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(math.ceil(L / step)))
        out += [(a[0] + (b[0] - a[0]) * t / n, a[1] + (b[1] - a[1]) * t / n) for t in range(1, n + 1)]
    return out


class Ground:
    """Bilinear heights (m) of the 2.W1 ground at province metres (x east, y south)."""

    def __init__(self, root: Path | None = None):
        import numpy as np

        self.h = np.load((root or data_root()) / "terrain" / "refined-height-f32.npy", mmap_mode="r")

    def z(self, x: float, y: float) -> float:
        n = self.h.shape[0] - 1
        c, r = min(max(x / su.PROVINCE_SAMPLE_M, 0), n - 1e-6), min(max(y / su.PROVINCE_SAMPLE_M, 0), n - 1e-6)
        c0, r0 = int(c), int(r)
        fc, fr = c - c0, r - r0
        a, b = float(self.h[r0, c0]), float(self.h[r0, c0 + 1])
        cc, d = float(self.h[r0 + 1, c0]), float(self.h[r0 + 1, c0 + 1])
        return (a * (1 - fc) + b * fc) * (1 - fr) + (cc * (1 - fc) + d * fc) * fr

    def length_3d(self, pts, step: float = 1.0) -> float:
        s = resample(pts, step)
        zs = [self.z(x, y) for x, y in s]
        return sum(math.sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2 + (zb - za) ** 2)
                   for a, b, za, zb in zip(s, s[1:], zs, zs[1:]))


# --- tracing ---------------------------------------------------------------------------------------------------------
class Surface:
    """The land-cover paint and water at the search grid (STRIDE samples)."""

    def __init__(self, root: Path | None = None):
        import numpy as np

        r = root or data_root()
        cov = np.load(r / "terrain" / "landcover-i16.npy", mmap_mode="r")
        n = (cov.shape[0] - 1) // STRIDE
        bodies = np.load(r / "hydrology-graph-bodies.npz")
        h = np.load(r / "terrain" / "refined-height-f32.npy", mmap_mode="r")
        self.n = n
        self.road = np.zeros((n, n), bool)
        self.track = np.zeros((n, n), bool)
        self.water = np.zeros((n, n), bool)
        for j in range(0, n, 64):  # bands keep the working set small
            j1 = min(j + 64, n)
            cb = np.asarray(cov[j * STRIDE:j1 * STRIDE, :n * STRIDE]).reshape(j1 - j, STRIDE, n, STRIDE)
            self.road[j:j1] = (cb == ROAD_COVER).any(axis=(1, 3))
            self.track[j:j1] = ((cb == TRACK_COVER) | (cb == PATH_COVER)).any(axis=(1, 3))
            sb = np.asarray(bodies["sea"][j * STRIDE:j1 * STRIDE:STRIDE, :n * STRIDE:STRIDE])
            lv = np.asarray(bodies["level"][j * STRIDE:j1 * STRIDE:STRIDE, :n * STRIDE:STRIDE])
            hb = np.asarray(h[j * STRIDE:j1 * STRIDE:STRIDE, :n * STRIDE:STRIDE])
            self.water[j:j1] = sb | (lv > hb + 0.05)

    def cost(self, j: int, i: int, own: str) -> float:
        on_road, on_track = self.road[j, i], self.track[j, i]
        if (own == "road" and on_road) or (own == "track" and on_track):
            return COST["own"]
        if on_road or on_track:
            return COST["other"]
        return COST["water"] if self.water[j, i] else COST["ground"]

    def snap(self, x: float, y: float, own: str, radius_m: float = 250.0) -> tuple[int, int]:
        """The nearest search cell of the route's own surface to a point (or the point's own cell)."""
        j0, i0 = int(y / STEP_M), int(x / STEP_M)
        grid = self.road if own == "road" else self.track
        r = int(radius_m / STEP_M)
        best, at = None, (min(max(j0, 0), self.n - 1), min(max(i0, 0), self.n - 1))
        for j in range(max(j0 - r, 0), min(j0 + r + 1, self.n)):
            for i in range(max(i0 - r, 0), min(i0 + r + 1, self.n)):
                if grid[j, i]:
                    d = (j - j0) ** 2 + (i - i0) ** 2
                    if best is None or d < best:
                        best, at = d, (j, i)
        return at

    def trace(self, a: tuple[float, float], b: tuple[float, float], own: str) -> tuple[list, float]:
        """Least-cost path from a to b (province metres); (polyline in metres, share of steps on own surface)."""
        s, t = self.snap(*a, own), self.snap(*b, own)
        m = int(MARGIN_M / STEP_M)
        j0, j1 = max(min(s[0], t[0]) - m, 0), min(max(s[0], t[0]) + m, self.n - 1)
        i0, i1 = max(min(s[1], t[1]) - m, 0), min(max(s[1], t[1]) + m, self.n - 1)
        dist = {s: 0.0}
        prev = {}
        pq = [(0.0, s)]
        nb = [(-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0),
              (-1, -1, 1.4142), (-1, 1, 1.4142), (1, -1, 1.4142), (1, 1, 1.4142)]
        while pq:
            d, u = heapq.heappop(pq)
            if u == t:
                break
            if d > dist.get(u, math.inf):
                continue
            for dj, di, w in nb:
                v = (u[0] + dj, u[1] + di)
                if not (j0 <= v[0] <= j1 and i0 <= v[1] <= i1):
                    continue
                nd = d + w * 0.5 * (self.cost(*u, own) + self.cost(*v, own))
                if nd < dist.get(v, math.inf):
                    dist[v], prev[v] = nd, u
                    heapq.heappush(pq, (nd, v))
        path = [t]
        while path[-1] != s:
            path.append(prev[path[-1]])
        path.reverse()
        on = sum(1 for j, i in path if (self.road if own == "road" else self.track)[j, i]) / len(path)
        pts = [((i + 0.5) * STEP_M, (j + 0.5) * STEP_M) for j, i in path]
        return [a] + simplify(pts, STEP_M / 2) + [b], on


# --- the network -----------------------------------------------------------------------------------------------------
def place_by_name(w) -> dict[str, str]:
    """A route's end name (`stormhold`) -> the place it names (`place.dunmer-north.stormhold`)."""
    out = {}
    for r in w.query("SELECT id FROM place WHERE position_m_x IS NOT NULL ORDER BY id"):
        out.setdefault(r["id"].rsplit(".", 1)[-1], r["id"])
    return out


def exit_point(surface, side: str) -> tuple[float, float]:
    """Where an exit road's paint meets the province edge: its westmost or northmost road cell."""
    import numpy as np

    js, is_ = np.nonzero(surface.road)
    k = int(np.argmin(is_)) if side == "west" else int(np.argmin(js))
    x, y = (is_[k] + 0.5) * STEP_M, (js[k] + 0.5) * STEP_M
    return (0.0, y) if side == "west" else (x, 0.0)


EXITS = {"blackwood-road": "west", "tear-road": "north"}  # old 0069: the two attested exits
EXIT_NAMES = {"blackwood-road": "Leyawiin", "tear-road": "Tear"}  # where each road leads (its route row's notes)


def build(w, root: Path | None = None) -> dict:
    surface, ground = Surface(root), Ground(root)
    names = place_by_name(w)
    pos = {r["id"]: (r["position_m_x"], r["position_m_y"]) for r in w.query(
        "SELECT id, position_m_x, position_m_y FROM place WHERE position_m_x IS NOT NULL")}
    stations = {r["id"]: r for r in w.query("SELECT * FROM travel_station")}
    st_of_place = {r["place_id"]: r["id"] for r in stations.values() if r["place_id"]}
    ref = {}
    rep = (root or data_root()) / "regions" / "major-routes-report.json"
    if rep.exists():
        ref = {k: v["lengthKm"] * 1000 for k, v in json.loads(rep.read_text())["roads"].items()}
    nodes: dict[str, dict] = {}

    def node_for(name: str) -> str | None:
        if name in EXITS:
            nid = f"exit.{name}"
            if nid not in nodes:
                x, y = exit_point(surface, EXITS[name])
                nodes[nid] = {"id": nid, "kind": "exit", "place_id": None, "station_id": None, "x_m": x, "y_m": y,
                             "name": EXIT_NAMES[name]}
            return nid
        pid = names.get(name)
        if pid:
            nid = f"node.{pid}"
            nodes.setdefault(nid, {"id": nid, "kind": "place", "place_id": pid,
                                   "station_id": st_of_place.get(pid), "x_m": pos[pid][0], "y_m": pos[pid][1]})
            return nid
        sid = next((s for s in sorted(stations) if s.endswith("." + name)), None)
        if sid:
            s = stations[sid]
            nid = f"node.{sid}"
            nodes.setdefault(nid, {"id": nid, "kind": "station", "place_id": s["place_id"], "station_id": sid,
                                   "x_m": s["position_m_x"], "y_m": s["position_m_y"]})
            return nid
        return None

    roads, edges, skipped = [], [], []
    for r in w.query('SELECT id, "from" a, "to" b, mode, class FROM route ORDER BY id'):
        na, nb = node_for(r["a"]), node_for(r["b"])
        if not na or not nb or na == nb:
            skipped.append((r["id"], r["a"] if not na else r["b"] if not nb else "same ends"))
            continue
        A, B = (nodes[na]["x_m"], nodes[na]["y_m"]), (nodes[nb]["x_m"], nodes[nb]["y_m"])
        land = r["mode"] != "boat" and r["class"] != "channel"
        edge = {"id": f"edge.{r['id']}", "route_id": r["id"], "from_node_id": na, "to_node_id": nb,
                "mode": r["mode"], "from_chain_m": 0.0}
        if land:
            own = "road" if r["mode"] == "road" and r["class"] in WIDTH else "track"
            pts, on = surface.trace(A, B, own)
            L3 = ground.length_3d(pts)
            edge.update(length_m=round(L3, 1), to_chain_m=round(length_2d(pts), 1), _pts=pts, _on=on)
            fw, sh = WIDTH[r["class"]] if own == "road" else (TRACK_WIDTH_M, 0.0)
            roads.append({"route_id": r["id"], "surface_cover": ROAD_COVER if own == "road" else TRACK_COVER,
                          "flat_width_m": fw, "shoulder_m": sh, "length_m": round(length_2d(pts), 1),
                          "length_3d_m": round(L3, 1), "reference_length_m": ref.get(r["id"]), "_pts": pts,
                          "why": f"traced off its {'BC_ROAD' if own == 'road' else 'TRACK and PATH'} paint "
                                 f"({on:.0%} of the steps on it)"})
        else:
            edge.update(length_m=round(math.hypot(B[0] - A[0], B[1] - A[1]), 1), to_chain_m=None, _pts=None)
        edges.append(edge)
    joins = join(nodes, edges, ground)
    write(w, nodes, roads, edges, pos, root)
    return {"nodes": len(nodes), "edges": len(edges), "roads": len(roads), "skipped": skipped, "joins": joins}


def sub_polyline(pts, c0: float, c1: float) -> list[tuple[float, float]]:
    """The part of a polyline between two chainages (2D metres from its start)."""
    out, ch = [], 0.0
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        for t in sorted({max(0.0, min(1.0, (c - ch) / L)) if L else 0.0 for c in (c0, c1)} | {0.0, 1.0}):
            c = ch + t * L
            if c0 - 1e-6 <= c <= c1 + 1e-6:
                q = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
                if not out or math.hypot(q[0] - out[-1][0], q[1] - out[-1][1]) > 1e-6:
                    out.append(q)
        ch += L
    return out


def components(node_ids, edges) -> list[set]:
    adj = defaultdict(set)
    for e in edges:
        adj[e["from_node_id"]].add(e["to_node_id"])
        adj[e["to_node_id"]].add(e["from_node_id"])
    seen, out = set(), []
    for n in sorted(node_ids):
        if n in seen:
            continue
        comp, stack = set(), [n]
        while stack:
            u = stack.pop()
            if u not in comp:
                comp.add(u)
                stack += adj[u]
        seen |= comp
        out.append(comp)
    return sorted(out, key=lambda c: (-len(c), min(c)))


def join(nodes, edges, ground) -> list[str]:
    """Join each detached piece of the network to the main one where it physically meets it: the piece's node
    nearest any land leg of the main network gets a junction on that leg (the leg split there) and a spur to it.
    A minor track or a ferry pair whose end stands beside a road is reached from that road (old 0069 §3)."""
    done = []
    while True:
        comps = components(nodes, edges)
        if len(comps) == 1:
            return done
        main, rest = comps[0], [n for c in comps[1:] for n in sorted(c)]
        best = None
        for nid in rest:
            x, y = nodes[nid]["x_m"], nodes[nid]["y_m"]
            for e in edges:
                if e["from_node_id"] not in main or not e.get("_pts"):
                    continue
                ch = 0.0
                for a, b in zip(e["_pts"], e["_pts"][1:]):
                    dx, dy = b[0] - a[0], b[1] - a[1]
                    L = math.hypot(dx, dy) or 1e-9
                    t = max(0.0, min(1.0, ((x - a[0]) * dx + (y - a[1]) * dy) / (L * L)))
                    d = math.hypot(a[0] + t * dx - x, a[1] + t * dy - y)
                    if best is None or d < best[0]:
                        best = (d, nid, e, ch + t * L, (a[0] + t * dx, a[1] + t * dy))
                    ch += L
        d, nid, e, at, q = best
        total = e["to_chain_m"]
        if at < 30.0 or total - at < 30.0:  # at a leg's end: join to its end node
            jid = e["from_node_id"] if at < total / 2 else e["to_node_id"]
        else:
            jid = f"junction.{e['route_id'].split('.', 1)[1]}.{int(at)}"
            nodes[jid] = {"id": jid, "kind": "junction", "place_id": None, "station_id": None,
                          "x_m": round(q[0], 2), "y_m": round(q[1], 2)}
            pts = e["_pts"]
            a_pts, b_pts = sub_polyline(pts, 0.0, at), sub_polyline(pts, at, total)
            e2 = dict(e, id=f"{e['id']}.{int(at)}", from_node_id=jid, from_chain_m=round(e["from_chain_m"] + at, 1),
                      to_chain_m=round(e["from_chain_m"] + total, 1), length_m=round(ground.length_3d(b_pts), 1),
                      _pts=b_pts)
            e.update(to_node_id=jid, to_chain_m=round(e["from_chain_m"] + at, 1),
                     length_m=round(ground.length_3d(a_pts), 1), _pts=a_pts)
            edges.append(e2)
        piece_route = next(x["route_id"] for x in edges if nid in (x["from_node_id"], x["to_node_id"])) \
            if any(nid in (x["from_node_id"], x["to_node_id"]) for x in edges) else e["route_id"]
        spur = [(nodes[nid]["x_m"], nodes[nid]["y_m"]), (nodes[jid]["x_m"], nodes[jid]["y_m"])]
        edges.append({"id": f"edge.spur.{nid.split('.', 1)[1]}", "route_id": piece_route, "from_node_id": nid,
                      "to_node_id": jid, "mode": "track", "from_chain_m": None, "to_chain_m": None,
                      "length_m": round(max(ground.length_3d(spur), 0.1), 1), "_pts": None})
        done.append(f"{nid} -> {jid} ({d:.0f} m)")


def landmarks(pts, pos, ends) -> list[tuple[str, float]]:
    out = []
    chain = [0.0]
    for a, b in zip(pts, pts[1:]):
        chain.append(chain[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    for pid, (x, y) in pos.items():
        if pid in ends:
            continue
        best = None
        for k, (a, b) in enumerate(zip(pts, pts[1:])):
            dx, dy = b[0] - a[0], b[1] - a[1]
            L2 = dx * dx + dy * dy or 1e-9
            t = max(0.0, min(1.0, ((x - a[0]) * dx + (y - a[1]) * dy) / L2))
            d = math.hypot(a[0] + t * dx - x, a[1] + t * dy - y)
            if best is None or d < best[0]:
                best = (d, chain[k] + t * math.sqrt(L2))
        if best and best[0] <= LANDMARK_M:
            out.append((pid, round(best[1], 1)))
    return out


def structures(root: Path | None = None) -> list[dict]:
    out = []
    for f in sorted(((root or data_root()) / "regions").glob("road-*.json")):
        d = json.loads(f.read_text())
        for p in d.get("placements", []):
            x, z, y = p["posM"]  # the old kit's frame: x east, y up, z south
            out.append({"id": p["id"], "route_id": d["wayId"], "role": p["role"], "from_m": p["fromM"],
                        "to_m": p["toM"], "x_m": x, "y_m": y, "z_m": z, "yaw_deg": p["yawDeg"],
                        "old_piece": p["assetId"]})
    return out


def write(w, nodes, roads, edges, pos, root) -> None:
    for t in ("signpost_arm", "signpost", "route_edge_landmark", "route_edge", "route_node", "road_structure",
              "road_point", "road"):
        w.con.execute(f'DELETE FROM "{t}"')
        w.dirty.add(t)
    w.insert_many("route_node", [nodes[k] for k in sorted(nodes)])
    for r in roads:
        pts = r.pop("_pts")
        w.insert("road", r)
        w.insert_many("road_point", [{"route_id": r["route_id"], "ord": k, "x_m": round(x, 2), "y_m": round(y, 2)}
                                     for k, (x, y) in enumerate(pts)])
    road_ids = {r["route_id"] for r in roads}
    w.insert_many("road_structure", [s for s in structures(root) if s["route_id"] in road_ids])
    deg = defaultdict(list)
    for e in edges:
        pts = e.pop("_pts")
        e.pop("_on", None)
        w.insert("route_edge", e)
        if pts:
            ends = {nodes[e["from_node_id"]]["place_id"], nodes[e["to_node_id"]]["place_id"]}
            for pid, at in landmarks(pts, pos, ends):
                w.insert("route_edge_landmark", edge_id=e["id"], place_id=pid, at_m=at)
            deg[e["from_node_id"]].append((e, pts[1] if len(pts) > 1 else pts[-1], e["to_node_id"]))
            deg[e["to_node_id"]].append((e, pts[-2] if len(pts) > 1 else pts[0], e["from_node_id"]))
    for nid, legs in sorted(deg.items()):
        if len(legs) < 2 or nodes[nid]["kind"] == "exit":
            continue
        n = nodes[nid]
        sid = f"sign.{nid.split('.', 1)[1]}"
        arms, named = [], set()
        for e, toward, far in sorted(legs, key=lambda x: x[0]["id"]):
            far = named_beyond(deg, nodes, nid, far, e)
            if far in named or far == nid:
                continue  # one arm per destination: the first leg (by id) that reaches it
            named.add(far)
            bearing = math.degrees(math.atan2(toward[0] - n["x_m"], -(toward[1] - n["y_m"]))) % 360
            arms.append({"signpost_id": sid, "ord": len(arms), "to_node_id": far, "bearing_deg": round(bearing, 1)})
        if len(arms) < 2:
            continue
        w.insert("signpost", id=sid, node_id=nid, x_m=n["x_m"], y_m=n["y_m"], yaw_deg=arms[0]["bearing_deg"])
        w.insert_many("signpost_arm", arms)


def named_beyond(deg, nodes, start: str, cur: str, edge: dict) -> str:
    """The first node with a name (a place, station or exit) reached from `start` along `edge` and on through
    junctions, keeping to the leg's own route where a junction offers it. A signpost arm reads that node's name, so
    an arm never points at a nameless junction."""
    prev, seen = start, {start}
    while nodes[cur]["kind"] == "junction" and cur not in seen:
        seen.add(cur)
        onward = [x for x in deg[cur] if x[2] != prev]
        if not onward:
            break
        same = [x for x in onward if x[0]["route_id"] == edge["route_id"]]
        edge, _, nxt = sorted(same or onward, key=lambda x: x[0]["id"])[0]
        prev, cur = cur, nxt
    return cur


# --- checks ----------------------------------------------------------------------------------------------------------
def check(w, root: Path | None = None) -> tuple[list[str], dict]:
    errs = []
    nodes = w.values("SELECT id FROM route_node")
    adj = defaultdict(set)
    for e in w.query("SELECT from_node_id a, to_node_id b, mode FROM route_edge"):
        adj[e["a"]].add(e["b"])
        adj[e["b"]].add(e["a"])

    def components(keep) -> list[set]:
        seen, comps = set(), []
        for n in sorted(keep):
            if n in seen:
                continue
            comp, stack = set(), [n]
            while stack:
                u = stack.pop()
                if u in comp:
                    continue
                comp.add(u)
                stack += [v for v in adj[u] if v in keep]
            seen |= comp
            comps.append(comp)
        return comps

    comps = components(set(nodes))
    if len(comps) != 1:
        sizes = sorted((len(c) for c in comps), reverse=True)
        errs.append(f"graph: {len(comps)} components (sizes {sizes[:8]}); smallest: "
                    f"{sorted(min(comps, key=len))[:3]}")
    ground = Ground(root)
    worst = 0.0
    for r in w.query("SELECT id, route_id, length_m, from_chain_m c0, to_chain_m c1 FROM route_edge "
                     "WHERE to_chain_m IS NOT NULL"):
        pts = [(p["x_m"], p["y_m"]) for p in w.query(
            "SELECT x_m, y_m FROM road_point WHERE route_id = ? ORDER BY ord", r["route_id"])]
        if not pts:
            continue
        L = ground.length_3d(sub_polyline(pts, r["c0"], r["c1"]), 0.5)
        dev = abs(r["length_m"] - L) / L
        worst = max(worst, dev)
        if dev > TOLERANCE:
            errs.append(f"{r['id']}: stored {r['length_m']} m vs terrain {L:.1f} m ({dev:.1%})")
    ref_dev = {}
    for r in w.query("SELECT route_id, length_m, length_3d_m, reference_length_m FROM road"):
        if r["reference_length_m"]:
            dev = (r["length_3d_m"] - r["reference_length_m"]) / r["reference_length_m"]
            ref_dev[r["route_id"]] = round(dev, 4)
            if abs(dev) > TOLERANCE:
                errs.append(f"{r['route_id']}: 3D {r['length_3d_m']} m vs the old chain's {r['reference_length_m']} m "
                            f"({dev:+.1%})")
    return errs, {"components": len(comps), "worst_terrain_dev": worst, "reference_dev": ref_dev}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cmd", choices=("build", "check"))
    a = ap.parse_args(argv)
    w = db.open()
    if a.cmd == "build":
        rep = build(w)
        w.save()
        print(f"nodes {rep['nodes']}, edges {rep['edges']}, roads {rep['roads']}; skipped {len(rep['skipped'])}:")
        for s in rep["skipped"]:
            print("  ", *s)
        print(f"joins {len(rep['joins'])}:", *rep["joins"], sep="\n   ")
    errs, m = check(w)
    print(f"check: {m['components']} component(s), worst terrain deviation {m['worst_terrain_dev']:.2%}; "
          f"against the old chain: {m['reference_dev']}")
    print("\n".join(errs))
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
