"""The navmesh's per-cell checkpoint (stitch.py's out/stitch): a change in one cell's land rebuilds that cell and its
ring and nothing else, the untouched cells' NAVM bytes stay as they were, and the cached build equals a clean one.
Needs the terrain's arrays ($ARGONIA_DATA) and the .NET SDK, as the sample build does."""
import gzip
import json
import shutil

import numpy as np
import pytest

from tools.argonia_world import skyrim_units as su
from tools.navmesh import __main__ as nav

BOX = (0, 0, 4, 4)
HIT = (2, 2)


def lines(out):
    d = {}
    for p in (out / "navm").glob("cy*.jsonl.gz"):
        for ln in gzip.open(p, "rt"):
            j = json.loads(ln)
            d[(j["x"], j["y"])] = ln
    return d


def bump(inn):
    g = json.loads((inn / "grid.json").read_text())
    h = np.memmap(inn / "height.f32", np.float32, "r+", shape=(g["rows"], g["cols"]))
    c = int((HIT[0] * su.CELL_UNITS + su.CELL_UNITS / 2 - g["x0"]) / g["step"])
    r = int((g["ytop"] - (HIT[1] * su.CELL_UNITS + su.CELL_UNITS / 2)) / g["step"])
    h[r - 2:r + 3, c - 2:c + 3] += np.float32(400)
    h.flush()


def test_one_cell_changed_rebuilds_its_ring_only(tmp_path, capsys):
    try:
        nav.build_tool()
        a = tmp_path / "a"
        first = nav.build(BOX, a, check=False)
    except (Exception, SystemExit) as e:  # no ground or no SDK on this machine
        pytest.skip(f"navmesh build unavailable: {e}")
    assert first["totals"]["built"] == 25
    before = lines(a)
    again = nav.build(BOX, a, check=False)
    assert (again["totals"]["reused"], again["totals"]["built"]) == (25, 0) and again["sha256"] == first["sha256"]
    ring = {(HIT[0] + dx, HIT[1] + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
    edited = nav.build(BOX, a, check=False, after_inputs=bump)
    assert (edited["totals"]["reused"], edited["totals"]["built"]) == (25 - len(ring), len(ring))
    after = lines(a)
    assert {c for c in after if after[c] != before[c]} <= ring and after[HIT] != before[HIT]
    assert all(after[c] == before[c] for c in after if c not in ring)
    clean = tmp_path / "clean"
    full = nav.build(BOX, clean, check=False, after_inputs=bump)
    assert full["totals"]["built"] == 25 and full["sha256"] == edited["sha256"] and lines(clean) == after
    assert {k: v for k, v in full["totals"].items() if k not in ("reused", "built")} == \
           {k: v for k, v in edited["totals"].items() if k not in ("reused", "built")}
    shutil.rmtree(clean)
