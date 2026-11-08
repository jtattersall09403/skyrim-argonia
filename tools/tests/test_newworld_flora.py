"""The new world's flora sets (nw-02 step 6): every region has a varied set, nothing Nordic, every base is a
catalogued mesh, water rules hold, and the regions differ from one another."""
import json
import re
from collections import defaultdict
from pathlib import Path

import pytest

from tools.argonia_world import db
from tools.newworld import flora

ROOT = Path(__file__).resolve().parents[2]
# Land regions share the swamp families of one province; 0.35 leaves every land pair under a third in common
# (measured max 0.29). The sea regions draw on Depths of Skyrim's small seabed pool (3 corals, 3 seaweeds,
# 3 kelps, 3 clams), so their ceiling is 0.5 (measured max 0.45).
LAND_MAX, SEA_MAX = 0.35, 0.5
NORDIC = re.compile(r"snow|pine|aspen|tundra|reach|birch|nord|skyrim\\")


@pytest.fixture(scope="module")
def w():
    return db.open(ROOT / "newworld", cache=False)


def test_every_region_has_a_varied_set(w):
    bases = defaultdict(set)
    habs = defaultdict(set)
    weight = defaultdict(float)
    for r in w.rows("region_flora"):
        bases[r.region_id].add(r.flora_base_id)
        habs[r.region_id].add(r.habitat_id)
        weight[r.region_id] += r.weight
    for reg in w.rows("region"):
        assert len(habs[reg.id]) >= 3, reg.id
        assert len(bases[reg.id]) >= (10 if reg.kind == "land" else 20), reg.id
        assert abs(weight[reg.id] - 1) < 1e-3, reg.id


def test_no_nordic_base(w):
    for b in w.rows("flora_base"):
        if b.nordic_override:
            assert "mangrove" in b.model.lower(), b.id
        else:
            assert not NORDIC.search(f"{b.edid} {b.model}".lower()), b.id


def test_every_base_is_a_catalogued_mesh(w):
    if not flora.CATALOGUE.exists():
        pytest.skip("the flora study's catalogue is not on this machine")
    cat = {(e["form"], e["modl"]): e for v in json.loads(flora.CATALOGUE.read_text())["catalogue"].values() for e in v}
    for b in w.rows("flora_base"):
        e = cat.get((b.form_key, b.model))
        assert e is not None, b.id
        assert not e["nordic_flag"] or b.nordic_override, b.id


def test_water_rules(w):
    hab = {h.id: h for h in w.rows("habitat")}
    fam = {f.id: f for f in w.rows("flora_family")}
    base = {b.id: b for b in w.rows("flora_base")}
    for r in w.rows("region_flora"):
        h, f = hab[r.habitat_id], fam[base[r.flora_base_id].flora_family_id]
        if r.water_max_m is not None:
            assert h.water == "standing", (r.region_id, r.flora_base_id)
            assert r.water_max_m <= min(h.depth_max_m, f.standing_water_max_m) <= 3.5
        if f.water_only:
            assert h.water != "dry", (r.region_id, r.flora_base_id)


def test_regions_differ():
    rows = flora.region_sets()[3]
    kind = {json.loads(line)["id"]: json.loads(line)["kind"]
            for line in (ROOT / "newworld/story/data/db/region.jsonl").read_text().splitlines()}
    for (a, b), j in flora.jaccard(rows).items():
        assert j < (SEA_MAX if "sea" in (kind[a], kind[b]) else LAND_MAX), (a, b, j)
