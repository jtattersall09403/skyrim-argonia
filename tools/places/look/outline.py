"""A piece's mesh as a section draws it: its model's own triangles (the studio's converted model, the same one the
page draws), placed by the piece's matrix, kept to the section's slab and projected; their union's outline is the
piece's shape in the cut. A flight's treads seen edge-on render as nothing in an orthographic side view, so the
outline is drawn from the triangles, never from the box. A piece with no readable model keeps its box."""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

from tools.places.look import geom

_TRIS: dict[str, np.ndarray | None] = {}


def model_tris(model: str | None) -> np.ndarray | None:
    """The model's triangles in its own frame (n, 3, 3), read from the studio's converted model; None for a model the
    converter could not read (its stand-in box)."""
    if not model:
        return None
    k = str(model).lower()
    if k not in _TRIS:
        got = None
        try:
            from tools.places import assets
            from tools.places.assets import glb
            info = assets.mesh_info(k)
            if info.get("tris") and not info.get("placeholder"):
                j, b = glb.read(open(info["glb"], "rb").read())
                parts = []
                for n in j.get("nodes", []):
                    if "mesh" not in n:
                        continue
                    m = np.array(n.get("matrix", [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]), float).reshape(4, 4).T
                    for p in j["meshes"][n["mesh"]]["primitives"]:
                        P = glb.accessor(j, b, p["attributes"]["POSITION"]) @ m[:3, :3].T + m[:3, 3]
                        idx = glb.accessor(j, b, p["indices"]).reshape(-1, 3)
                        parts.append(P[idx])
                got = np.concatenate(parts).astype(float) if parts else None
        except Exception:  # noqa: BLE001  an unreadable model draws as its box
            got = None
        _TRIS[k] = got
    return _TRIS[k]


def world_tris(p: dict, tris: np.ndarray) -> np.ndarray:
    M = np.asarray(p["m"], float)
    flat = tris.reshape(-1, 3)
    return (flat @ M[:3, :3].T + M[:3, 3]).reshape(-1, 3, 3)


def in_slab(W: np.ndarray, line, slab: float) -> np.ndarray:
    """The triangles with a corner within `slab` of the section's plane (through the line, upright)."""
    a, b = np.asarray(line[0][:2], float), np.asarray(line[1][:2], float)
    t = (b - a) / max(float(np.linalg.norm(b - a)), 1e-9)
    n = np.array([-t[1], t[0]])
    dist = np.abs((W[:, :, :2] - a) @ n)
    return W[(dist <= slab).any(axis=1)]


def mask(cam: dict, W: np.ndarray, size) -> Image.Image | None:
    """The projected triangles filled into a mask the size of the image."""
    if not len(W):
        return None
    pp = geom.project(cam, W.reshape(-1, 3)).reshape(-1, 3, 3)
    m = Image.new("L", size, 0)
    d = ImageDraw.Draw(m)
    for tri in pp:
        if (tri[:, 2] <= 0).any():
            continue
        d.polygon([(float(x), float(y)) for x, y, _ in tri], fill=255, outline=255)
    return m


def edge(m: Image.Image, width: int = 1) -> Image.Image:
    """The mask's outline: the mask less its own erosion."""
    er = m.filter(ImageFilter.MinFilter(1 + 2 * width))
    return ImageChops.subtract(m, er)


def piece_outline(cam: dict, p: dict, size, slab: float) -> Image.Image | None:
    """A crossed piece's outline in a section, from its mesh; None when its model has no triangles to read."""
    T = model_tris(p.get("model"))
    if T is None:
        return None
    W = in_slab(world_tris(p, T), cam["line"], slab)
    m = mask(cam, W, size)
    return edge(m) if m is not None else None
