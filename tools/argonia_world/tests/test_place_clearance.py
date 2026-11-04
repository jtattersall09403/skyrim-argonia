"""L1 (lane 1.15-r6-claywater-water; checks.md row 147, the still claywater-on.png of 2026-11-04: the player at the
quest-board marker shin-deep in the river): `python3 -m tools.argonia_world.places check claywater` is green on
the current game ground: every dry-land thing at the station stands 0.5 m or more over its cell's water, every dock
piece and the poler's work spot keep their 0.85 m deck seat, and the save's marker (the quest board) is dry."""
import pytest

from tools.argonia_world import db, place_build
from tools.argonia_world.places import __main__ as places


@pytest.fixture(scope="module")
def got():
    try:
        g = place_build.GameGround()
    except (FileNotFoundError, OSError) as e:
        pytest.skip(f"no terrain grid: {e}")
    return places.rows(db.open(), g, "claywater")


def test_claywater_stands_clear_of_its_water(got):
    assert len(got) > 100
    bad = [(d["short"], d["kind"], round(d["ground"] - (d["water"] or 0), 2)) for d in got if not d["ok"]]
    assert not bad, bad


def test_the_save_marker_is_first_and_dry(got):
    q = got[0]
    assert q["short"] == "quest-board" and q["kind"] == "dry" and q["ground"] - q["water"] >= places.DRY_M
    assert {d["short"] for d in got if d["kind"] == "dock"} >= {"land-dock1", "land-dock2", "poler-work", "signs"}
