"""The LOD archive's two keys (infra/gpu-box/lod.sh; owner ruling 2026-11-04 08:06, #37): the terrain LOD rebuilds
only when the land changed, the object LOD only when the placed objects or the forms they draw changed.

- terrain: every LAND record of ArgoniaWorld.esm (FormID, flags bar compression, decompressed data), salted with
  the terrain tool's pin (xlodgen), lod.ps1, lodsettings.py and the preset (lod.sh passes them).
- object: every REFR (the placed objects; ACHR actors draw no LOD) and every base form the plugin itself defines
  that a ref can draw (STAT, TREE, ...), plus the master list, salted with the object tools' pins (dyndolod,
  dyndolod-resources) and every stack mod's pin (the masters' forms and meshes come from those archives).
NAVM, NAVI, CELL (water height), WATR, WTHR, REGN, ECZN, NPC_, the levelled lists and the header are in neither:
a change to them lays the archive already made (decision 0037: a key names its inputs, never a superset).

    python -m tools.navmesh.lodkey <esm> [--terrain-salt T]... [--object-salt T]... [--*-salt-file P]...
    prints `terrain=<12 hex> object=<12 hex>`
"""
from __future__ import annotations

import argparse
import hashlib
import struct
import sys
from pathlib import Path

from tools.navmesh.esm import COMPRESSED, masters, records

TERRAIN = {b"LAND"}
OBJECT = {b"REFR", b"STAT", b"TREE", b"MSTT", b"SCOL", b"FURN", b"ACTI", b"DOOR", b"CONT", b"FLOR", b"LIGH",
          b"MISC", b"TXST", b"GRAS"}


def _h(tag: bytes, salts):
    h = hashlib.sha256(b"argonia-lod-key/2 " + tag + b"\n")
    for s in salts:
        h.update(struct.pack("<I", len(s)) + s)
    return h


def lod_keys(esm: Path, terrain_salts=(), object_salts=()) -> dict[str, str]:
    t = _h(b"terrain", terrain_salts)
    o = _h(b"object", list(object_salts) + ["\n".join(masters(esm)).encode()])
    for r in records(esm, TERRAIN | OBJECT):
        h = t if r.sig in TERRAIN else o
        h.update(r.sig + struct.pack("<III", r.fid, r.flags & ~COMPRESSED, len(r.data)) + r.data)
    return {"terrain": t.hexdigest()[:12], "object": o.hexdigest()[:12]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="lodkey")
    ap.add_argument("esm", type=Path)
    for half in ("terrain", "object"):
        ap.add_argument(f"--{half}-salt", action="append", default=[])
        ap.add_argument(f"--{half}-salt-file", action="append", default=[], type=Path)
    a = ap.parse_args(argv)
    salts = {h: [s.encode() for s in getattr(a, f"{h}_salt")] + [p.read_bytes() for p in getattr(a, f"{h}_salt_file")]
             for h in ("terrain", "object")}
    k = lod_keys(a.esm, salts["terrain"], salts["object"])
    print(f"terrain={k['terrain']} object={k['object']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
