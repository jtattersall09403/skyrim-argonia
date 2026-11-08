#!/usr/bin/env python3
"""The standing backstep cut to its first push (owner rulings 2026-11-08, walk 3).

Dynamic Dodge's backstep (`TKDodge/StepDodgeBack.hkx`, laid by our 80xxx OAR submods as `DodgeBack.hkx`) moves the
actor by AMR `animmotion X Y Z` annotations: the root's position in game units at each annotation's time. Its
travel comes in two pushes; the owner wants only the first, and the clip itself to end there ("holding the keys
while the clip plays whole looks stupid"). This cuts the clip in place: the hkaAnimation's `duration` becomes the
first push's last key time (0.333 s of 0.933 s), and each annotation track's count drops the annotations after it
(the motion keys and the 0.6 s footstep). The spline track data is left whole: Havok samples it by frame time
(`frameDuration`, `blockDuration`), so the poses up to the new duration are the author's own, and the behaviour's
clip generator ends the clip at `duration`. No byte moves: the annotations are put in time order by rewriting
their time floats and their text pointers' fixup targets, then each track's size drops, so every packfile offset
stays valid. A derived file, made at stage time from the player's own download
(decision 0003); never committed.

    backstep.py measure <hkx>...      each clip's duration, motion keys and pushes
    backstep.py cut <in> <out>        write <out> cut at the end of the first push
"""
from __future__ import annotations

import struct
import sys

UNITS_PER_M = 70.0  # Skyrim: 1 unit = 1/70 m (CK wiki "Unit")
GAP = 0.08          # a push ends where the motion keys stop for longer than this (seconds)
EPS = 1e-4


class Clip:
    """The hk 2010 64-bit packfile's one animation: its duration offset and annotation tracks."""

    def __init__(self, b: bytes):
        if b[:4] != b"\x57\xe0\xe0\x57" or b[16] != 8:
            raise ValueError("not a 64-bit Havok binary packfile")
        self.b = b
        i = b.find(b"__data__\x00")
        start, local, glob, virt, exports = struct.unpack_from("<5i", b, i + 20)
        self.start = start
        self.fix, self.fix_at = {}, {}
        for k in range(start + local, start + glob, 8):
            src, dst = struct.unpack_from("<2i", b, k)
            if src >= 0:
                self.fix[src], self.fix_at[src] = dst, k
        c = b.find(b"__classnames__\x00")
        cstart = struct.unpack_from("<i", b, c + 20)[0]
        self.anim = None
        for k in range(start + virt, start + exports, 12):
            src, _, name = struct.unpack_from("<3i", b, k)
            if src >= 0 and b[cstart + name:b.index(b"\x00", cstart + name)].endswith(b"Animation") \
                    and b"Binding" not in b[cstart + name:cstart + name + 40]:
                self.anim = src
        if self.anim is None:
            raise ValueError("no animation object")
        # hkaAnimation (64-bit): vtable 8, hkReferencedObject 8, type 4, duration 4, transform/float track counts,
        # extractedMotion 8, then annotationTracks {ptr 8, size 4, cap 4}; a track is {name 8, annotations 16}
        # and an annotation {float time, pad 4, char* text}
        self.dur_at = start + self.anim + 20
        self.tracks = self.fix.get(self.anim + 40)
        self.ntracks = struct.unpack_from("<i", b, start + self.anim + 48)[0] if self.tracks is not None else 0

    @property
    def duration(self) -> float:
        return struct.unpack_from("<f", self.b, self.dur_at)[0]

    def track_items(self):
        """(count offset, [(time, text)]) of each annotation track in slot order, the count honoured."""
        out = []
        for i in range(self.ntracks):
            o = self.tracks + 24 * i
            n = struct.unpack_from("<i", self.b, self.start + o + 16)[0]
            items = []
            for j in range(n):
                a = self.fix[o + 8] + 16 * j
                t = struct.unpack_from("<f", self.b, self.start + a)[0]
                s = self.start + self.fix[a + 8]
                items.append((t, self.b[s:self.b.index(b"\x00", s)].decode()))
            out.append((self.start + o + 16, items))
        return out


def keys(b: bytes) -> list[tuple[float, float, float, float]]:
    """(time, x, y, z) of each motion key."""
    ks = [(t, *map(float, txt.split()[1:4])) for _, items in Clip(b).track_items() for t, txt in items
          if txt.startswith("animmotion ")]
    return sorted(ks)


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
    """The clip ending at its first push's last key; (bytes, old travel, new) in units. Idempotent."""
    ks = keys(b)
    if not ks:
        raise ValueError("no animmotion annotations")
    end = ks[pushes(ks)[0][1]]
    clip = Clip(b)
    out = bytearray(b)
    struct.pack_into("<f", out, clip.dur_at, min(end[0], clip.duration))
    for i, (at, items) in enumerate(clip.track_items()):
        # the author's annotations are not in time order: sort the slots (each slot's time float and its text
        # pointer's fixup target, so no string moves), then keep the slots up to the cut
        base = clip.fix.get(clip.tracks + 24 * i + 8)
        slots = [base + 16 * j for j in range(len(items))]
        order = sorted(range(len(items)), key=lambda j: items[j][0])
        targets = [clip.fix[a + 8] for a in slots]
        for a, j in zip(slots, order):
            struct.pack_into("<f", out, clip.start + a, items[j][0])
            struct.pack_into("<i", out, clip.fix_at[a + 8] + 4, targets[j])
        struct.pack_into("<i", out, at, sum(t <= end[0] + EPS for t, _ in items))
    return bytes(out), abs(ks[-1][2]), abs(end[2])


def describe(b: bytes) -> str:
    ks = keys(b)
    if not ks:
        return "no animmotion"
    dist = lambda i, j: ((ks[j][1] - ks[i][1]) ** 2 + (ks[j][2] - ks[i][2]) ** 2) ** 0.5 / UNITS_PER_M
    parts = [f"{ks[a][0]:.3f}-{ks[z][0]:.3f}s to {dist(0, z):.2f} m" for a, z in pushes(ks)]
    other = [f"{t:.3f}s {txt}" for _, items in Clip(b).track_items() for t, txt in items
             if not txt.startswith("animmotion ")]
    return (f"duration {Clip(b).duration:.3f}s; travel {dist(0, len(ks) - 1):.2f} m by {ks[-1][0]:.3f}s; "
            f"key runs: " + "; ".join(parts) + "; other: " + (", ".join(other) or "none"))


def main(argv: list[str]) -> int:
    if len(argv) >= 2 and argv[0] == "measure":
        for p in argv[1:]:
            print(p, "|", describe(open(p, "rb").read()))
        return 0
    if len(argv) == 3 and argv[0] == "cut":
        data, old, new = cut(open(argv[1], "rb").read())
        open(argv[2], "wb").write(data)
        print(f"backstep: {old / UNITS_PER_M:.2f} m -> {new / UNITS_PER_M:.2f} m, {Clip(data).duration:.3f}s")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
