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


def test_counts_or_a_lair_never_make_a_settlement():
    from tools.places.sources_match import classify, settled
    lair = cand("db", [[0, 0]], 900, edid="DarkBrotherhoodSanctuaryLocation", keywords=["LocTypeTown"], residents=30)
    assert not settled(lair)
    crowd = cand("x", [[0, 0]], 900, edid="SomeBarrowLocation", residents=40, enemies=0, tags={"nordic": 9})
    assert classify(crowd)[0] not in ("city", "town", "village", "hamlet")


def test_population_is_the_same_on_a_rerun():
    from tools.places.sources_match import population
    p = {"status": "inhabited", "population": 100, "place_kind_id": "city"}
    assert population(p, [], {"residents": 322}) == population(p, [], {"residents": 322})


def test_two_clusters_in_one_cell_stay_two_places():
    a = cand("a", [[0, 0]], 100, keywords=["cluster"], location=None, box=[100, 100, 900, 900])
    b = cand("b", [[0, 0]], 100, keywords=["cluster"], location=None, box=[2500, 2500, 3900, 3900])
    assert len(physical_groups([a, b])) == 2
    check_unique([a, b])


def test_a_few_huts_with_beds_are_a_hamlet_and_ruin_pieces_a_ruin_of_their_tileset():
    from tools.places.sources_match import classify
    huts = cand("h", [[0, 0]], 120, keywords=["cluster"], location=None, residents=4, enemies=0,
                counts={"refs": 120, "building": 8, "furniture": 6}, tags={"argonian": 20})
    assert classify(huts)[0] == "hamlet"
    ruin = cand("r", [[0, 0]], 120, keywords=["cluster"], location=None, residents=0, enemies=3,
                counts={"refs": 120, "building": 12}, tags={"ayleid": 15, "ruin": 12})
    assert classify(ruin)[0] == "ruin-ayleid"
