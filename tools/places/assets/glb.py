"""A minimal glTF 2.0 binary writer and reader: meshes of triangles with POSITION, NORMAL, TEXCOORD_0, COLOR_0,
one node per primitive group with its 4x4 matrix, materials with a base colour texture by URI. Only what the
studio's meshes need; reading is for the proofs and the tests."""
from __future__ import annotations

import json
import struct

import numpy as np

FLOAT, UINT32 = 5126, 5125
ARRAY, ELEMENT = 34962, 34963


class Builder:
    def __init__(self):
        self.bin = bytearray()
        self.j: dict = {"asset": {"version": "2.0", "generator": "argonia tools.places.assets"}, "scene": 0,
                        "scenes": [{"nodes": []}], "nodes": [], "meshes": [], "materials": [], "textures": [],
                        "images": [], "samplers": [{"magFilter": 9729, "minFilter": 9987, "wrapS": 10497, "wrapT": 10497}],
                        "accessors": [], "bufferViews": [], "buffers": []}
        self._img: dict[str, int] = {}

    def _view(self, a: np.ndarray, target: int) -> int:
        while len(self.bin) % 4:
            self.bin.append(0)
        self.j["bufferViews"].append({"buffer": 0, "byteOffset": len(self.bin), "byteLength": a.nbytes, "target": target})
        self.bin += a.tobytes()
        return len(self.j["bufferViews"]) - 1

    def accessor(self, a: np.ndarray, kind: str, minmax: bool = False) -> int:
        if kind == "SCALAR":
            a = np.ascontiguousarray(a, "<u4").ravel()
            acc = {"componentType": UINT32, "count": int(a.size), "type": "SCALAR", "bufferView": self._view(a, ELEMENT)}
        else:
            a = np.ascontiguousarray(a, "<f4")
            acc = {"componentType": FLOAT, "count": int(a.shape[0]), "type": kind, "bufferView": self._view(a, ARRAY)}
            if minmax:
                acc["min"], acc["max"] = a.min(0).tolist(), a.max(0).tolist()
        self.j["accessors"].append(acc)
        return len(self.j["accessors"]) - 1

    def texture(self, uri: str) -> int:
        if uri not in self._img:
            self.j["images"].append({"uri": uri})
            self.j["textures"].append({"sampler": 0, "source": len(self.j["images"]) - 1})
            self._img[uri] = len(self.j["textures"]) - 1
        return self._img[uri]

    def material(self, m: dict) -> int:
        self.j["materials"].append(m)
        return len(self.j["materials"]) - 1

    def node(self, name: str, matrix: list[float] | None, prims: list[dict], extras: dict | None = None) -> None:
        self.j["meshes"].append({"name": name, "primitives": prims})
        n = {"name": name, "mesh": len(self.j["meshes"]) - 1}
        if matrix is not None:
            n["matrix"] = matrix
        if extras:
            n["extras"] = extras
        self.j["nodes"].append(n)
        self.j["scenes"][0]["nodes"].append(len(self.j["nodes"]) - 1)

    def glb(self, extras: dict | None = None) -> bytes:
        j = dict(self.j)
        if extras:
            j["extras"] = extras
        for k in ("materials", "textures", "images", "samplers", "meshes"):
            if not j[k]:
                del j[k]
        if "textures" not in j:
            j.pop("samplers", None)
        while len(self.bin) % 4:
            self.bin.append(0)
        if self.bin:
            j["buffers"] = [{"byteLength": len(self.bin)}]
        else:
            for k in ("buffers", "bufferViews", "accessors"):
                j.pop(k, None)
        js = json.dumps(j, separators=(",", ":")).encode()
        js += b" " * (-len(js) % 4)
        chunks = struct.pack("<II", len(js), 0x4E4F534A) + js
        if self.bin:
            chunks += struct.pack("<II", len(self.bin), 0x004E4942) + bytes(self.bin)
        return struct.pack("<III", 0x46546C67, 2, 12 + len(chunks)) + chunks


def read(raw: bytes) -> tuple[dict, bytes]:
    magic, _, _ = struct.unpack_from("<III", raw)
    if magic != 0x46546C67:
        raise ValueError("not a GLB")
    jl, _ = struct.unpack_from("<II", raw, 12)
    j = json.loads(raw[20:20 + jl])
    o = 20 + jl
    b = raw[o + 8:o + 8 + struct.unpack_from("<I", raw, o)[0]] if o < len(raw) else b""
    return j, b


def accessor(j: dict, b: bytes, i: int) -> np.ndarray:
    a = j["accessors"][i]
    v = j["bufferViews"][a["bufferView"]]
    n = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[a["type"]]
    dt = "<u4" if a["componentType"] == UINT32 else "<f4"
    arr = np.frombuffer(b, dt, a["count"] * n, v["byteOffset"])
    return arr if n == 1 else arr.reshape(-1, n)
