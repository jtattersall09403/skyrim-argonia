#!/usr/bin/env python3
"""LODSettings for the worlds whose terrain LOD ships without one (the map, docs/phases/4-first-act-built.md W-wrld-map).

The engine reads `Data\\LODSettings\\<world editor id>.lod` to place a world's terrain LOD, and the world map is drawn
from that LOD. BM&V ships .btr terrain for BlackMarsh, BlackMarsh2, BlackMarshNorth and Valenwood but a .lod for
Valenwood alone. The file is 16 bytes, little-endian: int16 south-west cell x, int16 south-west cell y, int32 stride
in cells (a power of two covering the level-32 chunks), int32 lowest level (4), int32 highest level (32); Valenwood's
own (-32,-32, 128, 4, 32) is what this rule gives from its .btr names. A derived file, made in the staged profile
from the player's mods by `stack.py stage` (decision 0014); never committed.

    lodsettings.py <mods dir> <out dir>    write <out>/LODSettings/<World>.lod for each world that lacks one
"""
from __future__ import annotations

import pathlib
import re
import struct
import sys

BTR = re.compile(r"^(?P<w>.+)\.(?P<l>\d+)\.(?P<x>-?\d+)\.(?P<y>-?\d+)\.btr$", re.I)


def settings(names: list[str]) -> bytes | None:
    """The .lod bytes for one world from its .btr file names (world.level.x.y.btr), or None without any."""
    chunks = [(int(m["l"]), int(m["x"]), int(m["y"])) for m in map(BTR.match, names) if m]
    if not chunks:
        return None
    top, low = max(c[0] for c in chunks), min(c[0] for c in chunks)
    big = [(x, y) for lvl, x, y in chunks if lvl == top]
    x0, y0 = min(x for x, _ in big), min(y for _, y in big)
    span = max(max(x for x, _ in big) - x0, max(y for _, y in big) - y0) + top
    stride = 1
    while stride < span:
        stride *= 2
    return struct.pack("<hhiii", x0, y0, stride, low, top)


def derive(mods: pathlib.Path, out: pathlib.Path) -> dict[str, bytes]:
    """Every world with .btr terrain under a mod's meshes/terrain/<World>/ and no LODSettings/<World>.lod in any
    mod: its .lod written under <out>/LODSettings. Returns {world: bytes}."""
    have, worlds = set(), {}
    for mod in sorted(p for p in mods.iterdir() if p.is_dir() and p.resolve() != out.resolve() and p.name != "argonia-lodsettings"):
        for d in mod.iterdir():
            if d.name.lower() == "lodsettings" and d.is_dir():
                have |= {f.stem.lower() for f in d.iterdir() if f.suffix.lower() == ".lod"}
            elif d.name.lower() == "meshes" and d.is_dir():
                for t in (t for t in d.iterdir() if t.name.lower() == "terrain" and t.is_dir()):
                    for w in (w for w in t.iterdir() if w.is_dir()):
                        names = [f.name for f in w.iterdir() if f.name.lower().startswith(w.name.lower() + ".")]
                        if names:
                            worlds.setdefault(w.name, []).extend(names)
    made = {}
    for w, names in sorted(worlds.items()):
        b = settings(names)
        if b is not None and w.lower() not in have:
            (out / "LODSettings").mkdir(parents=True, exist_ok=True)
            (out / "LODSettings" / f"{w}.lod").write_bytes(b)
            made[w] = b
    return made


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    for w, b in derive(pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])).items():
        print(w, struct.unpack("<hhiii", b))
