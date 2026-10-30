#!/usr/bin/env python3
"""ARG_Province's LODSettings file (2.W4 §c; game-12): xLODGen lists a worldspace only when
Data\\LODSettings\\<WRLD>.lod exists, and the game reads the same file to place the LOD. Made on the build VM from the
land the plugin build wrote (out/terrain/land/cy*.jsonl.gz: one cell per line, x and y), never committed (0014).

The format (16 bytes, little-endian; Skyrim.esm's Tamriel.lod is SW -64,-64, stride 128, levels 4..32):
  int16 SW cell x, int16 SW cell y, int32 stride (cells on a side, a power of two), int32 lowest level, int32 highest.
The SW corner is aligned to the highest level's 32-cell blocks, so a level-32 block's name (e.g. FWMF's map block
arg_province.32.0.0) keeps its cell, and the stride covers every cell.

    lodsettings.py [out/terrain/land] [out/lod/ARG_Province.lod]
"""
import gzip
import json
import pathlib
import struct
import sys

LEVEL_MIN, LEVEL_MAX = 4, 32


def settings(cells) -> tuple[int, int, int]:
    """(sw_x, sw_y, stride) covering every (x, y) cell, the corner aligned to LEVEL_MAX."""
    cells = list(cells)
    if not cells:
        raise ValueError("no cells")
    xs, ys = [c[0] for c in cells], [c[1] for c in cells]
    sw_x, sw_y = (min(xs) // LEVEL_MAX) * LEVEL_MAX, (min(ys) // LEVEL_MAX) * LEVEL_MAX
    span = max(max(xs) - sw_x, max(ys) - sw_y) + 1
    stride = LEVEL_MAX
    while stride < span:
        stride *= 2
    return sw_x, sw_y, stride


def encode(sw_x: int, sw_y: int, stride: int) -> bytes:
    return struct.pack("<hhiii", sw_x, sw_y, stride, LEVEL_MIN, LEVEL_MAX)


def land_cells(land: pathlib.Path):
    for f in sorted(land.glob("cy*.jsonl.gz")):
        with gzip.open(f, "rt") as fh:
            for line in fh:
                r = json.loads(line)
                yield r["x"], r["y"]


def main(argv):
    land = pathlib.Path(argv[0] if argv else "out/terrain/land")
    out = pathlib.Path(argv[1] if len(argv) > 1 else "out/lod/ARG_Province.lod")
    sw_x, sw_y, stride = settings(land_cells(land))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(encode(sw_x, sw_y, stride))
    print(f"{out}: SW {sw_x},{sw_y}, stride {stride}, levels {LEVEL_MIN}..{LEVEL_MAX}")


if __name__ == "__main__":
    main(sys.argv[1:])
