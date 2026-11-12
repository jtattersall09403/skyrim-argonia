"""Source places: one physical place is one source, and no two allocated sources share a cell."""
import pytest

from tools.places.sources_match import check_unique, physical_groups


def cand(sid, cells, refs, ws="W", group="skyrim", **kw):
    return {"source_id": sid, "cells": cells, "worldspace": ws, "group": group, "name": sid, "credit": group,
            "counts": {"refs": refs}, "keywords": [], "location": "L:1", "kind": "city", **kw}


def test_overlapping_candidates_are_one_place_and_the_richest_stands_for_it():
    reps = physical_groups([cand("town", [[0, 0], [1, 0]], 900), cand("marker", [[1, 0]], 50),
                            cand("other", [[5, 5]], 300), cand("elsewhere", [[0, 0]], 10, ws="X")])
    by = {r["source_id"]: r for r in reps}
    assert set(by) == {"town", "other", "elsewhere"}
    assert by["town"]["aliases"] == ["marker"]


def test_a_walled_citys_world_and_its_location_are_one_place():
    reps = physical_groups([cand("skyrim.whiterunlocation", [[3, -3]], 400, ws="Tamriel", edid="WhiterunLocation"),
                            cand("dos.cluster", [[5, -3]], 3000, ws="WR", group="dawnofskyrim",
                                 worldspace_edid="WhiterunWorld")])
    assert len(reps) == 1 and reps[0]["name"].startswith("skyrim.whiterunlocation")


def test_two_allocated_sources_on_one_cell_fail():
    with pytest.raises(AssertionError):
        check_unique([cand("a", [[0, 0]], 1), cand("b", [[0, 0], [0, 1]], 1)])
    check_unique([cand("a", [[0, 0]], 1), cand("b", [[0, 1]], 1)])
