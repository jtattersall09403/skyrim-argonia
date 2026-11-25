"""Whose dress a garment is: a garment is worn only by the people and offices it belongs to.

`newworld/sources/stock/item_material.json` carries the rule table (`dress`: each people and each office with its lore
source and who wears it) and tags each garment that belongs to a people (`people`) or an office (`office`). An untagged
garment is neutral: any wearer its race row fits may take it. A person's own people is the optional `people` of the
people source (`newworld/sources/people/<place>.json`), read here; their culture is the person's `culture_id`.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache

from tools.places.stock import split

PEOPLE = split.STOCK.parent / "people"


@lru_cache(maxsize=1)
def rules() -> dict:
    p = split.STOCK / "item_material.json"
    return json.loads(p.read_text(encoding="utf-8")).get("dress", {}) if p.exists() else {}


@lru_cache(maxsize=None)
def _people_of(place_id: str) -> dict[str, str]:
    p = PEOPLE / f"{place_id}.json"
    if not p.exists():
        return {}
    return {r["id"]: r["people"] for r in json.loads(p.read_text(encoding="utf-8")).get("people", []) if r.get("people")}


def peoples_of(person) -> set[str]:
    """The peoples a person belongs to: their people source's `people`, and every people whose `places` (the places
    the place record says are that people's own: item_material.json `dress`) hold the person's place."""
    own = _people_of(person.place_id).get(person.id)
    return ({own} if own else set()) | {k for k, v in rules().get("peoples", {}).items()
                                         if person.place_id in v["wearers"].get("places", [])}


def may_wear(garment_row: dict, person) -> bool:
    """True when the garment (its item_material row) is neutral or belongs to this person's people or office."""
    tab = rules()
    people, office = garment_row.get("people"), garment_row.get("office")
    if people:
        r = tab["peoples"][people]["wearers"]
        if people not in peoples_of(person) and getattr(person, "culture_id", None) not in r.get("cultures", []):
            return False
    if office:
        r = tab["offices"][office]["wearers"]
        if person.person_role_id not in r.get("roles", []) and \
                not re.search(r.get("match", r"(?!)"), person.trade or "", re.I):
            return False
    return True
