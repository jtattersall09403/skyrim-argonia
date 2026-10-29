"""A minimal PNG reader (8-bit greyscale, RGB or RGBA, non-interlaced) into a numpy array, so the old project's
colormaps load without Pillow on the build VM. Rows come back in file order (row 0 is the image's top)."""
from __future__ import annotations

import struct
import zlib
from pathlib import Path

import numpy as np

_CHANNELS = {0: 1, 2: 3, 4: 2, 6: 4}


def read(path: Path) -> np.ndarray:
    b = Path(path).read_bytes()
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
