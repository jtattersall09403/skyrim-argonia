"""Each place's law: native (no cell, the Owing), foreign (the Imperial cells) or none (tools/newworld/place_law.py;
docs/design/law.md)."""
import pytest

from tools.argonia_world import db
from tools.newworld import frame as f
from tools.newworld import place_law


@pytest.fixture(scope="module")
def world():
    return db.open(f.ROOT)


def test_the_built_world_keeps_the_law_invariants(world):
    assert place_law.problems(world) == []


@pytest.mark.parametrize("place, law", [
    ("helstrom", "native"),              # the Hist capital: no cell
    ("toklea", "native"),                # "no Archwarden garrison" is not the Archwardens
    ("gideon", "foreign"),               # the Governor's Mansion and its courthouse
    ("fort-thornmoth", "foreign"),       # an Archwarden fort keeps the Imperial cells
    ("blackrose-prison", "none"),        # held by the Blackguards' heirs: its fight is its answer
])
def test_a_places_law_is_read_from_who_holds_it(world, place, law):
    assert world.get("place_law", place).law_id == law


def test_a_foreign_post_without_a_cell_sends_to_the_nearest_fort(world):
    r = world.get("place_law", "outpost-29-m66")
    assert r.law_id == "foreign" and r.jail_place_id == "fort-thornmoth"
