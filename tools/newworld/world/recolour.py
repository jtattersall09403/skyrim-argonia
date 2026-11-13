"""Leaf textures laid again recoloured: a mod's texture whose colour is unnatural, shifted in hue, saturation and
value, written at the same data path into a folder of its own that stands above every mod.

    python -m tools.newworld.world.recolour lay <staged mods dir> <out folder>
        newworld/sources/flora/recolour.json: {data path: {mod, hue, sat, val}}; each texture is read from the staged
        mod, recoloured and written to <out>/<data path>; a file no longer listed is removed; prints "changed" when
        the folder changed. Exit 1 when a listed mod lacks its texture.

The output is an uncompressed 32-bit DDS (B8G8R8A8, Skyrim SE reads it) with its full mip chain made by halving,
alpha kept as the source has it. Derived at stage time from the owned file, never committed (decision 0003).
"""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
TABLE = REPO / "newworld" / "sources" / "flora" / "recolour.json"


def table() -> dict:
    return json.loads(TABLE.read_text())["textures"]


def rgb_to_hsv(c: np.ndarray):
    mx, mn = c.max(-1), c.min(-1)
    d = np.maximum(mx - mn, 1e-9)
    r, g, b = c[..., 0], c[..., 1], c[..., 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) / 6
    h = np.where(mx - mn < 1e-9, 0.0, h)
    s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-9), 0.0)
    return h, s, mx


def hsv_to_rgb(h, s, v) -> np.ndarray:
    i = np.floor(h * 6) % 6
    f = h * 6 - np.floor(h * 6)
    p, q, t = v * (1 - s), v * (1 - f * s), v * (1 - (1 - f) * s)
    out = np.zeros(h.shape + (3,))
    for k, (a, b, c) in enumerate(((v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q))):
        m = i == k
        out[m] = np.stack([a[m], b[m], c[m]], -1)
    return out


def recolour(rgba: np.ndarray, hue: float, sat: float, val: float) -> np.ndarray:
    """rgba uint8 (h, w, 4) -> the same with hue + `hue` degrees, saturation x `sat`, value x `val`; alpha kept."""
    c = rgba[..., :3].astype(np.float64) / 255
    h, s, v = rgb_to_hsv(c)
    rgb = hsv_to_rgb((h + hue / 360) % 1, np.clip(s * sat, 0, 1), np.clip(v * val, 0, 1))
    out = rgba.copy()
    out[..., :3] = np.round(rgb * 255).clip(0, 255).astype(np.uint8)
    return out


def dds_bgra(rgba: np.ndarray) -> bytes:
    """An uncompressed B8G8R8A8 DDS with the full mip chain (box-halved)."""
    h, w = rgba.shape[:2]
    levels, mips, a = 0, [], rgba.astype(np.float64)
    while True:
        mips.append(np.round(a).clip(0, 255).astype(np.uint8))
        levels += 1
        if a.shape[0] == 1 and a.shape[1] == 1:
            break
        hh, ww = max(1, a.shape[0] // 2), max(1, a.shape[1] // 2)
        a = a[: hh * 2 if a.shape[0] > 1 else 1, : ww * 2 if a.shape[1] > 1 else 1]
        a = a.reshape(hh, a.shape[0] // hh, ww, a.shape[1] // ww, 4).mean(axis=(1, 3))
    flags = 0x1 | 0x2 | 0x4 | 0x8 | 0x1000 | 0x20000  # caps, height, width, pitch, pixelformat, mipmapcount
    pf = struct.pack("<II4sIIIII", 32, 0x41, b"\0\0\0\0", 32, 0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)
    head = struct.pack("<4sIIIIIII", b"DDS ", 124, flags, h, w, w * 4, 0, levels) + b"\0" * 44 + pf
    head += struct.pack("<IIIII", 0x1000 | 0x8 | 0x400000, 0, 0, 0, 0)
    body = b"".join(m[..., [2, 1, 0, 3]].tobytes() for m in mips)
    return head + body


def decode(raw: bytes) -> np.ndarray:
    from tools.places.assets.dds import decode as dec
    return np.asarray(dec(raw).convert("RGBA"))


def ci_file(root: Path, rel: str) -> Path | None:
    p = root
    for part in rel.replace("\\", "/").split("/"):
        if not p.is_dir():
            return None
        hit = next((c for c in p.iterdir() if c.name.lower() == part.lower()), None)
        if hit is None:
            return None
        p = hit
    return p if p.is_file() else None


def lay(mods: Path, out: Path) -> bool:
    want = {}
    for rel, t in table().items():
        f = ci_file(mods / t["mod"], rel)
        if f is None:
            raise SystemExit(f"recolour {rel}: {t['mod']} holds no such file")
        want[rel.replace("\\", "/").lower()] = dds_bgra(recolour(decode(f.read_bytes()), t["hue"], t["sat"], t["val"]))
    changed = False
    if out.exists():
        for f in [f for f in out.rglob("*") if f.is_file()]:
            if str(f.relative_to(out)).lower() not in want:
                f.unlink()
                changed = True
    for rel, data in want.items():
        o = out / rel
        if not o.exists() or o.read_bytes() != data:
            o.parent.mkdir(parents=True, exist_ok=True)
            o.write_bytes(data)
            changed = True
    return changed


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[0] != "lay":
        print(__doc__)
        return 2
    if lay(Path(argv[1]), Path(argv[2])):
        print("changed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
