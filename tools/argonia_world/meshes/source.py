"""A mod's mesh by its Data path: the loose file in the staged mod folder, else the mod's own BSAs (v105, lz4 frames
decoded here in pure Python so the build VM needs no wheel). Reads only; nothing read is ever written to the repo."""
from __future__ import annotations

import struct
from pathlib import Path


def lz4_frame(b: bytes) -> bytes:
    if b[:4] != b"\x04\x22\x4d\x18":
        raise ValueError("not an lz4 frame")
    flg = b[4]
    o = 6 + (8 if flg & 0x08 else 0) + (4 if flg & 0x01 else 0) + 1
    out = bytearray()
    while True:
        n, = struct.unpack_from("<I", b, o)
        o += 4
        if n == 0:
            return bytes(out)
        raw, n = n & 0x80000000, n & 0x7FFFFFFF
        blk = b[o:o + n]
        o += n + (4 if flg & 0x10 else 0)
        if raw:
            out += blk
        else:
            _block(blk, out)


def _block(s: bytes, out: bytearray) -> None:
    i, n = 0, len(s)
    while i < n:
        tok = s[i]; i += 1
        ln = tok >> 4
        if ln == 15:
            while True:
                x = s[i]; i += 1; ln += x
                if x != 255:
                    break
        out += s[i:i + ln]; i += ln
        if i >= n:
            return
        off = s[i] | s[i + 1] << 8; i += 2
        ml = tok & 15
        if ml == 15:
            while True:
                x = s[i]; i += 1; ml += x
                if x != 255:
                    break
        ml += 4
        st = len(out) - off
        if off >= ml:
            out += out[st:st + ml]
        else:
            for k in range(ml):
                out.append(out[st + k])


def _bsa_index(path: Path) -> tuple[int, dict]:
    with path.open("rb") as f:
        h = f.read(36)
        _, ver, off, flags, nf, nfiles, _, tfn, _ = struct.unpack_from("<4sIIIIIIII", h, 0)
        rec = 24 if ver >= 105 else 16
        f.seek(off)
        fr = f.read(nf * rec)
        counts = [struct.unpack_from("<I", fr, i * rec + 8)[0] for i in range(nf)]
        body = f.read(sum(counts) * 16 + nf * 256 + tfn)
    o, recs = 0, []
    for c in counts:
        ln = body[o]
        d = body[o + 1:o + ln].rstrip(b"\0").decode("latin-1")
        o += 1 + ln
        recs += [(d, *struct.unpack_from("<QII", body, o + 16 * j)[1:]) for j in range(c)]
        o += 16 * c
    names = body[o:o + tfn].split(b"\0")
    return flags, {(d + "\\" + nm.decode("latin-1")).lower().replace("\\", "/"): (sz, fo)
                   for (d, sz, fo), nm in zip(recs, names)}


_IDX: dict = {}


def read(mod_dir: Path, rel: str) -> bytes:
    rel = rel.lower().replace("\\", "/")
    loose = {str(p.relative_to(mod_dir)).lower().replace("\\", "/"): p for p in mod_dir.rglob("*.nif")} \
        if mod_dir not in _IDX else None
    if loose is not None:
        _IDX[mod_dir] = (loose, [(b, *_bsa_index(b)) for b in sorted(mod_dir.glob("*.bsa"))])
    loose, bsas = _IDX[mod_dir]
    if rel in loose:
        return loose[rel].read_bytes()
    for b, flags, idx in bsas:
        if rel in idx:
            sz, fo = idx[rel]
            comp = bool(flags & 4) ^ bool(sz & 0x40000000)
            sz &= 0x3FFFFFFF
            with b.open("rb") as f:
                f.seek(fo)
                d = f.read(sz)
            if flags & 0x100:
                d = d[1 + d[0]:]
            return lz4_frame(d[4:]) if comp else d
    raise FileNotFoundError(f"{rel} not in {mod_dir}")
