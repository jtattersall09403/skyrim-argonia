"""Light identities of a place's people (tools/places/identities.py, read from newworld/sources/people) and their
names reaching the draft."""
import json

from tools.places import identities
from tools.places.draft import people as draft_people

HH = "x.household.h1"


def _write(tmp_path, rows, guard_body="levy", place="x"):
    """The people source (newworld/sources/people/<place>.json) beside the places folder tmp_path/places, and the
    lookups' guard bodies."""
    src = tmp_path / "sources" / "people"
    src.mkdir(parents=True, exist_ok=True)
    (src / "lookups.json").write_text(json.dumps({"guard_body": [{"id": "levy"}, {"id": "watch"}]}))
    people = [{"id": r["id"], "name": r["name"], "household": r["household"], "trade": r["trade"],
               "wealth": r["wealth"], "role": r.get("person_role", ROLES.get(r["id"])),
               "notes": [{"aspect": "backstory", "text": r["backstory"], "cites": r["cites"]}]} for r in rows]
    (src / f"{place}.json").write_text(json.dumps({"place_id": place, "guard_body": guard_body, "households": [],
                                                  "people": people}))


ROLES = {"x.a": "smith", "x.b": "resident", "x.g": "guard"}


def _place(tmp_path, rows):
    d = tmp_path / "places" / "x"
    d.mkdir(parents=True)
    folk = [{"id": "x.a", "name": "Ah-ja", "role": "smith", "home": "h1", "household": {"id": HH, "relation": "head"}},
            {"id": "x.b", "name": "Bee-ja", "role": "resident", "home": "h1",
             "household": {"id": HH, "relation": "partner"}},
            {"id": "x.g", "name": "Chee-ja", "role": "guard", "home": "h1"}]
    (d / "people.jsonl").write_text("".join(json.dumps(p) + "\n" for p in folk))
    _write(tmp_path, rows)
    return folk


def _row(pid, name, role, **kw):
    r = {"id": pid, "name": name, "household": {"id": HH, "role": role}, "trade": "smith", "wealth": "W3",
         "backstory": "He works the forge.", "cites": ["lore.md"]}
    r.update(kw)
    return r


def _check(tmp_path):
    return identities.check("x", tmp_path / "places", resolve=lambda c: c == "lore.md", names=({"nesh-deeka"}, {"okeemu"}))


def test_a_good_place_passes(tmp_path):
    _place(tmp_path, [_row("x.a", "Meshu-Ka", "head"), _row("x.b", "Neeshal", "partner"),
                      _row("x.g", "Uxal-Dee", "lodger", trade="the city levy")])
    assert _check(tmp_path) == []


def test_every_fault_is_named(tmp_path):
    _place(tmp_path, [_row("x.a", "Nesh-Deeka", "elder", wealth="W6", cites=["missing.md"], person_role="resident"),
                      _row("x.b", "Okeemu", "head", backstory="One. Two. Three."),
                      _row("x.b", "Okeemu", "head"),
                      _row("x.z", "Stone-Eye", "head")])
    bad = "\n".join(_check(tmp_path))
    for want in ("x.b: 2 rows", "x.z: no person", "x.g: person without an identity", "canon or never-reuse",
                 "already a talker's name", "name 'Okeemu' also", "role elder but people.jsonl has head",
                 "W6", "cite 'missing.md'", "3 sentences", f"household {HH}: 3 heads", "x.a: role 'resident'"):
        assert want in bad, want


def test_a_guard_belongs_to_the_levy_and_a_household_to_one_roof(tmp_path):
    folk = _place(tmp_path, [])
    folk[2]["home"] = "exterior"
    (tmp_path / "places" / "x" / "people.jsonl").write_text("".join(json.dumps(p) + "\n" for p in folk))
    _write(tmp_path, [_row("x.a", "Meshu-Ka", "head"), _row("x.b", "Neeshal", "partner"),
                      _row("x.g", "Uxal-Dee", "lodger")])
    bad = "\n".join(_check(tmp_path))
    assert "x.g: a guard whose trade does not name the place's levy" in bad
    assert f"household {HH}: members live in" in bad


def test_the_draft_takes_the_names(tmp_path):
    folk = _place(tmp_path, [_row("x.a", "Bee-ja", "head")])
    draft_people.apply_identities(folk, identities.read("x", tmp_path / "places"))
    names = [p["name"] for p in folk]
    assert names[0] == "Bee-ja" and names[2] == "Chee-ja"
    assert names[1] != "Bee-ja" and len(set(names)) == 3      # a placeholder that collides is minted again
    assert identities.read("nowhere", tmp_path / "places") == {}


def test_a_guard_names_the_places_own_guard_body(tmp_path):
    """The guard rule is the place's own word for its watch (the people source's guard_body, a lookup id), never
    one place's word for every place."""
    _place(tmp_path, [])
    good = [_row("x.a", "Meshu-Ka", "head"), _row("x.b", "Neeshal", "partner")]
    _write(tmp_path, good + [_row("x.g", "Uxal-Dee", "lodger", trade="the town watch, night")], guard_body="watch")
    assert _check(tmp_path) == []
    _write(tmp_path, good + [_row("x.g", "Uxal-Dee", "lodger", trade="the city levy")], guard_body="watch")
    assert "x.g: a guard whose trade does not name the place's watch" in _check(tmp_path)
    _write(tmp_path, good + [_row("x.g", "Uxal-Dee", "lodger", trade="the city levy")], guard_body="posse")
    assert any("guard_body 'posse' is not one of" in b for b in _check(tmp_path))


def test_a_name_is_checked_against_every_other_places_people(tmp_path):
    """A name another place's people source gives is taken; this place's own source is not read as another's."""
    _place(tmp_path, [])
    _write(tmp_path, [_row("y.a", "Meshu-Ka", "head")], place="y")
    _write(tmp_path, [_row("x.a", "Meshu-Ka", "head"), _row("x.b", "Neeshal", "partner"),
                      _row("x.g", "Uxal-Dee", "lodger", trade="the city levy")])
    given = identities.names_given("x", tmp_path / "places")
    assert given == {"meshu-ka": "the name of y.a (y)"}
    bad = identities.check("x", tmp_path / "places", resolve=lambda c: c == "lore.md", names=(set(), given))
    assert bad == ["x.a: 'Meshu-Ka' is already the name of y.a (y)"]
