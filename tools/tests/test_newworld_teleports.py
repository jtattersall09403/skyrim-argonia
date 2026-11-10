"""Teleport cells of the new world (tools/newworld/teleports.py): every arrival on land above the water, in the
place's own cell, clear of placed objects; the console names."""
import json

import numpy as np

from tools.newworld import teleports as tp
from tools.newworld.world import units as su


def world(tmp_path, h, cx0=-3, cy_top=-150, refs=()):
    """A tiny built world: land manifest, heightmap, cells.json and refs under <tmp>/plugin."""
    p = tmp_path / "plugin"
    (p / "land").mkdir(parents=True)
    (p / "refs" / "flora").mkdir(parents=True)
    g = {"build_id": "t", "width": h.shape[1], "height": h.shape[0], "origin_x": cx0 * 4096.0,
         "origin_y": (cy_top + 1) * 4096.0, "water": 0.0}
    (p / "land" / "manifest.json").write_text(json.dumps({"grid": g, "marker": {"cell": [cx0, cy_top]}}))
    np.save(p / "land" / "limited.npy", h.astype(np.float32))
    (p / "cells.json").write_text(json.dumps({"cells": {}}))
    (p / "refs" / "flora" / "cy-150.jsonl").write_text("".join(json.dumps({"x": x, "y": y}) + "\n" for x, y in refs))
    return p, su.Grid("t", h.shape[1], h.shape[0], g["origin_x"], g["origin_y"], 0.0)


def test_coc_name():
    assert tp.coc_name("Fort Gysilla") == "ANWFortGysilla"
    assert tp.coc_name("Uzu-Tegh") == "ANWUzuTegh"
    assert tp.coc_name("Wreck of the Silt Bride") == "ANWWreckOfTheSiltBride"


def test_landing_is_dry_in_own_cell_and_clear_of_refs(tmp_path):
    h = np.full((3 * 32 + 1, 3 * 32 + 1), -200.0)  # 3 x 3 cells of water
    h[40:60, 40:60] = 12.0  # an island in the middle cell, barely above the water as Helstrom's marsh is
    centre_x, centre_y = -3 * 4096 + 50 * 128, -149 * 4096 - 50 * 128
    p, g = world(tmp_path, h, refs=[(centre_x, centre_y)])  # a tree on the island's centre
    refs = tp.refs_by_cell(p)
    own = (int(centre_x // 4096), int(centre_y // 4096))
    lnd = tp.landing(g, h, refs, centre_x, centre_y, own)
    assert lnd["own_cell"] and lnd["cell"] == list(own)
    r, c = lnd["sample"]
    assert h[r - 1:r + 2, c - 1:c + 2].min() >= tp.LAND_MIN  # land above the water, all round
    assert np.hypot(lnd["x"] - centre_x, lnd["y"] - centre_y) >= tp.CLEAR  # not inside the tree
    assert lnd["z"] > h[r, c]


def test_landing_falls_back_to_a_neighbour_cell(tmp_path):
    h = np.full((3 * 32 + 1, 3 * 32 + 1), -200.0)
    h[5:20, 5:20] = 40.0  # dry land only in the north-west cell
    p, g = world(tmp_path, h)
    lnd = tp.landing(g, h, {}, -2 * 4096 + 2048.0, -150 * 4096 - 2048.0, (-2, -151))  # the middle cell, all water
    assert not lnd["own_cell"] and lnd["cell"] == [-3, -150]


def test_check_flags_a_landing_in_water(tmp_path):
    h = np.full((32 + 1, 32 + 1), 50.0)
    h[10:20, 10:20] = -100.0
    p, g = world(tmp_path, h, cx0=-8, cy_top=-148)
    (p / "map").mkdir()
    x, y = -8 * 4096 + 15 * 128, -147 * 4096 - 15 * 128  # in the pond
    doc = {"build_id": "t", "cells": [{"coc": "ANWHelstrom", "cell": [-8, -148]}],
           "teleports": [{"kind": "place", "id": "helstrom", "coc": "ANWHelstrom", "cell": [-8, -148], "place_cell": [-8, -148],
                          "x": x, "y": y, "z": 0.0, "own_cell": True}]}
    (p / "map" / "teleports.json").write_text(json.dumps(doc))
    bad = tp.check(p)
    assert any("not above the water" in b for b in bad)
