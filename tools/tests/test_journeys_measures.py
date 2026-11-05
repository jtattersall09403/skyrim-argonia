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
    a = M.build_key()
    monkeypatch.setattr(M, "MEASURE_VERSION", M.MEASURE_VERSION + 1)
    assert M.build_key() != a


def _writer(d, lo):
    M.reset(d)
    M._state["key"] = "k1"

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


def test_the_key_follows_shard_content_not_the_write(tmp_path, monkeypatch):
    import os
    veg = tmp_path / "out" / "terrain" / "vegetation"
    veg.mkdir(parents=True)
    (tmp_path / "out" / "terrain" / "land").mkdir(parents=True)
    (tmp_path / "out" / "water").mkdir()
    (tmp_path / "out" / "water" / "cells.jsonl").write_bytes(b"w")
    monkeypatch.setattr(M, "ROOT", tmp_path)
    shard = veg / "cy+000.jsonl.gz"
    shard.write_bytes(b"abcdef")
    a = M.build_key()
    shard.unlink()
    shard.write_bytes(b"abcdef")
    os.utime(shard, (1, 1))
    assert M.build_key() == a            # rewritten with identical bytes: unchanged
    shard.write_bytes(b"abcdeg")         # one byte, same size
    assert M.build_key() != a
