"""Owner play test 3, finding 10 ("almost always crocodiles"): over 1,000 simulated loads, no model and no subject
takes over a third of the draws. The engine picks uniformly among the loading screens whose conditions pass (ours have
none: intermediate.loading_screen_layer), so a row's share is its count over the eligible rows; the simulation draws
from exactly the records the layer writes."""
import collections
import json
import random

import pytest

from tools.argonia_world.intermediate import LOADING_SCREENS

LOADS = 1000


def draws(seed: int = 7) -> list[dict]:
    rows = [r for r in json.loads(LOADING_SCREENS.read_text(encoding="utf-8"))["screens"] if not r.get("conditions")]
    rng = random.Random(seed)
    return [rng.choice(rows) for _ in range(LOADS)]


def test_no_model_takes_a_third_of_loads():
    d = draws()
    top, n = collections.Counter(r["model"]["mesh"].lower() for r in d).most_common(1)[0]
    assert n <= LOADS / 3, f"{top}: {n} of {LOADS} loads"
    crocs = sum("crocodile" in r["model"]["shows"] for r in d)
    assert crocs <= LOADS / 3, f"crocodile: {crocs} of {LOADS} loads"


@pytest.mark.xfail(strict=True, reason="the Hist is 5 of 12 screens (~42%): a content call for the planner (lane 1.12-r4-menus)")
def test_no_subject_takes_a_third_of_loads():
    # one subject shown by several meshes counts once: the Hist (tree, roots, pool, taproot, fruit)
    d = draws()
    top, n = collections.Counter("hist" if "Hist" in r["model"]["shows"] else r["model"]["shows"] for r in d).most_common(1)[0]
    assert n <= LOADS / 3, f"{top}: {n} of {LOADS} loads"
