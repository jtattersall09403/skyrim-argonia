"""The draft check bounds a land row by its stage: the carried ground by the place's ground cap, the rest by patch_max."""
from tools.places.draft.check import patch_bound
from tools.places.draft.ground import CAP


def test_carried_ground_rows_are_bound_by_the_ground_cap_and_the_rest_by_patch_max():
    place = {"draft": {"ground_cap": 450}}
    assert patch_bound({"by": "ground"}, place, 105.0) == 450.0
    assert patch_bound({"by": "ground"}, {}, 105.0) == CAP
    assert patch_bound({"by": "sap"}, place, 105.0) == 105.0
    assert patch_bound({}, place, 105.0) == 105.0
