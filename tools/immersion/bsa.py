"""List the file paths inside a Skyrim SE BSA (version 104/105) without extracting anything.

Reads only the header, the folder and file records and the name block (a few hundred KB even for a 1.7 GB
archive); never file data (decision 0003).
"""
from __future__ import annotations

import struct
from pathlib import Path

_HEADER = struct.Struct("<4sIIIIIIII")  # magic, version, offset, archive flags, folders, files, folder names len, file names len, file flags
_FOLDER = {104: struct.Struct("<QII"), 105: struct.Struct("<QIIQ")}
_FILE = struct.Struct("<QII")
_NAMED_DIRS, _NAMED_FILES = 0x1, 0x2


def listing(path: str | Path) -> list[str]:
    """Every file path in the archive, lowercased, with forward slashes."""
    with open(path, "rb") as f:
        magic, version, offset, flags, nfolders, nfiles, _, names_len, _ = _HEADER.unpack(f.read(_HEADER.size))
        if magic != b"BSA\0" or version not in _FOLDER:
            raise ValueError(f"{path}: not an SSE/LE BSA (magic {magic!r}, version {version})")
        if not (flags & _NAMED_DIRS and flags & _NAMED_FILES):
            raise ValueError(f"{path}: archive has no name tables")
        f.seek(offset)
        rec = _FOLDER[version]
        counts = [rec.unpack(f.read(rec.size))[1] for _ in range(nfolders)]
        folders: list[tuple[str, int]] = []
        for n in counts:  # each folder block: bzstring folder name, then its file records
            ln = f.read(1)[0]
            folders.append((f.read(ln).rstrip(b"\0").decode("cp1252"), n))
            f.seek(_FILE.size * n, 1)
        names = f.read(names_len).split(b"\0")[:nfiles]  # the file name block follows; read only it
    out, k = [], 0
    for folder, n in folders:
        for _ in range(n):
            out.append(f"{folder}\\{names[k].decode('cp1252')}".replace("\\", "/").lower())
            k += 1
    if k != nfiles:
        raise ValueError(f"{path}: {k} names for {nfiles} files")
    return out
