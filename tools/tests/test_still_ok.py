"""tools/still_ok.py: blank, black, white, noise, near-duplicate and truncated stills."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import still_ok  # noqa: E402
from argonia_world.terrain import png  # noqa: E402

RNG = np.random.default_rng(1)


def make(tmp, name, img):
    return png.write(tmp / name, img)


def noise():
    return RNG.integers(0, 256, (48, 64, 3), dtype=np.uint8)


def test_noise_ok(tmp_path):
    ok, _, n = still_ok.check(make(tmp_path, "n.png", noise()))
    assert ok and n["std"] > 30


def test_blank_black_white(tmp_path):
    for name, v, word in (("g", 120, "blank"), ("b", 0, "black"), ("w", 255, "white")):
        ok, why, _ = still_ok.check(make(tmp_path, name + ".png", np.full((48, 64, 3), v, np.uint8)))
        assert not ok and word in why


def test_near_uniform_threshold(tmp_path):
    img = np.full((48, 64, 3), 100, np.uint8)
    img[:, :32] = 103
    p = make(tmp_path, "s.png", img)
    assert not still_ok.check(p)[0]
    assert still_ok.check(p, min_std=0.5)[0]


def test_prev(tmp_path):
    a = noise()
    pa = make(tmp_path, "a.png", a)
    b = a.copy()
    b[0, 0] = 255 - b[0, 0]  # one pixel differs: near-duplicate
    ok, why, _ = still_ok.check(make(tmp_path, "b.png", b), pa)
    assert not ok and "same as previous" in why
    assert not still_ok.check(pa, pa)[0]
    assert still_ok.check(make(tmp_path, "c.png", noise()), pa)[0]


def test_truncated_and_missing(tmp_path):
    p = make(tmp_path, "t.png", noise())
    p.write_bytes(p.read_bytes()[:60])
    ok, why, _ = still_ok.check(p)
    assert not ok and "unreadable" in why
    assert not still_ok.check(tmp_path / "none.png")[0]


def test_cli(tmp_path, capsys):
    p = make(tmp_path, "n.png", noise())
    assert still_ok.main([str(p), "--json"]) == 0
    assert still_ok.main([str(tmp_path / "x.png")]) == 1
