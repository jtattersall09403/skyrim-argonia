"""A minimal PNG reader (8-bit greyscale, RGB or RGBA, non-interlaced) into a numpy array, so the old project's
colormaps load without Pillow on the build VM. Rows come back in file order (row 0 is the image's top)."""
from __future__ import annotations

import struct
import zlib
from pathlib import Path

import numpy as np

_CHANNELS = {0: 1, 2: 3, 4: 2, 6: 4}


def read(path: Path) -> np.ndarray:
    """The decoded image. Sub/Average/Paeth rows decode one pixel at a time (~20 s for the 3k ground tint), so the
    array is cached under ~/.cache/argonia/png keyed by the file's bytes (every build worker loaded it, 2026-11-01)."""
    import hashlib
    import os
    b = Path(path).read_bytes()
    cache = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "argonia" / "png"
    hit = cache / (hashlib.sha256(b).hexdigest()[:32] + ".npy")
    if hit.exists():
        return np.load(hit)
    out = _decode(path, b)
    try:
        cache.mkdir(parents=True, exist_ok=True)
        tmp = hit.with_suffix(f".{os.getpid()}.npy")
        np.save(tmp, out)
        tmp.replace(hit)
    except OSError:  # a read-only home: decode every time
        pass
    return out


def _decode(path: Path, b: bytes) -> np.ndarray:
    if b[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path}: not a PNG")
    i, idat, head = 8, [], None
    while i < len(b):
        n, t = struct.unpack(">I4s", b[i:i + 8])
        body = b[i + 8:i + 8 + n]
        if t == b"IHDR":
            head = struct.unpack(">IIBBBBB", body)
        elif t == b"IDAT":
            idat.append(body)
        elif t == b"IEND":
            break
        i += 12 + n
    w, h, depth, ctype, _, _, interlace = head
    if depth != 8 or interlace or ctype not in _CHANNELS:
        raise ValueError(f"{path}: only 8-bit non-interlaced grey/RGB/RGBA (got depth {depth} type {ctype})")
    ch = _CHANNELS[ctype]
    raw = np.frombuffer(zlib.decompress(b"".join(idat)), dtype=np.uint8).reshape(h, 1 + w * ch)
    out = np.zeros((h, w * ch), dtype=np.uint8)
    prev = np.zeros(w * ch, dtype=np.int32)
    for r in range(h):
        f, line = raw[r, 0], raw[r, 1:].astype(np.int32)
        if f == 0:
            cur = line
        elif f == 2:
            cur = (line + prev) & 0xFF
        else:  # Sub, Average and Paeth depend on the reconstructed left neighbour: one pixel at a time
            cur = np.zeros_like(line)
            for x in range(line.size):
                a = cur[x - ch] if x >= ch else 0
                if f == 1:
                    p = a
                elif f == 3:
                    p = (a + prev[x]) >> 1
                else:
                    bb, c = prev[x], prev[x - ch] if x >= ch else 0
                    pa, pb, pc = abs(bb - c), abs(a - c), abs(a + bb - 2 * c)
                    p = a if pa <= pb and pa <= pc else (bb if pb <= pc else c)
                cur[x] = (line[x] + p) & 0xFF
        out[r] = cur
        prev = cur
    return out.reshape(h, w, ch)


def write(path: Path, img: np.ndarray) -> Path:
    """uint8 (h, w) greyscale, (h, w, 3) RGB or (h, w, 4) RGBA -> a PNG (row 0 the image's top)."""
    a = np.ascontiguousarray(img, dtype=np.uint8)
    h, w = a.shape[:2]
    ch = 1 if a.ndim == 2 else a.shape[2]
    ctype = {1: 0, 3: 2, 4: 6}[ch]
    raw = np.concatenate([np.zeros((h, 1), np.uint8), a.reshape(h, w * ch)], axis=1).tobytes()

    def chunk(t: bytes, d: bytes) -> bytes:
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, ctype, 0, 0, 0))
                  + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))
    return p
