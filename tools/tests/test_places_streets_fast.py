"""The streets check's fast paths answer as the plain ones do: a way's corridor squares hold every point within reach of
its line (ways._corridor); a model's turned box holds its whole cloud (ways.plan_box); the components of the walking
mesh asked again answer from the run's own copy, and a changed mesh is asked afresh (check.components)."""
import types

import numpy as np
from scipy.spatial import cKDTree

from tools.places import check as C
from tools.places import shape, ways, xform


def test_the_corridor_holds_every_point_within_reach():
    rnd = np.random.default_rng(5)
    line = np.cumsum(rnd.uniform(-40, 60, (200, 2)), axis=0)
    t = cKDTree(line)
    lo, hi = line.min(0) - 300, line.max(0) + 300
    near = ways._corridor(t, lo, hi, 200.0)
    P = rnd.uniform(lo, hi, (20000, 2))
    d = t.query(P)[0]
    inside = ways._in_corridor(near, np.c_[P, np.zeros(len(P))])
    assert inside[d <= 200.0].all() and (~inside).sum() > 1000


def test_a_models_turned_box_holds_its_cloud():
    shape.register("m/boxy.nif", [[-100, -40, 0], [120, -40, 0], [120, 60, 0], [-100, 60, 300]], [[0, 1, 2], [0, 2, 3]])
    p = {"id": "a", "model": "m/boxy.nif", "m": xform.matrix([500.0, -300.0, 10.0], [0.0, 0.0, 0.7], 1.3)}
    C0 = ways.cloud(p)
    lo, hi = ways.plan_box(p, C0)
    assert (C0[:, :2] >= lo).all() and (C0[:, :2] <= hi).all()


def _nav(fk, n, edges, links=()):
    return types.SimpleNamespace(fk=fk, tri=np.zeros((n, 3), int), edge=np.asarray(edges, int),
                                 flags=np.zeros(n, int), links=list(links), doors=[])


def test_components_asked_again_are_the_same_and_a_change_is_seen():
    navs = {"a": _nav("a", 3, [[1, -1, -1], [0, 2, -1], [1, -1, -1]]), "b": _nav("b", 2, [[-1, -1, -1], [-1, -1, -1]])}
    first = C.components(navs, {})
    assert C.components(navs, {}) == first == C._components(navs, {})
    navs["b"] = _nav("b", 2, [[1, -1, -1], [0, -1, -1]])
    assert C.components(navs, {}) == C._components(navs, {}) != first
