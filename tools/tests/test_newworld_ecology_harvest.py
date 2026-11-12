"""The ecology stage's harvestables (tools/newworld/ecology/harvest.py): the data binds every lore ingredient and every
kind to a real record, and the placement helpers keep to their grounds."""
import json
from pathlib import Path

import pytest

np = pytest.importorskip("numpy")

SRC = Path(__file__).resolve().parents[2] / "newworld/sources/ecology"
data = json.loads((SRC / "harvestables.json").read_text())
cat = json.loads((SRC / "harvest_bases.json").read_text())
bases = {b["ref"] for b in cat["bases"]}


def test_every_kind_record_is_in_the_catalogue_or_ours():
    ours = {"new:" + n["edid"] for n in data["new_records"]}
    for k, v in data["kinds"].items():
        assert v["records"], k
        for r in v["records"]:
            assert r in bases or r in ours, (k, r)


def test_every_lore_ingredient_of_every_region_is_bound_or_a_drop():
    for f in (SRC / "regions").glob("*.json"):
        for h in json.loads(f.read_text())["harvestables"]:
            m = data["lore"].get(h["ingredient"])
            assert m and (("kind" in m and m["kind"] in data["kinds"]) or m.get("drop")), (f.name, h["ingredient"])


def test_new_records_draw_on_real_meshes_and_ingredients():
    for n in data["new_records"]:
        assert n["flor_from"] in bases and n["ingr"]["from"] in cat["ingredients"], n["edid"]
        for src, i in n["ingr"].get("effects", []):
            assert src in cat["ingredients"] and i < len(cat["ingredients"][src]["effects"]), (n["edid"], src, i)


def test_nothing_nordic_reaches_the_player():
    for v in data["kinds"].values():
        assert "nordic" not in v["name"].lower()
    for rec in (r for v in data["kinds"].values() for r in v["records"]):
        assert "nordic" not in rec.lower()


def test_pools_name_known_kinds_and_masks():
    masks = {"bank", "bed-fresh", "bed-salt", "bed-brackish", "marsh", "shore", "canopy", "bush", "open", "rock", "any"}
    assert set(data["pools"]) == {"water", "shore", "forest", "mountain", "open"}
    for pool in data["pools"].values():
        for kind, mask, w in pool:
            assert kind in data["kinds"] and mask in masks and w > 0


def test_place_at_keeps_its_gap():
    pytest.importorskip("tools.newworld.ecology.toughness")
    from tools.newworld.ecology import harvest as H

    class CV:
        def world(self, ry, rx):
            return rx * 128.0, -ry * 128.0

        def ground(self, ry, rx):
            return 5.0

    mask = np.ones((32, 32), bool)
    rng = np.random.default_rng(1)
    taken = []
    for _ in range(30):
        H.place_at(CV(), mask, rng, taken)
    for i, a in enumerate(taken):
        for b in taken[:i]:
            assert (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 >= H.MIN_GAP ** 2
