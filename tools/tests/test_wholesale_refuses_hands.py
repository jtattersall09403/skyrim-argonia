"""A whole re-lay of a place that holds hand edits is refused unless --discard-hand-edits is given."""
import json

from tools.places.draft import wholesale


def _place(tmp_path, save=None):
    pdir = tmp_path / "p"
    (pdir / "spaces" / "exterior").mkdir(parents=True)
    (pdir / "place.json").write_text(json.dumps({"place_id": "p"}))
    if save == "agent":
        (pdir / "agent-edits").mkdir()
        (pdir / "agent-edits" / "a1.json").write_text(json.dumps({"ops": []}))
    if save == "owner":
        (pdir / "edits").mkdir()
        (pdir / "edits" / "o1.json").write_text(json.dumps({"final": True, "ops": []}))
    return pdir


def test_a_place_without_hands_may_be_relaid(tmp_path):
    assert wholesale.hand_refusal(_place(tmp_path)) is None


def test_an_agent_save_refuses_and_names_the_narrow_ways(tmp_path):
    why = wholesale.hand_refusal(_place(tmp_path, "agent"))
    assert why and "a1" in why and "--rooms" in why and "--discard-hand-edits" in why


def test_an_owner_finalised_save_refuses(tmp_path):
    assert "o1" in wholesale.hand_refusal(_place(tmp_path, "owner"))
