"""Light identities of a place's people (tools/places/identities.py) and their names reaching the draft."""
import json

from tools.places import identities
from tools.places.draft import people as draft_people

HH = "x.household.h1"


def _place(tmp_path, rows):
    d = tmp_path / "x"
    d.mkdir()
    folk = [{"id": "x.a", "name": "Ah-ja", "role": "smith", "home": "h1", "household": {"id": HH, "relation": "head"}},
            {"id": "x.b", "name": "Bee-ja", "role": "resident", "home": "h1",
             "household": {"id": HH, "relation": "partner"}},
            {"id": "x.g", "name": "Chee-ja", "role": "guard", "home": "h1"}]
    (d / "people.jsonl").write_text("".join(json.dumps(p) + "\n" for p in folk))
    (d / "identities.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    return folk


def _row(pid, name, role, **kw):
    r = {"id": pid, "name": name, "household": {"id": HH, "role": role}, "trade": "smith", "wealth": "W3",
         "backstory": "He works the forge.", "cites": ["lore.md"]}
    r.update(kw)
    return r


def _check(tmp_path):
    return identities.check("x", tmp_path, resolve=lambda c: c == "lore.md", names=({"nesh-deeka"}, {"okeemu"}))


def test_a_good_place_passes(tmp_path):
    _place(tmp_path, [_row("x.a", "Meshu-Ka", "head"), _row("x.b", "Neeshal", "partner"),
                      _row("x.g", "Uxal-Dee", "lodger", trade="the city levy")])
    assert _check(tmp_path) == []


def test_every_fault_is_named(tmp_path):
    _place(tmp_path, [_row("x.a", "Nesh-Deeka", "elder", wealth="W6", cites=["missing.md"]),
                      _row("x.b", "Okeemu", "head", backstory="One. Two. Three."),
                      _row("x.b", "Okeemu", "head"),
                      _row("x.z", "Stone-Eye", "head")])
    bad = "\n".join(_check(tmp_path))
    for want in ("x.b: 2 rows", "x.z: no person", "x.g: person without an identity", "canon or never-reuse",
                 "already a talker's name", "name 'Okeemu' also", "role elder but people.jsonl has head",
                 "W6", "cite 'missing.md'", "3 sentences", f"household {HH}: 3 heads"):
        assert want in bad, want


def test_a_guard_belongs_to_the_levy_and_a_household_to_one_roof(tmp_path):
    folk = _place(tmp_path, [])
    folk[2]["home"] = "exterior"
    (tmp_path / "x" / "people.jsonl").write_text("".join(json.dumps(p) + "\n" for p in folk))
    (tmp_path / "x" / "identities.jsonl").write_text("".join(json.dumps(r) + "\n" for r in [
        _row("x.a", "Meshu-Ka", "head"), _row("x.b", "Neeshal", "partner"), _row("x.g", "Uxal-Dee", "lodger")]))
    bad = "\n".join(_check(tmp_path))
    assert "x.g: a guard whose trade is not the levy" in bad
    assert f"household {HH}: members live in" in bad


def test_the_draft_takes_the_names(tmp_path):
    folk = _place(tmp_path, [_row("x.a", "Bee-ja", "head")])
    draft_people.apply_identities(folk, identities.read("x", tmp_path))
    names = [p["name"] for p in folk]
    assert names[0] == "Bee-ja" and names[2] == "Chee-ja"
    assert names[1] != "Bee-ja" and len(set(names)) == 3      # a placeholder that collides is minted again
    assert identities.read("nowhere", tmp_path) == {}
