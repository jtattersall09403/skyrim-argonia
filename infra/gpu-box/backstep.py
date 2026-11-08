#!/usr/bin/env python3
"""The standing backstep cut to its first push (owner ruling 2026-11-08).

Dynamic Dodge's backstep (`TKDodge/StepDodgeBack.hkx`, laid by our 80xxx OAR submods as `DodgeBack.hkx`) moves the
actor by AMR `animmotion X Y Z` annotations: the root's position in game units at each annotation's time. Its
travel comes in two pushes; the owner wants only the first. This rewrites, in place, every `animmotion` after the
first push's end to hold that end position, so the clip plays whole (no idle gap, its sounds kept) but travels
only the first push. The new number text is right-padded with spaces to the old text's length, so no offset in
the Havok packfile moves (AMR splits the line on spaces). A derived file, made at stage time from the player's own
download (decision 0003); never committed.

    backstep.py measure <hkx>...      each clip's motion keys (time, y) and its pushes
    backstep.py cut <in> <out>        write <out> with the travel cut after the first push
"""
from __future__ import annotations

import struct
import sys

UNITS_PER_M = 70.0  # Skyrim: 1 unit = 1/70 m (CK wiki "Unit")
GAP = 0.08          # a push ends where the motion keys stop for longer than this (seconds)


def _data_section(b: bytes) -> tuple[int, int, int]:
    """(data start, local fixups start, global fixups start) of the hk 2010 packfile's __data__ section."""
    i = b.find(b"__data__\x00")
    if i < 0 or b[:4] != b"\x57\xe0\xe0\x57":
        raise ValueError("not a Havok binary packfile")
    start, local, glob = struct.unpack_from("<3i", b, i + 20)
    return start, start + local, start + glob


def annotations(b: bytes) -> list[tuple[float, int, str]]:
    """(time, absolute string offset, text) of each `animmotion` annotation, by time. An hkaAnnotationTrack
    annotation is {float time; pad; char* text}: the text pointer is a local fixup whose source is 8 bytes after
    the time."""
    start, lf, gf = _data_section(b)
    out = []
    for k in range(lf, gf, 8):
        src, dst = struct.unpack_from("<2i", b, k)
        if src < 0:
            break
        s = start + dst
        if b.startswith(b"animmotion ", s):
            text = b[s:b.index(b"\x00", s)].decode()
            out.append((struct.unpack_from("<f", b, start + src - 8)[0], s, text))
    return sorted(out)


def keys(b: bytes) -> list[tuple[float, float, float, float]]:
    """(time, x, y, z) of each motion key."""
    return [(t, *map(float, txt.split()[1:4])) for t, _, txt in annotations(b)]


def pushes(ks: list[tuple[float, float, float, float]]) -> list[tuple[int, int]]:
    """(first, last) key index of each push: runs of keys no more than GAP seconds apart. The author keys a push
    densely (every 1-2 frames) and the stride between pushes sparsely; StepDodgeBack's first push is 0 to 0.333 s
    (keys 0.017-0.05 s apart), then one 0.1 s gap."""
    runs, a = [], 0
    for i in range(1, len(ks)):
        if ks[i][0] - ks[i - 1][0] > GAP:
            runs.append((a, i - 1))
            a = i
    return runs + [(a, len(ks) - 1)]


def cut(b: bytes) -> tuple[bytes, float, float]:
    """The clip with every key after the first push holding the first push's end; (bytes, old travel, new) in
    units. The held key's own text is reused, right-padded with spaces to each replaced text's length."""
    ann = annotations(b)
    if not ann:
        raise ValueError("no animmotion annotations")
    ks = keys(b)
    end = pushes(ks)[0][1]
    hold = ann[end][2]
    out = bytearray(b)
    for _, s, txt in ann[end + 1:]:
        if len(hold) > len(txt):
            raise ValueError(f"'{hold}' is longer than '{txt}'")
        out[s:s + len(txt)] = hold.ljust(len(txt)).encode()
    return bytes(out), abs(ks[-1][2]), abs(ks[end][2])


def describe(b: bytes) -> str:
    ks = keys(b)
    if not ks:
        return "no animmotion"
    dist = lambda i, j: ((ks[j][1] - ks[i][1]) ** 2 + (ks[j][2] - ks[i][2]) ** 2) ** 0.5 / UNITS_PER_M
    parts = [f"{ks[a][0]:.3f}-{ks[z][0]:.3f}s to {dist(0, z):.2f} m" for a, z in pushes(ks)]
    return f"travel {dist(0, len(ks) - 1):.2f} m by {ks[-1][0]:.3f}s; key runs: " + "; ".join(parts)


def main(argv: list[str]) -> int:
    if len(argv) >= 2 and argv[0] == "measure":
        for p in argv[1:]:
            print(p, "|", describe(open(p, "rb").read()))
        return 0
    if len(argv) == 3 and argv[0] == "cut":
        data, old, new = cut(open(argv[1], "rb").read())
        open(argv[2], "wb").write(data)
        print(f"backstep: {old / UNITS_PER_M:.2f} m -> {new / UNITS_PER_M:.2f} m")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
