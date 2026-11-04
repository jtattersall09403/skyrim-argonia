"""The LOD archive's key (infra/gpu-box/lod.sh): the sha256 of what the LOD is made from, never the whole ESM's.

LOD (xLODGen terrain, DynDOLOD objects) reads the world's LAND, CELL, WRLD and placed refs, and the tools' versions;
it never reads the navmesh. So the key hashes every record of ArgoniaWorld.esm but NAVM, NAVI and the TES4 header
(whose record count moves with the NAVM count), each as type, FormID, flags (bar compression) and decompressed data,
plus the salt files (the LOD tools' manifest pins, lod.ps1, the preset). A navmesh-only rebuild keeps the key; a
moved ref or a changed height moves it (decision 0037: a key names its inputs, not a superset).

    python -m tools.navmesh.lodkey <ArgoniaWorld.esm> [--salt <text>]... [--salt-file <path>]...   prints 12 hex
"""
from __future__ import annotations

import argparse
import hashlib
import struct
import sys
from pathlib import Path

from tools.navmesh.esm import COMPRESSED, records

NOT_LOD = {b"NAVM", b"NAVI", b"TES4"}


def lod_key(esm: Path, salts: list[bytes] = ()) -> str:
    h = hashlib.sha256(b"argonia-lod-key/1\n")
    for s in salts:
        h.update(struct.pack("<I", len(s)) + s)
    for r in records(esm, None):
        if r.sig in NOT_LOD:
            continue
        h.update(r.sig + struct.pack("<III", r.fid, r.flags & ~COMPRESSED, len(r.data)) + r.data)
    return h.hexdigest()[:12]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="lodkey")
    ap.add_argument("esm", type=Path)
    ap.add_argument("--salt", action="append", default=[])
    ap.add_argument("--salt-file", action="append", default=[], type=Path)
    a = ap.parse_args(argv)
    salts = [s.encode() for s in a.salt] + [p.read_bytes() for p in a.salt_file]
    print(lod_key(a.esm, salts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
