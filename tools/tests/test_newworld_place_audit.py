"""The seating rule and audit of every placed kind (tools/newworld/place/audit.py), on meshes made here."""
import math

import numpy as np
import pytest

from tools.newworld.place import audit as A

U = 70.0  # units a metre


def box(x0, x1, y0, y1, z0, z1, bottom=True):
    """A closed (or bottomless) box, faces wound outward."""
    V = np.array([[x, y, z] for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)], float)
    q = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]  # bottom, top, sides
    F = []
    for i, (a, b, c, d) in enumerate(q):
        if i == 0 and not bottom:
            continue
        F += [(a, b, c), (a, c, d)]
    return V, np.array(F)


def cylinder(r, z0, z1, n=16, cx=0.0, cy=0.0):
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    V = np.array([[cx + r * math.cos(t), cy + r * math.sin(t), z] for z in (z0, z1) for t in a])
    F = []
    for i in range(n):
        j = (i + 1) % n
        F += [(i, j, n + j), (i, n + j, n + i)]
    return V, np.array(F)


def prof(monkeypatch, V, F):
    monkeypatch.setattr(A, "surface", lambda model, resolver=None: (V, F))
    return A.profile("m.nif")


def flat(xs, ys):
    return np.zeros(len(np.atleast_1d(xs)))


def slope(xs, ys):  # rising 0.5 per unit east (about 27 degrees)
    return 0.5 * np.asarray(xs, float)


def test_a_log_is_seated_by_its_bulk_not_its_root_tip(monkeypatch):
    # a 6 m log 0.8 m thick, with a thin root 1 m below its bulk at one end
    V1, F1 = box(-3 * U, 3 * U, -0.4 * U, 0.4 * U, 0, 0.8 * U)
    V2, F2 = box(2.9 * U, 3.0 * U, -0.05 * U, 0.05 * U, -1.0 * U, 0)
    p = prof(monkeypatch, np.vstack([V1, V2]), np.vstack([F1, F2 + len(V1)]))
    j = A.judge(p, "log", (0, 0, 1.0 * U), (0, 0, 0), 1.0, flat)  # root tip touching: the bulk 1 m up
    assert j["measure"] == "bulk" and j["bulk"] == pytest.approx(1.0, abs=0.05)
    assert "bulk_hovers" in A.faults(j)
    z, _ = A.seat(p, "log", (0, 0, 1.0 * U), (0, 0, 0), 1.0, flat)
    j2 = A.judge(p, "log", (0, 0, z), (0, 0, 0), 1.0, flat)
    assert abs(j2["bulk"] - A.RULE["bulk"]["target"]) < 0.02 and not A.faults(j2)
    # a pose the placer refuses (its road clear) is passed over for the next yaw; none left, the log is refused
    z3, r3 = A.seat(p, "log", (0, 0, 1.0 * U), (0, 0, 0), 1.0, flat, ok=lambda z, r: r[2] != 0)
    assert r3[2] != 0
    assert A.seat(p, "log", (0, 0, 1.0 * U), (0, 0, 0), 1.0, flat, ok=lambda z, r: False) is None


def test_a_tree_on_a_slope_is_sunk_until_its_trunk_foot_is_under_the_ground_all_round(monkeypatch):
    V, F = cylinder(0.5 * U, -0.5 * U, 10 * U)
    p = prof(monkeypatch, V, F)
    assert p["trunk"] is not None
    # pivot on the ground at x = 0: the downhill side of the foot hovers
    z0 = float(slope(np.array([0.0]), np.array([0.0]))[0])
    j = A.judge(p, "canopy_tree", (0, 0, z0), (0, 0, 0), 1.0, slope)
    assert "trunk_hovers" in A.faults(j)
    z, _ = A.seat(p, "canopy_tree", (0, 0, z0), (0, 0, 0), 1.0, slope)
    j2 = A.judge(p, "canopy_tree", (0, 0, z), (0, 0, 0), 1.0, slope)
    assert j2["trunk"] == pytest.approx(A.RULE["trunk"]["target"], abs=0.02) and not A.faults(j2)


def test_a_bottomless_rock_buries_its_rim_and_one_that_cannot_is_refused(monkeypatch):
    V, F = box(-1 * U, 1 * U, -1 * U, 1 * U, 0, 2 * U, bottom=False)
    p = prof(monkeypatch, V, F)
    assert p["open_down"] >= A.OPEN_MIN and len(p["rim"])
    j = A.judge(p, "boulder", (0, 0, 0.3 * U), (0, 0, 0), 1.0, flat)
    assert j["measure"] == "rim" and "hollow_shows" in A.faults(j)
    z, _ = A.seat(p, "boulder", (0, 0, 0.3 * U), (0, 0, 0), 1.0, flat)
    assert not A.faults(A.judge(p, "boulder", (0, 0, z), (0, 0, 0), 1.0, flat))
    # 3 m up: burial past EXTRA_SINK_MAX of its 2 m height: not placed there
    assert A.seat(p, "boulder", (0, 0, 3 * U), (0, 0, 0), 1.0, flat) is None


def test_a_shell_is_turned_so_its_open_back_faces_into_the_hill(monkeypatch):
    # a box open on its +x side (its back), on a slope rising east: open side uphill is buried by the hill
    V, F = box(-1 * U, 1 * U, -1 * U, 1 * U, 0, 2 * U)
    keep = [f for f in F.tolist() if not all(V[i][0] > 0 for i in f)]
    p = prof(monkeypatch, V, np.array(keep))
    assert p["open_side"] >= A.OPEN_MIN
    z0 = 0.0
    def hill(xs, ys):  # rising 2 per unit east
        return 2.0 * np.asarray(xs, float)
    assert A.judge(p, "cliff", (0, 0, z0), (0, 0, math.pi), 1.0, hill)["rim"] > 1.0  # its back faces downhill
    z, rot = A.seat(p, "cliff", (0, 0, z0), (0, 0, math.pi), 1.0, hill)
    j = A.judge(p, "cliff", (0, 0, z), rot, 1.0, hill)
    assert not A.faults(j)
    assert z >= z0 - 2 * U * 0.36  # turned rather than buried past the cap


def test_a_tree_half_over_a_bank_is_not_placed_there(monkeypatch):
    V, F = cylinder(1.0 * U, -0.5 * U, 10 * U)
    p = prof(monkeypatch, V, F)

    def bank(xs, ys):  # the ground drops 8 m half a metre west of the pivot
        return np.where(np.asarray(xs, float) < -0.5 * U, -8 * U, 0.0)
    assert A.seat(p, "canopy_tree", (0, 0, 0), (0, 0, 0), 1.0, bank) is None
    assert A.seat(p, "canopy_tree", (0, 0, 0), (0, 0, 0), 1.0, flat) is not None
