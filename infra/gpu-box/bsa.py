#!/usr/bin/env python3
"""One file out of a Skyrim SE archive (BSA v105), stored or LZ4-compressed, in pure Python.

Used at stage time to lay a vanilla file from the player's own game (decision 0003: derived from the player's copy,
never committed), e.g. Skyrim's own DodgeBack.hkx as the standing backstep (owner walk 4, 2026-11-08).

    bsa.py <archive.bsa> <path inside> <out>
"""
from __future__ import annotations

import struct
import sys

COMPRESSED = 0x4      # archive flag: files compressed unless their size's toggle bit says otherwise
EMBED_NAMES = 0x100   # archive flag: each file's data starts with its full path as a bstring
TOGGLE = 0x40000000


def lz4_block(src: bytes, out: bytearray) -> None:
    """Decode one LZ4 block onto `out` (matches may reach into what earlier blocks wrote)."""
    i, n = 0, len(src)
    while i < n:
        token = src[i]
        i += 1
        lit = token >> 4
        if lit == 15:
            while True:
                b = src[i]
                i += 1
                lit += b
                if b != 255:
                    break
        out += src[i:i + lit]
        i += lit
        if i >= n:
            break
        off = src[i] | src[i + 1] << 8
        i += 2
        ml = token & 15
        if ml == 15:
            while True:
                b = src[i]
                i += 1
                ml += b
                if b != 255:
                    break
        ml += 4
        start = len(out) - off
        if off <= 0 or start < 0:
            raise ValueError("lz4: bad match offset")
        for k in range(ml):  # byte by byte: a match may overlap what it writes
            out.append(out[start + k])


def lz4_frame(b: bytes) -> bytes:
    if b[:4] != b"\x04\x22\x4d\x18":
        raise ValueError("not an LZ4 frame")
    flg = b[4]
    i = 6 + (8 if flg & 0x08 else 0) + (4 if flg & 0x01 else 0) + 1  # FLG, BD, content size, dict id, HC
    out = bytearray()
    while True:
        size = struct.unpack_from("<I", b, i)[0]
        i += 4
        if size == 0:
            break
        raw, size = size & 0x80000000, size & 0x7FFFFFFF
        if raw:
            out += b[i:i + size]
        else:
            lz4_block(b[i:i + size], out)
        i += size + (4 if flg & 0x10 else 0)
    return bytes(out)


def read_file(bsa_path: str, path: str) -> bytes:
    """`path` inside the archive (any case, / or \\); raises KeyError when absent."""
    path = path.replace("/", "\\").lower()
    folder, _, name = path.rpartition("\\")
    with open(bsa_path, "rb") as f:
        magic, version, _, flags, folders, _, _, names_len, _ = struct.unpack("<4sIIIIIIIH2x", f.read(36))
        if magic != b"BSA\0" or version != 105:
            raise ValueError(f"{bsa_path}: not a Skyrim SE archive")
        counts = [struct.unpack("<QIIQ", f.read(24))[1] for _ in range(folders)]
        records = []
        for count in counts:
            folder_name = f.read(f.read(1)[0])[:-1].decode().lower()
            for _ in range(count):
                _, size, offset = struct.unpack("<QII", f.read(16))
                records.append((folder_name, size, offset))
        names = f.read(names_len).split(b"\0")
        for (folder_name, size, offset), file_name in zip(records, names):
            if folder_name != folder or file_name.decode().lower() != name:
                continue
            packed = bool(flags & COMPRESSED) != bool(size & TOGGLE)
            f.seek(offset)
            data = f.read(size & ~TOGGLE & 0x3FFFFFFF)
            if flags & EMBED_NAMES:
                data = data[1 + data[0]:]
            if not packed:
                return data
            n = struct.unpack_from("<I", data)[0]
            out = lz4_frame(data[4:])
            if len(out) != n:
                raise ValueError(f"{path}: {len(out)} bytes unpacked, the archive says {n}")
            return out
    raise KeyError(f"{path} not in {bsa_path}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    with open(sys.argv[3], "wb") as o:
        o.write(read_file(sys.argv[1], sys.argv[2]))
