"""L1/L2: river and creek banks stay mostly open at eye height (lane 1.15-r6-bank-plants): the placer's bank rule,
the measure, and the build's open share against Skyrim.esm's bar (lists.BANK_OPEN_BAR)."""
import json
from pathlib import Path

import numpy as np
import pytest

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.vegetation import banks, lists, place
from tools.argonia_world.vegetation.place import CellInputs, Rule

V = su.LAND_VERTS
ROOT = Path(__file__).resolve().parents[4]


def rule(**kw):
    base = dict(form_key="000001:Skyrim.esm", density_per_ha=400.0, clustering=1, radius_m=0.0, min_slope=0,
                max_slope=40, min_height=None, max_height=None, water_min=None, water_max=None, conform=False,
                scale=(1.0, 1.0))
    base.update(kw)
    return Rule(**base)


def cell(bank, cx=0):
    return CellInputs(cx, 0, np.full((V, V), 10.0), np.full((V, V), -np.inf), np.full((V, V), 0.0),
                      np.zeros((V, V), bool), south_row=1000, west_col=1000, roads=[], footprints=[],
                      bank=np.full((V, V), bank))


def test_tall_plants_on_a_bank_stand_only_in_clumps():
    n_off = sum(len(place.place_cell(cell(False, cx), [rule(bank=True)])["u"]) for cx in range(8))
    n_on = sum(len(place.place_cell(cell(True, cx), [rule(bank=True)])["u"]) for cx in range(8))
    assert n_off > 500
    assert 0.5 * lists.BANK_CLUMP < n_on / n_off < 2.0 * lists.BANK_CLUMP


def test_low_plants_and_dry_ground_are_untouched():
    low = sum(len(place.place_cell(cell(True, cx), [rule(bank=False)])["u"]) for cx in range(4))
    off = sum(len(place.place_cell(cell(False, cx), [rule(bank=False)])["u"]) for cx in range(4))
    assert low == off


def test_bush01_is_tall_by_its_mesh_not_its_obnd():
    # King of the Murkmire's Bush01: OBND top 113 units (1.6 m), mesh top 438 units (6.3 m, data/canopy-radius.json)
    assert lists.bank_tall(113, 438.0, 1.2)
    assert not lists.bank_tall(50, None, 1.2)


def test_the_measure_sees_a_plant_on_the_line_and_not_beside_it():
    u = su.UNITS_PER_METRE
    xy, head = np.array([[0.0, 0.0]]), np.array([[1.0, 0.0]])
    on = banks.Plants(np.array([[5 * u, 0.0, 1 * u, 3 * u]]))
    beside = banks.Plants(np.array([[5 * u, 9 * u, 1 * u, 3 * u]]))
    low = banks.Plants(np.array([[5 * u, 0.0, 1 * u, 0.5 * u]]))
    assert banks.closed(xy, head, on)[0]
    assert not banks.closed(xy, head, beside)[0]
    assert not banks.closed(xy, head, low)[0]


def test_bank_points_face_the_water():
    H = np.zeros((20, 20))
    lev = np.full(H.shape, np.nan)
    H[:, :10] = -1.0
    lev[:, :] = 0.0
    xy, head = banks.bank_points(H, lev, 0.0, 0.0)
    assert len(xy) and (head[:, 0] < -0.9).all()


@pytest.mark.skipif(not (ROOT / "out" / "terrain" / "vegetation" / "summary.json").is_file(),
                    reason="no out/terrain vegetation")
def test_the_builds_river_banks_are_open_at_the_bar():
    s = json.loads((ROOT / "out" / "terrain" / "vegetation" / "summary.json").read_text())
    if not s.get("bank_open"):
        pytest.skip("the shards predate the bank rule (bank-plants regenerate owed)")
    assert s["bank_open"]["open_share"] >= lists.BANK_OPEN_BAR, s["bank_open"]
