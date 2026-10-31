"""Wind UI's frame retint (1.12 §3): colours only, bounds kept, knots cleared; tokens from theme.css."""
import struct

import numpy as np

from tools.ui_theme import swf, windui


def _shape(cid: int, rgba: tuple[int, int, int, int]) -> swf.Tag:
    """A DefineShape3 with one solid fill and no edges."""
    rect = swf.rect(0, 200, 0, 200)
    body = struct.pack("<H", cid) + rect + bytes([1, 0x00, *rgba]) + bytes([0]) + bytes([0x10]) + b"\x00"
    return swf.Tag(32, body, True)


def test_ramp_maps_grey_to_trim_and_clears_knots():
    stops = windui.ramp({"frame-ground": (14, 19, 13), "frame-trim": (111, 106, 53), "frame-trim-hi": (181, 168, 98)})
    m = swf.Movie(b"FWS", 8, b"", [_shape(1, (153, 153, 153, 255)), _shape(2, (255, 255, 255, 255))])
    before = [swf.read_rect(swf.BitReader(t.data, 2)) for t in m.tags]
    n, cleared = windui.retint(m, {2: "knot"}, stops)
    assert (n, cleared) == (2, [2])
    (o1,), _ = swf.shape_colours(m.tags[0])
    grey = np.array(list(m.tags[0].data[o1:o1 + 3]))
    assert grey[1] > grey[2] + 20  # gold-green, not grey
    (o2,), _ = swf.shape_colours(m.tags[1])
    assert m.tags[1].data[o2 + 3] == 0
    assert [swf.read_rect(swf.BitReader(t.data, 2)) for t in m.tags] == before
