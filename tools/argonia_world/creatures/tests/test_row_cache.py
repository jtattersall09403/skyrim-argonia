"""L2 (1.15 build speed): the creature plan cache. A row's key covers the code, the rules and every cell's planner
inputs; an equal key reloads the plans, a changed input or a stale stored key misses."""
import numpy as np

from tools.argonia_world.creatures import build


def _args(h=10.0):
    return [(-3, 5, np.full((33, 33), h), 0.0, "marsh", "D1", np.zeros((33, 33), bool), None)]


def test_row_key_covers_the_inputs():
    k = build.row_key("code", _args())
    assert k == build.row_key("code", _args())
    assert k != build.row_key("code", _args(h=11.0))  # the ground
    assert k != build.row_key("code2", _args())  # the code or the rules


def test_cached_row_round_trips_and_a_stale_key_misses(tmp_path):
    plans = [{"x": 1.0, "kind": "spawn"}]
    build.save_row(tmp_path, 5, "k", plans)
    assert build.load_row(tmp_path, 5, "k") == plans
    assert build.load_row(tmp_path, 5, "other") is None
    assert build.load_row(tmp_path, 4, "k") is None
