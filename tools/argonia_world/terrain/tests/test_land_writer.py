"""L1: ArgoniaGen's world writer (LandWorld.cs) on 4 synthetic cells, read back from the bytes: the WRLD, every
CELL's grid, and each LAND's heights, normals, colours and texture layers equal to the cell lines it was given;
written twice, the same bytes. Skipped where ArgoniaGen is not built (the build VM builds it in `make plugin`)."""
import os
import struct
import subprocess
from pathlib import Path

import numpy as np
import pytest

from tools.argonia_world.terrain import build, esm, world
from tools.argonia_world.terrain.landcover import table
from tools.argonia_world.terrain.tests.test_terrain import src

ROOT = Path(__file__).resolve().parents[4]
GEN = ROOT / "tools" / "ArgoniaGen" / "bin" / "Release" / "net10.0" / "ArgoniaGen"
QUADS = {"BottomLeft": 0, "BottomRight": 1, "TopLeft": 2, "TopRight": 3}


def _write(tmp: Path, name: str) -> bytes:
    out = tmp / name / "ArgoniaWorld.esm"
    env = dict(os.environ, DOTNET_ROOT=str(Path.home() / ".dotnet"), DOTNET_gcServer="0")
    r = subprocess.run([str(GEN), "world", "--in", str(tmp / "world.json"), "--land", str(tmp / "land"),
                        "--data", str(tmp), "--out", str(out)], capture_output=True, text=True, env=env, check=False)
    assert r.returncode == 0, r.stdout + r.stderr
    return out.read_bytes()


@pytest.mark.skipif(not GEN.exists(), reason="ArgoniaGen not built")
def test_four_cells_written_and_read_back(tmp_path):
    s = src()
    build.build(s, table(), tmp_path, cells=(-62, -62, -61, -61))
    lines = {(c["x"], c["y"]): c for c in build.read_cells(tmp_path)}
    assert len(lines) == 4
    world.write(tmp_path / "world.json", s.cell_range, tmp_path / "land")
    blob = _write(tmp_path, "a")
    assert _write(tmp_path, "b") == blob
    recs = list(esm.records(blob))
    wrld = [r for r in recs if r.sig == "WRLD"]
    assert len(wrld) == 1 and wrld[0].first("EDID") == b"ARG_Province\0" and wrld[0].formid & 0xFFFFFF == world.WRLD_ID
    cells = [r for r in recs if r.sig == "CELL"]
    lands = [r for r in recs if r.sig == "LAND"]
    assert len(cells) == 5 and len(lands) == 4  # the persistent top cell has no LAND
    grid = {}
    for c in cells:
        xclc = c.first("XCLC")
        if xclc and not c.flags & 0x400:
            grid[c.formid & 0xFFFFFF] = struct.unpack_from("<ii", xclc)
    for land in lands:
        k = (land.formid & 0xFFFFFF) - 1  # the LAND follows its CELL's id
        x, y = grid[k]
        line = lines[(x, y)]
        assert f"{k:06X}:ArgoniaWorld.esm" == line["cell"]
        u = build.unpack(line)
        vhgt = land.first("VHGT")
        assert struct.unpack_from("<f", vhgt)[0] == line["offset"]
        assert np.array_equal(np.frombuffer(vhgt[4:4 + 1089], np.int8).reshape(33, 33), u["vhgt"])
        assert np.array_equal(np.frombuffer(land.first("VNML"), np.int8).reshape(33, 33, 3), u["vnml"])
        assert np.array_equal(np.frombuffer(land.first("VCLR"), np.uint8).reshape(33, 33, 3), u["vclr"])
        assert struct.unpack("<I", land.first("DATA"))[0] == 0x1F
        # layers: per quadrant one BTXT then its ATXT/VTXT pairs, opacities equal to the alphas
        got: dict[int, list] = {0: [], 1: [], 2: [], 3: []}
        base: dict[int, int] = {}
        for i, (sig, b) in enumerate(land.subs):
            if sig == "BTXT":
                fid, q, _, layer = struct.unpack("<IBBH", b)
                base[q] = fid
                assert layer == 0xFFFF
            elif sig == "ATXT":
                fid, q, _, layer = struct.unpack("<IBBH", b)
                assert land.subs[i + 1][0] == "VTXT" and layer == len(got[q])
                a = np.zeros(289)
                for pos, _, op in struct.iter_unpack("<HHf", land.subs[i + 1][1]):
                    a[pos] = op
                got[q].append((fid, a))
        for qd in line["quads"]:
            q = QUADS[qd["q"]]
            assert q in base and len(got[q]) == len(qd["layers"])
            for (fid, a), lay in zip(got[q], qd["layers"]):
                want = np.frombuffer(__import__("base64").b64decode(lay["alpha"]), np.uint8) / 255.0
                assert fid & 0xFFFFFF == int(lay["ltex"].split(":")[0], 16)
                assert np.abs(a - want).max() < 1e-6
