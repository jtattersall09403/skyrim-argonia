"""L1: the DDS reader the texture-set check measures with (texcheck.py): DXT1 colour and DXT5/DXT3 alpha."""
import struct

import numpy as np

from tools.argonia_world.terrain import dds


def _dds(fourcc: bytes, blocks: bytes, w=4, h=4) -> bytes:
    hd = bytearray(128)
    hd[:4] = b"DDS "
    struct.pack_into("<IIII", hd, 4, 124, 0x1007, h, w)
    struct.pack_into("<I", hd, 28, 1)
    struct.pack_into("<I", hd, 80, 4)
    hd[84:88] = fourcc
    return bytes(hd) + blocks


def test_dxt1_flat_normal_and_opaque_alpha():
    c = (16 << 11) | (32 << 5) | 31  # ~ (128, 128, 255): a flat normal
    px = dds.mip0(_dds(b"DXT1", struct.pack("<HHI", c, c, 0)))
    assert px.shape == (4, 4, 4) and (px[..., 3] == 255).all() and abs(px[..., 2].mean() - 255) < 1


def test_dxt5_and_dxt3_alpha():
    a5 = bytes([20, 20, 0, 0, 0, 0, 0, 0])
    c = struct.pack("<HHI", 0xFFFF, 0, 0)
    assert np.allclose(dds.mip0(_dds(b"DXT5", a5 + c))[..., 3], 20)
    a3 = bytes([0x11] * 8)  # every nibble 1 -> 17
    assert np.allclose(dds.mip0(_dds(b"DXT3", a3 + c))[..., 3], 17)
