"""A Skyrim NIF to a GLB for the browser, in the mesh's own units and axes (Z up, game units).

The reader is `nifdump` (tools/places/assets/nifdump, built on ousnius/nifly: BSTriShape, BSDynamicTriShape,
BSSubIndexTriShape, NiTriShape and NiTriStrips, every SSE and LE vertex layout). Each drawable shape becomes one
node with the shape's transform to the root (its own and every parent node's) as the node matrix, so the GLB's
scene is the NIF's scene. Per shape: positions, normals, UVs (the shader's UV scale and offset applied), vertex
colours when the shader uses them (alpha only when it uses vertex alpha and is not a tree's, whose vertex
alpha weights its wind), the diffuse as the base colour texture
and the normal map as the normal texture, by URI (below). NiAlphaProperty's alpha test becomes alphaMode MASK at
its threshold, alpha blend becomes BLEND, the shader's two-sided flag becomes doubleSided. Hidden shapes (an
editor marker's) are left out; a skinned shape
(a book, a banner, a bird: skinned for physics or animation) is drawn in its bind pose.

A texture is referenced, never embedded: its URI is the studio's texture route, `/api/asset/tex?path=<data path,
lower case, forward slashes>&size=512` (256 for a normal map), so a texture shared by many meshes is fetched and
held once; a front end that wants another size rewrites `size` with its loader's URL modifier. The GLB's extras
list the plain data paths.

Levels: level 0 is the whole mesh. Level 1 is light: a mesh over LIGHT_TRIS triangles is simplified (quadric edge
collapse) to max(LIGHT_TRIS, a quarter); a lighter mesh's level 1 is its level 0. Triangle counts of both levels are
in the GLB's extras and the sidecar. A mesh that cannot be read becomes a placeholder box of the base's bounds,
flagged `placeholder` with the reason, never dropped."""
from __future__ import annotations

import json
import os
import struct
import subprocess
import tempfile
from pathlib import Path

import numpy as np

from tools.places.assets.glb import Builder

NIFDUMP = Path(os.environ.get("ARGONIA_NIFDUMP", Path.home() / ".argonia" / "bin" / "nifdump"))
VERSION = 6  # bump when the GLB this writes changes; it is part of every cache key
LIGHT_TRIS = 1500
ALPHA_BLEND, ALPHA_TEST = 0x1, 0x200
TREE_ANIM = 1 << 29


class MeshError(Exception):
    pass


def tex_uri(p: str) -> str:
    """The texture's URI, or '' for a slot that does not name a .dds file (empty or garbage)."""
    p = p.strip()
    if not p.lower().endswith(".dds") or not p.isprintable():
        return ""
    p = p.replace("\\", "/").lower().lstrip("/")
    if p.startswith("data/"):
        p = p[5:]
    return p if p.startswith("textures/") else "textures/" + p


def image_uri(path: str, size: int) -> str:
    from urllib.parse import quote
    return f"/api/asset/tex?path={quote(path, safe='/')}&size={size}"


def uri_path(uri: str) -> str:
    """The data path a texture URI names (the inverse of image_uri)."""
    from urllib.parse import parse_qs, urlsplit
    q = parse_qs(urlsplit(uri).query)
    return q["path"][0] if "path" in q else uri


def dump(nif: bytes, tmp: Path | None = None) -> dict:
    """nifdump's shapes, each with its arrays as numpy."""
    if not NIFDUMP.exists():
        raise MeshError(f"nifdump not built: run tools/places/assets/nifdump/build.sh ({NIFDUMP})")
    with tempfile.TemporaryDirectory(dir=tmp) as d:
        i, o = Path(d) / "in.nif", Path(d) / "out.bin"
        i.write_bytes(nif)
        r = subprocess.run([str(NIFDUMP), str(i), str(o)], capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            raise MeshError((r.stderr or r.stdout or f"nifdump exit {r.returncode}").strip()[:300])
        raw = o.read_bytes()
    hl = struct.unpack_from("<I", raw)[0]
    head = json.loads(raw[4:4 + hl].decode("utf-8", "replace"))
    blob = memoryview(raw)[4 + hl:]
    for s in head["shapes"]:
        n = s["verts"]
        s["P"] = np.frombuffer(blob, "<f4", n * 3, s["pos"]).reshape(n, 3)
        s["I"] = np.frombuffer(blob, "<u4", s["tris"] * 3, s["idx"]).reshape(-1, 3)
        s["N"] = np.frombuffer(blob, "<f4", n * 3, s["nrm"]).reshape(n, 3) if s["nrm"] >= 0 else None
        s["UV"] = np.frombuffer(blob, "<f4", n * 2, s["uv"]).reshape(n, 2) if s["uv"] >= 0 else None
        s["C"] = np.frombuffer(blob, "<f4", n * 4, s["col"]).reshape(n, 4) if s["col"] >= 0 else None
    return head


def _simplify(s: dict, ratio: float) -> dict:
    import fast_simplification as fs
    P, I = s["P"], s["I"].astype(np.int64)
    if ratio <= 0 or len(I) < 16:
        return s
    _, _, coll = fs.simplify(P.astype(np.float32), I, target_reduction=ratio, return_collapses=True)
    P2, I2, mp = fs.replay_simplification(P.astype(np.float32), I, coll)
    pick = np.full(len(P2), -1, np.int64)
    order = np.arange(len(mp))[::-1]
    pick[mp[order]] = order  # the first original vertex that maps onto each new one
    pick[pick < 0] = 0
    t = dict(s)
    t["P"], t["I"] = np.asarray(P2, np.float32), np.asarray(I2, np.uint32).reshape(-1, 3)
    for k in ("N", "UV", "C"):
        t[k] = s[k][pick] if s[k] is not None else None
    t["verts"], t["tris"] = len(P2), len(t["I"])
    return t


def drawable(head: dict) -> list[dict]:
    return [s for s in head["shapes"] if not s.get("hidden") and s["tris"] > 0]


def build(head: dict, level: int = 0) -> tuple[bytes, dict]:
    shapes = drawable(head)
    if not shapes:
        raise MeshError("no drawable shape (all hidden, skinned or empty)")
    full = sum(s["tris"] for s in shapes)
    if level >= 1 and full > LIGHT_TRIS:
        ratio = 1.0 - max(LIGHT_TRIS, full // 4) / full
        shapes = [_simplify(s, ratio) for s in shapes]
    g = Builder()
    textures = set()
    for s in shapes:
        sh = s.get("shader") or {}
        mat: dict = {"name": s["name"] or "shape", "pbrMetallicRoughness": {"metallicFactor": 0.0, "roughnessFactor": 1.0}}
        diffuse, normal = (tex_uri(t) for t in s["tex"])
        if diffuse and s["UV"] is not None:
            mat["pbrMetallicRoughness"]["baseColorTexture"] = {"index": g.texture(image_uri(diffuse, 512))}
            textures.add(diffuse)
            if normal and "effect" not in sh.get("type", "").lower():
                mat["normalTexture"] = {"index": g.texture(image_uri(normal, 256))}
                textures.add(normal)
        al = s.get("alpha")
        if al and al["flags"] & ALPHA_TEST:
            mat["alphaMode"], mat["alphaCutoff"] = "MASK", round(al["threshold"] / 255, 4)
        elif al and al["flags"] & ALPHA_BLEND:
            mat["alphaMode"] = "BLEND"
        if sh.get("two_sided"):
            mat["doubleSided"] = True
        attrs = {"POSITION": g.accessor(s["P"], "VEC3", minmax=True)}
        if s["N"] is not None:
            n = s["N"] / np.maximum(np.linalg.norm(s["N"], axis=1, keepdims=True), 1e-6)
            attrs["NORMAL"] = g.accessor(n, "VEC3")
        if s["UV"] is not None:
            uv = s["UV"] * np.array(sh.get("uv_scale", [1, 1]), np.float32) + np.array(sh.get("uv_offset", [0, 0]), np.float32)
            attrs["TEXCOORD_0"] = g.accessor(uv, "VEC2")
        if s["C"] is not None and sh.get("vertex_colors"):
            c = np.clip(s["C"], 0, 1).copy()
            if not sh.get("vertex_alpha") or sh.get("flags2", 0) & TREE_ANIM:  # a tree's vertex alpha is its wind weight
                c[:, 3] = 1.0
            attrs["COLOR_0"] = g.accessor(c, "VEC4")
        prim = {"attributes": attrs, "indices": g.accessor(s["I"], "SCALAR"), "material": g.material(mat), "mode": 4}
        m = s["m"]  # row-major 3x4 -> glTF column-major 4x4
        matrix = [m[0], m[4], m[8], 0, m[1], m[5], m[9], 0, m[2], m[6], m[10], 0, m[3], m[7], m[11], 1]
        g.node(s["name"] or "shape", None if matrix == [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1] else matrix, [prim],
               {"block": s["block"], "tris": s["tris"]})
    tris = sum(s["tris"] for s in shapes)
    meta = {"level": level, "tris": tris, "tris_full": full, "shapes": len(shapes), "textures": sorted(textures),
            "bounds": bounds(shapes)}
    return g.glb({"argonia": meta}), meta


def bounds(shapes: list[dict]) -> list[list[float]]:
    pts = []
    for s in shapes:
        m = np.array(s["m"], np.float64).reshape(3, 4)
        pts.append(s["P"] @ m[:, :3].T + m[:, 3])
    p = np.concatenate(pts)
    return [p.min(0).round(2).tolist(), p.max(0).round(2).tolist()]


def placeholder(bnds: list[list[float]] | None, why: str) -> tuple[bytes, dict]:
    """A box of the bounds (64 units a side about the origin when none are known), flagged."""
    lo, hi = (np.array(bnds[0], np.float32), np.array(bnds[1], np.float32)) if bnds else (np.full(3, -32, np.float32), np.full(3, 32, np.float32))
    hi = np.maximum(hi, lo + 1)
    c = np.array([[x, y, z] for z in (0, 1) for y in (0, 1) for x in (0, 1)], np.float32)
    P = lo + c * (hi - lo)
    I = np.array([0, 2, 1, 1, 2, 3, 4, 5, 6, 5, 7, 6, 0, 1, 4, 1, 5, 4, 2, 6, 3, 3, 6, 7, 0, 4, 2, 2, 4, 6, 1, 3, 5, 3, 7, 5], np.uint32)
    g = Builder()
    mat = g.material({"name": "placeholder", "pbrMetallicRoughness": {"baseColorFactor": [1.0, 0.0, 1.0, 0.5],
                                                                      "metallicFactor": 0.0, "roughnessFactor": 1.0},
                      "alphaMode": "BLEND", "doubleSided": True})
    g.node("placeholder", None, [{"attributes": {"POSITION": g.accessor(P, "VEC3", minmax=True)}, "indices": g.accessor(I, "SCALAR"),
                                  "material": mat, "mode": 4}])
    meta = {"level": 0, "tris": 12, "tris_full": 12, "shapes": 1, "textures": [], "placeholder": True, "why": why,
            "bounds": [lo.tolist(), hi.tolist()]}
    return g.glb({"argonia": meta}), meta
