"""NVNM, the navmesh geometry subrecord of a Skyrim SE NAVM, and NVMI, its entry in the NAVI: the codec.

The layout is the one in docs/research/journals/navmesh.md (xEdit's `wbNVNM`, tes4skyrim's `from_pgrd.py` and
`edge_links.py`, checked byte for byte against Skyrim.esm by `python -m tools.navmesh vanilla`). Every array has
a u32 count; integers little-endian:

    u32 version (12); u32 CRC "PathingCell" 0xA5E9A03C; FormID parent world (0 for an interior);
      exterior: s16 grid Y, s16 grid X | interior: FormID parent cell
    vertices   n x (f32 x, y, z), world units
    triangles  n x (u16 v0, v1, v2; s16 edge 0-1, 1-2, 2-0; u16 flags; u16 cover flags)
               an edge is the neighbour triangle, -1 for none, or (flag bit 0/1/2 set) an index into edge links
    edge links n x (u32 type, FormID navmesh, s16 triangle)   type 0 portal, 1 ledge up, 2 ledge down
    door tris  n x (s16 triangle, u32 CRC "PathingDoor" 0xE48B73F3, FormID door REFR), sorted by (triangle, door)
    cover tris n x s16 triangle
    grid       u32 divisor; f32 cell width, cell height; f32 min x, y, z, max x, y, z;
               divisor^2 x (u32 count, count x s16 triangle), rows from min y, columns from min x

Floats are kept as their f32 bit patterns (numpy float32), so decode then encode gives the same bytes.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass, field

import numpy as np

VERSION = 12
PATHING_CELL = 0xA5E9A03C
PATHING_DOOR = 0xE48B73F3

# triangle flags (xEdit wbNavmeshTriangleFlags)
EDGE_LINK = (0x0001, 0x0002, 0x0004)
DELETED = 0x0008
NO_LARGE_CREATURES = 0x0010
OVERLAPPING = 0x0020
PREFERRED = 0x0040
WATER = 0x0200
DOOR = 0x0400
FOUND = 0x0800

PORTAL, LEDGE_UP, LEDGE_DOWN = 0, 1, 2

TRI = np.dtype([("v", "<u2", 3), ("e", "<i2", 3), ("flags", "<u2"), ("cover", "<u2")])  # 16 bytes
LINK = np.dtype([("type", "<u4"), ("navm", "<u4"), ("tri", "<i2")])  # 10 bytes
DOOR_TRI = np.dtype([("tri", "<i2"), ("crc", "<u4"), ("door", "<u4")])  # 10 bytes


@dataclass
class Nvnm:
    world: int  # raw FormID of the parent worldspace, 0 for an interior
    grid_xy: tuple[int, int] | None  # exterior (x, y)
    cell: int | None  # interior parent cell
    verts: np.ndarray  # (n, 3) float32
    tris: np.ndarray  # (n,) TRI
    links: np.ndarray = field(default_factory=lambda: np.zeros(0, LINK))
    doors: np.ndarray = field(default_factory=lambda: np.zeros(0, DOOR_TRI))
    cover: np.ndarray = field(default_factory=lambda: np.zeros(0, "<i2"))
    divisor: int = 0
    cell_size: np.ndarray = field(default_factory=lambda: np.zeros(2, "<f4"))
    bounds: np.ndarray = field(default_factory=lambda: np.zeros(6, "<f4"))  # min x, y, z, max x, y, z
    grid: list = field(default_factory=list)  # divisor^2 arrays of s16
    version: int = VERSION
    crc: int = PATHING_CELL


def decode(b: bytes) -> Nvnm:
    o = 0

    def u32():
        nonlocal o
        v = struct.unpack_from("<I", b, o)[0]
        o += 4
        return v

    def arr(dt, n):
        nonlocal o
        a = np.frombuffer(b, dtype=dt, count=n, offset=o).copy()
        o += a.nbytes
        return a

    version, crc, world = u32(), u32(), u32()
    if world:
        gy, gx = struct.unpack_from("<hh", b, o)
        o += 4
        grid_xy, cell = (gx, gy), None
    else:
        grid_xy, cell = None, u32()
    verts = arr("<f4", 3 * u32()).reshape(-1, 3)
    tris = arr(TRI, u32())
    links = arr(LINK, u32())
    doors = arr(DOOR_TRI, u32())
    cover = arr("<i2", u32())
    divisor = u32()
    cell_size = arr("<f4", 2)
    bounds = arr("<f4", 6)
    grid = [arr("<i2", u32()) for _ in range(divisor * divisor)]
    if o != len(b):
        raise ValueError(f"NVNM: {len(b) - o} bytes left after the grid")
    return Nvnm(world, grid_xy, cell, verts, tris, links, doors, cover, divisor, cell_size, bounds, grid, version, crc)


def encode(n: Nvnm) -> bytes:
    out = [struct.pack("<III", n.version, n.crc, n.world)]
    if n.world:
        out.append(struct.pack("<hh", n.grid_xy[1], n.grid_xy[0]))
    else:
        out.append(struct.pack("<I", n.cell))
    for a, dt in ((n.verts.astype("<f4", copy=False).reshape(-1), None), (n.tris, TRI), (n.links, LINK),
                  (n.doors, DOOR_TRI), (n.cover, "<i2")):
        cnt = len(a) // 3 if dt is None else len(a)
        out.append(struct.pack("<I", cnt))
        out.append(np.ascontiguousarray(a).tobytes())
    out.append(struct.pack("<I", n.divisor))
    out.append(n.cell_size.astype("<f4").tobytes() + n.bounds.astype("<f4").tobytes())
    for c in n.grid:
        out.append(struct.pack("<I", len(c)) + np.asarray(c, "<i2").tobytes())
    return b"".join(out)


# ---- the lookup grid ------------------------------------------------------------------------------------------
def divisor_for(triangles: int) -> int:
    """The lookup grid's divisor as vanilla sets it, by triangle count: 1 under 17, 2 under 50, then one more per 50
    triangles up to 12 (all 12,817 Tamriel NAVMs of Skyrim.esm; tes4skyrim's span rule fits 2,721 of them)."""
    return 1 if triangles < 17 else 2 if triangles < 50 else min(12, triangles // 50 + 2)


def _tri_hits_rect(xs, ys, x0, y0, x1, y1) -> bool:
    """Separating-axis test in plan (touching counts)."""
    if max(xs) < x0 or min(xs) > x1 or max(ys) < y0 or min(ys) > y1:
        return False
    corners = ((x0, y0), (x1, y0), (x1, y1), (x0, y1))
    for k in range(3):
        ax, ay, bx, by = xs[k], ys[k], xs[(k + 1) % 3], ys[(k + 1) % 3]
        nx, ny = by - ay, ax - bx
        side = nx * (xs[(k + 2) % 3] - ax) + ny * (ys[(k + 2) % 3] - ay)
        if all((nx * (px - ax) + ny * (py - ay)) * side < 0 for px, py in corners):
            return False
    return True


def build_grid(n: Nvnm, divisor: int | None = None) -> None:
    """Set bounds, divisor, cell size and the lookup grid from the vertices and triangles: every triangle listed in
    every bucket its plan shape overlaps (the engine scans only the bucket under a point)."""
    v = n.verts.astype(np.float32)
    lo, hi = v.min(axis=0), v.max(axis=0)
    n.bounds = np.concatenate([lo, hi]).astype("<f4")
    span = (float(hi[0] - lo[0]) or 1.0, float(hi[1] - lo[1]) or 1.0)
    g = divisor or divisor_for(len(n.tris))
    cw, ch = np.float32(span[0] / g), np.float32(span[1] / g)
    n.divisor, n.cell_size = g, np.array([cw, ch], "<f4")
    cells: list[list[int]] = [[] for _ in range(g * g)]
    x0, y0 = float(lo[0]), float(lo[1])
    cwf, chf = float(cw), float(ch)
    for ti, t in enumerate(n.tris["v"]):
        xs = [float(v[t[k], 0]) for k in range(3)]
        ys = [float(v[t[k], 1]) for k in range(3)]
        r0 = min(max(int((min(ys) - y0) // chf), 0), g - 1)
        r1 = min(max(int((max(ys) - y0) // chf), 0), g - 1)
        c0 = min(max(int((min(xs) - x0) // cwf), 0), g - 1)
        c1 = min(max(int((max(xs) - x0) // cwf), 0), g - 1)
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                bx, by = x0 + c * cwf, y0 + r * chf
                if r0 == r1 and c0 == c1 or _tri_hits_rect(xs, ys, bx, by, bx + cwf, by + chf):
                    cells[r * g + c].append(ti)
    n.grid = [np.array(c, "<i2") for c in cells]


# ---- NVMI, one navmesh's entry in the NAVI ----------------------------------------------------------------------
def nvmi(navm: int, centre, edge_navms: list[int], doors: list[int], world: int, grid_xy: tuple[int, int],
         flags: int = 0, preferred: float = 0.0) -> bytes:
    """xEdit wbStructSK(NVMI): navmesh, flags, approx location, preferred %, edge links (sorted), preferred edge
    links, door links (CRC, door), has-island-data 0, pathing cell (CRC, world, grid y, grid x)."""
    b = [struct.pack("<II3ff", navm, flags, *[float(c) for c in centre], preferred)]
    el = sorted(set(edge_navms))
    b.append(struct.pack(f"<I{len(el)}I", len(el), *el))
    b.append(struct.pack("<I", 0))
    ds = sorted(set(doors))
    b.append(struct.pack("<I", len(ds)) + b"".join(struct.pack("<II", PATHING_DOOR, d) for d in ds))
    b.append(struct.pack("<BIIhh", 0, PATHING_CELL, world, grid_xy[1], grid_xy[0]))
    return b"".join(b)
