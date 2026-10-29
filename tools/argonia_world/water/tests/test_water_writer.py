"""L1: the water's writer (WaterRecords.cs through LandWorld.cs) on the terrain test's 4 synthetic cells, read back
from the bytes: the 4 WATR types and 4 plane activators, the WRLD's default water, one cell with a water height and
type, one with plane and piece references only, HasWater on both; written twice, the same bytes. Also the regrade
layer (terrain/water_regrade.py) and the greedy plane cover. Skipped where ArgoniaGen is not built."""
import json
import os
import struct
import subprocess
from pathlib import Path

import numpy as np
import pytest

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.terrain import build, esm, world
from tools.argonia_world.terrain.landcover import table
from tools.argonia_world.terrain.tests.test_terrain import src
from tools.argonia_world.terrain.water_regrade import Regrade
from tools.argonia_world.water import layer, plan

ROOT = Path(__file__).resolve().parents[4]
GEN = ROOT / "tools" / "ArgoniaGen" / "bin" / "Release" / "net10.0" / "ArgoniaGen"
HAS_WATER = 0x2  # CELL DATA flag (Cell.Flag.HasWater)


def _write(tmp: Path, name: str) -> bytes:
    out = tmp / name / "ArgoniaWorld.esm"
    env = dict(os.environ, DOTNET_ROOT=str(Path.home() / ".dotnet"), DOTNET_gcServer="0")
    r = subprocess.run([str(GEN), "world", "--in", str(tmp / "world.json"), "--land", str(tmp / "land"),
                        "--data", str(tmp), "--out", str(out), "--water", str(tmp / "water")],
                       capture_output=True, text=True, env=env, check=False)
    assert r.returncode == 0, r.stdout + r.stderr
    return out.read_bytes()


@pytest.mark.skipif(not GEN.exists(), reason="ArgoniaGen not built")
def test_water_written_and_read_back(tmp_path):
    s = src()
    build.build(s, table(), tmp_path, cells=(-62, -62, -61, -61))
    world.write(tmp_path / "world.json", s.cell_range, tmp_path / "land")
    wd = tmp_path / "water"
    wd.mkdir()
    (wd / "records.json").write_text(json.dumps({"schema": 1, "records": layer.records()}))
    height = {"x": -62, "y": -62, "waterHeight": 512.5, "waterType": layer.type_key("fresh"), "refs": [
        {"formKey": layer.ref_key(-62, -62, 0), "base": layer.plane_key("black"), "pos": [-253000.0, -253000.0, 700.0],
         "rot": [0.0, 0.0, 0.5], "scale": 0.25}]}
    planes = {"x": -61, "y": -61, "refs": [
        {"formKey": layer.ref_key(-61, -61, 0), "base": layer.plane_key("sea"), "pos": [-249000.0, -249000.0, 64.0],
         "rot": [0.0, 0.0, 0.0], "scale": 1.0},
        {"formKey": layer.ref_key(-61, -61, 1), "base": "01B37E:Skyrim.esm", "pos": [-249100.0, -249050.0, 60.0],
         "rot": [0.0, 0.0, 1.5], "scale": 0.5}]}
    (wd / "cells.jsonl").write_text("".join(json.dumps(x) + "\n" for x in (height, planes)))
    blob = _write(tmp_path, "a")
    assert _write(tmp_path, "b") == blob
    recs = list(esm.records(blob))
    by = {}
    for r in recs:
        by.setdefault(r.sig, []).append(r)
    watr = {r.formid & 0xFFFFFF: r for r in by["WATR"]}
    want = {int(rec["formKey"].split(":")[0], 16): rec for rec in layer.records() if rec["type"] == "WATR"}
    assert sorted(watr) == sorted(want) and len(watr) == 4
    for fid, rec in want.items():
        assert watr[fid].first("EDID") == rec["edid"].encode() + b"\0"
        assert watr[fid].first("ANAM")[0] == rec["opacity"]
    acti = {r.formid & 0xFFFFFF: r for r in by["ACTI"]}
    for rec in (x for x in layer.records() if x["type"] == "ACTI"):
        a = acti[int(rec["formKey"].split(":")[0], 16)]
        assert a.first("MODL") == rec["model"].encode() + b"\0"
        assert struct.unpack("<I", a.first("WNAM"))[0] & 0xFFFFFF == int(rec["waterType"].split(":")[0], 16)
    wrld = by["WRLD"][0]
    assert struct.unpack("<I", wrld.first("NAM2"))[0] & 0xFFFFFF == int(layer.type_key("sea").split(":")[0], 16)
    cells = {}
    for c in by["CELL"]:
        xclc = c.first("XCLC")
        if xclc and not c.flags & 0x400:
            cells[struct.unpack_from("<ii", xclc)] = c
    c = cells[(-62, -62)]
    assert struct.unpack("<f", c.first("XCLW"))[0] == 512.5
    assert struct.unpack("<I", c.first("XCWT"))[0] & 0xFFFFFF == int(layer.type_key("fresh").split(":")[0], 16)
    assert struct.unpack("<H", c.first("DATA")[:2])[0] & HAS_WATER
    assert cells[(-61, -61)].first("XCLW") is None or struct.unpack("<f", cells[(-61, -61)].first("XCLW"))[0] != 512.5
    refr = {r.formid & 0xFFFFFF: r for r in by["REFR"]}
    for line in (height, planes):
        for ref in line["refs"]:
            r = refr[int(ref["formKey"].split(":")[0], 16)]
            pos_rot = struct.unpack("<6f", r.first("DATA"))
            assert np.allclose(pos_rot, ref["pos"] + ref["rot"], atol=1e-3)
            scale = r.first("XSCL")
            assert (struct.unpack("<f", scale)[0] if scale else 1.0) == pytest.approx(ref["scale"])
    tes4 = by["TES4"][0]
    assert b"Skyrim.esm\0" in [b for s_, b in tes4.subs if s_ == "MAST"]


def test_regrade_raises_the_ground_only_to_its_floors():
    s = src()
    n = s.ground.shape[0]
    before = s.heights(s.pad, s.pad + n, s.pad, s.pad + n)
    cls_before = s.classes(s.pad, s.pad + n, s.pad, s.pad + n)
    i = 40 * n + 50
    floors = {i: float(before[40, 50]) + 3.0, i + 1: float(before[40, 51]) - 3.0}  # one above, one below the ground
    s.regrade = Regrade.from_flat(floors, n, s.pad)
    after = s.heights(s.pad, s.pad + n, s.pad, s.pad + n)
    assert after[40, 50] == pytest.approx(floors[i]) and after[40, 51] == before[40, 51]
    assert (after != before).sum() == 1
    assert np.array_equal(s.classes(s.pad, s.pad + n, s.pad, s.pad + n), cls_before)  # heights only, never classes
    win = s.heights(s.pad + 38, s.pad + 42, s.pad + 49, s.pad + 52)  # a window sees the same floor
    assert win[2, 1] == pytest.approx(floors[i])


def test_greedy_cover_tiles_a_diagonal_band_with_fewer_disjoint_squares():
    req = np.zeros((32, 32), dtype=bool)
    for k in range(32):
        req[k, max(0, k - 2):k + 3] = True  # a diagonal channel five samples wide
    ok = req.copy()
    sq = plan.greedy_cover(req, ok)
    cover = np.zeros(req.shape, dtype=int)
    for r, c, h, w in sq:
        assert h == w and ok[r:r + h, c:c + w].all()
        cover[r:r + h, c:c + w] += 1
    assert (cover[req] == 1).all() and cover.max() == 1  # every sample once, nothing outside the band
    quad = []
    plan.cover(req, ok, 0, 0, 32, 32, quad)
    assert len(sq) < sum(len(plan.squares(plan.Plane(0, 0, *b, 0.0, ""))) for b in quad)


def test_ref_keys_stay_in_the_reserved_range():
    x0, y0 = su.PROVINCE_CELL_SW
    last = layer.ref_key(x0 + su.PROVINCE_CELLS - 1, y0 + su.PROVINCE_CELLS - 1, layer.REFS_PER_CELL - 1)
    assert int(last.split(":")[0], 16) < 0x1000000
    with pytest.raises(ValueError):
        layer.ref_key(x0, y0, layer.REFS_PER_CELL)
