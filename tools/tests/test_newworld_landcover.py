"""Landcover: noise is unit-scaled and the habitat chooser respects water, cliffs and depth caps."""
import numpy as np

from tools.newworld import landcover as lc


def test_fbm_unit_std():
    a = lc.fbm(3, (60, 80))
    assert a.shape == (60, 80) and abs(float(a.std()) - 1) < 1e-3


def test_choose_water_cliff_and_free_land():
    habs = [h["id"] for h in lc.jsonl("habitat")]
    kidx = {k: i for i, k in enumerate(sorted({"ocean", "shallow-coast", "bay", "estuary", "river", "stream", "lake",
                                                "pond", "green-marsh", "blackwater-swamp"}))}
    fields = lc.Fields((64, 64), habs + ["_band", "_stand", "_glade"])
    ch = lc.Chooser(habs, ["r"], {0: {"swamp_hummock": 0.5, "dry_hammock": 0.5}}, fields, kidx)
    n = (4,)
    z = np.zeros(n, np.float32)
    c = {"wr": z + 10, "wc": z + 10, "reg": np.zeros(n, int), "water": np.array([True, False, False, False]),
         "depth": np.array([30, 0, 0, 0], np.float32), "h": np.array([-30, 5, 5, 5], np.float32),
         "slope": np.array([0, 60, 2, 2], np.float32), "shore": np.array([-100, 50, 500, 500], np.float32),
         "kind": np.array([kidx["ocean"]] * 4), "sea": z + 999, "run": z + 999}
    out = ch.choose(c)
    name = [habs[v - 1] for v in out]
    assert name[0] == "seabed_deep" and name[1] == "cliff_face"
    assert set(name[2:]) <= {"swamp_hummock", "dry_hammock"}
