"""A small DDS reader for the ground's texture-set check (texcheck.py): the header and mip 0 of DXT1/DXT3/DXT5 as
RGBA arrays, numpy only. Measures what the engine reads (alpha statistics, normal flatness); never writes art."""
from __future__ import annotations

import struct

import numpy as np


def header(b: bytes) -> dict:
    h, w = struct.unpack_from("<II", b, 12)
    mips = struct.unpack_from("<I", b, 28)[0]
    pf_flags = struct.unpack_from("<I", b, 80)[0]
    return {"w": w, "h": h, "mips": mips, "fourcc": b[84:88].decode("latin-1") if pf_flags & 4 else "",
            "bits": struct.unpack_from("<I", b, 88)[0], "pf_flags": pf_flags}


def _565(c: np.ndarray) -> np.ndarray:
    c = c.astype(np.uint32)
    r, g, bl = (c >> 11) & 31, (c >> 5) & 63, c & 31
    return np.stack([(r * 255 + 15) // 31, (g * 255 + 31) // 63, (bl * 255 + 15) // 31], -1).astype(np.float32)


def _color(blk: np.ndarray, dxt1: bool) -> tuple[np.ndarray, np.ndarray]:
    """(n, 8) colour blocks -> (n, 16, 3) RGB and (n, 16) punch-through alpha (DXT1 only)."""
    c0 = blk[:, 0].astype(np.uint16) | (blk[:, 1].astype(np.uint16) << 8)
    c1 = blk[:, 2].astype(np.uint16) | (blk[:, 3].astype(np.uint16) << 8)
    p0, p1 = _565(c0), _565(c1)
    four = (c0 > c1) | (not dxt1)
    f4 = four[:, None]
    pal = np.stack([p0, p1, np.where(f4, (2 * p0 + p1) / 3, (p0 + p1) / 2),
                    np.where(f4, (p0 + 2 * p1) / 3, 0)], 1)
    bits = blk[:, 4:8].astype(np.uint32)
    idx = bits[:, 0] | (bits[:, 1] << 8) | (bits[:, 2] << 16) | (bits[:, 3] << 24)
    sel = np.stack([(idx >> (2 * i)) & 3 for i in range(16)], 1)
    rgb = np.take_along_axis(pal, sel[:, :, None].astype(np.int64), 1)
    a = np.where(~four[:, None] & (sel == 3), 0.0, 255.0)
    return rgb, a


def _alpha5(blk: np.ndarray) -> np.ndarray:
    a0, a1 = blk[:, 0].astype(np.float32), blk[:, 1].astype(np.float32)
    lut = [a0, a1]
    big = (a0 > a1)
    for i in range(1, 7):
        lut.append(np.where(big, ((7 - i) * a0 + i * a1) / 7, 0))
    lut = np.stack(lut[:8], 1)
    small = ~big
    for i in range(1, 5):
        lut[small, 1 + i] = ((5 - i) * a0[small] + i * a1[small]) / 5
    lut[small, 6], lut[small, 7] = 0, 255
    v = np.zeros(len(blk), dtype=np.uint64)
    for i in range(6):
        v |= blk[:, 2 + i].astype(np.uint64) << np.uint64(8 * i)
    sel = np.stack([(v >> np.uint64(3 * i)) & np.uint64(7) for i in range(16)], 1).astype(np.int64)
    return np.take_along_axis(lut, sel, 1)


def _alpha3(blk: np.ndarray) -> np.ndarray:
    nib = np.stack([blk[:, :8] & 15, blk[:, :8] >> 4], -1).reshape(len(blk), 16)
    return nib.astype(np.float32) * 17


def mip0(b: bytes) -> np.ndarray:
    """(h, w, 4) float32 RGBA 0..255 of the top mip of a DXT1/3/5 (or 32-bit uncompressed) DDS."""
    hd = header(b)
    w, h, fc = hd["w"], hd["h"], hd["fourcc"]
    if fc == "" and hd["bits"] == 32:
        a = np.frombuffer(b, np.uint8, w * h * 4, 128).reshape(h, w, 4)[..., [2, 1, 0, 3]]
        return a.astype(np.float32)
    bs = 8 if fc == "DXT1" else 16
    if fc not in ("DXT1", "DXT3", "DXT5"):
        raise ValueError(f"unsupported DDS format {fc!r}")
    nb = max(1, w // 4) * max(1, h // 4)
    blk = np.frombuffer(b, np.uint8, nb * bs, 128).reshape(nb, bs)
    if fc == "DXT1":
        rgb, a = _color(blk, True)
    else:
        rgb, _ = _color(blk[:, 8:], False)
        a = _alpha3(blk[:, :8]) if fc == "DXT3" else _alpha5(blk[:, :8])
    px = np.concatenate([rgb, a[:, :, None]], -1).reshape(h // 4, w // 4, 4, 4, 4)
    return px.transpose(0, 2, 1, 3, 4).reshape(h, w, 4)
