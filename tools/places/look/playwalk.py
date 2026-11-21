"""`look <place> playwalk [<from> <to>] [--plan] [--changed] [--stride u] [--rooms]` and `look <place> in <room>
playwalk`: walk a place as a player would, along routes planned on the place's BUILT walkable mesh (the shortest walk
over its triangles, so up the stairs and over the bridges), with a station every few steps and at every stair foot
and head, bridge end and middle, doorway, sharp turn and deck edge; at each station the player's looks (ahead, down,
up, left, right, back, and the two forward diagonals where the way is tricky) from a person's eye on the mesh.

Every look is judged by its id buffer. A capture fault (the camera in a piece, a lens filled by one near thing, no
ground drawn) is retried by nudging the camera along the walk and sideways on the mesh; what the same evidence says
of the PLACE (the walk passes through a solid piece, a door opens onto a wall, no floor under a bridge's middle, a
ceiling lower than a person, the void seen through a room's shell) is reported as a fault of the place.

Out: LOOK_OUT/<place>/playwalk/<route>/ (strips of at most 8 stations, a forward-only filmstrip, a map, tiles/ with
every look full size, table.txt and table.json). Pure parts (planning, stations, the classifier, dedup, the room
planner) are tested in tools/tests/test_places_playwalk.py; run() drives the page."""
from __future__ import annotations

import hashlib
import heapq
import json
import math
import re
import time
from pathlib import Path

import numpy as np

from tools.places.look import geom

STRIDE = 256.0        # a station every this many units walked on one named route
PLACE_STRIDE = 768.0  # and on a whole place's walk (events still get theirs: about 15 minutes for a village)
EVENT_MERGE = 64.0    # a stride station this near an event station gives way to it
TURN_DEG = 45.0       # a turn sharper than this is a station
DROP_NEAR = 150.0     # the walk this near a deck edge with a drop beside it is a station
DROP = 96.0           # an open edge of the mesh over this much higher than what lies beyond it is a drop
STAIR_SLOPE = 0.3     # a rise over this share of the run (over 64 units) is a stair or a ramp
STAIR_MIN = 48.0      # and it climbs at least this much
DECK_OVER = 48.0      # the walk this far over the ground is on a deck, a walkway or a bridge
BRIDGE_OVER = 150.0   # and this far over (or over water) a bridge
FOV_H = 80.0          # the game's first-person view: 80 degrees across at 4:3
NEAR_LENS = 100.0     # a thing nearer than this...
LENS = 0.6            # ...covering more than this share of the frame fills the lens
NUDGES_ALONG = (16.0, -16.0, 32.0, -32.0, 64.0, -64.0)
NUDGES_SIDE = (24.0, -24.0, 48.0, -48.0)
REACH = 300.0         # a target this far off the mesh across the plan is walked to from its nearest triangle
REACH_Z = 220.0
OPEN_UNDER = re.compile(r"platform|deck|walkway|dock|pier|bridge|boardwalk|stilt|gangway", re.I)
EAVES_OVER_EYE = 150.0   # a building filling the lens whose top is under this over the eye: its roof is at head height
DOOR_OVER = 150.0   # a door this far over the end of the walk to it: its arrival lies under it
TOOL = 6             # the judging rules version: a route shot under older rules is shot again
KEY_XY, KEY_Z = 96.0, 64.0   # two stations in one such cell, facing within one eighth of a turn, are one view

LOOKS = (("ahead", 0, 0), ("down", 0, -20), ("up", 0, 20), ("left", 90, 0), ("right", -90, 0), ("back", 180, 0))
DIAGONALS = (("ahead-left", 45, 0), ("ahead-right", -45, 0))
TRICKY = ("stair", "ramp", "bridge", "walkway", "doorway", "turn", "way in")
FURNITURE_RE = re.compile(r"bed|chair|bench|stool|table|throne|workbench|chest|barrel|crate|sack|wardrobe|dresser|"
                          r"cupboard|endtable|counter|desk|crafting|anvil|forge|grindstone|smelter|tanning|alchemy|"
                          r"enchant|cookingpot|spit|sitmarker|sleep", re.I)
STALL_RE = re.compile(r"stall|market|merchant", re.I)
HIST_RE = re.compile(r"histtree|^hist\d", re.I)    # the Hist itself (its roots and glands are its dressing)


def fov_v(w: int, h: int) -> float:
    """The vertical field of a view FOV_H across at the tile's own width and height."""
    return round(math.degrees(2 * math.atan(math.tan(math.radians(FOV_H / 2)) * h / w)), 2)


# ---------- the shortest walk over the mesh ----------
def snap(M, pt, reach: float = REACH, reach_z: float = REACH_Z) -> tuple[int, list, float]:
    """(triangle, the point on it, how far off the mesh the point was): the triangle under the point within the
    mesh's own tolerance, else the nearest triangle centre within reach (across) and reach_z (up or down); (-1, pt, d)
    when none is."""
    z = pt[2] if len(pt) > 2 else None
    t, h = M.tri_at(pt[0], pt[1], z)
    if t >= 0:
        return t, [float(pt[0]), float(pt[1]), float(h)], 0.0
    d = np.hypot(M.C[:, 0] - pt[0], M.C[:, 1] - pt[1])
    if z is not None:
        d = np.where(np.abs(M.C[:, 2] - z) <= reach_z, d, np.inf)
    i = int(np.argmin(d)) if len(d) else -1
    if i < 0 or not np.isfinite(d[i]):
        return -1, list(pt), float("inf")
    off = float(d[i])
    if off > reach:
        return -1, list(pt), off
    return i, M.C[i].tolist(), off


def astar(M, a: int, b: int) -> list[int] | None:
    """The triangles of the shortest walk from triangle a to b (preferred-path triangles cheaper, water dearer)."""
    if a == b:
        return [a]
    C = M.C
    w = np.where(M.kind == 1, 0.6, np.where(M.kind == 2, 3.0, 1.0))
    g = {a: 0.0}
    prev = {}
    goal = C[b]
    q = [(0.0, a)]
    while q:
        f, u = heapq.heappop(q)
        if u == b:
            break
        gu = g[u]
        for v in M.nb[u]:
            v = int(v)
            if v < 0:
                continue
            nd = gu + float(np.linalg.norm(C[u] - C[v])) * float(w[v])
            if nd < g.get(v, math.inf):
                g[v], prev[v] = nd, u
                heapq.heappush(q, (nd + 0.6 * float(np.linalg.norm(C[v] - goal)), v))
    if b not in g:
        return None
    out = [b]
    while out[-1] != a:
        out.append(prev[out[-1]])
    return out[::-1]


def _shared(M, t, u):
    """The edge of t across which u lies (the mesh's own neighbour slot; vertices may be distinct copies)."""
    k = [i for i in range(3) if M.nb[t, i] == u]
    if k:
        return M.V[M.T[t, k[0]]], M.V[M.T[t, (k[0] + 1) % 3]]
    s = [int(v) for v in M.T[t] if v in set(M.T[u].tolist())]
    if len(s) >= 2:
        return M.V[s[0]], M.V[s[1]]
    return M.C[t], M.C[u]


def _in_tri(M, t, x, y):
    a, b, c = M.V[M.T[t]]
    from tools.places.look.mesh import _height_in
    return _height_in(a, b, c, x, y)


def _z_on(M, tris, x, y, zprev=None):
    """The height at (x, y) of the corridor's triangle under it (the one nearest zprev when several are)."""
    if not len(tris):
        return None
    W = M.V[M.T[np.asarray(tris, int)]]
    a, b, c = W[:, 0], W[:, 1], W[:, 2]
    d = (b[:, 1] - c[:, 1]) * (a[:, 0] - c[:, 0]) + (c[:, 0] - b[:, 0]) * (a[:, 1] - c[:, 1])
    ok = np.abs(d) > 1e-9
    d = np.where(ok, d, 1.0)
    l1 = ((b[:, 1] - c[:, 1]) * (x - c[:, 0]) + (c[:, 0] - b[:, 0]) * (y - c[:, 1])) / d
    l2 = ((c[:, 1] - a[:, 1]) * (x - c[:, 0]) + (a[:, 0] - c[:, 0]) * (y - c[:, 1])) / d
    l3 = 1 - l1 - l2
    inn = ok & (l1 >= -1e-6) & (l2 >= -1e-6) & (l3 >= -1e-6)
    if not inn.any():
        return None
    h = (l1 * a[:, 2] + l2 * b[:, 2] + l3 * c[:, 2])[inn]
    if zprev is None:
        return float(h[0])
    return float(h[np.argmin(np.abs(h - zprev))])


def corridor_line(M, tris: list[int], a, b) -> list[list[float]]:
    """The walk through a corridor of triangles: a, the middles of the edges crossed, b; then straightened where a
    straight line stays inside the corridor, heights from the corridor's own triangles (a stair keeps its steps)."""
    pts = [list(map(float, a[:3]))]
    for t, u in zip(tris, tris[1:]):
        p, q = _shared(M, t, u)
        pts.append(((p + q) / 2).tolist())
    pts.append(list(map(float, b[:3])))
    out = [pts[0]]
    i = 0
    while i < len(pts) - 1:
        j = len(pts) - 1
        while j > i + 1:
            lo, hi = max(0, i - 1), min(len(tris), j + 1)
            sub = tris[lo:hi]
            p, q = np.asarray(pts[i][:2]), np.asarray(pts[j][:2])
            n = max(2, int(np.linalg.norm(q - p) // 24))
            ok, zp = True, pts[i][2]
            for k in range(1, n):
                x, y = p + (q - p) * k / n
                z = _z_on(M, sub, x, y, zp)
                if z is None or abs(z - zp) > 40:
                    ok = False
                    break
                zp = z
            if ok:
                break
            j -= 1
        out.append(pts[j])
        i = j
    return out


def resample(M, tris, way, step: float = 16.0) -> np.ndarray:
    """The walk every `step` units: rows of (x, y, z, s walked)."""
    rows, s = [], 0.0
    zp = way[0][2]
    for p, q in zip(way, way[1:]):
        p, q = np.asarray(p, float), np.asarray(q, float)
        L = float(np.linalg.norm(q[:2] - p[:2]))
        n = max(1, int(L // step))
        for k in range(n):
            x, y = p[:2] + (q[:2] - p[:2]) * k / n
            z = _z_on(M, tris, x, y, zp) if tris else None
            z = float(p[2] + (q[2] - p[2]) * k / n) if z is None else z
            rows.append((x, y, z, s + L * k / n))
            zp = z
        s += L
    rows.append((*way[-1][:3], s))
    return np.asarray(rows, float)


def plan_route(M, name: str, a: dict, b: dict) -> dict:
    """One route from a to b ({name, pos, kind}) over the mesh: its corridor, its line, its length; when b cannot be
    walked to from a, the walk goes to where the mesh breaks and the route says where and how it breaks."""
    r = {"name": name, "from": a["name"], "to": b["name"], "from_kind": a.get("kind"), "to_kind": b.get("kind")}
    ta, pa, offa = snap(M, a["pos"])
    tb, pb, offb = snap(M, b["pos"])
    if ta < 0:
        return r | {"broken": {"why": f"{a['name']} is off the walkable mesh by {offa:.0f} u"}, "way": [], "tris": []}
    end, endp = tb, pb
    if tb < 0:
        r["broken"] = {"why": f"{b['name']} is off the walkable mesh by {offb:.0f} u: walked to the nearest spot"}
        d = np.hypot(M.C[:, 0] - b["pos"][0], M.C[:, 1] - b["pos"][1])
        d = np.where(M.lab == M.lab[ta], d, np.inf)
        end = int(np.argmin(d))
        endp = M.C[end].tolist()
    elif M.lab[ta] != M.lab[tb]:
        g = M.gap(int(M.lab[ta]), int(M.lab[tb]), near=b["pos"][:2])
        g = g or {}
        at = g.get("from") or b["pos"]
        d = np.hypot(M.C[:, 0] - at[0], M.C[:, 1] - at[1]) + 0.5 * np.abs(M.C[:, 2] - (at[2] if len(at) > 2 else 0))
        d = np.where(M.lab == M.lab[ta], d, np.inf)
        end = int(np.argmin(d))
        endp = M.C[end].tolist()
        r["broken"] = {"why": f"{b['name']} cannot be walked to from {a['name']}: the walk breaks at "
                              f"{[round(v) for v in g.get('at', at)]} ({g.get('kind', 'no way')}, {g.get('across', '?')} u across, "
                              f"{g.get('step', '?')} u up or down)", "gap": g}
    tris = astar(M, ta, end) or [ta]
    way = corridor_line(M, tris, pa, endp)
    P = resample(M, tris, way)
    return r | {"tris": tris, "way": [[round(v, 1) for v in q] for q in way], "length": round(float(P[-1, 3]), 1),
                "walk": P}


# ---------- stations ----------
def _runs(mask: np.ndarray) -> list[tuple[int, int]]:
    out, i, n = [], 0, len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j + 1 < n and mask[j + 1]:
                j += 1
            out.append((i, j))
            i = j + 1
        else:
            i += 1
    return out


def events(P: np.ndarray, ground, drops: np.ndarray | None = None) -> list[tuple[float, str]]:
    """What the walk meets that is a station whatever the stride: stair (or ramp) feet and heads, both ends and the
    middle of each bridge or walkway, each turn sharper than TURN_DEG, the first point of each stretch within
    DROP_NEAR of a drop (drops: (n, 2, 3) edge segments). (s walked, what)."""
    out: list[tuple[float, str]] = []
    n = len(P)
    if n < 2:
        return out
    k = 4   # 64 units at the 16-unit step
    climb = np.zeros(n, bool)
    for i in range(n - 1):
        j = min(n - 1, i + k)
        ds = P[j, 3] - P[i, 3]
        if ds > 1 and abs(P[j, 2] - P[i, 2]) / ds > STAIR_SLOPE:
            climb[i:j + 1] = True
    for i, j in _runs(climb):
        rise = P[j, 2] - P[i, 2]
        if abs(rise) < STAIR_MIN:
            continue
        what = "stair" if abs(rise) / max(P[j, 3] - P[i, 3], 1) > 0.5 else "ramp"
        lo, hi = (i, j) if rise > 0 else (j, i)
        out += [(float(P[lo, 3]), f"{what} foot"), (float(P[hi, 3]), f"{what} head")]
    over = np.zeros(n, bool)
    wet = np.zeros(n, bool)
    for i in range(n):
        g = ground.height(P[i, 0], P[i, 1])
        w = ground.water(P[i, 0], P[i, 1]) if hasattr(ground, "water") else None
        over[i] = g is None or P[i, 2] - g > DECK_OVER
        wet[i] = w is not None and g is not None and w > g + 8 and P[i, 2] > w
        if g is not None and P[i, 2] - g > BRIDGE_OVER:
            wet[i] = True
    for i, j in _runs(over):
        if P[j, 3] - P[i, 3] < 96:
            continue
        m = (i + j) // 2
        what = "bridge" if wet[i:j + 1].mean() > 0.3 else "walkway"
        out += [(float(P[i, 3]), f"{what} start"), (float(P[m, 3]), f"{what} middle"), (float(P[j, 3]), f"{what} end")]
    hd = np.arctan2(np.diff(P[:, 1]), np.diff(P[:, 0]))
    step = int(round(48 / max(P[1, 3] - P[0, 3], 1)))
    for i in range(step, n - 1 - step):
        a, b = hd[i - step], hd[min(len(hd) - 1, i + step)]
        d = abs((math.degrees(b - a) + 180) % 360 - 180)
        if d > TURN_DEG and (not out or out[-1][1] != "turn" or P[i, 3] - out[-1][0] > 96):
            out.append((float(P[i, 3]), "turn"))
    if drops is not None and len(drops):
        near = np.array([_seg_dist(P[i, :3], drops) <= DROP_NEAR for i in range(n)])
        for i, _j in _runs(near):
            out.append((float(P[i, 3]), "deck edge"))
    return sorted(out)


def _seg_dist(p, segs) -> float:
    a, b = segs[:, 0, :], segs[:, 1, :]
    ab = b - a
    t = np.clip(((p - a) * ab).sum(1) / np.maximum((ab * ab).sum(1), 1e-9), 0, 1)
    q = a + ab * t[:, None]
    d = np.hypot(q[:, 0] - p[0], q[:, 1] - p[1])
    d = np.where(np.abs(q[:, 2] - p[2]) < 64, d, np.inf)
    return float(d.min())


def drop_edges(M, ground, box=None) -> np.ndarray:
    """The mesh's open edges with a drop beyond them (DROP over what lies outside), within box (x1, y1, x2, y2)."""
    segs = []
    for i in range(len(M.T)):
        if box is not None:
            c = M.C[i]
            if not (box[0] <= c[0] <= box[2] and box[1] <= c[1] <= box[3]):
                continue
        for k in range(3):
            if M.nb[i, k] >= 0:
                continue
            p, q = M.V[M.T[i, k]], M.V[M.T[i, (k + 1) % 3]]
            mid = (p + q) / 2
            out = mid[:2] - M.C[i, :2]
            out = out / max(float(np.linalg.norm(out)), 1e-9)
            x, y = mid[:2] + out * 40
            g = ground.height(x, y)
            if g is None or mid[2] - g > DROP:
                segs.append((p, q))
    return np.asarray(segs, float).reshape(-1, 2, 3)


def stations(P: np.ndarray, evs: list[tuple[float, str]], stride: float = STRIDE, start: str = "start",
             end: str = "end") -> list[dict]:
    """Stations along the walk: one every `stride`, each event its own station (a stride station near one gives way
    to it), the start and the end; each with where it stands, the heading of the walk there and what it is."""
    if not len(P):
        return []
    L = float(P[-1, 3])
    want: list[tuple[float, str]] = [(0.0, start)]
    s = stride
    while s < L - stride / 2:
        want.append((s, ""))
        s += stride
    want.append((L, end))
    for es, what in evs:
        near = [k for k, (ws, ww) in enumerate(want) if abs(ws - es) <= EVENT_MERGE]
        if near:
            k = near[0]
            ws, ww = want[k]
            want[k] = (ws if ww else es, ", ".join(x for x in (ww, what) if x and what not in ww))
        else:
            want.append((es, what))
    want.sort()
    out = []
    for k, (ws, ww) in enumerate(want):
        i = int(np.clip(np.searchsorted(P[:, 3], ws), 0, len(P) - 1))
        j0, j1 = max(0, i - 3), min(len(P) - 1, i + 3)
        if j1 == j0:
            d = np.array([0.0, 1.0])
        else:
            d = P[j1, :2] - P[j0, :2]
            d = d / max(float(np.linalg.norm(d)), 1e-9)
        out.append({"n": k + 1, "s": round(float(P[i, 3])), "pos": [round(float(v), 1) for v in P[i, :3]],
                    "dir": [round(float(d[0]), 4), round(float(d[1]), 4)], "what": ww or "stride",
                    "heading": round((math.degrees(math.atan2(d[0], d[1])) + 360) % 360)})
    return out


def tricky(what: str) -> bool:
    return any(w in what for w in TRICKY)


def looks_of(st: dict) -> list[tuple[str, float, float]]:
    if st.get("looks"):
        return [tuple(x) for x in st["looks"]]
    return list(LOOKS) + (list(DIAGONALS) if tricky(st["what"]) else [])


def cam_of(st: dict, look: tuple, w: int, h: int, pos=None, inside: bool = False) -> dict:
    """The camera of one look: a person's eye over where the station stands, heading along the walk turned by the
    look's yaw (left positive) and tipped by its pitch."""
    name, yaw, pitch = look
    p = pos or st["pos"]
    eye = [p[0], p[1], p[2] + geom.EYE]
    a = math.atan2(st["dir"][1], st["dir"][0]) + math.radians(yaw)
    pr = math.radians(pitch)
    t = [eye[0] + 1000 * math.cos(a) * math.cos(pr), eye[1] + 1000 * math.sin(a) * math.cos(pr), eye[2] + 1000 * math.sin(pr)]
    return {"pos": [round(v, 2) for v in eye], "target": [round(v, 2) for v in t], "up": [0, 0, 1], "fov": fov_v(w, h),
            "w": w, "h": h, "near": 4, "far": 20000 if inside else 9000}


def nudges(M, P: np.ndarray, st: dict) -> list[list[float]]:
    """Where to stand instead when a look fails: along the walk back and forth up to 64 units, then sideways on the
    mesh; each on a triangle of the mesh."""
    out = []
    for ds in NUDGES_ALONG:
        s = st["s"] + ds
        if 0 <= s <= P[-1, 3]:
            i = int(np.clip(np.searchsorted(P[:, 3], s), 0, len(P) - 1))
            out.append([float(v) for v in P[i, :3]])
    nx, ny = -st["dir"][1], st["dir"][0]
    for dd in NUDGES_SIDE:
        x, y = st["pos"][0] + nx * dd, st["pos"][1] + ny * dd
        t, z = M.tri_at(x, y, st["pos"][2])
        if t >= 0:
            out.append([x, y, float(z)])
    return out


# ---------- dedup ----------
def key_of(st: dict) -> tuple:
    octant = int(((st["heading"] + 22.5) % 360) // 45)
    p = st["pos"]
    return (round(p[0] / KEY_XY), round(p[1] / KEY_XY), round(p[2] / KEY_Z), octant)


def dedup(routes: list[dict]) -> None:
    """Each station seen before (same cell, same heading) on an earlier route is marked `seen` (route, station) and
    not shot again; a route whose every station was seen is marked `same_as`."""
    seen: dict = {}
    for r in routes:
        for st in r.get("stations") or []:
            k = key_of(st)
            if k in seen and "doorway" not in st["what"] and not st["what"].startswith(("start", "end")):
                st["seen"] = seen[k]
            else:
                seen.setdefault(k, (r["name"], st["n"]))
        sts = r.get("stations") or []
        if sts and all("seen" in st or st["what"].startswith(("start", "end")) for st in sts) and len(sts) > 2:
            r["same_as"] = sorted({st["seen"][0] for st in sts if "seen" in st})


# ---------- what a look shows, and whose fault a failure is ----------
def boxed_in(ev: dict) -> bool:
    """Whether the piece the camera stands in (ev in_piece, its edid) fills over half of what the look shows."""
    name = ev.get("in_piece")
    if not name:
        return True
    top = (ev.get("fills") or [{}])[0]
    return top.get("edid") == name and top.get("share", 0) > 0.5


def in_piece(why: str | None) -> str | None:
    """The edid in a camera_inside reason ('... inside EDID (kind, id)', '... inside a tree's trunk (EDID)')."""
    if not why:
        return None
    m = re.search(r"inside a tree's \w+ \(([^)]+)\)", why) or re.search(r"inside (\S+) \(", why)
    return m.group(1) if m else None


def classify(look: str, what: str, ev: dict, inside: bool = False) -> dict:
    """A look's verdict from its evidence. ev: inside (why the camera stands in something, or None), all_inside (every
    nudge was in a piece too: the piece), near ({edid, kind, share, dist} of the thing filling most of the frame),
    land, water, sky (shares), floor_below (the share of pieces in the bottom middle of a down look), void (indoors,
    the share of the frame that is nothing). Returns {verdict good|failed, fault capture|place|None, why}.
    A piece's box is not its shape: the camera inside a box (the air under a deck on stilts, between a tree's roots)
    is a fault only when the picture agrees, that piece filling over half the frame."""
    if (ev.get("all_inside") or ev.get("inside")) and (not boxed_in(ev) or look == "up"):   # a deck overhead fills an up look
        ev = dict(ev, all_inside=None, inside=None)
    if ev.get("all_inside"):
        p = ev["all_inside"]
        if inside and ev.get("low_ceiling"):
            return {"verdict": "failed", "fault": "place", "why": f"the ceiling is lower than a person here ({p})"}
        if look in ("ahead", "down"):
            return {"verdict": "failed", "fault": "place", "why": f"the way passes through {p}: every spot near the station is inside it"}
        return {"verdict": "failed", "fault": "capture", "why": f"the eye stands against {p}, which fills the view {look}"}
    if ev.get("inside"):
        return {"verdict": "failed", "fault": "capture", "why": ev["inside"]}
    nr = ev.get("near")
    if nr and nr.get("share", 0) > LENS and nr.get("dist", 1e9) < NEAR_LENS:
        if "doorway" in what and look == "ahead" and nr.get("kind") in ("building", "static", "door"):
            return {"verdict": "failed", "fault": "place", "why": f"the door opens onto a wall: {nr.get('edid')} fills {nr['share']:.0%} of the view {nr['dist']:.0f} u ahead"}
        if nr.get("kind") == "building" and nr.get("top_over_eye") is not None and nr["top_over_eye"] < EAVES_OVER_EYE:
            return {"verdict": "failed", "fault": "place", "why": f"the top of {nr.get('edid')} is {nr['top_over_eye']} u over the eye, "
                                                                  f"{nr['dist']:.0f} u off the way: a house sunk to its eaves?"}
        return {"verdict": "failed", "fault": "capture", "why": f"{nr.get('edid')} ({nr.get('kind')}) fills {nr['share']:.0%} of the lens {nr['dist']:.0f} u away"}
    if look == "down" and "bridge middle" in what and ev.get("floor_below", 1.0) < 0.25:
        return {"verdict": "failed", "fault": "place", "why": "no floor under the bridge's middle: looking down shows the ground or water, not boards"}
    if inside and ev.get("void", 0) > 0.01:
        return {"verdict": "failed", "fault": "place", "why": f"the void shows through the room ({ev['void']:.0%} of the view is nothing)"}
    if not inside and look != "up" and ev.get("land", 0) + ev.get("water", 0) == 0 and ev.get("pieces", 1.0) < 0.98:
        return {"verdict": "failed", "fault": "capture", "why": "no ground is drawn"}
    return {"verdict": "good", "fault": None, "why": ""}


def evidence(ids: np.ndarray, table: list, id0: int, by_id: dict, eye) -> dict:
    """The classifier's evidence from one id buffer: the shares of land, water and nothing, the pieces' share, the
    three things filling most of the frame (with their distance from the eye) and the floor below a down look."""
    from tools.places.look import capture
    h, w = ids.shape
    n = float(w * h)
    vals, counts = np.unique(ids, return_counts=True)
    land = water = sky = pieces = 0
    by: dict = {}
    for v, c in zip(vals.tolist(), counts.tolist()):
        if v >= id0 and v - id0 < len(table):
            pieces += c
            by[table[v - id0][0]] = by.get(table[v - id0][0], 0) + c
        elif v == capture.LAND:
            land += c
        elif v == capture.WATER:
            water += c
        elif v == capture.NOTHING:
            sky += c
    fills = []
    for rid, c in sorted(by.items(), key=lambda kv: -kv[1])[:3]:
        p = by_id.get(rid) or {}
        dist = top = None
        if p.get("m"):
            lo, hi = geom.aabb(p)
            top = round(float(hi[2] - eye[2]))
            q = np.clip(np.asarray(eye, float), lo, hi)
            dist = float(np.linalg.norm(q - np.asarray(eye, float)))
            if dist == 0.0:   # the eye inside its box: how near its faces are is not known from the box
                dist = None
        fills.append({"piece": rid, "edid": p.get("edid"), "kind": p.get("kind"), "share": round(c / n, 3),
                      "dist": round(dist) if dist is not None else None, "top_over_eye": top})
    for nm, c in (("land", land), ("water", water), ("nothing", sky)):
        if c:
            fills.append({"edid": nm, "share": round(c / n, 3)})
    fills.sort(key=lambda f: -f["share"])
    bot = ids[int(h * 0.6):, int(w * 0.3):int(w * 0.7)]
    fb = float(((bot >= id0) & (bot - id0 < len(table))).mean()) if bot.size else 1.0
    near = next((f for f in fills if f.get("piece") and f.get("dist") is not None), None)
    return {"land": land / n, "water": water / n, "sky": sky / n, "void": sky / n, "pieces": pieces / n,
            "fills": fills[:3], "near": near, "floor_below": fb}


# ---------- what the routes go to ----------
def _xyz(p):
    return [p["m"][0][3], p["m"][1][3], p["m"][2][3]]


def points_of_interest(sc, files: dict) -> dict:
    """Where the player arrives (the landing, the ends of roads that leave the place, quest arrivals) and what the
    walk goes to (each door's arrival, stalls, stations, the Hist and its pool, quest spots): {arrivals, targets},
    each a list of {name, pos, kind}."""
    doors = []
    for p in sc.pieces:
        dd = p.get("door") or {}
        if p.get("kind") == "door" and dd.get("to_space"):
            doors.append({"name": f"door of {dd['to_space']}", "pos": list(dd.get("arrival") or _xyz(p)), "kind": "doorway",
                          "id": p["id"], "door_z": _xyz(p)[2]})
    arrivals = []
    paths = [q for q in files.get("paths") or [] if q.get("points")]
    ends = []
    for q in paths:
        for at, pt in (("from", q["points"][0]), ("to", q["points"][-1])):
            ends.append((q, at, pt))
    for q, at, pt in ends:
        if str(q.get(at)) == "landing":
            arrivals.append({"name": "landing", "pos": _on_ground(sc, pt), "kind": "arrival"})
    for q, at, pt in ends:
        if q.get("kind") != "street":
            continue
        joined = any(o is not q and min(math.dist(pt[:2], r[:2]) for r in o["points"]) < 200 for o in paths)
        near_door = any(math.dist(pt[:2], d["pos"][:2]) < 400 for d in doors)
        if not joined and not near_door:
            arrivals.append({"name": f"road end ({q['id'].rsplit('.', 1)[-1]} {at})", "pos": _on_ground(sc, pt), "kind": "arrival"})
    targets = list(doors)
    for p in sc.pieces:
        e = p.get("edid") or ""
        if STALL_RE.search(e) and p.get("kind") in ("static", "furniture", "activator", "building", "clutter", "container"):
            targets.append({"name": f"stall {e}", "pos": _xyz(p), "kind": "stall", "id": p["id"]})
        elif HIST_RE.search(e) and p.get("kind") in ("tree", "static", "activator"):
            targets.append({"name": f"the Hist {e}", "pos": _xyz(p), "kind": "hist", "id": p["id"]})
    for s in ((files.get("place") or {}).get("sap") or {}).get("added") or []:
        p = sc.by_id.get(s.get("id"))
        if p:
            targets.append({"name": "the Hist's sap pool", "pos": _xyz(p), "kind": "hist", "id": p["id"]})
    found = ((files.get("place") or {}).get("stations") or {}).get("found") or {}
    for k, ids in found.items():
        for i in ids:
            p = sc.by_id.get(i)
            if p and k != "shrine":
                targets.append({"name": f"{k} station", "pos": _xyz(p), "kind": "station", "id": i})
    for q in files.get("quests") or []:
        if q.get("space", "exterior") == "exterior" and q.get("pos"):
            name = f"quest spot {q.get('ref')}"
            (arrivals if re.search(r"landing|arriv", str(q.get("ref"))) else targets).append(
                {"name": name, "pos": list(q["pos"]), "kind": "quest"})
    seen, uniq = set(), []
    for t in targets:   # one walk to each spot: things within 96 units of one already listed are the same walk
        k = (round(t["pos"][0] / 96), round(t["pos"][1] / 96))
        if k not in seen:
            seen.add(k)
            uniq.append(t)
    return {"arrivals": arrivals, "targets": uniq, "doors": doors}


def _on_ground(sc, pt):
    g = sc.ground.height(pt[0], pt[1])
    return [float(pt[0]), float(pt[1]), float(g if g is not None else (pt[2] if len(pt) > 2 else 0.0))]


def centre_of(sc, poi: dict) -> dict:
    """The place's centre: the landing, else the middle of its stalls, else the middle of its doors."""
    land = [a for a in poi["arrivals"] if a["name"] == "landing"]
    if land:
        return land[0]
    st = [t["pos"] for t in poi["targets"] if t["kind"] == "stall"] or [d["pos"] for d in poi["doors"]]
    if not st:
        return {"name": "centre", "pos": [0, 0, 0], "kind": "centre"}
    c = np.mean(np.asarray(st, float), axis=0).tolist()
    return {"name": "centre", "pos": _on_ground(sc, c), "kind": "centre"}


def outdoor_plan(M, sc, files: dict) -> list[dict]:
    """The routes of a whole place: each arrival to the centre; the centre to each target; along each street."""
    poi = points_of_interest(sc, files)
    c = centre_of(sc, poi)
    want = [(a, c) for a in poi["arrivals"] if a is not c]
    want += [(c, t) for t in poi["targets"]]
    for q in files.get("paths") or []:
        if q.get("kind") == "street" and q.get("points"):
            a = {"name": f"{q['id'].rsplit('.', 1)[-1]} start", "pos": _on_ground(sc, q["points"][0]), "kind": "street"}
            b = {"name": f"{q['id'].rsplit('.', 1)[-1]} end", "pos": _on_ground(sc, q["points"][-1]), "kind": "street"}
            want.append((a, b))
    return want


def room_kind(info: dict, rows: list[dict], quests: list[dict], people: list[dict], space: str) -> dict:
    """Whether a room is copied whole and unchanged, or changed by us, from the place files: changed by a cut, by
    rows struck from the copy (a strip or a dropped door), by a piece we added or moved (any row but its doors with
    a base), by a quest spot in it, or by a person of ours given a work spot in it. A new name alone changes nothing
    a walk sees. {kind, why, things, spots, cut}: things are the rows added or moved, spots the quest and work spots."""
    why, things, spots = [], [], []
    cut = info.get("cut")
    if isinstance(cut, str):
        import ast
        try:
            cut = ast.literal_eval(cut)
        except (ValueError, SyntaxError):
            cut = {"box": None}
    if cut:
        why.append("cut")
    gone = [r for r in rows if r.get("removed")]
    if gone:
        why.append(f"{len(gone)} source pieces struck")
    for r in rows:
        if r.get("removed") or r.get("kind") == "door" or not r.get("pos") or not r.get("base"):
            continue
        things.append({"name": f"{'moved' if r.get('src') else 'added'} {r.get('edid') or r['id'].rsplit('.', 1)[-1]}",
                       "pos": list(r["pos"]), "id": r["id"]})
    if things:
        why.append(f"{len(things)} pieces added or moved")
    for q in quests:
        if q.get("space") == space and q.get("pos"):
            spots.append({"name": f"quest spot {q.get('ref')}", "pos": list(q["pos"])})
    for w in people:
        wk = w.get("work") or {}
        if wk.get("space") == space and wk.get("pos"):
            spots.append({"name": f"work spot of {w.get('name')}", "pos": list(wk["pos"])})
    if spots:
        why.append(f"{len(spots)} quest or work spots")
    return {"kind": "changed" if why else "unchanged", "why": why, "things": things, "spots": spots,
            "cut": (cut or {}).get("box") if isinstance(cut, dict) else None}


ENTER = (("ahead", 0, 0), ("left", 60, 0), ("right", -60, 0))
AT_THING = (("ahead", 0, 0), ("down", 0, -20), ("left", 90, 0), ("right", -90, 0))


def ways_in(M, pieces: list[dict]) -> list[dict]:
    """Each door of the room, standing just inside it: the mesh nearest the door, 64 units into the room, facing in."""
    out = []
    mid = M.C[M.lab == M.main].mean(axis=0) if M.main >= 0 else None
    for p in pieces:
        if p.get("kind") != "door" or not (p.get("door") or {}).get("to_space"):
            continue
        t, at, _ = snap(M, _xyz(p), reach=600, reach_z=400)
        if t < 0 or mid is None:
            continue
        v = mid[:2] - np.asarray(at[:2])
        v = v / max(float(np.linalg.norm(v)), 1e-9)
        t2, z2 = M.tri_at(at[0] + v[0] * 64, at[1] + v[1] * 64, at[2])
        pos = [at[0] + v[0] * 64, at[1] + v[1] * 64, float(z2)] if t2 >= 0 else list(at)
        out.append({"name": f"way in from {p['door']['to_space']}", "pos": pos, "dir": [float(v[0]), float(v[1])], "id": p["id"]})
    return out


def room_plan(M, kind: dict, pieces: list[dict]) -> list[dict]:
    """A room's stations: the entering set at each way in (ahead, left and right); in a changed room a short walk from
    the first way in to each thing added or moved and each quest or work spot (one station at each: ahead, down,
    left, right), and a look at each side of a cut from the floor nearest it. Each a route {name, stations, ...}."""
    doors = ways_in(M, pieces)
    sts = [_st(k + 1, d["pos"], d["dir"], f"way in, {d['name']}", ENTER) for k, d in enumerate(doors)]
    routes = [{"name": "entering", "from": "the doors", "to": "the room", "stations": sts, "length": 0}]
    if kind["kind"] != "changed" or not doors:
        return routes
    a = {"name": doors[0]["name"], "pos": doors[0]["pos"], "kind": "way in"}
    by = {p["id"]: p for p in pieces}
    things = []
    for t in kind["things"]:   # what a person walks up to: not a light, a marker or a piece the room no longer holds
        p = by.get(t.get("id"))
        if p is None or p.get("kind") in ("light", "marker", "sound", "other") or not p.get("model"):
            continue
        things.append(t | {"name": t["name"].split(" ", 1)[0] + " " + (p.get("edid") or t["name"].split(" ", 1)[-1])})
    for t in things + kind["spots"]:
        r = plan_route(M, f"{route_name(a, t)}-{len(routes)}", a, t | {"kind": "thing"})
        P = r.get("walk")
        r["stations"] = []
        if P is not None and len(P):
            j0 = max(0, len(P) - 5)
            d = P[-1, :2] - P[j0, :2]
            d = d / float(np.linalg.norm(d)) if np.linalg.norm(d) > 1 else np.array([0.0, 1.0])
            r["stations"] = [_st(1, P[-1, :3].tolist(), d.tolist(), f"at {t['name']}", AT_THING, s=float(P[-1, 3]))]
        routes.append(r)
    if kind.get("cut"):
        x1, y1, x2, y2 = kind["cut"]
        x1, x2, y1, y2 = min(x1, x2), max(x1, x2), min(y1, y2), max(y1, y2)
        sts = []
        for nm, edge, dv in (("west", (x1, (y1 + y2) / 2), (-1, 0)), ("east", (x2, (y1 + y2) / 2), (1, 0)),
                             ("south", ((x1 + x2) / 2, y1), (0, -1)), ("north", ((x1 + x2) / 2, y2), (0, 1))):
            d = np.hypot(M.C[:, 0] - edge[0], M.C[:, 1] - edge[1])
            i = int(np.argmin(d))
            if d[i] < 900:
                sts.append(_st(len(sts) + 1, M.C[i].tolist(), list(dv), f"the cut's {nm} side", (("ahead", 0, 0),)))
        if sts:
            routes.append({"name": "cut", "from": "the floor", "to": "the cut's sides", "stations": sts, "length": 0})
    return routes


def _st(n, pos, d, what, looks, s=0.0) -> dict:
    return {"n": n, "s": round(s), "pos": [round(float(v), 1) for v in pos], "dir": [round(float(d[0]), 4), round(float(d[1]), 4)],
            "what": what, "heading": round((math.degrees(math.atan2(d[0], d[1])) + 360) % 360), "looks": list(looks)}


def wall_ring(M, n: int = 8) -> list[dict]:
    """Eight points round the main floor near its walls, 48 units in from the open edge nearest each compass turn."""
    B = M.boundary(M.main)
    if not len(B):
        return []
    mids = B.mean(axis=1)
    c = M.C[M.lab == M.main].mean(axis=0)
    ang = np.arctan2(mids[:, 1] - c[1], mids[:, 0] - c[0])
    out = []
    for k in range(n):
        a = -math.pi + 2 * math.pi * k / n
        d = np.abs((ang - a + math.pi) % (2 * math.pi) - math.pi) + 1e-3 / (1 + np.hypot(mids[:, 0] - c[0], mids[:, 1] - c[1]))
        p = mids[int(np.argmin(d))]
        v = c[:2] - p[:2]
        v = v / max(float(np.linalg.norm(v)), 1e-9)
        x, y = p[:2] + v * 48
        t, z = M.tri_at(x, y, p[2])
        if t >= 0:
            out.append({"name": f"wall {k + 1}", "pos": [float(x), float(y), float(z)]})
    return out


def route_name(a: dict, b: dict) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", f"{a['name']}--{b['name']}".lower()).strip("-")
    return s[:70] + "-" + hashlib.sha1(s.encode()).hexdigest()[:4] if len(s) > 74 else s


def plan_all(M, want: list[tuple[dict, dict]], ground, stride: float, drops=None) -> list[dict]:
    """Every route planned and its stations placed, duplicates of an earlier route's stations marked."""
    routes, done = [], set()
    for a, b in want:
        k = (tuple(round(v / 32) for v in a["pos"][:2]), tuple(round(v / 32) for v in b["pos"][:2]))
        if k in done or k[0] == k[1]:
            continue
        done.add(k)
        nm = route_name(a, b)
        names = {x["name"] for x in routes}
        n = 2
        while nm in names:   # two doors to one room: two routes
            nm = f"{route_name(a, b)}-{n}"
            n += 1
        r = plan_route(M, nm, a, b)
        P = r.get("walk")
        if P is not None and len(P):
            evs = events(P, ground, drops)
            start = f"doorway of {a['name'][8:]}" if a.get("kind") == "doorway" else ("way in, " + a["name"]) if a.get("kind") == "way in" else f"start: {a['name']}"
            end = f"doorway of {b['name'][8:]}" if b.get("kind") == "doorway" else f"end: {b['name']}" + (" (the walk breaks here)" if r.get("broken") else "")
            r["stations"] = stations(P, evs, stride, start, end)
            if b.get("door_z") is not None and b["door_z"] - P[-1, 2] > DOOR_OVER:
                r["door_above"] = round(float(b["door_z"] - P[-1, 2]))
        else:
            r["stations"] = []
        routes.append(r)
    dedup(routes)
    return routes


def plan_lines(routes: list[dict], stale: dict | None) -> list[str]:
    out = []
    if stale and stale.get("stale"):
        out.append("STALE: the place files are newer than the build this walkable mesh is of; the strips are marked stale")
    for r in routes:
        n = len(r["stations"])
        new = sum("seen" not in s for s in r["stations"])
        line = f"{r['name']}: {r.get('length', 0):.0f} u, {n} stations ({new} new)"
        if r.get("same_as"):
            line += f"; every station already seen in {', '.join(r['same_as'])}"
        if r.get("broken"):
            line += f"; CANNOT BE WALKED TO: {r['broken']['why']}"
        if r.get("door_above"):
            line += f"; THE DOOR IS {r['door_above']} u OVER THE END OF THE WALK: its arrival is under it, no way up"
        out.append(line)
    return out


# ---------- the page: shooting, strips, tables ----------
def tile_size() -> tuple[int, int]:
    from tools.places.look import survey
    return survey.TW, survey.TH


def run(d, place: str, strokes, args: list[str], space: str = "exterior") -> dict:
    from tools.places.look import verbs
    from tools.places.look.scene import LOOK_OUT
    t0 = time.time()
    pos, o = verbs._opts(args, {"plan": False, "changed": False, "stride": True, "rooms": False, "again": False})
    if o.get("rooms") and space == "exterior":
        return run_rooms(d, place, strokes, o)
    stride = float(o.get("stride", STRIDE if len(pos) >= 2 or space != "exterior" else PLACE_STRIDE))
    inside = space != "exterior"
    sc = d.scene(place, strokes, space)
    M, facts = verbs.built_mesh(place, space)
    fallback = M is None
    if fallback:
        if inside:
            return {"error": f"{space} has no built walkable mesh: {facts.get('why')}"}
        M = paths_mesh(sc)
    if inside:
        rk = room_kind(sc.info, sc.files["spaces"][space]["refs"], sc.files.get("quests") or [],
                       sc.files.get("people") or [], space)
        want = []
    elif len(pos) >= 2:
        want = [(named(sc, M, pos[0]), named(sc, M, pos[1]))]
    else:
        want = outdoor_plan(M, sc, sc.files)
    drops = None
    if inside:
        routes = room_plan(M, rk, sc.pieces)
    else:
        pts = np.asarray([p for a, b in want for p in (a["pos"], b["pos"])], float)
        box = [pts[:, 0].min() - 1500, pts[:, 1].min() - 1500, pts[:, 0].max() + 1500, pts[:, 1].max() + 1500]
        drops = drop_edges(M, sc.ground, box)
        routes = plan_all(M, want, sc.ground, stride, drops)
    if o.get("changed") and not inside:
        routes = changed_only(sc, place, routes)
    lines = plan_lines(routes, facts)
    if inside:
        lines.insert(0, f"{space}: {rk['kind']}" + (f" ({', '.join(rk['why'])})" if rk["why"] else " (copied whole)"))
    if fallback:
        lines.insert(0, "NO BUILT MESH: walked on the place's paths, not the mesh")
    root = LOOK_OUT / place / "playwalk" / (space if inside else "")
    plan_out = {"place": place, "space": space, "lines": lines, "stale": bool(facts.get("stale")),
                "routes": [{k: v for k, v in r.items() if k not in ("walk", "tris")} for r in routes]}
    root.mkdir(parents=True, exist_ok=True)
    (root / "plan.json").write_text(json.dumps(plan_out, indent=1, default=float))
    if o.get("plan"):
        return {"plan": lines, "plan_json": str(root / "plan.json")}
    d.open(place)
    d.sync(strokes)
    d.go(space)
    passes = [("lit", True)]
    res = []
    for r in routes:
        for tag, fill in passes:
            res.append(shoot_route(d, sc, M, r, root, inside, fill, tag, bool(facts.get("stale")) or fallback,
                                   again=bool(o.get("again"))))
    if not inside:
        state_save(sc, place)
    looks = sum(x["looks"] for x in res)
    failed = sum(x["failed"] for x in res)
    mb = sum(f.stat().st_size for f in root.rglob("*.png")) / 1e6
    return {"lines": lines + [x["line"] for x in res], "routes": len(routes), "stations": sum(x["stations"] for x in res),
            "looks": looks, "failed": failed, "place_faults": [f for x in res for f in x["place_faults"]]
            + [f"{r['name']}: the door is {r['door_above']} u over the end of the walk" for r in routes if r.get("door_above")]
            + [f"{r['name']}: {r['broken']['why']}" for r in routes if r.get("broken")],
            "seconds": round(time.time() - t0, 1), "megabytes": round(mb, 1), "out": str(root)}


def named(sc, M, n: str) -> dict:
    from tools.places.look import verbs
    if n in ("landing", "centre", "center", "market"):
        poi = points_of_interest(sc, sc.files)
        if n == "market":
            st = [t["pos"] for t in poi["targets"] if t["kind"] == "stall"]
            if st:
                return {"name": "market", "pos": _on_ground(sc, np.median(np.asarray(st, float), axis=0).tolist()), "kind": "stall"}
        c = centre_of(sc, poi)
        if n == "landing" and c["name"] != "landing":
            q = [a for a in poi["arrivals"] if "landing" in a["name"]]
            if q:
                return q[0]
        return c
    th = sc.resolve(n)
    at = verbs.join_point(sc, th)
    kind = "doorway" if th["kind"] == "door" else th["kind"]
    name = f"door of {n}" if kind == "doorway" else th["name"]
    return {"name": name, "pos": list(at), "kind": kind}


def paths_mesh(sc):
    """No built mesh: a thin mesh of the place's paths (two triangles a segment, at the ground's height)."""
    from tools.places.look.mesh import Mesh
    V, T = [], []
    for q in sc.files.get("paths") or []:
        pts = q.get("points") or []
        for p, r in zip(pts, pts[1:]):
            d = np.asarray(r[:2], float) - np.asarray(p[:2], float)
            n = np.array([-d[1], d[0]]) / max(float(np.linalg.norm(d)), 1e-9) * 48
            base = len(V)
            for x, y in (np.asarray(p[:2]) + n, np.asarray(p[:2]) - n, np.asarray(r[:2]) + n, np.asarray(r[:2]) - n):
                V.append([x, y, sc.ground.height(x, y) or 0.0])
            T += [[base, base + 1, base + 2], [base + 1, base + 3, base + 2]]
    nb = _neighbours(np.asarray(T, int).reshape(-1, 3), np.asarray(V, float).reshape(-1, 3))
    return Mesh(V, T, nb)


def _neighbours(T, V, weld: float = 60.0):
    """Triangles joined across an edge, vertices within `weld` across the plan counted as one."""
    key = np.round(V[:, :2] / weld).astype(int) if len(V) else np.zeros((0, 2), int)
    vid = {}
    canon = [vid.setdefault(tuple(k), len(vid)) for k in key]
    edges: dict = {}
    for i, t in enumerate(T):
        for k in range(3):
            e = tuple(sorted((canon[t[k]], canon[t[(k + 1) % 3]])))
            edges.setdefault(e, []).append((i, k))
    nb = -np.ones((len(T), 3), int)
    for e, users in edges.items():
        for i, k in users:
            for j, _ in users:
                if j != i:
                    nb[i, k] = j
    return nb


def changed_only(sc, place, routes):
    from tools.places.look import survey
    from tools.places.look.scene import LOOK_OUT
    p = LOOK_OUT / place / "playwalk" / "state.json"
    last = json.loads(p.read_text()) if p.exists() else {}
    now = survey.structure_hashes(sc.files["spaces"]["exterior"]["refs"])
    ch = survey.changed(last, now)
    cl = sc.clusters()
    pts = np.asarray([_xyz(q)[:2] for c in ch for q in cl.get(c, [])] or [[1e12, 1e12]], float)
    keep = []
    for r in routes:
        P = r.get("walk")
        if P is None or not len(P):
            continue
        d = np.min(np.hypot(P[:, None, 0] - pts[None, :, 0], P[:, None, 1] - pts[None, :, 1]))
        if d <= 1000:
            keep.append(r)
    return keep


def state_save(sc, place):
    from tools.places.look import survey
    from tools.places.look.scene import LOOK_OUT
    p = LOOK_OUT / place / "playwalk" / "state.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(survey.structure_hashes(sc.files["spaces"]["exterior"]["refs"]), indent=1))


def shoot_route(d, sc, M, r: dict, root: Path, inside: bool, fill: bool, tag: str, stale: bool, again=False) -> dict:
    """Every new station of one route shot (each station's looks in one page call, failures retried by nudging),
    judged, and laid out as strips, a forward filmstrip, a map, tiles and a table."""
    from tools.places.look import framing
    w, h = tile_size()
    out = root / r["name"]
    key = hashlib.sha1(json.dumps([TOOL, r.get("way"), [s.get("seen") for s in r["stations"]], w, h, fill]).encode()).hexdigest()[:12]
    done = out / "table.json"
    if done.exists() and not again:
        old = json.loads(done.read_text())
        if old.get("key") == key:   # this route as planned was shot already: interrupted runs resume past it
            return old["summary"]
    tiles = out / "tiles"
    tiles.mkdir(parents=True, exist_ok=True)
    blocked = framing.blocker(sc.everything(), None if inside else sc.ground)
    by_id = {p["id"]: p for p in sc.everything()}
    P = r.get("walk")
    rows, imgs = [], {}
    pf = []
    for st in r["stations"]:
        if "seen" in st:
            rows.append({"station": st["n"], "s": st["s"], "what": st["what"], "seen": list(st["seen"])})
            continue
        lks = looks_of(st)
        cams = [cam_of(st, lk, w, h, inside=inside) for lk in lks]
        got = d.page.evaluate("(cs) => agent.shots(cs)", [c | {"ids": True, "fill": fill, "grass": False} for c in cams])
        eye = cams[0]["pos"]
        ins0 = blocked(eye) or blocked([eye[0], eye[1], st["pos"][2] + 40])
        alts = nudges(M, P, st) if P is not None else []
        free = [q for q in alts if not (blocked([q[0], q[1], q[2] + geom.EYE]) or blocked([q[0], q[1], q[2] + 40]))]
        all_in = None
        if ins0 and not free:
            all_in = ins0.split("inside ", 1)[-1] if "inside" in ins0 else ins0
        for k, (lk, c, rr) in enumerate(zip(lks, cams, got)):
            img, ev, verdict, at = _judge(sc, c, rr, by_id, lk, st, inside, ins0, all_in)
            tries = 0
            if verdict["fault"] == "capture":   # nudge: the first free spot, then the next
                for q in free[:2]:
                    tries += 1
                    c2 = cam_of(st, lk, w, h, pos=q, inside=inside)
                    rr2 = d.page.evaluate("(c) => agent.shot(c)", c2 | {"ids": True, "fill": fill, "grass": False})
                    i2, ev2, v2, _ = _judge(sc, c2, rr2, by_id, lk, st, inside, None, None)
                    if v2["verdict"] == "good" or v2["fault"] == "place":
                        img, ev, verdict, c = i2, ev2, v2, c2
                        break
            f = tiles / f"{st['n']:03d}-{lk[0]}.png"
            img.convert("RGB").save(f, compress_level=3)
            row = {"station": st["n"], "s": st["s"], "heading": st["heading"], "what": st["what"], "look": lk[0],
                   "file": str(f), "capture": verdict["verdict"], "fault": verdict["fault"], "why": verdict["why"],
                   "nudged": tries, "fills": [f"{x['edid']} {x['share']:.0%}" + (f" at {x['dist']} u" if x.get("dist") is not None else "") for x in ev["fills"]],
                   "eye": c["pos"]}
            rows.append(row)
            imgs[(st["n"], lk[0])] = (img, row)
            if verdict["fault"] == "place":
                pf.append(f"{r['name']} #{st['n']} ({st['what']}, {lk[0]}): {verdict['why']}")
    strips = make_strips(r, rows, imgs, out, inside, fill, stale)
    film = filmstrip(r, imgs, out, stale)
    mp = route_map(sc, M, r, out)
    looks = [x for x in rows if "look" in x]
    failed = [x for x in looks if x["capture"] == "failed"]
    summary = {"route": r["name"], "stations": sum("seen" not in s for s in r["stations"]), "looks": len(looks),
               "failed": len(failed), "capture_faults": sum(x["fault"] == "capture" for x in failed),
               "place_faults": sorted(set(pf)), "strips": strips, "filmstrip": film, "map": mp,
               "line": f"{r['name']}{' [' + tag + ']' if inside else ''}: {len(looks)} looks, {len(failed)} failed "
                       f"({sum(x['fault'] == 'place' for x in failed)} the place's); {out}"}
    (out / "table.json").write_text(json.dumps({"key": key, "route": {k: v for k, v in r.items() if k not in ("walk", "tris")},
                                                "rows": rows, "summary": summary}, indent=1, default=float))
    (out / "table.txt").write_text(table_text(r, rows, stale))
    return summary


def _judge(sc, c, rr, by_id, lk, st, inside, ins, all_in):
    from tools.places.look import capture, draw, verbs
    img = draw.from_data_url(rr["png"])
    ids = capture.decode(rr["ids"], c["w"], c["h"])
    img = capture.hatch(img, ids, rr["table"], rr["id0"], verbs.helper_label(sc))
    ev = evidence(ids, rr["table"], rr["id0"], by_id, c["pos"])
    ev["inside"], ev["all_inside"] = ins, all_in
    ev["in_piece"] = in_piece(ins)
    if ev["in_piece"] and (OPEN_UNDER.search(ev["in_piece"]) or inside):   # a deck on stilts, a room's shell: a box of air
        ev["inside"] = ev["all_inside"] = ev["in_piece"] = None
    ev["low_ceiling"] = bool(inside and all_in)
    v = classify(lk[0], st["what"], ev, inside)
    return img, ev, v, c


def table_text(r: dict, rows: list[dict], stale: bool) -> str:
    head = [f"route {r['name']}: {r['from']} to {r['to']}, {r.get('length', 0):.0f} u" + ("  STALE MESH" if stale else "")]
    if r.get("broken"):
        head.append(f"CANNOT BE WALKED TO: {r['broken']['why']}")
    out = head + ["station  walked  heading  what  look  capture  fills (three biggest)  file"]
    for x in rows:
        if "seen" in x:
            out.append(f"#{x['station']:<3} {x['s']:>6}  {x['what']}: seen already at {x['seen'][0]} #{x['seen'][1]}")
            continue
        cap = "good" if x["capture"] == "good" else f"FAILED ({x['fault']}): {x['why']}"
        out.append(f"#{x['station']:<3} {x['s']:>6}  {x['heading']:>3}  {x['what']}  {x['look']}  {cap}  "
                   f"[{'; '.join(x['fills'])}]  {Path(x['file']).name}")
    return "\n".join(out) + "\n"


def _label(img, row, small=(256, 192)):
    from PIL import ImageDraw
    from tools.places.look import capture, draw
    t = img.resize(small)
    if row["capture"] == "failed":
        t = capture.strike(t)
    dd = ImageDraw.Draw(t)
    draw.tag(dd, (small[0] // 2, 8), f"#{row['station']} {row['s']}u hdg {row['heading']} {row['look']}", size=11)
    draw.tag(dd, (small[0] // 2, small[1] - 26), row["what"][:40], size=10, fill=(255, 255, 160, 240))
    if row["capture"] == "failed":
        col = (255, 170, 60, 240) if row["fault"] == "place" else (255, 120, 120, 240)
        draw.tag(dd, (small[0] // 2, small[1] - 10), (("PLACE: " if row["fault"] == "place" else "") + row["why"])[:48], size=10, fill=col)
    return t


def make_strips(r, rows, imgs, out: Path, inside: bool, fill: bool, stale: bool) -> list[str]:
    from PIL import Image, ImageDraw
    from tools.places.look import draw
    present = {x["look"] for x in rows if "look" in x}
    cols = [lk[0] for lk in LOOKS + DIAGONALS if lk[0] in present]
    sts = sorted({x["station"] for x in rows if "look" in x})
    tw, th = 256, 192
    paths = []
    for k in range(0, len(sts), 8):
        part = sts[k:k + 8]
        img = Image.new("RGB", (tw * len(cols), th * len(part) + 28), (30, 30, 30))
        dd = ImageDraw.Draw(img)
        title = f"{r['from']} to {r['to']}  stations {part[0]}-{part[-1]}"
        if inside:
            title += "  " + ("neutral fill: viewer light, not the game's" if fill else "the room's own light: viewer light, not the game's")
        if stale:
            title += "  STALE MESH"
        dd.text((6, 6), title, fill=(255, 255, 255), font=draw.font(14, True))
        for i, sn in enumerate(part):
            for j, cn in enumerate(cols):
                got = imgs.get((sn, cn))
                if got:
                    img.paste(_label(*got).convert("RGB"), (j * tw, 28 + i * th))
        p = out / f"strip-{k // 8 + 1:02d}.png"
        img.save(p, compress_level=3)
        paths.append(str(p))
    return paths


def filmstrip(r, imgs, out: Path, stale: bool) -> str | None:
    from PIL import Image
    ahead = [(sn, v) for (sn, lk), v in sorted(imgs.items()) if lk == "ahead"]
    if not ahead:
        return None
    tw, th, cols = 256, 192, 6
    rows_n = (len(ahead) + cols - 1) // cols
    img = Image.new("RGB", (tw * cols, th * rows_n), (30, 30, 30))
    for i, (_, (im, row)) in enumerate(ahead):
        img.paste(_label(im, row).convert("RGB"), ((i % cols) * tw, (i // cols) * th))
    p = out / "forward.png"
    img.save(p, compress_level=3)
    return str(p)


def route_map(sc, M, r, out: Path, size: int = 640) -> str | None:
    """A small top view: the mesh about the route in grey, the walk in red, each station's number."""
    from PIL import Image, ImageDraw
    from tools.places.look import draw
    P = r.get("walk")
    if P is None or not len(P):
        return None
    x1, y1 = P[:, 0].min() - 400, P[:, 1].min() - 400
    x2, y2 = P[:, 0].max() + 400, P[:, 1].max() + 400
    s = size / max(x2 - x1, y2 - y1)
    img = Image.new("RGB", (size, size), (250, 250, 245))
    dd = ImageDraw.Draw(img)
    px = lambda x, y: ((x - x1) * s, size - (y - y1) * s)  # noqa: E731
    sel = np.where((M.C[:, 0] > x1) & (M.C[:, 0] < x2) & (M.C[:, 1] > y1) & (M.C[:, 1] < y2))[0]
    for t in sel[:60000]:
        a, b, c = M.V[M.T[t]]
        dd.polygon([px(*a[:2]), px(*b[:2]), px(*c[:2])], fill=(200, 215, 200) if M.lab[t] == M.main else (215, 200, 230))
    for p in getattr(sc, "pieces", []):
        if p.get("kind") in ("building",) and p.get("m"):
            lo, hi = geom.aabb(p)
            if hi[0] > x1 and lo[0] < x2 and hi[1] > y1 and lo[1] < y2:
                dd.rectangle([px(lo[0], hi[1]), px(hi[0], lo[1])], outline=(120, 90, 60))
    dd.line([px(*q[:2]) for q in P], fill=(210, 30, 30), width=3)
    for st in r["stations"]:
        draw.tag(dd, px(*st["pos"][:2]), str(st["n"]), size=11, fill=(255, 255, 200, 240) if "seen" not in st else (220, 220, 220, 200))
    if r.get("broken") and (r["broken"].get("gap") or {}).get("at"):
        g = r["broken"]["gap"]["at"]
        x, y = px(*g[:2])
        dd.ellipse([x - 8, y - 8, x + 8, y + 8], outline=(255, 0, 0), width=3)
    p = out / "map.png"
    img.save(p, compress_level=3)
    return str(p)


def run_rooms(d, place: str, strokes, o: dict) -> dict:
    """Every room of the place walked in turn: one line per room."""
    from tools.places.look import verbs
    t0 = time.time()
    sc = d.scene(place, strokes, "exterior")
    lines = []
    for sid in sc.files["spaces"]:
        if sid == "exterior":
            continue
        M, facts = verbs.built_mesh(place, sid)
        if M is None:
            lines.append(f"{sid}: no built walkable mesh")
            continue
        try:
            got = run(d, place, strokes, [], sid)
        except Exception as e:  # noqa: BLE001  one room's failure is its line, not the end of the walk
            lines.append(f"{sid}: {type(e).__name__}: {e}"[:200])
            continue
        void = any("void" in f for f in got.get("place_faults", []))
        unreach = [ln.split(":")[0] for ln in got.get("lines", []) if "CANNOT BE WALKED TO" in ln]
        if "error" in got:
            lines.append(f"{sid}: {got['error']}")
            continue
        lines.append(f"{got['lines'][0]}: {got.get('stations')} stations, {got.get('looks')} looks, "
                     f"{got.get('failed')} failed, void seen: {'yes' if void else 'no'}, cannot be walked to: "
                     f"{len(unreach)} ({got.get('seconds')} s)")
    return {"lines": lines, "seconds": round(time.time() - t0, 1)}
