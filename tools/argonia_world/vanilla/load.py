"""Read Skyrim.esm's Tamriel exterior once into a local cache (decision 0034; nothing here enters git, 0003).

    tamriel()  -> dict with
        cells  {(x, y): {"fid", "water" (XCLW or None), "flags", "h" (33x33 float32 units) or None,
                         "vclr" (33x33x3 uint8) or None, "btxt" [4 LTEX fid], "atxt" [(quad, layer, ltex, alpha 289)]}}
        refs   list of (cell (x, y), base fid, x, y, z, rx, ry, rz, scale)
        forms  {fid: (sig, edid, obnd (x0,y0,z0,x1,y1,z1) or None, extra)}  base forms, LTEX, TXST, WTHR, REGN raw
        world  {"water": default water height, "land": default land height}
The cache lives at ~/.cache/argonia-vanilla/tamriel.pkl (game-derived: never committed).
"""
from __future__ import annotations

import os
import pickle
import struct
import zlib
from pathlib import Path

import numpy as np

from ..skyrim_units import CELL_UNITS, VERTEX_SPACING_UNITS

TAMRIEL = 0x3C
CACHE = Path.home() / ".cache" / "argonia-vanilla" / "tamriel.pkl"
BASE_SIGS = {b"STAT", b"TREE", b"FLOR", b"MSTT", b"ACTI", b"DOOR", b"FURN", b"CONT", b"LIGH", b"MISC", b"SCOL",
             b"LTEX", b"TXST", b"WTHR", b"REGN", b"GRAS", b"CLMT", b"IMGS", b"WRLD", b"LCTN"}


def data_dir() -> Path:
    root = os.environ.get("ARGONIA_GAME_ROOT")
    return (Path(root) / "Data") if root else Path.home() / "games" / "skyrimse" / "Data"


def subs(body: bytes) -> list[tuple[bytes, bytes]]:
    out, i, big = [], 0, None
    while i + 6 <= len(body):
        sig = body[i:i + 4]
        size = struct.unpack_from("<H", body, i + 4)[0]
        i += 6
        if sig == b"XXXX":
            big = struct.unpack_from("<I", body, i)[0]
            i += size
            continue
        if big is not None:
            size, big = big, None
        out.append((sig, body[i:i + size]))
        i += size
    return out


def heights(vhgt: bytes) -> np.ndarray:
    off = struct.unpack_from("<f", vhgt)[0]
    d = np.frombuffer(vhgt, np.int8, 1089, 4).reshape(33, 33).astype(np.float64)
    col0 = off + np.cumsum(d[:, 0])
    rows = col0[:, None] + np.concatenate([np.zeros((33, 1)), np.cumsum(d[:, 1:], axis=1)], axis=1)
    return (rows * 8).astype(np.float32)


def _edid(sb):
    for s, b in sb:
        if s == b"EDID":
            return b.rstrip(b"\0").decode("latin1")
    return ""


def parse(path: Path) -> dict:
    blob = path.read_bytes()
    cells, refs, forms, world = {}, [], {}, {}
    cur = {"cell": None, "wrld": None}

    def body_of(i, size, flags):
        b = blob[i + 24:i + 24 + size]
        return zlib.decompress(b[4:]) if flags & 0x40000 else b

    def walk(i, end, wrld):
        while i < end:
            sig = blob[i:i + 4]
            size = struct.unpack_from("<I", blob, i + 4)[0]
            if sig == b"GRUP":
                label, gtype = struct.unpack_from("<Ii", blob, i + 8)
                top = blob[i + 8:i + 12]
                if gtype == 0 and top not in BASE_SIGS and top != b"CELL":
                    i += size
                    continue
                w = label if gtype == 1 else wrld
                if gtype == 1 and label != TAMRIEL:
                    i += size
                    continue
                walk(i + 24, i + size, w)
                i += size
                continue
            flags, fid = struct.unpack_from("<II", blob, i + 8)
            if sig in BASE_SIGS:
                sb = subs(body_of(i, size, flags))
                ob = next((struct.unpack("<6h", b[:12]) for s, b in sb if s == b"OBND"), None)
                keep = sb if sig in (b"LTEX", b"TXST", b"WTHR", b"REGN", b"WRLD", b"GRAS", b"CLMT", b"IMGS") else None
                forms[fid] = (sig.decode(), _edid(sb), ob, keep)
                if sig == b"WRLD" and fid == TAMRIEL:
                    for s, b in sb:
                        if s == b"DNAM":
                            world["land"], world["water"] = struct.unpack("<2f", b[:8])
                        if s == b"MNAM":
                            world["mnam"] = b.hex()
                        if s == b"NAM0":
                            world["min"] = struct.unpack("<2f", b[:8])
                        if s == b"NAM9":
                            world["max"] = struct.unpack("<2f", b[:8])
            elif wrld == TAMRIEL and sig == b"CELL":
                sb = subs(body_of(i, size, flags))
                d = dict(sb)
                if b"XCLC" in d:
                    x, y = struct.unpack_from("<ii", d[b"XCLC"])
                    c = {"fid": fid, "flags": d.get(b"DATA", b"\0")[0],
                         "water": struct.unpack("<f", d[b"XCLW"])[0] if b"XCLW" in d else None,
                         "edid": _edid(sb), "h": None, "vclr": None, "btxt": [None] * 4, "atxt": [],
                         "regions": [struct.unpack_from("<I", d[b"XCLR"], k)[0] for k in range(0, len(d.get(b"XCLR", b"")), 4)]}
                    cells[(x, y)] = c
                    cur["cell"] = (x, y)
                else:
                    cur["cell"] = None
            elif wrld == TAMRIEL and sig == b"LAND" and cur["cell"] is not None:
                c = cells[cur["cell"]]
                sb = subs(body_of(i, size, flags))
                last = None
                for s, b in sb:
                    if s == b"VHGT":
                        c["h"] = heights(b)
                    elif s == b"VCLR":
                        c["vclr"] = np.frombuffer(b, np.uint8, 3267).reshape(33, 33, 3).copy()
                    elif s == b"BTXT":
                        t, q = struct.unpack_from("<IB", b)
                        c["btxt"][q] = t
                    elif s == b"ATXT":
                        t, q, _, layer = struct.unpack_from("<IBBH", b)
                        last = [q, layer, t, np.zeros(289, np.float32)]
                        c["atxt"].append(last)
                    elif s == b"VTXT" and last is not None:
                        for k in range(0, len(b), 8):
                            pos, _, op = struct.unpack_from("<HHf", b, k)
                            if pos < 289:
                                last[3][pos] = op
            elif wrld == TAMRIEL and sig in (b"REFR",) and cur["cell"] is not None:
                sb = subs(body_of(i, size, flags))
                d = dict(sb)
                if b"NAME" in d and b"DATA" in d:
                    p = struct.unpack("<6f", d[b"DATA"][:24])
                    sc = struct.unpack("<f", d[b"XSCL"])[0] if b"XSCL" in d else 1.0
                    pc = (int(np.floor(p[0] / CELL_UNITS)), int(np.floor(p[1] / CELL_UNITS)))  # persistent refs sit in one cell
                    refs.append((pc, struct.unpack("<I", d[b"NAME"])[0], *p, sc,
                                 b"XTEL" in d, flags))
            i += 24 + size

    walk(struct.unpack_from("<I", blob, 4)[0] + 24, len(blob), None)
    return {"cells": cells, "refs": refs, "forms": forms, "world": world}


def tamriel(rebuild: bool = False) -> dict:
    if CACHE.exists() and not rebuild:
        return pickle.loads(CACHE.read_bytes())
    t = parse(data_dir() / "Skyrim.esm")
    u = parse(data_dir() / "Update.esm")  # Update.esm overrides Tamriel cells (water heights, some LAND); refs stay Skyrim.esm's
    for k, c in u["cells"].items():
        base = t["cells"].setdefault(k, c)
        if base is not c:
            base["water"] = c["water"] if c["water"] is not None else base["water"]
            if c["h"] is not None:
                base.update({f: c[f] for f in ("h", "vclr", "btxt", "atxt")})
    t["update_cells"] = len(u["cells"])
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_bytes(pickle.dumps(t, protocol=5))
    return t


def ground(t: dict, x: float, y: float) -> float | None:
    """Bilinear ground height at world units (x, y); None outside LAND."""
    cx, cy = int(np.floor(x / CELL_UNITS)), int(np.floor(y / CELL_UNITS))
    c = t["cells"].get((cx, cy))
    if not c or c["h"] is None:
        return None
    u, v = (x - cx * CELL_UNITS) / VERTEX_SPACING_UNITS, (y - cy * CELL_UNITS) / VERTEX_SPACING_UNITS
    i, j = min(int(v), 31), min(int(u), 31)
    fu, fv = u - j, v - i
    h = c["h"]
    return float(h[i, j] * (1 - fu) * (1 - fv) + h[i, j + 1] * fu * (1 - fv) + h[i + 1, j] * (1 - fu) * fv + h[i + 1, j + 1] * fu * fv)


if __name__ == "__main__":
    import time
    t0 = time.time()
    t = tamriel(rebuild=True)
    print(len(t["cells"]), sum(c["h"] is not None for c in t["cells"].values()), len(t["refs"]), len(t["forms"]),
          t["world"], f"{time.time() - t0:.0f}s")
