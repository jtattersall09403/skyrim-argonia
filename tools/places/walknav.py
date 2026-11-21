"""The owner's walking-mesh zones (a place's walk.jsonl; docs/design/place-studio.md, Build: the owner's walking zones)
applied to a built place's navmesh, after the hand-change rules and before finish_navmesh, outside and in a room.

Each row says what the owner wants, never which triangles to move, so it holds over every rebuild:

- `block` {outline}: no walking here. The mesh is cut along the outline and every piece inside it goes; the cut edge
  is re-triangulated with the rest of the cell (vertices near the outline are put on it first, short edges merged,
  flat triangles dropped: no slivers).
- `walk` {outline}: walk here. Whatever lay inside the outline is cut away and the outline itself is meshed on the
  surface under it (the height of the mesh that was there, else the height the studio's pen read on the ground, deck
  or stair), joined to what is round it by shared vertices.
- `join` {points: [a, b], gap}: these should connect. The open mesh edge nearest each point (within REACH of it in
  plan and STEP in height) is bridged by a strip WIDTH wide when the two edges are within `gap` (at most MAX_GAP) in
  plan, STEP in height and the walkable slope; otherwise the join is refused with a note that says why.

Rows apply in id order: blocks, then walk zones, then joins (a join sees the edges the zones made). Pure numpy over
carrynav's polygons and meshes: no game data here."""
from __future__ import annotations

import math
from types import SimpleNamespace

import numpy as np

from tools.places import carrynav as cn

STEP = 64.0         # a join bridges edges no more than this apart in height (a step, as the door rule measures it)
GAP = 256.0         # a join's distance in plan when the row gives none
MAX_GAP = 512.0     # and never more than this
REACH = 192.0       # a join's point finds the open edge within this of it in plan ...
REACH_Z = 128.0     # ... and this in height
WIDTH = 128.0       # a bridge's width along each edge (two agent widths)
KINDS = ("block", "walk", "join")


# ---- outlines as convex parts ------------------------------------------------------------------------------------------

def _area2(pts) -> float:
    return sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(pts, pts[1:] + pts[:1]))


def clean_outline(outline) -> list:
    """The outline as counter-clockwise [x, y, z] points, repeated and collinear points dropped."""
    pts = []
    for p in outline:
        q = (float(p[0]), float(p[1]), float(p[2]) if len(p) > 2 else 0.0)
        if not pts or math.hypot(q[0] - pts[-1][0], q[1] - pts[-1][1]) > 1.0:
            pts.append(q)
    if len(pts) > 1 and math.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1]) <= 1.0:
        pts.pop()
    if _area2(pts) < 0:
        pts.reverse()
    changed = True
    while changed and len(pts) > 3:
        changed = False
        for i in range(len(pts)):
            a, b, c = pts[i - 1], pts[i], pts[(i + 1) % len(pts)]
            cr = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
            if abs(cr) <= 1e-6 * max(1.0, math.hypot(b[0] - a[0], b[1] - a[1]) * math.hypot(c[0] - b[0], c[1] - b[1])):
                pts.pop(i)
                changed = True
                break
    return pts if len(pts) >= 3 and abs(_area2(pts)) > 1.0 else []


def _convex(poly) -> bool:
    n = len(poly)
    for i in range(n):
        a, b, c = poly[i - 1], poly[i], poly[(i + 1) % n]
        if (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]) < -1e-9:
            return False
    return True


def _inside_tri(p, a, b, c) -> bool:
    def s(u, v, w):
        return (v[0] - u[0]) * (w[1] - u[1]) - (v[1] - u[1]) * (w[0] - u[0])
    return s(a, b, p) >= 0 and s(b, c, p) >= 0 and s(c, a, p) >= 0


def convex_parts(outline) -> list:
    """A simple polygon (counter-clockwise) as few convex polygons: ear clipping, then neighbouring parts merged
    across their shared diagonal while the union stays convex (Hertel and Mehlhorn)."""
    pts = list(outline)
    if len(pts) < 3:
        return []
    if _convex(pts):
        return [pts]
    idx = list(range(len(pts)))
    ears = []
    guard = 0
    while len(idx) > 3 and guard < 10000:
        guard += 1
        for k in range(len(idx)):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            a, b, c = pts[i0], pts[i1], pts[i2]
            if (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]) <= 1e-9:
                continue
            if any(_inside_tri(pts[j], a, b, c) for j in idx if j not in (i0, i1, i2)):
                continue
            ears.append([i0, i1, i2])
            idx.pop(k)
            break
        else:
            break                       # a self-crossing outline: what is left goes whole
    ears.append(idx)
    parts = [list(e) for e in ears]
    merged = True
    while merged:
        merged = False
        for i in range(len(parts)):
            for j in range(i + 1, len(parts)):
                u = _merge(parts[i], parts[j])
                if u and _convex([pts[q] for q in u]):
                    parts[i] = u
                    parts.pop(j)
                    merged = True
                    break
            if merged:
                break
    return [[pts[q] for q in p] for p in parts]


def _merge(p, q):
    """Two index polygons sharing one edge (a, b in p, b, a in q) as one, or None."""
    for i in range(len(p)):
        a, b = p[i], p[(i + 1) % len(p)]
        for j in range(len(q)):
            if q[j] == b and q[(j + 1) % len(q)] == a:
                rest_q = [q[(j + 2 + k) % len(q)] for k in range(len(q) - 2)]
                return p[:i + 1] + rest_q + p[i + 1:]
    return None


# ---- surface heights ---------------------------------------------------------------------------------------------------

def _height_on(tris, x, y, z_hint):
    """The height at (x, y) of the triangle that holds it nearest z_hint (within STEP), or None."""
    best = None
    for t in tris:
        a, b, c = t
        d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(d) < 1e-9:
            continue
        l1 = ((b[1] - c[1]) * (x - c[0]) + (c[0] - b[0]) * (y - c[1])) / d
        l2 = ((c[1] - a[1]) * (x - c[0]) + (a[0] - c[0]) * (y - c[1])) / d
        l3 = 1 - l1 - l2
        if min(l1, l2, l3) < -1e-6:
            continue
        z = l1 * a[2] + l2 * b[2] + l3 * c[2]
        if abs(z - z_hint) <= STEP and (best is None or abs(z - z_hint) < abs(best - z_hint)):
            best = z
    return best


# ---- the zones on a set of meshes ------------------------------------------------------------------------------------

def _planes(part):
    return cn.planes([(p[0], p[1]) for p in part])


def _bb(poly):
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    return min(xs), min(ys), max(xs), max(ys)


def apply(meshes: dict, rows: list, cell_of=None, neighbours: dict | None = None) -> tuple[dict, dict]:
    """Apply the zones to `meshes` {key: [(tri (3x3), flags)]} (a key is an exterior cell, cut to its cell box, or one
    room's whole mesh when `cell_of` is None). Returns ({key: carrynav.finish_cell dict} for every key a row touched,
    stats {block, walk, join, joined, refused: [plain lines], removed, added})."""
    rows = sorted((r for r in rows if r.get("kind") in KINDS), key=lambda r: (KINDS.index(r["kind"]), r["id"]))
    st = {"block": 0, "walk": 0, "join": 0, "joined": 0, "refused": [], "removed": 0, "added": 0}
    zones = []
    for r in rows:
        if r["kind"] == "join":
            continue
        out = clean_outline(r.get("outline") or [])
        if not out:
            st["refused"].append(f"{r['kind']} zone {r['id']}: its outline encloses nothing")
            continue
        zones.append((r, out, convex_parts(out)))
    boxes = {}

    def key_box(k):
        if k not in boxes:
            boxes[k] = cn.planes(cn.cell_box(k)) if cell_of else None
        return boxes[k]
    touched = set()
    for r, out, _ in zones:
        bb = _bb(out)
        touched |= _keys_in(meshes, bb, cell_of)
    joins = [r for r in rows if r["kind"] == "join"]
    for r in joins:
        a, b = r["points"]
        touched |= _keys_in(meshes, (min(a[0], b[0]) - REACH, min(a[1], b[1]) - REACH, max(a[0], b[0]) + REACH, max(a[1], b[1]) + REACH), cell_of)
    if not touched:
        for r in joins:
            st["refused"].append(f"join {r['id']}: there is no walking mesh near it")
        return {}, st
    segs = []
    for _, out, _ in zones:
        segs += list(zip(out, out[1:] + out[:1]))
    soup = {}
    for k in touched:
        rows_k = meshes.get(k) or []
        V = np.asarray([p for t, _ in rows_k for p in t], float).reshape(-1, 3)
        fixed = None
        if cell_of and len(V):
            x0, y0 = k[0] * cn.CELL, k[1] * cn.CELL
            fixed = (np.abs(V[:, 0] - x0) < 0.5) | (np.abs(V[:, 0] - x0 - cn.CELL) < 0.5) | \
                    (np.abs(V[:, 1] - y0) < 0.5) | (np.abs(V[:, 1] - y0 - cn.CELL) < 0.5)
        cn.snap(V, segs, fixed=fixed)
        soup[k] = [([tuple(p) for p in V[3 * i:3 * i + 3].tolist()], f) for i, (_, f) in enumerate(rows_k)]
    removed_tris = {k: [] for k in touched}         # what lay inside a walk zone: the surface it is meshed on
    for r, out, parts in zones:
        st[r["kind"]] += 1
        hs = [_planes(p) for p in parts]
        pbb = [_bb(p) for p in parts]
        for k in touched:
            nxt = []
            for poly, f in soup[k]:
                pp = poly if cn.area2(poly) > 0 else poly[::-1]
                pieces = [pp]
                hit = False
                for h, bb in zip(hs, pbb):
                    if not cn._overlap(cn._bbox(pp), bb):
                        continue
                    if cn.intersect(pp, h) is None:
                        continue
                    hit = True
                    pieces = [q for piece in pieces for q in cn.minus(piece, h)]
                if hit:
                    st["removed"] += 1
                    if r["kind"] == "walk":
                        removed_tris[k].append(poly)
                nxt += [(q, f) for q in pieces]
            soup[k] = nxt
        if r["kind"] == "walk":
            under = [t for k in touched for t in removed_tris[k] if len(t) == 3]
            for part in parts:
                lifted = [(p[0], p[1], _lift(p, under)) for p in part]
                for k in touched:
                    q = lifted if not cell_of else cn.intersect(lifted, key_box(k))
                    if q is not None:
                        soup[k].append((q, cn_flags_new()))
                        st["added"] += 1
    meshes_out = {}
    for k in touched:
        m = cn.Mesh()
        for poly, f in soup[k]:
            if abs(cn.area2(poly)) >= 2 * cn.MIN_AREA:
                m.add_poly(poly if cn.area2(poly) > 0 else poly[::-1], int(f) & ~(cn.EDGE_BITS | cn.DOOR) & 0xFFFF, 0)
        meshes_out[k] = m
    for r in joins:
        st["join"] += 1
        why = _join(r, meshes_out, cell_of, key_box)
        if why:
            st["refused"].append(f"join {r['id']}: {why}")
        else:
            st["joined"] += 1
    if cell_of:
        done = cn.finish_cells(meshes_out, neighbours)
    else:
        done = {}
        for k, m in meshes_out.items():
            cn.fix_t_junctions(m)
            cn.collapse_short(m)
            for _ in range(8):
                flats = cn.drop_flat(m)
                cn.fix_t_junctions(m)
                if not flats:
                    break
            got = cn.finish_cell(m)
            if got["tris"]:
                done[k] = got
    for k in touched:
        done.setdefault(k, None)
    return done, st


def cn_flags_new() -> int:
    from tools.navmesh import nvnm
    return nvnm.FOUND


def _lift(p, under) -> float:
    z = _height_on(under, p[0], p[1], p[2])
    return float(p[2]) if z is None else float(z)


def _keys_in(meshes, bb, cell_of) -> set:
    if cell_of is None:
        got = set()
        for k, rows in meshes.items():
            pts = [q for t, _ in rows for q in t]
            if pts and cn._overlap(_bb(pts), bb):
                got.add(k)
        return got
    return {(cx, cy) for cx in range(math.floor(bb[0] / cn.CELL), math.floor(bb[2] / cn.CELL) + 1)
            for cy in range(math.floor(bb[1] / cn.CELL), math.floor(bb[3] / cn.CELL) + 1)}


def open_edges(meshes_out: dict, cell_of) -> list:
    """Every open edge of the meshes (a cell's border edges are seams, not open): [(key, p, q)]."""
    out = []
    for k, m in meshes_out.items():
        x0 = y0 = None
        if cell_of:
            x0, y0 = k[0] * cn.CELL, k[1] * cn.CELL
        for (i, j), uses in m.edges().items():
            if len(uses) != 1:
                continue
            p, q = m.V[i], m.V[j]
            if cell_of and ((abs(p[0] - x0) < 0.5 and abs(q[0] - x0) < 0.5) or (abs(p[0] - x0 - cn.CELL) < 0.5 and abs(q[0] - x0 - cn.CELL) < 0.5)
                            or (abs(p[1] - y0) < 0.5 and abs(q[1] - y0) < 0.5) or (abs(p[1] - y0 - cn.CELL) < 0.5 and abs(q[1] - y0 - cn.CELL) < 0.5)):
                continue
            out.append((k, tuple(p), tuple(q)))
    return out


def _closest(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 < 1e-12 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    return t, (a[0] + t * dx, a[1] + t * dy, a[2] + t * (b[2] - a[2]))


def _nearest_edge(p, edges, other=None):
    best, bd = None, float("inf")
    for e in edges:
        if other is not None and (e[1:] == other[1:] or e[1:] == other[2:0:-1]):
            continue
        _, c = _closest(p, e[1], e[2])
        d = math.hypot(c[0] - p[0], c[1] - p[1])
        if d <= REACH and abs(c[2] - p[2]) <= REACH_Z and d < bd:
            best, bd = e, d
    return best


def _span(e, toward):
    """The stretch of edge e WIDTH long round its point nearest `toward` (the whole edge when shorter)."""
    a, b = e[1], e[2]
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    if L <= WIDTH:
        return a, b
    t, _ = _closest(toward, a, b)
    h = WIDTH / 2 / L
    t0, t1 = max(0.0, t - h), min(1.0, t + h)
    if t1 - t0 < 2 * h:
        t0, t1 = (0.0, 2 * h) if t0 == 0.0 else (1.0 - 2 * h, 1.0)

    def at(t):
        return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]), a[2] + t * (b[2] - a[2]))
    return at(t0), at(t1)


def _cross2(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _segs_cross(p1, p2, q1, q2) -> bool:
    d1, d2 = _cross2(q1, q2, p1), _cross2(q1, q2, p2)
    d3, d4 = _cross2(p1, p2, q1), _cross2(p1, p2, q2)
    return d1 * d2 < 0 and d3 * d4 < 0


def _join(r, meshes_out, cell_of, key_box) -> str | None:
    """Bridge the two open edges a join names; None when bridged, else why not in plain words."""
    pa, pb = (tuple(map(float, p)) for p in r["points"])
    gap = min(float(r.get("gap") or GAP), MAX_GAP)
    edges = open_edges(meshes_out, cell_of)
    ea = _nearest_edge(pa, edges)
    if ea is None:
        return f"there is no open edge of the walking mesh within {REACH:.0f} of its first point"
    eb = _nearest_edge(pb, edges, ea)
    if eb is None:
        return f"there is no open edge of the walking mesh within {REACH:.0f} of its second point"
    a0, a1 = _span(ea, pb)
    b0, b1 = _span(eb, pa)
    if _segs_cross(a0, b0, a1, b1):
        b0, b1 = b1, b0
    ma = ((a0[0] + a1[0]) / 2, (a0[1] + a1[1]) / 2, (a0[2] + a1[2]) / 2)
    mb = ((b0[0] + b1[0]) / 2, (b0[1] + b1[1]) / 2, (b0[2] + b1[2]) / 2)
    d = math.hypot(mb[0] - ma[0], mb[1] - ma[1])
    dz = abs(mb[2] - ma[2])
    if d > gap:
        return f"the two edges are {d:.0f} apart, more than the {gap:.0f} the join allows"
    if dz > STEP:
        return f"the two edges are {dz:.0f} apart in height, more than a step ({STEP:.0f})"
    if d > 1e-6 and math.degrees(math.atan2(dz, d)) > cn.MAX_SLOPE_DEG:
        return f"the bridge would climb {math.degrees(math.atan2(dz, d)):.0f} degrees, steeper than one can walk"
    quad = [a0, a1, b1, b0]
    if cn.area2(quad) < 0:
        quad = quad[::-1]
    if abs(cn.area2(quad)) < 2 * cn.MIN_AREA:
        return "the two edges already meet"
    parts = convex_parts(quad) if not _convex(quad) else [quad]
    added = 0
    for part in parts:
        for k, m in meshes_out.items():
            q = part if not cell_of else cn.intersect(part, key_box(k))
            if q is not None:
                m.add_poly(q, cn_flags_new(), 0)
                added += 1
    return None if added else "the bridge falls outside the meshes it joins"


# ---- the build's two calls ---------------------------------------------------------------------------------------------

def _tris_of(nv) -> list:
    v = np.asarray(nv.verts, float)
    return [(v[t].tolist(), int(f)) for t, f in zip(nv.tris["v"].astype(int), nv.tris["flags"])]


def apply_exterior(mine: list[dict], rows: list[dict]) -> dict:
    """The exterior zones on the shipped cells (exterior_navmesh, before the seams are linked): each touched cell's
    NVNM replaced whole and its links opened (join_seams links it again). Returns the stats."""
    rows = [r for r in rows if (r.get("space") or "exterior") == "exterior"]
    if not rows:
        return {}
    by_cell = {tuple(n["cell"]): n for n in mine if n["space"] == "exterior"}
    meshes = {c: _tris_of(n["nv"]) for c, n in by_cell.items()}
    nb = {}
    for c, n in by_cell.items():
        v = np.asarray(n["nv"].verts, float)
        x0, y0 = c[0] * cn.CELL, c[1] * cn.CELL
        on = (np.abs(v[:, 0] - x0) < 0.5) | (np.abs(v[:, 0] - x0 - cn.CELL) < 0.5) | (np.abs(v[:, 1] - y0) < 0.5) | (np.abs(v[:, 1] - y0 - cn.CELL) < 0.5)
        nb[c] = v[on].tolist()
    done, st = apply(meshes, rows, cell_of=True, neighbours=nb)
    st["cells"] = 0
    for c, cell in sorted(done.items()):
        n = by_cell.get(c)
        if n is None:
            st["refused"].append(f"cell {c[0]},{c[1]}: a zone reaches it but the build does not ship it")
            continue
        if cell is None:
            continue
        n["nv"] = cn.to_nvnm(cell, n["nv"])
        n["joined"] = True
        n["nvmi"] = None
        st["cells"] += 1
    return st


def apply_interior(navs: list[dict], rows: list[dict]) -> dict:
    """A room's zones: the room's navmeshes joined into one (its first record kept), the zones applied, its links
    out of the room opened. `navs` is the room's list, changed in place. Returns the stats."""
    if not rows or not navs:
        return {}
    meshes = {0: [t for n in navs for t in _tris_of(n["nv"])]}
    done, st = apply(meshes, rows, cell_of=None)
    cell = done.get(0)
    if cell is None:
        st["refused"].append("the room's walking mesh is gone once the zones are applied")
        return st
    first = navs[0]
    tmpl = SimpleNamespace(world=0, grid_xy=None, cell=first["nv"].cell)
    first["nv"] = cn.to_nvnm(cell, tmpl)
    del navs[1:]
    st["merged"] = len(meshes)
    return st
