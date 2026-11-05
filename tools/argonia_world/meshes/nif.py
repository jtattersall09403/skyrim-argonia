"""A Skyrim SE NIF (20.2.0.7, BS stream 100) read into blocks and written back byte-exact (lane 1.15-r6-mesh-patcher).

Only what the mesh patcher touches is decoded: the header's block sizes and string table (shape names), the
BSLightingShaderProperty fields (shader flags 1/2, emissive colour and multiple, texture clamp, lighting effect 1, the
texture set ref), BSShaderTextureSet slots, and BSTriShape vertex data (positions, half-float UVs, vertex colours,
triangles). Layout from niftools' nif.xml (BSD-3, read as a spec), the same offsets as vegetation/leaf_hue.py.
Every other block is carried as bytes; `to_bytes()` of an unedited file equals its input.
"""
from __future__ import annotations

import struct

import numpy as np

SHAPES = ("BSTriShape", "BSMeshLODTriShape", "BSSubIndexTriShape")
# SLSF1 / SLSF2 bits by name (nif.xml SkyrimShaderPropertyFlags1/2): only those the patch table names
F1 = {"Specular": 0, "Skinned": 1, "Model_Space_Normals": 12, "Own_Emit": 22, "Remappable_Textures": 24,
      "Decal": 26, "ZBuffer_Test": 31}
F2 = {"ZBuffer_Write": 0, "Double_Sided": 4, "Vertex_Colors": 5, "Glow_Map": 6, "Tree_Anim": 29,
      "Soft_Lighting": 25, "Rim_Lighting": 26, "Back_Lighting": 27, "Effect_Lighting": 30}


class Nif:
    def __init__(self, b: bytes):
        if not b.startswith(b"Gamebryo File Format"):
            raise ValueError("not a NIF")
        o = b.index(b"\n") + 1
        ver, endian, _user, nb = struct.unpack_from("<IBII", b, o)
        o += 13
        bsver, = struct.unpack_from("<I", b, o)
        o += 4
        if ver != 0x14020007 or endian != 1 or bsver != 100:
            raise ValueError(f"NIF {ver:#x} bs {bsver}: only Skyrim SE (bs 100)")
        for _ in range(3):
            o += 1 + b[o]
        nt, = struct.unpack_from("<H", b, o)
        o += 2
        types = []
        for _ in range(nt):
            n, = struct.unpack_from("<I", b, o)
            types.append(b[o + 4:o + 4 + n].decode("latin-1"))
            o += 4 + n
        idx = struct.unpack_from(f"<{nb}H", b, o)
        o += 2 * nb
        self.types = [types[i & 0x7FFF] for i in idx]
        self.head = b[:o]
        sizes = struct.unpack_from(f"<{nb}I", b, o)
        o += 4 * nb
        m0 = o
        ns, _ = struct.unpack_from("<II", b, o)
        o += 8
        self.strings = []
        for _ in range(ns):
            n, = struct.unpack_from("<I", b, o)
            self.strings.append(b[o + 4:o + 4 + n].decode("latin-1"))
            o += 4 + n
        ng, = struct.unpack_from("<I", b, o)
        o += 4 + 4 * ng
        self.mid = b[m0:o]
        self.blocks = []
        for s in sizes:
            self.blocks.append(bytearray(b[o:o + s]))
            o += s
        self.foot = b[o:]

    def to_bytes(self) -> bytes:
        return (self.head + struct.pack(f"<{len(self.blocks)}I", *(len(x) for x in self.blocks)) + self.mid
                + b"".join(bytes(x) for x in self.blocks) + self.foot)

    # ---- shapes ----------------------------------------------------------------------------------------------------
    def shapes(self) -> list["Shape"]:
        return [Shape(self, i) for i, t in enumerate(self.types) if t in SHAPES]

    def name(self, i: int) -> str:
        k, = struct.unpack_from("<i", self.blocks[i], 0)
        return self.strings[k] if 0 <= k < len(self.strings) else ""


class Shape:
    """One BSTriShape and its BSLightingShaderProperty (None for an effect shader) and texture set."""

    def __init__(self, nif: Nif, i: int):
        self.nif, self.i = nif, i
        b = nif.blocks[i]
        self.name = nif.name(i)
        ne, = struct.unpack_from("<I", b, 4)
        q = 8 + 4 * ne + 4 + 4 + 12 + 36 + 4 + 4 + 16  # extra data, controller, flags, transform, collision, sphere
        _skin, self.shader, self.alpha_ref = struct.unpack_from("<iii", b, q)
        self._shader_at = q + 4
        q += 12
        self.desc, = struct.unpack_from("<Q", b, q)
        self.ntri, self.nv = struct.unpack_from("<HH", b, q + 8)
        self.vdata = q + 16
        self.vsize = (self.desc & 0xF) * 4
        self.attrs = (self.desc >> 44) & 0xFFF
        ok = 0 <= self.shader < len(nif.types) and nif.types[self.shader] == "BSLightingShaderProperty"
        self.prop = Lighting(nif, self.shader) if ok else None

    @property
    def alpha(self) -> tuple[int, int] | None:
        """The NiAlphaProperty's (flags, threshold), or None: bit 0 blend, bit 9 test (nif.xml AlphaFlags)."""
        a = self.alpha_ref
        if not (0 <= a < len(self.nif.types)) or self.nif.types[a] != "NiAlphaProperty":
            return None
        b = self.nif.blocks[a]
        ne, = struct.unpack_from("<I", b, 4)
        return struct.unpack_from("<HB", b, 8 + 4 * ne + 4)

    def set_alpha(self, flags: int, threshold: int) -> None:
        b = self.nif.blocks[self.alpha_ref]
        ne, = struct.unpack_from("<I", b, 4)
        struct.pack_into("<HB", b, 8 + 4 * ne + 4, flags, threshold)

    def _view(self, off: int, dtype, n: int) -> np.ndarray:
        b = np.frombuffer(bytes(self.nif.blocks[self.i][self.vdata:self.vdata + self.nv * self.vsize]), np.uint8)
        b = b.reshape(self.nv, self.vsize)[:, off:off + n * np.dtype(dtype).itemsize]
        return np.ascontiguousarray(b).view(dtype).reshape(self.nv, n)

    def positions(self) -> np.ndarray:
        return self._view(0, np.float32, 3).astype(float)  # SSE: full-precision Vector3 then bitangent X

    def set_shader(self, block: int) -> None:
        """Draw this shape with another shape's BSLightingShaderProperty (its flags and texture set)."""
        struct.pack_into("<i", self.nif.blocks[self.i], self._shader_at, block)
        self.shader = block
        self.prop = Lighting(self.nif, block)

    def has_uv(self) -> bool:
        return bool(self.attrs & 0x2) and self.nv > 0

    def uv(self) -> np.ndarray:
        return self._view(((self.desc >> 8) & 0xF) * 4, np.float16, 2).astype(float)

    def set_uv(self, uv: np.ndarray) -> None:
        off = ((self.desc >> 8) & 0xF) * 4
        h = uv.astype(np.float16)
        b = self.nif.blocks[self.i]
        for v in range(self.nv):
            o = self.vdata + v * self.vsize + off
            b[o:o + 4] = h[v].tobytes()

    def colours(self) -> np.ndarray | None:
        if not self.attrs & 0x20 or not self.nv:
            return None
        return self._view(((self.desc >> 24) & 0xF) * 4, np.uint8, 4).astype(float)

    def set_colours(self, rgb: np.ndarray) -> None:
        """Write per-vertex RGB (0..255; alpha kept). A shape without the colour attribute gains one (4 bytes at the
        end of each vertex; the vertex size, offsets, data size and attribute bits rewritten), so the engine multiplies
        it into the diffuse once the property's Vertex_Colors flag is set."""
        b = self.nif.blocks[self.i]
        if not self.attrs & 0x20:
            old = self.vsize
            rows = [bytes(b[self.vdata + v * old:self.vdata + (v + 1) * old]) + b"\xff\xff\xff\xff" for v in range(self.nv)]
            tail = bytes(b[self.vdata + self.nv * old:])
            self.desc = (self.desc & ~0xF & ~(0xF << 24)) | ((old // 4 + 1) & 0xF) | ((old // 4) << 24) | (0x20 << 44)
            q = self.vdata - 16
            struct.pack_into("<Q", b, q, self.desc)
            struct.pack_into("<I", b, q + 12, self.nv * (old + 4) + 6 * self.ntri)
            b[self.vdata:] = b"".join(rows) + tail
            self.vsize, self.attrs = old + 4, (self.desc >> 44) & 0xFFF
        co = ((self.desc >> 24) & 0xF) * 4
        c = np.clip(np.rint(rgb), 0, 255).astype(np.uint8)
        for v in range(self.nv):
            o = self.vdata + v * self.vsize + co
            b[o:o + 3] = c[v].tobytes()

    def triangles(self) -> np.ndarray:
        o = self.vdata + self.nv * self.vsize
        return np.frombuffer(bytes(self.nif.blocks[self.i][o:o + 6 * self.ntri]), "<u2").reshape(-1, 3)

    def ratios(self, uv: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
        """Per non-degenerate triangle: the UV-to-surface Jacobian's singular-value ratio (1 = square texels), and the
        triangles kept (the white-trunks lane's measure)."""
        t = self.triangles().astype(int)
        return ratios(self.positions(), self.uv() if uv is None else uv, t[(t < self.nv).all(1)])

    def stretch(self, uv: np.ndarray | None = None) -> float | None:
        """Median UV stretch ratio of the shape (None: no UVs or no triangles)."""
        if not self.has_uv() or not self.ntri:
            return None
        r, _ = self.ratios(uv)
        return float(np.median(r)) if len(r) else None

    def islands(self) -> np.ndarray:
        """Per vertex: its UV island (connected through the shape's triangles)."""
        par = np.arange(self.nv)

        def root(a):
            while par[a] != a:
                par[a] = par[par[a]]
                a = par[a]
            return a
        for a, b, c in self.triangles().astype(int):
            if max(a, b, c) >= self.nv:
                continue
            for x in (b, c):
                ra, rx = root(a), root(x)
                if ra != rx:
                    par[ra] = rx
        return np.array([root(v) for v in range(self.nv)])


class Lighting:
    """A BSLightingShaderProperty's fields by offset (q = after shader type, name, extra data, controller)."""

    def __init__(self, nif: Nif, i: int):
        self.nif, self.i = nif, i
        ne, = struct.unpack_from("<I", nif.blocks[i], 8)
        self.q = 12 + 4 * ne + 4

    def _get(self, fmt: str, off: int):
        return struct.unpack_from(fmt, self.nif.blocks[self.i], self.q + off)

    def _put(self, fmt: str, off: int, *v) -> None:
        struct.pack_into(fmt, self.nif.blocks[self.i], self.q + off, *v)

    @property
    def flags(self) -> tuple[int, int]:
        return self._get("<II", 0)

    def set_flags(self, f1: int, f2: int) -> None:
        self._put("<II", 0, f1, f2)

    @property
    def emissive(self) -> tuple[list[float], float]:
        r, g, b, m = self._get("<4f", 28)
        return [round(r, 3), round(g, 3), round(b, 3)], round(m, 3)

    def set_emissive(self, rgb, mult: float) -> None:
        self._put("<4f", 28, *rgb, mult)

    @property
    def clamp(self) -> int:
        return self._get("<I", 44)[0]

    @property
    def soft(self) -> float:
        return round(self._get("<f", 76)[0], 3)

    @property
    def texset(self) -> int:
        return self._get("<i", 24)[0]

    def slots(self) -> list[str]:
        t = self.texset
        if not (0 <= t < len(self.nif.types)) or self.nif.types[t] != "BSShaderTextureSet":
            return []
        b, out, o = self.nif.blocks[t], [], 4
        for _ in range(struct.unpack_from("<I", b, 0)[0]):
            n, = struct.unpack_from("<I", b, o)
            out.append(b[o + 4:o + 4 + n].decode("latin-1"))
            o += 4 + n
        return out

    def set_slot(self, slot: int, path: str) -> None:
        s = self.slots()
        s[slot] = path
        blk = struct.pack("<I", len(s)) + b"".join(struct.pack("<I", len(x)) + x.encode("latin-1") for x in s)
        self.nif.blocks[self.texset] = bytearray(blk)


def flag_names(f1: int, f2: int) -> list[str]:
    return [k for k, v in F1.items() if f1 >> v & 1] + [k for k, v in F2.items() if f2 >> v & 1]


def ratios(p: np.ndarray, uv: np.ndarray, t: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Per non-degenerate triangle of t (vertex indices into p, uv): the UV-to-surface Jacobian's singular-value
    ratio, and the triangles kept."""
    e1, e2 = p[t[:, 1]] - p[t[:, 0]], p[t[:, 2]] - p[t[:, 0]]
    d1, d2 = uv[t[:, 1]] - uv[t[:, 0]], uv[t[:, 2]] - uv[t[:, 0]]
    det = d1[:, 0] * d2[:, 1] - d2[:, 0] * d1[:, 1]
    keep = (np.abs(det) > 1e-9) & (np.linalg.norm(np.cross(e1, e2), axis=1) > 1e-9)
    e1, e2, d1, d2, det = e1[keep], e2[keep], d1[keep], d2[keep], det[keep]
    ju = (e1 * d2[:, 1:2] - e2 * d1[:, 1:2]) / det[:, None]  # dS/du
    jv = (e2 * d1[:, 0:1] - e1 * d2[:, 0:1]) / det[:, None]  # dS/dv
    a, c, bb = (ju * ju).sum(1), (jv * jv).sum(1), (ju * jv).sum(1)
    tr, dt = a + c, np.maximum(a * c - bb * bb, 0)
    disc = np.sqrt(np.maximum(tr * tr / 4 - dt, 0))
    s1, s2 = np.sqrt(tr / 2 + disc), np.sqrt(np.maximum(tr / 2 - disc, 0))
    return s1 / np.maximum(s2, 1e-12), t[keep]
