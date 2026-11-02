"""Owner play test 3, finding 10 ("almost always crocodiles"): over 1,000 simulated loads, no model and no subject
takes over a third of the draws. The engine picks uniformly among the loading screens whose conditions pass (ours have
only a `chance` row's GetRandomPercent: intermediate.loading_screen_layer); the simulation draws from exactly the rows
the layer writes. The Hist was 5 of 12 rows (~42%) before its rows took a chance of 50."""
import collections
import json
import random

from tools.argonia_world.intermediate import LOADING_SCREENS

LOADS = 1000


def draws(seed: int = 7) -> list[dict]:
    """Each load: the rows whose condition passes (a `chance` row passes on that share), then one of them."""
    rows = json.loads(LOADING_SCREENS.read_text(encoding="utf-8"))["screens"]
    rng = random.Random(seed)
    out = []
    for _ in range(LOADS):
        eligible = [r for r in rows if rng.random() * 100 < r.get("chance", 100)]
        out.append(rng.choice(eligible))
    return out


def test_no_model_takes_a_third_of_loads():
    d = draws()
    top, n = collections.Counter(r["model"]["mesh"].lower() for r in d).most_common(1)[0]
    assert n <= LOADS / 3, f"{top}: {n} of {LOADS} loads"
    crocs = sum("crocodile" in r["model"]["shows"] for r in d)
    assert crocs <= LOADS / 3, f"crocodile: {crocs} of {LOADS} loads"


def test_no_subject_takes_a_third_of_loads():
    # one subject shown by several meshes counts once: the Hist (tree, roots, pool, taproot, fruit)
    d = draws()
    top, n = collections.Counter("hist" if "Hist" in r["model"]["shows"] else r["model"]["shows"] for r in d).most_common(1)[0]
    assert n <= LOADS / 3, f"{top}: {n} of {LOADS} loads"


def test_chance_rows_carry_their_condition():
    from tools.argonia_world.intermediate import loading_screen_layer

    class Alloc:
        def form_key(self, edid, *_):
            return f"{abs(hash(edid)) % 0xFFFFFF:06X}:Argonia.esm"

    lscr = [r for r in loading_screen_layer(Alloc()).records if r["type"] == "LSCR"]
    hist = [r for r in lscr if r.get("conditions")]
    assert len(hist) == 5 and all(r["conditions"][0]["function"] == "GetRandomPercent" for r in hist)
