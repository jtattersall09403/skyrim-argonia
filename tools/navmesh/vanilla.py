"""The layout proof against Skyrim.esm (read only; nothing it reads or writes enters git, decision 0003).

    survey()      every NAVM's NVNM through decode then encode (byte-identical?), and the rules the stitch copies:
                  the lookup grid's divisor by triangle count, the NVMI's approx location (the vertex mean), its edge
                  links (the neighbour navmeshes), the triangle winding, the water triangles' depth under XCLW
    roundtrip()   20 Tamriel NAVMs, chosen to cover edge links, water, Preferred and door triangles, written by
                  ArgoniaGen's own parse-and-write path (NavmeshRecords.Parse, Mutagen) into a test plugin, read back
                  with the same reader (esm.py, nvnm.py): every NVNM byte-identical to the original
"""
from __future__ import annotations

import base64
import gzip
import json
import os
import struct
import subprocess
from collections import Counter
from pathlib import Path

import numpy as np

from tools.navmesh import esm, nvnm

ROOT = Path(__file__).resolve().parents[2]
TAMRIEL = 0x3C
GEN = ROOT / "tools" / "ArgoniaGen" / "bin" / "Release" / "net10.0" / "ArgoniaGen"


def data_dir() -> Path:
    root = os.environ.get("ARGONIA_GAME_ROOT")
    return (Path(root) / "Data") if root else Path.home() / "games" / "skyrimse" / "Data"


def _navms(path: Path):
    for r in esm.records(path, {b"NAVM"}, {b"WRLD"}):
        yield r, dict(esm.subrecords(r.data))[b"NVNM"]


def survey(path: Path | None = None) -> dict:
    path = path or data_dir() / "Skyrim.esm"
    out = Counter()
    cell_water = {}
    for r in esm.records(path, {b"CELL"}, {b"WRLD"}):
        d = dict(esm.subrecords(r.data))
        if b"XCLW" in d:
            cell_water[r.fid] = struct.unpack("<f", d[b"XCLW"])[0]
    navi = next(esm.records(path, {b"NAVI"}))
    centre = {}
    for s, b in esm.subrecords(navi.data):
        if s == b"NVMI":
            f, _, x, y, z = struct.unpack_from("<II3f", b)
            centre[f] = np.array([x, y, z], np.float32)
    depth = []
    for r, b in _navms(path):
        n = nvnm.decode(b)
        out["navm"] += 1
        out["codec_identical"] += nvnm.encode(n) == b
        if n.world != TAMRIEL:
            continue
        out["tamriel"] += 1
        t = len(n.tris)
        out["divisor_rule"] += n.divisor == nvnm.divisor_for(t)
        if r.fid in centre:
            out["centre_is_vertex_mean"] += bool(np.allclose(n.verts.mean(axis=0), centre[r.fid], atol=1.0))
        v, tv = n.verts, n.tris["v"].astype(int)
        a, bb, c = v[tv[:, 0]], v[tv[:, 1]], v[tv[:, 2]]
        cr = (bb[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (bb[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])
        out["tris"] += t
        out["tris_ccw"] += int((cr > 0).sum())
        out["tris_water"] += int(((n.tris["flags"] & nvnm.WATER) != 0).sum())
        out["tris_preferred"] += int(((n.tris["flags"] & nvnm.PREFERRED) != 0).sum())
        out["edge_links"] += len(n.links)
        w = cell_water.get(r.cell)
        wt = (n.tris["flags"] & nvnm.WATER) != 0
        if w is not None and w < 1e6 and wt.any():
            depth.extend((w - v[tv[wt]][:, :, 2].mean(axis=1)).tolist())
    d = np.array(depth)
    out = dict(out)
    out["water_depth_units_p50_p99_max"] = [round(float(np.percentile(d, q)), 1) for q in (50, 99)] + [round(float(d.max()), 1)]
    return out


def pick(path: Path, n: int = 20) -> list:
    """n Tamriel NAVMs in FormID order covering: edge links, water, Preferred, door triangles, large, small."""
    want = ["links", "water", "preferred", "doors", "large", "small"]
    got: dict[str, list] = {k: [] for k in want}
    every = []
    for r, b in _navms(path):
        m = nvnm.decode(b)
        if m.world != TAMRIEL:
            continue
        f = m.tris["flags"]
        tags = {"links": len(m.links) > 0, "water": bool((f & nvnm.WATER).any()),
                "preferred": bool((f & nvnm.PREFERRED).any()), "doors": len(m.doors) > 0,
                "large": len(m.tris) >= 1000 or len(b) > 0xFFFF, "small": len(m.tris) < 17}
        for k, on in tags.items():
            if on and len(got[k]) < (n + len(want) - 1) // len(want):
                got[k].append(r)
        every.append(r)
        if all(len(v) >= (n + len(want) - 1) // len(want) for v in got.values()):
            break
    chosen = {r.fid: r for v in got.values() for r in v}
    for r in every:
        if len(chosen) >= n:
            break
        chosen.setdefault(r.fid, r)
    return [chosen[k] for k in sorted(chosen)][:n]


def roundtrip(out: Path, n: int = 20) -> dict:
    data = data_dir()
    path = data / "Skyrim.esm"
    out.mkdir(parents=True, exist_ok=True)
    recs = pick(path, n)
    src = out / "vanilla-navm.jsonl.gz"
    with open(src, "wb") as f, gzip.GzipFile(fileobj=f, mode="wb", mtime=0, filename="") as z:
        for r in recs:
            m = nvnm.decode(dict(esm.subrecords(r.data))[b"NVNM"])
            head = struct.pack("<4sIIIIHH", r.sig, len(r.data), r.flags & ~esm.COMPRESSED, r.fid, r.vcs1, r.version, r.vcs2)
            z.write((json.dumps({"cell": f"{r.cell:06X}:Skyrim.esm", "x": m.grid_xy[0], "y": m.grid_xy[1],
                                 "navm": base64.b64encode(head + r.data).decode("ascii")}) + "\n").encode())
    test = out / "NavRoundTrip.esp"
    env = dict(os.environ, DOTNET_ROOT=str(Path.home() / ".dotnet"), DOTNET_gcServer="0")
    subprocess.run([str(GEN), "navmesh", "roundtrip", "--in", str(src), "--out", str(test), "--data", str(data)],
                   check=True, env=env, capture_output=True, text=True)
    back = {r.fid: r for r in esm.records(test, {b"NAVM"})}
    res = {"navm": len(recs), "written": len(back), "nvnm_identical": 0, "subrecords_identical": 0,
           "compressed": 0, "fids": [f"{r.fid:08X}" for r in recs], "differ": []}
    for r in recs:
        b = back.get(r.fid)
        if b is None:
            res["differ"].append(f"{r.fid:08X}: missing")
            continue
        same = dict(esm.subrecords(b.data))[b"NVNM"] == dict(esm.subrecords(r.data))[b"NVNM"]
        res["nvnm_identical"] += same
        res["subrecords_identical"] += b.data == r.data
        res["compressed"] += bool(b.flags & esm.COMPRESSED)
        if not same:
            res["differ"].append(f"{r.fid:08X}")
    test.unlink()
    return res
