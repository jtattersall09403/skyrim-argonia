"""The collision of a Skyrim SE mesh (NIF 20.2.0.7, user version 12, stream 83/100) as triangles in the mesh's units.

Only the blocks on the way to collision are read; every other block is skipped by its size (the header lists every
block's size from 20.2.0.5). The layout is niftools' `nif.xml` (BSD-3, read as a spec): the header; NiObjectNET,
NiAVObject and NiNode for the node tree and its transforms; bhkCollisionObject (and the P/SP variants) -> the body
(bhkRigidBody/T: its layer, and for T its translation and rotation) -> shapes: bhkMoppBvTreeShape, bhkListShape,
bhkTransformShape, bhkConvexTransformShape, bhkCompressedMeshShape (+ data: chunks with their transforms, big tris),
bhkPackedNiTriStripsShape (+ hkPackedNiTriStripsData), bhkConvexVerticesShape (hull), bhkBoxShape, bhkCapsuleShape
(as its bounding box). Havok works in its own units; HAVOK_SCALE turns them into the game's.

    collision(data) -> Collision(tris (n, 3, 3) float64 in mesh units, layers per triangle, tally of skipped kinds)
"""
from __future__ import annotations

import math
import struct
from dataclasses import dataclass, field

import numpy as np

HAVOK_SCALE = 69.99125  # Skyrim: one Havok unit in game units (nif.xml's #HAVOK_SCALE# for Skyrim)
NODE_SUFFIX = "Node"  # NiNode and every subclass (BSFadeNode, BSMultiBoundNode, BSLeafAnimNode, ...) begin as NiNode
NOT_NODES = {"BSFurnitureMarkerNode"}  # extra data, named like a node
COLLISION_OBJECTS = {"bhkCollisionObject", "bhkSPCollisionObject", "bhkPCollisionObject", "bhkBlendCollisionObject"}
# Skyrim collision layers that stand in an actor's way or carry it (SkyrimLayer): static, animstatic, trees, props,
# terrain, ground, stair helper, plus clutter as an obstacle; triggers, water, non-collidable, camera and pick layers
# are left out.
SOLID_LAYERS = {1, 2, 4, 9, 10, 13, 17, 31}


@dataclass
class Collision:
    tris: np.ndarray  # (n, 3, 3) mesh units
    layers: np.ndarray  # (n,) the body's SkyrimLayer per triangle
    skipped: dict = field(default_factory=dict)


class Nif:
    def __init__(self, b: bytes):
        self.b = b
        nl = b.index(b"\n")
        if not b.startswith(b"Gamebryo File Format"):
            raise ValueError("not a NIF")
        o = nl + 1
        self.version, endian, self.user, nblocks = struct.unpack_from("<IBII", b, o)
        o += 13
        if self.version != 0x14020007 or endian != 1:
            raise ValueError(f"NIF version {self.version:#x} unsupported")
        self.bsver = struct.unpack_from("<I", b, o)[0]
        o += 4
        for _ in range(3):  # author, process script, export script (byte-length strings)
            o += 1 + b[o]
        if self.bsver >= 103:
            o += 1 + b[o]
        ntypes = struct.unpack_from("<H", b, o)[0]
        o += 2
        types = []
        for _ in range(ntypes):
            n = struct.unpack_from("<I", b, o)[0]
            types.append(b[o + 4:o + 4 + n].decode("ascii"))
            o += 4 + n
        idx = struct.unpack_from(f"<{nblocks}H", b, o)
        o += 2 * nblocks
        self.types = [types[i & 0x7FFF] for i in idx]
        sizes = struct.unpack_from(f"<{nblocks}I", b, o)
        o += 4 * nblocks
        nstr, _ = struct.unpack_from("<II", b, o)
        o += 8
        for _ in range(nstr):
            o += 4 + struct.unpack_from("<I", b, o)[0]
        ngroups = struct.unpack_from("<I", b, o)[0]
        o += 4 + 4 * ngroups
        self.offsets = []
        for s in sizes:
            self.offsets.append(o)
            o += s
        self.sizes = sizes

    def u32(self, o):
        return struct.unpack_from("<I", self.b, o)[0]

    def i32(self, o):
        return struct.unpack_from("<i", self.b, o)[0]

    def f(self, o, n=1):
        v = struct.unpack_from(f"<{n}f", self.b, o)
        return v if n > 1 else v[0]


def _quat(x, y, z, w) -> np.ndarray:
    n = math.sqrt(x * x + y * y + z * z + w * w) or 1.0
    x, y, z, w = x / n, y / n, z / n, w / n
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def _affine(r: np.ndarray, t, s: float = 1.0) -> np.ndarray:
    m = np.eye(4)
    m[:3, :3] = r * s
    m[:3, 3] = t
    return m


def _hull_tris(pts: np.ndarray) -> np.ndarray:
    """The triangles of the convex hull of a small point set (a convex-vertices shape): every face plane through
    three points with all points on one side, fanned in angular order. O(n^4) worst case; shapes have tens of points."""
    pts = np.unique(np.round(pts, 4), axis=0)
    n = len(pts)
    if n < 4:
        return np.zeros((0, 3, 3))
    out, seen = [], set()
    centre = pts.mean(axis=0)
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                nrm = np.cross(pts[j] - pts[i], pts[k] - pts[i])
                ln = np.linalg.norm(nrm)
                if ln < 1e-9:
                    continue
                nrm /= ln
                d = (pts - pts[i]) @ nrm
                if d.max() > 1e-4 and d.min() < -1e-4:
                    continue
                if (pts[i] - centre) @ nrm < 0:
                    nrm = -nrm
                key = tuple(np.round(np.append(nrm, nrm @ pts[i]), 3))
                if key in seen:
                    continue
                seen.add(key)
                on = pts[np.abs((pts - pts[i]) @ nrm) <= 1e-4]
                c = on.mean(axis=0)
                u = on[0] - c
                u /= np.linalg.norm(u) or 1.0
                v = np.cross(nrm, u)
                order = np.argsort(np.arctan2((on - c) @ v, (on - c) @ u))
                ring = on[order]
                for m in range(1, len(ring) - 1):
                    out.append([ring[0], ring[m], ring[m + 1]])
    return np.array(out) if out else np.zeros((0, 3, 3))


def _box_tris(lo, hi) -> np.ndarray:
    c = np.array([[(lo, hi)[i & 1][0], (lo, hi)[i >> 1 & 1][1], (lo, hi)[i >> 2 & 1][2]] for i in range(8)])
    faces = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
    return np.array([[c[a], c[b], c[d]] for a, b, cc, d in faces for a, b, d in ((a, b, cc), (a, cc, d))])


class _Reader:
    def __init__(self, nif: Nif):
        self.n = nif
        self.tris: list[np.ndarray] = []
        self.layers: list[int] = []
        self.skipped: dict[str, int] = {}

    def skip(self, kind: str):
        self.skipped[kind] = self.skipped.get(kind, 0) + 1

    # ---- the node tree ----
    def av_object(self, i):
        """(local affine, collision ref, children) of a NiAVObject block (NiNode children only for nodes)."""
        n, o = self.n, self.n.offsets[i]
        o += 4  # name
        o += 4 + 4 * n.u32(o)  # extra data list
        o += 4  # controller
        o += 4 if n.bsver > 26 else 2  # flags
        t = n.f(o, 3)
        rot = np.array(n.f(o + 12, 9)).reshape(3, 3).T  # nif.xml Matrix33: m11 m21 m31 m12 ... (column by column)
        s = n.f(o + 48)
        o += 52
        if n.bsver <= 34:
            o += 4 + 4 * n.u32(o)
        coll = n.i32(o)
        o += 4
        kids = []
        if self._is_node(i):
            kids = list(struct.unpack_from(f"<{n.u32(o)}i", n.b, o + 4))
        return _affine(rot, t, s), coll, kids

    def walk(self, i, parent: np.ndarray, seen: set):
        if i < 0 or i in seen or i >= len(self.n.types):
            return
        seen.add(i)
        m, coll, kids = self.av_object(i)
        world = parent @ m
        if coll >= 0:
            self.collision_object(coll, world)
        for k in kids:
            if k >= 0 and k < len(self.n.types) and self._is_av(k):
                self.walk(k, world, seen)

    def _is_node(self, k):
        t = self.n.types[k]
        return t.endswith(NODE_SUFFIX) and t not in NOT_NODES

    def _is_av(self, k):
        t = self.n.types[k]
        return self._is_node(k) or t in ("BSTriShape", "BSSubIndexTriShape", "BSMeshLODTriShape",
                                                 "BSDynamicTriShape", "NiTriShape", "NiTriStrips")

    # ---- collision ----
    def collision_object(self, i, world):
        n = self.n
        t = n.types[i]
        if t not in COLLISION_OBJECTS:
            self.skip(t)
            return
        o = n.offsets[i] + 4 + 2  # target, flags
        body = n.i32(o)
        if body < 0:
            return
        bt = n.types[body]
        if bt not in ("bhkRigidBody", "bhkRigidBodyT"):  # a phantom is not solid
            self.skip(bt)
            return
        b = n.offsets[body]
        shape, layer = n.i32(b), n.b[b + 4]
        m = world @ np.diag([HAVOK_SCALE, HAVOK_SCALE, HAVOK_SCALE, 1.0])
        if bt == "bhkRigidBodyT":
            tr = np.array(n.f(b + 52, 3))
            q = n.f(b + 68, 4)
            m = m @ _affine(_quat(*q), tr)
        self.shape(shape, m, layer)

    def emit(self, tris: np.ndarray, m: np.ndarray, layer: int):
        if not len(tris):
            return
        p = tris.reshape(-1, 3) @ m[:3, :3].T + m[:3, 3]
        self.tris.append(p.reshape(-1, 3, 3))
        self.layers += [layer] * len(tris)

    def shape(self, i, m, layer):
        n = self.n
        if i < 0:
            return
        t, o = n.types[i], n.offsets[i]
        if t == "bhkMoppBvTreeShape":
            self.shape(n.i32(o), m, layer)
        elif t in ("bhkTransformShape", "bhkConvexTransformShape"):
            mm = np.array(n.f(o + 4 + 4 + 4 + 8, 16)).reshape(4, 4).T
            self.shape(n.i32(o), m @ mm, layer)
        elif t == "bhkListShape":
            for k in range(n.u32(o)):
                self.shape(n.i32(o + 4 + 4 * k), m, layer)
        elif t == "bhkConvexListShape":
            for k in range(n.u32(o)):
                self.shape(n.i32(o + 4 + 4 * k), m, layer)
        elif t == "bhkCompressedMeshShape":
            self.cms(n.i32(o + 4 + 4 + 4 + 4 + 16 + 4 + 16), m, layer)
        elif t == "bhkPackedNiTriStripsShape":
            self.packed(n.i32(o + 4 + 4 + 4 + 4 + 16 + 4 + 16), m, layer)
        elif t == "bhkConvexVerticesShape":
            o += 4 + 4 + 24
            nv = n.u32(o)
            v = np.array(n.f(o + 4, 4 * nv) if nv > 1 else [n.f(o + 4, 4)]).reshape(-1, 4)[:, :3]
            self.emit(_hull_tris(v), m, layer)
        elif t == "bhkBoxShape":
            d = np.array(n.f(o + 4 + 4 + 8, 3))
            self.emit(_box_tris(-d, d), m, layer)
        elif t == "bhkCapsuleShape":
            o += 4 + 4 + 8
            a, r1, b, r2 = np.array(n.f(o, 3)), n.f(o + 12), np.array(n.f(o + 16, 3)), n.f(o + 28)
            r = max(r1, r2, n.f(o - 12))
            self.emit(_box_tris(np.minimum(a, b) - r, np.maximum(a, b) + r), m, layer)
        elif t == "bhkSphereShape":
            r = n.f(o + 4)
            self.emit(_box_tris(np.full(3, -r), np.full(3, r)), m, layer)
        else:
            self.skip(t)

    def cms(self, i, m, layer):
        n = self.n
        if i < 0 or n.types[i] != "bhkCompressedMeshShapeData":
            return
        o = n.offsets[i] + 4 * 5 + 32 + 1 + 1  # bits, masks, error; aabb; welding type, material type
        for _ in range(3):  # materials 32, 16, 8
            o += 4 + 4 * n.u32(o)
        o += 4 + 8 * n.u32(o)  # chunk materials
        o += 4  # named materials
        nt = n.u32(o)
        xf = []
        for k in range(nt):
            tr = np.array(n.f(o + 4 + 32 * k, 3))
            q = n.f(o + 4 + 32 * k + 16, 4)
            xf.append(_affine(_quat(*q), tr))
        o += 4 + 32 * nt
        nbv = n.u32(o)
        bigv = np.array(n.f(o + 4, 4 * nbv)).reshape(-1, 4)[:, :3] if nbv > 1 else (
            np.array([n.f(o + 4, 4)])[:, :3] if nbv else np.zeros((0, 3)))
        o += 4 + 16 * nbv
        nbt = n.u32(o)
        big = [struct.unpack_from("<3H", n.b, o + 4 + 12 * k) for k in range(nbt)]
        o += 4 + 12 * nbt
        if big:
            self.emit(bigv[np.array(big)], m, layer)
        nch = n.u32(o)
        o += 4
        geo = []
        for _ in range(nch):
            ct = np.array(n.f(o, 3))
            o += 16
            _, ref, ti = struct.unpack_from("<IHH", n.b, o)
            o += 8
            nv = n.u32(o)
            v = np.frombuffer(n.b, "<u2", nv, o + 4).reshape(-1, 3).astype(np.float64) / 1000.0 + ct
            o += 4 + 2 * nv
            ni = n.u32(o)
            idx = np.frombuffer(n.b, "<u2", ni, o + 4).astype(np.int64)
            o += 4 + 2 * ni
            ns = n.u32(o)
            strips = struct.unpack_from(f"<{ns}H", n.b, o + 4)
            o += 4 + 2 * ns
            o += 4 + 2 * n.u32(o)  # welding
            if nv == 0 and ref != 0xFFFF and ref < len(geo):
                v, idx, strips = geo[ref]
            geo.append((v, idx, strips))
            tris, p = [], 0
            for s in strips:
                for k in range(s - 2):
                    a, b, c = idx[p + k], idx[p + k + 1], idx[p + k + 2]
                    tris.append((a, b, c) if k % 2 == 0 else (a, c, b))
                p += s
            for k in range(p, len(idx) - 2, 3):
                tris.append((idx[k], idx[k + 1], idx[k + 2]))
            tris = [t for t in tris if len(set(t)) == 3]
            if tris and len(v):
                self.emit(v[np.array(tris)], m @ (xf[ti] if ti < len(xf) else np.eye(4)), layer)

    def packed(self, i, m, layer):
        n = self.n
        if i < 0 or n.types[i] != "hkPackedNiTriStripsData":
            return
        o = n.offsets[i]
        nt = n.u32(o)
        tri = np.array([struct.unpack_from("<3H", n.b, o + 4 + 8 * k) for k in range(nt)], np.int64).reshape(-1, 3)
        o += 4 + 8 * nt
        nv = n.u32(o)
        comp = n.b[o + 4]
        o += 5
        if comp:
            v = np.frombuffer(n.b, "<f2", 3 * nv, o).astype(np.float64).reshape(-1, 3)
        else:
            v = np.frombuffer(n.b, "<f4", 3 * nv, o).astype(np.float64).reshape(-1, 3)
        if len(tri) and len(v):
            self.emit(v[tri], m, layer)


def collision(data: bytes) -> Collision:
    nif = Nif(data)
    r = _Reader(nif)
    roots = [i for i, t in enumerate(nif.types) if r._is_av(i)]
    seen: set = set()
    for i in roots[:1] + roots[1:]:  # the root first; any other unparented tree after
        r.walk(i, np.eye(4), seen)
    tris = np.concatenate(r.tris) if r.tris else np.zeros((0, 3, 3))
    return Collision(tris, np.array(r.layers, np.uint8), r.skipped)
