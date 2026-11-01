import struct

import numpy as np

from tools.argonia_world.vanilla.load import heights, subs
from tools.argonia_world.vanilla.measure import chamfer


def test_vhgt_decodes_offset_and_deltas():
    d = np.zeros((33, 33), np.int8)
    d[0, 0], d[1, 0], d[0, 1] = 2, 1, 3
    h = heights(struct.pack("<f", 10.0) + d.tobytes() + b"\0\0\0")
    assert h[0, 0] == (10 + 2) * 8 and h[0, 1] == (12 + 3) * 8 and h[1, 0] == 13 * 8 and h[1, 1] == 13 * 8


def test_subrecords_honour_xxxx():
    big = b"A" * 70000
    body = b"XXXX" + struct.pack("<HI", 4, len(big)) + b"DATA" + struct.pack("<H", 0) + big
    assert subs(body) == [(b"DATA", big)]


def test_chamfer_counts_vertex_steps():
    m = np.zeros((5, 5), bool)
    m[2, 2] = True
    d = chamfer(m, 3)
    assert d[2, 2] == 0 and d[0, 0] == 2 and d[2, 4] == 2
