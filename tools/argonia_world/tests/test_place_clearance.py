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


def test_no_prop_stands_in_a_kept_creatures_pen(got):
    """Lane 1.15-r6-claywater-pads-look (02-well-junction-s0: a post through the pen's guar): no prop within a kept
    creature's sandbox radius + PEN_BODY_M of its pen marker. The rule fires on the round-6 pen (on the well)."""
    assert not [d["short"] for d in got if d["kind"] == "in a pen"]
    w = db.open()
    for n in ("kept-guar-1-pen", "kept-guar-2-pen"):
        w.update("build_ref", f"ref.claywater-station.{n}", x_m=324.5, y_m=3059.2)
    refs = [r for r in w.rows("build_ref") if r.cell_id == "cell.claywater-station.exterior"]
    assert {"well", "well-water", "mortar-tub"} <= {k.split(".")[-1] for k in places.in_pen(w, refs)}


def test_every_unheighted_thing_sits_on_its_ground_or_its_water(got):
    """Every placed thing with no z of its own stands within SUPPORT_TOL_M of its ground (dry) or at its water seat
    (dock, boat): nothing afloat, no deck fitting off its deck (the Dagon Fel cleats beside the jetty, round 6)."""
    assert not [d["short"] for d in got if d["kind"] == "afloat"]
    assert not [d["short"] for d in got if "cleat" in d["short"]]
