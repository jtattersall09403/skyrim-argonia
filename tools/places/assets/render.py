"""An off-screen picture of a converted GLB, drawn from the GLB alone (the proof that the conversion is right).

A small software rasteriser: the scene's nodes with their matrices, the base colour texture (resolved and decoded
the way the studio's /api/asset/tex serves it), vertex colours, alpha test at the material's cutoff, a z-buffer and
one light. The camera looks at the mesh's bounds from the south-west, 25 degrees up, Z up as in the game."""
from __future__ import annotations

import io
import math

import numpy as np
from PIL import Image

from tools.places.assets import glb


def _texture(uri: str):
    from tools.places.assets import tex_info
    from tools.places.assets.nifglb import uri_path
    i = tex_info(uri_path(uri), 512)
    if not i:
        return None
    return np.asarray(Image.open(i["webp"]).convert("RGBA"), np.float32) / 255.0


def render(data: bytes, size: int = 512, azimuth: float = 225.0, elevation: float = 25.0) -> Image.Image:
    j, b = glb.read(data)
    tris = []  # (world verts [n,3], uv, colour, normal, idx, material)
    for n in j.get("nodes", []):
        m = np.array(n.get("matrix", [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]), np.float64).reshape(4, 4).T
        for p in j["meshes"][n["mesh"]]["primitives"]:
            a = p["attributes"]
            P = glb.accessor(j, b, a["POSITION"]) @ m[:3, :3].T + m[:3, 3]
            N = glb.accessor(j, b, a["NORMAL"]) @ m[:3, :3].T if "NORMAL" in a else None
            UV = glb.accessor(j, b, a["TEXCOORD_0"]) if "TEXCOORD_0" in a else None
            C = glb.accessor(j, b, a["COLOR_0"]) if "COLOR_0" in a else None
            idx = glb.accessor(j, b, p["indices"]).reshape(-1, 3)
            tris.append((P, UV, C, N, idx, j["materials"][p["material"]]))
    allp = np.concatenate([t[0] for t in tris])
    lo, hi = allp.min(0), allp.max(0)
    c = (lo + hi) / 2
    az, el = math.radians(azimuth), math.radians(elevation)
    fwd = -np.array([math.cos(el) * math.sin(az), math.cos(el) * math.cos(az), math.sin(el)])  # camera looks along fwd
    right = np.cross(fwd, [0, 0, 1.0])
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    R = np.stack([right, up, -fwd])
    q = (allp - c) @ R.T
    scale = (size * 0.9) / max(np.ptp(q[:, 0]), np.ptp(q[:, 1]), 1e-3)
    img = np.zeros((size, size, 3), np.float32) + np.array([0.82, 0.86, 0.9], np.float32)
    zb = np.full((size, size), -np.inf, np.float32)
    light = np.array([0.4, -0.5, 0.75])
    light /= np.linalg.norm(light)
    cache_tex: dict = {}
    for P, UV, C, N, idx, mat in tris:
        s = (P - c) @ R.T
        sx = s[:, 0] * scale + size / 2
        sy = size / 2 - s[:, 1] * scale
        sz = s[:, 2]
        pbr = mat.get("pbrMetallicRoughness", {})
        base = np.array(pbr.get("baseColorFactor", [1, 1, 1, 1]), np.float32)
        t = None
        if "baseColorTexture" in pbr and UV is not None:
            uri = j["images"][j["textures"][pbr["baseColorTexture"]["index"]]["source"]]["uri"]
            if uri not in cache_tex:
                cache_tex[uri] = _texture(uri)
            t = cache_tex[uri]
        cutoff = mat.get("alphaCutoff", 0.5) if mat.get("alphaMode") == "MASK" else None
        two = mat.get("doubleSided", False)
        for tri in idx:
            x, y = sx[tri], sy[tri]
            x0, x1 = max(int(x.min()), 0), min(int(x.max()) + 1, size)
            y0, y1 = max(int(y.min()), 0), min(int(y.max()) + 1, size)
            if x0 >= x1 or y0 >= y1:
                continue
            den = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
            if abs(den) < 1e-9:
                continue
            if den > 0 and not two:  # back face (counter-clockwise in Skyrim's winding seen from the front)
                continue
            gx, gy = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
            w0 = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / den
            w1 = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / den
            w2 = 1 - w0 - w1
            inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
            if not inside.any():
                continue
            z = w0 * sz[tri[0]] + w1 * sz[tri[1]] + w2 * sz[tri[2]]
            sub = zb[y0:y1, x0:x1]
            ok = inside & (z > sub)
            if not ok.any():
                continue
            col = np.broadcast_to(base, (*ok.shape, 4)).copy()
            if t is not None:
                u = w0 * UV[tri[0], 0] + w1 * UV[tri[1], 0] + w2 * UV[tri[2], 0]
                v = w0 * UV[tri[0], 1] + w1 * UV[tri[1], 1] + w2 * UV[tri[2], 1]
                th, tw = t.shape[:2]
                col *= t[(np.mod(v, 1) * th).astype(int) % th, (np.mod(u, 1) * tw).astype(int) % tw]
            if C is not None:
                col *= w0[..., None] * C[tri[0]] + w1[..., None] * C[tri[1]] + w2[..., None] * C[tri[2]]
            if cutoff is not None:
                ok &= col[..., 3] >= cutoff
            if N is not None:
                nn = N[tri].mean(0)
            else:
                nn = np.cross(P[tri[1]] - P[tri[0]], P[tri[2]] - P[tri[0]])
            nn = nn / max(np.linalg.norm(nn), 1e-9)
            shade = 0.35 + 0.65 * abs(float(nn @ light))
            sub[ok] = z[ok]
            img[y0:y1, x0:x1][ok] = col[..., :3][ok] * shade
    return Image.fromarray((img.clip(0, 1) * 255).astype(np.uint8), "RGB")


def to_png(data: bytes, size: int = 512) -> bytes:
    out = io.BytesIO()
    render(data, size).save(out, "PNG")
    return out.getvalue()
