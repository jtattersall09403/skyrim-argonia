"""L2/L1 (1.15 build speed): the land rows are reused by content key. After a ground edit in one band, a rebuild over
the last land reuses every row the edit cannot reach, rebuilds the rest, and its shards equal a from-scratch build's
byte for byte; a changed shared key (the code or tables, `row_base`) reuses nothing."""
import re
from pathlib import Path

import numpy as np

from tools.argonia_world.terrain import build
from tools.argonia_world.terrain.grid import Sources


def _src(edit: bool = False) -> Sources:
    n, pad = 8 * 32, 32
    yy, xx = np.mgrid[0:n + 1, 0:n + 1]
    g = (20 * np.sin(xx / 9.0) + 10 * np.cos(yy / 7.0) + 30).astype(np.float32)
    if edit:
        g[220:240, 10:40] += 25.0  # a hill near the south edge
    ap = np.zeros((n + 1 + 2 * pad,) * 2, np.float32)
    cover = ((xx // 16 + yy // 16) % 5).astype(np.int16) + 16
    return Sources(ground=g, apron=ap, cover=cover, tint=None, pad=pad)


def _shards(d: Path) -> dict[str, bytes]:
    return {p.name: p.read_bytes() for p in sorted((d / "land").glob("cy*.jsonl.gz"))}


def _reused(out: str) -> tuple[int, int]:
    m = re.search(r"land reuse: (\d+) of (\d+) rows", out)
    return int(m[1]), int(m[2])


def test_land_rows_reused_by_key(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(build, "ROW_MARGIN", 32)  # one cell of reach, so the small grid shows locality
    cells = (-63, -63, -62, -54)  # two columns, every row
    a = tmp_path / "a"
    build.build(_src(), None, a, cells=cells, row_base="base")
    assert _reused(capsys.readouterr().out)[0] == 0
    build.build(_src(), None, a, cells=cells, row_base="base")  # nothing changed: every row reused
    k, n = _reused(capsys.readouterr().out)
    assert k == n == 10
    build.build(_src(edit=True), None, a, cells=cells, row_base="base")
    k, n = _reused(capsys.readouterr().out)
    assert 0 < k < n  # the north rows kept, the edited band rebuilt
    fresh = tmp_path / "fresh"
    build.build(_src(edit=True), None, fresh, cells=cells, row_base="base")
    assert _shards(a) == _shards(fresh)  # L1: a cached rebuild's bytes are a from-scratch build's


def test_stale_shared_key_reuses_nothing(tmp_path, capsys):
    cells = (-63, -63, -62, -60)
    build.build(_src(), None, tmp_path, cells=cells, row_base="code-v1")
    capsys.readouterr()
    build.build(_src(), None, tmp_path, cells=cells, row_base="code-v2")  # a code or table change
    assert _reused(capsys.readouterr().out)[0] == 0
    build.build(_src(), None, tmp_path, cells=cells, row_base=None)  # no base: no keys kept, no reuse
    assert "land reuse" not in capsys.readouterr().out and not (tmp_path / "land" / "_keys").exists()
