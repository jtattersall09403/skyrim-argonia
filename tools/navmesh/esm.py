"""A read-only walk over a plugin's records (Skyrim SE layout), enough to read NAVM, NAVI and CELL.

The layout (UESP `Skyrim_Mod:Mod_File_Format`, xEdit `wbDefinitionsTES5.pas`): a record header is 24 bytes (type,
data size, flags, FormID, VCS, form version, VCS2); a GRUP header is 24 bytes (`GRUP`, total size, label, group type,
stamp, unknown). A record with flag 0x00040000 is zlib-compressed: a u32 uncompressed size, then the stream.
A subrecord is type, u16 size, data; an `XXXX` subrecord of 4 bytes carries the real size of the next one, whose own
u16 size is then 0. The game files are read in place (memory-mapped), never copied into the repo (decision 0003).
"""
from __future__ import annotations

import mmap
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path

COMPRESSED = 0x00040000
GROUP_CELL_TEMPORARY = 9
GROUP_CELL_CHILDREN = 6
GROUP_WORLD_CHILDREN = 1


@dataclass
class Record:
    sig: bytes
    flags: int
    fid: int
    vcs1: int
    version: int
    vcs2: int
    data: bytes  # the subrecords, decompressed
    raw_size: int  # the data size as stored (compressed or not)
    parents: tuple  # enclosing (group type, label) pairs, outermost first
    cell: int | None  # FormID of the CELL a cell-children group belongs to


def subrecords(data: bytes):
    """(type, payload) for each subrecord, honouring XXXX."""
    i, big = 0, None
    while i < len(data):
        sig = data[i:i + 4]
        size = struct.unpack_from("<H", data, i + 4)[0]
        i += 6
        if sig == b"XXXX":
            big = struct.unpack_from("<I", data, i)[0]
            i += size
            continue
        if big is not None:
            size, big = big, None
        yield sig, data[i:i + size]
        i += size


def pack_subrecord(sig: bytes, payload: bytes) -> bytes:
    if len(payload) > 0xFFFF:
        return b"XXXX" + struct.pack("<HI", 4, len(payload)) + sig + struct.pack("<H", 0) + payload
    return sig + struct.pack("<H", len(payload)) + payload


def records(path: Path, want: set[bytes], groups: set[bytes] | None = None):
    """Every record whose type is in `want`, in file order. `groups`: the top-level group labels to enter (None:
    all); the rest are skipped by size, which is what keeps a walk of Skyrim.esm fast."""
    with open(path, "rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as m:
        end = len(m)
        stack: list[tuple[int, int, bytes]] = []  # (end offset, group type, label)
        cell: int | None = None
        i = 0
        while i < end:
            while stack and i >= stack[-1][0]:
                stack.pop()
            sig = m[i:i + 4]
            if sig == b"GRUP":
                size, label, gtype = struct.unpack_from("<I4si", m, i + 4)
                if not stack and groups is not None and label not in groups:
                    i += size
                    continue
                if gtype == GROUP_CELL_CHILDREN:
                    cell = struct.unpack("<I", label)[0]
                stack.append((i + size, gtype, label))
                i += 24
                continue
            size, flags, fid, vcs1, version, vcs2 = struct.unpack_from("<IIIIHH", m, i + 4)
            if sig in want:
                raw = m[i + 24:i + 24 + size]
                data = zlib.decompress(raw[4:]) if flags & COMPRESSED else bytes(raw)
                in_cell = any(g in (GROUP_CELL_CHILDREN, GROUP_CELL_TEMPORARY) for _, g, _ in stack)
                yield Record(sig, flags, fid, vcs1, version, vcs2, data, size,
                             tuple((g, lab) for _, g, lab in stack), cell if in_cell else None)
            i += 24 + size


def masters(path: Path) -> list[str]:
    """The plugin's master file names (TES4 MAST), in order."""
    with open(path, "rb") as f:
        head = f.read(24)
        size = struct.unpack_from("<I", head, 4)[0]
        data = f.read(size)
    return [p[:-1].decode("cp1252") for s, p in subrecords(data) if s == b"MAST"]
