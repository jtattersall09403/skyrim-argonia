"""Lane 1.15-r4-trees: trees seated by their mod's own measured depth; the region classes' lists differ."""
from collections import defaultdict

import numpy as np

from tools.argonia_world.vegetation import lists, seat


def test_ground_bilinear():
    h = np.zeros((33, 33))
    h[:, 1] = 128.0  # rises west to east over the first quad
    assert seat.ground(h, 64.0, 10.0, (0, 0)) == 64.0


def test_seat_and_standing():
    t = {"forms": {"A:x.esm": {"seat": 340.0, "p10": 0, "p90": 0, "refs": 6},
                   "B:x.esm": {"seat": 206.0, "p10": 0, "p90": 0, "refs": 5},
                   "C:x.esm": {"seat": 50.0, "p10": 0, "p90": 0, "refs": 2}},
         "models": {"m\\c.nif": {"seat": 12.0, "p10": 0, "p90": 0, "refs": 9}}}
    assert seat.seat_of("A:x.esm", "m\\a.nif", t) == 340.0  # an erut tree, its roots buried by its mod
    assert seat.standing("A:x.esm", "m\\a.nif", -1, t)
    assert not seat.standing("B:x.esm", "m\\b.nif", 543, t)  # hanging moss: 337 units over the ground at its seat
    assert seat.seat_of("C:x.esm", "M/C.nif", t) == 12.0  # too few refs: its mesh's seat under another base
    assert not seat.standing("D:x.esm", "m\\d.nif", 0, t)  # never measured: not listed


def test_draft_splits_a_small_pool():
    pool = [{"form_key": f"{i:06X}:x.esm", "edid": f"shroom{i}", "model": f"m{i}.nif"} for i in range(12)]
    ecos = ("a", "b", "c", "d")
    d = lists.draft({e: pool for e in ecos}, "mushroom")
    seen = defaultdict(int)
    for e in ecos:
        assert len(d[e]) >= lists.CORE
        for f in d[e]:
            seen[f["form_key"]] += 1
    for e in ecos:  # every class differs from every other by at least a third of its kinds
        for o in ecos:
            if o != e:
                a, b = {f["form_key"] for f in d[e]}, {f["form_key"] for f in d[o]}
                assert len(a - b) / len(a) >= 1 / 3
