"""infra/gpu-box/bsa.py: a file out of a Skyrim SE archive, stored or LZ4-compressed (the vanilla hop back, walk 4)."""
import importlib.util
import pathlib
import struct

import pytest

spec = importlib.util.spec_from_file_location(
    "bsa", pathlib.Path(__file__).resolve().parents[2] / "infra" / "gpu-box" / "bsa.py")
bsa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bsa)

TEXT = b"Argonia " * 40 + b"hop back"
# python-lz4's frames of TEXT: plain, and with content size and both checksums (an overlapping match in each)
FRAME = bytes.fromhex("04224d186840480100000000000071160000008f4172676f6e6961200800ff2680686f70206261636b00000000")
FRAME_SUMS = bytes.fromhex("04224d187c4048010000000000003f160000008f4172676f6e6961200800ff2680686f70206261636b"
                           "4e8d313700000000b6105b94")


def archive(path, files, compressed):
    """A minimal v105 archive: one folder, the given {name: bytes}, packed with FRAME's codec when compressed."""
    folder = b"meshes\\actors\\character\\animations"
    names = b"".join(n.encode() + b"\0" for n in files)
    datas = []
    for d in files.values():
        datas.append(struct.pack("<I", len(d)) + FRAME if compressed else d)
    flags = 0x3 | (bsa.COMPRESSED if compressed else 0)
    head = struct.pack("<4sIIIIIIIH2x", b"BSA\0", 105, 36, flags, 1, len(files), len(folder) + 1, len(names), 0)
    folder_rec = struct.pack("<QIIQ", 0, len(files), 0, 0)
    block = bytes([len(folder) + 1]) + folder + b"\0"
    start = len(head) + len(folder_rec) + len(block) + 16 * len(files) + len(names)
    recs, off = b"", start
    for d in datas:
        recs += struct.pack("<QII", 0, len(d), off)
        off += len(d)
    path.write_bytes(head + folder_rec + block + recs + names + b"".join(datas))


@pytest.mark.parametrize("frame", [FRAME, FRAME_SUMS])
def test_lz4_frame(frame):
    assert bsa.lz4_frame(frame) == TEXT


def test_read_compressed_and_stored(tmp_path):
    a = tmp_path / "a.bsa"
    archive(a, {"dodgeback.hkx": TEXT}, compressed=True)
    assert bsa.read_file(str(a), "meshes/actors/character/animations/DodgeBack.hkx") == TEXT
    archive(a, {"other.hkx": b"x", "dodgeback.hkx": b"stored"}, compressed=False)
    assert bsa.read_file(str(a), "Meshes\\Actors\\Character\\Animations\\dodgeback.hkx") == b"stored"
    with pytest.raises(KeyError):
        bsa.read_file(str(a), "meshes/actors/character/animations/none.hkx")
