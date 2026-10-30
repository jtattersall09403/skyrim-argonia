"""L1 for infra/gpu-box/lodsettings.py: ARG_Province's LODSettings file, without which xLODGen lists no ARG_Province
(game-12: terrain LOD failed "ARG_Province not in the worldspace list")."""
import pathlib
import struct
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "infra" / "gpu-box"))
import lodsettings  # noqa: E402


def test_tamriel_shape():
    # Tamriel's own file reads SW -64,-64, stride 128, levels 4..32: cells -64..63 give the same
    assert lodsettings.settings([(-64, -64), (63, 63)]) == (-64, -64, 128)
    assert lodsettings.encode(-64, -64, 128) == struct.pack("<hhiii", -64, -64, 128, 4, 32)
    assert len(lodsettings.encode(0, 0, 32)) == 16


def test_corner_aligned_to_32_and_stride_covers_every_cell():
    sw_x, sw_y, stride = lodsettings.settings([(-130, -70), (63, 131)])
    assert (sw_x, sw_y) == (-160, -96) and sw_x % 32 == 0 and sw_y % 32 == 0
    assert stride == 256 and sw_x + stride > 63 and sw_y + stride > 131
    assert lodsettings.settings([(0, 0), (32, 0)])[2] == 64  # 33 cells need the next power of two
