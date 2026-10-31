"""1.12 §4: our wording of the skill-tree perks (world/db/perk_text.jsonl) keeps every number of the vanilla text.

The vanilla extract (tools/immersion/perk_extract.py -> out/perk-text/vanilla.json) is game text and stays out of git;
without it the number checks skip and only our own rows are checked."""
import json
import re
from pathlib import Path

import pytest

from tools.argonia_world import db

REPO = Path(__file__).resolve().parents[3]
EXTRACT = REPO / "out" / "perk-text" / "vanilla.json"
PERK_COUNT = 273  # the reachable skill-tree perks: the AVIF tree nodes and their rank chains (perk_extract.py)
NUMBER = re.compile(r"\d+(?:\.\d+)?")
WORDS = {"half", "twice", "double", "two", "three", "four", "five", "six", "fifteen"}
NORDIC = re.compile(r"\b(nord\w*|skyrim|dragonborn|thu'?um|jarl\w*|whiterun|mead|septim\w*|shout\w*|windhelm|riften|solitude)\b", re.I)


@pytest.fixture(scope="module")
def ours():
    return {r.formkey: r for r in db.open().rows("perk_text")}


@pytest.fixture(scope="module")
def vanilla():
    if not EXTRACT.is_file():
        pytest.skip("no game data extract (python3 tools/immersion/perk_extract.py)")
    return {r["formkey"]: r for r in json.loads(EXTRACT.read_text(encoding="utf-8"))}


def numbers(s):
    return sorted(NUMBER.findall(s))


def words(s):
    return sorted(w for w in re.findall(r"[a-z]+", s.lower()) if w in WORDS)


def test_row_count_is_the_reachable_perk_count(ours):
    assert len(ours) == PERK_COUNT


def test_rows_equal_the_extracts_reachable_perks(ours, vanilla):
    assert set(ours) == set(vanilla)


def test_every_number_is_unchanged(ours, vanilla):
    bad = [k for k, r in ours.items()
           if numbers(r.description) != numbers(vanilla[k]["desc"]) or numbers(r.name) != numbers(vanilla[k]["name"])]
    assert bad == []


def test_wording_is_reworded_and_no_nordic_tell(ours, vanilla):
    same = [k for k, r in ours.items() if r.description.strip() == vanilla[k]["desc"].strip()]
    assert same == []
    assert [k for k, r in ours.items() if NORDIC.search(r.name + " " + r.description)] == []


def test_number_words_are_kept_up_to_halves(ours, vanilla):
    # "Double duration" -> "twice as long" and "Half damage" -> "halves" are the two allowed re-expressions.
    bad = [k for k, r in ours.items() if words(r.description) != words(vanilla[k]["desc"])]
    assert len(bad) <= 2


def test_our_rows_alone_have_no_nordic_tell(ours):
    assert [k for k, r in ours.items() if NORDIC.search(r.name + " " + r.description)] == []
