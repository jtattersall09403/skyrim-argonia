"""The BM&V map's own pieces, without game files: the VHGT decode, the PNG writer, our markers' read."""
import struct

import numpy as np

from tools.bmv_map import build


def test_vhgt_decode():
    d = np.zeros((33, 33), np.int8)
    d[0, 0], d[1, 0], d[0, 1] = 2, 1, 3          # column 0 runs north from the offset; each row runs east
    h = build.vhgt(struct.pack("<f", 10.0) + d.tobytes() + b"\0\0\0")
    assert h[0, 0] == (10 + 2) * 8 and h[1, 0] == (10 + 3) * 8 and h[0, 1] == (10 + 2 + 3) * 8 and h[0, 32] == h[0, 1]


def test_png_round_trip():
    img = np.random.default_rng(1).integers(0, 256, (7, 5, 4), dtype=np.uint8)
    b = build.png(img)
    assert b[:8] == b"\x89PNG\r\n\x1a\n" and (build.unpng(b) == img).all()


def test_opening_marker_read_from_plugin():
    m = [x for x in build.markers() if x["edid"] == "ARG_OpeningMarker"]
    assert len(m) == 1 and m[0]["ws"] == "23D689:Black Marsh.esm" and (m[0]["x"], m[0]["y"]) == (30901.0, -2903.0)
