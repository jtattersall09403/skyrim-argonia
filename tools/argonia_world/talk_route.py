"""Directions as routes (docs/phases/4a-talk-to-everyone.md, recipe v2 rule 1): from a speaker's placed ref to a
target (a ref or a map marker), a walkable or swimmable route over BM&V's loaded world, told as Morrowind-style legs
with real landmarks at the turns, each waypoint with its form key.

The world (cached in out/talk_route/<worldspace>.pkl by `cache`): the winning navmesh triangles (walk; the water
flag), LAND heights against the cell's water height (shore, open water, islands), and every exterior REFR whose base
is a thing a person would name (wreck, ship, shrine, big tree, ruin, hut, dock, bridge, camp, signpost, map marker);
roads, docks and bridges from their statics.

The route: A* on a grid (GRID units a square): road, dock and bridge squares cost 0.8, navmesh 1, bare land 2.5,
water (ground under the water line) 3 (swimming); steep bare land is closed. The path is cut into legs by kind
(walk, road, shore, bridge, dock, swim, climb) and at its turns (Douglas-Peucker, TURN units); each leg ends at the
most notable landmark within REACH of its end, with its side. A target under CLOSE in a near-straight line is given
as paces and a compass point only.

    python3 -m tools.argonia_world.talk_route cache    [--world 23D689:Black Marsh.esm]
    python3 -m tools.argonia_world.talk_route route    --from REF --to REF|MARKER|x,y [--json]
    python3 -m tools.argonia_world.talk_route facts    --settlement bmv.lilmoth [--write]   # every directions fact
"""
from __future__ import annotations

import argparse
import heapq
import json
import math
import pickle
import re
import struct
import sys
from pathlib import Path

from tools.argonia_world import bmv_census as bc
from tools.argonia_world import db

WORLD = "23D689:Black Marsh.esm"
CACHE = db.REPO / "out/talk_route"
GRID = 192.0            # units a square (2.7 m)
UNITS_M = 70.0
PACE = 52.5             # units a pace (0.75 m)
CLOSE = 60 * UNITS_M    # under this, in a near-straight line: paces and a compass point
TURN = 700.0            # Douglas-Peucker tolerance: a bend this far off the line is a turn
REACH = 1600.0          # a leg's landmark lies this close to its end
MIN_LEG = 1400.0        # a run shorter than this merges into the one before
MAX_LEGS = 6            # a longer telling keeps only its longest legs, merged at the short ones
CLIMB = 700.0           # a leg rising this much is a climb
WATER_FLAG = 0x0200     # NVNM triangle flag: on water
BASE_SIGS = {"STAT", "SCOL", "TREE", "ACTI", "FURN", "CONT", "FLOR", "DOOR", "LIGH", "MSTT"}

# What a person calls a thing, from its base's model path or editor id (lower case), most notable first: kind,
# pattern, the phrase (what the player sees), weight.
LANDMARK = [
    ("wreck", r"wreck|sunken", "the wrecked ship", 9, 600),
    ("ship", r"shiplarge|shipimperial|imperialship|shipsail|longboat|caravel|carrack|galleon|daintysload",
     "the big ship", 9, 1800),
    ("rowboat", r"rowboat", "the rowing boat", 6, 400),
    ("boat", r"(?<![a-z])boat|canoe", "the boat", 6, 400),
    ("shrine", r"shrine", "the wayshrine", 8, 300),
    ("statue", r"statue|totem|idol|obelisk|monument|standingstone", "the standing stone", 8, 300),
    ("hist", r"(?<![a-z])hist(?!le)", "the Hist tree", 9, 600),
    ("bigtree", r"treegiant|giant.?tree|treemere|bigtree|tree.*(huge|large|giant|big)", "the great tree", 7, 1200),
    ("ruinhouse", r"destroyed|burnt|burned", "the ruined house", 7, 900),
    ("ruin", r"ruins?|xanmeer|ziggurat|ayleid|dwemer", "the ruin", 8, 900),
    ("lighthouse", r"lighthouse(?!fire)", "the lighthouse", 9, 1000),
    ("tower", r"tower", "the tower", 7, 900),
    ("bridge", r"bridge", "the bridge", 7, 600),
    ("dock", r"\\docks?\\|dock\d|dockstr|dockpier|pier|jetty", "the dock", 6, 500),
    ("hut", r"hut", "the hut", 5, 500),
    ("house", r"house|haus|manor|longhs", "the house", 5, 800),
    ("tent", r"tent(?!acle)", "the tent", 5, 300),
    ("signpost", r"signpost|roadsign|directionsign", "the signpost", 8, 0),
    ("well", r"\\well|well\d", "the well", 5, 200),
    ("cart", r"cart\b|cart\d|wagon", "the cart", 4, 300),
    ("spit", r"firespit|campfire|firepit", "the cooking fire", 4, 250),
    ("cave", r"caveentr|cave.*entrance|mineentr", "the cave mouth", 7, 300),
]
NOT_LANDMARK = re.compile(r"ingrd|flora|workbench|wall|roof|stair|porch|int\d*$|int\.nif|clutter|lighthousefire|"
                          r"rock|door")
LANDMARK_RX = [(k, re.compile(p), ph, w, mn) for k, p, ph, w, mn in LANDMARK]
ROAD = re.compile(r"road|\\path|path\d|cobble|trail")
BRIDGE = re.compile(r"bridge")
DOCK = re.compile(r"\\docks?\\|dock\d|dockstr|dockpier|pier|jetty|walkway|boardwalk")
COMPASS = ["east", "east-north-east", "north-east", "north-north-east", "north", "north-north-west", "north-west",
           "west-north-west", "west", "west-south-west", "south-west", "south-south-west", "south", "south-south-east",
           "south-east", "east-south-east"]


def compass(dx: float, dy: float, points: int = 16) -> str:
    a = math.degrees(math.atan2(dy, dx)) % 360
    return COMPASS[(round(a / (360 / points)) % points) * (16 // points)]


def _path(world: str) -> Path:
    return CACHE / f"{world.replace(':', '_').replace(' ', '_')}.pkl"


# --- the world: read once, cached ------------------------------------------------------------------------------------

def _vhgt(d: bytes) -> list[list[float]]:
    h = struct.unpack_from("<1089b", d, 4)
    out, row = [], struct.unpack_from("<f", d)[0] * 8
    for r in range(33):
        row += h[r * 33] * 8
        v, line = row, [row]
        for c in range(1, 33):
            v += h[r * 33 + c] * 8
            line.append(v)
        out.append(line)
    return out


def cache(world: str = WORLD) -> Path:
    """Read the load order's world for `world` into out/talk_route/<world>.pkl."""
    L = bc.Load()
    res = bc.Resolver(L, bc.MASTERS, BASE_SIGS)
    wrld = L.win(world)
    dn = wrld.sub("DNAM") if wrld else None
    default_water = struct.unpack_from("<2f", dn)[1] if dn else 0.0
    cells: dict[str, tuple] = {}
    for c in L.live("CELL"):
        if L.world_key(c) != world or bc.is_interior(c) or not c.sub("XCLC"):
            continue
        gx, gy = struct.unpack_from("<2i", c.sub("XCLC"))
        wl = c.sub("XCLW")
        water = struct.unpack("<f", wl[:4])[0] if wl else default_water
        cells[c.key] = (gx, gy, None if abs(water) > 1e9 else water)
    water = {(gx, gy): wl for gx, gy, wl in cells.values()}
    land = {}
    for r in L.live("LAND"):
        ck = L.cell_key(r)
        if ck in cells and r.sub("VHGT"):
            land[cells[ck][:2]] = _vhgt(r.sub("VHGT"))
    tris = []
    for r in L.live("NAVM"):
        if L.world_key(r) != world or not r.sub("NVNM"):
            continue
        d = r.sub("NVNM")
        nv = struct.unpack_from("<I", d, 16)[0]
        V = [struct.unpack_from("<3f", d, 20 + 12 * i) for i in range(nv)]
        o = 20 + 12 * nv
        nt = struct.unpack_from("<I", d, o)[0]
        o += 4
        for i in range(nt):
            a, b, c, _, _, _, fl = struct.unpack_from("<7H", d, o + 16 * i)
            if max(a, b, c) < nv:
                tris.append((V[a], V[b], V[c], bool(fl & WATER_FLAG)))
    refs = []
    for r in L.live("REFR"):
        if r.flags & bc.DISABLED or L.world_key(r) != world or not r.sub("DATA"):
            continue
        bk = r.ref("NAME")
        base = res.win.get(bk)
        is_marker = bk == bc.MAPMARKER
        if base is None and not is_marker:
            continue
        x, y, z = struct.unpack_from("<3f", r.sub("DATA"))
        xs = r.sub("XSCL")
        scale = struct.unpack("<f", xs)[0] if xs else 1.0
        o = base.sub("OBND") if base else None
        size = 0.0
        if o:
            b = struct.unpack("<6h", o)
            size = max(b[3] - b[0], b[4] - b[1], b[5] - b[2]) * scale
        marker = r.zstr("FULL") if is_marker and r.sub("FULL") else None
        if is_marker and not marker:
            continue
        refs.append({"key": r.key, "base": bk, "sig": base.sig if base else "STAT",
                     "edid": (base.edid if base else "MapMarker") or "",
                     "model": (base.zstr("MODL") if base else "") or "",
                     "name": base.name if base else None, "marker": marker, "x": x, "y": y, "z": z, "size": size})
    CACHE.mkdir(parents=True, exist_ok=True)
    p = _path(world)
    p.write_bytes(pickle.dumps({"world": world, "land": land, "water": water, "default_water": default_water,
                                "tris": tris, "refs": refs}))
    print(f"cached {p}: {len(land)} LAND, {len(tris)} navmesh triangles, {len(refs)} refs")
    return p


class World:
    def __init__(self, world: str = WORLD, names: dict[str, str] | None = None):
        p = _path(world)
        if not p.exists():
            cache(world)
        d = pickle.loads(p.read_bytes())
        self.land, self.water, self.dw, self.tris, self.refs = (d["land"], d["water"], d["default_water"],
                                                                d["tris"], d["refs"])
        self.by_key = {r["key"]: r for r in self.refs}
        for r in self.refs:
            text = (r["model"] + " " + r["edid"]).lower()
            r["lm"] = ("marker", (names or {}).get(r["marker"], r["marker"]), 10) if r["marker"] else None
            if r["lm"]:
                continue
            if NOT_LANDMARK.search(r["edid"].lower()) or NOT_LANDMARK.search(r["model"].lower().rsplit("\\", 1)[-1]):
                continue
            for k, rx, ph, w, mn in LANDMARK_RX:
                if rx.search(text) and r["size"] >= mn:
                    named = r["name"] if r["name"] and k in ("shrine", "statue", "ruin", "ship") else None
                    r["lm"] = (k, named or ph, w + min(3.0, r["size"] / 1500))
                    break

    def height(self, x: float, y: float) -> float | None:
        gx, gy = math.floor(x / 4096), math.floor(y / 4096)
        h = self.land.get((gx, gy))
        if h is None:
            return None
        c = min(32, max(0, round((x - gx * 4096) / 128)))
        r = min(32, max(0, round((y - gy * 4096) / 128)))
        return h[r][c]

    def water_at(self, x: float, y: float) -> float | None:
        return self.water.get((math.floor(x / 4096), math.floor(y / 4096)), self.dw)


# --- the grid and the search -------------------------------------------------------------------------------------------

class Grid:
    """The squares of a box around the start and the target: kind nav, navwater, land, water, steep or void; tag
    road, dock or bridge from the refs standing on it."""

    def __init__(self, W: World, x0: float, y0: float, x1: float, y1: float):
        pad = 4096 * 1.5
        self.ox, self.oy = min(x0, x1) - pad, min(y0, y1) - pad
        self.nx = int((max(x0, x1) + pad - self.ox) // GRID) + 1
        self.ny = int((max(y0, y1) + pad - self.oy) // GRID) + 1
        n = self.nx * self.ny
        self.h, self.kind, self.tag = [0.0] * n, ["land"] * n, [""] * n
        for j in range(self.ny):
            for i in range(self.nx):
                x, y = self.xy(i, j)
                h, wl, k = W.height(x, y), W.water_at(x, y), j * self.nx + i
                if h is None:
                    self.kind[k] = "void"
                    continue
                self.h[k] = h
                if wl is not None and h < wl - 40:
                    self.kind[k] = "water"
        for j in range(self.ny - 1):
            for i in range(self.nx - 1):
                k = j * self.nx + i
                if self.kind[k] == "land" and max(abs(self.h[k + 1] - self.h[k]),
                                                  abs(self.h[k + self.nx] - self.h[k])) > GRID * 1.1:
                    self.kind[k] = "steep"
        bx1, by1 = self.ox + self.nx * GRID, self.oy + self.ny * GRID
        for a, b, c, wat in W.tris:
            xs, ys = (a[0], b[0], c[0]), (a[1], b[1], c[1])
            if max(xs) < self.ox or min(xs) > bx1 or max(ys) < self.oy or min(ys) > by1:
                continue
            i0, i1 = int((min(xs) - self.ox) // GRID), int((max(xs) - self.ox) // GRID)
            j0, j1 = int((min(ys) - self.oy) // GRID), int((max(ys) - self.oy) // GRID)
            for j in range(max(0, j0), min(self.ny, j1 + 1)):
                for i in range(max(0, i0), min(self.nx, i1 + 1)):
                    x, y = self.xy(i, j)
                    if (i0 == i1 and j0 == j1) or _in_tri(x, y, a, b, c):
                        k = j * self.nx + i
                        self.kind[k] = "navwater" if wat else "nav"
                        self.h[k] = (a[2] + b[2] + c[2]) / 3
        for r in W.refs:
            m = (r["model"] + " " + r["edid"]).lower()
            tag = "bridge" if BRIDGE.search(m) else "dock" if DOCK.search(m) else "road" if ROAD.search(m) else ""
            if not tag or not (self.ox <= r["x"] <= bx1 and self.oy <= r["y"] <= by1):
                continue
            rad = max(GRID, r["size"] / 2 * (0.6 if tag == "road" else 0.8))
            for j in range(int((r["y"] - rad - self.oy) // GRID), int((r["y"] + rad - self.oy) // GRID) + 1):
                for i in range(int((r["x"] - rad - self.ox) // GRID), int((r["x"] + rad - self.ox) // GRID) + 1):
                    if 0 <= i < self.nx and 0 <= j < self.ny:
                        k = j * self.nx + i
                        if self.kind[k] in ("water", "steep", "void"):
                            self.kind[k] = "nav"      # a deck or a bridge over water or a slope is walked
                        if self.tag[k] in ("", "road"):
                            self.tag[k] = tag

    def xy(self, i: int, j: int) -> tuple[float, float]:
        return self.ox + (i + 0.5) * GRID, self.oy + (j + 0.5) * GRID

    def ij(self, x: float, y: float) -> tuple[int, int]:
        return int((x - self.ox) // GRID), int((y - self.oy) // GRID)

    def cost(self, k: int) -> float | None:
        kd = self.kind[k]
        if kd in ("steep", "void"):
            return None
        if self.tag[k]:
            return 0.8
        return {"nav": 1.0, "navwater": 1.6, "land": 2.5, "water": 3.0}[kd]

    def nearest_open(self, i: int, j: int) -> int:
        for r in range(40):
            for dj in range(-r, r + 1):
                for di in range(-r, r + 1):
                    ii, jj = i + di, j + dj
                    if 0 <= ii < self.nx and 0 <= jj < self.ny and self.cost(jj * self.nx + ii) is not None:
                        return jj * self.nx + ii
        return j * self.nx + i

    def astar(self, s: int, t: int) -> list[int]:
        nx, tx, ty = self.nx, t % self.nx, t // self.nx
        g, came, pq = {s: 0.0}, {}, [(0.0, s)]
        steps = [(1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414),
                 (-1, -1, 1.414)]
        while pq:
            _, u = heapq.heappop(pq)
            if u == t:
                break
            ux, uy, gu = u % nx, u // nx, g[u]
            for dx, dy, dl in steps:
                vx, vy = ux + dx, uy + dy
                if not (0 <= vx < nx and 0 <= vy < self.ny):
                    continue
                v = vy * nx + vx
                c = self.cost(v)
                if c is None:
                    continue
                ng = gu + c * dl
                if ng < g.get(v, 1e18):
                    g[v], came[v] = ng, u
                    heapq.heappush(pq, (ng + 0.8 * math.hypot(vx - tx, vy - ty), v))
        if t not in came and s != t:
            return []
        path, u = [t], t
        while u != s:
            u = came[u]
            path.append(u)
        return path[::-1]


def _in_tri(x, y, a, b, c) -> bool:
    d1 = (x - b[0]) * (a[1] - b[1]) - (a[0] - b[0]) * (y - b[1])
    d2 = (x - c[0]) * (b[1] - c[1]) - (b[0] - c[0]) * (y - c[1])
    d3 = (x - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (y - a[1])
    return not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0))


def _rdp(pts: list[tuple], eps: float) -> list[int]:
    """Indices kept by the Douglas-Peucker simplification of pts."""
    out = [0]

    def rec(a: int, b: int) -> None:
        (x0, y0), (x1, y1) = pts[a][:2], pts[b][:2]
        ln = math.hypot(x1 - x0, y1 - y0) or 1.0
        best, bi = 0.0, None
        for i in range(a + 1, b):
            d = abs((x1 - x0) * (y0 - pts[i][1]) - (x0 - pts[i][0]) * (y1 - y0)) / ln
            if d > best:
                best, bi = d, i
        if bi is not None and best > eps:
            rec(a, bi)
            out.append(bi)
            rec(bi, b)
    rec(0, len(pts) - 1)
    return out + [len(pts) - 1]


# --- the route as legs ---------------------------------------------------------------------------------------------

def _mode(G: Grid, k: int) -> str:
    if G.tag[k] in ("bridge", "dock"):
        return G.tag[k]
    if G.kind[k] == "water":
        return "swim"
    if G.tag[k] == "road":
        return "road"
    i, j = k % G.nx, k // G.nx
    for dj in (-2, 0, 2):
        for di in (-2, 0, 2):
            ii, jj = i + di, j + dj
            if 0 <= ii < G.nx and 0 <= jj < G.ny and G.kind[jj * G.nx + ii] in ("water", "navwater"):
                return "shore"
    return "walk"


def _landmark(W: World, x: float, y: float, used: set, heading: tuple) -> dict | None:
    best, bs = None, -1e9
    for r in W.refs:
        reach = REACH * (2 if r["lm"] and r["lm"][0] == "marker" else 1)
        if not r["lm"] or r["key"] in used or abs(r["x"] - x) > reach or abs(r["y"] - y) > reach:
            continue
        d = math.hypot(r["x"] - x, r["y"] - y)
        if d <= reach and r["lm"][2] - d / 400 > bs:
            best, bs = r, r["lm"][2] - d / 400
    if best is None:
        return None
    cx, cy = best["x"] - x, best["y"] - y
    side = "ahead"
    if math.hypot(cx, cy) > 300:
        side = "on your left" if heading[0] * cy - heading[1] * cx > 0 else "on your right"
    return {"key": best["key"], "what": best["lm"][1], "kind": best["lm"][0], "x": round(best["x"]),
            "y": round(best["y"]), "side": side}


def _island(G: Grid, k: int, start: int) -> bool:
    """True when the land at k is a small piece the start's land does not reach without water."""
    seen, todo = {k}, [k]
    while todo and len(seen) < 4000:
        u = todo.pop()
        if u == start:
            return False
        ux, uy = u % G.nx, u // G.nx
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            vx, vy = ux + dx, uy + dy
            v = vy * G.nx + vx
            if 0 <= vx < G.nx and 0 <= vy < G.ny and v not in seen and (G.kind[v] in ("land", "nav", "steep")
                                                                           or G.tag[v]):
                seen.add(v)
                todo.append(v)
    return len(seen) < 4000


def route(W: World, sx: float, sy: float, tx: float, ty: float, target: str) -> dict:
    straight = math.hypot(tx - sx, ty - sy)
    out = {"from": (round(sx), round(sy)), "to": target, "to_xy": (round(tx), round(ty)),
           "straight_m": round(straight / UNITS_M), "bearing": compass(tx - sx, ty - sy)}
    G = Grid(W, sx, sy, tx, ty)
    s, t = G.nearest_open(*G.ij(sx, sy)), G.nearest_open(*G.ij(tx, ty))
    path = G.astar(s, t)
    if not path:
        out.update(kind="none", legs=[])
        return out
    pts = [(*G.xy(k % G.nx, k // G.nx), G.h[k], _mode(G, k)) for k in path]
    seg = lambda a, b: math.hypot(pts[b][0] - pts[a][0], pts[b][1] - pts[a][1])
    length = sum(seg(i, i + 1) for i in range(len(pts) - 1))
    out["route_m"] = round(length / UNITS_M)
    if straight < CLOSE and length < straight * 1.35 + 600:
        out.update(kind="close", paces=round(straight / PACE), legs=[])
        return out
    runs, cur = [], [0]                 # runs of one mode; a short run joins the one before
    for i in range(1, len(pts)):
        if pts[i][3] != pts[cur[0]][3]:
            runs.append(cur)
            cur = [i - 1]
        cur.append(i)
    runs.append(cur)
    merged = []
    for r in runs:
        ln = sum(seg(r[i], r[i + 1]) for i in range(len(r) - 1))
        keep = ln >= MIN_LEG or (pts[r[0]][3] in ("bridge", "swim") and ln >= 400)
        if merged and not keep:
            merged[-1] += r[1:]
        else:
            merged.append(list(r))
    legs, used = [], set()
    for r in merged:
        mode = max(("walk", "road", "shore", "bridge", "dock", "swim"), key=lambda m: sum(pts[i][3] == m for i in r))
        sub = [pts[i] for i in r]
        cut = _rdp(sub, TURN * (2 if mode == "swim" else 1))
        for a, b in zip(cut, cut[1:]):
            p0, p1 = sub[a], sub[b]
            dx, dy = p1[0] - p0[0], p1[1] - p0[1]
            d = math.hypot(dx, dy)
            if d < MIN_LEG / 2 and legs:
                continue
            kind = "climb" if mode in ("walk", "road", "shore") and p1[2] - p0[2] > CLIMB else mode
            legs.append({"kind": kind, "heading": compass(dx, dy), "m": round(d / UNITS_M), "paces": round(d / PACE),
                         "start": (round(p0[0]), round(p0[1])), "end": (round(p1[0]), round(p1[1])),
                         "_h": (dx / (d or 1), dy / (d or 1))})
    legs = _merge(legs)
    used.add(target)
    for n, lg in enumerate(legs):
        lm = None if n == len(legs) - 1 else _landmark(W, *lg["end"], used, lg["_h"])
        if lm:
            used.add(lm["key"])
        lg["landmark"] = lm
        if lg["kind"] == "swim":
            lg["island"] = _island(G, G.nearest_open(*G.ij(*lg["end"])), s)
        del lg["_h"]
    out.update(kind="route", legs=legs)
    return out


def _join(a: dict, b: dict) -> dict:
    dx, dy = b["end"][0] - a["start"][0], b["end"][1] - a["start"][1]
    d = math.hypot(dx, dy)
    kind = a["kind"] if a["m"] >= b["m"] else b["kind"]
    return {"kind": kind, "heading": compass(dx, dy), "m": round(d / UNITS_M), "paces": round(d / PACE),
            "start": a["start"], "end": b["end"], "_h": (dx / (d or 1), dy / (d or 1))}


def _merge(legs: list[dict]) -> list[dict]:
    """Neighbours of one kind and heading become one leg; then the shortest leg joins a neighbour until MAX_LEGS
    remain (a swim or a bridge is never merged away while another can go)."""
    out = []
    for lg in legs:
        if out and out[-1]["kind"] == lg["kind"] and out[-1]["heading"] == lg["heading"]:
            out[-1] = _join(out[-1], lg)
        else:
            out.append(lg)
    while len(out) > MAX_LEGS:
        i = min(range(len(out)), key=lambda n: out[n]["m"] * (3 if out[n]["kind"] in ("swim", "bridge") else 1))
        j = i - 1 if i == len(out) - 1 or (i > 0 and out[i - 1]["m"] < out[i + 1]["m"]) else i + 1
        a, b = sorted((i, j))
        out[a:b + 1] = [_join(out[a], out[b])]
    n = 0
    while n < len(out) - 1:
        if out[n]["kind"] == out[n + 1]["kind"] and out[n]["heading"] == out[n + 1]["heading"]:
            out[n:n + 2] = [_join(out[n], out[n + 1])]
        else:
            n += 1
    return out


VERB = {"walk": "walk {h}", "road": "follow the path {h}", "shore": "follow the shore {h}",
        "bridge": "cross the bridge {h}", "dock": "go along the boards {h}", "swim": "swim {h}", "climb": "climb {h}"}


def describe(r: dict, target_name: str) -> str:
    """A plain, neutral telling of the route: the writer re-tells it in the speaker's own voice."""
    if r["kind"] == "close":
        text = f"{target_name} is about {r['paces']} paces {r['bearing']} of here, in sight."
        return text[0].upper() + text[1:]
    if r["kind"] == "none":
        return f"{target_name} lies about {r['straight_m']} m {r['bearing']} of here; no way on foot was found."
    bits = []
    for lg in r["legs"]:
        v = VERB[lg["kind"]].format(h=lg["heading"])
        if lg["kind"] == "swim" and lg.get("island"):
            v = f"swim to the island you can see to the {lg['heading']}"
        s = f"{v} about {lg['paces']} paces"
        if lg["landmark"]:
            s += f" until {lg['landmark']['what']} ({lg['landmark']['side']})"
        bits.append(s)
    bits[-1] += f", and {target_name} is there"
    text = "; then ".join(bits)
    return text[0].upper() + text[1:] + "."


def source(r: dict, speaker: str, target: str) -> str:
    wps = [f"{lg['landmark']['key']} {lg['landmark']['what']} ({lg['landmark']['x']}, {lg['landmark']['y']})"
           for lg in r.get("legs", []) if lg.get("landmark")]
    return (f"talk_route: speaker {speaker} {tuple(r['from'])}; " + (f"waypoints: {'; '.join(wps)}; " if wps else "")
            + f"target {target} {tuple(r['to_xy'])}")


# --- names the player sees, targets ----------------------------------------------------------------------------------

def renames(w) -> dict[str, str]:
    """BM&V's names our world edits change ('Docks' -> 'Soulrest'), from world_edit rows of kind name_place."""
    out = dict(re.findall(r'\["([^"]+)"\] = "([^"]+)"',      # MapFix.cs: BM&V's misspelt marker names fixed
                          (db.REPO / "tools/ArgoniaPlugin/MapFix.cs").read_text()))
    for e in w.rows("world_edit"):
        m = re.search(r"'([^']+)' named (?:the )?([A-Z][\w'-]+(?: [A-Z][\w'-]+)*)", e.description)
        if e.kind == "name_place" and m:
            out[m.group(1)] = m.group(2)
    return out


def resolve(W: World, w, key: str) -> tuple[float, float, str]:
    if re.fullmatch(r"-?[\d.]+,-?[\d.]+", key):
        x, y = map(float, key.split(","))
        return x, y, key
    m = w.get("bmv_map_marker", key)
    if m:
        return m.x, m.y, renames(w).get(m.name, m.name)
    t = w.get("bmv_talker", key)
    if t:
        tk = w.get("talker", key)
        return t.x, t.y, tk.known_as if tk else (t.name or key)
    r = W.by_key.get(key)
    if r:
        return r["x"], r["y"], r["marker"] or (r["lm"][1] if r["lm"] else r["name"] or r["edid"])
    raise SystemExit(f"unknown target {key}")


def facts(settlements: list[str], write: bool) -> int:
    """Every directions fact of the settlements re-made as a route from its speaker to its target; the old source
    names both ("speaker 00AC8E", "map marker 082193" or "target <key>")."""
    w = db.open()
    names = renames(w)
    W = World(names=names)
    marks = {m.id[:6]: m for m in w.rows("bmv_map_marker")}
    talkers = {t.id[:6]: t for t in w.rows("bmv_talker")}
    n = 0
    for f in w.rows("talk_fact"):
        if f.topic != "talk.directions" or f.settlement not in settlements:
            continue
        sp = re.search(r"speaker ([0-9A-F]{6})", f.source)
        tk = re.search(r"target ([0-9A-F]{6})", f.source) or re.search(r"([0-9A-F]{6})", f.source)
        spk = talkers.get(sp.group(1)) if sp else None
        tgt = None
        if tk:
            h = tk.group(1)
            m = marks.get(h)
            if m:
                tgt = (m.x, m.y, names.get(m.name, m.name), m.id)
            elif h in talkers:
                t = talkers[h]
                tw = w.get("talker", t.id)
                tgt = (t.x, t.y, tw.known_as if tw else t.name, t.id)
            else:
                r = next((r for k, r in W.by_key.items() if k.startswith(h + ":")), None)
                if r:
                    tgt = (r["x"], r["y"], r["lm"][1] if r["lm"] else (r["name"] or r["edid"]), r["key"])
        if spk is None or tgt is None:
            print(f"SKIP {f.id}: speaker or target not found in its source")
            continue
        r = route(W, spk.x, spk.y, tgt[0], tgt[1], tgt[3])
        claim, src = describe(r, tgt[2]), source(r, spk.id, tgt[3])
        print(f"{f.id}\n  {claim}\n  [{src}]")
        if write:
            w.update("talk_fact", f.id, claim=claim, source=src)
        n += 1
    if write:
        w.save()
    print(f"{n} directions facts routed")
    return n


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("cache").add_argument("--world", default=WORLD)
    r = sp.add_parser("route")
    r.add_argument("--from", dest="src", required=True)
    r.add_argument("--to", required=True)
    r.add_argument("--json", action="store_true")
    f = sp.add_parser("facts")
    f.add_argument("--settlement", action="append", required=True)
    f.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "cache":
        cache(a.world)
        return 0
    if a.cmd == "facts":
        facts(a.settlement, a.write)
        return 0
    w = db.open()
    W = World(names=renames(w))
    sx, sy, _ = resolve(W, w, a.src)
    tx, ty, tn = resolve(W, w, a.to)
    res = route(W, sx, sy, tx, ty, a.to)
    print(json.dumps(res, indent=1) if a.json else describe(res, tn) + "\n  [" + source(res, a.src, a.to) + "]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
