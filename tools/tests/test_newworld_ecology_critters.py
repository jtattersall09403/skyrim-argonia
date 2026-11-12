"""The ecology stage's critters (insects, fish, swarms as critter spawner refs): the bindings and measures they read."""
import json
from collections import Counter
from pathlib import Path

import numpy as np

from tools.newworld.ecology import place

SRC = Path(__file__).resolve().parents[2] / "newworld/sources/ecology"
BIND = json.loads((SRC / "bindings.json").read_text())
MEAS = json.loads((SRC / "skyrim_measures.json").read_text())


def test_every_critter_binding_is_a_measured_or_master_base():
    bases = MEAS["critters"]["bases"]
    for kind, b in BIND["critter_kinds"].items():
        if not b.get("critter"):
            continue
        plugin, edid = b["critter"].split(":")
        assert plugin in ("Skyrim.esm", "Black Marsh.esm"), kind      # masters: linked, never copied
        assert plugin == "Black Marsh.esm" or edid in bases, kind    # a Skyrim spawner Skyrim itself places
        assert b["function"] in BIND["critter_functions"] and b["time"] in ("day", "night", "any", "none")
        assert not BIND["kinds"][kind].get("records")


def test_night_bindings_stand_on_night_only_spawners():
    bases = MEAS["critters"]["bases"]
    for kind, b in BIND["critter_kinds"].items():
        if b.get("critter") and b["time"] == "night":
            hours = bases[b["critter"].split(":")[1]]["spawn_hours"]
            assert hours and all(start >= 18 for start, _, _ in hours), kind


def test_a_time_bound_row_never_takes_a_spawner_of_the_other_time():
    for f in (SRC / "regions").glob("*.json"):
        for r in json.loads(f.read_text())["creatures"]:
            b = BIND["critter_kinds"].get(r["kind"], {})
            if b.get("critter") and r["time"] in ("day", "night"):
                assert b["time"] in (r["time"], "none"), (f.stem, r["kind"])


def test_rates_are_skyrims_times_the_modders_factor():
    rates = place.critter_rates(BIND, MEAS)
    f = MEAS["critters"]["black_marsh"]["factor"]
    one = sum(MEAS["critters"]["bases"][n]["refs_per_100_cells_by_class"].get("shore", 0) for n in BIND["critter_functions"]["pond"]
              if n in MEAS["critters"]["bases"]) / 100 * f
    assert abs(rates["pond"]["shore"] - one) < 1e-9 and rates["pond"]["shore"] > rates["pond"].get("forest", 0)


class FakeCell:
    def __init__(self, ground):
        self.ground = ground

    def mask(self, row):
        return np.ones((32, 32), bool) if row["habitat"] == self.ground else np.zeros((32, 32), bool)

    def world(self, ry, rx):
        return 100.0 + rx, 200.0 - ry

    def ground_z(self):
        return 0.0


def test_critters_are_of_the_regions_kinds_and_the_cells_ground(monkeypatch):
    monkeypatch.setattr(place, "z_for", lambda cv, r, ry, rx: 16.0)
    rows = [{"kind": "torchbug", "habitat": "marsh", "time": "night", "size_class": "insect", "signature": False},
            {"kind": "fleshfly", "habitat": "any", "time": "day", "size_class": "insect", "signature": False},
            {"kind": "flying-fish", "habitat": "water-salt", "time": "day", "size_class": "small", "signature": False}]
    cv = FakeCell("marsh")
    rates = {"insects": {"shore": 5.0}, "pond": {"shore": 5.0}}
    out = place.critters(cv, "shore", rows, rates, BIND, np.random.default_rng(1), 0.0, Counter(), Counter(), "r")
    assert out and len(out) <= place.CRITTER_CAP
    assert {o["kind"] for o in out} == {"torchbug"}                 # only the kind whose ground the cell holds
    assert all(o["base"] == "Skyrim.esm:critterSpawnInsects_ManyNocturnalOnly" and o["time"] == "night" for o in out)
    again = place.critters(cv, "shore", rows, rates, BIND, np.random.default_rng(1), 0.0, Counter(), Counter(), "r")
    assert out == again                                              # the same seed writes the same refs
