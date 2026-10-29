"""From ArgoniaNav's raw cell meshes to the NAVM and NAVI contract ArgoniaGen writes (NavmeshRecords.cs).

Per cell, in order: read the raw mesh (raw/cy+NNN.bin); split each open edge at every vertex lying on it (Recast's
detail meshes can leave a T-junction between polygons); split each open edge on a cell seam at the neighbour's seam
vertices, so both sides of a seam have the same segments; find each triangle's neighbours; link every seam edge to
the neighbour's edge with the same two ends when both ends are within SEAM_DZ in height (a Portal edge link, both
ways, so links are symmetric by construction); flag water (swim) and road (Preferred) triangles; build the lookup
grid; encode the NVNM (nvnm.py). Cells are read north to south with three rows of raw meshes held, nothing more.

Output (`<out>/navm/cy+NNN.jsonl.gz`, gzip with no timestamp; one line per cell that has a navmesh):
    {"x", "y", "formKey", "navm": base64 NAVM record (header and NVNM, uncompressed)}
and `<out>/navi.json`: {"schema": 1, "masters": MASTERS, "self": SELF_FILE, "navi": base64 NAVI record}, the NVMI in
NAVM FormID order. Every FormID in those bytes is written against MASTERS (index 0 Skyrim.esm; index 1, one past
the masters, the plugin itself), which NavmeshRecords.cs hands to Mutagen's parser; Mutagen maps them on write.

NAVM FormIDs: NAVM_FIRST + the cell's index in the terrain grid, row-major from the grid's south-west cell (the
terrain's CELL/LAND pairs end below 0x30000, the water's REFRs at 0x4E0400).
"""
from __future__ import annotations

import base64
import gzip
import json
import struct
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from tools.argonia_world import skyrim_units as su
from tools.navmesh import nvnm, params
from tools.navmesh.esm import subrecords

MASTERS = ["Skyrim.esm"]
SELF_FILE = "ArgoniaWorld.esm"
SELF = len(MASTERS)  # a plugin's own records carry the index one past its masters
NAVI_FID = 0x012FB4  # Skyrim.esm's Navmesh Info Map (index 0)
FORM_VERSION = 44  # the SSE Creation Kit's (Skyrim.esm's own records say 40)
NAVM_FIRST = 0x600000
WATER, ROAD = 1, 2  # ArgoniaNav's area ids (63 is ground)
EPS = 0.5  # units: a vertex this close to an open edge in plan lies on it


def fid(local: int) -> int:
    return (SELF << 24) | local


def record(sig: bytes, form_id: int, subs: bytes) -> bytes:
    return struct.pack("<4sIIIIHH", sig, len(subs), 0, form_id, 0, FORM_VERSION, 0) + subs


def navi_record(nvmis: list[bytes]) -> bytes:
    """NAVI: NVER 12, one NVMI per navmesh, an empty NVPP (no preferred-pathing table: Tamriel's roads are not ours)."""
    from tools.navmesh.esm import pack_subrecord
    subs = pack_subrecord(b"NVER", struct.pack("<I", nvnm.VERSION))
    subs += b"".join(pack_subrecord(b"NVMI", m) for m in nvmis)
    subs += pack_subrecord(b"NVPP", struct.pack("<II", 0, 0))
    return record(b"NAVI", NAVI_FID, subs)


@dataclass
class Mesh:
    x: int
    y: int
    verts: list  # [x, y, z] floats
    tris: list  # [a, b, c]
    area: list  # per triangle
    links: dict = field(default_factory=dict)  # (tri, slot) -> (neighbour cell, neighbour tri)


# ---- reading ----------------------------------------------------------------------------------------------------
def read_raw(path: Path):
    b = path.read_bytes()
    o = 0
    while o < len(b):
        x, y, nv, nt = struct.unpack_from("<iiii", b, o)
        o += 16
        v = np.frombuffer(b, "<f4", 3 * nv, o).reshape(nv, 3)
        o += 12 * nv
        t = np.frombuffer(b, np.dtype([("v", "<u2", 3), ("a", "u1")]), nt, o)
        o += 7 * nt
        yield Mesh(x, y, v.astype(np.float64).tolist(), t["v"].astype(int).tolist(), t["a"].astype(int).tolist())


def raw_row(raw: Path, cy: int) -> dict[int, Mesh]:
    p = raw / f"cy{cy:+04d}.bin"
    return {m.x: m for m in read_raw(p)} if p.exists() else {}


# ---- geometry ---------------------------------------------------------------------------------------------------
def edges(m: Mesh) -> dict[tuple[int, int], list[tuple[int, int]]]:
    e = defaultdict(list)
    for ti, t in enumerate(m.tris):
        for k in range(3):
            a, b = t[k], t[(k + 1) % 3]
            e[(min(a, b), max(a, b))].append((ti, k))
    return e


def _on_segment(p, a, b) -> float | None:
    """The parameter of p along a-b when p lies strictly inside it in plan, else None."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    ll = dx * dx + dy * dy
    if ll == 0:
        return None
    s = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / ll
    if s <= 1e-9 or s >= 1 - 1e-9:
        return None
    qx, qy = a[0] + s * dx - p[0], a[1] + s * dy - p[1]
    return s if qx * qx + qy * qy <= EPS * EPS else None


def split_open_edges(m: Mesh, points_for) -> int:
    """Split open edges at the points `points_for(a, b)` returns ([(s, vertex index)]); repeat until none."""
    n = 0
    while True:
        todo = {}
        for (u, w), uses in sorted(edges(m).items()):
            if len(uses) != 1:
                continue
            ti, k = uses[0]
            if ti in todo:
                continue
            a, b = m.tris[ti][k], m.tris[ti][(k + 1) % 3]
            pts = points_for(m, a, b)
            if pts:
                todo[ti] = (k, pts)
        if not todo:
            return n
        for ti, (k, pts) in sorted(todo.items()):
            t = m.tris[ti]
            a, b, c = t[k], t[(k + 1) % 3], t[(k + 2) % 3]
            chain = [a] + [v for _, v in sorted(pts)] + [b]
            new = [[chain[i], chain[i + 1], c] for i in range(len(chain) - 1)]
            m.tris[ti] = new[0]
            m.tris.extend(new[1:])
            m.area.extend([m.area[ti]] * (len(new) - 1))
            n += len(new) - 1


class VertexHash:
    """Plan buckets of a mesh's vertices, for the T-junction repair."""

    def __init__(self, m: Mesh, size: float = 64.0):
        self.size, self.b = size, defaultdict(list)
        for i, v in enumerate(m.verts):
            self.b[(int(v[0] // size), int(v[1] // size))].append(i)

    def near(self, a, b):
        s = self.size
        for gx in range(int(min(a[0], b[0]) // s) - 1, int(max(a[0], b[0]) // s) + 2):
            for gy in range(int(min(a[1], b[1]) // s) - 1, int(max(a[1], b[1]) // s) + 2):
                yield from self.b.get((gx, gy), ())


def repair_t_junctions(m: Mesh) -> int:
    vh = VertexHash(m)

    def pts(mm, a, b):
        va, vb = mm.verts[a], mm.verts[b]
        out = []
        for i in vh.near(va, vb):
            if i in (a, b):
                continue
            s = _on_segment(mm.verts[i], va, vb)
            if s is not None and abs(va[2] + s * (vb[2] - va[2]) - mm.verts[i][2]) <= params.WELD_Z:
                out.append((s, i))
        return out
    return split_open_edges(m, pts)


def seam_of(m: Mesh, a: int, b: int) -> str | None:
    """Which seam (W, E, S, N) an edge lies on, if both its ends are on one."""
    x0, y0 = su.cell_origin(m.x, m.y)
    va, vb = m.verts[a], m.verts[b]
    for name, i, val in (("W", 0, x0), ("E", 0, x0 + su.CELL_UNITS), ("S", 1, y0), ("N", 1, y0 + su.CELL_UNITS)):
        if va[i] == val and vb[i] == val:
            return name
    return None


OPP = {"W": "E", "E": "W", "S": "N", "N": "S"}
STEP = {"W": (-1, 0), "E": (1, 0), "S": (0, -1), "N": (0, 1)}


def seam_points(m: Mesh, side: str) -> list[tuple[float, float, float]]:
    """The ends of every open edge on a seam, sorted."""
    out = set()
    for (u, w), uses in edges(m).items():
        if len(uses) == 1 and seam_of(m, u, w) == side:
            out.add(tuple(m.verts[u]))
            out.add(tuple(m.verts[w]))
    return sorted(out)


def split_seams(m: Mesh, neighbour_points: dict[str, list]) -> int:
    """Insert the neighbours' seam vertices into this mesh's seam edges (heights interpolated along the edge)."""
    index = {tuple(v[:2]): i for i, v in enumerate(m.verts)}

    def pts(mm, a, b):
        side = seam_of(mm, a, b)
        if side is None:
            return []
        va, vb = mm.verts[a], mm.verts[b]
        out = []
        for p in neighbour_points.get(side, ()):
            s = _on_segment(p, va, vb)
            if s is None:
                continue
            key = (p[0], p[1])
            if key not in index:
                index[key] = len(mm.verts)
                mm.verts.append([p[0], p[1], va[2] + s * (vb[2] - va[2])])
            out.append((s, index[key]))
        return out
    return split_open_edges(m, pts)


def neighbours(m: Mesh) -> list[list[int]]:
    """Per triangle, per edge slot, the triangle across it or -1."""
    nb = [[-1, -1, -1] for _ in m.tris]
    for uses in edges(m).values():
        if len(uses) == 2:
            (t1, k1), (t2, k2) = uses
            nb[t1][k1], nb[t2][k2] = t2, t1
    return nb


def seam_edges(m: Mesh, side: str) -> dict[tuple, tuple[int, int, float, float]]:
    """Open edges on a seam keyed by their ends' plan positions (sorted): (tri, slot, z at key[0], z at key[1])."""
    out = {}
    for (u, w), uses in edges(m).items():
        if len(uses) == 1 and seam_of(m, u, w) == side:
            ti, k = uses[0]
            pu, pw = tuple(m.verts[u][:2]), tuple(m.verts[w][:2])
            (p, zp), (q, zq) = sorted([(pu, m.verts[u][2]), (pw, m.verts[w][2])])
            out[(p, q)] = (ti, k, zp, zq)
    return out


def link_seam(a: Mesh, b: Mesh, side: str) -> int:
    """Portal links across a's `side` seam and b's opposite one, both ways."""
    ea, eb = seam_edges(a, side), seam_edges(b, OPP[side])
    n = 0
    for key in sorted(ea.keys() & eb.keys()):
        ta, ka, za0, za1 = ea[key]
        tb, kb, zb0, zb1 = eb[key]
        if abs(za0 - zb0) <= params.SEAM_DZ and abs(za1 - zb1) <= params.SEAM_DZ:
            a.links[(ta, ka)] = ((b.x, b.y), tb)
            b.links[(tb, kb)] = ((a.x, a.y), ta)
            n += 1
    return n


# ---- the stitch -------------------------------------------------------------------------------------------------
@dataclass
class Grid:
    """Cell -> NAVM local FormID by the terrain grid's index (row-major from the south-west)."""
    gx0: int
    gy0: int
    gw: int

    def local(self, x: int, y: int) -> int:
        return NAVM_FIRST + (y - self.gy0) * self.gw + (x - self.gx0)

    def form_key(self, x: int, y: int) -> str:
        return f"{self.local(x, y):06X}:ArgoniaWorld.esm"


def finish(m: Mesh, grid: Grid, world_local: int) -> tuple[bytes, bytes, dict]:
    """The NVNM and NVMI bytes and the stats of one finished cell mesh."""
    nb = neighbours(m)
    order = sorted(m.links)
    link_index = {k: i for i, k in enumerate(order)}
    tris = np.zeros(len(m.tris), nvnm.TRI)
    pref = 0
    for ti, t in enumerate(m.tris):
        e = list(nb[ti])
        flags = nvnm.FOUND
        for k in range(3):
            if (ti, k) in link_index:
                e[k] = link_index[(ti, k)]
                flags |= nvnm.EDGE_LINK[k]
        if m.area[ti] == WATER:
            flags |= nvnm.WATER
        elif m.area[ti] == ROAD:
            flags |= nvnm.PREFERRED
            pref += 1
        tris[ti] = (t, e, flags, 0)
    links = np.zeros(len(order), nvnm.LINK)
    for i, k in enumerate(order):
        (cx, cy), tj = m.links[k]
        links[i] = (nvnm.PORTAL, fid(grid.local(cx, cy)), tj)
    verts = np.asarray(m.verts, np.float32)
    n = nvnm.Nvnm(fid(world_local), (m.x, m.y), None, verts, tris, links)
    nvnm.build_grid(n)
    centre = verts.mean(axis=0)  # vanilla's NVMI approx location: the vertex mean (12,815 of 12,817 Tamriel)
    edge_navms = sorted({int(x) for x in links["navm"]})
    preferred = pref / len(m.tris) if m.tris else 0.0  # vanilla's Preferred %: the share of Preferred triangles
    mi = nvnm.nvmi(fid(grid.local(m.x, m.y)), centre, edge_navms, [], fid(world_local), (m.x, m.y),
                   preferred=preferred)
    stats = {"tris": len(m.tris), "verts": len(m.verts), "links": len(order),
             "water": int(sum(1 for a in m.area if a == WATER)), "road": pref}
    return nvnm.encode(n), mi, stats


def run(out: Path, box, grid: Grid, world_local: int) -> dict:
    """Stitch every raw cell of `box` under out/raw into out/navm and out/navi.json; returns the totals."""
    raw = out / "raw"
    dest = out / "navm"
    dest.mkdir(parents=True, exist_ok=True)
    for old in dest.glob("cy*.jsonl.gz"):
        old.unlink()
    x0, y0, x1, y1 = box
    rows: dict[int, dict[int, Mesh]] = {}
    seam_pts: dict[int, dict[int, dict[str, list]]] = {}
    done: dict[int, dict[int, Mesh]] = {}
    nvmis: list[tuple[int, bytes]] = []
    tot = defaultdict(int)

    def load(cy):
        if cy not in rows and y0 <= cy <= y1:
            rows[cy] = {x: m for x, m in raw_row(raw, cy).items() if m.tris}
            for m in rows[cy].values():
                tot["t_junction_splits"] += repair_t_junctions(m)
            seam_pts[cy] = {x: {s: seam_points(m, s) for s in "WESN"} for x, m in rows[cy].items()}

    def flush(cy):
        lines = []
        for x, m in sorted(done.pop(cy, {}).items()):
            nv, mi, st = finish(m, grid, world_local)
            for k, v in st.items():
                tot[k] += v
            tot["cells"] += 1
            from tools.navmesh.esm import pack_subrecord
            rec = record(b"NAVM", fid(grid.local(x, cy)), pack_subrecord(b"NVNM", nv))
            lines.append(json.dumps({"x": x, "y": cy, "formKey": grid.form_key(x, cy),
                                     "navm": base64.b64encode(rec).decode("ascii")}, sort_keys=True))
            nvmis.append((grid.local(x, cy), mi))
        if lines:
            with open(dest / f"cy{cy:+04d}.jsonl.gz", "wb") as f, gzip.GzipFile(fileobj=f, mode="wb", mtime=0, filename="") as z:
                z.write(("\n".join(lines) + "\n").encode("ascii"))

    for cy in range(y1, y0 - 1, -1):  # north to south
        for r in (cy + 1, cy, cy - 1):
            load(r)
        row = rows[cy]
        for x, m in sorted(row.items()):
            pts = {}
            for side, (dx, dy) in STEP.items():
                nbr = seam_pts.get(cy + dy, {}).get(x + dx)
                if nbr:
                    pts[side] = nbr[OPP[side]]
            tot["seam_splits"] += split_seams(m, pts)
        for x, m in sorted(row.items()):  # links within the row, then to the finished row to the north
            if x + 1 in row:
                tot["seam_links"] += link_seam(m, row[x + 1], "E")
            if x in done.get(cy + 1, {}):
                tot["seam_links"] += link_seam(m, done[cy + 1][x], "N")
        done[cy] = row
        flush(cy + 1)
        rows.pop(cy + 1, None)
        seam_pts.pop(cy + 1, None)
    flush(y0)
    nvmis.sort()
    (out / "navi.json").write_text(json.dumps({
        "schema": 1, "masters": MASTERS, "self": SELF_FILE, "count": len(nvmis),
        "navi": base64.b64encode(navi_record([b for _, b in nvmis])).decode("ascii")}, sort_keys=True) + "\n")
    return dict(tot)


def read_navm(out: Path):
    """Every (x, y, formKey, Nvnm) written under out/navm, north to south."""
    for p in sorted((out / "navm").glob("cy*.jsonl.gz"), key=lambda p: -int(p.name[2:6])):
        with gzip.open(p, "rt", encoding="ascii") as f:
            for line in f:
                d = json.loads(line)
                rec = base64.b64decode(d["navm"])
                yield d["x"], d["y"], d["formKey"], nvnm.decode(dict(subrecords(rec[24:]))[b"NVNM"])
