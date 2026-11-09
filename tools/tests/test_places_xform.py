"""tools/places/xform.py: the matrix maths every lane shares, against its own test vectors (lane W mirrors them)."""
import json
import math
import random

from tools.places import xform


def close(a, b, tol=1e-6):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def test_vectors_file_is_current():
    on_disk = json.loads(xform.VECTORS.read_text())
    assert on_disk == json.loads(json.dumps(xform.make_vectors())), "run: python -m tools.places xform vectors"


def test_vectors_points_and_round_trip():
    for c in json.loads(xform.VECTORS.read_text())["cases"]:
        m = xform.matrix(c["pos"], c["rot"], c["scale"])
        for p in c["points"]:
            assert close(xform.apply(m, p["local"]), p["world"])
        d = c["decomposed"]
        m2 = xform.matrix(d["pos"], d["rot"], d["scale"])
        assert all(close(m[i], m2[i]) for i in range(4))


def test_heading_is_clockwise_from_north():
    assert close(xform.forward([0, 0, math.pi / 2]), [1, 0, 0])
    assert close(xform.forward([0, 0, 0]), [0, 1, 0])
    assert close(xform.forward([0, 0, -math.pi / 2]), [-1, 0, 0])


def test_record_range_and_wrapped_angles_are_one_turn():
    a = xform.matrix([0, 0, 0], [0.3, 6.0, 5.9])
    b = xform.matrix([0, 0, 0], [0.3, 6.0 - 2 * math.pi, 5.9 - 2 * math.pi])
    assert all(close(a[i], b[i]) for i in range(3))


def test_decompose_random_round_trip():
    rnd = random.Random(7)
    for _ in range(500):
        pos = [rnd.uniform(-1e5, 1e5) for _ in range(3)]
        rot = [rnd.uniform(0, 2 * math.pi) for _ in range(3)]
        sc = rnd.uniform(0.2, 3)
        m = xform.matrix(pos, rot, sc)
        p, r, s = xform.decompose(m)
        m2 = xform.matrix(p, r, s)
        assert all(close(m[i], m2[i], 1e-4) for i in range(3)) and abs(s - sc) < 1e-9


def test_gimbal_lock_round_trip():
    m = xform.matrix([1, 2, 3], [0.4, -math.pi / 2, 1.1])
    p, r, s = xform.decompose(m)
    assert all(close(m[i], xform.matrix(p, r, s)[i]) for i in range(3))


def test_rotation_is_the_proven_candidate():
    rot = [0.2, 0.5, 2.0]
    assert xform.rotation(rot) == xform.CANDIDATES[xform.CONVENTION](*rot)
