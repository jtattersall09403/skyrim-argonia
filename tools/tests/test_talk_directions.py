"""Directions the Morrowind way: the brief's words for distance, the route's shape, the lint ban on counts (B13) and
talk_check reading a told route back against its measured legs."""
import re
from pathlib import Path

import yaml

from tools.argonia_world import talk_route as tr
from tools.argonia_world.talk_check import told_problems

SRC = ("talk_route: speaker 00AC8E:Black Marsh.esm (0, 0); waypoints: 0A1B2C:Black Marsh.esm the burnt-out house "
       "(500, 900); 0A1B2D:Black Marsh North.esp Lilmoth Dock (900, 900); legs: shore 400@45 | walk 190@0 | "
       "walk 135@315; target 082193:Black Marsh North.esp (1200, 600)")
BANS = Path(__file__).resolve().parents[2] / ".claude/skills/dialogue-write/bans.yaml"


def test_bands_follow_the_measured_length():
    assert [tr.band(m) for m in (30, 100, 400, 1500, 5000)] == ["near", "short", "fair", "long", "far"]


def test_brief_text_carries_no_count():
    assert tr.in_words("Walk north-east about 129 paces, and the fire is there.") == \
        "Walk north-east a short way, and the fire is there."
    assert tr.in_words("A gleamblossom grows about 40 m south of here.") == "A gleamblossom grows just south of here."
    assert not re.search(r"\d", tr.in_words("Follow the shore 900 m west, then 300 paces north."))


def test_shape_names_legs_anchors_and_bands():
    assert tr.shape(SRC) == ("3 legs (shore, walk, walk); distance fair, short, short; anchors: the burnt-out house, "
                             "Lilmoth Dock")


def test_true_telling_passes():
    text = ("Follow the shore north-east a fair way, then east a short way to the burnt-out house on your left. "
            "South-east a little way from there is Lilmoth Dock.")
    assert tr.check_told(text, SRC) == []


def test_wrong_heading_order_band_and_count_are_caught():
    got = tr.check_told("Head west to Lilmoth Dock, then past the burnt-out house, a long journey; three hundred "
                        "paces.", SRC)
    assert any("'west' is no leg's heading" in p for p in got)
    assert any("landmarks out of order" in p for p in got)
    assert any("says far" in p for p in got)
    assert any(p.startswith("a count") for p in got)


def test_a_side_is_not_a_heading():
    assert tr.check_told("Follow the shore north-east a fair way to the north side of the burnt-out house.", SRC) == []


def test_a_reply_telling_two_routes_fails_only_what_both_break():
    other = SRC.replace("legs: shore 400@45 | walk 190@0 | walk 135@315", "legs: road 200@270")
    wrong, counts = told_problems("Go north-east a fair way; or for the other place, follow the path south.",
                                  [SRC, other])
    assert wrong == [] and counts == []


def test_lint_b13_matches_the_check():
    ban = next(b for b in yaml.safe_load(BANS.read_text()) if b["id"].startswith("B13"))
    for line, hit in [("three hundred paces east", True), ("about 129 paces", True), ("a few paces", True),
                      ("forty yards past the dock", True), ("up the steps to the temple", False),
                      ("two houses south", False), ("a short way north", False)]:
        assert bool(re.search(ban["detect"], line)) is hit, line
        assert bool(tr.COUNT.search(line)) is hit, line
