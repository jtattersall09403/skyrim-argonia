"""Read named files out of a Skyrim SE BSA (version 105, LZ4 frames; 104, zlib), through a byte-range reader.

The reader is `read(offset, length) -> bytes`: a local file (`local(path)`) or a range copied off the game machine
(infra/gpu-box/mesh_extract.py), so only the directory and the wanted files ever move, never the archive. The layout
is UESP's `Skyrim_Mod:Archive_File_Format` (tools/immersion/bsa.py lists names the same way). Extracted files stay
in $ARGONIA_PRIVATE and are never committed (decision 0003).
"""
from __future__ import annotations

import struct
import zlib
from collections.abc import Callable
from pathlib import Path

HEADER = struct.Struct("<4sIIIIIIII")  # magic, version, offset, archive flags, folders, files, folder names, file names, file flags
FOLDER = {104: struct.Struct("<QII"), 105: struct.Struct("<QIIQ")}
FILE = struct.Struct("<QII")  # hash, size (bit 30: compression toggled), offset
COMPRESSED, EMBED_NAMES = 0x4, 0x100

Reader = Callable[[int, int], bytes]


def local(path: Path) -> Reader:
    def read(off: int, n: int) -> bytes:
        with open(path, "rb") as f:
            f.seek(off)
            return f.read(n)
    return read


def lz4_block(src: bytes, out: bytearray) -> None:
    """Decode one LZ4 block (the format behind each frame block) onto `out`."""
    i, n = 0, len(src)
    while i < n:
        tok = src[i]
        i += 1
        lit = tok >> 4
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
        ml = tok & 15
        if ml == 15:
            while True:
                b = src[i]
                i += 1
                ml += b
                if b != 255:
                    break
        ml += 4
        start = len(out) - off
        if off >= ml:
            out += out[start:start + ml]
        else:
            for k in range(ml):
                out.append(out[start + k])


def lz4_frame(src: bytes) -> bytes:
    """An LZ4 frame (magic 0x184D2204): blocks until the end mark; checksums are not verified."""
    if struct.unpack_from("<I", src)[0] != 0x184D2204:
        raise ValueError("not an LZ4 frame")
    flg = src[4]
    i = 4 + 2 + (8 if flg & 0x08 else 0) + (4 if flg & 0x01 else 0) + 1
    out = bytearray()
    while True:
        size = struct.unpack_from("<I", src, i)[0]
        i += 4
        if size == 0:
            break
        raw, size = size & 0x80000000, size & 0x7FFFFFFF
        if raw:
            out += src[i:i + size]
        else:
            lz4_block(src[i:i + size], out)
        i += size + (4 if flg & 0x10 else 0)
    return bytes(out)


class Archive:
    """The directory of one BSA: lowercased path with forward slashes -> (offset, stored size, compressed)."""

    def __init__(self, read: Reader):
        self.read = read
        magic, self.version, offset, self.flags, nfolders, nfiles, _, names_len, _ = HEADER.unpack(read(0, HEADER.size))
        if magic != b"BSA\0" or self.version not in FOLDER:
            raise ValueError(f"not an SSE/LE BSA ({magic!r}, version {self.version})")
        rec = FOLDER[self.version]
        head = read(offset, rec.size * nfolders)
        counts = [rec.unpack_from(head, k * rec.size)[1] for k in range(nfolders)]
        size = sum(counts) * (FILE.size + 1) + nfolders * 256 + names_len  # an upper bound for the blocks + names
        blob = read(offset + len(head), size)
        o, files = 0, []
        for n in counts:
            ln = blob[o]
            folder = blob[o + 1:o + 1 + ln].rstrip(b"\0").decode("cp1252")
            o += 1 + ln
            for k in range(n):
                _, fsize, foff = FILE.unpack_from(blob, o + k * FILE.size)
                files.append((folder, fsize, foff))
            o += n * FILE.size
        names = blob[o:o + names_len].split(b"\0")[:nfiles]
        self.files = {}
        for (folder, fsize, foff), name in zip(files, names):
            key = f"{folder}\\{name.decode('cp1252')}".replace("\\", "/").lower()
            comp = bool(self.flags & COMPRESSED) != bool(fsize & 0x40000000)
            self.files[key] = (foff, fsize & 0x3FFFFFFF, comp)

    def get(self, path: str) -> bytes:
        foff, size, comp = self.files[path.replace("\\", "/").lower()]
        data = self.read(foff, size)
        if self.flags & EMBED_NAMES:
            data = data[1 + data[0]:]
        if not comp:
            return data
        body = data[4:]
        return lz4_frame(body) if self.version == 105 else zlib.decompress(body)
