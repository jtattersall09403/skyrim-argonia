"""meshes.Resolver.collision keeps each mesh's solid collision on disk under its bytes' hash and the reader's code:
the kept answer is the one read, other bytes are read afresh, and a second read of one mesh never parses it again."""
import numpy as np

from tools.navmesh import meshes, nif

TRIS = np.arange(54, dtype=float).reshape(-1, 3, 3)


def test_a_meshs_collision_is_kept_by_its_bytes(tmp_path, monkeypatch):
    monkeypatch.setattr(meshes, "COLLISION_CACHE", tmp_path / "coll")
    c = nif.Collision(TRIS, np.ones(len(TRIS), np.uint8), {"skip:x": 2})
    assert meshes.cached_collision(b"mesh one") is None
    meshes.store_collision(b"mesh one", c)
    got = meshes.cached_collision(b"mesh one")
    assert np.array_equal(got.tris, c.tris) and got.tris.dtype == c.tris.dtype
    assert np.array_equal(got.layers, c.layers) and got.layers.dtype == c.layers.dtype and got.skipped == c.skipped
    assert meshes.cached_collision(b"mesh two") is None


def test_a_mesh_is_parsed_once_across_runs(tmp_path, monkeypatch):
    monkeypatch.setattr(meshes, "COLLISION_CACHE", tmp_path / "coll")
    reads = []
    whole = nif.Collision(TRIS, np.array([1, 15, 1, 2, 30, 4], np.uint8), {})
    monkeypatch.setattr(nif, "collision", lambda b: reads.append(b) or whole)
    monkeypatch.setattr(meshes.Resolver, "read", lambda self, m: b"mesh three")
    r = meshes.Resolver.__new__(meshes.Resolver)
    first = meshes.Resolver.collision.__wrapped__(r, "x.nif")     # past the run's own lru_cache: a new run
    again = meshes.Resolver.collision.__wrapped__(r, "x.nif")
    assert len(reads) == 1
    assert np.array_equal(first.layers, [1, 1, 2, 4]) and np.array_equal(first.tris, again.tris)
    assert np.array_equal(first.layers, again.layers)
