"""The stand-measure cache: hits, version invalidation, concurrent writers (lane 1.15-r6-stand-cache)."""
import multiprocessing as mp
import sqlite3

import pytest

from tools.journeys import measures as M


class _B:
    real = True


class _Fake:
    real = False


@pytest.fixture
def store(tmp_path):
    M.reset(tmp_path)
    M._state["key"] = "k1"
    M._state["gkey"] = "g"
    yield tmp_path
    M.reset()


def test_hit_skips_the_measure_and_rounds_the_key(store):
    calls = []

    @M.memo("t")
    def f(b, x, y=1.0):
        calls.append(x)
        return [x, 3]
    f(_B(), 5.00001)
    f(_B(), 5.0)
    assert calls == [5.00001]
    M.flush()
    M.reset(store)   # a new process reads it back
    M._state["key"] = "k1"
    M._state["gkey"] = "g"
    f(_B(), 5.0)
    assert calls == [5.00001]


def test_fixture_builds_are_never_cached(store):
    calls = []

    @M.memo("t")
    def f(b, x):
        calls.append(x)
        return x
    f(_Fake(), 1.0)
    f(_Fake(), 1.0)
    assert len(calls) == 2


def test_a_version_bump_moves_the_key(monkeypatch):
    M.reset()
    a = M.static_key()
    M.reset()
    monkeypatch.setattr(M, "MEASURE_VERSION", M.MEASURE_VERSION + 1)
    assert M.static_key() != a
    M.reset()


def _writer(d, lo):
    M.reset(d)
    M._state["key"] = "k1"
    M._state["gkey"] = "g"

    @M.memo("t")
    def f(b, x):
        return x
    for i in range(lo, lo + 300):
        f(_B(), float(i))
    M.flush()
    M.reset()


def test_two_writers_lose_nothing(store):
    ps = [mp.Process(target=_writer, args=(store, lo)) for lo in (0, 150)]
    [p.start() for p in ps]
    [p.join(60) for p in ps]
    assert all(p.exitcode == 0 for p in ps)
    n = sqlite3.connect(store / "k1.sqlite").execute("SELECT count(*) FROM m").fetchone()[0]
    assert n == 450


def _build_tree(tmp_path, monkeypatch):
    """A tiny out/ with cells (0, 0), (1, 0) and (9, 9): a shard line each, and a cells.jsonl row each."""
    import gzip
    import json
    o = tmp_path / "out"
    for d in ("vegetation", "land", "creatures"):
        (o / "terrain" / d).mkdir(parents=True)
    (o / "water").mkdir()
    line = lambda c, t: json.dumps({"refs": [t], "x": c[0], "y": c[1]}, sort_keys=True).encode() + b"\n"
    for cy, cs in ((0, [(0, 0), (1, 0)]), (9, [(9, 9)])):
        for d in ("vegetation", "land"):
            (o / "terrain" / d / f"cy{cy:+04d}.jsonl.gz").write_bytes(gzip.compress(b"".join(line(c, d) for c in cs), mtime=0))
    (o / "water" / "cells.jsonl").write_bytes(b"".join(json.dumps({"x": c[0], "y": c[1], "waterHeight": 0.0}).encode() + b"\n"
                                                       for c in ((0, 0), (1, 0), (9, 9))))
    monkeypatch.setattr(M, "ROOT", tmp_path)
    monkeypatch.setattr(M.db, "WORLD_ROOT", tmp_path)
    (tmp_path / M.db.DB_DIR).mkdir(parents=True)
    for t in M.READS_DB:
        (tmp_path / M.db.DB_DIR / f"{t}.jsonl").write_bytes(b"t")
    M.reset()
    return o


def _key_at(cell):
    u = M.su.CELL_UNITS
    x, y = (cell[0] + 0.5) * u, (cell[1] + 0.5) * u
    return M.local_key(*M.around(x, y, 25.0))


def test_the_key_follows_shard_content_not_the_write(tmp_path, monkeypatch):
    import os
    o = _build_tree(tmp_path, monkeypatch)
    shard = o / "terrain" / "vegetation" / "cy+000.jsonl.gz"
    raw = shard.read_bytes()
    a = _key_at((0, 0))
    shard.unlink()
    shard.write_bytes(raw)
    os.utime(shard, (1, 1))
    M.reset()
    assert _key_at((0, 0)) == a          # rewritten with identical bytes: unchanged


def test_a_far_cell_leaves_the_key_and_a_near_cell_moves_it(tmp_path, monkeypatch):
    import gzip
    o = _build_tree(tmp_path, monkeypatch)
    near, far = _key_at((0, 0)), _key_at((9, 9))

    p = o / "terrain" / "land" / "cy+009.jsonl.gz"   # a change in a cell far from the stand
    p.write_bytes(gzip.compress(gzip.decompress(p.read_bytes()).replace(b"land", b"lanD"), mtime=0))
    M.reset()
    assert _key_at((0, 0)) == near and _key_at((9, 9)) != far
    (o / "water" / "cells.jsonl").write_bytes((o / "water" / "cells.jsonl").read_bytes().replace(b'"x": 1,', b'"x": 1, "t": 1,'))
    M.reset()
    assert _key_at((0, 0)) != near        # cell (1, 0) is next to (0, 0): inside its padded reach
    M.reset()
    k = M.static_key()
    (tmp_path / M.db.DB_DIR / "object_form.jsonl").write_bytes(b"other")
    M.reset()
    assert M.static_key() != k            # a static table moves every key


def test_a_reach_memo_is_keyed_by_its_cells_only(tmp_path, monkeypatch):
    import gzip
    o = _build_tree(tmp_path, monkeypatch)
    M.reset(tmp_path / "cache")
    calls = []

    @M.memo("t", reach=lambda x, y: M.around(x, y, 10.0))
    def f(b, x, y):
        calls.append((x, y))
        return x

    u = M.su.CELL_UNITS
    here, there = (0.5 * u, 0.5 * u), (9.5 * u, 9.5 * u)
    f(_B(), *here)
    f(_B(), *there)
    assert M.stats() == "measures: 0 hit, 2 miss"
    p = o / "terrain" / "land" / "cy+009.jsonl.gz"
    p.write_bytes(gzip.compress(gzip.decompress(p.read_bytes()).replace(b"land", b"lanD"), mtime=0))
    st = (M._state["hit"], M._state["miss"])
    M.reset(tmp_path / "cache")           # a new process: the store holds both rows
    f(_B(), *here)
    f(_B(), *there)
    assert (M._state["hit"], M._state["miss"]) == (1, 1)   # the far cell's edit recomputed only the stand there
    assert st == (0, 2)
