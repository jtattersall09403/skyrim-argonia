"""A model's texture sets, what of them resolves in the NewWorld profile, and the native repair of a wrong path.

Only a missing diffuse (texture set slot 0) shows purple in game; a missing normal map or other slot renders without
it. So a base is refused only when a diffuse cannot be resolved; other missing slots are a warning count.

A diffuse whose path is wrong while the file sits in the same mod under another path (a moved folder, a doubled
.dds.dds) is repaired the way Skyrim's own records do it: an alternate texture on our copied record (the model's MODS
list: the 3D shape's name and index + a new TXST of ours holding the corrected paths). The mesh is never edited or
shipped. A match is by file name within the mod that lays the model; a name found at two paths is refused.

The NIF layout (20.2.0.7, Skyrim SE user version 12, bsver 100) follows niftools' nif.xml, read as a spec:
NiObjectNET (name, extra data, controller), NiAVObject (flags, transform, collision), NiNode children, BSTriShape and
its kin (bounds, skin, shader, alpha), NiTriShape/NiTriStrips (data, skin, material data, shader, alpha),
BSLightingShaderProperty (Skyrim shader type, NiObjectNET, flags, uv offset/scale, texture set) and
BSShaderTextureSet (count, sized strings).

    shapes(raw) -> [Shape(index, name, slots)]       the geometry in 3D index order, each with its 8 slot paths
    Audit(assets, mod_files).model(raw, mod)         -> {"missing_diffuse", "missing_other", "repairs"}
"""
from __future__ import annotations

import re
import struct
from dataclasses import dataclass

TRI_SHAPES = {"BSTriShape", "BSDynamicTriShape", "BSLODTriShape", "BSMeshLODTriShape", "BSSubIndexTriShape"}
GEOMETRY = {"NiTriShape", "NiTriStrips"}
NOT_NODES = {"BSFurnitureMarkerNode"}


@dataclass
class Shape:
    index: int  # the 3D index: the shape's place among the geometry met walking the node tree from the root
    name: str
    slots: list[str]  # the texture set's paths as the nif holds them (lower case, backslashes), "" when empty


def _norm(p: str) -> str:
    return p.lower().replace("/", "\\").strip()


def tex_key(p: str) -> str:
    """The data-relative path the engine reads (from the last textures\\ on)."""
    p = _norm(p)
    i = p.rfind("textures\\")
    return p[i:] if i >= 0 else "textures\\" + p.lstrip("\\")


def shapes(raw: bytes) -> list[Shape]:
    b = raw
    if not b.startswith(b"Gamebryo File Format"):
        return []
    o = b.index(b"\n") + 1
    version, endian, _user, nblocks = struct.unpack_from("<IBII", b, o)
    if version != 0x14020007 or endian != 1:
        return []
    o += 13
    bsver = struct.unpack_from("<I", b, o)[0]
    o += 4
    for _ in range(3):
        o += 1 + b[o]
    if bsver >= 103:
        o += 1 + b[o]
    ntypes = struct.unpack_from("<H", b, o)[0]
    o += 2
    names = []
    for _ in range(ntypes):
        n = struct.unpack_from("<I", b, o)[0]
        names.append(b[o + 4:o + 4 + n].decode("ascii"))
        o += 4 + n
    idx = struct.unpack_from(f"<{nblocks}H", b, o)
    o += 2 * nblocks
    types = [names[i & 0x7FFF] for i in idx]
    sizes = struct.unpack_from(f"<{nblocks}I", b, o)
    o += 4 * nblocks
    nstr, _ = struct.unpack_from("<II", b, o)
    o += 8
    strings = []
    for _ in range(nstr):
        n = struct.unpack_from("<I", b, o)[0]
        strings.append(b[o + 4:o + 4 + n].decode("latin-1"))
        o += 4 + n
    o += 4 + 4 * struct.unpack_from("<I", b, o)[0]
    offs = []
    for s in sizes:
        offs.append(o)
        o += s

    def i32(p):
        return struct.unpack_from("<i", b, p)[0]

    def net(p):  # NiObjectNET: name, extra data list, controller -> (name, offset after)
        nm = i32(p)
        ne = struct.unpack_from("<I", b, p + 4)[0]
        return (strings[nm] if 0 <= nm < len(strings) else ""), p + 8 + 4 * ne + 4

    def av_end(p):  # NiAVObject after NiObjectNET: flags u32, translation, rotation, scale, collision
        return p + 4 + 12 + 36 + 4 + 4

    def texset(shader):
        if not (0 <= shader < nblocks) or types[shader] != "BSLightingShaderProperty":
            return None
        p = offs[shader] + (4 if bsver < 130 else 0)  # Skyrim shader type
        _, p = net(p)
        p += 4 + 4 + 8 + 8  # flags 1, flags 2, uv offset, uv scale
        ts = i32(p)
        if not (0 <= ts < nblocks) or types[ts] != "BSShaderTextureSet":
            return None
        p = offs[ts]
        n = i32(p)
        p += 4
        out = []
        for _ in range(max(0, min(n, 16))):
            ln = struct.unpack_from("<I", b, p)[0]
            out.append(_norm(b[p + 4:p + 4 + ln].decode("latin-1")))
            p += 4 + ln
        return (out + [""] * 8)[:8]

    found: list[Shape] = []
    seen: set[int] = set()

    def walk(i):
        if not (0 <= i < nblocks) or i in seen:
            return
        seen.add(i)
        k = types[i]
        try:
            if k in TRI_SHAPES or k in GEOMETRY:
                name, p = net(offs[i])
                p = av_end(p)
                if k in TRI_SHAPES:
                    shader = i32(p + 16 + 4)
                else:
                    p += 8  # data, skin instance
                    nm = struct.unpack_from("<I", b, p)[0]
                    p += 4 + 8 * nm + 4 + 1  # material names + extra data, active material, needs update
                    shader = i32(p)
                found.append(Shape(len(found), name, texset(shader) or []))
            elif k.endswith("Node") and k not in NOT_NODES:
                _, p = net(offs[i])
                p = av_end(p)
                nc = struct.unpack_from("<I", b, p)[0]
                for c in struct.unpack_from(f"<{nc}i", b, p + 4):
                    walk(c)
        except (struct.error, IndexError):
            return

    walk(0)
    return found


def _variants(name: str) -> list[str]:
    """File names a wrong path may stand for: itself, and without a doubled extension (x.dds.dds -> x.dds)."""
    out = [name]
    m = re.match(r"^(.*?\.dds)(\.dds)+$", name)
    if m:
        out.append(m.group(1))
    return out


class Audit:
    """assets: has(path) over the NewWorld profile; mod_files(mod) -> the texture paths that mod lays (lower case,
    backslashes, data-relative), or None when the model's provider is not a mod (no repair then)."""

    def __init__(self, assets, mod_files):
        self.assets = assets
        self.mod_files = mod_files
        self._by_name: dict[str, dict[str, list[str]]] = {}

    def _names(self, mod: str) -> dict[str, list[str]]:
        if mod not in self._by_name:
            ix: dict[str, list[str]] = {}
            for f in self.mod_files(mod) or ():
                ix.setdefault(f.rsplit("\\", 1)[-1], []).append(f)
            self._by_name[mod] = ix
        return self._by_name[mod]

    def find(self, path: str, mod: str | None) -> tuple[str | None, str]:
        """(the corrected data-relative path or None, why)."""
        if not mod:
            return None, "model not laid by a mod"
        hits = set()
        for nm in _variants(tex_key(path).rsplit("\\", 1)[-1]):
            hits |= {f for f in self._names(mod).get(nm, []) if self.assets.has(f)}
        if len(hits) == 1:
            return hits.pop(), "by file name in the mod"
        return None, ("ambiguous: " + ", ".join(sorted(hits))) if hits else "no file of that name in the mod"

    def model(self, raw: bytes, mod: str | None) -> dict:
        missing_diffuse, missing_other, repairs = [], [], []
        for s in shapes(raw):
            if not s.slots:
                continue
            fixed = list(s.slots)
            changed = False
            for slot, p in enumerate(s.slots):
                if not p or self.assets.has(tex_key(p)):
                    continue
                new, why = self.find(p, mod)
                if new:
                    fixed[slot] = new
                    changed = True
                    if slot == 0:
                        continue
                if slot == 0 and not new:
                    missing_diffuse.append({"shape": s.name, "path": tex_key(p), "why": why})
                elif slot != 0 and not new:
                    missing_other.append({"shape": s.name, "slot": slot, "path": tex_key(p)})
            if changed:
                repairs.append({"shape": s.name, "index": s.index,
                                "slots": [tex_key(p)[len("textures\\"):] if p else "" for p in fixed],
                                "from": [tex_key(p) for p in s.slots if p]})
        return {"missing_diffuse": missing_diffuse, "missing_other": missing_other, "repairs": repairs}
