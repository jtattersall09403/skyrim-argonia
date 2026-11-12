"""A place's rope lanterns: on its Hist's limbs, counted as the source mod counts them, and found in the air when
the tree under them changes."""
import math

from tools.places.draft import hang

BASES = {"P:hist": {"edid": "HistTree04", "kind": "tree", "model": "hist.nif", "bounds": [[-50, -50, 0], [50, 50, 800]]},
         "P:fern": {"edid": "Fern", "kind": "plant", "model": "f.nif"},
         hang.LANTERNS[0]: {"edid": "L5", "kind": "clutter", "model": "l5.nif", "bounds": [[-22, -23, -112], [23, 22, 6]]},
         hang.LANTERNS[1]: {"edid": "L4", "kind": "clutter", "model": "l4.nif", "bounds": [[-22, -23, -151], [23, 22, 6]]}}
PTS = [[150.0, 0.0, 300.0, 20], [-150.0, 0.0, 320.0, 20], [0.0, 150.0, 340.0, 20], [0.0, -150.0, 360.0, 20],
       [110.0, 110.0, 380.0, 20], [-110.0, -110.0, 400.0, 20]]
SHAPE = {"anchor": [-2.0, 3.0, 6.0], "drop": 157.0}


def rows(tree_rot=0.0):
    ext = [{"id": "p.hist", "base": "P:hist", "kind": "tree", "pos": [1000.0, 2000.0, 50.0], "rot": [0, 0, tree_rot], "scale": 1.0}]
    return ext, hang.plan("p", ext, BASES, lambda x, y: 50.0, lambda m: PTS if m == "hist.nif" else [],
                          lambda b: SHAPE, [5])


def test_several_on_one_hist_each_on_a_limb():
    ext, out = rows(0.7)
    assert len(out) == 5 and len({r["why"] for r in out}) == 5
    assert all(r["seat"] == {"mode": "on", "on": "p.hist", "dz": round(r["pos"][2] - 50.0, 2)} for r in out)
    assert hang.faults(ext + out, BASES, lambda m: PTS if m == "hist.nif" else [], lambda b: SHAPE) == []


def test_a_changed_tree_leaves_them_in_the_air():
    ext, out = rows(0.0)
    ext[0]["rot"] = [0, 0, math.pi / 3]
    f = hang.faults(ext + out, BASES, lambda m: PTS if m == "hist.nif" else [], lambda b: SHAPE)
    assert len(f) == len(out)


def test_no_hist_no_lanterns():
    ext = [{"id": "p.f", "base": "P:fern", "kind": "plant", "pos": [0.0, 0.0, 0.0], "rot": [0, 0, 0], "scale": 1.0}]
    assert hang.plan("p", ext, BASES, lambda x, y: 0.0, lambda m: PTS, lambda b: SHAPE, [3]) == []
