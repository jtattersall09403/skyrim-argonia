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
as "just" and a compass point only.

    python3 -m tools.argonia_world.talk_route cache    [--world 23D689:Black Marsh.esm]
    python3 -m tools.argonia_world.talk_route route    --from REF --to REF|MARKER|x,y [--json]
    python3 -m tools.argonia_world.talk_route facts    --settlement bmv.lilmoth [--write] [--raw]  # every directions fact
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
CLOSE = 60 * UNITS_M    # under this, in a near-straight line: in sight, "just" and a compass point
TURN = 700.0            # Douglas-Peucker tolerance: a bend this far off the line is a turn
REACH = 1600.0          # a leg's landmark lies this close to its end
MIN_LEG = 1400.0        # a run shorter than this merges into the one before
SPACE = 3000.0          # two cuts of a telling stand at least this far apart along the path
MAX_LEGS = 4            # Morrowind gives two to four legs; a told route never has more
TOLD = 3                # a longer route tells this many landmarked legs, then "from there, ask again"
OWN = 4096.0            # the map marker nearest the speaker within this is the speaker's own place: never a waypoint
MERGE = 50 * PACE       # leg rule 1: a leg shorter joins its neighbour
SPLIT = 350 * PACE      # leg rule 2: a leg longer is cut at a landmark near its middle
SHORT = 150 * PACE      # a whole route shorter keeps its short legs
AWAY = 90.0             # leg rule 3: a first leg more than this many degrees off the target is re-planned
RARE = 3000.0           # a landmark is distinctive when no other of its look stands this close
SAME = 800.0            # pieces of one thing (a dock's planks, a waterfall's sheets) stand this close
CLIMB = 700.0           # a leg rising this much is a climb
WATER_FLAG = 0x0200     # NVNM triangle flag: on water
BASE_SIGS = {"STAT", "SCOL", "TREE", "ACTI", "FURN", "CONT", "FLOR", "DOOR", "LIGH", "MSTT"}

# What a person calls a thing, from its base's model path or editor id (lower case), most notable first: kind (the
# class talk_check knows), pattern, the phrase (what the player sees, from what the model shows), weight, least size.
LANDMARK = [
    ("wreck", r"wreck|sunken", "the wrecked boat", 10, 600),
    ("ship", r"shiplargedaintysload|shiplarge|imperialship|shipimperial|caravel|carrack|galleon", "the big ship", 10,
     1800),
    ("ship", r"shiplongboat", "the longboat", 7, 600),
    ("rowboat", r"rowboat", "the rowing boat", 5, 400),
    ("boat", r"boatracked", "the boat on its rack", 5, 400),
    ("boat", r"(?<![a-z])boat|canoe", "the boat", 5, 400),
    ("shrine", r"wshrn|wayshrine", "the wayshrine", 10, 300),
    ("shrine", r"shrine", "the shrine", 9, 300),
    ("statue", r"statuewithsword", "the statue with the sword", 9, 300),
    ("statue", r"standingstone|obelisk|monument", "the standing stone", 9, 300),
    ("statue", r"totem|idol", "the totem", 8, 300),
    ("statue", r"statue", "the statue", 8, 300),
    ("hist", r"(?<![a-z])hist(?!le)", "the Hist tree", 10, 600),
    ("bigtree", r"giantredwood|treegiant|giant.?tree|bigtree", "the giant tree", 7, 1200),
    ("bigtree", r"vurt_deadtree|deadtree|treepineforestdead", "the dead tree", 6, 600),
    ("ruinhouse", r"destroyed|burnt|burned", "the burnt-out house", 7, 900),
    ("ruin", r"dwemer(?!\\roads\\)|dwespecial|dweruin", "the Dwemer ruin", 9, 900),   # a Dwemer road piece is a road
    ("ruin", r"ayleid|arcolumn", "the old stone columns", 8, 600),
    ("ruin", r"xanmeer|ziggurat", "the stepped ruin", 9, 900),
    ("ruin", r"ruins?", "the ruin", 8, 900),
    ("gate", r"obgate", "the red Daedric gate", 10, 500),
    ("tower", r"cyrkeep", "the stone keep", 8, 1000),
    ("lighthouse", r"lighthouse(?!fire)", "the lighthouse", 10, 1000),
    ("tower", r"tower\w*dark", "the dark tower", 8, 900),
    ("tower", r"tower", "the stone tower", 8, 900),
    ("bridge", r"bridge", "the bridge", 7, 600),
    ("waterfall", r"fxwaterfall(?!mist)", "the waterfall", 8, 1500),
    ("graveyard", r"graveyardfence", "the graveyard", 7, 300),
    ("bones", r"cobrabones|dragonbones|whalebone", "the great bones", 9, 500),
    ("dock", r"dlc2rrdockpier|rtdockpier|pier|jetty", "the pier", 5, 500),
    ("dock", r"\\docks?\\|dock\d|dockstr|dockpier", "the dock", 3, 500),
    ("hut", r"stilthouse", "the stilt house", 6, 500),
    ("hut", r"bamboohut", "the bamboo hut", 6, 400),
    ("hut", r"alhut|hidehut", "the hide hut", 6, 400),
    ("hut", r"shack", "the shack", 5, 400),
    ("hut", r"hut", "the hut", 5, 500),
    ("house", r"swamp house", "the swamp house", 5, 800),
    ("house", r"tavern", "the big inn", 6, 800),
    ("house", r"manor|castlehouse", "the big stone house", 6, 800),
    ("house", r"farmhouse|bauernhaus", "the farmhouse", 5, 800),
    ("house", r"house|haus|longhs", "the house", 4, 800),
    ("tent", r"largeimperialtent", "the big tent", 5, 300),
    ("tent", r"tent(?!acle)", "the tent", 4, 300),
    ("signpost", r"signpost|roadsign|directionsign", "the signpost", 8, 0),
    ("well", r"\\well|well\d", "the well", 5, 200),
    ("cart", r"brokencart", "the broken cart", 6, 300),
    ("cart", r"cart\b|cart\d|wagon", "the cart", 4, 300),
    ("spit", r"giantcampfire", "the big fire pit", 5, 250),
    ("spit", r"firespit|campfire|firepit", "the cooking fire", 3, 250),
    ("cave", r"caveentr|cave.*entrance|mineentr", "the cave mouth", 8, 300),
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
        self.own: set = set()           # the speaker's own place for the route being told (route sets it)
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
        # distinctiveness: others of the same look near it (beyond its own pieces) make it a poor landmark
        cells: dict[tuple, list] = {}
        for r in self.refs:
            if r["lm"]:
                cells.setdefault((int(r["x"] // RARE), int(r["y"] // RARE)), []).append(r)
        for r in self.refs:
            if not r["lm"] or r["lm"][0] == "marker":
                continue
            cx, cy = int(r["x"] // RARE), int(r["y"] // RARE)
            twins = sum(1 for i in (-1, 0, 1) for j in (-1, 0, 1) for o in cells.get((cx + i, cy + j), ())
                        if o is not r and o["lm"][1] == r["lm"][1]
                        and SAME < math.hypot(o["x"] - r["x"], o["y"] - r["y"]) < RARE)
            r["twins"] = twins
            r["lm"] = (r["lm"][0], r["lm"][1], r["lm"][2] - 2.0 * min(twins, 5))

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

    def astar(self, s: int, t: int, blocked: set | None = None) -> list[int]:
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
                if c is None or (blocked and v in blocked):
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


def _landmark(W: World, x: float, y: float, used: set, heading: tuple, wide: float = 1) -> dict | None:
    """The most distinctive landmark a stranger would pick out near (x, y): a map marker, else a thing with at most
    one twin of the same look within RARE; nearer is better."""
    best, bs = None, -1e9
    for r in W.refs:
        lm = r["lm"]
        reach = REACH * wide * (2 if lm and lm[0] == "marker" else 1)
        if not lm or r["key"] in used or r["key"] in W.own or abs(r["x"] - x) > reach or abs(r["y"] - y) > reach:
            continue
        if lm[0] != "marker" and r.get("twins", 0) >= 2:
            continue
        d = math.hypot(r["x"] - x, r["y"] - y)
        if d <= reach and lm[2] - d / (400 * wide) > bs:
            best, bs = r, lm[2] - d / (400 * wide)
    if best is None or bs < 3:
        return None
    cx, cy = best["x"] - x, best["y"] - y
    side = "ahead"
    if math.hypot(cx, cy) > 300:
        side = "on your left" if heading[0] * cy - heading[1] * cx > 0 else "on your right"
    return {"key": best["key"], "what": best["lm"][1], "kind": best["lm"][0], "x": round(best["x"]),
            "y": round(best["y"]), "side": side, "score": round(bs, 1)}


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


def _angle(ax: float, ay: float, bx: float, by: float) -> float:
    """Degrees between two directions."""
    d = math.degrees(math.atan2(by, bx) - math.atan2(ay, ax)) % 360
    return min(d, 360 - d)


def route(W: World, sx: float, sy: float, tx: float, ty: float, target: str, shape: bool = True) -> dict:
    """The route told as legs. shape=False gives the raw cut without the leg rules, for measuring them."""
    straight = math.hypot(tx - sx, ty - sy)
    out = {"from": (round(sx), round(sy)), "to": target, "to_xy": (round(tx), round(ty)),
           "straight_m": round(straight / UNITS_M), "bearing": compass(tx - sx, ty - sy)}
    W.own = own_place(W, sx, sy)
    G = Grid(W, sx, sy, tx, ty)
    s, t = G.nearest_open(*G.ij(sx, sy)), G.nearest_open(*G.ij(tx, ty))
    path = G.astar(s, t)
    if not path:
        out.update(kind="none", legs=[])
        return out
    plan = _plan(W, G, s, path, target, shape)
    out["route_m"] = round(plan["along"][-1] / UNITS_M)
    if straight < CLOSE and plan["along"][-1] < straight * 1.35 + 600:
        out.update(kind="close", paces=round(straight / PACE), legs=[])
        return out
    away = lambda legs: _angle(legs[0]["end"][0] - sx, legs[0]["end"][1] - sy, tx - sx, ty - sy) > AWAY
    if shape and away(plan["legs"]):
        # rule 3: the first leg heads away; block that start and take the next-best one while it costs little
        blocked, best, cur = set(), None, plan
        for _ in range(3):
            end = _near_index(G, path, cur["legs"][0]["end"])
            for k in path[3:path.index(end) + 1]:
                i, j = k % G.nx, k // G.nx
                blocked |= {(j + dj) * G.nx + i + di for dj in range(-2, 3) for di in range(-2, 3)}
            blocked.discard(s)
            blocked.discard(t)
            alt = G.astar(s, t, blocked)
            if not alt:
                break
            cur = _plan(W, G, s, alt, target, shape)
            if cur["along"][-1] > plan["along"][-1] * 1.6:
                break
            path = alt
            if not away(cur["legs"]):
                best = cur
                break
        if best:
            plan = best
            out["route_m"] = round(plan["along"][-1] / UNITS_M)
        else:
            plan["legs"][0]["why"] = _forced(G, s, t, plan["legs"][0])
    legs = plan["legs"]
    if shape and len(legs) > MAX_LEGS:
        # Morrowind's way: the first landmarked legs, then "from there, ask again"
        keep = TOLD
        while keep > 1 and not legs[keep - 1]["landmark"]:
            keep -= 1
        end = legs[keep - 1]["end"]
        legs = legs[:keep] + [{"kind": "ask", "heading": compass(tx - end[0], ty - end[1], 8), "m": 0, "paces": 0,
                               "start": end, "end": (round(tx), round(ty)), "landmark": None, "past": []}]
    out.update(kind="route", legs=legs)
    return out


def own_place(W: World, x: float, y: float) -> set:
    """The speaker's own place: the map marker nearest (x, y) within OWN."""
    best = min((r for r in W.refs if r["lm"] and r["lm"][0] == "marker"
                and abs(r["x"] - x) < OWN and abs(r["y"] - y) < OWN),
               key=lambda r: math.hypot(r["x"] - x, r["y"] - y), default=None)
    return {best["key"]} if best and math.hypot(best["x"] - x, best["y"] - y) <= OWN else set()


def _near_index(G: Grid, path: list, xy: tuple) -> int:
    return min(path, key=lambda k: math.hypot(G.xy(k % G.nx, k // G.nx)[0] - xy[0],
                                              G.xy(k % G.nx, k // G.nx)[1] - xy[1]))


def _forced(G: Grid, s: int, t: int, leg: dict) -> str:
    """Why the world sends the first leg away from the target: what lies on the straight line."""
    (x0, y0), (x1, y1) = G.xy(s % G.nx, s // G.nx), G.xy(t % G.nx, t // G.nx)
    n = max(2, int(math.hypot(x1 - x0, y1 - y0) // GRID))
    kinds = [G.kind[j * G.nx + i] for i, j in (G.ij(x0 + (x1 - x0) * f / n, y0 + (y1 - y0) * f / n)
                                                for f in range(n + 1)) if 0 <= i < G.nx and 0 <= j < G.ny]
    if kinds.count("water") >= max(2, kinds.count("steep")):
        return "round the inlet"
    if kinds.count("steep") >= 2:
        return "round the cliffs"
    return "the path bends round" if leg["kind"] == "road" else "round the wet ground"


def _plan(W: World, G: Grid, s: int, path: list, target: str, shape: bool) -> dict:
    pts = [(*G.xy(k % G.nx, k // G.nx), G.h[k], _mode(G, k)) for k in path]
    seg = lambda a, b: math.hypot(pts[b][0] - pts[a][0], pts[b][1] - pts[a][1])
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
    for r in merged:                    # one mode a run: the run's most common
        m = max(("walk", "road", "shore", "bridge", "dock", "swim"), key=lambda m: sum(pts[i][3] == m for i in r))
        for i in r:
            pts[i] = (*pts[i][:3], m)
    along = [0.0]
    for i in range(len(pts) - 1):
        along.append(along[-1] + seg(i, i + 1))
    must = {r[0] for r in merged[1:] if "swim" in (pts[r[0] - 1][3], pts[r[0] + 1][3])
            or "bridge" in (pts[r[0] - 1][3], pts[r[0] + 1][3])}
    cuts = _cuts(W, pts, along, must, target)
    if shape:
        cuts = _rules(W, pts, along, must, cuts, target)
    return {"along": along, "legs": _build(G, s, pts, along, cuts, must, shape)}


def _heading(pts: list, i: int) -> tuple:
    a, c = pts[max(0, i - 10)], pts[min(len(pts) - 1, i + 10)]
    hx, hy = c[0] - a[0], c[1] - a[1]
    hl = math.hypot(hx, hy) or 1.0
    return hx / hl, hy / hl


def _cuts(W: World, pts: list, along: list, must: set, target: str) -> list[tuple]:
    """At most MAX_LEGS legs. The cuts a telling may use: where a swim or a bridge begins or ends (kept), and any
    point of the path with a distinctive landmark near it, best at a turn; every other cut needs a landmark, so a
    leg ends at a landmark, a far bank or the target."""
    n = len(pts)
    step = max(1, n // 300)
    scored = []
    for i in sorted(set(range(0, n, step)) | must):
        if i <= 0 or i >= n - 1 or along[i] < MIN_LEG or along[-1] - along[i] < MIN_LEG:
            continue
        a, c = pts[max(0, i - 10)], pts[min(n - 1, i + 10)]
        h1 = math.atan2(pts[i][1] - a[1], pts[i][0] - a[0])
        h2 = math.atan2(c[1] - pts[i][1], c[0] - pts[i][0])
        turn = abs((h2 - h1 + math.pi) % (2 * math.pi) - math.pi)
        lm = _landmark(W, pts[i][0], pts[i][1], {target}, _heading(pts, i))
        if lm is None and i not in must:
            continue
        dist = math.hypot(lm["x"] - pts[i][0], lm["y"] - pts[i][1]) if lm else 0.0
        scored.append((100.0 if i in must else lm["score"] + 3 * turn - dist / 600, i, lm))
    chosen, used, looks = [], {target}, set()
    for sc, i, lm in sorted(scored, key=lambda x: -x[0]):
        if len(chosen) >= MAX_LEGS - 1:
            break
        if any(abs(along[i] - along[j]) < SPACE for _, j, _ in chosen):
            continue
        if lm and (lm["key"] in used or lm["what"] in looks):
            if i not in must:
                continue
            lm = None
        chosen.append((sc, i, lm))
        if lm:
            used.add(lm["key"])
            looks.add(lm["what"])
    return [(0, None)] + sorted(((i, lm) for _, i, lm in chosen), key=lambda x: x[0]) + [(n - 1, None)]


def _rules(W: World, pts: list, along: list, must: set, cuts: list, target: str) -> list[tuple]:
    """Leg rules 1 and 2: a leg under MERGE joins its neighbour (the weaker inner cut goes) unless its cut is a swim
    or bridge edge or the whole route is under SHORT; a leg over SPLIT is cut at the best landmark near its middle,
    the search widening along the leg and out from it."""
    cuts = list(cuts)
    if along[-1] >= SHORT:
        again = True
        while again:
            again = False
            for k in range(len(cuts) - 1):
                if along[cuts[k + 1][0]] - along[cuts[k][0]] >= MERGE:
                    continue
                inner = [c for c in (k, k + 1) if 0 < c < len(cuts) - 1 and cuts[c][0] not in must]
                if inner:
                    del cuts[min(inner, key=lambda c: cuts[c][1]["score"] if cuts[c][1] else -1)]
                    again = True
                    break
    used = {target} | {lm["key"] for _, lm in cuts if lm}
    looks = {lm["what"] for _, lm in cuts if lm}
    k = 0
    while k < len(cuts) - 1:
        a, b = cuts[k][0], cuts[k + 1][0]
        if along[b] - along[a] > SPLIT:
            c = _mid_cut(W, pts, along, a, b, used, looks)
            if c:
                cuts.insert(k + 1, c)
                used.add(c[1]["key"])
                looks.add(c[1]["what"])
                continue
        k += 1
    return cuts


def _mid_cut(W: World, pts: list, along: list, a: int, b: int, used: set, looks: set) -> tuple | None:
    """The best landmark near the middle of the leg a..b: the middle third first, then wider along the leg and
    further out from it."""
    ln = along[b] - along[a]
    mid = along[a] + ln / 2
    for lo, hi, wide in ((1 / 3, 2 / 3, 1), (0.25, 0.75, 2), (0.2, 0.8, 3), (0.15, 0.85, 4)):
        best, bs = None, -1e9
        for i in range(a + 1, b):
            if not along[a] + lo * ln <= along[i] <= along[a] + hi * ln or i % 2:
                continue
            lm = _landmark(W, pts[i][0], pts[i][1], used, _heading(pts, i), wide)
            if lm is None or lm["what"] in looks:
                continue
            sc = lm["score"] - abs(along[i] - mid) / 2000
            if sc > bs:
                best, bs = (i, lm), sc
        if best:
            return best
    return None


def _terrain(G: Grid, pts: list, a: int, b: int, kind: str) -> str:
    """What a long leg with no landmark follows."""
    if kind == "road":
        return "along the path"
    if kind == "swim":
        return "across open water"
    wet = 0
    for x, y, _, _ in pts[a:b + 1]:
        i, j = G.ij(x, y)
        wet += any(0 <= i + di < G.nx and 0 <= j + dj < G.ny
                   and G.kind[(j + dj) * G.nx + i + di] in ("water", "navwater")
                   for di in (-3, 0, 3) for dj in (-3, 0, 3))
    return "along the shore" if wet > 0.5 * (b - a + 1) else "over open ground"


def _build(G: Grid, s: int, pts: list, along: list, cuts: list, must: set, shape: bool) -> list[dict]:
    """The legs between the cuts; neighbour legs of one kind and heading become one while the sum stays under
    SPLIT. With shape, each leg the rules let stand short or long carries its reason (why)."""
    seg = lambda a, b: math.hypot(pts[b][0] - pts[a][0], pts[b][1] - pts[a][1])
    legs = []
    for (a, _), (b, lm) in zip(cuts, cuts[1:]):
        p0, p1 = pts[a], pts[b]
        d = along[b] - along[a]
        modes: dict[str, float] = {}
        for i in range(a, b):
            modes[pts[i][3]] = modes.get(pts[i][3], 0.0) + seg(i, i + 1)
        mode = max(modes, key=modes.get)
        rise = p1[2] - p0[2]
        kind = "climb" if mode in ("walk", "road", "shore") and rise > CLIMB else mode
        lg = {"kind": kind, "heading": compass(p1[0] - p0[0], p1[1] - p0[1], 8), "m": round(d / UNITS_M),
              "paces": round(d / PACE), "start": (round(p0[0]), round(p0[1])), "end": (round(p1[0]), round(p1[1])),
              "landmark": lm, "past": [], "a": a, "b": b}
        if kind == "swim":
            lg["island"] = _island(G, G.nearest_open(*G.ij(*lg["end"])), s)
        pv = legs[-1] if legs else None
        if (pv and pv["kind"] == kind and pv["heading"] == lg["heading"] and kind != "swim"
                and (not shape or along[b] - along[pv["a"]] <= SPLIT)):
            lg.update(start=pv["start"], m=pv["m"] + lg["m"], paces=pv["paces"] + lg["paces"], a=pv["a"],
                      past=pv["past"] + ([pv["landmark"]] if pv["landmark"] else []))
            legs[-1] = lg
        else:
            legs.append(lg)
    for lg in legs:
        a, b = lg.pop("a"), lg.pop("b")
        if not shape:
            continue
        d = along[b] - along[a]
        if d < MERGE and along[-1] >= SHORT:
            why = ("a short swim" if lg["kind"] == "swim" else "a short crossing" if lg["kind"] == "bridge"
                   else "to the water's edge" if a in must or b in must else "")
            if why:
                lg["why"] = why
        if d > SPLIT:
            lg["why"] = _terrain(G, pts, a, b, lg["kind"]) if not lg["past"] else "no landmark near its middle"
    return legs


VERB = {"walk": "walk {h}", "road": "follow the path {h}", "shore": "follow the shore {h}",
        "bridge": "cross the bridge {h}", "dock": "go along the boards {h}", "swim": "swim {h}", "climb": "climb {h}"}

# How far, in the words Morrowind's direction lines use (never a count: 0 of its 356 direction lines gives one).
# A leg's measured length in metres picks its band; the told route and the brief carry only the band's words, and
# talk_check reads the words back to the band. Skyrim's scale: a person walks about 2 m a second, so a short way is
# under two minutes' walk, a long walk the far side of a settlement or the next landmark out of sight.
BANDS = [  # (under metres, band, the words that say it: the first is what describe() writes, the rest are read back)
    (60, "near", ["just", r"just (?:to the )?(?:north|south|east|west|past|beyond|across|outside|there|here)",
                  "right there", "close by", "a few steps", "in sight", "nearby"]),
    (200, "short", ["a short way", "a little way", "not far", "a short walk", "a stone's throw"]),
    (600, "fair", ["a fair way", "a good walk", "some way", "a fair walk"]),
    (2000, "long", ["a long walk", "a long way", "a good long way"]),
    (float("inf"), "far", ["far off", r"far (?:to the )?(?:north|south|east|west)", "a long journey",
                           "most of a day"]),
]
BAND_ORDER = [b for _, b, _ in BANDS]


def band(m: float) -> str:
    """The distance band of a length in metres."""
    return next(b for top, b, _ in BANDS if m < top)


def band_words(b: str) -> str:
    return next(ws for _, n, ws in BANDS if n == b)[0]


BAND_RE = [(n, re.compile(r"\b(?:" + "|".join(sorted(ws[1:] + [ws[0]], key=len, reverse=True)) + r")\b", re.I))
           for _, n, ws in BANDS]


MEASURE = re.compile(r"\b(?:about |some )?(\d+) ?(paces|m|metres|meters)\b")


def in_words(text: str) -> str:
    """Text for a writer with every measured distance ("about 129 paces", "60 m") put as the words of its band, so
    no count reaches the writer (briefs: talk_brief, quest-write's brief)."""
    def say(m: re.Match) -> str:
        n = int(m.group(1)) * (PACE / UNITS_M if m.group(2) == "paces" else 1)
        return band_words(band(n))
    return MEASURE.sub(say, text or "")


def describe(r: dict, target_name: str) -> str:
    """The route as a local tells it, the Morrowind way: each leg's way, compass point, distance in words and the
    landmark it ends at; no counts. The writer re-tells it in the speaker's own voice."""
    if r["kind"] == "close":
        text = f"{target_name} is just {r['bearing']} of here, in sight."
        return text[0].upper() + text[1:]
    if r["kind"] == "none":
        return (f"{target_name} lies {band_words(band(r['straight_m']))} {r['bearing']} of here; no way on foot "
                f"was found.")
    bits = []
    for n, lg in enumerate(r["legs"]):
        if lg["kind"] == "ask":
            bits.append(f"from there, ask again for {target_name}, which lies further {lg['heading']}")
            continue
        v = VERB[lg["kind"]].format(h=lg["heading"])
        if lg["kind"] == "swim" and lg.get("island"):
            v = f"swim to the island you can see to the {lg['heading']}"
        why = lg.get("why", "")
        if why.startswith(("round", "over", "across")) or (why.startswith("along") and why[10:] not in v):
            v += f" {why}"
        s = f"{v} {band_words(band(lg['m']))}"
        if lg.get("past"):
            s += " past " + " and ".join(p["what"] for p in lg["past"])
        if lg["landmark"]:
            side = "" if lg["landmark"]["side"] == "ahead" else f" {lg['landmark']['side']}"
            s += f" until you reach {lg['landmark']['what']}{side}"
        elif lg["kind"] == "swim" and n < len(r["legs"]) - 1:
            s += " to the far bank"
        bits.append(s)
    if r["legs"][-1]["kind"] != "ask":
        bits[-1] += f", and {target_name} is there"
    text = "; then ".join(bits)
    return text[0].upper() + text[1:] + "."


def _deg(a: tuple, b: tuple) -> int:
    return round(math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))) % 360


def legs_field(r: dict) -> str:
    """The legs as talk_check reads them: `kind paces@degrees (why) | ...` (degrees counter-clockwise from east)."""
    if r["kind"] != "route":
        return f"{r['kind']} {r.get('paces', 0)}@{_deg(r['from'], r['to_xy'])}"
    return " | ".join(f"{lg['kind']} {lg['paces']}@{_deg(lg['start'], lg['end'])}"
                      + (f" ({lg['why']})" if lg.get("why") else "") for lg in r["legs"])


LEG = re.compile(r"(\w+) (\d+)@(\d+)(?: \(([^)]*)\))?")


def leg_problems(src: str, W: World | None = None) -> list[str]:
    """The leg rules a directions fact's source breaks without a recorded reason: (1) a leg under MERGE in a route
    of SHORT or more, (2) a leg over SPLIT, (3) a first leg more than AWAY off the target; and always (4) more than
    MAX_LEGS legs, (5) given the world, a waypoint that is the speaker's own place (own_place)."""
    m = re.search(r"legs: ([^;]*);", src)
    pos = re.findall(r"\((-?\d+), (-?\d+)\)", src)
    if not m or len(pos) < 2:
        return ["no legs in its source: re-run talk_route facts"]
    legs = [(k, int(p), int(d), why) for k, p, d, why in LEG.findall(m.group(1))]
    if not legs or legs[0][0] in ("close", "none"):
        return []
    out: list[str] = []
    if len(legs) > MAX_LEGS:
        out.append(f"{len(legs)} legs (over {MAX_LEGS}: tell {TOLD}, then ask again)")
    if W is not None:
        sx, sy = map(float, pos[0])
        wps = re.search(r"waypoints: (.*?); legs:", src)
        out += [f"waypoint {k} is the speaker's own place" for k in own_place(W, sx, sy)
                if wps and k in wps.group(1)]
    legs = [lg for lg in legs if lg[0] != "ask"]
    out, total = out, sum(p for _, p, _, _ in legs)
    for n, (k, p, d, why) in enumerate(legs, 1):
        if p * PACE < MERGE and total * PACE >= SHORT and len(legs) > 1 and not why:
            out.append(f"leg {n} is {p} paces (under {round(MERGE / PACE)})")
        if p * PACE > SPLIT and not why:
            out.append(f"leg {n} is {p} paces (over {round(SPLIT / PACE)})")
    (sx, sy), (tx, ty) = map(int, pos[0]), map(int, pos[-1])
    d0 = legs[0][2]
    off = _angle(math.cos(math.radians(d0)), math.sin(math.radians(d0)), tx - sx, ty - sy)
    if off > AWAY and not legs[0][3]:
        out.append(f"leg 1 heads {round(off)} degrees off the target")
    return out


WAYPOINT = re.compile(r"[0-9A-F]{6}:.+?\.es[mpl] (.+?) \((-?\d+), (-?\d+)\)")
COUNT = re.compile(r"\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen|twenty|thirty|"
                   r"forty|fifty|sixty|seventy|eighty|ninety|hundred|a hundred|thousand|dozen)\b[\w\s-]{0,24}?"
                   r"\b(?:paces|steps|strides|yards|metres|meters|leagues|miles)\b|\bpaces\b", re.I)
WORD_DIR = re.compile(r"\b(north|south|east|west)(?:[- ]?(north|south|east|west))?(?:[- ]?(north|south|east|west))?"
                      r"(?:ward|ern|erly)?\b", re.I)


def _parse(src: str) -> tuple[list, list, tuple, tuple] | None:
    """A directions source as (legs [(kind, paces, degrees, why)], waypoints [(what, x, y)], speaker xy, target xy)."""
    m = re.search(r"legs: ([^;]*);", src)
    pos = re.findall(r"\((-?\d+), (-?\d+)\)", src)
    if not m or len(pos) < 2:
        return None
    legs = [(k, int(p), int(d), why) for k, p, d, why in LEG.findall(m.group(1))]
    wps = re.search(r"waypoints: (.*?); legs:", src)
    way = [(what.strip(), int(x), int(y)) for what, x, y in
           (WAYPOINT.findall(wps.group(1)) if wps else [])]
    return legs, way, tuple(map(int, pos[0])), tuple(map(int, pos[-1]))


def shape(src: str) -> str:
    """What a writer and a find agent need of a route's shape: legs, their kinds, anchors and distance bands."""
    p = _parse(src)
    if not p:
        return "no route"
    legs, way, (sx, sy), (tx, ty) = p
    if legs and legs[0][0] == "close":
        return "in sight: one compass point and \"just\"; no legs"
    told = [lg for lg in legs if lg[0] != "ask"]
    out = (f"{len(told)} leg{'s' * (len(told) != 1)} ({', '.join(lg[0] for lg in told)}); distance "
           f"{', '.join(band(lg[1] * PACE / UNITS_M) for lg in told)}; anchors: "
           f"{', '.join(w for w, _, _ in way) or 'none (what each leg follows)'}")
    return out + ("; then ask again" if any(lg[0] == "ask" for lg in legs) else "")


def _bearing_word(m: re.Match) -> float:
    """The angle (degrees counter-clockwise from east) a compass phrase names: north-north-east is two parts
    north-east to one part north."""
    ang = {"east": 0, "north": 90, "west": 180, "south": 270}
    parts = [ang[g.lower()] for g in m.groups() if g]
    weights = [1] if len(parts) == 1 else [1, 1] if len(parts) == 2 else [2, 1, 1]
    x = sum(w * math.cos(math.radians(a)) for w, a in zip(weights, parts))
    y = sum(w * math.sin(math.radians(a)) for w, a in zip(weights, parts))
    return math.degrees(math.atan2(y, x)) % 360


def _off(a: float, b: float) -> float:
    return abs((a - b + 180) % 360 - 180)


def check_told(text: str, src: str) -> list[str]:
    """What a told direction says that its route does not: a count of paces or another unit; a compass point no leg
    (nor the target's bearing) heads within 50 degrees of, or out of the legs' order; landmarks out of route order;
    a distance word more than one band off the leg it falls in. Empty when the telling is true to the route."""
    out = [f"a count: {m.group(0)!r}" for m in COUNT.finditer(text)]
    p = _parse(src)
    if not p:
        return out
    legs, way, (sx, sy), (tx, ty) = p
    told = [lg for lg in legs if lg[0] not in ("ask", "none")] or [("close", 0, _deg((sx, sy), (tx, ty)), "")]
    target = _deg((sx, sy), (tx, ty))
    heads = [lg[2] for lg in told] + [lg[2] for lg in legs if lg[0] == "ask"]
    low = text.lower()
    # landmarks in route order
    # (a summary may name a landmark before the legs do: each is looked for after the one before it on the way)
    pos, prev = -1, None
    for what, _, _ in way:
        core = re.sub(r"^(?:the|a|an) ", "", what.lower())
        if core not in low:
            continue
        i = low.find(core, pos + 1)
        if i < 0:
            out.append(f"landmarks out of order: {core!r} is told before {prev!r}, which comes first on the way")
            continue
        pos, prev = i, core
    # compass points: each on a leg at or after the last one matched, or the target's bearing
    k = 0
    for m in WORD_DIR.finditer(text):
        if re.match(r"(?:side|edge|end|bank|shore|gate|wall)\b", low[m.end():].lstrip()):
            continue  # "the north side": where a thing is, not a heading
        a = _bearing_word(m)
        hit = next((j for j in range(k, len(heads)) if _off(a, heads[j]) <= 50), None)
        if hit is None and _off(a, target) <= 50:
            continue
        if hit is None:
            back = any(_off(a, h) <= 50 for h in heads[:k])
            out.append(f"{m.group(0)!r} " + ("out of the legs' order" if back else
                                             f"is no leg's heading ({', '.join(str(h) for h in heads)} degrees)"))
            continue
        k = hit
    # distance words: each within one band of a leg (or the whole way)
    bands = [band(lg[1] * PACE / UNITS_M) for lg in told] + [band(sum(lg[1] for lg in told) * PACE / UNITS_M)]
    for name, rx in BAND_RE:
        for m in rx.finditer(text):
            if not any(abs(BAND_ORDER.index(name) - BAND_ORDER.index(b)) <= 1 for b in bands):
                out.append(f"{m.group(0)!r} says {name}; the way is {', '.join(bands[:-1])}")
    return out


def source(r: dict, speaker: str, target: str) -> str:
    wps = [f"{m['key']} {m['what']} ({m['x']}, {m['y']})"
           for lg in r.get("legs", []) for m in lg.get("past", []) + [lg.get("landmark")] if m]
    return (f"talk_route: speaker {speaker} {tuple(r['from'])}; " + (f"waypoints: {'; '.join(wps)}; " if wps else "")
            + f"legs: {legs_field(r)}; target {target} {tuple(r['to_xy'])}")


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


def facts(settlements: list[str], write: bool, world: str | None = None, shape: bool = True) -> int:
    """Every directions fact of the settlements re-made as a route from its speaker to its target, in the
    settlement's worldspace (bmv_settlement) unless world is given; the old source names both ("speaker 00AC8E",
    "map marker 082193" or "target <key>"). A fact whose claim changes is marked CHANGED."""
    w = db.open()
    names = renames(w)
    worlds: dict[str, World] = {}

    def world_of(s: str) -> World:
        ws = world or getattr(w.get("bmv_settlement", s), "worldspace", None) or WORLD
        if ws not in worlds:
            worlds[ws] = World(ws, names=names)
        return worlds[ws]
    marks = {m.id[:6]: m for m in w.rows("bmv_map_marker")}
    talkers = {t.id[:6]: t for t in w.rows("bmv_talker")}
    n = 0
    for f in w.rows("talk_fact"):
        if f.topic != "talk.directions" or f.settlement not in settlements:
            continue
        W = world_of(f.settlement)
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
        r = route(W, spk.x, spk.y, tgt[0], tgt[1], tgt[3], shape)
        claim, src = describe(r, tgt[2]), source(r, spk.id, tgt[3])
        print(f"{f.id}{'  CHANGED' if claim != f.claim else ''}\n  {claim}\n  [{src}]")
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
    f.add_argument("--world", help="override the settlement's worldspace (bmv_settlement.worldspace)")
    f.add_argument("--raw", action="store_true", help="without the leg rules (to measure them)")
    a = ap.parse_args(argv)
    if a.cmd == "cache":
        cache(a.world)
        return 0
    if a.cmd == "facts":
        facts(a.settlement, a.write, a.world, not a.raw)
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
