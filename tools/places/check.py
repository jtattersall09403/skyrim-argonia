"""Read the built place layer back and fail on each item of the contract's check list (place-studio.md, Build).

    python -m tools.places check <place_id> [--out DIR] [--json]

Reads out/places/plugin/ArgoniaNWPlaces.esp (records by tools/ArgoniaPlaces/Build `dump`, navmesh by its bytes),
the place's shard plan (which records are this place's, and its place files' rows), the world ESM's facts round the
place (ground, refs) and the world's own navmesh beside ours. Exit 1 when any check fails; every check is a
function of one context dict, so tools/tests can feed it a small broken fixture each.

Checks: seat, overlap, doors, people, navmesh, land, clear, services, nordic, rooms, levelled, plugin (masters, links),
jail, primitives, stock and promises (a stocked place: tools/places/stock/verify.py).
"""
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import math
import re
import struct
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from tools.places import build as B
from tools.places.people import TRAVEL_STOP

SEAT_TOL = 8.0  # units: one VHGT step
STOP_PLAN_TOL, STOP_Z_TOL = 96.0, 128.0  # a routine stop or arrival point is on navmesh within these
DECK_TOL = 48.0  # a line's point over a deck stands on a triangle within this of the deck's own surface
WATER = 0x200  # NVNM triangle flag: water (the triangle lies on the bed under it)
WADE = 64.0  # water up to the waist (half the CK's 128 agent height) is waded; deeper, one swims
OVERLAP_SHRINK = 0.8  # a ref is inside another's collision when its origin is within this share of the other's box
PLANT_DOOR_CLEAR = 128.0
SOLID = {"building", "static", "furniture", "container", "door", "activator", "rock"}
PLANT_TYPES = {"TREE", "FLOR"}
# Nordic: a base whose model or editor id is of Skyrim's Nordic culture (decision 0006). Paths are Skyrim.esm's own
# folders for the hold cities, Nordic farms and ruins; editor-id prefixes are the CK's for the same kits.
NORDIC_MODEL = re.compile(r"(^|/)(architecture/(whiterun|windhelm|solitude|markarth|riften|farmhouse|winterhold|dawnstar|"
                          r"falkreath|morthal|riverwood|nordic|nordichall)|dungeons/nordic|clutter/nordic|furniture/nordic|"
                          r"clutter/(?:[a-z]*/)?(?:talos|shrineoftalos)|/nord[a-z]*\d|/wr[a-z]+\d|/wh[a-z]+\d)", re.I)
NORDIC_EDID = re.compile(r"^(Nor[A-Z]|Nord|WR[A-Z]|WH[A-Z]|Whiterun|Windhelm|Solitude|Markarth|Riften|Farmhouse|Talos)", re.U)
CRAFT_KEYWORD = {"forge": "CraftingSmithingForge", "anvil": "CraftingSmithingForge", "armour-workbench": "CraftingSmithingArmorTable",
                 "grindstone": "CraftingSmithingSharpeningWheel", "smelter": "CraftingSmelter", "tanning-rack": "CraftingTanningRack",
                 "alchemy-lab": "WICraftingAlchemy", "arcane-enchanter": "WICraftingEnchanting", "cooking-pot": "CraftingCookpot",
                 "oven": "BYOHCraftingOven", "staff-enchanter": "DLC2StaffEnchanter"}
TRADE_JOB = {"trader-general": "JobMerchantFaction", "trader-blacksmith": "JobBlacksmithFaction", "trader-apothecary": "JobApothecaryFaction",
             "trader-spells": "JobSpellFaction", "trader-innkeeper": "JobInnkeeperFaction", "trader-fletcher": "JobFletcherFaction",
             "trader-jeweller": "JobJewelerFaction", "trader-clothier": "JobTailorFaction", "trader-hunter": "JobMiscFaction",
             "trader-bookseller": "JobMiscFaction", "fence": "JobFenceFaction"}
NOT_A_PLACE_SERVICE = {"combat-foes", "combat-boss", "combat-creature", "treasure", "boss-chest", "gold-hoard", "unique-item",
                       "harvest-common", "harvest-rare", "fishing", "ore-vein", "skill-book", "spell-tome", "word-wall",
                       "standing-stone", "free-bed", "follower", "player-home", "altar-power"}


# ---- geometry -------------------------------------------------------------------------------------------------------

def obb_contains(ref: dict, p, shrink: float = 1.0, pad: float = 0.0, z: bool = True) -> bool:
    """Whether point p stands inside ref's record box (bounds [x0, y0, z0, x1, y1, z1]) under its full three-axis
    rotation and scale: shrunk in plan by `shrink`, widened in plan by `pad` units; the full height (origins sit on
    the floor), or any height when z is False. The one overlap geometry: the drafter's `overlap.inside` calls it."""
    b = ref.get("bounds")
    if not b:
        return False
    s = float(ref.get("scale") or 1.0)
    R = B.rotation(*(ref.get("rot") or [0, 0, 0]))
    q = list(p) + [ref["pos"][2]] * (3 - len(p))
    local = R.T @ (np.asarray(q[:3], float) - np.asarray(ref["pos"], float)) / s
    lo, hi = np.array(b[:3], float), np.array(b[3:], float)
    c, h = (lo + hi) / 2, (hi - lo) / 2 * np.array([shrink, shrink, 1.0]) + np.array([pad, pad, 0.0]) / s
    ok = np.abs(local - c) <= h + np.array([0.0, 0.0, 1.0])
    return bool(ok[0] and ok[1] and (ok[2] or not z or len(p) < 3))


ON_TOP = 16.0  # units: a point this near a thing's top stands on it, not in it


def stands_inside(ref: dict, p, shrink: float = OVERLAP_SHRINK) -> bool:
    """Whether a standing point (an arrival, a stop) is inside ref's body: within `shrink` of its box in plan and
    below its top by more than ON_TOP (one standing on a deck or a roof is on it, not in it). The drafter's
    `geom.stands_in` calls this."""
    b = ref.get("bounds")
    if not b or not obb_contains(ref, p, shrink, 0.0, False):
        return False
    s = float(ref.get("scale") or 1.0)
    local = B.rotation(*(ref.get("rot") or [0, 0, 0])).T @ (np.asarray(p[:3], float) - np.asarray(ref["pos"], float)) / s
    top = b[5] if ref.get("walk") is None else float(ref["walk"])   # a walkway's deck, under its rails and posts
    return bool(b[2] - 1.0 <= local[2] < top - ON_TOP / s)


def point_seg(p, a, b) -> float:
    return float(B.seg_dist(p[0], p[1], a[0], a[1], b[0], b[1]))


def _seg_d(px: float, py: float, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """A point's distance in plan to each segment a[i]..b[i]."""
    dx, dy = b[:, 0] - a[:, 0], b[:, 1] - a[:, 1]
    L = dx * dx + dy * dy
    t = np.clip(((px - a[:, 0]) * dx + (py - a[:, 1]) * dy) / np.where(L > 0, L, 1.0), 0.0, 1.0)
    return np.hypot(px - (a[:, 0] + t * dx), py - (a[:, 1] + t * dy))


class Nav:
    """One navmesh decoded: verts, triangles, internal neighbours, edge links and door triangles."""

    def __init__(self, fk: str, space: str, cell, nv, key_of_raw):
        self.fk, self.space, self.cell = fk, space, cell
        self.verts = np.asarray(nv.verts, float)
        self.tri = nv.tris["v"].astype(int)
        self.flags = nv.tris["flags"].astype(int)
        self.edge = nv.tris["e"].astype(int)
        self.links = [(int(ln["type"]), key_of_raw(int(ln["navm"])), int(ln["tri"])) for ln in nv.links]
        self.doors = [(int(d["tri"]), key_of_raw(int(d["door"]))) for d in nv.doors]

    def _geom(self):
        """The triangles' corners, mean heights and plan bounds, as arrays (made at the first lookup)."""
        g = self.__dict__.get("_g")
        if g is None:
            v = np.asarray(self.verts, float).reshape(-1, 3)
            t = np.asarray(self.tri, int).reshape(-1, 3)
            a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
            box = (v[:, :2].min(axis=0), v[:, :2].max(axis=0)) if len(t) else (np.zeros(2), np.zeros(2))
            g = self._g = (a, b, c, (a[:, 2] + b[:, 2] + c[:, 2]) / 3, box)
        return g

    def near(self, p, plan_tol=STOP_PLAN_TOL, z_tol=STOP_Z_TOL) -> tuple[int, float]:
        """The triangle a standing point is on, and how well: within plan_tol of it in plan and z_tol of its mean height,
        the one under the point (else the nearest in plan) at the nearest height. (-1, inf) when none is."""
        a, b, c, zc, (lo, hi) = self._geom()
        px, py = float(p[0]), float(p[1])
        if not len(zc) or px < lo[0] - plan_tol or py < lo[1] - plan_tol or px > hi[0] + plan_tol or py > hi[1] + plan_tol:
            return -1, float("inf")
        dz = np.abs(zc - float(p[2]))
        idx = np.flatnonzero(dz <= z_tol)
        if not len(idx):
            return -1, float("inf")
        a, b, c, dz = a[idx], b[idx], c[idx], dz[idx]
        d1 = (px - b[:, 0]) * (a[:, 1] - b[:, 1]) - (a[:, 0] - b[:, 0]) * (py - b[:, 1])
        d2 = (px - c[:, 0]) * (b[:, 1] - c[:, 1]) - (b[:, 0] - c[:, 0]) * (py - c[:, 1])
        d3 = (px - a[:, 0]) * (c[:, 1] - a[:, 1]) - (c[:, 0] - a[:, 0]) * (py - a[:, 1])
        inside = ~(((d1 < 0) | (d2 < 0) | (d3 < 0)) & ((d1 > 0) | (d2 > 0) | (d3 > 0)))
        dp = np.minimum(np.minimum(_seg_d(px, py, a, b), _seg_d(px, py, b, c)), _seg_d(px, py, c, a))
        dp = np.where(inside, 0.0, dp)
        score = np.where(dp <= plan_tol, dp + dz * 0.01, np.inf)
        i = int(np.argmin(score))
        return (int(idx[i]), float(score[i])) if np.isfinite(score[i]) else (-1, float("inf"))

    def tri_at(self, p, plan_tol=STOP_PLAN_TOL, z_tol=STOP_Z_TOL) -> int:
        return self.near(p, plan_tol, z_tol)[0]

    def seam_edges(self) -> dict:
        """Every triangle edge lying on a cell line, by (the axis the line fixes, the line's cell index): rows of
        [lo, hi along the line, the two ends' place along it and height]. Made at the first asking."""
        got = self.__dict__.get("_seams")
        if got is None:
            a, b, c, _, _ = self._geom()
            got = self._seams = {}
            for p, q in ((a, b), (b, c), (c, a)):
                for ax in (0, 1):
                    line = np.round(p[:, ax] / B.CELL)
                    on = (np.abs(p[:, ax] - line * B.CELL) < 1) & (np.abs(q[:, ax] - line * B.CELL) < 1)
                    for i in np.flatnonzero(on):
                        u, w = float(p[i, 1 - ax]), float(q[i, 1 - ax])
                        got.setdefault((ax, int(line[i])), []).append((min(u, w), max(u, w), u, float(p[i, 2]), w, float(q[i, 2])))
            for k in got:
                got[k] = np.asarray(got[k], float)
        return got


class NavIndex:
    """Every navmesh by where it is, so a point is looked up in the meshes that can hold it: an exterior mesh by its
    cell, an interior's by its space."""

    def __init__(self, navs: dict):
        self.by_cell: dict = defaultdict(list)
        self.by_space: dict = defaultdict(list)
        for n in navs.values():
            if n.space == "exterior" and n.cell is not None:
                self.by_cell[tuple(n.cell)].append(n)
            else:
                self.by_space[n.space].append(n)

    def around(self, space: str, p, tol: float = STOP_PLAN_TOL) -> list:
        if space != "exterior":
            return self.by_space.get(space, [])
        cells = {B.cell_of(p[0] + dx, p[1] + dy) for dx in (-tol, tol) for dy in (-tol, tol)}
        return [n for c in sorted(cells) for n in self.by_cell.get(c, ())] + self.by_space.get("exterior", [])

    def at(self, space: str, p, plan_tol=STOP_PLAN_TOL, z_tol=STOP_Z_TOL):
        """(navmesh key, triangle) a standing point of `space` is on: the best of every mesh round it; None when off."""
        best, bs = None, float("inf")
        for n in self.around(space, p, plan_tol):
            t, sc = n.near(p, plan_tol, z_tol)
            if t >= 0 and sc < bs:
                best, bs = (n.fk, t), sc
        return best


def walked(n: Nav, water=None) -> np.ndarray:
    """Each triangle of a navmesh a street or a patrol may be laid on: dry, or water no deeper than WADE over it (a
    ford; `water(x, y)`, the water's level; without it, no water triangle)."""
    out = (np.asarray(n.flags, int) & WATER) == 0
    if water is not None and n.space == "exterior" and not out.all():
        v = np.asarray(n.verts, float).reshape(-1, 3)
        for i in np.flatnonzero(~out):
            c = v[np.asarray(n.tri[i], int)].mean(axis=0)
            w = water(float(c[0]), float(c[1]))
            out[i] = w is not None and w - c[2] <= WADE
    return out


def water_level(ctx: dict):
    """The water's level over a plan point (its cell's), or None where the cell has none."""
    water = {(c["x"], c["y"]): c.get("water") for c in ctx["facts"]["cells"]}

    def w(x: float, y: float) -> float | None:
        v = water.get(B.cell_of(x, y))
        return float(v) if v is not None and abs(v) < 1e8 else None
    return w


def nav_index(ctx: dict) -> NavIndex:
    if ctx.get("_nav_index_of") is not ctx["navs"]:
        ctx["_nav_index"], ctx["_nav_index_of"] = NavIndex(ctx["navs"]), ctx["navs"]
    return ctx["_nav_index"]


def components(navs: dict[str, Nav], door_pairs: dict[str, str], wade=None) -> dict[tuple[str, int], int]:
    """Connected components over every triangle: shared edges, edge links, and door triangles of paired doors. Water
    triangles join as any other, as Skyrim.esm's do (in Tamriel 16,729 water-dry shared edges and 1,670 water-dry
    edge links, measured): actors wade and swim them. `wade` (the water's level over a plan point): what joins without
    swimming (water deeper than a ford, `walked`, joins nothing), the drafter's test that a deck reaches its bank."""
    parent: dict = {}

    def find(x):
        while parent.setdefault(x, x) != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    door_tris: dict[str, list] = defaultdict(list)
    swum = {fk: ~walked(n, wade) for fk, n in navs.items()} if wade is not None else None

    def wet(n, i):
        return swum is not None and 0 <= i < len(swum[n.fk]) and bool(swum[n.fk][i])
    for n in navs.values():
        for i in range(len(n.tri)):
            find((n.fk, i))
            if wet(n, i):
                continue
            for k in range(3):
                e = int(n.edge[i][k])
                if n.flags[i] & (1 << k):
                    if 0 <= e < len(n.links):
                        _, tgt, tt = n.links[e]
                        if tgt in navs and not wet(navs[tgt], tt):
                            union((n.fk, i), (tgt, tt))
                elif e >= 0 and not wet(n, e):
                    union((n.fk, i), (n.fk, e))
        for ti, door in n.doors:
            door_tris[door].append((n.fk, ti))
    for d, partner in door_pairs.items():
        for a in door_tris.get(d, []):
            for b in door_tris.get(partner, []):
                union(a, b)
    return {k: find(k) for k in list(parent)}


# ---- loading --------------------------------------------------------------------------------------------------------

def load_navs(esp: Path, world_rows: dict) -> dict[str, Nav]:
    from tools.navmesh import esm, nvnm
    masters = esm.masters(esp)
    names = masters + [B.PLUGIN]

    def key_of_raw(raw: int) -> str:
        i = raw >> 24
        return B.key_of(names[i] if i < len(names) else "?", raw & 0xFFFFFF)

    cells = {}
    out = {}
    for rec in esm.records(esp, {b"NAVM", b"CELL"}):
        if rec.sig == b"CELL":
            continue
        nv = nvnm.decode(next(p for s, p in esm.subrecords(rec.data) if s == b"NVNM"))
        fk = key_of_raw(rec.fid)
        space = "exterior" if nv.world else key_of_raw(nv.cell)
        out[fk] = Nav(fk, space, nv.grid_xy, nv, key_of_raw)
        cells[fk] = nv.grid_xy
    # the world's navmesh round ours (for links out of ours, and stops outside our cells)
    for (x, y), e in world_rows.items():
        rec = base64.b64decode(e["navm"])
        fid = struct.unpack_from("<I", rec, 12)[0]
        fk = B.key_of(B.WORLD, fid & 0xFFFFFF)
        if fk in out:
            continue
        nv = nvnm.decode(next(p for s, p in esm.subrecords(rec[24:]) if s == b"NVNM"))
        wn = ["Skyrim.esm", B.WORLD]
        out[fk] = Nav(fk, "exterior", (x, y), nv, lambda r, wn=wn: B.key_of(wn[r >> 24] if (r >> 24) < 2 else "?", r & 0xFFFFFF))
        out[fk].world = True
    return out


def world_nav_rows(box) -> dict:
    rows = {}
    for p in sorted((B.WORLD_NAV / "navm").glob("cy*.jsonl.gz")):
        cy = int(p.name[2:6])
        if box[1] <= cy <= box[3]:
            for ln in gzip.open(p, "rt"):
                e = json.loads(ln)
                if box[0] <= e["x"] <= box[2]:
                    rows[(e["x"], e["y"])] = e
    return rows


def load(place_id: str, out: Path) -> dict:
    plan = json.loads((out / "shards" / place_id / "plan.json").read_text())
    esp = out / "plugin" / B.PLUGIN
    tmp = out / "tmp" / f"check_{place_id}"
    tmp.mkdir(parents=True, exist_ok=True)
    B.build_tool()
    B.tool("dump", str(esp), str(B.WORLD_ESM), str(tmp / "dump.json"))
    dump = json.loads((tmp / "dump.json").read_text())
    (tmp / "dump.json").unlink()
    cells = {(c["x"], c["y"]) for c in plan["cells"]}
    facts = B.world_facts(cells, tmp)
    tmp.rmdir()
    xs, ys = [c[0] for c in cells] or [0], [c[1] for c in cells] or [0]
    r = B.NAV_RING + 4  # every world mesh a shipped one can link into
    world_rows = world_nav_rows((min(xs) - r, min(ys) - r, max(xs) + r, max(ys) + r))
    navs = load_navs(esp, world_rows)
    edid = {c["fk"]: c["edid"] for c in dump["cells"]}
    for n in navs.values():
        n.space = edid.get(n.space, n.space) if n.space != "exterior" else n.space
    from tools.places.stock import verify as stock_verify
    return {"place_id": place_id, "plan": plan, "dump": dump, "facts": facts, "navs": navs, "gives": gives_of(place_id),
            "place_dir": B.PLACES / place_id, "stock": stock_verify.load(place_id, plan, dump, esp)}


def gives_of(place_id: str) -> list[dict]:
    return [r for r in B.jsonl(B.DB / "place_give.jsonl") if r["place_id"] == place_id]


# ---- the context --------------------------------------------------------------------------------------------------

def mine(ctx: dict) -> dict:
    """This place's records in the read-back, by key."""
    plan, dump = ctx["plan"], ctx["dump"]
    keys = {r["fk"] for r in plan["refs"]}
    ppl = plan.get("people") or {}
    keys |= {m["fk"] for m in ppl.get("markers", [])}
    refs = {r["fk"]: r for r in dump["refs"] if r["fk"] in keys}
    actors = {a["fk"]: a for a in dump["actors"] if a["fk"] in {x["fk"] for x in ppl.get("actors", [])}}
    npcs = {n["fk"]: n for n in dump["npcs"] if n["fk"] in {x["fk"] for x in ppl.get("npcs", [])}}
    return {"refs": refs, "actors": actors, "npcs": npcs, "rows": {r["fk"]: r for r in plan["refs"]}}


def ground(ctx: dict):
    """Ground height at (x, y) from the BUILT land: our LAND override where there is one, else the world's."""
    from tools.newworld.world import quantize
    steps = {}
    for c in ctx["facts"]["cells"]:
        if c.get("deltas"):
            steps[(c["x"], c["y"])] = B.cell_steps(c)
    for L in ctx["dump"]["land"]:
        if L.get("x") is not None:
            d = np.frombuffer(base64.b64decode(L["deltas"]), np.int8).reshape(33, 33)
            steps[(L["x"], L["y"])] = quantize.decode(float(L["offset"]), d)

    def z(x, y):
        cx, cy = B.cell_of(x, y)
        s = steps.get((cx, cy))
        if s is None:
            return None
        fx, fy = (x - cx * B.CELL) / B.QUAD, (y - cy * B.CELL) / B.QUAD
        i, j = min(int(fx), 31), min(int(fy), 31)
        u, v = fx - i, fy - j
        h = (s[j, i] * (1 - u) * (1 - v) + s[j, i + 1] * u * (1 - v) + s[j + 1, i] * (1 - u) * v + s[j + 1, i + 1] * u * v)
        return float(h) * 8.0
    return z, steps


DECK_SEAM = [(24.0, 0.0), (-24.0, 0.0), (0.0, 24.0), (0.0, -24.0)]  # a gap in a deck's faces narrower than this span is a seam
STAND_AREA = 1024.0  # square units: an upward surface smaller than a person's footprint (a post's or a rail's top) is not stood on


def _up_faces(model: str, bounds) -> np.ndarray:
    """A walkway model's upward faces one stands on (the deck, steps' treads: upward faces joined at their corners
    into a surface of at least STAND_AREA, so a post's or a rail's cap is left out), in model units; its record box's
    top when its collision cannot be read."""
    from tools.places import seat
    m = str(model or "").lower()
    if m not in _UP:
        try:
            t = seat._collision_tris(m)
        except Exception:
            t = None
        if t is None or not len(t):
            lo, hi = np.array(bounds[:3], float), np.array(bounds[3:], float)
            t = np.array([[[lo[0], lo[1], hi[2]], [hi[0], lo[1], hi[2]], [hi[0], hi[1], hi[2]]],
                          [[lo[0], lo[1], hi[2]], [hi[0], hi[1], hi[2]], [lo[0], hi[1], hi[2]]]], float)
        t = np.asarray(t, float).reshape(-1, 3, 3)
        n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
        ln = np.linalg.norm(n, axis=1)
        up = t[(ln > 0) & (n[:, 2] >= 0.7 * ln)]
        area = np.linalg.norm(np.cross(up[:, 1] - up[:, 0], up[:, 2] - up[:, 0]), axis=1) / 2
        parent = list(range(len(up)))

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i
        first: dict = {}
        for i, tri in enumerate(up):
            for v in tri:
                j = first.setdefault(tuple(np.round(v).astype(int)), i)
                a, b = find(i), find(j)
                if a != b:
                    parent[a] = b
        root = [find(i) for i in range(len(up))]
        size: dict = defaultdict(float)
        for i, r in enumerate(root):
            size[r] += area[i]
        _UP[m] = up[np.array([size[r] >= STAND_AREA for r in root], bool)] if len(up) else up
    return _UP[m]


_UP: dict = {}


def surfaces(ctx: dict):
    """(ground, deck, wet): the height of a plan point on the built land; the walked surface of the place's walkway
    pieces over it (their collision's upward faces under the deck's own top, `walk`, so rails and posts are not
    stood on), or None where no deck stands; and the water's level where the ground is under it, else None."""
    z, _ = ground(ctx)
    m = mine(ctx)
    water = water_level(ctx)
    faces, boxes = [], []
    for fk, row in m["rows"].items():
        r = m["refs"].get(fk)
        if row.get("walk") is None or r is None or r.get("space") != "exterior" or not r.get("bounds"):
            continue
        s = float(r.get("scale") or 1.0)
        up = _up_faces(r.get("model"), r["bounds"])
        up = up[up.mean(axis=1)[:, 2] <= float(row["walk"]) + ON_TOP]
        if not len(up):
            continue
        w = up.reshape(-1, 3) * s @ B.rotation(*(r.get("rot") or [0, 0, 0])).T + np.asarray(r["pos"], float)
        w = w.reshape(-1, 3, 3)
        faces.append(w)
        boxes.append((w[:, :, :2].min(axis=(0, 1)), w[:, :, :2].max(axis=(0, 1))))

    def deck(x: float, y: float) -> float | None:
        h = deck_at(x, y)
        if h is None:   # a seam between two treads or two boards is still the deck: the surface just round the point
            near = [v for v in (deck_at(x + dx, y + dy) for dx, dy in DECK_SEAM) if v is not None]
            h = max(near) if len(near) >= 2 else None
        return h

    def deck_at(x: float, y: float) -> float | None:
        best = None
        for (lo, hi), T in zip(boxes, faces):
            if not (lo[0] <= x <= hi[0] and lo[1] <= y <= hi[1]):
                continue
            a, e1, e2 = T[:, 0], T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]
            den = e1[:, 0] * e2[:, 1] - e2[:, 0] * e1[:, 1]
            dd = np.where(den == 0, 1.0, den)
            vx, vy = x - a[:, 0], y - a[:, 1]
            u = (vx * e2[:, 1] - e2[:, 0] * vy) / dd
            v = (e1[:, 0] * vy - vx * e1[:, 1]) / dd
            ok = (den != 0) & (u >= -1e-6) & (v >= -1e-6) & (u + v <= 1 + 1e-6)
            if ok.any():
                h = float((a[:, 2] + u * e1[:, 2] + v * e2[:, 2])[ok].max())
                best = h if best is None else max(best, h)
        return best

    def wet(x: float, y: float) -> float | None:
        w, g = water(x, y), z(x, y)
        return w if w is not None and g is not None and g < w - 8 else None
    return z, deck, wet


# ---- the checks -----------------------------------------------------------------------------------------------------

def check_plugin(ctx) -> list[str]:
    d = ctx["dump"]
    bad = [f"unresolved link: {u}" for u in d["unresolved"]]
    if B.WORLD not in d["masters"]:
        bad.append(f"not mastered on {B.WORLD}: masters {d['masters']}")
    return bad


def built_ground(ctx):
    """lane D's seat.Ground (the one seating function's view of land and water) over the BUILT land heights."""
    from tools.places import seat as S
    pid = ctx.get("place_id")
    g = S.ground_for(pid) if pid and (S.BUNDLES / f"ground.{pid}").exists() else S.Ground({}, {})  # water: the ground bundle
    _, steps = ground(ctx)
    for (cx, cy), st in steps.items():
        g.cells[(cx, cy)] = [float(v) * 8.0 for v in np.asarray(st, np.float64).reshape(-1)]
    return g


def check_seat(ctx) -> list[str]:
    """Every exterior ref's BUILT z is what seat.seat_z gives at its BUILT x, y, yaw on the built land."""
    from tools.places import seat as S
    g = built_ground(ctx)
    m = mine(ctx)
    built = []
    for r in ctx["plan"]["refs"]:
        if r["space"] != "exterior":
            continue
        got = m["refs"].get(r["fk"])
        if got is None:
            if (r.get("seat") or {}).get("mode", "free") != "free":
                ctx.setdefault("_seat_missing", []).append(f"{r['id']}: not in the plugin")
            continue
        built.append({"id": r["id"], "seat": r.get("seat") or {"mode": "free"}, "pos": list(got["pos"]),
                      "rot": list(r.get("rot") or [0, 0, 0])})
    want = {x["id"]: x["pos"][2] for x in built}
    trial = [dict(x, pos=list(x["pos"])) for x in built]
    S.seat_all(trial, g)
    bad = list(ctx.pop("_seat_missing", []))
    for x in trial:
        if abs(x["pos"][2] - want[x["id"]]) > SEAT_TOL:
            s = x["seat"]
            bad.append(f"{x['id']}: built z {want[x['id']]:.0f}, seat {s.get('mode')}+{s.get('dz', 0)} gives {x['pos'][2]:.0f}")
    return bad


def overlap_pairs(things: list[dict], pad: float = 0.0, z: bool = True) -> list[tuple[dict, dict]]:
    """Every (a, b) of solids in one space where a's origin stands inside b's box and the source did not have them so.
    Each thing: {id, kind, space, pos, rot, scale, bounds, src?, cluster?, seat?}. The one overlap rule: `check` runs it
    on the plugin's read-back, the drafter on its rows (bounds from its bundle) while fitting and in `draft check`."""
    grid: dict = defaultdict(list)
    solid = [t for t in things if t.get("kind") in SOLID]
    for b in solid:
        bb = b.get("bounds")
        if not bb:
            continue
        rad = math.sqrt(sum(max(abs(bb[i]), abs(bb[i + 3])) ** 2 for i in range(3))) * float(b.get("scale") or 1.0) + pad
        x, y = b["pos"][0], b["pos"][1]
        for i in range(math.floor((x - rad) / 1024), math.floor((x + rad) / 1024) + 1):
            for j in range(math.floor((y - rad) / 1024), math.floor((y + rad) / 1024) + 1):
                grid[(b["space"], i, j)].append(b)
    out = []
    for a in solid:
        for b in grid.get((a["space"], math.floor(a["pos"][0] / 1024), math.floor(a["pos"][1] / 1024)), ()):
            if a is b or a.get("id") == b.get("id"):
                continue
            if a["space"] != "exterior" and b.get("kind") in ("building", "static"):
                continue  # an interior's shell and walls hold the room
            if obb_contains(b, a["pos"], OVERLAP_SHRINK, pad, z) and not _source_had(a, b):
                out.append((a, b))
    return out


def check_overlap(ctx) -> list[str]:
    m = mine(ctx)
    rows = m["rows"]
    things = [{**rows[r["fk"]], "space": r["space"], "pos": r["pos"], "rot": r["rot"], "scale": r.get("scale"),
               "bounds": r.get("bounds")} for r in m["refs"].values() if r["fk"] in rows]
    return [f"{a['id']} stands inside {b['id']}" for a, b in overlap_pairs(things)]


def rests(a: dict, b: dict) -> bool:
    """One of the pair rests on the other: its seat names the other as what it stands `on` (a barrel on a deck, a
    flight of steps hung on its pier, a walkway piece on the one it continues) or as its `carrier` (the ship whose
    gangway it is). The one carrier rule, the drafter's and the build's."""
    sa, sb = a.get("seat") or {}, b.get("seat") or {}
    return b.get("id") in (sa.get("on"), sa.get("carrier")) or a.get("id") in (sb.get("on"), sb.get("carrier"))


def _source_had(a: dict, b: dict) -> bool:
    """The pair may stand in each other: one rests on the other (`rests`), or the source had them in this relative
    pose: both copied, and either inside one copied interior (it keeps its frame) or in one exterior cluster (the fit
    moves a cluster as one rigid piece)."""
    if rests(a, b):
        return True
    if not (a.get("src") and b.get("src") and a["space"] == b["space"]):
        return False
    return a["space"] != "exterior" or (a.get("cluster") is not None and a.get("cluster") == b.get("cluster"))


def door_pairs(ctx) -> dict[str, str]:
    return {r["fk"]: r["door"]["to_ref"] for r in mine(ctx)["refs"].values() if r.get("door")}


def check_doors(ctx) -> list[str]:
    m = mine(ctx)
    refs = {**{r["fk"]: r for r in ctx["dump"]["refs"]}}
    idx = nav_index(ctx)
    solids: dict = defaultdict(list)  # per space: the bodies an arrival can stand in, each with its reach in plan
    for o in ctx["dump"]["refs"]:
        row = m["rows"].get(o["fk"])
        # an interior's shell holds the room: its buildings and statics are not bodies to stand in
        if row and o.get("bounds") and row.get("kind") in (SOLID if o["space"] == "exterior" else SOLID - {"building", "static"}):
            bb = o["bounds"]
            reach = math.sqrt(sum(max(abs(bb[i]), abs(bb[i + 3])) ** 2 for i in range(3))) * float(o.get("scale") or 1.0)
            solids[o["space"]].append((o, row, reach))
    bad = []
    for r in m["refs"].values():
        d = r.get("door")
        if not d:
            continue
        rid = m["rows"].get(r["fk"], {}).get("id", r["fk"])
        p = refs.get(d["to_ref"])
        if p is None or not p.get("door") or p["door"]["to_ref"] != r["fk"]:
            bad.append(f"door {rid}: its partner {d['to_ref']} does not lead back")
            continue
        if not r.get("persistent"):
            bad.append(f"door {rid}: a load door must be persistent")
        # the marker by this door (where one lands using the partner): on navmesh, out of every wall
        at = p["door"]["to_pos"]
        space = r["space"]
        on_id = (m["rows"].get(r["fk"], {}).get("seat") or {}).get("on")
        stands_on = next((x["fk"] for x in m["rows"].values() if x.get("id") == on_id), None) if on_id else None
        if idx.at(space, at) is None:
            bad.append(f"door {rid}: its arrival point {[round(v) for v in at]} is on no navmesh (facing a wall?)")
        for o, row, reach in solids.get(space, ()):
            if o["fk"] == stands_on or o["fk"] == r["fk"]:
                continue  # the thing the door stands on (its own building) holds the door, not the arrival
            if math.dist(at[:2], o["pos"][:2]) <= reach and stands_inside({**o, "walk": row.get("walk")}, at):
                bad.append(f"door {rid}: its arrival point is inside {row.get('id', o['fk'])}")
    return bad


def check_people(ctx) -> list[str]:
    m = mine(ctx)
    ppl = ctx["plan"].get("people") or {}
    allrefs = {r["fk"]: r for r in ctx["dump"]["refs"]}
    pk = {p["fk"]: p for p in ctx["dump"]["packages"]}
    comp = components(ctx["navs"], door_pairs(ctx))
    node = nav_index(ctx).at
    bad = []

    def where(fk):
        r = allrefs.get(fk)
        if r is None:
            return None
        return r["space"], r["pos"]

    for n in ppl.get("npcs", []):
        got = m["npcs"].get(n["fk"])
        who = n["id"]
        if got is None:
            bad.append(f"{who}: no actor base in the plugin")
            continue
        beds = [r for r in m["refs"].values() if r.get("owner") == n["fk"] and r.get("base_type") == "FURN"]
        if not beds and n.get("role") != "innkeeper":  # vanilla's innkeepers keep the inn all day (one 24-hour package)
            bad.append(f"{who}: no bed owned")
        prev = None
        for k in got["packages"]:
            p = pk.get(k)
            if p is None:
                bad.append(f"{who}: package {k} missing")
                continue
            tgt = p.get("location") or p.get("target")
            if p.get("target_linked"):  # a patrol, the vanilla way: the actor's own linked ref (no keyword) starts the chain
                act = next((a for a in ctx["dump"]["actors"] if a.get("base") == n["fk"]), {})
                tgt = next((ln["ref"] for ln in act.get("linked") or [] if not ln.get("keyword")), None)
                if tgt is None:
                    bad.append(f"{who}: {p['edid']} patrols its linked ref, but the actor has no linked ref without a keyword")
                    continue
                chain, cur = [], tgt
                while cur and cur not in chain:  # the chain of markers must be ours and resolve
                    r = allrefs.get(cur)
                    if r is None:
                        bad.append(f"{who}: {p['edid']} patrol chain reaches {cur}, which is not a ref of ours")
                        break
                    chain.append(cur)
                    cur = next((ln["ref"] for ln in r.get("linked") or [] if not ln.get("keyword")), None)
                if len(chain) < 2:
                    bad.append(f"{who}: {p['edid']} patrol chain has fewer than two markers")
                # every marker stands on the walking mesh, on the island of the marker before it (a loop's first
                # after its last): the game walks marker to marker, and stops at one it cannot path to
                on = [node(*where(k)) for k in chain]
                for j, k in enumerate(chain):
                    if on[j] is None:
                        sp, at = where(k)
                        bad.append(f"{who}: {p['edid']} patrol marker {j + 1} of {len(chain)} at {[round(v) for v in at]} in {sp} "
                                   f"is off the navmesh")
                legs = list(zip(range(len(chain)), range(1, len(chain)))) + ([(len(chain) - 1, chain.index(cur))] if cur in chain else [])
                for i, j in legs:
                    if on[i] is not None and on[j] is not None and comp.get(on[i]) != comp.get(on[j]):
                        bad.append(f"{who}: {p['edid']} patrol marker {j + 1} of {len(chain)} is not reachable from marker {i + 1}")
                if chain and on[0] is not None:
                    if prev is not None and comp.get(prev) != comp.get(on[0]):
                        bad.append(f"{who}: {p['edid']} is not reachable from the stop before")
                    prev = on[0]
                continue
            w = where(tgt) if tgt else None
            if w is None:
                bad.append(f"{who}: {p['edid']} has no place of ours")
                continue
            nd = node(*w)
            if nd is None:
                bad.append(f"{who}: {p['edid']} stop {[round(v) for v in w[1]]} in {w[0]} is off the navmesh")
                continue
            if prev is not None and comp.get(prev) != comp.get(nd):
                bad.append(f"{who}: {p['edid']} is not reachable from the stop before")
            prev = nd
    return bad


def check_navmesh(ctx) -> list[str]:
    navs = ctx["navs"]
    mine_navs = {k: n for k, n in navs.items() if not getattr(n, "world", False)}
    bad = []
    # every edge link is answered from the other side (joined edge for edge)
    for n in mine_navs.values():
        for i in range(len(n.tri)):
            for k in range(3):
                if not n.flags[i] & (1 << k):
                    continue
                e = int(n.edge[i][k])
                if not 0 <= e < len(n.links):
                    bad.append(f"{n.fk}: tri {i} names edge link {e}, which the mesh does not have ({len(n.links)} links)")
                    continue
                _, tgt, tt = n.links[e]
                o = navs.get(tgt)
                if o is None:
                    bad.append(f"{n.fk}: tri {i} links into {tgt}, which is not loaded")
                    continue
                if not 0 <= tt < len(o.tri):
                    bad.append(f"{n.fk}: tri {i} links {tgt} tri {tt}, which {tgt} does not have ({len(o.tri)} triangles)")
                    continue
                if not any(o.flags[tt] & (1 << q) and 0 <= int(o.edge[tt][q]) < len(o.links) and o.links[int(o.edge[tt][q])][1] == n.fk
                           and o.links[int(o.edge[tt][q])][2] == i for q in range(3)):
                    bad.append(f"{n.fk}: tri {i} links {tgt} tri {tt}, which does not link back (unjoined edge)")
    # open edges of ours on a seam with a neighbour's navmesh across: unjoined
    idx = nav_index(ctx)
    for n in mine_navs.values():
        if n.space != "exterior" or n.cell is None:
            continue
        x0, y0 = n.cell[0] * B.CELL, n.cell[1] * B.CELL
        for i in range(len(n.tri)):
            for k in range(3):
                if n.flags[i] & (1 << k) or n.edge[i][k] >= 0:
                    continue
                a, b = n.verts[n.tri[i][k]], n.verts[n.tri[i][(k + 1) % 3]]
                on = (abs(a[0] - x0) < 1 and abs(b[0] - x0) < 1) or (abs(a[0] - x0 - B.CELL) < 1 and abs(b[0] - x0 - B.CELL) < 1) or \
                     (abs(a[1] - y0) < 1 and abs(b[1] - y0) < 1) or (abs(a[1] - y0 - B.CELL) < 1 and abs(b[1] - y0 - B.CELL) < 1)
                if on and _across(idx, n, (a + b) / 2, a, b):
                    bad.append(f"{n.fk}: open seam edge at {[round(v) for v in (a + b) / 2]} with navmesh across it (unjoined)")
    # islands that hold a door or a routine stop of the place
    comp = components(navs, door_pairs(ctx))
    sizes = defaultdict(int)
    for k, c in comp.items():
        sizes[c] += 1
    main = max(sizes, key=sizes.get) if sizes else None
    m = mine(ctx)
    for r in m["refs"].values():
        if not r.get("door"):
            continue
        for n in mine_navs.values():
            for ti, d in n.doors:
                if d == r["fk"] and comp.get((n.fk, ti)) != main:
                    bad.append(f"door {m['rows'].get(r['fk'], {}).get('id', r['fk'])}: its navmesh is an island ({sizes[comp[(n.fk, ti)]]} triangles)")
    return bad


def check_streets(ctx) -> list[str]:
    """Every street, path and walkway (its line sampled every 64 units) and every guard's patrol point stands on the
    town's main network at its own level, never laid along water: over a deck, on a dry triangle within DECK_TOL of
    the deck's own surface (never the seabed under it); on land or in a ford (water no deeper than WADE), on the
    triangle the stop lookup finds; over deeper water with no deck, only on a dry triangle right over it; and a line's
    point reached from the one before without a drop or climb steeper than a walked slope (`walk.Walkable.line_ok`)."""
    from tools.places.draft import walk
    pdir = ctx.get("place_dir")
    paths = ctx["paths"] if "paths" in ctx else (B.jsonl(pdir / "paths.jsonl") if pdir else [])
    folk = ctx["folk"] if "folk" in ctx else (B.jsonl(pdir / "people.jsonl") if pdir else [])
    if not paths and not folk:
        return []
    W = walk.Walkable(ctx, *surfaces(ctx))
    st, pa = walk.off_network(paths, folk, W)
    ctx["streets"] = {"street_points": sum(len(walk.samples(p["points"])) for p in paths), "street_off": len(st),
                      "patrol_points": sum(len((p.get("patrol") or {}).get("points") or []) for p in folk),
                      "patrol_off": len(pa)}
    return ([f"street {s} point {[round(v) for v in q]} is off the built walkable network{W.why(q)}" for s, q in st]
            + [f"{who}: patrol point {[round(v) for v in q]} is off the built walkable network{W.why(q)}" for who, q in pa])


def _across(idx: NavIndex, n, mid, a=None, b=None) -> bool:
    """A neighbour's navmesh meets this open seam edge: one of its own edges lies on the same cell line over a
    stretch of ours at a like height (the world's seam audit, tools/navmesh/province.seam_audit: a neighbour that
    only touches the line at a corner, or none, is where walkable ground ends at the seam, a boundary)."""
    from tools.navmesh import params
    if a is None:
        a = b = mid
    ax = 0 if abs(a[0] - b[0]) < 1 else 1  # the axis the cell line fixes
    line = (ax, int(round(a[ax] / B.CELL)))
    lo, hi = sorted((float(a[1 - ax]), float(b[1 - ax])))

    def zat(u0, z0, u1, z1, m):
        d = u1 - u0
        return np.where(np.abs(d) > 1e-6, z0 + (m - u0) / np.where(np.abs(d) > 1e-6, d, 1.0) * (z1 - z0), (z0 + z1) / 2)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        for o in idx.by_cell.get((n.cell[0] + dx, n.cell[1] + dy), ()):
            E = o.seam_edges().get(line)
            if o is n or E is None:
                continue
            s0, s1 = np.maximum(lo, E[:, 0]), np.minimum(hi, E[:, 1])
            m = (s0 + s1) / 2
            ours = zat(float(a[1 - ax]), float(a[2]), float(b[1 - ax]), float(b[2]), m)
            if ((s1 - s0 >= 1) & (np.abs(ours - zat(E[:, 2], E[:, 3], E[:, 4], E[:, 5], m)) <= params.SEAM_DZ)).any():
                return True
    return False


def check_land(ctx) -> list[str]:
    from tools.newworld.world import quantize
    bad = []
    rows = B.jsonl(ctx["place_dir"] / "land.jsonl") if ctx.get("place_dir") else []
    rows = ctx.get("land_rows", rows)
    _, steps = ground(ctx)
    world = {(c["x"], c["y"]): B.cell_steps(c) for c in ctx["facts"]["cells"] if c.get("deltas")}
    for r in rows:
        cx, cy = r["cell"]
        if (cx, cy) not in world or (cx, cy) not in steps:
            bad.append(f"land {cx},{cy}: land.jsonl patches a cell the world has no land for")
            continue
        for row, col, dz in r["verts"]:
            want = round(world[(cx, cy)][int(row), int(col)] + dz / 8.0)
            got = steps[(cx, cy)][int(row), int(col)]
            if abs(got - want) > 0.5:
                bad.append(f"land {cx},{cy} [{row},{col}]: built {got * 8:.0f}, land.jsonl wants {want * 8:.0f}")
    built = {(L["x"], L["y"]) for L in ctx["dump"]["land"] if L.get("x") is not None}
    for (cx, cy) in built:
        s = steps[(cx, cy)]
        for (dx, dy), mine_edge, their_edge in (((1, 0), (slice(None), 32), (slice(None), 0)), ((-1, 0), (slice(None), 0), (slice(None), 32)),
                                                ((0, 1), (32, slice(None)), (0, slice(None))), ((0, -1), (0, slice(None)), (32, slice(None)))):
            o = steps.get((cx + dx, cy + dy))
            if o is not None and not np.array_equal(s[mine_edge], o[their_edge]):
                bad.append(f"land {cx},{cy}: tears at the seam with {cx + dx},{cy + dy} ({int(np.abs(s[mine_edge] - o[their_edge]).max() * 8)} units)")
    del quantize
    return bad


def check_clear(ctx) -> list[str]:
    bad = []
    over = {o["fk"]: o for o in ctx["dump"]["overrides"]}
    cleared = set()
    for c in ctx["plan"]["clear"]:
        o = over.get(c["fk"])
        cleared.add(c["fk"])
        if o is None or not (int(o["flags"]) & 0x800):
            bad.append(f"cleared plant {c['fk']} is still enabled")
    m = mine(ctx)
    buildings = [r for r in m["refs"].values() if m["rows"].get(r["fk"], {}).get("kind") in ("building", "static") and r["space"] == "exterior"]
    doors = [r for r in m["refs"].values() if r.get("door") and r["space"] == "exterior"]
    paths = ctx.get("paths") if "paths" in ctx else (B.jsonl(ctx["place_dir"] / "paths.jsonl") if ctx.get("place_dir") else [])
    G = 1024.0  # a grid over the place: each plant is tested against what reaches its square only
    near_b, near_d, near_p = defaultdict(list), defaultdict(list), defaultdict(list)

    def squares(x0, y0, x1, y1):
        return ((i, j) for i in range(math.floor(x0 / G), math.floor(x1 / G) + 1) for j in range(math.floor(y0 / G), math.floor(y1 / G) + 1))
    for b in buildings:
        bb = b.get("bounds")
        if bb:
            rad = math.sqrt(sum(max(abs(bb[i]), abs(bb[i + 3])) ** 2 for i in range(3))) * float(b.get("scale") or 1.0)
            for sq in squares(b["pos"][0] - rad, b["pos"][1] - rad, b["pos"][0] + rad, b["pos"][1] + rad):
                near_b[sq].append(b)
    for d in doors:
        for sq in squares(d["pos"][0] - PLANT_DOOR_CLEAR, d["pos"][1] - PLANT_DOOR_CLEAR, d["pos"][0] + PLANT_DOOR_CLEAR, d["pos"][1] + PLANT_DOOR_CLEAR):
            near_d[sq].append(d)
    for pa in paths:
        half = float(pa.get("width", 256)) / 2
        for a, b in zip(pa["points"][:-1], pa["points"][1:]):
            for sq in squares(min(a[0], b[0]) - half, min(a[1], b[1]) - half, max(a[0], b[0]) + half, max(a[1], b[1]) + half):
                near_p[sq].append((pa["id"], half, a, b))
    for cell in ctx["facts"]["cells"]:
        for w in cell.get("refs", []):
            if w["fk"] in cleared or int(w.get("flags", 0)) & 0x800 or not (w.get("base_type") in PLANT_TYPES or w.get("plant") is True):  # a plant by its kind, never by default
                continue
            p = w.get("pos")
            if p is None:
                continue
            why = None
            sq = (math.floor(p[0] / G), math.floor(p[1] / G))
            if any(obb_contains(b, p, 1.0) for b in near_b.get(sq, ())):
                why = "in a building"
            elif any(math.dist(p[:2], d["pos"][:2]) < PLANT_DOOR_CLEAR for d in near_d.get(sq, ())):
                why = "in a doorway"
            else:
                on = next((pid for pid, half, a, b in near_p.get(sq, ()) if point_seg(p, a, b) < half), None)
                why = f"on path {on}" if on is not None else None
            if why:
                bad.append(f"world plant {w['fk']} ({w['base']}) stands {why}")
    return bad


RENT_ROOM_FACTION, RENT_WI = "Skyrim.esm:09CC97", "Skyrim.esm:035D64"
RENT_INN_RANKS = {RENT_ROOM_FACTION: -1, "Skyrim.esm:05091B": 0, "Skyrim.esm:051596": 0}  # an innkeeper's factions, as Dagur's
_CMP = {"EqualTo": lambda a, b: a == b, "NotEqualTo": lambda a, b: a != b, "GreaterThan": lambda a, b: a > b,
        "GreaterThanOrEqualTo": lambda a, b: a >= b, "LessThan": lambda a, b: a < b, "LessThanOrEqualTo": lambda a, b: a <= b}


def rent_offer_verdicts(npc: dict, offer: list[dict]) -> list[tuple[str, str]]:
    """Each condition of vanilla's rent offer INFO (Skyrim.esm:079B1A, read into dump["rent_offer"]) against this
    actor base's records: (the condition in words, "ok" | "FAIL" | "runtime: why" | "not evaluated: why"). Conditions on
    the actor are decided from the base's factions, ranks and ids; what only the running game knows (the player's gold,
    an actor value) is named, never guessed."""
    ranks = {f["faction"]: f["rank"] for f in npc.get("faction_ranks") or []}
    out = []
    for c in offer:
        fn, op, want = c.get("fn", "?"), c.get("op", "EqualTo"), c.get("value")
        text = f"{fn} {c.get('faction') or c.get('actor_value') or c.get('item') or c.get('object') or ''} {op} {want} ({c.get('run_on')})"
        if c.get("run_on") != "Subject":
            out.append((text, f"runtime: {c.get('run_on')} is the player or a reference, not this actor's records"))
        elif fn == "GetInFaction" and isinstance(want, (int, float)):
            out.append((text, "ok" if _CMP[op](1 if c["faction"] in ranks else 0, want) else "FAIL"))
        elif fn == "GetFactionRank" and isinstance(want, (int, float)):
            out.append((text, "ok" if _CMP[op](ranks.get(c["faction"], -1), want) else "FAIL"))
        elif fn == "GetIsID" and isinstance(want, (int, float)):
            out.append((text, "ok" if _CMP[op](1 if c["object"] in (npc["fk"], npc.get("template")) else 0, want) else "FAIL"))
        elif fn == "GetActorValue":
            out.append((text, "runtime: an actor value is set by scripts; a new base starts at its source's value"))
        else:
            out.append((text, f"not evaluated: {fn} is not one the check knows"))
    return out


def inn_room_problems(npc: dict, m: dict, facts: dict, dump: dict) -> list[str]:
    """What one innkeeper lacks to rent a room the vanilla way (empty: nothing)."""
    bad = []
    ranks = {f["faction"]: f["rank"] for f in npc.get("faction_ranks") or []}
    for fa, want in RENT_INN_RANKS.items():
        if ranks.get(fa) != want:
            bad.append(f"{fa} at rank {want} (has {ranks.get(fa)})")
    if npc.get("voice") not in (dump.get("rent_voices") or []):
        bad.append(f"a voice of form list Skyrim.esm:03B4A5 (has {npc.get('voice')})")
    script = next((s for s in npc.get("scripts") or [] if s["name"] == "RentRoomScript"), None)
    props = {p["name"]: p.get("value") for p in (script or {}).get("props", [])}
    if script is None:
        bad.append("RentRoomScript")
    else:
        bed = m["refs"].get(props.get("Bed"))
        if not (bed and bed.get("base_type") == "FURN" and bed.get("owner") in facts and facts[bed["owner"]].get("vendor")
                and bed["owner"] in npc.get("faction_keys", [])):
            bad.append(f"RentRoomScript Bed {props.get('Bed')} a FURN ref of ours owned by this innkeeper's vendor faction")
        if props.get("WI") != RENT_WI:
            bad.append(f"RentRoomScript WI {RENT_WI} (has {props.get('WI')})")
    bad += [f"rent offer 079B1A: {t}" for t, v in rent_offer_verdicts(npc, dump.get("rent_offer") or []) if v == "FAIL"]
    return bad


SHRINE_SCRIPT = "TempleBlessingScript"
SHRINE_SECONDS = 28800  # eight hours, as vanilla's blessings


def shrine_problems(ctx: dict, m: dict) -> list[str]:
    """What the place's Hist shrine lacks to bless the vanilla way (empty: nothing). A ref of ours whose base is an
    activator of ours carrying TempleBlessingScript with TempleBlessing a spell of ours (Resist Disease for eight hours at one
    fixed magnitude), BlessingMessage a message of ours with text, and AltarRemoveMsg set."""
    dump = ctx["dump"]
    acts = {a["fk"]: a for a in dump.get("activators") or []}
    spells = {s["fk"]: s for s in dump.get("spells") or []}
    msgs = {x["fk"]: x for x in dump.get("messages") or []}
    shrines = [r for r in m["refs"].values() if r.get("base") in acts]
    if not shrines:
        return ["no shrine ref: the draft must add one where the source town's shrine or Hist stands"]
    tried = []
    for r in shrines:
        bad = []
        sc = next((x for x in acts[r["base"]].get("scripts") or [] if x["name"] == SHRINE_SCRIPT), None)
        props = {p["name"]: p.get("value") for p in (sc or {}).get("props", [])}
        if sc is None:
            bad.append(f"base {acts[r['base']].get('edid')} has no {SHRINE_SCRIPT}")
        else:
            sp = spells.get(props.get("TempleBlessing") or "")
            if sp is None:
                bad.append(f"TempleBlessing {props.get('TempleBlessing')} is not a spell of ours")
            else:
                eff = [e for e in sp["effects"] if e.get("actor_value") == "ResistDisease"]
                if not eff:
                    bad.append(f"{sp.get('edid')} has no Resist Disease effect")
                elif not all(e.get("duration") == SHRINE_SECONDS and (e.get("magnitude") or 0) > 0 for e in eff):
                    bad.append(f"{sp.get('edid')}: Resist Disease must last {SHRINE_SECONDS} s at a fixed magnitude above 0 "
                               f"(has {[(e.get('magnitude'), e.get('duration')) for e in eff]})")
            msg = msgs.get(props.get("BlessingMessage") or "")
            if msg is None or not (msg.get("text") or "").strip():
                bad.append(f"BlessingMessage {props.get('BlessingMessage')} is not a message of ours with text")
            if not props.get("AltarRemoveMsg"):
                bad.append("AltarRemoveMsg is not set")
        if not bad:
            return []
        tried.append(f"{m['rows'].get(r['fk'], {}).get('id', r['fk'])}: " + "; ".join(bad))
    return ["the shrine lacks " + " | ".join(tried)]


BOAT_SCRIPT, BOAT_GOLD = "TIF_ARG_BoatTravel", "Skyrim.esm:00000F"
BOAT_PEX = B.ROOT / "out" / "gpu" / "papyrus" / "TIF_ARG_BoatTravel.pex"
WARNINGS: list[str] = []  # what a check notes without failing; main prints them


def travel_problems(ctx: dict, m: dict, facts: dict, npcs: list[dict], mode: str) -> list[str]:
    """What a place's stop of one mode lacks to take the player on each of its routes (empty: nothing). A placed person
    of ours in that mode's travel faction of ours; for every route of the stop (travel_route) whose destination has an
    arrival point (its map marker in the world ESM), an INFO on that faction (subject in it, the player holding the
    fare in gold) running TIF_ARG_BoatTravel with Destination that marker, Fare the route's fare, Gold001 set and the
    fragment Fragment_0. A route whose destination has no arrival point yet is not offered: it waits on that place."""
    from tools.places.people import TRAVEL_TAG
    dump = ctx["dump"]
    markers = dump.get("world_markers") or {}
    by_edid = {v: k for k, v in markers.items()}
    routes = ctx.get("routes", B.travel_routes(ctx.get("place_id", ""))).get(mode, [])
    if not routes:
        return [f"the network gives this {mode} stop no route"]
    tag = f"_{TRAVEL_TAG[mode]}_"
    ops = [(n, [f for f in n["faction_keys"] if tag in (facts.get(f, {}).get("edid") or "") and f.startswith(B.PLUGIN + ":")]) for n in npcs]
    ops = [(n, fs) for n, fs in ops if fs]
    if not ops:
        return [f"no person of ours in a {TRAVEL_TAG[mode].lower()} faction of ours"]
    infos = [i for t in dump.get("topics") or [] for i in t.get("infos") or []]
    tried = []
    for n, fs in ops:
        bad = []
        for r in routes:
            dest = r["to_place_id"]
            want = "ANW_MapMarker_" + dest.replace("-", "_")
            if want not in by_edid:
                WARNINGS.append(f"travel: {mode} to {dest} waits on that place (no {want} in the world ESM)")
                continue
            mine_ = [i for i in infos if any(c.get("fn") == "GetInFaction" and c.get("faction") in fs and c.get("run_on") == "Subject"
                                             and c.get("op") == "EqualTo" and c.get("value") == 1 for c in i.get("conditions") or [])
                     and any(sc["name"] == BOAT_SCRIPT for sc in i.get("scripts") or [])]
            hit = [i for i in mine_ if next((p["value"] for sc in i["scripts"] for p in sc["props"] if p["name"] == "Destination"), None) == by_edid[want]]
            if not hit:
                bad.append(f"{dest}: no INFO of this operator running {BOAT_SCRIPT} to {want}"
                           + ("" if mine_ else f" (no {BOAT_SCRIPT} line at all)"))
                continue
            i = hit[0]
            props = {p["name"]: p["value"] for sc in i["scripts"] for p in sc["props"]}
            fare = props.get("Fare")
            if fare != r["fare"]:
                bad.append(f"{dest}: Fare {fare!r} is not the route's {r['fare']}")
                continue
            if props.get("Gold001") != BOAT_GOLD:
                bad.append(f"{dest}: Gold001 is {props.get('Gold001')!r} (want {BOAT_GOLD})")
            if not any(c.get("fn") == "GetGold" and c.get("run_on") == "Target" and c.get("op") == "GreaterThanOrEqualTo" and c.get("value") == fare
                       or c.get("fn") == "GetItemCount" and c.get("item") == BOAT_GOLD and c.get("op") == "GreaterThanOrEqualTo" and c.get("value") == fare
                       for c in i.get("conditions") or []):
                bad.append(f"{dest}: no condition that the player holds {fare} gold")
            fr = i.get("fragment") or {}
            if fr.get("file") != BOAT_SCRIPT or fr.get("on_end") != "Fragment_0":
                bad.append(f"{dest}: fragment {fr} is not {BOAT_SCRIPT} OnEnd Fragment_0")
        if not bad:
            if not BOAT_PEX.exists():
                WARNINGS.append(f"{BOAT_PEX} is not compiled: the travel lines do nothing in game until it is")
            return []
        tried.append("; ".join(bad))
    return tried[:1]


def service_rows(ctx) -> list[str]:
    """Each placed person's services against the record's promises (draft/people.service_problems): the person
    file is the drafter's copy of the promise and is read as the truth by the stock and the studio."""
    from tools.places.draft import people as draft_people
    folk = ctx.get("folk")
    if folk is None:
        pf = Path(ctx["place_dir"]) / "people.jsonl" if ctx.get("place_dir") else None
        folk = B.jsonl(pf) if pf and pf.exists() else []
    if not folk:
        return []
    routes = ctx.get("routes", B.travel_routes(ctx.get("place_id", "")))
    dests = {mode: [r["to_place_id"] for r in rs] for mode, rs in routes.items()}
    return draft_people.service_problems(folk, ctx["gives"], dests)


def check_services(ctx) -> list[str]:
    bad = service_rows(ctx)
    m = mine(ctx)
    facts = {f["fk"]: f for f in ctx["dump"]["factions"]}
    classes = {c["fk"]: c for c in ctx["dump"]["classes"]}
    placed_npcs = {a["base"] for a in m["actors"].values()}
    npcs = [n for n in m["npcs"].values() if n["fk"] in placed_npcs]
    for g in ctx["gives"]:
        k = g["give_kind_id"]
        if k in NOT_A_PLACE_SERVICE:
            continue
        ok = False
        if k in TRADE_JOB:
            ok = any(TRADE_JOB[k] in n["factions"] and any(facts.get(f, {}).get("vendor") and facts[f].get("chest") for f in n["faction_keys"]) for n in npcs)
        elif k == "trainer":
            ok = any("JobTrainerFaction" in n["factions"] and classes.get(n["class"], {}).get("teaches") for n in npcs)
        elif k == "inn-room":
            tried = [inn_room_problems(n, m, facts, ctx["dump"]) for n in npcs if "JobInnkeeperFaction" in n["factions"]]
            ok = any(not t for t in tried)
            if not ok:
                bad.append(f"promised {k} ({g.get('detail', '')}): " + ("no innkeeper (JobInnkeeperFaction)" if not tried else "the innkeeper lacks " + "; ".join(tried[0])))
                continue
        elif k in CRAFT_KEYWORD:
            ok = any(CRAFT_KEYWORD[k] in (r.get("keywords") or []) for r in m["refs"].values())
        elif k == "shrine-blessing":
            tried = shrine_problems(ctx, m)
            if tried:
                bad.append(f"promised {k} ({g.get('detail', '')}): " + tried[0])
                continue
            ok = True
        elif k in TRAVEL_STOP:
            mode = TRAVEL_STOP[k]
            own = "ANW_MapMarker_" + ctx.get("place_id", "").replace("-", "_")
            tried = travel_problems(ctx, m, facts, npcs, mode)
            if own not in (ctx["dump"].get("world_markers") or {}).values():
                tried = [f"no arrival point here ({own} is not in the world ESM): passages to this place land nowhere"] + tried
            if tried:
                bad.append(f"promised {k} ({g.get('detail', '')}): " + tried[0])
                continue
            ok = True
        if not ok:
            bad.append(f"promised {k} ({g.get('detail', '')}): nobody and nothing gives it")
    return bad


def is_nordic(model: str | None, edid: str | None) -> bool:
    return bool((model and NORDIC_MODEL.search(model)) or (edid and NORDIC_EDID.match(edid)))


def source_bases(ctx) -> set[str]:
    """The bases the source place itself uses (its bundle's bases.jsonl; `source_bases` in a test's context)."""
    if ctx.get("source_bases") is not None:
        return set(ctx["source_bases"])
    pj = Path(ctx.get("place_dir") or B.PLACES / ctx.get("place_id", "")) / "place.json"
    source_id = json.loads(pj.read_text()).get("source_id") if pj.exists() else None
    p = B.OUT / "bundles" / f"src.{source_id}" / "bases.jsonl"
    return {r["key"] for r in B.jsonl(p)} if source_id and p.exists() else set()


def check_nordic(ctx) -> list[str]:
    """Nothing Nordic among what we add from elsewhere (decision 0006). A piece the source place itself uses is
    accepted as it comes and is not judged. Any other ref of ours (a station, a replacement, a laid piece): the
    Nordic review's looked-at verdict on its base (newworld/places/nordic_review.jsonl) outranks the folder and
    editor-id rule."""
    from tools.places.draft.io import nordic_review
    review = ctx.get("nordic_review")
    review = nordic_review() if review is None else review
    own = source_bases(ctx)
    m = mine(ctx)
    bad = []
    for r in m["refs"].values():
        if r.get("base_type") not in ("STAT", "MSTT", "DOOR", "FURN", "CONT", "ACTI", "LIGH", "TREE", "FLOR", "MISC"):
            continue
        if r.get("base_type") == "LIGH" and not r.get("model"):
            continue  # a light with no model shows nothing: no look to judge
        if m["rows"].get(r["fk"], {}).get("base") in own:
            continue  # the source place's own piece
        v = review.get(m["rows"].get(r["fk"], {}).get("base"))
        if v["verdict"] == "nordic" if v else is_nordic(r.get("model"), r.get("base_edid")):
            bad.append(f"{m['rows'].get(r['fk'], {}).get('id', r['fk'])}: Nordic base {r.get('base_edid')} ({r.get('model')})")
    return bad


def copied_room_expected(I: dict, place_dir: Path, plan: dict, refs: list[dict] | None = None) -> tuple[dict[str, str], str] | None:
    """The source refs a copied room must be built with, by key -> bundle kind: the bundle's cell (the load order's
    winner of every ref, people aside; `refs` gives its rows instead), the kept room where the space copies one room
    (the Build recipe's room rule), less what the place's own rows remove and the loose things the stock takes out.
    None: no bundle to compare."""
    copy_of = I.get("copy_of")
    if not I.get("copy") or not copy_of or "/" not in copy_of:
        return None
    src_id, cell = copy_of.split("/", 1)
    if refs is None:
        rp = B.OUT / "bundles" / f"src.{src_id}" / "spaces" / cell / "refs.jsonl"
        if not rp.exists():
            return None
        refs = B.jsonl(rp)
    refs = [r for r in refs if r.get("kind") not in ("actor", "npc") and "pos" in r]
    want = {r["id"]: r.get("kind") for r in refs}
    if I.get("room"):
        tmp = B.OUT / "tmp" / f"rooms_{I['space']}"
        tmp.mkdir(parents=True, exist_ok=True)
        kept = B.room_partition(copy_of, refs, tmp)["rooms"].get(I["room"], {}).get("refs", set())
        want = {k: v for k, v in want.items() if k in kept}
    rows = B.jsonl(place_dir / "spaces" / I["space"] / "refs.jsonl")
    for r in rows:
        if r.get("removed") and r.get("src"):
            want.pop(r["src"], None)
    for t in (plan.get("stock") or {}).get("taken_out", []):
        if want.get(t.get("holder")) not in (None, "container"):
            want.pop(t["holder"], None)
    return want, copy_of


def check_rooms(ctx) -> list[str]:
    """Every copied room is built whole: its built refs and lights are the source cell's kept room as the bundle holds
    it (every plugin of the source's load order, the winner per ref), one line per room that is not, naming what is
    missing."""
    m, plan = mine(ctx), ctx["plan"]
    built: dict[str, dict[str, dict]] = {}
    for fk, r in m["refs"].items():
        row = m["rows"].get(fk) or {}
        if row.get("space") not in (None, "exterior") and row.get("src"):
            built.setdefault(row["space"], {})[row["src"]] = r
    bad = []
    for I in plan.get("interiors", []):
        got = copied_room_expected(I, Path(ctx.get("place_dir") or B.PLACES / ctx.get("place_id", "")), plan,
                                   (ctx.get("room_refs") or {}).get(I.get("copy_of")))
        if got is None:
            continue
        want, copy_of = got
        have = built.get(I["space"], {})
        lights_want = sum(1 for k in want.values() if k == "light")
        lights_have = sum(1 for k, r in have.items() if k in want and r.get("base_type") == "LIGH")
        missing = sorted(set(want) - set(have))
        if missing or lights_have != lights_want:
            by_plugin = Counter(k.split(":", 1)[0] for k in missing)
            bad.append(f"room {I['space']} ({copy_of}): built {len(set(have) & set(want))} refs, {lights_have} lights of the "
                       f"source's kept room's {len(want)} refs, {lights_want} lights; missing {len(missing)} "
                       f"({dict(by_plugin)}; {missing[:5]})")
    return bad


def check_levelled(ctx) -> list[str]:
    return [f"levelled: {x}" for x in ctx["dump"]["levelled"]]


def check_stock(ctx) -> list[str]:
    from tools.places.stock import verify
    return verify.check_stock(ctx)


def check_promises(ctx) -> list[str]:
    from tools.places.stock import verify
    return verify.check_promises(ctx)


def island_report(ctx, person: str | None = None) -> list[str]:
    """The walkable islands of the built place (navmesh triangles joined by edges, edge links and paired doors): per
    island its triangles, doors, routine stops and people, the main one first; with `person`, each leg of that
    person's day and the islands its two stops are on. The studio and the lessons agent read the same lines."""
    comp = components(ctx["navs"], door_pairs(ctx))
    sizes = defaultdict(int)
    for c in comp.values():
        sizes[c] += 1
    m = mine(ctx)
    info = defaultdict(lambda: {"doors": set(), "stops": 0, "people": set(), "spaces": set()})
    for n in ctx["navs"].values():
        for ti, d in n.doors:
            if d in m["rows"]:
                info[comp[(n.fk, ti)]]["doors"].add(m["rows"][d]["id"].split(".")[-1][:6])
    allrefs = {r["fk"]: r for r in ctx["dump"]["refs"]}
    pk = {p["fk"]: p for p in ctx["dump"]["packages"]}
    legs = []
    for n in (ctx["plan"].get("people") or {}).get("npcs", []):
        got = m["npcs"].get(n["fk"])
        prev = None
        for k in (got or {}).get("packages", []):
            p = pk.get(k) or {}
            r = allrefs.get(p.get("location") or p.get("target"))
            if r is None:
                continue
            nd = nav_index(ctx).at(r["space"], r["pos"])
            c = comp.get(nd)
            info[c]["stops"] += 1
            info[c]["people"].add(n["id"])
            info[c]["spaces"].add(r["space"])
            if person and n["id"].endswith(person):
                legs.append(f"  {p.get('edid')}: {r['space']} {[round(v) for v in r['pos']]} on island "
                            f"{sizes.get(c, 0)} tris{' (not reachable from the stop before)' if prev is not None and prev != c else ''}")
            prev = c
    main = max(sizes, key=sizes.get) if sizes else None
    out = []
    for c in sorted(info, key=lambda c: (c != main, -sizes.get(c, 0))):
        i = info[c]
        out.append(f"island {sizes.get(c, 0)} tris{' (main)' if c == main else ''}: doors {sorted(i['doors'])}, "
                   f"{i['stops']} stops of {len(i['people'])} people, spaces {sorted(i['spaces'])}")
    return out + legs


JAIL_FLAGS = ("TrackCrime", "CanBeOwner")
GUARD_FACTIONS = ("Skyrim.esm:086EEE", "Skyrim.esm:02BE3B")  # IsGuardFaction, GuardDialogueFaction: the arrest lines' speakers
NOTES: list[str] = []  # what a passing check says plainly; main prints them


def check_jail(ctx) -> list[str]:
    """The crime faction's sentence by the place's law. A jail as vanilla's hold factions have it: JAIL and WAIT our
    exterior prison marker, STOL and PLCN our two evidence chests, each a ref of our plugin; the jail marker on its
    room's navmesh, the release point on the town's main network; the chests in the jail, empty, never respawning,
    owned by the faction. Native law's Owing: JAIL and WAIT the return spot's prison marker, whose teleport leads to
    the work spot's and back, both on the town's main network; the worker's mat beside the work spot; STOL the stolen
    goods chest, out of reach under the ground, empty, never respawning, owned by the faction; no PLCN; the Owing's
    line first in vanilla's "go to jail" topic, said only by this faction's guards, running vanilla's fragment that
    keeps the player's belongings. Either way every guard is in IsGuardFaction and GuardDialogueFaction. A place with
    no sentence fines only, which is said, not failed, unless its law is native (the Owing is then missing)."""
    from tools.places.people import GO_TO_JAIL, OWING_LINE, OWING_PROMPT
    ppl = ctx["plan"].get("people") or {}
    cf = ppl.get("crime_faction") or {}
    pid = ctx.get("place_id") or ctx["plan"].get("place_id")
    if not cf:
        return []
    jail = cf.get("jail")
    m = mine(ctx)
    if not jail:
        if cf.get("law") == "native":
            return [f"{pid}: native law with no Owing: run `draft jail {pid}`"]
        NOTES.append(f"jail: {pid} has no sentence ({cf.get('law_why') or cf.get('law') or 'no jail room'}): its crime faction fines only")
        # with no sentence, vanilla's "go to jail" line must never be offered: no guard speaks the arrest lines
        return [f"{n['id']}: a guard in GuardDialogueFaction, whose arrest lines offer a sentence {pid} does not have"
                for n in ppl.get("npcs", []) if n.get("role") == "guard" and m["npcs"].get(n["fk"]) is not None
                and GUARD_FACTIONS[1] in (m["npcs"][n["fk"]].get("faction_keys") or [])]
    owing = jail.get("owing")
    bad = []
    # the space where the sentence is served as the read-back names it: the jail's cell's editor id, or outside
    space = "exterior" if owing else (next((I.get("edid") for I in ctx["plan"].get("interiors") or []
                                             if I.get("space") == jail.get("space")), None) or jail.get("space"))
    fac = next((f for f in ctx["dump"].get("factions") or [] if f["fk"] == cf["fk"]), None)
    if fac is None:
        return [f"crime faction {cf['fk']} is not in the plugin"]
    fields = ("jail", "wait", "stolen") + (() if owing else ("inventory",))
    for k in fields:
        want = jail["exterior" if k in ("jail", "wait") else k]
        if fac.get(k) != want:
            bad.append(f"crime faction {cf['edid']}: {k} is {fac.get(k) or 'unset'}, not {want}")
        if want not in m["refs"]:
            bad.append(f"crime faction {cf['edid']}: its {k} {want} is not a ref of ours in the plugin")
    if owing and fac.get("inventory"):
        bad.append(f"crime faction {cf['edid']}: the Owing takes nothing of the player's, yet PLCN is {fac['inventory']}")
    for fl in JAIL_FLAGS:
        if fl not in str(fac.get("flag_names") or ""):
            bad.append(f"crime faction {cf['edid']}: no {fl} flag (vanilla's hold factions have it)")
    if not fac.get("arrest"):
        bad.append(f"crime faction {cf['edid']}: does not arrest")
    idx = nav_index(ctx)
    comp = components(ctx["navs"], door_pairs(ctx))
    sizes: dict = defaultdict(int)
    for c in comp.values():
        sizes[c] += 1
    main = max(sizes, key=sizes.get) if sizes else None
    ext, inner = m["refs"].get(jail["exterior"]), m["refs"].get(jail["marker"])
    where = "the work spot's marker" if owing else "jail marker"
    if inner is None or inner.get("space") != space:
        bad.append(f"{where} {jail['marker']}: not a ref of ours in {space}")
    elif owing:
        nd = idx.at("exterior", inner["pos"])
        if nd is None or comp.get(nd) != main:
            bad.append(f"the Owing's work spot at {[round(v) for v in inner['pos']]} is off the town's main network")
    elif idx.at(inner["space"], inner["pos"]) is None:
        bad.append(f"jail marker at {[round(v) for v in inner['pos']]} in {inner['space']} is off its room's navmesh")
    if ext is not None and ext.get("door") and inner is not None:
        land = inner.get("door", {}).get("to_pos") or ext["pos"]  # where a released prisoner stands
        nd = idx.at("exterior", land)
        if nd is None or comp.get(nd) != main:
            bad.append(f"release point at {[round(v) for v in land]} is off the town's main network")
        if (ext.get("door") or {}).get("to_ref") != jail["marker"] or (inner.get("door") or {}).get("to_ref") != jail["exterior"]:
            bad.append(f"exterior marker {jail['exterior']} and {where} {jail['marker']} do not lead to each other")
    elif ext is not None:
        bad.append(f"exterior jail marker {jail['exterior']}: no teleport to the {where}")
    if owing and inner is not None:
        bed = m["refs"].get(jail.get("bed") or "")
        if bed is None:
            bad.append(f"the Owing's mat {jail.get('bed')}: not a ref of ours in the plugin")
        elif math.dist(bed["pos"], inner["pos"]) > 256:
            bad.append(f"the Owing's mat stands {math.dist(bed['pos'], inner['pos']):.0f} units from the work spot")
    for k in ("stolen",) + (() if owing else ("inventory",)):
        c = m["refs"].get(jail[k])
        if c is None:
            continue
        if not owing and c.get("space") != space:
            bad.append(f"evidence chest {k}: in {c.get('space')}, not the jail {space}")
        if owing and inner is not None and not c["pos"][2] < inner["pos"][2] - 1024:
            bad.append(f"the Owing's stolen goods chest at {[round(v) for v in c['pos']]} is within reach")
        if c.get("contents"):
            bad.append(f"evidence chest {k}: holds {len(c['contents'])} things (it starts empty)")
        if c.get("respawns"):
            bad.append(f"evidence chest {k}: respawns")
        if c.get("owner") != cf["fk"]:
            bad.append(f"evidence chest {k}: owned by {c.get('owner') or 'nobody'}, not the crime faction {cf['fk']}")
    if owing:
        topic = next((t for t in ctx["dump"].get("topics") or [] if t["fk"] == GO_TO_JAIL), None)
        info = next((i for i in (topic or {}).get("infos") or [] if i["fk"] == owing.get("info")), None)
        if info is None:
            bad.append(f"the Owing's line {owing.get('info')} is not in vanilla's go-to-jail topic {GO_TO_JAIL}")
        else:
            if info.get("prompt") != OWING_PROMPT:
                bad.append(f"the Owing's line reads {info.get('prompt')!r}, not {OWING_PROMPT!r}")
            if info.get("previous"):
                bad.append(f"the Owing's line follows {info['previous']}: it must come first, before vanilla's unconditioned line")
            if not any(c.get("fn") == "GetInFaction" and c.get("faction") == cf["fk"] and c.get("value") == 1 for c in info.get("conditions") or []):
                bad.append(f"the Owing's line is not limited to the guards of {cf['edid']}")
            want = "TIF__" + OWING_LINE.split(":")[1].rjust(8, "0")
            if ((info.get("fragment") or {}).get("file") or "").upper() != want.upper():
                bad.append(f"the Owing's line runs {(info.get('fragment') or {}).get('file')}, not vanilla's {want} (the sentence that keeps the player's belongings)")
    for n in ppl.get("npcs", []):
        got = m["npcs"].get(n["fk"])
        if n.get("role") == "guard" and got is not None:
            gone = [f for f in GUARD_FACTIONS if f not in (got.get("faction_keys") or [])]
            if gone:
                bad.append(f"{n['id']}: a guard not in {', '.join(gone)} (vanilla's arrest lines need both)")
    return bad


def _prim_same(a: dict | None, b: dict | None) -> bool:
    if not a or not b or a.get("type") != b.get("type") or list(a.get("color") or []) != list(b.get("color") or []):
        return False
    return all(abs(float(x) - float(y)) < 0.01 for x, y in zip(a.get("bounds") or [], b.get("bounds") or []))


def primitive_inputs(ctx) -> tuple[dict, list[dict], dict] | None:
    """(the source's refs by space id, the ledger, the place files' removed sources by space) for check_primitives:
    a fixture's `primitive_inputs`, else the source bundle and the place files."""
    if "primitive_inputs" in ctx:
        return ctx["primitive_inputs"]
    pdir = ctx.get("place_dir")
    if not pdir or not (pdir / "place.json").exists():
        return None
    place = json.loads((pdir / "place.json").read_text())
    bdir = B.OUT / "bundles" / f"src.{place.get('source_id')}" / "spaces"
    if not bdir.exists():
        return None

    def src_refs(d: Path):
        if (d / "refs.jsonl").exists():
            return B.jsonl(d / "refs.jsonl")
        if (d / "refs.jsonl.gz").exists():
            return [json.loads(ln) for ln in gzip.open(d / "refs.jsonl.gz", "rt") if ln.strip()]
        return []
    src = {d.name: [r for r in src_refs(d) if r.get("primitive")] for d in bdir.iterdir() if d.is_dir()}
    ledger = B.jsonl(pdir / "ledger.jsonl") if (pdir / "ledger.jsonl").exists() else []
    removed = {sp.name: {x["src"] for x in B.jsonl(sp / "refs.jsonl") if x.get("removed") and x.get("src")}
               for sp in (pdir / "spaces").iterdir() if (sp / "refs.jsonl").exists()} if (pdir / "spaces").exists() else {}
    return src, ledger, removed


def check_primitives(ctx) -> list[str]:
    """Every copied ref whose source has a primitive is built with it, identical (type, half extents, colour), or is in
    the ledger as dropped with its reason (`draft primitives`). A source ref outside a copy's kept room is not copied."""
    got = primitive_inputs(ctx)
    if got is None:
        return []
    src, ledger, removed = got
    led = {(lr.get("copy") or lr["space"], lr["src"]): lr for lr in ledger}
    m = mine(ctx)
    rows = ctx["plan"]["refs"]
    by_id = {r["id"]: r for r in rows}
    by_src = {(r["space"], r.get("src")): r for r in rows if r.get("src")}
    bad, n = [], Counter()

    def built(row, want, what):
        b = m["refs"].get(row["fk"]) if row else None
        if b is None:
            bad.append(f"{what}: has a primitive in the source and is neither built nor in the ledger as dropped")
        elif not _prim_same(b.get("primitive"), want):
            bad.append(f"{what}: built with primitive {b.get('primitive')}, the source's is {want}")
        else:
            n["written"] += 1

    for r in src.get("exterior", []):
        lr = led.get(("exterior", r["id"]))
        if lr and lr.get("status") == "dropped":
            n["dropped"] += 1
            if not lr.get("why"):
                bad.append(f"{r['id']}: dropped with no reason in the ledger")
            continue
        as_ = (lr or {}).get("as")
        built(by_id.get(as_[0] if isinstance(as_, list) else as_) or by_src.get(("exterior", r["id"])), r["primitive"], r["id"])
    for I in ctx["plan"].get("interiors") or []:
        if not I.get("copy_of"):
            continue
        sid = I["space"]
        for r in src.get(I["copy_of"].split("/", 1)[1], []):
            row = by_src.get((sid, r["id"]))
            if row is not None:
                built(row, r["primitive"], f"{sid}/{r['id']}")
            elif r["id"] in removed.get(sid, set()):
                lr = led.get((sid, r["id"]))
                n["dropped"] += 1
                if not lr or lr.get("status") != "dropped" or not lr.get("why"):
                    bad.append(f"{sid}/{r['id']}: removed with no ledger row saying why")
            else:
                n["not_in_room"] += 1
    ctx["primitives"] = dict(n)
    return bad


CHECKS = {"plugin": check_plugin, "seat": check_seat, "overlap": check_overlap, "doors": check_doors, "people": check_people,
          "navmesh": check_navmesh, "streets": check_streets, "land": check_land, "clear": check_clear, "services": check_services,
          "nordic": check_nordic, "rooms": check_rooms, "levelled": check_levelled, "jail": check_jail,
          "primitives": check_primitives, "stock": check_stock, "promises": check_promises}


def run(ctx: dict) -> dict[str, list[str]]:
    NOTES.clear()
    return {name: fn(ctx) for name, fn in CHECKS.items()}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="python -m tools.places check")
    ap.add_argument("place_id")
    ap.add_argument("--out", default=str(B.OUT))
    ap.add_argument("--places-dir", default=str(B.PLACES))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--reach", nargs="?", const="", default=None, metavar="PERSON",
                    help="only the island report (and one person's legs): what is cut off from what")
    a = ap.parse_args(argv)
    t0 = time.time()
    ctx = load(a.place_id, Path(a.out))
    if a.reach is not None:
        print("\n".join(island_report(ctx, a.reach or None)))
        return 0
    ctx["place_dir"] = Path(a.places_dir) / a.place_id
    res = run(ctx)
    counts = ctx["dump"]["counts"]
    esp_sha = hashlib.sha256((Path(a.out) / "plugin" / B.PLUGIN).read_bytes()).hexdigest()  # which build was checked
    report = {"place_id": a.place_id, "check_s": round(time.time() - t0, 1), "masters": ctx["dump"]["masters"], "counts": counts,
              "esp_sha256": esp_sha,
              "results": {k: {"ok": not v, "failures": v[:50], "n": len(v)} for k, v in res.items()},
              "notes": list(NOTES), "primitives": ctx.get("primitives")}
    shard = Path(a.out) / "shards" / a.place_id
    (shard / "check.json").write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    # the full lists, never cut, one file per check, so nothing is hidden
    full = shard / "check_failures"
    full.mkdir(parents=True, exist_ok=True)
    for k, v in res.items():
        (full / f"{k}.txt").write_text("".join(f"{f}\n" for f in v))
    if a.json:
        print(json.dumps(report, sort_keys=True))
    else:
        for w in WARNINGS:
            print(f"warn {w}")
        for w in NOTES:
            print(f"note {w}")
        for k, v in res.items():
            print(f"{'ok  ' if not v else 'FAIL'} {k}" + ("" if not v else f" ({len(v)})"))
            for f in v[:20]:
                print(f"     {f}")
        print(f"check {a.place_id}: {sum(1 for v in res.values() if not v)}/{len(res)} green in {report['check_s']} s")
    return 0 if not any(res.values()) else 1
